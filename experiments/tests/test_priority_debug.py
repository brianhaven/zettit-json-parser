#!/usr/bin/env python3
"""
Debug script to test specific priority ordering issue
Testing "Wood Preservatives Market Size, Share, Growth Report 2030"
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

def test_priority_debug():
    """Debug the specific priority ordering issue."""
    logger.info("=== Priority Debug Test ===\n")
    
    # Import required modules
    parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    pattern_lib = import_module_from_path("pattern_library_manager_v1", 
                                        os.path.join(parent_dir, "00b_pattern_library_manager_v1.py"))
    script_03 = import_module_from_path("report_type_extractor_v2", 
                                      os.path.join(parent_dir, "03_report_type_extractor_v2.py"))
    
    # Initialize components
    pattern_manager = pattern_lib.PatternLibraryManager()
    report_extractor = script_03.MarketAwareReportTypeExtractor(pattern_manager)
    
    # Test case that's failing
    test_title = "Wood Preservatives Market Size, Share, Growth Report 2030"
    after_date_removal = "Wood Preservatives Market Size, Share, Growth Report"
    
    logger.info(f"Original Title: {test_title}")
    logger.info(f"After Date Removal: {after_date_removal}")
    logger.info("")
    
    # Check what patterns are loaded in compound_type
    logger.info("=== COMPOUND TYPE PATTERNS (first 10) ===")
    for i, pattern in enumerate(report_extractor.compound_type_patterns[:10]):
        logger.info(f"{i+1:2d}. Priority {pattern.get('priority', '?')} | {pattern.get('term', 'NO_TERM')} | Pattern: {pattern.get('pattern', 'NO_PATTERN')[:60]}")
    logger.info("")
    
    # Test the extraction
    logger.info("=== EXTRACTION TEST ===")
    result = report_extractor.extract(test_title)
    
    logger.info(f"Extracted Report Type: '{result.extracted_report_type}'")
    logger.info(f"Expected: 'Market Size, Share, Growth Report'")
    logger.info(f"Status: {'✅ SUCCESS' if result.extracted_report_type == 'Market Size, Share, Growth Report' else '❌ FAILED'}")
    
    pattern_manager.close_connection()
    
    return result.extracted_report_type == 'Market Size, Share, Growth Report'

if __name__ == "__main__":
    success = test_priority_debug()
    sys.exit(0 if success else 1)