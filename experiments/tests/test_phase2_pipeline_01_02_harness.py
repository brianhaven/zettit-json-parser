#!/usr/bin/env python3

"""
Phase 2 Pipeline Testing Harness: Market Term Classifier → Date Extractor
Tests the integration of 01_market_term_classifier_v1.py and 02_date_extractor_v1.py
Generates comprehensive reports for date extraction analysis and pattern library enhancement
"""

import os
import sys
import json
import logging
from datetime import datetime, timezone
import pytz
from typing import Dict, List, Optional, Tuple, Any
from pathlib import Path
import random
from collections import Counter, defaultdict

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# MongoDB imports
from pymongo import MongoClient
from dotenv import load_dotenv

# Import the modules to test
import importlib.util

# Load the classifier module dynamically
classifier_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '01_market_term_classifier_v1.py')
spec = importlib.util.spec_from_file_location("market_term_classifier_v1", classifier_path)
classifier_module = importlib.util.module_from_spec(spec)
sys.modules["market_term_classifier_v1"] = classifier_module
spec.loader.exec_module(classifier_module)

# Load the date extractor module dynamically
date_extractor_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '02_date_extractor_v1.py')
spec2 = importlib.util.spec_from_file_location("date_extractor_v1", date_extractor_path)
date_extractor_module = importlib.util.module_from_spec(spec2)
sys.modules["date_extractor_v1"] = date_extractor_module
spec2.loader.exec_module(date_extractor_module)

# Import the classes
MarketTermClassifier = classifier_module.MarketTermClassifier
MarketTermType = classifier_module.MarketTermType
ClassificationResult = classifier_module.ClassificationResult

DateExtractor = date_extractor_module.DateExtractor
DateFormat = date_extractor_module.DateFormat
DateExtractionResult = date_extractor_module.DateExtractionResult

# Import PatternLibraryManager for DateExtractor
pattern_manager_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '00b_pattern_library_manager_v1.py')
spec3 = importlib.util.spec_from_file_location("pattern_library_manager_v1", pattern_manager_path)
pattern_manager_module = importlib.util.module_from_spec(spec3)
sys.modules["pattern_library_manager_v1"] = pattern_manager_module
spec3.loader.exec_module(pattern_manager_module)

