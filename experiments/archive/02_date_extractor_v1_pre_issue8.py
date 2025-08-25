#!/usr/bin/env python3

"""
Enhanced Date Extractor with Numeric Pre-filtering
Distinguishes between titles with no dates vs titles with unextracted dates.
"""

import re
import logging
from typing import Optional, Dict, List, Tuple
from dataclasses import dataclass
from enum import Enum
from datetime import datetime
import os
import sys
import importlib.util

# Dynamic import for pattern library manager
try:
    pattern_manager_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '00b_pattern_library_manager_v1.py')
    spec = importlib.util.spec_from_file_location("pattern_library_manager_v1", pattern_manager_path)
    pattern_module = importlib.util.module_from_spec(spec)
    sys.modules["pattern_library_manager_v1"] = pattern_module
    spec.loader.exec_module(pattern_module)
    PatternLibraryManager = pattern_module.PatternLibraryManager
    PatternType = pattern_module.PatternType
except Exception as e:
    raise ImportError(f"Could not import PatternLibraryManager: {e}") from e

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DateFormat(Enum):
    """Date format types for classification."""
    TERMINAL_COMMA = "terminal_comma"       # ", 2030"
    RANGE_FORMAT = "range_format"           # ", 2020-2027"
    BRACKET_FORMAT = "bracket_format"       # "[2023 Report]"
    EMBEDDED_FORMAT = "embedded_format"     # "Outlook 2031"
    MULTIPLE_DATES = "multiple_dates"       # Multiple date patterns
    NO_NUMERIC_CONTENT = "no_numeric_content"  # No numbers in title
    UNKNOWN = "unknown"

@dataclass
class EnhancedDateExtractionResult:
    """Enhanced result of date extraction with numeric pre-filtering."""
    title: str
    extracted_date_range: Optional[str]
    start_year: Optional[int]
    end_year: Optional[int]
    format_type: DateFormat
    confidence: float
    matched_pattern: Optional[str]
    raw_match: Optional[str]
    has_numeric_content: bool
    numeric_values_found: List[str]
    categorization: str  # "success", "no_dates_present", "dates_missed"
    notes: Optional[str] = None

