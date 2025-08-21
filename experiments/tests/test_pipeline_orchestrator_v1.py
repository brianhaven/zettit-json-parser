#!/usr/bin/env python3

"""
Comprehensive Test Suite for Pipeline Orchestrator v1.0
Tests all functionality including batch processing, error handling, MongoDB integration,
and end-to-end pipeline processing with mock components.
"""

import sys
import os
import unittest
from unittest.mock import Mock, patch, MagicMock
import tempfile
import json
import shutil
from datetime import datetime, timezone

# Add parent directory to path to import the orchestrator module
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import Pipeline Orchestrator using importlib
import importlib.util
spec = importlib.util.spec_from_file_location("pipeline_orchestrator", "07_pipeline_orchestrator_v1.py")
pipeline_orchestrator_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(pipeline_orchestrator_module)

PipelineOrchestrator = pipeline_orchestrator_module.PipelineOrchestrator
ProcessingResult = pipeline_orchestrator_module.ProcessingResult
ProcessingStatus = pipeline_orchestrator_module.ProcessingStatus
ExtractedElements = pipeline_orchestrator_module.ExtractedElements

class TestPipelineOrchestrator(unittest.TestCase):
    """Test suite for Pipeline Orchestrator functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Mock MongoDB connection
        self.mock_mongo_client = Mock()
        self.mock_db = Mock()
        self.mock_mongo_client.__getitem__.return_value = self.mock_db
        
        # Create temporary directory for outputs
        self.temp_dir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()
        
    def tearDown(self):
        """Clean up test fixtures."""
        # Clean up temporary directory
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
        os.chdir(self.original_cwd)
    
    def create_mock_orchestrator(self, **kwargs):
        """Create a PipelineOrchestrator with mocked dependencies."""
        with patch('pymongo.MongoClient') as mock_client:
            mock_client.return_value = self.mock_mongo_client
            self.mock_mongo_client.__getitem__.return_value = self.mock_db
            
            # Mock the admin command for connection test
            self.mock_db.admin.command.return_value = True
            
            # Mock component initialization
            with patch.object(PipelineOrchestrator, '_initialize_components'):
                orchestrator = PipelineOrchestrator(
                    mongodb_uri="mongodb://test", 
                    **kwargs
                )
                
                # Manually set up mock components
                orchestrator.components = self._create_mock_components()
                
                return orchestrator
    
    def _create_mock_components(self):
        """Create mock pipeline components."""
        components = {}
        
        # Mock Market Term Classifier
        mock_market_result = Mock()
        mock_market_result.market_type.value = "standard"
        mock_market_classifier = Mock()
        mock_market_classifier.classify.return_value = mock_market_result
        components['market_classifier'] = mock_market_classifier
        
        # Mock Date Extractor
        mock_date_result = Mock()
        mock_date_result.extracted_date = "2030"
        mock_date_extractor = Mock()
        mock_date_extractor.extract.return_value = mock_date_result
        components['date_extractor'] = mock_date_extractor
        
        # Mock Report Type Extractor
        mock_report_result = Mock()
        mock_report_result.extracted_report_type = "Market Report"
        mock_report_extractor = Mock()
        mock_report_extractor.extract.return_value = mock_report_result
        components['report_extractor'] = mock_report_extractor
        
        # Mock Geographic Detector (functional)
        components['geographic_detector'] = Mock()
        
        # Mock Topic Extractor
        mock_topic_result = Mock()
        mock_topic_result.extracted_topic = "Artificial Intelligence"
        mock_topic_result.normalized_topic_name = "artificial-intelligence"
        mock_topic_extractor = Mock()
        mock_topic_extractor.extract.return_value = mock_topic_result
        components['topic_extractor'] = mock_topic_extractor
        
        # Mock Confidence Tracker
        mock_confidence_result = Mock()
        mock_confidence_result.overall_confidence = 0.85
        mock_confidence_tracker = Mock()
        mock_confidence_tracker.calculateOverallConfidence.return_value = mock_confidence_result
        components['confidence_tracker'] = mock_confidence_tracker
        
        return components
    
    def test_orchestrator_initialization(self):
        """Test Pipeline Orchestrator initialization."""
        orchestrator = self.create_mock_orchestrator()
        
        # Verify initialization
        self.assertIsNotNone(orchestrator)
        self.assertEqual(orchestrator.batch_size, 100)
        self.assertEqual(orchestrator.retry_attempts, 3)
        self.assertEqual(orchestrator.timeout_seconds, 30)
        self.assertIsNotNone(orchestrator.components)
        
    def test_orchestrator_custom_parameters(self):
        """Test orchestrator initialization with custom parameters."""
        orchestrator = self.create_mock_orchestrator(
            batch_size=50,
            retry_attempts=5,
            timeout_seconds=60
        )
        
        self.assertEqual(orchestrator.batch_size, 50)
        self.assertEqual(orchestrator.retry_attempts, 5)
        self.assertEqual(orchestrator.timeout_seconds, 60)
    
    def test_process_single_title_success(self):
        """Test successful processing of a single title."""
        orchestrator = self.create_mock_orchestrator()
        
        title = "Global Artificial Intelligence Market Report, 2030"
        batch_id = "test_batch"
        processing_id = "test_processing_001"
        
        result = orchestrator.processTitle(title, batch_id, processing_id)
        
        # Verify result structure
        self.assertIsInstance(result, ProcessingResult)
        self.assertEqual(result.title, title)
        self.assertEqual(result.batch_id, batch_id)
        self.assertEqual(result.processing_id, processing_id)
        self.assertEqual(result.status, ProcessingStatus.COMPLETED)
        
        # Verify extracted elements
        self.assertIsNotNone(result.extracted_elements)
        self.assertEqual(result.extracted_elements.market_term_type, "standard")
        self.assertEqual(result.extracted_elements.extracted_forecast_date_range, "2030")
        self.assertEqual(result.extracted_elements.extracted_report_type, "Market Report")
        self.assertEqual(result.extracted_elements.topic, "Artificial Intelligence")
        self.assertEqual(result.extracted_elements.topicName, "artificial-intelligence")
        
        # Verify confidence analysis
        self.assertIsNotNone(result.confidence_analysis)
        
        # Verify timing
        self.assertGreater(result.processing_time_seconds, 0)
    
    def test_process_single_title_low_confidence(self):
        """Test processing with low confidence requiring review."""
        orchestrator = self.create_mock_orchestrator()
        
        # Set up low confidence result
        mock_confidence_result = Mock()
        mock_confidence_result.overall_confidence = 0.6  # Below 0.8 threshold
        orchestrator.components['confidence_tracker'].calculateOverallConfidence.return_value = mock_confidence_result
        
        title = "Ambiguous Market Title"
        result = orchestrator.processTitle(title, "test_batch", "test_001")
        
        self.assertEqual(result.status, ProcessingStatus.REQUIRES_REVIEW)
        self.assertIn("low_confidence", result.flags)
    
    def test_process_single_title_error_handling(self):
        """Test error handling during single title processing."""
        orchestrator = self.create_mock_orchestrator()
        
        # Make market classifier raise an exception
        orchestrator.components['market_classifier'].classify.side_effect = Exception("Classification failed")
        
        title = "Test Title"
        result = orchestrator.processTitle(title, "test_batch", "test_001")
        
        self.assertEqual(result.status, ProcessingStatus.FAILED)
        self.assertIsNotNone(result.error_message)
        self.assertIn("processing_error", result.flags)
        self.assertGreater(result.processing_time_seconds, 0)
    
    def test_process_batch_success(self):
        """Test successful batch processing."""
        orchestrator = self.create_mock_orchestrator(batch_size=3)
        
        titles = [
            "Global AI Market Report, 2030",
            "North America IoT Market Analysis", 
            "5G Technology Market Size, 2025-2028"
        ]
        
        results = orchestrator.processBatch(titles, "test_batch_001")
        
        # Verify results
        self.assertEqual(len(results), 3)
        self.assertTrue(all(isinstance(r, ProcessingResult) for r in results))
        
        # Verify batch ID consistency
        batch_ids = set(r.batch_id for r in results)
        self.assertEqual(len(batch_ids), 1)
        self.assertEqual(batch_ids.pop(), "test_batch_001")
        
        # Verify processing IDs are unique
        processing_ids = [r.processing_id for r in results]
        self.assertEqual(len(processing_ids), len(set(processing_ids)))
        
        # Verify statistics updated
        self.assertGreater(orchestrator.processing_stats['total_titles_processed'], 0)
    
    def test_process_batch_auto_generated_id(self):
        """Test batch processing with auto-generated batch ID."""
        orchestrator = self.create_mock_orchestrator()
        
        titles = ["Test Title 1", "Test Title 2"]
        results = orchestrator.processBatch(titles)
        
        # Verify batch ID was generated
        batch_id = results[0].batch_id
        self.assertIsNotNone(batch_id)
        self.assertTrue(batch_id.startswith("batch_"))
        
        # All results should have same batch ID
        self.assertTrue(all(r.batch_id == batch_id for r in results))
    
    def test_progress_tracking(self):
        """Test progress tracking functionality."""
        orchestrator = self.create_mock_orchestrator()
        
        # This should not raise any exceptions
        orchestrator.trackProgress(50, 100, "test_batch")
        orchestrator.trackProgress(100, 100, "test_batch")
        orchestrator.trackProgress(0, 100, "test_batch")
    
    def test_error_handling_with_retries(self):
        """Test error handling and retry mechanism."""
        orchestrator = self.create_mock_orchestrator()
        
        # Test retry decision
        test_error = Exception("Network timeout")
        
        # Should retry for first few attempts
        self.assertTrue(orchestrator.handleErrors("Test Title", test_error, 1))
        self.assertTrue(orchestrator.handleErrors("Test Title", test_error, 2))
        
        # Should not retry after max attempts
        self.assertFalse(orchestrator.handleErrors("Test Title", test_error, 3))
    
    def test_save_results_success(self):
        """Test successful saving of results to MongoDB."""
        orchestrator = self.create_mock_orchestrator()
        
        # Create sample results
        results = [
            ProcessingResult(
                title="Test Title",
                original_title="Test Title",
                batch_id="test_batch",
                processing_id="test_001",
                status=ProcessingStatus.COMPLETED,
                extracted_elements=ExtractedElements(topic="Test Topic")
            )
        ]
        
        # Mock successful MongoDB insert
        mock_collection = Mock()
        self.mock_db.__getitem__.return_value = mock_collection
        mock_collection.insert_many.return_value = Mock()
        
        success = orchestrator.saveResults(results)
        
        self.assertTrue(success)
        mock_collection.insert_many.assert_called_once()
    
    def test_save_results_empty_list(self):
        """Test saving empty results list."""
        orchestrator = self.create_mock_orchestrator()
        
        success = orchestrator.saveResults([])
        self.assertTrue(success)
    
    def test_save_results_mongodb_error(self):
        """Test handling MongoDB errors during save."""
        orchestrator = self.create_mock_orchestrator()
        
        results = [ProcessingResult(
            title="Test",
            original_title="Test",
            batch_id="test",
            processing_id="test_001",
            status=ProcessingStatus.COMPLETED,
            extracted_elements=ExtractedElements()
        )]
        
        # Mock MongoDB error
        from pymongo.errors import PyMongoError
        mock_collection = Mock()
        self.mock_db.__getitem__.return_value = mock_collection
        mock_collection.insert_many.side_effect = PyMongoError("Connection failed")
        
        success = orchestrator.saveResults(results)
        self.assertFalse(success)
    
    def test_generate_report_with_results(self):
        """Test report generation with provided results."""
        orchestrator = self.create_mock_orchestrator()
        
        # Change to temp directory for output
        os.chdir(self.temp_dir)
        
        # Create sample results
        results = [
            ProcessingResult(
                title="Test Title 1",
                original_title="Test Title 1",
                batch_id="test_batch",
                processing_id="test_001",
                status=ProcessingStatus.COMPLETED,
                extracted_elements=ExtractedElements(topic="Test Topic 1"),
                processing_time_seconds=1.5,
                confidence_analysis={'overall_confidence': 0.85}
            ),
            ProcessingResult(
                title="Test Title 2",
                original_title="Test Title 2",
                batch_id="test_batch",
                processing_id="test_002",
                status=ProcessingStatus.FAILED,
                extracted_elements=ExtractedElements(),
                processing_time_seconds=0.8,
                error_message="Processing failed"
            )
        ]
        
        # Create outputs directory in temp dir
        os.makedirs("outputs", exist_ok=True)
        
        filename = orchestrator.generateReport("test_batch", results)
        
        # Verify report was generated
        self.assertTrue(filename.endswith('.json'))
        self.assertTrue(os.path.exists(filename))
        
        # Verify report content
        with open(filename, 'r') as f:
            report_data = json.load(f)
        
        self.assertEqual(report_data['batch_id'], "test_batch")
        self.assertIn('batch_summary', report_data)
        self.assertEqual(report_data['batch_summary']['total_titles'], 2)
        self.assertEqual(report_data['batch_summary']['completed'], 1)
        self.assertEqual(report_data['batch_summary']['failed'], 1)
        
    def test_confidence_distribution_analysis(self):
        """Test confidence distribution analysis."""
        orchestrator = self.create_mock_orchestrator()
        
        # Create results with varying confidence scores
        results = [
            ProcessingResult(
                title="High Confidence", original_title="High Confidence",
                batch_id="test", processing_id="001", status=ProcessingStatus.COMPLETED,
                extracted_elements=ExtractedElements(),
                confidence_analysis={'overall_confidence': 0.9}
            ),
            ProcessingResult(
                title="Medium Confidence", original_title="Medium Confidence",
                batch_id="test", processing_id="002", status=ProcessingStatus.COMPLETED,
                extracted_elements=ExtractedElements(),
                confidence_analysis={'overall_confidence': 0.65}
            ),
            ProcessingResult(
                title="Low Confidence", original_title="Low Confidence",
                batch_id="test", processing_id="003", status=ProcessingStatus.REQUIRES_REVIEW,
                extracted_elements=ExtractedElements(),
                confidence_analysis={'overall_confidence': 0.3}
            )
        ]
        
        analysis = orchestrator._analyze_confidence_distribution(results)
        
        self.assertEqual(analysis['count'], 3)
        self.assertEqual(analysis['high_confidence'], 1)
        self.assertEqual(analysis['medium_confidence'], 1)
        self.assertEqual(analysis['low_confidence'], 1)
        self.assertAlmostEqual(analysis['average'], 0.617, places=2)
        
    def test_get_processing_statistics(self):
        """Test processing statistics calculation."""
        orchestrator = self.create_mock_orchestrator()
        
        # Simulate some processing
        orchestrator.processing_stats['total_titles_processed'] = 100
        orchestrator.processing_stats['successful_extractions'] = 85
        orchestrator.processing_stats['failed_extractions'] = 10
        orchestrator.processing_stats['requires_review_count'] = 5
        orchestrator.processing_stats['total_processing_time'] = 50.0
        
        stats = orchestrator.get_processing_statistics()
        
        self.assertEqual(stats['total_titles_processed'], 100)
        self.assertAlmostEqual(stats['overall_success_rate'], 0.85)
        self.assertAlmostEqual(stats['overall_review_rate'], 0.05)
        self.assertAlmostEqual(stats['overall_failure_rate'], 0.10)
        self.assertAlmostEqual(stats['overall_titles_per_second'], 2.0)
    
    def test_timestamps_generation(self):
        """Test timestamp generation functionality."""
        orchestrator = self.create_mock_orchestrator()
        
        pdt_str, utc_str, utc_datetime = orchestrator._get_timestamps()
        
        # Verify timestamp formats
        self.assertIsInstance(pdt_str, str)
        self.assertIsInstance(utc_str, str)
        self.assertIsInstance(utc_datetime, datetime)
        
        # Verify UTC timestamp format
        self.assertTrue(utc_str.endswith('UTC'))
        
        # Verify PDT timestamp contains timezone info
        self.assertTrue('PDT' in pdt_str or 'PST' in pdt_str)
    
    def test_batch_id_generation(self):
        """Test batch ID generation."""
        orchestrator = self.create_mock_orchestrator()
        
        batch_id1 = orchestrator._generate_batch_id()
        batch_id2 = orchestrator._generate_batch_id()
        
        # Verify format
        self.assertTrue(batch_id1.startswith('batch_'))
        self.assertTrue(batch_id2.startswith('batch_'))
        
        # Verify uniqueness
        self.assertNotEqual(batch_id1, batch_id2)
    
    def test_processing_id_generation(self):
        """Test processing ID generation."""
        orchestrator = self.create_mock_orchestrator()
        
        batch_id = "test_batch"
        
        id1 = orchestrator._generate_processing_id(batch_id, 0)
        id2 = orchestrator._generate_processing_id(batch_id, 1)
        id3 = orchestrator._generate_processing_id(batch_id, 99)
        
        # Verify format
        self.assertEqual(id1, "test_batch_title_0000")
        self.assertEqual(id2, "test_batch_title_0001")
        self.assertEqual(id3, "test_batch_title_0099")
    
    def test_geographic_entities_processing(self):
        """Test geographic entities processing placeholder."""
        orchestrator = self.create_mock_orchestrator()
        
        result = orchestrator._process_geographic_entities("Global Market Report")
        
        # Verify placeholder structure
        self.assertIsInstance(result, dict)
        self.assertIn('extracted_regions', result)
        self.assertIn('confidence', result)
        self.assertIsInstance(result['extracted_regions'], list)
    
    def test_integration_with_all_components(self):
        """Test end-to-end integration with all pipeline components."""
        orchestrator = self.create_mock_orchestrator()
        
        title = "Global Artificial Intelligence Market Size & Share Report, 2030"
        result = orchestrator.processTitle(title, "integration_test", "int_001")
        
        # Verify all components were called
        orchestrator.components['market_classifier'].classify.assert_called_with(title)
        orchestrator.components['date_extractor'].extract.assert_called_with(title)
        orchestrator.components['report_extractor'].extract.assert_called()
        orchestrator.components['topic_extractor'].extract.assert_called()
        orchestrator.components['confidence_tracker'].calculateOverallConfidence.assert_called()
        
        # Verify result completeness
        self.assertEqual(result.status, ProcessingStatus.COMPLETED)
        self.assertIsNotNone(result.extracted_elements.market_term_type)
        self.assertIsNotNone(result.extracted_elements.extracted_forecast_date_range)
        self.assertIsNotNone(result.extracted_elements.extracted_report_type)
        self.assertIsNotNone(result.extracted_elements.topic)
        self.assertIsNotNone(result.extracted_elements.topicName)

class TestPipelineOrchestratorEdgeCases(unittest.TestCase):
    """Test edge cases and error conditions for Pipeline Orchestrator."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.mock_mongo_client = Mock()
        self.mock_db = Mock()
        self.mock_mongo_client.__getitem__.return_value = self.mock_db
        
    def create_mock_orchestrator(self):
        """Create a mock orchestrator for edge case testing."""
        with patch('pymongo.MongoClient') as mock_client:
            mock_client.return_value = self.mock_mongo_client
            self.mock_mongo_client.__getitem__.return_value = self.mock_db
            self.mock_db.admin.command.return_value = True
            
            with patch.object(PipelineOrchestrator, '_initialize_components'):
                orchestrator = PipelineOrchestrator(mongodb_uri="mongodb://test")
                orchestrator.components = {}  # Empty components for edge testing
                return orchestrator
    
    def test_empty_title_processing(self):
        """Test processing of empty or whitespace-only titles."""
        orchestrator = self.create_mock_orchestrator()
        orchestrator.components = self._create_minimal_mock_components()
        
        # Test empty string
        result = orchestrator.processTitle("", "test_batch", "test_001")
        self.assertEqual(result.status, ProcessingStatus.FAILED)
        
        # Test whitespace only
        result = orchestrator.processTitle("   ", "test_batch", "test_002")
        self.assertEqual(result.status, ProcessingStatus.FAILED)
    
    def test_none_title_processing(self):
        """Test processing of None title."""
        orchestrator = self.create_mock_orchestrator()
        orchestrator.components = self._create_minimal_mock_components()
        
        try:
            result = orchestrator.processTitle(None, "test_batch", "test_001")
            # Should handle gracefully or raise appropriate exception
            self.assertIn(result.status, [ProcessingStatus.FAILED])
        except (TypeError, AttributeError):
            # Expected behavior for None input
            pass
    
    def test_mongodb_connection_failure(self):
        """Test handling of MongoDB connection failures."""
        with patch('pymongo.MongoClient') as mock_client:
            mock_client.side_effect = Exception("Connection failed")
            
            with self.assertRaises(Exception):
                PipelineOrchestrator(mongodb_uri="mongodb://invalid")
    
    def test_component_initialization_failure(self):
        """Test handling of component initialization failures."""
        with patch('pymongo.MongoClient') as mock_client:
            mock_client.return_value = self.mock_mongo_client
            self.mock_db.admin.command.return_value = True
            
            # Mock importlib to fail
            with patch('importlib.util.spec_from_file_location') as mock_spec:
                mock_spec.return_value = None
                
                with self.assertRaises(Exception):
                    PipelineOrchestrator(mongodb_uri="mongodb://test")
    
    def test_batch_processing_with_mixed_results(self):
        """Test batch processing with mixed success/failure results."""
        orchestrator = self.create_mock_orchestrator()
        
        # Create components that succeed for some titles, fail for others
        components = self._create_mixed_result_components()
        orchestrator.components = components
        
        titles = [
            "Success Title 1",
            "Failure Title",
            "Success Title 2",
            "Error Title"
        ]
        
        results = orchestrator.processBatch(titles, "mixed_batch")
        
        self.assertEqual(len(results), 4)
        
        # Check that we have mixed results
        statuses = [r.status for r in results]
        self.assertIn(ProcessingStatus.COMPLETED, statuses)
        self.assertIn(ProcessingStatus.FAILED, statuses)
    
    def _create_minimal_mock_components(self):
        """Create minimal mock components that can handle basic processing."""
        components = {}
        
        # Each component returns minimal valid results
        for component_name in ['market_classifier', 'date_extractor', 'report_extractor', 
                              'topic_extractor', 'confidence_tracker']:
            mock_component = Mock()
            
            if component_name == 'market_classifier':
                mock_result = Mock()
                mock_result.market_type.value = "standard"
                mock_component.classify.return_value = mock_result
            elif component_name == 'confidence_tracker':
                mock_result = Mock()
                mock_result.overall_confidence = 0.5
                mock_component.calculateOverallConfidence.return_value = mock_result
            else:
                mock_result = Mock()
                for attr in ['extracted_date', 'extracted_report_type', 'extracted_topic', 'normalized_topic_name']:
                    setattr(mock_result, attr, None)
                mock_component.extract.return_value = mock_result
            
            components[component_name] = mock_component
        
        components['geographic_detector'] = Mock()
        
        return components
    
    def _create_mixed_result_components(self):
        """Create components that succeed/fail based on title content."""
        components = {}
        
        def create_conditional_component(success_keyword, component_type='extract'):
            mock_component = Mock()
            
            def conditional_method(title, *args, **kwargs):
                if success_keyword in title:
                    mock_result = Mock()
                    if component_type == 'classify':
                        mock_result.market_type.value = "standard"
                    elif component_type == 'confidence':
                        mock_result.overall_confidence = 0.8
                    else:
                        for attr in ['extracted_date', 'extracted_report_type', 'extracted_topic', 'normalized_topic_name']:
                            setattr(mock_result, attr, f"mock_{attr}")
                    return mock_result
                else:
                    raise Exception("Component failure")
            
            if component_type == 'classify':
                mock_component.classify.side_effect = conditional_method
            elif component_type == 'confidence':
                mock_component.calculateOverallConfidence.side_effect = conditional_method
            else:
                mock_component.extract.side_effect = conditional_method
            
            return mock_component
        
        components['market_classifier'] = create_conditional_component("Success", 'classify')
        components['date_extractor'] = create_conditional_component("Success", 'extract')
        components['report_extractor'] = create_conditional_component("Success", 'extract')
        components['topic_extractor'] = create_conditional_component("Success", 'extract')
        components['confidence_tracker'] = create_conditional_component("Success", 'confidence')
        components['geographic_detector'] = Mock()
        
        return components

def run_all_tests():
    """Run all pipeline orchestrator tests."""
    print("Pipeline Orchestrator Test Suite")
    print("=" * 50)
    
    # Create test suite
    test_suite = unittest.TestSuite()
    
    # Add all test cases from both test classes
    test_classes = [TestPipelineOrchestrator, TestPipelineOrchestratorEdgeCases]
    
    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        test_suite.addTest(tests)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2, buffer=True)
    result = runner.run(test_suite)
    
    # Print summary
    print("\n" + "=" * 50)
    print("TEST SUMMARY:")
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    
    if result.failures:
        print("\nFAILURES:")
        for test, traceback in result.failures:
            print(f"  {test}: {traceback}")
    
    if result.errors:
        print("\nERRORS:")
        for test, traceback in result.errors:
            print(f"  {test}: {traceback}")
    
    success = len(result.failures) == 0 and len(result.errors) == 0
    
    if success:
        print("\n✅ All Pipeline Orchestrator tests passed!")
    else:
        print("\n❌ Some Pipeline Orchestrator tests failed!")
    
    return success

if __name__ == "__main__":
    print("Starting Pipeline Orchestrator Test Suite...")
    success = run_all_tests()
    
    if not success:
        sys.exit(1)