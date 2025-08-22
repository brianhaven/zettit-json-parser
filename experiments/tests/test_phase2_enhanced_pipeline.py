#!/usr/bin/env python3

"""
Enhanced Phase 2 Pipeline Test with Numeric Pre-filtering
Distinguishes between titles with no dates vs titles with missed dates.
"""

import os
import sys
import logging
from datetime import datetime, timezone
import pytz
from pathlib import Path
from dotenv import load_dotenv
import importlib.util
import json
from typing import Dict, List
from pymongo import MongoClient

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class EnhancedPhase2TestHarness:
    """Enhanced Phase 2 pipeline test with numeric pre-filtering."""
    
    def __init__(self):
        """Initialize the enhanced test harness."""
        
        # Import modules dynamically
        self._import_modules()
        
        # Initialize components
        self.pattern_manager = self.PatternLibraryManager()
        self.classifier = self.MarketTermClassifier(self.pattern_manager)
        self.enhanced_extractor = self.EnhancedDateExtractor(self.pattern_manager)
        
        # Connect to MongoDB
        self.client = MongoClient(os.getenv('MONGODB_URI'))
        self.db = self.client['deathstar']
        self.collection = self.db['markets_raw']
        
        # Results storage
        self.results = []
        self.categorized_results = {
            'successful_extractions': [],
            'no_dates_present': [],
            'dates_missed': [],
            'processing_errors': []
        }
        
        logger.info(f"Connected to MongoDB. Found {self.collection.count_documents({})} documents in markets_raw")
    
    def _import_modules(self):
        """Import required modules dynamically."""
        
        # Market Term Classifier
        classifier_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '01_market_term_classifier_v1.py')
        spec = importlib.util.spec_from_file_location("market_term_classifier_v1", classifier_path)
        classifier_module = importlib.util.module_from_spec(spec)
        sys.modules["market_term_classifier_v1"] = classifier_module
        spec.loader.exec_module(classifier_module)
        
        self.MarketTermClassifier = classifier_module.MarketTermClassifier
        self.MarketTermType = classifier_module.MarketTermType
        self.ClassificationResult = classifier_module.ClassificationResult
        
        # Enhanced Date Extractor (now the main 02 script)
        extractor_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '02_date_extractor_v1.py')
        spec2 = importlib.util.spec_from_file_location("enhanced_date_extractor_v1", extractor_path)
        extractor_module = importlib.util.module_from_spec(spec2)
        sys.modules["enhanced_date_extractor_v1"] = extractor_module
        spec2.loader.exec_module(extractor_module)
        
        self.EnhancedDateExtractor = extractor_module.EnhancedDateExtractor
        self.DateFormat = extractor_module.DateFormat
        self.EnhancedDateExtractionResult = extractor_module.EnhancedDateExtractionResult
        
        # Pattern Library Manager
        pattern_manager_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '00b_pattern_library_manager_v1.py')
        spec3 = importlib.util.spec_from_file_location("pattern_library_manager_v1", pattern_manager_path)
        pattern_manager_module = importlib.util.module_from_spec(spec3)
        sys.modules["pattern_library_manager_v1"] = pattern_manager_module
        spec3.loader.exec_module(pattern_manager_module)
        
        self.PatternLibraryManager = pattern_manager_module.PatternLibraryManager
        self.PatternType = pattern_manager_module.PatternType
    
    def fetch_test_documents(self, sample_size: int = 1000) -> List[Dict]:
        """Fetch test documents from MongoDB."""
        logger.info(f"Fetching {sample_size} random documents from MongoDB...")
        
        # Use simple find with limit instead of aggregation to avoid memory issues
        documents = list(self.collection.find().limit(sample_size))
        
        logger.info(f"Successfully fetched {len(documents)} documents")
        return documents
    
    def run_enhanced_pipeline_test(self, sample_size: int = 1000):
        """Run the enhanced pipeline test."""
        logger.info("Starting Enhanced Phase 2 Pipeline Test")
        
        # Fetch test documents
        documents = self.fetch_test_documents(sample_size)
        
        # Process each document
        logger.info("Processing documents through enhanced 01→02 pipeline...")
        
        for i, doc in enumerate(documents, 1):
            if i % 100 == 0:
                logger.info(f"Processed {i}/{len(documents)} documents...")
            
            try:
                title = doc.get('report_title_short', '')
                
                # Step 1: Market Term Classification
                classification_result = self.classifier.classify(title)
                market_type = classification_result.market_type
                
                # Step 2: Enhanced Date Extraction
                extraction_result = self.enhanced_extractor.extract(title)
                
                # Create result record
                result = {
                    'title': title,
                    'market_classification': str(market_type),
                    'extraction_result': {
                        'extracted_date_range': extraction_result.extracted_date_range,
                        'format_type': str(extraction_result.format_type),
                        'confidence': extraction_result.confidence,
                        'matched_pattern': extraction_result.matched_pattern,
                        'raw_match': extraction_result.raw_match,
                        'has_numeric_content': extraction_result.has_numeric_content,
                        'numeric_values_found': extraction_result.numeric_values_found,
                        'categorization': extraction_result.categorization,
                        'notes': extraction_result.notes
                    }
                }
                
                self.results.append(result)
                
                # Categorize result - map the categorization to the correct key
                category = extraction_result.categorization
                if category == "success":
                    self.categorized_results['successful_extractions'].append(result)
                elif category == "no_dates_present":
                    self.categorized_results['no_dates_present'].append(result)
                elif category == "dates_missed":
                    self.categorized_results['dates_missed'].append(result)
                
            except Exception as e:
                error_result = {
                    'title': title,
                    'error': str(e),
                    'categorization': 'processing_error'
                }
                self.results.append(error_result)
                self.categorized_results['processing_errors'].append(error_result)
                logger.error(f"Error processing '{title}': {e}")
        
        logger.info(f"Enhanced pipeline testing complete. Processed {len(documents)} documents.")
    
    def generate_enhanced_reports(self) -> str:
        """Generate enhanced reports with detailed categorization."""
        
        # Create timestamp-based output directory
        pdt = pytz.timezone('America/Los_Angeles')
        utc_now = datetime.now(timezone.utc)
        pdt_now = utc_now.astimezone(pdt)
        
        timestamp = pdt_now.strftime('%Y%m%d_%H%M%S')
        
        # Use absolute path for outputs directory
        script_dir = Path(__file__).parent.parent.parent
        output_dir = script_dir / "outputs" / f"{timestamp}_enhanced_phase2_pipeline"
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Generating enhanced reports in {output_dir}")
        
        # Generate summary report
        self._generate_enhanced_summary(output_path, pdt_now, utc_now)
        
        # Generate detailed categorized results
        self._generate_categorized_results(output_path)
        
        # Generate the specific lists you requested
        self._generate_title_lists(output_path)
        
        # Generate complete results
        self._generate_complete_results(output_path)
        
        logger.info(f"All enhanced reports generated in {output_dir}")
        return str(output_path)
    
    def _generate_enhanced_summary(self, output_path: Path, pdt_time: datetime, utc_time: datetime):
        """Generate enhanced summary with categorization."""
        
        total_processed = len(self.results)
        successful = len(self.categorized_results['successful_extractions'])
        no_dates = len(self.categorized_results['no_dates_present'])
        dates_missed = len(self.categorized_results['dates_missed'])
        errors = len(self.categorized_results['processing_errors'])
        
        # Calculate actual failure rate (excluding no_dates_present)
        titles_with_dates = successful + dates_missed
        actual_failure_rate = (dates_missed / titles_with_dates * 100) if titles_with_dates > 0 else 0
        true_success_rate = (successful / titles_with_dates * 100) if titles_with_dates > 0 else 0
        
        summary = f"""# Enhanced Phase 2 Pipeline Test Results: Market Term Classifier → Enhanced Date Extractor

**Analysis Date (PDT):** {pdt_time.strftime('%Y-%m-%d %H:%M:%S PDT')}
**Analysis Date (UTC):** {utc_time.strftime('%Y-%m-%d %H:%M:%S UTC')}
**Sample Size:** {total_processed:,} documents
**Successfully Processed:** {total_processed:,} documents

## Enhanced Pipeline Performance Summary

### Date Extraction Categorization
- **Successful Extractions**: {successful} ({successful/total_processed*100:.1f}%)
- **No Dates Present**: {no_dates} ({no_dates/total_processed*100:.1f}%)
- **Dates Missed**: {dates_missed} ({dates_missed/total_processed*100:.1f}%)
- **Processing Errors**: {errors} ({errors/total_processed*100:.1f}%)

### Key Insights

#### Actual Performance Metrics
- **Titles with Dates**: {titles_with_dates} ({titles_with_dates/total_processed*100:.1f}%)
- **True Success Rate**: {true_success_rate:.1f}% (of titles with dates)
- **True Failure Rate**: {actual_failure_rate:.1f}% (dates missed / titles with dates)

#### Pattern Coverage Analysis
- **No Numeric Content**: Titles without any dates (correctly identified)
- **Dates Missed**: Titles with year-like numbers but no patterns matched
- **Success Rate Improvement**: Focus should be on the {dates_missed} titles in "dates_missed" category

### Next Steps
1. Review `titles_with_dates_missed.txt` for pattern gaps
2. Analyze `numeric_analysis.json` for pattern enhancement opportunities
3. Consider the {no_dates} titles without dates as correctly processed (not failures)

## Files Generated
- `enhanced_summary.md` - This overview report
- `categorized_results.json` - Results organized by category
- `titles_with_dates_missed.txt` - Simple list of titles where dates were missed
- `titles_no_dates_present.txt` - Simple list of titles without dates
- `titles_successful_extractions.txt` - Simple list of successfully processed titles
- `numeric_analysis.json` - Detailed numeric content analysis
- `complete_results.json` - Complete pipeline results
"""
        
        with open(output_path / "enhanced_summary.md", 'w') as f:
            f.write(summary)
    
    def _generate_categorized_results(self, output_path: Path):
        """Generate categorized results JSON."""
        
        categorized_data = {
            'metadata': {
                'total_documents': len(self.results),
                'categories': {
                    'successful_extractions': len(self.categorized_results['successful_extractions']),
                    'no_dates_present': len(self.categorized_results['no_dates_present']),
                    'dates_missed': len(self.categorized_results['dates_missed']),
                    'processing_errors': len(self.categorized_results['processing_errors'])
                },
                'generation_time': datetime.now().isoformat()
            },
            'categorized_results': self.categorized_results
        }
        
        with open(output_path / "categorized_results.json", 'w') as f:
            json.dump(categorized_data, f, indent=2)
    
    def _generate_title_lists(self, output_path: Path):
        """Generate simple title lists for manual review."""
        
        # Titles where dates were missed (the important ones to review)
        dates_missed_titles = [result['title'] for result in self.categorized_results['dates_missed']]
        with open(output_path / "titles_with_dates_missed.txt", 'w') as f:
            f.write("# Titles with Dates Missed (Pattern Gaps)\n")
            f.write("# These titles contain year-like numbers but no patterns matched\n")
            f.write("# Review these for potential pattern library enhancements\n\n")
            for title in sorted(dates_missed_titles):
                f.write(f"{title}\n")
        
        # Titles without dates (should not be considered failures)
        no_dates_titles = [result['title'] for result in self.categorized_results['no_dates_present']]
        with open(output_path / "titles_no_dates_present.txt", 'w') as f:
            f.write("# Titles with No Dates Present\n")
            f.write("# These titles were correctly identified as not containing dates\n")
            f.write("# These should NOT be considered failures\n\n")
            for title in sorted(no_dates_titles):
                f.write(f"{title}\n")
        
        # Successfully extracted titles
        success_titles = [result['title'] for result in self.categorized_results['successful_extractions']]
        with open(output_path / "titles_successful_extractions.txt", 'w') as f:
            f.write("# Titles with Successful Date Extractions\n")
            f.write("# These titles had dates successfully extracted\n\n")
            for title in sorted(success_titles):
                f.write(f"{title}\n")
    
    def _generate_complete_results(self, output_path: Path):
        """Generate complete results JSON."""
        
        complete_data = {
            'metadata': {
                'total_documents': len(self.results),
                'generation_time': datetime.now().isoformat(),
                'extractor_stats': self.enhanced_extractor.get_stats()
            },
            'results': self.results
        }
        
        with open(output_path / "complete_results.json", 'w') as f:
            json.dump(complete_data, f, indent=2)
        
        # Also generate numeric analysis
        numeric_analysis = self._analyze_numeric_patterns()
        with open(output_path / "numeric_analysis.json", 'w') as f:
            json.dump(numeric_analysis, f, indent=2)
    
    def _analyze_numeric_patterns(self) -> Dict:
        """Analyze numeric patterns in the results."""
        
        analysis = {
            'dates_missed_analysis': [],
            'no_dates_analysis': [],
            'success_patterns': []
        }
        
        # Analyze dates missed
        for result in self.categorized_results['dates_missed']:
            extraction = result['extraction_result']
            analysis['dates_missed_analysis'].append({
                'title': result['title'],
                'numeric_values': extraction['numeric_values_found'],
                'notes': extraction['notes']
            })
        
        # Analyze no dates (sample)
        for result in self.categorized_results['no_dates_present'][:50]:  # First 50 as sample
            extraction = result['extraction_result']
            analysis['no_dates_analysis'].append({
                'title': result['title'],
                'numeric_values': extraction['numeric_values_found'],
                'has_numeric_content': extraction['has_numeric_content']
            })
        
        # Analyze successful patterns (sample)
        for result in self.categorized_results['successful_extractions'][:50]:  # First 50 as sample
            extraction = result['extraction_result']
            analysis['success_patterns'].append({
                'title': result['title'],
                'extracted_date': extraction['extracted_date_range'],
                'format_type': extraction['format_type'],
                'matched_pattern': extraction['matched_pattern']
            })
        
        return analysis

