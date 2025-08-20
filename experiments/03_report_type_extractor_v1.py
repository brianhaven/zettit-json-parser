#!/usr/bin/env python3

"""
Report Type Extraction System v1.0
Extracts report types from market research titles using MongoDB patterns.
Designed to work after date extraction for clean topic identification.
Created for Market Research Title Parser project.
"""

import re
import logging
from typing import Dict, List, Optional, Tuple, Any, Union
from dataclasses import dataclass
from enum import Enum
from datetime import datetime, timezone
import pytz

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ReportTypeFormat(Enum):
    """Enumeration of report type format types."""
    TERMINAL_TYPE = "terminal_type"        # "Market Report, 2030" → "Report"
    EMBEDDED_TYPE = "embedded_type"        # "Global Market Analysis" → "Analysis"  
    PREFIX_TYPE = "prefix_type"            # "Market Size Report" → "Report"
    COMPOUND_TYPE = "compound_type"        # "Market Research Report" → "Research Report"
    UNKNOWN = "unknown"

@dataclass
class ReportTypeExtractionResult:
    """Result of report type extraction."""
    title: str
    original_title: str
    extracted_report_type: Optional[str]
    normalized_report_type: Optional[str]
    format_type: ReportTypeFormat
    confidence: float
    matched_pattern: Optional[str]
    raw_match: Optional[str]
    date_removed_title: Optional[str]
    notes: Optional[str] = None

@dataclass
class ReportTypeExtractionStats:
    """Statistics for report type extraction results."""
    total_processed: int
    successful_extractions: int
    terminal_type_count: int
    embedded_type_count: int
    prefix_type_count: int
    compound_type_count: int
    failed_extractions: int
    success_rate: float

