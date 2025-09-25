#!/usr/bin/env python3
"""
Test script to validate Issue #26 regression fix for topic cleanup.
This script tests that word-based separators (And, Plus, Or) are properly removed from the remaining title/topic.

The real issue is not with the report type reconstruction, but with what remains in the topic after extraction.
"""

import sys
import os
import json
import logging
from datetime import datetime
import pytz
from typing import Dict, List, Any
from dotenv import load_dotenv

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Dynamic imports
import importlib.util

def import_module_from_path(module_name: str, file_path: str):
    """Import a module from a file path."""
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

def create_organized_output_directory(script_name: str) -> str:
    """Create organized output directory with YYYY/MM/DD structure."""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    experiments_dir = os.path.dirname(script_dir)
    project_root = os.path.dirname(experiments_dir)
    outputs_dir = os.path.join(project_root, 'outputs')

    # Create YYYY/MM/DD structure
    pdt = pytz.timezone('America/Los_Angeles')
    now_pdt = datetime.now(pdt)

    year_dir = os.path.join(outputs_dir, str(now_pdt.year))
    month_dir = os.path.join(year_dir, f"{now_pdt.month:02d}")
    day_dir = os.path.join(month_dir, f"{now_pdt.day:02d}")

    # Create timestamped subdirectory
    timestamp = now_pdt.strftime('%Y%m%d_%H%M%S')
    output_dir = os.path.join(day_dir, f"{timestamp}_{script_name}")

    os.makedirs(output_dir, exist_ok=True)
    logger.info(f"Created output directory: {output_dir}")

    return output_dir

def create_output_file_header(script_name: str, description: str = "") -> str:
    """Create standardized file header with dual timestamps."""
    pdt = pytz.timezone('America/Los_Angeles')
    now_pdt = datetime.now(pdt)
    now_utc = datetime.now(pytz.UTC)

    header = f"""# {script_name.replace('_', ' ').title()} Output
# {description}
# Analysis Date (PDT): {now_pdt.strftime('%Y-%m-%d %H:%M:%S %Z')}
# Analysis Date (UTC): {now_utc.strftime('%Y-%m-%d %H:%M:%S %Z')}
{'='*80}

"""
    return header

