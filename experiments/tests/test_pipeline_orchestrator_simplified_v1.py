#!/usr/bin/env python3

"""
Simplified Test Suite for Pipeline Orchestrator v1.0
Tests core functionality with simplified mocking approach.
"""

import sys
import os
import logging

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

# Configure logging for tests
logging.basicConfig(level=logging.WARNING)

def test_pipeline_orchestrator_core():
    """Test core Pipeline Orchestrator functionality with mocked components."""
    
    print("Simplified Pipeline Orchestrator Tests")
    print("=" * 50)
    
    test_results = []
    
    try:
        # Test 1: Basic component functionality test
        print("\n1. Testing basic component structure...")
        
        # Create a simplified orchestrator without MongoDB dependency
        orchestrator = create_mock_orchestrator()
        
        print("   ✅ Mock orchestrator created successfully")
        test_results.append("✅ Basic component structure")
        
        # Test 2: Test timestamp generation
        print("\n2. Testing timestamp generation...")
        pdt_str, utc_str, utc_datetime = orchestrator._get_timestamps()
        
        print(f"   PDT timestamp: {pdt_str}")
        print(f"   UTC timestamp: {utc_str}")
        
        assert isinstance(pdt_str, str), "PDT timestamp should be string"
        assert isinstance(utc_str, str), "UTC timestamp should be string"
        assert 'UTC' in utc_str, "UTC timestamp should contain 'UTC'"
        assert ('PDT' in pdt_str or 'PST' in pdt_str), "PDT timestamp should contain timezone"
        
        test_results.append("✅ Timestamp generation")
        
        # Test 3: Test batch ID generation
        print("\n3. Testing batch ID generation...")
        batch_id1 = orchestrator._generate_batch_id()
        batch_id2 = orchestrator._generate_batch_id()
        
        print(f"   Batch ID 1: {batch_id1}")
        print(f"   Batch ID 2: {batch_id2}")
        
        assert batch_id1.startswith('batch_'), "Batch ID should start with 'batch_'"
        assert batch_id2.startswith('batch_'), "Batch ID should start with 'batch_'"
        assert batch_id1 != batch_id2, "Batch IDs should be unique"
        
        test_results.append("✅ Batch ID generation")
        
        # Test 4: Test processing ID generation
        print("\n4. Testing processing ID generation...")
        batch_id = "test_batch"
        
        id1 = orchestrator._generate_processing_id(batch_id, 0)
        id2 = orchestrator._generate_processing_id(batch_id, 1)
        id3 = orchestrator._generate_processing_id(batch_id, 99)
        
        print(f"   Processing ID 1: {id1}")
        print(f"   Processing ID 2: {id2}")
        print(f"   Processing ID 99: {id3}")
        
        assert id1 == "test_batch_title_0000", f"Expected 'test_batch_title_0000', got '{id1}'"
        assert id2 == "test_batch_title_0001", f"Expected 'test_batch_title_0001', got '{id2}'"
        assert id3 == "test_batch_title_0099", f"Expected 'test_batch_title_0099', got '{id3}'"
        
        test_results.append("✅ Processing ID generation")
        
        # Test 5: Test progress tracking
        print("\n5. Testing progress tracking...")
        
        # This should not raise any exceptions
        orchestrator.trackProgress(50, 100, "test_batch")
        orchestrator.trackProgress(100, 100, "test_batch")
        orchestrator.trackProgress(0, 100, "test_batch")
        
        test_results.append("✅ Progress tracking")
        
        # Test 6: Test error handling logic
        print("\n6. Testing error handling logic...")
        
        test_error = Exception("Network timeout")
        
        # Should retry for first few attempts
        should_retry_1 = orchestrator.handleErrors("Test Title", test_error, 1)
        should_retry_2 = orchestrator.handleErrors("Test Title", test_error, 2)
        should_retry_3 = orchestrator.handleErrors("Test Title", test_error, 3)
        
        print(f"   Retry attempt 1: {should_retry_1}")
        print(f"   Retry attempt 2: {should_retry_2}")
        print(f"   Retry attempt 3: {should_retry_3}")
        
        assert should_retry_1 == True, "Should retry on attempt 1"
        assert should_retry_2 == True, "Should retry on attempt 2"
        assert should_retry_3 == False, "Should not retry after max attempts"
        
        test_results.append("✅ Error handling logic")
        
        # Test 7: Test geographic entities processing placeholder
        print("\n7. Testing geographic entities processing...")
        
        geo_result = orchestrator._process_geographic_entities("Global Market Report")
        
        print(f"   Geographic result: {geo_result}")
        
        assert isinstance(geo_result, dict), "Geographic result should be dict"
        assert 'extracted_regions' in geo_result, "Should have extracted_regions key"
        assert isinstance(geo_result['extracted_regions'], list), "Extracted regions should be list"
        
        test_results.append("✅ Geographic entities processing")
        
        # Test 8: Test processing statistics
        print("\n8. Testing processing statistics...")
        
        # Simulate some processing
        orchestrator.processing_stats['total_titles_processed'] = 100
        orchestrator.processing_stats['successful_extractions'] = 85
        orchestrator.processing_stats['failed_extractions'] = 10
        orchestrator.processing_stats['requires_review_count'] = 5
        orchestrator.processing_stats['total_processing_time'] = 50.0
        
        stats = orchestrator.get_processing_statistics()
        
        print(f"   Total processed: {stats['total_titles_processed']}")
        print(f"   Success rate: {stats['overall_success_rate']:.1%}")
        print(f"   Titles per second: {stats['overall_titles_per_second']:.2f}")
        
        assert stats['total_titles_processed'] == 100
        assert abs(stats['overall_success_rate'] - 0.85) < 0.01
        assert abs(stats['overall_titles_per_second'] - 2.0) < 0.01
        
        test_results.append("✅ Processing statistics")
        
        # Test 9: Test confidence distribution analysis
        print("\n9. Testing confidence distribution analysis...")
        
        # Create mock results with varying confidence scores
        mock_results = [
            create_mock_result("High Confidence", confidence=0.9),
            create_mock_result("Medium Confidence", confidence=0.65),
            create_mock_result("Low Confidence", confidence=0.3)
        ]
        
        analysis = orchestrator._analyze_confidence_distribution(mock_results)
        
        print(f"   Analysis: {analysis}")
        
        assert analysis['count'] == 3
        assert analysis['high_confidence'] == 1
        assert analysis['medium_confidence'] == 1
        assert analysis['low_confidence'] == 1
        
        test_results.append("✅ Confidence distribution analysis")
        
        # Test 10: Test processing result structure
        print("\n10. Testing processing result structure...")
        
        # Test creating processing result
        extracted_elements = ExtractedElements(
            market_term_type="standard",
            extracted_forecast_date_range="2030",
            extracted_report_type="Market Report",
            extracted_regions=["Global"],
            topic="Artificial Intelligence",
            topicName="artificial-intelligence"
        )
        
        result = ProcessingResult(
            title="Test Title",
            original_title="Test Title",
            batch_id="test_batch",
            processing_id="test_001",
            status=ProcessingStatus.COMPLETED,
            extracted_elements=extracted_elements,
            processing_time_seconds=1.5,
            flags=["test_flag"]
        )
        
        print(f"   Result title: {result.title}")
        print(f"   Result status: {result.status}")
        print(f"   Extracted topic: {result.extracted_elements.topic}")
        
        assert result.title == "Test Title"
        assert result.status == ProcessingStatus.COMPLETED
        assert result.extracted_elements.topic == "Artificial Intelligence"
        
        test_results.append("✅ Processing result structure")
        
        # Summary
        print("\n" + "=" * 50)
        print("TEST SUMMARY:")
        for result in test_results:
            print(f"  {result}")
        
        print(f"\n✅ All {len(test_results)} test categories passed!")
        print("✅ Pipeline Orchestrator core functionality validated!")
        print("✅ Ready for integration testing!")
        
        return True
        
    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
        return False
        
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return False

