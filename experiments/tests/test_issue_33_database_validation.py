#!/usr/bin/env python3
"""
Database validation test for Git Issue #33: Regional Separator Word Cleanup Enhancement
Tests the v3 fixed implementation against real database titles to ensure no regressions.
"""

import os
import sys
import json
import importlib.util
from datetime import datetime
from dotenv import load_dotenv
from pymongo import MongoClient

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

def validate_with_database_titles():
    """Validate the v3 implementation with real database titles."""

    # Import required modules
    parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    # Import pattern library manager and both detector versions
    pattern_manager = import_module_from_path("pattern_library_manager",
                                             os.path.join(parent_dir, "00b_pattern_library_manager_v1.py"))
    script04_v2 = import_module_from_path("geographic_detector_v2",
                                          os.path.join(parent_dir, "04_geographic_entity_detector_v2.py"))
    script04_v3 = import_module_from_path("geographic_detector_v3_fixed",
                                          os.path.join(parent_dir, "04_geographic_entity_detector_v3_fixed.py"))

    # Import output directory manager
    output_manager = import_module_from_path("output_manager",
                                            os.path.join(parent_dir, "00c_output_directory_manager_v1.py"))

    # Initialize components
    pattern_lib_manager = pattern_manager.PatternLibraryManager(os.getenv('MONGODB_URI'))
    detector_v2 = script04_v2.GeographicEntityDetector(pattern_lib_manager)
    detector_v3 = script04_v3.GeographicEntityDetector(pattern_lib_manager)

    # Connect to MongoDB to get real titles
    client = MongoClient(os.getenv('MONGODB_URI'))
    db = client['deathstar']
    markets_collection = db['markets_raw']

    # Find titles with potential separator patterns
    separator_patterns = [
        {"report_title_short": {"$regex": r"\bAnd\b", "$options": "i"}},
        {"report_title_short": {"$regex": r"\bPlus\b", "$options": "i"}},
        {"report_title_short": {"$regex": r"\s&\s", "$options": "i"}},
    ]

    # Get sample titles with separators
    titles_with_separators = []
    for pattern in separator_patterns:
        titles = list(markets_collection.find(pattern, {"report_title_short": 1}).limit(10))
        titles_with_separators.extend(titles)

    # Also get some regular titles for comparison
    regular_titles = list(markets_collection.find(
        {"report_title_short": {"$regex": "Market", "$options": "i"}},
        {"report_title_short": 1}
    ).limit(20))

    all_test_titles = titles_with_separators + regular_titles

    print("\n" + "="*100)
    print("Git Issue #33: Database Validation Test")
    print("="*100)
    print(f"\nTest Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Total titles to test: {len(all_test_titles)}")

    # Track results
    results = []
    improvements = 0
    regressions = 0
    consistent = 0

    print("\n" + "-"*100)
    print("TESTING DATABASE TITLES")
    print("-"*100)

    for i, doc in enumerate(all_test_titles[:30], 1):  # Test first 30 titles
        title = doc['report_title_short']

        # Skip very long titles for cleaner output
        if len(title) > 150:
            continue

        # Process with both versions
        result_v2 = detector_v2.extract_geographic_entities(title)
        result_v3 = detector_v3.extract_geographic_entities(title)

        # Check for improvements or regressions
        has_separator_artifact_v2 = any(word in result_v2.title.split()
                                       for word in ['And', 'and', 'Plus', 'plus'])
        has_separator_artifact_v3 = any(word in result_v3.title.split()
                                       for word in ['And', 'and', 'Plus', 'plus'])

        if has_separator_artifact_v2 and not has_separator_artifact_v3:
            improvements += 1
            status = "🎯 IMPROVED"
        elif not has_separator_artifact_v2 and has_separator_artifact_v3:
            regressions += 1
            status = "⚠️  REGRESSION"
        else:
            consistent += 1
            status = "✅ CONSISTENT"

        # Only show titles with differences or separator issues
        if status != "✅ CONSISTENT" or has_separator_artifact_v2:
            print(f"\nTitle {i}: {title[:80]}...")
            print(f"  v2: '{result_v2.title[:60]}...' (regions: {len(result_v2.extracted_regions)})")
            print(f"  v3: '{result_v3.title[:60]}...' (regions: {len(result_v3.extracted_regions)})")
            print(f"  Status: {status}")

        results.append({
            "title": title,
            "v2_result": result_v2.title,
            "v2_regions": result_v2.extracted_regions,
            "v3_result": result_v3.title,
            "v3_regions": result_v3.extracted_regions,
            "status": status
        })

    # Print summary
    print("\n" + "="*100)
    print("VALIDATION SUMMARY")
    print("="*100)

    print(f"\nTotal titles tested: {len(results)}")
    print(f"Improvements: {improvements} (v3 fixed separator issues)")
    print(f"Regressions: {regressions} (v3 introduced issues)")
    print(f"Consistent: {consistent} (same behavior)")

    if regressions == 0:
        print("\n✅ NO REGRESSIONS DETECTED - Safe to deploy v3")
    else:
        print(f"\n⚠️  WARNING: {regressions} regressions detected - Review before deployment")

    # Save detailed results
    output_dir = output_manager.create_organized_output_directory("issue_33_database_validation")

    output_file = os.path.join(output_dir, "database_validation_results.json")
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump({
            "test_date": datetime.now().isoformat(),
            "total_tested": len(results),
            "improvements": improvements,
            "regressions": regressions,
            "consistent": consistent,
            "results": results
        }, f, indent=2, ensure_ascii=False)

    print(f"\nDetailed results saved to: {output_file}")

    # Close MongoDB connection
    client.close()

    # Return success status
    return regressions == 0

if __name__ == "__main__":
    success = validate_with_database_titles()
    if success:
        print("\n🎉 Issue #33 validation successful!")
    else:
        print("\n⚠️  Issue #33 validation found regressions")