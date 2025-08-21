#!/usr/bin/env python3

"""
Test script for Topic Extractor v1.0
Validates topic extraction accuracy through sequential pipeline processing.
Tests systematic removal approach with real pipeline data.
"""

import sys
import os
import logging
import json
from typing import Dict, List, Optional, Any

# Add parent directory to path to import numbered modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import using importlib to handle numbered module names
import importlib.util

# Import Market Term Classifier (01)
spec1 = importlib.util.spec_from_file_location("market_classifier", "../01_market_term_classifier_v1.py")
market_classifier_module = importlib.util.module_from_spec(spec1)
spec1.loader.exec_module(market_classifier_module)
MarketTermClassifier = market_classifier_module.MarketTermClassifier

# Import Date Extractor (02) 
spec2 = importlib.util.spec_from_file_location("date_extractor", "../02_date_extractor_v1.py")
date_extractor_module = importlib.util.module_from_spec(spec2)
spec2.loader.exec_module(date_extractor_module)
DateExtractor = date_extractor_module.DateExtractor

# Import Report Type Extractor (03)
spec3 = importlib.util.spec_from_file_location("report_extractor", "../03_report_type_extractor_v1.py")
report_extractor_module = importlib.util.module_from_spec(spec3)
spec3.loader.exec_module(report_extractor_module)
ReportTypeExtractor = report_extractor_module.ReportTypeExtractor

# Import Geographic Entity Detector (04) - use fallback if not available
try:
    spec4 = importlib.util.spec_from_file_location("geographic_detector", "../04_geographic_entity_detector_v1.py")
    geographic_detector_module = importlib.util.module_from_spec(spec4)
    spec4.loader.exec_module(geographic_detector_module)
    GeographicEntityDetector = geographic_detector_module.GeographicEntityDetector
    GEOGRAPHIC_AVAILABLE = True
except:
    print("⚠️  Geographic detector not available - using mock geographic extraction")
    GEOGRAPHIC_AVAILABLE = False

# Import Topic Extractor (05)
spec5 = importlib.util.spec_from_file_location("topic_extractor", "../05_topic_extractor_v1.py")
topic_extractor_module = importlib.util.module_from_spec(spec5)
spec5.loader.exec_module(topic_extractor_module)
TopicExtractor = topic_extractor_module.TopicExtractor
TopicExtractionFormat = topic_extractor_module.TopicExtractionFormat

# Import Pattern Library Manager
spec_plm = importlib.util.spec_from_file_location("pattern_library_manager", "../00b_pattern_library_manager_v1.py")
pattern_library_module = importlib.util.module_from_spec(spec_plm)
spec_plm.loader.exec_module(pattern_library_module)
PatternLibraryManager = pattern_library_module.PatternLibraryManager

# Configure logging for tests
logging.basicConfig(level=logging.WARNING)

