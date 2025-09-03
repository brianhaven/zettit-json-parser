#!/usr/bin/env python3
"""
Quick test to verify v3 keyword removal fix
"""

import sys
import os
from pymongo import MongoClient
from dotenv import load_dotenv
import importlib.util

# Load environment variables
load_dotenv()

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def import_module_from_path(module_name: str, file_path: str):
    """Import a module from a file path."""
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

# Import modules
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
pattern_manager = import_module_from_path("pattern_library_manager",
                                        os.path.join(parent_dir, "00b_pattern_library_manager_v1.py"))
script01 = import_module_from_path("market_classifier", 
                                 os.path.join(parent_dir, "01_market_term_classifier_v1.py"))
script02 = import_module_from_path("date_extractor",
                                 os.path.join(parent_dir, "02_date_extractor_v1.py"))
script03v3 = import_module_from_path("report_extractor_v3",
                                   os.path.join(parent_dir, "03_report_type_extractor_v3.py"))

def test_keyword_fix():
    """Test the keyword removal fix for specific problem cases."""
    
    # Initialize components
    pattern_lib_manager = pattern_manager.PatternLibraryManager(os.getenv('MONGODB_URI'))
    market_classifier = script01.MarketTermClassifier(pattern_lib_manager)
    date_extractor = script02.EnhancedDateExtractor(pattern_lib_manager)
    report_extractor_v3 = script03v3.DictionaryBasedReportTypeExtractor(pattern_lib_manager)
    
    # Test cases that were failing
    test_cases = [
        "Ultralight And Light Aircraft Market Size & Share Report, 2030",
        "Data Capture Hardware In Retail Market Size Industry Report, 2025"
    ]
    
    print("Testing v3 keyword removal fix:")
    print("=" * 60)
    
    for title in test_cases:
        print(f"\nOriginal Title: {title}")
        
        # Process through pipeline
        market_result = market_classifier.classify(title)
        print(f"Market Type: {market_result.market_type}")
        
        date_result = date_extractor.extract(market_result.title)
        print(f"After Date Removal: {date_result.title}")
        
        report_result = report_extractor_v3.extract(date_result.title, market_result.market_type)
        print(f"Report Type: {report_result.extracted_report_type}")
        print(f"Final Topic: {report_result.title}")
        
        # Check if the fix worked
        if "Ultralight And Light Aircraft" in title and "And" in report_result.title:
            print("✅ SUCCESS: 'And' preserved in title")
        elif "Data Capture Hardware" in title and "Data" in report_result.title:
            print("✅ SUCCESS: 'Data' preserved in title")
        else:
            print("❌ ISSUE: Keywords may still be missing")
        
        print("-" * 40)

if __name__ == "__main__":
    test_keyword_fix()