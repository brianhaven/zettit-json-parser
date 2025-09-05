#!/usr/bin/env python3
"""
Test Main Extract Method
========================

Test the main extract method to verify the fix works.
"""

import os
import sys
from dotenv import load_dotenv
import importlib.util

load_dotenv()
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def import_module_from_path(module_name: str, file_path: str):
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

def test_main_extract():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    pattern_manager = import_module_from_path("pattern_library_manager", 
                                            os.path.join(current_dir, "00b_pattern_library_manager_v1.py"))
    script03v3 = import_module_from_path("report_extractor_v3",
                                       os.path.join(current_dir, "03_report_type_extractor_v3.py"))
    
    pattern_lib_manager = pattern_manager.PatternLibraryManager(os.getenv('MONGODB_URI'))
    report_extractor = script03v3.DictionaryBasedReportTypeExtractor(pattern_lib_manager)
    
    print("=== Testing Main Extract Method ===\n")
    
    test_cases = [
        {
            "title": "Carbon Black Market For Textile Fibers Growth Report",
            "market_type": "market_for",
            "expected_report": "Market Growth Report"
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        title = test_case["title"]
        market_type = test_case["market_type"]
        expected_report = test_case["expected_report"]
        
        print(f"=== Test {i}: {market_type} ===")
        print(f"Title: '{title}'")
        print(f"Market Type: '{market_type}'")
        print(f"Expected Report: '{expected_report}'")
        
        try:
            # Call the main extract method
            result = report_extractor.extract(title, market_type)
            
            print(f"Extracted Report Type: '{result.extracted_report_type}'")
            print(f"Pipeline Forward: '{result.title}'")
            print(f"Success: {result.success}")
            print(f"Confidence: {result.confidence}")
            
            if result.extracted_report_type == expected_report:
                print("✅ SUCCESS: Report type matches expected")
            else:
                print(f"❌ FAILED: Expected '{expected_report}', got '{result.extracted_report_type}'")
                
        except Exception as e:
            print(f"❌ ERROR: {e}")
            import traceback
            traceback.print_exc()
        
        print("-" * 50)
        print()

if __name__ == "__main__":
    test_main_extract()