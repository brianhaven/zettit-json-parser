#!/usr/bin/env python3

"""
Simplified Test for Topic Extractor v1.0
Tests topic extraction with mock extracted_elements data to validate core functionality.
Focuses on systematic removal approach without full pipeline dependencies.
"""

import sys
import os
import logging

# Add parent directory to path to import numbered modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import Topic Extractor using importlib
import importlib.util
spec = importlib.util.spec_from_file_location("topic_extractor", "../05_topic_extractor_v1.py")
topic_extractor_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(topic_extractor_module)

TopicExtractor = topic_extractor_module.TopicExtractor
TopicExtractionFormat = topic_extractor_module.TopicExtractionFormat

# Configure logging for tests
logging.basicConfig(level=logging.WARNING)

def test_topic_extractor_core():
    """Test core TopicExtractor functionality with mock extracted_elements."""
    
    print("Simplified Topic Extractor Tests")
    print("=" * 50)
    
    # Initialize extractor (without pattern library manager for simplified testing)
    extractor = TopicExtractor()
    test_results = []
    
    try:
        # Test 1: Standard market pattern processing
        print("\n1. Testing Standard Market patterns...")
        standard_test_cases = [
            {
                'title': "Global Artificial Intelligence Market Size & Share Report, 2030",
                'extracted_elements': {
                    'market_term_type': 'standard',
                    'extracted_forecast_date_range': '2030',
                    'extracted_report_type': 'Market Size & Share Report',
                    'extracted_regions': ['Global']
                },
                'expected_topic': 'Artificial Intelligence'
            },
            {
                'title': "APAC Personal Protective Equipment Market Analysis", 
                'extracted_elements': {
                    'market_term_type': 'standard',
                    'extracted_forecast_date_range': None,
                    'extracted_report_type': 'Market Analysis',
                    'extracted_regions': ['APAC']
                },
                'expected_topic': 'Personal Protective Equipment'
            },
            {
                'title': "5G Technology Market Report, 2025-2030",
                'extracted_elements': {
                    'market_term_type': 'standard', 
                    'extracted_forecast_date_range': '2025-2030',
                    'extracted_report_type': 'Market Report',
                    'extracted_regions': []
                },
                'expected_topic': '5G Technology'
            }
        ]
        
        for test_case in standard_test_cases:
            result = extractor.extract(test_case['title'], test_case['extracted_elements'])
            
            print(f"   Title: {test_case['title'][:60]}...")
            print(f"   Expected: '{test_case['expected_topic']}'")
            print(f"   Extracted: '{result.extracted_topic}'")
            print(f"   Normalized: '{result.normalized_topic_name}'")
            print(f"   Confidence: {result.confidence:.3f}")
            print(f"   Format: {result.format_type.value}")
            print()
            
            # Validate results
            assert result.extracted_topic is not None, f"No topic extracted from: {test_case['title']}"
            assert result.extracted_topic == test_case['expected_topic'], f"Expected '{test_case['expected_topic']}', got '{result.extracted_topic}'"
            assert result.format_type == TopicExtractionFormat.STANDARD_MARKET
            assert result.confidence > 0.5, f"Low confidence: {result.confidence}"
        
        test_results.append("✅ Standard Market pattern processing")
        
        # Test 2: Market for pattern processing
        print("2. Testing Market For patterns...")
        market_for_test_cases = [
            {
                'title': "Global Market for Advanced Materials in Aerospace, 2030",
                'extracted_elements': {
                    'market_term_type': 'market_for',
                    'extracted_forecast_date_range': '2030',
                    'extracted_report_type': None,
                    'extracted_regions': ['Global']
                },
                'expected_topic_contains': 'Advanced Materials'
            },
            {
                'title': "Market for Electric Vehicles in Europe",
                'extracted_elements': {
                    'market_term_type': 'market_for',
                    'extracted_forecast_date_range': None,
                    'extracted_report_type': None,
                    'extracted_regions': ['Europe']
                },
                'expected_topic_contains': 'Electric Vehicles'
            }
        ]
        
        for test_case in market_for_test_cases:
            result = extractor.extract(test_case['title'], test_case['extracted_elements'])
            
            print(f"   Title: {test_case['title']}")
            print(f"   Extracted: '{result.extracted_topic}'")
            print(f"   Normalized: '{result.normalized_topic_name}'")
            print(f"   Confidence: {result.confidence:.3f}")
            print(f"   Format: {result.format_type.value}")
            print()
            
            # Validate results
            assert result.extracted_topic is not None, f"No topic extracted from: {test_case['title']}"
            assert test_case['expected_topic_contains'] in result.extracted_topic, f"Expected '{test_case['expected_topic_contains']}' in topic"
            assert result.format_type == TopicExtractionFormat.MARKET_FOR
        
        test_results.append("✅ Market For pattern processing")
        
        # Test 3: Market in pattern processing
        print("3. Testing Market In patterns...")
        market_in_test_cases = [
            {
                'title': "Pharmaceutical Market in North America Analysis",
                'extracted_elements': {
                    'market_term_type': 'market_in',
                    'extracted_forecast_date_range': None,
                    'extracted_report_type': 'Analysis',
                    'extracted_regions': ['North America']
                },
                'expected_topic': 'Pharmaceutical'
            },
            {
                'title': "Technology Market in Asia Pacific, 2025-2030",
                'extracted_elements': {
                    'market_term_type': 'market_in',
                    'extracted_forecast_date_range': '2025-2030',
                    'extracted_report_type': None,
                    'extracted_regions': ['Asia Pacific']
                },
                'expected_topic': 'Technology'
            }
        ]
        
        for test_case in market_in_test_cases:
            result = extractor.extract(test_case['title'], test_case['extracted_elements'])
            
            print(f"   Title: {test_case['title']}")
            print(f"   Expected: '{test_case['expected_topic']}'")
            print(f"   Extracted: '{result.extracted_topic}'")
            print(f"   Confidence: {result.confidence:.3f}")
            print()
            
            # Validate results
            assert result.extracted_topic is not None, f"No topic extracted from: {test_case['title']}"
            assert result.format_type == TopicExtractionFormat.MARKET_IN
        
        test_results.append("✅ Market In pattern processing")
        
        # Test 4: Systematic removal validation
        print("4. Testing Systematic Removal approach...")
        removal_test_cases = [
            {
                'title': "North America & Europe 5G Technology Market Size Report, 2030",
                'extracted_elements': {
                    'market_term_type': 'standard',
                    'extracted_forecast_date_range': '2030',
                    'extracted_report_type': 'Market Size Report',
                    'extracted_regions': ['North America', 'Europe']
                },
                'description': "Should remove regions, date, and report type, preserve 5G technical compound"
            },
            {
                'title': "Global IoT & AI Solutions Market Analysis, 2025-2028",
                'extracted_elements': {
                    'market_term_type': 'standard',
                    'extracted_forecast_date_range': '2025-2028',
                    'extracted_report_type': 'Market Analysis',
                    'extracted_regions': ['Global']
                },
                'description': "Should preserve technical compounds IoT & AI"
            }
        ]
        
        for test_case in removal_test_cases:
            result = extractor.extract(test_case['title'], test_case['extracted_elements'])
            
            print(f"   Title: {test_case['title']}")
            print(f"   Removed Elements:")
            print(f"     Date: {test_case['extracted_elements']['extracted_forecast_date_range']}")
            print(f"     Report: {test_case['extracted_elements']['extracted_report_type']}")
            print(f"     Regions: {test_case['extracted_elements']['extracted_regions']}")
            print(f"   Final Topic: '{result.extracted_topic}'")
            print(f"   Technical Compounds: {result.technical_compounds_preserved}")
            print(f"   Raw Remainder: '{result.raw_remainder_before_processing}'")
            print(f"   Description: {test_case['description']}")
            print()
            
            # Validate systematic removal worked
            assert result.extracted_topic is not None, f"Systematic removal failed for: {test_case['title']}"
            
            # Verify extracted elements don't appear in final topic
            extracted_elements = test_case['extracted_elements']
            if extracted_elements['extracted_forecast_date_range']:
                assert extracted_elements['extracted_forecast_date_range'] not in result.extracted_topic, "Date not properly removed"
            
            if extracted_elements['extracted_regions']:
                for region in extracted_elements['extracted_regions']:
                    assert region not in result.extracted_topic, f"Region '{region}' not properly removed from topic"
        
        test_results.append("✅ Systematic Removal validation")
        
        # Test 5: Topic normalization
        print("5. Testing Topic Normalization...")
        normalization_cases = [
            ("Artificial Intelligence", "artificial-intelligence"),
            ("5G Technology", "5g-technology"),
            ("Personal Protective Equipment", "personal-protective-equipment"),
            ("IoT & AI Solutions", "iot-ai-solutions"),
            ("Advanced Materials", "advanced-materials")
        ]
        
        for original, expected_normalized in normalization_cases:
            normalized = extractor.normalize_topic(original)
            print(f"   '{original}' → '{normalized}'")
            assert normalized == expected_normalized, f"Normalization failed: expected '{expected_normalized}', got '{normalized}'"
        
        test_results.append("✅ Topic Normalization")
        
        # Test 6: Technical compound preservation
        print("6. Testing Technical Compound Preservation...")
        technical_test_cases = [
            ("5G Technology Solutions", ["5G"]),
            ("IoT & AI Market", ["IoT", "AI"]),
            ("4K Video Streaming", ["4K"]),
            ("API Management Tools", ["API"])
        ]
        
        for text, expected_compounds in technical_test_cases:
            found_compounds = extractor._find_technical_compounds(text)
            print(f"   '{text}' → {found_compounds}")
            
            for expected in expected_compounds:
                assert expected in found_compounds, f"Technical compound '{expected}' not found in '{text}'"
        
        test_results.append("✅ Technical Compound Preservation")
        
        # Test 7: Confidence scoring
        print("7. Testing Confidence Scoring...")
        confidence_test_cases = [
            {
                'title': "Global Artificial Intelligence Market Report, 2030",
                'extracted_elements': {
                    'market_term_type': 'standard',
                    'extracted_forecast_date_range': '2030',
                    'extracted_report_type': 'Market Report',
                    'extracted_regions': ['Global']
                },
                'min_confidence': 0.7
            },
            {
                'title': "X Market",  # Very minimal topic
                'extracted_elements': {
                    'market_term_type': 'standard',
                    'extracted_forecast_date_range': None,
                    'extracted_report_type': None,
                    'extracted_regions': []
                },
                'min_confidence': 0.3  # Lower confidence for minimal topics
            }
        ]
        
        for test_case in confidence_test_cases:
            result = extractor.extract(test_case['title'], test_case['extracted_elements'])
            
            print(f"   Title: {test_case['title']}")
            print(f"   Topic: '{result.extracted_topic}'")
            print(f"   Confidence: {result.confidence:.3f}")
            print(f"   Min Expected: {test_case['min_confidence']:.3f}")
            print()
            
            assert result.confidence >= test_case['min_confidence'], f"Confidence {result.confidence} below minimum {test_case['min_confidence']}"
        
        test_results.append("✅ Confidence Scoring")
        
        # Get final statistics
        print("8. Processing Statistics...")
        stats = extractor.get_extraction_statistics()
        confidence_metrics = extractor.get_confidence()
        
        print(f"   Total Processed: {stats.total_processed}")
        print(f"   Successful Extractions: {stats.successful_extractions}")
        print(f"   Success Rate: {stats.success_rate:.1%}")
        print(f"   Overall Confidence: {confidence_metrics['overall_confidence']:.1%}")
        print()
        
        assert stats.success_rate > 0.85, f"Success rate {stats.success_rate:.1%} too low"
        
        test_results.append("✅ Statistics and Performance")
        
        # Summary
        print("\n" + "=" * 50)
        print("TEST SUMMARY:")
        for result in test_results:
            print(f"  {result}")
        
        print(f"\n✅ All {len(test_results)} test suites passed!")
        print("✅ Topic Extractor core functionality validated!")
        print("✅ Systematic removal approach working correctly!")
        print("✅ Ready for pipeline integration!")
        
        return True
        
    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
        return False
        
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_edge_cases():
    """Test edge cases and error handling."""
    
    print("\n" + "=" * 50)
    print("EDGE CASE TESTING")
    print("=" * 50)
    
    extractor = TopicExtractor()
    
    try:
        # Test empty/null inputs
        print("1. Testing Empty/Null Inputs...")
        
        empty_cases = [
            ("", {}),
            ("   ", {}),
            (None, {}),
        ]
        
        for title, extracted_elements in empty_cases:
            try:
                if title is None:
                    continue  # Skip None test for now
                result = extractor.extract(title, extracted_elements)
                print(f"   Empty input result: {result.extracted_topic}")
            except Exception as e:
                print(f"   Empty input handled: {type(e).__name__}")
        
        # Test malformed titles
        print("\n2. Testing Malformed Titles...")
        
        malformed_cases = [
            ("Market", {'market_term_type': 'standard'}),
            ("Global Market", {'market_term_type': 'standard'}),
            ("Just some random text", {'market_term_type': 'standard'}),
        ]
        
        for title, extracted_elements in malformed_cases:
            result = extractor.extract(title, extracted_elements)
            print(f"   '{title}' → '{result.extracted_topic}' (confidence: {result.confidence:.3f})")
        
        print("\n✅ Edge case testing completed")
        return True
        
    except Exception as e:
        print(f"\n❌ Edge case testing failed: {e}")
        return False

if __name__ == "__main__":
    print("Starting Simplified Topic Extractor Test Suite...")
    print("=" * 60)
    
    # Run core functionality tests
    core_tests_passed = test_topic_extractor_core()
    
    # Run edge case tests
    edge_tests_passed = test_edge_cases()
    
    # Final results
    print("\n" + "=" * 60)
    print("FINAL TEST RESULTS:")
    print("=" * 60)
    
    if core_tests_passed and edge_tests_passed:
        print("🎉 ALL TESTS PASSED!")
        print("✅ Topic Extractor core functionality validated")
        print("✅ Systematic removal approach confirmed")
        print("✅ Ready for full pipeline integration")
        sys.exit(0)
    else:
        print("❌ SOME TESTS FAILED")
        if not core_tests_passed:
            print("❌ Core functionality tests failed")
        if not edge_tests_passed:
            print("❌ Edge case tests failed")
        sys.exit(1)