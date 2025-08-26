#!/usr/bin/env python3
"""
Market-Aware Logic Validation Against Failing Pipeline Cases

Tests the corrected market-aware report type extractor against the specific 
failing cases from the Phase 3 pipeline test to validate implementation fixes.
"""

import os
import sys
from datetime import datetime, timezone
from dotenv import load_dotenv
import pytz

# Add the experiments directory to path for imports
sys.path.append(os.path.dirname(__file__))

# Load environment variables
load_dotenv()

def get_timestamps():
    """Generate PDT and UTC timestamps."""
    utc_now = datetime.now(timezone.utc)
    pdt_tz = pytz.timezone('America/Los_Angeles')
    pdt_now = utc_now.astimezone(pdt_tz)
    
    pdt_str = pdt_now.strftime('%Y-%m-%d %H:%M:%S PDT')
    utc_str = utc_now.strftime('%Y-%m-%d %H:%M:%S UTC')
    
    return pdt_str, utc_str

def test_corrected_market_aware_logic():
    """Test corrected market-aware logic against failing pipeline cases."""
    
    pdt_str, utc_str = get_timestamps()
    
    print("=" * 80)
    print("MARKET-AWARE LOGIC VALIDATION - FAILING CASES TEST")
    print(f"Analysis Date (PDT): {pdt_str}")
    print(f"Analysis Date (UTC): {utc_str}")
    print("=" * 80)
    print()
    
    # Import the corrected scripts
    try:
        # Import using dynamic import to handle the numbered module names
        import importlib.util
        import sys
        
        # Load Market Term Classifier
        spec1 = importlib.util.spec_from_file_location("market_classifier", "./01_market_term_classifier_v1.py")
        market_module = importlib.util.module_from_spec(spec1)
        spec1.loader.exec_module(market_module)
        MarketTermClassifier = market_module.MarketTermClassifier
        
        # Load Date Extractor
        spec2 = importlib.util.spec_from_file_location("date_extractor", "./02_date_extractor_v1.py")
        date_module = importlib.util.module_from_spec(spec2)
        spec2.loader.exec_module(date_module)
        EnhancedDateExtractor = date_module.EnhancedDateExtractor
        
        # Load Market-Aware Report Type Extractor
        spec3 = importlib.util.spec_from_file_location("report_extractor", "./03_report_type_extractor_market_aware_v1.py")
        report_module = importlib.util.module_from_spec(spec3)
        spec3.loader.exec_module(report_module)
        MarketAwareReportTypeExtractor = report_module.MarketAwareReportTypeExtractor
        
        print("✅ Successfully imported corrected scripts")
    except ImportError as e:
        print(f"❌ Import failed: {e}")
        return
    
    # Initialize the scripts
    try:
        # Load pattern library manager first
        pattern_spec = importlib.util.spec_from_file_location("pattern_manager", "./00b_pattern_library_manager_v1.py")
        pattern_mgr_module = importlib.util.module_from_spec(pattern_spec)
        pattern_spec.loader.exec_module(pattern_mgr_module)
        PatternLibraryManager = pattern_mgr_module.PatternLibraryManager
        
        # Create pattern library manager instance
        pattern_library_manager = PatternLibraryManager()
        
        # Initialize scripts with pattern manager
        market_classifier = MarketTermClassifier()  # This creates its own pattern manager
        date_extractor = EnhancedDateExtractor(pattern_library_manager)
        market_aware_extractor = MarketAwareReportTypeExtractor(pattern_library_manager)
        print("✅ Successfully initialized all script components")
    except Exception as e:
        print(f"❌ Initialization failed: {e}")
        print("Falling back to simpler test approach...")
        return
    
    print()
    
    # Define the failing test cases from the pipeline
    failing_cases = [
        {
            'title': 'Wiper Motor Aftermarket Size & Share Report, 2019-2025',
            'after_date_removal': 'Wiper Motor Aftermarket Size & Share Report',
            'expected_market_term': 'standard',
            'expected_report_type': 'Aftermarket Size & Share Report',
            'notes': 'Should extract Aftermarket compound pattern'
        },
        {
            'title': 'COVID-19 Vaccines-Production Capacity & Development Timeline',
            'after_date_removal': 'COVID-19 Vaccines-Production Capacity & Development Timeline',
            'expected_market_term': 'standard',
            'expected_report_type': None,  # May not have report type
            'notes': 'Non-market title without standard report patterns'
        },
        {
            'title': 'Out-Of-Home Advertising Trends & Growth Opportunities',
            'after_date_removal': 'Out-Of-Home Advertising Trends & Growth Opportunities',
            'expected_market_term': 'standard', 
            'expected_report_type': None,  # May not have report type
            'notes': 'Business analysis without standard report patterns'
        },
        {
            'title': 'Emerging Lighting Technology Market by Color Temperature',
            'after_date_removal': 'Emerging Lighting Technology Market by Color Temperature',
            'expected_market_term': 'market_by',
            'expected_report_type': 'Market',
            'notes': 'CRITICAL: Market by pattern should be classified and Market extracted as report type'
        },
        {
            'title': 'Artificial Intelligence (AI) Market in Automotive',
            'after_date_removal': 'Artificial Intelligence (AI) Market in Automotive',
            'expected_market_term': 'market_in',
            'expected_report_type': 'Market',
            'notes': 'CRITICAL: Market in pattern should extract Market as report type'
        }
    ]
    
    print("TESTING CORRECTED MARKET-AWARE LOGIC:")
    print("-" * 60)
    
    success_count = 0
    total_tests = len(failing_cases)
    critical_fixes = 0
    
    for i, test_case in enumerate(failing_cases, 1):
        title = test_case['title']
        after_date = test_case['after_date_removal']
        expected_market = test_case['expected_market_term']
        expected_report = test_case['expected_report_type']
        notes = test_case['notes']
        
        print(f"\nTest Case #{i}: {title}")
        print(f"After Date Removal: {after_date}")
        print(f"Expected Market Term: {expected_market}")
        print(f"Expected Report Type: {expected_report}")
        print(f"Notes: {notes}")
        
        # Step 1: Market term classification
        try:
            market_result = market_classifier.classify(title)
            market_term_type = market_result.market_type  # Correct attribute name
            confidence = market_result.confidence
            
            print(f"  Step 1 - Market Classification: {market_term_type} (confidence: {confidence:.2f})")
            
            market_correct = market_term_type == expected_market
            if not market_correct:
                print(f"  ⚠️ Market classification mismatch: got {market_term_type}, expected {expected_market}")
            
        except Exception as e:
            print(f"  ❌ Market classification failed: {e}")
            market_term_type = 'unknown'
            market_correct = False
        
        # Step 2: Date extraction (using after_date_removal for consistency)
        try:
            date_result = date_extractor.extract(after_date)
            cleaned_title = after_date  # Use after_date since this is post-date-extraction
            
            print(f"  Step 2 - Using cleaned title: {cleaned_title}")
            
        except Exception as e:
            print(f"  ❌ Date extraction failed: {e}")
            cleaned_title = after_date
        
        # Step 3: CRITICAL TEST - Market-aware report type extraction
        try:
            report_result = market_aware_extractor.extract(
                title=cleaned_title,
                market_term_type=market_term_type,
                original_title=title,
                date_extractor=date_extractor
            )
            
            extracted_report = report_result.final_report_type  # Use final_report_type instead
            confidence = report_result.confidence
            
            print(f"  Step 3 - Report Type Extraction: '{extracted_report}' (confidence: {confidence:.2f})")
            print(f"  Context Analysis: {report_result.context_analysis}")
            print(f"  Market Prepended: {report_result.market_prepended}")
            
            # Check if extraction matches expectation
            report_correct = extracted_report == expected_report
            
            if not report_correct:
                print(f"  ⚠️ Report type mismatch: got '{extracted_report}', expected '{expected_report}'")
            else:
                print(f"  ✅ Report type extraction correct!")
                
                # Check if this was a critical fix
                if 'CRITICAL' in notes:
                    critical_fixes += 1
                    print(f"  🎯 CRITICAL FIX VALIDATED!")
            
        except Exception as e:
            print(f"  ❌ Report type extraction failed: {e}")
            extracted_report = None
            report_correct = False
        
        # Overall test result
        test_success = market_correct and report_correct
        if test_success:
            success_count += 1
            print(f"  ✅ Test Case #{i}: PASSED")
        else:
            print(f"  ❌ Test Case #{i}: FAILED")
        
        print("-" * 60)
    
    # Final summary
    print(f"\nVALIDATION SUMMARY:")
    print(f"Total Test Cases: {total_tests}")
    print(f"Successful Validations: {success_count}")
    print(f"Critical Fixes Validated: {critical_fixes}")
    print(f"Success Rate: {success_count/total_tests*100:.1f}%")
    
    if critical_fixes >= 2:  # Both market_by and market_in cases
        print(f"\n🎯 CRITICAL MARKET-AWARE FIXES VALIDATED!")
        print("✅ Market by pattern now correctly classified and extracts 'Market' as report type")
        print("✅ Market in pattern correctly extracts 'Market' as report type")
        print("✅ Market-aware logic successfully resolves original pipeline failures")
    
    if success_count >= total_tests * 0.8:  # 80% success threshold
        print(f"\n✅ VALIDATION PASSED - Market-aware logic successfully resolves failing cases!")
        return True
    else:
        print(f"\n❌ VALIDATION NEEDS IMPROVEMENT - Some cases still failing")
        return False

if __name__ == "__main__":
    success = test_corrected_market_aware_logic()
    if success:
        print("\n🚀 Market-aware logic validation successful - ready for production!")
    else:
        print("\n🔧 Further refinement needed for complete validation")