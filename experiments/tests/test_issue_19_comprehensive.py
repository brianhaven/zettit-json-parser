#!/usr/bin/env python3
"""
Comprehensive test for GitHub Issue #19: Ampersand and Symbol Preservation
Tests edge cases and validates the fix across the entire pipeline.
"""

import sys
import os
import json
import logging
from datetime import datetime
from pathlib import Path
import pytz
from typing import Dict, List, Tuple
import importlib.util
from dotenv import load_dotenv

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
    ]
)
logger = logging.getLogger(__name__)

# Dynamic imports
def import_module_from_path(module_name: str, file_path: str):
    """Import a module from a file path."""
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

def create_organized_output_directory(script_name: str) -> str:
    """Create organized output directory with YYYY/MM/DD structure."""
    parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    output_manager = import_module_from_path("output_manager",
                                           os.path.join(parent_dir, "00c_output_directory_manager_v1.py"))
    return output_manager.create_organized_output_directory(script_name)

def create_output_file_header(script_name: str, description: str = "") -> str:
    """Create standardized file header with dual timestamps."""
    parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    output_manager = import_module_from_path("output_manager",
                                           os.path.join(parent_dir, "00c_output_directory_manager_v1.py"))
    return output_manager.create_output_file_header(script_name, description)

def run_pipeline(title: str, components: Dict):
    """Run the complete pipeline on a title."""
    # Step 1: Market classification
    market_result = components['market_classifier'].classify(title)

    # Step 2: Date extraction
    date_result = components['date_extractor'].extract(market_result.title)

    # Step 3: Report type extraction
    report_result = components['report_extractor'].extract(
        date_result.title,
        market_term_type=market_result.market_type
    )

    # Step 4: Geographic detection
    geo_result = components['geo_detector'].extract_geographic_entities(report_result.title)

    return {
        'original_title': title,
        'market_type': market_result.market_type,
        'date_extracted': date_result.extracted_date_range,
        'report_type': report_result.extracted_report_type,
        'regions': geo_result.extracted_regions,
        'final_topic': geo_result.title,
        'pipeline_stages': {
            'after_market': market_result.title,
            'after_date': date_result.title,
            'after_report': report_result.title,
            'after_geo': geo_result.title
        }
    }