class ReportTypeExtractor:
    """
    Report Type Extraction System for market research titles.
    
    Extracts report types using database patterns with smart combination logic:
    - Uses existing date patterns to handle date variations dynamically
    - Processes titles after date extraction for cleaner results
    - Stores only core report types in database (not 4,000+ combinations)
    """
    
    def __init__(self, pattern_library_manager):
        """
        Initialize the Report Type Extractor.
        
        Args:
            pattern_library_manager: PatternLibraryManager instance for pattern retrieval (REQUIRED)
        """
        if not pattern_library_manager:
            raise ValueError("PatternLibraryManager is required - ReportTypeExtractor must use database patterns only")
        
        self.pattern_library_manager = pattern_library_manager
        self.extraction_stats = {
            'total_processed': 0,
            'successful_extractions': 0,
            'terminal_type': 0,
            'embedded_type': 0,
            'prefix_type': 0,
            'compound_type': 0,
            'failed_extractions': 0
        }
        
        # Initialize empty pattern lists (will be populated from database)
        self.terminal_type_patterns = []
        self.embedded_type_patterns = []
        self.prefix_type_patterns = []
        self.compound_type_patterns = []
        
        # Load report type patterns from database (required)
        self._load_library_patterns()
        
        # Common report type normalizations
        self.report_type_normalizations = {}
        self._load_normalizations()
    
    def _load_library_patterns(self) -> None:
        """Load report type patterns from MongoDB pattern library (REQUIRED)."""
        try:
            from pattern_library_manager_v1 import PatternType
            
            # Load report type patterns from MongoDB by category
            report_patterns = self.pattern_library_manager.get_patterns(PatternType.REPORT_TYPE)
            
            if not report_patterns:
                raise RuntimeError("No report type patterns found in MongoDB pattern_libraries collection. Please run initialize_report_patterns.py first.")
            
            # Organize patterns by format type
            terminal_type_patterns = []
            embedded_type_patterns = []
            prefix_type_patterns = []
            compound_type_patterns = []
            
            for pattern in report_patterns:
                if not pattern.get('active', True):
                    continue
                    
                format_type = pattern.get('format_type', '')
                pattern_regex = pattern.get('pattern', '')
                
                if not pattern_regex:
                    logger.warning(f"Pattern '{pattern.get('term', 'unknown')}' has no regex pattern")
                    continue
                
                if format_type == 'terminal_type':
                    terminal_type_patterns.append(pattern_regex)
                elif format_type == 'embedded_type':
                    embedded_type_patterns.append(pattern_regex)
                elif format_type == 'prefix_type':
                    prefix_type_patterns.append(pattern_regex)
                elif format_type == 'compound_type':
                    compound_type_patterns.append(pattern_regex)
                else:
                    logger.warning(f"Unknown format_type '{format_type}' for pattern '{pattern.get('term', 'unknown')}'")
            
            # Validate that we have patterns for each format type
            if not terminal_type_patterns:
                logger.warning("No terminal type patterns found in database")
            if not embedded_type_patterns:
                logger.warning("No embedded type patterns found in database")
            if not prefix_type_patterns:
                logger.warning("No prefix type patterns found in database")
            if not compound_type_patterns:
                logger.warning("No compound type patterns found in database")
            
            # Set patterns from database
            self.terminal_type_patterns = terminal_type_patterns
            self.embedded_type_patterns = embedded_type_patterns
            self.prefix_type_patterns = prefix_type_patterns
            self.compound_type_patterns = compound_type_patterns
            
            logger.info(f"Successfully loaded report type patterns from MongoDB:")
            logger.info(f"  - Terminal type: {len(terminal_type_patterns)} patterns")
            logger.info(f"  - Embedded type: {len(embedded_type_patterns)} patterns")
            logger.info(f"  - Prefix type: {len(prefix_type_patterns)} patterns")
            logger.info(f"  - Compound type: {len(compound_type_patterns)} patterns")
            logger.info(f"  - Total: {len(report_patterns)} patterns loaded")
            
        except Exception as e:
            error_msg = f"CRITICAL: Failed to load report type patterns from MongoDB: {e}"
            logger.error(error_msg)
            raise RuntimeError(error_msg + "\n\nReportTypeExtractor requires database patterns. Please check:\n1. MongoDB connection\n2. pattern_libraries collection exists\n3. Run initialize_report_patterns.py to populate patterns")
    
    def _load_normalizations(self) -> None:
        """Load report type normalizations from database or set defaults."""
        try:
            # Try to load normalizations from database
            normalizations = self.pattern_library_manager.get_patterns(PatternType.REPORT_TYPE)
            for pattern in normalizations:
                term = pattern.get('term', '')
                normalized = pattern.get('normalized_form', term)
                if term and normalized:
                    self.report_type_normalizations[term.lower()] = normalized
            
            logger.info(f"Loaded {len(self.report_type_normalizations)} report type normalizations")
            
        except Exception as e:
            logger.warning(f"Could not load normalizations from database: {e}")
            
            # Set basic normalizations as fallback
            self.report_type_normalizations = {
                'rpt': 'Report',
                'analysis': 'Analysis',
                'study': 'Study',
                'research': 'Research',
                'outlook': 'Outlook',
                'forecast': 'Forecast',
                'overview': 'Overview',
                'insights': 'Insights',
                'intelligence': 'Intelligence',
                'assessment': 'Assessment'
            }
            logger.info("Using fallback normalizations")
    
    def _get_timestamps(self) -> tuple:
        """Generate PDT and UTC timestamps."""
        utc_now = datetime.now(timezone.utc)
        pdt_tz = pytz.timezone('America/Los_Angeles')
        pdt_now = utc_now.astimezone(pdt_tz)
        
        pdt_str = pdt_now.strftime('%Y-%m-%d %H:%M:%S %Z')
        utc_str = utc_now.strftime('%Y-%m-%d %H:%M:%S UTC')
        
        return pdt_str, utc_str, utc_now
    
    def _preprocess_title(self, title: str) -> Tuple[str, List[str]]:
        """
        Preprocess title for report type extraction.
        
        Args:
            title: Title text (potentially with dates already removed)
            
        Returns:
            Tuple of (processed_title, list_of_preprocessing_steps)
        """
        preprocessing_steps = []
        processed_title = title
        
        # Step 1: Strip whitespace
        processed_title = processed_title.strip()
        preprocessing_steps.append("whitespace_trimmed")
        
        # Step 2: Normalize multiple spaces
        processed_title = re.sub(r'\s+', ' ', processed_title)
        preprocessing_steps.append("spaces_normalized")
        
        # Step 3: Remove common punctuation that interferes with matching
        processed_title = re.sub(r'[,\.]+$', '', processed_title)  # Remove trailing commas/periods
        preprocessing_steps.append("trailing_punctuation_removed")
        
        logger.debug(f"Preprocessed '{title}' -> '{processed_title}' (steps: {preprocessing_steps})")
        
        return processed_title, preprocessing_steps
    
    def remove_dates_from_title(self, title: str, date_extractor=None) -> Tuple[str, Optional[str]]:
        """
        Remove dates from title using DateExtractor if available.
        
        Args:
            title: Original title
            date_extractor: Optional DateExtractor instance
            
        Returns:
            Tuple of (title_without_dates, extracted_date_range)
        """
        if not date_extractor:
            # No date extractor provided, return original title
            return title, None
        
        try:
            # Extract date first
            date_result = date_extractor.extract(title)
            
            if date_result.extracted_date_range and date_result.raw_match:
                # Remove the matched date pattern from title
                title_without_date = title.replace(date_result.raw_match, '').strip()
                
                # Clean up multiple spaces and punctuation
                title_without_date = re.sub(r'\s+', ' ', title_without_date)
                title_without_date = re.sub(r'[,\.]+$', '', title_without_date)
                
                logger.debug(f"Removed date '{date_result.raw_match}' from title: '{title}' -> '{title_without_date}'")
                return title_without_date, date_result.extracted_date_range
            
            return title, None
            
        except Exception as e:
            logger.warning(f"Error removing dates from title: {e}")
            return title, None
    
    def normalize_report_type(self, report_type: str) -> str:
        """
        Normalize report type to standard form.
        
        Args:
            report_type: Raw extracted report type
            
        Returns:
            Normalized report type
        """
        if not report_type:
            return ""
        
        # Check normalizations map
        normalized = self.report_type_normalizations.get(report_type.lower())
        if normalized:
            return normalized
        
        # Default: title case
        return report_type.title()
    
    def _calculate_confidence(self, format_type: ReportTypeFormat, report_type: str, 
                             raw_match: str) -> float:
        """
        Calculate confidence score for report type extraction.
        
        Args:
            format_type: Type of format detected
            report_type: Extracted report type
            raw_match: Raw matched text
            
        Returns:
            Confidence score between 0.0 and 1.0
        """
        confidence = 0.5  # Base confidence
        
        # Higher confidence for specific patterns
        if format_type == ReportTypeFormat.TERMINAL_TYPE:
            confidence = 0.90  # High reliability - clear separation
        elif format_type == ReportTypeFormat.COMPOUND_TYPE:
            confidence = 0.95  # Very high reliability - specific compound patterns
        elif format_type == ReportTypeFormat.PREFIX_TYPE:
            confidence = 0.85  # Good reliability - clear prefix patterns
        elif format_type == ReportTypeFormat.EMBEDDED_TYPE:
            confidence = 0.80  # Lower reliability - embedded in text
        else:
            confidence = 0.30  # Unknown pattern
        
        # Adjust based on report type clarity
        if report_type:
            common_types = ['report', 'analysis', 'study', 'research', 'outlook', 'forecast']
            if report_type.lower() in common_types:
                confidence *= 1.1  # Boost for common types
            
            if len(report_type) >= 3:  # Avoid very short matches
                confidence *= 1.05
        
        return round(min(confidence, 1.0), 3)
    
    def extract_terminal_type(self, title: str) -> ReportTypeExtractionResult:
        """
        Extract terminal report types (at end of title).
        
        Args:
            title: Title to extract from
            
        Returns:
            ReportTypeExtractionResult with extraction details
        """
        for pattern in self.terminal_type_patterns:
            match = re.search(pattern, title, re.IGNORECASE)
            if match:
                report_type = match.group(1) if match.groups() else match.group(0)
                normalized_type = self.normalize_report_type(report_type)
                confidence = self._calculate_confidence(
                    ReportTypeFormat.TERMINAL_TYPE, report_type, match.group(0)
                )
                
                return ReportTypeExtractionResult(
                    title=title,
                    original_title=title,
                    extracted_report_type=report_type,
                    normalized_report_type=normalized_type,
                    format_type=ReportTypeFormat.TERMINAL_TYPE,
                    confidence=confidence,
                    matched_pattern=pattern,
                    raw_match=match.group(0),
                    date_removed_title=None,
                    notes="Terminal type format"
                )
        
        return ReportTypeExtractionResult(
            title=title,
            original_title=title,
            extracted_report_type=None,
            normalized_report_type=None,
            format_type=ReportTypeFormat.UNKNOWN,
            confidence=0.0,
            matched_pattern=None,
            raw_match=None,
            date_removed_title=None,
            notes="No terminal type detected"
        )
    
    def extract_embedded_type(self, title: str) -> ReportTypeExtractionResult:
        """
        Extract embedded report types (within title text).
        
        Args:
            title: Title to extract from
            
        Returns:
            ReportTypeExtractionResult with extraction details
        """
        for pattern in self.embedded_type_patterns:
            match = re.search(pattern, title, re.IGNORECASE)
            if match:
                report_type = match.group(1) if match.groups() else match.group(0)
                normalized_type = self.normalize_report_type(report_type)
                confidence = self._calculate_confidence(
                    ReportTypeFormat.EMBEDDED_TYPE, report_type, match.group(0)
                )
                
                return ReportTypeExtractionResult(
                    title=title,
                    original_title=title,
                    extracted_report_type=report_type,
                    normalized_report_type=normalized_type,
                    format_type=ReportTypeFormat.EMBEDDED_TYPE,
                    confidence=confidence,
                    matched_pattern=pattern,
                    raw_match=match.group(0),
                    date_removed_title=None,
                    notes="Embedded type format"
                )
        
        return ReportTypeExtractionResult(
            title=title,
            original_title=title,
            extracted_report_type=None,
            normalized_report_type=None,
            format_type=ReportTypeFormat.UNKNOWN,
            confidence=0.0,
            matched_pattern=None,
            raw_match=None,
            date_removed_title=None,
            notes="No embedded type detected"
        )
    
    def extract_prefix_type(self, title: str) -> ReportTypeExtractionResult:
        """
        Extract prefix report types (at start of title).
        
        Args:
            title: Title to extract from
            
        Returns:
            ReportTypeExtractionResult with extraction details
        """
        for pattern in self.prefix_type_patterns:
            match = re.search(pattern, title, re.IGNORECASE)
            if match:
                report_type = match.group(1) if match.groups() else match.group(0)
                normalized_type = self.normalize_report_type(report_type)
                confidence = self._calculate_confidence(
                    ReportTypeFormat.PREFIX_TYPE, report_type, match.group(0)
                )
                
                return ReportTypeExtractionResult(
                    title=title,
                    original_title=title,
                    extracted_report_type=report_type,
                    normalized_report_type=normalized_type,
                    format_type=ReportTypeFormat.PREFIX_TYPE,
                    confidence=confidence,
                    matched_pattern=pattern,
                    raw_match=match.group(0),
                    date_removed_title=None,
                    notes="Prefix type format"
                )
        
        return ReportTypeExtractionResult(
            title=title,
            original_title=title,
            extracted_report_type=None,
            normalized_report_type=None,
            format_type=ReportTypeFormat.UNKNOWN,
            confidence=0.0,
            matched_pattern=None,
            raw_match=None,
            date_removed_title=None,
            notes="No prefix type detected"
        )
    
    def extract_compound_type(self, title: str) -> ReportTypeExtractionResult:
        """
        Extract compound report types (multiple words).
        
        Args:
            title: Title to extract from
            
        Returns:
            ReportTypeExtractionResult with extraction details
        """
        for pattern in self.compound_type_patterns:
            match = re.search(pattern, title, re.IGNORECASE)
            if match:
                report_type = match.group(1) if match.groups() else match.group(0)
                normalized_type = self.normalize_report_type(report_type)
                confidence = self._calculate_confidence(
                    ReportTypeFormat.COMPOUND_TYPE, report_type, match.group(0)
                )
                
                return ReportTypeExtractionResult(
                    title=title,
                    original_title=title,
                    extracted_report_type=report_type,
                    normalized_report_type=normalized_type,
                    format_type=ReportTypeFormat.COMPOUND_TYPE,
                    confidence=confidence,
                    matched_pattern=pattern,
                    raw_match=match.group(0),
                    date_removed_title=None,
                    notes="Compound type format"
                )
        
        return ReportTypeExtractionResult(
            title=title,
            original_title=title,
            extracted_report_type=None,
            normalized_report_type=None,
            format_type=ReportTypeFormat.UNKNOWN,
            confidence=0.0,
            matched_pattern=None,
            raw_match=None,
            date_removed_title=None,
            notes="No compound type detected"
        )
    
    def extract(self, title: str, original_title: str = None, date_extractor=None) -> ReportTypeExtractionResult:
        """
        Extract report type from title using all available patterns.
        
        Args:
            title: Title to extract from (potentially with dates already removed)
            original_title: Original title before date removal (for reference)
            date_extractor: Optional DateExtractor instance for smart date removal
            
        Returns:
            ReportTypeExtractionResult with best extraction found
        """
        if not title or not title.strip():
            return ReportTypeExtractionResult(
                title=title,
                original_title=original_title or title,
                extracted_report_type=None,
                normalized_report_type=None,
                format_type=ReportTypeFormat.UNKNOWN,
                confidence=0.0,
                matched_pattern=None,
                raw_match=None,
                date_removed_title=None,
                notes="Empty or whitespace-only title"
            )
        
        # Track processing
        self.extraction_stats['total_processed'] += 1
        
        # Preprocess title
        processed_title, preprocessing_steps = self._preprocess_title(title)
        
        # If date_extractor provided and we're working with original title, remove dates first
        date_removed_title = None
        if date_extractor and original_title:
            processed_title, extracted_date = self.remove_dates_from_title(original_title, date_extractor)
            date_removed_title = processed_title
        
        # Try extraction methods in order of reliability
        extraction_methods = [
            self.extract_compound_type,     # Highest reliability (95%)
            self.extract_terminal_type,     # High reliability (90%)
            self.extract_prefix_type,       # Good reliability (85%)
            self.extract_embedded_type,     # Lower reliability (80%)
        ]
        
        best_result = None
        best_confidence = 0.0
        
        for method in extraction_methods:
            result = method(processed_title)
            
            if result.extracted_report_type and result.confidence > best_confidence:
                best_result = result
                best_confidence = result.confidence
        
        # Use best result or create failure result
        if best_result and best_result.extracted_report_type:
            # Update statistics
            self.extraction_stats['successful_extractions'] += 1
            
            if best_result.format_type == ReportTypeFormat.TERMINAL_TYPE:
                self.extraction_stats['terminal_type'] += 1
            elif best_result.format_type == ReportTypeFormat.EMBEDDED_TYPE:
                self.extraction_stats['embedded_type'] += 1
            elif best_result.format_type == ReportTypeFormat.PREFIX_TYPE:
                self.extraction_stats['prefix_type'] += 1
            elif best_result.format_type == ReportTypeFormat.COMPOUND_TYPE:
                self.extraction_stats['compound_type'] += 1
            
            # Update result with additional context
            best_result.original_title = original_title or title
            best_result.date_removed_title = date_removed_title
            
            logger.debug(f"Report type extracted from '{title}': {best_result.extracted_report_type}")
            return best_result
        
        else:
            # No extraction successful
            self.extraction_stats['failed_extractions'] += 1
            
            return ReportTypeExtractionResult(
                title=processed_title,
                original_title=original_title or title,
                extracted_report_type=None,
                normalized_report_type=None,
                format_type=ReportTypeFormat.UNKNOWN,
                confidence=0.0,
                matched_pattern=None,
                raw_match=None,
                date_removed_title=date_removed_title,
                notes="No report type patterns detected"
            )
    
    def extract_batch(self, titles: List[str], date_extractor=None) -> List[ReportTypeExtractionResult]:
        """
        Extract report types from a batch of titles.
        
        Args:
            titles: List of titles to process
            date_extractor: Optional DateExtractor instance for date removal
            
        Returns:
            List of ReportTypeExtractionResult objects
        """
        results = []
        
        logger.info(f"Starting batch report type extraction of {len(titles)} titles")
        
        for i, title in enumerate(titles):
            if i > 0 and i % 1000 == 0:
                logger.info(f"Processed {i}/{len(titles)} titles...")
            
            result = self.extract(title, original_title=title, date_extractor=date_extractor)
            results.append(result)
        
        logger.info(f"Completed batch report type extraction of {len(titles)} titles")
        return results
    
    def get_extraction_statistics(self) -> ReportTypeExtractionStats:
        """
        Get current extraction statistics.
        
        Returns:
            ReportTypeExtractionStats object with current statistics
        """
        total = self.extraction_stats['total_processed']
        
        if total == 0:
            return ReportTypeExtractionStats(
                total_processed=0,
                successful_extractions=0,
                terminal_type_count=0,
                embedded_type_count=0,
                prefix_type_count=0,
                compound_type_count=0,
                failed_extractions=0,
                success_rate=0.0
            )
        
        return ReportTypeExtractionStats(
            total_processed=total,
            successful_extractions=self.extraction_stats['successful_extractions'],
            terminal_type_count=self.extraction_stats['terminal_type'],
            embedded_type_count=self.extraction_stats['embedded_type'],
            prefix_type_count=self.extraction_stats['prefix_type'],
            compound_type_count=self.extraction_stats['compound_type'],
            failed_extractions=self.extraction_stats['failed_extractions'],
            success_rate=round((self.extraction_stats['successful_extractions'] / total) * 100, 2)
        )