def main():
    """Main function to run enhanced Phase 2 test."""
    
    test_harness = EnhancedPhase2TestHarness()
    
    # Run the enhanced test
    test_harness.run_enhanced_pipeline_test(sample_size=1000)
    
    # Generate enhanced reports
    output_dir = test_harness.generate_enhanced_reports()
    
    # Display summary
    stats = test_harness.enhanced_extractor.get_stats()
    total = stats['total_processed']
    successful = stats['successful_extractions']
    no_dates = stats['no_dates_present']
    dates_missed = stats['dates_missed']
    
    print(f"\n✅ Enhanced Phase 2 Pipeline Test Complete!")
    print(f"📊 Results Summary:")
    print(f"  - Total Processed: {total}")
    print(f"  - Successful Extractions: {successful} ({successful/total*100:.1f}%)")
    print(f"  - No Dates Present: {no_dates} ({no_dates/total*100:.1f}%)")
    print(f"  - Dates Missed: {dates_missed} ({dates_missed/total*100:.1f}%)")
    titles_with_dates = successful + dates_missed
    true_success_rate = (successful / titles_with_dates * 100) if titles_with_dates > 0 else 0
    print(f"  - True Success Rate: {true_success_rate:.1f}% (of titles with dates)")
    print(f"📁 Full results in: {output_dir}")
    print(f"📋 Review 'titles_with_dates_missed.txt' for pattern gaps")

if __name__ == "__main__":
    main()