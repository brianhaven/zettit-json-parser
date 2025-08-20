#!/usr/bin/env python3

"""
Add Missing Date Patterns to MongoDB
Adds specific patterns for common variations that were missed in initial testing.
"""

import os
import logging
from dotenv import load_dotenv
from pattern_library_manager_v1 import PatternLibraryManager, PatternType

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def add_missing_date_patterns():
    """Add missing date extraction patterns identified from testing."""
    
    # Load environment variables
    load_dotenv()
    
    try:
        # Initialize pattern manager
        pattern_manager = PatternLibraryManager()
        
        # Define missing date patterns identified from testing
        missing_patterns = [
            # Embedded format with intervening words
            {
                "type": "date_pattern",
                "term": "Year Technology Outlook",
                "pattern": r'\b(\d{4})\s+Technology\s+Outlook\b',
                "format_type": "embedded_format",
                "description": "Year followed by Technology Outlook: '2030 Technology Outlook'",
                "priority": 15,
                "active": True,
                "confidence_weight": 0.87
            },
            {
                "type": "date_pattern",
                "term": "Year Market Outlook",
                "pattern": r'\b(\d{4})\s+Market\s+Outlook\b',
                "format_type": "embedded_format", 
                "description": "Year followed by Market Outlook: '2030 Market Outlook'",
                "priority": 16,
                "active": True,
                "confidence_weight": 0.86
            },
            {
                "type": "date_pattern",
                "term": "Year Industry Outlook",
                "pattern": r'\b(\d{4})\s+Industry\s+Outlook\b',
                "format_type": "embedded_format",
                "description": "Year followed by Industry Outlook: '2030 Industry Outlook'",
                "priority": 17,
                "active": True,
                "confidence_weight": 0.86
            },
            {
                "type": "date_pattern",
                "term": "Year Global Forecast",
                "pattern": r'\b(\d{4})\s+Global\s+Forecast\b',
                "format_type": "embedded_format",
                "description": "Year followed by Global Forecast: '2030 Global Forecast'",
                "priority": 18,
                "active": True,
                "confidence_weight": 0.85
            },
            {
                "type": "date_pattern",
                "term": "Year Market Forecast",
                "pattern": r'\b(\d{4})\s+Market\s+Forecast\b',
                "format_type": "embedded_format",
                "description": "Year followed by Market Forecast: '2030 Market Forecast'",
                "priority": 19,
                "active": True,
                "confidence_weight": 0.85
            },
            {
                "type": "date_pattern",
                "term": "Year Industry Forecast",
                "pattern": r'\b(\d{4})\s+Industry\s+Forecast\b',
                "format_type": "embedded_format",
                "description": "Year followed by Industry Forecast: '2030 Industry Forecast'",
                "priority": 20,
                "active": True,
                "confidence_weight": 0.84
            },
            
            # Terminal comma with variations
            {
                "type": "date_pattern",
                "term": "Terminal Comma Analysis Year",
                "pattern": r',\s*Analysis\s+(\d{4})\s*$',
                "format_type": "terminal_comma",
                "description": "Analysis followed by year: ', Analysis 2030'",
                "priority": 3,
                "active": True,
                "confidence_weight": 0.92
            },
            {
                "type": "date_pattern",
                "term": "Terminal Comma Report Year", 
                "pattern": r',\s*Report\s+(\d{4})\s*$',
                "format_type": "terminal_comma",
                "description": "Report followed by year: ', Report 2030'",
                "priority": 4,
                "active": True,
                "confidence_weight": 0.92
            },
            
            # Embedded patterns without comma that commonly fail
            {
                "type": "date_pattern",
                "term": "Market Report Year End No Comma",
                "pattern": r'\bMarket\s+Report\s+(\d{4})\s*$',
                "format_type": "embedded_format",
                "description": "Market Report followed by year: 'Market Report 2030'",
                "priority": 21,
                "active": True,
                "confidence_weight": 0.88
            },
            {
                "type": "date_pattern",
                "term": "Industry Report Year End No Comma",
                "pattern": r'\bIndustry\s+Report\s+(\d{4})\s*$',
                "format_type": "embedded_format",
                "description": "Industry Report followed by year: 'Industry Report 2030'",
                "priority": 22,
                "active": True,
                "confidence_weight": 0.87
            },
            {
                "type": "date_pattern",
                "term": "Global Report Year End No Comma",
                "pattern": r'\bGlobal\s+Report\s+(\d{4})\s*$',
                "format_type": "embedded_format",
                "description": "Global Report followed by year: 'Global Report 2030'",
                "priority": 23,
                "active": True,
                "confidence_weight": 0.86
            },
            
            # Bracket variations that might be missed
            {
                "type": "date_pattern",
                "term": "Bracket Year Edition",
                "pattern": r'\[(\d{4})\s*Edition\]',
                "format_type": "bracket_format",
                "description": "Bracketed year with Edition: '[2023 Edition]'",
                "priority": 11,
                "active": True,
                "confidence_weight": 0.89
            },
            {
                "type": "date_pattern",
                "term": "Parentheses Year Edition",
                "pattern": r'\((\d{4})\s*Edition\)',
                "format_type": "bracket_format",
                "description": "Parentheses year with Edition: '(2023 Edition)'",
                "priority": 12,
                "active": True,
                "confidence_weight": 0.88
            },
            
            # Range format edge cases
            {
                "type": "date_pattern",
                "term": "Range Format Through",
                "pattern": r',\s*(\d{4})\s*through\s*(\d{4})\s*$',
                "format_type": "range_format",
                "description": "Date range with 'through': ', 2020 through 2027'",
                "priority": 5,
                "active": True,
                "confidence_weight": 0.95
            },
            {
                "type": "date_pattern",
                "term": "Range Format Until",
                "pattern": r',\s*(\d{4})\s*until\s*(\d{4})\s*$',
                "format_type": "range_format",
                "description": "Date range with 'until': ', 2020 until 2027'",
                "priority": 6,
                "active": True,
                "confidence_weight": 0.94
            }
        ]
        
        logger.info(f"Adding {len(missing_patterns)} missing date extraction patterns...")
        
        # Add each missing pattern to the collection
        added_count = 0
        skipped_count = 0
        
        for pattern_data in missing_patterns:
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
                    logger.info(f"Added pattern: {pattern_data['term']} ({pattern_data['format_type']})")
                
            except Exception as e:
                logger.error(f"Failed to add pattern {pattern_data['term']}: {e}")
        
        logger.info(f"Missing pattern addition complete:")
        logger.info(f"  - Added: {added_count} patterns")
        logger.info(f"  - Skipped (existing): {skipped_count} patterns")
        logger.info(f"  - Total patterns attempted: {len(missing_patterns)}")
        
        # Verify the total patterns in database
        all_date_patterns = pattern_manager.get_patterns(PatternType.DATE_PATTERN)
        logger.info(f"  - Total date patterns in database: {len(all_date_patterns)}")
        
        # Show updated breakdown by format type
        format_counts = {}
        for pattern in all_date_patterns:
            format_type = pattern.get('format_type', 'unknown')
            format_counts[format_type] = format_counts.get(format_type, 0) + 1
        
        logger.info("Updated date patterns by format type:")
        for format_type, count in format_counts.items():
            logger.info(f"  - {format_type}: {count} patterns")
        
        pattern_manager.close_connection()
        print("✅ Missing date pattern addition completed successfully!")
        return True
        
    except Exception as e:
        logger.error(f"Failed to add missing date patterns: {e}")
        print(f"❌ Missing pattern addition failed: {e}")
        return False


if __name__ == "__main__":
    success = add_missing_date_patterns()
    exit(0 if success else 1)