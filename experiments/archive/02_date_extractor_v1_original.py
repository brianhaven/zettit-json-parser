#!/usr/bin/env python3

"""
Date Extraction System v1.0
Extracts forecast date ranges from market research titles with high accuracy.
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

class DateFormat(Enum):
    """Enumeration of date format types."""
    TERMINAL_COMMA = "terminal_comma"  # ", 2030"
    RANGE_FORMAT = "range_format"      # ", 2020-2027"
    BRACKET_FORMAT = "bracket_format"  # "[2023 Report]"
    EMBEDDED_FORMAT = "embedded_format" # "Outlook 2031"
    MULTIPLE_DATES = "multiple_dates"   # Multiple date patterns
    UNKNOWN = "unknown"

@dataclass
class DateExtractionResult:
    """Result of date extraction."""
    title: str
    extracted_date_range: Optional[str]
    start_year: Optional[int]
    end_year: Optional[int]
    format_type: DateFormat
    confidence: float
    matched_pattern: Optional[str]
    raw_match: Optional[str]
    notes: Optional[str] = None

@dataclass
class DateExtractionStats:
    """Statistics for date extraction results."""
    total_processed: int
    successful_extractions: int
    terminal_comma_count: int
    range_format_count: int
    bracket_format_count: int
    embedded_format_count: int
    multiple_dates_count: int
    failed_extractions: int
    success_rate: float

class DateExtractor:
    """
    Date Extraction System for market research titles.
    
    Extracts forecast date ranges with target 98-99% accuracy:
    - Terminal comma format: ", 2030"
    - Range format: ", 2020-2027" 
    - Bracket format: "[2023 Report]"
    - Embedded format: "Outlook 2031"
    """
    
    def __init__(self, pattern_library_manager):
        """
        Initialize the Date Extractor.
        
        Args:
            pattern_library_manager: PatternLibraryManager instance for pattern retrieval (REQUIRED)
        """
        if not pattern_library_manager:
            raise ValueError("PatternLibraryManager is required - DateExtractor must use database patterns only")
        
        self.pattern_library_manager = pattern_library_manager
        self.extraction_stats = {
            'total_processed': 0,
            'successful_extractions': 0,
            'terminal_comma': 0,
            'range_format': 0,
            'bracket_format': 0,
            'embedded_format': 0,
            'multiple_dates': 0,
            'failed_extractions': 0
        }
        
        # Initialize empty pattern lists (will be populated from database)
        self.terminal_comma_patterns = []
        self.range_format_patterns = []
        self.bracket_format_patterns = []
        self.embedded_format_patterns = []
        self.multiple_dates_pattern = r'\b\d{4}\b'  # Simple year detection pattern
        
        # Load patterns from database (required)
        self._load_library_patterns()
        
        # Current year for validation
        self.current_year = datetime.now().year
        self.min_valid_year = 2020  # Minimum realistic forecast year
        self.max_valid_year = 2040  # Maximum realistic forecast year
    
    def _load_library_patterns(self) -> None:
        """Load date patterns from MongoDB pattern library (REQUIRED)."""
        try:
            from pattern_library_manager_v1 import PatternType
            
            # Load date patterns from MongoDB by category
            date_patterns = self.pattern_library_manager.get_patterns(PatternType.DATE_PATTERN)
            
            if not date_patterns:
                raise RuntimeError("No date patterns found in MongoDB pattern_libraries collection. Please run initialize_date_patterns.py first.")
            
            # Organize patterns by format type
            terminal_comma_patterns = []
            range_format_patterns = []
            bracket_format_patterns = []
            embedded_format_patterns = []
            
            for pattern in date_patterns:
                if not pattern.get('active', True):
                    continue
                    
                format_type = pattern.get('format_type', '')
                pattern_regex = pattern.get('pattern', '')
                
                if not pattern_regex:
                    logger.warning(f"Pattern '{pattern.get('term', 'unknown')}' has no regex pattern")
                    continue
                
                if format_type == 'terminal_comma':
                    terminal_comma_patterns.append(pattern_regex)
                elif format_type == 'range_format':
                    range_format_patterns.append(pattern_regex)
                elif format_type == 'bracket_format':
                    bracket_format_patterns.append(pattern_regex)
                elif format_type == 'embedded_format':
                    embedded_format_patterns.append(pattern_regex)
                else:
                    logger.warning(f"Unknown format_type '{format_type}' for pattern '{pattern.get('term', 'unknown')}'")
            
            # Validate that we have patterns for each format type
            if not terminal_comma_patterns:
                raise RuntimeError("No terminal comma patterns found in database")
            if not range_format_patterns:
                raise RuntimeError("No range format patterns found in database")
            if not bracket_format_patterns:
                raise RuntimeError("No bracket format patterns found in database")
            if not embedded_format_patterns:
                raise RuntimeError("No embedded format patterns found in database")
            
            # Set patterns from database
            self.terminal_comma_patterns = terminal_comma_patterns
            self.range_format_patterns = range_format_patterns
            self.bracket_format_patterns = bracket_format_patterns
            self.embedded_format_patterns = embedded_format_patterns
            
            logger.info(f"Successfully loaded date patterns from MongoDB:")
            logger.info(f"  - Terminal comma: {len(terminal_comma_patterns)} patterns")
            logger.info(f"  - Range format: {len(range_format_patterns)} patterns")
            logger.info(f"  - Bracket format: {len(bracket_format_patterns)} patterns")
            logger.info(f"  - Embedded format: {len(embedded_format_patterns)} patterns")
            logger.info(f"  - Total: {len(date_patterns)} patterns loaded")
            
        except Exception as e:
            error_msg = f"CRITICAL: Failed to load date patterns from MongoDB: {e}"
            logger.error(error_msg)
            raise RuntimeError(error_msg + "\n\nDateExtractor requires database patterns. Please check:\n1. MongoDB connection\n2. pattern_libraries collection exists\n3. Run initialize_date_patterns.py to populate patterns")
    
    def _get_timestamps(self) -> tuple:
        """Generate PDT and UTC timestamps."""
        utc_now = datetime.now(timezone.utc)
        pdt_tz = pytz.timezone('America/Los_Angeles')
        pdt_now = utc_now.astimezone(pdt_tz)
        
        pdt_str = pdt_now.strftime('%Y-%m-%d %H:%M:%S %Z')
        utc_str = utc_now.strftime('%Y-%m-%d %H:%M:%S UTC')
        
        return pdt_str, utc_str, utc_now
    
    def _validate_year(self, year: int) -> bool:
        """Validate if year is within realistic range for market research."""
        return self.min_valid_year <= year <= self.max_valid_year
    
    def _normalize_date_range(self, start_year: Optional[int], end_year: Optional[int] = None) -> str:
        """
        Normalize date range to standardized format.
        
        Args:
            start_year: Starting year
            end_year: Ending year (optional for single year)
            
        Returns:
            Normalized date range string
        """
        if not start_year:
            return ""
        
        if end_year and end_year != start_year:
            return f"{start_year}-{end_year}"
        else:
            return str(start_year)
    
    def _calculate_confidence(self, format_type: DateFormat, start_year: Optional[int], 
                             end_year: Optional[int], raw_match: str) -> float:
        """
        Calculate confidence score for date extraction.
        
        Args:
            format_type: Type of date format detected
            start_year: Extracted start year
            end_year: Extracted end year
            raw_match: Raw matched text
            
        Returns:
            Confidence score between 0.0 and 1.0
        """
        confidence = 0.5  # Base confidence
        
        # Higher confidence for specific patterns
        if format_type == DateFormat.TERMINAL_COMMA:
            confidence = 0.95  # Very reliable pattern
        elif format_type == DateFormat.RANGE_FORMAT:
            confidence = 0.98  # Most reliable pattern
        elif format_type == DateFormat.BRACKET_FORMAT:
            confidence = 0.90  # Reliable pattern
        elif format_type == DateFormat.EMBEDDED_FORMAT:
            confidence = 0.85  # Good pattern but more ambiguous
        elif format_type == DateFormat.MULTIPLE_DATES:
            confidence = 0.60  # Lower confidence due to ambiguity
        else:
            confidence = 0.30  # Unknown pattern
        
        # Adjust based on year validation
        if start_year and not self._validate_year(start_year):
            confidence *= 0.5  # Reduce confidence for invalid years
        
        if end_year and not self._validate_year(end_year):
            confidence *= 0.5
        
        # Adjust based on range logic
        if start_year and end_year:
            if end_year < start_year:
                confidence *= 0.3  # Very low confidence for backwards ranges
            elif end_year == start_year:
                confidence *= 0.9  # Slightly reduce for redundant ranges
            elif (end_year - start_year) > 15:
                confidence *= 0.7  # Reduce for very long ranges
        
        return round(min(confidence, 1.0), 3)
    
    def extract_terminal_comma_format(self, title: str) -> DateExtractionResult:
        """
        Extract terminal comma format dates: ", 2030"
        
        Args:
            title: Title to extract from
            
        Returns:
            DateExtractionResult with extraction details
        """
        for pattern in self.terminal_comma_patterns:
            match = re.search(pattern, title, re.IGNORECASE)
            if match:
                year = int(match.group(1))
                
                if self._validate_year(year):
                    date_range = self._normalize_date_range(year)
                    confidence = self._calculate_confidence(
                        DateFormat.TERMINAL_COMMA, year, None, match.group(0)
                    )
                    
                    return DateExtractionResult(
                        title=title,
                        extracted_date_range=date_range,
                        start_year=year,
                        end_year=None,
                        format_type=DateFormat.TERMINAL_COMMA,
                        confidence=confidence,
                        matched_pattern=pattern,
                        raw_match=match.group(0),
                        notes="Terminal comma format"
                    )
        
        return DateExtractionResult(
            title=title,
            extracted_date_range=None,
            start_year=None,
            end_year=None,
            format_type=DateFormat.UNKNOWN,
            confidence=0.0,
            matched_pattern=None,
            raw_match=None,
            notes="No terminal comma format detected"
        )
    
    def extract_range_format(self, title: str) -> DateExtractionResult:
        """
        Extract range format dates: ", 2020-2027"
        
        Args:
            title: Title to extract from
            
        Returns:
            DateExtractionResult with extraction details
        """
        for pattern in self.range_format_patterns:
            match = re.search(pattern, title, re.IGNORECASE)
            if match:
                if len(match.groups()) == 2:
                    start_year = int(match.group(1))
                    end_year_str = match.group(2)
                    
                    # Handle abbreviated end year (e.g., "2020-27")
                    if len(end_year_str) == 2:
                        end_year = int(str(start_year)[:2] + end_year_str)
                    else:
                        end_year = int(end_year_str)
                    
                    if self._validate_year(start_year) and self._validate_year(end_year):
                        date_range = self._normalize_date_range(start_year, end_year)
                        confidence = self._calculate_confidence(
                            DateFormat.RANGE_FORMAT, start_year, end_year, match.group(0)
                        )
                        
                        return DateExtractionResult(
                            title=title,
                            extracted_date_range=date_range,
                            start_year=start_year,
                            end_year=end_year,
                            format_type=DateFormat.RANGE_FORMAT,
                            confidence=confidence,
                            matched_pattern=pattern,
                            raw_match=match.group(0),
                            notes="Range format"
                        )
        
        return DateExtractionResult(
            title=title,
            extracted_date_range=None,
            start_year=None,
            end_year=None,
            format_type=DateFormat.UNKNOWN,
            confidence=0.0,
            matched_pattern=None,
            raw_match=None,
            notes="No range format detected"
        )
    
    def extract_bracket_format(self, title: str) -> DateExtractionResult:
        """
        Extract bracket format dates: "[2023 Report]"
        
        Args:
            title: Title to extract from
            
        Returns:
            DateExtractionResult with extraction details
        """
        for pattern in self.bracket_format_patterns:
            match = re.search(pattern, title, re.IGNORECASE)
            if match:
                year = int(match.group(1))
                
                if self._validate_year(year):
                    date_range = self._normalize_date_range(year)
                    confidence = self._calculate_confidence(
                        DateFormat.BRACKET_FORMAT, year, None, match.group(0)
                    )
                    
                    return DateExtractionResult(
                        title=title,
                        extracted_date_range=date_range,
                        start_year=year,
                        end_year=None,
                        format_type=DateFormat.BRACKET_FORMAT,
                        confidence=confidence,
                        matched_pattern=pattern,
                        raw_match=match.group(0),
                        notes="Bracket format"
                    )
        
        return DateExtractionResult(
            title=title,
            extracted_date_range=None,
            start_year=None,
            end_year=None,
            format_type=DateFormat.UNKNOWN,
            confidence=0.0,
            matched_pattern=None,
            raw_match=None,
            notes="No bracket format detected"
        )
    
    def extract_embedded_format(self, title: str) -> DateExtractionResult:
        """
        Extract embedded format dates: "Outlook 2031"
        
        Args:
            title: Title to extract from
            
        Returns:
            DateExtractionResult with extraction details
        """
        for pattern in self.embedded_format_patterns:
            match = re.search(pattern, title, re.IGNORECASE)
            if match:
                year = int(match.group(1))
                
                if self._validate_year(year):
                    date_range = self._normalize_date_range(year)
                    confidence = self._calculate_confidence(
                        DateFormat.EMBEDDED_FORMAT, year, None, match.group(0)
                    )
                    
                    return DateExtractionResult(
                        title=title,
                        extracted_date_range=date_range,
                        start_year=year,
                        end_year=None,
                        format_type=DateFormat.EMBEDDED_FORMAT,
                        confidence=confidence,
                        matched_pattern=pattern,
                        raw_match=match.group(0),
                        notes="Embedded format"
                    )
        
        return DateExtractionResult(
            title=title,
            extracted_date_range=None,
            start_year=None,
            end_year=None,
            format_type=DateFormat.UNKNOWN,
            confidence=0.0,
            matched_pattern=None,
            raw_match=None,
            notes="No embedded format detected"
        )
    
    def extract(self, title: str) -> DateExtractionResult:
        """
        Extract date information from title using all available patterns.
        
        Args:
            title: Title to extract dates from
            
        Returns:
            DateExtractionResult with best extraction found
        """
        if not title or not title.strip():
            return DateExtractionResult(
                title=title,
                extracted_date_range=None,
                start_year=None,
                end_year=None,
                format_type=DateFormat.UNKNOWN,
                confidence=0.0,
                matched_pattern=None,
                raw_match=None,
                notes="Empty or whitespace-only title"
            )
        
        # Track processing
        self.extraction_stats['total_processed'] += 1
        
        # Try extraction methods in order of reliability
        extraction_methods = [
            self.extract_range_format,      # Highest reliability (98%)
            self.extract_terminal_comma_format,  # Very high reliability (95%)
            self.extract_bracket_format,    # High reliability (90%)
            self.extract_embedded_format,   # Good reliability (85%)
        ]
        
        best_result = None
        best_confidence = 0.0
        
        for method in extraction_methods:
            result = method(title)
            
            if result.extracted_date_range and result.confidence > best_confidence:
                best_result = result
                best_confidence = result.confidence
        
        # Check for multiple dates (lower priority)
        if not best_result or best_confidence < 0.8:
            years = re.findall(self.multiple_dates_pattern, title)
            valid_years = [int(year) for year in years if self._validate_year(int(year))]
            
            if len(valid_years) > 1:
                # Multiple dates detected - use latest year as forecast
                latest_year = max(valid_years)
                date_range = self._normalize_date_range(latest_year)
                confidence = self._calculate_confidence(
                    DateFormat.MULTIPLE_DATES, latest_year, None, f"Multiple years: {valid_years}"
                )
                
                multiple_result = DateExtractionResult(
                    title=title,
                    extracted_date_range=date_range,
                    start_year=latest_year,
                    end_year=None,
                    format_type=DateFormat.MULTIPLE_DATES,
                    confidence=confidence,
                    matched_pattern=self.multiple_dates_pattern,
                    raw_match=f"Years found: {valid_years}",
                    notes=f"Multiple dates detected, using latest: {latest_year}"
                )
                
                if not best_result or confidence > best_confidence:
                    best_result = multiple_result
        
        # Use best result or create failure result
        if best_result and best_result.extracted_date_range:
            # Update statistics
            self.extraction_stats['successful_extractions'] += 1
            
            if best_result.format_type == DateFormat.TERMINAL_COMMA:
                self.extraction_stats['terminal_comma'] += 1
            elif best_result.format_type == DateFormat.RANGE_FORMAT:
                self.extraction_stats['range_format'] += 1
            elif best_result.format_type == DateFormat.BRACKET_FORMAT:
                self.extraction_stats['bracket_format'] += 1
            elif best_result.format_type == DateFormat.EMBEDDED_FORMAT:
                self.extraction_stats['embedded_format'] += 1
            elif best_result.format_type == DateFormat.MULTIPLE_DATES:
                self.extraction_stats['multiple_dates'] += 1
            
            logger.debug(f"Date extracted from '{title}': {best_result.extracted_date_range}")
            return best_result
        
        else:
            # No extraction successful
            self.extraction_stats['failed_extractions'] += 1
            
            return DateExtractionResult(
                title=title,
                extracted_date_range=None,
                start_year=None,
                end_year=None,
                format_type=DateFormat.UNKNOWN,
                confidence=0.0,
                matched_pattern=None,
                raw_match=None,
                notes="No date patterns detected"
            )
    
    def extract_batch(self, titles: List[str]) -> List[DateExtractionResult]:
        """
        Extract dates from a batch of titles.
        
        Args:
            titles: List of titles to process
            
        Returns:
            List of DateExtractionResult objects
        """
        results = []
        
        logger.info(f"Starting batch date extraction of {len(titles)} titles")
        
        for i, title in enumerate(titles):
            if i > 0 and i % 1000 == 0:
                logger.info(f"Processed {i}/{len(titles)} titles...")
            
            result = self.extract(title)
            results.append(result)
        
        logger.info(f"Completed batch date extraction of {len(titles)} titles")
        return results
    
    def get_extraction_statistics(self) -> DateExtractionStats:
        """
        Get current extraction statistics.
        
        Returns:
            DateExtractionStats object with current statistics
        """
        total = self.extraction_stats['total_processed']
        
        if total == 0:
            return DateExtractionStats(
                total_processed=0,
                successful_extractions=0,
                terminal_comma_count=0,
                range_format_count=0,
                bracket_format_count=0,
                embedded_format_count=0,
                multiple_dates_count=0,
                failed_extractions=0,
                success_rate=0.0
            )
        
        return DateExtractionStats(
            total_processed=total,
            successful_extractions=self.extraction_stats['successful_extractions'],
            terminal_comma_count=self.extraction_stats['terminal_comma'],
            range_format_count=self.extraction_stats['range_format'],
            bracket_format_count=self.extraction_stats['bracket_format'],
            embedded_format_count=self.extraction_stats['embedded_format'],
            multiple_dates_count=self.extraction_stats['multiple_dates'],
            failed_extractions=self.extraction_stats['failed_extractions'],
            success_rate=round((self.extraction_stats['successful_extractions'] / total) * 100, 2)
        )
    
    def reset_statistics(self) -> None:
        """Reset extraction statistics."""
        self.extraction_stats = {
            'total_processed': 0,
            'successful_extractions': 0,
            'terminal_comma': 0,
            'range_format': 0,
            'bracket_format': 0,
            'embedded_format': 0,
            'multiple_dates': 0,
            'failed_extractions': 0
        }
        logger.info("Date extraction statistics reset")
    
    def export_extraction_report(self, filename: Optional[str] = None) -> str:
        """
        Export extraction statistics to a formatted report.
        
        Args:
            filename: Optional filename to save report to
            
        Returns:
            Report content as string
        """
        pdt_time, utc_time, _ = self._get_timestamps()
        stats = self.get_extraction_statistics()
        
        report = f"""Date Extraction Report
{'='*50}
Analysis Date (PDT): {pdt_time}
Analysis Date (UTC): {utc_time}
{'='*50}

