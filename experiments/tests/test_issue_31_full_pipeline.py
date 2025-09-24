#!/usr/bin/env python3
"""
Full Pipeline Test for Issue #31 Fix
Tests the complete extraction pipeline with content preservation
"""

import os
import sys
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple
import pytz
import json
from dotenv import load_dotenv
from pymongo import MongoClient

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import importlib.util

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

def import_module_from_path(module_name: str, file_path: str):
    """Import a module from a file path."""
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

def create_organized_output_directory(script_name: str) -> str:
    """Create organized output directory using YYYY/MM/DD structure."""
    # Get absolute path to outputs directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    experiments_dir = os.path.dirname(script_dir)
    project_root = os.path.dirname(experiments_dir)
    outputs_dir = os.path.join(project_root, 'outputs')

    # Create timestamp in Pacific Time
    pdt = pytz.timezone('America/Los_Angeles')
    now_pdt = datetime.now(pdt)

    # Create YYYY/MM/DD structure
    year_dir = os.path.join(outputs_dir, str(now_pdt.year))
    month_dir = os.path.join(year_dir, f"{now_pdt.month:02d}")
    day_dir = os.path.join(month_dir, f"{now_pdt.day:02d}")

    # Create timestamped subdirectory
    timestamp = now_pdt.strftime('%Y%m%d_%H%M%S')
    output_dir = os.path.join(day_dir, f"{timestamp}_{script_name}")
    os.makedirs(output_dir, exist_ok=True)

    return output_dir

def create_output_file_header(script_name: str, description: str = "") -> str:
    """Create standardized output file header with dual timestamps."""
    pdt = pytz.timezone('America/Los_Angeles')
    now_pdt = datetime.now(pdt)
    now_utc = datetime.now(pytz.UTC)

    header = f"""================================================================================
Test Script: {script_name}
Description: {description}
Analysis Date (PDT): {now_pdt.strftime('%Y-%m-%d %H:%M:%S')} PDT
Analysis Date (UTC): {now_utc.strftime('%Y-%m-%d %H:%M:%S')} UTC
================================================================================

"""
    return header

