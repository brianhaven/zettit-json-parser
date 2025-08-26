#!/usr/bin/env python3

"""
Comprehensive debugging script for 03_report_type_extractor_v2.py with live data.

This script identifies all issues preventing ~100% extraction success rate.
"""

import sys
import os
from datetime import datetime
import logging
import re
import importlib.util
from pymongo import MongoClient
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add the experiments directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the corrected implementation and pattern manager using importlib
experiments_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Import pattern library manager
pattern_manager_path = os.path.join(experiments_dir, '00b_pattern_library_manager_v1.py')
spec = importlib.util.spec_from_file_location("pattern_manager", pattern_manager_path)
pattern_manager = importlib.util.module_from_spec(spec)
spec.loader.exec_module(pattern_manager)
PatternLibraryManager = pattern_manager.PatternLibraryManager

# Import market term classifier
classifier_path = os.path.join(experiments_dir, '01_market_term_classifier_v1.py')
spec = importlib.util.spec_from_file_location("classifier", classifier_path)
classifier_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(classifier_module)
MarketTermClassifier = classifier_module.MarketTermClassifier

# Import date extractor
date_extractor_path = os.path.join(experiments_dir, '02_date_extractor_v1.py')
spec = importlib.util.spec_from_file_location("date_extractor", date_extractor_path)
date_extractor_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(date_extractor_module)
DateExtractor = date_extractor_module.EnhancedDateExtractor

# Import corrected report type extractor (now the main file)
report_extractor_path = os.path.join(experiments_dir, '03_report_type_extractor_v2.py')
spec = importlib.util.spec_from_file_location("report_extractor", report_extractor_path)
report_extractor_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(report_extractor_module)
MarketAwareReportTypeExtractor = report_extractor_module.MarketAwareReportTypeExtractor

def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    return logging.getLogger(__name__)

def analyze_pattern_structure(pattern_manager, logger):
    """Analyze pattern structure to identify issues."""
    logger.info("="*60)
    logger.info("PATTERN STRUCTURE ANALYSIS")
    logger.info("="*60)
    
    # Get database connection 
    client = MongoClient(os.getenv('MONGODB_URI'))
    db = client['deathstar']
    
    # Check pattern categories
    pipeline = [
        {"$match": {"type": "report_type", "active": True}},
        {"$group": {
            "_id": "$format_type",
            "count": {"$sum": 1},
            "samples": {"$push": {"term": "$term", "pattern": "$pattern"}}
        }},
        {"$sort": {"count": -1}}
    ]
    
    categories = list(db.pattern_libraries.aggregate(pipeline))
    
    for category in categories:
        logger.info(f"\n--- {category['_id']} ({category['count']} patterns) ---")
        for sample in category['samples'][:3]:  # Show first 3 samples
            logger.info(f"  {sample['term']}: {sample['pattern']}")
    
    # Sample some common patterns that should match our test data
    common_patterns = list(db.pattern_libraries.find({
        "type": "report_type",
        "active": True,
        "term": {"$in": [
            "Market Report Terminal",
            "Market Size Share Report", 
            "Market Share Report Terminal",
            "Market Size Report Terminal"
        ]}
    }))
    
    logger.info(f"\n--- KEY PATTERNS FOR TEST DATA ---")
    for pattern in common_patterns:
        logger.info(f"  {pattern['term']}: {pattern['pattern']}")
    
    client.close()

def test_pattern_matching_directly(logger):
    """Test pattern matching directly against sample titles."""
    logger.info("="*60)
    logger.info("DIRECT PATTERN MATCHING TEST")
    logger.info("="*60)
    
    # Test titles from real data
    test_titles = [
        "APAC & Middle East Personal Protective Equipment Market Report",
        "Automotive Steel Wheels Market Size & Share Report", 
        "Ammunition Market Size, Share And Growth Report",
        "Antimicrobial Medical Textiles Market, Industry Report"
    ]
    
    # Test patterns
    test_patterns = [
        (r'\bMarket\s+(Report)\s*$', "Market Report Terminal"),
        (r'\bMarket\s+Size,?\s+Share,?\s*&?\s*Growth?\s*(Report)(?:\s*$|[,.])', "Market Size Share Report"),
        (r'\bMarket\s+Size,?\s+&?\s+Share,?\s+(Report)(?:\s*$|[,.])', "Market Size & Share Report"),
        (r'\bMarket,?\s+(Industry\s+Report)(?:\s*$|[,.])', "Market Industry Report")
    ]
    
    for title in test_titles:
        logger.info(f"\n--- Testing: {title} ---")
        found_match = False
        
        for pattern, name in test_patterns:
            match = re.search(pattern, title, re.IGNORECASE)
            if match:
                logger.info(f"  ✅ MATCH: {name}")
                logger.info(f"     Pattern: {pattern}")
                logger.info(f"     Captured: {match.groups()}")
                found_match = True
                break
        
        if not found_match:
            logger.info(f"  ❌ NO MATCH FOUND")

