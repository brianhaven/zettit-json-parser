#!/usr/bin/env python3
"""
MongoDB Sample Test for Issue #23: Date Artifact Cleanup Enhancement
Tests the fix with actual titles from the MongoDB database.
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
import random

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
    """Test Issue #23 fix with MongoDB sample data."""

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

    # Initialize all components
    market_classifier = script01.MarketTermClassifier(pattern_lib_manager)
    date_extractor = script02.EnhancedDateExtractor(pattern_lib_manager)
    report_extractor = script03.PureDictionaryReportTypeExtractor(pattern_lib_manager)
    geo_detector = script04.GeographicEntityDetector(pattern_lib_manager)
    topic_extractor = script05.TopicExtractor(pattern_lib_manager)

    # Connect to MongoDB to get real titles
    client = MongoClient(os.getenv('MONGODB_URI'))
    db = client['deathstar']
    markets_collection = db['markets_raw']

    # Query for titles with dates (likely to have artifacts)
    # Focus on titles with parentheses, brackets, or "Forecast to" patterns
    sample_titles = []

    # Get titles with parentheses and dates
    cursor = markets_collection.find(
        {'report_title_short': {'$regex': r'\(.*202[0-9].*\)', '$options': 'i'}},
        {'report_title_short': 1}
    ).limit(10)
    sample_titles.extend([doc['report_title_short'] for doc in cursor])

    # Get titles with brackets and dates
    cursor = markets_collection.find(
        {'report_title_short': {'$regex': r'\[.*202[0-9].*\]', '$options': 'i'}},
        {'report_title_short': 1}
    ).limit(10)
    sample_titles.extend([doc['report_title_short'] for doc in cursor])

    # Get titles with "Forecast to"
    cursor = markets_collection.find(
        {'report_title_short': {'$regex': r'Forecast to', '$options': 'i'}},
        {'report_title_short': 1}
    ).limit(10)
    sample_titles.extend([doc['report_title_short'] for doc in cursor])

    # Get titles with date ranges
    cursor = markets_collection.find(
        {'report_title_short': {'$regex': r'202[0-9]\s*-\s*203[0-9]', '$options': 'i'}},
        {'report_title_short': 1}
    ).limit(10)
    sample_titles.extend([doc['report_title_short'] for doc in cursor])

    # Get random sample of other titles
    cursor = markets_collection.aggregate([
        {'$match': {'report_title_short': {'$regex': 'Market', '$options': 'i'}}},
        {'$sample': {'size': 20}}
    ])
    sample_titles.extend([doc['report_title_short'] for doc in cursor])

    # Remove duplicates
    sample_titles = list(set(sample_titles))

    print(f"\n{'='*80}")
    print(f"MONGODB SAMPLE TEST - ISSUE #23 DATE ARTIFACT CLEANUP")
    print(f"{'='*80}")
    print(f"Testing {len(sample_titles)} titles from MongoDB database")

    # Create output directory
    output_dir = create_organized_output_directory("test_issue_23_mongodb")

    # Process each title
    results = []
    artifacts_found = []
    processing_errors = []

    for i, title in enumerate(sample_titles, 1):
        print(f"\n[{i}/{len(sample_titles)}] Processing: {title[:80]}...")

        try:
            # Step 1: Market classification
            market_result = market_classifier.classify(title)

            # Step 2: Date extraction
            date_result = date_extractor.extract(market_result.title)

            # Step 3: Report type extraction
            report_result = report_extractor.extract(date_result.title, market_result.market_type)

            # Step 4: Geographic detection
            geo_result = geo_detector.extract_geographic_entities(report_result.title)

            # Step 5: Topic extraction (Issue #23 fix applied here)
            topic_result = topic_extractor.extract(
                geo_result.title,
                extracted_elements={
                    'dates': [date_result.extracted_date_range] if date_result.extracted_date_range else [],
                    'report_types': [report_result.extracted_report_type] if report_result.extracted_report_type else [],
                    'regions': geo_result.extracted_regions,
                    'market_type': market_result.market_type
                }
            )

            # Check for artifacts
            topic = topic_result.extracted_topic
            has_artifacts = False
            detected_artifact = None

            if topic:
                # Check for various artifact patterns
                artifact_patterns = [
                    ('()', 'Empty parentheses'),
                    ('[]', 'Empty brackets'),
                    ('  ', 'Double spaces'),
                    (', Forecast to', 'Orphaned Forecast to'),
                    (', to', 'Orphaned comma-to'),
                    (' to', 'Orphaned to at end'),
                    (' through', 'Orphaned through'),
                    (' till', 'Orphaned till'),
                    (' until', 'Orphaned until')
                ]

                for pattern, description in artifact_patterns:
                    # Check for pattern in topic
                    found = False
                    if pattern in topic:
                        found = True
                    elif pattern.startswith(' ') and pattern.strip() and topic.endswith(pattern.strip()):
                        found = True

                    if found:
                        has_artifacts = True
                        detected_artifact = description
                        artifacts_found.append({
                            'title': title,
                            'topic': topic,
                            'artifact': detected_artifact
                        })
                        print(f"  ⚠️  ARTIFACT DETECTED: {description} in '{topic}'")
                        break

            # Store result
            result = {
                'title': title,
                'extracted_topic': topic,
                'has_artifacts': has_artifacts,
                'artifact_type': detected_artifact,
                'extracted_date': date_result.extracted_date_range,
                'extracted_report_type': report_result.extracted_report_type
            }
            results.append(result)

            if not has_artifacts and topic:
                print(f"  ✓ Clean topic: '{topic}'")

        except Exception as e:
            print(f"  ✗ ERROR: {str(e)}")
            processing_errors.append({
                'title': title,
                'error': str(e)
            })

    # Calculate statistics
    total_processed = len(results)
    clean_count = sum(1 for r in results if not r['has_artifacts'])
    artifact_count = len(artifacts_found)
    error_count = len(processing_errors)
    success_rate = (clean_count / total_processed * 100) if total_processed > 0 else 0

    # Write results to files
    output_file = os.path.join(output_dir, "mongodb_sample_results.json")
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump({
            'summary': {
                'total_titles': len(sample_titles),
                'processed': total_processed,
                'clean_extractions': clean_count,
                'artifacts_found': artifact_count,
                'processing_errors': error_count,
                'success_rate': success_rate
            },
            'artifacts_detected': artifacts_found,
            'processing_errors': processing_errors,
            'sample_results': results[:20]  # Save first 20 for review
        }, f, indent=2)

    # Write detailed report
    report_file = os.path.join(output_dir, "mongodb_sample_report.txt")
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(create_file_header("Issue #23 MongoDB Sample Test", "Real Data Validation"))
        f.write("\nTEST SUMMARY\n")
        f.write("="*80 + "\n")
        f.write(f"Total Titles: {len(sample_titles)}\n")
        f.write(f"Successfully Processed: {total_processed}\n")
        f.write(f"Clean Extractions: {clean_count}\n")
        f.write(f"Artifacts Found: {artifact_count}\n")
        f.write(f"Processing Errors: {error_count}\n")
        f.write(f"Success Rate: {success_rate:.1f}%\n\n")

        if artifact_count > 0:
            f.write("ARTIFACTS DETECTED\n")
            f.write("="*80 + "\n")
            for artifact in artifacts_found[:10]:  # Show first 10
                f.write(f"\nTitle: {artifact['title']}\n")
                f.write(f"Topic: '{artifact['topic']}'\n")
                f.write(f"Artifact: {artifact['artifact']}\n")

        if error_count > 0:
            f.write("\nPROCESSING ERRORS\n")
            f.write("="*80 + "\n")
            for error in processing_errors[:10]:  # Show first 10
                f.write(f"\nTitle: {error['title']}\n")
                f.write(f"Error: {error['error']}\n")

    # Final summary
    print(f"\n{'='*80}")
    print("MONGODB SAMPLE TEST SUMMARY")
    print("="*80)
    print(f"Total Titles: {len(sample_titles)}")
    print(f"Successfully Processed: {total_processed}")
    print(f"Clean Extractions: {clean_count}")
    print(f"Artifacts Found: {artifact_count}")
    print(f"Processing Errors: {error_count}")
    print(f"Success Rate: {success_rate:.1f}%")

    if artifact_count == 0 and error_count == 0:
        print("\n✓ PERFECT - No artifacts detected, no errors!")
    elif artifact_count == 0:
        print(f"\n✓ No artifacts detected (but {error_count} processing errors)")
    else:
        print(f"\n⚠ {artifact_count} artifacts still detected - review needed")

    print(f"\nResults saved to: {output_dir}")

    return artifact_count == 0

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)