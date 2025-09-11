#!/usr/bin/env python3
"""
Integration test for Issue #18 - Test full pipeline with curated geographic patterns.
Validates that the curation changes work correctly in the complete processing pipeline.
"""

import os
import sys
import json
import importlib.util
from datetime import datetime
import pytz
from pymongo import MongoClient
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

def create_output_directory(script_name: str) -> str:
    """Create organized output directory with YYYY/MM/DD structure."""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    experiments_dir = os.path.dirname(script_dir)  
    project_root = os.path.dirname(experiments_dir)
    outputs_dir = os.path.join(project_root, 'outputs')
    
    pdt = pytz.timezone('America/Los_Angeles')
    now = datetime.now(pdt)
    
    year_dir = os.path.join(outputs_dir, str(now.year))
    month_dir = os.path.join(year_dir, f"{now.month:02d}")
    day_dir = os.path.join(month_dir, f"{now.day:02d}")
    
    timestamp = now.strftime('%Y%m%d_%H%M%S')
    output_dir = os.path.join(day_dir, f"{timestamp}_{script_name}")
    os.makedirs(output_dir, exist_ok=True)
    
    return output_dir

def create_file_header(script_name: str, description: str = "") -> str:
    """Create standardized file header with dual timestamps."""
    pdt = pytz.timezone('America/Los_Angeles')
    now_pdt = datetime.now(pdt)
    now_utc = datetime.now(pytz.UTC)
    
    header = f"""================================================================================
{script_name.upper()}
{description}
================================================================================

**Analysis Date (PDT):** {now_pdt.strftime('%Y-%m-%d %H:%M:%S')} PDT
**Analysis Date (UTC):** {now_utc.strftime('%Y-%m-%d %H:%M:%S')} UTC

================================================================================

"""
    return header

