#!/usr/bin/env python3

"""
Data-Driven Report Type Pattern Discovery
Uses existing 01→02 pipeline to systematically discover all report type patterns in the dataset.

Strategy:
1. Use 01 script to filter out special market terms ("market_for", "market_in")  
2. Use 02 script to remove dates from titles
3. Find "Market" in remaining text and extract "Market" + everything after it
4. Handle special cases like "Aftermarket" (exclude these)
5. Deduplicate and create a simple list for manual review

This will reveal the actual patterns that exist in the data for building the pattern library.
"""

import os
import sys
import logging
import importlib.util
import re
from datetime import datetime, timezone
from collections import defaultdict, Counter
from pymongo import MongoClient
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Dynamic imports for existing pipeline components
def import_pipeline_components():
    """Import the existing 01 and 02 scripts."""
    components = {}
    
    try:
        # Import 01 market term classifier
        spec = importlib.util.spec_from_file_location(
            "market_term_classifier_v1", 
            "01_market_term_classifier_v1.py"
        )
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        
        components['market_classifier'] = module.MarketTermClassifier
        components['ClassificationResult'] = module.ClassificationResult
        logger.info("✅ Imported 01_market_term_classifier_v1")
        
    except Exception as e:
        logger.error(f"Failed to import market term classifier: {e}")
        sys.exit(1)
    
    try:
        # Import 02 date extractor
        spec = importlib.util.spec_from_file_location(
            "date_extractor_v1", 
            "02_date_extractor_v1.py"
        )
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        
        components['date_extractor'] = module.EnhancedDateExtractor
        components['DateExtractionResult'] = module.EnhancedDateExtractionResult
        logger.info("✅ Imported 02_date_extractor_v1")
        
    except Exception as e:
        logger.error(f"Failed to import date extractor: {e}")
        sys.exit(1)
    
    return components

