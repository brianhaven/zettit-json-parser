#!/usr/bin/env python3

"""
Test Market-Aware Report Type Extractor v2.0
Tests the enhanced 03_report_type_extractor_v2.py with market term awareness.

Key Features:
- Tests complete pipeline: 01→02→03v2 with market-aware report type extraction
- Uses single shared PatternLibraryManager for all components (NO multiple DB connections)
- Follows proven database connection pattern from working test harnesses
- Generates comprehensive outputs matching Phase 3 structure
- Validates confusing term handling and Market prefix fallback

Created for Market Research Title Parser project.
"""

import os
import sys
import json
import logging
import importlib.util
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from collections import defaultdict
import pytz

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# MongoDB imports
from pymongo import MongoClient
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Dynamic imports following working test pattern
def import_module_from_path(module_name: str, file_path: str):
    """Import a module from a file path."""
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

# Import pattern library manager (SHARED across all components)
try:
    parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    pattern_lib = import_module_from_path("pattern_library_manager_v1", os.path.join(parent_dir, "00b_pattern_library_manager_v1.py"))
    PatternLibraryManager = pattern_lib.PatternLibraryManager
except Exception as e:
    logger.error(f"Could not import PatternLibraryManager: {e}")
    sys.exit(1)

# Import market term classifier  
try:
    market_term_lib = import_module_from_path("market_term_classifier_v1", os.path.join(parent_dir, "01_market_term_classifier_v1.py"))
    MarketTermClassifier = market_term_lib.MarketTermClassifier
except Exception as e:
    logger.error(f"Could not import MarketTermClassifier: {e}")
    sys.exit(1)

# Import date extractor
try:
    date_extractor_lib = import_module_from_path("date_extractor_v1", os.path.join(parent_dir, "02_date_extractor_v1.py"))
    EnhancedDateExtractor = date_extractor_lib.EnhancedDateExtractor
except Exception as e:
    logger.error(f"Could not import EnhancedDateExtractor: {e}")
    sys.exit(1)

# Import market-aware report type extractor v2
try:
    report_type_lib = import_module_from_path("report_type_extractor_v2", os.path.join(parent_dir, "03_report_type_extractor_v2.py"))
    MarketAwareReportTypeExtractor = report_type_lib.MarketAwareReportTypeExtractor
except Exception as e:
    logger.error(f"Could not import MarketAwareReportTypeExtractor: {e}")
    sys.exit(1)

@dataclass
class MarketAwarePipelineResult:
    """Complete pipeline result for market-aware testing."""
    title: str
    original_title: str
    
    # Market term classification (Phase 1)
    market_term_type: str
    market_term_confidence: float
    
    # Date extraction (Phase 2)
    extracted_date_range: Optional[str]
    date_confidence: float
    cleaned_title: str
    
    # Market-aware report type extraction (Phase 3v2)
    final_report_type: Optional[str]
    report_type_confidence: float
    market_prepended: bool
    context_analysis: str
    confusing_terms_found: List[str]
    fallback_used: bool
    
    # Processing metadata
    success: bool
    error: Optional[str] = None

