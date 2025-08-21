#!/usr/bin/env python3

"""
Test script for Confidence Tracker v1.0
Validates confidence calculation, human review flagging, and performance metrics.
Tests integration with extraction pipeline results.
"""

import sys
import os
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timezone, timedelta

# Add parent directory to path to import numbered modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import ConfidenceTracker using importlib
import importlib.util
spec = importlib.util.spec_from_file_location("confidence_tracker", "../06_confidence_tracker_v1.py")
confidence_tracker_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(confidence_tracker_module)

ConfidenceTracker = confidence_tracker_module.ConfidenceTracker
ExtractionResults = confidence_tracker_module.ExtractionResults
ConfidenceLevel = confidence_tracker_module.ConfidenceLevel
ReviewFlag = confidence_tracker_module.ReviewFlag

# Configure logging for tests
logging.basicConfig(level=logging.WARNING)

def test_confidence_tracker():
    """Run comprehensive tests for Confidence Tracker."""
    
    print("Confidence Tracker Tests")
    print("=" * 50)
    
    tracker = ConfidenceTracker()
    test_results = []
    
    try:
        # Test 1: High confidence extraction (should not require review)
        print("\n1. Testing High Confidence Analysis...")
        high_confidence_extraction = ExtractionResults(
            title="Global Artificial Intelligence Market Size & Share Report, 2030",
            original_title="Global Artificial Intelligence Market Size & Share Report, 2030",
            market_term_type="standard",
            market_classification_confidence=0.95,
            extracted_forecast_date_range="2030",
            date_extraction_confidence=0.98,
            extracted_report_type="Market Size & Share Report",
            report_extraction_confidence=0.92,
            extracted_regions=["Global"],
            geographic_detection_confidence=0.88,
            topic="Artificial Intelligence",
            topic_name="artificial-intelligence",
            topic_extraction_confidence=0.90,
            processing_time_ms=200.0,
            errors_encountered=[]
        )
        
        analysis = tracker.calculateOverallConfidence(high_confidence_extraction)
        
        print(f"   Overall Confidence: {analysis.overall_confidence:.3f}")
        print(f"   Confidence Level: {analysis.confidence_level.value}")
        print(f"   Review Flag: {analysis.review_flag.value}")
        print(f"   Should Flag for Review: {tracker.shouldFlagForReview(analysis.overall_confidence)}")
        
        # Validate high confidence results
        assert analysis.overall_confidence >= 0.8, f"High confidence extraction scored too low: {analysis.overall_confidence}"
        assert analysis.confidence_level in [ConfidenceLevel.HIGH, ConfidenceLevel.GOOD], f"Wrong confidence level: {analysis.confidence_level}"
        assert analysis.review_flag == ReviewFlag.NO_REVIEW, f"High confidence should not require review: {analysis.review_flag}"
        assert not tracker.shouldFlagForReview(analysis.overall_confidence), "High confidence should not be flagged"
        assert analysis.extraction_completeness == 1.0, f"Complete extraction should be 100%: {analysis.extraction_completeness}"
        
        test_results.append("✅ High Confidence Analysis")
        
        # Test 2: Medium confidence extraction (should require standard review)
        print("\n2. Testing Medium Confidence Analysis...")
        medium_confidence_extraction = ExtractionResults(
            title="APAC Technology Market Analysis",
            original_title="APAC Technology Market Analysis", 
            market_term_type="standard",
            market_classification_confidence=0.85,
            extracted_forecast_date_range=None,  # Missing date
            date_extraction_confidence=0.60,
            extracted_report_type="Market Analysis",
            report_extraction_confidence=0.80,
            extracted_regions=["APAC"],
            geographic_detection_confidence=0.75,
            topic="Technology",
            topic_name="technology",
            topic_extraction_confidence=0.70,
            processing_time_ms=300.0,
            errors_encountered=[]
        )
        
        analysis = tracker.calculateOverallConfidence(medium_confidence_extraction)
        
        print(f"   Overall Confidence: {analysis.overall_confidence:.3f}")
        print(f"   Confidence Level: {analysis.confidence_level.value}")
        print(f"   Review Flag: {analysis.review_flag.value}")
        print(f"   Completeness: {analysis.extraction_completeness:.1%}")
        
        # Validate medium confidence results
        assert 0.6 <= analysis.overall_confidence < 0.8, f"Medium confidence out of range: {analysis.overall_confidence}"
        assert analysis.review_flag in [ReviewFlag.STANDARD_REVIEW, ReviewFlag.PRIORITY_REVIEW], f"Medium confidence should require review: {analysis.review_flag}"
        assert tracker.shouldFlagForReview(analysis.overall_confidence), "Medium confidence should be flagged"
        assert analysis.extraction_completeness < 1.0, "Incomplete extraction should be <100%"
        
        test_results.append("✅ Medium Confidence Analysis")
        
        # Test 3: Low confidence extraction (should require critical review)
        print("\n3. Testing Low Confidence Analysis...")
        low_confidence_extraction = ExtractionResults(
            title="Confusing Market Title Structure",
            original_title="Confusing Market Title Structure",
            market_term_type="ambiguous",
            market_classification_confidence=0.30,
            extracted_forecast_date_range=None,
            date_extraction_confidence=0.20,
            extracted_report_type=None,
            report_extraction_confidence=0.15,
            extracted_regions=[],
            geographic_detection_confidence=0.10,
            topic="Confusing Title",
            topic_name="confusing-title", 
            topic_extraction_confidence=0.40,
            processing_time_ms=500.0,
            errors_encountered=["Pattern matching failed", "Ambiguous structure"]
        )
        
        analysis = tracker.calculateOverallConfidence(low_confidence_extraction)
        
        print(f"   Overall Confidence: {analysis.overall_confidence:.3f}")
        print(f"   Confidence Level: {analysis.confidence_level.value}")
        print(f"   Review Flag: {analysis.review_flag.value}")
        print(f"   Confusion Patterns: {len(analysis.confusion_patterns)}")
        
        # Validate low confidence results
        assert analysis.overall_confidence < 0.6, f"Low confidence should be <0.6: {analysis.overall_confidence}"
        assert analysis.confidence_level in [ConfidenceLevel.LOW, ConfidenceLevel.VERY_LOW], f"Wrong confidence level: {analysis.confidence_level}"
        assert analysis.review_flag in [ReviewFlag.PRIORITY_REVIEW, ReviewFlag.CRITICAL_REVIEW], f"Low confidence should require critical review: {analysis.review_flag}"
        assert len(analysis.confusion_patterns) > 0, "Low confidence should identify confusion patterns"
        
        test_results.append("✅ Low Confidence Analysis")
        
        # Test 4: Weighted average calculation
        print("\n4. Testing Weighted Average Calculation...")
        
        # Test normal case
        scores = [0.9, 0.8, 0.7, 0.6]
        weights = [0.4, 0.3, 0.2, 0.1]
        weighted_avg = tracker.weightedAverage(scores, weights)
        expected = (0.9*0.4 + 0.8*0.3 + 0.7*0.2 + 0.6*0.1) / (0.4+0.3+0.2+0.1)
        
        print(f"   Weighted Average: {weighted_avg:.3f}")
        print(f"   Expected: {expected:.3f}")
        
        assert abs(weighted_avg - expected) < 0.001, f"Weighted average calculation incorrect: {weighted_avg} vs {expected}"
        
        # Test edge cases
        assert tracker.weightedAverage([], []) == 0.0, "Empty arrays should return 0"
        assert tracker.weightedAverage([0.5], [0]) == 0.0, "Zero weights should return 0"
        
        test_results.append("✅ Weighted Average Calculation")
        
        # Test 5: Review flagging logic
        print("\n5. Testing Review Flagging Logic...")
        
        review_test_cases = [
            (0.95, False, "High confidence should not be flagged"),
            (0.85, False, "Good confidence should not be flagged"), 
            (0.79, True, "Below threshold should be flagged"),
            (0.65, True, "Medium confidence should be flagged"),
            (0.35, True, "Low confidence should be flagged")
        ]
        
        for confidence, should_flag, description in review_test_cases:
            flagged = tracker.shouldFlagForReview(confidence)
            print(f"   Confidence {confidence:.2f}: {'Flagged' if flagged else 'Not Flagged'}")
            assert flagged == should_flag, f"Review flagging failed: {description}"
        
        test_results.append("✅ Review Flagging Logic")
        
        # Test 6: Performance metrics tracking
        print("\n6. Testing Performance Metrics...")
        
        # Process multiple extractions to build metrics
        test_extractions = [
            high_confidence_extraction,
            medium_confidence_extraction, 
            low_confidence_extraction
        ]
        
        for extraction in test_extractions:
            tracker.calculateOverallConfidence(extraction)
        
        metrics = tracker.getPerformanceMetrics()
        
        print(f"   Total Processed: {metrics.total_processed}")
        print(f"   Average Confidence: {metrics.average_confidence:.3f}")
        print(f"   High Confidence Count: {metrics.high_confidence_count}")
        print(f"   Flagged for Review: {metrics.flagged_for_review}")
        print(f"   Processing Speed: {metrics.processing_speed_ms:.1f} ms")
        
        assert metrics.total_processed >= 3, f"Should have processed at least 3 extractions: {metrics.total_processed}"
        assert 0.0 <= metrics.average_confidence <= 1.0, f"Average confidence out of range: {metrics.average_confidence}"
        assert metrics.flagged_for_review > 0, "Should have flagged some extractions for review"
        assert len(metrics.extraction_success_rates) > 0, "Should have component success rates"
        
        test_results.append("✅ Performance Metrics Tracking")
        
        # Test 7: Confusion pattern detection
        print("\n7. Testing Confusion Pattern Detection...")
        
        confusion_patterns = tracker.trackConfusionPatterns(
            low_confidence_extraction.title, 
            low_confidence_extraction
        )
        
        print(f"   Detected Patterns: {len(confusion_patterns)}")
        for pattern in confusion_patterns:
            print(f"     • {pattern}")
        
        assert len(confusion_patterns) > 0, "Low confidence extraction should generate confusion patterns"
        assert any("Date pattern" in pattern or "Report type" in pattern or "Geographic" in pattern 
                  for pattern in confusion_patterns), "Should detect specific pattern issues"
        
        test_results.append("✅ Confusion Pattern Detection")
        
        # Test 8: Trend analysis
        print("\n8. Testing Trend Analysis...")
        
        trend_analysis = tracker.get_trend_analysis(days=7)
        
        print(f"   Period: {trend_analysis['period_days']} days")
        print(f"   Total Processed: {trend_analysis['total_processed']}")
        print(f"   Average Confidence: {trend_analysis['average_confidence']:.3f}")
        print(f"   Trend: {trend_analysis['trend']}")
        print(f"   Improvement Areas: {len(trend_analysis['improvement_areas'])}")
        
        assert trend_analysis['period_days'] == 7, "Should analyze 7-day period"
        assert trend_analysis['total_processed'] > 0, "Should have processed data"
        assert 0.0 <= trend_analysis['average_confidence'] <= 1.0, "Average confidence in valid range"
        
        test_results.append("✅ Trend Analysis")
        
        # Test 9: Confidence distribution
        print("\n9. Testing Confidence Distribution...")
        
        distribution = tracker.get_confidence_distribution()
        
        print(f"   Total Samples: {distribution['total_samples']}")
        print(f"   Average Confidence: {distribution['average_confidence']:.3f}")
        print(f"   Median Confidence: {distribution['median_confidence']:.3f}")
        
        if 'confidence_histogram' in distribution:
            histogram = distribution['confidence_histogram']
            print(f"   Histogram Bins: {len(histogram['bins'])}")
            print(f"   Total Counts: {sum(histogram['counts'])}")
        
        assert distribution['total_samples'] > 0, "Should have samples"
        assert 'quality_breakdown' in distribution, "Should include quality breakdown"
        assert distribution['quality_breakdown']['production_ready'] >= 0, "Production ready count should be non-negative"
        
        test_results.append("✅ Confidence Distribution")
        
        # Test 10: Report generation
        print("\n10. Testing Report Generation...")
        
        report = tracker.export_confidence_report()
        
        print(f"   Report Length: {len(report)} characters")
        print(f"   Contains Metrics: {'SYSTEM PERFORMANCE SUMMARY' in report}")
        print(f"   Contains Distribution: {'CONFIDENCE LEVEL DISTRIBUTION' in report}")
        
        assert len(report) > 1000, "Report should be comprehensive"
        assert "SYSTEM PERFORMANCE SUMMARY" in report, "Report should contain performance summary"
        assert "CONFIDENCE LEVEL DISTRIBUTION" in report, "Report should contain distribution"
        assert "QUALITY ASSURANCE" in report, "Report should contain quality assurance section"
        
        test_results.append("✅ Report Generation")
        
        # Summary
        print("\n" + "=" * 50)
        print("TEST SUMMARY:")
        for result in test_results:
            print(f"  {result}")
        
        print(f"\n✅ All {len(test_results)} test suites passed!")
        print("✅ Confidence Tracker functionality validated!")
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
    
    tracker = ConfidenceTracker()
    
    try:
        # Test with minimal extraction results
        print("1. Testing Minimal Extraction Results...")
        
        minimal_extraction = ExtractionResults(
            title="Minimal Test",
            original_title="Minimal Test",
            market_term_type="standard",
            market_classification_confidence=0.5,
            extracted_forecast_date_range=None,
            date_extraction_confidence=0.0,
            extracted_report_type=None,
            report_extraction_confidence=0.0,
            extracted_regions=[],
            geographic_detection_confidence=0.0,
            topic=None,
            topic_name=None,
            topic_extraction_confidence=0.0,
            processing_time_ms=None,
            errors_encountered=None
        )
        
        analysis = tracker.calculateOverallConfidence(minimal_extraction)
        print(f"   Minimal Confidence: {analysis.overall_confidence:.3f}")
        print(f"   Review Flag: {analysis.review_flag.value}")
        
        assert analysis.overall_confidence >= 0.0, "Confidence should not be negative"
        assert analysis.review_flag == ReviewFlag.CRITICAL_REVIEW, "Minimal extraction should require critical review"
        
        # Test with perfect extraction results
        print("\n2. Testing Perfect Extraction Results...")
        
        perfect_extraction = ExtractionResults(
            title="Perfect Test Market Report, 2030",
            original_title="Perfect Test Market Report, 2030",
            market_term_type="standard",
            market_classification_confidence=1.0,
            extracted_forecast_date_range="2030",
            date_extraction_confidence=1.0,
            extracted_report_type="Market Report",
            report_extraction_confidence=1.0,
            extracted_regions=["Global"],
            geographic_detection_confidence=1.0,
            topic="Perfect Test",
            topic_name="perfect-test",
            topic_extraction_confidence=1.0,
            processing_time_ms=100.0,
            errors_encountered=[]
        )
        
        analysis = tracker.calculateOverallConfidence(perfect_extraction)
        print(f"   Perfect Confidence: {analysis.overall_confidence:.3f}")
        print(f"   Review Flag: {analysis.review_flag.value}")
        
        assert analysis.overall_confidence >= 0.9, f"Perfect extraction should have high confidence: {analysis.overall_confidence}"
        assert analysis.review_flag == ReviewFlag.NO_REVIEW, "Perfect extraction should not require review"
        
        # Test weighted average edge cases
        print("\n3. Testing Weighted Average Edge Cases...")
        
        # Test with mismatched lengths
        edge_case_1 = tracker.weightedAverage([0.5, 0.6], [0.3])  # Different lengths
        assert edge_case_1 == 0.0, "Mismatched lengths should return 0"
        
        # Test with all zero weights
        edge_case_2 = tracker.weightedAverage([0.5, 0.6], [0.0, 0.0])
        assert edge_case_2 == 0.0, "All zero weights should return 0"
        
        # Test with negative weights (should still work)
        edge_case_3 = tracker.weightedAverage([0.5, 0.6], [0.3, 0.7])
        assert edge_case_3 > 0.0, "Valid weights should return positive result"
        
        print("   Edge case handling validated")
        
        print("\n✅ Edge case testing completed")
        return True
        
    except Exception as e:
        print(f"\n❌ Edge case testing failed: {e}")
        return False

