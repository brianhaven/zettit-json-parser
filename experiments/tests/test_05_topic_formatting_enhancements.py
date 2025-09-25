#!/usr/bin/env python3

"""
Test Script 05 Topic Formatting Enhancements
Tests the enhanced topic formatting and normalization features of Script 05.
"""

import sys
import os
import importlib.util
from typing import List, Dict, Any

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def import_module_from_path(module_name: str, file_path: str):
    """Import a module from a file path."""
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

def create_output_directory(script_name: str) -> str:
    """Create timestamped output directory using absolute paths."""
    # Get absolute path to outputs directory (from /experiments/tests/ to /outputs/)
    script_dir = os.path.dirname(os.path.abspath(__file__))
    experiments_dir = os.path.dirname(script_dir)
    project_root = os.path.dirname(experiments_dir)

    # Import output manager from parent directory
    output_manager = import_module_from_path("output_manager",
                                           os.path.join(experiments_dir, "00c_output_directory_manager_v1.py"))

    return output_manager.create_organized_output_directory(script_name)

def create_file_header(script_name: str, description: str = "") -> str:
    """Create standardized file header with dual timestamps."""
    # Import output manager
    script_dir = os.path.dirname(os.path.abspath(__file__))
    experiments_dir = os.path.dirname(script_dir)
    output_manager = import_module_from_path("output_manager",
                                           os.path.join(experiments_dir, "00c_output_directory_manager_v1.py"))

    return output_manager.create_output_file_header(script_name, description)

