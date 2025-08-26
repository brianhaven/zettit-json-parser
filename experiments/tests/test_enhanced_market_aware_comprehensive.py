#!/usr/bin/env python3
"""
Enhanced Market-Aware Extractor Comprehensive Test
Based on working Phase 3 pipeline test pattern with comprehensive outputs
"""

import os
import sys
import re
import json
import logging
import importlib.util
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict
from collections import defaultdict
import pytz

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Dynamic imports for all pipeline components
def import_module_from_path(module_name: str, file_path: str):
    """Import a module from a file path."""
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

# Import pattern library manager
try:
    pattern_lib = import_module_from_path("pattern_library_manager_v1", "00b_pattern_library_manager_v1.py")
    PatternLibraryManager = pattern_lib.PatternLibraryManager
    PatternType = pattern_lib.PatternType
except Exception as e:
    logger.error(f"Could not import PatternLibraryManager: {e}")
    sys.exit(1)

# Import market term classifier
try:
    market_term_lib = import_module_from_path("market_term_classifier_v1", "01_market_term_classifier_v1.py")
    MarketTermClassifier = market_term_lib.MarketTermClassifier
    ClassificationResult = market_term_lib.ClassificationResult
except Exception as e:
    logger.error(f"Could not import MarketTermClassifier: {e}")
    sys.exit(1)

# Import date extractor (enhanced version)
try:
    date_extractor_lib = import_module_from_path("date_extractor_v1", "02_date_extractor_v1.py")
    EnhancedDateExtractor = date_extractor_lib.EnhancedDateExtractor
    EnhancedDateExtractionResult = date_extractor_lib.EnhancedDateExtractionResult
except Exception as e:
    logger.error(f"Could not import EnhancedDateExtractor: {e}")
    sys.exit(1)

# Import enhanced market-aware report type extractor
try:
    report_type_lib = import_module_from_path("report_type_extractor_market_aware_v1", "03_report_type_extractor_market_aware_v1.py")
    MarketAwareReportTypeExtractor = report_type_lib.MarketAwareReportTypeExtractor
except Exception as e:
    logger.error(f"Could not import MarketAwareReportTypeExtractor: {e}")
    sys.exit(1)

@dataclass
class EnhancedPipelineResult:
    """Complete enhanced pipeline extraction result."""
    title: str
    original_title: str
    
    # Market term classification (Phase 1)
    market_term_type: str
    market_term_confidence: float
    
    # Date extraction (Phase 2)
    extracted_date_range: Optional[str]
    date_confidence: float
    date_categorization: str
    title_after_date_removal: str
    
    # Enhanced report type extraction (Phase 3)
    extracted_report_type: Optional[str]
    normalized_report_type: Optional[str]
    report_type_confidence: float
    report_type_raw_match: Optional[str]
    context_analysis: str
    
    # Enhanced features
    confusing_terms_found: List[str]
    market_prefix_fallback_used: bool
    
    # Final topic (for validation)
    remaining_for_topic: str
    
    # Metadata
    processing_notes: List[str]
    total_confidence: float

@dataclass
class EnhancedPipelineStats:
    """Statistics for enhanced pipeline testing."""
    total_processed: int
    market_term_classification_stats: Dict
    date_extraction_stats: Dict
    report_type_stats: Dict
    enhanced_features_stats: Dict
    end_to_end_success_rate: float
    common_report_types: Dict[str, int]
    missing_report_types: List[str]