Extraction Summary:
  Total Titles Processed: {stats.total_processed:,}
  Successful Extractions: {stats.successful_extractions:,} ({stats.success_rate:.2f}%)
  Failed Extractions:     {stats.failed_extractions:,} ({(stats.failed_extractions/stats.total_processed)*100:.2f}%)

Format Distribution:
  Terminal Comma Format:  {stats.terminal_comma_count:6,} ({(stats.terminal_comma_count/stats.total_processed)*100:6.2f}%)
  Range Format:           {stats.range_format_count:6,} ({(stats.range_format_count/stats.total_processed)*100:6.2f}%)
  Bracket Format:         {stats.bracket_format_count:6,} ({(stats.bracket_format_count/stats.total_processed)*100:6.2f}%)
  Embedded Format:        {stats.embedded_format_count:6,} ({(stats.embedded_format_count/stats.total_processed)*100:6.2f}%)
  Multiple Dates:         {stats.multiple_dates_count:6,} ({(stats.multiple_dates_count/stats.total_processed)*100:6.2f}%)

Performance Metrics:
  Target Success Rate:    98-99%
  Actual Success Rate:    {stats.success_rate:.2f}%
  Performance Status:     {'✅ MEETS TARGET' if stats.success_rate >= 98 else '⚠️  BELOW TARGET' if stats.success_rate >= 95 else '❌ NEEDS IMPROVEMENT'}

