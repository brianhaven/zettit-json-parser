#!/usr/bin/env python3

"""
Pattern Enhancement Verification Test
Tests specific edge cases that should now work with enhanced patterns.
"""

import os
import sys
import logging
from dotenv import load_dotenv
import importlib.util

# Load environment variables
load_dotenv()

# Dynamic import for date extractor
try:
    date_extractor_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '02_date_extractor_v1.py')
    spec = importlib.util.spec_from_file_location("date_extractor_v1", date_extractor_path)
    date_extractor_module = importlib.util.module_from_spec(spec)
    sys.modules["date_extractor_v1"] = date_extractor_module
    spec.loader.exec_module(date_extractor_module)
    DateExtractor = date_extractor_module.DateExtractor
except Exception as e:
    raise ImportError(f"Could not import DateExtractor: {e}") from e

# Dynamic import for pattern library manager
try:
    pattern_manager_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '00b_pattern_library_manager_v1.py')
    spec = importlib.util.spec_from_file_location("pattern_library_manager_v1", pattern_manager_path)
    pattern_module = importlib.util.module_from_spec(spec)
    sys.modules["pattern_library_manager_v1"] = pattern_module
    spec.loader.exec_module(pattern_module)
    PatternLibraryManager = pattern_module.PatternLibraryManager
    PatternType = pattern_module.PatternType
except Exception as e:
    raise ImportError(f"Could not import PatternLibraryManager: {e}") from e

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_pattern_enhancement():
    """Test specific edge cases that should now work with enhanced patterns."""
    
    logger.info("Testing pattern enhancement with edge cases...")
    
    # Initialize components
    pattern_manager = PatternLibraryManager()
    date_extractor = DateExtractor(pattern_manager)
    
    # Test cases that previously failed (from edge_cases.json)
    test_cases = [
        # Standalone ranges without commas (main gap identified)
        "U.S. Heavy Movable Bridges Market Size, Industry Report, 2019-2025",
        "Global Software Market Analysis 2020-2030",
        "Healthcare Technology Market 2022-2028",
        "Renewable Energy Market Study 2023-2030",
        
        # Fiscal year patterns
        "Government Spending Analysis FY 2025",
        "Healthcare Budget Report Fiscal Year 2026",
        
        # Quarter patterns 
        "Market Performance Q1 2025",
        "Financial Analysis Quarter 3 2024",
        
        # Standalone year patterns
        "AI Technology Market 2025",
        "Blockchain Market Report 2030",
        "Global Economy Analysis 2026",
        
        # Bracket patterns
        "Technology Market [2025]",
        "Financial Report [2023 Analysis]",
        
        # Edge case ranges
        "Market Study 2020 to 2030",
        "Industry Analysis 2021 through 2027"
    ]
    
    results = {
        'successful': 0,
        'failed': 0,
        'details': []
    }
    
    logger.info(f"Testing {len(test_cases)} enhanced pattern cases...")
    
    for i, title in enumerate(test_cases, 1):
        try:
            result = date_extractor.extract(title)
            
            if result.extracted_date_range:
                results['successful'] += 1
                status = "✅ SUCCESS"
                logger.info(f"{i:2d}. {status}: '{title}' → '{result.extracted_date_range}' ({result.format_type})")
            else:
                results['failed'] += 1
                status = "❌ FAILED"
                logger.warning(f"{i:2d}. {status}: '{title}' → No date found")
                
            results['details'].append({
                'title': title,
                'extracted_date': result.extracted_date_range,
                'format_type': str(result.format_type),
                'confidence': result.confidence,
                'success': bool(result.extracted_date_range)
            })
            
        except Exception as e:
            results['failed'] += 1
            logger.error(f"{i:2d}. ERROR: '{title}' → {e}")
            results['details'].append({
                'title': title,
                'extracted_date': None,
                'format_type': 'error',
                'confidence': 0.0,
                'success': False,
                'error': str(e)
            })
    
    # Calculate improvement metrics
    total_cases = len(test_cases)
    success_rate = (results['successful'] / total_cases) * 100
    
    logger.info("Pattern Enhancement Test Results:")
    logger.info(f"  - Total test cases: {total_cases}")
    logger.info(f"  - Successful extractions: {results['successful']}")
    logger.info(f"  - Failed extractions: {results['failed']}")
    logger.info(f"  - Success rate: {success_rate:.1f}%")
    
    # Check total pattern count in database
    all_date_patterns = pattern_manager.get_patterns(PatternType.DATE_PATTERN)
    logger.info(f"  - Total date patterns in database: {len(all_date_patterns)}")
    
    pattern_manager.close_connection()
    
    print(f"\n✅ Pattern Enhancement Test Complete!")
    print(f"Success Rate: {success_rate:.1f}% ({results['successful']}/{total_cases})")
    
    if success_rate >= 80:
        print("🎯 Pattern enhancement appears successful!")
        return True
    else:
        print("⚠️  Pattern enhancement needs more work.")
        return False

if __name__ == "__main__":
    test_pattern_enhancement()