PatternLibraryManager = pattern_manager_module.PatternLibraryManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class Phase2PipelineTestHarness:
    """Test harness for Phase 2 pipeline integration testing (01→02)."""
    
    def __init__(self, sample_size: int = 1000):
        """
        Initialize the test harness.
        
        Args:
            sample_size: Number of documents to test (default 1000)
        """
        self.sample_size = sample_size
        self.classifier = MarketTermClassifier()
        
        # Initialize PatternLibraryManager for DateExtractor
        self.pattern_library_manager = PatternLibraryManager()
        self.date_extractor = DateExtractor(self.pattern_library_manager)
        
        self.results = []
        self.classification_stats = defaultdict(int)
        self.date_extraction_stats = defaultdict(int)
        self.date_format_patterns = defaultdict(list)
        self.edge_cases = []
        
        # Load environment variables
        load_dotenv()
        
        # Initialize MongoDB connection
        self._connect_mongodb()
        
    def _connect_mongodb(self) -> None:
        """Connect to MongoDB database."""
        mongodb_uri = os.getenv('MONGODB_URI')
        if not mongodb_uri:
            raise ValueError("MONGODB_URI environment variable not set")
        
        self.client = MongoClient(mongodb_uri)
        self.db = self.client['deathstar']
        self.collection = self.db['markets_raw']
        
        # Verify connection
        doc_count = self.collection.count_documents({})
        logger.info(f"Connected to MongoDB. Found {doc_count:,} documents in markets_raw")
    
    def fetch_test_documents(self) -> List[Dict]:
        """
        Fetch random sample of documents from MongoDB.
        
        Returns:
            List of document dictionaries
        """
        logger.info(f"Fetching {self.sample_size} random documents from MongoDB...")
        
        # Use aggregation pipeline for random sampling
        pipeline = [
            {"$sample": {"size": self.sample_size}},
            {"$project": {
                "_id": 1,
                "report_title_short": 1,
                "report_title": 1,
                "description": 1
            }}
        ]
        
        documents = list(self.collection.aggregate(pipeline))
        logger.info(f"Successfully fetched {len(documents)} documents")
        
        return documents
    
    def run_pipeline_on_document(self, doc: Dict) -> Dict:
        """
        Run the complete 01→02 pipeline on a single document.
        
        Args:
            doc: MongoDB document
            
        Returns:
            Dictionary with pipeline results
        """
        # Extract title for processing
        title = doc.get('report_title_short', '') or doc.get('report_title', '')
        if not title:
            return {
                'document_id': str(doc.get('_id', '')),
                'title': '',
                'error': 'No title found',
                'classification_result': None,
                'date_extraction_result': None
            }
        
        try:
            # Step 1: Market Term Classification
            classification_result = self.classifier.classify(title)
            
            # Step 2: Date Extraction
            date_extraction_result = self.date_extractor.extract(title)
            
            # Combine results
            pipeline_result = {
                'document_id': str(doc.get('_id', '')),
                'title': title,
                'description': doc.get('description', ''),
                'classification_result': {
                    'market_term_type': classification_result.market_type.value,
                    'confidence': classification_result.confidence,
                    'matched_pattern': classification_result.matched_pattern,
                    'processing_notes': getattr(classification_result, 'notes', None)
                },
                'date_extraction_result': {
                    'extracted_date_range': date_extraction_result.extracted_date_range,
                    'start_year': date_extraction_result.start_year,
                    'end_year': date_extraction_result.end_year,
                    'format_type': date_extraction_result.format_type.value,
                    'confidence': date_extraction_result.confidence,
                    'matched_pattern': date_extraction_result.matched_pattern,
                    'raw_match': date_extraction_result.raw_match,
                    'notes': date_extraction_result.notes
                },
                'error': None
            }
            
            return pipeline_result
            
        except Exception as e:
            logger.error(f"Error processing document {doc.get('_id')}: {e}")
            return {
                'document_id': str(doc.get('_id', '')),
                'title': title,
                'error': str(e),
                'classification_result': None,
                'date_extraction_result': None
            }
    
    def run_test_suite(self) -> None:
        """Run the complete test suite."""
        logger.info("Starting Phase 2 Pipeline Test Suite (01→02)")
        
        # Fetch test documents
        documents = self.fetch_test_documents()
        
        # Process each document through the pipeline
        logger.info("Processing documents through 01→02 pipeline...")
        processed_count = 0
        
        for i, doc in enumerate(documents, 1):
            if i % 100 == 0:
                logger.info(f"Processed {i}/{len(documents)} documents...")
            
            result = self.run_pipeline_on_document(doc)
            self.results.append(result)
            
            # Update statistics
            if result['error'] is None:
                processed_count += 1
                
                # Classification stats
                if result['classification_result']:
                    market_type = result['classification_result']['market_term_type']
                    self.classification_stats[market_type] += 1
                
                # Date extraction stats
                if result['date_extraction_result']:
                    date_result = result['date_extraction_result']
                    has_date = date_result['extracted_date_range'] is not None
                    
                    if has_date:
                        self.date_extraction_stats['successful_extractions'] += 1
                        format_type = date_result['format_type']
                        self.date_extraction_stats[f'format_{format_type}'] += 1
                        
                        # Collect format patterns for analysis
                        if date_result['raw_match']:
                            self.date_format_patterns[format_type].append({
                                'title': result['title'],
                                'raw_match': date_result['raw_match'],
                                'extracted_date': date_result['extracted_date_range'],
                                'confidence': date_result['confidence']
                            })
                    else:
                        self.date_extraction_stats['failed_extractions'] += 1
                        
                        # Collect potential edge cases
                        self.edge_cases.append({
                            'title': result['title'],
                            'classification': market_type,
                            'reason': 'No date found'
                        })
        
        self.date_extraction_stats['total_processed'] = processed_count
        
        logger.info(f"Phase 2 pipeline testing complete. Processed {processed_count} documents.")
    
    def generate_reports(self) -> str:
        """
        Generate comprehensive test reports.
        
        Returns:
            Output directory path
        """
        # Create timestamp-based output directory
        pdt = pytz.timezone('America/Los_Angeles')
        utc_now = datetime.now(timezone.utc)
        pdt_now = utc_now.astimezone(pdt)
        
        timestamp = pdt_now.strftime('%Y%m%d_%H%M%S')
        
        # Use absolute path for outputs directory
        script_dir = Path(__file__).parent.parent.parent  # Go up from tests/ to project root
        output_dir = script_dir / "outputs" / f"{timestamp}_phase2_pipeline_01_02"
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Generating reports in {output_dir}")
        
        # Generate summary markdown report
        self._generate_summary_report(output_path, pdt_now, utc_now)
        
        # Generate detailed JSON report
        self._generate_detailed_json_report(output_path)
        
        # Generate date pattern analysis
        self._generate_date_pattern_analysis(output_path)
        
        # Generate edge cases report
        self._generate_edge_cases_report(output_path)
        
        # Generate sample data for manual review
        self._generate_sample_data(output_path)
        
        logger.info(f"All reports generated in {output_dir}")
        return str(output_path)
    
    def _generate_summary_report(self, output_path: Path, pdt_time: datetime, utc_time: datetime) -> None:
        """Generate summary markdown report."""
        total_processed = self.date_extraction_stats['total_processed']
        successful_dates = self.date_extraction_stats.get('successful_extractions', 0)
        failed_dates = self.date_extraction_stats.get('failed_extractions', 0)
        
        date_success_rate = (successful_dates / total_processed * 100) if total_processed > 0 else 0
        
        summary_content = f"""# Phase 2 Pipeline Test Results: Market Term Classifier → Date Extractor

**Analysis Date (PDT):** {pdt_time.strftime('%Y-%m-%d %H:%M:%S PDT')}
**Analysis Date (UTC):** {utc_time.strftime('%Y-%m-%d %H:%M:%S UTC')}
**Sample Size:** {self.sample_size:,} documents
**Successfully Processed:** {total_processed:,} documents

## Pipeline Performance Summary

### Market Term Classification Results
"""
        
        for market_type, count in self.classification_stats.items():
            percentage = (count / total_processed * 100) if total_processed > 0 else 0
            summary_content += f"- **{market_type.replace('_', ' ').title()}**: {count:,} ({percentage:.2f}%)\n"
        
        summary_content += f"""
### Date Extraction Results
- **Successful Extractions**: {successful_dates:,} ({date_success_rate:.2f}%)
- **Failed Extractions**: {failed_dates:,} ({100 - date_success_rate:.2f}%)

### Date Format Distribution
"""
        
        for format_key, count in self.date_extraction_stats.items():
            if format_key.startswith('format_'):
                format_name = format_key.replace('format_', '').replace('_', ' ').title()
                percentage = (count / successful_dates * 100) if successful_dates > 0 else 0
                summary_content += f"- **{format_name}**: {count:,} ({percentage:.2f}%)\n"
        
        summary_content += f"""
## Key Insights

### Date Pattern Discovery
"""
        
        for format_type, patterns in self.date_format_patterns.items():
            if patterns:
                avg_confidence = sum(p['confidence'] for p in patterns) / len(patterns)
                summary_content += f"- **{format_type.replace('_', ' ').title()}**: {len(patterns)} patterns found (avg confidence: {avg_confidence:.3f})\n"
        
        summary_content += f"""
### Edge Cases Identified
- **Total Edge Cases**: {len(self.edge_cases)}
- **Primary Issue**: No date patterns found in titles

## Recommendations

### Pattern Library Enhancement
1. Analyze date format variations in detailed patterns report
2. Build comprehensive date pattern library in MongoDB
3. Focus on edge cases for pattern discovery

### Accuracy Improvement Opportunities
1. **Current Date Extraction Rate**: {date_success_rate:.2f}%
2. **Target**: >98% accuracy
3. **Gap to Close**: {98 - date_success_rate:.2f} percentage points

## Next Steps
1. Review detailed date pattern analysis
2. Enhance date pattern library in MongoDB
3. Run iteration 2 with improved patterns
4. Continue until >98% accuracy achieved

## Files Generated
- `summary_report.md` - This overview report
- `detailed_results.json` - Complete pipeline results
- `date_pattern_analysis.json` - Date format pattern analysis
- `edge_cases.json` - Titles requiring pattern enhancement
- `sample_data.json` - Random sample for manual review (50 titles)
"""
        
        with open(output_path / "summary_report.md", 'w', encoding='utf-8') as f:
            f.write(summary_content)
    
    def _generate_detailed_json_report(self, output_path: Path) -> None:
        """Generate detailed JSON report with all results."""
        detailed_report = {
            'metadata': {
                'phase': 'Phase 2: Market Term Classifier → Date Extractor',
                'sample_size': self.sample_size,
                'total_processed': self.date_extraction_stats['total_processed'],
                'generation_time_utc': datetime.now(timezone.utc).isoformat(),
                'generation_time_pdt': datetime.now(pytz.timezone('America/Los_Angeles')).isoformat()
            },
            'statistics': {
                'classification_stats': dict(self.classification_stats),
                'date_extraction_stats': dict(self.date_extraction_stats)
            },
            'results': self.results
        }
        
        with open(output_path / "detailed_results.json", 'w', encoding='utf-8') as f:
            json.dump(detailed_report, f, indent=2, ensure_ascii=False)
    
    def _generate_date_pattern_analysis(self, output_path: Path) -> None:
        """Generate comprehensive date pattern analysis."""
        pattern_analysis = {
            'format_patterns': {},
            'confidence_distribution': {},
            'pattern_variations': {}
        }
        
        for format_type, patterns in self.date_format_patterns.items():
            if patterns:
                # Analyze confidence scores
                confidences = [p['confidence'] for p in patterns]
                pattern_analysis['confidence_distribution'][format_type] = {
                    'count': len(confidences),
                    'avg_confidence': sum(confidences) / len(confidences),
                    'min_confidence': min(confidences),
                    'max_confidence': max(confidences)
                }
                
                # Analyze raw pattern variations
                raw_matches = [p['raw_match'] for p in patterns if p['raw_match']]
                pattern_analysis['pattern_variations'][format_type] = {
                    'unique_patterns': list(set(raw_matches)),
                    'pattern_frequency': dict(Counter(raw_matches))
                }
                
                # Store sample patterns
                pattern_analysis['format_patterns'][format_type] = patterns[:10]  # First 10 examples
        
        with open(output_path / "date_pattern_analysis.json", 'w', encoding='utf-8') as f:
            json.dump(pattern_analysis, f, indent=2, ensure_ascii=False)
    
    def _generate_edge_cases_report(self, output_path: Path) -> None:
        """Generate edge cases report for pattern enhancement."""
        edge_cases_report = {
            'metadata': {
                'total_edge_cases': len(self.edge_cases),
                'description': 'Titles that failed date extraction and require pattern analysis'
            },
            'edge_cases': self.edge_cases
        }
        
        with open(output_path / "edge_cases.json", 'w', encoding='utf-8') as f:
            json.dump(edge_cases_report, f, indent=2, ensure_ascii=False)
    
    def _generate_sample_data(self, output_path: Path) -> None:
        """Generate random sample for manual review."""
        # Select 50 random successful results for manual review
        successful_results = [r for r in self.results if r['error'] is None]
        sample_size = min(50, len(successful_results))
        sample_data = random.sample(successful_results, sample_size)
        
        sample_report = {
            'metadata': {
                'sample_size': sample_size,
                'description': 'Random sample of pipeline results for manual quality review'
            },
            'samples': sample_data
        }
        
        with open(output_path / "sample_data.json", 'w', encoding='utf-8') as f:
            json.dump(sample_report, f, indent=2, ensure_ascii=False)

def main():
    """Main execution function."""
    print("Phase 2 Pipeline Test Harness: Market Term Classifier → Date Extractor")
    print("=" * 70)
    
    # Create test harness with larger sample for Phase 2
    sample_size = 1000  # Start with 1000, can increase to 2000 if needed
    test_harness = Phase2PipelineTestHarness(sample_size=sample_size)
    
    # Run the test suite
    test_harness.run_test_suite()
    
    # Generate comprehensive reports
    output_dir = test_harness.generate_reports()
    
    print(f"\nPhase 2 pipeline testing complete!")
    print(f"Reports generated in: {output_dir}")
    print("\nNext steps:")
    print("1. Review summary_report.md for overview")
    print("2. Analyze date_pattern_analysis.json for pattern enhancement")
    print("3. Review edge_cases.json for pattern library additions")
    print("4. Use sample_data.json for manual quality validation")

if __name__ == "__main__":
    main()