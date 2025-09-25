#!/usr/bin/env python3
"""
Test script to validate Issue #26 regression fix for word-based separator cleanup.
Tests the enhanced _clean_reconstructed_type() method in Script 03 v4.

This script specifically tests:
1. Original "&" symbol separator cleanup (existing fix)
2. Word-based separator cleanup for "And", "Plus", "Or" (regression fix)
3. Mixed separator scenarios
4. Edge cases to ensure no regressions
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

class Issue26RegressionTester:
    """Test harness for Issue #26 regression fix validation."""

    def __init__(self, output_dir: str):
        self.output_dir = output_dir
        self.test_results = []

        # Import Script 03 v4
        parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
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
        self.report_extractor = script03.PureDictionaryReportTypeExtractor(self.pattern_lib_manager)

        logger.info("Initialized Script 03 v4 for testing")

    def test_separator_cleanup(self, test_cases: List[Dict[str, str]]) -> Dict[str, Any]:
        """Test separator cleanup functionality with provided test cases."""
        results = {
            'total_tests': len(test_cases),
            'passed': 0,
            'failed': 0,
            'test_details': []
        }

        for i, test_case in enumerate(test_cases, 1):
            input_title = test_case.get('input', '')
            expected_output = test_case.get('expected', '')
            test_type = test_case.get('type', 'unknown')

            # Process title through Script 03
            try:
                result = self.report_extractor.extract(input_title)
                actual_output = result.extracted_report_type

                # Check if the output matches expected
                passed = actual_output == expected_output

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
                    'expected': expected_output,
                    'actual': actual_output,
                    'status': status,
                    'passed': passed
                }

                results['test_details'].append(test_detail)

                logger.info(f"Test {i} [{test_type}]: {status}")
                logger.info(f"  Input: {input_title}")
                logger.info(f"  Expected: {expected_output}")
                logger.info(f"  Actual: {actual_output}")

            except Exception as e:
                results['failed'] += 1
                test_detail = {
                    'test_number': i,
                    'test_type': test_type,
                    'input': input_title,
                    'expected': expected_output,
                    'actual': f"ERROR: {str(e)}",
                    'status': "❌ ERROR",
                    'passed': False
                }
                results['test_details'].append(test_detail)
                logger.error(f"Test {i} failed with error: {str(e)}")

        return results

    def test_real_world_examples(self) -> Dict[str, Any]:
        """Test with real-world examples from the 200-document test that showed regressions."""
        real_world_cases = [
            {
                'input': 'Timing Relay Market Size, Share And Growth Report, 2024-2030',
                'expected': 'Market Size, Share Growth Report',
                'type': 'word_separator_And',
                'description': 'Real case from 200-doc test showing "And" artifact'
            },
            {
                'input': 'Polymeric Biomaterials Market Size And Share Report, 2025',
                'expected': 'Market Size Share Report',
                'type': 'word_separator_And',
                'description': 'Real case showing "And" between Size and Share'
            },
            {
                'input': 'Gift Wrapping Products Market Size And Share Report, 2024-2029',
                'expected': 'Market Size Share Report',
                'type': 'word_separator_And',
                'description': 'Real case with date range and "And" separator'
            },
            {
                'input': 'Aviation IoT Market Size, Share And Growth Report, 2024',
                'expected': 'Market Size, Share Growth Report',
                'type': 'word_separator_And',
                'description': 'Mixed comma and "And" separators'
            },
            {
                'input': 'Market Analysis Plus Forecast Report, 2025',
                'expected': 'Market Analysis Forecast Report',
                'type': 'word_separator_Plus',
                'description': 'Testing "Plus" word separator'
            },
            {
                'input': 'Market Trends Or Outlook Report, 2024-2030',
                'expected': 'Market Trends Outlook Report',
                'type': 'word_separator_Or',
                'description': 'Testing "Or" word separator'
            }
        ]

        return self.test_separator_cleanup(real_world_cases)

    def test_comprehensive_scenarios(self) -> Dict[str, Any]:
        """Test comprehensive scenarios including edge cases."""
        comprehensive_cases = [
            # Symbol separator tests (existing functionality)
            {
                'input': 'Market & Size & Share & Report',
                'expected': 'Market Size Share Report',
                'type': 'symbol_ampersand'
            },
            {
                'input': 'Market & Trends & Analysis',
                'expected': 'Market Trends Analysis',
                'type': 'symbol_ampersand'
            },

            # Word separator tests (new functionality)
            {
                'input': 'Market Size And Share Report',
                'expected': 'Market Size Share Report',
                'type': 'word_and'
            },
            {
                'input': 'Market Analysis And Forecast Report',
                'expected': 'Market Analysis Forecast Report',
                'type': 'word_and'
            },
            {
                'input': 'Market Growth Plus Trends Report',
                'expected': 'Market Growth Trends Report',
                'type': 'word_plus'
            },
            {
                'input': 'Market Overview Or Summary Report',
                'expected': 'Market Overview Summary Report',
                'type': 'word_or'
            },

            # Mixed separator tests
            {
                'input': 'Market & Size And Share Report',
                'expected': 'Market Size Share Report',
                'type': 'mixed_ampersand_and'
            },
            {
                'input': 'Market Size & Trends Plus Growth Report',
                'expected': 'Market Size Trends Growth Report',
                'type': 'mixed_ampersand_plus'
            },

            # Case insensitive tests
            {
                'input': 'Market Size AND Share Report',
                'expected': 'Market Size Share Report',
                'type': 'uppercase_AND'
            },
            {
                'input': 'Market Analysis and Forecast Report',
                'expected': 'Market Analysis Forecast Report',
                'type': 'lowercase_and'
            },
            {
                'input': 'Market Growth PLUS Trends Report',
                'expected': 'Market Growth Trends Report',
                'type': 'uppercase_PLUS'
            },

            # Edge cases - ensure we don't over-clean
            {
                'input': 'Orlando Market Analysis Report',
                'expected': 'Market Analysis Report',
                'type': 'edge_orlando',
                'description': 'Should not remove "Or" from Orlando'
            },
            {
                'input': 'Portland Market Study Report',
                'expected': 'Market Study Report',
                'type': 'edge_portland',
                'description': 'Should not remove "and" from Portland'
            }
        ]

        return self.test_separator_cleanup(comprehensive_cases)

    def generate_test_report(self, real_world_results: Dict, comprehensive_results: Dict):
        """Generate comprehensive test report."""
        report_content = create_output_file_header(
            "Issue #26 Regression Fix Test Report",
            "Validation of enhanced separator cleanup functionality"
        )

        # Summary section
        report_content += f"""
## TEST SUMMARY

### Real-World Examples Test
- Total Tests: {real_world_results['total_tests']}
- Passed: {real_world_results['passed']} ✅
- Failed: {real_world_results['failed']} ❌
- Success Rate: {(real_world_results['passed'] / real_world_results['total_tests'] * 100):.1f}%

### Comprehensive Scenarios Test
- Total Tests: {comprehensive_results['total_tests']}
- Passed: {comprehensive_results['passed']} ✅
- Failed: {comprehensive_results['failed']} ❌
- Success Rate: {(comprehensive_results['passed'] / comprehensive_results['total_tests'] * 100):.1f}%

### Overall Results
- Total Tests Run: {real_world_results['total_tests'] + comprehensive_results['total_tests']}
- Total Passed: {real_world_results['passed'] + comprehensive_results['passed']}
- Total Failed: {real_world_results['failed'] + comprehensive_results['failed']}
- Overall Success Rate: {((real_world_results['passed'] + comprehensive_results['passed']) / (real_world_results['total_tests'] + comprehensive_results['total_tests']) * 100):.1f}%

{'='*80}

## REAL-WORLD EXAMPLES TEST DETAILS

These test cases are taken directly from the 200-document pipeline test that revealed the regression.

"""
        # Add real-world test details
        for test in real_world_results['test_details']:
            report_content += f"""
### Test #{test['test_number']}: {test['test_type']}
- **Status:** {test['status']}
- **Input:** `{test['input']}`
- **Expected:** `{test['expected']}`
- **Actual:** `{test['actual']}`
{f"- **Description:** {test.get('description', '')}" if test.get('description') else ''}
"""

        report_content += f"""
{'='*80}

## COMPREHENSIVE SCENARIOS TEST DETAILS

These test cases cover all separator types and edge cases to ensure robust functionality.

"""
        # Add comprehensive test details
        for test in comprehensive_results['test_details']:
            report_content += f"""
### Test #{test['test_number']}: {test['test_type']}
- **Status:** {test['status']}
- **Input:** `{test['input']}`
- **Expected:** `{test['expected']}`
- **Actual:** `{test['actual']}`
{f"- **Description:** {test.get('description', '')}" if test.get('description') else ''}
"""

        # Add conclusion
        report_content += f"""
{'='*80}

## CONCLUSION

"""
        if (real_world_results['failed'] + comprehensive_results['failed']) == 0:
            report_content += """
✅ **ALL TESTS PASSED!** The Issue #26 regression fix successfully handles:
- Symbol separators (&)
- Word-based separators (And, Plus, Or)
- Mixed separator scenarios
- Case-insensitive matching
- Edge cases (words containing separator substrings)

The enhanced `_clean_reconstructed_type()` method in Script 03 v4 now properly removes all types of separator artifacts while preserving meaningful content.
"""
        else:
            report_content += f"""
⚠️ **TESTS FAILED!** {real_world_results['failed'] + comprehensive_results['failed']} test(s) did not pass.

Please review the failed test cases above and adjust the implementation accordingly.
"""

        # Write report to file
        report_path = os.path.join(self.output_dir, 'issue_26_regression_fix_test_report.md')
        with open(report_path, 'w') as f:
            f.write(report_content)

        logger.info(f"Test report written to: {report_path}")

        # Also save JSON results for programmatic access
        json_results = {
            'timestamp': datetime.now(pytz.timezone('America/Los_Angeles')).isoformat(),
            'real_world_results': real_world_results,
            'comprehensive_results': comprehensive_results,
            'summary': {
                'total_tests': real_world_results['total_tests'] + comprehensive_results['total_tests'],
                'total_passed': real_world_results['passed'] + comprehensive_results['passed'],
                'total_failed': real_world_results['failed'] + comprehensive_results['failed'],
                'success_rate': ((real_world_results['passed'] + comprehensive_results['passed']) /
                               (real_world_results['total_tests'] + comprehensive_results['total_tests']) * 100)
            }
        }

        json_path = os.path.join(self.output_dir, 'test_results.json')
        with open(json_path, 'w') as f:
            json.dump(json_results, f, indent=2)

        logger.info(f"JSON results saved to: {json_path}")

def main():
    """Main test execution."""
    logger.info("Starting Issue #26 Regression Fix Validation")
    logger.info("="*80)

    # Create output directory
    output_dir = create_organized_output_directory('issue_26_regression_fix_test')

    # Initialize tester
    tester = Issue26RegressionTester(output_dir)

    # Run real-world example tests
    logger.info("\n" + "="*80)
    logger.info("TESTING REAL-WORLD EXAMPLES")
    logger.info("="*80)
    real_world_results = tester.test_real_world_examples()

    # Run comprehensive scenario tests
    logger.info("\n" + "="*80)
    logger.info("TESTING COMPREHENSIVE SCENARIOS")
    logger.info("="*80)
    comprehensive_results = tester.test_comprehensive_scenarios()

    # Generate report
    logger.info("\n" + "="*80)
    logger.info("GENERATING TEST REPORT")
    logger.info("="*80)
    tester.generate_test_report(real_world_results, comprehensive_results)

    # Print summary
    total_tests = real_world_results['total_tests'] + comprehensive_results['total_tests']
    total_passed = real_world_results['passed'] + comprehensive_results['passed']
    total_failed = real_world_results['failed'] + comprehensive_results['failed']

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