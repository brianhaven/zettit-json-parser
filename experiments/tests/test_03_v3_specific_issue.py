#!/usr/bin/env python3
"""
Test specific v3 issue with duplication and cleanup
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

def test_specific_issue():
    """Test the specific duplication and cleanup issues."""
    
    # Initialize components
    pattern_lib_manager = pattern_manager.PatternLibraryManager(os.getenv('MONGODB_URI'))
    report_extractor_v3 = script03v3.DictionaryBasedReportTypeExtractor(pattern_lib_manager)
    
    # Problem case from test harness
    title = "Digital Signature Market Forecast 2018-2026"
    
    print(f"Testing specific issue with: '{title}'")
    print("=" * 60)
    
    # Step-by-step debugging
    print("1. Dictionary keyword detection:")
    keyword_result = report_extractor_v3.detect_keywords_in_title(title)
    print(f"   Keywords found: {keyword_result.keywords_found}")
    print(f"   Sequence: {keyword_result.sequence}")
    print(f"   Market boundary detected: {keyword_result.market_boundary_detected}")
    
    print("\n2. Report type reconstruction:")
    reconstructed = report_extractor_v3.reconstruct_report_type_from_keywords(keyword_result, title)
    print(f"   Reconstructed: '{reconstructed}'")
    
    print("\n3. Full extraction:")
    result = report_extractor_v3.extract(title, "standard")
    print(f"   Extracted Report Type: '{result.extracted_report_type}'")
    print(f"   Final Topic: '{result.title}'")
    print(f"   Success: {result.success}")
    
    print("\n4. Analysis:")
    if "Forecast Forecast" in result.extracted_report_type:
        print("   ❌ DUPLICATION ISSUE: 'Forecast' appears twice in report type")
    if "Market Forecast" in result.title:
        print("   ❌ CLEANUP ISSUE: Report type not removed from final topic")
    
    print(f"\n5. Expected vs Actual:")
    print(f"   Expected Report Type: 'Market Forecast'")
    print(f"   Actual Report Type: '{result.extracted_report_type}'")
    print(f"   Expected Topic: 'Digital Signature'")  
    print(f"   Actual Topic: '{result.title}'")

if __name__ == "__main__":
    test_specific_issue()