#!/usr/bin/env python3

"""
Comprehensive Geographic Parsing Experiments v1.0
Tests 6 different title parsing scenarios with MongoDB patterns and spaCy NER models.
Created for Market Research Title Parser project.

Experiment Scenarios:
1. report_title_short as-is from database
2. report_title_short with dates/report types removed  
3. report_title_short normalized to lowercase
4. report_title_full as-is from database
5. report_title_full normalized to lowercase
6. All scenarios tested with MongoDB patterns + spaCy (GPE/LOC only)

Evaluation metrics:
- Detection accuracy
- Entity type precision
- Geographic coverage
- Model performance comparison
"""

import os
import re
import json
import logging
import time
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple, Any, Union
from dataclasses import dataclass, asdict
from enum import Enum
from collections import Counter, defaultdict
import pytz
from dotenv import load_dotenv
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError

# Import the enhanced geographic entity detector
try:
    from geographic_entity_detector_v1 import (
        GeographicEntityDetector, DetectionResult, DetectedEntity, 
        EntityType, DetectionStats
    )
except ImportError as e:
    print(f"Error importing GeographicEntityDetector: {e}")
    exit(1)

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ExperimentScenario(Enum):
    """Experiment scenario types."""
    TITLE_SHORT_ORIGINAL = "title_short_original"
    TITLE_SHORT_CLEANED = "title_short_cleaned"
    TITLE_SHORT_LOWERCASE = "title_short_lowercase"
    TITLE_FULL_ORIGINAL = "title_full_original"
    TITLE_FULL_LOWERCASE = "title_full_lowercase"

@dataclass
class ExperimentResult:
    """Results for a single experiment scenario."""
    scenario: ExperimentScenario
    model_config: str  # "patterns_only" or "patterns_spacy"
    total_processed: int
    titles_with_entities: int
    total_entities_detected: int
    unique_entities: List[str]
    entity_type_distribution: Dict[str, int]
    confidence_distribution: Dict[str, int]  # Low/Medium/High confidence counts
    detection_rate: float
    avg_entities_per_title: float
    processing_time_seconds: float
    sample_results: List[Dict[str, Any]]  # First 10 results for manual review

@dataclass
class ComprehensiveExperimentReport:
    """Complete experiment report with all scenarios."""
    experiment_timestamp_pdt: str
    experiment_timestamp_utc: str
    mongodb_connection_status: str
    spacy_model_status: str
    dataset_info: Dict[str, Any]
    scenario_results: List[ExperimentResult]
    comparative_analysis: Dict[str, Any]
    recommendations: List[str]

