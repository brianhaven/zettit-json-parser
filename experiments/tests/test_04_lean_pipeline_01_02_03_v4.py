#!/usr/bin/env python3
"""
Complete pipeline test: 01→02→03v4→04 with Issue #21 fixes
Tests the full processing pipeline with v4 report type extractor fixes.

Usage:
    python3 test_04_lean_pipeline_01_02_03_v4.py [quantity]
    
    quantity: Number of titles to test (default: 100)
    Examples:
        python3 test_04_lean_pipeline_01_02_03_v4.py 25    # Test 25 titles
        python3 test_04_lean_pipeline_01_02_03_v4.py 500   # Test 500 titles  
        python3 test_04_lean_pipeline_01_02_03_v4.py       # Test 100 titles (default)
"""

import os
import sys
import json
import logging
from datetime import datetime
from typing import Dict, Any, List
import importlib.util
import argparse
import pytz

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv()

# Setup logging - INFO level for Issue #21 validation
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
    
    # Create timestamp in Pacific Time
    pdt = pytz.timezone('America/Los_Angeles')
    timestamp = datetime.now(pdt).strftime('%Y%m%d_%H%M%S')
    
    # Create timestamped subdirectory
    output_dir = os.path.join(outputs_dir, f"{timestamp}_{script_name}")
    os.makedirs(output_dir, exist_ok=True)
    
    return output_dir

def get_timestamp() -> str:
    """Get formatted timestamp in PDT."""
    pdt = pytz.timezone('America/Los_Angeles')
    return datetime.now(pdt).strftime('%Y-%m-%d %H:%M:%S PDT')

def load_test_titles_from_database(quantity: int = 100) -> List[str]:
    """Load titles from MongoDB for testing."""
    try:
        client = MongoClient(os.getenv('MONGODB_URI'))
        db = client['deathstar']
        collection = db['markets_raw']
        
        # Get random sample of titles
        pipeline = [
            {"$sample": {"size": quantity}},
            {"$project": {"report_title_short": 1, "_id": 0}}
        ]
        
        results = list(collection.aggregate(pipeline))
        titles = [doc['report_title_short'] for doc in results if 'report_title_short' in doc]
        
        logger.info(f"Loaded {len(titles)} titles from database")
        return titles
        
    except Exception as e:
        logger.error(f"Failed to load titles from database: {e}")
        return []