class ReportTypeDiscovery:
    """Data-driven discovery of report type patterns using existing pipeline."""
    
    def __init__(self, sample_size=None):
        self.sample_size = sample_size
        self.components = import_pipeline_components()
        
        # Initialize pattern library manager for date extractor
        try:
            spec = importlib.util.spec_from_file_location(
                "pattern_library_manager_v1", 
                "00b_pattern_library_manager_v1.py"
            )
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            pattern_manager = module.PatternLibraryManager()
            logger.info("✅ Initialized PatternLibraryManager for date extractor")
            
        except Exception as e:
            logger.error(f"Failed to initialize PatternLibraryManager: {e}")
            sys.exit(1)
        
        # Initialize pipeline components
        self.market_classifier = self.components['market_classifier']()
        self.date_extractor = self.components['date_extractor'](pattern_manager)
        
        # Special market cases to exclude (like "Aftermarket")
        self.special_market_cases = [
            "Aftermarket", "Farmer's Market", "Farmers Market", "Supermarket", 
            "Hypermarket", "Stock Market", "Black Market", "Flea Market",
            "Mass Market", "Niche Market", "Secondary Market", "Primary Market",
            "Grey Market", "Gray Market"
        ]
        
        # Connect to MongoDB
        self.db = None
        self._connect_to_mongodb()
        
        # Results storage
        self.discovered_patterns = []
        self.pattern_frequency = Counter()
        self.sample_extractions = defaultdict(list)  # Store examples for each pattern
        
    def _connect_to_mongodb(self):
        """Connect to MongoDB database."""
        try:
            mongodb_uri = os.getenv('MONGODB_URI')
            if not mongodb_uri:
                raise ValueError("MONGODB_URI environment variable not found")
            
            client = MongoClient(mongodb_uri)
            self.db = client['deathstar']
            logger.info("✅ Connected to MongoDB database: deathstar")
            
        except Exception as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            sys.exit(1)
    
    def _get_sample_titles(self):
        """Get sample titles from MongoDB."""
        try:
            if self.sample_size:
                # Get sample of titles
                pipeline = [
                    {"$sample": {"size": self.sample_size}},
                    {"$project": {"report_title_short": 1, "_id": 1}}
                ]
                logger.info(f"Retrieving sample of {self.sample_size} titles...")
            else:
                # Get ALL titles for comprehensive analysis
                pipeline = [
                    {"$project": {"report_title_short": 1, "_id": 1}}
                ]
                logger.info("Retrieving ALL titles from database for comprehensive analysis...")
            
            cursor = self.db.markets_raw.aggregate(pipeline)
            titles = []
            
            for doc in cursor:
                title = doc.get('report_title_short', '').strip()
                if title and len(title) > 10:  # Basic quality filter
                    titles.append(title)
            
            logger.info(f"✅ Retrieved {len(titles)} titles from MongoDB")
            return titles
            
        except Exception as e:
            logger.error(f"Failed to retrieve titles: {e}")
            return []
    
    def _is_special_market_case(self, text):
        """Check if text contains special market cases that should be excluded."""
        text_lower = text.lower()
        for special_case in self.special_market_cases:
            if special_case.lower() in text_lower:
                return True, special_case
        return False, None
    
    def _extract_potential_report_type(self, title_after_date_removal):
        """Extract potential report type from 'Market' to end of string."""
        
        # Find 'Market' in the text
        market_match = re.search(r'\bMarket\b', title_after_date_removal, re.IGNORECASE)
        if not market_match:
            return None, "No 'Market' found"
        
        # Extract from 'Market' to end
        start_pos = market_match.start()
        potential_report_type = title_after_date_removal[start_pos:].strip()
        
        # Check if this is a special market case that should be excluded
        is_special, special_case = self._is_special_market_case(potential_report_type)
        if is_special:
            return None, f"Special market case: {special_case}"
        
        # Clean up the potential report type
        # Remove trailing punctuation
        potential_report_type = re.sub(r'[.,;:!?]+$', '', potential_report_type).strip()
        
        # Skip if too short or too long
        if len(potential_report_type) < 6:  # "Market" alone is 6 chars
            return None, "Too short"
        
        if len(potential_report_type) > 100:  # Reasonable upper bound
            return None, "Too long"
        
        return potential_report_type, "Extracted"
    
    def discover_patterns(self):
        """Main discovery process using 01→02 pipeline."""
        
        logger.info("Starting data-driven report type pattern discovery...")
        logger.info("="*60)
        
        # Get sample titles
        titles = self._get_sample_titles()
        if not titles:
            logger.error("No titles retrieved, aborting discovery")
            return False
        
        logger.info(f"Processing {len(titles)} titles through 01→02 pipeline...")
        
        processed_count = 0
        standard_market_count = 0
        extracted_patterns = []
        
        for i, title in enumerate(titles):
            try:
                # Step 1: Market term classification (filter out market_for/market_in)
                market_classification = self.market_classifier.classify(title)
                
                # Only process "standard" market terms
                if market_classification.market_type.value != "standard":
                    continue
                
                standard_market_count += 1
                
                # Step 2: Date extraction and removal
                date_result = self.date_extractor.extract(title)
                
                # Manually remove the extracted date from title if found
                title_after_date_removal = title
                if date_result.raw_match:
                    title_after_date_removal = title.replace(date_result.raw_match, '').strip()
                    # Clean up extra spaces and punctuation
                    title_after_date_removal = re.sub(r'\s+', ' ', title_after_date_removal)
                    title_after_date_removal = re.sub(r'[,;]\s*$', '', title_after_date_removal)
                
                # Step 3: Extract potential report type from 'Market' to end
                potential_report_type, extraction_reason = self._extract_potential_report_type(
                    title_after_date_removal
                )
                
                if potential_report_type:
                    extracted_patterns.append({
                        'original_title': title,
                        'title_after_date_removal': title_after_date_removal,
                        'extracted_date': date_result.extracted_date_range,
                        'potential_report_type': potential_report_type,
                        'extraction_reason': extraction_reason
                    })
                    
                    # Track frequency and examples
                    self.pattern_frequency[potential_report_type] += 1
                    if len(self.sample_extractions[potential_report_type]) < 5:
                        self.sample_extractions[potential_report_type].append(title)
                
                processed_count += 1
                
                # Progress logging
                if processed_count % 500 == 0:
                    logger.info(f"Processed {processed_count} standard market titles...")
                
            except Exception as e:
                logger.warning(f"Error processing title '{title[:50]}...': {e}")
                continue
        
        self.discovered_patterns = extracted_patterns
        
        logger.info(f"✅ Discovery complete:")
        logger.info(f"  - Total titles processed: {len(titles)}")
        logger.info(f"  - Standard market titles: {standard_market_count}")
        logger.info(f"  - Report type patterns discovered: {len(extracted_patterns)}")
        logger.info(f"  - Unique patterns found: {len(self.pattern_frequency)}")
        
        return True
    
    def generate_discovery_report(self):
        """Generate comprehensive discovery report for manual review."""
        
        # Create timestamped output directory
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_dir = f"../outputs/{timestamp}_report_type_discovery"
        os.makedirs(output_dir, exist_ok=True)
        
        # Generate timestamps
        now_utc = datetime.now(timezone.utc)
        now_pdt = now_utc.astimezone()
        pdt_str = now_pdt.strftime("%Y-%m-%d %H:%M:%S %Z")
        utc_str = now_utc.strftime("%Y-%m-%d %H:%M:%S UTC")
        
        # 1. Unique patterns ranked by frequency
        patterns_file = f"{output_dir}/unique_patterns_by_frequency.txt"
        with open(patterns_file, 'w', encoding='utf-8') as f:
            f.write(f"Discovered Report Type Patterns - Ranked by Frequency\n")
            f.write(f"Analysis Date (PDT): {pdt_str}\n")
            f.write(f"Analysis Date (UTC): {utc_str}\n")
            f.write(f"="*80 + "\n\n")
            
            f.write(f"Total Unique Patterns Found: {len(self.pattern_frequency)}\n")
            f.write(f"Total Pattern Instances: {sum(self.pattern_frequency.values())}\n\n")
            
            f.write(f"Patterns Ranked by Frequency:\n")
            f.write("-" * 60 + "\n")
            
            for i, (pattern, count) in enumerate(self.pattern_frequency.most_common(), 1):
                percentage = (count / len(self.discovered_patterns)) * 100
                f.write(f"{i:3d}. {pattern}\n")
                f.write(f"     Frequency: {count} occurrences ({percentage:.1f}%)\n")
                f.write(f"     Examples: {'; '.join(self.sample_extractions[pattern][:3])}\n\n")
        
        # 2. All patterns with full examples
        detailed_file = f"{output_dir}/detailed_patterns_with_examples.txt"
        with open(detailed_file, 'w', encoding='utf-8') as f:
            f.write(f"Detailed Report Type Pattern Analysis\n")
            f.write(f"Analysis Date (PDT): {pdt_str}\n")
            f.write(f"Analysis Date (UTC): {utc_str}\n")
            f.write(f"="*80 + "\n\n")
            
            for pattern, count in self.pattern_frequency.most_common():
                f.write(f"PATTERN: {pattern}\n")
                f.write(f"Frequency: {count} occurrences\n")
                f.write(f"Examples:\n")
                
                for example in self.sample_extractions[pattern][:5]:
                    f.write(f"  - {example}\n")
                
                f.write("-" * 80 + "\n\n")
        
        # 3. Raw data export for advanced analysis
        raw_file = f"{output_dir}/raw_extraction_data.txt"
        with open(raw_file, 'w', encoding='utf-8') as f:
            f.write(f"Raw Report Type Extraction Data\n")
            f.write(f"Analysis Date (PDT): {pdt_str}\n")
            f.write(f"Analysis Date (UTC): {utc_str}\n")
            f.write(f"="*80 + "\n\n")
            
            for i, extraction in enumerate(self.discovered_patterns[:1000], 1):  # First 1000 for review
                f.write(f"{i:4d}. Original: {extraction['original_title']}\n")
                f.write(f"      After Date Removal: {extraction['title_after_date_removal']}\n")
                f.write(f"      Extracted Date: {extraction['extracted_date'] or 'None'}\n")
                f.write(f"      Report Type: {extraction['potential_report_type']}\n")
                f.write(f"      Reason: {extraction['extraction_reason']}\n")
                f.write("\n")
        
        # 4. Simple pattern list for quick scanning
        simple_list_file = f"{output_dir}/simple_pattern_list.txt"
        with open(simple_list_file, 'w', encoding='utf-8') as f:
            f.write(f"Simple Pattern List for Quick Review\n")
            f.write(f"Analysis Date (PDT): {pdt_str}\n")
            f.write(f"Analysis Date (UTC): {utc_str}\n")
            f.write(f"Total Patterns: {len(self.pattern_frequency)}\n")
            f.write(f"="*60 + "\n\n")
            
            for pattern, count in self.pattern_frequency.most_common():
                f.write(f"{pattern}\n")
        
        # 5. Summary statistics
        summary_file = f"{output_dir}/discovery_summary.md"
        with open(summary_file, 'w', encoding='utf-8') as f:
            f.write(f"# Report Type Pattern Discovery Summary\n\n")
            f.write(f"**Analysis Date (PDT):** {pdt_str}\n")
            f.write(f"**Analysis Date (UTC):** {utc_str}\n\n")
            
            f.write(f"## Discovery Results\n\n")
            sample_text = f"- **Sample Size:** {self.sample_size:,} titles\n" if self.sample_size else f"- **Full Database:** ALL {len(self.discovered_patterns):,} standard market titles\n"
            f.write(sample_text)
            f.write(f"- **Standard Market Titles:** {len(self.discovered_patterns):,}\n")
            f.write(f"- **Unique Patterns Found:** {len(self.pattern_frequency):,}\n")
            f.write(f"- **Total Pattern Instances:** {sum(self.pattern_frequency.values()):,}\n\n")
            
            f.write(f"## Top 20 Most Common Patterns\n\n")
            for i, (pattern, count) in enumerate(self.pattern_frequency.most_common(20), 1):
                percentage = (count / len(self.discovered_patterns)) * 100
                f.write(f"{i}. **{pattern}** - {count} occurrences ({percentage:.1f}%)\n")
            
            f.write(f"\n## Next Steps\n\n")
            f.write(f"1. **Manual Review:** Examine `simple_pattern_list.txt` for quick scanning\n")
            f.write(f"2. **Pattern Classification:** Identify which patterns are actual report types vs noise\n")
            f.write(f"3. **Pattern Addition:** Add approved patterns to MongoDB pattern_libraries collection\n")
            f.write(f"4. **Special Cases:** Handle acronym-based and malformed patterns separately\n")
            f.write(f"5. **Test Validation:** Re-run Phase 3 pipeline to measure improvement\n")
        
        logger.info(f"✅ Discovery reports generated in: {output_dir}")
        logger.info(f"  - simple_pattern_list.txt: Quick scanning list (NEW)")
        logger.info(f"  - unique_patterns_by_frequency.txt: Manual review file")
        logger.info(f"  - detailed_patterns_with_examples.txt: Full analysis")
        logger.info(f"  - raw_extraction_data.txt: Raw data for advanced analysis")
        logger.info(f"  - discovery_summary.md: Executive summary")
        
        return output_dir
    
    def cleanup(self):
        """Clean up resources."""
        if self.db is not None:
            self.db.client.close()
            logger.info("✅ MongoDB connection closed")

def main():
    """Main function for report type pattern discovery."""
    
    print("Data-Driven Report Type Pattern Discovery")
    print("="*60)
    print("Strategy: Use 01→02 pipeline to systematically discover report type patterns")
    print()
    
    # Initialize discovery engine - use full database for comprehensive analysis
    discovery = ReportTypeDiscovery(sample_size=None)  # None = use all titles
    
    try:
        # Run pattern discovery
        success = discovery.discover_patterns()
        
        if success:
            # Generate comprehensive reports
            output_dir = discovery.generate_discovery_report()
            
            print("\n✅ Report Type Pattern Discovery completed successfully!")
            print(f"\nGenerated files in: {output_dir}")
            print("- simple_pattern_list.txt (NEW: Quick scanning)")
            print("- unique_patterns_by_frequency.txt (PRIORITY: Manual review)")
            print("- detailed_patterns_with_examples.txt")
            print("- raw_extraction_data.txt")
            print("- discovery_summary.md")
            print("\nRecommendation: Review 'simple_pattern_list.txt' first for quick scanning!")
            
        else:
            print("\n❌ Report Type Pattern Discovery failed!")
            return False
            
    except Exception as e:
        logger.error(f"Discovery failed: {e}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        # Clean up
        discovery.cleanup()
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)