class GeographicParsingExperimentSuite:
    """
    Comprehensive experiment suite for testing geographic entity detection
    across multiple title parsing scenarios and model configurations.
    """
    
    def __init__(self, max_titles_per_scenario: int = 1000):
        """
        Initialize the experiment suite.
        
        Args:
            max_titles_per_scenario: Maximum titles to test per scenario (for performance)
        """
        self.max_titles_per_scenario = max_titles_per_scenario
        
        # Initialize MongoDB connection
        self.mongo_client = None
        self.db = None
        self._connect_to_mongodb()
        
        # Initialize geographic detectors
        self.pattern_detector = GeographicEntityDetector(use_models=False)
        self.pattern_spacy_detector = GeographicEntityDetector(use_models=True)
        
        # Experiment tracking
        self.experiment_results = []
        self.dataset_cache = {}
        
        logger.info(f"Initialized experiment suite with max {max_titles_per_scenario} titles per scenario")
    
    def _connect_to_mongodb(self) -> bool:
        """Connect to MongoDB database."""
        try:
            mongodb_uri = os.getenv('MONGODB_URI')
            if not mongodb_uri:
                raise ValueError("MONGODB_URI environment variable not set")
            
            self.mongo_client = MongoClient(mongodb_uri, serverSelectionTimeoutMS=5000)
            self.db = self.mongo_client['deathstar']
            
            # Test connection
            self.db.command('ping')
            logger.info("Successfully connected to MongoDB database: deathstar")
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            return False
    
    def _get_timestamps(self) -> tuple:
        """Generate PDT and UTC timestamps."""
        utc_now = datetime.now(timezone.utc)
        pdt_tz = pytz.timezone('America/Los_Angeles')
        pdt_now = utc_now.astimezone(pdt_tz)
        
        pdt_str = pdt_now.strftime('%Y-%m-%d %H:%M:%S %Z')
        utc_str = utc_now.strftime('%Y-%m-%d %H:%M:%S UTC')
        
        return pdt_str, utc_str, utc_now
    
    def _load_dataset_sample(self) -> List[Dict[str, Any]]:
        """Load a sample of market research titles from MongoDB."""
        if 'titles' in self.dataset_cache:
            return self.dataset_cache['titles']
        
        try:
            # Query the markets_raw collection
            pipeline = [
                {"$match": {
                    "report_title_short": {"$exists": True, "$ne": None, "$ne": ""},
                    "report_title_full": {"$exists": True, "$ne": None, "$ne": ""}
                }},
                {"$sample": {"size": self.max_titles_per_scenario}},
                {"$project": {
                    "_id": 1,
                    "report_title_short": 1,
                    "report_title_full": 1,
                    "extracted_forecast_date_range": 1,
                    "extracted_report_type": 1
                }}
            ]
            
            titles = list(self.db.markets_raw.aggregate(pipeline))
            self.dataset_cache['titles'] = titles
            
            logger.info(f"Loaded {len(titles)} title samples from MongoDB")
            return titles
            
        except Exception as e:
            logger.error(f"Failed to load dataset: {e}")
            return []
    
    def _prepare_title_variants(self, title_data: Dict[str, Any]) -> Dict[ExperimentScenario, str]:
        """
        Prepare all title variants for a single title record.
        
        Args:
            title_data: MongoDB record with title fields
            
        Returns:
            Dictionary mapping scenarios to prepared title strings
        """
        variants = {}
        
        # Scenario 1: report_title_short as-is
        variants[ExperimentScenario.TITLE_SHORT_ORIGINAL] = title_data.get('report_title_short', '').strip()
        
        # Scenario 2: report_title_short with dates/report types removed
        short_cleaned = title_data.get('report_title_short', '').strip()
        
        # Remove extracted date range if available
        if title_data.get('extracted_forecast_date_range'):
            date_range = title_data['extracted_forecast_date_range']
            short_cleaned = short_cleaned.replace(date_range, '').strip()
        
        # Remove extracted report type if available
        if title_data.get('extracted_report_type'):
            report_type = title_data['extracted_report_type']
            short_cleaned = short_cleaned.replace(report_type, '').strip()
        
        # Additional cleaning - remove common date patterns
        date_patterns = [
            r'\b(2019|2020|2021|2022|2023|2024|2025|2026|2027|2028|2029|2030)\b',
            r'\b(20\d{2}[-–]\d{2})\b',
            r'\b(20\d{2}[-–]20\d{2})\b',
        ]
        for pattern in date_patterns:
            short_cleaned = re.sub(pattern, '', short_cleaned, flags=re.IGNORECASE)
        
        # Clean up extra whitespace and punctuation
        short_cleaned = re.sub(r'\s+', ' ', short_cleaned).strip()
        short_cleaned = re.sub(r'[,;]\s*$', '', short_cleaned)  # Remove trailing punctuation
        
        variants[ExperimentScenario.TITLE_SHORT_CLEANED] = short_cleaned
        
        # Scenario 3: report_title_short normalized to lowercase
        variants[ExperimentScenario.TITLE_SHORT_LOWERCASE] = variants[ExperimentScenario.TITLE_SHORT_ORIGINAL].lower()
        
        # Scenario 4: report_title_full as-is
        variants[ExperimentScenario.TITLE_FULL_ORIGINAL] = title_data.get('report_title_full', '').strip()
        
        # Scenario 5: report_title_full normalized to lowercase
        variants[ExperimentScenario.TITLE_FULL_LOWERCASE] = variants[ExperimentScenario.TITLE_FULL_ORIGINAL].lower()
        
        return variants
    
    def _categorize_confidence(self, confidence: float) -> str:
        """Categorize confidence score into Low/Medium/High."""
        if confidence < 0.6:
            return "Low"
        elif confidence < 0.8:
            return "Medium"
        else:
            return "High"
    
    def _run_single_scenario_experiment(self, scenario: ExperimentScenario, 
                                      use_spacy: bool = False) -> ExperimentResult:
        """
        Run experiment for a single scenario with specified model configuration.
        
        Args:
            scenario: Experiment scenario to test
            use_spacy: Whether to use spaCy + patterns (True) or patterns only (False)
            
        Returns:
            ExperimentResult with detailed metrics
        """
        model_config = "patterns_spacy" if use_spacy else "patterns_only"
        detector = self.pattern_spacy_detector if use_spacy else self.pattern_detector
        
        logger.info(f"Running experiment: {scenario.value} with {model_config}")
        
        # Load dataset
        dataset = self._load_dataset_sample()
        if not dataset:
            logger.error(f"No dataset available for {scenario.value}")
            return None
        
        start_time = time.time()
        
        # Track results
        results = []
        all_entities = []
        confidence_counts = {"Low": 0, "Medium": 0, "High": 0}
        entity_types = Counter()
        
        # Process each title
        for i, title_data in enumerate(dataset):
            if i % 100 == 0 and i > 0:
                logger.info(f"Processed {i}/{len(dataset)} titles for {scenario.value}")
            
            # Get title variant for this scenario
            title_variants = self._prepare_title_variants(title_data)
            title_to_test = title_variants.get(scenario)
            
            if not title_to_test:
                continue
            
            # Run detection
            detection_result = detector.detect(title_to_test)
            
            # Track entities
            for entity in detection_result.entities:
                all_entities.append(entity.entity)
                entity_types[entity.entity_type.value] += 1
                confidence_counts[self._categorize_confidence(entity.confidence)] += 1
            
            # Store sample results (first 10)
            if len(results) < 10:
                results.append({
                    "title_id": str(title_data.get('_id', '')),
                    "original_title": title_to_test,
                    "entities_found": detection_result.extracted_regions,
                    "confidence_score": detection_result.confidence_score,
                    "detection_method": detection_result.detection_method,
                    "processing_notes": detection_result.processing_notes
                })
        
        processing_time = time.time() - start_time
        
        # Calculate metrics
        stats = detector.get_detection_statistics()
        unique_entities = list(set(all_entities))
        
        return ExperimentResult(
            scenario=scenario,
            model_config=model_config,
            total_processed=stats.total_processed,
            titles_with_entities=stats.titles_with_entities,
            total_entities_detected=stats.total_entities_detected,
            unique_entities=unique_entities,
            entity_type_distribution=dict(entity_types),
            confidence_distribution=confidence_counts,
            detection_rate=stats.detection_rate,
            avg_entities_per_title=stats.average_entities_per_title,
            processing_time_seconds=round(processing_time, 2),
            sample_results=results
        )
    
    def run_comprehensive_experiments(self) -> ComprehensiveExperimentReport:
        """
        Run all experiment scenarios with both model configurations.
        
        Returns:
            ComprehensiveExperimentReport with complete results
        """
        pdt_time, utc_time, _ = self._get_timestamps()
        
        logger.info("Starting comprehensive geographic parsing experiments")
        print("="*80)
        print("COMPREHENSIVE GEOGRAPHIC PARSING EXPERIMENTS")
        print("="*80)
        print(f"Experiment Start Time (PDT): {pdt_time}")
        print(f"Experiment Start Time (UTC): {utc_time}")
        print(f"Max titles per scenario: {self.max_titles_per_scenario}")
        print()
        
        # Check system status
        mongodb_status = "Connected" if self.db is not None else "Disconnected"
        spacy_status = "Available" if self.pattern_spacy_detector.spacy_model is not None else "Not Available"
        
        print(f"MongoDB Status: {mongodb_status}")
        print(f"spaCy Model Status: {spacy_status}")
        print()
        
        # Get dataset info
        dataset = self._load_dataset_sample()
        dataset_info = {
            "total_titles_loaded": len(dataset),
            "collection": "markets_raw",
            "sampling_method": "random"
        }
        
        all_results = []
        
        # Run experiments for each scenario
        scenarios = [
            ExperimentScenario.TITLE_SHORT_ORIGINAL,
            ExperimentScenario.TITLE_SHORT_CLEANED,
            ExperimentScenario.TITLE_SHORT_LOWERCASE,
            ExperimentScenario.TITLE_FULL_ORIGINAL,
            ExperimentScenario.TITLE_FULL_LOWERCASE
        ]
        
        for scenario in scenarios:
            # Test with patterns only
            result_patterns = self._run_single_scenario_experiment(scenario, use_spacy=False)
            if result_patterns:
                all_results.append(result_patterns)
            
            # Test with patterns + spaCy
            result_patterns_spacy = self._run_single_scenario_experiment(scenario, use_spacy=True)
            if result_patterns_spacy:
                all_results.append(result_patterns_spacy)
            
            # Reset detector statistics between scenarios
            self.pattern_detector.detection_stats = {
                'total_processed': 0, 'titles_with_entities': 0, 
                'total_entities_detected': 0, 'compound_entities_detected': 0,
                'model_entities_detected': 0
            }
            self.pattern_spacy_detector.detection_stats = {
                'total_processed': 0, 'titles_with_entities': 0,
                'total_entities_detected': 0, 'compound_entities_detected': 0,
                'model_entities_detected': 0
            }
        
        # Analyze results
        comparative_analysis = self._analyze_results(all_results)
        recommendations = self._generate_recommendations(all_results, comparative_analysis)
        
        return ComprehensiveExperimentReport(
            experiment_timestamp_pdt=pdt_time,
            experiment_timestamp_utc=utc_time,
            mongodb_connection_status=mongodb_status,
            spacy_model_status=spacy_status,
            dataset_info=dataset_info,
            scenario_results=all_results,
            comparative_analysis=comparative_analysis,
            recommendations=recommendations
        )
    
    def _analyze_results(self, results: List[ExperimentResult]) -> Dict[str, Any]:
        """Analyze and compare experiment results."""
        analysis = {
            "best_detection_rate": {"scenario": "", "model": "", "rate": 0.0},
            "most_entities_detected": {"scenario": "", "model": "", "count": 0},
            "best_confidence_distribution": {"scenario": "", "model": "", "high_confidence_pct": 0.0},
            "fastest_processing": {"scenario": "", "model": "", "time": float('inf')},
            "scenario_comparisons": {},
            "model_comparisons": {"patterns_only": {}, "patterns_spacy": {}}
        }
        
        # Track best performers
        for result in results:
            scenario_name = result.scenario.value
            model_name = result.model_config
            
            # Best detection rate
            if result.detection_rate > analysis["best_detection_rate"]["rate"]:
                analysis["best_detection_rate"] = {
                    "scenario": scenario_name,
                    "model": model_name,
                    "rate": result.detection_rate
                }
            
            # Most entities detected
            if result.total_entities_detected > analysis["most_entities_detected"]["count"]:
                analysis["most_entities_detected"] = {
                    "scenario": scenario_name,
                    "model": model_name,
                    "count": result.total_entities_detected
                }
            
            # Best confidence distribution (highest % of high confidence)
            total_confidences = sum(result.confidence_distribution.values())
            if total_confidences > 0:
                high_conf_pct = (result.confidence_distribution.get("High", 0) / total_confidences) * 100
                if high_conf_pct > analysis["best_confidence_distribution"]["high_confidence_pct"]:
                    analysis["best_confidence_distribution"] = {
                        "scenario": scenario_name,
                        "model": model_name,
                        "high_confidence_pct": round(high_conf_pct, 2)
                    }
            
            # Fastest processing
            if result.processing_time_seconds < analysis["fastest_processing"]["time"]:
                analysis["fastest_processing"] = {
                    "scenario": scenario_name,
                    "model": model_name,
                    "time": result.processing_time_seconds
                }
            
            # Model comparisons - initialize if not exists
            if model_name not in analysis["model_comparisons"]:
                analysis["model_comparisons"][model_name] = {
                    "avg_detection_rate": 0.0,
                    "avg_entities_per_title": 0.0,
                    "total_unique_entities": 0,
                    "scenario_count": 0
                }
            else:
                # Ensure all keys exist
                if "avg_detection_rate" not in analysis["model_comparisons"][model_name]:
                    analysis["model_comparisons"][model_name]["avg_detection_rate"] = 0.0
                if "avg_entities_per_title" not in analysis["model_comparisons"][model_name]:
                    analysis["model_comparisons"][model_name]["avg_entities_per_title"] = 0.0
                if "total_unique_entities" not in analysis["model_comparisons"][model_name]:
                    analysis["model_comparisons"][model_name]["total_unique_entities"] = 0
                if "scenario_count" not in analysis["model_comparisons"][model_name]:
                    analysis["model_comparisons"][model_name]["scenario_count"] = 0
            
            model_stats = analysis["model_comparisons"][model_name]
            model_stats["avg_detection_rate"] += result.detection_rate
            model_stats["avg_entities_per_title"] += result.avg_entities_per_title
            model_stats["total_unique_entities"] += len(result.unique_entities)
            model_stats["scenario_count"] += 1
        
        # Calculate averages for model comparisons
        for model_name, stats in analysis["model_comparisons"].items():
            if stats["scenario_count"] > 0:
                stats["avg_detection_rate"] = round(stats["avg_detection_rate"] / stats["scenario_count"], 2)
                stats["avg_entities_per_title"] = round(stats["avg_entities_per_title"] / stats["scenario_count"], 2)
        
        return analysis
    
    def _generate_recommendations(self, results: List[ExperimentResult], 
                                 analysis: Dict[str, Any]) -> List[str]:
        """Generate recommendations based on experiment results."""
        recommendations = []
        
        # Best overall configuration
        best_rate = analysis["best_detection_rate"]
        recommendations.append(
            f"BEST OVERALL: Use {best_rate['scenario']} with {best_rate['model']} "
            f"for highest detection rate ({best_rate['rate']:.2f}%)"
        )
        
        # Performance comparison
        patterns_stats = analysis["model_comparisons"].get("patterns_only", {})
        spacy_stats = analysis["model_comparisons"].get("patterns_spacy", {})
        
        if patterns_stats and spacy_stats:
            if spacy_stats["avg_detection_rate"] > patterns_stats["avg_detection_rate"]:
                improvement = spacy_stats["avg_detection_rate"] - patterns_stats["avg_detection_rate"]
                recommendations.append(
                    f"spaCy Integration provides {improvement:.2f}% average detection rate improvement"
                )
            else:
                recommendations.append("MongoDB patterns alone perform as well as patterns + spaCy")
        
        # Title processing recommendations
        title_short_results = [r for r in results if "title_short" in r.scenario.value]
        title_full_results = [r for r in results if "title_full" in r.scenario.value]
        
        if title_short_results and title_full_results:
            avg_short_rate = sum(r.detection_rate for r in title_short_results) / len(title_short_results)
            avg_full_rate = sum(r.detection_rate for r in title_full_results) / len(title_full_results)
            
            if avg_full_rate > avg_short_rate:
                recommendations.append(
                    f"Use report_title_full for better detection ({avg_full_rate:.2f}% vs {avg_short_rate:.2f}%)"
                )
            else:
                recommendations.append("report_title_short performs as well as report_title_full")
        
        # Confidence recommendations
        best_conf = analysis["best_confidence_distribution"]
        recommendations.append(
            f"Highest confidence results from {best_conf['scenario']} with {best_conf['model']} "
            f"({best_conf['high_confidence_pct']:.1f}% high confidence)"
        )
        
        return recommendations
    
    def export_experiment_report(self, report: ComprehensiveExperimentReport, 
                               export_json: bool = True, export_txt: bool = True) -> Dict[str, str]:
        """
        Export experiment report to JSON and/or text files.
        
        Args:
            report: ComprehensiveExperimentReport to export
            export_json: Whether to export JSON format
            export_txt: Whether to export text format
            
        Returns:
            Dictionary with exported file paths
        """
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        exported_files = {}
        
        if export_json:
            json_filename = f"../outputs/{timestamp}_comprehensive_geographic_parsing_experiment_results.json"
            
            # Convert dataclasses to dictionaries for JSON serialization
            report_dict = {
                "experiment_timestamp_pdt": report.experiment_timestamp_pdt,
                "experiment_timestamp_utc": report.experiment_timestamp_utc,
                "mongodb_connection_status": report.mongodb_connection_status,
                "spacy_model_status": report.spacy_model_status,
                "dataset_info": report.dataset_info,
                "scenario_results": [asdict(result) for result in report.scenario_results],
                "comparative_analysis": report.comparative_analysis,
                "recommendations": report.recommendations
            }
            
            with open(json_filename, 'w', encoding='utf-8') as f:
                json.dump(report_dict, f, indent=2, ensure_ascii=False, default=str)
            
            exported_files["json"] = json_filename
            logger.info(f"Exported JSON report to {json_filename}")
        
        if export_txt:
            txt_filename = f"../outputs/{timestamp}_comprehensive_geographic_parsing_experiment_results.txt"
            
            with open(txt_filename, 'w', encoding='utf-8') as f:
                f.write("COMPREHENSIVE GEOGRAPHIC PARSING EXPERIMENT RESULTS\n")
                f.write("="*80 + "\n")
                f.write(f"Analysis Date (PDT): {report.experiment_timestamp_pdt}\n")
                f.write(f"Analysis Date (UTC): {report.experiment_timestamp_utc}\n")
                f.write("="*80 + "\n\n")
                
                f.write("SYSTEM STATUS\n")
                f.write("-"*40 + "\n")
                f.write(f"MongoDB: {report.mongodb_connection_status}\n")
                f.write(f"spaCy Model: {report.spacy_model_status}\n")
                f.write(f"Dataset Size: {report.dataset_info.get('total_titles_loaded', 0)} titles\n\n")
                
                f.write("EXPERIMENT RESULTS BY SCENARIO\n")
                f.write("-"*40 + "\n")
                
                for result in report.scenario_results:
                    f.write(f"\nScenario: {result.scenario.value}\n")
                    f.write(f"Model: {result.model_config}\n")
                    f.write(f"Detection Rate: {result.detection_rate:.2f}%\n")
                    f.write(f"Total Entities: {result.total_entities_detected}\n")
                    f.write(f"Unique Entities: {len(result.unique_entities)}\n")
                    f.write(f"Avg Entities/Title: {result.avg_entities_per_title:.2f}\n")
                    f.write(f"Processing Time: {result.processing_time_seconds}s\n")
                    
                    if result.confidence_distribution:
                        f.write("Confidence Distribution:\n")
                        for conf_level, count in result.confidence_distribution.items():
                            f.write(f"  {conf_level}: {count}\n")
                    f.write("-"*30 + "\n")
                
                f.write("\nCOMPARATIVE ANALYSIS\n")
                f.write("-"*40 + "\n")
                
                analysis = report.comparative_analysis
                f.write(f"Best Detection Rate: {analysis['best_detection_rate']['scenario']} "
                       f"with {analysis['best_detection_rate']['model']} "
                       f"({analysis['best_detection_rate']['rate']:.2f}%)\n")
                
                f.write(f"Most Entities Detected: {analysis['most_entities_detected']['scenario']} "
                       f"with {analysis['most_entities_detected']['model']} "
                       f"({analysis['most_entities_detected']['count']} entities)\n")
                
                f.write(f"Best Confidence: {analysis['best_confidence_distribution']['scenario']} "
                       f"with {analysis['best_confidence_distribution']['model']} "
                       f"({analysis['best_confidence_distribution']['high_confidence_pct']:.1f}% high confidence)\n")
                
                f.write("\nRECOMMENDATIONS\n")
                f.write("-"*40 + "\n")
                for i, rec in enumerate(report.recommendations, 1):
                    f.write(f"{i}. {rec}\n")
                
                f.write("\n" + "="*80 + "\n")
                f.write("END OF REPORT\n")
            
            exported_files["txt"] = txt_filename
            logger.info(f"Exported text report to {txt_filename}")
        
        return exported_files