class FullPipelineTester:
    """Full pipeline tester for Issue #31 fix validation."""

    def __init__(self):
        """Initialize the tester with all pipeline components."""
        # Import required modules
        parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

        # Import PatternLibraryManager
        pattern_manager = import_module_from_path(
            "pattern_library_manager",
            os.path.join(parent_dir, "00b_pattern_library_manager_v1.py")
        )

        # Import all pipeline scripts
        script01 = import_module_from_path(
            "market_classifier",
            os.path.join(parent_dir, "01_market_term_classifier_v1.py")
        )

        script02 = import_module_from_path(
            "date_extractor",
            os.path.join(parent_dir, "02_date_extractor_v1.py")
        )

        script03 = import_module_from_path(
            "report_extractor",
            os.path.join(parent_dir, "03_report_type_extractor_v4.py")
        )

        script04 = import_module_from_path(
            "geo_detector",
            os.path.join(parent_dir, "04_geographic_entity_detector_v2.py")
        )

        # Initialize components
        self.pattern_lib_manager = pattern_manager.PatternLibraryManager(os.getenv('MONGODB_URI'))
        self.market_classifier = script01.MarketTermClassifier(self.pattern_lib_manager)
        self.date_extractor = script02.EnhancedDateExtractor(self.pattern_lib_manager)
        self.report_extractor = script03.PureDictionaryReportTypeExtractor(self.pattern_lib_manager)

        # Script 04 v2 also uses PatternLibraryManager now
        self.geo_detector = script04.GeographicEntityDetector(self.pattern_lib_manager)

        # Test titles specifically for Issue #31
        self.test_titles = self._load_test_titles()

    def _load_test_titles(self) -> List[Dict]:
        """Load test titles from Issue #31."""
        return [
            # Core test case from issue
            {
                "title": "Real-Time Locating Systems Market Size, RTLS Industry Report, 2025",
                "expected_contains": ["RTLS", "Real-Time Locating Systems"],
                "category": "core_issue"
            },
            # Additional test cases
            {
                "title": "Artificial Intelligence Market Analysis, AI Technology Report, 2030",
                "expected_contains": ["AI", "Artificial Intelligence"],
                "category": "acronym"
            },
            {
                "title": "Internet of Things Market Trends, IoT Industry Study, 2025",
                "expected_contains": ["IoT", "Internet of Things"],
                "category": "acronym"
            },
            {
                "title": "5G Network Market Size, Next-Gen Telecom Report, 2025",
                "expected_contains": ["5G Network", "Next-Gen"],
                "category": "compound"
            },
            {
                "title": "Electric Vehicle Market by Battery Type Report, 2025",
                "expected_contains": ["Electric Vehicle", "Battery Type"],
                "category": "market_by"
            },
            {
                "title": "API Management Market Analysis, REST vs SOAP Report, 2026",
                "expected_contains": ["API Management", "REST", "SOAP"],
                "category": "multi_acronym"
            },
            {
                "title": "Supply Chain Management Market Forecast, SCM Platform Analysis, 2024-2029",
                "expected_contains": ["SCM", "Supply Chain Management"],
                "category": "acronym"
            },
            {
                "title": "Software-Defined Networking Market Research, SDN Controller Report, 2026",
                "expected_contains": ["Software-Defined Networking", "SDN"],
                "category": "compound"
            },
            {
                "title": "AR/VR/MR Technologies Market Overview, XR Industry Report, 2025",
                "expected_contains": ["AR", "VR", "MR", "XR"],
                "category": "multi_acronym"
            },
            {
                "title": "Cybersecurity Market by Solution Type Report, 2025-2030",
                "expected_contains": ["Cybersecurity", "Solution Type"],
                "category": "market_by"
            }
        ]

    def process_full_pipeline(self, title: str) -> Dict:
        """Process title through complete pipeline (01 -> 02 -> 03 -> 04)."""
        try:
            # Step 1: Market term classification
            market_result = self.market_classifier.classify(title)
            logger.debug(f"Market classification: {market_result.market_type}")

            # Step 2: Date extraction
            date_result = self.date_extractor.extract(market_result.title)
            logger.debug(f"Date extracted: {date_result.extracted_date_range}")

            # Step 3: Report type extraction (with content preservation)
            report_result = self.report_extractor.extract(
                title=date_result.title,
                market_term_type=market_result.market_type
            )
            logger.debug(f"Report type: {report_result.extracted_report_type}")

            # Step 4: Geographic entity detection
            geo_result = self.geo_detector.extract_geographic_entities(report_result.title)

            # Final topic is what remains after geographic extraction
            # geo_result is a GeographicExtractionResult object with .title and .extracted_regions attributes
            final_topic = geo_result.title if hasattr(geo_result, 'title') else report_result.title

            return {
                "success": True,
                "original_title": title,
                "market_type": market_result.market_type,
                "extracted_date": date_result.extracted_date_range,
                "extracted_report_type": report_result.extracted_report_type,
                "extracted_regions": geo_result.extracted_regions if hasattr(geo_result, 'extracted_regions') else [],
                "final_topic": final_topic,
                "processing_stages": {
                    "after_market_classification": market_result.title,
                    "after_date_extraction": date_result.title,
                    "after_report_type_extraction": report_result.title,
                    "after_geographic_extraction": final_topic
                }
            }

        except Exception as e:
            logger.error(f"Pipeline error: {e}")
            return {
                "success": False,
                "original_title": title,
                "error": str(e)
            }

    def run_all_tests(self) -> Tuple[List[Dict], Dict]:
        """Run all test cases through full pipeline."""
        results = []
        statistics = {
            "total": 0,
            "passed": 0,
            "failed": 0,
            "by_category": {}
        }

        for test_case in self.test_titles:
            title = test_case["title"]
            expected_contains = test_case["expected_contains"]
            category = test_case["category"]

            # Initialize category stats
            if category not in statistics["by_category"]:
                statistics["by_category"][category] = {
                    "total": 0,
                    "passed": 0,
                    "failed": 0
                }

            # Process through full pipeline
            result = self.process_full_pipeline(title)

            # Check if expected content is preserved in final topic
            passed = False
            if result["success"] and result.get("final_topic"):
                final_topic_lower = result["final_topic"].lower()
                # Check if at least one expected term is preserved
                for expected in expected_contains:
                    if expected.lower() in final_topic_lower:
                        passed = True
                        break

            # Add test metadata
            result["test_case"] = test_case
            result["test_passed"] = passed

            # Update statistics
            statistics["total"] += 1
            statistics["by_category"][category]["total"] += 1

            if passed:
                statistics["passed"] += 1
                statistics["by_category"][category]["passed"] += 1
            else:
                statistics["failed"] += 1
                statistics["by_category"][category]["failed"] += 1

            results.append(result)

            # Log progress
            status = "✓" if passed else "✗"
            logger.info(f"{status} {category}: {title[:50]}... -> {result.get('final_topic', 'ERROR')}")

        # Calculate percentages
        statistics["success_rate"] = (statistics["passed"] / statistics["total"] * 100) if statistics["total"] > 0 else 0

        for category in statistics["by_category"]:
            cat_stats = statistics["by_category"][category]
            cat_stats["success_rate"] = (cat_stats["passed"] / cat_stats["total"] * 100) if cat_stats["total"] > 0 else 0

        return results, statistics

