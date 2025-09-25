#!/usr/bin/env python3
"""
Debug script for Git Issue #33: Understanding regional group detection
"""

import os
import sys
import re
import importlib.util
from dotenv import load_dotenv

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Load environment variables
load_dotenv()

def import_module_from_path(module_name: str, file_path: str):
    """Import a module from a file path."""
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

def debug_regional_detection():
    """Debug the regional group detection logic."""

    # Import required modules
    parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    pattern_manager = import_module_from_path("pattern_library_manager",
                                             os.path.join(parent_dir, "00b_pattern_library_manager_v1.py"))
    script04_v3 = import_module_from_path("geographic_detector_v3",
                                          os.path.join(parent_dir, "04_geographic_entity_detector_v3.py"))

    # Initialize components
    pattern_lib_manager = pattern_manager.PatternLibraryManager(os.getenv('MONGODB_URI'))
    detector_v3 = script04_v3.GeographicEntityDetector(pattern_lib_manager)

    # Test case: "U.S. And Europe Digital Pathology"
    test_text = "U.S. And Europe Digital Pathology"

    print("\n" + "="*80)
    print("DEBUG: Regional Group Detection")
    print("="*80)
    print(f"\nInput text: '{test_text}'")

    # Step 1: Find all geographic matches
    print("\n" + "-"*80)
    print("Step 1: Finding All Geographic Matches")
    print("-"*80)

    all_matches = []
    for pattern in detector_v3.geographic_patterns[:20]:  # Check top 20 patterns
        try:
            matches = list(re.finditer(pattern.pattern, test_text, re.IGNORECASE))
            for match in matches:
                if not detector_v3.is_part_of_hyphenated_word(test_text, match):
                    all_matches.append((match.start(), match.end(), match.group(), pattern.term))
                    print(f"Found: '{match.group()}' at [{match.start()}:{match.end()}] -> Pattern: '{pattern.term}'")
        except Exception as e:
            continue

    # Sort matches by position
    all_matches.sort(key=lambda x: x[0])

    print(f"\nTotal matches found: {len(all_matches)}")

    # Step 2: Analyze text between matches
    print("\n" + "-"*80)
    print("Step 2: Analyzing Text Between Matches")
    print("-"*80)

    if len(all_matches) >= 2:
        for i in range(len(all_matches) - 1):
            current = all_matches[i]
            next_match = all_matches[i + 1]

            between_start = current[1]
            between_end = next_match[0]
            between_text = test_text[between_start:between_end]
            between_text_stripped = between_text.strip()

            print(f"\nBetween '{current[2]}' and '{next_match[2]}':")
            print(f"  - Raw text: '{between_text}'")
            print(f"  - Stripped: '{between_text_stripped}'")
            print(f"  - Is separator?: {between_text_stripped in detector_v3.REGIONAL_SEPARATORS}")

            if between_text_stripped in detector_v3.REGIONAL_SEPARATORS:
                print(f"  ✅ REGIONAL GROUP DETECTED: '{current[2]} {between_text_stripped} {next_match[2]}'")

    # Step 3: Test the detect_regional_groups method
    print("\n" + "-"*80)
    print("Step 3: Testing detect_regional_groups Method")
    print("-"*80)

    regional_groups = detector_v3.detect_regional_groups(test_text)

    print(f"\nRegional groups found: {len(regional_groups)}")

    for i, group in enumerate(regional_groups, 1):
        print(f"\nGroup {i}:")
        print(f"  - Full text: '{group.full_text}'")
        print(f"  - Position: [{group.full_start}:{group.full_end}]")
        print(f"  - Regions: {[r[2] for r in group.regions]}")
        print(f"  - Separators: {[s[2] for s in group.separators]}")

    # Step 4: Test the full extraction
    print("\n" + "-"*80)
    print("Step 4: Full Extraction Result")
    print("-"*80)

    result = detector_v3.extract_geographic_entities(test_text)

    print(f"\nExtracted regions: {result.extracted_regions}")
    print(f"Remaining text: '{result.title}'")
    print(f"Confidence: {result.confidence:.3f}")

    # Additional test cases
    print("\n" + "="*80)
    print("ADDITIONAL TEST CASES")
    print("="*80)

    additional_tests = [
        "Latin America Plus Asia Pacific Services",
        "North America & Europe Technology",
        "Europe And Middle East Healthcare"
    ]

    for test in additional_tests:
        print(f"\n'{test}':")
        groups = detector_v3.detect_regional_groups(test)
        print(f"  - Regional groups: {len(groups)}")
        if groups:
            for g in groups:
                print(f"    • '{g.full_text}'")

        result = detector_v3.extract_geographic_entities(test)
        print(f"  - Result: '{result.title}'")

if __name__ == "__main__":
    debug_regional_detection()