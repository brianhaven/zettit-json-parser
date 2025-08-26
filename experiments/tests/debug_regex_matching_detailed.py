#!/usr/bin/env python3

"""
Debug the regex matching logic in detail to understand why patterns aren't matching.
"""

import sys
import os
import re
import logging
from pymongo import MongoClient
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    return logging.getLogger(__name__)

def test_specific_patterns():
    """Test specific failing patterns with their exact database patterns."""
    logger = setup_logging()
    
    logger.info("="*60)
    logger.info("DETAILED REGEX MATCHING DEBUG")
    logger.info("="*60)
    
    # Get database connection
    client = MongoClient(os.getenv('MONGODB_URI'))
    db = client['deathstar']
    
    # Failing test cases from our comprehensive test
    failing_cases = [
        {
            "title": "Ammunition Market Size, Share And Growth Report",
            "expected": "Market Size, Share And Growth Report"
        },
        {
            "title": "Antimicrobial Medical Textiles Market, Industry Report", 
            "expected": "Market, Industry Report"
        },
        {
            "title": "APAC & Middle East Personal Protective Equipment Market Report",
            "expected": "Market Report" 
        },
        {
            "title": "Automotive Timing Belt Market Size And Share Report",
            "expected": "Market Size And Share Report"
        },
        {
            "title": "Clean-In-Place Market Size, Share & Growth Report",
            "expected": "Market Size, Share & Growth Report"
        }
    ]
    
    for case in failing_cases:
        title = case["title"]
        expected = case["expected"]
        
        logger.info(f"\n--- TESTING: {title} ---")
        logger.info(f"Expected Pattern: {expected}")
        
        # Get relevant patterns from database
        search_terms = expected.replace("Market ", "").split()
        regex_query = ".*".join([re.escape(term) for term in search_terms])
        
        patterns = list(db.pattern_libraries.find({
            "type": "report_type",
            "active": True,
            "term": {"$regex": regex_query, "$options": "i"}
        }))
        
        logger.info(f"Found {len(patterns)} potential matching patterns:")
        
        found_match = False
        for pattern_doc in patterns:
            pattern_text = pattern_doc.get('pattern', '')
            term = pattern_doc.get('term', '')
            
            logger.info(f"\n  Testing pattern: {term}")
            logger.info(f"  Regex: {pattern_text}")
            
            try:
                # Test the regex pattern
                match = re.search(pattern_text, title, re.IGNORECASE)
                if match:
                    logger.info(f"  ✅ MATCH! Groups: {match.groups()}")
                    found_match = True
                    break
                else:
                    logger.info(f"  ❌ No match")
                    
                    # Debug why it didn't match by testing parts
                    logger.info("    Debugging pattern parts:")
                    
                    # Test if basic Market word matches
                    if "Market" in title:
                        logger.info("    ✓ Contains 'Market'")
                    else:
                        logger.info("    ✗ Missing 'Market'")
                    
                    # Test word boundaries
                    if re.search(r'\bMarket\b', title, re.IGNORECASE):
                        logger.info("    ✓ 'Market' word boundary matches")
                    else:
                        logger.info("    ✗ 'Market' word boundary fails")
                        
            except Exception as e:
                logger.error(f"  ❌ REGEX ERROR: {str(e)}")
        
        if not found_match:
            logger.error(f"  🚨 NO PATTERNS MATCHED for: {title}")
            
    client.close()

def test_working_patterns():
    """Test patterns that we know are working to compare.""" 
    logger = setup_logging()
    
    logger.info("\n" + "="*60)
    logger.info("TESTING WORKING PATTERNS FOR COMPARISON")
    logger.info("="*60)
    
    # Get database connection
    client = MongoClient(os.getenv('MONGODB_URI'))
    db = client['deathstar']
    
    # Known working cases
    working_cases = [
        "Glass Fiber Reinforced Gypsum Market Size Report",
        "HDPE And LLDPE Geomembrane Market Size Report"
    ]
    
    for title in working_cases:
        logger.info(f"\n--- WORKING CASE: {title} ---")
        
        # Test against Market Size Report pattern specifically
        pattern_doc = db.pattern_libraries.find_one({
            "type": "report_type",
            "active": True,
            "term": "Market Size Report Terminal"
        })
        
        if pattern_doc:
            pattern_text = pattern_doc.get('pattern', '')
            logger.info(f"Pattern: {pattern_text}")
            
            match = re.search(pattern_text, title, re.IGNORECASE)
            if match:
                logger.info(f"✅ MATCH! Groups: {match.groups()}")
            else:
                logger.info(f"❌ No match - this should be working!")
    
    client.close()

def main():
    """Main debug function."""
    test_specific_patterns()
    test_working_patterns()

if __name__ == "__main__":
    main()