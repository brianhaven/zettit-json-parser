#!/usr/bin/env python3
"""
Debug test for DEW acronym pattern matching issue (Fresh version)
"""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv
load_dotenv()

import importlib.util
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def test_dew_pattern_fresh():
    """Test the DEW title with completely fresh module loading."""
    
    print("=== LOADING MODULES FRESH ===")
    
    # Load pattern library manager
    pattern_spec = importlib.util.spec_from_file_location('pattern_manager', '00b_pattern_library_manager_v1.py')
    pattern_module = importlib.util.module_from_spec(pattern_spec)
    pattern_spec.loader.exec_module(pattern_module)
    PatternLibraryManager = pattern_module.PatternLibraryManager
    
    # Load the extractor module
    extractor_spec = importlib.util.spec_from_file_location('report_extractor', '03_report_type_extractor_v2.py')
    extractor_module = importlib.util.module_from_spec(extractor_spec)
    extractor_spec.loader.exec_module(extractor_module)
    MarketAwareReportTypeExtractor = extractor_module.MarketAwareReportTypeExtractor
    
    # Initialize fresh instances
    print("Creating fresh pattern manager...")
    pattern_manager = PatternLibraryManager()
    
    print("Creating fresh extractor...")
    extractor = MarketAwareReportTypeExtractor(pattern_manager)
    
    # Test the specific problematic title
    test_title = 'Directed Energy Weapons Market Size, DEW Industry Report'
    print(f'Testing title: {test_title}')
    print(f'Market term type: standard (simulating standard workflow)')
    print()
    
    # Extract without date (simulate pipeline state)
    result = extractor.extract(test_title, market_term_type='standard')
    
    print("=== FRESH EXTRACTION RESULTS ===")
    print(f'Result format_type: {result.format_type}')
    print(f'Result extracted_report_type: {result.extracted_report_type}')
    print(f'Result final_report_type: {result.final_report_type}')
    print(f'Result matched_pattern: {result.matched_pattern}')
    print(f'Result notes: {result.notes}')
    print(f'Result confidence: {result.confidence}')
    print()
    
    # Check what the issue is
    print("=== ANALYSIS ===")
    if result.format_type.value == 'compound_type':
        print("❌ ISSUE PERSISTS: Title matched compound_type instead of acronym_embedded")
        print("The pattern priority issue still exists even with fresh loading.")
    elif result.format_type.value == 'acronym_embedded':
        print("✅ SUCCESS: Title correctly matched acronym_embedded pattern")
        print("The pattern priority issue has been resolved!")
    else:
        print(f"❓ UNEXPECTED: Title matched {result.format_type.value}")

if __name__ == "__main__":
    test_dew_pattern_fresh()