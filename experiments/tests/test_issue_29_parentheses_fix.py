#!/usr/bin/env python3
"""
Test script to validate Issue #29 fix: Parentheses conflict between Scripts 02 and 03v4
"""

import os
import sys
import json
import logging
from datetime import datetime
import pytz
from typing import Dict, Any
import importlib.util
from dotenv import load_dotenv
from pymongo import MongoClient

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def import_module_from_path(module_name: str, file_path: str):
    """Import a module from a file path."""
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

def create_organized_output_directory(script_name: str) -> str:
    """Create organized output directory with YYYY/MM/DD structure."""
    # Get project root
    script_dir = os.path.dirname(os.path.abspath(__file__))
    experiments_dir = os.path.dirname(script_dir)
    project_root = os.path.dirname(experiments_dir)

    # Create timestamp in Pacific Time
    pdt = pytz.timezone('America/Los_Angeles')
    now = datetime.now(pdt)

    # Create organized directory structure: outputs/YYYY/MM/DD/YYYYMMDD_HHMMSS_script_name/
    year_dir = os.path.join(project_root, 'outputs', str(now.year))
    month_dir = os.path.join(year_dir, f"{now.month:02d}")
    day_dir = os.path.join(month_dir, f"{now.day:02d}")

    timestamp = now.strftime('%Y%m%d_%H%M%S')
    output_dir = os.path.join(day_dir, f"{timestamp}_{script_name}")

    os.makedirs(output_dir, exist_ok=True)
    return output_dir

def create_output_file_header(script_name: str, description: str = "") -> str:
    """Create standardized file header with dual timestamps."""
    pdt = pytz.timezone('America/Los_Angeles')
    utc = pytz.UTC

    now_pdt = datetime.now(pdt)
    now_utc = datetime.now(utc)

    pdt_suffix = "PDT" if now_pdt.dst() else "PST"

    header = f"""# {script_name} - Output Report
{description}

**Analysis Date ({pdt_suffix}):** {now_pdt.strftime('%Y-%m-%d %H:%M:%S')} {pdt_suffix}
**Analysis Date (UTC):** {now_utc.strftime('%Y-%m-%d %H:%M:%S')} UTC

{'=' * 80}
"""
    return header

