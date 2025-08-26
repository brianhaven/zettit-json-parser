#!/usr/bin/env python3
"""
Test Enhanced Market-Aware Extractor with Small Sample
Following the working Phase3 pipeline test pattern
"""

import os
import sys
import json
import logging
import importlib.util
from datetime import datetime, timezone
from typing import Dict, List, Optional
from dataclasses import dataclass
import pytz
from pymongo import MongoClient
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Dynamic imports following the working pattern
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
except Exception as e:
    logger.error(f"Could not import PatternLibraryManager: {e}")
    sys.exit(1)

# Import market term classifier  
try:
    market_term_lib = import_module_from_path("market_term_classifier_v1", "01_market_term_classifier_v1.py")
    MarketTermClassifier = market_term_lib.MarketTermClassifier
except Exception as e:
    logger.error(f"Could not import MarketTermClassifier: {e}")
    sys.exit(1)

# Import date extractor
try:
    date_extractor_lib = import_module_from_path("date_extractor_v1", "02_date_extractor_v1.py")
    EnhancedDateExtractor = date_extractor_lib.EnhancedDateExtractor
except Exception as e:
    logger.error(f"Could not import EnhancedDateExtractor: {e}")
    sys.exit(1)

# Import market-aware report type extractor
try:
    report_type_lib = import_module_from_path("report_type_extractor_market_aware_v1", "03_report_type_extractor_market_aware_v1.py")
    MarketAwareReportTypeExtractor = report_type_lib.MarketAwareReportTypeExtractor
except Exception as e:
    logger.error(f"Could not import MarketAwareReportTypeExtractor: {e}")
    sys.exit(1)

@dataclass
class TestResult:
    """Single test result."""
    title: str
    market_term: str
    market_confidence: float
    date_extracted: Optional[str]
    cleaned_title: str
    report_type: Optional[str] 
    report_confidence: float
    context_analysis: str
    confusing_terms: List[str]
    fallback_used: bool
    success: bool
    error: Optional[str] = None

