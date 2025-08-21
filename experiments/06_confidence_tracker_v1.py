#!/usr/bin/env python3

"""
Confidence Tracking System v1.0
Calculates confidence scores for extraction results and flags titles requiring human review.
Integrates with all pipeline extractors (01-05) to provide comprehensive quality assurance.
Created for Market Research Title Parser project.
"""

import os
import re
import logging
import json
from typing import Dict, List, Optional, Tuple, Any, Union
from dataclasses import dataclass, asdict
from enum import Enum
from datetime import datetime, timezone
from collections import defaultdict, Counter
import statistics
import pytz

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ConfidenceLevel(Enum):
    """Confidence level classifications."""
    HIGH = "high"           # >= 0.9
    GOOD = "good"           # >= 0.8
    MEDIUM = "medium"       # >= 0.6
    LOW = "low"             # >= 0.4
    VERY_LOW = "very_low"   # < 0.4

class ReviewFlag(Enum):
    """Human review flags."""
    NO_REVIEW = "no_review"
    STANDARD_REVIEW = "standard_review"
    PRIORITY_REVIEW = "priority_review"
    CRITICAL_REVIEW = "critical_review"

@dataclass
class ExtractionResults:
    """Container for all extraction results from pipeline components."""
    title: str
    original_title: str
    
    # Market Term Classification (01)
    market_term_type: str
    market_classification_confidence: float
    
    # Date Extraction (02)
    extracted_forecast_date_range: Optional[str]
    date_extraction_confidence: float
    
    # Report Type Extraction (03)
    extracted_report_type: Optional[str]
    report_extraction_confidence: float
    
    # Geographic Detection (04)
    extracted_regions: List[str]
    geographic_detection_confidence: float
    
    # Topic Extraction (05)
    topic: Optional[str]
    topic_name: Optional[str]
    topic_extraction_confidence: float
    
    # Processing metadata
    processing_time_ms: Optional[float] = None
    errors_encountered: List[str] = None

@dataclass
class ConfidenceAnalysis:
    """Comprehensive confidence analysis result."""
    title: str
    overall_confidence: float
    confidence_level: ConfidenceLevel
    review_flag: ReviewFlag
    weighted_scores: Dict[str, float]
    component_scores: Dict[str, float]
    extraction_completeness: float
    confusion_patterns: List[str]
    quality_indicators: Dict[str, Any]
    recommendation: str
    processing_timestamp: datetime

@dataclass
class PerformanceMetrics:
    """System performance metrics."""
    total_processed: int
    high_confidence_count: int
    good_confidence_count: int
    medium_confidence_count: int
    low_confidence_count: int
    very_low_confidence_count: int
    flagged_for_review: int
    average_confidence: float
    extraction_success_rates: Dict[str, float]
    processing_speed_ms: float
    trend_direction: str

@dataclass
class ConfusionPattern:
    """Pattern confusion tracking."""
    title: str
    component: str
    expected_result: Optional[str]
    actual_result: Optional[str]
    confidence_score: float
    pattern_issue: str
    timestamp: datetime

