#!/usr/bin/env python3
"""
Debug date extraction for specific problematic title
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

def test_date_extraction_debug():
    """Debug date extraction for the failing title."""
    logger.info("=== Date Extraction Debug Test ===\n")
    
    # Import required modules
    parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    pattern_lib = import_module_from_path("pattern_library_manager_v1", 
                                        os.path.join(parent_dir, "00b_pattern_library_manager_v1.py"))
    script_02 = import_module_from_path("date_extractor_v1", 
                                      os.path.join(parent_dir, "02_date_extractor_v1.py"))
    
    # Initialize components
    pattern_manager = pattern_lib.PatternLibraryManager()
    date_extractor = script_02.EnhancedDateExtractor(pattern_manager)
    
    # Test case that's failing in the pipeline
    test_title = "Wood Preservatives Market Size, Share, Growth Report 2030"
    
    logger.info(f"Original Title: {test_title}")
    logger.info("")
    
    # Test date extraction
    logger.info("=== DATE EXTRACTION TEST ===")
    result = date_extractor.extract(test_title)
    
    logger.info(f"Extracted Date: '{result.extracted_date_range}'")
    logger.info(f"Cleaned Title: '{result.cleaned_title}'")
    logger.info(f"Status: {'✅ SUCCESS' if result.extracted_date_range else '❌ NO DATE FOUND'}")
    logger.info("")
    
    # Check what should happen in pipeline
    expected_cleaned = test_title.replace(" 2030", "")
    actual_cleaned = result.cleaned_title
    
    logger.info("=== PIPELINE IMPACT ===")
    logger.info(f"Expected Cleaned: '{expected_cleaned}'")
    logger.info(f"Actual Cleaned:   '{actual_cleaned}'")
    logger.info(f"Match: {'✅ CORRECT' if actual_cleaned == expected_cleaned else '❌ MISMATCH'}")
    
    pattern_manager.close_connection()
    
    return result.extracted_date_range is not None

if __name__ == "__main__":
    success = test_date_extraction_debug()
    sys.exit(0 if success else 1)