class MarketAwarePipelineTestHarness:
    """Test harness for Market-Aware Report Type Extractor v2 following proven patterns."""
    
    def __init__(self, sample_size: int = 20):
        """
        Initialize test harness with SINGLE shared PatternLibraryManager.
        
        Args:
            sample_size: Number of documents to test (default 20 for validation)
        """
        self.sample_size = sample_size
        
        logger.info("Initializing Market-Aware Pipeline components...")
        
        # CRITICAL: Single PatternLibraryManager shared across ALL components
        # This prevents multiple database connections per title
        self.pattern_library_manager = PatternLibraryManager()
        
        # All pipeline components share the SAME pattern manager instance
        self.market_classifier = MarketTermClassifier(self.pattern_library_manager)
        self.date_extractor = EnhancedDateExtractor(self.pattern_library_manager) 
        self.market_aware_extractor = MarketAwareReportTypeExtractor(self.pattern_library_manager)
        
        # Results storage
        self.test_results: List[MarketAwarePipelineResult] = []
        
        # Load environment variables
        load_dotenv()
        
        logger.info("✅ Market-Aware Pipeline components initialized successfully")
    
    def _get_timestamps(self) -> tuple:
        """Generate PDT and UTC timestamps."""
        utc_now = datetime.now(timezone.utc)
        pdt_tz = pytz.timezone('America/Los_Angeles')
        pdt_now = utc_now.astimezone(pdt_tz)
        
        pdt_str = pdt_now.strftime('%Y-%m-%d %H:%M:%S %Z')
        utc_str = utc_now.strftime('%Y-%m-%d %H:%M:%S UTC')
        
        return pdt_str, utc_str, utc_now
    
    def _get_sample_titles(self) -> List[str]:
        """
        Get sample titles from MongoDB following proven pattern.
        Uses separate connection for data retrieval only (not patterns).
        """
        try:
            # Separate connection for data retrieval following working pattern
            client = MongoClient(os.getenv('MONGODB_URI'))
            db = client['deathstar']
            collection = db['markets_raw']
            
            # Get sample titles using aggregation pipeline
            sample_titles = []
            cursor = collection.aggregate([
                {'$sample': {'size': self.sample_size}},
                {'$project': {'report_title_short': 1, '_id': 0}}
            ])
            
            for doc in cursor:
                if 'report_title_short' in doc and doc['report_title_short']:
                    sample_titles.append(doc['report_title_short'].strip())
            
            # Immediate cleanup
            client.close()
            logger.info(f"Retrieved {len(sample_titles)} sample titles from MongoDB")
            return sample_titles
            
        except Exception as e:
            logger.error(f"Failed to retrieve sample titles: {e}")
            return []
    
    def _process_single_title(self, title: str) -> MarketAwarePipelineResult:
        """Process single title through market-aware pipeline."""
        
        # Step 1: Market term classification  
        try:
            market_result = self.market_classifier.classify(title)
            market_term_type = market_result.market_type.value if hasattr(market_result.market_type, 'value') else str(market_result.market_type)
            market_confidence = market_result.confidence
        except Exception as e:
            logger.warning(f"Market classification failed for '{title}': {e}")
            market_term_type = 'standard'
            market_confidence = 0.0
        
        # Step 2: Date extraction
        try:
            date_result = self.date_extractor.extract(title)
            date_extracted = date_result.extracted_date_range
            cleaned_title = date_result.cleaned_title
            date_confidence = date_result.confidence
        except Exception as e:
            logger.warning(f"Date extraction failed for '{title}': {e}")
            date_extracted = None
            cleaned_title = title
            date_confidence = 0.0
        
        # Step 3: Market-aware report type extraction
        try:
            report_result = self.market_aware_extractor.extract(
                title=cleaned_title,
                market_term_type=market_term_type,
                original_title=title,
                date_extractor=self.date_extractor
            )
            
            final_report_type = report_result.final_report_type
            report_confidence = report_result.confidence
            market_prepended = getattr(report_result, 'market_prepended', False)
            context_analysis = getattr(report_result, 'context_analysis', 'No context analysis')
            confusing_terms = getattr(report_result, 'confusing_terms_found', [])
            fallback_used = getattr(report_result, 'fallback_used', False)
            success = final_report_type is not None
            error = None
            
        except Exception as e:
            logger.warning(f"Market-aware report type extraction failed for '{title}': {e}")
            final_report_type = None
            report_confidence = 0.0
            market_prepended = False
            context_analysis = f"Error: {e}"
            confusing_terms = []
            fallback_used = False
            success = False
            error = str(e)
        
        return MarketAwarePipelineResult(
            title=title,
            original_title=title,
            market_term_type=market_term_type,
            market_term_confidence=market_confidence,
            extracted_date_range=date_extracted,
            date_confidence=date_confidence,
            cleaned_title=cleaned_title,
            final_report_type=final_report_type,
            report_type_confidence=report_confidence,
            market_prepended=market_prepended,
            context_analysis=context_analysis,
            confusing_terms_found=confusing_terms,
            fallback_used=fallback_used,
            success=success,
            error=error
        )
    
    def run_test(self) -> bool:
        """Run the market-aware pipeline test."""
        try:
            logger.info("Starting Market-Aware Pipeline Test v2...")
            logger.info("=" * 60)
            
            # Get sample titles
            sample_titles = self._get_sample_titles()
            if not sample_titles:
                logger.error("No sample titles retrieved for testing")
                return False
            
            # Process each title
            logger.info(f"Processing {len(sample_titles)} titles through market-aware pipeline...")
            
            for i, title in enumerate(sample_titles):
                logger.info(f"Processing {i+1}/{len(sample_titles)}: {title[:60]}...")
                
                try:
                    result = self._process_single_title(title)
                    self.test_results.append(result)
                except Exception as e:
                    logger.warning(f"Failed to process title '{title}': {e}")
                    continue
            
            logger.info(f"✅ Successfully processed {len(self.test_results)} titles")
            
            # Generate analysis
            self._generate_analysis()
            return True
            
        except Exception as e:
            logger.error(f"Test failed: {e}")
            return False
    
    def _generate_analysis(self):
        """Generate comprehensive analysis and save results."""
        
        # Create timestamped output directory using absolute path
        pdt_str, utc_str, utc_now = self._get_timestamps()
        timestamp = utc_now.astimezone(pytz.timezone('America/Los_Angeles')).strftime('%Y%m%d_%H%M%S')
        # Get absolute path to outputs directory
        script_dir = os.path.dirname(os.path.abspath(__file__))
        experiments_dir = os.path.dirname(script_dir)
        outputs_dir = os.path.join(os.path.dirname(experiments_dir), 'outputs')
        output_dir = os.path.join(outputs_dir, f"{timestamp}_market_aware_pipeline_v2_test")
        os.makedirs(output_dir, exist_ok=True)
        
        # Calculate statistics
        total = len(self.test_results)
        successful = sum(1 for r in self.test_results if r.success)
        success_rate = (successful / total) * 100 if total > 0 else 0
        
        # Market term distribution
        market_terms = defaultdict(int)
        for result in self.test_results:
            market_terms[result.market_term_type] += 1
        
        # Report type distribution  
        report_types = defaultdict(int)
        for result in self.test_results:
            if result.final_report_type:
                report_types[result.final_report_type] += 1
        
        # Enhanced feature statistics
        market_prepended_count = sum(1 for r in self.test_results if r.market_prepended)
        confusing_terms_handled = sum(1 for r in self.test_results if r.confusing_terms_found)
        fallback_used_count = sum(1 for r in self.test_results if r.fallback_used)
        
        # Console output
        print("\n" + "=" * 80)
        print("MARKET-AWARE REPORT TYPE EXTRACTOR V2 TEST RESULTS")
        print("=" * 80)
        print(f"Analysis Date (PDT): {pdt_str}")
        print(f"Analysis Date (UTC): {utc_str}")
        print()
        print(f"Overall Performance:")
        print(f"  Total Titles Processed: {total}")
        print(f"  Successful Extractions: {successful}")
        print(f"  Success Rate: {success_rate:.1f}%")
        print()
        print(f"Enhanced Market-Aware Features:")
        print(f"  Market Prefix Added: {market_prepended_count}")
        print(f"  Confusing Terms Handled: {confusing_terms_handled}")
        print(f"  Fallback Strategy Used: {fallback_used_count}")
        print()
        print(f"Market Term Distribution:")
        for term, count in sorted(market_terms.items(), key=lambda x: x[1], reverse=True):
            print(f"  {term}: {count} ({count/total*100:.1f}%)")
        print()
        print(f"Report Type Distribution:")
        for rtype, count in sorted(report_types.items(), key=lambda x: x[1], reverse=True)[:10]:
            print(f"  '{rtype}': {count} ({count/successful*100:.1f}%)")
        
        # Save detailed results JSON
        results_file = f"{output_dir}/detailed_results.json"
        with open(results_file, 'w') as f:
            json.dump({
                'metadata': {
                    'pdt_timestamp': pdt_str,
                    'utc_timestamp': utc_str,
                    'total_processed': total,
                    'successful': successful,
                    'success_rate': success_rate,
                    'market_prepended': market_prepended_count,
                    'confusing_terms_handled': confusing_terms_handled,
                    'fallback_used': fallback_used_count
                },
                'results': [
                    {
                        'title': r.title,
                        'market_term_type': r.market_term_type,
                        'market_confidence': r.market_term_confidence,
                        'date_extracted': r.extracted_date_range,
                        'cleaned_title': r.cleaned_title,
                        'final_report_type': r.final_report_type,
                        'report_confidence': r.report_type_confidence,
                        'market_prepended': r.market_prepended,
                        'context_analysis': r.context_analysis,
                        'confusing_terms': r.confusing_terms_found,
                        'fallback_used': r.fallback_used,
                        'success': r.success,
                        'error': r.error
                    } for r in self.test_results
                ]
            }, f, indent=2)
        
        # Save summary report
        summary_file = f"{output_dir}/summary_report.md"
        with open(summary_file, 'w') as f:
            f.write(f"# Market-Aware Report Type Extractor v2 Test Summary\n\n")
            f.write(f"**Analysis Date (PDT):** {pdt_str}  \n")
            f.write(f"**Analysis Date (UTC):** {utc_str}\n\n")
            f.write(f"## Executive Summary\n\n")
            f.write(f"- **Total Titles Processed:** {total}\n")
            f.write(f"- **Successful Extractions:** {successful} ({success_rate:.1f}%)\n")
            f.write(f"- **Market Prefix Added:** {market_prepended_count}\n")
            f.write(f"- **Confusing Terms Handled:** {confusing_terms_handled}\n")
            f.write(f"- **Fallback Strategy Used:** {fallback_used_count}\n\n")
            
            f.write(f"## Market Term Distribution\n\n")
            for term, count in sorted(market_terms.items(), key=lambda x: x[1], reverse=True):
                f.write(f"- **{term}:** {count} titles ({count/total*100:.1f}%)\n")
            
            f.write(f"\n## Report Type Distribution\n\n")
            for rtype, count in sorted(report_types.items(), key=lambda x: x[1], reverse=True)[:10]:
                f.write(f"- **{rtype}:** {count} titles ({count/successful*100:.1f}%)\n")
        
        # Save detailed report for manual review
        details_file = f"{output_dir}/detailed_analysis.txt"
        with open(details_file, 'w') as f:
            f.write(f"Market-Aware Report Type Extractor v2 - Detailed Analysis\n")
            f.write(f"Analysis Date (PDT): {pdt_str}\n") 
            f.write(f"Analysis Date (UTC): {utc_str}\n")
            f.write(f"{'='*80}\n\n")
            
            for i, result in enumerate(self.test_results, 1):
                f.write(f"Test #{i}: {result.title}\n")
                f.write(f"  Market Type: {result.market_term_type} (conf: {result.market_term_confidence:.3f})\n")
                f.write(f"  Date: {result.extracted_date_range}\n")
                f.write(f"  Cleaned: {result.cleaned_title}\n")
                f.write(f"  Report Type: '{result.final_report_type}' (conf: {result.report_type_confidence:.3f})\n")
                f.write(f"  Context: {result.context_analysis}\n")
                if result.market_prepended:
                    f.write(f"  🎯 Market Prefix Added\n")
                if result.confusing_terms_found:
                    f.write(f"  ⚠️  Confusing Terms: {result.confusing_terms_found}\n")
                if result.fallback_used:
                    f.write(f"  🔄 Fallback Strategy Used\n")
                f.write(f"  Success: {'✅' if result.success else '❌'}\n")
                if result.error:
                    f.write(f"  Error: {result.error}\n")
                f.write(f"\n")
        
        print(f"\n📁 Results saved to: {output_dir}")
        print(f"  - Summary: {summary_file}")
        print(f"  - Detailed JSON: {results_file}")
        print(f"  - Manual Review: {details_file}")
    
    def cleanup(self):
        """Clean up resources."""
        try:
            if hasattr(self, 'pattern_library_manager'):
                self.pattern_library_manager.close_connection()
                logger.info("✅ Pattern library manager cleaned up")
        except Exception as e:
            logger.warning(f"Cleanup warning: {e}")

def main():
    """Main function."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Market-Aware Pipeline Test v2')
    parser.add_argument('--limit', type=int, default=20, help='Number of titles to test (default: 20)')
    args = parser.parse_args()
    
    print("Market-Aware Report Type Extractor v2 Test")
    print("=" * 60)
    
    # Use command line argument for sample size
    tester = MarketAwarePipelineTestHarness(sample_size=args.limit)
    
    try:
        success = tester.run_test()
        
        if success:
            print("\n✅ Market-aware pipeline test completed successfully!")
        else:
            print("\n❌ Market-aware pipeline test failed!")
            return False
            
    except Exception as e:
        logger.error(f"Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        tester.cleanup()
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)