class ConfidenceTracker:
    """
    Confidence Tracking System for market research title extraction pipeline.
    
    Calculates weighted confidence scores across all extraction components,
    flags titles for human review, and tracks performance metrics for 
    continuous system improvement.
    """
    
    def __init__(self, pattern_library_manager=None, mongodb_client=None):
        """
        Initialize the Confidence Tracker.
        
        Args:
            pattern_library_manager: Optional pattern library for confusion tracking
            mongodb_client: Optional MongoDB client for metrics storage
        """
        self.pattern_library_manager = pattern_library_manager
        self.mongodb_client = mongodb_client
        
        # Confidence tracking storage
        self.confidence_history = []
        self.confusion_patterns = []
        self.performance_metrics = {
            'total_processed': 0,
            'confidence_scores': [],
            'extraction_completeness': [],
            'component_success_rates': defaultdict(list),
            'processing_times': [],
            'review_flags': defaultdict(int)
        }
        
        # Confidence calculation weights
        self._initialize_confidence_weights()
        
        # Review thresholds
        self.review_threshold = 0.8
        self.priority_review_threshold = 0.6
        self.critical_review_threshold = 0.4
        
        logger.info("ConfidenceTracker initialized - ready for quality assurance processing")
    
    def _initialize_confidence_weights(self) -> None:
        """Initialize weights for different extraction components."""
        
        # Component weights based on importance and reliability
        self.component_weights = {
            'market_classification': 0.15,    # Less critical, high accuracy expected
            'date_extraction': 0.20,          # Important, affects topic extraction
            'report_extraction': 0.15,        # Important, affects topic extraction
            'geographic_detection': 0.25,     # Critical, complex patterns
            'topic_extraction': 0.25          # Most critical, final output
        }
        
        # Completeness weights (penalty for missing extractions)
        self.completeness_weights = {
            'date_missing': -0.1,
            'report_missing': -0.05,
            'regions_missing': -0.15,
            'topic_missing': -0.3
        }
        
        # Quality indicators and their impact on confidence
        self.quality_indicators = {
            'technical_compounds_preserved': +0.05,
            'proper_normalization': +0.03,
            'consistent_formatting': +0.02,
            'processing_errors': -0.15,
            'pattern_conflicts': -0.10
        }
        
        logger.debug("Confidence calculation weights initialized")
    
    def _get_timestamps(self) -> tuple:
        """Generate PDT and UTC timestamps."""
        utc_now = datetime.now(timezone.utc)
        pdt_tz = pytz.timezone('America/Los_Angeles')
        pdt_now = utc_now.astimezone(pdt_tz)
        
        pdt_str = pdt_now.strftime('%Y-%m-%d %H:%M:%S %Z')
        utc_str = utc_now.strftime('%Y-%m-%d %H:%M:%S UTC')
        
        return pdt_str, utc_str, utc_now
    
    def calculateOverallConfidence(self, extraction_results: ExtractionResults) -> ConfidenceAnalysis:
        """
        Calculate overall confidence score for extraction results.
        
        Args:
            extraction_results: Complete extraction results from pipeline
            
        Returns:
            ConfidenceAnalysis with detailed confidence assessment
        """
        title = extraction_results.title
        
        # Step 1: Extract individual component confidence scores
        component_scores = {
            'market_classification': extraction_results.market_classification_confidence,
            'date_extraction': extraction_results.date_extraction_confidence,
            'report_extraction': extraction_results.report_extraction_confidence,
            'geographic_detection': extraction_results.geographic_detection_confidence,
            'topic_extraction': extraction_results.topic_extraction_confidence
        }
        
        # Step 2: Calculate weighted average of component scores
        weighted_score = self.weightedAverage(
            list(component_scores.values()),
            list(self.component_weights.values())
        )
        
        # Step 3: Apply extraction completeness adjustments
        completeness_score = self._calculate_extraction_completeness(extraction_results)
        completeness_adjustment = self._get_completeness_adjustment(extraction_results)
        
        # Step 4: Apply quality indicator adjustments
        quality_adjustment = self._assess_quality_indicators(extraction_results)
        
        # Step 5: Calculate final overall confidence
        overall_confidence = max(0.0, min(1.0, 
            weighted_score + completeness_adjustment + quality_adjustment
        ))
        
        # Step 6: Determine confidence level and review flag
        confidence_level = self._get_confidence_level(overall_confidence)
        review_flag = self._determine_review_flag(overall_confidence, extraction_results)
        
        # Step 7: Track confusion patterns
        confusion_patterns = self.trackConfusionPatterns(title, extraction_results)
        
        # Step 8: Generate quality indicators summary
        quality_indicators = {
            'extraction_completeness': completeness_score,
            'weighted_component_score': weighted_score,
            'completeness_adjustment': completeness_adjustment,
            'quality_adjustment': quality_adjustment,
            'component_breakdown': component_scores,
            'processing_time_ms': extraction_results.processing_time_ms or 0
        }
        
        # Step 9: Generate recommendation
        recommendation = self._generate_recommendation(
            overall_confidence, confidence_level, review_flag, extraction_results
        )
        
        # Create confidence analysis result
        analysis = ConfidenceAnalysis(
            title=title,
            overall_confidence=round(overall_confidence, 3),
            confidence_level=confidence_level,
            review_flag=review_flag,
            weighted_scores=dict(zip(component_scores.keys(), 
                [score * weight for score, weight in zip(component_scores.values(), self.component_weights.values())])),
            component_scores=component_scores,
            extraction_completeness=completeness_score,
            confusion_patterns=confusion_patterns,
            quality_indicators=quality_indicators,
            recommendation=recommendation,
            processing_timestamp=datetime.now(timezone.utc)
        )
        
        # Track for performance metrics
        self._track_analysis_result(analysis, extraction_results)
        
        logger.debug(f"Calculated confidence {overall_confidence:.3f} for: {title[:50]}...")
        
        return analysis
    
    def weightedAverage(self, confidence_scores: List[float], weights: List[float]) -> float:
        """
        Calculate weighted average of confidence scores.
        
        Args:
            confidence_scores: List of individual confidence scores
            weights: List of weights for each score
            
        Returns:
            Weighted average confidence score
        """
        if not confidence_scores or not weights or len(confidence_scores) != len(weights):
            logger.warning("Invalid input for weighted average calculation")
            return 0.0
        
        total_weighted_sum = sum(score * weight for score, weight in zip(confidence_scores, weights))
        total_weights = sum(weights)
        
        if total_weights == 0:
            return 0.0
        
        return total_weighted_sum / total_weights
    
    def shouldFlagForReview(self, confidence: float) -> bool:
        """
        Determine if a title should be flagged for human review.
        
        Args:
            confidence: Overall confidence score
            
        Returns:
            True if human review is needed (< 0.8)
        """
        return confidence < self.review_threshold
    
    def trackConfusionPatterns(self, title: str, extraction_results: ExtractionResults) -> List[str]:
        """
        Track pattern confusion for library improvement.
        
        Args:
            title: Original title
            extraction_results: Extraction results to analyze
            
        Returns:
            List of confusion patterns identified
        """
        confusion_patterns = []
        
        # Check for low confidence components that might indicate pattern issues
        component_confidences = {
            'market_classification': extraction_results.market_classification_confidence,
            'date_extraction': extraction_results.date_extraction_confidence,
            'report_extraction': extraction_results.report_extraction_confidence,
            'geographic_detection': extraction_results.geographic_detection_confidence,
            'topic_extraction': extraction_results.topic_extraction_confidence
        }
        
        for component, confidence in component_confidences.items():
            if confidence < 0.7:  # Low confidence threshold for pattern confusion
                pattern_issue = self._identify_pattern_issue(component, extraction_results)
                if pattern_issue:
                    confusion_patterns.append(f"{component}: {pattern_issue}")
                    
                    # Store detailed confusion pattern
                    confusion = ConfusionPattern(
                        title=title,
                        component=component,
                        expected_result=None,  # Would need ground truth data
                        actual_result=self._get_component_result(component, extraction_results),
                        confidence_score=confidence,
                        pattern_issue=pattern_issue,
                        timestamp=datetime.now(timezone.utc)
                    )
                    self.confusion_patterns.append(confusion)
        
        # Check for conflicting extractions
        conflicts = self._detect_extraction_conflicts(extraction_results)
        confusion_patterns.extend(conflicts)
        
        return confusion_patterns
    
    def getPerformanceMetrics(self) -> PerformanceMetrics:
        """
        Get comprehensive system performance statistics.
        
        Returns:
            PerformanceMetrics with current system performance
        """
        total_processed = self.performance_metrics['total_processed']
        
        if total_processed == 0:
            return PerformanceMetrics(
                total_processed=0,
                high_confidence_count=0,
                good_confidence_count=0,
                medium_confidence_count=0,
                low_confidence_count=0,
                very_low_confidence_count=0,
                flagged_for_review=0,
                average_confidence=0.0,
                extraction_success_rates={},
                processing_speed_ms=0.0,
                trend_direction="stable"
            )
        
        confidence_scores = self.performance_metrics['confidence_scores']
        
        # Calculate confidence level counts
        level_counts = {
            'high': sum(1 for score in confidence_scores if score >= 0.9),
            'good': sum(1 for score in confidence_scores if 0.8 <= score < 0.9),
            'medium': sum(1 for score in confidence_scores if 0.6 <= score < 0.8),
            'low': sum(1 for score in confidence_scores if 0.4 <= score < 0.6),
            'very_low': sum(1 for score in confidence_scores if score < 0.4)
        }
        
        # Calculate extraction success rates
        success_rates = {}
        for component, scores in self.performance_metrics['component_success_rates'].items():
            if scores:
                success_rates[component] = sum(1 for score in scores if score >= 0.8) / len(scores)
        
        # Calculate average processing speed
        processing_times = self.performance_metrics['processing_times']
        avg_speed = statistics.mean(processing_times) if processing_times else 0.0
        
        # Calculate trend direction
        trend_direction = self._calculate_trend_direction(confidence_scores)
        
        return PerformanceMetrics(
            total_processed=total_processed,
            high_confidence_count=level_counts['high'],
            good_confidence_count=level_counts['good'],
            medium_confidence_count=level_counts['medium'],
            low_confidence_count=level_counts['low'],
            very_low_confidence_count=level_counts['very_low'],
            flagged_for_review=self.performance_metrics['review_flags'].get('flagged', 0),
            average_confidence=round(statistics.mean(confidence_scores), 3) if confidence_scores else 0.0,
            extraction_success_rates=success_rates,
            processing_speed_ms=round(avg_speed, 2),
            trend_direction=trend_direction
        )
    
    def _calculate_extraction_completeness(self, extraction_results: ExtractionResults) -> float:
        """Calculate extraction completeness score (0.0 - 1.0)."""
        completeness_score = 0.0
        total_components = 4  # date, report, regions, topic (market classification always present)
        
        if extraction_results.extracted_forecast_date_range:
            completeness_score += 0.25
        if extraction_results.extracted_report_type:
            completeness_score += 0.25
        if extraction_results.extracted_regions:
            completeness_score += 0.25
        if extraction_results.topic:
            completeness_score += 0.25
        
        return completeness_score
    
    def _get_completeness_adjustment(self, extraction_results: ExtractionResults) -> float:
        """Calculate confidence adjustment based on extraction completeness."""
        adjustment = 0.0
        
        if not extraction_results.extracted_forecast_date_range:
            adjustment += self.completeness_weights['date_missing']
        if not extraction_results.extracted_report_type:
            adjustment += self.completeness_weights['report_missing']
        if not extraction_results.extracted_regions:
            adjustment += self.completeness_weights['regions_missing']
        if not extraction_results.topic:
            adjustment += self.completeness_weights['topic_missing']
        
        return adjustment
    
    def _assess_quality_indicators(self, extraction_results: ExtractionResults) -> float:
        """Assess quality indicators and return confidence adjustment."""
        adjustment = 0.0
        
        # Check for technical compounds preservation
        if extraction_results.topic and re.search(r'\b[A-Z0-9]+\b', extraction_results.topic):
            adjustment += self.quality_indicators['technical_compounds_preserved']
        
        # Check for proper normalization
        if extraction_results.topic_name and re.match(r'^[a-z0-9-]+$', extraction_results.topic_name):
            adjustment += self.quality_indicators['proper_normalization']
        
        # Check for processing errors
        if extraction_results.errors_encountered:
            adjustment += self.quality_indicators['processing_errors']
        
        return adjustment
    
    def _get_confidence_level(self, confidence: float) -> ConfidenceLevel:
        """Determine confidence level from score."""
        if confidence >= 0.9:
            return ConfidenceLevel.HIGH
        elif confidence >= 0.8:
            return ConfidenceLevel.GOOD
        elif confidence >= 0.6:
            return ConfidenceLevel.MEDIUM
        elif confidence >= 0.4:
            return ConfidenceLevel.LOW
        else:
            return ConfidenceLevel.VERY_LOW
    
    def _determine_review_flag(self, confidence: float, extraction_results: ExtractionResults) -> ReviewFlag:
        """Determine appropriate review flag based on confidence and results."""
        if confidence >= self.review_threshold:
            return ReviewFlag.NO_REVIEW
        elif confidence >= self.priority_review_threshold:
            return ReviewFlag.STANDARD_REVIEW
        elif confidence >= self.critical_review_threshold:
            return ReviewFlag.PRIORITY_REVIEW
        else:
            return ReviewFlag.CRITICAL_REVIEW
    
    def _identify_pattern_issue(self, component: str, extraction_results: ExtractionResults) -> Optional[str]:
        """Identify specific pattern issues for a component."""
        issues = {
            'date_extraction': self._check_date_pattern_issues(extraction_results),
            'report_extraction': self._check_report_pattern_issues(extraction_results),
            'geographic_detection': self._check_geographic_pattern_issues(extraction_results),
            'topic_extraction': self._check_topic_pattern_issues(extraction_results)
        }
        
        return issues.get(component)
    
    def _check_date_pattern_issues(self, extraction_results: ExtractionResults) -> Optional[str]:
        """Check for date pattern issues."""
        if not extraction_results.extracted_forecast_date_range:
            # Check if title likely contains a date that wasn't extracted
            if re.search(r'\b(20[0-9]{2}|19[0-9]{2})\b', extraction_results.title):
                return "Date pattern present but not extracted"
        return None
    
    def _check_report_pattern_issues(self, extraction_results: ExtractionResults) -> Optional[str]:
        """Check for report type pattern issues."""
        if not extraction_results.extracted_report_type:
            common_report_terms = ['report', 'analysis', 'study', 'outlook', 'forecast']
            title_lower = extraction_results.title.lower()
            if any(term in title_lower for term in common_report_terms):
                return "Report type indicators present but not extracted"
        return None
    
    def _check_geographic_pattern_issues(self, extraction_results: ExtractionResults) -> Optional[str]:
        """Check for geographic pattern issues."""
        if not extraction_results.extracted_regions:
            common_regions = ['global', 'north america', 'europe', 'asia', 'apac', 'china', 'us', 'uk']
            title_lower = extraction_results.title.lower()
            if any(region in title_lower for region in common_regions):
                return "Geographic indicators present but not extracted"
        return None
    
    def _check_topic_pattern_issues(self, extraction_results: ExtractionResults) -> Optional[str]:
        """Check for topic extraction pattern issues."""
        if not extraction_results.topic:
            return "No topic extracted from title"
        elif len(extraction_results.topic.strip()) < 2:
            return "Extracted topic too short"
        return None
    
    def _detect_extraction_conflicts(self, extraction_results: ExtractionResults) -> List[str]:
        """Detect conflicts between different extractions."""
        conflicts = []
        
        # Check for date conflicts (date in topic when should be extracted separately)
        if extraction_results.topic and re.search(r'\b20[0-9]{2}\b', extraction_results.topic):
            if extraction_results.extracted_forecast_date_range:
                conflicts.append("Date appears in both topic and date extraction")
        
        # Check for region conflicts (region in topic when should be extracted separately)
        if extraction_results.topic and extraction_results.extracted_regions:
            topic_lower = extraction_results.topic.lower()
            for region in extraction_results.extracted_regions:
                if region.lower() in topic_lower:
                    conflicts.append(f"Region '{region}' appears in both topic and region extraction")
        
        return conflicts
    
    def _get_component_result(self, component: str, extraction_results: ExtractionResults) -> Optional[str]:
        """Get the actual result for a specific component."""
        component_results = {
            'market_classification': extraction_results.market_term_type,
            'date_extraction': extraction_results.extracted_forecast_date_range,
            'report_extraction': extraction_results.extracted_report_type,
            'geographic_detection': ', '.join(extraction_results.extracted_regions) if extraction_results.extracted_regions else None,
            'topic_extraction': extraction_results.topic
        }
        
        return component_results.get(component)
    
    def _generate_recommendation(self, confidence: float, confidence_level: ConfidenceLevel, 
                               review_flag: ReviewFlag, extraction_results: ExtractionResults) -> str:
        """Generate human-readable recommendation based on analysis."""
        if review_flag == ReviewFlag.NO_REVIEW:
            return f"High quality extraction ({confidence:.1%}) - ready for production use"
        elif review_flag == ReviewFlag.STANDARD_REVIEW:
            return f"Good extraction ({confidence:.1%}) - minor review recommended"
        elif review_flag == ReviewFlag.PRIORITY_REVIEW:
            return f"Moderate confidence ({confidence:.1%}) - priority review needed"
        else:
            return f"Low confidence ({confidence:.1%}) - critical review required"
    
    def _track_analysis_result(self, analysis: ConfidenceAnalysis, extraction_results: ExtractionResults) -> None:
        """Track analysis result for performance metrics."""
        self.performance_metrics['total_processed'] += 1
        self.performance_metrics['confidence_scores'].append(analysis.overall_confidence)
        self.performance_metrics['extraction_completeness'].append(analysis.extraction_completeness)
        
        # Track component success rates
        for component, score in analysis.component_scores.items():
            self.performance_metrics['component_success_rates'][component].append(score)
        
        # Track processing time
        if extraction_results.processing_time_ms:
            self.performance_metrics['processing_times'].append(extraction_results.processing_time_ms)
        
        # Track review flags
        flag_key = 'flagged' if analysis.review_flag != ReviewFlag.NO_REVIEW else 'not_flagged'
        self.performance_metrics['review_flags'][flag_key] += 1
        
        # Store in history
        self.confidence_history.append(analysis)
    
    def _calculate_trend_direction(self, confidence_scores: List[float]) -> str:
        """Calculate trend direction for confidence scores."""
        if len(confidence_scores) < 10:
            return "insufficient_data"
        
        # Compare recent scores to earlier scores
        recent_scores = confidence_scores[-10:]
        earlier_scores = confidence_scores[-20:-10] if len(confidence_scores) >= 20 else confidence_scores[:-10]
        
        if not earlier_scores:
            return "stable"
        
        recent_avg = statistics.mean(recent_scores)
        earlier_avg = statistics.mean(earlier_scores)
        
        difference = recent_avg - earlier_avg
        
        if difference > 0.05:
            return "improving"
        elif difference < -0.05:
            return "declining"
        else:
            return "stable"
    
    def get_trend_analysis(self, days: int = 7) -> Dict[str, Any]:
        """
        Get trend analysis for confidence scores over time.
        
        Args:
            days: Number of days to analyze
            
        Returns:
            Dictionary with trend analysis data
        """
        from datetime import timedelta
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)
        
        recent_analyses = [
            analysis for analysis in self.confidence_history
            if analysis.processing_timestamp >= cutoff_date
        ]
        
        if not recent_analyses:
            return {
                'period_days': days,
                'total_processed': 0,
                'trend': 'no_data',
                'confidence_distribution': {},
                'improvement_areas': []
            }
        
        confidence_scores = [analysis.overall_confidence for analysis in recent_analyses]
        
        # Calculate confidence distribution
        distribution = {
            'high': sum(1 for score in confidence_scores if score >= 0.9),
            'good': sum(1 for score in confidence_scores if 0.8 <= score < 0.9),
            'medium': sum(1 for score in confidence_scores if 0.6 <= score < 0.8),
            'low': sum(1 for score in confidence_scores if 0.4 <= score < 0.6),
            'very_low': sum(1 for score in confidence_scores if score < 0.4)
        }
        
        # Identify improvement areas
        improvement_areas = []
        component_averages = defaultdict(list)
        
        for analysis in recent_analyses:
            for component, score in analysis.component_scores.items():
                component_averages[component].append(score)
        
        for component, scores in component_averages.items():
            avg_score = statistics.mean(scores)
            if avg_score < 0.8:
                improvement_areas.append({
                    'component': component,
                    'average_confidence': round(avg_score, 3),
                    'suggestion': f"Review {component} patterns and accuracy"
                })
        
        return {
            'period_days': days,
            'total_processed': len(recent_analyses),
            'average_confidence': round(statistics.mean(confidence_scores), 3),
            'trend': self._calculate_trend_direction(confidence_scores),
            'confidence_distribution': distribution,
            'improvement_areas': improvement_areas,
            'flagged_for_review': sum(1 for analysis in recent_analyses 
                                    if analysis.review_flag != ReviewFlag.NO_REVIEW)
        }
    
    def get_confidence_distribution(self) -> Dict[str, Any]:
        """
        Get visualization helpers for confidence distribution.
        
        Returns:
            Dictionary with data suitable for visualization
        """
        if not self.confidence_history:
            return {'message': 'No confidence data available'}
        
        confidence_scores = [analysis.overall_confidence for analysis in self.confidence_history]
        
        # Create histogram data
        bins = [0.0, 0.2, 0.4, 0.6, 0.8, 0.9, 1.0]
        bin_counts = [0] * (len(bins) - 1)
        
        for score in confidence_scores:
            for i in range(len(bins) - 1):
                if bins[i] <= score < bins[i + 1] or (i == len(bins) - 2 and score == 1.0):
                    bin_counts[i] += 1
                    break
        
        return {
            'total_samples': len(confidence_scores),
            'average_confidence': round(statistics.mean(confidence_scores), 3),
            'median_confidence': round(statistics.median(confidence_scores), 3),
            'confidence_histogram': {
                'bins': [f"{bins[i]:.1f}-{bins[i+1]:.1f}" for i in range(len(bins)-1)],
                'counts': bin_counts,
                'percentages': [round((count / len(confidence_scores)) * 100, 1) for count in bin_counts]
            },
            'quality_breakdown': {
                'high_quality': sum(1 for score in confidence_scores if score >= 0.9),
                'production_ready': sum(1 for score in confidence_scores if score >= 0.8),
                'needs_review': sum(1 for score in confidence_scores if score < 0.8),
                'critical_review': sum(1 for score in confidence_scores if score < 0.4)
            }
        }
    
    def export_confidence_report(self, filename: Optional[str] = None) -> str:
        """
        Export comprehensive confidence tracking report.
        
        Args:
            filename: Optional filename to save report to
            
        Returns:
            Report content as string
        """
        pdt_time, utc_time, _ = self._get_timestamps()
        metrics = self.getPerformanceMetrics()
        trend_analysis = self.get_trend_analysis()
        distribution = self.get_confidence_distribution()
        
        report = f"""Confidence Tracking System Report
{'='*60}
Analysis Date (PDT): {pdt_time}
Analysis Date (UTC): {utc_time}
{'='*60}

SYSTEM PERFORMANCE SUMMARY:
  Total Titles Processed: {metrics.total_processed:,}
  Average Confidence:     {metrics.average_confidence:.1%}
  Processing Speed:       {metrics.processing_speed_ms:.1f} ms/title
  Trend Direction:        {metrics.trend_direction.title()}

CONFIDENCE LEVEL DISTRIBUTION:
  High Confidence (≥90%):     {metrics.high_confidence_count:6,} ({(metrics.high_confidence_count/max(metrics.total_processed,1))*100:5.1f}%)
  Good Confidence (≥80%):     {metrics.good_confidence_count:6,} ({(metrics.good_confidence_count/max(metrics.total_processed,1))*100:5.1f}%)
  Medium Confidence (≥60%):   {metrics.medium_confidence_count:6,} ({(metrics.medium_confidence_count/max(metrics.total_processed,1))*100:5.1f}%)
  Low Confidence (≥40%):      {metrics.low_confidence_count:6,} ({(metrics.low_confidence_count/max(metrics.total_processed,1))*100:5.1f}%)
  Very Low Confidence (<40%): {metrics.very_low_confidence_count:6,} ({(metrics.very_low_confidence_count/max(metrics.total_processed,1))*100:5.1f}%)

QUALITY ASSURANCE:
  Production Ready (≥80%):    {metrics.high_confidence_count + metrics.good_confidence_count:6,} ({((metrics.high_confidence_count + metrics.good_confidence_count)/max(metrics.total_processed,1))*100:5.1f}%)
  Flagged for Review (<80%):  {metrics.flagged_for_review:6,} ({(metrics.flagged_for_review/max(metrics.total_processed,1))*100:5.1f}%)

COMPONENT SUCCESS RATES:"""
        
        for component, success_rate in metrics.extraction_success_rates.items():
            component_name = component.replace('_', ' ').title()
            report += f"\n  {component_name:25} {success_rate:.1%}"
        
        if trend_analysis['improvement_areas']:
            report += "\n\nIMPROVEMENT OPPORTUNITIES:"
            for area in trend_analysis['improvement_areas']:
                report += f"\n  • {area['component'].replace('_', ' ').title()}: {area['average_confidence']:.1%} - {area['suggestion']}"
        
        report += f"""

PATTERN CONFUSION TRACKING:
  Confusion Patterns Detected: {len(self.confusion_patterns):,}
  Most Common Issues:"""
        
        # Analyze most common confusion patterns
        if self.confusion_patterns:
            issue_counts = Counter([pattern.pattern_issue for pattern in self.confusion_patterns])
            for issue, count in issue_counts.most_common(5):
                report += f"\n    • {issue}: {count} occurrences"
        else:
            report += "\n    • No significant confusion patterns detected"
        
        report += f"""

CONFIDENCE TRACKING TARGETS:
  Target Success Rate:        ≥95% production ready (≥80% confidence)
  Current Success Rate:       {((metrics.high_confidence_count + metrics.good_confidence_count)/max(metrics.total_processed,1))*100:.1f}%
  Target Review Rate:         ≤5% requiring human review
  Current Review Rate:        {(metrics.flagged_for_review/max(metrics.total_processed,1))*100:.1f}%
  
  Performance Status:         {'✅ Meeting Targets' if ((metrics.high_confidence_count + metrics.good_confidence_count)/max(metrics.total_processed,1)) >= 0.95 and (metrics.flagged_for_review/max(metrics.total_processed,1)) <= 0.05 else '⚠️ Below Targets'}

SYSTEM RECOMMENDATIONS:
  • Focus improvement efforts on components with <80% success rates
  • Review confusion patterns for pattern library enhancement opportunities  
  • Monitor trend direction for early detection of quality degradation
  • Implement automated retraining for components showing declining performance
"""
        
        if filename:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(report)
            logger.info(f"Confidence tracking report exported to {filename}")
        
        return report


