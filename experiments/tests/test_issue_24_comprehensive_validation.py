#!/usr/bin/env python3
"""
Comprehensive validation for Issue #24 fix
Tests that the date removal fix doesn't cause regressions
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

def comprehensive_validation():
    """Comprehensive validation of Issue #24 fix."""
    
    # Create output directory
    output_dir = create_output_directory("test_issue_24_comprehensive")
    output_file = os.path.join(output_dir, "comprehensive_results.txt")
    
    # Initialize components
    pattern_lib_manager = pattern_manager.PatternLibraryManager(os.getenv('MONGODB_URI'))
    date_extractor = script02.EnhancedDateExtractor(pattern_lib_manager)
    
    # Test categories
    test_categories = {
        "Multi-Comma Complex Titles": [
            "Global Market for AI, Machine Learning, and Deep Learning Technologies, 2025-2030",
            "North America, Europe IoT Market, Healthcare, Automotive Applications, 2024-2028",
            "European Market for Renewable Energy, Wind, Solar, and Hydroelectric Power Markets, 2025",
        ],
        "Simple Date Formats": [
            "Market Report, 2030",
            "Market Analysis, 2023-2030",
            "Market Study [2024]",
            "Market Outlook 2031",
        ],
        "No Date Titles": [
            "Global Artificial Intelligence Market Analysis",
            "North America IoT Market Report",
            "European Renewable Energy Market Study",
        ],
        "Complex Separators": [
            "Market in Asia-Pacific: Semiconductors, Electronics & Components, Q1 2025",
            "Global Market - Technology & Innovation Trends (2024-2029)",
            "Market Analysis | Healthcare Sector | 2025",
        ],
        "Edge Cases": [
            "Market for 5G Technology, Global Analysis, 2024 to 2030",
            "2025 Market Forecast: AI and Machine Learning",
            "Market Size, Share & Trends Analysis Report, 2024-2032",
        ]
    }
    
    # Process all test cases
    all_results = []
    category_stats = {}
    
    for category, titles in test_categories.items():
        category_results = []
        success_count = 0
        
        for title in titles:
            result = date_extractor.extract(title)
            
            # Validate results
            validation = {
                'title_cleaned': result.extracted_date_range is None or result.extracted_date_range not in result.title,
                'cleaned_matches_title': result.title == result.cleaned_title,
                'date_extracted_if_present': True  # Will check below
            }
            
            # Check if date should have been extracted
            has_year = any(str(year) in title for year in range(2020, 2041))
            if has_year and not result.extracted_date_range:
                validation['date_extracted_if_present'] = False
            
            all_valid = all(validation.values())
            if all_valid:
                success_count += 1
            
            category_results.append({
                'original': title,
                'extracted_date': result.extracted_date_range,
                'returned_title': result.title,
                'cleaned_title': result.cleaned_title,
                'categorization': result.categorization,
                'validation': validation,
                'success': all_valid
            })
        
        category_stats[category] = {
            'total': len(titles),
            'success': success_count,
            'rate': f"{(success_count/len(titles)*100):.1f}%"
        }
        all_results.append((category, category_results))
    
    # Write comprehensive report
    with open(output_file, 'w') as f:
        f.write(create_output_file_header("test_issue_24_comprehensive", "Comprehensive Validation Report"))
        f.write("\n")
        f.write("=" * 80)
        f.write("\nIssue #24 Fix - Comprehensive Validation Report\n")
        f.write("=" * 80)
        f.write("\n\n")
        
        # Overall summary
        total_tests = sum(stats['total'] for stats in category_stats.values())
        total_success = sum(stats['success'] for stats in category_stats.values())
        overall_rate = (total_success / total_tests * 100) if total_tests > 0 else 0
        
        f.write("OVERALL SUMMARY\n")
        f.write("-" * 40)
        f.write(f"\nTotal Test Cases: {total_tests}\n")
        f.write(f"Successful: {total_success}\n")
        f.write(f"Success Rate: {overall_rate:.1f}%\n\n")
        
        if overall_rate >= 95:
            f.write("✅ SUCCESS: Fix is working correctly with high success rate!\n")
        elif overall_rate >= 90:
            f.write("⚠️  WARNING: Fix is mostly working but some edge cases remain.\n")
        else:
            f.write("❌ FAILURE: Fix has issues that need attention.\n")
        
        # Category summaries
        f.write("\n" + "=" * 80)
        f.write("\nCATEGORY SUMMARIES\n")
        f.write("=" * 80)
        f.write("\n\n")
        
        for category, stats in category_stats.items():
            f.write(f"{category}:\n")
            f.write(f"  Tests: {stats['total']}, Success: {stats['success']}, Rate: {stats['rate']}\n")
        
        # Detailed results by category
        f.write("\n" + "=" * 80)
        f.write("\nDETAILED RESULTS BY CATEGORY\n")
        f.write("=" * 80)
        f.write("\n")
        
        for category, results in all_results:
            f.write(f"\n{'-'*80}\n")
            f.write(f"{category}\n")
            f.write(f"{'-'*80}\n\n")
            
            for i, result in enumerate(results, 1):
                status = "✅" if result['success'] else "❌"
                f.write(f"{status} Test {i}:\n")
                f.write(f"  Original: {result['original']}\n")
                f.write(f"  Date:     {result['extracted_date'] or 'None'}\n")
                f.write(f"  Returned: {result['returned_title']}\n")
                f.write(f"  Category: {result['categorization']}\n")
                
                if not result['success']:
                    f.write("  Issues:\n")
                    for check, passed in result['validation'].items():
                        if not passed:
                            f.write(f"    - {check}: FAILED\n")
                f.write("\n")
        
        # Key findings
        f.write("=" * 80)
        f.write("\nKEY FINDINGS\n")
        f.write("=" * 80)
        f.write("\n\n")
        
        f.write("1. Date Removal: ")
        date_removal_works = all(
            r['validation']['title_cleaned'] 
            for _, results in all_results 
            for r in results
        )
        if date_removal_works:
            f.write("✅ All dates are properly removed from titles\n")
        else:
            f.write("❌ Some dates are not being removed\n")
        
        f.write("2. Title Consistency: ")
        title_consistency = all(
            r['validation']['cleaned_matches_title'] 
            for _, results in all_results 
            for r in results
        )
        if title_consistency:
            f.write("✅ Returned title always matches cleaned_title\n")
        else:
            f.write("❌ Inconsistency between title and cleaned_title\n")
        
        f.write("3. Date Detection: ")
        date_detection_rate = sum(
            1 for _, results in all_results 
            for r in results 
            if r['validation']['date_extracted_if_present']
        ) / total_tests * 100
        f.write(f"{'✅' if date_detection_rate >= 95 else '⚠️'} {date_detection_rate:.1f}% accuracy\n")
        
        f.write("\n" + "=" * 80)
        f.write("\nCONCLUSION\n")
        f.write("=" * 80)
        f.write("\n\n")
        
        if overall_rate >= 95 and date_removal_works and title_consistency:
            f.write("✅ Issue #24 is RESOLVED. The fix is working correctly!\n")
            f.write("The single-line change successfully addresses the date removal bug.\n")
            f.write("All downstream processing should now work correctly with cleaned titles.\n")
        else:
            f.write("⚠️  Additional work may be needed to fully resolve Issue #24.\n")
            f.write("Review the detailed results above for specific failure cases.\n")
    
    # Print summary to console
    print(f"\n{'='*60}")
    print("Issue #24 Comprehensive Validation Complete")
    print(f"{'='*60}")
    print(f"Results written to: {output_file}")
    print(f"Overall Success Rate: {overall_rate:.1f}%")
    print(f"Date Removal Working: {'YES ✅' if date_removal_works else 'NO ❌'}")
    print(f"Title Consistency: {'YES ✅' if title_consistency else 'NO ❌'}")
    print(f"{'='*60}\n")
    
    return overall_rate >= 95

if __name__ == "__main__":
    success = comprehensive_validation()
    sys.exit(0 if success else 1)