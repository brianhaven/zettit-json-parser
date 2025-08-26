#!/usr/bin/env python3

"""
Enhance Report Type Patterns in MongoDB
Based on Phase 3 test results, adds missing comma-separated patterns
like "Market Size, Report", "Market, Report", etc.
"""

import os
import sys
import logging
import importlib.util
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Dynamic import for pattern library manager
try:
    spec = importlib.util.spec_from_file_location(
        "pattern_library_manager_v1", 
        "00b_pattern_library_manager_v1.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    
    PatternLibraryManager = module.PatternLibraryManager
    PatternType = module.PatternType
except Exception as e:
    logger.error(f"Could not import PatternLibraryManager: {e}")
    sys.exit(1)

def enhance_report_patterns():
    """Add enhanced report type patterns based on Phase 3 test results."""
    
    try:
        # Initialize pattern manager
        pattern_manager = PatternLibraryManager()
        
        # Enhanced patterns based on Phase 3 analysis
        # These handle comma-separated formats that were missed
        enhanced_patterns = [
            # Comma-separated terminal patterns (most common in failed extractions)
            {
                "type": "report_type",
                "term": "Market Size Report Terminal",
                "pattern": r'\bMarket\s+Size,?\s+(Report)(?:\s*$|[,.])',
                "format_type": "comma_separated",
                "description": "Market Size, Report: 'Global AI Market Size, Report'",
                "priority": 1,
                "active": True,
                "confidence_weight": 0.93,
                "normalized_form": "Report"
            },
            {
                "type": "report_type", 
                "term": "Market Share Report Terminal",
                "pattern": r'\bMarket\s+Share,?\s+(Report)(?:\s*$|[,.])',
                "format_type": "comma_separated",
                "description": "Market Share, Report: 'Industry Market Share, Report'",
                "priority": 1,
                "active": True,
                "confidence_weight": 0.93,
                "normalized_form": "Report"
            },
            {
                "type": "report_type",
                "term": "Market Analysis Terminal",
                "pattern": r'\bMarket,?\s+(Analysis)(?:\s*$|[,.])',
                "format_type": "comma_separated", 
                "description": "Market, Analysis: 'Global Market, Analysis'",
                "priority": 1,
                "active": True,
                "confidence_weight": 0.92,
                "normalized_form": "Analysis"
            },
            {
                "type": "report_type",
                "term": "Market Report Terminal",
                "pattern": r'\bMarket,?\s+(Report)(?:\s*$|[,.])',
                "format_type": "comma_separated",
                "description": "Market, Report: 'AI Market, Report'", 
                "priority": 1,
                "active": True,
                "confidence_weight": 0.92,
                "normalized_form": "Report"
            },
            
            # Complex compound patterns with Size, Share indicators
            {
                "type": "report_type",
                "term": "Market Size Share Report",
                "pattern": r'\bMarket\s+Size,?\s+Share,?\s*&?\s*Growth?\s*(Report)(?:\s*$|[,.])',
                "format_type": "complex_compound",
                "description": "Market Size, Share & Growth Report",
                "priority": 1,
                "active": True,
                "confidence_weight": 0.94,
                "normalized_form": "Report"
            },
            {
                "type": "report_type",
                "term": "Global Industry Report",
                "pattern": r'\bGlobal\s+Industry\s+(Report)(?:\s*$|[,.])',
                "format_type": "compound_type",
                "description": "Global Industry Report",
                "priority": 2,
                "active": True,
                "confidence_weight": 0.91,
                "normalized_form": "Report"
            },
            
            # Industry-specific patterns
            {
                "type": "report_type",
                "term": "Industry Report Terminal",
                "pattern": r'\bIndustry,?\s+(Report)(?:\s*$|[,.])',
                "format_type": "comma_separated",
                "description": "Industry, Report: 'Healthcare Industry, Report'",
                "priority": 2,
                "active": True,
                "confidence_weight": 0.90,
                "normalized_form": "Report"
            },
            {
                "type": "report_type",
                "term": "Industry Analysis Terminal", 
                "pattern": r'\bIndustry,?\s+(Analysis)(?:\s*$|[,.])',
                "format_type": "comma_separated",
                "description": "Industry, Analysis: 'Tech Industry, Analysis'",
                "priority": 2,
                "active": True,
                "confidence_weight": 0.90,
                "normalized_form": "Analysis"
            },
            
            # Trends patterns (6.4% occurrence in failed extractions)
            {
                "type": "report_type",
                "term": "Market Trends Terminal",
                "pattern": r'\bMarket,?\s+(Trends)(?:\s*$|[,.])',
                "format_type": "comma_separated",
                "description": "Market, Trends: 'AI Market, Trends'",
                "priority": 3,
                "active": True,
                "confidence_weight": 0.89,
                "normalized_form": "Trends"
            },
            {
                "type": "report_type",
                "term": "Industry Trends Terminal",
                "pattern": r'\bIndustry,?\s+(Trends)(?:\s*$|[,.])',
                "format_type": "comma_separated",
                "description": "Industry, Trends: 'Healthcare Industry, Trends'",
                "priority": 3,
                "active": True,
                "confidence_weight": 0.89,
                "normalized_form": "Trends"
            },
            
            # Data and Research patterns (lower occurrence but still present)
            {
                "type": "report_type",
                "term": "Market Data Terminal",
                "pattern": r'\bMarket,?\s+(Data)(?:\s*$|[,.])',
                "format_type": "comma_separated",
                "description": "Market, Data: 'Global Market, Data'",
                "priority": 4,
                "active": True,
                "confidence_weight": 0.87,
                "normalized_form": "Data"
            },
            {
                "type": "report_type",
                "term": "Market Research Terminal",
                "pattern": r'\bMarket,?\s+(Research)(?:\s*$|[,.])',
                "format_type": "comma_separated",
                "description": "Market, Research: 'Industry Market, Research'",
                "priority": 4,
                "active": True,
                "confidence_weight": 0.88,
                "normalized_form": "Research"
            },
            
            # Intelligence patterns (0.2% occurrence)
            {
                "type": "report_type",
                "term": "Market Intelligence Terminal",
                "pattern": r'\bMarket,?\s+(Intelligence)(?:\s*$|[,.])',
                "format_type": "comma_separated",
                "description": "Market, Intelligence: 'Digital Market, Intelligence'",
                "priority": 5,
                "active": True,
                "confidence_weight": 0.86,
                "normalized_form": "Intelligence"
            },
            
            # Forecast patterns (0.1% occurrence)
            {
                "type": "report_type",
                "term": "Market Forecast Terminal",
                "pattern": r'\bMarket,?\s+(Forecast)(?:\s*$|[,.])',
                "format_type": "comma_separated",
                "description": "Market, Forecast: 'Technology Market, Forecast'",
                "priority": 6,
                "active": True,
                "confidence_weight": 0.85,
                "normalized_form": "Forecast"
            },
            
            # Additional compound variations
            {
                "type": "report_type",
                "term": "Size Share Analysis",
                "pattern": r'\bSize,?\s+Share,?\s+(Analysis)(?:\s*$|[,.])',
                "format_type": "compound_type",
                "description": "Size, Share Analysis: 'Market Size, Share Analysis'",
                "priority": 3,
                "active": True,
                "confidence_weight": 0.91,
                "normalized_form": "Analysis"
            },
            {
                "type": "report_type",
                "term": "Size Growth Report",
                "pattern": r'\bSize,?\s*&?\s*Growth\s+(Report)(?:\s*$|[,.])',
                "format_type": "compound_type",
                "description": "Size & Growth Report: 'Market Size & Growth Report'",
                "priority": 3,
                "active": True,
                "confidence_weight": 0.91,
                "normalized_form": "Report"
            }
        ]
        
        logger.info(f"Adding {len(enhanced_patterns)} enhanced report type patterns...")
        
        # Add each enhanced pattern to the collection
        added_count = 0
        skipped_count = 0
        
        for pattern_data in enhanced_patterns:
            try:
                # Check if pattern already exists
                existing = pattern_manager.search_patterns(pattern_data["term"])
                
                if existing:
                    logger.debug(f"Skipping existing pattern: {pattern_data['term']}")
                    skipped_count += 1
                    continue
                
                # Add the enhanced pattern
                pattern_id = pattern_manager.add_pattern(
                    PatternType.REPORT_TYPE,
                    term=pattern_data["term"],
                    aliases=[],
                    priority=pattern_data.get("priority", 3),
                    active=pattern_data.get("active", True),
                    pattern=pattern_data["pattern"],
                    format_type=pattern_data.get("format_type", "enhanced"),
                    description=pattern_data.get("description", ""),
                    confidence_weight=pattern_data.get("confidence_weight", 0.85),
                    normalized_form=pattern_data.get("normalized_form", "Report")
                )
                
                if pattern_id:
                    added_count += 1
                    logger.info(f"✅ Added enhanced pattern: {pattern_data['term']} ({pattern_data['format_type']})")
                
            except Exception as e:
                logger.error(f"Failed to add pattern {pattern_data['term']}: {e}")
        
        logger.info(f"\n{'='*60}")
        logger.info(f"Enhanced pattern addition complete:")
        logger.info(f"  - Added: {added_count} patterns")
        logger.info(f"  - Skipped (existing): {skipped_count} patterns")
        logger.info(f"  - Total patterns attempted: {len(enhanced_patterns)}")
        
        # Verify the patterns were added
        all_report_patterns = pattern_manager.get_patterns(PatternType.REPORT_TYPE)
        logger.info(f"  - Total report patterns in database: {len(all_report_patterns)}")
        
        # Show breakdown by format type
        format_counts = {}
        for pattern in all_report_patterns:
            metadata = pattern.get('metadata', {})
            format_type = metadata.get('format_type', pattern.get('format_type', 'unknown'))
            format_counts[format_type] = format_counts.get(format_type, 0) + 1
        
        logger.info("Enhanced report patterns by format type:")
        for format_type, count in sorted(format_counts.items()):
            logger.info(f"  - {format_type}: {count} patterns")
        
        pattern_manager.close_connection()
        return True
        
    except Exception as e:
        logger.error(f"Failed to enhance report patterns: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = enhance_report_patterns()
    if success:
        print("\n✅ Enhanced report type patterns successfully added to MongoDB")
        print("These patterns handle comma-separated formats like 'Market Size, Report'")
        print("Run Phase 3 test again to measure improvement in extraction rates")
    else:
        print("\n❌ Failed to add enhanced report type patterns")
        sys.exit(1)