#!/usr/bin/env python3

"""
Add Approved Discovered Report Type Patterns to MongoDB
Based on comprehensive pattern discovery results, adds validated patterns while avoiding duplicates.
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

def get_approved_patterns():
    """
    Returns approved patterns from comprehensive discovery (Tiers 1-3 + selected Tier 4).
    These are based on user's manual review feedback.
    """
    
    # Based on user approval: Tiers 1-3 all approved, plus selected Tier 4 patterns
    approved_patterns = [
        # Tier 1: High-frequency core patterns (already mostly covered by existing patterns)
        {"term": "Market Size Report", "pattern": r'\bMarket\s+Size\s+(Report)(?:\s*$|[,.])', "priority": 1, "confidence": 0.95},
        {"term": "Market Size Industry Report", "pattern": r'\bMarket\s+Size,\s+Industry\s+(Report)(?:\s*$|[,.])', "priority": 1, "confidence": 0.95},
        {"term": "Market Size Share Report", "pattern": r'\bMarket\s+Size\s*&\s*Share\s+(Report)(?:\s*$|[,.])', "priority": 1, "confidence": 0.95},
        {"term": "Market Report", "pattern": r'\bMarket\s+(Report)(?:\s*$|[,.])', "priority": 1, "confidence": 0.94},
        {"term": "Market Industry Report", "pattern": r'\bMarket,\s+Industry\s+(Report)(?:\s*$|[,.])', "priority": 1, "confidence": 0.94},
        {"term": "Market Size Share Growth Report", "pattern": r'\bMarket\s+Size,\s+Share\s*&\s*Growth\s+(Report)(?:\s*$|[,.])', "priority": 1, "confidence": 0.94},
        {"term": "Market Size And Share Report", "pattern": r'\bMarket\s+Size\s+And\s+Share\s+(Report)(?:\s*$|[,.])', "priority": 1, "confidence": 0.94},
        
        # Tier 2: Medium-frequency patterns  
        {"term": "Market Size Share Industry Report", "pattern": r'\bMarket\s+Size\s*&\s*Share,\s+Industry\s+(Report)(?:\s*$|[,.])', "priority": 2, "confidence": 0.93},
        {"term": "Market Size Share Trends Report", "pattern": r'\bMarket\s+Size,\s+Share\s*&\s*Trends\s+(Report)(?:\s*$|[,.])', "priority": 2, "confidence": 0.93},
        {"term": "Market Size Share And Growth Report", "pattern": r'\bMarket\s+Size,\s+Share\s+And\s+Growth\s+(Report)(?:\s*$|[,.])', "priority": 2, "confidence": 0.93},
        {"term": "Market Size Share And Trends Report", "pattern": r'\bMarket\s+Size,\s+Share\s+And\s+Trends\s+(Report)(?:\s*$|[,.])', "priority": 2, "confidence": 0.92},
        {"term": "Market Insights", "pattern": r'\bMarket\s+(Insights)(?:\s*$|[,.])', "priority": 2, "confidence": 0.92},
        {"term": "Market Size Share Global Industry Report", "pattern": r'\bMarket\s+Size,\s+Share,\s+Global\s+Industry\s+(Report)(?:\s*$|[,.])', "priority": 2, "confidence": 0.92},
        {"term": "Market Size Global Industry Report", "pattern": r'\bMarket\s+Size,\s+Global\s+Industry\s+(Report)(?:\s*$|[,.])', "priority": 2, "confidence": 0.92},
        {"term": "Market Size Share Terminal", "pattern": r'\bMarket\s+Size\s*&\s*Share(?:\s*$|[,.])', "priority": 2, "confidence": 0.91},
        {"term": "Market Industry Terminal", "pattern": r'\bMarket,\s+Industry(?:\s*$|[,.])', "priority": 2, "confidence": 0.91},
        {"term": "Market Size Share Industry Terminal", "pattern": r'\bMarket\s+Size,\s+Share,\s+Industry(?:\s*$|[,.])', "priority": 2, "confidence": 0.91},
        {"term": "Market Size Terminal", "pattern": r'\bMarket\s+Size(?:\s*$|[,.])', "priority": 2, "confidence": 0.90},
        {"term": "Market Report Terminal", "pattern": r'\bMarket,\s+(Report)(?:\s*$|[,.])', "priority": 2, "confidence": 0.90},
        {"term": "Market Size Share Terminal2", "pattern": r'\bMarket\s+Size,\s+Share(?:\s*$|[,.])', "priority": 2, "confidence": 0.90},
        
        # Tier 3: Lower frequency but still legitimate patterns
        {"term": "Market Size Share Growth Terminal", "pattern": r'\bMarket\s+Size,\s+Share,\s+Growth(?:\s*$|[,.])', "priority": 3, "confidence": 0.89},
        {"term": "Market Size Share Growth Analysis Report", "pattern": r'\bMarket\s+Size,\s+Share\s*&\s*Growth\s+(Analysis\s+Report)(?:\s*$|[,.])', "priority": 3, "confidence": 0.89},
        {"term": "Market Size Growth Report", "pattern": r'\bMarket\s+Size\s*&\s*Growth\s+(Report)(?:\s*$|[,.])', "priority": 3, "confidence": 0.89},
        {"term": "Market Outlook", "pattern": r'\bMarket\s+(Outlook)(?:\s*$|[,.])', "priority": 3, "confidence": 0.88},
        {"term": "Market Size Industry Terminal", "pattern": r'\bMarket\s+Size,\s+Industry(?:\s*$|[,.])', "priority": 3, "confidence": 0.88},
        {"term": "Market Size Share Analysis Report", "pattern": r'\bMarket\s+Size\s*&\s*Share\s+(Analysis\s+Report)(?:\s*$|[,.])', "priority": 3, "confidence": 0.88},
        {"term": "Market Trends", "pattern": r'\bMarket\s+(Trends)(?:\s*$|[,.])', "priority": 3, "confidence": 0.87},
        {"term": "Market Size Report Terminal", "pattern": r'\bMarket\s+Size,\s+(Report)(?:\s*$|[,.])', "priority": 3, "confidence": 0.87},
        {"term": "Market Analysis", "pattern": r'\bMarket\s+(Analysis)(?:\s*$|[,.])', "priority": 3, "confidence": 0.86},
        {"term": "Market Size Share Growth Industry Report", "pattern": r'\bMarket\s+Size,\s+Share\s*&\s*Growth,\s+Industry\s+(Report)(?:\s*$|[,.])', "priority": 3, "confidence": 0.86},
        {"term": "Market Forecast", "pattern": r'\bMarket\s+(Forecast)(?:\s*$|[,.])', "priority": 3, "confidence": 0.85},
        {"term": "Market Forecast Report", "pattern": r'\bMarket\s+(Forecast\s+Report)(?:\s*$|[,.])', "priority": 3, "confidence": 0.85},
        {"term": "Market Size Share Trends Analysis Report", "pattern": r'\bMarket\s+Size,\s+Share\s*&\s*Trends\s+(Analysis\s+Report)(?:\s*$|[,.])', "priority": 3, "confidence": 0.85},
        
        # Tier 4: Selected approved patterns (Forecast and Analysis formats)
        {"term": "Market Forecast Format", "pattern": r'\bMarket\s+\(Forecast\s*\)(?:\s*$|[,.])', "priority": 4, "confidence": 0.84},
        {"term": "Market Size Share Analysis Industry Research Report Growth Trends", "pattern": r'\bMarket\s+Size\s*&\s*Share\s+Analysis\s*-\s*Industry\s+Research\s+Report\s*-\s*Growth\s+Trends(?:\s*$|[,.])', "priority": 4, "confidence": 0.84},
    ]
    
    return approved_patterns

def add_discovered_patterns():
    """Add approved discovered patterns to MongoDB while avoiding duplicates."""
    
    try:
        # Initialize pattern manager
        pattern_manager = PatternLibraryManager()
        
        # Get existing patterns to check for duplicates
        existing_patterns = pattern_manager.get_patterns(PatternType.REPORT_TYPE)
        existing_terms = set(pattern.get('term', '').lower() for pattern in existing_patterns)
        
        logger.info(f"Found {len(existing_patterns)} existing report type patterns")
        
        # Get approved patterns from discovery
        approved_patterns = get_approved_patterns()
        
        logger.info(f"Adding {len(approved_patterns)} approved discovered patterns...")
        
        # Add each approved pattern to the collection
        added_count = 0
        skipped_count = 0
        
        for pattern_data in approved_patterns:
            try:
                # Check if pattern already exists (case-insensitive)
                if pattern_data["term"].lower() in existing_terms:
                    logger.debug(f"Skipping existing pattern: {pattern_data['term']}")
                    skipped_count += 1
                    continue
                
                # Add the pattern
                pattern_id = pattern_manager.add_pattern(
                    PatternType.REPORT_TYPE,
                    term=pattern_data["term"],
                    aliases=[],
                    priority=pattern_data.get("priority", 3),
                    active=True,
                    pattern=pattern_data["pattern"],
                    format_type="discovered",
                    description=f"Discovered from comprehensive data analysis - {pattern_data.get('confidence', 0.85):.0%} confidence",
                    confidence_weight=pattern_data.get("confidence", 0.85),
                    normalized_form=pattern_data["pattern"].split('(')[-1].split(')')[0] if '(' in pattern_data["pattern"] else "Report"
                )
                
                if pattern_id:
                    added_count += 1
                    logger.info(f"✅ Added discovered pattern: {pattern_data['term']} (confidence: {pattern_data.get('confidence', 0.85):.0%})")
                    # Add to existing terms to avoid duplicates in this batch
                    existing_terms.add(pattern_data["term"].lower())
                
            except Exception as e:
                logger.error(f"Failed to add pattern {pattern_data['term']}: {e}")
        
        logger.info(f"\n{'='*60}")
        logger.info(f"Discovered pattern addition complete:")
        logger.info(f"  - Added: {added_count} patterns")
        logger.info(f"  - Skipped (existing): {skipped_count} patterns")
        logger.info(f"  - Total patterns attempted: {len(approved_patterns)}")
        
        # Verify the patterns were added
        all_report_patterns = pattern_manager.get_patterns(PatternType.REPORT_TYPE)
        logger.info(f"  - Total report patterns in database: {len(all_report_patterns)}")
        
        # Show breakdown by format type
        format_counts = {}
        for pattern in all_report_patterns:
            metadata = pattern.get('metadata', {})
            format_type = metadata.get('format_type', pattern.get('format_type', 'unknown'))
            format_counts[format_type] = format_counts.get(format_type, 0) + 1
        
        logger.info("Report patterns by format type:")
        for format_type, count in sorted(format_counts.items()):
            logger.info(f"  - {format_type}: {count} patterns")
        
        pattern_manager.close_connection()
        return True
        
    except Exception as e:
        logger.error(f"Failed to add discovered patterns: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = add_discovered_patterns()
    if success:
        print("\n✅ Approved discovered report type patterns successfully added to MongoDB")
        print("These patterns are based on comprehensive analysis of all 19,553 titles")
        print("Run Phase 3 pipeline test again to measure significant improvement")
    else:
        print("\n❌ Failed to add approved discovered report type patterns")
        sys.exit(1)