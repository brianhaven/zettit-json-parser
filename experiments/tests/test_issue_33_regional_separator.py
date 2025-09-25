#!/usr/bin/env python3
"""
Test script for Git Issue #33: Regional Separator Word Cleanup Enhancement
Tests the current behavior and validates the fix for regional separator word handling.
"""

import os
import sys
import importlib.util
from datetime import datetime
from dotenv import load_dotenv

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

def test_issue_33_cases():
    """Test the specific cases from Issue #33."""

    # Import required modules
    parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    pattern_manager = import_module_from_path("pattern_library_manager",
                                             os.path.join(parent_dir, "00b_pattern_library_manager_v1.py"))
    script04 = import_module_from_path("geographic_detector",
                                       os.path.join(parent_dir, "04_geographic_entity_detector_v2.py"))

    # Initialize components
    pattern_lib_manager = pattern_manager.PatternLibraryManager(os.getenv('MONGODB_URI'))
    geo_detector = script04.GeographicEntityDetector(pattern_lib_manager)

    # Test cases from Issue #33
    test_cases = [
        {
            "input": "U.S. And Europe Digital Pathology",
            "expected": "Digital Pathology",
            "description": "Regional separator 'And' should be removed with regions"
        },
        {
            "input": "Asia Pacific And North America Energy Solutions",
            "expected": "Energy Solutions",
            "description": "Multi-region with 'And' separator"
        },
        {
            "input": "Europe And Middle East Healthcare",
            "expected": "Healthcare",
            "description": "Adjacent regions with 'And'"
        },
        {
            "input": "Canada And United States Market",
            "expected": "Market",
            "description": "Country-level regions with 'And'"
        },
        {
            "input": "APAC And EMEA Software Solutions",
            "expected": "Software Solutions",
            "description": "Acronym regions with 'And'"
        },
        {
            "input": "North America & Europe Technology",
            "expected": "Technology",
            "description": "Regions with '&' separator"
        },
        {
            "input": "Latin America Plus Asia Pacific Services",
            "expected": "Services",
            "description": "Regions with 'Plus' separator"
        }
    ]

    print("\n" + "="*80)
    print("Git Issue #33: Regional Separator Word Cleanup Enhancement Test")
    print("="*80)
    print(f"\nTest Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("\n" + "-"*80)
    print("CURRENT BEHAVIOR TEST (Before Fix)")
    print("-"*80)

    all_passed = True

    for i, test_case in enumerate(test_cases, 1):
        print(f"\nTest Case {i}: {test_case['description']}")
        print(f"Input:     '{test_case['input']}'")

        # Process with geographic entity detector
        result = geo_detector.extract_geographic_entities(test_case['input'])

        print(f"Regions:   {result.extracted_regions}")
        print(f"Output:    '{result.title}'")
        print(f"Expected:  '{test_case['expected']}'")

        if result.title == test_case['expected']:
            print("Status:    ✅ PASS")
        else:
            print("Status:    ❌ FAIL")
            all_passed = False

            # Show what went wrong
            if "And" in result.title or "and" in result.title.lower():
                print("Issue:     'And' separator left as artifact")
            elif "&" in result.title:
                print("Issue:     '&' separator left as artifact")
            elif "Plus" in result.title:
                print("Issue:     'Plus' separator left as artifact")

    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)

    if all_passed:
        print("\n✅ All test cases passed!")
    else:
        print("\n❌ Some test cases failed - Issue #33 fix needed")

    print("\nNext Steps:")
    print("1. Implement enhanced regional group detection")
    print("2. Add cohesive removal of regional groups with separators")
    print("3. Retest to confirm all cases pass")

if __name__ == "__main__":
    test_issue_33_cases()