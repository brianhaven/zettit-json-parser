#!/usr/bin/env python3
"""
Short Alias Filtering Analysis Script

Tests context-aware short alias filtering logic against all 19,558 market research titles 
to identify false positives and validate the approach before integration into the main pipeline.

Key Goals:
1. Analyze current short alias matching problems 
2. Test proposed context-aware filtering solutions
3. Generate categorized results for manual review
4. Identify patterns that need refinement

Usage:
    python3 test_short_alias_filtering_analysis.py
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

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv()

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class ShortAliasMatch:
    """Represents a short alias match for analysis."""
    title: str
    matched_text: str
    resolved_region: str
    alias: str
    pattern_term: str
    match_start: int
    match_end: int
    context_before: str
    context_after: str
    is_valid_current: bool
    is_valid_proposed: bool
    reason_rejected: str = ""

@dataclass 
class AnalysisResults:
    """Results of short alias filtering analysis."""
    total_titles: int
    total_short_alias_matches: int
    false_positives_caught: List[ShortAliasMatch]
    legitimate_matches_preserved: List[ShortAliasMatch]
    legitimate_matches_lost: List[ShortAliasMatch]
    new_false_positives: List[ShortAliasMatch]
    unchanged_results: List[ShortAliasMatch]

class ShortAliasFilteringAnalyzer:
    """Analyzes short alias filtering logic against full dataset."""
    
    def __init__(self, mongodb_uri: str, resources_file: str):
        self.mongodb_uri = mongodb_uri
        self.resources_file = resources_file
        
        # Load geographic patterns
        self.geographic_patterns = self._load_geographic_patterns()
        self.short_alias_patterns = self._identify_short_alias_patterns()
        
        # Common English words that should never match as geographic
        self.common_words_blacklist = {
            'on', 'in', 'us', 'no', 'an', 'as', 'at', 'be', 'by', 'do', 'go',
            'he', 'if', 'is', 'it', 'me', 'of', 'or', 'so', 'to', 'we', 'up',
            'am', 'my', 'hi', 'ok', 'oh', 'ah', 'eh', 'um', 'ex', 'ad', 'id'
        }
        
        # Prepositions and articles
        self.prepositions = {
            'on', 'in', 'at', 'by', 'for', 'to', 'of', 'with', 'from', 'over',
            'under', 'above', 'below', 'through', 'across', 'between', 'among'
        }
        
        self.articles = {'a', 'an', 'the'}
        
        logger.info(f"Loaded {len(self.geographic_patterns)} total geographic patterns")
        logger.info(f"Identified {len(self.short_alias_patterns)} short alias patterns")
        logger.info(f"Common words blacklist: {len(self.common_words_blacklist)} entries")
    
    def _load_geographic_patterns(self) -> Dict:
        """Load geographic patterns from MongoDB."""
        try:
            client = MongoClient(self.mongodb_uri)
            db = client['deathstar']
            
            patterns = {}
            cursor = db.pattern_libraries.find({"type": "geographic_entity", "active": True})
            
            for pattern_doc in cursor:
                term = pattern_doc.get('term', '')
                aliases = pattern_doc.get('aliases', [])
                priority = pattern_doc.get('priority', 10)
                entity_type = pattern_doc.get('entity_type', 'unknown')
                
                if term:
                    patterns[term] = {
                        'term': term,
                        'aliases': aliases,
                        'priority': priority,
                        'entity_type': entity_type
                    }
            
            client.close()
            logger.info(f"Loaded {len(patterns)} geographic patterns from MongoDB")
            return patterns
            
        except Exception as e:
            logger.error(f"Failed to load geographic patterns: {e}")
            return {}
    
    def _identify_short_alias_patterns(self) -> Dict:
        """Identify patterns with short aliases (≤3 characters)."""
        short_patterns = {}
        
        for term, pattern_data in self.geographic_patterns.items():
            short_aliases = [alias for alias in pattern_data['aliases'] 
                           if alias and len(alias.strip()) <= 3]
            
            if short_aliases:
                short_patterns[term] = {
                    **pattern_data,
                    'short_aliases': short_aliases
                }
        
        return short_patterns
    
    def _load_market_titles(self) -> List[str]:
        """Load all market research titles from resources file (JSONL format)."""
        try:
            titles = []
            with open(self.resources_file, 'r', encoding='utf-8') as f:
                for line_num, line in enumerate(f, 1):
                    line = line.strip()
                    if not line:
                        continue
                    
                    try:
                        # Remove trailing comma if present
                        if line.endswith(','):
                            line = line[:-1]
                        
                        # Parse each line as JSON
                        item = json.loads(line)
                        
                        if isinstance(item, dict):
                            # Try different possible field names
                            title = (item.get('report_title_short') or 
                                    item.get('title') or 
                                    item.get('report_title') or
                                    item.get('name', ''))
                            if title and title.strip():
                                titles.append(title.strip())
                        elif isinstance(item, str):
                            titles.append(item.strip())
                    
                    except json.JSONDecodeError as e:
                        logger.warning(f"Failed to parse line {line_num}: {e}")
                        continue
                    
                    # Progress indicator for large files
                    if line_num % 5000 == 0:
                        logger.info(f"Processed {line_num} lines, found {len(titles)} titles...")
            
            logger.info(f"Loaded {len(titles)} titles from {self.resources_file}")
            return titles
            
        except Exception as e:
            logger.error(f"Failed to load titles from {self.resources_file}: {e}")
            return []
    
    def _extract_titles_from_object(self, obj) -> List[str]:
        """Recursively extract titles from nested object structure."""
        titles = []
        
        if isinstance(obj, dict):
            for key, value in obj.items():
                if key in ['report_title_short', 'title', 'report_title', 'name'] and isinstance(value, str):
                    titles.append(value.strip())
                elif isinstance(value, (dict, list)):
                    titles.extend(self._extract_titles_from_object(value))
        elif isinstance(obj, list):
            for item in obj:
                if isinstance(item, str):
                    titles.append(item.strip())
                elif isinstance(item, (dict, list)):
                    titles.extend(self._extract_titles_from_object(item))
        
        return titles
    
    def _find_current_matches(self, title: str) -> List[ShortAliasMatch]:
        """Find short alias matches using current logic (simple word boundaries)."""
        matches = []
        
        for term, pattern_data in self.short_alias_patterns.items():
            # Create regex pattern for all aliases (including short ones)
            all_terms = [term] + pattern_data['aliases']
            
            for alias_term in all_terms:
                if not alias_term or len(alias_term.strip()) > 3:
                    continue
                
                # Current logic: simple word boundaries
                pattern = rf'\b{re.escape(alias_term.strip())}\b'
                
                for match in re.finditer(pattern, title, re.IGNORECASE):
                    start, end = match.span()
                    matched_text = match.group().strip()
                    
                    # Get context
                    context_start = max(0, start - 20)
                    context_end = min(len(title), end + 20)
                    context_before = title[context_start:start]
                    context_after = title[end:context_end]
                    
                    matches.append(ShortAliasMatch(
                        title=title,
                        matched_text=matched_text,
                        resolved_region=term,  # Primary term
                        alias=alias_term,
                        pattern_term=term,
                        match_start=start,
                        match_end=end,
                        context_before=context_before,
                        context_after=context_after,
                        is_valid_current=True,  # Current logic accepts all word-boundary matches
                        is_valid_proposed=False,  # Will be determined by proposed logic
                        reason_rejected=""
                    ))
        
        return matches
    
    def _apply_proposed_filtering(self, match: ShortAliasMatch) -> bool:
        """Apply proposed context-aware filtering logic."""
        matched_lower = match.matched_text.lower().strip()
        
        # Layer 1: Common words blacklist
        if matched_lower in self.common_words_blacklist:
            match.reason_rejected = f"Common word blacklist: '{matched_lower}'"
            return False
        
        # Layer 2: Preposition context detection
        if self._is_preposition_context(match):
            match.reason_rejected = f"Preposition context detected"
            return False
        
        # Layer 3: Article context detection  
        if self._is_article_context(match):
            match.reason_rejected = f"Article context detected"
            return False
        
        # Layer 4: Mid-sentence lowercase context
        if self._is_suspicious_lowercase_context(match):
            match.reason_rejected = f"Suspicious lowercase mid-sentence context"
            return False
        
        # Layer 5: Pattern validation for very short matches
        if len(matched_lower) <= 2 and self._is_suspicious_very_short_match(match):
            match.reason_rejected = f"Suspicious very short match context"
            return False
        
        return True
    
    def _is_preposition_context(self, match: ShortAliasMatch) -> bool:
        """Check if match appears to be in preposition context."""
        matched_lower = match.matched_text.lower().strip()
        
        if matched_lower not in self.prepositions:
            return False
        
        # Look for patterns like "Spending on Core", "Focus in Technology"
        before_words = match.context_before.strip().split()
        after_words = match.context_after.strip().split()
        
        # Check if preceded by typical preposition-using verbs
        preposition_verbs = {
            'spending', 'focus', 'focusing', 'specializing', 'based', 'located',
            'operating', 'working', 'engaged', 'involved', 'participating'
        }
        
        if before_words and before_words[-1].lower() in preposition_verbs:
            return True
        
        # Check if followed by non-geographic nouns
        non_geographic_nouns = {
            'core', 'administration', 'healthcare', 'technology', 'development',
            'research', 'analysis', 'management', 'services', 'solutions'
        }
        
        if after_words and after_words[0].lower() in non_geographic_nouns:
            return True
        
        return False
    
    def _is_article_context(self, match: ShortAliasMatch) -> bool:
        """Check if match appears to be an article."""
        matched_lower = match.matched_text.lower().strip()
        
        if matched_lower not in self.articles:
            return False
        
        # Articles are usually followed by nouns, not geographic context
        after_words = match.context_after.strip().split()
        
        # If followed by common business nouns, likely an article
        business_nouns = {
            'market', 'industry', 'analysis', 'report', 'study', 'research',
            'solution', 'service', 'product', 'system', 'technology', 'platform'
        }
        
        if after_words and after_words[0].lower() in business_nouns:
            return True
        
        return False
    
    def _is_suspicious_lowercase_context(self, match: ShortAliasMatch) -> bool:
        """Check if lowercase match in middle of sentence is suspicious."""
        if not match.matched_text.islower():
            return False
        
        # Check if it's in the middle of the sentence (not at start)
        before_text = match.context_before.strip()
        if not before_text:
            return False  # At start of text, could be legitimate
        
        # Look for sentence-like context
        title_words = match.title.split()
        match_word_index = None
        
        for i, word in enumerate(title_words):
            if match.matched_text.lower() in word.lower():
                match_word_index = i
                break
        
        if match_word_index is None:
            return False
        
        # If in middle 50% of title and lowercase, more suspicious
        if 0.25 < (match_word_index / len(title_words)) < 0.75:
            return True
        
        return False
    
    def _is_suspicious_very_short_match(self, match: ShortAliasMatch) -> bool:
        """Additional validation for 1-2 character matches."""
        matched_lower = match.matched_text.lower().strip()
        
        # Single letters are very suspicious unless clearly geographic
        if len(matched_lower) == 1:
            return True
        
        # Two-letter matches need more context validation
        if len(matched_lower) == 2:
            # Check if surrounded by non-geographic context
            context_words = (match.context_before + " " + match.context_after).lower().split()
            
            business_context_words = {
                'market', 'industry', 'analysis', 'report', 'technology', 'healthcare',
                'spending', 'administration', 'management', 'services', 'solutions',
                'research', 'development', 'innovation', 'strategy', 'operations'
            }
            
            # If surrounded primarily by business terms, suspicious
            business_word_count = sum(1 for word in context_words if word in business_context_words)
            
            if business_word_count >= 2:
                return True
        
        return False
    
    def analyze_titles(self, titles: List[str]) -> AnalysisResults:
        """Analyze all titles and categorize results."""
        logger.info(f"Analyzing {len(titles)} titles for short alias matches...")
        
        false_positives_caught = []
        legitimate_matches_preserved = []
        legitimate_matches_lost = []
        new_false_positives = []
        unchanged_results = []
        
        total_short_alias_matches = 0
        
        for i, title in enumerate(titles):
            if i % 1000 == 0:
                logger.info(f"Processed {i}/{len(titles)} titles...")
            
            current_matches = self._find_current_matches(title)
            total_short_alias_matches += len(current_matches)
            
            for match in current_matches:
                # Apply proposed filtering
                match.is_valid_proposed = self._apply_proposed_filtering(match)
                
                # Categorize the result
                if match.is_valid_current and not match.is_valid_proposed:
                    # Current logic accepted, proposed rejected
                    if self._is_likely_false_positive(match):
                        false_positives_caught.append(match)
                    else:
                        legitimate_matches_lost.append(match)
                
                elif not match.is_valid_current and match.is_valid_proposed:
                    # This shouldn't happen with current logic setup
                    new_false_positives.append(match)
                
                elif match.is_valid_current and match.is_valid_proposed:
                    # Both accept - preserved
                    legitimate_matches_preserved.append(match)
                
                else:
                    # Both reject - unchanged
                    unchanged_results.append(match)
        
        return AnalysisResults(
            total_titles=len(titles),
            total_short_alias_matches=total_short_alias_matches,
            false_positives_caught=false_positives_caught,
            legitimate_matches_preserved=legitimate_matches_preserved,
            legitimate_matches_lost=legitimate_matches_lost,
            new_false_positives=new_false_positives,
            unchanged_results=unchanged_results
        )
    
    def _is_likely_false_positive(self, match: ShortAliasMatch) -> bool:
        """Heuristic to determine if a match is likely a false positive."""
        # This is a manual evaluation helper
        # For this analysis, we'll be conservative and mark matches as suspicious
        # based on context patterns we've identified
        
        matched_lower = match.matched_text.lower().strip()
        
        # Known problematic patterns
        if matched_lower in self.common_words_blacklist:
            return True
        
        # Check for business/technical context
        full_context = (match.context_before + " " + match.context_after).lower()
        
        business_indicators = [
            'spending', 'administration', 'management', 'technology', 'healthcare',
            'research', 'development', 'analysis', 'solutions', 'services'
        ]
        
        for indicator in business_indicators:
            if indicator in full_context:
                return True
        
        return False
    
    def generate_analysis_reports(self, results: AnalysisResults, output_dir: str):
        """Generate comprehensive analysis reports."""
        os.makedirs(output_dir, exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S PDT')
        
        # 1. Summary Report
        summary_file = os.path.join(output_dir, "short_alias_analysis_summary.txt")
        with open(summary_file, 'w') as f:
            f.write("Short Alias Filtering Analysis Summary\n")
            f.write(f"Analysis Date: {timestamp}\n")
            f.write("=" * 60 + "\n\n")
            
            f.write(f"Dataset: {results.total_titles:,} titles analyzed\n")
            f.write(f"Total short alias matches found: {results.total_short_alias_matches:,}\n\n")
            
            f.write("RESULTS BREAKDOWN:\n")
            f.write(f"  False Positives Caught: {len(results.false_positives_caught):,} (GOOD)\n")
            f.write(f"  Legitimate Matches Preserved: {len(results.legitimate_matches_preserved):,} (GOOD)\n")
            f.write(f"  Legitimate Matches Lost: {len(results.legitimate_matches_lost):,} (NEEDS TUNING)\n")
            f.write(f"  New False Positives: {len(results.new_false_positives):,} (BAD)\n")
            f.write(f"  Unchanged Results: {len(results.unchanged_results):,} (NEUTRAL)\n\n")
            
            # Calculate effectiveness
            total_improvements = len(results.false_positives_caught)
            total_regressions = len(results.legitimate_matches_lost) + len(results.new_false_positives)
            
            f.write("EFFECTIVENESS METRICS:\n")
            f.write(f"  Improvements: {total_improvements:,}\n")
            f.write(f"  Regressions: {total_regressions:,}\n")
            f.write(f"  Net Benefit: {total_improvements - total_regressions:,}\n")
            
            if results.total_short_alias_matches > 0:
                improvement_rate = (total_improvements / results.total_short_alias_matches) * 100
                f.write(f"  Improvement Rate: {improvement_rate:.1f}%\n")
        
        # 2. False Positives Caught (Good Results)
        fp_file = os.path.join(output_dir, "false_positives_caught.txt")
        with open(fp_file, 'w') as f:
            f.write("False Positives Successfully Caught by New Logic\n")
            f.write(f"Analysis Date: {timestamp}\n")
            f.write("=" * 60 + "\n\n")
            f.write(f"Total: {len(results.false_positives_caught)} cases\n\n")
            
            # Group by reason
            reason_groups = defaultdict(list)
            for match in results.false_positives_caught:
                reason_groups[match.reason_rejected].append(match)
            
            for reason, matches in reason_groups.items():
                f.write(f"\n{reason.upper()} ({len(matches)} cases):\n")
                f.write("-" * 40 + "\n")
                for match in matches[:10]:  # Show first 10 examples
                    f.write(f"  '{match.matched_text}' in: {match.title}\n")
                    f.write(f"    Would resolve to: {match.resolved_region}\n")
                    f.write(f"    Context: ...{match.context_before}[{match.matched_text}]{match.context_after}...\n\n")
                if len(matches) > 10:
                    f.write(f"    ... and {len(matches) - 10} more similar cases\n\n")
        
        # 3. Legitimate Matches Lost (Problems to Fix)
        lost_file = os.path.join(output_dir, "legitimate_matches_lost.txt")
        with open(lost_file, 'w') as f:
            f.write("Legitimate Matches Lost by New Logic (NEEDS ATTENTION)\n")
            f.write(f"Analysis Date: {timestamp}\n")
            f.write("=" * 60 + "\n\n")
            f.write(f"Total: {len(results.legitimate_matches_lost)} cases\n\n")
            
            if results.legitimate_matches_lost:
                f.write("These are potentially valid geographic matches that the new logic incorrectly rejects:\n\n")
                
                for match in results.legitimate_matches_lost:
                    f.write(f"LOST: '{match.matched_text}' -> {match.resolved_region}\n")
                    f.write(f"  Title: {match.title}\n") 
                    f.write(f"  Reason Rejected: {match.reason_rejected}\n")
                    f.write(f"  Context: ...{match.context_before}[{match.matched_text}]{match.context_after}...\n\n")
            else:
                f.write("✅ No legitimate matches lost! This is excellent.\n")
        
        # 4. Pattern Frequency Analysis
        freq_file = os.path.join(output_dir, "short_alias_frequency_analysis.txt")
        with open(freq_file, 'w') as f:
            f.write("Short Alias Pattern Frequency Analysis\n")
            f.write(f"Analysis Date: {timestamp}\n")
            f.write("=" * 60 + "\n\n")
            
            # Count matches by alias
            alias_counter = Counter()
            region_counter = Counter()
            
            all_matches = (results.false_positives_caught + results.legitimate_matches_preserved + 
                          results.legitimate_matches_lost + results.new_false_positives)
            
            for match in all_matches:
                alias_counter[match.alias.lower()] += 1
                region_counter[match.resolved_region] += 1
            
            f.write("MOST PROBLEMATIC ALIASES:\n")
            for alias, count in alias_counter.most_common(20):
                f.write(f"  '{alias}': {count:,} matches\n")
            
            f.write(f"\nMOST MATCHED REGIONS:\n")
            for region, count in region_counter.most_common(20):
                f.write(f"  '{region}': {count:,} matches\n")
        
        # 5. Sample Preserved Matches (for validation)
        preserved_file = os.path.join(output_dir, "legitimate_matches_preserved_sample.txt")
        with open(preserved_file, 'w') as f:
            f.write("Sample of Legitimate Matches Preserved (for validation)\n")
            f.write(f"Analysis Date: {timestamp}\n")
            f.write("=" * 60 + "\n\n")
            f.write(f"Total preserved: {len(results.legitimate_matches_preserved)}\n")
            f.write("Showing first 50 examples:\n\n")
            
            for match in results.legitimate_matches_preserved[:50]:
                f.write(f"✅ '{match.matched_text}' -> {match.resolved_region}\n")
                f.write(f"    Title: {match.title}\n")
                f.write(f"    Context: ...{match.context_before}[{match.matched_text}]{match.context_after}...\n\n")
        
        logger.info(f"Analysis reports generated in: {output_dir}")

def main():
    """Run the short alias filtering analysis."""
    logger.info("Starting Short Alias Filtering Analysis")
    
    # Configuration
    mongodb_uri = os.getenv('MONGODB_URI')
    if not mongodb_uri:
        logger.error("MONGODB_URI environment variable not set")
        return
    
    # Use resources file 
    script_dir = os.path.dirname(os.path.abspath(__file__))
    experiments_dir = os.path.dirname(script_dir)
    project_root = os.path.dirname(experiments_dir)
    resources_file = os.path.join(project_root, 'resources', 'deathstar.markets_raw_collapsed.json')
    
    if not os.path.exists(resources_file):
        logger.error(f"Resources file not found: {resources_file}")
        return
    
    # Create analyzer
    analyzer = ShortAliasFilteringAnalyzer(mongodb_uri, resources_file)
    
    # Load titles
    titles = analyzer._load_market_titles()
    if not titles:
        logger.error("No titles loaded from resources file")
        return
    
    logger.info(f"Loaded {len(titles)} titles for analysis")
    
    # Run analysis
    results = analyzer.analyze_titles(titles)
    
    # Generate reports
    output_dir = os.path.join(project_root, 'outputs', f"short_alias_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
    analyzer.generate_analysis_reports(results, output_dir)
    
    logger.info("Short alias filtering analysis completed!")
    logger.info(f"Results saved to: {output_dir}")
    
    # Print summary
    print(f"\n🔍 SHORT ALIAS FILTERING ANALYSIS COMPLETE")
    print(f"📊 Dataset: {results.total_titles:,} titles")
    print(f"🎯 Total short alias matches: {results.total_short_alias_matches:,}")
    print(f"✅ False positives caught: {len(results.false_positives_caught):,}")
    print(f"⚠️  Legitimate matches lost: {len(results.legitimate_matches_lost):,}")
    print(f"💾 Results saved to: {output_dir}")

if __name__ == "__main__":
    main()