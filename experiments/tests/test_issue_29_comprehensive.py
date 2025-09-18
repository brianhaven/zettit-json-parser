#!/usr/bin/env python3
"""
Comprehensive test for Issue #29 resolution with expanded test cases
"""

import os
import sys
import json
import logging
from datetime import datetime
import pytz
from typing import Dict, Any, List, Tuple
import importlib.util
from dotenv import load_dotenv

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Load environment variables
load_dotenv()

# Configure logging
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

def create_organized_output_directory(script_name: str) -> str:
    """Create organized output directory with YYYY/MM/DD structure."""
    # Get project root
    script_dir = os.path.dirname(os.path.abspath(__file__))
    experiments_dir = os.path.dirname(script_dir)
    project_root = os.path.dirname(experiments_dir)

    # Create timestamp in Pacific Time
    pdt = pytz.timezone('America/Los_Angeles')
    now = datetime.now(pdt)

    # Create organized directory structure
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

    header = f"""# {script_name} - Comprehensive Test Report
{description}

**Analysis Date ({pdt_suffix}):** {now_pdt.strftime('%Y-%m-%d %H:%M:%S')} {pdt_suffix}
**Analysis Date (UTC):** {now_utc.strftime('%Y-%m-%d %H:%M:%S')} UTC

{'=' * 80}
"""
    return header

def run_pipeline(title: str, components: Dict) -> Dict[str, Any]:
    """Run a single title through the pipeline and return results."""

    market_classifier = components['market_classifier']
    date_extractor = components['date_extractor']
    report_extractor = components['report_extractor']

    # Step 1: Market Term Classification
    market_result = market_classifier.classify(title)

    # Step 2: Date Extraction
    date_result = date_extractor.extract(market_result.title)

    # Check for parentheses artifacts after date extraction
    has_unmatched_parens = ('(' in date_result.title and ')' not in date_result.title) or \
                           (')' in date_result.title and '(' not in date_result.title)

    # Step 3: Report Type Extraction
    report_result = report_extractor.extract(date_result.title, market_result.market_type)

    # Check for artifacts
    has_artifacts = any(char in report_result.title for char in ['(', ')', '[', ']'])

    return {
        'market_type': market_result.market_type,
        'date': date_result.extracted_date_range,
        'report_type': report_result.extracted_report_type,
        'topic': report_result.title,
        'has_unmatched_parens': has_unmatched_parens,
        'has_artifacts': has_artifacts,
        'intermediate_title': date_result.title,
        'preserved_words': date_result.preserved_words if hasattr(date_result, 'preserved_words') else []
    }

