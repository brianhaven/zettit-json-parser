#!/usr/bin/env python3
"""
Integration test for Issue #23: Date Artifact Cleanup Enhancement
Tests the complete pipeline with real market research titles to ensure
the fix doesn't break existing functionality.
"""

import os
import sys
from pathlib import Path
from datetime import datetime
import pytz
import json
import importlib.util
from typing import Dict, Any, List
from pymongo import MongoClient
from dotenv import load_dotenv

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Load environment variables
load_dotenv()

# Import modules dynamically
def import_module_from_path(module_name: str, file_path: str):
    """Import a module from a file path."""
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

# Create output directory
def create_organized_output_directory(script_name: str) -> str:
    """Create organized output directory with YYYY/MM/DD structure."""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    experiments_dir = os.path.dirname(script_dir)
    project_root = os.path.dirname(experiments_dir)
    outputs_dir = os.path.join(project_root, 'outputs')

    # Create timestamp in Pacific Time
    pdt = pytz.timezone('America/Los_Angeles')
    now = datetime.now(pdt)

    # Create YYYY/MM/DD directory structure
    year_dir = os.path.join(outputs_dir, now.strftime('%Y'))
    month_dir = os.path.join(year_dir, now.strftime('%m'))
    day_dir = os.path.join(month_dir, now.strftime('%d'))

    # Create timestamped subdirectory
    timestamp = now.strftime('%Y%m%d_%H%M%S')
    output_dir = os.path.join(day_dir, f"{timestamp}_{script_name}")
    os.makedirs(output_dir, exist_ok=True)

    return output_dir

# Create file header with dual timestamps
def create_file_header(script_name: str, description: str = "") -> str:
    """Create standardized file header with dual timestamps."""
    pdt = pytz.timezone('America/Los_Angeles')
    utc = pytz.timezone('UTC')
    now_pdt = datetime.now(pdt)
    now_utc = datetime.now(utc)

    header = f"""================================================================================
{script_name.upper()} - {description}
================================================================================
Analysis Date (PDT): {now_pdt.strftime('%Y-%m-%d %H:%M:%S')} PDT
Analysis Date (UTC): {now_utc.strftime('%Y-%m-%d %H:%M:%S')} UTC
================================================================================

"""
    return header