def demo_confidence_tracker():
    """Demonstrate ConfidenceTracker functionality."""
    
    print("Confidence Tracking System Demo")
    print("=" * 50)
    
    # Initialize tracker
    tracker = ConfidenceTracker()
    
    # Sample extraction results
    sample_extractions = [
        ExtractionResults(
            title="Global Artificial Intelligence Market Size & Share Report, 2030",
            original_title="Global Artificial Intelligence Market Size & Share Report, 2030",
            market_term_type="standard",
            market_classification_confidence=0.95,
            extracted_forecast_date_range="2030",
            date_extraction_confidence=0.98,
            extracted_report_type="Market Size & Share Report",
            report_extraction_confidence=0.92,
            extracted_regions=["Global"],
            geographic_detection_confidence=0.85,
            topic="Artificial Intelligence",
            topic_name="artificial-intelligence",
            topic_extraction_confidence=0.88,
            processing_time_ms=250.5,
            errors_encountered=[]
        ),
        ExtractionResults(
            title="APAC Personal Protective Equipment Market Analysis",
            original_title="APAC Personal Protective Equipment Market Analysis",
            market_term_type="standard",
            market_classification_confidence=0.93,
            extracted_forecast_date_range=None,
            date_extraction_confidence=0.70,  # Low confidence - no date found
            extracted_report_type="Market Analysis",
            report_extraction_confidence=0.89,
            extracted_regions=["APAC"],
            geographic_detection_confidence=0.92,
            topic="Personal Protective Equipment",
            topic_name="personal-protective-equipment",
            topic_extraction_confidence=0.85,
            processing_time_ms=180.3,
            errors_encountered=[]
        ),
        ExtractionResults(
            title="Complex Technical Title with Issues",
            original_title="Complex Technical Title with Issues",
            market_term_type="ambiguous",
            market_classification_confidence=0.45,  # Low confidence
            extracted_forecast_date_range=None,
            date_extraction_confidence=0.30,
            extracted_report_type=None,
            report_extraction_confidence=0.25,
            extracted_regions=[],
            geographic_detection_confidence=0.20,
            topic="Technical Title",
            topic_name="technical-title",
            topic_extraction_confidence=0.55,
            processing_time_ms=450.7,
            errors_encountered=["Pattern matching failed", "Ambiguous structure"]
        )
    ]
    
    try:
        print("\n1. Confidence Analysis Examples:")
        print("-" * 40)
        
        for i, extraction in enumerate(sample_extractions, 1):
            analysis = tracker.calculateOverallConfidence(extraction)
            
            print(f"\n{i}. Title: {extraction.title}")
            print(f"   Overall Confidence: {analysis.overall_confidence:.3f} ({analysis.confidence_level.value})")
            print(f"   Review Flag: {analysis.review_flag.value}")
            print(f"   Recommendation: {analysis.recommendation}")
            print(f"   Completeness: {analysis.extraction_completeness:.1%}")
            
            if analysis.confusion_patterns:
                print(f"   Confusion Patterns: {'; '.join(analysis.confusion_patterns)}")
        
        # Get performance metrics
        print("\n2. Performance Metrics:")
        print("-" * 40)
        
        metrics = tracker.getPerformanceMetrics()
        
        print(f"Total Processed: {metrics.total_processed}")
        print(f"Average Confidence: {metrics.average_confidence:.3f}")
        print(f"High Confidence: {metrics.high_confidence_count}")
        print(f"Good Confidence: {metrics.good_confidence_count}")
        print(f"Flagged for Review: {metrics.flagged_for_review}")
        print(f"Processing Speed: {metrics.processing_speed_ms:.1f} ms/title")
        print(f"Trend Direction: {metrics.trend_direction}")
        
        # Show component success rates
        print("\nComponent Success Rates:")
        for component, rate in metrics.extraction_success_rates.items():
            print(f"  {component}: {rate:.1%}")
        
        # Get trend analysis
        print("\n3. Trend Analysis:")
        print("-" * 40)
        
        trend_analysis = tracker.get_trend_analysis(days=30)
        print(f"Period: {trend_analysis['period_days']} days")
        print(f"Total Processed: {trend_analysis['total_processed']}")
        print(f"Average Confidence: {trend_analysis['average_confidence']:.3f}")
        print(f"Trend: {trend_analysis['trend']}")
        print(f"Flagged for Review: {trend_analysis['flagged_for_review']}")
        
        if trend_analysis['improvement_areas']:
            print("\nImprovement Areas:")
            for area in trend_analysis['improvement_areas']:
                print(f"  • {area['component']}: {area['average_confidence']:.3f}")
        
        # Get confidence distribution
        print("\n4. Confidence Distribution:")
        print("-" * 40)
        
        distribution = tracker.get_confidence_distribution()
        if 'confidence_histogram' in distribution:
            print(f"Total Samples: {distribution['total_samples']}")
            print(f"Average: {distribution['average_confidence']:.3f}")
            print(f"Median: {distribution['median_confidence']:.3f}")
            
            print("\nHistogram:")
            for i, bin_range in enumerate(distribution['confidence_histogram']['bins']):
                count = distribution['confidence_histogram']['counts'][i]
                percentage = distribution['confidence_histogram']['percentages'][i]
                print(f"  {bin_range}: {count:3d} ({percentage:4.1f}%)")
        
        # Export comprehensive report
        print("\n5. Comprehensive Report:")
        print("-" * 40)
        
        report = tracker.export_confidence_report()
        print(report[:500] + "..." if len(report) > 500 else report)
        
        print("\n✅ Confidence Tracking System demo completed successfully!")
        
    except Exception as e:
        print(f"❌ Demo failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    demo_confidence_tracker()