def test_comprehensive_symbol_preservation():
    """Run comprehensive tests for symbol preservation."""

    logger.info("=" * 80)
    logger.info("Comprehensive Symbol Preservation Test for Issue #19")
    logger.info("=" * 80)

    # Import and initialize components
    parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    try:
        # Import modules
        pattern_manager = import_module_from_path("pattern_library_manager",
                                                os.path.join(parent_dir, "00b_pattern_library_manager_v1.py"))
        script01 = import_module_from_path("market_classifier",
                                         os.path.join(parent_dir, "01_market_term_classifier_v1.py"))
        script02 = import_module_from_path("date_extractor",
                                         os.path.join(parent_dir, "02_date_extractor_v1.py"))
        script03 = import_module_from_path("report_extractor",
                                         os.path.join(parent_dir, "03_report_type_extractor_v4.py"))
        script04 = import_module_from_path("geo_detector",
                                         os.path.join(parent_dir, "04_geographic_entity_detector_v2.py"))

        # Initialize components
        pattern_lib_manager = pattern_manager.PatternLibraryManager(os.getenv('MONGODB_URI'))

        components = {
            'market_classifier': script01.MarketTermClassifier(pattern_lib_manager),
            'date_extractor': script02.EnhancedDateExtractor(pattern_lib_manager),
            'report_extractor': script03.PureDictionaryReportTypeExtractor(pattern_lib_manager),
            'geo_detector': script04.GeographicEntityDetector(pattern_lib_manager)
        }

        logger.info("✓ All components initialized successfully")

    except Exception as e:
        logger.error(f"Failed to initialize components: {e}")
        return False

    # Define comprehensive test cases
    test_suites = {
        "Ampersand Cases": [
            ("Oil & Gas Market Report, 2025", "Oil & Gas"),
            ("Food & Beverage Market Analysis", "Food & Beverage"),
            ("M&A Market Outlook, 2030", "M&A"),
            ("R&D Market for Science & Technology", "R&D for Science & Technology"),
            ("Health & Wellness Market In Fitness & Nutrition", "Health & Wellness in Fitness & Nutrition"),
        ],
        "Plus Symbol Cases": [
            ("Technology + Innovation Market Study", "Technology + Innovation"),
            ("Design + Manufacturing Market Report", "Design + Manufacturing"),
            ("Sales + Marketing Market Analysis", "Sales + Marketing"),
        ],
        "Multiple Symbols": [
            ("IT & Software + Hardware Market Report", "IT & Software + Hardware"),
            ("Food & Beverage + Hotels/Restaurants Market", "Food & Beverage + Hotels/Restaurants"),
            ("Aerospace & Defense / Security Market", "Aerospace & Defense / Security"),
        ],
        "Edge Cases": [
            ("&& Double Ampersand Market Report", "&& Double Ampersand"),
            ("Market & Report & Analysis & Study", "Market & & Analysis & Study"),
            ("A&B&C&D Market Report", "A&B&C&D"),
            ("Market+++Report", "Market+++"),
        ],
        "Geographic with Symbols": [
            ("U.S. Oil & Gas Market Report", "Oil & Gas"),
            ("Asia-Pacific M&A Market Analysis", "M&A"),
            ("European Food + Beverage Market", "Food + Beverage"),
            ("Global IT & Telecom Market Study", "IT & Telecom"),
        ]
    }

    # Create output directory
    output_dir = create_organized_output_directory("test_issue_19_comprehensive")
    logger.info(f"Output directory: {output_dir}")

    # Track results
    all_results = []
    total_passed = 0
    total_failed = 0

    # Run test suites
    for suite_name, test_cases in test_suites.items():
        logger.info(f"\n{'='*60}")
        logger.info(f"Test Suite: {suite_name}")
        logger.info(f"{'='*60}")

        suite_results = []

        for title, expected_topic_part in test_cases:
            try:
                result = run_pipeline(title, components)

                # Check if expected symbols are preserved
                symbols_to_check = ['&', '+', '/'] if any(s in title for s in ['&', '+', '/']) else []
                symbols_preserved = all(s in result['final_topic'] for s in symbols_to_check if s in title)

                # Check if expected topic part is in final result
                topic_correct = expected_topic_part in result['final_topic']

                passed = symbols_preserved and topic_correct

                if passed:
                    logger.info(f"✅ PASS: '{title}' → '{result['final_topic']}'")
                    total_passed += 1
                else:
                    logger.error(f"❌ FAIL: '{title}'")
                    logger.error(f"  Expected: '{expected_topic_part}' in result")
                    logger.error(f"  Got: '{result['final_topic']}'")
                    total_failed += 1

                suite_results.append({
                    'title': title,
                    'expected': expected_topic_part,
                    'result': result,
                    'passed': passed,
                    'symbols_preserved': symbols_preserved,
                    'topic_correct': topic_correct
                })

            except Exception as e:
                logger.error(f"❌ ERROR: '{title}' - {e}")
                total_failed += 1
                suite_results.append({
                    'title': title,
                    'expected': expected_topic_part,
                    'error': str(e),
                    'passed': False
                })

        all_results.append({
            'suite': suite_name,
            'results': suite_results
        })

    # Generate summary
    logger.info(f"\n{'='*80}")
    logger.info("COMPREHENSIVE TEST SUMMARY")
    logger.info(f"{'='*80}")
    logger.info(f"Total Test Cases: {total_passed + total_failed}")
    logger.info(f"Passed: {total_passed}")
    logger.info(f"Failed: {total_failed}")
    logger.info(f"Success Rate: {(total_passed/(total_passed+total_failed)*100):.1f}%")

    # Save results
    results_file = os.path.join(output_dir, "comprehensive_test_results.json")
    with open(results_file, 'w', encoding='utf-8') as f:
        json.dump(all_results, f, indent=2)
    logger.info(f"\nDetailed results saved to: {results_file}")

    # Generate markdown report
    report_file = os.path.join(output_dir, "comprehensive_test_report.md")
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(create_output_file_header("Issue #19 Comprehensive Symbol Preservation Test",
                                         "Complete validation of symbol preservation across all edge cases"))
        f.write("\n\n# Comprehensive Symbol Preservation Test Report\n\n")
        f.write(f"## Overall Summary\n\n")
        f.write(f"- **Total Test Cases:** {total_passed + total_failed}\n")
        f.write(f"- **Passed:** {total_passed}\n")
        f.write(f"- **Failed:** {total_failed}\n")
        f.write(f"- **Success Rate:** {(total_passed/(total_passed+total_failed)*100 if (total_passed+total_failed) > 0 else 0):.1f}%\n\n")

        for suite_data in all_results:
            f.write(f"## {suite_data['suite']}\n\n")
            f.write("| Status | Title | Expected | Result |\n")
            f.write("|--------|-------|----------|--------|\n")

            for test in suite_data['results']:
                status = "✅" if test['passed'] else "❌"
                title = test['title'][:50] + "..." if len(test['title']) > 50 else test['title']
                if 'error' not in test:
                    result = test['result']['final_topic']
                else:
                    result = f"ERROR: {test['error'][:30]}"
                f.write(f"| {status} | {title} | {test['expected']} | {result} |\n")
            f.write("\n")

    logger.info(f"Report saved to: {report_file}")

    return total_failed == 0

if __name__ == "__main__":
    try:
        success = test_comprehensive_symbol_preservation()
        if success:
            logger.info("\n✅ ALL COMPREHENSIVE TESTS PASSED!")
            sys.exit(0)
        else:
            logger.warning("\n⚠️ Some tests failed - review results")
            sys.exit(1)
    except Exception as e:
        logger.error(f"Test execution failed: {e}")
        sys.exit(1)