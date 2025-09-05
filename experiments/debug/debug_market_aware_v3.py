#!/usr/bin/env python3
"""
Debug Market-Aware Workflow v3 Pattern Matching Issues
=====================================================

Specifically debug why market_in and market_for processing is returning empty report types.
Add detailed logging to trace exactly where the pattern matching fails.
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

def debug_market_aware_workflow():
    """Debug the market-aware workflow pattern matching failures."""
    
    # Import required modules
    current_dir = os.path.dirname(os.path.abspath(__file__))
    pattern_manager = import_module_from_path("pattern_library_manager", 
                                            os.path.join(current_dir, "00b_pattern_library_manager_v1.py"))
    script01 = import_module_from_path("market_classifier", 
                                     os.path.join(current_dir, "01_market_term_classifier_v1.py"))
    script03v3 = import_module_from_path("report_extractor_v3",
                                       os.path.join(current_dir, "03_report_type_extractor_v3.py"))
    
    # Initialize components
    pattern_lib_manager = pattern_manager.PatternLibraryManager(os.getenv('MONGODB_URI'))
    market_classifier = script01.MarketTermClassifier(pattern_lib_manager)
    report_extractor = script03v3.DictionaryBasedReportTypeExtractor(pattern_lib_manager)
    
    print("=== Debugging Market-Aware Workflow v3 ===\n")
    
    # Focus on the two failing cases
    test_cases = [
        {
            "title": "Sulfur, Arsine, and Mercury Remover Market in Oil & Gas Industry",
            "issue": "market_in processing - empty report type",
            "expected_topic": "Sulfur, Arsine, and Mercury Remover in Oil & Gas",
            "expected_report": "Market Industry"
        },
        {
            "title": "Carbon Black Market For Textile Fibers Growth Report, 2020",
            "issue": "market_for processing - empty report type", 
            "expected_topic": "Carbon Black for Textile Fibers",
            "expected_report": "Market Growth Report"
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        title = test_case["title"]
        issue = test_case["issue"]
        expected_topic = test_case["expected_topic"]
        expected_report = test_case["expected_report"]
        
        print(f"=== Test {i}: {issue} ===")
        print(f"Original Title: {title}")
        print(f"Expected Topic: {expected_topic}")
        print(f"Expected Report: {expected_report}")
        print()
        
        try:
            # Step 1: Market classification
            market_result = market_classifier.classify(title)
            market_type = market_result.market_type
            print(f"1. Market Classification: {market_type}")
            
            # Step 2: Simulate date removal
            title_after_date = title.replace(", 2020", "")
            print(f"2. After Date Removal: '{title_after_date}'")
            
            # Step 3: Debug the market-aware processing step by step
            print(f"3. Market-Aware Processing Debug:")
            print(f"   Input title: '{title_after_date}'")
            print(f"   Market type: '{market_type}'")
            
            # Access the internal method to debug step by step
            if hasattr(report_extractor, 'extract_market_term_workflow'):
                print(f"\n   Step 3a: Extract Market Term Workflow")
                try:
                    market_term, remaining_title, pipeline_forward = report_extractor.extract_market_term_workflow(
                        title_after_date, market_type
                    )
                    print(f"   → Market term extracted: '{market_term}'")
                    print(f"   → Remaining title: '{remaining_title}'")
                    print(f"   → Pipeline forward: '{pipeline_forward}'")
                except Exception as e:
                    print(f"   ❌ ERROR in extract_market_term_workflow: {e}")
                    import traceback
                    traceback.print_exc()
                    continue
                
                # Step 3b: Debug pattern search without Market
                print(f"\n   Step 3b: Search Report Patterns Without Market")
                try:
                    if hasattr(report_extractor, '_search_report_patterns_without_market_v3'):
                        search_result = report_extractor._search_report_patterns_without_market_v3(remaining_title)
                        print(f"   → Search result type: {type(search_result)}")
                        if isinstance(search_result, dict):
                            print(f"   → Search result keys: {search_result.keys()}")
                            for key, value in search_result.items():
                                print(f"   → {key}: {value}")
                        else:
                            print(f"   → Search result: {search_result}")
                    else:
                        print(f"   ❌ Method '_search_report_patterns_without_market_v3' not found")
                except Exception as e:
                    print(f"   ❌ ERROR in _search_report_patterns_without_market_v3: {e}")
                    import traceback
                    traceback.print_exc()
            else:
                print(f"   ❌ Method 'extract_market_term_workflow' not found in extractor")
            
            # Step 4: Run the full extraction to see final result
            print(f"\n4. Full Extraction Result:")
            report_result = report_extractor.extract(title_after_date, market_type)
            print(f"   → Extracted Report Type: '{report_result.extracted_report_type}'")
            print(f"   → Remaining Title: '{report_result.title}'")
            print(f"   → Success: {report_result.success}")
            print(f"   → Confidence: {getattr(report_result, 'confidence', 'N/A')}")
            
            # Check for any debug attributes
            if hasattr(report_result, 'debug_info'):
                print(f"   → Debug Info: {report_result.debug_info}")
            
        except Exception as e:
            print(f"❌ OVERALL ERROR: {e}")
            import traceback
            traceback.print_exc()
        
        print("-" * 80)
        print()

if __name__ == "__main__":
    debug_market_aware_workflow()