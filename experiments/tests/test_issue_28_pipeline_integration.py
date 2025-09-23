#!/usr/bin/env python3
"""
Full Pipeline Test for Issue #28: 'Market in' Context Integration
Tests the complete processing pipeline to verify orphaned preposition cleanup.
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

def process_title_through_pipeline(title: str, components: Dict) -> Dict:
    """Process a title through the complete pipeline."""

    result = {
        "original_title": title,
        "stages": {}
    }

    # Stage 1: Market Term Classification
    market_result = components["market_classifier"].classify(title)
    result["stages"]["01_market_classification"] = {
        "market_term_type": market_result.market_type,  # Fixed attribute name
        "confidence": market_result.confidence,
        "remaining": market_result.title
    }

    # Stage 2: Date Extraction
    date_result = components["date_extractor"].extract(market_result.title)
    result["stages"]["02_date_extraction"] = {
        "extracted_date": date_result.extracted_date_range,
        "confidence": date_result.confidence,
        "remaining": date_result.title
    }

    # Stage 3: Report Type Extraction (v4 Pure Dictionary)
    report_result = components["report_extractor"].extract(
        date_result.title,
        market_term_type=market_result.market_type  # Fixed attribute name
    )
    result["stages"]["03_report_type"] = {
        "extracted_report_type": report_result.extracted_report_type,
        "confidence": report_result.confidence,
        "remaining": report_result.title
    }

    # Stage 4: Geographic Entity Detection (with Issue #28 fix)
    geo_result = components["geo_detector"].extract_geographic_entities(report_result.title)
    result["stages"]["04_geographic_detection"] = {
        "extracted_regions": geo_result.extracted_regions,
        "confidence": geo_result.confidence,
        "remaining": geo_result.title  # This should have orphaned prepositions cleaned
    }

    # Final topic is what remains after all extraction
    result["final_topic"] = geo_result.title

    return result

def run_pipeline_test():
    """Run full pipeline test for Issue #28."""

    # Import required modules
    parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    # Import pattern library manager
    pattern_manager = import_module_from_path("pattern_library_manager",
                                             os.path.join(parent_dir, "00b_pattern_library_manager_v1.py"))

    # Import pipeline scripts
    script01 = import_module_from_path("market_classifier",
                                       os.path.join(parent_dir, "01_market_term_classifier_v1.py"))
    script02 = import_module_from_path("date_extractor",
                                       os.path.join(parent_dir, "02_date_extractor_v1.py"))
    script03 = import_module_from_path("report_extractor",
                                       os.path.join(parent_dir, "03_report_type_extractor_v4.py"))
    script04 = import_module_from_path("geographic_detector",
                                       os.path.join(parent_dir, "04_geographic_entity_detector_v2.py"))

    # Import output directory manager
    output_manager = import_module_from_path("output_manager",
                                            os.path.join(parent_dir, "00c_output_directory_manager_v1.py"))

    # Initialize pattern library manager
    pattern_lib_manager = pattern_manager.PatternLibraryManager(os.getenv('MONGODB_URI'))

    # Initialize pipeline components
    components = {
        "market_classifier": script01.MarketTermClassifier(pattern_lib_manager),
        "date_extractor": script02.EnhancedDateExtractor(pattern_lib_manager),
        "report_extractor": script03.PureDictionaryReportTypeExtractor(pattern_lib_manager),
        "geo_detector": script04.GeographicEntityDetector(pattern_lib_manager)
    }

    # Test cases specifically for Issue #28
    test_cases = [
        {
            "title": "Retail Market in Singapore - Size, Outlook & Statistics",
            "expected_topic": "Retail",
            "description": "Main Issue #28 case from GitHub issue"
        },
        {
            "title": "Technology Market in Asia Pacific, 2025-2030",
            "expected_topic": "Technology",
            "description": "Market in with date range"
        },
        {
            "title": "Artificial Intelligence (AI) Market in Automotive Outlook & Trends, 2025-2035",
            "expected_topic": "Artificial Intelligence (AI) in Automotive",
            "description": "Market in with industry context (not geographic)"
        },
        {
            "title": "Healthcare Market for Europe Analysis and Forecast, 2024-2029",
            "expected_topic": "Healthcare",
            "description": "Market for pattern with Europe"
        },
        {
            "title": "APAC Personal Protective Equipment Market Analysis, 2024-2029",
            "expected_topic": "Personal Protective Equipment",
            "description": "Standard pattern (no orphaned prepositions)"
        },
        {
            "title": "Global Automotive Components Market by Region, 2023-2028",
            "expected_topic": "Automotive Components",
            "description": "Market by pattern"
        },
        {
            "title": "Software Solutions Market of United States Report, 2025",
            "expected_topic": "Software Solutions",
            "description": "Market of pattern"
        }
    ]

    print("\n" + "="*80)
    print("Full Pipeline Test for Issue #28: 'Market in' Context Integration")
    print("="*80 + "\n")

    results = []

    for test_case in test_cases:
        title = test_case["title"]
        expected = test_case["expected_topic"]
        description = test_case["description"]

        print(f"Processing: {description}")
        print(f"Input: '{title}'")

        # Process through pipeline
        pipeline_result = process_title_through_pipeline(title, components)
        actual_topic = pipeline_result["final_topic"]

        # Check success
        success = actual_topic == expected

        # Store result
        test_result = {
            "title": title,
            "expected_topic": expected,
            "actual_topic": actual_topic,
            "success": success,
            "description": description,
            "pipeline_stages": pipeline_result["stages"]
        }
        results.append(test_result)

        # Print result
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"Expected Topic: '{expected}'")
        print(f"Actual Topic: '{actual_topic}'")
        print(f"Result: {status}")

        # Show pipeline stages for failures
        if not success:
            print("\nPipeline Stages:")
            for stage, data in pipeline_result["stages"].items():
                print(f"  {stage}:")
                for key, value in data.items():
                    print(f"    {key}: {value}")

        print("-" * 40 + "\n")

    # Summary
    passed = sum(1 for r in results if r["success"])
    total = len(results)

    print("="*80)
    print(f"Test Summary: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
    if passed == total:
        print("✅ Issue #28 is RESOLVED! All tests passed.")
    else:
        print(f"⚠️  {total - passed} test(s) still failing.")
    print("="*80 + "\n")

    # Create output directory and save results
    output_dir = output_manager.create_organized_output_directory("issue_28_pipeline_test")

    # Save detailed results
    output_file = os.path.join(output_dir, "issue_28_pipeline_results.json")
    with open(output_file, 'w') as f:
        json.dump({
            "test_date": datetime.now().isoformat(),
            "issue": "Issue #28: 'Market in' Context Integration",
            "total_tests": total,
            "passed": passed,
            "success_rate": f"{passed/total*100:.1f}%",
            "resolved": passed == total,
            "test_results": results
        }, f, indent=2)

    print(f"Detailed results saved to: {output_file}")

    # Create summary report
    summary_file = os.path.join(output_dir, "issue_28_summary.txt")
    with open(summary_file, 'w') as f:
        f.write(output_manager.create_output_file_header("Issue #28 Resolution Test",
                                                         "Orphaned Preposition Cleanup Fix Validation"))
        f.write("\n\n")
        f.write("ISSUE #28 RESOLUTION TEST SUMMARY\n")
        f.write("="*60 + "\n\n")

        f.write(f"Test Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Total Tests: {total}\n")
        f.write(f"Passed: {passed}\n")
        f.write(f"Failed: {total - passed}\n")
        f.write(f"Success Rate: {passed/total*100:.1f}%\n")
        f.write(f"Status: {'✅ RESOLVED' if passed == total else '⚠️  PARTIALLY RESOLVED'}\n\n")

        f.write("Test Results:\n")
        f.write("-"*60 + "\n")
        for result in results:
            status = "✅" if result["success"] else "❌"
            f.write(f"{status} {result['description']}\n")
            f.write(f"   Title: {result['title']}\n")
            f.write(f"   Expected: '{result['expected_topic']}'\n")
            f.write(f"   Actual: '{result['actual_topic']}'\n\n")

        f.write("\nFIX IMPLEMENTATION:\n")
        f.write("-"*60 + "\n")
        f.write("Modified: experiments/04_geographic_entity_detector_v2.py\n")
        f.write("Method: cleanup_remaining_text()\n")
        f.write("Change: Added regex patterns to remove orphaned prepositions:\n")
        f.write("  - End of text: r'\\s+(in|for|by|of|at|to|with|from)\\s*$'\n")
        f.write("  - Start of text: r'^(in|for|by|of|at|to|with|from)\\s+'\n\n")

        f.write("This fix ensures that when geographic entities are removed,\n")
        f.write("any orphaned prepositions are also cleaned up, resulting in\n")
        f.write("clean, predictable topic extraction.\n")

    print(f"Summary report saved to: {summary_file}")

    return passed == total

if __name__ == "__main__":
    try:
        success = run_pipeline_test()
        exit_code = 0 if success else 1
        sys.exit(exit_code)
    except Exception as e:
        logger.error(f"Pipeline test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)