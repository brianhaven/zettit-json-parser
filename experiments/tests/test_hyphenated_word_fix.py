#!/usr/bin/env python3
"""
Quick test to validate hyphenated word fix in Script 04 v2.
Tests the specific "De-identified" → "Delaware" false positive issue.
"""

import os
import sys
import logging
import importlib.util
from dotenv import load_dotenv

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

load_dotenv()

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def import_module_from_path(module_name: str, file_path: str):
    """Import a module from a file path."""
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

def test_hyphenated_word_fix():
    """Test that hyphenated words don't trigger false geographic matches."""
    logger.info("Testing hyphenated word fix in Script 04 v2")
    
    # Import required modules
    parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    # Import PatternLibraryManager
    pattern_manager = import_module_from_path("pattern_library_manager",
                                            os.path.join(parent_dir, "00b_pattern_library_manager_v1.py"))
    
    # Import Script 04 v2
    script04 = import_module_from_path("geographic_entity_detector_v2",
                                     os.path.join(parent_dir, "04_geographic_entity_detector_v2.py"))
    
    # Initialize components
    pattern_lib_manager = pattern_manager.PatternLibraryManager(os.getenv('MONGODB_URI'))
    geo_detector = script04.GeographicEntityDetector(pattern_lib_manager)
    
    # Test cases for hyphenated words
    test_cases = [
        {
            'text': 'De-identified Health Data Market Size, Industry Report, 2030',
            'expected_regions': [],  # Should NOT detect Delaware
            'description': 'De-identified should not match Delaware'
        },
        {
            'text': 'Co-operative Banking Market Analysis, 2030',
            'expected_regions': [],  # Should NOT detect Colorado
            'description': 'Co-operative should not match Colorado'
        },
        {
            'text': 'Re-engineering Services Market, 2025-2030',
            'expected_regions': [],  # Should NOT detect any "Re-" regions
            'description': 'Re-engineering should not match geographic regions'
        },
        {
            'text': 'Anti-bacterial Coatings Market Report, 2030',
            'expected_regions': [],  # Should NOT detect Antigua
            'description': 'Anti-bacterial should not match Antigua'
        },
        {
            'text': 'Delaware State Healthcare Market, 2030',
            'expected_regions': ['Delaware'],  # SHOULD detect Delaware when not hyphenated
            'description': 'Delaware should be detected when not part of hyphenated word'
        }
    ]
    
    results = []
    
    for i, test_case in enumerate(test_cases, 1):
        logger.info(f"\n--- Test Case {i}: {test_case['description']} ---")
        logger.info(f"Input: {test_case['text']}")
        
        try:
            result = geo_detector.extract_geographic_entities(test_case['text'])
            
            # Check if results match expectations
            success = result.extracted_regions == test_case['expected_regions']
            
            test_result = {
                'test_case': i,
                'description': test_case['description'],
                'input_text': test_case['text'],
                'expected_regions': test_case['expected_regions'],
                'actual_regions': result.extracted_regions,
                'success': success,
                'remaining_text': result.remaining_text,
                'confidence': result.confidence
            }
            
            results.append(test_result)
            
            # Log results
            status = "✅ PASS" if success else "❌ FAIL"
            logger.info(f"Expected: {test_case['expected_regions']}")
            logger.info(f"Actual: {result.extracted_regions}")
            logger.info(f"Status: {status}")
            logger.info(f"Remaining: {result.remaining_text}")
            
        except Exception as e:
            logger.error(f"Error in test case {i}: {e}")
            results.append({
                'test_case': i,
                'description': test_case['description'],
                'input_text': test_case['text'],
                'expected_regions': test_case['expected_regions'],
                'actual_regions': [],
                'success': False,
                'error': str(e)
            })
    
    # Summary
    passed = sum(1 for r in results if r['success'])
    total = len(results)
    
    logger.info(f"\n=== HYPHENATED WORD FIX TEST SUMMARY ===")
    logger.info(f"Tests Passed: {passed}/{total}")
    logger.info(f"Success Rate: {passed/total*100:.1f}%")
    
    if passed == total:
        logger.info("🎉 All hyphenated word tests PASSED! Fix is working correctly.")
    else:
        logger.warning(f"⚠️ {total-passed} tests failed. Review the fix implementation.")
        for result in results:
            if not result['success']:
                logger.warning(f"  Failed: {result['description']}")
                logger.warning(f"    Expected: {result['expected_regions']}")
                logger.warning(f"    Got: {result['actual_regions']}")
    
    pattern_lib_manager.close_connection()
    return passed == total

if __name__ == "__main__":
    success = test_hyphenated_word_fix()
    sys.exit(0 if success else 1)