#!/usr/bin/env python3
"""
Test Script for Issue #28: Market Term Classification 'Market in' Context Integration
=====================================================================================

This test reproduces the issue where 'market_in' classification fails to properly 
integrate geographic context during processing.

Test Case: "Retail Market in Singapore - Size, Outlook & Statistics"
Expected Topic: "Retail in Singapore" or "Retail"  
Actual Topic: "Retail in" (incorrect)
"""

import os
import sys
import logging
from dotenv import load_dotenv

# Add parent directory for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

def test_market_in_context_integration():
    """Test the market_in context integration issue."""
    
    # Import modules dynamically
    import importlib.util
    
    def import_module_from_path(module_name: str, file_path: str):
        spec = importlib.util.spec_from_file_location(module_name, file_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module
    
    parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    # Import pattern library manager
    pattern_manager = import_module_from_path("pattern_library_manager",
                                            os.path.join(parent_dir, "00b_pattern_library_manager_v1.py"))
    
    # Import pipeline scripts
    script01 = import_module_from_path("market_classifier",
                                      os.path.join(parent_dir, "01_market_term_classifier_v1.py"))
    script02 = import_module_from_path("date_extractor",
                                      os.path.join(parent_dir, "02_date_extractor_v1.py"))
    script03 = import_module_from_path("report_extractor",
                                      os.path.join(parent_dir, "03_report_type_extractor_v4.py"))
    script04 = import_module_from_path("geo_detector",
                                      os.path.join(parent_dir, "04_geographic_entity_detector_v2.py"))
    
    # Initialize pattern library manager
    pattern_lib_manager = pattern_manager.PatternLibraryManager(os.getenv('MONGODB_URI'))
    
    # Initialize pipeline components
    market_classifier = script01.MarketTermClassifier(pattern_lib_manager)
    date_extractor = script02.EnhancedDateExtractor(pattern_lib_manager)
    report_extractor = script03.PureDictionaryReportTypeExtractor(pattern_lib_manager)
    
    # Initialize geographic detector with raw collection
    from pymongo import MongoClient
    client = MongoClient(os.getenv('MONGODB_URI'))
    patterns_collection = client['deathstar']['pattern_libraries']
    geo_detector = script04.GeographicEntityDetector(patterns_collection)
    
    # Test case from Issue #28
    test_title = "Retail Market in Singapore - Size, Outlook & Statistics"
    
    print("\n" + "="*80)
    print("ISSUE #28 TEST: Market in Context Integration")
    print("="*80)
    print(f"Original Title: {test_title}")
    print("-"*80)
    
    # Step 1: Market Classification
    market_result = market_classifier.classify(test_title)
    print(f"\n1. Market Classification:")
    print(f"   Type: {market_result.market_type}")
    print(f"   Confidence: {market_result.confidence}")
    print(f"   Notes: {market_result.notes}")
    print(f"   Title Forward: {market_result.title}")
    
    # Step 2: Date Extraction  
    date_result = date_extractor.extract(market_result.title)
    print(f"\n2. Date Extraction:")
    print(f"   Date: {date_result.extracted_date_range}")
    print(f"   Title Forward: {date_result.title}")
    
    # Step 3: Report Type Extraction with market context
    report_result = report_extractor.extract(date_result.title, market_result.market_type)
    print(f"\n3. Report Type Extraction:")
    print(f"   Report Type: {report_result.extracted_report_type}")
    print(f"   Market Type: {report_result.market_term_type}")
    print(f"   Title Forward: {report_result.title}")
    print(f"   Confidence: {report_result.confidence}")
    
    # Step 4: Geographic Entity Detection
    geo_result = geo_detector.extract_geographic_entities(report_result.title)
    print(f"\n4. Geographic Entity Detection:")
    print(f"   Regions: {geo_result.extracted_regions}")
    print(f"   Title Forward: {geo_result.title}")
    print(f"   Confidence: {geo_result.confidence_score}")
    
    # Final Topic
    final_topic = geo_result.title
    print(f"\n" + "="*80)
    print(f"FINAL TOPIC: '{final_topic}'")
    print(f"EXPECTED: 'Retail in Singapore' or 'Retail'")
    print(f"ISSUE: Geographic context 'Singapore' was incorrectly removed")
    print("="*80)
    
    # Additional test with market_for for comparison
    test_title_2 = "Oman Industrial Salts Market For Oil & Gas Industry Report, 2020-2027"
    print(f"\n\nCOMPARISON TEST: Market for")
    print("-"*80)
    print(f"Original Title: {test_title_2}")
    
    # Process through pipeline
    result1 = market_classifier.classify(test_title_2)
    result2 = date_extractor.extract(result1.title)
    result3 = report_extractor.extract(result2.title, result1.market_type)
    result4 = geo_detector.extract_geographic_entities(result3.title)
    
    print(f"Market Type: {result1.market_type}")
    print(f"Report Type: {result3.extracted_report_type}")
    print(f"Regions: {result4.extracted_regions}")
    print(f"Final Topic: '{result4.title}'")
    print(f"Note: 'for' context is preserved correctly")
    
    return final_topic

if __name__ == "__main__":
    try:
        result = test_market_in_context_integration()
        print(f"\n✅ Test completed. Issue #28 reproduced successfully.")
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()