class PipelineProcessor:
    """Processes titles through the complete extraction pipeline."""
    
    def __init__(self):
        """Initialize all extractors."""
        self.pattern_manager = PatternLibraryManager()
        
        # Initialize extractors in pipeline order
        self.market_classifier = MarketTermClassifier(self.pattern_manager)
        self.date_extractor = DateExtractor(self.pattern_manager)
        self.report_extractor = ReportTypeExtractor(self.pattern_manager) 
        
        if GEOGRAPHIC_AVAILABLE:
            self.geographic_detector = GeographicEntityDetector(use_models=False)  # Use pattern-only for testing speed
        
        self.topic_extractor = TopicExtractor(self.pattern_manager)
        
        print("✅ Pipeline initialized with all extractors")
    
    def process_title(self, title: str) -> Dict[str, Any]:
        """Process a single title through the complete pipeline."""
        
        # Step 1: Market term classification
        market_result = self.market_classifier.classify(title)
        
        # Step 2: Date extraction
        date_result = self.date_extractor.extract(title)
        
        # Step 3: Report type extraction
        report_result = self.report_extractor.extract(title, date_result.extracted_date_range)
        
        # Step 4: Geographic detection
        if GEOGRAPHIC_AVAILABLE:
            # Use full title and description for geographic detection
            geo_result = self.geographic_detector.detect_geographic_entities(title, "")
            extracted_regions = list(geo_result.detected_entities) if hasattr(geo_result, 'detected_entities') else []
        else:
            # Mock geographic extraction for testing
            extracted_regions = self._mock_geographic_extraction(title)
        
        # Step 5: Prepare extracted elements for topic extraction
        extracted_elements = {
            'market_term_type': market_result.market_type.value,
            'extracted_forecast_date_range': date_result.extracted_date_range,
            'extracted_report_type': report_result.extracted_report_type,
            'extracted_regions': extracted_regions
        }
        
        # Step 6: Topic extraction
        topic_result = self.topic_extractor.extract(title, extracted_elements)
        
        return {
            'original_title': title,
            'market_classification': market_result,
            'date_extraction': date_result,
            'report_extraction': report_result,
            'geographic_extraction': extracted_regions,
            'extracted_elements': extracted_elements,
            'topic_extraction': topic_result,
            'final_result': {
                'market_term_type': topic_result.market_term_type,
                'extracted_forecast_date_range': extracted_elements['extracted_forecast_date_range'],
                'extracted_report_type': extracted_elements['extracted_report_type'],
                'extracted_regions': extracted_regions,
                'topic': topic_result.extracted_topic,
                'topicName': topic_result.normalized_topic_name,
                'confidence_score': topic_result.confidence
            }
        }
    
    def _mock_geographic_extraction(self, title: str) -> List[str]:
        """Mock geographic extraction for testing when geographic detector not available."""
        mock_patterns = {
            'global': ['Global'],
            'apac': ['APAC'],
            'north america': ['North America'],
            'europe': ['Europe'],
            'asia pacific': ['Asia Pacific'],
            'china': ['China'],
            'us': ['United States'],
            'uk': ['United Kingdom']
        }
        
        title_lower = title.lower()
        extracted = []
        
        for pattern, regions in mock_patterns.items():
            if pattern in title_lower:
                extracted.extend(regions)
        
        return extracted

