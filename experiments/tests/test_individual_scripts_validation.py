#!/usr/bin/env python3

"""
Individual Script Validation Test
Test each script (01, 02, 03) individually to verify they work correctly.
This helps debug the pipeline integration test.
"""

import sys
import os
import logging
from datetime import datetime
import importlib.util
from pymongo import MongoClient
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add the experiments directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

experiments_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def import_module_dynamically(module_name: str, file_path: str):
    """Import a module dynamically from file path."""
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

def setup_logging() -> logging.Logger:
    """Set up logging."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    return logging.getLogger(__name__)

def test_market_classifier():
    """Test Script 01: Market Term Classifier"""
    logger = setup_logging()
    logger.info("Testing Script 01: Market Term Classifier")
    
    # Import pattern library manager
    pattern_manager_module = import_module_dynamically(
        "pattern_manager", 
        os.path.join(experiments_dir, '00b_pattern_library_manager_v1.py')
    )
    PatternLibraryManager = pattern_manager_module.PatternLibraryManager
    
    # Import market classifier
    market_classifier_module = import_module_dynamically(
        "market_classifier",
        os.path.join(experiments_dir, '01_market_term_classifier_v1.py') 
    )
    MarketTermClassifier = market_classifier_module.MarketTermClassifier
    
    # Initialize
    pattern_manager = PatternLibraryManager()
    classifier = MarketTermClassifier(pattern_manager)
    
    # Test cases
    test_titles = [
        "APAC Personal Protective Equipment Market Report",
        "Veterinary Vaccine Market for Livestock Analysis", 
        "AI Solutions Market in Healthcare Outlook"
    ]
    
    for title in test_titles:
        result = classifier.classify(title)
        logger.info(f"Title: {title}")
        logger.info(f"  Market Type: {result.market_type}")
        logger.info(f"  Confidence: {result.confidence}")
        logger.info(f"  Pattern: {result.matched_pattern}")
        print()

def test_date_extractor():
    """Test Script 02: Date Extractor"""
    logger = setup_logging()
    logger.info("Testing Script 02: Enhanced Date Extractor")
    
    # Import pattern library manager
    pattern_manager_module = import_module_dynamically(
        "pattern_manager", 
        os.path.join(experiments_dir, '00b_pattern_library_manager_v1.py')
    )
    PatternLibraryManager = pattern_manager_module.PatternLibraryManager
    
    # Import date extractor
    date_extractor_module = import_module_dynamically(
        "date_extractor",
        os.path.join(experiments_dir, '02_date_extractor_v1.py')
    )
    EnhancedDateExtractor = date_extractor_module.EnhancedDateExtractor
    
    # Initialize
    pattern_manager = PatternLibraryManager()
    extractor = EnhancedDateExtractor(pattern_manager)
    
    # Test cases
    test_titles = [
        "APAC Personal Protective Equipment Market Report, 2030",
        "Veterinary Vaccine Market for Livestock Analysis, 2025-2030", 
        "AI Solutions Market in Healthcare Outlook [2024]",
        "Global Market Study 2025",
        "Market Analysis without dates"
    ]
    
    for title in test_titles:
        result = extractor.extract(title)
        logger.info(f"Title: {title}")
        logger.info(f"  Extracted Date: {result.extracted_date_range}")
        logger.info(f"  Cleaned Title: {result.cleaned_title}")
        logger.info(f"  Format: {result.format_type}")
        logger.info(f"  Status: {result.categorization}")
        logger.info(f"  Confidence: {result.confidence}")
        print()

def test_report_type_extractor():
    """Test Script 03: Report Type Extractor"""
    logger = setup_logging()
    logger.info("Testing Script 03: Market-Aware Report Type Extractor")
    
    # Import pattern library manager
    pattern_manager_module = import_module_dynamically(
        "pattern_manager", 
        os.path.join(experiments_dir, '00b_pattern_library_manager_v1.py')
    )
    PatternLibraryManager = pattern_manager_module.PatternLibraryManager
    
    # Import report extractor
    report_extractor_module = import_module_dynamically(
        "report_extractor", 
        os.path.join(experiments_dir, '03_report_type_extractor_v2.py')
    )
    MarketAwareReportTypeExtractor = report_extractor_module.MarketAwareReportTypeExtractor
    
    # Initialize
    pattern_manager = PatternLibraryManager()
    extractor = MarketAwareReportTypeExtractor(pattern_manager)
    
    # Test cases (titles after date removal)
    test_cases = [
        {
            "title": "APAC Personal Protective Equipment Market Report",
            "market_type": "standard"
        },
        {
            "title": "Veterinary Vaccine Market for Livestock Analysis", 
            "market_type": "market_for"
        },
        {
            "title": "AI Solutions Market in Healthcare Outlook",
            "market_type": "market_in"
        }
    ]
    
    for case in test_cases:
        result = extractor.extract(case["title"], case["market_type"])
        logger.info(f"Title: {case['title']}")
        logger.info(f"  Market Type: {case['market_type']}")
        logger.info(f"  Extracted Report Type: {result.final_report_type}")
        logger.info(f"  Processing Workflow: {result.processing_workflow}")
        logger.info(f"  Pipeline Forward Title: {result.title}")
        logger.info(f"  Confidence: {result.confidence}")
        print()

def main():
    """Run all individual script tests."""
    logger = setup_logging()
    logger.info("="*60)
    logger.info("Individual Script Validation Tests")
    logger.info("="*60)
    
    try:
        test_market_classifier()
        print("="*40)
        test_date_extractor()
        print("="*40)
        test_report_type_extractor()
        
        logger.info("✅ All individual script tests completed!")
        
    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()