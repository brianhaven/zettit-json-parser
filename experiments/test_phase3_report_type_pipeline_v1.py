#!/usr/bin/env python3

"""
Phase 3 Report Type Extractor Pipeline Test
Tests the complete 01→02→03 pipeline with comprehensive report type extraction.

Key Features:
- Tests pipeline sequence: Market Term Classification → Date Extraction → Report Type Extraction
- Handles special market cases (Aftermarket, Farmer's Market, etc.)
- Uses MongoDB patterns only (no hardcoded patterns)
- Generates .txt files for manual review like Phase 2
- Comprehensive analysis and pattern discovery

Created for Market Research Title Parser project.
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

# Import report type extractor
try:
    report_type_lib = import_module_from_path("report_type_extractor_v1", "03_report_type_extractor_v1.py")
    ReportTypeExtractor = report_type_lib.ReportTypeExtractor
    ReportTypeExtractionResult = report_type_lib.ReportTypeExtractionResult
    ReportTypeFormat = report_type_lib.ReportTypeFormat
except Exception as e:
    logger.error(f"Could not import ReportTypeExtractor: {e}")
    sys.exit(1)

@dataclass
class PipelineExtractionResult:
    """Complete pipeline extraction result for Phase 3 testing."""
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
    
    # Report type extraction (Phase 3)
    extracted_report_type: Optional[str]
    normalized_report_type: Optional[str]
    report_type_format: str
    report_type_confidence: float
    report_type_raw_match: Optional[str]
    
    # Special handling
    has_special_market_case: bool
    special_market_patterns: List[str]
    
    # Final topic (for validation)
    remaining_for_topic: str
    
    # Metadata
    processing_notes: List[str]
    total_confidence: float

@dataclass
class PipelineTestStats:
    """Statistics for Phase 3 pipeline testing."""
    total_processed: int
    market_term_classification_stats: Dict
    date_extraction_stats: Dict
    report_type_stats: Dict
    special_market_cases: int
    end_to_end_success_rate: float
    common_report_types: Dict[str, int]
    missing_report_types: List[str]

class SpecialMarketCaseHandler:
    """Handles special market cases where 'Market' should remain in topic."""
    
    def __init__(self):
        """Initialize special market case patterns."""
        # Note: These patterns identify cases where "Market" is part of the topic, not a report type
        self.special_patterns = [
            # Compound market types
            (r'\bAftermarket\b', 'Aftermarket', 'automotive/parts aftermarket'),
            (r"\bFarmer'?s?\s+Market\b", "Farmer's Market", 'farmers market'),
            (r'\bSupermarket\b', 'Supermarket', 'retail supermarket'),
            (r'\bHypermarket\b', 'Hypermarket', 'large retail store'),
            
            # Specific market types
            (r'\bStock\s+Market\b', 'Stock Market', 'financial market'),
            (r'\bBlack\s+Market\b', 'Black Market', 'underground economy'),
            (r'\bFlea\s+Market\b', 'Flea Market', 'marketplace type'),
            (r'\bGr[ea]y\s+Market\b', 'Grey Market', 'parallel imports'),
            
            # Market descriptors (potentially part of topic)
            (r'\bMass\s+Market\b', 'Mass Market', 'market segment'),
            (r'\bNiche\s+Market\b', 'Niche Market', 'specialized market'),
            (r'\bSecondary\s+Market\b', 'Secondary Market', 'resale market'),
            (r'\bPrimary\s+Market\b', 'Primary Market', 'initial market'),
            
            # Geographic + Market combinations (be careful)
            (r'\bEmerging\s+Market\b', 'Emerging Market', 'developing economy'),
            (r'\bDeveloped\s+Market\b', 'Developed Market', 'mature economy'),
        ]
        
        logger.info(f"Initialized {len(self.special_patterns)} special market case patterns")
    
    def check_special_cases(self, title: str) -> Tuple[bool, List[str]]:
        """
        Check if title contains special market cases.
        
        Returns:
            (has_special_cases, list_of_matched_patterns)
        """
        matched_patterns = []
        
        for pattern_regex, pattern_name, description in self.special_patterns:
            if re.search(pattern_regex, title, re.IGNORECASE):
                matched_patterns.append(f"{pattern_name} ({description})")
        
        return len(matched_patterns) > 0, matched_patterns

class Phase3PipelineTester:
    """Comprehensive Phase 3 pipeline tester for report type extraction."""
    
    def __init__(self, sample_size: int = 1000):
        """Initialize Phase 3 pipeline tester."""
        self.sample_size = sample_size
        self.special_handler = SpecialMarketCaseHandler()
        
        # Initialize pipeline components
        logger.info("Initializing Phase 3 pipeline components...")
        
        # Pattern library manager
        self.pattern_manager = PatternLibraryManager()
        
        # Pipeline components
        self.market_term_classifier = MarketTermClassifier(self.pattern_manager)
        self.date_extractor = EnhancedDateExtractor(self.pattern_manager)
        self.report_type_extractor = ReportTypeExtractor(self.pattern_manager)
        
        # Results storage
        self.pipeline_results: List[PipelineExtractionResult] = []
        
        logger.info("✅ Phase 3 pipeline components initialized successfully")
    
    def _get_timestamps(self) -> Tuple[str, str, datetime]:
        """Generate PDT and UTC timestamps."""
        utc_now = datetime.now(timezone.utc)
        pdt_tz = pytz.timezone('America/Los_Angeles')
        pdt_now = utc_now.astimezone(pdt_tz)
        
        pdt_str = pdt_now.strftime('%Y-%m-%d %H:%M:%S %Z')
        utc_str = utc_now.strftime('%Y-%m-%d %H:%M:%S UTC')
        
        return pdt_str, utc_str, utc_now
    
    def _get_sample_titles(self) -> List[str]:
        """Get sample titles from MongoDB for testing."""
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
            logger.error(f"Failed to retrieve sample titles: {e}")
            return []
    
    def _process_single_title(self, title: str) -> PipelineExtractionResult:
        """Process a single title through the complete Phase 3 pipeline."""
        processing_notes = []
        
        # Phase 1: Market Term Classification
        market_classification = self.market_term_classifier.classify(title)
        processing_notes.append(f"Market term: {market_classification.market_type.value}")
        
        # Phase 2: Date Extraction (Enhanced with bracket format preservation - GitHub Issue #8)
        date_result = self.date_extractor.extract(title)
        # Use the cleaned_title property which preserves important words from brackets
        title_after_date = date_result.cleaned_title
        processing_notes.append(f"Date extraction: {date_result.categorization}")
        if hasattr(date_result, 'preserved_words') and date_result.preserved_words:
            processing_notes.append(f"Preserved words: {', '.join(date_result.preserved_words)}")
        
        # Check for special market cases before report type extraction
        has_special_case, special_patterns = self.special_handler.check_special_cases(title_after_date)
        if has_special_case:
            processing_notes.append(f"Special market cases: {', '.join(special_patterns)}")
        
        # Phase 3: Report Type Extraction (process ALL titles, including market_for/market_in)
        # Note: Script 03 will need to be enhanced to handle market term awareness
        report_type_result = self.report_type_extractor.extract(
            title_after_date, 
            original_title=title,
            date_extractor=self.date_extractor
        )
        processing_notes.append(f"Report type: {report_type_result.format_type.value}")
        
        # Calculate remaining text for topic extraction
        remaining_text = title_after_date
        if report_type_result.raw_match and not has_special_case:
            # Only remove report type if no special market cases
            remaining_text = remaining_text.replace(report_type_result.raw_match, '').strip()
            remaining_text = re.sub(r'\s+', ' ', remaining_text)
            remaining_text = re.sub(r'[,\.]+$', '', remaining_text)
        
        # Calculate combined confidence
        total_confidence = (
            market_classification.confidence * 0.2 +  # 20% weight
            date_result.confidence * 0.3 +             # 30% weight  
            report_type_result.confidence * 0.5        # 50% weight
        )
        
        return PipelineExtractionResult(
            title=title,
            original_title=title,
            
            # Market term classification
            market_term_type=market_classification.market_type.value,
            market_term_confidence=market_classification.confidence,
            
            # Date extraction
            extracted_date_range=date_result.extracted_date_range,
            date_confidence=date_result.confidence,
            date_categorization=date_result.categorization,
            title_after_date_removal=title_after_date,
            
            # Report type extraction
            extracted_report_type=report_type_result.extracted_report_type,
            normalized_report_type=report_type_result.normalized_report_type,
            report_type_format=report_type_result.format_type.value,
            report_type_confidence=report_type_result.confidence,
            report_type_raw_match=report_type_result.raw_match,
            
            # Special handling
            has_special_market_case=has_special_case,
            special_market_patterns=special_patterns,
            
            # Final topic
            remaining_for_topic=remaining_text,
            
            # Metadata
            processing_notes=processing_notes,
            total_confidence=total_confidence
        )
    
    def run_pipeline_test(self) -> bool:
        """Run the complete Phase 3 pipeline test."""
        try:
            logger.info("Starting Phase 3 Pipeline Test...")
            logger.info("="*60)
            
            # Get sample titles
            sample_titles = self._get_sample_titles()
            if not sample_titles:
                logger.error("No sample titles retrieved for testing")
                return False
            
            # Process each title through the pipeline
            logger.info(f"Processing {len(sample_titles)} titles through Phase 3 pipeline...")
            
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
            self._generate_analysis_reports()
            
            return True
            
        except Exception as e:
            logger.error(f"Phase 3 pipeline test failed: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def _generate_analysis_reports(self):
        """Generate comprehensive analysis reports for Phase 3 testing."""
        pdt_str, utc_str, utc_now = self._get_timestamps()
        timestamp = utc_now.strftime('%Y%m%d_%H%M%S')
        
        # Create timestamped subdirectory following established pattern
        outputs_base = "../outputs"
        output_dir = f"{outputs_base}/{timestamp}_phase3_pipeline_01_02_03"
        os.makedirs(output_dir, exist_ok=True)
        
        # Store the output directory for use in other methods
        self.current_output_dir = output_dir
        
        # 1. Generate JSON results file
        json_file = f"{output_dir}/pipeline_results.json"
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump([asdict(result) for result in self.pipeline_results], f, indent=2, ensure_ascii=False)
        
        # 2. Generate summary report
        self._generate_summary_report(timestamp, pdt_str, utc_str)
        
        # 3. Generate manual review files (.txt format like Phase 2)
        self._generate_manual_review_files(timestamp, pdt_str, utc_str)
        
        # 4. Generate pattern analysis report
        self._generate_pattern_analysis_report(timestamp, pdt_str, utc_str)
        
        logger.info(f"✅ Analysis reports generated in: {output_dir}")
    
    def _generate_summary_report(self, timestamp: str, pdt_str: str, utc_str: str):
        """Generate executive summary report."""
        summary_file = f"{self.current_output_dir}/summary_report.md"
        
        # Calculate statistics
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
        
        # Special cases stats
        special_cases = sum(1 for r in self.pipeline_results if r.has_special_market_case)
        
        # Generate report
        with open(summary_file, 'w', encoding='utf-8') as f:
            f.write(f"""# Phase 3 Pipeline Test Summary Report

