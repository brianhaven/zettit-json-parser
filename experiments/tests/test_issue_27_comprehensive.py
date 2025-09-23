#!/usr/bin/env python3
"""
Comprehensive test for Issue #27 fix - Test with 250 documents to ensure no regression
"""

import os
import sys
import logging
from datetime import datetime
import pytz
import json
from typing import List, Dict
from pymongo import MongoClient
import random

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

def test_250_documents():
    """Test Script 03 v4 with 250 documents to ensure no regression."""

    # Import required modules
    parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    pattern_manager = import_module_from_path("pattern_library_manager",
                                            os.path.join(parent_dir, "00b_pattern_library_manager_v1.py"))
    script03 = import_module_from_path("report_extractor",
                                     os.path.join(parent_dir, "03_report_type_extractor_v4.py"))

    # Initialize components
    from dotenv import load_dotenv
    load_dotenv()

    pattern_lib_manager = pattern_manager.PatternLibraryManager(os.getenv('MONGODB_URI'))
    report_extractor = script03.PureDictionaryReportTypeExtractor(pattern_lib_manager)

    # Connect to MongoDB to fetch test documents
    client = MongoClient(os.getenv('MONGODB_URI'))
    db = client['deathstar']
    collection = db['markets_raw']

    # Fetch 250 random documents
    pipeline = [
        {"$match": {"report_title_short": {"$exists": True, "$ne": ""}}},
        {"$sample": {"size": 250}},
        {"$project": {"report_title_short": 1, "_id": 1}}
    ]

    documents = list(collection.aggregate(pipeline))
    logger.info(f"Fetched {len(documents)} documents for testing")

    results = []
    success_count = 0
    failure_count = 0
    empty_topic_count = 0

    print("\n" + "="*80)
    print(f"Testing Issue #27 Fix with {len(documents)} Documents")
    print("="*80 + "\n")

    for i, doc in enumerate(documents, 1):
        title = doc['report_title_short']

        try:
            # Extract report type
            result = report_extractor.extract(title)

            # Check for success
            success = bool(result.extracted_report_type)
            if success:
                success_count += 1
            else:
                failure_count += 1

            # Check for empty topic (content loss)
            if result.title == "" or result.title is None:
                empty_topic_count += 1
                logger.warning(f"Empty topic for: {title}")

            results.append({
                'doc_id': str(doc['_id']),
                'title': title,
                'extracted_report_type': result.extracted_report_type,
                'remaining_topic': result.title,
                'confidence': result.confidence,
                'success': success,
                'empty_topic': result.title == "" or result.title is None
            })

            if i % 50 == 0:
                print(f"Processed {i}/{len(documents)} documents...")

        except Exception as e:
            logger.error(f"Error processing document {doc['_id']}: {e}")
            failure_count += 1
            results.append({
                'doc_id': str(doc['_id']),
                'title': title,
                'extracted_report_type': "",
                'remaining_topic': title,
                'confidence': 0.0,
                'success': False,
                'empty_topic': False,
                'error': str(e)
            })

    # Calculate statistics
    success_rate = (success_count / len(documents)) * 100 if documents else 0
    empty_topic_rate = (empty_topic_count / len(documents)) * 100 if documents else 0

    print("\n" + "="*80)
    print("Test Results Summary")
    print("="*80)
    print(f"Total Documents: {len(documents)}")
    print(f"Successful Extractions: {success_count} ({success_rate:.1f}%)")
    print(f"Failed Extractions: {failure_count} ({100 - success_rate:.1f}%)")
    print(f"Empty Topics (Content Loss): {empty_topic_count} ({empty_topic_rate:.1f}%)")
    print("="*80 + "\n")

    return results, {
        'total_documents': len(documents),
        'successful': success_count,
        'failed': failure_count,
        'empty_topics': empty_topic_count,
        'success_rate': success_rate,
        'empty_topic_rate': empty_topic_rate
    }

def save_comprehensive_results(results: List[Dict], stats: Dict, output_dir: str):
    """Save comprehensive test results to JSON files."""

    # Save summary
    summary_file = os.path.join(output_dir, "issue_27_comprehensive_summary.json")

    pdt = pytz.timezone('America/Los_Angeles')
    now_pdt = datetime.now(pdt)
    now_utc = datetime.now(pytz.utc)

    summary_data = {
        'test_metadata': {
            'issue': 'Issue #27: Pre-Market Dictionary Terms Causing Content Loss',
            'test_type': 'Comprehensive 250-document test',
            'script': 'Script 03 v4: Pure Dictionary Report Type Extractor',
            'test_date_pdt': now_pdt.strftime('%Y-%m-%d %H:%M:%S PDT'),
            'test_date_utc': now_utc.strftime('%Y-%m-%d %H:%M:%S UTC')
        },
        'statistics': stats,
        'fix_impact': {
            'description': 'Changed from span-based removal to position-based removal',
            'expected_improvement': 'Reduced content loss while maintaining extraction accuracy'
        }
    }

    with open(summary_file, 'w') as f:
        json.dump(summary_data, f, indent=2)

    print(f"Summary saved to: {summary_file}")

    # Save detailed results
    detailed_file = os.path.join(output_dir, "issue_27_comprehensive_details.json")
    with open(detailed_file, 'w') as f:
        json.dump(results, f, indent=2)

    print(f"Detailed results saved to: {detailed_file}")

    # Save cases with empty topics for analysis
    empty_topics = [r for r in results if r.get('empty_topic')]
    if empty_topics:
        empty_file = os.path.join(output_dir, "issue_27_empty_topics.json")
        with open(empty_file, 'w') as f:
            json.dump(empty_topics, f, indent=2)
        print(f"Empty topic cases saved to: {empty_file}")

def main():
    """Main execution function."""
    try:
        # Create output directory
        output_dir = create_organized_output_directory("issue_27_comprehensive")
        logger.info(f"Output directory created: {output_dir}")

        # Run comprehensive test
        results, stats = test_250_documents()

        # Save results
        save_comprehensive_results(results, stats, output_dir)

        # Return status based on results
        # Success if we maintain 85%+ success rate and have <5% empty topics
        return 0 if (stats['success_rate'] >= 85 and stats['empty_topic_rate'] < 5) else 1

    except Exception as e:
        logger.error(f"Error during testing: {e}", exc_info=True)
        return 1

if __name__ == "__main__":
    sys.exit(main())