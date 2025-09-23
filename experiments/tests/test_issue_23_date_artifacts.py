#!/usr/bin/env python3
"""
Test script for Issue #23: Date Artifact Cleanup Enhancement
Tests the 5-line regex enhancement added to Script 05's _apply_systematic_removal method

Test Cases:
1. Empty brackets after date removal
2. Empty parentheses after date removal
3. Double spaces from date removal
4. Orphaned connectors like "Forecast to" without date
"""

import os
import sys
from pathlib import Path
from datetime import datetime
import pytz
import json
import importlib.util
from typing import Dict, Any, List

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import modules dynamically
def import_module_from_path(module_name: str, file_path: str):
    """Import a module from a file path."""
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

# Create output directory
def create_organized_output_directory(script_name: str) -> str:
    """Create organized output directory with YYYY/MM/DD structure."""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    experiments_dir = os.path.dirname(script_dir)
    project_root = os.path.dirname(experiments_dir)
    outputs_dir = os.path.join(project_root, 'outputs')

    # Create timestamp in Pacific Time
    pdt = pytz.timezone('America/Los_Angeles')
    now = datetime.now(pdt)

    # Create YYYY/MM/DD directory structure
    year_dir = os.path.join(outputs_dir, now.strftime('%Y'))
    month_dir = os.path.join(year_dir, now.strftime('%m'))
    day_dir = os.path.join(month_dir, now.strftime('%d'))

    # Create timestamped subdirectory
    timestamp = now.strftime('%Y%m%d_%H%M%S')
    output_dir = os.path.join(day_dir, f"{timestamp}_{script_name}")
    os.makedirs(output_dir, exist_ok=True)

    return output_dir

# Create file header with dual timestamps
def create_file_header(script_name: str, description: str = "") -> str:
    """Create standardized file header with dual timestamps."""
    pdt = pytz.timezone('America/Los_Angeles')
    utc = pytz.timezone('UTC')
    now_pdt = datetime.now(pdt)
    now_utc = datetime.now(utc)

    header = f"""================================================================================
{script_name.upper()} - {description}
================================================================================
Analysis Date (PDT): {now_pdt.strftime('%Y-%m-%d %H:%M:%S')} PDT
Analysis Date (UTC): {now_utc.strftime('%Y-%m-%d %H:%M:%S')} UTC
================================================================================

"""
    return header