def test_pipeline_with_curated_patterns():
    """Test the full pipeline with curated geographic patterns."""
    
    # Import pipeline components
    parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    # Import PatternLibraryManager
    pattern_manager = import_module_from_path("pattern_library_manager",
                                            os.path.join(parent_dir, "00b_pattern_library_manager_v1.py"))
    
    # Import Script 04 (Geographic Entity Detector)
    script04 = import_module_from_path("geographic_detector",
                                      os.path.join(parent_dir, "04_geographic_entity_detector_v2.py"))
    
    # Initialize PatternLibraryManager with connection string
    pattern_lib_manager = pattern_manager.PatternLibraryManager(os.getenv('MONGODB_URI'))
    
    # Initialize geographic detector with PatternLibraryManager (Script 04 v2 architecture)
    geo_detector = script04.GeographicEntityDetector(pattern_lib_manager)
    
    # Create output directory
    output_dir = create_output_directory("issue_18_pipeline_test")
    output_file = os.path.join(output_dir, "pipeline_test_results.txt")
    
    results = []
    results.append("=" * 80)
    results.append("ISSUE #18 PIPELINE INTEGRATION TEST")
    results.append("Testing full pipeline with curated geographic patterns")
    results.append("=" * 80)
    
    # Test cases that should NOT extract problematic abbreviations
    false_positive_test_cases = [
        {
            "title": "ID card printer Market Analysis, 2024",
            "expected_regions": [],
            "should_not_extract": "Idaho",
            "reason": "'ID' archived as abbreviation"
        },
        {
            "title": "Microsoft MS Office Market Study",
            "expected_regions": [],
            "should_not_extract": "Mississippi", 
            "reason": "'MS' archived as abbreviation"
        },
        {
            "title": "Market for widgets OR gadgets",
            "expected_regions": [],
            "should_not_extract": "Oregon",
            "reason": "'OR' archived as abbreviation"
        },
        {
            "title": "GO programming language Market",
            "expected_regions": [],
            "should_not_extract": "Goiás",
            "reason": "'GO' archived as abbreviation"
        }
    ]
    
    # Test cases for correct extraction
    correct_extraction_test_cases = [
        {
            "title": "Idaho potato Market Analysis",
            "expected_regions": ["Idaho"],
            "reason": "Full state name should extract"
        },
        {
            "title": "Oregon timber Market Report",
            "expected_regions": ["Oregon"],
            "reason": "Full state name should extract"
        },
        {
            "title": "Mississippi river transportation Market",
            "expected_regions": ["Mississippi"],
            "reason": "Full state name should extract"
        },
        {
            "title": "North America automotive Market",
            "expected_regions": ["North America"],
            "reason": "Continental region should extract"
        }
    ]
    
    # Test cases for compound region splitting
    compound_region_test_cases = [
        {
            "title": "North America and Europe semiconductor Market",
            "expected_regions": ["North America", "Europe"],
            "reason": "Invalid compound should split into separate regions"
        },
        {
            "title": "Asia and Middle East pharmaceutical Market",
            "expected_regions": ["Asia", "Middle East"],
            "reason": "Invalid compound should split into separate regions"
        }
    ]
    
    # Test cases for valid compound preservation
    valid_compound_test_cases = [
        {
            "title": "Australia and New Zealand dairy Market",
            "expected_regions": ["Australia and New Zealand"],
            "reason": "Valid ANZ compound should remain intact"
        },
        {
            "title": "Europe, Middle East and Africa telecom Market",
            "expected_regions": ["Europe, Middle East and Africa"],
            "reason": "Valid EMEA compound should remain intact"
        },
        {
            "title": "Bosnia and Herzegovina tourism Market",
            "expected_regions": ["Bosnia and Herzegovina"],
            "reason": "Valid country name should remain intact"
        }
    ]
    
    # Run tests
    results.append("\n1. FALSE POSITIVE PREVENTION TESTS")
    results.append("-" * 50)
    
    for test_case in false_positive_test_cases:
        title = test_case["title"]
        expected = test_case["expected_regions"]
        should_not = test_case["should_not_extract"]
        reason = test_case["reason"]
        
        # Extract regions using the detector
        result = geo_detector.extract_geographic_entities(title)
        extracted = result.extracted_regions if hasattr(result, 'extracted_regions') else []
        
        results.append(f"\nTitle: '{title}'")
        results.append(f"  Expected: {expected}")
        results.append(f"  Extracted: {extracted}")
        results.append(f"  Should NOT extract: {should_not}")
        
        if should_not not in extracted:
            results.append(f"  ✓ PASS - {reason}")
        else:
            results.append(f"  ✗ FAIL - {should_not} incorrectly extracted")
    
    results.append("\n\n2. CORRECT EXTRACTION TESTS")
    results.append("-" * 50)
    
    for test_case in correct_extraction_test_cases:
        title = test_case["title"]
        expected = test_case["expected_regions"]
        reason = test_case["reason"]
        
        result = geo_detector.extract_geographic_entities(title)
        extracted = result.extracted_regions if hasattr(result, 'extracted_regions') else []
        
        results.append(f"\nTitle: '{title}'")
        results.append(f"  Expected: {expected}")
        results.append(f"  Extracted: {extracted}")
        
        if all(region in extracted for region in expected):
            results.append(f"  ✓ PASS - {reason}")
        else:
            missing = [r for r in expected if r not in extracted]
            results.append(f"  ✗ FAIL - Missing: {missing}")
    
    results.append("\n\n3. COMPOUND REGION SPLITTING TESTS")
    results.append("-" * 50)
    
    for test_case in compound_region_test_cases:
        title = test_case["title"]
        expected = test_case["expected_regions"]
        reason = test_case["reason"]
        
        result = geo_detector.extract_geographic_entities(title)
        extracted = result.extracted_regions if hasattr(result, 'extracted_regions') else []
        
        results.append(f"\nTitle: '{title}'")
        results.append(f"  Expected: {expected}")
        results.append(f"  Extracted: {extracted}")
        
        if all(region in extracted for region in expected):
            # Also check that invalid compound is NOT extracted
            invalid_compound = " and ".join(expected)
            if invalid_compound not in extracted:
                results.append(f"  ✓ PASS - {reason}")
            else:
                results.append(f"  ✗ FAIL - Invalid compound '{invalid_compound}' not removed")
        else:
            missing = [r for r in expected if r not in extracted]
            results.append(f"  ✗ FAIL - Missing: {missing}")
    
    results.append("\n\n4. VALID COMPOUND PRESERVATION TESTS")
    results.append("-" * 50)
    
    for test_case in valid_compound_test_cases:
        title = test_case["title"]
        expected = test_case["expected_regions"]
        reason = test_case["reason"]
        
        result = geo_detector.extract_geographic_entities(title)
        extracted = result.extracted_regions if hasattr(result, 'extracted_regions') else []
        
        results.append(f"\nTitle: '{title}'")
        results.append(f"  Expected: {expected}")
        results.append(f"  Extracted: {extracted}")
        
        if all(region in extracted for region in expected):
            results.append(f"  ✓ PASS - {reason}")
        else:
            missing = [r for r in expected if r not in extracted]
            results.append(f"  ✗ FAIL - Missing: {missing}")
    
    # Summary
    results.append("\n\n" + "=" * 80)
    results.append("TEST SUMMARY")
    results.append("=" * 80)
    
    total_tests = (len(false_positive_test_cases) + len(correct_extraction_test_cases) + 
                  len(compound_region_test_cases) + len(valid_compound_test_cases))
    
    results.append(f"\nTotal tests run: {total_tests}")
    results.append("\nNote: This test validates that Issue #18 curation changes are working correctly")
    results.append("in the actual processing pipeline.")
    
    # Write results to file
    header = create_file_header("Issue #18 Pipeline Integration Test", 
                               "Full pipeline test with curated geographic patterns")
    
    with open(output_file, 'w') as f:
        f.write(header)
        f.write('\n'.join(results))
        f.write("\n\n" + "=" * 80)
        f.write("\nEND OF PIPELINE TEST")
        f.write("\n" + "=" * 80 + "\n")
    
    # Print results to console
    print('\n'.join(results))
    
    print(f"\n\nResults saved to: {output_file}")
    
    return output_dir

if __name__ == "__main__":
    test_pipeline_with_curated_patterns()