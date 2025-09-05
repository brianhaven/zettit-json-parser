#!/usr/bin/env python3
"""
Debug Search Patterns Without Market v3
========================================

Debug why the _search_report_patterns_without_market_v3 method is not finding patterns.
"""

import os
import sys
from dotenv import load_dotenv
import importlib.util

# Load environment variables
load_dotenv()

# Add current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def import_module_from_path(module_name: str, file_path: str):
    """Import a module from a file path."""
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

def debug_search_patterns():
    """Debug the search patterns method directly."""
    
    # Import required modules
    current_dir = os.path.dirname(os.path.abspath(__file__))
    pattern_manager = import_module_from_path("pattern_library_manager", 
                                            os.path.join(current_dir, "00b_pattern_library_manager_v1.py"))
    script03v3 = import_module_from_path("report_extractor_v3",
                                       os.path.join(current_dir, "03_report_type_extractor_v3.py"))
    
    # Initialize components
    pattern_lib_manager = pattern_manager.PatternLibraryManager(os.getenv('MONGODB_URI'))
    report_extractor = script03v3.DictionaryBasedReportTypeExtractor(pattern_lib_manager)
    
    print("=== Debugging Search Patterns Without Market v3 ===\n")
    
    # Test cases
    test_cases = [
        {
            "text": "Sulfur, Arsine, and Mercury Remover Industry",
            "expected": "Should find 'Industry'"
        },
        {
            "text": "Carbon Black Growth Report",  
            "expected": "Should find 'Growth Report'"
        },
        {
            "text": "Industry",
            "expected": "Should find 'Industry' (single word)"
        },
        {
            "text": "Growth Report",
            "expected": "Should find 'Growth Report' (direct match)"
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        text = test_case["text"]
        expected = test_case["expected"]
        
        print(f"=== Test {i}: '{text}' ===")
        print(f"Expected: {expected}")
        
        try:
            # Test the internal method directly
            if hasattr(report_extractor, '_search_report_patterns_without_market_v3'):
                result = report_extractor._search_report_patterns_without_market_v3(text)
                print(f"Result type: {type(result)}")
                print(f"Result: {result}")
                
                if isinstance(result, dict):
                    for key, value in result.items():
                        print(f"  {key}: {value}")
                        
                    if result.get('extracted_report_type'):
                        print(f"✅ SUCCESS: Found '{result.get('extracted_report_type')}'")
                    else:
                        print(f"❌ FAILED: No report type found")
            else:
                print(f"❌ Method '_search_report_patterns_without_market_v3' not found")
                
        except Exception as e:
            print(f"❌ ERROR: {e}")
            import traceback
            traceback.print_exc()
        
        print("-" * 50)
        print()

if __name__ == "__main__":
    debug_search_patterns()