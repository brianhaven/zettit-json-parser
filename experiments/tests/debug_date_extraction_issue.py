#!/usr/bin/env python3

"""
Debug the date extraction issue specifically.
"""

import sys
import os
import logging
import importlib.util
from pymongo import MongoClient
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add the experiments directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import components
experiments_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Import pattern library manager
pattern_manager_path = os.path.join(experiments_dir, '00b_pattern_library_manager_v1.py')
spec = importlib.util.spec_from_file_location("pattern_manager", pattern_manager_path)
pattern_manager = importlib.util.module_from_spec(spec)
spec.loader.exec_module(pattern_manager)
PatternLibraryManager = pattern_manager.PatternLibraryManager

# Import date extractor
date_extractor_path = os.path.join(experiments_dir, '02_date_extractor_v1.py')
spec = importlib.util.spec_from_file_location("date_extractor", date_extractor_path)
date_extractor_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(date_extractor_module)
DateExtractor = date_extractor_module.EnhancedDateExtractor

def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    return logging.getLogger(__name__)

def main():
    """Debug date extraction."""
    logger = setup_logging()
    
    logger.info("="*60)
    logger.info("DEBUGGING DATE EXTRACTION ISSUE")
    logger.info("="*60)
    
    try:
        # Initialize components
        pattern_manager = PatternLibraryManager()
        date_extractor = DateExtractor(pattern_manager)
        
        # Test titles
        test_titles = [
            "APAC & Middle East Personal Protective Equipment Market Report, 2030",
            "Automotive Steel Wheels Market Size & Share Report, 2030",
            "Electric Submersible Pumps Market Size, Share Report 2030"
        ]
        
        for title in test_titles:
            logger.info(f"\n--- Testing: {title} ---")
            
            result = date_extractor.extract(title)
            
            logger.info(f"Original: {title}")
            logger.info(f"Extracted Date: {result.extracted_date_range}")
            logger.info(f"Categorization: {result.categorization}")
            logger.info(f"Title Without Date: {result.cleaned_title}")
            logger.info(f"Confidence: {result.confidence}")
            logger.info(f"Matched Pattern: {result.matched_pattern}")
            
            # Check if date was actually removed
            has_date_in_original = any(str(year) in title for year in range(2020, 2041))
            has_date_in_result = any(str(year) in result.cleaned_title for year in range(2020, 2041))
            
            if has_date_in_original and has_date_in_result:
                logger.error(f"❌ DATE NOT REMOVED! Date still present in result")
            elif has_date_in_original and not has_date_in_result:
                logger.info(f"✅ DATE PROPERLY REMOVED")
            else:
                logger.info(f"ℹ️  NO DATE IN ORIGINAL TITLE")
        
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()