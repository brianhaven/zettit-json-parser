#!/usr/bin/env python3
"""
Debug Reconstruction Simple
===========================

Focus only on the reconstruction logic to find the bug.
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

def test_reconstruction():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    pattern_manager = import_module_from_path("pattern_library_manager", 
                                            os.path.join(current_dir, "00b_pattern_library_manager_v1.py"))
    script03v3 = import_module_from_path("report_extractor_v3",
                                       os.path.join(current_dir, "03_report_type_extractor_v3.py"))
    
    pattern_lib_manager = pattern_manager.PatternLibraryManager(os.getenv('MONGODB_URI'))
    report_extractor = script03v3.DictionaryBasedReportTypeExtractor(pattern_lib_manager)
    
    print("=== Testing Reconstruction Logic ===\n")
    
    # Test the reconstruction method directly
    extracted_type = "Growth Report"
    market_term = "Market For Textile Fibers"
    
    print(f"Input extracted_type: '{extracted_type}'")
    print(f"Input market_term: '{market_term}'")
    
    if hasattr(report_extractor, '_reconstruct_report_type_with_market_v3'):
        result = report_extractor._reconstruct_report_type_with_market_v3(extracted_type, market_term)
        print(f"Reconstruction result: '{result}'")
        print(f"Result type: {type(result)}")
        print(f"Result is None: {result is None}")
        print(f"Result is empty string: {result == ''}")
    else:
        print("Method not found")

if __name__ == "__main__":
    test_reconstruction()