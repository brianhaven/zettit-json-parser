#!/usr/bin/env python3
"""
Pipeline Integration Test for Issue #19 Fix
Tests that the complete pipeline works correctly with symbol preservation.
"""

import sys
import os
import json
import logging
from datetime import datetime
import importlib.util
from dotenv import load_dotenv

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

def import_module_from_path(module_name: str, file_path: str):
    """Import a module from a file path."""
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

def run_complete_pipeline_test():
    """Run a complete pipeline test with various titles."""

    parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    # Import modules
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
    pattern_lib_manager = pattern_manager.PatternLibraryManager(os.getenv('MONGODB_URI'))

    market_classifier = script01.MarketTermClassifier(pattern_lib_manager)
    date_extractor = script02.EnhancedDateExtractor(pattern_lib_manager)
    report_extractor = script03.PureDictionaryReportTypeExtractor(pattern_lib_manager)
    geo_detector = script04.GeographicEntityDetector(pattern_lib_manager)

    # Test cases
    test_titles = [
        "U.S. Oil & Gas Market Report, 2025",
        "Food & Beverage Market For Hotels + Restaurants Analysis, 2030",
        "Asia-Pacific M&A Market In Technology/Software Report",
        "Global R&D Market Outlook & Forecast, 2024-2029",
        "European Food + Beverage Market Research Report",
    ]

    print("\n" + "="*80)
    print("PIPELINE INTEGRATION TEST - ISSUE #19 FIX VALIDATION")
    print("="*80)

    all_passed = True

    for title in test_titles:
        print(f"\n📊 Processing: {title}")
        print("-" * 60)

        try:
            # Run through complete pipeline
            result1 = market_classifier.classify(title)
            print(f"1️⃣ Market Type: {result1.market_type}")

            result2 = date_extractor.extract(result1.title)
            print(f"2️⃣ Date: {result2.extracted_date_range or 'None'}")

            result3 = report_extractor.extract(result2.title, market_term_type=result1.market_type)
            print(f"3️⃣ Report Type: {result3.extracted_report_type}")

            result4 = geo_detector.extract_geographic_entities(result3.title)
            print(f"4️⃣ Regions: {result4.extracted_regions}")
            print(f"5️⃣ Final Topic: {result4.title}")

            # Check for symbol preservation
            symbols_in_original = [s for s in ['&', '+', '/'] if s in title]
            symbols_in_result = [s for s in symbols_in_original if s in result4.title]

            if len(symbols_in_result) == len(symbols_in_original):
                print(f"✅ Symbols preserved: {symbols_in_original}")
            else:
                print(f"⚠️ Some symbols lost: Original {symbols_in_original}, Result {symbols_in_result}")
                all_passed = False

        except Exception as e:
            print(f"❌ Error: {e}")
            all_passed = False

    print("\n" + "="*80)
    if all_passed:
        print("✅ ALL PIPELINE TESTS PASSED - Symbol preservation working correctly!")
    else:
        print("⚠️ Some issues detected - review output above")
    print("="*80)

    return all_passed

if __name__ == "__main__":
    success = run_complete_pipeline_test()
    sys.exit(0 if success else 1)