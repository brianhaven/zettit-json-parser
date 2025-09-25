#!/usr/bin/env python3
"""
Comparison test for Git Issue #33: Regional Separator Word Cleanup Enhancement
Compares Script 04 v2 (current) vs v3 (enhanced) to validate the fix.
"""

import os
import sys
import json
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

def run_comparison_test():
    """Run comparison test between v2 and v3 implementations."""

    # Import required modules
    parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    # Import pattern library manager
    pattern_manager = import_module_from_path("pattern_library_manager",
                                             os.path.join(parent_dir, "00b_pattern_library_manager_v1.py"))

    # Import both versions of Script 04
    script04_v2 = import_module_from_path("geographic_detector_v2",
                                          os.path.join(parent_dir, "04_geographic_entity_detector_v2.py"))
    script04_v3 = import_module_from_path("geographic_detector_v3",
                                          os.path.join(parent_dir, "04_geographic_entity_detector_v3.py"))

    # Initialize components
    pattern_lib_manager = pattern_manager.PatternLibraryManager(os.getenv('MONGODB_URI'))

    # Initialize both detectors
    detector_v2 = script04_v2.GeographicEntityDetector(pattern_lib_manager)
    detector_v3 = script04_v3.GeographicEntityDetector(pattern_lib_manager)

    # Issue #33 specific test cases
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
        },
        {
            "input": "United States, Europe And Asia Manufacturing",
            "expected": "Manufacturing",
            "description": "Multiple regions with mixed separators"
        },
        {
            "input": "Middle East and North Africa Banking",
            "expected": "Banking",
            "description": "Lowercase 'and' separator"
        },
        {
            "input": "Europe Plus Middle East Plus Africa Retail",
            "expected": "Retail",
            "description": "Multiple 'Plus' separators"
        }
    ]

    print("\n" + "="*100)
    print("Git Issue #33: Regional Separator Word Cleanup Enhancement - COMPARISON TEST")
    print("="*100)
    print(f"\nTest Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # Track results
    v2_passes = 0
    v3_passes = 0
    comparison_results = []

    for i, test_case in enumerate(test_cases, 1):
        print("\n" + "-"*100)
        print(f"Test Case {i}: {test_case['description']}")
        print("-"*100)
        print(f"Input:          '{test_case['input']}'")
        print(f"Expected:       '{test_case['expected']}'")

        # Test v2 (current implementation)
        result_v2 = detector_v2.extract_geographic_entities(test_case['input'])
        v2_pass = result_v2.title == test_case['expected']
        if v2_pass:
            v2_passes += 1

        print(f"\nScript 04 v2:   '{result_v2.title}' {'✅ PASS' if v2_pass else '❌ FAIL'}")
        print(f"  - Regions:    {result_v2.extracted_regions}")
        print(f"  - Confidence: {result_v2.confidence:.3f}")

        # Test v3 (enhanced implementation)
        result_v3 = detector_v3.extract_geographic_entities(test_case['input'])
        v3_pass = result_v3.title == test_case['expected']
        if v3_pass:
            v3_passes += 1

        print(f"\nScript 04 v3:   '{result_v3.title}' {'✅ PASS' if v3_pass else '❌ FAIL'}")
        print(f"  - Regions:    {result_v3.extracted_regions}")
        print(f"  - Confidence: {result_v3.confidence:.3f}")

        # Improvement status
        if not v2_pass and v3_pass:
            print(f"\n🎯 IMPROVEMENT: v3 fixed this case!")
        elif v2_pass and v3_pass:
            print(f"\n✅ CONSISTENT: Both versions handle this correctly")
        elif not v2_pass and not v3_pass:
            print(f"\n⚠️  NEEDS WORK: Neither version handles this case")
        else:
            print(f"\n⚠️  REGRESSION: v2 worked but v3 failed")

        # Store comparison results
        comparison_results.append({
            "test_case": i,
            "description": test_case["description"],
            "input": test_case["input"],
            "expected": test_case["expected"],
            "v2_output": result_v2.title,
            "v2_regions": result_v2.extracted_regions,
            "v2_confidence": result_v2.confidence,
            "v2_pass": v2_pass,
            "v3_output": result_v3.title,
            "v3_regions": result_v3.extracted_regions,
            "v3_confidence": result_v3.confidence,
            "v3_pass": v3_pass,
            "improved": not v2_pass and v3_pass
        })

    # Print summary
    print("\n" + "="*100)
    print("TEST SUMMARY")
    print("="*100)

    print(f"\nScript 04 v2 (Current): {v2_passes}/{len(test_cases)} passed ({v2_passes/len(test_cases)*100:.1f}%)")
    print(f"Script 04 v3 (Enhanced): {v3_passes}/{len(test_cases)} passed ({v3_passes/len(test_cases)*100:.1f}%)")

    improvements = sum(1 for r in comparison_results if r["improved"])
    print(f"\nImprovements: {improvements} cases fixed by v3")

    if v3_passes > v2_passes:
        print(f"\n✅ SUCCESS: v3 shows {v3_passes - v2_passes} improvements over v2!")
    elif v3_passes == v2_passes:
        print(f"\n✅ STABLE: v3 maintains same success rate as v2")
    else:
        print(f"\n⚠️  WARNING: v3 has {v2_passes - v3_passes} regressions from v2")

    # Save results to file
    output_dir = os.path.join(parent_dir, "../outputs/issue_33_comparison")
    os.makedirs(output_dir, exist_ok=True)

    output_file = os.path.join(output_dir, f"comparison_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump({
            "test_date": datetime.now().isoformat(),
            "total_cases": len(test_cases),
            "v2_passes": v2_passes,
            "v3_passes": v3_passes,
            "improvements": improvements,
            "results": comparison_results
        }, f, indent=2)

    print(f"\nDetailed results saved to: {output_file}")

    # Check if Issue #33 is resolved
    issue_33_cases = ["U.S. And Europe Digital Pathology", "Latin America Plus Asia Pacific Services"]
    issue_33_fixed = all(
        r["v3_pass"] and not r["v2_pass"]
        for r in comparison_results
        if r["input"] in issue_33_cases
    )

    if issue_33_fixed:
        print("\n" + "="*100)
        print("🎉 Git Issue #33 RESOLVED!")
        print("="*100)
        print("The enhanced v3 implementation successfully handles regional separator words.")
    else:
        print("\n" + "="*100)
        print("⚠️  Git Issue #33 - Further work needed")
        print("="*100)

if __name__ == "__main__":
    run_comparison_test()