def main():
    """Test Issue #23 date artifact cleanup enhancement."""

    # Import Script 05
    parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    script05 = import_module_from_path("topic_extractor",
                                      os.path.join(parent_dir, "05_topic_extractor_v1.py"))

    # Create topic extractor instance (no DB needed for this test)
    topic_extractor = script05.TopicExtractor(pattern_library_manager=None)

    # Test cases from Issue #23
    test_cases = [
        {
            "id": "Case 1",
            "input": "AI in Healthcare Market []",
            "expected": "AI in Healthcare",
            "description": "Empty brackets after date removal"
        },
        {
            "id": "Case 2",
            "input": "Machine Learning Market ()",
            "expected": "Machine Learning",
            "description": "Empty parentheses after date removal"
        },
        {
            "id": "Case 3",
            "input": "Robotics  Market",
            "expected": "Robotics",
            "description": "Double spaces from date removal"
        },
        {
            "id": "Case 4",
            "input": "Blockchain Market, Forecast to",
            "expected": "Blockchain",
            "description": "Orphaned 'Forecast to' connector"
        },
        {
            "id": "Case 5",
            "input": "IoT Market Analysis to",
            "expected": "IoT",
            "description": "Orphaned 'to' connector at end"
        },
        {
            "id": "Case 6",
            "input": "5G Network Market through",
            "expected": "5G Network",
            "description": "Orphaned 'through' connector"
        },
        {
            "id": "Case 7",
            "input": "Cloud Computing Market till",
            "expected": "Cloud Computing",
            "description": "Orphaned 'till' connector"
        },
        {
            "id": "Case 8",
            "input": "Quantum Computing Market until",
            "expected": "Quantum Computing",
            "description": "Orphaned 'until' connector"
        },
        {
            "id": "Case 9",
            "input": "Edge Computing Market  ()  []",
            "expected": "Edge Computing",
            "description": "Multiple empty containers and spaces"
        },
        {
            "id": "Case 10",
            "input": "AR/VR Market, Forecast to  ()",
            "expected": "AR/VR",
            "description": "Combined artifacts"
        }
    ]

    # Create output directory
    output_dir = create_organized_output_directory("test_issue_23")

    # Test results
    results = []
    all_passed = True

    print("\n" + "="*80)
    print("TESTING ISSUE #23 DATE ARTIFACT CLEANUP ENHANCEMENT")
    print("="*80)

    for test_case in test_cases:
        # Process test case through _apply_systematic_removal
        processing_notes = []

        # Strip "Market" variants to simulate pipeline preprocessing
        test_input = test_case["input"]
        test_input = test_input.replace("Market Analysis", "")
        test_input = test_input.replace("Market", "")
        test_input = test_input.strip()

        # Apply systematic removal (which now includes artifact cleanup)
        # Create extracted_elements dict (empty for this test)
        extracted_elements = {
            'dates': [],
            'report_types': [],
            'regions': []
        }
        result = topic_extractor._apply_systematic_removal(
            test_input, extracted_elements, processing_notes
        )

        # Check if result matches expected
        passed = result == test_case["expected"]
        if not passed:
            all_passed = False

        # Store result
        test_result = {
            "test_id": test_case["id"],
            "description": test_case["description"],
            "input": test_case["input"],
            "preprocessed": test_input,
            "expected": test_case["expected"],
            "actual": result,
            "passed": passed,
            "processing_notes": processing_notes
        }
        results.append(test_result)

        # Print result
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"\n{status} - {test_case['id']}: {test_case['description']}")
        print(f"  Input:    '{test_case['input']}'")
        print(f"  Expected: '{test_case['expected']}'")
        print(f"  Actual:   '{result}'")
        if not passed:
            print(f"  ERROR: Output mismatch!")
            for note in processing_notes:
                print(f"    > {note}")

    # Write results to JSON file
    output_file = os.path.join(output_dir, "issue_23_test_results.json")
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump({
            "test_summary": {
                "total_tests": len(test_cases),
                "passed": sum(1 for r in results if r["passed"]),
                "failed": sum(1 for r in results if not r["passed"]),
                "all_passed": all_passed
            },
            "test_results": results
        }, f, indent=2)

    # Write human-readable report
    report_file = os.path.join(output_dir, "issue_23_test_report.txt")
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(create_file_header("Issue #23 Test Report", "Date Artifact Cleanup Enhancement"))
        f.write("\nTEST SUMMARY\n")
        f.write("="*80 + "\n")
        f.write(f"Total Tests: {len(test_cases)}\n")
        f.write(f"Passed: {sum(1 for r in results if r['passed'])}\n")
        f.write(f"Failed: {sum(1 for r in results if not r['passed'])}\n")
        f.write(f"Success Rate: {(sum(1 for r in results if r['passed']) / len(test_cases)) * 100:.1f}%\n\n")

        f.write("DETAILED RESULTS\n")
        f.write("="*80 + "\n")

        for result in results:
            status = "PASS" if result["passed"] else "FAIL"
            f.write(f"\n[{status}] {result['test_id']}: {result['description']}\n")
            f.write(f"  Input:    '{result['input']}'\n")
            f.write(f"  Expected: '{result['expected']}'\n")
            f.write(f"  Actual:   '{result['actual']}'\n")
            if result["processing_notes"]:
                f.write("  Processing Notes:\n")
                for note in result["processing_notes"]:
                    f.write(f"    - {note}\n")

    # Final summary
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    print(f"Total Tests: {len(test_cases)}")
    print(f"Passed: {sum(1 for r in results if r['passed'])}")
    print(f"Failed: {sum(1 for r in results if not r['passed'])}")
    print(f"Success Rate: {(sum(1 for r in results if r['passed']) / len(test_cases)) * 100:.1f}%")

    if all_passed:
        print("\n✓ ALL TESTS PASSED - Issue #23 fix is working correctly!")
    else:
        print("\n✗ Some tests failed - review the implementation")

    print(f"\nResults saved to: {output_dir}")

    return all_passed

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)