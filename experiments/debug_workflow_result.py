#!/usr/bin/env python3
"""
Debug Workflow Result
=====================

Test the market aware workflow method directly to see what it returns.
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

def debug_workflow_result():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    pattern_manager = import_module_from_path("pattern_library_manager", 
                                            os.path.join(current_dir, "00b_pattern_library_manager_v1.py"))
    script03v3 = import_module_from_path("report_extractor_v3",
                                       os.path.join(current_dir, "03_report_type_extractor_v3.py"))
    
    pattern_lib_manager = pattern_manager.PatternLibraryManager(os.getenv('MONGODB_URI'))
    report_extractor = script03v3.DictionaryBasedReportTypeExtractor(pattern_lib_manager)
    
    print("=== Testing Market Aware Workflow Directly ===\n")
    
    title = "Carbon Black Market For Textile Fibers Growth Report"
    market_type = "market_for"
    
    print(f"Input: title='{title}', market_type='{market_type}'")
    
    try:
        # Test the workflow method directly
        if hasattr(report_extractor, '_process_market_aware_workflow_v3'):
            result = report_extractor._process_market_aware_workflow_v3(title, market_type)
            print(f"Workflow result type: {type(result)}")
            print(f"Workflow result: {result}")
            
            if isinstance(result, dict):
                print("Dictionary contents:")
                for key, value in result.items():
                    print(f"  {key}: {value}")
                
                # Test the specific keys being accessed
                extracted_type = result.get('extracted_report_type')
                pipeline_text = result.get('pipeline_forward_text', title)
                confidence = result.get('confidence', 0.0)
                
                print(f"\nExtracted from result:")
                print(f"  extracted_report_type: '{extracted_type}'")
                print(f"  pipeline_forward_text: '{pipeline_text}'")
                print(f"  confidence: {confidence}")
        else:
            print("Method '_process_market_aware_workflow_v3' not found")
            
    except Exception as e:
        print(f"ERROR in workflow: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_workflow_result()