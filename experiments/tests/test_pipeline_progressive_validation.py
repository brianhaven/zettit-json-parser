#!/usr/bin/env python3

"""
Progressive Pipeline Validation Test Suite
Tests Scripts 01→02→03 with increasing document counts: 100 → 250 → 1000

Generates comprehensive output files for manual review:
- Detailed JSON results with full extraction data
- Summary statistics and success rates
- One-line simplified results for quick manual scanning
- Error analysis and pattern performance metrics

Created for Market Research Title Parser project.
"""

import sys
import os
import json
import logging
from datetime import datetime, timezone
import pytz
from typing import Dict, List, Optional, Any
import importlib.util
from pymongo import MongoClient
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add the experiments directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import all required modules using dynamic imports
experiments_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def import_module_dynamically(module_name: str, file_path: str):
    """Import a module dynamically from file path."""
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

# Import pattern library manager
pattern_manager = import_module_dynamically(
    "pattern_manager", 
    os.path.join(experiments_dir, '00b_pattern_library_manager_v1.py')
)
PatternLibraryManager = pattern_manager.PatternLibraryManager

# Import market term classifier
market_classifier = import_module_dynamically(
    "market_classifier",
    os.path.join(experiments_dir, '01_market_term_classifier_v1.py') 
)
MarketTermClassifier = market_classifier.MarketTermClassifier

# Import date extractor
date_extractor = import_module_dynamically(
    "date_extractor",
    os.path.join(experiments_dir, '02_date_extractor_v1.py')
)
EnhancedDateExtractor = date_extractor.EnhancedDateExtractor

# Import report type extractor  
report_extractor = import_module_dynamically(
    "report_extractor", 
    os.path.join(experiments_dir, '03_report_type_extractor_v2.py')
)
MarketAwareReportTypeExtractor = report_extractor.MarketAwareReportTypeExtractor

