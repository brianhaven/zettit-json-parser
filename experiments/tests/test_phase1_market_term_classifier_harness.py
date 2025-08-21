#!/usr/bin/env python3

"""
Phase 1 Testing Harness for Market Term Classifier
Tests the 01_market_term_classifier_v1.py on real MongoDB documents
Generates markdown and JSON reports for manual review
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

# Import the classifier to test
import importlib.util
import sys

# Load the classifier module dynamically
classifier_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '01_market_term_classifier_v1.py')
spec = importlib.util.spec_from_file_location("market_term_classifier_v1", classifier_path)
classifier_module = importlib.util.module_from_spec(spec)
sys.modules["market_term_classifier_v1"] = classifier_module
spec.loader.exec_module(classifier_module)

# Import the classes
MarketTermClassifier = classifier_module.MarketTermClassifier
MarketTermType = classifier_module.MarketTermType
ClassificationResult = classifier_module.ClassificationResult

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class MarketTermClassifierTestHarness:
    """Test harness for systematic testing of Market Term Classifier."""
    
    def __init__(self, sample_size: int = 1000):
        """
        Initialize the test harness.
        
        Args:
            sample_size: Number of documents to test (default 1000)
        """
        self.sample_size = sample_size
        self.classifier = MarketTermClassifier()
        self.results = []
        self.stats = defaultdict(int)
        self.pattern_variations = defaultdict(list)
        
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
        
        # Use MongoDB aggregation to get random sample
        pipeline = [
            {"$sample": {"size": self.sample_size}},
            {"$project": {
                "_id": 1,
                "report_title_short": 1,
                "report_description_full": 1,
                "url": 1
            }}
        ]
        
        documents = list(self.collection.aggregate(pipeline))
        logger.info(f"Fetched {len(documents)} documents for testing")
        
        return documents
    
    def run_classification_tests(self, documents: List[Dict]) -> None:
        """
        Run classification on all test documents.
        
        Args:
            documents: List of documents to test
        """
        logger.info("Starting classification tests...")
        
        for idx, doc in enumerate(documents, 1):
            if idx % 100 == 0:
                logger.info(f"Processing document {idx}/{len(documents)}...")
            
            title = doc.get('report_title_short', '')
            if not title:
                logger.warning(f"Document {doc.get('_id', 'unknown')} has no report_title_short, skipping")
                continue
            
            logger.debug(f"Processing title: {title[:100]}...")
            
            # Run classification
            result = self.classifier.classify(title)
            
            # Store result with document metadata
            test_result = {
                'document_id': str(doc.get('_id', '')),
                'original_title': title,
                'classification': result.market_type.value,
                'confidence': result.confidence,
                'matched_pattern': result.matched_pattern,
                'preprocessing': result.preprocessing_applied,
                'notes': result.notes
            }
            
            self.results.append(test_result)
            
            # Update statistics
            self.stats['total'] += 1
            self.stats[result.market_type.value] += 1
            
            # Track pattern variations
            if result.market_type in [MarketTermType.MARKET_FOR, MarketTermType.MARKET_IN]:
                self.pattern_variations[result.market_type.value].append({
                    'title': title,
                    'pattern': result.matched_pattern
                })
    
    def analyze_results(self) -> Dict:
        """
        Analyze classification results and generate statistics.
        
        Returns:
            Dictionary of analysis results
        """
        logger.info("Analyzing classification results...")
        
        analysis = {
            'summary': {
                'total_documents': self.stats['total'],
                'market_for_count': self.stats['market_for'],
                'market_in_count': self.stats['market_in'],
                'standard_count': self.stats['standard'],
                'ambiguous_count': self.stats['ambiguous'],
                'market_for_percentage': (self.stats['market_for'] / self.stats['total'] * 100) if self.stats['total'] > 0 else 0,
                'market_in_percentage': (self.stats['market_in'] / self.stats['total'] * 100) if self.stats['total'] > 0 else 0,
                'standard_percentage': (self.stats['standard'] / self.stats['total'] * 100) if self.stats['total'] > 0 else 0,
                'ambiguous_percentage': (self.stats['ambiguous'] / self.stats['total'] * 100) if self.stats['total'] > 0 else 0
            },
            'confidence_distribution': self._analyze_confidence_distribution(),
            'pattern_variations': self._analyze_pattern_variations(),
            'sample_results': self._get_sample_results()
        }
        
        return analysis
    
    def _analyze_confidence_distribution(self) -> Dict:
        """Analyze confidence score distribution."""
        confidence_ranges = {
            'high (>0.9)': 0,
            'medium (0.7-0.9)': 0,
            'low (<0.7)': 0
        }
        
        for result in self.results:
            conf = result['confidence']
            if conf > 0.9:
                confidence_ranges['high (>0.9)'] += 1
            elif conf >= 0.7:
                confidence_ranges['medium (0.7-0.9)'] += 1
            else:
                confidence_ranges['low (<0.7)'] += 1
        
        return confidence_ranges
    
    def _analyze_pattern_variations(self) -> Dict:
        """Analyze variations in matched patterns."""
        variations = {}
        
        for pattern_type, examples in self.pattern_variations.items():
            if examples:
                # Get unique patterns
                unique_patterns = list(set(ex['pattern'] for ex in examples if ex['pattern']))
                variations[pattern_type] = {
                    'count': len(examples),
                    'unique_patterns': unique_patterns,
                    'sample_titles': [ex['title'] for ex in examples[:5]]  # First 5 examples
                }
        
        return variations
    
    def _get_sample_results(self) -> Dict:
        """Get sample results for each classification type."""
        samples = {}
        
        for class_type in ['market_for', 'market_in', 'standard', 'ambiguous']:
            type_results = [r for r in self.results if r['classification'] == class_type]
            if type_results:
                # Get up to 10 samples
                sample_size = min(10, len(type_results))
                samples[class_type] = random.sample(type_results, sample_size)
        
        return samples
    
    def generate_markdown_report(self, analysis: Dict, output_path: str) -> None:
        """
        Generate markdown report for manual review.
        
        Args:
            analysis: Analysis results dictionary
            output_path: Path to save the markdown file
        """
        logger.info(f"Generating markdown report: {output_path}")
        
        # Get timestamps
        pdt = pytz.timezone('America/Los_Angeles')
        utc = pytz.UTC
        now_pdt = datetime.now(pdt)
        now_utc = datetime.now(utc)
        
        markdown_content = f"""# Market Term Classifier Testing Report - Phase 1

