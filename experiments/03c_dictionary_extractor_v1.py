#!/usr/bin/env python3

"""
Script 03c: Dictionary Extractor v1
Extracts keywords, separators, and punctuation dictionaries from existing 921 report_type patterns
for use in Script 03 v3 simplified algorithmic detection

This script analyzes all report_type patterns to build comprehensive dictionaries that will
replace complex regex pattern matching with intelligent keyword + order detection.
"""

import os
import sys
import json
import re
from datetime import datetime
import pytz
from pymongo import MongoClient
from collections import defaultdict, Counter
from typing import Dict, List, Set, Tuple
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class DictionaryExtractor:
    """Extracts keyword, separator, and punctuation dictionaries from report type patterns."""
    
    def __init__(self, connection_string: str):
        """Initialize with MongoDB connection."""
        self.client = MongoClient(connection_string)
        self.db = self.client['deathstar']
        self.patterns_collection = self.db['pattern_libraries']
        
        # Dictionaries to build
        self.keywords = Counter()
        self.separators = Counter()
        self.punctuation = Counter()
        self.boundaries = Counter()
        
        # Format type analysis
        self.format_types = Counter()
        
        # Pattern analysis
        self.patterns_analyzed = 0
        self.patterns_failed = 0
        
    def extract_dictionaries(self) -> Dict:
        """Main method to extract all dictionaries from patterns."""
        logger.info("Starting dictionary extraction from report_type patterns...")
        
        # Load all active report_type patterns
        patterns = list(self.patterns_collection.find({
            "type": "report_type",
            "active": True
        }))
        
        logger.info(f"Found {len(patterns)} active report_type patterns to analyze")
        
        # Analyze each pattern
        for pattern_doc in patterns:
            self.analyze_pattern(pattern_doc)
        
        # Build final dictionaries
        return self.build_final_dictionaries()
    
    def analyze_pattern(self, pattern_doc: dict):
        """Analyze a single pattern document to extract components."""
        try:
            term = pattern_doc.get('term', '')
            pattern = pattern_doc.get('pattern', '')
            format_type = pattern_doc.get('format_type', '')
            normalized_form = pattern_doc.get('normalized_form', '')
            
            # Count format types
            self.format_types[format_type] += 1
            
            # Extract keywords from term
            self.extract_keywords_from_term(term)
            
            # Extract components from regex pattern
            self.extract_components_from_pattern(pattern)
            
            # Extract boundary markers
            self.extract_boundaries_from_pattern(pattern, format_type)
            
            self.patterns_analyzed += 1
            
        except Exception as e:
            logger.warning(f"Failed to analyze pattern {pattern_doc.get('_id')}: {e}")
            self.patterns_failed += 1
    
    def extract_keywords_from_term(self, term: str):
        """Extract keywords from the term field."""
        if not term:
            return
        
        # Split on common separators and extract individual words
        words = re.split(r'[\s,&]+', term)
        
        for word in words:
            word = word.strip()
            if word and len(word) > 1:  # Skip single characters and empty
                self.keywords[word] += 1
    
    def extract_components_from_pattern(self, pattern: str):
        """Extract separators and punctuation from regex patterns."""
        if not pattern:
            return
        
        # Common separator patterns in regex
        separator_patterns = {
            r'\\s\+': ' ',  # \s+ -> space
            r'\\s\*': ' ',  # \s* -> optional space
            r'\\s': ' ',    # \s -> space
            r',\\s\*': ', ', # ,\s* -> comma space
            r',\\s\+': ', ', # ,\s+ -> comma space
            r',': ',',      # plain comma
            r'&': '&',      # ampersand
            r'\\s*&\\s*': ' & ',  # spaced ampersand
            r'\\s+And\\s+': ' And ',  # " And "
        }
        
        for regex_pattern, separator in separator_patterns.items():
            if re.search(regex_pattern, pattern):
                self.separators[separator] += 1
        
        # Extract punctuation boundaries
        punctuation_patterns = {
            r'\$': 'end',           # End of string
            r'\^': 'start',         # Start of string  
            r'\\b': 'word_boundary', # Word boundary
            r'\[,\.\]': 'comma_period',  # [,.] character class
            r'\(\?\:': 'non_capture_group', # (?:...)
        }
        
        for regex_pattern, punct_type in punctuation_patterns.items():
            if re.search(regex_pattern, pattern):
                self.punctuation[punct_type] += 1
    
    def extract_boundaries_from_pattern(self, pattern: str, format_type: str):
        """Extract boundary markers from patterns."""
        if not pattern:
            return
        
        # Look for Market as boundary
        if 'Market' in pattern:
            self.boundaries['Market'] += 1
        
        # Look for Industry as boundary
        if 'Industry' in pattern:
            self.boundaries['Industry'] += 1
        
        # Look for Global as boundary
        if 'Global' in pattern:
            self.boundaries['Global'] += 1
        
        # Count format-specific boundaries
        if format_type == 'terminal_type':
            self.boundaries['terminal_end'] += 1
        elif format_type == 'prefix_type':
            self.boundaries['prefix_start'] += 1
        elif format_type == 'compound_type':
            self.boundaries['compound_middle'] += 1
    
    def build_final_dictionaries(self) -> Dict:
        """Build final structured dictionaries with frequency analysis."""
        
        # Build keyword dictionary with frequency ordering
        keyword_dict = {
            'primary_keywords': [],
            'secondary_keywords': [],
            'frequency_analysis': dict(self.keywords.most_common(50))
        }
        
        # Categorize keywords by frequency
        total_patterns = self.patterns_analyzed
        for keyword, count in self.keywords.most_common(50):
            frequency_percent = (count / total_patterns) * 100
            
            if frequency_percent >= 10:  # Appears in 10%+ of patterns
                keyword_dict['primary_keywords'].append({
                    'word': keyword,
                    'frequency': count,
                    'percentage': round(frequency_percent, 2)
                })
            else:
                keyword_dict['secondary_keywords'].append({
                    'word': keyword,
                    'frequency': count,
                    'percentage': round(frequency_percent, 2)
                })
        
        # Build separator dictionary
        separator_dict = {
            'common_separators': list(self.separators.keys()),
            'frequency_analysis': dict(self.separators.most_common())
        }
        
        # Build punctuation dictionary
        punctuation_dict = {
            'boundary_markers': list(self.punctuation.keys()),
            'frequency_analysis': dict(self.punctuation.most_common())
        }
        
        # Build boundary dictionary
        boundary_dict = {
            'primary_boundaries': list(self.boundaries.keys()),
            'frequency_analysis': dict(self.boundaries.most_common())
        }
        
        # Build format analysis
        format_analysis = {
            'format_types': dict(self.format_types.most_common()),
            'total_patterns': self.patterns_analyzed
        }
        
        return {
            'keywords': keyword_dict,
            'separators': separator_dict,
            'punctuation': punctuation_dict,
            'boundaries': boundary_dict,
            'format_analysis': format_analysis,
            'extraction_stats': {
                'patterns_analyzed': self.patterns_analyzed,
                'patterns_failed': self.patterns_failed,
                'success_rate': round((self.patterns_analyzed / (self.patterns_analyzed + self.patterns_failed)) * 100, 2)
            }
        }
    
    def generate_report(self, dictionaries: Dict, output_dir: str):
        """Generate comprehensive analysis report."""
        
        # Create timestamp
        pdt = pytz.timezone('America/Los_Angeles')
        utc = pytz.timezone('UTC')
        timestamp_pdt = datetime.now(pdt).strftime('%Y-%m-%d %H:%M:%S %Z')
        timestamp_utc = datetime.now(utc).strftime('%Y-%m-%d %H:%M:%S %Z')
        
        # Save raw dictionaries as JSON
        dict_filename = os.path.join(output_dir, 'report_type_dictionaries.json')
        with open(dict_filename, 'w') as f:
            json.dump(dictionaries, f, indent=2)
        
        # Generate human-readable report
        report_filename = os.path.join(output_dir, 'dictionary_extraction_report.md')
        
        with open(report_filename, 'w') as f:
            f.write(f"""# Script 03v3 Dictionary Extraction Report

**Analysis Date (PDT):** {timestamp_pdt}
**Analysis Date (UTC):** {timestamp_utc}
**Source Patterns:** {dictionaries['extraction_stats']['patterns_analyzed']} active report_type patterns
**Success Rate:** {dictionaries['extraction_stats']['success_rate']}%

## Executive Summary

This analysis extracted keyword, separator, and punctuation dictionaries from {dictionaries['extraction_stats']['patterns_analyzed']} report type patterns to enable Script 03 v3 algorithmic detection approach.

## Primary Keywords (≥10% frequency)

""")
            
            # Primary keywords table
            for keyword_data in dictionaries['keywords']['primary_keywords']:
                f.write(f"- **{keyword_data['word']}**: {keyword_data['frequency']} patterns ({keyword_data['percentage']}%)\n")
            
            f.write(f"""
## Secondary Keywords (<10% frequency)

Total secondary keywords found: {len(dictionaries['keywords']['secondary_keywords'])}

""")
            
            # Show top 20 secondary keywords
            for keyword_data in dictionaries['keywords']['secondary_keywords'][:20]:
                f.write(f"- {keyword_data['word']}: {keyword_data['frequency']} patterns ({keyword_data['percentage']}%)\n")
            
            f.write(f"""
## Separators Analysis

Common separators found in patterns:

""")
            
            for separator, count in dictionaries['separators']['frequency_analysis'].items():
                f.write(f"- `\"{separator}\"`: {count} patterns\n")
            
            f.write(f"""
## Boundary Markers Analysis

Boundary markers found in patterns:

""")
            
            for boundary, count in dictionaries['boundaries']['frequency_analysis'].items():
                f.write(f"- **{boundary}**: {count} patterns\n")
            
            f.write(f"""
## Format Type Distribution

""")
            
            for format_type, count in dictionaries['format_analysis']['format_types'].items():
                percentage = (count / dictionaries['format_analysis']['total_patterns']) * 100
                f.write(f"- **{format_type}**: {count} patterns ({percentage:.1f}%)\n")
            
            f.write(f"""
## Implementation Recommendations

### Market Boundary Detection
- **Primary boundary word**: "Market" (found in {dictionaries['boundaries']['frequency_analysis'].get('Market', 0)} patterns)
- **Secondary boundaries**: Industry, Global

### Keyword Detection Priority
1. **High Priority** (≥10% frequency): {len(dictionaries['keywords']['primary_keywords'])} keywords
2. **Medium Priority** (<10% frequency): {len(dictionaries['keywords']['secondary_keywords'])} keywords

### Separator Handling
- **Primary separators**: Space, comma+space, ampersand
- **Complex separators**: "And", "&" with surrounding spaces

### Algorithm Design
1. Use "Market" as primary boundary detection
2. Search for keywords in frequency order (primary first)
3. Detect separators between found keywords
4. Handle edge cases for non-dictionary words

## Next Steps

1. Implement keyword detection algorithm using primary keywords
2. Create separator detection between keyword boundaries
3. Build edge case detection for non-dictionary words
4. Test against current v2 implementation for accuracy validation

""")
        
        logger.info(f"Dictionary extraction complete!")
        logger.info(f"Raw dictionaries saved to: {dict_filename}")
        logger.info(f"Analysis report saved to: {report_filename}")
        
        return dict_filename, report_filename

