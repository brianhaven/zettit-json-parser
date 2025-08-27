#!/usr/bin/env python3
"""
Geographic Pattern Alias Curation Analysis Script

Analyzes which geographic aliases are likely business/technical terms vs legitimate 
geographic references in market research titles to inform pattern library curation.

Key Goals:
1. Identify aliases that are primarily business/technical terms (TV, DC, AC, Car, etc.)
2. Evaluate frequency and context of alias usage across all 19,558 titles
3. Recommend which aliases to move to 'deprecated_aliases' field vs keep active
4. Preserve questionable aliases for future use while removing from active matching

Usage:
    python3 test_alias_curation_analysis.py
"""

import json
import os
import sys
import re
import logging
from collections import defaultdict, Counter
from datetime import datetime
from typing import Dict, List, Tuple, Set
from dataclasses import dataclass
import importlib.util
import pytz

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv()

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class AliasUsageAnalysis:
    """Represents analysis of a specific alias usage."""
    alias: str
    region: str
    total_matches: int
    sample_titles: List[str]
    contexts: List[str]
    business_term_likelihood: float  # 0.0-1.0 where 1.0 = definitely business term
    recommendation: str  # 'keep', 'deprecate', 'review'

class AliasCurationAnalyzer:
    """Analyzes geographic pattern aliases for business vs geographic usage."""
    
    def __init__(self):
        self.mongo_uri = os.getenv('MONGODB_URI')
        if not self.mongo_uri:
            raise ValueError("MONGODB_URI environment variable is required")
        
        self.resources_file = "/home/ec2-user/zettit/services/json-parser/resources/deathstar.markets_raw_collapsed.json"
        self.geographic_patterns = {}
        self.market_titles = []
        
        # Business/technical term patterns that suggest aliases should be deprecated
        self.business_indicators = {
            'tv': ['4k', 'smart', 'lcd', 'oled', 'led', 'hd', 'uhd', 'digital', 'cable', 'streaming'],
            'dc': ['motor', 'current', 'electric', 'brushless', 'battery', 'power', 'voltage'],
            'ac': ['motor', 'current', 'electric', 'alternating', 'power', 'voltage', 'hvac'],
            'car': ['automotive', 'vehicle', 'electric', 'battery', 'engine', 'auto'],
            'gm': ['general motors', 'automotive', 'crops', 'modified', 'genetic'],
            'li': ['lithium', 'battery', 'ion', 'metal', 'based'],
            'bi': ['business intelligence', 'platform', 'analytics', 'data'],
            'can': ['aerosol', 'metal', 'aluminum', 'steel', 'container'],
            'us': ['united states'],  # Keep - overwhelmingly geographic
            'up': ['uttar pradesh', 'state'],  # Geographic context
        }
        
        # Common business/technical abbreviations unlikely to be geographic
        self.likely_business_terms = {
            'tv', 'dc', 'ac', 'gm', 'li', 'bi', 'ai', 'iot', 'api', 'cpu', 'gpu', 
            'ssd', 'led', 'lcd', 'oled', 'hd', 'uhd', '4k', '5g', 'wifi', 'usb',
            'ram', 'rom', 'cd', 'dvd', 'blu'
        }
    
    def create_output_directory(self) -> str:
        """Create timestamped output directory."""
        # Get absolute path to outputs directory (from /experiments/tests/ to /outputs/)
        script_dir = os.path.dirname(os.path.abspath(__file__))
        experiments_dir = os.path.dirname(script_dir)  
        project_root = os.path.dirname(experiments_dir)
        outputs_dir = os.path.join(project_root, 'outputs')
        
        # Create timestamp in Pacific Time
        pdt = pytz.timezone('America/Los_Angeles')
        timestamp = datetime.now(pdt).strftime('%Y%m%d_%H%M%S')
        
        # Create timestamped subdirectory
        output_dir = os.path.join(outputs_dir, f"{timestamp}_alias_curation_analysis")
        os.makedirs(output_dir, exist_ok=True)
        
        return output_dir
    
    def load_geographic_patterns(self):
        """Load geographic patterns from MongoDB."""
        logger.info("Loading geographic patterns from MongoDB...")
        
        client = MongoClient(self.mongo_uri)
        db = client['deathstar']
        
        # Get all geographic patterns
        patterns = list(db.pattern_libraries.find({"type": "geographic_entity", "active": True}))
        logger.info(f"Loaded {len(patterns)} geographic patterns from MongoDB")
        
        # Organize patterns by term
        for pattern in patterns:
            self.geographic_patterns[pattern['term']] = {
                'term': pattern['term'],
                'aliases': pattern.get('aliases', []),
                'priority': pattern.get('priority', 5)
            }
        
        client.close()
    
    def load_market_titles(self) -> List[str]:
        """Load all market research titles from resources file."""
        titles = []
        with open(self.resources_file, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue
                
                # Remove trailing comma if present
                if line.endswith(','):
                    line = line[:-1]
                
                try:
                    item = json.loads(line)
                    if 'report_title_short' in item:
                        titles.append(item['report_title_short'])
                    else:
                        logger.warning(f"No 'report_title_short' field in line {line_num}")
                except json.JSONDecodeError as e:
                    logger.warning(f"Failed to parse line {line_num}: {e}")
                    continue
        
        logger.info(f"Loaded {len(titles)} titles from resources file")
        return titles
    
    def analyze_alias_usage(self, alias: str, region: str, titles: List[str]) -> AliasUsageAnalysis:
        """Analyze how a specific alias is used across all titles."""
        matches = []
        contexts = []
        
        # Create word boundary pattern for the alias
        pattern = rf'\b{re.escape(alias)}\b'
        
        for title in titles:
            if re.search(pattern, title, re.IGNORECASE):
                matches.append(title)
                
                # Extract context around the match
                match = re.search(pattern, title, re.IGNORECASE)
                if match:
                    start = max(0, match.start() - 20)
                    end = min(len(title), match.end() + 20)
                    context = title[start:end]
                    contexts.append(context)
        
        # Calculate business term likelihood
        business_likelihood = self.calculate_business_likelihood(alias, matches)
        
        # Generate recommendation
        recommendation = self.generate_recommendation(alias, business_likelihood, len(matches))
        
        return AliasUsageAnalysis(
            alias=alias,
            region=region,
            total_matches=len(matches),
            sample_titles=matches[:10],  # First 10 examples
            contexts=contexts[:10],
            business_term_likelihood=business_likelihood,
            recommendation=recommendation
        )
    
    def calculate_business_likelihood(self, alias: str, matching_titles: List[str]) -> float:
        """Calculate likelihood that alias usage is business/technical vs geographic."""
        if not matching_titles:
            return 0.0
        
        alias_lower = alias.lower()
        business_indicators = self.business_indicators.get(alias_lower, [])
        
        # Check if alias is in known business terms
        if alias_lower in self.likely_business_terms:
            base_score = 0.8
        else:
            base_score = 0.3
        
        # Count business context indicators
        business_context_count = 0
        for title in matching_titles:
            title_lower = title.lower()
            for indicator in business_indicators:
                if indicator in title_lower:
                    business_context_count += 1
                    break
        
        # Calculate context-based adjustment
        if matching_titles:
            context_score = business_context_count / len(matching_titles)
            final_score = (base_score + context_score) / 2
        else:
            final_score = base_score
        
        return min(1.0, final_score)
    
    def generate_recommendation(self, alias: str, business_likelihood: float, match_count: int) -> str:
        """Generate curation recommendation based on analysis."""
        if business_likelihood >= 0.7:
            return 'deprecate'
        elif business_likelihood >= 0.4 or match_count < 5:
            return 'review'
        else:
            return 'keep'
    
    def run_analysis(self):
        """Run the complete alias curation analysis."""
        logger.info("Starting Alias Curation Analysis")
        
        # Create output directory
        output_dir = self.create_output_directory()
        logger.info(f"Output directory: {output_dir}")
        
        # Load data
        self.load_geographic_patterns()
        self.market_titles = self.load_market_titles()
        
        # Analyze all aliases
        all_analyses = []
        alias_counts = defaultdict(int)
        
        logger.info("Analyzing alias usage patterns...")
        for region, pattern_data in self.geographic_patterns.items():
            for alias in pattern_data['aliases']:
                if alias and len(alias.strip()) <= 5:  # Focus on short aliases
                    analysis = self.analyze_alias_usage(alias, region, self.market_titles)
                    all_analyses.append(analysis)
                    alias_counts[analysis.recommendation] += 1
        
        # Sort by business likelihood (highest first)
        all_analyses.sort(key=lambda x: x.business_term_likelihood, reverse=True)
        
        # Generate reports
        self.generate_summary_report(output_dir, all_analyses, alias_counts)
        self.generate_deprecation_recommendations(output_dir, all_analyses)
        self.generate_curation_script(output_dir, all_analyses)
        
        logger.info(f"Analysis complete! Reports saved to: {output_dir}")
    
    def generate_summary_report(self, output_dir: str, analyses: List[AliasUsageAnalysis], counts: Dict[str, int]):
        """Generate comprehensive summary report."""
        pdt = pytz.timezone('America/Los_Angeles')
        timestamp = datetime.now(pdt).strftime('%Y-%m-%d %H:%M:%S PDT')
        
        summary_file = os.path.join(output_dir, "alias_curation_summary.txt")
        with open(summary_file, 'w') as f:
            f.write("Geographic Pattern Alias Curation Analysis Summary\n")
            f.write(f"Analysis Date: {timestamp}\n")
            f.write("=" * 60 + "\n\n")
            
            f.write(f"Dataset: {len(self.market_titles)} market research titles\n")
            f.write(f"Total aliases analyzed: {len(analyses)}\n\n")
            
            f.write("CURATION RECOMMENDATIONS:\n")
            f.write(f"  Deprecate (likely business terms): {counts.get('deprecate', 0)}\n")
            f.write(f"  Review (uncertain): {counts.get('review', 0)}\n")
            f.write(f"  Keep (likely geographic): {counts.get('keep', 0)}\n\n")
            
            f.write("TOP PROBLEMATIC ALIASES (likely business terms):\n")
            f.write("-" * 50 + "\n")
            for analysis in analyses[:20]:  # Top 20
                f.write(f"'{analysis.alias}' -> {analysis.region}\n")
                f.write(f"  Matches: {analysis.total_matches}\n")
                f.write(f"  Business likelihood: {analysis.business_term_likelihood:.2f}\n")
                f.write(f"  Recommendation: {analysis.recommendation.upper()}\n")
                if analysis.sample_titles:
                    f.write(f"  Sample: {analysis.sample_titles[0]}\n")
                f.write("\n")
    
    def generate_deprecation_recommendations(self, output_dir: str, analyses: List[AliasUsageAnalysis]):
        """Generate specific deprecation recommendations."""
        pdt = pytz.timezone('America/Los_Angeles')
        timestamp = datetime.now(pdt).strftime('%Y-%m-%d %H:%M:%S PDT')
        
        deprecation_file = os.path.join(output_dir, "deprecation_recommendations.txt")
        with open(deprecation_file, 'w') as f:
            f.write("Alias Deprecation Recommendations\n")
            f.write(f"Analysis Date: {timestamp}\n")
            f.write("=" * 50 + "\n\n")
            
            # Group by recommendation
            for recommendation in ['deprecate', 'review', 'keep']:
                matching_analyses = [a for a in analyses if a.recommendation == recommendation]
                if not matching_analyses:
                    continue
                
                f.write(f"{recommendation.upper()} ({len(matching_analyses)} aliases):\n")
                f.write("-" * 30 + "\n")
                
                for analysis in matching_analyses:
                    f.write(f"'{analysis.alias}' -> {analysis.region}\n")
                    f.write(f"  Matches: {analysis.total_matches}, Business likelihood: {analysis.business_term_likelihood:.2f}\n")
                    if analysis.sample_titles:
                        f.write(f"  Example: {analysis.sample_titles[0]}\n")
                    f.write("\n")
                f.write("\n")
    
    def generate_curation_script(self, output_dir: str, analyses: List[AliasUsageAnalysis]):
        """Generate MongoDB script to implement deprecations."""
        pdt = pytz.timezone('America/Los_Angeles')
        timestamp = datetime.now(pdt).strftime('%Y-%m-%d %H:%M:%S PDT')
        
        script_file = os.path.join(output_dir, "mongodb_curation_script.js")
        with open(script_file, 'w') as f:
            f.write("// MongoDB Script for Geographic Pattern Alias Curation\n")
            f.write(f"// Generated: {timestamp}\n")
            f.write("// Execute in MongoDB shell or Compass\n\n")
            
            # Generate update operations for deprecations
            deprecate_analyses = [a for a in analyses if a.recommendation == 'deprecate']
            
            f.write(f"// DEPRECATE {len(deprecate_analyses)} business term aliases\n")
            f.write("// Move aliases to deprecated_aliases field and remove from active aliases\n\n")
            
            for analysis in deprecate_analyses:
                f.write(f"// Deprecate '{analysis.alias}' from {analysis.region}\n")
                f.write(f"db.pattern_libraries.updateOne(\n")
                f.write(f'  {{ "type": "geographic_entity", "term": "{analysis.region}" }},\n')
                f.write(f"  {{\n")
                f.write(f'    $addToSet: {{ "deprecated_aliases": "{analysis.alias}" }},\n')
                f.write(f'    $pull: {{ "aliases": "{analysis.alias}" }}\n')
                f.write(f"  }}\n")
                f.write(f");\n\n")
        
        logger.info(f"Generated MongoDB curation script: {script_file}")

if __name__ == "__main__":
    analyzer = AliasCurationAnalyzer()
    analyzer.run_analysis()