def main():
    """Run comprehensive geographic parsing experiments."""
    
    print("Comprehensive Geographic Parsing Experiments")
    print("=" * 60)
    print()
    
    try:
        # Initialize experiment suite
        experiment_suite = GeographicParsingExperimentSuite(max_titles_per_scenario=200)  # Smaller sample for testing
        
        # Run comprehensive experiments
        report = experiment_suite.run_comprehensive_experiments()
        
        if not report:
            print("❌ Experiment failed")
            return
        
        # Export results
        exported_files = experiment_suite.export_experiment_report(report)
        
        print("\n" + "="*80)
        print("EXPERIMENT SUMMARY")
        print("="*80)
        print(f"Total Scenarios Tested: {len(report.scenario_results)}")
        print(f"Best Detection Rate: {report.comparative_analysis['best_detection_rate']['rate']:.2f}%")
        print(f"Best Configuration: {report.comparative_analysis['best_detection_rate']['scenario']} "
              f"+ {report.comparative_analysis['best_detection_rate']['model']}")
        
        print("\nTOP RECOMMENDATIONS:")
        for i, rec in enumerate(report.recommendations[:3], 1):
            print(f"{i}. {rec}")
        
        print(f"\nResults exported to:")
        for format_type, filepath in exported_files.items():
            print(f"  {format_type.upper()}: {filepath}")
        
        print("\n✅ Comprehensive geographic parsing experiments completed successfully!")
        
    except Exception as e:
        print(f"❌ Experiment failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()