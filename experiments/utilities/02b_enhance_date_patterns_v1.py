#!/usr/bin/env python3

"""
Enhance Date Patterns in MongoDB - Phase 2 Iteration 1
Adds missing date patterns discovered through Phase 2 pipeline testing.
Focus: Range patterns without commas, standalone years, and edge cases.
"""

import os
import sys
import logging
from dotenv import load_dotenv
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
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def enhance_date_patterns():
    """Enhance date extraction patterns based on Phase 2 testing results."""
    
    # Load environment variables
    load_dotenv()
    
    try:
        # Initialize pattern manager
        pattern_manager = PatternLibraryManager()
        
        # Enhanced date patterns based on edge case analysis
        enhanced_patterns = [
            
            # === RANGE FORMAT ENHANCEMENTS ===
            # Patterns for ranges without leading commas (major gap identified)
            {
                "type": "date_pattern",
                "term": "Standalone Range Format",
                "pattern": r'\b(\d{4})\s*[-–—]\s*(\d{4})\b',
                "format_type": "range_format",
                "description": "Date range without comma: '2019-2025' embedded in text",
                "priority": 1,
                "active": True,
                "confidence_weight": 0.90
            },
            {
                "type": "date_pattern",
                "term": "Standalone Range with Spaces",
                "pattern": r'\b(\d{4})\s*[-–—]\s*(\d{4})\s*[.]?\s*$',
                "format_type": "range_format",
                "description": "Date range at end without comma: '2019 - 2025.'",
                "priority": 2,
                "active": True,
                "confidence_weight": 0.92
            },
            {
                "type": "date_pattern",
                "term": "Range with To Standalone",
                "pattern": r'\b(\d{4})\s*to\s*(\d{4})\b',
                "format_type": "range_format",
                "description": "Date range with 'to' without comma: '2019 to 2025'",
                "priority": 3,
                "active": True,
                "confidence_weight": 0.89
            },
            {
                "type": "date_pattern",
                "term": "Range with Through",
                "pattern": r'\b(\d{4})\s*through\s*(\d{4})\b',
                "format_type": "range_format",
                "description": "Date range with 'through': '2019 through 2025'",
                "priority": 4,
                "active": True,
                "confidence_weight": 0.88
            },
            
            # === EMBEDDED FORMAT ENHANCEMENTS ===
            # Additional patterns for standalone years
            {
                "type": "date_pattern",
                "term": "Standalone Year Market",
                "pattern": r'\bmarket\s+(\d{4})\b',
                "format_type": "embedded_format",
                "description": "Year after 'market': 'market 2025'",
                "priority": 8,
                "active": True,
                "confidence_weight": 0.75
            },
            {
                "type": "date_pattern",
                "term": "Report Year Standalone",
                "pattern": r'\breport\s+(\d{4})\b',
                "format_type": "embedded_format",
                "description": "Year after 'report': 'report 2025'",
                "priority": 9,
                "active": True,
                "confidence_weight": 0.78
            },
            {
                "type": "date_pattern", 
                "term": "Analysis Year Standalone",
                "pattern": r'\banalysis\s+(\d{4})\b',
                "format_type": "embedded_format",
                "description": "Year after 'analysis': 'analysis 2025'",
                "priority": 10,
                "active": True,
                "confidence_weight": 0.77
            },
            {
                "type": "date_pattern",
                "term": "Study Year Standalone", 
                "pattern": r'\bstudy\s+(\d{4})\b',
                "format_type": "embedded_format",
                "description": "Year after 'study': 'study 2025'",
                "priority": 11,
                "active": True,
                "confidence_weight": 0.76
            },
            {
                "type": "date_pattern",
                "term": "Size Year Standalone",
                "pattern": r'\bsize\s+(\d{4})\b',
                "format_type": "embedded_format", 
                "description": "Year after 'size': 'size 2025'",
                "priority": 12,
                "active": True,
                "confidence_weight": 0.74
            },
            
            # === TERMINAL COMMA ENHANCEMENTS ===
            # Additional terminal patterns found in edge cases
            {
                "type": "date_pattern",
                "term": "Terminal Comma with Report",
                "pattern": r',\s*report\s*(\d{4})\s*$',
                "format_type": "terminal_comma",
                "description": "Terminal comma with report: ', report 2030'",
                "priority": 5,
                "active": True,
                "confidence_weight": 0.91
            },
            {
                "type": "date_pattern",
                "term": "Terminal Comma Analysis",
                "pattern": r',\s*analysis\s*(\d{4})\s*$',
                "format_type": "terminal_comma",
                "description": "Terminal comma with analysis: ', analysis 2030'",
                "priority": 6,
                "active": True,
                "confidence_weight": 0.90
            },
            
            # === BRACKET FORMAT ENHANCEMENTS ===
            # Additional bracket patterns for single years
            {
                "type": "date_pattern",
                "term": "Simple Year Brackets",
                "pattern": r'\[(\d{4})\]',
                "format_type": "bracket_format",
                "description": "Simple year in brackets: '[2025]'",
                "priority": 3,
                "active": True,
                "confidence_weight": 0.87
            },
            {
                "type": "date_pattern",
                "term": "Year Range Brackets",
                "pattern": r'\[(\d{4})\s*[-–—]\s*(\d{4})\]',
                "format_type": "bracket_format",
                "description": "Year range in brackets: '[2020-2025]'",
                "priority": 4,
                "active": True,
                "confidence_weight": 0.89
            },
            {
                "type": "date_pattern",
                "term": "Parentheses Year Only",
                "pattern": r'\((\d{4})\)',
                "format_type": "bracket_format",
                "description": "Year in parentheses: '(2025)'",
                "priority": 5,
                "active": True,
                "confidence_weight": 0.85
            },
            {
                "type": "date_pattern",
                "term": "Parentheses Year Range",
                "pattern": r'\((\d{4})\s*[-–—]\s*(\d{4})\)',
                "format_type": "bracket_format",
                "description": "Year range in parentheses: '(2020-2025)'",
                "priority": 6,
                "active": True,
                "confidence_weight": 0.87
            },
            
            # === EDGE CASE PATTERNS ===
            # Patterns for fiscal years and quarters
            {
                "type": "date_pattern",
                "term": "Fiscal Year",
                "pattern": r'\bfy\s*(\d{4})\b|\bfiscal\s*year\s*(\d{4})\b',
                "format_type": "embedded_format",
                "description": "Fiscal year: 'FY 2025' or 'fiscal year 2025'",
                "priority": 13,
                "active": True,
                "confidence_weight": 0.82
            },
            {
                "type": "date_pattern",
                "term": "Quarter Year",
                "pattern": r'\bq[1-4]\s*(\d{4})\b|\bquarter\s*[1-4]\s*(\d{4})\b',
                "format_type": "embedded_format",
                "description": "Quarter year: 'Q1 2025' or 'quarter 1 2025'",
                "priority": 14,
                "active": True,
                "confidence_weight": 0.80
            },
            {
                "type": "date_pattern",
                "term": "Year Quarter",
                "pattern": r'\b(\d{4})\s*q[1-4]\b|\b(\d{4})\s*quarter\s*[1-4]\b',
                "format_type": "embedded_format",
                "description": "Year quarter: '2025 Q1' or '2025 quarter 1'",
                "priority": 15,
                "active": True,
                "confidence_weight": 0.81
            },
            
            # === FALLBACK PATTERNS ===
            # Last resort patterns for isolated years
            {
                "type": "date_pattern",
                "term": "Standalone Year at End",
                "pattern": r'\b(\d{4})\s*$',
                "format_type": "embedded_format",
                "description": "Standalone year at end of title: '...2025'",
                "priority": 20,
                "active": True,
                "confidence_weight": 0.60
            },
            {
                "type": "date_pattern",
                "term": "Standalone Year in Text",
                "pattern": r'\b(\d{4})\b(?!\s*[-–—]\s*\d{4})',
                "format_type": "embedded_format", 
                "description": "Standalone year in text (not part of range): '...2025...'",
                "priority": 21,
                "active": True,
                "confidence_weight": 0.50
            }
        ]
        
        # Add patterns to database
        logger.info(f"Adding {len(enhanced_patterns)} enhanced date extraction patterns...")
        
        added_count = 0
        skipped_count = 0
        
        for pattern_data in enhanced_patterns:
            try:
                # Check if pattern already exists
                existing = pattern_manager.search_patterns(pattern_data["term"])
                if existing:
                    logger.info(f"Found {len(existing)} patterns matching '{pattern_data['term']}'")
                    skipped_count += 1
                    continue
                
                # Add the pattern using the correct method signature
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
                    logger.info(f"✅ Added pattern: {pattern_data['term']}")
                else:
                    logger.warning(f"❌ Failed to add pattern: {pattern_data['term']}")
                    
            except Exception as e:
                logger.error(f"Error adding pattern '{pattern_data['term']}': {e}")
        
        # Report results
        logger.info("Enhanced date pattern initialization complete:")
        logger.info(f"  - Added: {added_count} patterns")
        logger.info(f"  - Skipped (existing): {skipped_count} patterns")
        logger.info(f"  - Total patterns attempted: {len(enhanced_patterns)}")
        
        # Verify total patterns in database
        all_date_patterns = pattern_manager.get_patterns(PatternType.DATE_PATTERN)
        logger.info(f"  - Total date patterns in database: {len(all_date_patterns)}")
        
        # Show patterns by format type for verification
        format_counts = {}
        for pattern in all_date_patterns:
            format_type = pattern.get('format_type', 'unknown')
            format_counts[format_type] = format_counts.get(format_type, 0) + 1
        
        logger.info("Enhanced date patterns by format type:")
        for format_type, count in format_counts.items():
            logger.info(f"  - {format_type}: {count} patterns")
        
        print("✅ Enhanced date pattern initialization completed successfully!")
        
    except Exception as e:
        logger.error(f"Error initializing enhanced date patterns: {e}")
        raise
    finally:
        # Close MongoDB connection
        if 'pattern_manager' in locals():
            pattern_manager.close_connection()
            logger.info("MongoDB connection closed")

if __name__ == "__main__":
    enhance_date_patterns()