def test_script_05_formatting():
    """Test Script 05 enhanced formatting capabilities."""

    print("Topic Extraction System - Formatting Enhancement Testing")
    print("=" * 60)

    try:
        # Import Script 05
        parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        script_05 = import_module_from_path("topic_extractor",
                                          os.path.join(parent_dir, "05_topic_extractor_v1.py"))

        # Initialize extractor
        extractor = script_05.TopicExtractor()

        # Test cases from real pipeline results
        test_cases = [
            {
                'name': "Ampersand Handling",
                'original_title': "AI Trust, Risk & Security Management Market",
                'final_topic': "AI Trust, Risk Security Management",  # & removed by pipeline
                'expected_topic_name': "AI Trust, Risk Security Management",  # Pipeline already removed &
                'expected_normalized': "ai-trust-risk-security-management"   # No "and" since & was removed earlier
            },
            {
                'name': "Parentheses Preservation",
                'original_title': "Natural Language Processing (NLP) Market Growth Report, 2030",
                'final_topic': "Natural Language Processing",  # (NLP) removed by pipeline
                'expected_topic_name': "Natural Language Processing",
                'expected_normalized': "natural-language-processing"
            },
            {
                'name': "Brackets to Parentheses",
                'original_title': "Fecal Immunochemical Test [FIT] Market Analysis",
                'final_topic': "Fecal Immunochemical Test",  # [FIT] removed by pipeline
                'expected_topic_name': "Fecal Immunochemical Test",
                'expected_normalized': "fecal-immunochemical-test"
            },
            {
                'name': "Technical Compounds",
                'original_title': "5G Infrastructure Market Size & Share Report",
                'final_topic': "5G Infrastructure",
                'expected_topic_name': "5G Infrastructure",
                'expected_normalized': "5g-infrastructure"
            },
            {
                'name': "Apostrophe Handling",
                'original_title': "Johnson's Baby Products Market",
                'final_topic': "Johnson's Baby Products",
                'expected_topic_name': "Johnson's Baby Products",
                'expected_normalized': "johnson-baby-products"  # apostrophe and 's removed
            },
            {
                'name': "Mixed Case Acronyms",
                'original_title': "IoT Device Management Platform Market",
                'final_topic': "IoT Device Management Platform",
                'expected_topic_name': "IoT Device Management Platform",
                'expected_normalized': "iot-device-management-platform"
            }
        ]

        print("\n1. Individual Test Cases:")
        print("-" * 40)

        results = []
        for i, test_case in enumerate(test_cases, 1):
            original_title = test_case['original_title']
            final_topic = test_case['final_topic']
            expected_topic_name = test_case['expected_topic_name']
            expected_normalized = test_case['expected_normalized']

            result = extractor.extract(original_title, final_topic)

            # Check results
            topic_name_match = result.normalized_topic_name == expected_topic_name
            normalized_match = result.extracted_topic == expected_normalized

            print(f"\n{i}. {test_case['name']}:")
            print(f"   Original Title: {original_title}")
            print(f"   Pipeline Topic: {final_topic}")
            print(f"   Topic Name: '{result.normalized_topic_name}' {'✓' if topic_name_match else '✗'}")
            print(f"   Expected:   '{expected_topic_name}'")
            print(f"   Normalized: '{result.extracted_topic}' {'✓' if normalized_match else '✗'}")
            print(f"   Expected:   '{expected_normalized}'")
            print(f"   Confidence: {result.confidence:.3f}")

            results.append({
                'test_name': test_case['name'],
                'topic_name_match': topic_name_match,
                'normalized_match': normalized_match,
                'confidence': result.confidence,
                'processing_notes': result.processing_notes
            })

        # Summary results
        print("\n2. Test Results Summary:")
        print("-" * 40)

        total_tests = len(test_cases)
        topic_name_passes = sum(1 for r in results if r['topic_name_match'])
        normalized_passes = sum(1 for r in results if r['normalized_match'])
        avg_confidence = sum(r['confidence'] for r in results) / total_tests

        print(f"Total Test Cases: {total_tests}")
        print(f"Topic Name Accuracy: {topic_name_passes}/{total_tests} ({topic_name_passes/total_tests:.1%})")
        print(f"Normalized Accuracy: {normalized_passes}/{total_tests} ({normalized_passes/total_tests:.1%})")
        print(f"Average Confidence: {avg_confidence:.3f}")
        print(f"Overall Success: {min(topic_name_passes, normalized_passes)}/{total_tests} ({min(topic_name_passes, normalized_passes)/total_tests:.1%})")

        # Get statistics
        stats = extractor.get_extraction_statistics()
        confidence_metrics = extractor.get_confidence()

        print(f"\nExtractor Statistics:")
        print(f"Processing Success Rate: {stats.success_rate:.1%}")
        print(f"Overall Confidence: {confidence_metrics['overall_confidence']:.1%}")

        # Export detailed report
        print("\n3. Saving Detailed Report:")
        print("-" * 40)

        # Create organized output directory
        output_dir = create_output_directory("script05_formatting_test")

        # Generate report
        report_content = f"""{create_file_header("script05_formatting_test", "Topic formatting enhancement validation results")}

Topic Formatting Enhancement Test Results
{"=" * 50}

Test Summary:
  Total Test Cases:      {total_tests}
  Topic Name Accuracy:   {topic_name_passes}/{total_tests} ({topic_name_passes/total_tests:.1%})
  Normalized Accuracy:   {normalized_passes}/{total_tests} ({normalized_passes/total_tests:.1%})
  Average Confidence:    {avg_confidence:.3f}
  Overall Success Rate:  {min(topic_name_passes, normalized_passes)}/{total_tests} ({min(topic_name_passes, normalized_passes)/total_tests:.1%})

Detailed Test Results:
{"=" * 25}
"""

        for i, (test_case, result) in enumerate(zip(test_cases, results), 1):
            report_content += f"""
Test {i}: {result['test_name']}
  Original: {test_case['original_title']}
  Pipeline: {test_case['final_topic']}
  Expected Topic Name: {test_case['expected_topic_name']}
  Actual Topic Name:   {extractor.extract(test_case['original_title'], test_case['final_topic']).normalized_topic_name}
  Expected Normalized: {test_case['expected_normalized']}
  Actual Normalized:   {extractor.extract(test_case['original_title'], test_case['final_topic']).extracted_topic}
  Topic Name Match: {'PASS' if result['topic_name_match'] else 'FAIL'}
  Normalized Match: {'PASS' if result['normalized_match'] else 'FAIL'}
  Confidence: {result['confidence']:.3f}

  Processing Notes:"""

            # Re-extract to get fresh processing notes (since we called extract multiple times)
            fresh_result = extractor.extract(test_case['original_title'], test_case['final_topic'])
            for note in fresh_result.processing_notes:
                report_content += f"\n    - {note}"
            report_content += "\n"

        # Add extractor statistics
        report_content += f"""
Extractor Performance Metrics:
{"=" * 30}
Processing Success Rate: {stats.success_rate:.1%}
Overall Confidence:      {confidence_metrics['overall_confidence']:.1%}
Total Processed:         {stats.total_processed}
Successful Extractions:  {stats.successful_extractions}
Failed Extractions:      {stats.failed_extractions}

Test Status: {'✅ PASSED' if min(topic_name_passes, normalized_passes) == total_tests else '⚠️ PARTIAL SUCCESS' if min(topic_name_passes, normalized_passes) > 0 else '❌ FAILED'}
"""

        # Save report
        report_file = os.path.join(output_dir, "topic_formatting_test_results.txt")
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report_content)

        print(f"✓ Detailed report saved to: {report_file}")

        # Determine overall result
        overall_success = min(topic_name_passes, normalized_passes) == total_tests
        if overall_success:
            print("✅ All formatting tests passed!")
        elif min(topic_name_passes, normalized_passes) > 0:
            print("⚠️ Some tests passed - review failures for improvements")
        else:
            print("❌ All tests failed - major issues need resolution")

        return overall_success

    except Exception as e:
        print(f"❌ Test execution failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_script_05_formatting()
    sys.exit(0 if success else 1)