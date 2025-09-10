#!/usr/bin/env python3
"""
Test script for Issue #26: Verify separator artifact cleanup in Script 03 v4.

This script tests that the fix properly removes "&" separators from reconstructed
report types while preserving the correct word boundaries.
"""

import os
import sys
import importlib.util
from pathlib import Path
from dotenv import load_dotenv
from pymongo import MongoClient
import logging
from datetime import datetime
import pytz

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Load environment variables
load_dotenv()

def import_module_from_path(module_name: str, file_path: str):
    """Import a module from a file path."""
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

def create_test_output_directory():
    """Create timestamped output directory for test results."""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    experiments_dir = os.path.dirname(script_dir)
    project_root = os.path.dirname(experiments_dir)
    outputs_dir = os.path.join(project_root, 'outputs')
    
    pdt = pytz.timezone('America/Los_Angeles')
    timestamp = datetime.now(pdt).strftime('%Y%m%d_%H%M%S')
    
    output_dir = os.path.join(outputs_dir, f"{timestamp}_issue_26_separator_fix_test")
    os.makedirs(output_dir, exist_ok=True)
    
    return output_dir

def test_separator_cleanup():
    """Test that separator artifacts are properly cleaned from report types."""
    
    # Import modules
    parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    # Import PatternLibraryManager
    pattern_manager = import_module_from_path("pattern_library_manager",
                                            os.path.join(parent_dir, "00b_pattern_library_manager_v1.py"))
    
    # Import Script 03 v4
    script03 = import_module_from_path("report_extractor",
                                      os.path.join(parent_dir, "03_report_type_extractor_v4.py"))
    
    # Initialize components
    pattern_lib_manager = pattern_manager.PatternLibraryManager(os.getenv('MONGODB_URI'))
    report_extractor = script03.PureDictionaryReportTypeExtractor(pattern_lib_manager)
    
    # Test cases from Issue #26
    test_cases = [
        {
            "input": "Market & Size & Share & Report",
            "expected": "Market Size Share Report",
            "description": "Multiple & separators"
        },
        {
            "input": "Market & Size & Trends & Report",
            "expected": "Market Size Trends Report",
            "description": "Multiple & separators with Trends"
        },
        {
            "input": "Market & Size & Share & Industry & Report",
            "expected": "Market Size Share Industry Report",
            "description": "Multiple & separators with Industry"
        },
        {
            "input": "Market & Size & Share & Analysis & Report",
            "expected": "Market Size Share Analysis Report",
            "description": "Multiple & separators with Analysis"
        },
        {
            "input": "Market & Size & Share & Growth & Analysis & Report",
            "expected": "Market Size Share Growth Analysis Report",
            "description": "Multiple & separators with Growth Analysis"
        },
        {
            "input": "Market Size & Outlook & Statistics",
            "expected": "Market Size Outlook Statistics",
            "description": "Mixed spacing with & separators"
        }
    ]
    
    # Create output directory
    output_dir = create_test_output_directory()
    output_file = os.path.join(output_dir, "test_results.txt")
    
    # Run tests
    results = []
    passed = 0
    failed = 0
    
    logger.info("=" * 60)
    logger.info("Testing Issue #26 Separator Cleanup Fix")
    logger.info("=" * 60)
    
    with open(output_file, 'w') as f:
        f.write("Issue #26 Separator Cleanup Test Results\n")
        f.write("=" * 60 + "\n")
        f.write(f"Test Date (PDT): {datetime.now(pytz.timezone('America/Los_Angeles')).strftime('%Y-%m-%d %H:%M:%S %Z')}\n")
        f.write(f"Test Date (UTC): {datetime.now(pytz.UTC).strftime('%Y-%m-%d %H:%M:%S %Z')}\n")
        f.write("=" * 60 + "\n\n")
        
        for i, test_case in enumerate(test_cases, 1):
            logger.info(f"\nTest Case {i}: {test_case['description']}")
            logger.info(f"Input: {test_case['input']}")
            
            # Extract report type
            result = report_extractor.extract(test_case['input'])
            
            # Check if extraction was successful
            if result.extracted_report_type:
                actual = result.extracted_report_type
                expected = test_case['expected']
                
                # Check if cleanup worked
                if actual == expected:
                    status = "PASSED"
                    passed += 1
                    logger.info(f"✓ PASSED: Got expected '{expected}'")
                else:
                    status = "FAILED"
                    failed += 1
                    logger.error(f"✗ FAILED: Expected '{expected}', got '{actual}'")
                
                # Record result
                results.append({
                    "test": i,
                    "input": test_case['input'],
                    "expected": expected,
                    "actual": actual,
                    "status": status,
                    "description": test_case['description']
                })
                
                # Write to file
                f.write(f"Test Case {i}: {test_case['description']}\n")
                f.write(f"  Input:    {test_case['input']}\n")
                f.write(f"  Expected: {expected}\n")
                f.write(f"  Actual:   {actual}\n")
                f.write(f"  Status:   {status}\n")
                f.write("-" * 40 + "\n")
            else:
                failed += 1
                logger.error(f"✗ FAILED: No report type extracted")
                f.write(f"Test Case {i}: {test_case['description']}\n")
                f.write(f"  Input:    {test_case['input']}\n")
                f.write(f"  Status:   FAILED - No extraction\n")
                f.write("-" * 40 + "\n")
        
        # Summary
        logger.info("\n" + "=" * 60)
        logger.info(f"Test Summary: {passed}/{len(test_cases)} tests passed")
        if passed == len(test_cases):
            logger.info("✓ ALL TESTS PASSED - Issue #26 fix is working correctly!")
        else:
            logger.warning(f"✗ {failed} tests failed - Review needed")
        
        f.write("\n" + "=" * 60 + "\n")
        f.write(f"Summary: {passed}/{len(test_cases)} tests passed\n")
        if passed == len(test_cases):
            f.write("✓ ALL TESTS PASSED - Issue #26 fix is working correctly!\n")
        else:
            f.write(f"✗ {failed} tests failed - Review needed\n")
    
    logger.info(f"\nTest results saved to: {output_file}")
    return passed == len(test_cases)

if __name__ == "__main__":
    try:
        success = test_separator_cleanup()
        sys.exit(0 if success else 1)
    except Exception as e:
        logger.error(f"Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)