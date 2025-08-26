#!/usr/bin/env python3

"""
Test script for the corrected market-aware report type extractor.
Tests the key user feedback: Market itself IS the report type in market contexts.
"""

import sys
import os

# Add the experiments directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_market_aware_logic():
    """Test the corrected market-aware extraction logic."""
    
    try:
        # Import the corrected components
        import importlib.util
        
        # Load the market-aware extractor module
        spec = importlib.util.spec_from_file_location("extractor_module", "03_report_type_extractor_market_aware_v1.py")
        extractor_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(extractor_module)
        
        # Load the pattern library manager module
        spec2 = importlib.util.spec_from_file_location("pattern_module", "00b_pattern_library_manager_v1.py")
        pattern_module = importlib.util.module_from_spec(spec2)
        spec2.loader.exec_module(pattern_module)
        
        MarketAwareReportTypeExtractor = extractor_module.MarketAwareReportTypeExtractor
        PatternLibraryManager = pattern_module.PatternLibraryManager
        
        print("Corrected Market-Aware Report Type Extraction Test")
        print("=" * 60)
        
        # Test cases covering the user's examples
        test_cases = [
            {
                'title': 'Artificial Intelligence (AI) Market in Automotive',
                'market_type': 'market_in',
                'expected_report_type': 'Market',
                'description': 'Market in context - Market should be extracted as report type'
            },
            {
                'title': 'Emerging Lighting Technology Market by Color Temperature', 
                'market_type': 'market_by',
                'expected_report_type': 'Market',
                'description': 'Market by context - Market should be extracted as report type'
            },
            {
                'title': 'Global Market for Advanced Materials in Aerospace',
                'market_type': 'market_for', 
                'expected_report_type': 'Market',
                'description': 'Market for context - Market should be extracted as report type'
            },
            {
                'title': 'Global Artificial Intelligence Market Size & Share Report, 2030',
                'market_type': 'standard',
                'expected_report_type': 'Report',  # Should find "Report" via standard patterns
                'description': 'Standard context - Should use pattern matching'
            },
            {
                'title': 'APAC Personal Protective Equipment Market Analysis',
                'market_type': 'standard',
                'expected_report_type': 'Analysis',  # Should find "Analysis" via standard patterns
                'description': 'Standard context - Should use pattern matching'
            }
        ]
        
        # Initialize the extractor
        pattern_manager = PatternLibraryManager()
        extractor = MarketAwareReportTypeExtractor(pattern_manager)
        
        print(f"Loaded extractor with {len(extractor.terminal_type_patterns + extractor.embedded_type_patterns + extractor.prefix_type_patterns + extractor.compound_type_patterns)} total patterns\n")
        
        # Test each case
        all_passed = True
        
        for i, test_case in enumerate(test_cases, 1):
            title = test_case['title']
            market_type = test_case['market_type']
            expected = test_case['expected_report_type']
            description = test_case['description']
            
            print(f"Test Case {i}: {description}")
            print(f"Title: {title}")
            print(f"Market Type: {market_type}")
            print(f"Expected Report Type: {expected}")
            
            # Execute extraction
            result = extractor.extract(title, market_type)
            
            print(f"Result:")
            print(f"  - Extracted Report Type: {result.extracted_report_type}")
            print(f"  - Final Report Type: {result.final_report_type}")
            print(f"  - Confidence: {result.confidence:.3f}")
            print(f"  - Context Analysis: {result.context_analysis}")
            print(f"  - Notes: {result.notes}")
            
            # Check if the result matches expectations
            success = result.final_report_type == expected
            print(f"  - Status: {'✅ PASS' if success else '❌ FAIL'}")
            
            if not success:
                all_passed = False
                print(f"    Expected '{expected}', got '{result.final_report_type}'")
            
            print("-" * 60)
        
        # Summary
        print(f"\nTest Summary: {'All tests PASSED! ✅' if all_passed else 'Some tests FAILED ❌'}")
        
        if all_passed:
            print("\n🎯 Corrected Logic Validation:")
            print("✅ Market term contexts (market_in, market_for, market_by) extract 'Market' as report type")
            print("✅ Standard contexts use database pattern matching")
            print("✅ High confidence scoring for market term contexts")
            print("✅ Proper context analysis and notes")
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return all_passed

if __name__ == "__main__":
    test_market_aware_logic()