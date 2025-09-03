#!/usr/bin/env python3
"""
Script 03 v2 vs v3 Comparison Test Harness
Comprehensive testing framework to validate dictionary approach against current v2 implementation.

This test harness:
1. Runs identical test cases through both Script 03 v2 and v3
2. Generates detailed comparison reports with success/failure analysis
3. Analyzes final_topics.txt output files to identify issues
4. Targets 100% success rate validation
5. Provides actionable insights for improvements

Usage:
    python3 test_03_v2_vs_v3_comparison_harness.py [quantity]
    
    quantity: Number of titles to test (default: 25)
    Examples:
        python3 test_03_v2_vs_v3_comparison_harness.py 25    # Test 25 titles
        python3 test_03_v2_vs_v3_comparison_harness.py 100   # Test 100 titles
        python3 test_03_v2_vs_v3_comparison_harness.py       # Test 25 titles (default)
"""

import os
import sys
import json
import logging
from datetime import datetime
from typing import Dict, Any, List, Tuple
import importlib.util
import argparse
from collections import defaultdict

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv()

# Setup logging - WARNING level for performance
logging.basicConfig(level=logging.WARNING, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def import_module_from_path(module_name: str, file_path: str):
    """Import a module from a file path."""
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

def create_output_directory(script_name: str) -> str:
    """Create timestamped output directory using absolute paths."""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    experiments_dir = os.path.dirname(script_dir)  
    project_root = os.path.dirname(experiments_dir)
    outputs_dir = os.path.join(project_root, 'outputs')
    
    try:
        import pytz
        pdt = pytz.timezone('America/Los_Angeles')
        timestamp = datetime.now(pdt).strftime('%Y%m%d_%H%M%S')
    except ImportError:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    output_dir = os.path.join(outputs_dir, f"{timestamp}_{script_name}")
    os.makedirs(output_dir, exist_ok=True)
    
    return output_dir

def get_timestamp():
    """Generate timestamp for Pacific Time."""
    try:
        import pytz
        pst = pytz.timezone('US/Pacific')
        utc = pytz.timezone('UTC')
        
        now_pst = datetime.now(pst)
        now_utc = datetime.now(utc)
        
        return {
            'pst': now_pst.strftime("%Y-%m-%d %H:%M:%S %Z"),
            'utc': now_utc.strftime("%Y-%m-%d %H:%M:%S %Z"),
            'filename': now_pst.strftime("%Y%m%d_%H%M%S")
        }
    except ImportError:
        now = datetime.now()
        return {
            'pst': now.strftime("%Y-%m-%d %H:%M:%S PST"),
            'utc': now.strftime("%Y-%m-%d %H:%M:%S UTC"),
            'filename': now.strftime("%Y%m%d_%H%M%S")
        }

def get_diverse_test_cases(quantity: int = 25) -> List[Dict[str, Any]]:
    """Get diverse test cases covering different patterns and edge cases."""
    client = MongoClient(os.getenv('MONGODB_URI'))
    db = client['deathstar']
    collection = db['markets_raw']
    
    # Diverse sampling strategy to cover different patterns
    test_cases = []
    
    # 1. Market term titles (market_for, market_in, market_by)
    market_samples = list(collection.aggregate([
        {"$match": {"report_title_short": {"$regex": "Market (for|in|by)", "$options": "i"}}},
        {"$sample": {"size": max(1, quantity // 4)}}
    ]))
    test_cases.extend(market_samples)
    
    # 2. Standard titles with different report types
    standard_samples = list(collection.aggregate([
        {"$match": {
            "report_title_short": {"$regex": "(Analysis|Report|Study|Forecast|Outlook)", "$options": "i"},
            "$and": [{"report_title_short": {"$not": {"$regex": "Market (for|in|by)", "$options": "i"}}}]
        }},
        {"$sample": {"size": max(1, quantity // 4)}}
    ]))
    test_cases.extend(standard_samples)
    
    # 3. Complex titles with dates and regions
    complex_samples = list(collection.aggregate([
        {"$match": {
            "report_title_short": {"$regex": "(2024|2025|2026|Global|APAC|Europe)", "$options": "i"}
        }},
        {"$sample": {"size": max(1, quantity // 4)}}
    ]))
    test_cases.extend(complex_samples)
    
    # 4. Random diverse sampling for remaining
    remaining_needed = quantity - len(test_cases)
    if remaining_needed > 0:
        remaining_samples = list(collection.aggregate([
            {"$sample": {"size": remaining_needed}}
        ]))
        test_cases.extend(remaining_samples)
    
    # Ensure we have exact quantity
    test_cases = test_cases[:quantity]
    
    client.close()
    return test_cases

def run_pipeline_through_version(test_cases: List[Dict], version: str, output_dir: str) -> List[Dict]:
    """Run test cases through complete 01→02→03→04 pipeline with specified Script 03 version (v2 or v3)."""
    logger.info(f"Running {len(test_cases)} test cases through complete 01→02→03({version})→04 pipeline")
    
    # Import required modules
    parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    # Import Scripts 01, 02, and 04 (same for both tests)
    script01 = import_module_from_path("market_term_classifier", 
                                     os.path.join(parent_dir, "01_market_term_classifier_v1.py"))
    script02 = import_module_from_path("date_extractor",
                                     os.path.join(parent_dir, "02_date_extractor_v1.py"))
    script04 = import_module_from_path("geographic_entity_detector_v2",
                                     os.path.join(parent_dir, "04_geographic_entity_detector_v2.py"))
    
    # Import appropriate Script 03 version
    script03_file = f"03_report_type_extractor_{version}.py"
    script03 = import_module_from_path("report_extractor",
                                     os.path.join(parent_dir, script03_file))
    
    # Initialize pattern library manager
    pattern_manager = import_module_from_path("pattern_library_manager",
                                            os.path.join(parent_dir, "00b_pattern_library_manager_v1.py"))
    pattern_lib_manager = pattern_manager.PatternLibraryManager(os.getenv('MONGODB_URI'))
    
    # Initialize components (all use PatternLibraryManager for consistency)
    market_classifier = script01.MarketTermClassifier(pattern_lib_manager)
    date_extractor = script02.EnhancedDateExtractor(pattern_lib_manager)
    
    # Version-specific report extractor class names
    if version == "v2":
        report_extractor = script03.MarketAwareReportTypeExtractor(pattern_lib_manager)
    else:  # v3
        report_extractor = script03.DictionaryBasedReportTypeExtractor(pattern_lib_manager)
    
    geo_detector = script04.GeographicEntityDetector(pattern_lib_manager)
    
    results = []
    
    for i, case in enumerate(test_cases, 1):
        title = case['report_title_short']
        logger.info(f"Processing {i}/{len(test_cases)}: {title[:50]}...")
        
        result = {
            'test_case': i,
            'original_title': title,
            'version': version
        }
        
        try:
            current_title = title
            
            # Stage 1: Market Term Classification
            market_result = market_classifier.classify(current_title)
            result['market_term_type'] = market_result.market_type
            result['market_confidence'] = market_result.confidence
            logger.debug(f"Stage 1 - Market Classification: {market_result.market_type}")
            
            # Stage 2: Date Extraction
            date_result = date_extractor.extract(current_title)
            result['extracted_forecast_date_range'] = date_result.extracted_date_range or ''
            result['date_confidence'] = date_result.confidence
            if date_result.extracted_date_range:
                current_title = date_result.cleaned_title
                logger.debug(f"Stage 2 - Date Extracted: {date_result.extracted_date_range}")
            else:
                logger.debug("Stage 2 - No date found")
            
            # Stage 3: Report Type Extraction (VERSION-SPECIFIC)
            report_result = report_extractor.extract(current_title, market_result.market_type)
            result['extracted_report_type'] = report_result.extracted_report_type or ''
            result['report_confidence'] = report_result.confidence
            if report_result.extracted_report_type:
                current_title = report_result.title  # Pipeline forward text
                logger.debug(f"Stage 3 - Report Type ({version}): {report_result.extracted_report_type}")
            else:
                logger.debug(f"Stage 3 - No report type found ({version})")
            
            # Stage 4: Geographic Entity Detection
            geo_result = geo_detector.extract_geographic_entities(current_title)
            result['extracted_regions'] = geo_result.extracted_regions if geo_result else []
            result['geo_confidence'] = geo_result.confidence_score if geo_result else 1.0
            if geo_result and geo_result.extracted_regions:
                current_title = geo_result.title  # Fixed: use .title instead of .remaining_text
                logger.debug(f"Stage 4 - Regions: {geo_result.extracted_regions}")
            else:
                logger.debug("Stage 4 - No geographic regions found")
            
            # Final topic after complete pipeline
            result['topic'] = current_title.strip()
            
            # Compile confidence scores
            result['confidence_scores'] = {
                'market_classification': result['market_confidence'],
                'date_extraction': result['date_confidence'], 
                'report_type': result['report_confidence'],
                'geographic_extraction': result['geo_confidence']
            }
            
            # Overall success determination (more comprehensive)
            result['success'] = bool(
                result['topic'] and  # Final topic exists
                (result['extracted_report_type'] or result['extracted_regions'] or result['extracted_forecast_date_range'])  # At least one extraction
            )
            result['error'] = None
            
            logger.debug(f"Final Topic ({version}): {result['topic']}")
            
        except Exception as e:
            result['success'] = False
            result['error'] = str(e)
            result['market_term_type'] = None
            result['extracted_forecast_date_range'] = ''
            result['extracted_report_type'] = ''
            result['extracted_regions'] = []
            result['topic'] = title  # Fallback to original
            result['confidence_scores'] = {
                'market_classification': 0.0,
                'date_extraction': 0.0,
                'report_type': 0.0,
                'geographic_extraction': 0.0
            }
            logger.error(f"Error processing '{title}' with {version}: {e}")
        
        results.append(result)
    
    # Close connection
    pattern_lib_manager.close_connection()
    
    return results

def generate_comprehensive_output_files(results: List[Dict], version: str, output_dir: str) -> None:
    """Generate comprehensive output files matching the reference test structure."""
    timestamp = get_timestamp()
    
    # 1) Final topics file (CRITICAL for analysis)
    final_topics_file = os.path.join(output_dir, f"final_topics_{version}.txt")
    with open(final_topics_file, 'w') as f:
        f.write(f"Final Topics (Pipeline Forward Text) - {version.upper()}\n")
        f.write(f"Analysis Date (PDT): {timestamp['pst']}\n")
        f.write("=" * 50 + "\n\n")
        
        for result in results:
            if result['topic']:
                f.write(f"{result['topic']}\n")
    
    # 2) Market classifications file
    market_classifications_file = os.path.join(output_dir, f"market_classifications_{version}.txt")
    with open(market_classifications_file, 'w') as f:
        f.write(f"Market Term Classifications - {version.upper()}\n")
        f.write(f"Analysis Date (PDT): {timestamp['pst']}\n")
        f.write("=" * 50 + "\n\n")
        
        # Group by market term type
        market_terms = [r for r in results if r['market_term_type'] != 'standard']
        standard_terms = [r for r in results if r['market_term_type'] == 'standard']
        
        f.write("MARKET TERM CLASSIFICATIONS:\n")
        for result in market_terms:
            f.write(f"{result['original_title']}\n")
        
        f.write(f"\nSTANDARD CLASSIFICATIONS:\n")
        for result in standard_terms:
            f.write(f"{result['original_title']}\n")
    
    # 3) Extracted dates file (deduplicated)
    dates_file = os.path.join(output_dir, f"extracted_dates_{version}.txt")
    unique_dates = set()
    for result in results:
        if result['extracted_forecast_date_range']:
            unique_dates.add(result['extracted_forecast_date_range'])
    
    with open(dates_file, 'w') as f:
        f.write(f"Extracted Dates (Deduplicated) - {version.upper()}\n")
        f.write(f"Analysis Date (PDT): {timestamp['pst']}\n")
        f.write("=" * 50 + "\n\n")
        
        for date in sorted(unique_dates):
            f.write(f"{date}\n")
    
    # 4) Extracted report types file (deduplicated)
    report_types_file = os.path.join(output_dir, f"extracted_report_types_{version}.txt")
    unique_report_types = set()
    for result in results:
        if result['extracted_report_type']:
            unique_report_types.add(result['extracted_report_type'])
    
    with open(report_types_file, 'w') as f:
        f.write(f"Extracted Report Types (Deduplicated) - {version.upper()}\n")
        f.write(f"Analysis Date (PDT): {timestamp['pst']}\n")
        f.write("=" * 50 + "\n\n")
        
        for report_type in sorted(unique_report_types):
            f.write(f"{report_type}\n")
    
    # 5) Extracted regions file (deduplicated)
    regions_file = os.path.join(output_dir, f"extracted_regions_{version}.txt")
    with open(regions_file, 'w') as f:
        f.write(f"Extracted Regions (Deduplicated) - {version.upper()}\n")
        f.write(f"Analysis Date (PDT): {timestamp['pst']}\n")
        f.write("=" * 50 + "\n\n")
        
        # Collect all regions and deduplicate while preserving order
        all_regions = []
        seen_regions = set()
        for result in results:
            for region in result['extracted_regions']:
                if region not in seen_regions:
                    all_regions.append(region)
                    seen_regions.add(region)
        
        for region in all_regions:
            f.write(f"{region}\n")
    
    # 6) One-line pipeline results file
    oneline_file = os.path.join(output_dir, f"oneline_pipeline_results_{version}.txt")
    with open(oneline_file, 'w') as f:
        f.write(f"Complete Pipeline Results: 01→02→03({version})→04\n")
        f.write(f"Analysis Date (PDT): {timestamp['pst']}\n")
        f.write("=" * 100 + "\n\n")
        f.write("Format: ORIGINAL → [MARKET] [DATE] [REPORT] [REGIONS] → TOPIC\n\n")
        
        for result in results:
            market_type = result['market_term_type'][:3].upper() if result['market_term_type'] else 'STD'
            date_str = result['extracted_forecast_date_range'] or 'None'
            report_str = result['extracted_report_type'] or 'None'
            regions_str = ', '.join(result['extracted_regions']) if result['extracted_regions'] else 'None'
            topic = result['topic'] or 'None'
            
            f.write(f"{result['test_case']:2d}. {result['original_title']}\n")
            f.write(f"    → [{market_type}] [{date_str}] [{report_str[:20]}...] [{regions_str}] → {topic}\n\n")
    
    # 7) Successful pipeline extractions file
    successful_file = os.path.join(output_dir, f"successful_extractions_{version}.txt")
    with open(successful_file, 'w') as f:
        f.write(f"Successful Complete Extractions - {version.upper()}\n")
        f.write(f"Analysis Date (PDT): {timestamp['pst']}\n")
        f.write(f"Analysis Date (UTC): {timestamp['utc']}\n")
        f.write("=" * 80 + "\n\n")
        
        successful_results = [r for r in results if r['extracted_regions'] or r['extracted_report_type'] or r['extracted_forecast_date_range']]
        f.write(f"Total Successful Pipeline Extractions: {len(successful_results)}\n\n")
        
        for result in successful_results:
            f.write(f"Original: {result['original_title']}\n")
            f.write(f"Market Type: {result['market_term_type']}\n")
            f.write(f"Date Range: {result['extracted_forecast_date_range'] or 'None'}\n")
            f.write(f"Report Type: {result['extracted_report_type'] or 'None'}\n")
            f.write(f"Geographic Regions: {', '.join(result['extracted_regions']) if result['extracted_regions'] else 'None'}\n")
            f.write(f"Final Topic: {result['topic']}\n")
            f.write(f"Geographic Confidence: {result['confidence_scores']['geographic_extraction']:.3f}\n")
            f.write("-" * 60 + "\n\n")

def analyze_final_topics(results: List[Dict], version: str, output_dir: str) -> Dict[str, Any]:
    """Analyze final_topics.txt output to identify issues and patterns."""
    logger.info(f"Analyzing final topics and generating output files for version {version}")
    
    # Generate all comprehensive output files
    generate_comprehensive_output_files(results, version, output_dir)
    
    # Analysis of final topics
    analysis = {
        'total_cases': len(results),
        'successful_extractions': len([r for r in results if r['success']]),
        'failed_extractions': len([r for r in results if not r['success']]),
        'success_rate': len([r for r in results if r['success']]) / len(results) * 100,
        'issues_detected': [],
        'patterns_found': defaultdict(int),
        'version': version
    }
    
    # Detailed issue detection
    for result in results:
        if not result['success']:
            analysis['issues_detected'].append({
                'title': result['original_title'],
                'error': result['error'],
                'market_type': result['market_term_type'],
                'test_case_id': result['test_case']
            })
        else:
            # Pattern analysis for successful cases
            if result['market_term_type']:
                analysis['patterns_found'][result['market_term_type']] += 1
            if result['extracted_report_type']:
                analysis['patterns_found'][f"report_type: {result['extracted_report_type']}"] += 1
    
    return analysis

def generate_comparison_report(v2_results: List[Dict], v3_results: List[Dict], 
                             v2_analysis: Dict, v3_analysis: Dict, 
                             output_dir: str, timestamp: Dict) -> None:
    """Generate comprehensive comparison report."""
    
    comparison_file = os.path.join(output_dir, "v2_vs_v3_comparison_report.md")
    
    with open(comparison_file, 'w') as f:
        f.write("# Script 03 v2 vs v3 Comprehensive Comparison Report\n\n")
        f.write(f"**Analysis Date (PDT):** {timestamp['pst']}  \n")
        f.write(f"**Analysis Date (UTC):** {timestamp['utc']}\n\n")
        
        f.write("## Executive Summary\n\n")
        f.write(f"**Test Cases:** {len(v2_results)} diverse market research titles\n")
        f.write(f"**v2 Success Rate:** {v2_analysis['success_rate']:.2f}% ({v2_analysis['successful_extractions']}/{v2_analysis['total_cases']})\n")
        f.write(f"**v3 Success Rate:** {v3_analysis['success_rate']:.2f}% ({v3_analysis['successful_extractions']}/{v3_analysis['total_cases']})\n")
        
        success_diff = v3_analysis['success_rate'] - v2_analysis['success_rate']
        if success_diff > 0:
            f.write(f"**Improvement:** +{success_diff:.2f}% with v3 dictionary approach ✅\n\n")
        elif success_diff < 0:
            f.write(f"**Regression:** {success_diff:.2f}% with v3 dictionary approach ❌\n\n")
        else:
            f.write(f"**Performance:** Equal success rates between versions\n\n")
        
        f.write("## Detailed Performance Analysis\n\n")
        
        # Side-by-side comparison
        f.write("### Success/Failure Breakdown\n\n")
        f.write("| Metric | v2 (Pattern-Based) | v3 (Dictionary-Based) | Difference |\n")
        f.write("|--------|-------------------|----------------------|------------|\n")
        f.write(f"| Successful | {v2_analysis['successful_extractions']} | {v3_analysis['successful_extractions']} | {v3_analysis['successful_extractions'] - v2_analysis['successful_extractions']:+d} |\n")
        f.write(f"| Failed | {v2_analysis['failed_extractions']} | {v3_analysis['failed_extractions']} | {v3_analysis['failed_extractions'] - v2_analysis['failed_extractions']:+d} |\n")
        f.write(f"| Success Rate | {v2_analysis['success_rate']:.2f}% | {v3_analysis['success_rate']:.2f}% | {success_diff:+.2f}% |\n\n")
        
        # Case-by-case comparison
        f.write("## Case-by-Case Detailed Analysis\n\n")
        f.write("| Case | Original Title | v2 Result | v3 Result | Status |\n")
        f.write("|------|---------------|-----------|-----------|--------|\n")
        
        for i, (v2_result, v3_result) in enumerate(zip(v2_results, v3_results), 1):
            title_short = v2_result['original_title'][:40] + "..." if len(v2_result['original_title']) > 40 else v2_result['original_title']
            v2_status = "✅ SUCCESS" if v2_result['success'] else "❌ FAILED"
            v3_status = "✅ SUCCESS" if v3_result['success'] else "❌ FAILED"
            
            if v2_result['success'] and v3_result['success']:
                overall_status = "🟢 Both Success"
            elif not v2_result['success'] and not v3_result['success']:
                overall_status = "🔴 Both Failed"
            elif v3_result['success'] and not v2_result['success']:
                overall_status = "🟡 v3 Fixed"
            else:
                overall_status = "🟠 v3 Regression"
            
            f.write(f"| {i} | {title_short} | {v2_status} | {v3_status} | {overall_status} |\n")
        
        f.write("\n")
        
        # Issues analysis
        if v2_analysis['issues_detected'] or v3_analysis['issues_detected']:
            f.write("## Issues Requiring Attention\n\n")
            
            if v3_analysis['issues_detected']:
                f.write("### v3 Dictionary Approach Issues\n\n")
                for issue in v3_analysis['issues_detected']:
                    f.write(f"**Case {issue['test_case_id']}:** {issue['title']}\n")
                    f.write(f"- **Error:** {issue['error']}\n")
                    f.write(f"- **Market Type:** {issue['market_type']}\n\n")
            
            # Identify cases that work in v2 but fail in v3
            v3_regressions = []
            for i, (v2_result, v3_result) in enumerate(zip(v2_results, v3_results)):
                if v2_result['success'] and not v3_result['success']:
                    v3_regressions.append({
                        'case_id': i + 1,
                        'title': v2_result['original_title'],
                        'v2_report_type': v2_result['extracted_report_type'],
                        'v3_error': v3_result['error']
                    })
            
            if v3_regressions:
                f.write("### Critical v3 Regressions (worked in v2, failed in v3)\n\n")
                for reg in v3_regressions:
                    f.write(f"**Case {reg['case_id']}:** {reg['title']}\n")
                    f.write(f"- **v2 extracted:** {reg['v2_report_type']}\n")
                    f.write(f"- **v3 error:** {reg['v3_error']}\n\n")
        
        # Recommendations
        f.write("## Recommendations\n\n")
        if v3_analysis['success_rate'] >= v2_analysis['success_rate']:
            if v3_analysis['success_rate'] >= 100.0:
                f.write("✅ **VALIDATION COMPLETE**: v3 dictionary approach achieves 100% success rate\n")
                f.write("- Ready for production deployment\n")
                f.write("- Dictionary-based architecture validated\n")
                f.write("- No regressions detected\n\n")
            else:
                f.write(f"⚠️  **PARTIAL SUCCESS**: v3 achieves {v3_analysis['success_rate']:.2f}% success rate\n")
                f.write("- Investigate remaining failure cases\n")
                f.write("- Enhance dictionary patterns based on failed cases\n")
                f.write("- Consider edge case handling improvements\n\n")
        else:
            f.write("❌ **REGRESSION DETECTED**: v3 performs worse than v2\n")
            f.write("- Review dictionary algorithm implementation\n")
            f.write("- Analyze regression cases for pattern gaps\n")
            f.write("- Consider reverting to v2 approach until issues resolved\n\n")
        
        # Next steps
        f.write("## Next Steps\n\n")
        if v3_analysis['failed_extractions'] > 0:
            f.write(f"1. **Address {v3_analysis['failed_extractions']} failed cases** in v3 implementation\n")
            f.write("2. **Enhance dictionary patterns** based on failure analysis\n")
            f.write("3. **Re-run validation** to confirm 100% success rate\n")
            f.write("4. **Update GitHub Issue #20** with validation results\n\n")
        else:
            f.write("1. **Validation successful** - proceed to production deployment\n")
            f.write("2. **Update GitHub Issue #20** with successful validation\n")
            f.write("3. **Begin Phase 5 Topic Extractor testing**\n\n")

def test_v2_vs_v3_comparison(test_quantity: int = 25):
    """Main comparison test function."""
    logger.info(f"Starting Script 03 v2 vs v3 comparison with {test_quantity} test cases")
    
    # Create output directory
    output_dir = create_output_directory("script03_v2_vs_v3_comparison")
    timestamp = get_timestamp()
    
    logger.info(f"Output directory: {output_dir}")
    
    # Get diverse test cases
    logger.info("Gathering diverse test cases from database...")
    test_cases = get_diverse_test_cases(test_quantity)
    
    # Save test cases for reference
    test_cases_file = os.path.join(output_dir, "test_cases.json")
    with open(test_cases_file, 'w') as f:
        json.dump([{'id': i+1, 'title': case['report_title_short']} for i, case in enumerate(test_cases)], f, indent=2)
    
    # Run tests through v2
    logger.info("Running test cases through Script 03 v2...")
    v2_results = run_pipeline_through_version(test_cases, "v2", output_dir)
    
    # Run tests through v3  
    logger.info("Running test cases through Script 03 v3...")
    v3_results = run_pipeline_through_version(test_cases, "v3", output_dir)
    
    # Analyze results
    logger.info("Analyzing results and generating final topics...")
    v2_analysis = analyze_final_topics(v2_results, "v2", output_dir)
    v3_analysis = analyze_final_topics(v3_results, "v3", output_dir)
    
    # Generate comprehensive comparison report
    logger.info("Generating comprehensive comparison report...")
    generate_comparison_report(v2_results, v3_results, v2_analysis, v3_analysis, output_dir, timestamp)
    
    # Save detailed results
    detailed_results_file = os.path.join(output_dir, "detailed_results.json")
    with open(detailed_results_file, 'w') as f:
        json.dump({
            'v2_results': v2_results,
            'v3_results': v3_results,
            'v2_analysis': v2_analysis,
            'v3_analysis': v3_analysis,
            'test_metadata': {
                'timestamp': timestamp,
                'test_quantity': test_quantity,
                'output_directory': output_dir
            }
        }, f, indent=2, default=str)
    
    # Print summary
    print("\n" + "="*80)
    print("SCRIPT 03 v2 vs v3 COMPARISON COMPLETE")
    print("="*80)
    print(f"Test Cases: {test_quantity}")
    print(f"v2 Success Rate: {v2_analysis['success_rate']:.2f}% ({v2_analysis['successful_extractions']}/{v2_analysis['total_cases']})")
    print(f"v3 Success Rate: {v3_analysis['success_rate']:.2f}% ({v3_analysis['successful_extractions']}/{v3_analysis['total_cases']})")
    
    success_diff = v3_analysis['success_rate'] - v2_analysis['success_rate']
    if success_diff > 0:
        print(f"Improvement: +{success_diff:.2f}% with v3 dictionary approach ✅")
    elif success_diff < 0:
        print(f"Regression: {success_diff:.2f}% with v3 dictionary approach ❌")
    else:
        print("Performance: Equal success rates")
    
    print(f"\nOutput Directory: {output_dir}")
    print("Key Files:")
    print(f"- v2_vs_v3_comparison_report.md (Main analysis)")
    print(f"- final_topics_v2.txt (v2 final topics)")
    print(f"- final_topics_v3.txt (v3 final topics)")
    print(f"- detailed_results.json (Raw data)")
    
    if v3_analysis['success_rate'] >= 100.0:
        print("\n🎯 TARGET ACHIEVED: 100% success rate with v3!")
        print("✅ Ready to proceed to next validation phase")
    else:
        print(f"\n⚠️  TARGET MISSED: {100 - v3_analysis['success_rate']:.2f}% gap to 100% success")
        print("❌ Review failed cases and enhance v3 implementation")
    
    print("="*80)
    
    return output_dir

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Script 03 v2 vs v3 Comparison Test')
    parser.add_argument('quantity', type=int, nargs='?', default=25,
                      help='Number of test cases to run (default: 25)')
    
    args = parser.parse_args()
    
    try:
        output_dir = test_v2_vs_v3_comparison(args.quantity)
        sys.exit(0)
    except Exception as e:
        logger.error(f"Test harness failed: {e}")
        sys.exit(1)