def demo_report_type_extraction():
    """Demonstrate Report Type Extractor functionality."""
    
    print("Report Type Extraction System Demo")
    print("=" * 50)
    
    # Sample titles for testing different report type formats
    sample_titles = [
        # Terminal type format (after comma)
        "Global AI Market Size Report, 2030",  # After date removal: "Global AI Market Size Report"
        "Healthcare Technology Analysis, 2025-2030",  # After date removal: "Healthcare Technology Analysis"
        "APAC Consumer Electronics Study, 2031",  # After date removal: "APAC Consumer Electronics Study"
        
        # Embedded type format (within title)
        "Blockchain Market Research Overview",
        "Automotive Industry Forecast Report",
        "Digital Health Market Insights",
        "Renewable Energy Assessment Study",
        
        # Prefix type format (at start)
        "Market Report: Global Semiconductors",
        "Industry Analysis: 5G Technology",
        "Research Study: Electric Vehicles",
        
        # Compound type format
        "Global Technology Market Research Report",
        "Healthcare Industry Intelligence Assessment",
        "APAC Market Size and Share Analysis",
        
        # Edge cases
        "Global Market Trends",  # No clear report type
        "Annual Financial Report 2023",  # Non-market research
        "Innovation in Healthcare",  # No report type
    ]
    
    try:
        # Initialize extractor with pattern library manager (REQUIRED)
        from pattern_library_manager_v1 import PatternLibraryManager
        pattern_manager = PatternLibraryManager()
        extractor = ReportTypeExtractor(pattern_manager)
        print("✅ Using MongoDB pattern library for report type extraction")
        
        print(f"\n1. Individual Extraction Examples:")
        print("-" * 40)
        
        for title in sample_titles[:8]:  # Show first 8 examples
            # For demo, simulate date removal (in real use, would use DateExtractor)
            title_no_date = re.sub(r',\s*\d{4}(\s*[-–—]\s*\d{4})?\s*$', '', title).strip()
            
            # Extract report type
            result = extractor.extract(title_no_date, original_title=title)
            print(f"Title: {title[:70]}...")
            print(f"  After date removal: {title_no_date}")
            print(f"  Report Type: {result.extracted_report_type}")
            print(f"  Normalized: {result.normalized_report_type}")
            print(f"  Format: {result.format_type.value}")
            print(f"  Confidence: {result.confidence:.3f}")
            print(f"  Raw Match: {result.raw_match}")
            print()
        
        # Close pattern manager
        pattern_manager.close_connection()
        
        print("✅ Report Type Extraction demo completed successfully!")
        
    except Exception as e:
        print(f"❌ Demo failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    demo_report_type_extraction()