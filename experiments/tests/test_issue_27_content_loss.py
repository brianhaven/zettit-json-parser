#!/usr/bin/env python3
"""
Test script for Issue #27: Pre-Market Dictionary Terms Causing Content Loss

Tests the fix for Script 03 v4's content loss issue where topic keywords
are incorrectly removed when they match dictionary terms.
"""

import os
import sys
import logging
from datetime import datetime
import pytz
import json
from typing import List, Dict, Tuple

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def import_module_from_path(module_name: str, file_path: str):
    """Import a module from a specific file path."""
    import importlib.util
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

def test_issue_27_failing_cases():
    """Test the documented failing cases from Issue #27."""

    # Import required modules
    parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    pattern_manager = import_module_from_path("pattern_library_manager",
                                            os.path.join(parent_dir, "00b_pattern_library_manager_v1.py"))
    script03 = import_module_from_path("report_extractor",
                                     os.path.join(parent_dir, "03_report_type_extractor_v4.py"))

    # Initialize components
    from dotenv import load_dotenv
    load_dotenv()

    pattern_lib_manager = pattern_manager.PatternLibraryManager(os.getenv('MONGODB_URI'))
    report_extractor = script03.PureDictionaryReportTypeExtractor(pattern_lib_manager)

    # Test cases from Issue #27
    test_cases = [
        {
            "title": "Oil & Gas Data Management Market",
            "expected_report_type": "Market",
            "expected_topic": "Oil & Gas Data Management",
            "issue": "Currently loses 'Data Management' from topic"
        },
        {
            "title": "Data Monetization Market Outlook, Trends, Analysis",
            "expected_report_type": "Market Outlook Trends Analysis",
            "expected_topic": "Data Monetization",
            "issue": "Currently loses entire 'Data Monetization' topic"
        },
        {
            "title": "Europe Building Information Modeling Market Analysis Report, 2024",
            "expected_report_type": "Market Analysis Report",
            "expected_topic": "Europe Building Information Modeling",
            "issue": "May lose 'Information' or 'Modeling' from topic"
        },
        {
            "title": "Asia-Pacific Advanced Analytics Market Research Study",
            "expected_report_type": "Market Research Study",
            "expected_topic": "Asia-Pacific Advanced Analytics",
            "issue": "May lose 'Advanced' or 'Analytics' from topic"
        },
        {
            "title": "Global Food Processing Equipment Market Trends & Opportunities",
            "expected_report_type": "Market Trends Opportunities",
            "expected_topic": "Global Food Processing Equipment",
            "issue": "May lose 'Processing' from topic"
        }
    ]

    results = []

    print("\n" + "="*80)
    print("Testing Issue #27: Content Loss in Script 03 v4")
    print("="*80 + "\n")

    for i, test_case in enumerate(test_cases, 1):
        print(f"Test Case {i}: {test_case['title']}")
        print(f"Issue: {test_case['issue']}")

        # Extract report type
        result = report_extractor.extract(test_case['title'])

        # Check results
        passed = True
        status = "✓ PASS"

        if result.extracted_report_type != test_case['expected_report_type']:
            passed = False
            status = "✗ FAIL"
            print(f"  Report Type: {result.extracted_report_type} (Expected: {test_case['expected_report_type']}) ✗")
        else:
            print(f"  Report Type: {result.extracted_report_type} ✓")

        if result.title != test_case['expected_topic']:
            passed = False
            status = "✗ FAIL"
            print(f"  Topic: '{result.title}' (Expected: '{test_case['expected_topic']}') ✗")
        else:
            print(f"  Topic: '{result.title}' ✓")

        print(f"  Status: {status}")

        results.append({
            'test_case': i,
            'title': test_case['title'],
            'expected_report_type': test_case['expected_report_type'],
            'actual_report_type': result.extracted_report_type,
            'expected_topic': test_case['expected_topic'],
            'actual_topic': result.title,
            'passed': passed,
            'issue': test_case['issue']
        })

        print()

    # Summary
    passed_count = sum(1 for r in results if r['passed'])
    total_count = len(results)

    print("="*80)
    print(f"Summary: {passed_count}/{total_count} tests passed")
    print("="*80)

    return results

def create_output_directory(script_name: str) -> str:
    """Create organized output directory with YYYY/MM/DD structure."""
    # Get absolute path to outputs directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    experiments_dir = os.path.dirname(script_dir)
    project_root = os.path.dirname(experiments_dir)
    outputs_dir = os.path.join(project_root, 'outputs')

    # Create timestamp in Pacific Time
    pdt = pytz.timezone('America/Los_Angeles')
    now = datetime.now(pdt)

    # Create YYYY/MM/DD structure
    year_dir = os.path.join(outputs_dir, now.strftime('%Y'))
    month_dir = os.path.join(year_dir, now.strftime('%m'))
    day_dir = os.path.join(month_dir, now.strftime('%d'))

    # Create timestamped subdirectory
    timestamp = now.strftime('%Y%m%d_%H%M%S')
    output_dir = os.path.join(day_dir, f"{timestamp}_{script_name}")
    os.makedirs(output_dir, exist_ok=True)

    return output_dir

def save_test_results(results: List[Dict], output_dir: str):
    """Save test results to JSON file."""
    output_file = os.path.join(output_dir, "issue_27_test_results.json")

    # Add metadata
    pdt = pytz.timezone('America/Los_Angeles')
    now_pdt = datetime.now(pdt)
    now_utc = datetime.now(pytz.utc)

    output_data = {
        'test_metadata': {
            'issue': 'Issue #27: Pre-Market Dictionary Terms Causing Content Loss',
            'script': 'Script 03 v4: Pure Dictionary Report Type Extractor',
            'test_date_pdt': now_pdt.strftime('%Y-%m-%d %H:%M:%S PDT'),
            'test_date_utc': now_utc.strftime('%Y-%m-%d %H:%M:%S UTC'),
            'total_tests': len(results),
            'passed': sum(1 for r in results if r['passed']),
            'failed': sum(1 for r in results if not r['passed'])
        },
        'test_results': results
    }

    with open(output_file, 'w') as f:
        json.dump(output_data, f, indent=2)

    print(f"\nTest results saved to: {output_file}")

def main():
    """Main execution function."""
    try:
        # Create output directory
        output_dir = create_output_directory("issue_27_test")
        logger.info(f"Output directory created: {output_dir}")

        # Run tests
        results = test_issue_27_failing_cases()

        # Save results
        save_test_results(results, output_dir)

        # Return status based on results
        all_passed = all(r['passed'] for r in results)
        return 0 if all_passed else 1

    except Exception as e:
        logger.error(f"Error during testing: {e}", exc_info=True)
        return 1

if __name__ == "__main__":
    sys.exit(main())