class EnhancedExtractorTester:
    """Test enhanced market-aware extractor following working pipeline pattern."""
    
    def __init__(self, sample_size: int = 20):
        """Initialize tester."""
        self.sample_size = sample_size
        
        logger.info("Initializing enhanced extractor components...")
        
        # Single pattern library manager shared across all components
        self.pattern_manager = PatternLibraryManager()
        
        # Pipeline components - all share the same pattern manager
        self.market_classifier = MarketTermClassifier(self.pattern_manager)
        self.date_extractor = EnhancedDateExtractor(self.pattern_manager)
        self.market_aware_extractor = MarketAwareReportTypeExtractor(self.pattern_manager)
        
        # Results storage
        self.test_results: List[TestResult] = []
        
        logger.info("✅ Enhanced extractor components initialized successfully")
    
    def _get_sample_titles(self) -> List[str]:
        """Get sample titles from MongoDB for testing."""
        try:
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
    
    def _process_single_title(self, title: str) -> TestResult:
        """Process a single title through the enhanced pipeline."""
        
        # Step 1: Market term classification  
        try:
            market_result = self.market_classifier.classify(title)
            market_term = market_result.market_type
            market_confidence = market_result.confidence
        except Exception as e:
            logger.warning(f"Market classification failed for '{title}': {e}")
            market_term = 'standard'
            market_confidence = 0.0
        
        # Step 2: Date extraction
        try:
            date_result = self.date_extractor.extract(title)
            date_extracted = date_result.extracted_date_range
            cleaned_title = date_result.cleaned_title
        except Exception as e:
            logger.warning(f"Date extraction failed for '{title}': {e}")
            date_extracted = None
            cleaned_title = title
        
        # Step 3: Market-aware report type extraction
        try:
            report_result = self.market_aware_extractor.extract(
                title=cleaned_title,
                market_term_type=market_term,
                original_title=title,
                date_extractor=self.date_extractor
            )
            
            report_type = report_result.final_report_type
            report_confidence = report_result.confidence
            context_analysis = report_result.context_analysis
            confusing_terms = getattr(report_result, 'confusing_terms_found', [])
            fallback_used = getattr(report_result, 'market_prepended', False)
            success = report_type is not None
            error = None
            
        except Exception as e:
            logger.warning(f"Report type extraction failed for '{title}': {e}")
            report_type = None
            report_confidence = 0.0
            context_analysis = f"Error: {e}"
            confusing_terms = []
            fallback_used = False
            success = False
            error = str(e)
        
        return TestResult(
            title=title,
            market_term=market_term,
            market_confidence=market_confidence,
            date_extracted=date_extracted,
            cleaned_title=cleaned_title,
            report_type=report_type,
            report_confidence=report_confidence,
            context_analysis=context_analysis,
            confusing_terms=confusing_terms,
            fallback_used=fallback_used,
            success=success,
            error=error
        )
    
    def run_test(self) -> bool:
        """Run the enhanced extractor test."""
        try:
            logger.info("Starting Enhanced Market-Aware Extractor Test...")
            logger.info("="*60)
            
            # Get sample titles
            sample_titles = self._get_sample_titles()
            if not sample_titles:
                logger.error("No sample titles retrieved for testing")
                return False
            
            # Process each title
            logger.info(f"Processing {len(sample_titles)} titles through enhanced pipeline...")
            
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
        """Generate analysis and save results."""
        
        # Create timestamped output directory
        utc_now = datetime.now(timezone.utc)
        pdt_tz = pytz.timezone('America/Los_Angeles')
        pdt_now = utc_now.astimezone(pdt_tz)
        
        timestamp = pdt_now.strftime('%Y%m%d_%H%M%S')
        output_dir = f"../outputs/{timestamp}_enhanced_extractor_small_test"
        os.makedirs(output_dir, exist_ok=True)
        
        pdt_str = pdt_now.strftime('%Y-%m-%d %H:%M:%S PDT')
        utc_str = utc_now.strftime('%Y-%m-%d %H:%M:%S UTC')
        
        # Calculate stats
        total = len(self.test_results)
        successful = sum(1 for r in self.test_results if r.success)
        success_rate = (successful / total) * 100 if total > 0 else 0
        
        # Confidence analysis
        confidences = [r.report_confidence for r in self.test_results if r.success]
        avg_confidence = sum(confidences) / len(confidences) if confidences else 0
        
        # Market term distribution
        market_terms = {}
        for result in self.test_results:
            market_terms[result.market_term] = market_terms.get(result.market_term, 0) + 1
        
        # Report type distribution  
        report_types = {}
        for result in self.test_results:
            if result.report_type:
                report_types[result.report_type] = report_types.get(result.report_type, 0) + 1
        
        # Confusing terms found
        confusing_found = sum(1 for r in self.test_results if r.confusing_terms)
        fallback_used = sum(1 for r in self.test_results if r.fallback_used)
        
        # Console output
        print("\n" + "="*80)
        print("ENHANCED MARKET-AWARE EXTRACTOR TEST RESULTS")
        print("="*80)
        print(f"Analysis Date (PDT): {pdt_str}")
        print(f"Analysis Date (UTC): {utc_str}")
        print()
        print(f"Overall Performance:")
        print(f"  Total Titles Tested: {total}")
        print(f"  Successful Extractions: {successful}")
        print(f"  Success Rate: {success_rate:.1f}%")
        print(f"  Average Confidence: {avg_confidence:.3f}")
        print()
        print(f"Enhanced Features:")
        print(f"  Confusing Terms Handled: {confusing_found}")
        print(f"  Market Prefix Fallback Used: {fallback_used}")
        print()
        print(f"Market Term Distribution:")
        for term, count in sorted(market_terms.items(), key=lambda x: x[1], reverse=True):
            print(f"  {term}: {count} ({count/total*100:.1f}%)")
        print()
        print(f"Report Type Distribution:")
        for rtype, count in sorted(report_types.items(), key=lambda x: x[1], reverse=True)[:10]:
            print(f"  '{rtype}': {count} ({count/successful*100:.1f}%)")
        
        # Save detailed results
        results_file = f"{output_dir}/detailed_results.json"
        with open(results_file, 'w') as f:
            json.dump({
                'metadata': {
                    'pdt_timestamp': pdt_str,
                    'utc_timestamp': utc_str,
                    'total_tested': total,
                    'successful': successful,
                    'success_rate': success_rate,
                    'average_confidence': avg_confidence
                },
                'results': [
                    {
                        'title': r.title,
                        'market_term': r.market_term,
                        'market_confidence': r.market_confidence,
                        'date_extracted': r.date_extracted,
                        'cleaned_title': r.cleaned_title,
                        'report_type': r.report_type,
                        'report_confidence': r.report_confidence,
                        'context_analysis': r.context_analysis,
                        'confusing_terms': r.confusing_terms,
                        'fallback_used': r.fallback_used,
                        'success': r.success,
                        'error': r.error
                    } for r in self.test_results
                ]
            }, f, indent=2)
        
        # Save readable report
        report_file = f"{output_dir}/test_report.txt" 
        with open(report_file, 'w') as f:
            f.write(f"Enhanced Market-Aware Extractor Test Report\n")
            f.write(f"Analysis Date (PDT): {pdt_str}\n")
            f.write(f"Analysis Date (UTC): {utc_str}\n") 
            f.write(f"{'='*60}\n\n")
            
            f.write(f"DETAILED RESULTS:\n\n")
            for i, result in enumerate(self.test_results, 1):
                f.write(f"Test #{i}: {result.title}\n")
                f.write(f"  Market Term: {result.market_term} (conf: {result.market_confidence:.2f})\n")
                f.write(f"  Date Extracted: {result.date_extracted}\n")
                f.write(f"  Cleaned Title: {result.cleaned_title}\n")
                f.write(f"  Report Type: '{result.report_type}' (conf: {result.report_confidence:.2f})\n")
                f.write(f"  Context: {result.context_analysis}\n")
                if result.confusing_terms:
                    f.write(f"  Confusing Terms: {result.confusing_terms}\n")
                if result.fallback_used:
                    f.write(f"  🔄 Market Prefix Fallback Used\n")
                f.write(f"  Success: {'✅' if result.success else '❌'}\n")
                if result.error:
                    f.write(f"  Error: {result.error}\n")
                f.write(f"\n")
        
        print(f"\n📁 Results saved to: {output_dir}")
        print(f"  - Detailed JSON: {results_file}")
        print(f"  - Readable report: {report_file}")
    
    def cleanup(self):
        """Clean up resources."""
        try:
            self.pattern_manager.close_connection()
            logger.info("✅ Resources cleaned up")
        except Exception as e:
            logger.warning(f"Cleanup warning: {e}")

def main():
    """Main function."""
    
    print("Enhanced Market-Aware Extractor Small Test")
    print("="*60)
    
    # Test with small sample first
    tester = EnhancedExtractorTester(sample_size=20)
    
    try:
        success = tester.run_test()
        
        if success:
            print("\n✅ Enhanced extractor test completed successfully!")
        else:
            print("\n❌ Enhanced extractor test failed!")
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