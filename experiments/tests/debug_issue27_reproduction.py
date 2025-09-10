#!/usr/bin/env python3
"""
Debug script for Issue #27: Reproduce content loss in Script 03 v4
"""

import os
import sys
import logging
from dotenv import load_dotenv
from pymongo import MongoClient
import importlib.util

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

load_dotenv()

# Setup debug logging
logging.basicConfig(level=logging.DEBUG, format='%(name)s - %(levelname)s - %(message)s')

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
script03 = import_module_from_path("report_extractor",
                                 os.path.join(parent_dir, "03_report_type_extractor_v4.py"))

# Initialize components
pattern_lib_manager = pattern_manager.PatternLibraryManager(os.getenv('MONGODB_URI'))
report_extractor = script03.PureDictionaryReportTypeExtractor(pattern_lib_manager)

# Test failing examples
test_cases = [
    "Data Monetization Market Outlook, Trends, Analysis",
    "Data Brokers Market",
    "Oil & Gas Data Management Market"
]

print("\n" + "="*80)
print("DEBUGGING ISSUE #27: Content Loss in Script 03 v4")
print("="*80)

for i, title in enumerate(test_cases, 1):
    print(f"\nTest Case {i}: {title}")
    print("-" * 40)
    
    # Process through extractor
    result = report_extractor.extract(title, market_term_type="standard")
    
    print(f"Extracted Report Type: '{result.extracted_report_type}'")
    print(f"Remaining Title (Topic): '{result.title}'")
    print(f"Keywords Detected: {result.keywords_detected}")
    print(f"Confidence: {result.confidence:.2f}")
    
    if result.dictionary_result:
        print(f"Dictionary Keywords Found: {result.dictionary_result.keywords_found}")
        print(f"Keyword Positions: {result.dictionary_result.keyword_positions}")
        print(f"Separators: {result.dictionary_result.separators}")

print("\n" + "="*80)
print("Analysis Complete")
print("="*80)