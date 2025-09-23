#!/usr/bin/env python3
"""
Debug script for Issue #27: Detailed analysis of extraction process
"""

import os
import sys
import logging
from datetime import datetime
import pytz
import json

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def import_module_from_path(module_name: str, file_path: str):
    """Import a module from a specific file path."""
    import importlib.util
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

def debug_extraction_process():
    """Debug the exact extraction process for failing cases."""

    # Import required modules
    parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    pattern_manager = import_module_from_path("pattern_library_manager",
                                            os.path.join(parent_dir, "00b_pattern_library_manager_v1.py"))
    script03 = import_module_from_path("report_extractor",
                                     os.path.join(parent_dir, "03_report_type_extractor_v4.py"))

    # Initialize components
    from dotenv import load_dotenv
    load_dotenv()

    pattern_lib_manager = pattern_manager.PatternLibraryManager(os.getenv('MONGODB_URI'))
    report_extractor = script03.PureDictionaryReportTypeExtractor(pattern_lib_manager)

    # Debug test cases
    test_cases = [
        "Data Monetization Market Outlook, Trends, Analysis",
        "Europe Building Information Modeling Market Analysis Report, 2024",
        "Global Food Processing Equipment Market Trends & Opportunities"
    ]

    print("\n" + "="*80)
    print("Debugging Issue #27: Extraction Process Details")
    print("="*80 + "\n")

    for test_case in test_cases:
        print(f"Title: {test_case}")
        print("-" * 60)

        # Extract report type with full details
        result = report_extractor.extract(test_case)

        print(f"Original Title: {test_case}")
        print(f"Extracted Type: '{result.extracted_report_type}'")
        print(f"Remaining Title: '{result.title}'")

        # Debug the extraction details
        if hasattr(result, 'dictionary_result') and result.dictionary_result:
            dr = result.dictionary_result
            print(f"Keywords Found: {dr.keywords_found}")
            print(f"Keyword Positions: {dr.keyword_positions}")

        # Show what string replacement would do
        if result.extracted_report_type:
            manual_replace = test_case.replace(result.extracted_report_type, "", 1)
            print(f"Manual Replace Result: '{manual_replace.strip()}'")

        print("\n")

def main():
    """Main execution function."""
    try:
        debug_extraction_process()
        return 0
    except Exception as e:
        logger.error(f"Error during debugging: {e}", exc_info=True)
        return 1

if __name__ == "__main__":
    sys.exit(main())