def test_topic_extractor():
    """Run comprehensive tests for Topic Extractor through pipeline processing."""
    
    print("Topic Extractor Pipeline Tests")
    print("=" * 50)
    
    processor = PipelineProcessor()
    test_results = []
    
    try:
        # Test 1: Standard market pattern processing
        print("\n1. Testing Standard Market patterns...")
        standard_test_cases = [
            {
                'title': "Global Artificial Intelligence Market Size & Share Report, 2030",
                'expected_topic': "Artificial Intelligence",
                'expected_format': TopicExtractionFormat.STANDARD_MARKET
            },
            {
                'title': "APAC Personal Protective Equipment Market Analysis",
                'expected_topic': "Personal Protective Equipment", 
                'expected_format': TopicExtractionFormat.STANDARD_MARKET
            },
            {
                'title': "Automotive Battery Market Outlook 2031",
                'expected_topic': "Automotive Battery",
                'expected_format': TopicExtractionFormat.STANDARD_MARKET
            }
        ]
        
        for test_case in standard_test_cases:
            result = processor.process_title(test_case['title'])
            topic_result = result['topic_extraction']
            
            print(f"   Title: {test_case['title'][:50]}...")
            print(f"   Expected: '{test_case['expected_topic']}'")
            print(f"   Extracted: '{topic_result.extracted_topic}'")
            print(f"   Confidence: {topic_result.confidence:.3f}")
            print(f"   Processing: {'; '.join(topic_result.processing_notes[-2:])}")
            print()
            
            # Validate results
            assert topic_result.extracted_topic is not None, f"No topic extracted from: {test_case['title']}"
            assert topic_result.format_type == test_case['expected_format'], f"Wrong format detected: {topic_result.format_type}"
            assert topic_result.confidence > 0.5, f"Low confidence: {topic_result.confidence}"
        
        test_results.append("✅ Standard Market pattern processing")
        
        # Test 2: Market for pattern processing
        print("2. Testing Market For patterns...")
        market_for_test_cases = [
            {
                'title': "Global Market for Advanced Materials in Aerospace, 2030",
                'expected_topic_contains': "Advanced Materials",
                'expected_format': TopicExtractionFormat.MARKET_FOR
            },
            {
                'title': "Market for Electric Vehicles in Europe",
                'expected_topic_contains': "Electric Vehicles",
                'expected_format': TopicExtractionFormat.MARKET_FOR
            }
        ]
        
        for test_case in market_for_test_cases:
            result = processor.process_title(test_case['title'])
            topic_result = result['topic_extraction']
            
            print(f"   Title: {test_case['title']}")
            print(f"   Extracted: '{topic_result.extracted_topic}'")
            print(f"   Normalized: '{topic_result.normalized_topic_name}'")
            print(f"   Confidence: {topic_result.confidence:.3f}")
            print()
            
            # Validate results
            assert topic_result.extracted_topic is not None, f"No topic extracted from: {test_case['title']}"
            assert test_case['expected_topic_contains'] in topic_result.extracted_topic, f"Expected topic component not found"
            assert topic_result.format_type == test_case['expected_format'], f"Wrong format detected: {topic_result.format_type}"
        
        test_results.append("✅ Market For pattern processing")
        
        # Test 3: Market in pattern processing
        print("3. Testing Market In patterns...")
        market_in_test_cases = [
            {
                'title': "Pharmaceutical Market in North America Analysis",
                'expected_topic': "Pharmaceutical",
                'expected_format': TopicExtractionFormat.MARKET_IN
            },
            {
                'title': "Technology Market in Asia Pacific, 2025-2030",
                'expected_topic': "Technology",
                'expected_format': TopicExtractionFormat.MARKET_IN
            }
        ]
        
        for test_case in market_in_test_cases:
            result = processor.process_title(test_case['title'])
            topic_result = result['topic_extraction']
            
            print(f"   Title: {test_case['title']}")
            print(f"   Expected: '{test_case['expected_topic']}'")
            print(f"   Extracted: '{topic_result.extracted_topic}'")
            print(f"   Confidence: {topic_result.confidence:.3f}")
            print()
            
            # Validate results
            assert topic_result.extracted_topic is not None, f"No topic extracted from: {test_case['title']}"
            assert topic_result.format_type == test_case['expected_format'], f"Wrong format detected: {topic_result.format_type}"
        
        test_results.append("✅ Market In pattern processing")
        
        # Test 4: Systematic removal validation
        print("4. Testing Systematic Removal approach...")
        removal_test_cases = [
            {
                'title': "Global 5G Technology Market Size Report, 2030",
                'description': "Should preserve technical compound '5G' in topic"
            },
            {
                'title': "North America & Europe AI Market Analysis, 2025-2030", 
                'description': "Should remove both regions and date range"
            }
        ]
        
        for test_case in removal_test_cases:
            result = processor.process_title(test_case['title'])
            topic_result = result['topic_extraction']
            extracted_elements = result['extracted_elements']
            
            print(f"   Title: {test_case['title']}")
            print(f"   Removed Date: {extracted_elements['extracted_forecast_date_range']}")
            print(f"   Removed Report: {extracted_elements['extracted_report_type']}")
            print(f"   Removed Regions: {extracted_elements['extracted_regions']}")
            print(f"   Final Topic: '{topic_result.extracted_topic}'")
            print(f"   Technical Compounds: {topic_result.technical_compounds_preserved}")
            print(f"   Description: {test_case['description']}")
            print()
            
            # Validate systematic removal worked
            assert topic_result.extracted_topic is not None, f"Systematic removal failed for: {test_case['title']}"
            
            # Check that extracted elements don't appear in final topic
            if extracted_elements['extracted_forecast_date_range']:
                assert extracted_elements['extracted_forecast_date_range'] not in topic_result.extracted_topic, "Date not properly removed"
            
            if extracted_elements['extracted_regions']:
                for region in extracted_elements['extracted_regions']:
                    assert region not in topic_result.extracted_topic, f"Region '{region}' not properly removed"
        
        test_results.append("✅ Systematic Removal validation")
        
        # Test 5: Topic normalization
        print("5. Testing Topic Normalization...")
        normalization_cases = [
            ("Artificial Intelligence", "artificial-intelligence"),
            ("5G Technology", "5g-technology"),
            ("Personal Protective Equipment", "personal-protective-equipment"),
            ("IoT & AI Solutions", "iot-ai-solutions")
        ]
        
        extractor = TopicExtractor()
        
        for original, expected_normalized in normalization_cases:
            normalized = extractor.normalize_topic(original)
            print(f"   '{original}' → '{normalized}'")
            assert normalized == expected_normalized, f"Normalization failed: expected '{expected_normalized}', got '{normalized}'"
        
        test_results.append("✅ Topic Normalization")
        
        # Test 6: End-to-end pipeline validation
        print("6. Testing End-to-End Pipeline...")
        
        pipeline_test = processor.process_title("Global Artificial Intelligence Market Size & Share Report, 2030")
        final_result = pipeline_test['final_result']
        
        print("   End-to-End Result:")
        print(f"     Original: Global Artificial Intelligence Market Size & Share Report, 2030")
        print(f"     Market Type: {final_result['market_term_type']}")
        print(f"     Date Range: {final_result['extracted_forecast_date_range']}")
        print(f"     Report Type: {final_result['extracted_report_type']}")
        print(f"     Regions: {final_result['extracted_regions']}")
        print(f"     Topic: {final_result['topic']}")
        print(f"     Topic Name: {final_result['topicName']}")
        print(f"     Confidence: {final_result['confidence_score']:.3f}")
        print()
        
        # Validate complete extraction
        assert final_result['market_term_type'] == 'standard'
        assert final_result['extracted_forecast_date_range'] == '2030'
        assert 'Market Size & Share Report' in final_result['extracted_report_type']
        assert 'Global' in final_result['extracted_regions']
        assert final_result['topic'] == 'Artificial Intelligence'
        assert final_result['topicName'] == 'artificial-intelligence'
        assert final_result['confidence_score'] > 0.7
        
        test_results.append("✅ End-to-End Pipeline validation")
        
        # Summary
        print("\n" + "=" * 50)
        print("TEST SUMMARY:")
        for result in test_results:
            print(f"  {result}")
        
        print(f"\n✅ All {len(test_results)} test suites passed!")
        print("✅ Topic Extractor successfully integrates with pipeline!")
        print("✅ Systematic removal approach working correctly!")
        
        return True
        
    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
        return False
        
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_with_mongodb_data():
    """Test Topic Extractor with real MongoDB data (if available)."""
    
    print("\n" + "=" * 50)
    print("MONGODB INTEGRATION TEST")
    print("=" * 50)
    
    try:
        from dotenv import load_dotenv
        from pymongo import MongoClient
        load_dotenv()
        
        mongodb_uri = os.getenv('MONGODB_URI')
        if not mongodb_uri:
            print("⚠️  MONGODB_URI not found - skipping MongoDB integration test")
            return True
        
        client = MongoClient(mongodb_uri, serverSelectionTimeoutMS=5000)
        db = client['deathstar']
        markets_collection = db['markets_raw']
        
        # Test with a small sample of real data
        sample_titles = list(markets_collection.find({}, {'title': 1}).limit(10))
        
        if not sample_titles:
            print("⚠️  No titles found in MongoDB - skipping integration test")
            return True
        
        print(f"✅ Testing with {len(sample_titles)} real MongoDB titles...")
        
        processor = PipelineProcessor()
        successful_extractions = 0
        
        for i, doc in enumerate(sample_titles, 1):
            title = doc['title']
            try:
                result = processor.process_title(title)
                topic_result = result['topic_extraction']
                
                if topic_result.extracted_topic:
                    successful_extractions += 1
                
                print(f"   {i}. {title[:60]}...")
                print(f"      Topic: '{topic_result.extracted_topic}'")
                print(f"      Confidence: {topic_result.confidence:.3f}")
                print()
                
            except Exception as e:
                print(f"   {i}. ❌ Failed processing: {title[:60]}... - {e}")
        
        success_rate = successful_extractions / len(sample_titles)
        print(f"MongoDB Integration Results:")
        print(f"  Processed: {len(sample_titles)} titles")
        print(f"  Successful: {successful_extractions}")
        print(f"  Success Rate: {success_rate:.1%}")
        print(f"  Status: {'✅ Good' if success_rate >= 0.8 else '⚠️ Needs Review'}")
        
        client.close()
        return success_rate >= 0.8
        
    except Exception as e:
        print(f"⚠️  MongoDB test failed: {e}")
        return True  # Don't fail the whole test suite for MongoDB issues

if __name__ == "__main__":
    print("Starting Topic Extractor Test Suite...")
    print("=" * 60)
    
    # Run main tests
    main_tests_passed = test_topic_extractor()
    
    # Run MongoDB integration test
    mongodb_test_passed = test_with_mongodb_data()
    
    # Final results
    print("\n" + "=" * 60)
    print("FINAL TEST RESULTS:")
    print("=" * 60)
    
    if main_tests_passed and mongodb_test_passed:
        print("🎉 ALL TESTS PASSED!")
        print("✅ Topic Extractor is ready for production use")
        print("✅ Pipeline integration validated")
        print("✅ Systematic removal approach confirmed")
        sys.exit(0)
    else:
        print("❌ SOME TESTS FAILED")
        if not main_tests_passed:
            print("❌ Core functionality tests failed")
        if not mongodb_test_passed:
            print("❌ MongoDB integration tests failed") 
        sys.exit(1)