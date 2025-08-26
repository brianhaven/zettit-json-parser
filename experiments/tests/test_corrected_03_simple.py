#!/usr/bin/env python3

"""
Simple test for corrected 03_report_type_extractor_v2.py implementation.
"""

import sys
import os
from datetime import datetime
import logging
import importlib.util

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

# Import corrected extractor (now the main file)
corrected_extractor_path = os.path.join(experiments_dir, '03_report_type_extractor_v2.py')
spec = importlib.util.spec_from_file_location("corrected_extractor", corrected_extractor_path)
corrected_extractor = importlib.util.module_from_spec(spec)
spec.loader.exec_module(corrected_extractor)
MarketAwareReportTypeExtractor = corrected_extractor.MarketAwareReportTypeExtractor

def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    return logging.getLogger(__name__)

def main():
    """Main test function."""
    logger = setup_logging()
    
    logger.info("="*60)
    logger.info("Testing Corrected Market-Aware Report Type Extractor")
    logger.info(f"Analysis Date (PDT): {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} PDT")
    logger.info(f"Analysis Date (UTC): {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC")
    logger.info("="*60)
    
    try:
        # Initialize components
        pattern_manager = PatternLibraryManager()
        logger.info("✅ PatternLibraryManager initialized successfully")
        
        extractor = MarketAwareReportTypeExtractor(pattern_manager)
        logger.info("✅ MarketAwareReportTypeExtractor initialized successfully")
        
        # Simple test cases
        test_cases = [
            {
                "title": "APAC Personal Protective Equipment Market Report",
                "market_type": "standard",
                "expected": "Market Report"
            },
            {
                "title": "Veterinary Vaccine Market for Livestock Analysis",
                "market_type": "market_for", 
                "expected": "Market Analysis"
            }
        ]
        
        for i, test_case in enumerate(test_cases, 1):
            logger.info(f"\n--- Test Case {i} ---")
            logger.info(f"Input: {test_case['title']}")
            logger.info(f"Market Type: {test_case['market_type']}")
            
            result = extractor.extract(test_case['title'], test_case['market_type'])
            
            logger.info(f"Expected: {test_case['expected']}")
            logger.info(f"Actual: {result.final_report_type}")
            logger.info(f"Processing Workflow: {result.processing_workflow}")
            logger.info(f"Confidence: {result.confidence}")
            logger.info(f"Notes: {result.notes}")
            
            if result.final_report_type:
                success = result.final_report_type == test_case['expected']
                logger.info(f"{'✅ SUCCESS' if success else '❌ MISMATCH'}")
            else:
                logger.info("❌ NO EXTRACTION")
        
        logger.info("\n" + "="*60)
        logger.info("Test completed!")
        
    except Exception as e:
        logger.error(f"❌ Test failed with error: {str(e)}")
        import traceback
        traceback.print_exc()
        raise

if __name__ == "__main__":
    main()