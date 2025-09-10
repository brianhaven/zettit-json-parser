#!/usr/bin/env python3
"""
Regression test for Issue #26 fix: Verify that the separator cleanup doesn't break existing functionality.

This script tests the fix with a variety of real market research titles to ensure:
1. The separator cleanup works for affected titles
2. Non-affected titles continue to work properly
3. Overall success rate remains at or above 90%
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
    
    output_dir = os.path.join(outputs_dir, f"{timestamp}_issue_26_regression_test")
    os.makedirs(output_dir, exist_ok=True)
    
    return output_dir

def test_regression():
    """Run regression test to ensure fix doesn't break existing functionality."""
    
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
    
    # Test cases including both problematic and normal titles
    test_cases = [
        # Problematic titles with & separators (should be cleaned)
        {
            "input": "Global Market & Size & Share & Report 2025",
            "expected_contains": ["Market", "Size", "Share", "Report"],
            "should_not_contain": ["&"],
            "type": "separator_cleanup"
        },
        {
            "input": "Market & Industry & Analysis & Forecast",
            "expected_contains": ["Market", "Industry", "Analysis"],
            "should_not_contain": ["&"],
            "type": "separator_cleanup"
        },
        # Normal titles (should work as before)
        {
            "input": "Global Automotive Market Analysis Report 2025",
            "expected_contains": ["Market", "Analysis", "Report"],
            "should_not_contain": ["&"],
            "type": "normal"
        },
        {
            "input": "APAC Personal Protective Equipment Market Study",
            "expected_contains": ["Market", "Study"],
            "should_not_contain": ["&"],
            "type": "normal"
        },
        {
            "input": "North America Healthcare Market Size and Forecast",
            "expected_contains": ["Market", "Size"],
            "should_not_contain": ["&"],
            "type": "normal"
        },
        {
            "input": "Europe Electric Vehicle Market Trends Report",
            "expected_contains": ["Market", "Trends", "Report"],
            "should_not_contain": ["&"],
            "type": "normal"
        },
        {
            "input": "Global Market Research and Analysis",
            "expected_contains": ["Market", "Research"],
            "should_not_contain": ["&"],
            "type": "normal_with_and"
        },
        {
            "input": "Market Size and Share Analysis",
            "expected_contains": ["Market", "Size"],
            "should_not_contain": ["&"],
            "type": "normal_with_and"
        },
        # Edge cases
        {
            "input": "Market Report",
            "expected_contains": ["Market", "Report"],
            "should_not_contain": ["&"],
            "type": "simple"
        },
        {
            "input": "Market Analysis",
            "expected_contains": ["Market", "Analysis"],
            "should_not_contain": ["&"],
            "type": "simple"
        }
    ]
    
    # Create output directory
    output_dir = create_test_output_directory()
    output_file = os.path.join(output_dir, "regression_test_results.txt")
    
    # Run tests
    results = []
    passed = 0
    failed = 0
    
    logger.info("=" * 60)
    logger.info("Issue #26 Fix - Regression Test")
    logger.info("=" * 60)
    
    with open(output_file, 'w') as f:
        f.write("Issue #26 Fix - Regression Test Results\n")
        f.write("=" * 60 + "\n")
        f.write(f"Test Date (PDT): {datetime.now(pytz.timezone('America/Los_Angeles')).strftime('%Y-%m-%d %H:%M:%S %Z')}\n")
        f.write(f"Test Date (UTC): {datetime.now(pytz.UTC).strftime('%Y-%m-%d %H:%M:%S %Z')}\n")
        f.write("=" * 60 + "\n\n")
        
        for i, test_case in enumerate(test_cases, 1):
            logger.info(f"\nTest Case {i} ({test_case['type']})")
            logger.info(f"Input: {test_case['input']}")
            
            # Extract report type
            result = report_extractor.extract(test_case['input'])
            
            # Check if extraction was successful
            if result.extracted_report_type:
                actual = result.extracted_report_type
                test_passed = True
                
                # Check expected content
                for expected_word in test_case['expected_contains']:
                    if expected_word not in actual:
                        test_passed = False
                        logger.error(f"  ✗ Missing expected word: '{expected_word}'")
                
                # Check unwanted content
                for unwanted in test_case['should_not_contain']:
                    if unwanted in actual:
                        test_passed = False
                        logger.error(f"  ✗ Contains unwanted character: '{unwanted}'")
                
                if test_passed:
                    status = "PASSED"
                    passed += 1
                    logger.info(f"  ✓ PASSED: '{actual}'")
                else:
                    status = "FAILED"
                    failed += 1
                    logger.error(f"  ✗ FAILED: '{actual}'")
                
                # Record result
                results.append({
                    "test": i,
                    "type": test_case['type'],
                    "input": test_case['input'],
                    "actual": actual,
                    "status": status,
                    "remaining": result.title if hasattr(result, 'title') else 'N/A'
                })
                
                # Write to file
                f.write(f"Test Case {i} ({test_case['type']}):\n")
                f.write(f"  Input:        {test_case['input']}\n")
                f.write(f"  Extracted:    {actual}\n")
                f.write(f"  Remaining:    {result.title if hasattr(result, 'title') else 'N/A'}\n")
                f.write(f"  Status:       {status}\n")
                f.write("-" * 40 + "\n")
            else:
                failed += 1
                logger.error(f"  ✗ FAILED: No report type extracted")
                f.write(f"Test Case {i} ({test_case['type']}):\n")
                f.write(f"  Input:        {test_case['input']}\n")
                f.write(f"  Status:       FAILED - No extraction\n")
                f.write("-" * 40 + "\n")
        
        # Calculate success rate
        total_tests = len(test_cases)
        success_rate = (passed / total_tests) * 100 if total_tests > 0 else 0
        
        # Summary
        logger.info("\n" + "=" * 60)
        logger.info(f"Regression Test Summary:")
        logger.info(f"  Total Tests: {total_tests}")
        logger.info(f"  Passed: {passed}")
        logger.info(f"  Failed: {failed}")
        logger.info(f"  Success Rate: {success_rate:.1f}%")
        
        if success_rate >= 90:
            logger.info("✓ SUCCESS: Regression test passed (>= 90% success rate)")
            logger.info("✓ Issue #26 fix is working without breaking existing functionality!")
        else:
            logger.warning(f"✗ WARNING: Success rate {success_rate:.1f}% is below 90% threshold")
        
        f.write("\n" + "=" * 60 + "\n")
        f.write("SUMMARY:\n")
        f.write(f"  Total Tests: {total_tests}\n")
        f.write(f"  Passed: {passed}\n")
        f.write(f"  Failed: {failed}\n")
        f.write(f"  Success Rate: {success_rate:.1f}%\n")
        f.write("\n")
        
        if success_rate >= 90:
            f.write("✓ SUCCESS: Regression test passed (>= 90% success rate)\n")
            f.write("✓ Issue #26 fix is working without breaking existing functionality!\n")
        else:
            f.write(f"✗ WARNING: Success rate {success_rate:.1f}% is below 90% threshold\n")
    
    logger.info(f"\nTest results saved to: {output_file}")
    return success_rate >= 90

if __name__ == "__main__":
    try:
        success = test_regression()
        sys.exit(0 if success else 1)
    except Exception as e:
        logger.error(f"Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)