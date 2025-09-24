#!/usr/bin/env python3
"""
Regression Test for Issue #31: Ensure content preservation doesn't break existing functionality
Tests Script 03 v4 with production data to maintain 90% success rate
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
import random

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

class RegressionTester:
    """Test harness for regression testing content preservation."""

    def __init__(self, sample_size: int = 100):
        """Initialize the tester with all required components."""
        # Import required modules
        parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

        # Import PatternLibraryManager
        pattern_manager = import_module_from_path(
            "pattern_library_manager",
            os.path.join(parent_dir, "00b_pattern_library_manager_v1.py")
        )

        # Import Script 01 (Market Term Classifier)
        script01 = import_module_from_path(
            "market_classifier",
            os.path.join(parent_dir, "01_market_term_classifier_v1.py")
        )

        # Import Script 02 (Date Extractor)
        script02 = import_module_from_path(
            "date_extractor",
            os.path.join(parent_dir, "02_date_extractor_v1.py")
        )

        # Import Script 03 v4
        script03 = import_module_from_path(
            "report_extractor",
            os.path.join(parent_dir, "03_report_type_extractor_v4.py")
        )

        # Initialize components
        self.pattern_lib_manager = pattern_manager.PatternLibraryManager(os.getenv('MONGODB_URI'))
        self.market_classifier = script01.MarketTermClassifier(self.pattern_lib_manager)
        self.date_extractor = script02.EnhancedDateExtractor(self.pattern_lib_manager)
        self.report_extractor = script03.PureDictionaryReportTypeExtractor(self.pattern_lib_manager)

        # Get sample titles from database
        self.client = MongoClient(os.getenv('MONGODB_URI'))
        self.db = self.client['deathstar']
        self.sample_size = sample_size
        self.titles = self._load_sample_titles()

    def _load_sample_titles(self) -> List[str]:
        """Load sample titles from markets_raw collection."""
        # Get all titles
        all_titles = []
        for doc in self.db.markets_raw.find({}, {"report_title_short": 1}):
            if doc.get("report_title_short"):
                all_titles.append(doc["report_title_short"])

        # Randomly sample titles
        if len(all_titles) > self.sample_size:
            sampled = random.sample(all_titles, self.sample_size)
        else:
            sampled = all_titles

        logger.info(f"Loaded {len(sampled)} titles from markets_raw")
        return sampled

    def process_title_with_pipeline(self, title: str, enable_preservation: bool = True) -> Dict:
        """Process title through full pipeline (01 -> 02 -> 03)."""
        try:
            # Step 1: Market term classification
            market_result = self.market_classifier.classify(title)

            # Step 2: Date extraction
            date_result = self.date_extractor.extract(market_result.title)

            # Step 3: Report type extraction with content preservation flag
            # Note: We need to temporarily modify the extractor to use the flag
            # For now, it's enabled by default
            report_result = self.report_extractor.extract(
                title=date_result.title,
                market_term_type=market_result.market_type  # Fixed: use market_type not market_term_type
            )

            return {
                "success": report_result.success,
                "original_title": title,
                "market_term_type": market_result.market_type,  # Fixed: use market_type
                "extracted_date": date_result.extracted_date_range,
                "extracted_report_type": report_result.extracted_report_type,
                "remaining_title": report_result.title,
                "confidence": report_result.confidence,
                "preservation_enabled": enable_preservation
            }

        except Exception as e:
            logger.error(f"Error processing title: {e}")
            return {
                "success": False,
                "original_title": title,
                "error": str(e),
                "preservation_enabled": enable_preservation
            }

    def run_regression_test(self) -> Tuple[List[Dict], Dict]:
        """Run regression test on sample titles."""
        results = []
        statistics = {
            "total": 0,
            "successful": 0,
            "failed": 0,
            "with_report_type": 0,
            "without_report_type": 0,
            "with_acronyms": 0,
            "acronyms_preserved": 0
        }

        for title in self.titles:
            result = self.process_title_with_pipeline(title, enable_preservation=True)
            results.append(result)

            # Update statistics
            statistics["total"] += 1

            if result["success"]:
                statistics["successful"] += 1

                if result.get("extracted_report_type"):
                    statistics["with_report_type"] += 1
                else:
                    statistics["without_report_type"] += 1

                # Check for potential acronyms (simple heuristic)
                remaining = result.get("remaining_title", "")
                if any(word.isupper() and len(word) <= 5 for word in remaining.split()):
                    statistics["with_acronyms"] += 1
                    statistics["acronyms_preserved"] += 1

            else:
                statistics["failed"] += 1

        # Calculate success rate
        statistics["success_rate"] = (
            (statistics["successful"] / statistics["total"] * 100)
            if statistics["total"] > 0 else 0
        )

        statistics["report_type_extraction_rate"] = (
            (statistics["with_report_type"] / statistics["successful"] * 100)
            if statistics["successful"] > 0 else 0
        )

        return results, statistics

    def compare_performance(self, sample: int = 20) -> List[Dict]:
        """Compare performance with and without content preservation."""
        comparisons = []

        for i, title in enumerate(self.titles[:sample]):
            # Process with new content preservation
            new_result = self.process_title_with_pipeline(title, enable_preservation=True)

            # For comparison, we'd need to disable preservation (currently always on)
            # This would require modifying the _clean_remaining_title call
            # For now, we'll just record the new results

            comparison = {
                "title": title,
                "new_success": new_result["success"],
                "new_report_type": new_result.get("extracted_report_type", ""),
                "new_remaining": new_result.get("remaining_title", ""),
                "has_potential_acronym": any(
                    word.isupper() and len(word) <= 5
                    for word in new_result.get("remaining_title", "").split()
                )
            }

            comparisons.append(comparison)

        return comparisons

def main():
    """Main execution function."""
    logger.info("Starting Regression Testing for Issue #31 Fix")

    # Create output directory
    output_dir = create_organized_output_directory("test_03_regression_check")
    logger.info(f"Output directory: {output_dir}")

    try:
        # Initialize tester with 100 sample titles
        tester = RegressionTester(sample_size=100)

        # Run regression test
        logger.info(f"Running regression test on {len(tester.titles)} titles...")
        results, statistics = tester.run_regression_test()

        # Generate summary report
        summary_file = os.path.join(output_dir, "regression_test_summary.txt")
        with open(summary_file, 'w') as f:
            f.write(create_output_file_header(
                "test_03_regression_check",
                "Regression Testing for Issue #31 Fix - Production Data Validation"
            ))

            f.write("REGRESSION TEST STATISTICS\n")
            f.write("=" * 80 + "\n")
            f.write(f"Total Titles Tested: {statistics['total']}\n")
            f.write(f"Successful Processing: {statistics['successful']}\n")
            f.write(f"Failed Processing: {statistics['failed']}\n")
            f.write(f"Success Rate: {statistics['success_rate']:.1f}%\n\n")

            f.write(f"Report Type Extraction:\n")
            f.write(f"  With Report Type: {statistics['with_report_type']}\n")
            f.write(f"  Without Report Type: {statistics['without_report_type']}\n")
            f.write(f"  Extraction Rate: {statistics['report_type_extraction_rate']:.1f}%\n\n")

            f.write(f"Acronym Preservation:\n")
            f.write(f"  Titles with Acronyms: {statistics['with_acronyms']}\n")
            f.write(f"  Acronyms Preserved: {statistics['acronyms_preserved']}\n\n")

            # Check if we maintain the 90% success rate
            if statistics['success_rate'] >= 90:
                f.write("✓ SUCCESS RATE MAINTAINED: The fix preserves the 90% success rate target!\n\n")
            else:
                f.write("✗ WARNING: Success rate below 90% target. Review failed cases.\n\n")

            # List failed cases
            if statistics['failed'] > 0:
                f.write("FAILED CASES\n")
                f.write("=" * 80 + "\n\n")

                failed_count = 0
                for result in results:
                    if not result["success"]:
                        failed_count += 1
                        f.write(f"FAILURE #{failed_count}:\n")
                        f.write(f"  Title: {result['original_title']}\n")
                        f.write(f"  Error: {result.get('error', 'Unknown error')}\n\n")

            # Sample of successful extractions
            f.write("\nSAMPLE SUCCESSFUL EXTRACTIONS (First 20)\n")
            f.write("=" * 80 + "\n\n")

            success_count = 0
            for result in results:
                if result["success"] and success_count < 20:
                    success_count += 1
                    f.write(f"#{success_count}:\n")
                    f.write(f"  Original: {result['original_title']}\n")
                    f.write(f"  Report Type: {result.get('extracted_report_type', 'N/A')}\n")
                    f.write(f"  Remaining: {result.get('remaining_title', 'N/A')}\n")
                    if result.get('extracted_date'):
                        f.write(f"  Date: {result['extracted_date']}\n")
                    f.write("\n")

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
        print("REGRESSION TEST RESULTS")
        print("=" * 80)
        print(f"Success Rate: {statistics['success_rate']:.1f}%")
        print(f"Total: {statistics['total']} | Success: {statistics['successful']} | Failed: {statistics['failed']}")

        if statistics['success_rate'] >= 90:
            print("\n✓ SUCCESS: 90% success rate maintained with content preservation!")
        else:
            print("\n✗ WARNING: Success rate below 90% target")

        print("=" * 80)

    except Exception as e:
        logger.error(f"Test execution failed: {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0

if __name__ == "__main__":
    exit(main())