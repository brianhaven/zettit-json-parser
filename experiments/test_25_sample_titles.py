#!/usr/bin/env python3
"""
Test 25 Sample Titles - Comprehensive Market-Aware Processing
============================================================

Test Script 03 v3 with 25 sample titles to validate market-aware workflow fixes.
Display report type and pipeline forward text for each title.
"""

import os
import sys
from dotenv import load_dotenv
import importlib.util
from datetime import datetime
import pytz

load_dotenv()
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def import_module_from_path(module_name: str, file_path: str):
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

def test_25_sample_titles():
    """Test comprehensive market-aware processing with 25 sample titles."""
    
    # Import required modules
    current_dir = os.path.dirname(os.path.abspath(__file__))
    pattern_manager = import_module_from_path("pattern_library_manager", 
                                            os.path.join(current_dir, "00b_pattern_library_manager_v1.py"))
    script01 = import_module_from_path("market_classifier", 
                                     os.path.join(current_dir, "01_market_term_classifier_v1.py"))
    script03v3 = import_module_from_path("report_extractor_v3",
                                       os.path.join(current_dir, "03_report_type_extractor_v3.py"))
    
    # Initialize components  
    pattern_lib_manager = pattern_manager.PatternLibraryManager(os.getenv('MONGODB_URI'))
    market_classifier = script01.MarketTermClassifier(pattern_lib_manager)
    report_extractor = script03v3.DictionaryBasedReportTypeExtractor(pattern_lib_manager)
    
    # Test titles as provided by user
    test_titles = [
        "Carbon Black Market For Textile Fibers Growth Report",
        "Sulfur, Arsine, and Mercury Remover Market in Oil & Gas Industry",
        "Private LTE & 5G Network Market Outlook, 2024-2030",
        "APAC Personal Protective Equipment Market Analysis",
        "North American Smart Grid Technology Market Study", 
        "European Automotive Battery Market Forecast, 2025-2030",
        "Global Renewable Energy Market Size Report",
        "Asia-Pacific Cloud Computing Market Trends",
        "Latin America Food Processing Equipment Market Research",
        "Middle East Construction Materials Market Overview",
        "U.S. Artificial Intelligence Market Growth Analysis",
        "China Manufacturing Automation Market Intelligence",
        "India Software Development Market Statistics",
        "Japan Robotics Technology Market Insights",
        "Germany Industrial IoT Market Assessment",
        "UK Financial Technology Market Evaluation",
        "France Healthcare IT Market Performance",
        "Brazil Agricultural Technology Market Dynamics",
        "Russia Energy Storage Market Landscape",
        "South Korea Semiconductor Market Projections", 
        "Australia Mining Equipment Market Survey",
        "Canada Telecommunications Market Review",
        "Mexico Automotive Parts Market Snapshot",
        "Indonesia Palm Oil Market Update",
        "Thailand Tourism Technology Market Brief"
    ]
    
    print("=" * 80)
    print("COMPREHENSIVE TEST: 25 Sample Titles - Script 03 v3 Market-Aware Processing")
    print("=" * 80)
    
    # Get current timestamp
    pdt = pytz.timezone('America/Los_Angeles')
    timestamp = datetime.now(pdt).strftime('%Y-%m-%d %H:%M:%S PDT')
    utc_timestamp = datetime.now(pytz.UTC).strftime('%Y-%m-%d %H:%M:%S UTC')
    
    print(f"Analysis Date (PDT): {timestamp}")
    print(f"Analysis Date (UTC): {utc_timestamp}")
    print()
    
    success_count = 0
    market_aware_count = 0
    standard_count = 0
    results = []
    
    for i, title in enumerate(test_titles, 1):
        print(f"=== Test {i:2d}: {title[:50]}{'...' if len(title) > 50 else ''} ===")
        
        try:
            # Step 1: Market classification
            market_result = market_classifier.classify(title)
            market_type = market_result.market_type
            
            # Step 2: Report type extraction (simulating date removal for testing)
            report_result = report_extractor.extract(title, market_type)
            
            # Track statistics
            if market_type != "standard":
                market_aware_count += 1
            else:
                standard_count += 1
                
            if report_result.success:
                success_count += 1
            
            # Display results
            print(f"  Title: {title}")
            print(f"  Market Type: {market_type}")
            print(f"  Report Type: '{report_result.extracted_report_type}'")
            print(f"  Pipeline Forward: '{report_result.title}'")
            print(f"  Success: {report_result.success}")
            print(f"  Confidence: {report_result.confidence:.3f}")
            
            # Store result for analysis
            results.append({
                'title': title,
                'market_type': market_type,
                'report_type': report_result.extracted_report_type,
                'pipeline_forward': report_result.title,
                'success': report_result.success,
                'confidence': report_result.confidence
            })
            
        except Exception as e:
            print(f"  ERROR: {e}")
            results.append({
                'title': title,
                'market_type': 'ERROR',
                'report_type': '',
                'pipeline_forward': title,
                'success': False,
                'confidence': 0.0
            })
        
        print()
    
    # Summary analysis
    print("=" * 80)
    print("ANALYSIS SUMMARY")
    print("=" * 80)
    print(f"Total Titles Processed: {len(test_titles)}")
    print(f"Successful Extractions: {success_count}/{len(test_titles)} ({success_count/len(test_titles)*100:.1f}%)")
    print(f"Market-Aware Processing: {market_aware_count} titles ({market_aware_count/len(test_titles)*100:.1f}%)")  
    print(f"Standard Processing: {standard_count} titles ({standard_count/len(test_titles)*100:.1f}%)")
    print()
    
    # Market type breakdown
    market_types = {}
    for result in results:
        market_type = result['market_type']
        if market_type not in market_types:
            market_types[market_type] = 0
        market_types[market_type] += 1
    
    print("Market Type Distribution:")
    for market_type, count in market_types.items():
        print(f"  {market_type}: {count} titles ({count/len(test_titles)*100:.1f}%)")
    print()
    
    # Report type analysis
    report_types = {}
    for result in results:
        if result['success'] and result['report_type']:
            report_type = result['report_type']
            if report_type not in report_types:
                report_types[report_type] = 0
            report_types[report_type] += 1
    
    print("Successfully Extracted Report Types:")
    for report_type, count in sorted(report_types.items()):
        print(f"  '{report_type}': {count} occurrences")
    print()
    
    # Confidence analysis
    confidences = [r['confidence'] for r in results if r['success']]
    if confidences:
        avg_confidence = sum(confidences) / len(confidences)
        print(f"Average Confidence: {avg_confidence:.3f}")
        print(f"Confidence Range: {min(confidences):.3f} - {max(confidences):.3f}")
    
    # Failed extractions
    failures = [r for r in results if not r['success']]
    if failures:
        print(f"\nFailed Extractions ({len(failures)} titles):")
        for failure in failures:
            print(f"  - {failure['title']} (Market Type: {failure['market_type']})")
    
    print("\n" + "=" * 80)
    print("✅ COMPREHENSIVE TEST COMPLETED")
    print("=" * 80)

if __name__ == "__main__":
    test_25_sample_titles()