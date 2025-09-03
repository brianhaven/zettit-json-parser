#!/usr/bin/env python3
"""
Debug specific v3 failure with Data Analytics Outsourcing Market Size & Share Report 2030

Issue Analysis:
- v2 extracted: "Market Size & Share Report" 
- v3 extracted: "Market Data Size Share Report" (incorrect reconstruction)
- v3 final topic: "" (empty, causing failure)

Root cause likely in reconstruction or cleanup logic.
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
script03v3 = import_module_from_path("report_extractor_v3",
                                   os.path.join(parent_dir, "03_report_type_extractor_v3.py"))

def debug_failure_case():
    """Debug the Data Analytics Outsourcing failure case."""
    
    # Initialize components
    pattern_lib_manager = pattern_manager.PatternLibraryManager(os.getenv('MONGODB_URI'))
    report_extractor_v3 = script03v3.DictionaryBasedReportTypeExtractor(pattern_lib_manager)
    
    # Problem case from test harness - Case 39
    title = "U.S. Research Antibodies Market, Industry Report, 2030"
    
    print(f"Debugging failure with: '{title}'")
    print("=" * 80)
    
    # Step-by-step debugging
    print("1. Dictionary keyword detection:")
    keyword_result = report_extractor_v3.detect_keywords_in_title(title)
    print(f"   Keywords found: {keyword_result.keywords_found}")
    print(f"   Market boundary detected: {keyword_result.market_boundary_detected}")
    print(f"   Sequence: {keyword_result.sequence}")
    if keyword_result.keyword_positions:
        print(f"   Keyword positions: {keyword_result.keyword_positions}")
    
    print("\n2. Report type reconstruction:")
    reconstructed = report_extractor_v3.reconstruct_report_type_from_keywords(keyword_result, title)
    print(f"   Reconstructed: '{reconstructed}'")
    
    print("\n3. Full extraction (with date):")
    result = report_extractor_v3.extract(title, "standard")
    print(f"   Extracted Report Type: '{result.extracted_report_type}'")
    print(f"   Final Topic: '{result.title}'")
    print(f"   Success: {result.success}")
    
    print("\n3b. Full extraction (without date for comparison):")
    title_no_date = "Data Analytics Outsourcing Market Size & Share Report"
    result_no_date = report_extractor_v3.extract(title_no_date, "standard")
    print(f"   Extracted Report Type: '{result_no_date.extracted_report_type}'")
    print(f"   Final Topic: '{result_no_date.title}'")
    print(f"   Success: {result_no_date.success}")
    
    print("\n4. Issue Analysis:")
    if "Data" in result.extracted_report_type:
        print("   ❌ RECONSTRUCTION ISSUE: 'Data' incorrectly included in report type")
    if result.title == "":
        print("   ❌ CLEANUP ISSUE: Report type removal left empty final topic")
        
    print(f"\n5. Expected vs Actual:")
    print(f"   Expected Report Type: 'Market Size & Share Report'")
    print(f"   Actual Report Type: '{result.extracted_report_type}'")
    print(f"   Expected Topic: 'Data Analytics Outsourcing'")  
    print(f"   Actual Topic: '{result.title}'")

if __name__ == "__main__":
    debug_failure_case()