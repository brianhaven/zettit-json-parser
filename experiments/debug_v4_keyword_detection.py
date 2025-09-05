#!/usr/bin/env python3
"""
Debug Script for Issue #21 - Keyword Detection in v4 Extractor
==============================================================

Debug why PureDictionaryReportTypeExtractor is not finding keywords.
"""

import os
import sys
import logging
import importlib.util
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def import_module_from_path(module_name: str, file_path: str):
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

def main():
    load_dotenv()
    
    # Test titles
    test_cases = [
        ("Material Handling Equipment Market In Biomass Power Plant Report", "market_in"),
        ("Cloud Computing Market in Healthcare Industy", "market_in"),
        ("Nanocapsules Market for Cosmetics Repot", "market_for"),
        ("High Purity Quartz Sand Market for UVC Lighting Share and Size Outlook", "market_for")
    ]
    
    # Import modules
    current_dir = os.path.dirname(os.path.abspath(__file__))
    pattern_manager = import_module_from_path("pattern_library_manager",
                                            os.path.join(current_dir, "00b_pattern_library_manager_v1.py"))
    script03_v4 = import_module_from_path("report_type_extractor_v4",
                                        os.path.join(current_dir, "03_report_type_extractor_v4.py"))
    
    # Initialize
    pattern_lib_manager = pattern_manager.PatternLibraryManager(os.getenv('MONGODB_URI'))
    extractor = script03_v4.PureDictionaryReportTypeExtractor(pattern_lib_manager)
    
    print("="*80)
    print("DEBUG: KEYWORD DETECTION IN V4 EXTRACTOR")
    print("="*80)
    
    print(f"Loaded Keywords:")
    print(f"  Primary: {extractor.primary_keywords}")
    print(f"  Secondary: {extractor.secondary_keywords}")
    print(f"  All: {extractor.all_keywords}")
    print()
    
    for title, market_type in test_cases:
        print(f"Testing: '{title}'")
        print("-" * 60)
        
        # Test keyword position finding
        keyword_positions = extractor._find_keyword_positions(title)
        print(f"Found keyword positions: {keyword_positions}")
        
        # Test dictionary detection
        dictionary_result = extractor.detect_keywords_in_title(title)
        print(f"Dictionary result:")
        print(f"  Keywords found: {dictionary_result.keywords_found}")
        print(f"  Sequence: {dictionary_result.sequence}")
        print(f"  Separators: {dictionary_result.separators}")
        print(f"  Confidence: {dictionary_result.confidence:.3f}")
        
        # Test full extraction
        result = extractor.extract(title, market_type)
        print(f"Final result:")
        print(f"  Extracted report type: '{result.extracted_report_type}'")
        print(f"  Remaining title: '{result.title}'")
        print(f"  Confidence: {result.confidence:.3f}")
        
        print()

if __name__ == "__main__":
    main()