#!/usr/bin/env python3
"""
Debug script to trace ampersand loss in geographic extraction
"""

import sys
import os
import importlib.util
from dotenv import load_dotenv

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Load environment variables
load_dotenv()

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
script04 = import_module_from_path("geo_detector",
                                 os.path.join(parent_dir, "04_geographic_entity_detector_v2.py"))

# Initialize PatternLibraryManager
pattern_lib_manager = pattern_manager.PatternLibraryManager(os.getenv('MONGODB_URI'))

# Initialize geographic detector
geo_detector = script04.GeographicEntityDetector(pattern_lib_manager)

# Test cases
test_cases = [
    "U.S. Windows & Patio Doors for Single Family Homes",
    "Oil & Gas",
    "Food + Beverages",
    "Mergers & Acquisitions in Banking/Finance"
]

print("=" * 80)
print("DEBUG: Tracing ampersand loss in geographic extraction")
print("=" * 80)

for test_case in test_cases:
    print(f"\nInput: '{test_case}'")

    # Extract geographic entities
    result = geo_detector.extract_geographic_entities(test_case)

    print(f"Extracted regions: {result.extracted_regions}")
    print(f"Remaining text: '{result.title}'")

    # Check if symbols are preserved
    if '&' in test_case and '&' not in result.title:
        print(f"❌ AMPERSAND LOST!")
    elif '+' in test_case and '+' not in result.title:
        print(f"❌ PLUS LOST!")
    else:
        print(f"✅ Symbols preserved")