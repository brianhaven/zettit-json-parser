#!/usr/bin/env python3

"""
Test Suite for Geographic Entity Detection System v1.0
Comprehensive testing for pattern-based and model-based geographic entity detection.
Created for Market Research Title Parser project.
"""

import os
import sys
import logging
import json
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
from collections import Counter, defaultdict
import pytz

# Add experiments directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from geographic_entity_detector_v1 import GeographicEntityDetector, DetectionResult
from pattern_library_manager_v1 import PatternLibraryManager, PatternType

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class GeographicDetectionTester:
    """
    Comprehensive test suite for Geographic Entity Detection System.
    
    Tests pattern-based detection, model integration, and accuracy metrics.
    """
    
    def __init__(self, use_models=False):
        """Initialize the tester."""
        self.use_models = use_models
        self.detector = GeographicEntityDetector(use_models=use_models)
        self.pattern_manager = PatternLibraryManager()
        
        # Test results storage
        self.test_results = {
            'pattern_tests': [],
            'model_tests': [],
            'accuracy_tests': [],
            'performance_tests': []
        }
    
    def _get_timestamps(self) -> tuple:
        """Generate PDT and UTC timestamps."""
        utc_now = datetime.now(timezone.utc)
        pdt_tz = pytz.timezone('America/Los_Angeles')
        pdt_now = utc_now.astimezone(pdt_tz)
        
        pdt_str = pdt_now.strftime('%Y-%m-%d %H:%M:%S %Z')
        utc_str = utc_now.strftime('%Y-%m-%d %H:%M:%S UTC')
        
        return pdt_str, utc_str, utc_now
    
    def test_mongodb_pattern_library(self) -> Dict[str, Any]:
        """Test MongoDB pattern library functionality."""
        logger.info("Testing MongoDB pattern library...")
        
        try:
            # Get geographic patterns
            geo_patterns = self.pattern_manager.get_patterns(PatternType.GEOGRAPHIC_ENTITY)
            
            # Analyze patterns
            pattern_analysis = {
                'total_patterns': len(geo_patterns),
                'patterns_by_priority': Counter(p['priority'] for p in geo_patterns),
                'patterns_with_aliases': len([p for p in geo_patterns if p.get('aliases')]),
                'sample_patterns': {}
            }
            
            # Sample patterns by priority
            for priority in range(1, 6):
                priority_patterns = [p for p in geo_patterns if p['priority'] == priority]
                if priority_patterns:
                    pattern_analysis['sample_patterns'][priority] = [
                        {'term': p['term'], 'aliases': p.get('aliases', [])} 
                        for p in priority_patterns[:5]
                    ]
            
            self.test_results['pattern_tests'].append({
                'test_name': 'mongodb_pattern_library',
                'status': 'pass',
                'results': pattern_analysis
            })
            
            logger.info(f"MongoDB test passed: {len(geo_patterns)} patterns loaded")
            return pattern_analysis
            
        except Exception as e:
            error_result = {'error': str(e)}
            self.test_results['pattern_tests'].append({
                'test_name': 'mongodb_pattern_library',
                'status': 'fail',
                'results': error_result
            })
            logger.error(f"MongoDB test failed: {e}")
            return error_result
    
    def test_compound_first_processing(self) -> Dict[str, Any]:
        """Test compound-first processing logic."""
        logger.info("Testing compound-first processing...")
        
        # Test cases where compound entities should be detected before simple ones
        test_cases = [
            {
                'title': 'North America Market Analysis Report',
                'expected': ['North America'],
                'should_not_contain': ['America']
            },
            {
                'title': 'Asia Pacific and Middle East Market Study',
                'expected': ['Asia Pacific', 'Middle East'], 
                'should_not_contain': ['Asia', 'East']
            },
            {
                'title': 'Eastern Europe Technology Market Outlook',
                'expected': ['Eastern Europe'],
                'should_not_contain': ['Europe']
            },
            {
                'title': 'South America Regional Market Report',
                'expected': ['South America'],
                'should_not_contain': ['America']
            }
        ]
        
        results = {
            'total_tests': len(test_cases),
            'passed': 0,
            'failed': 0,
            'test_details': []
        }
        
        for test_case in test_cases:
            title = test_case['title']
            expected = test_case['expected']
            should_not_contain = test_case.get('should_not_contain', [])
            
            detection_result = self.detector.detect(title)
            detected_entities = detection_result.extracted_regions
            
            # Check if expected entities are detected
            expected_found = all(entity in detected_entities for entity in expected)
            
            # Check if unwanted simple entities are NOT detected
            unwanted_found = any(entity in detected_entities for entity in should_not_contain)
            
            test_passed = expected_found and not unwanted_found
            
            test_detail = {
                'title': title,
                'expected': expected,
                'detected': detected_entities,
                'should_not_contain': should_not_contain,
                'passed': test_passed,
                'confidence': detection_result.confidence_score
            }
            
            results['test_details'].append(test_detail)
            
            if test_passed:
                results['passed'] += 1
            else:
                results['failed'] += 1
        
        test_status = 'pass' if results['failed'] == 0 else 'fail'
        
        self.test_results['pattern_tests'].append({
            'test_name': 'compound_first_processing',
            'status': test_status,
            'results': results
        })
        
        logger.info(f"Compound-first test: {results['passed']}/{results['total_tests']} passed")
        return results
    
    def test_geographic_accuracy(self) -> Dict[str, Any]:
        """Test detection accuracy with known cases."""
        logger.info("Testing geographic detection accuracy...")
        
        # Curated test cases with expected results
        accuracy_test_cases = [
            # Clear geographic patterns - should detect
            {'title': 'Global Automotive Market Report', 'expected_count': 0, 'description': 'Global without specific geography'},
            {'title': 'APAC Semiconductor Market Analysis', 'expected_count': 1, 'description': 'Regional acronym'},
            {'title': 'North America Healthcare Market', 'expected_count': 1, 'description': 'Compound region'},
            {'title': 'Europe and Asia Technology Market', 'expected_count': 2, 'description': 'Multiple regions'},
            {'title': 'United States Manufacturing Market', 'expected_count': 1, 'description': 'Country name'},
            {'title': 'EMEA Financial Services Market', 'expected_count': 1, 'description': 'Regional acronym'},
            
            # Tricky cases - context matters
            {'title': 'After Market Services Analysis', 'expected_count': 0, 'description': 'After Market (not geographic)'},
            {'title': 'Farmers Market Industry Report', 'expected_count': 0, 'description': 'Farmers Market (not geographic)'},
            {'title': 'Stock Market Performance Review', 'expected_count': 0, 'description': 'Stock Market (not geographic)'},
            
            # Multiple geography patterns
            {'title': 'Asia Pacific, Europe and North America Market', 'expected_count': 3, 'description': 'Three regions'},
            {'title': 'China and India Technology Market', 'expected_count': 2, 'description': 'Two countries'},
            
            # Edge cases
            {'title': 'Blockchain Technology Market Trends', 'expected_count': 0, 'description': 'No geography'},
            {'title': 'Market Research Methodology', 'expected_count': 0, 'description': 'Generic market title'},
        ]
        
        results = {
            'total_tests': len(accuracy_test_cases),
            'correct_predictions': 0,
            'accuracy_percentage': 0.0,
            'test_details': []
        }
        
        for test_case in accuracy_test_cases:
            title = test_case['title']
            expected_count = test_case['expected_count']
            description = test_case['description']
            
            detection_result = self.detector.detect(title)
            detected_count = len(detection_result.extracted_regions)
            
            is_correct = detected_count == expected_count
            
            test_detail = {
                'title': title,
                'description': description,
                'expected_count': expected_count,
                'detected_count': detected_count,
                'detected_entities': detection_result.extracted_regions,
                'correct': is_correct,
                'confidence': detection_result.confidence_score
            }
            
            results['test_details'].append(test_detail)
            
            if is_correct:
                results['correct_predictions'] += 1
        
        results['accuracy_percentage'] = round(
            (results['correct_predictions'] / results['total_tests']) * 100, 2
        )
        
        test_status = 'pass' if results['accuracy_percentage'] >= 80 else 'fail'
        
        self.test_results['accuracy_tests'].append({
            'test_name': 'geographic_accuracy',
            'status': test_status,
            'results': results
        })
        
        logger.info(f"Accuracy test: {results['accuracy_percentage']}% correct")
        return results
    
    def test_performance_metrics(self) -> Dict[str, Any]:
        """Test detection performance with larger dataset."""
        logger.info("Testing detection performance...")
        
        # Generate test dataset with various patterns
        test_titles = [
            # Geographic patterns
            'APAC Technology Market Report 2030',
            'North America Healthcare Analysis',
            'Europe Automotive Industry Study',
            'Asia Pacific Renewable Energy Market',
            'Middle East Oil and Gas Report',
            'Latin America Agriculture Market',
            'United States AI Market Outlook',
            'China Manufacturing Sector Analysis',
            'India Software Market Report',
            'Germany Industrial Market Study',
            
            # Non-geographic patterns  
            'Blockchain Technology Market Trends',
            'Artificial Intelligence Market Report',
            'Cloud Computing Industry Analysis',
            'Cybersecurity Market Outlook',
            'IoT Technology Market Study',
            'Renewable Energy Market Report',
            'Healthcare Technology Analysis',
            'Financial Services Market Report',
            'E-commerce Platform Market',
            'Digital Marketing Industry Study',
            
            # Mixed patterns
            'Global Automotive Market Report',
            'Worldwide Technology Trends',
            'International Trade Analysis',
            'After Market Services Report',
            'Stock Market Performance Review'
        ]
        
        # Perform batch detection
        import time
        start_time = time.time()
        
        batch_results = self.detector.detect_batch(test_titles)
        
        end_time = time.time()
        processing_time = end_time - start_time
        
        # Analyze results
        titles_with_geography = sum(1 for result in batch_results if result.extracted_regions)
        total_entities = sum(len(result.extracted_regions) for result in batch_results)
        
        confidence_scores = [result.confidence_score for result in batch_results]
        avg_confidence = sum(confidence_scores) / len(confidence_scores)
        
        performance_metrics = {
            'total_titles': len(test_titles),
            'processing_time_seconds': round(processing_time, 3),
            'titles_per_second': round(len(test_titles) / processing_time, 1),
            'titles_with_geography': titles_with_geography,
            'geography_detection_rate': round((titles_with_geography / len(test_titles)) * 100, 2),
            'total_entities_detected': total_entities,
            'average_entities_per_title': round(total_entities / len(test_titles), 2),
            'average_confidence': round(avg_confidence, 3),
            'confidence_distribution': {
                'high_confidence_0.9+': sum(1 for score in confidence_scores if score >= 0.9),
                'medium_confidence_0.7-0.89': sum(1 for score in confidence_scores if 0.7 <= score < 0.9),
                'low_confidence_below_0.7': sum(1 for score in confidence_scores if score < 0.7)
            }
        }
        
        self.test_results['performance_tests'].append({
            'test_name': 'performance_metrics',
            'status': 'pass',
            'results': performance_metrics
        })
        
        logger.info(f"Performance test: {performance_metrics['titles_per_second']} titles/sec")
        return performance_metrics
    
    def test_model_integration_placeholders(self) -> Dict[str, Any]:
        """Test NLP model integration placeholders."""
        logger.info("Testing NLP model integration placeholders...")
        
        # Test that models can be initialized (even if not available)
        detector_with_models = GeographicEntityDetector(use_models=True)
        
        model_status = {
            'spacy_model_available': detector_with_models.spacy_model is not None,
            'gliner_model_available': detector_with_models.gliner_model is not None,
            'models_enabled': detector_with_models.use_models
        }
        
        # Test detection with models enabled (should not fail)
        test_title = "North America Technology Market Report"
        result = detector_with_models.detect(test_title)
        
        model_test_result = {
            'model_status': model_status,
            'detection_successful': len(result.processing_notes) > 0,
            'entities_detected': result.extracted_regions
        }
        
        self.test_results['model_tests'].append({
            'test_name': 'model_integration_placeholders',
            'status': 'pass',
            'results': model_test_result
        })
        
        logger.info("Model integration test completed")
        return model_test_result
    
    def run_comprehensive_tests(self) -> Dict[str, Any]:
        """Run all test suites and generate comprehensive report."""
        logger.info("Starting comprehensive test suite...")
        
        pdt_time, utc_time, _ = self._get_timestamps()
        
        # Run all tests
        mongodb_results = self.test_mongodb_pattern_library()
        compound_results = self.test_compound_first_processing()
        accuracy_results = self.test_geographic_accuracy()
        performance_results = self.test_performance_metrics()
        model_results = self.test_model_integration_placeholders()
        
        # Compile comprehensive report
        comprehensive_report = {
            'metadata': {
                'test_date_pdt': pdt_time,
                'test_date_utc': utc_time,
                'test_version': 'v1.0',
                'models_enabled': self.use_models
            },
            'test_summary': {
                'total_test_suites': 5,
                'passed_suites': sum(1 for suite in self.test_results.values() 
                                   for test in suite if test['status'] == 'pass'),
                'failed_suites': sum(1 for suite in self.test_results.values() 
                                   for test in suite if test['status'] == 'fail')
            },
            'mongodb_test': mongodb_results,
            'compound_processing_test': compound_results,
            'accuracy_test': accuracy_results,
            'performance_test': performance_results,
            'model_integration_test': model_results,
            'detector_statistics': self.detector.get_detection_statistics().__dict__
        }
        
        # Overall success assessment
        overall_success = (
            compound_results.get('failed', 1) == 0 and
            accuracy_results.get('accuracy_percentage', 0) >= 80 and
            performance_results.get('titles_per_second', 0) >= 10
        )
        
        comprehensive_report['overall_assessment'] = {
            'success': overall_success,
            'key_metrics': {
                'compound_processing_success': compound_results.get('failed', 1) == 0,
                'accuracy_percentage': accuracy_results.get('accuracy_percentage', 0),
                'performance_titles_per_second': performance_results.get('titles_per_second', 0)
            }
        }
        
        logger.info(f"Comprehensive tests completed. Overall success: {overall_success}")
        return comprehensive_report
    
    def export_test_report(self, filename: Optional[str] = None) -> str:
        """Export test results to formatted report."""
        pdt_time, utc_time, _ = self._get_timestamps()
        
        # Run comprehensive tests if not already done
        if not any(self.test_results.values()):
            comprehensive_results = self.run_comprehensive_tests()
        else:
            comprehensive_results = self.test_results
        
        # Generate report
        report = f"""Geographic Entity Detection Test Report
{'='*60}
Analysis Date (PDT): {pdt_time}
Analysis Date (UTC): {utc_time}
{'='*60}

TEST SUMMARY:
"""
        
        # Add test results to report
        for suite_name, tests in self.test_results.items():
            if tests:
                report += f"\n{suite_name.upper()}:\n"
                for test in tests:
                    status_symbol = "✅" if test['status'] == 'pass' else "❌"
                    report += f"  {status_symbol} {test['test_name']}: {test['status']}\n"
        
        # Add key metrics
        report += f"\nKEY PERFORMANCE METRICS:\n"
        
        if filename:
            # Save full results as JSON
            json_filename = filename.replace('.txt', '.json')
            with open(json_filename, 'w', encoding='utf-8') as f:
                json.dump(comprehensive_results if 'comprehensive_results' in locals() else self.test_results, 
                         f, indent=2, ensure_ascii=False, default=str)
            
            # Save formatted report
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(report)
                
            logger.info(f"Test report exported to {filename}")
            logger.info(f"Detailed results exported to {json_filename}")
        
        return report


