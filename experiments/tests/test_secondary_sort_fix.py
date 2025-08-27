#!/usr/bin/env python3
"""
Test secondary sorting fix for Script 03
Validates that longer patterns match before shorter ones within same priority.
"""

import os
import sys
import logging
import importlib.util
from dotenv import load_dotenv

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

load_dotenv()

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

def import_module_from_path(module_name: str, file_path: str):
    """Import a module from a file path."""
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

def test_secondary_sort_fix():
    """Test that longer patterns match before shorter ones within same priority."""
    logger.info("=== Script 03 Secondary Sort Fix Test ===\n")
    
    # Import required modules
    parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    pattern_lib = import_module_from_path("pattern_library_manager_v1", 
                                        os.path.join(parent_dir, "00b_pattern_library_manager_v1.py"))
    script_03 = import_module_from_path("report_type_extractor_v2", 
                                      os.path.join(parent_dir, "03_report_type_extractor_v2.py"))
    
    # Initialize components
    pattern_manager = pattern_lib.PatternLibraryManager()
    report_extractor = script_03.MarketAwareReportTypeExtractor(pattern_manager)
    
    # Key test cases that were failing
    test_cases = [
        {
            "title": "Busbar Market Size, Share, Global Industry Analysis Report",
            "expected_report": "Market Size, Share, Global Industry Analysis Report",
            "before_fix": "Market Size, Share,"
        },
        {
            "title": "Fire Truck Market Size, Share, Growth, Industry Report",
            "expected_report": "Market Size, Share, Growth, Industry Report", 
            "before_fix": "Market Size, Share,"
        },
        {
            "title": "Surface Computing Market Size, Share, Trends Report", 
            "expected_report": "Market Size, Share, Trends Report",
            "before_fix": "Market Size, Share,"
        }
    ]
    
    results = []
    
    for i, case in enumerate(test_cases, 1):
        logger.info(f"Test {i}: {case['title']}")
        
        try:
            result = report_extractor.extract(case['title'])
            
            success = result.extracted_report_type == case['expected_report']
            
            logger.info(f"  Before Fix: '{case['before_fix']}'")
            logger.info(f"  Expected:   '{case['expected_report']}'")
            logger.info(f"  Actual:     '{result.extracted_report_type}'")
            logger.info(f"  Status:     {'✅ FIXED' if success else '❌ STILL BROKEN'}")
            logger.info(f"  Remaining:  '{result.title.strip()}'")
            
            results.append(success)
            
        except Exception as e:
            logger.error(f"  ERROR: {e}")
            results.append(False)
            
        logger.info("")
    
    # Summary
    passed = sum(results)
    total = len(results)
    
    logger.info("=== SUMMARY ===")
    logger.info(f"Tests Passed: {passed}/{total}")
    
    if passed == total:
        logger.info("🎉 Secondary sort fix is WORKING! Longer patterns now match first.")
    else:
        logger.info("⚠️ Secondary sort fix needs more work.")
    
    pattern_manager.close_connection()
    return passed == total

if __name__ == "__main__":
    success = test_secondary_sort_fix()
    sys.exit(0 if success else 1)