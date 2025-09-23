#!/usr/bin/env python3
"""
Test Script for GitHub Issue #19: Market Term Symbol Preservation
Validates that ampersands (&) and other special characters are preserved during market term extraction.
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
from pymongo import MongoClient

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
    # Import the output directory manager using the same pattern as main scripts
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

def test_ampersand_preservation():
    """Test that ampersands and other symbols are preserved in market term processing."""

    logger.info("=" * 80)
    logger.info("GitHub Issue #19: Ampersand Preservation Test")
    logger.info("=" * 80)

    # Import required modules
    parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    try:
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
        script04 = import_module_from_path("geo_detector",
                                         os.path.join(parent_dir, "04_geographic_entity_detector_v2.py"))

        logger.info("✓ All modules imported successfully")

    except Exception as e:
        logger.error(f"Failed to import modules: {e}")
        return

    # Initialize components
    try:
        # Initialize PatternLibraryManager
        pattern_lib_manager = pattern_manager.PatternLibraryManager(os.getenv('MONGODB_URI'))

        # Initialize pipeline components
        market_classifier = script01.MarketTermClassifier(pattern_lib_manager)
        date_extractor = script02.EnhancedDateExtractor(pattern_lib_manager)
        report_extractor = script03.PureDictionaryReportTypeExtractor(pattern_lib_manager)

        # Script 04 v2 also uses PatternLibraryManager now (lean architecture updated)
        geo_detector = script04.GeographicEntityDetector(pattern_lib_manager)

        logger.info("✓ All components initialized successfully")

    except Exception as e:
        logger.error(f"Failed to initialize components: {e}")
        return

    # Define test cases with ampersands and other special characters
    test_cases = [
        # Primary test cases from Issue #19
        {
            "title": "U.S. Windows & Patio Doors Market For Single Family Homes, Report, 2030",
            "expected_topic": "Windows & Patio Doors for Single Family Homes",
            "expected_symbol": "&",
            "category": "Ampersand in market term"
        },
        {
            "title": "Oman Industrial Salts Market For Oil & Gas Industry Report, 2020-2027",
            "expected_topic": "Industrial Salts for Oil & Gas Industry",
            "expected_symbol": "&",
            "category": "Ampersand in context"
        },
        # Additional test cases with various symbols
        {
            "title": "Global Food & Beverage Market For Hotels/Restaurants Industry Analysis, 2025",
            "expected_topic": "Food & Beverage for Hotels/Restaurants",
            "expected_symbol": "&",
            "category": "Multiple symbols (&, /)"
        },
        {
            "title": "Asia-Pacific R&D Market For Pharmaceuticals + Biotech Outlook, 2024-2030",
            "expected_topic": "R&D for Pharmaceuticals + Biotech",
            "expected_symbol": "&",
            "category": "Complex symbols (&, +)"
        },
        {
            "title": "European Mergers & Acquisitions Market In Banking/Finance Report",
            "expected_topic": "Mergers & Acquisitions in Banking/Finance",
            "expected_symbol": "&",
            "category": "Market In pattern with &"
        },
        # Standard market patterns with symbols
        {
            "title": "Oil & Gas Market Analysis and Trends, 2025",
            "expected_topic": "Oil & Gas",
            "expected_symbol": "&",
            "category": "Standard pattern with &"
        },
        {
            "title": "Food + Beverages Market Research Report, 2030",
            "expected_topic": "Food + Beverages",
            "expected_symbol": "+",
            "category": "Plus symbol preservation"
        },
        {
            "title": "Telecom/Media Market Outlook & Forecast, 2025-2035",
            "expected_topic": "Telecom/Media",
            "expected_symbol": "/",
            "category": "Slash symbol preservation"
        }
    ]

    # Create output directory
    output_dir = create_organized_output_directory("test_issue_19_ampersand_preservation")
    logger.info(f"Output directory: {output_dir}")

    # Process test cases
    results = []
    passed_tests = 0
    failed_tests = 0

    for i, test_case in enumerate(test_cases, 1):
        logger.info(f"\n{'='*60}")
        logger.info(f"Test Case {i}: {test_case['category']}")
        logger.info(f"Title: {test_case['title']}")

        try:
            # Step 1: Market classification
            market_result = market_classifier.classify(test_case['title'])
            logger.info(f"  Market Type: {market_result.market_type}")

            # Step 2: Date extraction
            date_result = date_extractor.extract(market_result.title)
            logger.info(f"  Date Extracted: {date_result.extracted_date_range}")

            # Step 3: Report type extraction with market term type
            report_result = report_extractor.extract(
                date_result.title,
                market_term_type=market_result.market_type
            )
            logger.info(f"  Report Type: {report_result.extracted_report_type}")
            logger.info(f"  Pipeline Forward: {report_result.title}")

            # Step 4: Geographic detection
            geo_result = geo_detector.extract_geographic_entities(report_result.title)
            regions = geo_result.extracted_regions
            logger.info(f"  Geographic Entities: {regions}")

            # The geographic detector already removes regions from the title
            final_topic = geo_result.title

            # Check if symbol was preserved
            symbol_preserved = test_case['expected_symbol'] in final_topic

            # Determine test result
            test_passed = symbol_preserved

            if test_passed:
                logger.info(f"  ✅ PASSED: Symbol '{test_case['expected_symbol']}' preserved")
                logger.info(f"  Final Topic: {final_topic}")
                passed_tests += 1
                status = "PASSED"
            else:
                logger.error(f"  ❌ FAILED: Symbol '{test_case['expected_symbol']}' NOT preserved")
                logger.error(f"  Expected: {test_case['expected_topic']}")
                logger.error(f"  Got: {final_topic}")
                failed_tests += 1
                status = "FAILED"

            # Store result
            results.append({
                "test_case": i,
                "category": test_case['category'],
                "original_title": test_case['title'],
                "market_type": market_result.market_type,
                "date_extracted": date_result.extracted_date_range,
                "report_type": report_result.extracted_report_type,
                "regions": regions,
                "final_topic": final_topic,
                "expected_topic": test_case['expected_topic'],
                "symbol_tested": test_case['expected_symbol'],
                "symbol_preserved": symbol_preserved,
                "status": status
            })

        except Exception as e:
            logger.error(f"  ❌ ERROR processing test case: {e}")
            failed_tests += 1
            results.append({
                "test_case": i,
                "category": test_case['category'],
                "original_title": test_case['title'],
                "status": "ERROR",
                "error": str(e)
            })

    # Generate summary report
    logger.info(f"\n{'='*80}")
    logger.info("TEST SUMMARY")
    logger.info(f"{'='*80}")
    logger.info(f"Total Tests: {len(test_cases)}")
    logger.info(f"Passed: {passed_tests}")
    logger.info(f"Failed: {failed_tests}")
    logger.info(f"Success Rate: {(passed_tests/len(test_cases)*100):.1f}%")

    # Save detailed results
    results_file = os.path.join(output_dir, "test_results.json")
    with open(results_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2)
    logger.info(f"\nDetailed results saved to: {results_file}")

    # Generate markdown report
    report_file = os.path.join(output_dir, "test_report.md")
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(create_output_file_header("Issue #19 Ampersand Preservation Test",
                                         "Validation of symbol preservation during market term extraction"))
        f.write("\n\n# GitHub Issue #19: Ampersand Preservation Test Report\n\n")
        f.write(f"## Summary\n\n")
        f.write(f"- **Total Tests:** {len(test_cases)}\n")
        f.write(f"- **Passed:** {passed_tests}\n")
        f.write(f"- **Failed:** {failed_tests}\n")
        f.write(f"- **Success Rate:** {(passed_tests/len(test_cases)*100):.1f}%\n\n")

        f.write("## Test Results\n\n")
        f.write("| # | Category | Title | Symbol | Status | Result |\n")
        f.write("|---|----------|-------|--------|--------|--------|\n")

        for result in results:
            if result['status'] != 'ERROR':
                f.write(f"| {result['test_case']} | {result['category']} | {result['original_title'][:50]}... | "
                       f"{result['symbol_tested']} | {result['status']} | {result['final_topic']} |\n")
            else:
                f.write(f"| {result['test_case']} | {result['category']} | {result['original_title'][:50]}... | "
                       f"- | ERROR | {result.get('error', 'Unknown error')} |\n")

        f.write("\n## Detailed Analysis\n\n")
        for result in results:
            f.write(f"### Test Case {result['test_case']}: {result['category']}\n\n")
            f.write(f"**Original Title:** {result['original_title']}\n\n")
            if result['status'] != 'ERROR':
                f.write(f"**Processing Steps:**\n")
                f.write(f"1. Market Type: {result['market_type']}\n")
                f.write(f"2. Date Extracted: {result.get('date_extracted', 'None')}\n")
                f.write(f"3. Report Type: {result.get('report_type', 'None')}\n")
                f.write(f"4. Regions: {result.get('regions', [])}\n")
                f.write(f"5. Final Topic: {result['final_topic']}\n\n")
                f.write(f"**Expected:** {result['expected_topic']}\n")
                f.write(f"**Symbol Preserved:** {'✅ Yes' if result['symbol_preserved'] else '❌ No'}\n\n")
            else:
                f.write(f"**Error:** {result.get('error', 'Unknown error')}\n\n")

    logger.info(f"Test report saved to: {report_file}")

    return passed_tests == len(test_cases)

if __name__ == "__main__":
    try:
        success = test_ampersand_preservation()
        if success:
            logger.info("\n✅ ALL TESTS PASSED - Issue #19 fix validated!")
            sys.exit(0)
        else:
            logger.warning("\n⚠️ Some tests failed - review results for details")
            sys.exit(1)
    except Exception as e:
        logger.error(f"Test execution failed: {e}")
        sys.exit(1)