def run_complete_pipeline_test(test_quantity: int = 100):
    """Run the complete processing pipeline test with v4 extractor."""
    
    print("\n" + "="*80)
    print("COMPLETE PIPELINE TEST: 01→02→03v4→04 (Issue #21 fixes)")
    print("="*80)
    
    # Create output directory
    output_dir = create_output_directory("pipeline_03v4_test")
    print(f"✓ Output directory: {output_dir}")
    
    # Import modules
    try:
        parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        
        # Import pipeline components
        pattern_manager = import_module_from_path("pattern_library_manager",
                                                os.path.join(parent_dir, "00b_pattern_library_manager_v1.py"))
        script01 = import_module_from_path("market_classifier",
                                         os.path.join(parent_dir, "01_market_term_classifier_v1.py"))
        script02 = import_module_from_path("date_extractor", 
                                         os.path.join(parent_dir, "02_date_extractor_v1.py"))
        script03_v4 = import_module_from_path("report_extractor_v4",
                                            os.path.join(parent_dir, "03_report_type_extractor_v4.py"))
        script04 = import_module_from_path("geographic_detector",
                                         os.path.join(parent_dir, "04_geographic_entity_detector_v2.py"))
        
        print("✓ Successfully imported all pipeline modules")
        
    except Exception as e:
        print(f"✗ Failed to import modules: {e}")
        return
    
    # Initialize components
    try:
        # Initialize PatternLibraryManager
        pattern_lib_manager = pattern_manager.PatternLibraryManager(os.getenv('MONGODB_URI'))
        
        # Initialize pipeline components
        market_classifier = script01.MarketTermClassifier(pattern_lib_manager)
        date_extractor = script02.EnhancedDateExtractor(pattern_lib_manager)
        report_extractor = script03_v4.PureDictionaryReportTypeExtractor(pattern_lib_manager)
        
        # Geographic detector uses PatternLibraryManager (v2 architecture)
        geo_detector = script04.GeographicEntityDetector(pattern_lib_manager)
        
        print("✓ Successfully initialized all pipeline components")
        print(f"  - Market Classifier: {type(market_classifier).__name__}")
        print(f"  - Date Extractor: {type(date_extractor).__name__}")
        print(f"  - Report Extractor: {type(report_extractor).__name__} (v4 - Issue #21 fixes)")
        print(f"  - Geographic Detector: {type(geo_detector).__name__}")
        
    except Exception as e:
        print(f"✗ Failed to initialize components: {e}")
        return
    
    # Load test cases from database
    test_cases = load_test_titles_from_database(test_quantity)
    if not test_cases:
        print("✗ No test cases loaded from database")
        return
        
    print(f"✓ Loaded {len(test_cases)} test cases from database")
    
    # Process test cases
    results = []
    successful_extractions = 0
    timestamp = get_timestamp()
    
    print(f"\\nProcessing {len(test_cases)} test cases through complete pipeline...")
    
    if len(test_cases) < test_quantity:
        print(f"⚠ Only retrieved {len(test_cases)} titles from database, requested {test_quantity}")
    
    for i, original_title in enumerate(test_cases, 1):
        print(f"\\n--- Pipeline Test {i}: {original_title} ---")
        
        try:
            # Stage 1: Market Term Classification
            market_result = market_classifier.classify(original_title)
            current_title = original_title
            print(f"Stage 1 - Market Classification: {market_result.market_type}")
            
            # Stage 2: Date Extraction
            date_result = date_extractor.extract(current_title)
            if date_result.extracted_date_range:
                current_title = date_result.title  # Use cleaned title for next stage
                print(f"Stage 2 - Date Extracted: {date_result.extracted_date_range}")
            else:
                print("Stage 2 - No date found")
            
            # Stage 3: Report Type Extraction (V4 with Issue #21 fixes)
            report_result = report_extractor.extract(
                current_title, 
                market_result.market_type
            )
            if report_result.extracted_report_type:
                current_title = report_result.title  # title contains the pipeline forward text (Issue #14)
                print(f"Stage 3 - Report Type: {report_result.extracted_report_type}")
            else:
                print("Stage 3 - No report type found")
            
            # Stage 4: Geographic Entity Detection (Lean approach)
            geo_result = geo_detector.extract_geographic_entities(current_title)
            if geo_result.extracted_regions:
                current_title = geo_result.remaining_text
                print(f"Stage 4 - Regions: {geo_result.extracted_regions}")
            else:
                print("Stage 4 - No geographic regions found")
            
            # Final topic is what remains
            final_topic = current_title.strip()
            print(f"Final Topic: {final_topic}")
            
            # Track successful extractions (at least report type or regions found)
            if report_result.extracted_report_type or geo_result.extracted_regions:
                successful_extractions += 1
            
            # Compile complete result
            result = {
                'test_case': i,
                'original_title': original_title,
                'market_term_type': market_result.market_type,
                'market_confidence': getattr(market_result, 'confidence', 0.0),
                'extracted_date_range': getattr(date_result, 'extracted_date_range', None),
                'date_confidence': getattr(date_result, 'confidence', 0.0),
                'extracted_report_type': getattr(report_result, 'extracted_report_type', None),
                'report_confidence': getattr(report_result, 'confidence', 0.0),
                'extracted_regions': getattr(geo_result, 'extracted_regions', []),
                'region_confidence': getattr(geo_result, 'confidence', 0.0),
                'final_topic': final_topic,
                'processing_successful': bool(report_result.extracted_report_type or geo_result.extracted_regions)
            }
            
            results.append(result)
            
        except Exception as e:
            logger.error(f"Pipeline test {i} failed: {e}")
            results.append({
                'test_case': i,
                'original_title': original_title,
                'error': str(e),
                'processing_successful': False
            })
    
    # Generate comprehensive results
    print(f"\\n" + "="*80)
    print("PIPELINE TEST RESULTS SUMMARY")
    print("="*80)
    print(f"Total Tests: {len(results)}")
    print(f"Successful Extractions: {successful_extractions}")
    print(f"Success Rate: {(successful_extractions/len(results)*100):.1f}%")
    
    # Save detailed results
    results_file = os.path.join(output_dir, "pipeline_results.json")
    with open(results_file, 'w', encoding='utf-8') as f:
        json.dump({
            'test_metadata': {
                'test_date': timestamp,
                'test_quantity': test_quantity,
                'actual_tests': len(results),
                'success_rate': successful_extractions/len(results)*100,
                'extractor_version': 'v4_issue_21_fixes'
            },
            'test_results': results
        }, f, indent=2, ensure_ascii=False)
    
    print(f"✓ Detailed results saved to: {results_file}")
    
    # Generate final topics file for analysis
    final_topics_file = os.path.join(output_dir, "final_topics.txt")
    with open(final_topics_file, 'w', encoding='utf-8') as f:
        f.write(f"# FINAL TOPICS FROM PIPELINE PROCESSING\\n")
        f.write(f"# Generated: {timestamp}\\n")
        f.write(f"# Extractor: Script 03 v4 (Issue #21 fixes)\\n") 
        f.write(f"# Success Rate: {(successful_extractions/len(results)*100):.1f}%\\n\\n")
        
        for result in results:
            if 'final_topic' in result:
                f.write(f"ORIGINAL: {result['original_title']}\\n")
                f.write(f"FINAL:    {result['final_topic']}\\n")
                if result.get('extracted_report_type'):
                    f.write(f"REPORT:   {result['extracted_report_type']}\\n")
                if result.get('extracted_regions'):
                    f.write(f"REGIONS:  {result['extracted_regions']}\\n")
                f.write("\\n")
    
    print(f"✓ Final topics saved to: {final_topics_file}")
    
    # Issue #21 specific analysis
    keyword_detection_analysis = []
    for result in results:
        if result.get('extracted_report_type'):
            report_type = result['extracted_report_type']
            # Look for Issue #21 keywords
            if any(keyword in report_type for keyword in ['Report', 'Industry', 'industy', 'repot']):
                keyword_detection_analysis.append({
                    'title': result['original_title'],
                    'report_type': report_type,
                    'detected_keywords': [kw for kw in ['Report', 'Industry', 'industy', 'repot'] if kw in report_type]
                })
    
    if keyword_detection_analysis:
        print(f"\\n🎯 Issue #21 Keyword Detection Analysis:")
        print(f"   Found {len(keyword_detection_analysis)} titles with target keywords")
        for item in keyword_detection_analysis[:5]:  # Show first 5
            print(f"   ✓ '{item['report_type']}' detected {item['detected_keywords']}")
        if len(keyword_detection_analysis) > 5:
            print(f"   ... and {len(keyword_detection_analysis) - 5} more")
    
    print(f"\\n✓ Pipeline test completed successfully")
    print(f"📁 All outputs saved to: {output_dir}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Run complete pipeline test with Issue #21 fixes')
    parser.add_argument('quantity', type=int, nargs='?', default=100,
                      help='Number of titles to test (default: 100)')
    
    args = parser.parse_args()
    
    # Validate quantity
    if args.quantity <= 0:
        print("Error: Quantity must be a positive integer")
        sys.exit(1)
    elif args.quantity > 2000:
        print("Warning: Testing more than 2000 titles may take a long time")
    
    run_complete_pipeline_test(args.quantity)