def run_full_pipeline_test(logger):
    """Run full pipeline test with live data."""
    logger.info("="*60)
    logger.info("FULL PIPELINE TEST WITH LIVE DATA")
    logger.info("="*60)
    
    try:
        # Initialize all components
        pattern_manager = PatternLibraryManager()
        market_classifier = MarketTermClassifier(pattern_manager)
        date_extractor = DateExtractor(pattern_manager)
        report_extractor = MarketAwareReportTypeExtractor(pattern_manager)
        
        logger.info("✅ All components initialized successfully")
        
        # Get sample data from database
        client = MongoClient(os.getenv('MONGODB_URI'))
        db = client['deathstar']
        
        # Get 20 real titles
        sample_docs = list(db.markets_raw.find({}, {"report_title_short": 1, "_id": 0}).limit(20))
        titles = [doc["report_title_short"] for doc in sample_docs]
        
        logger.info(f"Testing with {len(titles)} real titles from database")
        
        successful_extractions = 0
        failed_extractions = 0
        
        for i, title in enumerate(titles, 1):
            logger.info(f"\n--- Test {i}: {title} ---")
            
            try:
                # Step 1: Market classification
                market_result = market_classifier.classify(title)
                market_type = market_result.market_term_type if hasattr(market_result, 'market_term_type') else 'standard'
                logger.info(f"  Market Type: {market_type}")
                
                # Step 2: Date extraction
                date_result = date_extractor.extract(title)
                title_after_date = date_result.cleaned_title if hasattr(date_result, 'cleaned_title') else title
                extracted_date = date_result.extracted_date_range if hasattr(date_result, 'extracted_date_range') else 'No date'
                logger.info(f"  Date: {extracted_date}")
                logger.info(f"  After Date: {title_after_date}")
                
                # Step 3: Report type extraction
                report_result = report_extractor.extract(title_after_date, market_type)
                
                if report_result.final_report_type:
                    logger.info(f"  ✅ SUCCESS: {report_result.final_report_type}")
                    logger.info(f"     Confidence: {report_result.confidence}")
                    logger.info(f"     Workflow: {report_result.processing_workflow}")
                    successful_extractions += 1
                else:
                    logger.info(f"  ❌ FAILED: No report type extracted")
                    logger.info(f"     Notes: {report_result.notes}")
                    failed_extractions += 1
                    
            except Exception as e:
                logger.error(f"  ❌ ERROR: {str(e)}")
                failed_extractions += 1
        
        # Final statistics
        total = successful_extractions + failed_extractions
        success_rate = (successful_extractions / total * 100) if total > 0 else 0
        
        logger.info("="*60)
        logger.info("PIPELINE TEST RESULTS")
        logger.info("="*60)
        logger.info(f"Total Processed: {total}")
        logger.info(f"Successful Extractions: {successful_extractions}")
        logger.info(f"Failed Extractions: {failed_extractions}")
        logger.info(f"Success Rate: {success_rate:.1f}%")
        
        if success_rate < 95:
            logger.error(f"❌ SUCCESS RATE TOO LOW: {success_rate:.1f}% (Target: ~100%)")
        else:
            logger.info(f"✅ SUCCESS RATE ACCEPTABLE: {success_rate:.1f}%")
        
        client.close()
        
    except Exception as e:
        logger.error(f"Pipeline test failed: {str(e)}")
        import traceback
        traceback.print_exc()

def main():
    """Main diagnostic function."""
    logger = setup_logging()
    
    logger.info("="*60)
    logger.info("COMPREHENSIVE DEBUGGING: Script 03 Pattern Matching")
    logger.info(f"Analysis Date (PDT): {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} PDT")
    logger.info(f"Analysis Date (UTC): {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC")
    logger.info("="*60)
    
    try:
        # Initialize pattern manager
        pattern_manager = PatternLibraryManager()
        
        # 1. Analyze pattern structure
        analyze_pattern_structure(pattern_manager, logger)
        
        # 2. Test pattern matching directly
        test_pattern_matching_directly(logger)
        
        # 3. Run full pipeline test
        run_full_pipeline_test(logger)
        
        logger.info("\n" + "="*60)
        logger.info("DEBUGGING COMPLETE - CHECK RESULTS ABOVE")
        logger.info("="*60)
        
    except Exception as e:
        logger.error(f"❌ Debugging failed with error: {str(e)}")
        import traceback
        traceback.print_exc()
        raise

if __name__ == "__main__":
    main()