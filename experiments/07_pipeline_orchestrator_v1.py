#!/usr/bin/env python3

"""
Processing Pipeline Orchestrator v1.0
Central orchestrator for the complete market research title processing pipeline.
Manages systematic processing through all extraction components with progress tracking.
Created for Market Research Title Parser project.
"""

import os
import sys
import logging
import importlib.util
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
import pytz
import json
import time
import traceback
from enum import Enum

# MongoDB imports
from pymongo import MongoClient
from pymongo.errors import PyMongoError

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ProcessingStatus(Enum):
    """Enumeration of processing status values."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    REQUIRES_REVIEW = "requires_review"

@dataclass
class ExtractedElements:
    """Container for all extracted elements from pipeline components."""
    market_term_type: Optional[str] = None
    extracted_forecast_date_range: Optional[str] = None
    extracted_report_type: Optional[str] = None
    extracted_regions: Optional[List[str]] = None
    topic: Optional[str] = None
    topicName: Optional[str] = None

@dataclass
class ProcessingResult:
    """Result of complete pipeline processing for a single title."""
    title: str
    original_title: str
    batch_id: str
    processing_id: str
    status: ProcessingStatus
    extracted_elements: ExtractedElements
    confidence_analysis: Optional[Dict[str, Any]] = None
    processing_time_seconds: float = 0.0
    error_message: Optional[str] = None
    component_results: Optional[Dict[str, Any]] = None
    created_timestamp: Optional[str] = None
    flags: Optional[List[str]] = None

@dataclass
class BatchProcessingStats:
    """Statistics for batch processing operations."""
    batch_id: str
    total_titles: int
    completed: int
    failed: int
    requires_review: int
    processing_time_seconds: float
    success_rate: float
    titles_per_second: float
    start_timestamp: str
    end_timestamp: str

class PipelineOrchestrator:
    """
    Central orchestrator for the market research title processing pipeline.
    
    Coordinates processing through all components:
    01: Market Term Classification
    02: Date Extraction  
    03: Report Type Extraction
    04: Geographic Entity Detection
    05: Topic Extraction
    06: Confidence Tracking
    """
    
    def __init__(self, mongodb_uri: str = None, batch_size: int = 100, 
                 retry_attempts: int = 3, timeout_seconds: int = 30):
        """
        Initialize the Pipeline Orchestrator.
        
        Args:
            mongodb_uri: MongoDB connection string
            batch_size: Number of titles to process in each batch
            retry_attempts: Number of retry attempts for failed processing
            timeout_seconds: Timeout for individual title processing
        """
        self.batch_size = batch_size
        self.retry_attempts = retry_attempts
        self.timeout_seconds = timeout_seconds
        
        # Initialize MongoDB connection
        self.mongodb_uri = mongodb_uri or os.getenv('MONGODB_URI')
        self.client = None
        self.db = None
        self._connect_to_mongodb()
        
        # Pipeline components
        self.components = {}
        self._initialize_components()
        
        # Processing statistics
        self.processing_stats = {
            'batches_processed': 0,
            'total_titles_processed': 0,
            'successful_extractions': 0,
            'failed_extractions': 0,
            'requires_review_count': 0,
            'total_processing_time': 0.0
        }
        
        logger.info("Pipeline Orchestrator initialized successfully")
    
    def _connect_to_mongodb(self) -> None:
        """Establish MongoDB connection."""
        if not self.mongodb_uri:
            raise ValueError("MongoDB URI not provided and MONGODB_URI not set in environment")
        
        try:
            self.client = MongoClient(self.mongodb_uri)
            self.db = self.client['deathstar']
            
            # Test connection
            self.db.admin.command('ping')
            logger.info("Connected to MongoDB successfully")
            
        except Exception as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            raise
    
    def _initialize_components(self) -> None:
        """Initialize all pipeline processing components."""
        try:
            # Import and initialize Market Term Classifier (01)
            spec = importlib.util.spec_from_file_location(
                "market_classifier", 
                "01_market_term_classifier_v1.py"
            )
            market_classifier_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(market_classifier_module)
            self.components['market_classifier'] = market_classifier_module.MarketTermClassifier()
            
            # Import and initialize Date Extractor (02)
            spec = importlib.util.spec_from_file_location(
                "date_extractor", 
                "02_date_extractor_v1.py"
            )
            date_extractor_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(date_extractor_module)
            self.components['date_extractor'] = date_extractor_module.DateExtractor()
            
            # Import and initialize Report Type Extractor (03)
            spec = importlib.util.spec_from_file_location(
                "report_extractor", 
                "03_report_type_extractor_v1.py"
            )
            report_extractor_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(report_extractor_module)
            self.components['report_extractor'] = report_extractor_module.ReportTypeExtractor()
            
            # Import Geographic Entity Detection functions (04)
            spec = importlib.util.spec_from_file_location(
                "geographic_detector", 
                "04_geographic_entity_detector_v1.py"
            )
            geographic_detector_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(geographic_detector_module)
            self.components['geographic_detector'] = geographic_detector_module
            
            # Import and initialize Topic Extractor (05)
            spec = importlib.util.spec_from_file_location(
                "topic_extractor", 
                "05_topic_extractor_v1.py"
            )
            topic_extractor_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(topic_extractor_module)
            self.components['topic_extractor'] = topic_extractor_module.TopicExtractor()
            
            # Import and initialize Confidence Tracker (06)
            spec = importlib.util.spec_from_file_location(
                "confidence_tracker", 
                "06_confidence_tracker_v1.py"
            )
            confidence_tracker_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(confidence_tracker_module)
            self.components['confidence_tracker'] = confidence_tracker_module.ConfidenceTracker()
            
            logger.info("All pipeline components initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize pipeline components: {e}")
            raise
    
    def _get_timestamps(self) -> Tuple[str, str, datetime]:
        """Generate PDT and UTC timestamps."""
        utc_now = datetime.now(timezone.utc)
        pdt_tz = pytz.timezone('America/Los_Angeles')
        pdt_now = utc_now.astimezone(pdt_tz)
        
        pdt_str = pdt_now.strftime('%Y-%m-%d %H:%M:%S %Z')
        utc_str = utc_now.strftime('%Y-%m-%d %H:%M:%S UTC')
        
        return pdt_str, utc_str, utc_now
    
    def _generate_batch_id(self) -> str:
        """Generate unique batch ID with timestamp and microseconds."""
        pdt_str, _, utc_now = self._get_timestamps()
        return f"batch_{utc_now.strftime('%Y%m%d_%H%M%S_%f')}"
    
    def _generate_processing_id(self, batch_id: str, index: int) -> str:
        """Generate unique processing ID for individual titles."""
        return f"{batch_id}_title_{index:04d}"
    
    def processTitle(self, title: str, batch_id: str, processing_id: str) -> ProcessingResult:
        """
        Process individual title through all pipeline extractors.
        
        Args:
            title: Title to process
            batch_id: Batch identifier
            processing_id: Unique processing identifier
            
        Returns:
            ProcessingResult with complete extraction results
        """
        start_time = time.time()
        pdt_str, utc_str, _ = self._get_timestamps()
        
        result = ProcessingResult(
            title=title,
            original_title=title,
            batch_id=batch_id,
            processing_id=processing_id,
            status=ProcessingStatus.PROCESSING,
            extracted_elements=ExtractedElements(),
            created_timestamp=pdt_str,
            flags=[]
        )
        
        component_results = {}
        
        try:
            logger.debug(f"Processing title: {title[:60]}...")
            
            # Step 1: Market Term Classification
            logger.debug("Step 1: Market term classification")
            market_result = self.components['market_classifier'].classify(title)
            component_results['market_classification'] = asdict(market_result)
            result.extracted_elements.market_term_type = market_result.market_type.value
            
            # Step 2: Date Extraction
            logger.debug("Step 2: Date extraction")
            date_result = self.components['date_extractor'].extract(title)
            component_results['date_extraction'] = asdict(date_result)
            result.extracted_elements.extracted_forecast_date_range = date_result.extracted_date
            
            # Step 3: Report Type Extraction
            logger.debug("Step 3: Report type extraction")
            report_result = self.components['report_extractor'].extract(
                title, 
                original_title=title,
                date_extractor=self.components['date_extractor']
            )
            component_results['report_extraction'] = asdict(report_result)
            result.extracted_elements.extracted_report_type = report_result.extracted_report_type
            
            # Step 4: Geographic Entity Detection
            logger.debug("Step 4: Geographic entity detection")
            # Note: Geographic detector uses functional approach, need to adapt
            geographic_result = self._process_geographic_entities(title)
            component_results['geographic_detection'] = geographic_result
            result.extracted_elements.extracted_regions = geographic_result.get('extracted_regions', [])
            
            # Step 5: Topic Extraction
            logger.debug("Step 5: Topic extraction")
            extracted_elements_dict = {
                'market_term_type': result.extracted_elements.market_term_type,
                'extracted_forecast_date_range': result.extracted_elements.extracted_forecast_date_range,
                'extracted_report_type': result.extracted_elements.extracted_report_type,
                'extracted_regions': result.extracted_elements.extracted_regions or []
            }
            
            topic_result = self.components['topic_extractor'].extract(title, extracted_elements_dict)
            component_results['topic_extraction'] = asdict(topic_result)
            result.extracted_elements.topic = topic_result.extracted_topic
            result.extracted_elements.topicName = topic_result.normalized_topic_name
            
            # Step 6: Confidence Analysis
            logger.debug("Step 6: Confidence analysis")
            # Create ExtractionResults object for confidence tracker
            extraction_results = self._create_extraction_results(component_results, result.extracted_elements)
            confidence_analysis = self.components['confidence_tracker'].calculateOverallConfidence(extraction_results)
            result.confidence_analysis = asdict(confidence_analysis)
            component_results['confidence_analysis'] = asdict(confidence_analysis)
            
            # Determine final status and flags
            if confidence_analysis.overall_confidence < 0.8:
                result.status = ProcessingStatus.REQUIRES_REVIEW
                result.flags.append("low_confidence")
            else:
                result.status = ProcessingStatus.COMPLETED
            
            # Check for specific issues
            if not result.extracted_elements.topic:
                result.flags.append("no_topic_extracted")
            
            if confidence_analysis.overall_confidence < 0.5:
                result.flags.append("very_low_confidence")
            
            result.component_results = component_results
            result.processing_time_seconds = time.time() - start_time
            
            logger.debug(f"Successfully processed title: {result.extracted_elements.topic or 'N/A'} "
                        f"(confidence: {confidence_analysis.overall_confidence:.3f})")
            
            return result
            
        except Exception as e:
            error_msg = f"Error processing title '{title}': {str(e)}"
            logger.error(error_msg)
            logger.debug(traceback.format_exc())
            
            result.status = ProcessingStatus.FAILED
            result.error_message = error_msg
            result.processing_time_seconds = time.time() - start_time
            result.component_results = component_results  # Partial results
            result.flags.append("processing_error")
            
            return result
    
    def _process_geographic_entities(self, title: str) -> Dict[str, Any]:
        """
        Process geographic entities using the functional geographic detector.
        
        Args:
            title: Title to process
            
        Returns:
            Dictionary with geographic detection results
        """
        try:
            # The geographic detector uses functional approach
            # We need to adapt it for single title processing
            
            # For now, return a simple structure
            # In production, this would integrate with the geographic detection functions
            return {
                'extracted_regions': [],
                'confidence': 0.0,
                'processing_method': 'placeholder',
                'notes': 'Geographic detection needs integration with functional approach'
            }
            
        except Exception as e:
            logger.warning(f"Geographic entity detection failed: {e}")
            return {
                'extracted_regions': [],
                'confidence': 0.0,
                'error': str(e)
            }
    
    def _create_extraction_results(self, component_results: Dict, extracted_elements: ExtractedElements):
        """
        Create ExtractionResults object for confidence tracker.
        
        Args:
            component_results: Raw component results
            extracted_elements: Extracted elements container
            
        Returns:
            ExtractionResults object compatible with confidence tracker
        """
        # Import the ExtractionResults class from confidence tracker
        ExtractionResults = self.components['confidence_tracker'].__class__.__module__
        
        # Create a simple dictionary structure that matches expected format
        extraction_results = type('ExtractionResults', (), {
            'market_classification': component_results.get('market_classification', {}),
            'date_extraction': component_results.get('date_extraction', {}),
            'report_type_extraction': component_results.get('report_extraction', {}),
            'geographic_detection': component_results.get('geographic_detection', {}),
            'topic_extraction': component_results.get('topic_extraction', {}),
            'extracted_elements': {
                'market_term_type': extracted_elements.market_term_type,
                'extracted_forecast_date_range': extracted_elements.extracted_forecast_date_range,
                'extracted_report_type': extracted_elements.extracted_report_type,
                'extracted_regions': extracted_elements.extracted_regions,
                'topic': extracted_elements.topic,
                'topicName': extracted_elements.topicName
            }
        })()
        
        return extraction_results
    
    def processBatch(self, titles: List[str], batch_id: str = None) -> List[ProcessingResult]:
        """
        Process a batch of titles through the complete pipeline.
        
        Args:
            titles: List of titles to process
            batch_id: Optional batch identifier (auto-generated if not provided)
            
        Returns:
            List of ProcessingResult objects
        """
        if not batch_id:
            batch_id = self._generate_batch_id()
        
        start_time = time.time()
        pdt_start, utc_start, _ = self._get_timestamps()
        
        logger.info(f"Starting batch processing: {batch_id} ({len(titles)} titles)")
        
        results = []
        for i, title in enumerate(titles):
            processing_id = self._generate_processing_id(batch_id, i)
            
            # Progress tracking
            if i % 10 == 0 and i > 0:
                self.trackProgress(i, len(titles), batch_id)
            
            # Process individual title
            result = self.processTitle(title, batch_id, processing_id)
            results.append(result)
            
            # Update statistics
            if result.status == ProcessingStatus.COMPLETED:
                self.processing_stats['successful_extractions'] += 1
            elif result.status == ProcessingStatus.FAILED:
                self.processing_stats['failed_extractions'] += 1
            elif result.status == ProcessingStatus.REQUIRES_REVIEW:
                self.processing_stats['requires_review_count'] += 1
        
        # Final progress update
        self.trackProgress(len(titles), len(titles), batch_id)
        
        end_time = time.time()
        processing_time = end_time - start_time
        pdt_end, utc_end, _ = self._get_timestamps()
        
        # Update overall statistics
        self.processing_stats['batches_processed'] += 1
        self.processing_stats['total_titles_processed'] += len(titles)
        self.processing_stats['total_processing_time'] += processing_time
        
        # Create batch statistics
        batch_stats = BatchProcessingStats(
            batch_id=batch_id,
            total_titles=len(titles),
            completed=sum(1 for r in results if r.status == ProcessingStatus.COMPLETED),
            failed=sum(1 for r in results if r.status == ProcessingStatus.FAILED),
            requires_review=sum(1 for r in results if r.status == ProcessingStatus.REQUIRES_REVIEW),
            processing_time_seconds=processing_time,
            success_rate=(sum(1 for r in results if r.status == ProcessingStatus.COMPLETED) / len(titles)) if titles else 0,
            titles_per_second=len(titles) / processing_time if processing_time > 0 else 0,
            start_timestamp=pdt_start,
            end_timestamp=pdt_end
        )
        
        logger.info(f"Batch processing complete: {batch_id}")
        logger.info(f"  Completed: {batch_stats.completed}")
        logger.info(f"  Failed: {batch_stats.failed}")
        logger.info(f"  Requires Review: {batch_stats.requires_review}")
        logger.info(f"  Success Rate: {batch_stats.success_rate:.1%}")
        logger.info(f"  Processing Speed: {batch_stats.titles_per_second:.2f} titles/second")
        
        return results
    
    def trackProgress(self, current: int, total: int, batch_id: str) -> None:
        """
        Update processing progress.
        
        Args:
            current: Current number of processed items
            total: Total number of items to process
            batch_id: Batch identifier
        """
        percentage = (current / total * 100) if total > 0 else 0
        logger.info(f"Progress [{batch_id}]: {current}/{total} ({percentage:.1f}%)")
    
    def handleErrors(self, title: str, error: Exception, attempt: int) -> bool:
        """
        Manage processing errors with retry logic.
        
        Args:
            title: Title that failed processing
            error: Exception that occurred
            attempt: Current attempt number (1-based)
            
        Returns:
            True if should retry, False otherwise
        """
        logger.warning(f"Processing error (attempt {attempt}/{self.retry_attempts}): {title[:50]}... - {str(error)}")
        
        if attempt < self.retry_attempts:
            # Exponential backoff for retries
            wait_time = 2 ** (attempt - 1)  # 1, 2, 4 seconds
            time.sleep(wait_time)
            return True
        else:
            logger.error(f"Max retries exceeded for title: {title[:50]}...")
            return False
    
    def saveResults(self, results: List[ProcessingResult], collection_name: str = "markets_processed") -> bool:
        """
        Store processed results in MongoDB.
        
        Args:
            results: List of processing results to save
            collection_name: MongoDB collection name
            
        Returns:
            True if successful, False otherwise
        """
        if not results:
            logger.warning("No results to save")
            return True
        
        try:
            collection = self.db[collection_name]
            
            # Convert results to dictionaries
            documents = []
            for result in results:
                doc = asdict(result)
                doc['_id'] = result.processing_id  # Use processing_id as MongoDB _id
                documents.append(doc)
            
            # Insert documents
            collection.insert_many(documents, ordered=False)
            
            logger.info(f"Saved {len(documents)} processing results to {collection_name}")
            return True
            
        except PyMongoError as e:
            logger.error(f"Failed to save results to MongoDB: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error saving results: {e}")
            return False
    
    def generateReport(self, batch_id: str, results: List[ProcessingResult] = None) -> str:
        """
        Generate processing summary report.
        
        Args:
            batch_id: Batch identifier
            results: Optional list of results (fetched from DB if not provided)
            
        Returns:
            Report filename
        """
        pdt_str, utc_str, utc_now = self._get_timestamps()
        timestamp_str = utc_now.strftime('%Y%m%d_%H%M%S')
        filename = f"../outputs/{timestamp_str}_processing_report_{batch_id}.json"
        
        try:
            # Create outputs directory if it doesn't exist
            os.makedirs("../outputs", exist_ok=True)
            
            # Generate report data
            report_data = {
                'batch_id': batch_id,
                'generated_timestamp_pdt': pdt_str,
                'generated_timestamp_utc': utc_str,
                'overall_statistics': self.processing_stats.copy(),
                'batch_summary': {},
                'sample_results': []
            }
            
            if results:
                # Batch-specific statistics
                total = len(results)
                completed = sum(1 for r in results if r.status == ProcessingStatus.COMPLETED)
                failed = sum(1 for r in results if r.status == ProcessingStatus.FAILED)
                requires_review = sum(1 for r in results if r.status == ProcessingStatus.REQUIRES_REVIEW)
                
                report_data['batch_summary'] = {
                    'total_titles': total,
                    'completed': completed,
                    'failed': failed,
                    'requires_review': requires_review,
                    'success_rate': (completed / total) if total > 0 else 0,
                    'average_processing_time': sum(r.processing_time_seconds for r in results) / total if total > 0 else 0,
                    'confidence_distribution': self._analyze_confidence_distribution(results)
                }
                
                # Sample results (first 10 successful, first 5 failed, first 5 requiring review)
                successful_samples = [asdict(r) for r in results if r.status == ProcessingStatus.COMPLETED][:10]
                failed_samples = [asdict(r) for r in results if r.status == ProcessingStatus.FAILED][:5]
                review_samples = [asdict(r) for r in results if r.status == ProcessingStatus.REQUIRES_REVIEW][:5]
                
                report_data['sample_results'] = {
                    'successful': successful_samples,
                    'failed': failed_samples,
                    'requires_review': review_samples
                }
            
            # Write report file
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(report_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Generated processing report: {filename}")
            return filename
            
        except Exception as e:
            logger.error(f"Failed to generate report: {e}")
            return ""
    
    def _analyze_confidence_distribution(self, results: List[ProcessingResult]) -> Dict[str, Any]:
        """
        Analyze confidence score distribution across results.
        
        Args:
            results: List of processing results
            
        Returns:
            Dictionary with confidence distribution analysis
        """
        confidences = []
        for result in results:
            if result.confidence_analysis and 'overall_confidence' in result.confidence_analysis:
                confidences.append(result.confidence_analysis['overall_confidence'])
        
        if not confidences:
            return {'error': 'No confidence scores available'}
        
        return {
            'count': len(confidences),
            'min': min(confidences),
            'max': max(confidences),
            'average': sum(confidences) / len(confidences),
            'high_confidence': sum(1 for c in confidences if c >= 0.8),
            'medium_confidence': sum(1 for c in confidences if 0.5 <= c < 0.8),
            'low_confidence': sum(1 for c in confidences if c < 0.5),
            'distribution': {
                'high_percentage': (sum(1 for c in confidences if c >= 0.8) / len(confidences)) * 100,
                'medium_percentage': (sum(1 for c in confidences if 0.5 <= c < 0.8) / len(confidences)) * 100,
                'low_percentage': (sum(1 for c in confidences if c < 0.5) / len(confidences)) * 100
            }
        }
    
    def get_processing_statistics(self) -> Dict[str, Any]:
        """Get overall processing statistics."""
        stats = self.processing_stats.copy()
        
        if stats['total_titles_processed'] > 0:
            stats['overall_success_rate'] = (stats['successful_extractions'] / stats['total_titles_processed'])
            stats['overall_review_rate'] = (stats['requires_review_count'] / stats['total_titles_processed'])
            stats['overall_failure_rate'] = (stats['failed_extractions'] / stats['total_titles_processed'])
        
        if stats['total_processing_time'] > 0:
            stats['overall_titles_per_second'] = (stats['total_titles_processed'] / stats['total_processing_time'])
        
        return stats

def demo_pipeline_orchestrator():
    """Demonstration of the Pipeline Orchestrator functionality."""
    print("Pipeline Orchestrator Demo")
    print("=" * 50)
    
    try:
        # Initialize orchestrator
        orchestrator = PipelineOrchestrator(batch_size=5)
        
        # Sample titles for testing
        sample_titles = [
            "Global Artificial Intelligence Market Size & Share Report, 2030",
            "North America Personal Protective Equipment Market Analysis",
            "Market for 5G Technology Solutions in Europe, 2025-2028",
            "Pharmaceutical Market in Asia Pacific Analysis",
            "IoT Device Management Market Report, 2024-2030"
        ]
        
        print(f"Processing {len(sample_titles)} sample titles...")
        
        # Process batch
        results = orchestrator.processBatch(sample_titles)
        
        # Display results
        print(f"\nProcessing Results:")
        print("-" * 30)
        
        for result in results:
            print(f"\nTitle: {result.title}")
            print(f"Status: {result.status.value}")
            print(f"Topic: {result.extracted_elements.topic or 'N/A'}")
            print(f"Market Type: {result.extracted_elements.market_term_type or 'N/A'}")
            print(f"Date Range: {result.extracted_elements.extracted_forecast_date_range or 'N/A'}")
            print(f"Report Type: {result.extracted_elements.extracted_report_type or 'N/A'}")
            
            if result.confidence_analysis:
                confidence = result.confidence_analysis.get('overall_confidence', 0)
                print(f"Confidence: {confidence:.3f}")
            
            if result.flags:
                print(f"Flags: {', '.join(result.flags)}")
            
            print(f"Processing Time: {result.processing_time_seconds:.3f}s")
        
        # Generate report
        report_file = orchestrator.generateReport("demo", results)
        if report_file:
            print(f"\nGenerated report: {report_file}")
        
        # Display statistics
        stats = orchestrator.get_processing_statistics()
        print(f"\nOverall Statistics:")
        print(f"  Total Processed: {stats['total_titles_processed']}")
        print(f"  Success Rate: {stats.get('overall_success_rate', 0):.1%}")
        print(f"  Review Rate: {stats.get('overall_review_rate', 0):.1%}")
        
        return True
        
    except Exception as e:
        print(f"Demo failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("Starting Pipeline Orchestrator Demo...")
    success = demo_pipeline_orchestrator()
    
    if success:
        print("\n✅ Pipeline Orchestrator demo completed successfully!")
    else:
        print("\n❌ Pipeline Orchestrator demo failed!")
        sys.exit(1)