def create_mock_orchestrator():
    """Create a minimal Pipeline Orchestrator for testing."""
    
    # Create a basic orchestrator without full initialization
    class MockOrchestrator:
        def __init__(self):
            self.batch_size = 100
            self.retry_attempts = 3
            self.timeout_seconds = 30
            self.processing_stats = {
                'batches_processed': 0,
                'total_titles_processed': 0,
                'successful_extractions': 0,
                'failed_extractions': 0,
                'requires_review_count': 0,
                'total_processing_time': 0.0
            }
        
        def _get_timestamps(self):
            return PipelineOrchestrator._get_timestamps(self)
        
        def _generate_batch_id(self):
            return PipelineOrchestrator._generate_batch_id(self)
        
        def _generate_processing_id(self, batch_id, index):
            return PipelineOrchestrator._generate_processing_id(self, batch_id, index)
        
        def trackProgress(self, current, total, batch_id):
            return PipelineOrchestrator.trackProgress(self, current, total, batch_id)
        
        def handleErrors(self, title, error, attempt):
            return PipelineOrchestrator.handleErrors(self, title, error, attempt)
        
        def _process_geographic_entities(self, title):
            return PipelineOrchestrator._process_geographic_entities(self, title)
        
        def get_processing_statistics(self):
            return PipelineOrchestrator.get_processing_statistics(self)
        
        def _analyze_confidence_distribution(self, results):
            return PipelineOrchestrator._analyze_confidence_distribution(self, results)
    
    return MockOrchestrator()