def main():
    """Main function to run comprehensive tests."""
    print("Geographic Entity Detection Test Suite v1.0")
    print("=" * 70)
    
    try:
        # Initialize tester
        tester = GeographicDetectionTester(use_models=False)
        
        # Run comprehensive tests
        results = tester.run_comprehensive_tests()
        
        # Export results
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_file = f"../outputs/{timestamp}_geographic_detection_test_results.txt"
        
        os.makedirs("../outputs", exist_ok=True)
        report = tester.export_test_report(output_file)
        
        # Print summary
        print("\n" + "=" * 70)
        print("📊 TEST RESULTS SUMMARY")
        print("=" * 70)
        
        if results.get('overall_assessment', {}).get('success', False):
            print("✅ OVERALL STATUS: PASSED")
        else:
            print("❌ OVERALL STATUS: FAILED")
        
        print(f"\nKey Metrics:")
        key_metrics = results.get('overall_assessment', {}).get('key_metrics', {})
        print(f"  Compound Processing: {'✅' if key_metrics.get('compound_processing_success') else '❌'}")
        print(f"  Accuracy: {key_metrics.get('accuracy_percentage', 0):.1f}%")
        print(f"  Performance: {key_metrics.get('performance_titles_per_second', 0):.1f} titles/sec")
        
        print(f"\nDetailed results saved to: {output_file}")
        print("\n✅ Geographic Entity Detection test suite completed!")
        
    except Exception as e:
        logger.error(f"Test suite failed: {e}")
        print(f"❌ Test suite failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()