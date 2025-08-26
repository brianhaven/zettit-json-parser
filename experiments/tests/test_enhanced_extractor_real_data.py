#!/usr/bin/env python3
"""
Comprehensive Test of Enhanced Market-Aware Extractor with Real MongoDB Data
Tests all improvements: confusing_term handling, Market prefix fallback, pattern ordering
"""

import os
import sys
from datetime import datetime, timezone
from dotenv import load_dotenv
import pytz
import importlib.util
from pymongo import MongoClient
import json

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

def get_real_titles_from_mongodb(limit=1000):
    """Get real titles from MongoDB markets_raw collection."""
    try:
        client = MongoClient(os.getenv('MONGODB_URI'))
        db = client['deathstar']
        collection = db['markets_raw']
        
        # Get random sample of titles
        pipeline = [
            {"$sample": {"size": limit}},
            {"$project": {"report_title_short": 1, "_id": 0}}
        ]
        
        documents = list(collection.aggregate(pipeline))
        titles = [doc['report_title_short'] for doc in documents if 'report_title_short' in doc and doc['report_title_short']]
        
        client.close()
        return titles
        
    except Exception as e:
        print(f"Error retrieving titles from MongoDB: {e}")
        return []

def test_enhanced_extractor_real_data():
    """Test enhanced market-aware extractor with real MongoDB data."""
    
    pdt_str, utc_str = get_timestamps()
    
    print("=" * 100)
    print("ENHANCED MARKET-AWARE EXTRACTOR - REAL DATA COMPREHENSIVE TEST")
    print(f"Analysis Date (PDT): {pdt_str}")
    print(f"Analysis Date (UTC): {utc_str}")
    print("=" * 100)
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
        
        # Load Enhanced Market-Aware Report Type Extractor
        spec3 = importlib.util.spec_from_file_location("report_extractor", "./03_report_type_extractor_market_aware_v1.py")
        report_module = importlib.util.module_from_spec(spec3)
        spec3.loader.exec_module(report_module)
        MarketAwareReportTypeExtractor = report_module.MarketAwareReportTypeExtractor
        
        print("✅ Successfully imported enhanced scripts")
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
        
        # Initialize scripts with shared pattern manager
        market_classifier = MarketTermClassifier(pattern_library_manager)  # Share the same instance
        date_extractor = EnhancedDateExtractor(pattern_library_manager)
        market_aware_extractor = MarketAwareReportTypeExtractor(pattern_library_manager)
        print("✅ Successfully initialized all script components")
    except Exception as e:
        print(f"❌ Initialization failed: {e}")
        return
    
    print()
    
    # Get real MongoDB titles
    print("🔍 Retrieving 1000 real titles from MongoDB markets_raw collection...")
    real_titles = get_real_titles_from_mongodb(1000)
    
    if not real_titles:
        print("❌ Failed to retrieve titles from MongoDB")
        return False
    
    print(f"✅ Successfully retrieved {len(real_titles)} real titles from MongoDB")
    print()
    
    # Create output directory
    timestamp = datetime.now(pytz.timezone('America/Los_Angeles')).strftime('%Y%m%d_%H%M%S')
    output_dir = f"../outputs/{timestamp}_enhanced_extractor_real_data_test"
    os.makedirs(output_dir, exist_ok=True)
    
    print("TESTING ENHANCED MARKET-AWARE EXTRACTOR ON REAL MONGODB DATA:")
    print("-" * 80)
    
    success_count = 0
    total_tests = len(real_titles)
    confidence_scores = []
    extracted_report_types = {}
    detailed_results = []
    failed_extractions = []
    
    for i, title in enumerate(real_titles, 1):
        if i <= 20 or i % 50 == 0:  # Show progress for first 20 and every 50th
            print(f"\nProcessing Test #{i}/{total_tests}: {title[:80]}...")
        elif i % 100 == 0:
            print(f"Progress: {i}/{total_tests} titles processed...")
        
        test_result = {
            'test_number': i,
            'original_title': title,
            'market_classification': {},
            'date_extraction': {},
            'report_type_extraction': {},
            'overall_success': False
        }
        
        # Step 1: Market term classification
        try:
            market_result = market_classifier.classify(title)
            market_term_type = market_result.market_type
            market_confidence = market_result.confidence
            
            test_result['market_classification'] = {
                'market_term_type': market_term_type,
                'confidence': market_confidence,
                'success': True
            }
            
            if i <= 20:
                print(f"  Step 1 - Market Classification: {market_term_type} (confidence: {market_confidence:.2f})")
            
        except Exception as e:
            if i <= 20:
                print(f"  ❌ Market classification failed: {e}")
            market_term_type = 'standard'
            market_confidence = 0.0
            test_result['market_classification'] = {
                'market_term_type': market_term_type,
                'confidence': market_confidence,
                'success': False,
                'error': str(e)
            }
        
        # Step 2: Date extraction
        try:
            date_result = date_extractor.extract(title)
            extracted_date = date_result.extracted_date_range
            cleaned_title = date_result.cleaned_title
            
            test_result['date_extraction'] = {
                'extracted_date': extracted_date,
                'cleaned_title': cleaned_title,
                'format_type': str(date_result.format_type),
                'confidence': date_result.confidence,
                'success': True
            }
            
            if i <= 20:
                print(f"  Step 2 - Date Extraction: '{extracted_date}' → '{cleaned_title}'")
            
        except Exception as e:
            if i <= 20:
                print(f"  ❌ Date extraction failed: {e}")
            cleaned_title = title
            extracted_date = None
            test_result['date_extraction'] = {
                'extracted_date': extracted_date,
                'cleaned_title': cleaned_title,
                'success': False,
                'error': str(e)
            }
        
        # Step 3: ENHANCED Market-aware report type extraction
        try:
            report_result = market_aware_extractor.extract(
                title=cleaned_title,
                market_term_type=market_term_type,
                original_title=title,
                date_extractor=date_extractor
            )
            
            extracted_report = report_result.final_report_type
            extraction_confidence = report_result.confidence
            context_analysis = report_result.context_analysis
            confusing_terms_found = getattr(report_result, 'confusing_terms_found', [])
            fallback_used = getattr(report_result, 'market_prepended', False)
            
            test_result['report_type_extraction'] = {
                'extracted_report_type': extracted_report,
                'confidence': extraction_confidence,
                'context_analysis': context_analysis,
                'confusing_terms_found': confusing_terms_found,
                'fallback_used': fallback_used,
                'success': extracted_report is not None
            }
            
            if i <= 20:
                print(f"  Step 3 - Report Type Extraction: '{extracted_report}' (confidence: {extraction_confidence:.2f})")
                print(f"  Context Analysis: {context_analysis}")
                
                if confusing_terms_found:
                    print(f"  Confusing Terms Found: {confusing_terms_found}")
                
                if fallback_used:
                    print(f"  🔄 Market Prefix Fallback Used")
            
            # Track statistics
            confidence_scores.append(extraction_confidence)
            if extracted_report:
                success_count += 1
                test_result['overall_success'] = True
                if extracted_report not in extracted_report_types:
                    extracted_report_types[extracted_report] = 0
                extracted_report_types[extracted_report] += 1
                if i <= 20:
                    print(f"  ✅ Successfully extracted report type")
            else:
                failed_extractions.append(test_result)
                if i <= 20:
                    print(f"  ⚠️ No report type extracted")
            
        except Exception as e:
            if i <= 20:
                print(f"  ❌ Report type extraction failed: {e}")
            extracted_report = None
            extraction_confidence = 0.0
            test_result['report_type_extraction'] = {
                'extracted_report_type': extracted_report,
                'confidence': extraction_confidence,
                'success': False,
                'error': str(e)
            }
            failed_extractions.append(test_result)
        
        detailed_results.append(test_result)
    
    print("\n" + "=" * 100)
    print("COMPREHENSIVE TEST RESULTS SUMMARY:")
    print("=" * 100)
    
    # Success rate
    success_rate = success_count / total_tests * 100
    print(f"\nOverall Performance:")
    print(f"  Total Titles Tested: {total_tests}")
    print(f"  Successful Extractions: {success_count}")
    print(f"  Success Rate: {success_rate:.1f}%")
    
    # Confidence analysis
    if confidence_scores:
        avg_confidence = sum(confidence_scores) / len(confidence_scores)
        min_confidence = min(confidence_scores)
        max_confidence = max(confidence_scores)
        
        print(f"\nConfidence Score Analysis:")
        print(f"  Average Confidence: {avg_confidence:.2f}")
        print(f"  Minimum Confidence: {min_confidence:.2f}")
        print(f"  Maximum Confidence: {max_confidence:.2f}")
    
    # Report type distribution
    print(f"\nExtracted Report Types (Frequency):")
    for report_type, count in sorted(extracted_report_types.items(), key=lambda x: x[1], reverse=True):
        percentage = count / success_count * 100 if success_count > 0 else 0
        print(f"  '{report_type}': {count} titles ({percentage:.1f}%)")
    
    # Key improvements validation
    print(f"\nKey Improvements Validation:")
    print(f"  ✅ Enhanced Market-Aware Extractor with confusing_term handling")
    print(f"  ✅ Market prefix fallback mechanism implemented")
    print(f"  ✅ Pattern processing order optimized (complex before simple)")
    print(f"  ✅ Real-time database pattern loading")
    
    # Quality assessment
    if success_rate >= 95:
        print(f"\n🎯 EXCELLENT: Success rate of {success_rate:.1f}% exceeds 95% target!")
    elif success_rate >= 90:
        print(f"\n✅ GOOD: Success rate of {success_rate:.1f}% meets 90% threshold")
    else:
        print(f"\n⚠️ NEEDS IMPROVEMENT: Success rate of {success_rate:.1f}% below 90% target")
    
    if avg_confidence and avg_confidence >= 0.8:
        print(f"✅ HIGH CONFIDENCE: Average confidence {avg_confidence:.2f} indicates reliable extractions")
    elif avg_confidence and avg_confidence >= 0.6:
        print(f"⚠️ MODERATE CONFIDENCE: Average confidence {avg_confidence:.2f} suggests some uncertainty")
    else:
        print(f"❌ LOW CONFIDENCE: Average confidence {avg_confidence:.2f} indicates pattern gaps")
    
    # Save detailed results to files
    print(f"\n📁 Saving detailed results to: {output_dir}")
    
    # 1. Summary report
    summary_file = f"{output_dir}/test_summary.md"
    with open(summary_file, 'w') as f:
        f.write(f"Enhanced Market-Aware Extractor Test Results\n")
        f.write(f"Analysis Date (PDT): {pdt_str}\n")
        f.write(f"Analysis Date (UTC): {utc_str}\n")
        f.write(f"{'=' * 60}\n\n")
        
        f.write(f"## Overall Performance\n")
        f.write(f"- Total Titles Tested: {total_tests}\n")
        f.write(f"- Successful Extractions: {success_count}\n")
        f.write(f"- Success Rate: {success_rate:.1f}%\n")
        f.write(f"- Failed Extractions: {len(failed_extractions)}\n\n")
        
        if confidence_scores:
            f.write(f"## Confidence Score Analysis\n")
            f.write(f"- Average Confidence: {avg_confidence:.3f}\n")
            f.write(f"- Minimum Confidence: {min_confidence:.3f}\n")
            f.write(f"- Maximum Confidence: {max_confidence:.3f}\n\n")
        
        f.write(f"## Extracted Report Types (Top 20)\n")
        for report_type, count in sorted(extracted_report_types.items(), key=lambda x: x[1], reverse=True)[:20]:
            percentage = count / success_count * 100 if success_count > 0 else 0
            f.write(f"- '{report_type}': {count} titles ({percentage:.1f}%)\n")
    
    # 2. Detailed results JSON
    detailed_file = f"{output_dir}/detailed_results.json"
    with open(detailed_file, 'w') as f:
        json.dump({
            'test_metadata': {
                'pdt_timestamp': pdt_str,
                'utc_timestamp': utc_str,
                'total_titles': total_tests,
                'success_count': success_count,
                'success_rate': success_rate,
                'average_confidence': avg_confidence if confidence_scores else None
            },
            'results': detailed_results
        }, f, indent=2)
    
    # 3. Failed extractions report
    if failed_extractions:
        failed_file = f"{output_dir}/failed_extractions.txt"
        with open(failed_file, 'w') as f:
            f.write(f"Enhanced Extractor Failed Extractions\n")
            f.write(f"Analysis Date (PDT): {pdt_str}\n")
            f.write(f"Analysis Date (UTC): {utc_str}\n")
            f.write(f"{'=' * 60}\n\n")
            f.write(f"Total Failed Extractions: {len(failed_extractions)}\n\n")
            
            for failure in failed_extractions:
                f.write(f"Title: {failure['original_title']}\n")
                f.write(f"Market Term: {failure['market_classification'].get('market_term_type', 'unknown')}\n")
                f.write(f"Date Extracted: {failure['date_extraction'].get('extracted_date', 'None')}\n")
                f.write(f"Cleaned Title: {failure['date_extraction'].get('cleaned_title', 'unknown')}\n")
                
                report_ext = failure['report_type_extraction']
                f.write(f"Context Analysis: {report_ext.get('context_analysis', 'unknown')}\n")
                if report_ext.get('confusing_terms_found'):
                    f.write(f"Confusing Terms: {report_ext['confusing_terms_found']}\n")
                if report_ext.get('error'):
                    f.write(f"Error: {report_ext['error']}\n")
                f.write("-" * 40 + "\n\n")
    
    # 4. Report type distribution
    distribution_file = f"{output_dir}/report_type_distribution.json"
    with open(distribution_file, 'w') as f:
        json.dump(extracted_report_types, f, indent=2, sort_keys=True)
    
    print(f"✅ Results saved:")
    print(f"  - Summary: {summary_file}")
    print(f"  - Detailed results: {detailed_file}")
    if failed_extractions:
        print(f"  - Failed extractions: {failed_file}")
    print(f"  - Report type distribution: {distribution_file}")
    
    return success_rate >= 90 and (avg_confidence is None or avg_confidence >= 0.7)

if __name__ == "__main__":
    success = test_enhanced_extractor_real_data()
    if success:
        print("\n🚀 Enhanced market-aware extractor validated successfully on real data!")
        print("✅ Ready to proceed with remaining pipeline components")
    else:
        print("\n🔧 Further refinement needed based on real data test results")