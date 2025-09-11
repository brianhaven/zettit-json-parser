#!/usr/bin/env python3
"""
Test script to validate Issue #18 geographic pattern curation changes.
Tests both false positive prevention and correct extraction after curation.
"""

import os
import sys
import json
from datetime import datetime
import pytz
from pymongo import MongoClient
from dotenv import load_dotenv
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Load environment variables
load_dotenv()

def create_output_directory(script_name: str) -> str:
    """Create organized output directory with YYYY/MM/DD structure."""
    # Get absolute path to outputs directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    experiments_dir = os.path.dirname(script_dir)  
    project_root = os.path.dirname(experiments_dir)
    outputs_dir = os.path.join(project_root, 'outputs')
    
    # Create timestamp in Pacific Time
    pdt = pytz.timezone('America/Los_Angeles')
    now = datetime.now(pdt)
    
    # Create organized directory structure
    year_dir = os.path.join(outputs_dir, str(now.year))
    month_dir = os.path.join(year_dir, f"{now.month:02d}")
    day_dir = os.path.join(month_dir, f"{now.day:02d}")
    
    # Create timestamped subdirectory
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

def test_geographic_patterns():
    """Test geographic patterns for Issue #18 validation."""
    
    # Connect to MongoDB
    client = MongoClient(os.getenv('MONGODB_URI'))
    db = client['deathstar']
    patterns_collection = db['pattern_libraries']
    
    # Create output directory
    output_dir = create_output_directory("issue_18_validation")
    output_file = os.path.join(output_dir, "validation_results.txt")
    
    results = []
    
    # Test cases for false positives that should be prevented
    false_positive_test_cases = [
        ("ID card printer Market Analysis, 2024", "ID", "Idaho"),
        ("IDentity management Market Report", "ID", "Idaho"),
        ("Microsoft MS Office Market Study", "MS", "Mississippi"),
        ("MS degree holders in Market Research", "MS", "Mississippi"),
        ("IT infrastructure Market Outlook", "IT", "Italy"),
        ("Information Technology (IT) Market", "IT", "Italy"),
        ("Market for widgets OR gadgets", "OR", "Oregon"),
        ("GO programming language Market", "GO", "Goiás"),
        ("Market trends IN technology", "IN", "Indiana"),
    ]
    
    # Test cases for correct extraction that should still work
    correct_extraction_test_cases = [
        ("Idaho potato Market Analysis", "Idaho"),
        ("Oregon timber Market Report", "Oregon"),
        ("Mississippi river Market Study", "Mississippi"),
        ("Italy fashion Market Overview", "Italy"),
        ("Indiana automotive Market", "Indiana"),
        ("North America Market Report", "North America"),
        ("Europe Market Analysis", "Europe"),
        ("Asia Market Study", "Asia"),
        ("Middle East Market Overview", "Middle East"),
    ]
    
    # Test cases for compound regions that should extract as separate entities
    compound_region_test_cases = [
        ("North America and Europe Market Report", ["North America", "Europe"]),
        ("Asia and Middle East Market Analysis", ["Asia", "Middle East"]),
        ("North and South America Market Study", ["North America", "South America"]),
        ("Europe and Asia Market Overview", ["Europe", "Asia"]),
    ]
    
    # Valid compound regions that should extract as single entities
    valid_compound_test_cases = [
        ("Australia and New Zealand Market Report", ["Australia and New Zealand"]),
        ("Europe, Middle East and Africa Market Analysis", ["Europe, Middle East and Africa"]),
        ("Bosnia and Herzegovina Market Study", ["Bosnia and Herzegovina"]),
        ("Trinidad and Tobago Market Overview", ["Trinidad and Tobago"]),
    ]
    
    results.append("=" * 80)
    results.append("ISSUE #18 GEOGRAPHIC PATTERN VALIDATION")
    results.append("=" * 80)
    
    # Check current state of patterns
    results.append("\n1. CHECKING PROBLEMATIC ABBREVIATIONS")
    results.append("-" * 50)
    
    regions_to_check = ["Idaho", "Oregon", "Mississippi", "Italy", "Indiana", "Goiás"]
    
    for region in regions_to_check:
        pattern = patterns_collection.find_one({
            "type": "geographic_entity",
            "term": region
        })
        
        if pattern:
            aliases = pattern.get("aliases", [])
            archived = pattern.get("archived_aliases", [])
            
            results.append(f"\n{region}:")
            results.append(f"  Active aliases: {aliases}")
            results.append(f"  Archived aliases: {archived}")
            
            # Check specific abbreviations
            if region == "Idaho" and "ID" in aliases:
                results.append("  ⚠ WARNING: 'ID' still active (should be archived)")
            elif region == "Idaho" and "ID" in archived:
                results.append("  ✓ 'ID' properly archived")
                
            if region == "Oregon" and "OR" in aliases:
                results.append("  ⚠ WARNING: 'OR' still active (should be archived)")
            elif region == "Oregon" and "OR" in archived:
                results.append("  ✓ 'OR' properly archived")
    
    # Check compound regions
    results.append("\n\n2. CHECKING COMPOUND REGIONS")
    results.append("-" * 50)
    
    invalid_compounds = [
        "North America and Europe",
        "North and South America",
        "Europe and Asia",
        "Asia and Middle East",
        "North and Central America"
    ]
    
    for compound in invalid_compounds:
        pattern = patterns_collection.find_one({
            "type": "geographic_entity",
            "term": compound
        })
        
        if pattern:
            results.append(f"\n'{compound}': ⚠ Still exists (should be removed)")
        else:
            results.append(f"\n'{compound}': ✓ Properly removed")
    
    # Simulate extraction tests
    results.append("\n\n3. FALSE POSITIVE PREVENTION TESTS")
    results.append("-" * 50)
    results.append("\nThese titles should NOT extract the listed regions:")
    
    for title, abbrev, region in false_positive_test_cases:
        results.append(f"\n'{title}'")
        results.append(f"  Should NOT extract: {region} (from '{abbrev}')")
        
        # Check if the abbreviation is archived
        pattern = patterns_collection.find_one({
            "type": "geographic_entity",
            "term": region
        })
        
        if pattern:
            if abbrev in pattern.get("archived_aliases", []):
                results.append(f"  ✓ '{abbrev}' is archived - false positive prevented")
            elif abbrev in pattern.get("aliases", []):
                results.append(f"  ⚠ '{abbrev}' is still active - false positive possible")
            else:
                results.append(f"  ℹ '{abbrev}' not found in pattern")
    
    results.append("\n\n4. CORRECT EXTRACTION TESTS")
    results.append("-" * 50)
    results.append("\nThese titles SHOULD extract the listed regions:")
    
    for title, expected_region in correct_extraction_test_cases:
        results.append(f"\n'{title}'")
        results.append(f"  Should extract: {expected_region}")
        
        # Check if the full region name exists
        pattern = patterns_collection.find_one({
            "type": "geographic_entity",
            "term": expected_region
        })
        
        if pattern:
            results.append(f"  ✓ Pattern exists for '{expected_region}'")
        else:
            results.append(f"  ⚠ Pattern missing for '{expected_region}'")
    
    results.append("\n\n5. COMPOUND REGION SPLITTING TESTS")
    results.append("-" * 50)
    results.append("\nThese compound regions should extract as separate entities:")
    
    for title, expected_regions in compound_region_test_cases:
        results.append(f"\n'{title}'")
        results.append(f"  Should extract: {expected_regions}")
        
        # Check that compound doesn't exist but components do
        compound_term = " and ".join(expected_regions[:2]) if len(expected_regions) == 2 else title.split("Market")[0].strip()
        compound_pattern = patterns_collection.find_one({
            "type": "geographic_entity",
            "term": compound_term
        })
        
        if compound_pattern:
            results.append(f"  ⚠ Compound pattern still exists")
        else:
            results.append(f"  ✓ Compound pattern properly removed")
            
        # Check that individual regions exist
        for region in expected_regions:
            pattern = patterns_collection.find_one({
                "type": "geographic_entity",
                "term": region
            })
            if pattern:
                results.append(f"    ✓ '{region}' pattern exists")
            else:
                results.append(f"    ⚠ '{region}' pattern missing")
    
    results.append("\n\n6. VALID COMPOUND PRESERVATION TESTS")
    results.append("-" * 50)
    results.append("\nThese valid compounds should extract as single entities:")
    
    for title, expected_regions in valid_compound_test_cases:
        results.append(f"\n'{title}'")
        results.append(f"  Should extract: {expected_regions}")
        
        for region in expected_regions:
            pattern = patterns_collection.find_one({
                "type": "geographic_entity",
                "term": region
            })
            if pattern:
                results.append(f"  ✓ Pattern exists for '{region}'")
            else:
                results.append(f"  ⚠ Pattern missing for '{region}'")
    
    # Write results to file
    header = create_file_header("Issue #18 Validation", "Geographic Pattern Curation Validation Results")
    
    with open(output_file, 'w') as f:
        f.write(header)
        f.write('\n'.join(results))
        f.write("\n\n" + "=" * 80)
        f.write("\nEND OF VALIDATION REPORT")
        f.write("\n" + "=" * 80 + "\n")
    
    # Print results to console
    print('\n'.join(results))
    
    print(f"\n\nResults saved to: {output_file}")
    
    return output_dir

if __name__ == "__main__":
    test_geographic_patterns()