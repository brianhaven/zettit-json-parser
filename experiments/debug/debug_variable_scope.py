#!/usr/bin/env python3
"""
Debug Variable Scope Issue
==========================

Check the exact variable flow in the main extract method.
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

def debug_variable_scope():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    pattern_manager = import_module_from_path("pattern_library_manager", 
                                            os.path.join(current_dir, "00b_pattern_library_manager_v1.py"))
    script03v3 = import_module_from_path("report_extractor_v3",
                                       os.path.join(current_dir, "03_report_type_extractor_v3.py"))
    
    pattern_lib_manager = pattern_manager.PatternLibraryManager(os.getenv('MONGODB_URI'))
    report_extractor = script03v3.DictionaryBasedReportTypeExtractor(pattern_lib_manager)
    
    print("=== Debugging Variable Scope in Main Extract ===\n")
    
    # Add debug logging to trace variable values
    original_extract = report_extractor.extract
    
    def debug_extract(title, market_type):
        print(f"ENTRY: title='{title}', market_type='{market_type}'")
        
        # Call the original method with instrumentation
        result = original_extract(title, market_type)
        
        print(f"RESULT: extracted_report_type='{result.extracted_report_type}'")
        print(f"RESULT: title='{result.title}'")
        print(f"RESULT: confidence={result.confidence}")
        
        return result
    
    report_extractor.extract = debug_extract
    
    # Test the failing case
    title = "Carbon Black Market For Textile Fibers Growth Report"
    market_type = "market_for"
    
    print(f"Testing: '{title}' with market_type '{market_type}'")
    result = report_extractor.extract(title, market_type)
    
    print(f"\nFinal Result:")
    print(f"  Report Type: '{result.extracted_report_type}'")
    print(f"  Pipeline Forward: '{result.title}'")
    print(f"  Success: {result.success}")

if __name__ == "__main__":
    debug_variable_scope()