def test_parentheses_conflict():
    """Test the parentheses conflict issue and validate the fix."""

    # Import necessary modules
    parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    # Import PatternLibraryManager
    pattern_manager = import_module_from_path("pattern_library_manager",
                                            os.path.join(parent_dir, "00b_pattern_library_manager_v1.py"))

    # Import pipeline scripts
    script01 = import_module_from_path("market_classifier",
                                     os.path.join(parent_dir, "01_market_term_classifier_v1.py"))
    script02 = import_module_from_path("date_extractor",
                                     os.path.join(parent_dir, "02_date_extractor_v1.py"))
    script03 = import_module_from_path("report_extractor",
                                     os.path.join(parent_dir, "03_report_type_extractor_v4.py"))

    # Initialize PatternLibraryManager
    pattern_lib_manager = pattern_manager.PatternLibraryManager(os.getenv('MONGODB_URI'))

    # Initialize components
    market_classifier = script01.MarketTermClassifier(pattern_lib_manager)
    date_extractor = script02.EnhancedDateExtractor(pattern_lib_manager)
    report_extractor = script03.PureDictionaryReportTypeExtractor(pattern_lib_manager)

    # Test cases with parenthetical dates and report types
    test_cases = [
        {
            "title": "Battery Fuel Gauge Market (Forecast 2020-2030)",
            "expected": {
                "date": "2020-2030",
                "report_type": "Market Forecast",
                "topic": "Battery Fuel Gauge"
            }
        },
        {
            "title": "Global Smart Grid Market (Analysis & Forecast 2024-2029)",
            "expected": {
                "date": "2024-2029",
                "report_type": "Market Analysis & Forecast",
                "topic": "Global Smart Grid"
            }
        },
        {
            "title": "Electric Vehicle Market (2025-2035 Outlook)",
            "expected": {
                "date": "2025-2035",
                "report_type": "Market Outlook",
                "topic": "Electric Vehicle"
            }
        },
        {
            "title": "Digital Health Market (Industry Analysis 2023-2028)",
            "expected": {
                "date": "2023-2028",
                "report_type": "Market Industry Analysis",
                "topic": "Digital Health"
            }
        },
        {
            "title": "Renewable Energy Market Research Report (2024)",
            "expected": {
                "date": "2024",
                "report_type": "Market Research Report",
                "topic": "Renewable Energy"
            }
        }
    ]

    results = []

    logger.info("=" * 80)
    logger.info("Testing Issue #29: Parentheses Conflict Resolution")
    logger.info("=" * 80)

    for i, test_case in enumerate(test_cases, 1):
        title = test_case["title"]
        expected = test_case["expected"]

        logger.info(f"\nTest Case {i}: {title}")
        logger.info("-" * 60)

        # Step 1: Market Term Classification
        market_result = market_classifier.classify(title)
        logger.info(f"  Market Type: {market_result.market_type}")

        # Step 2: Date Extraction
        date_result = date_extractor.extract(market_result.title)
        logger.info(f"  Date Extracted: {date_result.extracted_date_range}")
        logger.info(f"  After Date Extraction: '{date_result.title}'")

        # Check for parentheses artifacts after date extraction
        has_unmatched_parens = ('(' in date_result.title and ')' not in date_result.title) or \
                               (')' in date_result.title and '(' not in date_result.title)

        if has_unmatched_parens:
            logger.warning(f"  ⚠️  UNMATCHED PARENTHESES DETECTED: '{date_result.title}'")

        # Step 3: Report Type Extraction
        report_result = report_extractor.extract(date_result.title, market_result.market_type)
        logger.info(f"  Report Type: {report_result.extracted_report_type}")
        logger.info(f"  Final Topic: '{report_result.title}'")

        # Check results
        date_match = date_result.extracted_date_range == expected["date"]
        report_match = report_result.extracted_report_type == expected["report_type"]
        topic_match = report_result.title == expected["topic"]

        # Check for artifacts
        has_artifacts = any(char in report_result.title for char in ['(', ')', '[', ']'])

        result = {
            "test_case": i,
            "original_title": title,
            "expected": expected,
            "actual": {
                "date": date_result.extracted_date_range,
                "report_type": report_result.extracted_report_type,
                "topic": report_result.title
            },
            "date_match": date_match,
            "report_match": report_match,
            "topic_match": topic_match,
            "has_artifacts": has_artifacts,
            "has_unmatched_parens": has_unmatched_parens,
            "pass": date_match and report_match and topic_match and not has_artifacts
        }

        results.append(result)

        # Print validation
        if result["pass"]:
            logger.info("  ✅ TEST PASSED")
        else:
            logger.error("  ❌ TEST FAILED")
            if not date_match:
                logger.error(f"    - Date mismatch: expected '{expected['date']}', got '{date_result.extracted_date_range}'")
            if not report_match:
                logger.error(f"    - Report type mismatch: expected '{expected['report_type']}', got '{report_result.extracted_report_type}'")
            if not topic_match:
                logger.error(f"    - Topic mismatch: expected '{expected['topic']}', got '{report_result.title}'")
            if has_artifacts:
                logger.error(f"    - Topic contains artifacts: '{report_result.title}'")

    # Summary
    logger.info("\n" + "=" * 80)
    logger.info("TEST SUMMARY")
    logger.info("=" * 80)

    passed = sum(1 for r in results if r["pass"])
    failed = len(results) - passed

    logger.info(f"Total Tests: {len(results)}")
    logger.info(f"Passed: {passed}")
    logger.info(f"Failed: {failed}")
    logger.info(f"Success Rate: {(passed/len(results)*100):.1f}%")

    # Save detailed results
    output_dir = create_organized_output_directory("test_issue_29")

    # Save JSON results
    json_path = os.path.join(output_dir, "test_results.json")
    with open(json_path, 'w') as f:
        json.dump(results, f, indent=2)
    logger.info(f"\nDetailed results saved to: {json_path}")

    # Save detailed report
    report_path = os.path.join(output_dir, "detailed_report.txt")
    with open(report_path, 'w') as f:
        f.write(create_output_file_header("Issue #29 Parentheses Conflict Test",
                                         "Testing parentheses handling between Scripts 02 and 03v4"))
        f.write("\n")

        for result in results:
            f.write(f"\nTest Case {result['test_case']}: {result['original_title']}\n")
            f.write("-" * 60 + "\n")
            f.write(f"Expected:\n")
            f.write(f"  Date: {result['expected']['date']}\n")
            f.write(f"  Report Type: {result['expected']['report_type']}\n")
            f.write(f"  Topic: {result['expected']['topic']}\n")
            f.write(f"Actual:\n")
            f.write(f"  Date: {result['actual']['date']}\n")
            f.write(f"  Report Type: {result['actual']['report_type']}\n")
            f.write(f"  Topic: {result['actual']['topic']}\n")
            f.write(f"Status: {'✅ PASS' if result['pass'] else '❌ FAIL'}\n")
            if not result['pass']:
                f.write(f"Issues:\n")
                if not result['date_match']:
                    f.write(f"  - Date mismatch\n")
                if not result['report_match']:
                    f.write(f"  - Report type mismatch\n")
                if not result['topic_match']:
                    f.write(f"  - Topic mismatch\n")
                if result['has_artifacts']:
                    f.write(f"  - Contains parentheses artifacts\n")
                if result['has_unmatched_parens']:
                    f.write(f"  - Unmatched parentheses after date extraction\n")

        f.write("\n" + "=" * 80 + "\n")
        f.write("SUMMARY\n")
        f.write("=" * 80 + "\n")
        f.write(f"Total Tests: {len(results)}\n")
        f.write(f"Passed: {passed}\n")
        f.write(f"Failed: {failed}\n")
        f.write(f"Success Rate: {(passed/len(results)*100):.1f}%\n")

    logger.info(f"Detailed report saved to: {report_path}")

    return results, passed == len(results)

if __name__ == "__main__":
    try:
        results, all_passed = test_parentheses_conflict()
        if not all_passed:
            logger.error("\n⚠️  Some tests failed - Issue #29 is still present")
            sys.exit(1)
        else:
            logger.info("\n✅ All tests passed - Issue #29 appears to be resolved!")
    except Exception as e:
        logger.error(f"Error during testing: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)