**Analysis Date (PDT):** {pdt_str}  
**Analysis Date (UTC):** {utc_str}

## Executive Summary

- **Total Titles Processed:** {total:,}
- **Market Term Classification Rate:** {(sum(market_term_counts.values())/total)*100:.1f}%
- **Date Extraction Success:** {(date_success/total)*100:.1f}% ({date_success:,}/{total:,})
- **Titles with No Dates:** {(date_no_dates/total)*100:.1f}% ({date_no_dates:,}/{total:,})
- **Report Type Extraction Success:** {(report_type_success/total)*100:.1f}% ({report_type_success:,}/{total:,})
- **Special Market Cases Found:** {(special_cases/total)*100:.1f}% ({special_cases:,}/{total:,})

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

## Phase 3: Report Type Extraction Results

- **Successful Extractions:** {report_type_success:,} ({(report_type_success/total)*100:.1f}%)
- **Failed Extractions:** {total - report_type_success:,} ({((total - report_type_success)/total)*100:.1f}%)

### Most Common Report Types

""")
            for report_type, count in sorted(report_type_counts.items(), key=lambda x: x[1], reverse=True)[:10]:
                percentage = (count/total)*100
                f.write(f"- **{report_type}:** {count:,} titles ({percentage:.1f}%)\n")
            
            f.write(f"""

