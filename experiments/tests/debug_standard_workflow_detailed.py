#!/usr/bin/env python3

"""
Debug the standard workflow processing in detail to see where it's failing
compared to our standalone pattern tests.
"""

import sys
import os
import re
import logging
import importlib.util
from pymongo import MongoClient
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add the experiments directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import pattern library manager
experiments_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
pattern_manager_path = os.path.join(experiments_dir, '00b_pattern_library_manager_v1.py')
spec = importlib.util.spec_from_file_location("pattern_manager", pattern_manager_path)
pattern_manager = importlib.util.module_from_spec(spec)
spec.loader.exec_module(pattern_manager)
PatternLibraryManager = pattern_manager.PatternLibraryManager

# Import report extractor 
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

def test_failing_pattern_direct_vs_pipeline(logger):
    """Compare direct pattern matching vs pipeline processing."""
    logger.info("="*60)
    logger.info("COMPARING DIRECT VS PIPELINE PATTERN MATCHING")
    logger.info("="*60)
    
    # Initialize pattern manager and extractor
    pattern_manager = PatternLibraryManager()
    extractor = MarketAwareReportTypeExtractor(pattern_manager)
    
    # Get database connection
    client = MongoClient(os.getenv('MONGODB_URI'))
    db = client['deathstar']
    
    # Test the known failing case
    test_title = "Antimicrobial Medical Textiles Market, Industry Report"
    
    logger.info(f"\nTesting title: {test_title}")
    
    # 1. Test direct database pattern matching
    logger.info("\n--- 1. DIRECT DATABASE PATTERN TEST ---")
    pattern_doc = db.pattern_libraries.find_one({
        "type": "report_type",
        "active": True,
        "term": "Manual Review #6: Market, Industry Report"
    })
    
    if pattern_doc:
        pattern_text = pattern_doc.get('pattern', '')
        logger.info(f"Found pattern: {pattern_text}")
        
        match = re.search(pattern_text, test_title, re.IGNORECASE)
        if match:
            logger.info(f"✅ DIRECT MATCH: {match.groups()}")
        else:
            logger.info(f"❌ DIRECT NO MATCH")
    
    # 2. Test through pipeline
    logger.info("\n--- 2. PIPELINE PROCESSING TEST ---")
    result = extractor.extract(test_title, 'standard')
    logger.info(f"Pipeline result: {result.final_report_type}")
    logger.info(f"Pipeline notes: {result.notes}")
    logger.info(f"Pipeline confidence: {result.confidence}")
    
    # 3. Test pattern loading in extractor  
    logger.info("\n--- 3. PATTERN LOADING IN EXTRACTOR ---")
    compound_patterns = extractor.compound_type_patterns
    logger.info(f"Loaded {len(compound_patterns)} compound patterns")
    
    # Find our specific pattern
    target_pattern = None
    for pattern in compound_patterns:
        if "Industry Report" in pattern.get('term', ''):
            target_pattern = pattern
            break
    
    if target_pattern:
        logger.info(f"Found target pattern in extractor: {target_pattern['term']}")
        logger.info(f"Pattern regex: {target_pattern['pattern']}")
        
        # Test this pattern directly
        try:
            pattern_regex = re.compile(target_pattern['pattern'], re.IGNORECASE)
            match = pattern_regex.search(test_title)
            if match:
                logger.info(f"✅ EXTRACTOR PATTERN MATCH: {match.groups()}")
            else:
                logger.info(f"❌ EXTRACTOR PATTERN NO MATCH")
        except Exception as e:
            logger.error(f"❌ EXTRACTOR PATTERN ERROR: {e}")
    else:
        logger.error("❌ TARGET PATTERN NOT FOUND IN EXTRACTOR")
    
    # 4. Test confusing terms removal
    logger.info("\n--- 4. CONFUSING TERMS TEST ---")
    temp_title, removed_terms = extractor._create_confusing_terms_free_text(test_title)
    logger.info(f"Original title: {test_title}")
    logger.info(f"After confusing terms removal: {temp_title}")
    logger.info(f"Removed terms: {removed_terms}")
    
    client.close()

def main():
    """Main debug function."""
    logger = setup_logging()
    test_failing_pattern_direct_vs_pipeline(logger)

if __name__ == "__main__":
    main()