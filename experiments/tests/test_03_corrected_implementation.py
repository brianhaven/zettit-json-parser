#!/usr/bin/env python3

"""
Test script to verify the corrected 03_report_type_extractor_v2_corrected.py implementation.

This script tests both standard and market-aware processing workflows.
"""

import sys
import os
from datetime import datetime
import logging
from typing import Dict, Any
import importlib.util

# Add the experiments directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the corrected implementation and pattern manager using importlib
experiments_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Import corrected extractor
corrected_extractor_path = os.path.join(experiments_dir, '03_report_type_extractor_v2_corrected.py')
spec = importlib.util.spec_from_file_location("corrected_extractor", corrected_extractor_path)
corrected_extractor = importlib.util.module_from_spec(spec)
spec.loader.exec_module(corrected_extractor)
ReportTypeExtractor = corrected_extractor.MarketAwareReportTypeExtractor

# Import pattern library manager
pattern_manager_path = os.path.join(experiments_dir, '00b_pattern_library_manager_v1.py')
spec = importlib.util.spec_from_file_location("pattern_manager", pattern_manager_path)
pattern_manager = importlib.util.module_from_spec(spec)
spec.loader.exec_module(pattern_manager)
PatternLibraryManager = pattern_manager.PatternLibraryManager

def setup_logging() -> logging.Logger:
    """Set up logging for the test script."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    return logging.getLogger(__name__)

def test_standard_processing(extractor: ReportTypeExtractor, logger: logging.Logger):
    """Test standard processing workflow with real titles."""
    logger.info("Testing STANDARD processing workflow...")
    
    test_cases = [
        {
            "title": "APAC & Middle East Personal Protective Equipment Market Report, 2030",
            "title_after_date": "APAC & Middle East Personal Protective Equipment Market Report",
            "market_type": "standard",
            "expected_report_type": "Market Report"
        },
        {
            "title": "Automotive Steel Wheels Market Size & Share Report, 2030", 
            "title_after_date": "Automotive Steel Wheels Market Size & Share Report",
            "market_type": "standard",
            "expected_report_type": "Market Size & Share Report"
        },
        {
            "title": "Antimicrobial Medical Textiles Market, Industry Report, 2030",
            "title_after_date": "Antimicrobial Medical Textiles Market, Industry Report", 
            "market_type": "standard",
            "expected_report_type": "Market, Industry Report"
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        logger.info(f"\n--- Standard Test Case {i} ---")
        logger.info(f"Input: {test_case['title_after_date']}")
        logger.info(f"Market Type: {test_case['market_type']}")
        
        result = extractor.extract(
            test_case['title_after_date'], 
            test_case['market_type']
        )
        
        logger.info(f"Expected: {test_case['expected_report_type']}")
        logger.info(f"Actual Result Type: {result.final_report_type}")
        logger.info(f"Confidence: {result.confidence}")
        logger.info(f"Notes: {result.notes}")
        
        if result.final_report_type:
            success = result.final_report_type == test_case['expected_report_type']
            logger.info(f"✅ SUCCESS" if success else f"❌ MISMATCH")
        else:
            logger.info(f"❌ NO EXTRACTION")

def test_market_aware_processing(extractor: ReportTypeExtractor, logger: logging.Logger):
    """Test market-aware processing workflow with synthetic market term examples."""
    logger.info("\n" + "="*60)
    logger.info("Testing MARKET-AWARE processing workflow...")
    
    # These are synthetic examples to test the market-aware logic
    test_cases = [
        {
            "title": "Veterinary Vaccine Market for Livestock Analysis, 2025-2030",
            "title_after_date": "Veterinary Vaccine Market for Livestock Analysis",
            "market_type": "market_for",
            "expected_report_type": "Market Analysis",
            "expected_pipeline_forward": "Veterinary Vaccine for Livestock"
        },
        {
            "title": "AI Solutions Market in Healthcare Outlook, 2024-2029",
            "title_after_date": "AI Solutions Market in Healthcare Outlook", 
            "market_type": "market_in",
            "expected_report_type": "Market Outlook",
            "expected_pipeline_forward": "AI Solutions in Healthcare"
        },
        {
            "title": "Smart Devices Market by Region Report, 2023-2028",
            "title_after_date": "Smart Devices Market by Region Report",
            "market_type": "market_by", 
            "expected_report_type": "Market Report",
            "expected_pipeline_forward": "Smart Devices by Region"
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        logger.info(f"\n--- Market-Aware Test Case {i} ---")
        logger.info(f"Input: {test_case['title_after_date']}")
        logger.info(f"Market Type: {test_case['market_type']}")
        
        result = extractor.extract(
            test_case['title_after_date'], 
            test_case['market_type']
        )
        
        logger.info(f"Expected Report Type: {test_case['expected_report_type']}")
        logger.info(f"Expected Pipeline Forward: {test_case['expected_pipeline_forward']}")
        logger.info(f"Actual Report Type: {result.final_report_type}")
        logger.info(f"Actual Pipeline Forward: {result.title}")  # This should be the title for next stage
        logger.info(f"Processing Workflow: {result.processing_workflow}")
        logger.info(f"Confidence: {result.confidence}")
        logger.info(f"Notes: {result.notes}")
        
        if result.final_report_type:
            report_success = result.final_report_type == test_case['expected_report_type']
            # For market-aware, need to check what field contains the pipeline-forward title
            pipeline_success = result.title == test_case['expected_pipeline_forward'] 
            logger.info(f"Report Type: {'✅ SUCCESS' if report_success else '❌ MISMATCH'}")
            logger.info(f"Pipeline Forward: {'✅ SUCCESS' if pipeline_success else '❌ MISMATCH'}")
        else:
            logger.info(f"❌ INCOMPLETE EXTRACTION")

def main():
    """Main test function."""
    logger = setup_logging()
    
    logger.info("="*60)
    logger.info("Testing Report Type Extractor V2 Corrected Implementation")
    logger.info(f"Analysis Date (PDT): {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} PDT")
    logger.info(f"Analysis Date (UTC): {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC")
    logger.info("="*60)
    
    try:
        # Initialize the pattern library manager first
        pattern_manager = PatternLibraryManager()
        logger.info("✅ PatternLibraryManager initialized successfully")
        
        # Initialize the extractor with pattern manager
        extractor = ReportTypeExtractor(pattern_manager)
        logger.info("✅ ReportTypeExtractor initialized successfully")
        
        # Test standard processing
        test_standard_processing(extractor, logger)
        
        # Test market-aware processing  
        test_market_aware_processing(extractor, logger)
        
        logger.info("\n" + "="*60)
        logger.info("Test completed! Check results above.")
        logger.info("="*60)
        
    except Exception as e:
        logger.error(f"❌ Test failed with error: {str(e)}")
        raise

if __name__ == "__main__":
    main()