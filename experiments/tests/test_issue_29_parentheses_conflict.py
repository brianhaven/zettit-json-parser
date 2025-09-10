#!/usr/bin/env python3
"""
Test Script for Issue #29: Parentheses Conflict between Scripts 02 and 03v4
Analyzes how parenthetical content is processed by the pipeline
"""

import os
import sys
import json
import re
from typing import Dict, List

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Dynamic imports
import importlib.util

def import_module_from_path(module_name: str, file_path: str):
    """Import a module from a file path."""
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

# Import modules
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Import pattern library manager
pattern_manager = import_module_from_path("pattern_library_manager",
                                        os.path.join(parent_dir, "00b_pattern_library_manager_v1.py"))

# Import scripts
script01 = import_module_from_path("market_classifier", 
                                 os.path.join(parent_dir, "01_market_term_classifier_v1.py"))
script02 = import_module_from_path("date_extractor",
                                 os.path.join(parent_dir, "02_date_extractor_v1.py"))
script03 = import_module_from_path("report_extractor",
                                 os.path.join(parent_dir, "03_report_type_extractor_v4.py"))

def analyze_parentheses_processing(title: str):
    """Analyze how parentheses are handled through the pipeline."""
    print(f"\n{'='*80}")
    print(f"ANALYZING: {title}")
    print('='*80)
    
    # Find parenthetical content
    paren_matches = re.findall(r'\([^)]+\)', title)
    print(f"\nParenthetical content found: {paren_matches}")
    
    # Initialize components
    from dotenv import load_dotenv
    load_dotenv()
    
    pattern_lib_manager = pattern_manager.PatternLibraryManager(os.getenv('MONGODB_URI'))
    
    # Initialize pipeline components
    market_classifier = script01.MarketTermClassifier(pattern_lib_manager)
    date_extractor = script02.EnhancedDateExtractor(pattern_lib_manager)
    report_extractor = script03.PureDictionaryReportTypeExtractor(pattern_lib_manager)
    
    # Step 1: Market Classification
    print("\n--- STEP 1: Market Classification ---")
    market_result = market_classifier.classify(title)
    print(f"  Input: {title}")
    print(f"  Market Type: {market_result.market_type}")  # Fixed attribute name
    print(f"  Output: {market_result.title}")
    
    # Step 2: Date Extraction
    print("\n--- STEP 2: Date Extraction ---")
    date_result = date_extractor.extract(market_result.title)
    print(f"  Input: {market_result.title}")
    print(f"  Extracted Date: {date_result.extracted_date_range}")
    print(f"  Raw Match: {date_result.raw_match}")
    print(f"  Cleaned Title: {date_result.cleaned_title}")
    print(f"  Output (result.title): {date_result.title}")
    
    # Analyze what happened to parentheses
    print("\n  Parentheses Analysis:")
    print(f"    Original parentheses: {paren_matches}")
    print(f"    After date extraction: ", end="")
    remaining_parens = re.findall(r'[()]', date_result.title)
    print(f"{remaining_parens}")
    
    # Step 3: Report Type Extraction
    print("\n--- STEP 3: Report Type Extraction ---")
    report_result = report_extractor.extract(date_result.title, market_result.market_type)
    print(f"  Input: {date_result.title}")
    print(f"  Extracted Report Type: {report_result.extracted_report_type}")
    print(f"  Output (result.title): {report_result.title}")
    
    # Final analysis
    print("\n--- FINAL ANALYSIS ---")
    print(f"  Original Title: {title}")
    print(f"  Final Topic: '{report_result.title}'")
    
    # Check for parentheses artifacts
    artifacts = re.findall(r'[()]', report_result.title)
    if artifacts:
        print(f"\n  ⚠️  PARENTHESES ARTIFACTS DETECTED: {artifacts}")
        print(f"  This is the issue - trailing parenthesis remains!")
    else:
        print(f"\n  ✓ No parentheses artifacts")
    
    return {
        'original': title,
        'parenthetical_content': paren_matches,
        'after_date': date_result.title,
        'after_report': report_result.title,
        'artifacts': artifacts
    }

def main():
    """Test parentheses handling in pipeline."""
    
    # Test cases with compound parenthetical content
    test_cases = [
        "Battery Fuel Gauge Market (Forecast 2020-2030)",
        "Global Smart Grid Market (Analysis & Forecast 2024-2029)",
        "AI Market Report (2025-2035 Outlook)",
        "Electric Vehicle Market (Trends 2023-2028)",
        "Market Study (Industry Analysis 2024)",
        "Software Market (Global Forecast to 2030)",
        "Healthcare IT Market (Forecast and Analysis 2025-2030)"
    ]
    
    results = []
    for title in test_cases:
        result = analyze_parentheses_processing(title)
        results.append(result)
    
    # Summary
    print(f"\n{'='*80}")
    print("SUMMARY OF PARENTHESES ISSUES")
    print('='*80)
    
    issues_found = 0
    for r in results:
        if r['artifacts']:
            issues_found += 1
            print(f"\n❌ ISSUE: {r['original']}")
            print(f"   Final: '{r['after_report']}'")
            print(f"   Artifacts: {r['artifacts']}")
        else:
            print(f"\n✓ OK: {r['original']}")
    
    print(f"\n\nTotal issues found: {issues_found}/{len(test_cases)}")

if __name__ == "__main__":
    main()