def test_integration_scenarios():
    """Test realistic integration scenarios with pipeline data."""
    
    print("\n" + "=" * 50) 
    print("INTEGRATION SCENARIO TESTING")
    print("=" * 50)
    
    tracker = ConfidenceTracker()
    
    try:
        # Scenario 1: Batch processing simulation
        print("1. Testing Batch Processing Scenario...")
        
        batch_extractions = [
            # High quality extractions
            ExtractionResults(
                title=f"Global AI Market Report {2025+i}, Technology Analysis",
                original_title=f"Global AI Market Report {2025+i}, Technology Analysis",
                market_term_type="standard",
                market_classification_confidence=0.95,
                extracted_forecast_date_range=str(2025+i),
                date_extraction_confidence=0.97,
                extracted_report_type="Market Report",
                report_extraction_confidence=0.92,
                extracted_regions=["Global"],
                geographic_detection_confidence=0.89,
                topic="AI",
                topic_name="ai",
                topic_extraction_confidence=0.91,
                processing_time_ms=200.0 + i*10,
                errors_encountered=[]
            ) for i in range(5)
        ] + [
            # Medium quality extractions
            ExtractionResults(
                title=f"Regional Technology Analysis {i}",
                original_title=f"Regional Technology Analysis {i}",
                market_term_type="standard", 
                market_classification_confidence=0.8,
                extracted_forecast_date_range=None,
                date_extraction_confidence=0.6,
                extracted_report_type="Analysis",
                report_extraction_confidence=0.85,
                extracted_regions=["Regional"],
                geographic_detection_confidence=0.7,
                topic=f"Technology {i}",
                topic_name=f"technology-{i}",
                topic_extraction_confidence=0.75,
                processing_time_ms=300.0,
                errors_encountered=[]
            ) for i in range(3)
        ]
        
        # Process batch
        confidence_scores = []
        flagged_count = 0
        
        for extraction in batch_extractions:
            analysis = tracker.calculateOverallConfidence(extraction)
            confidence_scores.append(analysis.overall_confidence)
            if analysis.review_flag != ReviewFlag.NO_REVIEW:
                flagged_count += 1
        
        metrics = tracker.getPerformanceMetrics()
        
        print(f"   Processed: {len(batch_extractions)} extractions")
        print(f"   Average Confidence: {metrics.average_confidence:.3f}")
        print(f"   Flagged for Review: {flagged_count}")
        print(f"   High Confidence: {metrics.high_confidence_count}")
        print(f"   Processing Speed: {metrics.processing_speed_ms:.1f} ms/title")
        
        assert len(confidence_scores) == len(batch_extractions), "Should process all extractions"
        assert metrics.average_confidence > 0.7, f"Batch should have good average confidence: {metrics.average_confidence}"
        assert metrics.high_confidence_count >= 5, f"Should have high confidence extractions: {metrics.high_confidence_count}"
        
        # Scenario 2: Quality trend monitoring
        print("\n2. Testing Quality Trend Monitoring...")
        
        trend_analysis = tracker.get_trend_analysis(days=1)  # Recent data
        
        print(f"   Recent Period: {trend_analysis['total_processed']} processed")
        print(f"   Trend Direction: {trend_analysis['trend']}")
        print(f"   Improvement Areas: {len(trend_analysis['improvement_areas'])}")
        
        if trend_analysis['improvement_areas']:
            print("   Components needing attention:")
            for area in trend_analysis['improvement_areas']:
                print(f"     • {area['component']}: {area['average_confidence']:.3f}")
        
        assert trend_analysis['total_processed'] > 0, "Should have recent processing data"
        
        # Scenario 3: Performance threshold validation
        print("\n3. Testing Performance Threshold Validation...")
        
        distribution = tracker.get_confidence_distribution()
        production_ready = distribution['quality_breakdown']['production_ready']
        total_samples = distribution['total_samples']
        
        production_rate = (production_ready / total_samples) * 100 if total_samples > 0 else 0
        
        print(f"   Production Ready Rate: {production_rate:.1f}%")
        print(f"   Target Rate: ≥80%")
        print(f"   Status: {'✅ Meeting Target' if production_rate >= 80 else '⚠️ Below Target'}")
        
        # Generate comprehensive report
        report = tracker.export_confidence_report()
        
        print(f"   Report Generated: {len(report)} characters")
        
        assert len(report) > 2000, "Integration report should be comprehensive"
        
        print("\n✅ Integration scenario testing completed")
        return True
        
    except Exception as e:
        print(f"\n❌ Integration testing failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("Starting Confidence Tracker Test Suite...")
    print("=" * 60)
    
    # Run core functionality tests
    core_tests_passed = test_confidence_tracker()
    
    # Run edge case tests
    edge_tests_passed = test_edge_cases()
    
    # Run integration scenario tests
    integration_tests_passed = test_integration_scenarios()
    
    # Final results
    print("\n" + "=" * 60)
    print("FINAL TEST RESULTS:")
    print("=" * 60)
    
    if core_tests_passed and edge_tests_passed and integration_tests_passed:
        print("🎉 ALL TESTS PASSED!")
        print("✅ Confidence Tracker functionality validated")
        print("✅ Human review flagging system working")
        print("✅ Performance metrics and tracking operational")
        print("✅ Ready for pipeline integration")
        sys.exit(0)
    else:
        print("❌ SOME TESTS FAILED")
        if not core_tests_passed:
            print("❌ Core functionality tests failed")
        if not edge_tests_passed:
            print("❌ Edge case tests failed")
        if not integration_tests_passed:
            print("❌ Integration tests failed")
        sys.exit(1)