class EnhancedDateExtractor:
    """
    Enhanced Date Extraction System with numeric pre-filtering.
    
    Distinguishes between:
    - Titles with no dates (not failures)
    - Titles with dates that we failed to extract (actual failures)
    """
    
    def __init__(self, pattern_library_manager):
        """
        Initialize the Enhanced Date Extractor.
        
        Args:
            pattern_library_manager: PatternLibraryManager instance for pattern retrieval (REQUIRED)
        """
        if not pattern_library_manager:
            raise ValueError("PatternLibraryManager is required")
        
        self.pattern_library_manager = pattern_library_manager
        self.date_patterns = self._load_date_patterns()
        
        # Numeric content patterns
        self.numeric_patterns = {
            'four_digit_years': re.compile(r'\b(19|20)\d{2}\b'),  # 1900-2099 range
            'any_numbers': re.compile(r'\d+'),  # Any numeric content
            'potential_years': re.compile(r'\b(202[0-9]|203[0-9]|204[0-9]|195[0-9]|196[0-9]|197[0-9]|198[0-9]|199[0-9])\b')  # Extended year range
        }
        
        # Statistics tracking
        self.extraction_stats = {
            'total_processed': 0,
            'successful_extractions': 0,
            'no_dates_present': 0,
            'dates_missed': 0,
            'has_numeric_but_no_date': 0
        }
        
        logger.info(f"Enhanced Date Extractor initialized with {len(self.date_patterns)} patterns")
    
    def _load_date_patterns(self) -> Dict[str, List[Dict]]:
        """Load date patterns from MongoDB, organized by format type."""
        patterns = self.pattern_library_manager.get_patterns(PatternType.DATE_PATTERN)
        organized_patterns = {
            'terminal_comma': [],
            'range_format': [],
            'bracket_format': [],
            'embedded_format': []
        }
        
        for pattern in patterns:
            format_type = pattern.get('format_type', 'embedded_format')
            if format_type in organized_patterns:
                organized_patterns[format_type].append(pattern)
        
        total_patterns = sum(len(patterns) for patterns in organized_patterns.values())
        logger.info(f"Successfully loaded date patterns from MongoDB:")
        for format_type, pattern_list in organized_patterns.items():
            logger.info(f"  - {format_type.replace('_', ' ').title()}: {len(pattern_list)} patterns")
        logger.info(f"  - Total: {total_patterns} patterns loaded")
        
        return organized_patterns
    
    def _analyze_numeric_content(self, title: str) -> Tuple[bool, List[str], Dict[str, bool]]:
        """
        Analyze numeric content in title to determine if dates might be present.
        
        Returns:
            (has_numeric_content, numeric_values_found, analysis_details)
        """
        analysis = {
            'has_four_digit_years': False,
            'has_potential_years': False,
            'has_any_numbers': False
        }
        
        numeric_values = []
        
        # Check for four-digit years (most reliable indicator)
        four_digit_matches = self.numeric_patterns['four_digit_years'].findall(title)
        if four_digit_matches:
            analysis['has_four_digit_years'] = True
            numeric_values.extend([f"{match[0]}{match[1:]}" for match in four_digit_matches])
        
        # Check for potential years (extended range)
        potential_year_matches = self.numeric_patterns['potential_years'].findall(title)
        if potential_year_matches:
            analysis['has_potential_years'] = True
            numeric_values.extend(potential_year_matches)
        
        # Check for any numeric content
        any_number_matches = self.numeric_patterns['any_numbers'].findall(title)
        if any_number_matches:
            analysis['has_any_numbers'] = True
            numeric_values.extend(any_number_matches)
        
        # Remove duplicates while preserving order
        numeric_values = list(dict.fromkeys(numeric_values))
        
        # Determine if we think dates might be present
        has_numeric_content = (
            analysis['has_four_digit_years'] or 
            analysis['has_potential_years'] or
            (analysis['has_any_numbers'] and len(numeric_values) > 0)
        )
        
        return has_numeric_content, numeric_values, analysis
    
    def extract(self, title: str) -> EnhancedDateExtractionResult:
        """
        Extract date information from title with enhanced categorization.
        
        Args:
            title: Input title text
            
        Returns:
            EnhancedDateExtractionResult with detailed analysis
        """
        self.extraction_stats['total_processed'] += 1
        
        # Step 1: Analyze numeric content
        has_numeric_content, numeric_values, analysis = self._analyze_numeric_content(title)
        
        # Step 2: If no numeric content, categorize as "no dates present"
        if not has_numeric_content:
            self.extraction_stats['no_dates_present'] += 1
            return EnhancedDateExtractionResult(
                title=title,
                extracted_date_range=None,
                start_year=None,
                end_year=None,
                format_type=DateFormat.NO_NUMERIC_CONTENT,
                confidence=1.0,  # High confidence that no dates are present
                matched_pattern=None,
                raw_match=None,
                has_numeric_content=False,
                numeric_values_found=numeric_values,
                categorization="no_dates_present",
                notes="No numeric content detected - no dates expected"
            )
        
        # Step 3: Try to extract dates using existing patterns
        extraction_result = self._try_extract_with_patterns(title)
        
        # Step 4: Categorize the result
        if extraction_result['extracted_date_range']:
            self.extraction_stats['successful_extractions'] += 1
            categorization = "success"
            notes = f"Successfully extracted date using {extraction_result['format_type']} pattern"
        else:
            # Has numeric content but no date extracted - potential pattern gap
            if analysis['has_four_digit_years'] or analysis['has_potential_years']:
                self.extraction_stats['dates_missed'] += 1
                categorization = "dates_missed"
                notes = f"Contains year-like numbers {numeric_values} but no patterns matched - potential pattern gap"
            else:
                self.extraction_stats['has_numeric_but_no_date'] += 1
                categorization = "no_dates_present"
                notes = f"Contains numbers {numeric_values} but likely not dates"
        
        return EnhancedDateExtractionResult(
            title=title,
            extracted_date_range=extraction_result['extracted_date_range'],
            start_year=extraction_result['start_year'],
            end_year=extraction_result['end_year'],
            format_type=extraction_result['format_type'],
            confidence=extraction_result['confidence'],
            matched_pattern=extraction_result['matched_pattern'],
            raw_match=extraction_result['raw_match'],
            has_numeric_content=has_numeric_content,
            numeric_values_found=numeric_values,
            categorization=categorization,
            notes=notes
        )
    
    def _try_extract_with_patterns(self, title: str) -> Dict:
        """Try to extract dates using loaded patterns."""
        # This mirrors the original date extractor logic
        # Try each pattern type in priority order
        
        for format_type, patterns in self.date_patterns.items():
            for pattern_data in patterns:
                try:
                    pattern = re.compile(pattern_data['pattern'])
                    match = pattern.search(title)
                    
                    if match:
                        raw_match = match.group(0)
                        groups = match.groups()
                        
                        # Extract date information based on format type
                        if format_type == 'range_format' and len(groups) >= 2:
                            start_year = int(groups[0]) if groups[0] else None
                            end_year = int(groups[1]) if groups[1] else None
                            extracted_date = f"{start_year}-{end_year}"
                        elif len(groups) >= 1 and groups[0]:
                            year = int(groups[0])
                            start_year = end_year = year
                            extracted_date = str(year)
                        else:
                            continue
                        
                        return {
                            'extracted_date_range': extracted_date,
                            'start_year': start_year,
                            'end_year': end_year,
                            'format_type': DateFormat(format_type),
                            'confidence': pattern_data.get('confidence_weight', 0.8),
                            'matched_pattern': pattern_data['pattern'],
                            'raw_match': raw_match
                        }
                        
                except (ValueError, re.error) as e:
                    logger.debug(f"Pattern error for '{pattern_data.get('term', 'unknown')}': {e}")
                    continue
        
        # No patterns matched
        return {
            'extracted_date_range': None,
            'start_year': None,
            'end_year': None,
            'format_type': DateFormat.UNKNOWN,
            'confidence': 0.0,
            'matched_pattern': None,
            'raw_match': None
        }
    
    def get_stats(self) -> Dict[str, int]:
        """Get extraction statistics."""
        return self.extraction_stats.copy()
    
    def close_connection(self):
        """Close database connection."""
        if self.pattern_library_manager:
            self.pattern_library_manager.close_connection()

if __name__ == "__main__":
    # Test the enhanced extractor
    from dotenv import load_dotenv
    load_dotenv()
    
    pattern_manager = PatternLibraryManager()
    extractor = EnhancedDateExtractor(pattern_manager)
    
    # Test cases
    test_titles = [
        "Floor Paints Market",  # No dates
        "Helium-3 Market",  # No dates
        "AI Technology Market Size Report, 2030",  # Clear date
        "Healthcare Market 2025-2030",  # Range
        "Some Market Report [2024]",  # Bracket
        "Technology Overview",  # No numbers at all
        "Component Analysis Part 3",  # Numbers but not dates
    ]
    
    print("Enhanced Date Extractor Test Results:")
    print("=" * 60)
    
    for title in test_titles:
        result = extractor.extract(title)
        print(f"Title: {title}")
        print(f"  Result: {result.categorization}")
        print(f"  Extracted: {result.extracted_date_range}")
        print(f"  Numeric values: {result.numeric_values_found}")
        print(f"  Notes: {result.notes}")
        print()
    
    print("Final Statistics:")
    stats = extractor.get_stats()
    for key, value in stats.items():
        print(f"  {key.replace('_', ' ').title()}: {value}")
    
    extractor.close_connection()