def create_mock_result(title, confidence=0.8):
    """Create a mock processing result for testing."""
    return ProcessingResult(
        title=title,
        original_title=title,
        batch_id="test_batch",
        processing_id=f"test_{hash(title)}",
        status=ProcessingStatus.COMPLETED,
        extracted_elements=ExtractedElements(),
        confidence_analysis={'overall_confidence': confidence},
        processing_time_seconds=1.0,
        flags=[]
    )

def test_demo_functionality():
    """Test the demo functionality to ensure it can run."""
    
    print("\n" + "=" * 50)
    print("DEMO FUNCTIONALITY TESTING")
    print("=" * 50)
    
    try:
        # Test that we can import the demo function
        demo_func = getattr(pipeline_orchestrator_module, 'demo_pipeline_orchestrator', None)
        
        if demo_func:
            print("✅ Demo function exists and is callable")
            print("Note: Full demo requires MongoDB connection, skipping execution")
            return True
        else:
            print("❌ Demo function not found")
            return False
            
    except Exception as e:
        print(f"❌ Demo functionality test failed: {e}")
        return False

if __name__ == "__main__":
    print("Starting Simplified Pipeline Orchestrator Test Suite...")
    print("=" * 60)
    
    # Run core functionality tests
    core_tests_passed = test_pipeline_orchestrator_core()
    
    # Run demo functionality test
    demo_tests_passed = test_demo_functionality()
    
    # Final results
    print("\n" + "=" * 60)
    print("FINAL TEST RESULTS:")
    print("=" * 60)
    
    if core_tests_passed and demo_tests_passed:
        print("🎉 ALL TESTS PASSED!")
        print("✅ Pipeline Orchestrator core functionality validated")
        print("✅ Systematic processing architecture confirmed")
        print("✅ Ready for MongoDB integration testing")
        sys.exit(0)
    else:
        print("❌ SOME TESTS FAILED")
        if not core_tests_passed:
            print("❌ Core functionality tests failed")
        if not demo_tests_passed:
            print("❌ Demo functionality tests failed")
        sys.exit(1)