def main():
    """Main execution function."""
    logger.info("Starting Full Pipeline Test for Issue #31 Fix")

    # Create output directory
    output_dir = create_organized_output_directory("test_issue_31_full_pipeline")
    logger.info(f"Output directory: {output_dir}")

    try:
        # Initialize tester
        tester = FullPipelineTester()

        # Run all tests
        logger.info(f"Running {len(tester.test_titles)} test cases through full pipeline...")
        results, statistics = tester.run_all_tests()

        # Generate summary report
        summary_file = os.path.join(output_dir, "full_pipeline_summary.txt")
        with open(summary_file, 'w') as f:
            f.write(create_output_file_header(
                "test_issue_31_full_pipeline",
                "Full Pipeline Testing for Issue #31 - Content Preservation Validation"
            ))

            f.write("FULL PIPELINE TEST STATISTICS\n")
            f.write("=" * 80 + "\n")
            f.write(f"Total Test Cases: {statistics['total']}\n")
            f.write(f"Passed: {statistics['passed']}\n")
            f.write(f"Failed: {statistics['failed']}\n")
            f.write(f"Success Rate: {statistics['success_rate']:.1f}%\n\n")

            f.write("RESULTS BY CATEGORY\n")
            f.write("=" * 80 + "\n")
            for category, cat_stats in statistics["by_category"].items():
                f.write(f"\n{category.upper()}:\n")
                f.write(f"  Total: {cat_stats['total']}\n")
                f.write(f"  Passed: {cat_stats['passed']}\n")
                f.write(f"  Failed: {cat_stats['failed']}\n")
                f.write(f"  Success Rate: {cat_stats['success_rate']:.1f}%\n")

            f.write("\n" + "=" * 80 + "\n")
            f.write("DETAILED TEST RESULTS\n")
            f.write("=" * 80 + "\n\n")

            for i, result in enumerate(results, 1):
                status = "PASS" if result["test_passed"] else "FAIL"
                f.write(f"Test #{i} [{status}] - {result['test_case']['category']}\n")
                f.write(f"  Original: {result['original_title']}\n")
                f.write(f"  Expected: {result['test_case']['expected_contains']}\n")
                if result["success"]:
                    f.write(f"  Final Topic: {result['final_topic']}\n")
                    f.write(f"  Report Type: {result.get('extracted_report_type', 'N/A')}\n")
                    if result.get('extracted_date'):
                        f.write(f"  Date: {result['extracted_date']}\n")
                    if result.get('extracted_regions'):
                        f.write(f"  Regions: {result['extracted_regions']}\n")
                    f.write(f"  Processing Stages:\n")
                    for stage, text in result['processing_stages'].items():
                        f.write(f"    {stage}: {text}\n")
                else:
                    f.write(f"  Error: {result.get('error', 'Unknown')}\n")
                f.write("\n")

            if statistics['failed'] == 0:
                f.write("=" * 80 + "\n")
                f.write("✓ ALL TEST CASES PASSED!\n")
                f.write("=" * 80 + "\n")

        logger.info(f"Summary report saved to: {summary_file}")

        # Save detailed results as JSON
        results_file = os.path.join(output_dir, "detailed_results.json")
        with open(results_file, 'w') as f:
            json.dump({
                "statistics": statistics,
                "results": results
            }, f, indent=2)

        logger.info(f"Detailed results saved to: {results_file}")

        # Print summary to console
        print("\n" + "=" * 80)
        print("FULL PIPELINE TEST RESULTS - ISSUE #31 FIX")
        print("=" * 80)
        print(f"Overall Success Rate: {statistics['success_rate']:.1f}%")
        print(f"Total: {statistics['total']} | Passed: {statistics['passed']} | Failed: {statistics['failed']}")
        print("\nBy Category:")
        for category, cat_stats in statistics["by_category"].items():
            print(f"  {category}: {cat_stats['success_rate']:.1f}% ({cat_stats['passed']}/{cat_stats['total']})")

        if statistics['success_rate'] == 100:
            print("\n✓ SUCCESS: All test cases passed with content preservation!")
        print("=" * 80)

    except Exception as e:
        logger.error(f"Test execution failed: {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0

if __name__ == "__main__":
    exit(main())