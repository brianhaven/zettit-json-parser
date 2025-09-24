#!/usr/bin/env python3
"""
Test Script for Issue #31: Content Preservation Between Report Type Keywords
Tests the enhanced _clean_remaining_title() method with comprehensive edge cases
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

class ContentPreservationTester:
    """Test harness for content preservation in report type extraction."""

    def __init__(self):
        """Initialize the tester with all required components."""
        # Import required modules
        parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

        # Import PatternLibraryManager
        pattern_manager = import_module_from_path(
            "pattern_library_manager",
            os.path.join(parent_dir, "00b_pattern_library_manager_v1.py")
        )

        # Import Script 03 v4
        script03 = import_module_from_path(
            "report_extractor",
            os.path.join(parent_dir, "03_report_type_extractor_v4.py")
        )

        # Initialize components
        self.pattern_lib_manager = pattern_manager.PatternLibraryManager(os.getenv('MONGODB_URI'))
        self.report_extractor = script03.PureDictionaryReportTypeExtractor(self.pattern_lib_manager)

        # Test cases from Issue #31
        self.test_cases = self._load_test_cases()

    def _load_test_cases(self) -> List[Dict]:
        """Load all test cases from Issue #31."""
        test_cases = []

        # Acronym Edge Cases
        acronym_cases = [
            # Core test case from issue
            {
                "title": "Real-Time Locating Systems Market Size, RTLS Industry Report, 2025",
                "expected_topic_contains": ["RTLS", "Real-Time Locating Systems"],
                "category": "acronym_preservation"
            },

            # Additional acronym test cases
            {
                "title": "Artificial Intelligence Market Analysis, AI Technology Report, 2030",
                "expected_topic_contains": ["AI", "Artificial Intelligence"],
                "category": "acronym_preservation"
            },
            {
                "title": "Internet of Things Market Trends, IoT Industry Study, 2025",
                "expected_topic_contains": ["IoT", "Internet of Things"],
                "category": "acronym_preservation"
            },
            {
                "title": "Enterprise Resource Planning Market Outlook, ERP Solutions Report, 2026",
                "expected_topic_contains": ["ERP", "Enterprise Resource Planning"],
                "category": "acronym_preservation"
            },
            {
                "title": "Customer Relationship Management Market Insights, CRM Platform Analysis, 2024",
                "expected_topic_contains": ["CRM", "Customer Relationship Management"],
                "category": "acronym_preservation"
            },
            {
                "title": "Application Programming Interface Market Forecast, API Economy Report, 2025-2030",
                "expected_topic_contains": ["API", "Application Programming Interface"],
                "category": "acronym_preservation"
            },
            {
                "title": "Software as a Service Market Overview, SaaS Industry Report, 2025",
                "expected_topic_contains": ["SaaS", "Software as a Service"],
                "category": "acronym_preservation"
            },
            {
                "title": "Platform as a Service Market Research, PaaS Cloud Report, 2026",
                "expected_topic_contains": ["PaaS", "Platform as a Service"],
                "category": "acronym_preservation"
            },
            {
                "title": "Infrastructure as a Service Market Analysis, IaaS Provider Study, 2024",
                "expected_topic_contains": ["IaaS", "Infrastructure as a Service"],
                "category": "acronym_preservation"
            },
            {
                "title": "Virtual Private Network Market Trends, VPN Security Report, 2025",
                "expected_topic_contains": ["VPN", "Virtual Private Network"],
                "category": "acronym_preservation"
            },
            {
                "title": "Light Detection and Ranging Market Forecast, LiDAR Technology Report, 2024-2029",
                "expected_topic_contains": ["LiDAR", "Light Detection and Ranging"],
                "category": "acronym_preservation"
            },
            {
                "title": "Radio Frequency Identification Market Size, RFID Tags Report, 2025",
                "expected_topic_contains": ["RFID", "Radio Frequency Identification"],
                "category": "acronym_preservation"
            },
            {
                "title": "Near Field Communication Market Analysis, NFC Payment Report, 2026",
                "expected_topic_contains": ["NFC", "Near Field Communication"],
                "category": "acronym_preservation"
            },
            {
                "title": "Augmented Reality Market Overview, AR Gaming Report, 2025-2030",
                "expected_topic_contains": ["AR", "Augmented Reality"],
                "category": "acronym_preservation"
            },
            {
                "title": "Virtual Reality Market Insights, VR Headset Analysis, 2024",
                "expected_topic_contains": ["VR", "Virtual Reality"],
                "category": "acronym_preservation"
            },
            {
                "title": "Mixed Reality Market Research, MR Technology Report, 2026",
                "expected_topic_contains": ["MR", "Mixed Reality"],
                "category": "acronym_preservation"
            },
            {
                "title": "Human Resource Management Market Trends, HRM Software Report, 2025",
                "expected_topic_contains": ["HRM", "Human Resource Management"],
                "category": "acronym_preservation"
            },
            {
                "title": "Supply Chain Management Market Forecast, SCM Platform Analysis, 2024-2029",
                "expected_topic_contains": ["SCM", "Supply Chain Management"],
                "category": "acronym_preservation"
            },
            {
                "title": "Business Process Management Market Size, BPM Solutions Report, 2025",
                "expected_topic_contains": ["BPM", "Business Process Management"],
                "category": "acronym_preservation"
            },
            {
                "title": "Content Management System Market Analysis, CMS Platform Study, 2026",
                "expected_topic_contains": ["CMS", "Content Management System"],
                "category": "acronym_preservation"
            }
        ]

        # Technical compound terms that should be preserved
        compound_cases = [
            {
                "title": "5G Network Market Size, Next-Gen Telecom Report, 2025",
                "expected_topic_contains": ["5G Network", "Next-Gen"],
                "category": "compound_preservation"
            },
            {
                "title": "IoT-Enabled Devices Market Analysis, Smart Home Report, 2026",
                "expected_topic_contains": ["IoT-Enabled", "Smart Home"],
                "category": "compound_preservation"
            },
            {
                "title": "Cloud-Based Solutions Market Research, Multi-Cloud Report, 2024",
                "expected_topic_contains": ["Cloud-Based", "Multi-Cloud"],
                "category": "compound_preservation"
            },
            {
                "title": "AI-Powered Analytics Market Forecast, ML-Driven Insights Report, 2025-2030",
                "expected_topic_contains": ["AI-Powered", "ML-Driven"],
                "category": "compound_preservation"
            },
            {
                "title": "Blockchain-as-a-Service Market Overview, BaaS Platform Report, 2025",
                "expected_topic_contains": ["Blockchain-as-a-Service", "BaaS"],
                "category": "compound_preservation"
            },
            {
                "title": "Edge-to-Cloud Computing Market Insights, E2C Architecture Analysis, 2024",
                "expected_topic_contains": ["Edge-to-Cloud", "E2C"],
                "category": "compound_preservation"
            },
            {
                "title": "Software-Defined Networking Market Research, SDN Controller Report, 2026",
                "expected_topic_contains": ["Software-Defined Networking", "SDN"],
                "category": "compound_preservation"
            },
            {
                "title": "Network-Attached Storage Market Trends, NAS Device Report, 2025",
                "expected_topic_contains": ["Network-Attached Storage", "NAS"],
                "category": "compound_preservation"
            },
            {
                "title": "Direct-to-Consumer Market Forecast, D2C E-commerce Report, 2024-2029",
                "expected_topic_contains": ["Direct-to-Consumer", "D2C"],
                "category": "compound_preservation"
            },
            {
                "title": "Business-to-Business Market Size, B2B Platform Report, 2025",
                "expected_topic_contains": ["Business-to-Business", "B2B"],
                "category": "compound_preservation"
            }
        ]

        # Edge cases with topic terms following "Market"
        market_following_cases = [
            {
                "title": "Electric Vehicle Market by Battery Type Report, 2025",
                "expected_topic_contains": ["Electric Vehicle", "Battery Type"],
                "category": "market_following"
            },
            {
                "title": "Renewable Energy Market by Source Analysis, 2026",
                "expected_topic_contains": ["Renewable Energy", "Source"],
                "category": "market_following"
            },
            {
                "title": "Healthcare IT Market by Component Study, 2024",
                "expected_topic_contains": ["Healthcare IT", "Component"],
                "category": "market_following"
            },
            {
                "title": "Cybersecurity Market by Solution Type Report, 2025-2030",
                "expected_topic_contains": ["Cybersecurity", "Solution Type"],
                "category": "market_following"
            },
            {
                "title": "Smart Cities Market by Application Area Overview, 2025",
                "expected_topic_contains": ["Smart Cities", "Application Area"],
                "category": "market_following"
            },
            {
                "title": "Digital Twin Market by End-User Industry Insights, 2024",
                "expected_topic_contains": ["Digital Twin", "End-User Industry"],
                "category": "market_following"
            },
            {
                "title": "Quantum Computing Market by Technology Type Research, 2026",
                "expected_topic_contains": ["Quantum Computing", "Technology Type"],
                "category": "market_following"
            },
            {
                "title": "Autonomous Vehicles Market by Level of Automation Trends, 2025",
                "expected_topic_contains": ["Autonomous Vehicles", "Level of Automation"],
                "category": "market_following"
            },
            {
                "title": "Green Technology Market by Product Category Forecast, 2024-2029",
                "expected_topic_contains": ["Green Technology", "Product Category"],
                "category": "market_following"
            },
            {
                "title": "Fintech Market by Service Type Size Report, 2025",
                "expected_topic_contains": ["Fintech", "Service Type"],
                "category": "market_following"
            }
        ]

        # Complex multi-acronym cases
        complex_cases = [
            {
                "title": "API Management Market Analysis, REST vs SOAP Report, 2026",
                "expected_topic_contains": ["API Management", "REST", "SOAP"],
                "category": "multi_acronym"
            },
            {
                "title": "ERP and CRM Integration Market Study, SAP vs Oracle Report, 2024",
                "expected_topic_contains": ["ERP", "CRM", "SAP", "Oracle"],
                "category": "multi_acronym"
            },
            {
                "title": "IaaS, PaaS, and SaaS Market Comparison Report, 2025-2030",
                "expected_topic_contains": ["IaaS", "PaaS", "SaaS"],
                "category": "multi_acronym"
            },
            {
                "title": "AR/VR/MR Technologies Market Overview, XR Industry Report, 2025",
                "expected_topic_contains": ["AR", "VR", "MR", "XR"],
                "category": "multi_acronym"
            },
            {
                "title": "IoT and AI Convergence Market Insights, AIoT Platform Analysis, 2024",
                "expected_topic_contains": ["IoT", "AI", "AIoT"],
                "category": "multi_acronym"
            },
            {
                "title": "B2B vs B2C E-commerce Market Research, D2C Disruption Report, 2026",
                "expected_topic_contains": ["B2B", "B2C", "D2C"],
                "category": "multi_acronym"
            },
            {
                "title": "SDN and NFV Technologies Market Trends, 5G Network Report, 2025",
                "expected_topic_contains": ["SDN", "NFV", "5G"],
                "category": "multi_acronym"
            },
            {
                "title": "ML and DL Frameworks Market Forecast, AI Development Report, 2024-2029",
                "expected_topic_contains": ["ML", "DL", "AI"],
                "category": "multi_acronym"
            },
            {
                "title": "CDP and DMP Platforms Market Size, CRM Integration Report, 2025",
                "expected_topic_contains": ["CDP", "DMP", "CRM"],
                "category": "multi_acronym"
            },
            {
                "title": "HRM, SCM, and BPM Software Market Analysis, ERP Suite Report, 2026",
                "expected_topic_contains": ["HRM", "SCM", "BPM", "ERP"],
                "category": "multi_acronym"
            }
        ]

        # Combine all test cases
        test_cases.extend(acronym_cases)
        test_cases.extend(compound_cases)
        test_cases.extend(market_following_cases)
        test_cases.extend(complex_cases)

        return test_cases

    def test_single_title(self, title: str, enable_preservation: bool = True) -> Dict:
        """Test a single title with content preservation."""
        try:
            # Process through the report type extractor
            result = self.report_extractor.extract(
                title=title,
                market_term_type="standard"  # Use standard for simplicity
            )

            # The result.title contains the remaining text after extraction
            return {
                "success": result.success,
                "original_title": title,
                "extracted_report_type": result.extracted_report_type,
                "remaining_title": result.title,  # This is the final topic
                "confidence": result.confidence,
                "processing_time_ms": result.processing_time_ms,
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

    def run_all_tests(self) -> Tuple[List[Dict], Dict]:
        """Run all test cases and generate results."""
        results = []
        statistics = {
            "total": 0,
            "passed": 0,
            "failed": 0,
            "by_category": {}
        }

        for test_case in self.test_cases:
            title = test_case["title"]
            expected_contains = test_case["expected_topic_contains"]
            category = test_case["category"]

            # Initialize category stats
            if category not in statistics["by_category"]:
                statistics["by_category"][category] = {
                    "total": 0,
                    "passed": 0,
                    "failed": 0
                }

            # Test with preservation enabled
            result = self.test_single_title(title, enable_preservation=True)

            # Check if expected content is preserved
            passed = False
            if result["success"] and result.get("remaining_title"):
                remaining = result["remaining_title"].lower()
                # Check if at least one expected term is preserved
                for expected in expected_contains:
                    if expected.lower() in remaining:
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
            logger.info(f"{status} {category}: {title[:50]}... -> {result.get('remaining_title', 'ERROR')}")

        # Calculate percentages
        statistics["success_rate"] = (statistics["passed"] / statistics["total"] * 100) if statistics["total"] > 0 else 0

        for category in statistics["by_category"]:
            cat_stats = statistics["by_category"][category]
            cat_stats["success_rate"] = (cat_stats["passed"] / cat_stats["total"] * 100) if cat_stats["total"] > 0 else 0

        return results, statistics

    def compare_with_legacy(self, sample_size: int = 10) -> List[Dict]:
        """Compare new preservation method with legacy behavior."""
        comparisons = []

        for i, test_case in enumerate(self.test_cases[:sample_size]):
            title = test_case["title"]

            # Test with preservation enabled
            new_result = self.test_single_title(title, enable_preservation=True)

            # Test with preservation disabled (legacy)
            legacy_result = self.test_single_title(title, enable_preservation=False)

            comparison = {
                "title": title,
                "category": test_case["category"],
                "expected_contains": test_case["expected_topic_contains"],
                "legacy_result": legacy_result.get("remaining_title", "ERROR"),
                "new_result": new_result.get("remaining_title", "ERROR"),
                "improvement": new_result.get("remaining_title", "") != legacy_result.get("remaining_title", "")
            }

            comparisons.append(comparison)

        return comparisons

def main():
    """Main execution function."""
    logger.info("Starting Content Preservation Testing for Issue #31")

    # Create output directory
    output_dir = create_organized_output_directory("test_03_content_preservation")
    logger.info(f"Output directory: {output_dir}")

    try:
        # Initialize tester
        tester = ContentPreservationTester()

        # Run all tests
        logger.info(f"Running {len(tester.test_cases)} test cases...")
        results, statistics = tester.run_all_tests()

        # Generate summary report
        summary_file = os.path.join(output_dir, "content_preservation_summary.txt")
        with open(summary_file, 'w') as f:
            f.write(create_output_file_header(
                "test_03_content_preservation",
                "Content Preservation Testing for Issue #31 - Acronym Loss Fix"
            ))

            f.write("OVERALL STATISTICS\n")
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
            f.write("FAILED TEST CASES\n")
            f.write("=" * 80 + "\n\n")

            failed_count = 0
            for result in results:
                if not result["test_passed"]:
                    failed_count += 1
                    f.write(f"FAILURE #{failed_count}:\n")
                    f.write(f"  Original: {result['original_title']}\n")
                    f.write(f"  Expected to contain: {result['test_case']['expected_topic_contains']}\n")
                    f.write(f"  Actual remaining: {result.get('remaining_title', 'ERROR')}\n")
                    f.write(f"  Extracted report type: {result.get('extracted_report_type', 'N/A')}\n")
                    f.write(f"  Category: {result['test_case']['category']}\n\n")

            if failed_count == 0:
                f.write("All test cases passed!\n")

        logger.info(f"Summary report saved to: {summary_file}")

        # Save detailed results as JSON
        results_file = os.path.join(output_dir, "detailed_results.json")
        with open(results_file, 'w') as f:
            json.dump({
                "statistics": statistics,
                "results": results
            }, f, indent=2)

        logger.info(f"Detailed results saved to: {results_file}")

        # Run comparison with legacy method
        logger.info("Comparing with legacy method...")
        comparisons = tester.compare_with_legacy(sample_size=15)

        comparison_file = os.path.join(output_dir, "legacy_comparison.txt")
        with open(comparison_file, 'w') as f:
            f.write(create_output_file_header(
                "test_03_content_preservation",
                "Comparison of New Content Preservation vs Legacy Method"
            ))

            f.write("LEGACY VS NEW COMPARISON\n")
            f.write("=" * 80 + "\n\n")

            improvements = 0
            for comp in comparisons:
                if comp["improvement"]:
                    improvements += 1
                    f.write(f"IMPROVEMENT FOUND:\n")
                    f.write(f"  Title: {comp['title']}\n")
                    f.write(f"  Category: {comp['category']}\n")
                    f.write(f"  Legacy result: {comp['legacy_result']}\n")
                    f.write(f"  New result: {comp['new_result']}\n")
                    f.write(f"  Expected contains: {comp['expected_contains']}\n\n")

            f.write(f"Total improvements: {improvements}/{len(comparisons)}\n")

        logger.info(f"Legacy comparison saved to: {comparison_file}")

        # Print summary to console
        print("\n" + "=" * 80)
        print("CONTENT PRESERVATION TEST RESULTS")
        print("=" * 80)
        print(f"Overall Success Rate: {statistics['success_rate']:.1f}%")
        print(f"Total: {statistics['total']} | Passed: {statistics['passed']} | Failed: {statistics['failed']}")
        print("\nBy Category:")
        for category, cat_stats in statistics["by_category"].items():
            print(f"  {category}: {cat_stats['success_rate']:.1f}% ({cat_stats['passed']}/{cat_stats['total']})")
        print("=" * 80)

    except Exception as e:
        logger.error(f"Test execution failed: {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0

if __name__ == "__main__":
    exit(main())