class Issue26TopicCleanupTester:
    """Test harness for Issue #26 regression fix - topic cleanup validation."""

    def __init__(self, output_dir: str):
        self.output_dir = output_dir
        self.test_results = []

        # Import Scripts 02 and 03
        parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

        script02 = import_module_from_path(
            "date_extractor",
            os.path.join(parent_dir, "02_date_extractor_v1.py")
        )
        script03 = import_module_from_path(
            "report_extractor",
            os.path.join(parent_dir, "03_report_type_extractor_v4.py")
        )

        # Import PatternLibraryManager
        pattern_manager = import_module_from_path(
            "pattern_library_manager",
            os.path.join(parent_dir, "00b_pattern_library_manager_v1.py")
        )

        # Initialize components
        self.pattern_lib_manager = pattern_manager.PatternLibraryManager(os.getenv('MONGODB_URI'))
        self.date_extractor = script02.EnhancedDateExtractor(self.pattern_lib_manager)
        self.report_extractor = script03.PureDictionaryReportTypeExtractor(self.pattern_lib_manager)

        logger.info("Initialized Script 02 and 03 for topic cleanup testing")

    def test_topic_cleanup(self, test_cases: List[Dict[str, str]]) -> Dict[str, Any]:
        """Test that topics are properly cleaned of word separators."""
        results = {
            'total_tests': len(test_cases),
            'passed': 0,
            'failed': 0,
            'test_details': []
        }

        for i, test_case in enumerate(test_cases, 1):
            input_title = test_case.get('input', '')
            expected_topic = test_case.get('expected_topic', '')
            test_type = test_case.get('type', 'unknown')
            description = test_case.get('description', '')

            try:
                # Step 1: Extract date
                date_result = self.date_extractor.extract(input_title)
                title_after_date = date_result.title

                # Step 2: Extract report type and get remaining title (which becomes the topic)
                report_result = self.report_extractor.extract(title_after_date)
                actual_topic = report_result.title  # This is the remaining title after report type extraction

                # Check if the topic matches expected
                passed = actual_topic == expected_topic

                if passed:
                    results['passed'] += 1
                    status = "✅ PASS"
                else:
                    results['failed'] += 1
                    status = "❌ FAIL"

                test_detail = {
                    'test_number': i,
                    'test_type': test_type,
                    'input': input_title,
                    'expected_topic': expected_topic,
                    'actual_topic': actual_topic,
                    'extracted_date': date_result.extracted_date_range,
                    'extracted_report_type': report_result.extracted_report_type,
                    'status': status,
                    'passed': passed,
                    'description': description
                }

                results['test_details'].append(test_detail)

                logger.info(f"Test {i} [{test_type}]: {status}")
                logger.info(f"  Input: {input_title}")
                logger.info(f"  Date extracted: {date_result.extracted_date_range}")
                logger.info(f"  Report type: {report_result.extracted_report_type}")
                logger.info(f"  Expected topic: {expected_topic}")
                logger.info(f"  Actual topic: {actual_topic}")

            except Exception as e:
                results['failed'] += 1
                test_detail = {
                    'test_number': i,
                    'test_type': test_type,
                    'input': input_title,
                    'expected_topic': expected_topic,
                    'actual_topic': f"ERROR: {str(e)}",
                    'status': "❌ ERROR",
                    'passed': False
                }
                results['test_details'].append(test_detail)
                logger.error(f"Test {i} failed with error: {str(e)}")

        return results

    def test_real_world_problems(self) -> Dict[str, Any]:
        """Test with the actual problematic cases from the 200-document test."""
        real_world_cases = [
            {
                'input': 'Timing Relay Market Size, Share And Growth Report, 2024-2030',
                'expected_topic': 'Timing Relay',
                'type': 'word_separator_And',
                'description': 'Original case showing "And" artifact in topic'
            },
            {
                'input': 'Polymeric Biomaterials Market Size And Share Report, 2025',
                'expected_topic': 'Polymeric Biomaterials',
                'type': 'word_separator_And',
                'description': 'Another case with "And" between Size and Share'
            },
            {
                'input': 'Gift Wrapping Products Market Size And Share Report, 2024-2029',
                'expected_topic': 'Gift Wrapping Products',
                'type': 'word_separator_And',
                'description': 'Case with date range and "And" separator'
            },
            {
                'input': 'Aviation IoT Market Size, Share And Growth Report, 2024',
                'expected_topic': 'Aviation IoT',
                'type': 'mixed_comma_And',
                'description': 'Mixed comma and "And" separators'
            },
            {
                'input': 'Smart Materials Market Analysis Plus Forecast, 2025-2030',
                'expected_topic': 'Smart Materials',
                'type': 'word_separator_Plus',
                'description': 'Testing "Plus" word separator'
            },
            {
                'input': 'Electric Vehicles Market Trends Or Outlook, 2024-2035',
                'expected_topic': 'Electric Vehicles',
                'type': 'word_separator_Or',
                'description': 'Testing "Or" word separator'
            },
            {
                'input': 'Nanotechnology Market Size & Share And Growth Report, 2025',
                'expected_topic': 'Nanotechnology',
                'type': 'mixed_ampersand_And',
                'description': 'Mixed & symbol and "And" word separators'
            }
        ]

        return self.test_topic_cleanup(real_world_cases)

    def test_edge_cases(self) -> Dict[str, Any]:
        """Test edge cases to ensure we don't over-clean legitimate words."""
        edge_cases = [
            {
                'input': 'Portland Oregon Market Analysis Report, 2025',
                'expected_topic': 'Portland Oregon',
                'type': 'edge_portland_oregon',
                'description': 'Should not remove "Or" from Oregon'
            },
            {
                'input': 'Orlando Tourism Market Study, 2024-2026',
                'expected_topic': 'Orlando Tourism',
                'type': 'edge_orlando',
                'description': 'Should not remove "Or" from Orlando'
            },
            {
                'input': 'Anderson Consulting Market Research Report, 2025',
                'expected_topic': 'Anderson Consulting',
                'type': 'edge_anderson',
                'description': 'Should not remove "and" from Anderson'
            },
            {
                'input': 'Plus-Size Fashion Market Analysis, 2024',
                'expected_topic': 'Plus-Size Fashion',
                'type': 'edge_plus_size',
                'description': 'Should not remove "Plus" from Plus-Size'
            }
        ]

        return self.test_topic_cleanup(edge_cases)

    def generate_test_report(self, real_world_results: Dict, edge_case_results: Dict):
        """Generate comprehensive test report for topic cleanup."""
        report_content = create_output_file_header(
            "Issue #26 Topic Cleanup Test Report",
            "Validation of word separator removal from topics/remaining titles"
        )

        # Summary section
        report_content += f"""
## TEST SUMMARY

### Real-World Problems Test
- Total Tests: {real_world_results['total_tests']}
- Passed: {real_world_results['passed']} ✅
- Failed: {real_world_results['failed']} ❌
- Success Rate: {(real_world_results['passed'] / real_world_results['total_tests'] * 100):.1f}%

### Edge Cases Test
- Total Tests: {edge_case_results['total_tests']}
- Passed: {edge_case_results['passed']} ✅
- Failed: {edge_case_results['failed']} ❌
- Success Rate: {(edge_case_results['passed'] / edge_case_results['total_tests'] * 100):.1f}%

### Overall Results
- Total Tests Run: {real_world_results['total_tests'] + edge_case_results['total_tests']}
- Total Passed: {real_world_results['passed'] + edge_case_results['passed']}
- Total Failed: {real_world_results['failed'] + edge_case_results['failed']}
- Overall Success Rate: {((real_world_results['passed'] + edge_case_results['passed']) / (real_world_results['total_tests'] + edge_case_results['total_tests']) * 100):.1f}%

{'='*80}

## REAL-WORLD PROBLEMS TEST DETAILS

These are the actual cases that showed "And" artifacts in topics from the 200-document test.

"""
        # Add real-world test details
        for test in real_world_results['test_details']:
            report_content += f"""
### Test #{test['test_number']}: {test['test_type']}
- **Status:** {test['status']}
- **Input:** `{test['input']}`
- **Extracted Date:** `{test.get('extracted_date', 'N/A')}`
- **Extracted Report Type:** `{test.get('extracted_report_type', 'N/A')}`
- **Expected Topic:** `{test['expected_topic']}`
- **Actual Topic:** `{test['actual_topic']}`
- **Description:** {test.get('description', '')}
"""

        report_content += f"""
{'='*80}

## EDGE CASES TEST DETAILS

These test cases ensure we don't over-clean legitimate words containing separator substrings.

"""
        # Add edge case test details
        for test in edge_case_results['test_details']:
            report_content += f"""
### Test #{test['test_number']}: {test['test_type']}
- **Status:** {test['status']}
- **Input:** `{test['input']}`
- **Extracted Date:** `{test.get('extracted_date', 'N/A')}`
- **Extracted Report Type:** `{test.get('extracted_report_type', 'N/A')}`
- **Expected Topic:** `{test['expected_topic']}`
- **Actual Topic:** `{test['actual_topic']}`
- **Description:** {test.get('description', '')}
"""

        # Add conclusion
        report_content += f"""
{'='*80}

## CONCLUSION

"""
        if (real_world_results['failed'] + edge_case_results['failed']) == 0:
            report_content += """
✅ **ALL TESTS PASSED!** The Issue #26 regression fix successfully:
- Removes word-based separators (And, Plus, Or) from topics
- Preserves legitimate words containing separator substrings
- Properly cleans topics after report type extraction
- Handles mixed separator scenarios

The enhanced cleanup logic in Script 03 v4 now properly removes separator artifacts from the remaining title (topic) while preserving meaningful content.
"""
        else:
            report_content += f"""
⚠️ **TESTS FAILED!** {real_world_results['failed'] + edge_case_results['failed']} test(s) did not pass.

Please review the failed test cases above and adjust the implementation accordingly.
"""

        # Write report to file
        report_path = os.path.join(self.output_dir, 'issue_26_topic_cleanup_test_report.md')
        with open(report_path, 'w') as f:
            f.write(report_content)

        logger.info(f"Test report written to: {report_path}")

        # Also save JSON results
        json_results = {
            'timestamp': datetime.now(pytz.timezone('America/Los_Angeles')).isoformat(),
            'real_world_results': real_world_results,
            'edge_case_results': edge_case_results,
            'summary': {
                'total_tests': real_world_results['total_tests'] + edge_case_results['total_tests'],
                'total_passed': real_world_results['passed'] + edge_case_results['passed'],
                'total_failed': real_world_results['failed'] + edge_case_results['failed'],
                'success_rate': ((real_world_results['passed'] + edge_case_results['passed']) /
                               (real_world_results['total_tests'] + edge_case_results['total_tests']) * 100)
            }
        }

        json_path = os.path.join(self.output_dir, 'test_results.json')
        with open(json_path, 'w') as f:
            json.dump(json_results, f, indent=2)

        logger.info(f"JSON results saved to: {json_path}")