def setup_logging() -> logging.Logger:
    """Set up logging for the test suite."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    return logging.getLogger(__name__)

def get_pdt_timestamp() -> str:
    """Get current PDT timestamp."""
    pdt = pytz.timezone('US/Pacific')
    return datetime.now(pdt).strftime('%Y%m%d_%H%M%S')

def get_dual_timestamps() -> tuple:
    """Get dual PDT and UTC timestamps for output headers."""
    pdt = pytz.timezone('US/Pacific') 
    utc = pytz.timezone('UTC')
    now_pdt = datetime.now(pdt)
    now_utc = datetime.now(utc)
    return (
        now_pdt.strftime('%Y-%m-%d %H:%M:%S PDT'),
        now_utc.strftime('%Y-%m-%d %H:%M:%S UTC')
    )

def load_test_documents(count: int) -> List[Dict]:
    """Load stratified random test documents from markets_raw collection."""
    import random
    
    client = MongoClient(os.getenv('MONGODB_URI'))
    db = client['deathstar']
    
    # Get publisher distribution first
    publisher_pipeline = [
        {"$match": {"report_title_short": {"$exists": True, "$ne": None, "$ne": ""}}},
        {"$group": {"_id": "$publisherID", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}}
    ]
    
    publishers = list(db.markets_raw.aggregate(publisher_pipeline))
    total_docs = sum(p['count'] for p in publishers)
    
    print(f"📊 Total eligible documents in database: {total_docs:,}")
    print(f"🏢 Publisher distribution:")
    for pub in publishers:
        percentage = (pub['count'] / total_docs) * 100
        print(f"  - {pub['_id']}: {pub['count']:,} documents ({percentage:.1f}%)")
    
    if count >= total_docs:
        # If we want all or more than available, just get all
        documents = list(db.markets_raw.find(
            {"report_title_short": {"$exists": True, "$ne": None, "$ne": ""}},
            {"report_title_short": 1, "_id": 1, "publisherID": 1}
        ))
        print(f"📝 Retrieved all {len(documents)} available documents")
    else:
        # Stratified sampling: ensure proportional representation from each publisher
        documents = []
        
        print(f"🎲 Performing stratified sampling for {count} documents...")
        
        for pub in publishers:
            pub_id = pub['_id']
            pub_count = pub['count']
            
            # Calculate how many documents to sample from this publisher
            # Use proportional allocation with minimum 1 document if publisher has data
            target_from_pub = max(1, int((pub_count / total_docs) * count))
            
            # Don't sample more than available
            target_from_pub = min(target_from_pub, pub_count)
            
            if target_from_pub > 0:
                print(f"  📥 Sampling {target_from_pub} documents from {pub_id}...")
                
                # Get all documents from this publisher
                pub_docs = list(db.markets_raw.find(
                    {
                        "report_title_short": {"$exists": True, "$ne": None, "$ne": ""}, 
                        "publisherID": pub_id
                    },
                    {"report_title_short": 1, "_id": 1, "publisherID": 1}
                ))
                
                # Randomly sample from this publisher's documents
                if len(pub_docs) <= target_from_pub:
                    selected_docs = pub_docs
                else:
                    selected_docs = random.sample(pub_docs, target_from_pub)
                
                documents.extend(selected_docs)
        
        # If we haven't reached our target count, fill remaining slots randomly
        if len(documents) < count:
            remaining_needed = count - len(documents)
            print(f"  🔄 Need {remaining_needed} more documents, sampling randomly...")
            
            # Get document IDs already selected
            selected_ids = {doc['_id'] for doc in documents}
            
            # Sample additional documents
            extra_docs = []
            cursor = db.markets_raw.aggregate([
                {"$match": {
                    "report_title_short": {"$exists": True, "$ne": None, "$ne": ""}, 
                    "_id": {"$nin": list(selected_ids)}
                }},
                {"$sample": {"size": remaining_needed}}
            ])
            
            for doc in cursor:
                extra_docs.append({
                    "_id": doc["_id"],
                    "report_title_short": doc["report_title_short"],
                    "publisherID": doc.get("publisherID")
                })
            
            documents.extend(extra_docs)
        
        # Shuffle the final list to avoid publisher clustering
        random.shuffle(documents)
    
    client.close()
    
    # Verify stratified sampling worked
    final_publishers = {}
    for doc in documents:
        pub_id = doc.get('publisherID', 'unknown')
        final_publishers[pub_id] = final_publishers.get(pub_id, 0) + 1
    
    print(f"✅ Final sample publisher diversity: {len(final_publishers)} unique publishers")
    for pub_id, count_in_sample in sorted(final_publishers.items(), key=lambda x: x[1], reverse=True):
        percentage = (count_in_sample / len(documents)) * 100
        print(f"  - {pub_id}: {count_in_sample} documents ({percentage:.1f}%)")
    
    return documents

class PipelineValidator:
    """Progressive pipeline validation orchestrator."""
    
    def __init__(self):
        self.logger = setup_logging()
        self.timestamp = get_pdt_timestamp()
        
        # Initialize all pipeline components
        self.logger.info("Initializing pipeline components...")
        
        try:
            self.pattern_manager = PatternLibraryManager()
            self.market_classifier = MarketTermClassifier(self.pattern_manager)
            self.date_extractor = EnhancedDateExtractor(self.pattern_manager)
            self.report_extractor = MarketAwareReportTypeExtractor(self.pattern_manager)
            self.logger.info("✅ All pipeline components initialized successfully")
        except Exception as e:
            self.logger.error(f"❌ Failed to initialize pipeline components: {e}")
            raise
    
    def process_single_document(self, doc: Dict) -> Dict:
        """Process a single document through the pipeline."""
        title = doc.get('report_title_short', '')
        doc_id = str(doc.get('_id', 'unknown'))
        
        result = {
            'document_id': doc_id,
            'original_title': title,
            'pipeline_results': {},
            'errors': [],
            'success_flags': {
                'market_classification': False,
                'date_extraction': False, 
                'report_type_extraction': False
            }
        }
        
        try:
            # Step 1: Market Term Classification
            market_result = self.market_classifier.classify(title)
            result['pipeline_results']['market_classification'] = {
                'market_type': market_result.market_type,
                'confidence': market_result.confidence,
                'matched_pattern': market_result.matched_pattern,
                'notes': market_result.notes
            }
            result['success_flags']['market_classification'] = True
            
            # Step 2: Date Extraction
            date_result = self.date_extractor.extract(title)
            result['pipeline_results']['date_extraction'] = {
                'extracted_date': date_result.extracted_date_range,
                'title_after_removal': date_result.cleaned_title,
                'format_type': date_result.format_type.value if date_result.format_type else None,
                'confidence': date_result.confidence,
                'extraction_status': date_result.categorization,
                'notes': f"Matched: {date_result.matched_pattern}, Preserved: {date_result.preserved_words}"
            }
            result['success_flags']['date_extraction'] = True
            
            # Step 3: Report Type Extraction
            report_result = self.report_extractor.extract(
                date_result.cleaned_title,
                market_result.market_type
            )
            result['pipeline_results']['report_type_extraction'] = {
                'final_report_type': report_result.final_report_type,
                'processing_workflow': report_result.processing_workflow,
                'confidence': report_result.confidence,
                'notes': report_result.notes,
                'title_for_next_stage': report_result.title
            }
            result['success_flags']['report_type_extraction'] = bool(report_result.final_report_type)
            
        except Exception as e:
            result['errors'].append(f"Pipeline processing error: {str(e)}")
            self.logger.error(f"Error processing document {doc_id}: {e}")
        
        return result
    
    def run_validation_test(self, document_count: int) -> Dict:
        """Run validation test with specified document count."""
        self.logger.info(f"Starting validation test with {document_count} documents...")
        
        # Load test documents
        documents = load_test_documents(document_count)
        if len(documents) < document_count:
            self.logger.warning(f"Only {len(documents)} documents available (requested {document_count})")
        
        # Process all documents
        results = []
        success_counts = {
            'market_classification': 0,
            'date_extraction': 0,
            'report_type_extraction': 0,
            'full_pipeline': 0
        }
        
        for i, doc in enumerate(documents, 1):
            if i % 25 == 0:
                self.logger.info(f"Progress: {i}/{len(documents)} documents processed")
            
            result = self.process_single_document(doc)
            results.append(result)
            
            # Update success counts
            for step, success in result['success_flags'].items():
                if success:
                    success_counts[step] += 1
            
            # Check full pipeline success
            if all(result['success_flags'].values()):
                success_counts['full_pipeline'] += 1
        
        # Calculate success rates
        total_docs = len(documents)
        success_rates = {
            step: (count / total_docs * 100) if total_docs > 0 else 0
            for step, count in success_counts.items()
        }
        
        # Generate comprehensive results
        pdt_time, utc_time = get_dual_timestamps()
        
        validation_results = {
            'test_metadata': {
                'analysis_date_pdt': pdt_time,
                'analysis_date_utc': utc_time,
                'document_count': total_docs,
                'requested_count': document_count,
                'pipeline_version': '01→02→03'
            },
            'success_rates': success_rates,
            'success_counts': success_counts,
            'detailed_results': results,
            'summary_statistics': self._generate_summary_statistics(results)
        }
        
        self.logger.info(f"Validation test completed:")
        self.logger.info(f"  - Market Classification: {success_rates['market_classification']:.1f}%")
        self.logger.info(f"  - Date Extraction: {success_rates['date_extraction']:.1f}%")
        self.logger.info(f"  - Report Type Extraction: {success_rates['report_type_extraction']:.1f}%")
        self.logger.info(f"  - Full Pipeline: {success_rates['full_pipeline']:.1f}%")
        
        return validation_results
    
    def _generate_summary_statistics(self, results: List[Dict]) -> Dict:
        """Generate summary statistics from results."""
        total = len(results)
        
        # Market type distribution
        market_types = {}
        date_statuses = {}
        report_types = {}
        
        for result in results:
            # Market type stats
            market_type = result['pipeline_results'].get('market_classification', {}).get('market_type', 'unknown')
            market_types[market_type] = market_types.get(market_type, 0) + 1
            
            # Date extraction stats
            date_status = result['pipeline_results'].get('date_extraction', {}).get('extraction_status', 'unknown')
            date_statuses[date_status] = date_statuses.get(date_status, 0) + 1
            
            # Report type stats
            report_type = result['pipeline_results'].get('report_type_extraction', {}).get('final_report_type')
            if report_type:
                report_types[report_type] = report_types.get(report_type, 0) + 1
        
        return {
            'market_type_distribution': market_types,
            'date_extraction_statuses': date_statuses,
            'report_type_distribution': report_types,
            'total_unique_report_types': len(report_types)
        }
    
    def save_output_files(self, results: Dict, document_count: int) -> None:
        """Save comprehensive output files for manual review."""
        outputs_base = os.path.join(experiments_dir, '..', 'outputs')
        os.makedirs(outputs_base, exist_ok=True)
        
        # Create timestamped subdirectory (matching previous script pattern)
        subdir_name = f"{self.timestamp}_pipeline_validation_{document_count}docs"
        outputs_dir = os.path.join(outputs_base, subdir_name)
        os.makedirs(outputs_dir, exist_ok=True)
        
        # 1. Detailed JSON results
        json_file = os.path.join(outputs_dir, "detailed_results.json")
        with open(json_file, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        # 2. Summary report
        summary_file = os.path.join(outputs_dir, "summary_report.md")
        self._write_summary_report(results, summary_file)
        
        # 3. One-line simplified results for manual review
        oneline_file = os.path.join(outputs_dir, "oneline_results.txt")
        self._write_oneline_results(results, oneline_file)
        
        # 4. Error analysis
        error_file = os.path.join(outputs_dir, "error_analysis.txt")
        self._write_error_analysis(results, error_file)
        
        self.logger.info(f"Output files saved to directory: {subdir_name}")
        self.logger.info(f"  - Detailed results: detailed_results.json")
        self.logger.info(f"  - Summary report: summary_report.md")
        self.logger.info(f"  - One-line results: oneline_results.txt")
        self.logger.info(f"  - Error analysis: error_analysis.txt")
    
    def _write_summary_report(self, results: Dict, file_path: str) -> None:
        """Write summary report to markdown file."""
        with open(file_path, 'w') as f:
            f.write(f"# Pipeline Validation Summary Report\n\n")
            f.write(f"**Analysis Date (PDT):** {results['test_metadata']['analysis_date_pdt']}\n")
            f.write(f"**Analysis Date (UTC):** {results['test_metadata']['analysis_date_utc']}\n")
            f.write(f"**Document Count:** {results['test_metadata']['document_count']}\n")
            f.write(f"**Pipeline Version:** {results['test_metadata']['pipeline_version']}\n\n")
            
            f.write(f"## Success Rates\n\n")
            for step, rate in results['success_rates'].items():
                f.write(f"- **{step.replace('_', ' ').title()}:** {rate:.1f}% ({results['success_counts'][step]}/{results['test_metadata']['document_count']})\n")
            
            f.write(f"\n## Summary Statistics\n\n")
            stats = results['summary_statistics']
            
            f.write(f"### Market Type Distribution\n")
            for market_type, count in sorted(stats['market_type_distribution'].items()):
                f.write(f"- {market_type}: {count}\n")
            
            f.write(f"\n### Date Extraction Status\n")
            for status, count in sorted(stats['date_extraction_statuses'].items()):
                f.write(f"- {status}: {count}\n")
            
            f.write(f"\n### Report Type Results\n")
            f.write(f"- Total unique report types extracted: {stats['total_unique_report_types']}\n")
            f.write(f"- Top 10 most common report types:\n")
            sorted_report_types = sorted(stats['report_type_distribution'].items(), key=lambda x: x[1], reverse=True)[:10]
            for report_type, count in sorted_report_types:
                f.write(f"  - {report_type}: {count}\n")
    
    def _write_oneline_results(self, results: Dict, file_path: str) -> None:
        """Write one-line results for quick manual review."""
        with open(file_path, 'w') as f:
            f.write(f"# One-Line Pipeline Results for Manual Review\n")
            f.write(f"# Generated: {results['test_metadata']['analysis_date_pdt']}\n") 
            f.write(f"# Format: [SUCCESS_FLAGS] ORIGINAL_TITLE → MARKET_TYPE | DATE_EXTRACTED | REPORT_TYPE\n\n")
            
            for result in results['detailed_results']:
                # Success flags
                flags = result['success_flags']
                flag_str = f"[{'M' if flags['market_classification'] else '-'}{'D' if flags['date_extraction'] else '-'}{'R' if flags['report_type_extraction'] else '-'}]"
                
                # Extracted values
                market_type = result['pipeline_results'].get('market_classification', {}).get('market_type', 'NONE')
                extracted_date = result['pipeline_results'].get('date_extraction', {}).get('extracted_date', 'NONE')
                report_type = result['pipeline_results'].get('report_type_extraction', {}).get('final_report_type', 'NONE')
                
                f.write(f"{flag_str} {result['original_title']} → {market_type} | {extracted_date} | {report_type}\n")
    
    def _write_error_analysis(self, results: Dict, file_path: str) -> None:
        """Write error analysis for debugging."""
        with open(file_path, 'w') as f:
            f.write(f"# Error Analysis Report\n")
            f.write(f"# Generated: {results['test_metadata']['analysis_date_pdt']}\n\n")
            
            error_docs = [r for r in results['detailed_results'] if r['errors']]
            f.write(f"Total documents with errors: {len(error_docs)}\n\n")
            
            if error_docs:
                for result in error_docs:
                    f.write(f"Document ID: {result['document_id']}\n")
                    f.write(f"Title: {result['original_title']}\n")
                    f.write(f"Errors: {', '.join(result['errors'])}\n")
                    f.write(f"Success flags: {result['success_flags']}\n")
                    f.write("---\n")

def main():
    """Main function to run progressive validation tests."""
    logger = setup_logging()
    
    logger.info("="*60)
    logger.info("Progressive Pipeline Validation Test Suite")
    logger.info("Testing Scripts 01→02→03 with live data")
    logger.info("="*60)
    
    validator = PipelineValidator()
    
    # Check for command line argument for specific test count
    if len(sys.argv) > 1:
        try:
            count = int(sys.argv[1])
            logger.info(f"\n🚀 Running single test with {count} documents...")
            
            results = validator.run_validation_test(count)
            validator.save_output_files(results, count)
            
            logger.info(f"✅ Test with {count} documents completed successfully!")
            logger.info(f"Full pipeline success rate: {results['success_rates']['full_pipeline']:.1f}%")
            
            return
            
        except ValueError:
            logger.error(f"❌ Invalid argument: {sys.argv[1]}. Please provide a valid number.")
            return
        except Exception as e:
            logger.error(f"❌ Test with {count} documents failed: {e}")
            return
    
    # Default: run progressive tests
    test_counts = [100, 250, 1000]  # Progressive test sizes
    
    for count in test_counts:
        logger.info(f"\n🚀 Starting validation test with {count} documents...")
        
        try:
            results = validator.run_validation_test(count)
            validator.save_output_files(results, count)
            
            logger.info(f"✅ Test with {count} documents completed successfully!")
            logger.info(f"Full pipeline success rate: {results['success_rates']['full_pipeline']:.1f}%")
            
            # Pause for manual review (in actual usage)
            print(f"\n⏸️  PAUSE FOR MANUAL REVIEW")
            print(f"Please review the output files for {count} documents before proceeding.")
            print(f"Files saved in directory: {validator.timestamp}_pipeline_validation_{count}docs/")
            print("Press Enter to continue to next test size or Ctrl+C to stop...")
            input()
            
        except Exception as e:
            logger.error(f"❌ Test with {count} documents failed: {e}")
            break
    
    logger.info("\n🎯 Progressive validation testing completed!")

if __name__ == "__main__":
    main()