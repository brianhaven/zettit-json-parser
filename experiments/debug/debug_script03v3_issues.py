#!/usr/bin/env python3
"""
Debug Script for Script 03 v3 Issues
=====================================

Testing the specific issues found in the test harness:
1. "&" removal in "Private LTE & 5G Network"  
2. lowercase "in" leaving stray "n" in "Sulfur, Arsine, and Mercury Remover n Oil & Gas Industry"
3. "Market For" corruption in "Carbon Black xtile Fibers"
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

def test_script03v3_issues():
    """Test the specific issues found in Script 03 v3."""
    
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
    
    print("=== Testing Script 03 v3 Issues ===\n")
    
    # Test cases with known issues
    test_cases = [
        {
            "title": "U.S. Private LTE & 5G Network Market Size Report, 2030",
            "issue": "& removal", 
            "expected_topic": "should preserve &"
        },
        {
            "title": "Sulfur, Arsine, and Mercury Remover Market in Oil & Gas Industry",
            "issue": "lowercase 'in' parsing",
            "expected_topic": "should not have stray 'n'"
        },
        {
            "title": "Carbon Black Market For Textile Fibers Growth Report, 2020", 
            "issue": "Market For corruption",
            "expected_topic": "should not corrupt 'Textile'"
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        title = test_case["title"]
        issue = test_case["issue"]
        
        print(f"Test {i}: {issue}")
        print(f"Original Title: {title}")
        
        try:
            # Step 1: Market classification
            market_result = market_classifier.classify(title)
            print(f"Market Type: {market_result.market_type}")
            
            # Step 2: Report type extraction (after date removal simulation)
            # Simulate date removal for testing
            title_after_date = title.replace(", 2030", "").replace(", 2020", "")
            
            report_result = report_extractor.extract(title_after_date, market_result.market_type)
            
            print(f"Extracted Report Type: '{report_result.extracted_report_type}'")
            print(f"Remaining Title: '{report_result.title}'")
            
            # Detailed debugging for market term extraction
            if hasattr(report_result, 'market_prefix_extracted') and report_result.market_prefix_extracted:
                print(f"Market Prefix: '{report_result.market_prefix_extracted}'")
            if hasattr(report_result, 'market_context_preserved') and report_result.market_context_preserved:
                print(f"Market Context: '{report_result.market_context_preserved}'")
            
            # Check dictionary detection details
            if hasattr(report_result, 'dictionary_result') and report_result.dictionary_result:
                dict_result = report_result.dictionary_result
                print(f"Keywords Found: {dict_result.keywords_found}")
                print(f"Market Boundary: {dict_result.market_boundary_detected}")
                if dict_result.separators:
                    print(f"Separators Found: {dict_result.separators}")
                if dict_result.boundary_markers:
                    print(f"Boundary Markers: {dict_result.boundary_markers}")
            
        except Exception as e:
            print(f"ERROR: {e}")
            import traceback
            traceback.print_exc()
        
        print("-" * 80)
        print()

if __name__ == "__main__":
    test_script03v3_issues()