## Special Market Cases

- **Total Special Cases:** {special_cases:,} ({(special_cases/total)*100:.1f}%)

These are cases where 'Market' remains part of the topic rather than being extracted as a report type.

## Recommendations for Next Iteration

1. **Report Type Pattern Enhancement:** Review failed extractions to identify missing patterns
2. **Special Case Validation:** Verify special market case handling is working correctly
3. **Confidence Scoring:** Analyze low-confidence extractions for pattern improvements
4. **Edge Case Handling:** Review complex titles with multiple patterns

""")
        
        logger.info(f"✅ Summary report generated: {summary_file}")
    
    def _generate_manual_review_files(self, timestamp: str, pdt_str: str, utc_str: str):
        """Generate .txt files for manual review like Phase 2."""
        
        # 1. Successful report type extractions
        success_file = f"{self.current_output_dir}/successful_extractions.txt"
        with open(success_file, 'w', encoding='utf-8') as f:
            f.write(f"Phase 3 Successful Report Type Extractions\n")
            f.write(f"Analysis Date (PDT): {pdt_str}\n")
            f.write(f"Analysis Date (UTC): {utc_str}\n")
            f.write(f"{'='*80}\n\n")
            
            successful = [r for r in self.pipeline_results if r.extracted_report_type]
            f.write(f"Total Successful Extractions: {len(successful):,}\n\n")
            
            for result in successful[:200]:  # First 200 for review
                f.write(f"Original: {result.original_title}\n")
                f.write(f"After Date Removal: {result.title_after_date_removal}\n")
                f.write(f"Report Type: {result.extracted_report_type}\n")
                f.write(f"Normalized: {result.normalized_report_type}\n")
                f.write(f"Format: {result.report_type_format}\n")
                f.write(f"Confidence: {result.report_type_confidence:.3f}\n")
                f.write(f"Raw Match: {result.report_type_raw_match}\n")
                f.write(f"Remaining Topic: {result.remaining_for_topic}\n")
                if result.has_special_market_case:
                    f.write(f"Special Cases: {', '.join(result.special_market_patterns)}\n")
                f.write(f"Notes: {', '.join(result.processing_notes)}\n")
                f.write(f"{'-'*40}\n\n")
        
        # 2. Failed extractions for pattern analysis
        failed_file = f"{self.current_output_dir}/failed_extractions.txt"
        with open(failed_file, 'w', encoding='utf-8') as f:
            f.write(f"Phase 3 Failed Report Type Extractions\n")
            f.write(f"Analysis Date (PDT): {pdt_str}\n")
            f.write(f"Analysis Date (UTC): {utc_str}\n")
            f.write(f"{'='*80}\n\n")
            
            failed = [r for r in self.pipeline_results if not r.extracted_report_type]
            f.write(f"Total Failed Extractions: {len(failed):,}\n\n")
            
            for result in failed[:200]:  # First 200 for review
                f.write(f"Original: {result.original_title}\n")
                f.write(f"After Date Removal: {result.title_after_date_removal}\n")
                f.write(f"Date Extracted: {result.extracted_date_range or 'None'}\n")
                f.write(f"Market Term: {result.market_term_type}\n")
                f.write(f"Remaining for Analysis: {result.remaining_for_topic}\n")
                if result.has_special_market_case:
                    f.write(f"Special Cases: {', '.join(result.special_market_patterns)}\n")
                f.write(f"Notes: {', '.join(result.processing_notes)}\n")
                f.write(f"{'-'*40}\n\n")
        
        # 3. Special market cases
        special_file = f"{self.current_output_dir}/special_market_cases.txt"
        with open(special_file, 'w', encoding='utf-8') as f:
            f.write(f"Phase 3 Special Market Cases\n")
            f.write(f"Analysis Date (PDT): {pdt_str}\n")
            f.write(f"Analysis Date (UTC): {utc_str}\n")
            f.write(f"{'='*80}\n\n")
            
            special_cases = [r for r in self.pipeline_results if r.has_special_market_case]
            f.write(f"Total Special Market Cases: {len(special_cases):,}\n\n")
            
            for result in special_cases:
                f.write(f"Original: {result.original_title}\n")
                f.write(f"Special Patterns: {', '.join(result.special_market_patterns)}\n")
                f.write(f"Report Type Extracted: {result.extracted_report_type or 'None'}\n")
                f.write(f"Topic Preserved: {result.remaining_for_topic}\n")
                f.write(f"{'-'*40}\n\n")
        
        logger.info(f"✅ Manual review files generated")
    
    def _generate_pattern_analysis_report(self, timestamp: str, pdt_str: str, utc_str: str):
        """Generate pattern analysis for missing report types."""
        pattern_file = f"{self.current_output_dir}/pattern_analysis.txt"
        
        # Analyze failed extractions to identify potential new patterns
        failed_results = [r for r in self.pipeline_results if not r.extracted_report_type]
        
        # Look for common words in failed extractions that might be report types
        word_counts = defaultdict(int)
        potential_patterns = []
        
        for result in failed_results:
            # Analyze remaining text for potential report type words
            remaining_lower = result.title_after_date_removal.lower()
            words = re.findall(r'\b(?:report|analysis|study|research|outlook|forecast|assessment|overview|insights|intelligence|survey|review|brief|summary|data|statistics|trends|market|industry)\b', remaining_lower)
            for word in words:
                word_counts[word] += 1
        
        with open(pattern_file, 'w', encoding='utf-8') as f:
            f.write(f"Phase 3 Pattern Analysis Report\n")
            f.write(f"Analysis Date (PDT): {pdt_str}\n")
            f.write(f"Analysis Date (UTC): {utc_str}\n")
            f.write(f"{'='*80}\n\n")
            
            f.write(f"Failed Extractions Analysis\n")
            f.write(f"Total Failed Extractions: {len(failed_results):,}\n\n")
            
            f.write(f"Potential Report Type Words Found in Failed Extractions:\n")
            for word, count in sorted(word_counts.items(), key=lambda x: x[1], reverse=True):
                percentage = (count/len(failed_results))*100
                f.write(f"- {word}: {count:,} occurrences ({percentage:.1f}%)\n")
            
            f.write(f"\nSample Failed Extractions for Pattern Development:\n")
            f.write(f"{'-'*60}\n")
            
            for result in failed_results[:50]:  # First 50 for manual review
                f.write(f"Title: {result.title_after_date_removal}\n")
                f.write(f"Market Type: {result.market_term_type}\n")
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
    """Main function for Phase 3 pipeline testing."""
    
    print("Phase 3 Report Type Extractor Pipeline Test")
    print("="*60)
    
    # Initialize tester
    tester = Phase3PipelineTester(sample_size=1000)
    
    try:
        # Run pipeline test
        success = tester.run_pipeline_test()
        
        if success:
            print("\n✅ Phase 3 Pipeline Test completed successfully!")
            print("\nGenerated files:")
            print("- Pipeline results JSON")
            print("- Executive summary report")
            print("- Manual review files (.txt format)")
            print("- Pattern analysis for missing report types")
            print(f"\nCheck {tester.current_output_dir}/ directory for all generated files.")
            
        else:
            print("\n❌ Phase 3 Pipeline Test failed!")
            return False
            
    except Exception as e:
        logger.error(f"Phase 3 pipeline test failed: {e}")
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