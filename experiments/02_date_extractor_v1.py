#!/usr/bin/env python3

"""
Enhanced Date Extractor with Bracket Format Preservation
Fixes GitHub Issue #8: Preserves report type words when removing date patterns.

Key Enhancement: For bracket patterns like [2023 Report], extracts "2023" but preserves "Report".
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
import json

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

# Dynamic import of organized output directory manager
try:
    _spec = importlib.util.spec_from_file_location("output_dir_manager", os.path.join(os.path.dirname(__file__), "00c_output_directory_manager_v1.py"))
    _output_module = importlib.util.module_from_spec(_spec)
    _spec.loader.exec_module(_output_module)
    create_organized_output_directory = _output_module.create_organized_output_directory
    create_output_file_header = _output_module.create_output_file_header
except Exception as e:
    logger.warning(f"Could not import output directory manager: {e}. Output functionality limited.")

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
    """Enhanced result of date extraction with bracket format preservation."""
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
    # NEW: Enhanced bracket format support
    preserved_words: List[str]  # Words to preserve when removing date pattern
    cleaned_title: str  # Title with date removed but important words preserved
    notes: Optional[str] = None

class EnhancedDateExtractor:
    """
    Enhanced Date Extraction System with bracket format preservation.
    
    Key enhancement for GitHub Issue #8:
    - For bracket patterns like [2023 Report], extracts "2023" but preserves "Report"
    - Provides cleaned_title that preserves important words for downstream processing
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
        
        # Bracket preservation patterns - words that should be preserved when removing brackets
        self.preservation_words = {
            'report_types': ['report', 'analysis', 'study', 'update', 'edition', 'survey', 'review', 'outlook'],
            'market_terms': ['market', 'industry', 'segment', 'sector']
        }
        
        # Statistics tracking
        self.extraction_stats = {
            'total_processed': 0,
            'successful_extractions': 0,
            'no_dates_present': 0,
            'dates_missed': 0,
            'has_numeric_but_no_date': 0,
            'bracket_preservations': 0  # NEW: Track bracket word preservations
        }
        
        logger.info(f"Enhanced Date Extractor initialized with {len(self.date_patterns)} patterns")
        logger.info(f"Bracket preservation enabled for {sum(len(words) for words in self.preservation_words.values())} word types")
    
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
    
    def _extract_preservation_words(self, raw_match: str, format_type: str) -> List[str]:
        """
        Extract words from the raw match that should be preserved.
        
        For bracket/parentheses patterns, identify important words that should be kept
        when removing the date pattern.
        
        Args:
            raw_match: The full matched text (e.g., "[2023 Report]")
            format_type: The pattern format type
            
        Returns:
            List of words to preserve
        """
        if format_type != 'bracket_format':
            return []
        
        # Extract words from bracket/parentheses content
        # Remove brackets/parentheses and years, keep meaningful words
        content = re.sub(r'[\[\]()]', '', raw_match)  # Remove brackets/parentheses
        content = re.sub(r'\b\d{4}\b', '', content)   # Remove years
        content = re.sub(r'\s+', ' ', content).strip()  # Clean spaces
        
        preserved = []
        if content:
            words = content.lower().split()
            for word in words:
                # Check if word should be preserved
                for word_category, preservation_list in self.preservation_words.items():
                    if word in preservation_list:
                        preserved.append(word.title())  # Preserve with proper capitalization
                        break
        
        return preserved
    
    def _create_cleaned_title(self, title: str, raw_match: str, preserved_words: List[str]) -> str:
        """
        Create a cleaned title with date pattern removed but important words preserved.
        
        Args:
            title: Original title
            raw_match: The matched date pattern text
            preserved_words: Words to preserve from the pattern
            
        Returns:
            Cleaned title with preserved words
        """
        if not raw_match:
            return title
        
        # Remove the raw match
        cleaned = title.replace(raw_match, '').strip()
        
        # Add preserved words back
        if preserved_words:
            preserved_text = ' '.join(preserved_words)
            if cleaned:
                cleaned = f"{cleaned} {preserved_text}"
            else:
                cleaned = preserved_text
        
        # Clean up spacing and punctuation
        cleaned = re.sub(r'\s+', ' ', cleaned).strip()
        cleaned = re.sub(r'[,\.]+$', '', cleaned)  # Remove trailing punctuation
        
        return cleaned
    
    def extract(self, title: str) -> EnhancedDateExtractionResult:
        """
        Extract date information from title with enhanced bracket format preservation.
        
        Args:
            title: Input title text
            
        Returns:
            EnhancedDateExtractionResult with detailed analysis and bracket preservation
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
                preserved_words=[],
                cleaned_title=title,
                notes="No numeric content detected - no dates expected"
            )
        
        # Step 3: Try to extract dates using existing patterns
        extraction_result = self._try_extract_with_patterns(title)
        
        # Step 4: Handle bracket format preservation
        preserved_words = []
        if extraction_result['raw_match'] and extraction_result['format_type'] == DateFormat.BRACKET_FORMAT:
            preserved_words = self._extract_preservation_words(
                extraction_result['raw_match'], 
                'bracket_format'
            )
            if preserved_words:
                self.extraction_stats['bracket_preservations'] += 1
        
        # Step 5: Create cleaned title with preservation
        cleaned_title = self._create_cleaned_title(
            title,
            extraction_result['raw_match'],
            preserved_words
        )
        
        # Step 6: Categorize the result
        if extraction_result['extracted_date_range']:
            self.extraction_stats['successful_extractions'] += 1
            categorization = "success"
            preservation_note = f" (preserved: {', '.join(preserved_words)})" if preserved_words else ""
            notes = f"Successfully extracted date using {extraction_result['format_type']} pattern{preservation_note}"
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
            preserved_words=preserved_words,
            cleaned_title=cleaned_title,
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
                            
                            # Year range validation (2005-2049) - lenient single-number approach
                            # At least one number must be in the valid year range
                            valid_range = False
                            if start_year and 2005 <= start_year <= 2049:
                                valid_range = True
                            if end_year and 2005 <= end_year <= 2049:
                                valid_range = True
                            
                            if not valid_range:
                                # Neither number is in valid year range - skip this match
                                continue
                            
                            extracted_date = f"{start_year}-{end_year}"
                        elif len(groups) >= 1 and groups[0]:
                            year = int(groups[0])
                            
                            # Single year validation (2005-2049)
                            if not (2005 <= year <= 2049):
                                # Year is not in valid range - skip this match
                                continue
                            
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
        """Get extraction statistics including bracket preservations."""
        return self.extraction_stats.copy()
    
    def close_connection(self):
        """Close database connection."""
        if self.pattern_library_manager:
            self.pattern_library_manager.close_connection()

def demo_extraction_with_output_save():
    """Demonstration function that saves extraction results to organized output directory.
    
    This is a placeholder function to provide output functionality consistent with other main scripts.
    Script 02 primarily serves as a pipeline component and doesn't normally generate standalone output files.
    """
    from dotenv import load_dotenv
    import pytz
    from datetime import datetime
    
    load_dotenv()
    
    try:
        # Initialize components
        pattern_manager = PatternLibraryManager()
        extractor = EnhancedDateExtractor(pattern_manager)
        
        # Create organized output directory
        output_dir = create_organized_output_directory("script02_date_extractor_demo")
        
        # Test cases including the failing GitHub Issue #8 case
        test_titles = [
            "Automatic Weapons Market Size And Share [2023 Report]",  # GitHub Issue #8
            "AI Technology Market Size Report, 2030",  # Clear date
            "Healthcare Market 2025-2030",  # Range
            "Some Market Analysis [2024 Study]",  # Bracket with Study
            "Technology Overview",  # No numbers at all
            "Component Analysis Part 3",  # Numbers but not dates
            "Market Research [2023 Edition]",  # Edition variant
            "Industry Survey (2024 Update)",  # Parentheses variant
        ]
        
        # Process test cases
        results = []
        for title in test_titles:
            result = extractor.extract(title)
            results.append({
                'original_title': title,
                'categorization': result.categorization,
                'extracted_date_range': result.extracted_date_range,
                'format_type': result.format_type.value if result.format_type else None,
                'raw_match': result.raw_match,
                'preserved_words': result.preserved_words,
                'cleaned_title': result.cleaned_title,
                'notes': result.notes,
                'confidence': result.confidence
            })
        
        # Save results to organized output files
        
        # 1. Summary report
        report_file = os.path.join(output_dir, "date_extraction_demo_report.txt")
        with open(report_file, 'w', encoding='utf-8') as f:
            header = create_output_file_header("script02_date_extractor_demo", "Enhanced Date Extractor demonstration results with bracket preservation")
            f.write(header + "\n\n")
            
            f.write("🔧 Enhanced Date Extractor with Bracket Preservation Test Results:\n")
            f.write("=" * 80 + "\n\n")
            
            for result in results:
                f.write(f"Title: {result['original_title']}\n")
                f.write(f"  Result: {result['categorization']}\n")
                f.write(f"  Extracted: {result['extracted_date_range']}\n")
                f.write(f"  Format: {result['format_type']}\n")
                f.write(f"  Raw Match: {result['raw_match']}\n")
                f.write(f"  Preserved Words: {result['preserved_words']}\n")
                f.write(f"  Cleaned Title: {result['cleaned_title']}\n")
                f.write(f"  Notes: {result['notes']}\n")
                f.write(f"  Confidence: {result['confidence']}\n")
                f.write("\n")
            
            # Add statistics
            stats = extractor.get_stats()
            f.write("Final Statistics:\n")
            for key, value in stats.items():
                f.write(f"  {key.replace('_', ' ').title()}: {value}\n")
        
        # 2. JSON results for programmatic access
        json_file = os.path.join(output_dir, "date_extraction_results.json")
        with open(json_file, 'w', encoding='utf-8') as f:
            output_data = {
                'metadata': {
                    'script': 'script02_date_extractor_demo',
                    'description': 'Enhanced Date Extractor demonstration results',
                    'test_cases': len(results),
                    'extraction_stats': extractor.get_stats(),
                    'output_structure': 'organized_YYYY_MM_DD'
                },
                'results': results
            }
            json.dump(output_data, f, indent=2, ensure_ascii=False)
        
        print(f"✓ Date extraction demo completed successfully")
        print(f"📁 Results saved to: {output_dir}")
        print(f"  - Summary report: {report_file}")
        print(f"  - JSON results: {json_file}")
        
        extractor.close_connection()
        
    except Exception as e:
        logger.error(f"Demo extraction with output save failed: {e}")
        raise

if __name__ == "__main__":
    # Test the enhanced extractor with bracket format preservation
    # For output file generation, use: demo_extraction_with_output_save()
    from dotenv import load_dotenv
    load_dotenv()
    
    pattern_manager = PatternLibraryManager()
    extractor = EnhancedDateExtractor(pattern_manager)
    
    # Test cases including the failing GitHub Issue #8 case
    test_titles = [
        "Automatic Weapons Market Size And Share [2023 Report]",  # GitHub Issue #8
        "AI Technology Market Size Report, 2030",  # Clear date
        "Healthcare Market 2025-2030",  # Range
        "Some Market Analysis [2024 Study]",  # Bracket with Study
        "Technology Overview",  # No numbers at all
        "Component Analysis Part 3",  # Numbers but not dates
        "Market Research [2023 Edition]",  # Edition variant
        "Industry Survey (2024 Update)",  # Parentheses variant
    ]
    
    print("🔧 Enhanced Date Extractor with Bracket Preservation Test Results:")
    print("=" * 80)
    
    for title in test_titles:
        result = extractor.extract(title)
        print(f"Title: {title}")
        print(f"  Result: {result.categorization}")
        print(f"  Extracted: {result.extracted_date_range}")
        print(f"  Format: {result.format_type}")
        print(f"  Raw Match: {result.raw_match}")
        print(f"  Preserved Words: {result.preserved_words}")
        print(f"  Cleaned Title: {result.cleaned_title}")
        print(f"  Notes: {result.notes}")
        print()
    
    print("Final Statistics:")
    stats = extractor.get_stats()
    for key, value in stats.items():
        print(f"  {key.replace('_', ' ').title()}: {value}")
    
    extractor.close_connection()