Pattern Effectiveness:
  Most Common Format:     {self._get_most_common_format(stats)}
  Least Common Format:    {self._get_least_common_format(stats)}
"""
        
        if filename:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(report)
            logger.info(f"Date extraction report exported to {filename}")
        
        return report
    
    def _get_most_common_format(self, stats: DateExtractionStats) -> str:
        """Get the most common date format from statistics."""
        formats = {
            'Terminal Comma': stats.terminal_comma_count,
            'Range Format': stats.range_format_count,
            'Bracket Format': stats.bracket_format_count,
            'Embedded Format': stats.embedded_format_count,
            'Multiple Dates': stats.multiple_dates_count
        }
        
        if not any(formats.values()):
            return "None"
        
        return max(formats, key=formats.get)
    
    def _get_least_common_format(self, stats: DateExtractionStats) -> str:
        """Get the least common date format from statistics."""
        formats = {
            'Terminal Comma': stats.terminal_comma_count,
            'Range Format': stats.range_format_count,
            'Bracket Format': stats.bracket_format_count,
            'Embedded Format': stats.embedded_format_count,
            'Multiple Dates': stats.multiple_dates_count
        }
        
        # Filter out zeros
        non_zero_formats = {k: v for k, v in formats.items() if v > 0}
        
        if not non_zero_formats:
            return "None"
        
        return min(non_zero_formats, key=non_zero_formats.get)


def demo_date_extraction():
    """Demonstrate Date Extractor functionality."""
    
    print("Date Extraction System Demo")
    print("=" * 50)
    
    # Sample titles for testing different date formats
    sample_titles = [
        # Terminal comma format
        "Global Artificial Intelligence Market Size & Share Report, 2030",
        "APAC Personal Protective Equipment Market Analysis, 2025",
        "Automotive Battery Market Report, 2031.",
        
        # Range format
        "Blockchain Technology Market Trends, 2020-2027",
        "Healthcare Market Research, 2023–2030",
        "Software Market Intelligence, 2024 to 2029",
        "Technology Market Study, 2023-27",
        
        # Bracket format
        "Renewable Energy Market Analysis [2024 Report]",
        "Financial Services Study [2023]",
        "Industry Overview (2025 Update)",
        
        # Embedded format
        "Cybersecurity Market Outlook 2031",
        "AI Technology Forecast 2030",
        "Digital Health Projections 2028",
        "Market Analysis Through 2032",
        "Industry Growth by 2029",
        "2030 Technology Outlook",
        "Market Research Report 2030",
        
        # Multiple dates / Edge cases
        "Market Evolution from 2020 to 2030 Analysis",
        "Industry Report 2023 with 2025 Projections",
        "Annual Financial Report 2023",  # No forecast date
        "Technology Innovation Trends",  # No dates
    ]
    
    try:
        # Initialize extractor with pattern library manager (REQUIRED)
        from pattern_library_manager_v1 import PatternLibraryManager
        pattern_manager = PatternLibraryManager()
        extractor = DateExtractor(pattern_manager)
        print("✅ Using MongoDB pattern library for date extraction")
        
        print(f"\n1. Individual Extraction Examples:")
        print("-" * 40)
        
        for title in sample_titles[:8]:  # Show first 8 examples
            result = extractor.extract(title)
            print(f"Title: {title[:70]}...")
            print(f"  Date Range: {result.extracted_date_range}")
            print(f"  Format: {result.format_type.value}")
            print(f"  Confidence: {result.confidence:.3f}")
            print(f"  Raw Match: {result.raw_match}")
            print()
        
        # Batch extraction
        print("2. Batch Extraction Results:")
        print("-" * 40)
        
        batch_results = extractor.extract_batch(sample_titles)
        
        # Get statistics
        stats = extractor.get_extraction_statistics()
        
        print(f"Total Processed: {stats.total_processed}")
        print(f"Successful Extractions: {stats.successful_extractions} ({stats.success_rate:.1f}%)")
        print(f"Terminal Comma: {stats.terminal_comma_count}")
        print(f"Range Format: {stats.range_format_count}")
        print(f"Bracket Format: {stats.bracket_format_count}")
        print(f"Embedded Format: {stats.embedded_format_count}")
        print(f"Failed: {stats.failed_extractions}")
        
        # Export report
        print("\n3. Detailed Extraction Report:")
        print("-" * 40)
        
        report = extractor.export_extraction_report()
        print(report)
        
        print("✅ Date Extraction demo completed successfully!")
        
        # Close pattern manager if used
        if 'pattern_manager' in locals():
            pattern_manager.close_connection()
        
    except Exception as e:
        print(f"❌ Demo failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    demo_date_extraction()