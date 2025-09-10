#!/usr/bin/env python3
"""
Live data test for Issue #26 fix: Test with actual titles from MongoDB.

This script tests the separator cleanup fix with real market research titles
from the database to ensure production readiness.
"""

import os
import sys
import importlib.util
from pathlib import Path
from dotenv import load_dotenv
from pymongo import MongoClient
import logging
from datetime import datetime
import pytz
import json

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Load environment variables
load_dotenv()

def import_module_from_path(module_name: str, file_path: str):
    """Import a module from a file path."""
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

def create_test_output_directory():
    """Create timestamped output directory for test results."""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    experiments_dir = os.path.dirname(script_dir)
    project_root = os.path.dirname(experiments_dir)
    outputs_dir = os.path.join(project_root, 'outputs')
    
    pdt = pytz.timezone('America/Los_Angeles')
    timestamp = datetime.now(pdt).strftime('%Y%m%d_%H%M%S')
    
    output_dir = os.path.join(outputs_dir, f"{timestamp}_issue_26_live_data_test")
    os.makedirs(output_dir, exist_ok=True)
    
    return output_dir

def test_with_live_data():
    """Test the fix with actual titles from MongoDB."""
    
    # Import modules
    parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    # Import PatternLibraryManager
    pattern_manager = import_module_from_path("pattern_library_manager",
                                            os.path.join(parent_dir, "00b_pattern_library_manager_v1.py"))
    
    # Import Script 03 v4
    script03 = import_module_from_path("report_extractor",
                                      os.path.join(parent_dir, "03_report_type_extractor_v4.py"))
    
    # Initialize components
    pattern_lib_manager = pattern_manager.PatternLibraryManager(os.getenv('MONGODB_URI'))
    report_extractor = script03.PureDictionaryReportTypeExtractor(pattern_lib_manager)
    
    # Connect to MongoDB for test data
    client = MongoClient(os.getenv('MONGODB_URI'))
    db = client['deathstar']
    
    # Get sample of real titles
    # Focus on titles with multiple keywords that might have separator issues
    pipeline = [
        {
            "$match": {
                "report_title_short": {
                    "$regex": "Market.*(Size|Share|Growth|Analysis|Report|Trends|Forecast)",
                    "$options": "i"
                }
            }
        },
        {"$sample": {"size": 50}},  # Random sample of 50 titles
        {"$project": {"report_title_short": 1, "_id": 1}}
    ]
    
    titles = list(db.markets_raw.aggregate(pipeline))
    
    # Create output directory
    output_dir = create_test_output_directory()
    output_file = os.path.join(output_dir, "live_data_test_results.json")
    detailed_file = os.path.join(output_dir, "detailed_results.txt")
    
    # Run tests
    results = []
    successful = 0
    with_separators = 0
    cleaned = 0
    failed = 0
    
    logger.info("=" * 60)
    logger.info("Issue #26 Fix - Live Data Test")
    logger.info(f"Testing with {len(titles)} real titles from MongoDB")
    logger.info("=" * 60)
    
    with open(detailed_file, 'w') as f:
        f.write("Issue #26 Fix - Live Data Test Results\n")
        f.write("=" * 60 + "\n")
        f.write(f"Test Date (PDT): {datetime.now(pytz.timezone('America/Los_Angeles')).strftime('%Y-%m-%d %H:%M:%S %Z')}\n")
        f.write(f"Test Date (UTC): {datetime.now(pytz.UTC).strftime('%Y-%m-%d %H:%M:%S %Z')}\n")
        f.write(f"Total Titles Tested: {len(titles)}\n")
        f.write("=" * 60 + "\n\n")
        
        for i, doc in enumerate(titles, 1):
            title = doc['report_title_short']
            
            # Extract report type
            result = report_extractor.extract(title)
            
            # Check results
            if result.extracted_report_type:
                successful += 1
                
                # Check if & was in original and if it was cleaned
                had_separator = "&" in title
                has_separator_now = "&" in result.extracted_report_type
                
                if had_separator:
                    with_separators += 1
                    if not has_separator_now:
                        cleaned += 1
                
                # Record result
                test_result = {
                    "test_num": i,
                    "title": title,
                    "extracted_report_type": result.extracted_report_type,
                    "remaining": result.title if hasattr(result, 'title') else None,
                    "had_separator": had_separator,
                    "has_separator_now": has_separator_now,
                    "cleaned": had_separator and not has_separator_now,
                    "success": True
                }
                results.append(test_result)
                
                # Log issues
                if has_separator_now:
                    logger.warning(f"Test {i}: Still has separator - '{result.extracted_report_type}'")
                    f.write(f"[WARNING] Test {i}:\n")
                    f.write(f"  Title: {title}\n")
                    f.write(f"  Extracted: {result.extracted_report_type} (still has &)\n")
                    f.write("-" * 40 + "\n")
                elif had_separator:
                    logger.debug(f"Test {i}: Successfully cleaned separator")
                    f.write(f"[CLEANED] Test {i}:\n")
                    f.write(f"  Title: {title}\n")
                    f.write(f"  Extracted: {result.extracted_report_type} (& removed)\n")
                    f.write("-" * 40 + "\n")
                    
            else:
                failed += 1
                test_result = {
                    "test_num": i,
                    "title": title,
                    "extracted_report_type": None,
                    "success": False
                }
                results.append(test_result)
                logger.debug(f"Test {i}: No extraction")
                f.write(f"[FAILED] Test {i}:\n")
                f.write(f"  Title: {title}\n")
                f.write(f"  Result: No extraction\n")
                f.write("-" * 40 + "\n")
        
        # Calculate statistics
        success_rate = (successful / len(titles)) * 100 if titles else 0
        cleanup_rate = (cleaned / with_separators) * 100 if with_separators > 0 else 100
        
        # Summary
        logger.info("\n" + "=" * 60)
        logger.info("Live Data Test Summary:")
        logger.info(f"  Total Titles: {len(titles)}")
        logger.info(f"  Successful Extractions: {successful} ({success_rate:.1f}%)")
        logger.info(f"  Failed Extractions: {failed}")
        logger.info(f"  Titles with & in original: {with_separators}")
        logger.info(f"  Successfully cleaned: {cleaned} ({cleanup_rate:.1f}% of those with &)")
        
        f.write("\n" + "=" * 60 + "\n")
        f.write("SUMMARY:\n")
        f.write(f"  Total Titles: {len(titles)}\n")
        f.write(f"  Successful Extractions: {successful} ({success_rate:.1f}%)\n")
        f.write(f"  Failed Extractions: {failed}\n")
        f.write(f"  Titles with & in original: {with_separators}\n")
        f.write(f"  Successfully cleaned: {cleaned} ({cleanup_rate:.1f}% of those with &)\n")
        f.write("\n")
        
        if success_rate >= 90 and cleanup_rate == 100:
            logger.info("✓ SUCCESS: Live data test passed!")
            logger.info("✓ All separator artifacts were successfully cleaned!")
            f.write("✓ SUCCESS: Live data test passed!\n")
            f.write("✓ All separator artifacts were successfully cleaned!\n")
        elif success_rate >= 90:
            logger.info(f"✓ SUCCESS: Extraction rate {success_rate:.1f}% meets 90% threshold")
            logger.warning(f"⚠ WARNING: Cleanup rate {cleanup_rate:.1f}% - some separators remain")
            f.write(f"✓ SUCCESS: Extraction rate {success_rate:.1f}% meets 90% threshold\n")
            f.write(f"⚠ WARNING: Cleanup rate {cleanup_rate:.1f}% - some separators remain\n")
        else:
            logger.warning(f"✗ WARNING: Success rate {success_rate:.1f}% is below 90% threshold")
            f.write(f"✗ WARNING: Success rate {success_rate:.1f}% is below 90% threshold\n")
    
    # Save JSON results
    with open(output_file, 'w') as f:
        json.dump({
            "test_date": datetime.now(pytz.UTC).isoformat(),
            "total_titles": len(titles),
            "successful": successful,
            "failed": failed,
            "with_separators": with_separators,
            "cleaned": cleaned,
            "success_rate": success_rate,
            "cleanup_rate": cleanup_rate,
            "results": results
        }, f, indent=2)
    
    logger.info(f"\nDetailed results saved to: {detailed_file}")
    logger.info(f"JSON results saved to: {output_file}")
    
    return success_rate >= 90

if __name__ == "__main__":
    try:
        success = test_with_live_data()
        sys.exit(0 if success else 1)
    except Exception as e:
        logger.error(f"Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)