def main():
    """Main test execution."""
    logger.info("Starting Issue #26 Topic Cleanup Validation")
    logger.info("="*80)

    # Create output directory
    output_dir = create_organized_output_directory('issue_26_topic_cleanup_test')

    # Initialize tester
    tester = Issue26TopicCleanupTester(output_dir)

    # Run real-world problem tests
    logger.info("\n" + "="*80)
    logger.info("TESTING REAL-WORLD PROBLEMS")
    logger.info("="*80)
    real_world_results = tester.test_real_world_problems()

    # Run edge case tests
    logger.info("\n" + "="*80)
    logger.info("TESTING EDGE CASES")
    logger.info("="*80)
    edge_case_results = tester.test_edge_cases()

    # Generate report
    logger.info("\n" + "="*80)
    logger.info("GENERATING TEST REPORT")
    logger.info("="*80)
    tester.generate_test_report(real_world_results, edge_case_results)

    # Print summary
    total_tests = real_world_results['total_tests'] + edge_case_results['total_tests']
    total_passed = real_world_results['passed'] + edge_case_results['passed']
    total_failed = real_world_results['failed'] + edge_case_results['failed']

    logger.info("\n" + "="*80)
    logger.info("FINAL SUMMARY")
    logger.info("="*80)
    logger.info(f"Total Tests: {total_tests}")
    logger.info(f"Passed: {total_passed} ✅")
    logger.info(f"Failed: {total_failed} ❌")
    logger.info(f"Success Rate: {(total_passed / total_tests * 100):.1f}%")

    if total_failed == 0:
        logger.info("\n✅ ALL TESTS PASSED! Issue #26 regression fix is working correctly.")
    else:
        logger.warning(f"\n⚠️ {total_failed} test(s) failed. Please review the test report.")

    logger.info(f"\nOutput directory: {output_dir}")
    logger.info("Test validation complete!")

if __name__ == "__main__":
    main()