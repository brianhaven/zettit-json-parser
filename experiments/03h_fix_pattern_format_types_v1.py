#!/usr/bin/env python3

"""
Fix Report Type Pattern Format Types for Proper Loading
Updates format_type fields for comprehensive patterns to match expected categories.
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

def categorize_pattern_format_type(term: str, pattern: str) -> str:
    """
    Categorize pattern format type based on term and pattern structure.
    
    Args:
        term: The pattern term
        pattern: The regex pattern
        
    Returns:
        Format type: terminal_type, embedded_type, prefix_type, or compound_type
    """
    
    # Clean term for analysis
    clean_term = term.replace("Manual Review #", "").replace(": ", "").strip()
    
    # Terminal types: Single words at end (Report, Analysis, Outlook, etc.)
    if clean_term in ['Market Report', 'Market Analysis', 'Market Outlook', 'Market Forecast', 'Market Insights', 'Market Trends', 'Market Growth']:
        return 'terminal_type'
    
    # Embedded types: Simple Market + single descriptor
    if clean_term in ['Market Terminal', 'Market Share Terminal', 'Market Size Terminal']:
        return 'embedded_type'
        
    # Prefix types: Market + simple descriptor + type word
    if clean_term.startswith('Market Size Report') or clean_term.startswith('Market Share Report'):
        if clean_term.count(',') == 0 and clean_term.count('&') == 0:
            return 'prefix_type'
    
    # Everything else is compound_type (complex patterns with multiple descriptors)
    return 'compound_type'

def fix_pattern_format_types():
    """Fix format_type fields for comprehensive patterns."""
    
    try:
        # Initialize pattern manager
        pattern_manager = PatternLibraryManager()
        
        # Get all report type patterns
        all_patterns = pattern_manager.get_patterns(PatternType.REPORT_TYPE)
        logger.info(f"Found {len(all_patterns)} total report type patterns")
        
        # Find patterns that need format_type fixes
        patterns_to_fix = []
        problematic_format_types = {
            'comprehensive_approved', 'discovered', 'manual_approved', 
            'comma_separated', 'complex_compound'
        }
        
        for pattern in all_patterns:
            format_type = pattern.get('metadata', {}).get('format_type') or pattern.get('format_type', '')
            
            if format_type in problematic_format_types:
                patterns_to_fix.append(pattern)
        
        logger.info(f"Found {len(patterns_to_fix)} patterns with problematic format_types")
        
        # Fix each pattern
        fixed_count = 0
        category_counts = {
            'terminal_type': 0,
            'embedded_type': 0, 
            'prefix_type': 0,
            'compound_type': 0
        }
        
        for pattern in patterns_to_fix:
            try:
                pattern_id = pattern.get('_id')
                term = pattern.get('term', '')
                pattern_regex = pattern.get('pattern', '')
                
                # Determine correct format type
                correct_format_type = categorize_pattern_format_type(term, pattern_regex)
                category_counts[correct_format_type] += 1
                
                # Update the pattern in database
                updates = {
                    'format_type': correct_format_type,
                    'description': f"Auto-categorized as {correct_format_type} pattern"
                }
                success = pattern_manager.update_pattern(
                    pattern_id=str(pattern_id),
                    updates=updates
                )
                
                if success:
                    fixed_count += 1
                    logger.debug(f"✅ Fixed pattern '{term}' -> {correct_format_type}")
                else:
                    logger.error(f"❌ Failed to update pattern '{term}'")
                    
            except Exception as e:
                logger.error(f"Failed to fix pattern {pattern.get('term', 'unknown')}: {e}")
        
        logger.info(f"\n{'='*60}")
        logger.info(f"Pattern format type fix complete:")
        logger.info(f"  - Fixed: {fixed_count} patterns")
        logger.info(f"  - Failed: {len(patterns_to_fix) - fixed_count} patterns")
        logger.info(f"  - Total patterns attempted: {len(patterns_to_fix)}")
        
        logger.info(f"\nPattern categorization breakdown:")
        for category, count in category_counts.items():
            logger.info(f"  - {category}: {count} patterns")
        
        # Verify the fix worked
        updated_patterns = pattern_manager.get_patterns(PatternType.REPORT_TYPE)
        format_counts = {}
        for pattern in updated_patterns:
            format_type = pattern.get('metadata', {}).get('format_type') or pattern.get('format_type', 'unknown')
            format_counts[format_type] = format_counts.get(format_type, 0) + 1
        
        logger.info(f"\nUpdated format type distribution:")
        for format_type, count in sorted(format_counts.items()):
            logger.info(f"  - {format_type}: {count} patterns")
        
        pattern_manager.close_connection()
        return True
        
    except Exception as e:
        logger.error(f"Failed to fix pattern format types: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = fix_pattern_format_types()
    if success:
        print(f"\n✅ Pattern format types successfully fixed!")
        print(f"📋 Phase 3 Report Type Extractor should now properly load all patterns")
        print(f"🚀 Re-run Phase 3 pipeline test to measure dramatic improvement")
    else:
        print(f"\n❌ Failed to fix pattern format types")
        sys.exit(1)