class EnhancedMarketAwareTester:
    """Enhanced Market-Aware Report Type Extractor comprehensive tester."""
    
    def __init__(self, sample_size: int = 1000):
        """Initialize enhanced pipeline tester."""
        self.sample_size = sample_size
        
        # Initialize pipeline components
        logger.info("Initializing Enhanced Market-Aware Pipeline components...")
        
        # Pattern library manager (shared across all components)
        self.pattern_manager = PatternLibraryManager()
        
        # Pipeline components with shared pattern manager
        self.market_term_classifier = MarketTermClassifier(self.pattern_manager)
        self.date_extractor = EnhancedDateExtractor(self.pattern_manager)
        self.market_aware_extractor = MarketAwareReportTypeExtractor(self.pattern_manager)
        
        # Results storage
        self.pipeline_results: List[EnhancedPipelineResult] = []
        self.current_output_dir = None
        
        logger.info("✅ Enhanced Market-Aware Pipeline components initialized successfully")
    
    def _get_sample_titles(self) -> List[str]:
        """Get sample titles from MongoDB for testing - using exact working pattern."""
        try:
            from pymongo import MongoClient
            from dotenv import load_dotenv
            load_dotenv()
            
            client = MongoClient(os.getenv('MONGODB_URI'))
            db = client['deathstar']
            collection = db['markets_raw']
            
            # Get sample titles
            sample_titles = []
            cursor = collection.aggregate([
                {'$sample': {'size': self.sample_size}},
                {'$project': {'report_title_short': 1, '_id': 0}}
            ])
            
            for doc in cursor:
                if 'report_title_short' in doc and doc['report_title_short']:
                    sample_titles.append(doc['report_title_short'].strip())
            
            client.close()
            logger.info(f"Retrieved {len(sample_titles)} sample titles from MongoDB")
            return sample_titles
            
        except Exception as e:
            logger.error(f"Error retrieving sample titles: {e}")
            return []
    
    def _process_single_title(self, title: str) -> EnhancedPipelineResult:
        """Process a single title through the enhanced pipeline."""
        
        processing_notes = []
        
        # Phase 1: Market term classification
        try:
            market_result = self.market_term_classifier.classify(title)
            market_term_type = market_result.market_type
            market_confidence = market_result.confidence
            processing_notes.append(f"Market term: {market_term_type}")
        except Exception as e:
            logger.warning(f"Market classification failed for '{title}': {e}")
            market_term_type = 'standard'
            market_confidence = 0.0
            processing_notes.append(f"Market classification failed: {e}")
        
        # Phase 2: Date extraction
        try:
            date_result = self.date_extractor.extract(title)
            extracted_date = date_result.extracted_date_range
            date_confidence = date_result.confidence
            date_categorization = date_result.categorization
            title_after_date_removal = date_result.cleaned_title
            processing_notes.append(f"Date extraction: {date_categorization}")
        except Exception as e:
            logger.warning(f"Date extraction failed for '{title}': {e}")
            extracted_date = None
            date_confidence = 0.0
            date_categorization = "failed"
            title_after_date_removal = title
            processing_notes.append(f"Date extraction failed: {e}")
        
        # Phase 3: Enhanced Market-aware report type extraction
        try:
            report_result = self.market_aware_extractor.extract(
                title=title_after_date_removal,
                market_term_type=market_term_type,
                original_title=title,
                date_extractor=self.date_extractor
            )
            
            extracted_report = report_result.final_report_type
            report_confidence = report_result.confidence
            context_analysis = report_result.context_analysis
            confusing_terms = getattr(report_result, 'confusing_terms_found', [])
            fallback_used = getattr(report_result, 'market_prepended', False)
            raw_match = getattr(report_result, 'raw_match', None)
            
            processing_notes.append(f"Report type: {extracted_report or 'unknown'}")
            
            if confusing_terms:
                processing_notes.append(f"Confusing terms: {', '.join(confusing_terms)}")
            if fallback_used:
                processing_notes.append("Market prefix fallback used")
                
        except Exception as e:
            logger.warning(f"Report type extraction failed for '{title}': {e}")
            extracted_report = None
            report_confidence = 0.0
            context_analysis = f"Error: {e}"
            confusing_terms = []
            fallback_used = False
            raw_match = None
            processing_notes.append(f"Report type extraction failed: {e}")
        
        # Calculate remaining topic (remove extracted elements)
        remaining_for_topic = title_after_date_removal
        if extracted_report and extracted_report in title_after_date_removal:
            remaining_for_topic = title_after_date_removal.replace(extracted_report, '').strip()
        
        # Clean up remaining topic
        remaining_for_topic = re.sub(r'\s+', ' ', remaining_for_topic).strip()
        remaining_for_topic = re.sub(r'^[,\-\s]+|[,\-\s]+$', '', remaining_for_topic)
        
        # Calculate total confidence
        total_confidence = (market_confidence + date_confidence + report_confidence) / 3
        
        return EnhancedPipelineResult(
            title=title,
            original_title=title,
            market_term_type=market_term_type,
            market_term_confidence=market_confidence,
            extracted_date_range=extracted_date,
            date_confidence=date_confidence,
            date_categorization=date_categorization,
            title_after_date_removal=title_after_date_removal,
            extracted_report_type=extracted_report,
            normalized_report_type=extracted_report,  # Same for now
            report_type_confidence=report_confidence,
            report_type_raw_match=raw_match,
            context_analysis=context_analysis,
            confusing_terms_found=confusing_terms,
            market_prefix_fallback_used=fallback_used,
            remaining_for_topic=remaining_for_topic,
            processing_notes=processing_notes,
            total_confidence=total_confidence
        )
    
    def run_pipeline_test(self) -> bool:
        """Run the complete enhanced pipeline test."""
        try:
            logger.info("Starting Enhanced Market-Aware Pipeline Test...")
            logger.info("="*80)
            
            # Get sample titles using the working method
            sample_titles = self._get_sample_titles()
            if not sample_titles:
                logger.error("No sample titles retrieved for testing")
                return False
            
            # Process each title through the pipeline
            logger.info(f"Processing {len(sample_titles)} titles through Enhanced Pipeline...")
            
            for i, title in enumerate(sample_titles):
                if i > 0 and i % 100 == 0:
                    logger.info(f"Processed {i}/{len(sample_titles)} titles...")
                
                try:
                    result = self._process_single_title(title)
                    self.pipeline_results.append(result)
                except Exception as e:
                    logger.warning(f"Failed to process title '{title}': {e}")
                    continue
            
            logger.info(f"✅ Successfully processed {len(self.pipeline_results)} titles")
            
            # Generate comprehensive analysis
            self._generate_comprehensive_reports()
            
            return True
            
        except Exception as e:
            logger.error(f"Enhanced pipeline test failed: {e}")
            return False
    
    def _generate_comprehensive_reports(self):
        """Generate comprehensive analysis reports matching Phase 3 output structure."""
        
        # Create timestamped output directory
        utc_now = datetime.now(timezone.utc)
        pdt_tz = pytz.timezone('America/Los_Angeles')
        pdt_now = utc_now.astimezone(pdt_tz)
        
        timestamp = pdt_now.strftime('%Y%m%d_%H%M%S')
        self.current_output_dir = f"../outputs/{timestamp}_enhanced_market_aware_comprehensive"
        os.makedirs(self.current_output_dir, exist_ok=True)
        
        pdt_str = pdt_now.strftime('%Y-%m-%d %H:%M:%S PDT')
        utc_str = utc_now.strftime('%Y-%m-%d %H:%M:%S UTC')
        
        # Generate all reports
        self._generate_summary_report(timestamp, pdt_str, utc_str)
        self._generate_results_json(timestamp, pdt_str, utc_str)
        self._generate_manual_review_files(timestamp, pdt_str, utc_str)
        self._generate_pattern_analysis_report(timestamp, pdt_str, utc_str)
        
        logger.info(f"✅ Comprehensive reports generated in: {self.current_output_dir}")
    
    def _generate_summary_report(self, timestamp: str, pdt_str: str, utc_str: str):
        """Generate executive summary report matching Phase 3 format."""
        
        total = len(self.pipeline_results)
        
        # Market term stats
        market_term_counts = defaultdict(int)
        for result in self.pipeline_results:
            market_term_counts[result.market_term_type] += 1
        
        # Date extraction stats
        date_success = sum(1 for r in self.pipeline_results if r.extracted_date_range)
        date_no_dates = sum(1 for r in self.pipeline_results if r.date_categorization == "no_dates_present")
        
        # Report type stats
        report_type_success = sum(1 for r in self.pipeline_results if r.extracted_report_type)
        report_type_counts = defaultdict(int)
        for result in self.pipeline_results:
            if result.normalized_report_type:
                report_type_counts[result.normalized_report_type] += 1
        
        # Enhanced features stats
        confusing_terms_handled = sum(1 for r in self.pipeline_results if r.confusing_terms_found)
        fallback_used = sum(1 for r in self.pipeline_results if r.market_prefix_fallback_used)
        
        # Generate report
        summary_file = f"{self.current_output_dir}/summary_report.md"
        with open(summary_file, 'w', encoding='utf-8') as f:
            f.write(f"""# Enhanced Market-Aware Extractor Test Summary Report

**Analysis Date (PDT):** {pdt_str}  
**Analysis Date (UTC):** {utc_str}

## Executive Summary

- **Total Titles Processed:** {total:,}
- **Market Term Classification Rate:** {(sum(market_term_counts.values())/total)*100:.1f}%
- **Date Extraction Success:** {(date_success/total)*100:.1f}% ({date_success:,}/{total:,})
- **Titles with No Dates:** {(date_no_dates/total)*100:.1f}% ({date_no_dates:,}/{total:,})
- **Report Type Extraction Success:** {(report_type_success/total)*100:.1f}% ({report_type_success:,}/{total:,})

## Enhanced Features Performance

- **Confusing Terms Handled:** {confusing_terms_handled:,} ({(confusing_terms_handled/total)*100:.1f}%)
- **Market Prefix Fallback Used:** {fallback_used:,} ({(fallback_used/total)*100:.1f}%)

## Phase 1: Market Term Classification Results

""")
            for term_type, count in sorted(market_term_counts.items(), key=lambda x: x[1], reverse=True):
                percentage = (count/total)*100
                f.write(f"- **{term_type}:** {count:,} titles ({percentage:.1f}%)\n")
            
            f.write(f"""

## Phase 2: Date Extraction Results

- **Successful Extractions:** {date_success:,} ({(date_success/total)*100:.1f}%)
- **No Dates Present:** {date_no_dates:,} ({(date_no_dates/total)*100:.1f}%)
- **Missed Dates:** {total - date_success - date_no_dates:,} ({((total - date_success - date_no_dates)/total)*100:.1f}%)

## Phase 3: Enhanced Report Type Extraction Results

- **Successful Extractions:** {report_type_success:,} ({(report_type_success/total)*100:.1f}%)
- **Failed Extractions:** {total - report_type_success:,} ({((total - report_type_success)/total)*100:.1f}%)

### Most Common Report Types

""")
            for report_type, count in sorted(report_type_counts.items(), key=lambda x: x[1], reverse=True)[:10]:
                percentage = (count/total)*100
                f.write(f"- **{report_type}:** {count:,} titles ({percentage:.1f}%)\n")
            
            f.write(f"""

## Enhanced Market-Aware Features

- **Confusing Terms Handled:** {confusing_terms_handled:,} ({(confusing_terms_handled/total)*100:.1f}%)
- **Market Prefix Fallback Used:** {fallback_used:,} ({(fallback_used/total)*100:.1f}%)

These are the enhanced features that differentiate this from the standard report type extractor.

## Recommendations for Next Iteration

1. **Enhanced Feature Optimization:** Analyze cases where confusing terms and fallback mechanisms are used
2. **Pattern Coverage:** Review failed extractions to identify missing patterns
3. **Confidence Scoring:** Analyze low-confidence extractions for improvements
4. **Performance Validation:** Compare enhanced vs standard extractor performance

""")
        
        logger.info(f"✅ Summary report generated: {summary_file}")
    
    def _generate_results_json(self, timestamp: str, pdt_str: str, utc_str: str):
        """Generate detailed JSON results file."""
        
        results_file = f"{self.current_output_dir}/pipeline_results.json"
        with open(results_file, 'w', encoding='utf-8') as f:
            json.dump({
                'metadata': {
                    'test_type': 'enhanced_market_aware_extractor',
                    'timestamp': timestamp,
                    'pdt_timestamp': pdt_str,
                    'utc_timestamp': utc_str,
                    'sample_size': self.sample_size,
                    'total_processed': len(self.pipeline_results)
                },
                'results': [asdict(result) for result in self.pipeline_results]
            }, f, indent=2, ensure_ascii=False)
        
        logger.info(f"✅ Pipeline results JSON generated: {results_file}")
    
    def _generate_manual_review_files(self, timestamp: str, pdt_str: str, utc_str: str):
        """Generate .txt files for manual review like Phase 3."""
        
        # 1. Successful extractions
        successful = [r for r in self.pipeline_results if r.extracted_report_type]
        success_file = f"{self.current_output_dir}/successful_extractions.txt"
        with open(success_file, 'w', encoding='utf-8') as f:
            f.write(f"Enhanced Market-Aware Successful Extractions\n")
            f.write(f"Analysis Date (PDT): {pdt_str}\n")
            f.write(f"Analysis Date (UTC): {utc_str}\n")
            f.write(f"{'='*80}\n\n")
            f.write(f"Total Successful Extractions: {len(successful):,}\n\n")
            
            for result in successful[:200]:  # First 200 for review
                f.write(f"Original: {result.original_title}\n")
                f.write(f"After Date Removal: {result.title_after_date_removal}\n")
                f.write(f"Market Term: {result.market_term_type}\n")
                f.write(f"Report Type: {result.extracted_report_type}\n")
                f.write(f"Confidence: {result.report_type_confidence:.3f}\n")
                f.write(f"Context: {result.context_analysis}\n")
                if result.confusing_terms_found:
                    f.write(f"Confusing Terms: {', '.join(result.confusing_terms_found)}\n")
                if result.market_prefix_fallback_used:
                    f.write(f"Market Fallback: Yes\n")
                f.write(f"Remaining Topic: {result.remaining_for_topic}\n")
                f.write(f"Notes: {', '.join(result.processing_notes)}\n")
                f.write(f"{'-'*40}\n\n")
        
        # 2. Failed extractions
        failed = [r for r in self.pipeline_results if not r.extracted_report_type]
        failed_file = f"{self.current_output_dir}/failed_extractions.txt"
        with open(failed_file, 'w', encoding='utf-8') as f:
            f.write(f"Enhanced Market-Aware Failed Extractions\n")
            f.write(f"Analysis Date (PDT): {pdt_str}\n")
            f.write(f"Analysis Date (UTC): {utc_str}\n")
            f.write(f"{'='*80}\n\n")
            f.write(f"Total Failed Extractions: {len(failed)}\n\n")
            
            for result in failed:
                f.write(f"Original: {result.original_title}\n")
                f.write(f"After Date Removal: {result.title_after_date_removal}\n")
                f.write(f"Date Extracted: {result.extracted_date_range}\n")
                f.write(f"Market Term: {result.market_term_type}\n")
                f.write(f"Remaining for Analysis: {result.title_after_date_removal}\n")
                if result.confusing_terms_found:
                    f.write(f"Confusing Terms: {', '.join(result.confusing_terms_found)}\n")
                f.write(f"Notes: {', '.join(result.processing_notes)}\n")
                f.write(f"{'-'*40}\n\n")
        
        # 3. Enhanced features cases
        enhanced_cases = [r for r in self.pipeline_results if r.confusing_terms_found or r.market_prefix_fallback_used]
        enhanced_file = f"{self.current_output_dir}/enhanced_features_cases.txt"
        with open(enhanced_file, 'w', encoding='utf-8') as f:
            f.write(f"Enhanced Market-Aware Features Cases\n")
            f.write(f"Analysis Date (PDT): {pdt_str}\n")
            f.write(f"Analysis Date (UTC): {utc_str}\n")
            f.write(f"{'='*80}\n\n")
            f.write(f"Total Enhanced Feature Cases: {len(enhanced_cases)}\n\n")
            
            for result in enhanced_cases:
                f.write(f"Original: {result.original_title}\n")
                f.write(f"Market Term: {result.market_term_type}\n")
                f.write(f"Report Type: {result.extracted_report_type}\n")
                if result.confusing_terms_found:
                    f.write(f"🔍 Confusing Terms Handled: {', '.join(result.confusing_terms_found)}\n")
                if result.market_prefix_fallback_used:
                    f.write(f"🔄 Market Prefix Fallback Used\n")
                f.write(f"Context: {result.context_analysis}\n")
                f.write(f"{'-'*40}\n\n")
        
        logger.info(f"✅ Manual review files generated")
    
    def _generate_pattern_analysis_report(self, timestamp: str, pdt_str: str, utc_str: str):
        """Generate pattern analysis report for failed cases."""
        
        failed = [r for r in self.pipeline_results if not r.extracted_report_type]
        
        pattern_file = f"{self.current_output_dir}/pattern_analysis.txt"
        with open(pattern_file, 'w', encoding='utf-8') as f:
            f.write(f"Enhanced Market-Aware Pattern Analysis Report\n")
            f.write(f"Analysis Date (PDT): {pdt_str}\n")
            f.write(f"Analysis Date (UTC): {utc_str}\n")
            f.write(f"{'='*80}\n\n")
            
            f.write(f"## Pattern Gap Analysis\n\n")
            f.write(f"Total Failed Extractions: {len(failed)}\n\n")
            
            f.write(f"## Failed Cases by Market Term Type\n\n")
            market_failures = defaultdict(int)
            for result in failed:
                market_failures[result.market_term_type] += 1
            
            for market_type, count in sorted(market_failures.items(), key=lambda x: x[1], reverse=True):
                f.write(f"- {market_type}: {count} failures\n")
            
            f.write(f"\n## Sample Failed Titles for Pattern Development\n\n")
            
            for result in failed[:50]:  # First 50 failures
                f.write(f"Title: {result.title_after_date_removal}\n")
                f.write(f"Market Type: {result.market_term_type}\n")
                f.write(f"Context: {result.context_analysis}\n")
                f.write(f"\n")
        
        logger.info(f"✅ Pattern analysis report generated: {pattern_file}")
    
    def cleanup(self):
        """Clean up resources."""
        try:
            self.pattern_manager.close_connection()
            logger.info("✅ Resources cleaned up")
        except Exception as e:
            logger.warning(f"Cleanup warning: {e}")

def main():
    """Main function for enhanced market-aware extractor testing."""
    
    print("Enhanced Market-Aware Extractor Comprehensive Test")
    print("="*80)
    
    # Initialize tester
    tester = EnhancedMarketAwareTester(sample_size=1000)
    
    try:
        # Run pipeline test
        success = tester.run_pipeline_test()
        
        if success:
            print("\n✅ Enhanced Market-Aware Extractor Test completed successfully!")
            print("\nGenerated files:")
            print("- Pipeline results JSON")
            print("- Executive summary report")
            print("- Manual review files (.txt format)")
            print("- Enhanced features analysis")
            print("- Pattern analysis for failed cases")
            print(f"\nCheck {tester.current_output_dir}/ directory for all generated files.")
            
        else:
            print("\n❌ Enhanced Market-Aware Extractor Test failed!")
            return False
            
    except Exception as e:
        logger.error(f"Enhanced pipeline test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        # Clean up
        tester.cleanup()
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)