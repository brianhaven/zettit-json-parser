#!/usr/bin/env python3
"""
Debug script to understand what's happening with parentheses in date extraction
"""

import os
import sys
import logging
from dotenv import load_dotenv

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

import importlib.util

def import_module_from_path(module_name: str, file_path: str):
    """Import a module from a file path."""
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

def debug_date_extraction():
    """Debug what's happening with date extraction."""

    # Import necessary modules
    parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    # Import PatternLibraryManager
    pattern_manager = import_module_from_path("pattern_library_manager",
                                            os.path.join(parent_dir, "00b_pattern_library_manager_v1.py"))

    # Import date extractor
    script02 = import_module_from_path("date_extractor",
                                     os.path.join(parent_dir, "02_date_extractor_v1.py"))

    # Initialize PatternLibraryManager
    pattern_lib_manager = pattern_manager.PatternLibraryManager(os.getenv('MONGODB_URI'))

    # Initialize components
    date_extractor = script02.EnhancedDateExtractor(pattern_lib_manager)

    # Test case
    title = "Battery Fuel Gauge Market (Forecast 2020-2030)"

    logger.info(f"Original Title: '{title}'")

    # Extract with debugging
    result = date_extractor.extract(title)

    logger.info(f"Date Extracted: {result.extracted_date_range}")
    logger.info(f"Raw Match: '{result.raw_match}'")
    logger.info(f"Matched Pattern: {result.matched_pattern}")
    logger.info(f"Cleaned Title: '{result.cleaned_title}'")
    logger.info(f"Title (for pipeline): '{result.title}'")
    logger.info(f"Preserved Words: {result.preserved_words}")
    logger.info(f"Format Type: {result.format_type}")

    # Let's also check what happens when we manually test the pattern
    import re

    # Check if the pattern captures the whole parenthetical section
    test_patterns = [
        r'\(.*?(\d{4})\s*-\s*(\d{4}).*?\)',  # Captures whole parentheses
        r'(\d{4})\s*-\s*(\d{4})',            # Only captures date range
    ]

    for pattern in test_patterns:
        match = re.search(pattern, title)
        if match:
            logger.info(f"\nPattern: {pattern}")
            logger.info(f"  Full Match: '{match.group(0)}'")
            logger.info(f"  Groups: {match.groups()}")

            # Simulate cleanup
            cleaned = title.replace(match.group(0), '').strip()
            logger.info(f"  After removal: '{cleaned}'")

if __name__ == "__main__":
    debug_date_extraction()