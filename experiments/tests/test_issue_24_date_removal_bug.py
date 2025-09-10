#!/usr/bin/env python3
"""
Test script for GitHub Issue #24: Date Removal Bug Fix
Tests that dates are properly removed from titles during extraction
"""

import sys
import os
import json
from datetime import datetime
import pytz
from pathlib import Path
from dotenv import load_dotenv

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Load environment variables
load_dotenv()

# Dynamic import pattern for main scripts
import importlib.util

def import_module_from_path(module_name: str, file_path: str):
    """Import a module from a file path."""
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

# Import required modules
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
pattern_manager = import_module_from_path("pattern_library_manager",
                                        os.path.join(parent_dir, "00b_pattern_library_manager_v1.py"))
script02 = import_module_from_path("date_extractor",
                                 os.path.join(parent_dir, "02_date_extractor_v1.py"))

def create_output_directory(script_name: str) -> str:
    """Create organized output directory with YYYY/MM/DD structure."""
    # Get project root
    script_dir = os.path.dirname(os.path.abspath(__file__))
    experiments_dir = os.path.dirname(script_dir)
    project_root = os.path.dirname(experiments_dir)
    
    # Create timestamp in Pacific Time
    pdt = pytz.timezone('America/Los_Angeles')
    now = datetime.now(pdt)
    
    # Create organized path: outputs/YYYY/MM/DD/YYYYMMDD_HHMMSS_script_name/
    year = now.strftime('%Y')
    month = now.strftime('%m')
    day = now.strftime('%d')
    timestamp = now.strftime('%Y%m%d_%H%M%S')
    
    output_dir = os.path.join(project_root, 'outputs', year, month, day, f"{timestamp}_{script_name}")
    os.makedirs(output_dir, exist_ok=True)
    
    return output_dir

def create_output_file_header(script_name: str, description: str = "") -> str:
    """Create standardized file header with dual timestamps."""
    pdt = pytz.timezone('America/Los_Angeles')
    utc = pytz.UTC
    
    now_pdt = datetime.now(pdt)
    now_utc = datetime.now(utc)
    
    header = f"""================================================================================
{script_name.upper().replace('_', ' ')}
{description}
================================================================================
Analysis Date (PDT): {now_pdt.strftime('%Y-%m-%d %H:%M:%S')} PDT
Analysis Date (UTC): {now_utc.strftime('%Y-%m-%d %H:%M:%S')} UTC
================================================================================

"""
    return header

def test_date_removal_bug():
    """Test the date removal bug identified in Issue #24."""
    
    # Create output directory
    output_dir = create_output_directory("test_issue_24_date_removal_bug")
    output_file = os.path.join(output_dir, "test_results.txt")
    
    # Initialize components
    pattern_lib_manager = pattern_manager.PatternLibraryManager(os.getenv('MONGODB_URI'))
    date_extractor = script02.EnhancedDateExtractor(pattern_lib_manager)
    
    # Test cases from Issue #24
    test_cases = [
        "Global Market for AI, Machine Learning, and Deep Learning Technologies, 2025-2030",
        "North America, Europe IoT Market, Healthcare, Automotive Applications, 2024-2028",
        "Market in Asia-Pacific: Semiconductors, Electronics & Components, Q1 2025",
        "European Market for Renewable Energy, Wind, Solar, and Hydroelectric Power Markets, 2025",
        "Market Report, 2030",
        "Market Analysis, 2023-2030",
        "Market Study [2024]",
        "Market Outlook 2031"
    ]
    
    results = []
    bug_detected = False
    
    for title in test_cases:
        result = date_extractor.extract(title)
        
        # Check if date was extracted but not removed from title
        if result.extracted_date_range and result.extracted_date_range in result.title:
            bug_detected = True
            status = "BUG DETECTED"
        else:
            status = "OK"
        
        results.append({
            'original_title': title,
            'extracted_date': result.extracted_date_range,
            'returned_title': result.title,
            'cleaned_title': result.cleaned_title,
            'status': status,
            'bug_present': result.extracted_date_range and result.extracted_date_range in result.title
        })
    
    # Write results to file
    with open(output_file, 'w') as f:
        f.write(create_output_file_header("test_issue_24_date_removal_bug", "Date Removal Bug Test"))
        f.write("\n")
        f.write("=" * 80)
        f.write("\nGitHub Issue #24: Date Removal Bug Test Results\n")
        f.write("=" * 80)
        f.write("\n\n")
        
        if bug_detected:
            f.write("⚠️  BUG CONFIRMED: Dates are not being removed from the returned title!\n")
            f.write("The bug is on line 332 of 02_date_extractor_v1.py\n")
            f.write("It returns 'title=title' instead of 'title=cleaned_title'\n\n")
        else:
            f.write("✅ NO BUG DETECTED: Dates are being properly removed from titles.\n\n")
        
        f.write("-" * 80)
        f.write("\nDetailed Test Results:\n")
        f.write("-" * 80)
        f.write("\n\n")
        
        for i, result in enumerate(results, 1):
            f.write(f"Test Case {i}: {result['status']}\n")
            f.write(f"Original:  {result['original_title']}\n")
            f.write(f"Date:      {result['extracted_date'] or 'None'}\n")
            f.write(f"Returned:  {result['returned_title']}\n")
            f.write(f"Cleaned:   {result['cleaned_title']}\n")
            if result['bug_present']:
                f.write(f"⚠️  ERROR: Date '{result['extracted_date']}' still present in returned title!\n")
            f.write("\n")
        
        # Summary statistics
        f.write("-" * 80)
        f.write("\nSummary:\n")
        f.write("-" * 80)
        f.write(f"\nTotal test cases: {len(test_cases)}\n")
        f.write(f"Cases with bug:   {sum(1 for r in results if r['bug_present'])}\n")
        f.write(f"Cases without bug: {sum(1 for r in results if not r['bug_present'])}\n")
        
        if bug_detected:
            f.write("\n⚠️  ACTION REQUIRED: Fix line 332 in 02_date_extractor_v1.py\n")
            f.write("Change: title=title,\n")
            f.write("To:     title=cleaned_title,\n")
    
    # Print summary to console
    print(f"\n{'='*60}")
    print("Issue #24 Date Removal Bug Test Complete")
    print(f"{'='*60}")
    print(f"Results written to: {output_file}")
    print(f"Bug detected: {'YES ⚠️' if bug_detected else 'NO ✅'}")
    if bug_detected:
        print("\nFIX REQUIRED:")
        print("  File: 02_date_extractor_v1.py")
        print("  Line: 332")
        print("  Change: title=title,")
        print("  To:     title=cleaned_title,")
    print(f"{'='*60}\n")
    
    return bug_detected

if __name__ == "__main__":
    bug_found = test_date_removal_bug()
    sys.exit(1 if bug_found else 0)