def comprehensive_test():
    """Comprehensive test for Issue #29 resolution."""

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
    components = {
        'market_classifier': script01.MarketTermClassifier(pattern_lib_manager),
        'date_extractor': script02.EnhancedDateExtractor(pattern_lib_manager),
        'report_extractor': script03.PureDictionaryReportTypeExtractor(pattern_lib_manager)
    }

    # Comprehensive test cases
    test_cases = [
        # Original Issue #29 cases
        {
            "category": "Parenthetical Date+Report",
            "title": "Battery Fuel Gauge Market (Forecast 2020-2030)",
            "expected": {
                "date": "2020-2030",
                "report_type": "Market Forecast",
                "topic": "Battery Fuel Gauge"
            }
        },
        {
            "category": "Parenthetical Date+Report",
            "title": "Global Smart Grid Market (Analysis & Forecast 2024-2029)",
            "expected": {
                "date": "2024-2029",
                "report_type": "Market Analysis Forecast",  # Script 03 strips &
                "topic": "Global Smart Grid"
            }
        },
        # Date at beginning of parentheses
        {
            "category": "Date First",
            "title": "Electric Vehicle Market (2025-2035 Outlook)",
            "expected": {
                "date": "2025-2035",
                "report_type": "Market Outlook",
                "topic": "Electric Vehicle"
            }
        },
        # Multiple words before date
        {
            "category": "Multiple Words",
            "title": "Digital Health Market (Industry Analysis 2023-2028)",
            "expected": {
                "date": "2023-2028",
                "report_type": "Market Industry Analysis",
                "topic": "Digital Health"
            }
        },
        # Parentheses with single year
        {
            "category": "Single Year",
            "title": "Renewable Energy Market Research Report (2024)",
            "expected": {
                "date": "2024",
                "report_type": "Market Research Report",
                "topic": "Renewable Energy"
            }
        },
        # Brackets instead of parentheses
        {
            "category": "Brackets",
            "title": "AI Chipset Market [Forecast 2024-2030]",
            "expected": {
                "date": "2024-2030",
                "report_type": "Market Forecast",
                "topic": "AI Chipset"
            }
        },
        # No parentheses
        {
            "category": "No Parentheses",
            "title": "Blockchain Market Analysis 2025-2030",
            "expected": {
                "date": "2025-2030",
                "report_type": "Market Analysis",
                "topic": "Blockchain"
            }
        },
        # Complex parenthetical content
        {
            "category": "Complex Content",
            "title": "Cloud Computing Market (Global Analysis & Forecast 2024-2029)",
            "expected": {
                "date": "2024-2029",
                "report_type": "Market Global Analysis Forecast",  # Script 03 strips &
                "topic": "Cloud Computing"
            }
        },
        # Date with comma separator
        {
            "category": "Comma Date",
            "title": "IoT Sensors Market Report, 2024-2028",
            "expected": {
                "date": "2024-2028",
                "report_type": "Market Report",
                "topic": "IoT Sensors"
            }
        },
        # Empty parentheses after date removal
        {
            "category": "Empty After Removal",
            "title": "Quantum Computing Market (2025)",
            "expected": {
                "date": "2025",
                "report_type": "Market",
                "topic": "Quantum Computing"
            }
        },
        # Multiple parenthetical sections
        {
            "category": "Multiple Parentheses",
            "title": "5G Network (Infrastructure) Market (Analysis 2024-2029)",
            "expected": {
                "date": "2024-2029",
                "report_type": "Market Analysis",
                "topic": "5G Network (Infrastructure)"  # Should preserve first parentheses
            }
        },
        # Nested complexity
        {
            "category": "Nested",
            "title": "Edge Computing Market (North America) Report 2025-2030",
            "expected": {
                "date": "2025-2030",
                "report_type": "Market Report",
                "topic": "Edge Computing (North America)"
            }
        }
    ]

    results = []
    category_stats = {}

    logger.info("=" * 80)
    logger.info("COMPREHENSIVE TEST: Issue #29 Parentheses Conflict Resolution")
    logger.info("=" * 80)

    for i, test_case in enumerate(test_cases, 1):
        category = test_case["category"]
        title = test_case["title"]
        expected = test_case["expected"]

        logger.info(f"\nTest {i} - {category}: {title}")
        logger.info("-" * 60)

        # Run pipeline
        actual = run_pipeline(title, components)

        # Log results
        logger.info(f"  Market Type: {actual['market_type']}")
        logger.info(f"  Date Extracted: {actual['date']}")
        logger.info(f"  After Date: '{actual['intermediate_title']}'")
        if actual['preserved_words']:
            logger.info(f"  Preserved Words: {actual['preserved_words']}")
        logger.info(f"  Report Type: {actual['report_type']}")
        logger.info(f"  Final Topic: '{actual['topic']}'")

        # Check results
        date_match = actual['date'] == expected.get('date')
        report_match = actual['report_type'] == expected.get('report_type')
        topic_match = actual['topic'] == expected.get('topic')

        result = {
            "test": i,
            "category": category,
            "title": title,
            "expected": expected,
            "actual": {
                "date": actual['date'],
                "report_type": actual['report_type'],
                "topic": actual['topic']
            },
            "date_match": date_match,
            "report_match": report_match,
            "topic_match": topic_match,
            "has_artifacts": actual['has_artifacts'],
            "has_unmatched_parens": actual['has_unmatched_parens'],
            "pass": date_match and report_match and topic_match and not actual['has_artifacts']
        }

        results.append(result)

        # Update category stats
        if category not in category_stats:
            category_stats[category] = {'total': 0, 'passed': 0}
        category_stats[category]['total'] += 1
        if result['pass']:
            category_stats[category]['passed'] += 1

        # Print status
        if result['pass']:
            logger.info("  ✅ PASS")
        else:
            logger.error("  ❌ FAIL")
            if not date_match:
                logger.error(f"    Date: expected '{expected.get('date')}', got '{actual['date']}'")
            if not report_match:
                logger.error(f"    Report: expected '{expected.get('report_type')}', got '{actual['report_type']}'")
            if not topic_match:
                logger.error(f"    Topic: expected '{expected.get('topic')}', got '{actual['topic']}'")
            if actual['has_artifacts']:
                logger.error(f"    Has parentheses/bracket artifacts")

    # Summary
    logger.info("\n" + "=" * 80)
    logger.info("TEST SUMMARY")
    logger.info("=" * 80)

    total_passed = sum(1 for r in results if r['pass'])
    total_tests = len(results)

    logger.info(f"\nOverall: {total_passed}/{total_tests} tests passed ({total_passed/total_tests*100:.1f}%)")

    logger.info("\nBy Category:")
    for category, stats in category_stats.items():
        passed = stats['passed']
        total = stats['total']
        logger.info(f"  {category}: {passed}/{total} ({passed/total*100:.0f}%)")

    # Save results
    output_dir = create_organized_output_directory("test_issue_29_comprehensive")

    # Save JSON results
    json_path = os.path.join(output_dir, "test_results.json")
    with open(json_path, 'w') as f:
        json.dump({
            'results': results,
            'category_stats': category_stats,
            'summary': {
                'total_tests': total_tests,
                'passed': total_passed,
                'failed': total_tests - total_passed,
                'success_rate': total_passed / total_tests * 100
            }
        }, f, indent=2)

    logger.info(f"\nResults saved to: {json_path}")

    # Save detailed report
    report_path = os.path.join(output_dir, "detailed_report.txt")
    with open(report_path, 'w') as f:
        f.write(create_output_file_header("Issue #29 Comprehensive Test",
                                         "Expanded test suite for parentheses conflict resolution"))

        f.write("\n\nTEST RESULTS\n")
        f.write("=" * 80 + "\n\n")

        for result in results:
            status = "✅ PASS" if result['pass'] else "❌ FAIL"
            f.write(f"Test {result['test']} - {result['category']}: {status}\n")
            f.write(f"Title: {result['title']}\n")
            f.write(f"Expected: date={result['expected'].get('date')}, "
                   f"report={result['expected'].get('report_type')}, "
                   f"topic={result['expected'].get('topic')}\n")
            f.write(f"Actual:   date={result['actual']['date']}, "
                   f"report={result['actual']['report_type']}, "
                   f"topic={result['actual']['topic']}\n")
            if not result['pass']:
                f.write("Issues: ")
                issues = []
                if not result['date_match']:
                    issues.append("date mismatch")
                if not result['report_match']:
                    issues.append("report type mismatch")
                if not result['topic_match']:
                    issues.append("topic mismatch")
                if result['has_artifacts']:
                    issues.append("parentheses artifacts")
                f.write(", ".join(issues) + "\n")
            f.write("\n")

        f.write("\nSUMMARY\n")
        f.write("=" * 80 + "\n")
        f.write(f"Total Tests: {total_tests}\n")
        f.write(f"Passed: {total_passed}\n")
        f.write(f"Failed: {total_tests - total_passed}\n")
        f.write(f"Success Rate: {total_passed/total_tests*100:.1f}%\n\n")

        f.write("By Category:\n")
        for category, stats in category_stats.items():
            f.write(f"  {category}: {stats['passed']}/{stats['total']} "
                   f"({stats['passed']/stats['total']*100:.0f}%)\n")

    logger.info(f"Report saved to: {report_path}")

    return results, total_passed == total_tests

if __name__ == "__main__":
    try:
        results, all_passed = comprehensive_test()
        if all_passed:
            logger.info("\n✅ ALL TESTS PASSED - Issue #29 is fully resolved!")
            sys.exit(0)
        else:
            logger.warning("\n⚠️  Some tests failed - further investigation needed")
            sys.exit(1)
    except Exception as e:
        logger.error(f"Error during testing: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)