**Analysis Date (PDT):** {now_pdt.strftime('%Y-%m-%d %H:%M:%S PDT')}  
**Analysis Date (UTC):** {now_utc.strftime('%Y-%m-%d %H:%M:%S UTC')}

## Summary Statistics

| Metric | Count | Percentage |
|--------|-------|------------|
| Total Documents | {analysis['summary']['total_documents']:,} | 100% |
| Market For | {analysis['summary']['market_for_count']} | {analysis['summary']['market_for_percentage']:.2f}% |
| Market In | {analysis['summary']['market_in_count']} | {analysis['summary']['market_in_percentage']:.2f}% |
| Standard | {analysis['summary']['standard_count']} | {analysis['summary']['standard_percentage']:.2f}% |
| Ambiguous | {analysis['summary']['ambiguous_count']} | {analysis['summary']['ambiguous_percentage']:.2f}% |

## Confidence Distribution

| Confidence Range | Count |
|-----------------|-------|
"""
        
        for range_name, count in analysis['confidence_distribution'].items():
            markdown_content += f"| {range_name} | {count} |\n"
        
        # Add pattern variations section
        markdown_content += "\n## Pattern Variations Discovered\n\n"
        
        if analysis['pattern_variations']:
            for pattern_type, info in analysis['pattern_variations'].items():
                markdown_content += f"### {pattern_type.replace('_', ' ').title()}\n\n"
                markdown_content += f"- **Total Found:** {info['count']}\n"
                markdown_content += f"- **Unique Patterns:** {len(info['unique_patterns'])}\n"
                markdown_content += f"- **Sample Titles:**\n"
                for title in info['sample_titles']:
                    markdown_content += f"  - {title}\n"
                markdown_content += "\n"
        else:
            markdown_content += "No special pattern variations found (all standard processing).\n\n"
        
        # Add sample results section
        markdown_content += "## Sample Results for Manual Review\n\n"
        
        for class_type, samples in analysis['sample_results'].items():
            markdown_content += f"### {class_type.replace('_', ' ').title()} Classifications\n\n"
            
            if samples:
                for idx, sample in enumerate(samples, 1):
                    markdown_content += f"**{idx}. Title:** {sample['original_title']}\n"
                    markdown_content += f"   - **Confidence:** {sample['confidence']:.3f}\n"
                    if sample['matched_pattern']:
                        markdown_content += f"   - **Pattern:** {sample['matched_pattern']}\n"
                    if sample['notes']:
                        markdown_content += f"   - **Notes:** {sample['notes']}\n"
                    markdown_content += "\n"
            else:
                markdown_content += "No samples found for this classification type.\n\n"
        
        # Add recommendations section
        markdown_content += self._generate_recommendations(analysis)
        
        # Write the report
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(markdown_content)
        
        logger.info(f"Markdown report saved to {output_path}")
    
    def generate_json_report(self, analysis: Dict, output_path: str) -> None:
        """
        Generate JSON report for programmatic analysis.
        
        Args:
            analysis: Analysis results dictionary
            output_path: Path to save the JSON file
        """
        logger.info(f"Generating JSON report: {output_path}")
        
        # Get timestamps
        pdt = pytz.timezone('America/Los_Angeles')
        utc = pytz.UTC
        now_pdt = datetime.now(pdt)
        now_utc = datetime.now(utc)
        
        json_report = {
            'metadata': {
                'analysis_date_pdt': now_pdt.strftime('%Y-%m-%d %H:%M:%S PDT'),
                'analysis_date_utc': now_utc.strftime('%Y-%m-%d %H:%M:%S UTC'),
                'sample_size': self.sample_size,
                'classifier_version': '1.0'
            },
            'summary': analysis['summary'],
            'confidence_distribution': analysis['confidence_distribution'],
            'pattern_variations': analysis['pattern_variations'],
            'sample_results': analysis['sample_results'],
            'full_results': self.results  # Include all results for detailed analysis
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(json_report, f, indent=2, ensure_ascii=False)
        
        logger.info(f"JSON report saved to {output_path}")
    
    def _generate_recommendations(self, analysis: Dict) -> str:
        """Generate recommendations based on analysis results."""
        recommendations = "\n## Recommendations\n\n"
        
        # Check if percentages match expected ranges
        market_for_pct = analysis['summary']['market_for_percentage']
        market_in_pct = analysis['summary']['market_in_percentage']
        
        recommendations += "### Pattern Distribution Analysis\n\n"
        
        if market_for_pct < 0.1:
            recommendations += f"- ⚠️ **Market For** patterns ({market_for_pct:.2f}%) are below expected ~0.2%. May need pattern enhancement.\n"
        elif market_for_pct > 0.5:
            recommendations += f"- ⚠️ **Market For** patterns ({market_for_pct:.2f}%) are above expected ~0.2%. May have false positives.\n"
        else:
            recommendations += f"- ✅ **Market For** patterns ({market_for_pct:.2f}%) are within expected range (~0.2%).\n"
        
        if market_in_pct < 0.05:
            recommendations += f"- ⚠️ **Market In** patterns ({market_in_pct:.2f}%) are below expected ~0.1%. May need pattern enhancement.\n"
        elif market_in_pct > 0.3:
            recommendations += f"- ⚠️ **Market In** patterns ({market_in_pct:.2f}%) are above expected ~0.1%. May have false positives.\n"
        else:
            recommendations += f"- ✅ **Market In** patterns ({market_in_pct:.2f}%) are within expected range (~0.1%).\n"
        
        # Check confidence distribution
        confidence_dist = analysis['confidence_distribution']
        high_conf = confidence_dist.get('high (>0.9)', 0)
        low_conf = confidence_dist.get('low (<0.7)', 0)
        
        recommendations += "\n### Confidence Score Analysis\n\n"
        
        total_docs = self.stats['total']
        if total_docs > 0:
            if high_conf / total_docs > 0.95:
                recommendations += "- ✅ Excellent confidence scores - over 95% of classifications have high confidence.\n"
            elif low_conf / total_docs > 0.1:
                recommendations += f"- ⚠️ {low_conf} documents ({low_conf/total_docs*100:.1f}%) have low confidence. Review for pattern improvements.\n"
        
        # Check for ambiguous classifications
        if analysis['summary']['ambiguous_count'] > 0:
            recommendations += f"\n### Ambiguous Classifications\n\n"
            recommendations += f"- ⚠️ Found {analysis['summary']['ambiguous_count']} ambiguous classifications. These need manual review.\n"
        
        recommendations += "\n### Next Steps\n\n"
        recommendations += "1. Review sample results for misclassifications\n"
        recommendations += "2. Identify new pattern variations from the results\n"
        recommendations += "3. Update MongoDB pattern library with discovered patterns\n"
        recommendations += "4. Run iteration 2 tests to measure improvement\n"
        
        return recommendations
    
    def run_full_test(self) -> None:
        """Run the complete test harness workflow."""
        logger.info("=" * 80)
        logger.info("Starting Phase 1: Market Term Classifier Testing")
        logger.info("=" * 80)
        
        # Fetch test documents
        documents = self.fetch_test_documents()
        
        # Run classification tests
        self.run_classification_tests(documents)
        
        # Analyze results
        analysis = self.analyze_results()
        
        # Generate output directory with timestamp
        pdt = pytz.timezone('America/Los_Angeles')
        timestamp = datetime.now(pdt).strftime('%Y%m%d_%H%M%S')
        output_dir = Path('../../outputs') / f'{timestamp}_phase1_market_term_classifier'
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate reports
        markdown_path = output_dir / 'classification_report.md'
        json_path = output_dir / 'classification_results.json'
        
        self.generate_markdown_report(analysis, str(markdown_path))
        self.generate_json_report(analysis, str(json_path))
        
        # Print summary to console
        logger.info("=" * 80)
        logger.info("Test Harness Complete!")
        logger.info("=" * 80)
        logger.info(f"Total documents tested: {self.stats['total']:,}")
        logger.info(f"Market For: {self.stats['market_for']} ({analysis['summary']['market_for_percentage']:.2f}%)")
        logger.info(f"Market In: {self.stats['market_in']} ({analysis['summary']['market_in_percentage']:.2f}%)")
        logger.info(f"Standard: {self.stats['standard']} ({analysis['summary']['standard_percentage']:.2f}%)")
        logger.info(f"Ambiguous: {self.stats['ambiguous']} ({analysis['summary']['ambiguous_percentage']:.2f}%)")
        logger.info("=" * 80)
        logger.info(f"Reports saved to: {output_dir}")
        logger.info("=" * 80)


def main():
    """Main entry point for the test harness."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Test Market Term Classifier on MongoDB documents')
    parser.add_argument('--sample-size', type=int, default=1000,
                        help='Number of documents to test (default: 1000)')
    parser.add_argument('--seed', type=int, default=None,
                        help='Random seed for reproducible sampling')
    
    args = parser.parse_args()
    
    # Set random seed if provided
    if args.seed:
        random.seed(args.seed)
        logger.info(f"Using random seed: {args.seed}")
    
    # Create and run test harness
    harness = MarketTermClassifierTestHarness(sample_size=args.sample_size)
    harness.run_full_test()


if __name__ == '__main__':
    main()