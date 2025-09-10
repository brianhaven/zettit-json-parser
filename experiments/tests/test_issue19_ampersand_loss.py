#!/usr/bin/env python3
"""
Test script to analyze ampersand (&) loss in market term extraction (Issue #19).
"""

import os
import sys
import logging
from dotenv import load_dotenv
from pymongo import MongoClient
import importlib.util

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def import_module_from_path(module_name: str, file_path: str):
    """Import a module from a file path."""
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

def test_ampersand_preservation():
    """Test ampersand preservation in market term extraction."""
    load_dotenv()
    
    # Import modules
    parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    pattern_manager = import_module_from_path("pattern_library_manager",
                                            os.path.join(parent_dir, "00b_pattern_library_manager_v1.py"))
    script03 = import_module_from_path("report_extractor",
                                     os.path.join(parent_dir, "03_report_type_extractor_v4.py"))
    
    # Initialize
    pattern_lib_manager = pattern_manager.PatternLibraryManager(os.getenv('MONGODB_URI'))
    extractor = script03.PureDictionaryReportTypeExtractor(pattern_lib_manager)
    
    # Test cases from Issue #19
    test_cases = [
        {
            "title": "U.S. Windows & Patio Doors Market For Single Family Homes, Report, 2030",
            "market_type": "market_for",
            "expected_context": "Windows & Patio Doors for Single Family Homes",
            "expected_report": "Market Report"
        },
        {
            "title": "Oman Industrial Salts Market For Oil & Gas Industry Report, 2020-2027",
            "market_type": "market_for",
            "expected_context": "Industrial Salts for Oil & Gas Industry",
            "expected_report": "Market Report"
        },
        {
            "title": "Africa Polyvinylpyrrolidone Market for Pharmaceutical & Cosmetic Industries",
            "market_type": "market_for",
            "expected_context": "Polyvinylpyrrolidone for Pharmaceutical & Cosmetic Industries",
            "expected_report": "Market"
        },
        {
            "title": "Big Data Market In The Oil & Gas Sector, Global Industry Report, 2025",
            "market_type": "market_in",
            "expected_context": "Big Data in The Oil & Gas Sector",
            "expected_report": "Market Global Industry Report"
        }
    ]
    
    print("\n" + "="*80)
    print("ISSUE #19: AMPERSAND (&) PRESERVATION TEST")
    print("="*80)
    
    for i, test in enumerate(test_cases, 1):
        print(f"\n{i}. Testing: {test['title']}")
        print("-" * 60)
        
        # Test market term extraction workflow
        market_term, remaining, pipeline_forward = extractor.extract_market_term_workflow(
            test['title'], test['market_type']
        )
        
        print(f"   Market Term Extracted: '{market_term}'")
        print(f"   Remaining Title: '{remaining}'")
        print(f"   Pipeline Forward: '{pipeline_forward}'")
        print(f"   Expected Context: '{test['expected_context']}'")
        
        # Check for ampersand preservation
        has_ampersand_in_original = "&" in test['title']
        has_ampersand_in_pipeline = "&" in pipeline_forward
        
        if has_ampersand_in_original:
            if has_ampersand_in_pipeline:
                print(f"   ✓ Ampersand PRESERVED in pipeline forward")
            else:
                print(f"   ✗ Ampersand LOST in pipeline forward")
        
        # Full extraction test
        result = extractor.extract(test['title'], test['market_type'])
        print(f"\n   Full Extraction Results:")
        print(f"   Report Type: '{result.extracted_report_type}'")
        print(f"   Final Topic: '{result.title}'")
        print(f"   Expected Report: '{test['expected_report']}'")
        
        # Check if ampersand is preserved in final topic
        if has_ampersand_in_original:
            if "&" in result.title:
                print(f"   ✓ Ampersand PRESERVED in final topic")
            else:
                print(f"   ✗ Ampersand LOST in final topic")

if __name__ == "__main__":
    test_ampersand_preservation()