def main():
    """Run integration test for Issue #23 fix."""

    # Import all required modules
    parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

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
    script05 = import_module_from_path("topic_extractor",
                                      os.path.join(parent_dir, "05_topic_extractor_v1.py"))

    # Initialize PatternLibraryManager
    pattern_lib_manager = pattern_manager.PatternLibraryManager(os.getenv('MONGODB_URI'))

    # Initialize all components (all use PatternLibraryManager now)
    market_classifier = script01.MarketTermClassifier(pattern_lib_manager)
    date_extractor = script02.EnhancedDateExtractor(pattern_lib_manager)
    report_extractor = script03.PureDictionaryReportTypeExtractor(pattern_lib_manager)
    geo_detector = script04.GeographicEntityDetector(pattern_lib_manager)  # v2 uses PatternLibraryManager
    topic_extractor = script05.TopicExtractor(pattern_lib_manager)

    # Test titles that could potentially have date artifacts
    test_titles = [
        # Titles with dates in various formats that should be cleanly removed
        "Global AI Market Analysis, 2024-2030",
        "North America Cloud Computing Market Forecast to 2035",
        "APAC Robotics Market (2025-2032)",
        "European IoT Market Study [2024]",
        "Machine Learning in Healthcare Market, Forecast to 2030",

        # Titles that might create artifacts after date removal
        "Blockchain Market Analysis () 2024-2029",
        "5G Network Market [] Through 2031",
        "Quantum Computing Market, 2024 to 2030",
        "Edge Computing Market Analysis, Forecast to",

        # Complex titles with multiple components
        "Global Artificial Intelligence (AI) in Healthcare Market Analysis, Forecast to 2030",
        "North America Machine Learning Market for Retail, 2024-2029",
        "APAC Cloud Computing Market in Banking and Financial Services (2025-2031)",

        # Titles without dates (should remain unchanged)
        "Global Digital Transformation Market Analysis",
        "IoT Platform Market Overview",
        "Cybersecurity Market Trends and Opportunities"
    ]

    # Create output directory
    output_dir = create_organized_output_directory("test_issue_23_integration")

    # Process each title through the complete pipeline
    results = []
    artifacts_found = []
    clean_extractions = []

    print("\n" + "="*80)
    print("INTEGRATION TEST - ISSUE #23 DATE ARTIFACT CLEANUP")
    print("="*80)

    for title in test_titles:
        print(f"\nProcessing: {title}")

        # Step 1: Market classification
        market_result = market_classifier.classify(title)

        # Step 2: Date extraction
        date_result = date_extractor.extract(market_result.title)

        # Step 3: Report type extraction
        report_result = report_extractor.extract(date_result.title, market_result.market_type)

        # Step 4: Geographic detection
        geo_result = geo_detector.extract_geographic_entities(report_result.title)

        # Step 5: Topic extraction (this is where Issue #23 fix applies)
        topic_result = topic_extractor.extract(
            geo_result.title,  # Use .title instead of ['remaining_text']
            extracted_elements={
                'dates': [date_result.extracted_date_range] if date_result.extracted_date_range else [],
                'report_types': [report_result.extracted_report_type] if report_result.extracted_report_type else [],
                'regions': geo_result.extracted_regions,  # Use .extracted_regions instead of ['regions']
                'market_type': market_result.market_type  # Include market type in extracted elements
            }
        )

        # Check for artifacts that should have been cleaned
        topic = topic_result.extracted_topic
        has_artifacts = False
        artifact_patterns = ['()', '[]', '  ', ', Forecast to', ' to$', ' through$', ' till$', ' until$']

        for pattern in artifact_patterns:
            if topic and (pattern in topic or (pattern.endswith('$') and topic.endswith(pattern[:-1]))):
                has_artifacts = True
                artifacts_found.append({
                    'title': title,
                    'topic': topic,
                    'artifact': pattern
                })
                break

        if not has_artifacts:
            clean_extractions.append(title)

        # Store complete result
        result = {
            'original_title': title,
            'market_type': market_result.market_type,
            'extracted_date': date_result.extracted_date_range,
            'extracted_report_type': report_result.extracted_report_type,
            'extracted_regions': geo_result.extracted_regions,  # Use .extracted_regions
            'extracted_topic': topic_result.extracted_topic,
            'normalized_topic': topic_result.normalized_topic_name,
            'has_artifacts': has_artifacts,
            'processing_notes': topic_result.processing_notes
        }
        results.append(result)

        print(f"  → Market Type: {result['market_type']}")
        print(f"  → Date: {result['extracted_date']}")
        print(f"  → Report Type: {result['extracted_report_type']}")
        print(f"  → Regions: {result['extracted_regions']}")
        print(f"  → Topic: '{result['extracted_topic']}'")

        if has_artifacts:
            print(f"  ⚠️  ARTIFACT DETECTED in topic!")

    # Calculate statistics
    total_titles = len(test_titles)
    clean_count = len(clean_extractions)
    artifact_count = len(artifacts_found)
    success_rate = (clean_count / total_titles) * 100

    # Write detailed results
    output_file = os.path.join(output_dir, "integration_test_results.json")
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump({
            'summary': {
                'total_titles': total_titles,
                'clean_extractions': clean_count,
                'artifacts_found': artifact_count,
                'success_rate': success_rate
            },
            'results': results,
            'artifacts_detected': artifacts_found
        }, f, indent=2)

    # Write human-readable report
    report_file = os.path.join(output_dir, "integration_test_report.txt")
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(create_file_header("Issue #23 Integration Test", "Complete Pipeline Validation"))
        f.write("\nTEST SUMMARY\n")
        f.write("="*80 + "\n")
        f.write(f"Total Titles Tested: {total_titles}\n")
        f.write(f"Clean Extractions: {clean_count}\n")
        f.write(f"Artifacts Found: {artifact_count}\n")
        f.write(f"Success Rate: {success_rate:.1f}%\n\n")

        if artifact_count > 0:
            f.write("ARTIFACTS DETECTED\n")
            f.write("="*80 + "\n")
            for artifact in artifacts_found:
                f.write(f"\nTitle: {artifact['title']}\n")
                f.write(f"Topic: '{artifact['topic']}'\n")
                f.write(f"Artifact: {artifact['artifact']}\n")

        f.write("\nDETAILED RESULTS\n")
        f.write("="*80 + "\n")
        for result in results:
            status = "✓" if not result['has_artifacts'] else "⚠"
            f.write(f"\n[{status}] {result['original_title']}\n")
            f.write(f"  Market Type: {result['market_type']}\n")
            f.write(f"  Date: {result['extracted_date']}\n")
            f.write(f"  Report Type: {result['extracted_report_type']}\n")
            f.write(f"  Regions: {result['extracted_regions']}\n")
            f.write(f"  Topic: '{result['extracted_topic']}'\n")
            f.write(f"  Normalized: '{result['normalized_topic']}'\n")

    # Final summary
    print("\n" + "="*80)
    print("INTEGRATION TEST SUMMARY")
    print("="*80)
    print(f"Total Titles: {total_titles}")
    print(f"Clean Extractions: {clean_count}")
    print(f"Artifacts Found: {artifact_count}")
    print(f"Success Rate: {success_rate:.1f}%")

    if artifact_count == 0:
        print("\n✓ NO ARTIFACTS DETECTED - Issue #23 fix successfully integrated!")
    else:
        print(f"\n⚠ {artifact_count} artifacts detected - review needed")

    print(f"\nResults saved to: {output_dir}")

    return artifact_count == 0

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)