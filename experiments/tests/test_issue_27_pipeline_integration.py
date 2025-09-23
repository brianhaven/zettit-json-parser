#!/usr/bin/env python3
"""
Pipeline integration test for Issue #27 fix
Tests the complete extraction pipeline (01→02→03→04) to ensure fix doesn't break integration
"""

import os
import sys
import logging
from datetime import datetime
import pytz
import json
from typing import List, Dict
from pymongo import MongoClient

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def import_module_from_path(module_name: str, file_path: str):
    """Import a module from a specific file path."""
    import importlib.util
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

def create_organized_output_directory(script_name: str) -> str:
    """Create organized output directory with YYYY/MM/DD structure."""
    # Get absolute path to outputs directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    experiments_dir = os.path.dirname(script_dir)
    project_root = os.path.dirname(experiments_dir)
    outputs_dir = os.path.join(project_root, 'outputs')

    # Create timestamp in Pacific Time
    pdt = pytz.timezone('America/Los_Angeles')
    now = datetime.now(pdt)

    # Create YYYY/MM/DD structure
    year_dir = os.path.join(outputs_dir, now.strftime('%Y'))
    month_dir = os.path.join(year_dir, now.strftime('%m'))
    day_dir = os.path.join(month_dir, now.strftime('%d'))

    # Create timestamped subdirectory
    timestamp = now.strftime('%Y%m%d_%H%M%S')
    output_dir = os.path.join(day_dir, f"{timestamp}_{script_name}")
    os.makedirs(output_dir, exist_ok=True)

    return output_dir

def test_pipeline_integration():
    """Test complete pipeline integration with Issue #27 fix."""

    # Import required modules
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

    # Initialize components
    from dotenv import load_dotenv
    load_dotenv()

    # Initialize PatternLibraryManager
    pattern_lib_manager = pattern_manager.PatternLibraryManager(os.getenv('MONGODB_URI'))

    # Initialize pipeline components
    market_classifier = script01.MarketTermClassifier(pattern_lib_manager)
    date_extractor = script02.EnhancedDateExtractor(pattern_lib_manager)
    report_extractor = script03.PureDictionaryReportTypeExtractor(pattern_lib_manager)
    geo_detector = script04.GeographicEntityDetector(pattern_lib_manager)  # Script 04 v2 also uses PatternLibraryManager

    # Test cases specifically for Issue #27 validation
    test_cases = [
        {
            "title": "Oil & Gas Data Management Market, 2024-2029",
            "description": "Topic with dictionary keywords"
        },
        {
            "title": "Data Monetization Market Outlook, Trends, Analysis, 2025",
            "description": "Data at beginning of title"
        },
        {
            "title": "Europe Building Information Modeling Market Analysis Report, 2024",
            "description": "Complex topic with multiple dictionary terms"
        },
        {
            "title": "Asia-Pacific Advanced Analytics Market Research Study, 2024-2030",
            "description": "Geographic region with advanced topic"
        },
        {
            "title": "Global Food Processing Equipment Market Trends & Opportunities, 2025",
            "description": "Processing keyword in topic"
        }
    ]

    results = []

    print("\n" + "="*80)
    print("Pipeline Integration Test for Issue #27 Fix")
    print("="*80 + "\n")

    for i, test_case in enumerate(test_cases, 1):
        title = test_case['title']
        print(f"Test Case {i}: {title}")
        print(f"Description: {test_case['description']}")
        print("-" * 60)

        try:
            # Step 1: Market Term Classification
            market_result = market_classifier.classify(title)
            remaining = market_result.title if hasattr(market_result, 'title') else title
            print(f"1. Market Type: {market_result.market_type}")

            # Step 2: Date Extraction
            date_result = date_extractor.extract(remaining)
            remaining = date_result.title
            print(f"2. Date Extracted: {date_result.extracted_date_range if date_result.extracted_date_range else 'None'}")

            # Step 3: Report Type Extraction (Issue #27 fix applied here)
            report_result = report_extractor.extract(remaining, market_result.market_type)
            remaining = report_result.title
            print(f"3. Report Type: {report_result.extracted_report_type}")
            print(f"   Remaining After Report: '{remaining}'")

            # Step 4: Geographic Entity Detection
            geo_result = geo_detector.extract_geographic_entities(remaining)
            final_topic = geo_result.title  # Access object attribute
            regions = geo_result.extracted_regions  # Access object attribute
            print(f"4. Geographic Regions: {regions if regions else 'None'}")
            print(f"   Final Topic: '{final_topic}'")

            # Validate no content loss
            content_preserved = bool(final_topic and final_topic.strip())
            print(f"✓ Content Preserved: {content_preserved}")

            results.append({
                'test_case': i,
                'title': title,
                'market_type': market_result.market_type,
                'date': date_result.extracted_date_range,
                'report_type': report_result.extracted_report_type,
                'regions': regions,
                'final_topic': final_topic,
                'content_preserved': content_preserved,
                'description': test_case['description']
            })

        except Exception as e:
            logger.error(f"Error processing test case {i}: {e}")
            results.append({
                'test_case': i,
                'title': title,
                'error': str(e),
                'content_preserved': False
            })

        print("\n")

    # Summary
    preserved_count = sum(1 for r in results if r.get('content_preserved'))
    total_count = len(results)

    print("="*80)
    print(f"Pipeline Integration Summary: {preserved_count}/{total_count} tests preserved content")
    print("="*80 + "\n")

    return results

def save_pipeline_results(results: List[Dict], output_dir: str):
    """Save pipeline integration test results."""

    output_file = os.path.join(output_dir, "issue_27_pipeline_results.json")

    pdt = pytz.timezone('America/Los_Angeles')
    now_pdt = datetime.now(pdt)
    now_utc = datetime.now(pytz.utc)

    output_data = {
        'test_metadata': {
            'issue': 'Issue #27: Pre-Market Dictionary Terms Causing Content Loss',
            'test_type': 'Pipeline Integration Test (01→02→03→04)',
            'test_date_pdt': now_pdt.strftime('%Y-%m-%d %H:%M:%S PDT'),
            'test_date_utc': now_utc.strftime('%Y-%m-%d %H:%M:%S UTC'),
            'pipeline_scripts': [
                '01_market_term_classifier_v1.py',
                '02_date_extractor_v1.py',
                '03_report_type_extractor_v4.py (WITH FIX)',
                '04_geographic_entity_detector_v2.py'
            ]
        },
        'summary': {
            'total_tests': len(results),
            'content_preserved': sum(1 for r in results if r.get('content_preserved')),
            'content_lost': sum(1 for r in results if not r.get('content_preserved'))
        },
        'test_results': results
    }

    with open(output_file, 'w') as f:
        json.dump(output_data, f, indent=2)

    print(f"Pipeline results saved to: {output_file}")

def main():
    """Main execution function."""
    try:
        # Create output directory
        output_dir = create_organized_output_directory("issue_27_pipeline")
        logger.info(f"Output directory created: {output_dir}")

        # Run pipeline integration test
        results = test_pipeline_integration()

        # Save results
        save_pipeline_results(results, output_dir)

        # Return status based on results
        all_preserved = all(r.get('content_preserved') for r in results)
        return 0 if all_preserved else 1

    except Exception as e:
        logger.error(f"Error during testing: {e}", exc_info=True)
        return 1

if __name__ == "__main__":
    sys.exit(main())