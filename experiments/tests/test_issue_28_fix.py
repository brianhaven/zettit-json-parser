#!/usr/bin/env python3
"""
Test script for verifying Issue #28 fix: Orphaned Preposition Cleanup
Tests that geographic removal properly cleans up orphaned prepositions.
"""

import os
import sys
import json
import logging
import importlib.util
from datetime import datetime
from dotenv import load_dotenv
from typing import Dict, List

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def import_module_from_path(module_name: str, file_path: str):
    """Import a module from a file path."""
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

def test_orphaned_preposition_cleanup():
    """Test Issue #28 fix for orphaned preposition cleanup."""

    # Import required modules
    parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    # Import pattern library manager
    pattern_manager = import_module_from_path("pattern_library_manager",
                                             os.path.join(parent_dir, "00b_pattern_library_manager_v1.py"))

    # Import geographic entity detector
    script04 = import_module_from_path("geographic_detector",
                                       os.path.join(parent_dir, "04_geographic_entity_detector_v2.py"))

    # Import output directory manager
    output_manager = import_module_from_path("output_manager",
                                            os.path.join(parent_dir, "00c_output_directory_manager_v1.py"))

    # Initialize pattern library manager
    pattern_lib_manager = pattern_manager.PatternLibraryManager(os.getenv('MONGODB_URI'))

    # Initialize geographic detector
    geo_detector = script04.GeographicEntityDetector(pattern_lib_manager)

    # Test cases for Issue #28
    test_cases = [
        {
            "input": "Retail in Singapore",
            "expected_topic": "Retail",
            "description": "Main Issue #28 case - 'Market in' pattern with Singapore"
        },
        {
            "input": "Technology in Asia Pacific",
            "expected_topic": "Technology",
            "description": "Technology market in region"
        },
        {
            "input": "Advanced Materials in Aerospace",
            "expected_topic": "Advanced Materials",
            "description": "Materials market (no geographic entity)"
        },
        {
            "input": "Healthcare Services for Europe",
            "expected_topic": "Healthcare Services",
            "description": "Market for pattern with Europe"
        },
        {
            "input": "Automotive Components by Japan",
            "expected_topic": "Automotive Components",
            "description": "Market by pattern with Japan"
        },
        {
            "input": "Software Solutions of United States",
            "expected_topic": "Software Solutions",
            "description": "Market of pattern with United States"
        },
        {
            "input": "Personal Protective Equipment",
            "expected_topic": "Personal Protective Equipment",
            "description": "Standard case without prepositions"
        },
        {
            "input": "in Technology",
            "expected_topic": "Technology",
            "description": "Orphaned preposition at start"
        },
        {
            "input": "Manufacturing in",
            "expected_topic": "Manufacturing",
            "description": "Orphaned preposition at end"
        },
        {
            "input": "Global Market for Advanced Materials in Aerospace",
            "expected_topic": "Advanced Materials",
            "description": "Complex case with 'for' and 'in'"
        }
    ]

    results = []

    print("\n" + "="*80)
    print("Testing Issue #28 Fix: Orphaned Preposition Cleanup")
    print("="*80 + "\n")

    for test_case in test_cases:
        input_text = test_case["input"]
        expected = test_case["expected_topic"]
        description = test_case["description"]

        # Extract geographic entities
        result = geo_detector.extract_geographic_entities(input_text)

        # The remaining text after geographic extraction should have orphaned prepositions cleaned
        actual_topic = result.title

        # Check if fix works
        success = actual_topic == expected

        test_result = {
            "input": input_text,
            "expected": expected,
            "actual": actual_topic,
            "extracted_regions": result.extracted_regions,
            "success": success,
            "description": description
        }

        results.append(test_result)

        # Print result
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status}: {description}")
        print(f"  Input: '{input_text}'")
        print(f"  Expected: '{expected}'")
        print(f"  Actual: '{actual_topic}'")
        if result.extracted_regions:
            print(f"  Extracted Regions: {result.extracted_regions}")
        print()

    # Summary
    passed = sum(1 for r in results if r["success"])
    total = len(results)

    print("\n" + "="*80)
    print(f"Test Summary: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
    print("="*80 + "\n")

    # Create output directory and save results
    output_dir = output_manager.create_organized_output_directory("test_issue_28_fix")

    # Save test results
    output_file = os.path.join(output_dir, "issue_28_test_results.json")
    with open(output_file, 'w') as f:
        json.dump({
            "test_date": datetime.now().isoformat(),
            "issue": "Issue #28: Orphaned Preposition Cleanup",
            "total_tests": total,
            "passed": passed,
            "success_rate": f"{passed/total*100:.1f}%",
            "test_cases": results
        }, f, indent=2)

    print(f"Test results saved to: {output_file}")

    # Return success status
    return passed == total

if __name__ == "__main__":
    try:
        success = test_orphaned_preposition_cleanup()
        exit_code = 0 if success else 1
        sys.exit(exit_code)
    except Exception as e:
        logger.error(f"Test failed with error: {e}")
        sys.exit(1)