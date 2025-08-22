#!/usr/bin/env python3

"""
Initialize Date Patterns in MongoDB
Populates the pattern_libraries collection with date extraction patterns.
"""

import os
import sys
import logging
from dotenv import load_dotenv
import importlib.util

# Dynamic import for pattern library manager (filename starts with numbers)
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
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def initialize_date_patterns():
    """Initialize date extraction patterns in MongoDB pattern_libraries collection."""
    
    # Load environment variables
    load_dotenv()
    
    try:
        # Initialize pattern manager
        pattern_manager = PatternLibraryManager()
        
        # Define date extraction patterns by format type
        date_patterns = [
            # Terminal comma format patterns: ", 2030"
            {
                "type": "date_pattern",
                "term": "Terminal Comma Year",
                "pattern": r',\s*(\d{4})\s*$',
                "format_type": "terminal_comma",
                "description": "Year at end with comma: ', 2030'",
                "priority": 1,
                "active": True,
                "confidence_weight": 0.95
            },
            {
                "type": "date_pattern", 
                "term": "Terminal Comma Year with Period",
                "pattern": r',\s*(\d{4})\s*[.]?\s*$',
                "format_type": "terminal_comma",
                "description": "Year at end with comma and optional period: ', 2030.'",
                "priority": 2,
                "active": True,
                "confidence_weight": 0.93
            },
            
            # Range format patterns: ", 2020-2027"
            {
                "type": "date_pattern",
                "term": "Range Format Standard",
                "pattern": r',\s*(\d{4})\s*[-–—]\s*(\d{4})\s*$',
                "format_type": "range_format",
                "description": "Date range with various dashes: ', 2020-2027'",
                "priority": 1,
                "active": True,
                "confidence_weight": 0.98
            },
            {
                "type": "date_pattern",
                "term": "Range Format with Period",
                "pattern": r',\s*(\d{4})\s*[-–—]\s*(\d{4})\s*[.]?\s*$',
                "format_type": "range_format", 
                "description": "Date range with period: ', 2020-2027.'",
                "priority": 2,
                "active": True,
                "confidence_weight": 0.97
            },
            {
                "type": "date_pattern",
                "term": "Range Format with To",
                "pattern": r',\s*(\d{4})\s*to\s*(\d{4})\s*$',
                "format_type": "range_format",
                "description": "Date range with 'to': ', 2020 to 2027'",
                "priority": 3,
                "active": True,
                "confidence_weight": 0.96
            },
            {
                "type": "date_pattern",
                "term": "Range Format Abbreviated",
                "pattern": r',\s*(\d{4})\s*-\s*(\d{2})\s*$',
                "format_type": "range_format",
                "description": "Abbreviated end year: ', 2020-27'",
                "priority": 4,
                "active": True,
                "confidence_weight": 0.94
            },
            
            # Bracket format patterns: "[2023 Report]"
            {
                "type": "date_pattern",
                "term": "Bracket Report",
                "pattern": r'\[(\d{4})\s*Report\]',
                "format_type": "bracket_format",
                "description": "Bracketed year with Report: '[2023 Report]'",
                "priority": 1,
                "active": True,
                "confidence_weight": 0.92
            },
            {
                "type": "date_pattern",
                "term": "Bracket Analysis",
                "pattern": r'\[(\d{4})\s*Analysis\]',
                "format_type": "bracket_format",
                "description": "Bracketed year with Analysis: '[2023 Analysis]'",
                "priority": 2,
                "active": True,
                "confidence_weight": 0.91
            },
            {
                "type": "date_pattern",
                "term": "Bracket Study",
                "pattern": r'\[(\d{4})\s*Study\]',
                "format_type": "bracket_format",
                "description": "Bracketed year with Study: '[2023 Study]'",
                "priority": 3,
                "active": True,
                "confidence_weight": 0.91
            },
            {
                "type": "date_pattern",
                "term": "Bracket Update",
                "pattern": r'\[(\d{4})\s*Update\]',
                "format_type": "bracket_format",
                "description": "Bracketed year with Update: '[2023 Update]'",
                "priority": 4,
                "active": True,
                "confidence_weight": 0.90
            },
            {
                "type": "date_pattern",
                "term": "Bracket Simple",
                "pattern": r'\[(\d{4})\]',
                "format_type": "bracket_format",
                "description": "Simple bracketed year: '[2023]'",
                "priority": 5,
                "active": True,
                "confidence_weight": 0.88
            },
            {
                "type": "date_pattern",
                "term": "Parentheses Report",
                "pattern": r'\((\d{4})\s*Report\)',
                "format_type": "bracket_format",
                "description": "Parentheses year with Report: '(2023 Report)'",
                "priority": 6,
                "active": True,
                "confidence_weight": 0.89
            },
            {
                "type": "date_pattern",
                "term": "Parentheses Analysis",
                "pattern": r'\((\d{4})\s*Analysis\)',
                "format_type": "bracket_format",
                "description": "Parentheses year with Analysis: '(2023 Analysis)'",
                "priority": 7,
                "active": True,
                "confidence_weight": 0.88
            },
            {
                "type": "date_pattern",
                "term": "Parentheses Study",
                "pattern": r'\((\d{4})\s*Study\)',
                "format_type": "bracket_format",
                "description": "Parentheses year with Study: '(2023 Study)'",
                "priority": 8,
                "active": True,
                "confidence_weight": 0.88
            },
            {
                "type": "date_pattern",
                "term": "Parentheses Update",
                "pattern": r'\((\d{4})\s*Update\)',
                "format_type": "bracket_format",
                "description": "Parentheses year with Update: '(2023 Update)'",
                "priority": 9,
                "active": True,
                "confidence_weight": 0.87
            },
            {
                "type": "date_pattern",
                "term": "Parentheses Simple",
                "pattern": r'\((\d{4})\)',
                "format_type": "bracket_format",
                "description": "Simple parentheses year: '(2023)'",
                "priority": 10,
                "active": True,
                "confidence_weight": 0.85
            },
            
            # Embedded format patterns: "Outlook 2031" (no comma)
            {
                "type": "date_pattern",
                "term": "Outlook Year",
                "pattern": r'\bOutlook\s+(\d{4})\b',
                "format_type": "embedded_format",
                "description": "Outlook followed by year: 'Outlook 2031'",
                "priority": 1,
                "active": True,
                "confidence_weight": 0.88
            },
            {
                "type": "date_pattern",
                "term": "Forecast Year",
                "pattern": r'\bForecast\s+(\d{4})\b',
                "format_type": "embedded_format",
                "description": "Forecast followed by year: 'Forecast 2031'",
                "priority": 2,
                "active": True,
                "confidence_weight": 0.87
            },
            {
                "type": "date_pattern",
                "term": "Projections Year",
                "pattern": r'\bProjections?\s+(\d{4})\b',
                "format_type": "embedded_format",
                "description": "Projection(s) followed by year: 'Projections 2031'",
                "priority": 3,
                "active": True,
                "confidence_weight": 0.86
            },
            {
                "type": "date_pattern",
                "term": "Through Year",
                "pattern": r'\bThrough\s+(\d{4})\b',
                "format_type": "embedded_format",
                "description": "Through followed by year: 'Through 2031'",
                "priority": 4,
                "active": True,
                "confidence_weight": 0.85
            },
            {
                "type": "date_pattern",
                "term": "By Year",
                "pattern": r'\bby\s+(\d{4})\b',
                "format_type": "embedded_format",
                "description": "By followed by year: 'by 2031'",
                "priority": 5,
                "active": True,
                "confidence_weight": 0.84
            },
            {
                "type": "date_pattern",
                "term": "To Year Not Range",
                "pattern": r'\bto\s+(\d{4})\b(?!\s*[-–—]\s*\d{4})',
                "format_type": "embedded_format",
                "description": "To followed by year (not part of range): 'to 2031'",
                "priority": 6,
                "active": True,
                "confidence_weight": 0.83
            },
            {
                "type": "date_pattern",
                "term": "Until Year",
                "pattern": r'\buntil\s+(\d{4})\b',
                "format_type": "embedded_format",
                "description": "Until followed by year: 'until 2031'",
                "priority": 7,
                "active": True,
                "confidence_weight": 0.82
            },
            {
                "type": "date_pattern",
                "term": "Year Outlook",
                "pattern": r'\b(\d{4})\s+Outlook\b',
                "format_type": "embedded_format", 
                "description": "Year followed by Outlook: '2031 Outlook'",
                "priority": 8,
                "active": True,
                "confidence_weight": 0.85
            },
            {
                "type": "date_pattern",
                "term": "Year Forecast",
                "pattern": r'\b(\d{4})\s+Forecast\b',
                "format_type": "embedded_format",
                "description": "Year followed by Forecast: '2031 Forecast'",
                "priority": 9,
                "active": True,
                "confidence_weight": 0.84
            },
            {
                "type": "date_pattern",
                "term": "Year Projections",
                "pattern": r'\b(\d{4})\s+Projections?\b',
                "format_type": "embedded_format",
                "description": "Year followed by Projection(s): '2031 Projection'",
                "priority": 10,
                "active": True,
                "confidence_weight": 0.83
            },
            {
                "type": "date_pattern",
                "term": "Report Year End",
                "pattern": r'\bReport\s+(\d{4})\s*$',
                "format_type": "embedded_format",
                "description": "Report followed by year at end: 'Report 2030'",
                "priority": 11,
                "active": True,
                "confidence_weight": 0.86
            },
            {
                "type": "date_pattern",
                "term": "Analysis Year End",
                "pattern": r'\bAnalysis\s+(\d{4})\s*$',
                "format_type": "embedded_format",
                "description": "Analysis followed by year at end: 'Analysis 2030'",
                "priority": 12,
                "active": True,
                "confidence_weight": 0.85
            },
            {
                "type": "date_pattern",
                "term": "Study Year End",
                "pattern": r'\bStudy\s+(\d{4})\s*$',
                "format_type": "embedded_format",
                "description": "Study followed by year at end: 'Study 2030'",
                "priority": 13,
                "active": True,
                "confidence_weight": 0.84
            },
            {
                "type": "date_pattern",
                "term": "Update Year End", 
                "pattern": r'\bUpdate\s+(\d{4})\s*$',
                "format_type": "embedded_format",
                "description": "Update followed by year at end: 'Update 2030'",
                "priority": 14,
                "active": True,
                "confidence_weight": 0.83
            }
        ]
        
        logger.info(f"Initializing {len(date_patterns)} date extraction patterns...")
        
        # Add each date pattern to the collection
        added_count = 0
        skipped_count = 0
        
        for pattern_data in date_patterns:
            try:
                # Check if pattern already exists
                existing = pattern_manager.search_patterns(pattern_data["term"])
                if existing:
                    logger.debug(f"Skipping existing pattern: {pattern_data['term']}")
                    skipped_count += 1
                    continue
                
                # Add the pattern
                pattern_id = pattern_manager.add_pattern(
                    PatternType.DATE_PATTERN,
                    term=pattern_data["term"],
                    aliases=[],
                    priority=pattern_data["priority"],
                    active=pattern_data["active"],
                    pattern=pattern_data["pattern"],
                    format_type=pattern_data["format_type"],
                    description=pattern_data["description"],
                    confidence_weight=pattern_data["confidence_weight"]
                )
                
                if pattern_id:
                    added_count += 1
                    logger.debug(f"Added pattern: {pattern_data['term']} ({pattern_data['format_type']})")
                
            except Exception as e:
                logger.error(f"Failed to add pattern {pattern_data['term']}: {e}")
        
        logger.info(f"Date pattern initialization complete:")
        logger.info(f"  - Added: {added_count} patterns")
        logger.info(f"  - Skipped (existing): {skipped_count} patterns")
        logger.info(f"  - Total patterns defined: {len(date_patterns)}")
        
        # Verify the patterns were added
        all_date_patterns = pattern_manager.get_patterns(PatternType.DATE_PATTERN)
        logger.info(f"  - Total date patterns in database: {len(all_date_patterns)}")
        
        # Show breakdown by format type
        format_counts = {}
        for pattern in all_date_patterns:
            format_type = pattern.get('format_type', 'unknown')
            format_counts[format_type] = format_counts.get(format_type, 0) + 1
        
        logger.info("Date patterns by format type:")
        for format_type, count in format_counts.items():
            logger.info(f"  - {format_type}: {count} patterns")
        
        pattern_manager.close_connection()
        print("✅ Date pattern initialization completed successfully!")
        return True
        
    except Exception as e:
        logger.error(f"Failed to initialize date patterns: {e}")
        print(f"❌ Date pattern initialization failed: {e}")
        return False


if __name__ == "__main__":
    success = initialize_date_patterns()
    exit(0 if success else 1)