def create_output_directory() -> str:
    """Create timestamped output directory."""
    pdt = pytz.timezone('America/Los_Angeles')
    timestamp = datetime.now(pdt).strftime('%Y%m%d_%H%M%S')
    output_dir = f"../outputs/{timestamp}_script03v3_dictionary_extraction"
    os.makedirs(output_dir, exist_ok=True)
    return output_dir

def main():
    """Main execution function."""
    try:
        # Load environment variables
        from dotenv import load_dotenv
        load_dotenv()
        
        connection_string = os.getenv('MONGODB_URI')
        if not connection_string:
            raise ValueError("MongoDB connection string not found in environment variables")
        
        # Create output directory
        output_dir = create_output_directory()
        logger.info(f"Output directory created: {output_dir}")
        
        # Initialize extractor
        extractor = DictionaryExtractor(connection_string)
        
        # Extract dictionaries
        dictionaries = extractor.extract_dictionaries()
        
        # Generate report
        dict_file, report_file = extractor.generate_report(dictionaries, output_dir)
        
        # Print summary
        print(f"\n{'='*60}")
        print(f"SCRIPT 03V3 DICTIONARY EXTRACTION COMPLETE")
        print(f"{'='*60}")
        print(f"Patterns Analyzed: {dictionaries['extraction_stats']['patterns_analyzed']}")
        print(f"Primary Keywords: {len(dictionaries['keywords']['primary_keywords'])}")
        print(f"Secondary Keywords: {len(dictionaries['keywords']['secondary_keywords'])}")
        print(f"Separators Found: {len(dictionaries['separators']['common_separators'])}")
        print(f"Boundary Markers: {len(dictionaries['boundaries']['primary_boundaries'])}")
        print(f"Success Rate: {dictionaries['extraction_stats']['success_rate']}%")
        print(f"\nFiles Generated:")
        print(f"- Dictionary Data: {dict_file}")
        print(f"- Analysis Report: {report_file}")
        print(f"{'='*60}")
        
        # Show top keywords preview
        print(f"\nTOP KEYWORDS PREVIEW:")
        for i, keyword_data in enumerate(dictionaries['keywords']['primary_keywords'][:10], 1):
            print(f"{i:2d}. {keyword_data['word']} ({keyword_data['frequency']} patterns, {keyword_data['percentage']}%)")
        
    except Exception as e:
        logger.error(f"Dictionary extraction failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()