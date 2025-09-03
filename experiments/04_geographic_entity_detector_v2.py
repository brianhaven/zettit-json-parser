#!/usr/bin/env python3
"""
Geographic Entity Detection System v2 - Lean Pattern-Based Approach
Database-driven systematic removal solution consistent with Scripts 01-03 architecture.

Features:
1. MongoDB-driven pattern matching (926 geographic entities)
2. Priority-based processing (complex → simple patterns)
3. Comprehensive alias resolution system
4. Multi-region extraction capabilities
5. Consistent with Scripts 01-03 lean architecture

Processing Order: Run after report type extraction (03) to systematically remove geographic regions.
"""

import os
import sys
import re
import json
import logging
import importlib.util
from datetime import datetime
from typing import List, Dict, Set, Tuple, Optional
from dataclasses import dataclass
from enum import Enum
from dotenv import load_dotenv

# Dynamic import for pattern library manager
try:
    pattern_manager_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '00b_pattern_library_manager_v1.py')
    spec = importlib.util.spec_from_file_location("pattern_library_manager_v1", pattern_manager_path)
    pattern_module = importlib.util.module_from_spec(spec)
    sys.modules["pattern_library_manager_v1"] = pattern_module
    spec.loader.exec_module(pattern_module)
    PatternLibraryManager = pattern_module.PatternLibraryManager
    PatternType = pattern_module.PatternType
except Exception as e:
    raise ImportError(f"Could not import PatternLibraryManager: {e}") from e

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class GeographicExtractionResult:
    """Result object for geographic entity extraction."""
    
    def __init__(self, extracted_regions: List[str] = None, title: str = "", 
                 confidence_score: float = 0.0, processing_notes: str = ""):
        self.extracted_regions = extracted_regions or []
        self.title = title  # Standardized: changed from remaining_text to title for consistency
        self.confidence_score = confidence_score
        self.processing_notes = processing_notes

@dataclass
class GeographicPattern:
    """Geographic pattern data structure."""
    term: str
    aliases: List[str]
    priority: int
    pattern: str
    active: bool
    success_count: int = 0
    failure_count: int = 0

class GeographicEntityDetector:
    """
    Lean pattern-based geographic entity detector.
    Consistent with Scripts 01-03 database-driven architecture.
    """
    
    def __init__(self, pattern_library_manager):
        """
        Initialize with PatternLibraryManager (consistent with Scripts 01-03).
        
        Args:
            pattern_library_manager: PatternLibraryManager instance for pattern retrieval (REQUIRED)
        """
        if not pattern_library_manager:
            raise ValueError("PatternLibraryManager is required")
        
        self.pattern_library_manager = pattern_library_manager
        self.geographic_patterns: List[GeographicPattern] = []
        self.load_geographic_patterns()
    
    def load_geographic_patterns(self) -> None:
        """Load geographic patterns from MongoDB with priority ordering."""
        try:
            logger.info("Loading geographic patterns from MongoDB...")
            
            # Use PatternLibraryManager to load patterns (consistent with Scripts 01-03)
            pattern_docs = self.pattern_library_manager.get_patterns(PatternType.GEOGRAPHIC_ENTITY)
            
            self.geographic_patterns = []
            
            for pattern_doc in pattern_docs:
                pattern = GeographicPattern(
                    term=pattern_doc['term'],
                    aliases=pattern_doc.get('aliases', []),
                    priority=pattern_doc.get('priority', 999),
                    pattern=pattern_doc.get('pattern', ''),
                    active=pattern_doc.get('active', True),
                    success_count=pattern_doc.get('success_count', 0),
                    failure_count=pattern_doc.get('failure_count', 0)
                )
                
                # Build regex pattern if not provided
                if not pattern.pattern:
                    pattern.pattern = self.build_pattern_regex(pattern)
                
                self.geographic_patterns.append(pattern)
            
            # Sort patterns by priority (1 = highest), then by term length (longest first)
            # This ensures compound patterns like "Europe, Middle East and Africa" are processed
            # before individual patterns like "Europe", "Middle East", "Africa"
            self.geographic_patterns.sort(key=lambda p: (p.priority, -len(p.term)))
            
            logger.info(f"Loaded {len(self.geographic_patterns)} geographic patterns")
            logger.info(f"First 5 patterns (highest priority): {[(p.term, p.priority) for p in self.geographic_patterns[:5]]}")
            
        except Exception as e:
            logger.error(f"Error loading geographic patterns: {e}")
            self.geographic_patterns = []
    
    def build_pattern_regex(self, pattern: GeographicPattern) -> str:
        """Build regex pattern for geographic entity matching."""
        # Create pattern for main term and all aliases
        terms = [pattern.term] + pattern.aliases
        
        # Escape special regex characters and create alternatives
        escaped_terms = []
        for term in terms:
            if term and term.strip():
                # For compound patterns with commas and conjunctions, be more precise
                if ',' in term or ' and ' in term or ' & ' in term:
                    # Build exact pattern that captures the full compound structure
                    escaped_term = re.escape(term.strip())
                    # Allow for flexible spacing around punctuation
                    escaped_term = escaped_term.replace(r'\,', r'\s*,\s*')
                    escaped_term = escaped_term.replace(r'\ and\ ', r'\s+(?:and|&)\s+')
                    escaped_term = escaped_term.replace(r'\ \&\ ', r'\s*&\s*')
                    escaped_terms.append(f"\\b{escaped_term}\\b")
                else:
                    # Simple term - standard word boundary matching
                    escaped_term = re.escape(term.strip())
                    escaped_terms.append(f"\\b{escaped_term}\\b")
        
        if not escaped_terms:
            return ""
        
        # Create pattern with case-insensitive matching
        # For compound patterns, put the most specific (longest) patterns first
        escaped_terms.sort(key=len, reverse=True)
        regex_pattern = f"({'|'.join(escaped_terms)})"
        logger.debug(f"Built pattern for '{pattern.term}' (priority {pattern.priority}): {regex_pattern}")
        return regex_pattern
    
    def extract_geographic_entities(self, title: str) -> GeographicExtractionResult:
        """
        Extract geographic entities using priority-based pattern matching.
        Consistent with Scripts 01-03 systematic removal approach.
        """
        if not title or not title.strip():
            return GeographicExtractionResult(
                extracted_regions=[],
                title="",
                confidence_score=1.0,
                processing_notes="Empty input text"
            )
        
        logger.info(f"Processing text: {title[:100]}...")
        
        extracted_regions = []
        working_text = title.strip()
        processing_notes = []
        
        # Process patterns in priority order (complex → simple)
        for pattern in self.geographic_patterns:
            if not pattern.pattern or not working_text:
                continue
            
            try:
                # Case-insensitive pattern matching
                matches = re.finditer(pattern.pattern, working_text, re.IGNORECASE)
                pattern_matches = []
                
                for match in matches:
                    matched_text = match.group().strip()
                    if matched_text and len(matched_text) >= 2:
                        # Skip matches that are part of hyphenated words
                        if self.is_part_of_hyphenated_word(working_text, match):
                            logger.debug(f"Skipping '{matched_text}' - part of hyphenated word")
                            continue
                        pattern_matches.append((match, matched_text))
                
                # Process matches for this pattern
                if pattern_matches:
                    # Remove matched regions from working text (reverse order to maintain positions)
                    for match, matched_text in reversed(pattern_matches):
                        # Resolve to primary term (not alias)
                        resolved_region = self.resolve_to_primary_term(matched_text, pattern)
                        
                        if resolved_region not in extracted_regions:
                            extracted_regions.append(resolved_region)
                        
                        # Remove from working text with context cleanup
                        working_text = self.remove_match_with_cleanup(working_text, match)
                    
                    processing_notes.append(f"Pattern '{pattern.term}': {len(pattern_matches)} matches")
                    logger.debug(f"Found {len(pattern_matches)} matches for pattern: {pattern.term}")
                
            except Exception as e:
                logger.warning(f"Error processing pattern '{pattern.term}': {e}")
                continue
        
        # Calculate confidence score
        confidence_score = self.calculate_confidence_score(
            original_text=title,
            extracted_regions=extracted_regions,
            remaining_text=working_text
        )
        
        # Clean up remaining text
        working_text = self.cleanup_remaining_text(working_text)
        
        result = GeographicExtractionResult(
            extracted_regions=extracted_regions,
            title=working_text,
            confidence_score=confidence_score,
            processing_notes="; ".join(processing_notes)
        )
        
        logger.info(f"Extracted {len(extracted_regions)} regions: {extracted_regions}")
        logger.info(f"Remaining text: {working_text[:100]}...")
        
        return result
    
    def resolve_to_primary_term(self, matched_text: str, pattern: GeographicPattern) -> str:
        """Resolve alias to primary term for consistency."""
        # Check if matched text is an alias
        matched_lower = matched_text.lower()
        
        # If it's an alias, return the primary term
        for alias in pattern.aliases:
            if alias.lower() == matched_lower:
                return pattern.term
        
        # If it matches the primary term (case-insensitive), return primary term with proper case
        if pattern.term.lower() == matched_lower:
            return pattern.term
        
        # Otherwise, return the matched text as-is (preserving original case)
        return matched_text
    
    def remove_match_with_cleanup(self, text: str, match) -> str:
        """Remove matched text with surrounding punctuation and whitespace cleanup."""
        start, end = match.span()
        
        # For compound patterns, extend removal more aggressively
        extended_start = start
        extended_end = end
        
        # Look backwards for punctuation/whitespace to include in removal
        while extended_start > 0 and text[extended_start - 1] in ' ,;&-()[]{}':
            extended_start -= 1
        
        # Look forwards for punctuation/whitespace to include in removal  
        while extended_end < len(text) and text[extended_end] in ' ,;&-()[]{}':
            extended_end += 1
        
        # Check if we need to extend further for compound patterns
        # Look for dangling "and" or "&" patterns that should be included
        remaining_start = text[:extended_start].strip()
        remaining_end = text[extended_end:].strip()
        
        # If we have dangling connectors, extend the removal
        if remaining_start.endswith(('and', '&')) or remaining_end.startswith(('and', '&')):
            # Extend removal to capture compound pattern artifacts
            while extended_start > 0 and text[extended_start - 1:extended_start] not in [' ', '\t']:
                if text[extended_start - 1:extended_start + 3] == 'and' or text[extended_start - 1:extended_start] == '&':
                    extended_start -= 3 if text[extended_start - 1:extended_start + 2] == 'and' else 1
                    break
                extended_start -= 1
        
        # Remove the extended match
        cleaned_text = text[:extended_start] + " " + text[extended_end:]
        
        # Comprehensive cleanup of artifacts
        cleaned_text = re.sub(r'\s*,\s*,\s*', ', ', cleaned_text)    # Double commas
        cleaned_text = re.sub(r'\s*&\s*&\s*', ' & ', cleaned_text)   # Double ampersands  
        cleaned_text = re.sub(r'\s*,\s*and\s*,\s*', ' ', cleaned_text) # Comma-and-comma artifacts
        cleaned_text = re.sub(r'\s*and\s*and\s*', ' ', cleaned_text) # Double "and" connectors
        cleaned_text = re.sub(r'\s+', ' ', cleaned_text)             # Multiple spaces
        cleaned_text = re.sub(r'^\s*[,;&-]\s*', '', cleaned_text)    # Leading punctuation
        cleaned_text = re.sub(r'\s*[,;&-]\s*$', '', cleaned_text)    # Trailing punctuation
        cleaned_text = re.sub(r'^\s*and\s*', '', cleaned_text, flags=re.IGNORECASE) # Leading "and"
        cleaned_text = re.sub(r'\s*and\s*$', '', cleaned_text, flags=re.IGNORECASE) # Trailing "and"
        
        return cleaned_text.strip()
    
    def calculate_confidence_score(self, original_text: str, extracted_regions: List[str], 
                                 remaining_text: str) -> float:
        """Calculate confidence score for extraction quality."""
        if not original_text:
            return 1.0
        
        # Base confidence factors
        base_confidence = 0.8
        
        # Confidence boost for successful extractions
        if extracted_regions:
            extraction_boost = min(0.2, len(extracted_regions) * 0.05)
            base_confidence += extraction_boost
        
        # Confidence reduction for suspicious remaining text patterns
        suspicious_patterns = [
            r'\b(and|&)\s*$',  # Ends with dangling connector
            r'^\s*(and|&)\b',  # Starts with dangling connector
            r'\b\w{1}\b',      # Single letter words (likely artifacts)
        ]
        
        for pattern in suspicious_patterns:
            if re.search(pattern, remaining_text, re.IGNORECASE):
                base_confidence -= 0.1
        
        # Ensure confidence stays within valid range
        return max(0.0, min(1.0, base_confidence))
    
    def is_part_of_hyphenated_word(self, text: str, match) -> bool:
        """
        Check if a match is part of a hyphenated word.
        
        Examples that should be ignored:
        - "De-identified" → "De" should not match Delaware
        - "Co-operative" → "Co" should not match Colorado  
        - "Re-engineer" → "Re" should not match regions starting with "Re"
        - "Anti-bacterial" → "Anti" should not match Antigua
        
        Args:
            text: The full text being processed
            match: The regex match object
            
        Returns:
            True if the match is part of a hyphenated word, False otherwise
        """
        start, end = match.span()
        
        # Check if there's a hyphen immediately before the match
        if start > 0 and text[start-1] == '-':
            return True
        
        # Check if there's a hyphen immediately after the match
        if end < len(text) and text[end] == '-':
            return True
        
        # Additional context check: look for word boundaries with hyphens
        # Get surrounding context (up to 10 characters before and after)
        context_start = max(0, start - 10)
        context_end = min(len(text), end + 10)
        context = text[context_start:context_end]
        
        # Check if the match is surrounded by alphanumeric characters and hyphens
        # Pattern: word-Match-word or word-Match or Match-word
        match_in_context = match.group()
        context_pattern = rf'\w+-{re.escape(match_in_context)}(?:-\w+)?|\w+-{re.escape(match_in_context)}|{re.escape(match_in_context)}-\w+'
        
        if re.search(context_pattern, context, re.IGNORECASE):
            return True
        
        return False
    
    def cleanup_remaining_text(self, text: str) -> str:
        """Final cleanup of remaining text after geographic extraction."""
        if not text:
            return ""
        
        # Remove dangling connectors and artifacts
        text = re.sub(r'^\s*(and|&|,|;|-)\s*', '', text, flags=re.IGNORECASE)
        text = re.sub(r'\s*(and|&|,|;|-)\s*$', '', text, flags=re.IGNORECASE)
        
        # Clean up multiple spaces and normalize
        text = re.sub(r'\s+', ' ', text)
        
        # Remove single character artifacts
        words = text.split()
        cleaned_words = [word for word in words if len(word.strip('.,;:-()[]{}')) > 1]
        
        return ' '.join(cleaned_words).strip()

def get_timestamp():
    """Generate timestamp for Pacific Time."""
    try:
        from pytz import timezone
        pst = timezone('US/Pacific')
        utc = timezone('UTC')
        
        now_pst = datetime.now(pst)
        now_utc = datetime.now(utc)
        
        return {
            'pst': now_pst.strftime("%Y-%m-%d %H:%M:%S %Z"),
            'utc': now_utc.strftime("%Y-%m-%d %H:%M:%S %Z"),
            'filename': now_pst.strftime("%Y%m%d_%H%M%S")
        }
    except ImportError:
        # Fallback if pytz not available
        now = datetime.now()
        return {
            'pst': now.strftime("%Y-%m-%d %H:%M:%S PST"),
            'utc': now.strftime("%Y-%m-%d %H:%M:%S UTC"),
            'filename': now.strftime("%Y%m%d_%H%M%S")
        }


def create_output_directory(script_name: str) -> str:
    """Create timestamped output directory from experiments directory."""
    try:
        import pytz
        timestamp = datetime.now(pytz.timezone('America/Los_Angeles')).strftime('%Y%m%d_%H%M%S')
    except ImportError:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    output_dir = f"../outputs/{timestamp}_{script_name}"
    os.makedirs(output_dir, exist_ok=True)
    return output_dir

def test_geographic_extraction(limit=50):
    """Test the lean geographic extraction with sample data."""
    logger.info("Starting lean geographic entity extraction test...")
    
    try:
        # Initialize PatternLibraryManager (consistent with Scripts 01-03)
        pattern_lib_manager = PatternLibraryManager(os.getenv('MONGODB_URI'))
        
        # Initialize detector with PatternLibraryManager
        detector = GeographicEntityDetector(pattern_lib_manager)
        
        if not detector.geographic_patterns:
            logger.error("No geographic patterns loaded")
            return
        
        # Test with sample titles (simulating Script 03 output)
        test_cases = [
            "APAC Personal Protective Equipment",
            "North America Europe Automotive Technology", 
            "Middle East & Africa Healthcare Systems",
            "Asia Pacific and Latin America Energy Solutions",
            "Europe, Middle East and Africa Financial Services",
            "Global Semiconductor Manufacturing",
            "United States Canada Mexico Trade",
            "Southeast Asia Manufacturing Trends"
        ]
        
        timestamp = get_timestamp()
        results = []
        
        logger.info(f"Processing {len(test_cases)} test cases...")
        
        for i, test_text in enumerate(test_cases, 1):
            logger.info(f"\n--- Test Case {i}: {test_text} ---")
            
            extraction_result = detector.extract_geographic_entities(test_text)
            
            result_data = {
                'test_case': i,
                'input_text': test_text,
                'extracted_regions': extraction_result.extracted_regions,
                'remaining_text': extraction_result.remaining_text,
                'confidence_score': extraction_result.confidence_score,
                'processing_notes': extraction_result.processing_notes
            }
            
            results.append(result_data)
            
            logger.info(f"Extracted: {extraction_result.extracted_regions}")
            logger.info(f"Remaining: '{extraction_result.remaining_text}'")
            logger.info(f"Confidence: {extraction_result.confidence_score:.2f}")
        
        # Create output directory and save results
        output_dir = create_output_directory("script04_lean_test")
        
        # Save detailed results
        results_file = os.path.join(output_dir, "lean_extraction_results.json")
        with open(results_file, 'w') as f:
            json.dump({
                'timestamp_pst': timestamp['pst'],
                'timestamp_utc': timestamp['utc'],
                'test_config': {
                    'approach': 'lean_pattern_based',
                    'total_patterns': len(detector.geographic_patterns),
                    'test_cases': len(test_cases)
                },
                'results': results
            }, f, indent=2)
        
        # Generate successful extractions file for manual review
        successful_file = os.path.join(output_dir, "successful_extractions.txt")
        with open(successful_file, 'w') as f:
            f.write("Phase 4 Successful Geographic Extractions\n")
            f.write(f"Analysis Date (PDT): {timestamp['pst']}\n")
            f.write(f"Analysis Date (UTC): {timestamp['utc']}\n")
            f.write("=" * 80 + "\n\n")
            f.write(f"Total Successful Extractions: {len([r for r in results if r['extracted_regions']])}\n\n")
            
            for result in results:
                if result['extracted_regions']:
                    f.write(f"Original: {result['input_text']}\n")
                    f.write(f"Extracted Regions: {', '.join(result['extracted_regions'])}\n")
                    f.write(f"Remaining Text: {result['remaining_text']}\n")
                    f.write(f"Confidence: {result['confidence_score']:.3f}\n")
                    f.write(f"Processing Notes: {result['processing_notes']}\n")
                    f.write("-" * 40 + "\n\n")
        
        # Generate failed extractions file for manual review
        failed_file = os.path.join(output_dir, "failed_extractions.txt")
        with open(failed_file, 'w') as f:
            f.write("Phase 4 Failed Geographic Extractions\n")
            f.write(f"Analysis Date (PDT): {timestamp['pst']}\n")
            f.write(f"Analysis Date (UTC): {timestamp['utc']}\n")
            f.write("=" * 80 + "\n\n")
            
            failed_results = [r for r in results if not r['extracted_regions']]
            f.write(f"Total Failed Extractions: {len(failed_results)}\n\n")
            
            if failed_results:
                for result in failed_results:
                    f.write(f"Original: {result['input_text']}\n")
                    f.write(f"No regions extracted - remaining text: {result['remaining_text']}\n")
                    f.write(f"Confidence: {result['confidence_score']:.3f}\n")
                    f.write("-" * 40 + "\n\n")
            else:
                f.write("No failed extractions in test cases.\n")
        
        # Generate one-line extraction summary for quick scanning
        oneline_file = os.path.join(output_dir, "oneline_extractions.txt")
        with open(oneline_file, 'w') as f:
            f.write("Phase 4 Geographic Extraction One-Line Summary\n")
            f.write(f"Analysis Date (PDT): {timestamp['pst']}\n")
            f.write("=" * 80 + "\n\n")
            f.write("Format: INPUT → [REGIONS] → REMAINING\n\n")
            
            for i, result in enumerate(results, 1):
                regions = result['extracted_regions']
                remaining = result['remaining_text']
                regions_str = f"[{', '.join(regions)}]" if regions else "[None]"
                f.write(f"{i:2d}. {result['input_text']} → {regions_str} → {remaining}\n")
        
        # Generate pattern analysis file
        pattern_analysis_file = os.path.join(output_dir, "pattern_analysis.txt")
        with open(pattern_analysis_file, 'w') as f:
            f.write("Phase 4 Geographic Pattern Analysis\n")
            f.write(f"Analysis Date (PDT): {timestamp['pst']}\n")
            f.write(f"Analysis Date (UTC): {timestamp['utc']}\n")
            f.write("=" * 80 + "\n\n")
            f.write(f"Total Patterns Loaded: {len(detector.geographic_patterns)}\n")
            f.write(f"Test Cases Processed: {len(test_cases)}\n")
            f.write(f"Successful Extractions: {len([r for r in results if r['extracted_regions']])}\n")
            f.write(f"Failed Extractions: {len([r for r in results if not r['extracted_regions']])}\n\n")
            
            # Pattern priority distribution
            priority_counts = {}
            for pattern in detector.geographic_patterns:
                priority_counts[pattern.priority] = priority_counts.get(pattern.priority, 0) + 1
            
            f.write("Pattern Priority Distribution:\n")
            for priority in sorted(priority_counts.keys()):
                f.write(f"- Priority {priority}: {priority_counts[priority]} patterns\n")
            
            f.write(f"\nAverage Confidence Score: {sum(r['confidence_score'] for r in results) / len(results):.3f}\n")
            
            # High confidence extractions
            high_confidence = [r for r in results if r['confidence_score'] >= 0.90]
            f.write(f"High Confidence (≥0.90): {len(high_confidence)} cases\n")
            
            # Medium confidence extractions  
            med_confidence = [r for r in results if 0.80 <= r['confidence_score'] < 0.90]
            f.write(f"Medium Confidence (0.80-0.89): {len(med_confidence)} cases\n")
            
            # Low confidence extractions
            low_confidence = [r for r in results if r['confidence_score'] < 0.80]
            f.write(f"Low Confidence (<0.80): {len(low_confidence)} cases\n")
        
        # Generate summary report
        summary_file = os.path.join(output_dir, "summary_report.md")
        with open(summary_file, 'w') as f:
            f.write(f"""# Script 04 v2 Lean Approach Test Results

**Analysis Date (PDT):** {timestamp['pst']}  
**Analysis Date (UTC):** {timestamp['utc']}

## Test Configuration
- **Approach:** Lean Pattern-Based (consistent with Scripts 01-03)
- **Total Patterns:** {len(detector.geographic_patterns)} geographic entities
- **Test Cases:** {len(test_cases)} sample titles

## Results Summary

| Test Case | Input | Extracted Regions | Remaining Text | Confidence |
|-----------|--------|-------------------|----------------|------------|
""")
            
            for result in results:
                regions_str = ", ".join(result['extracted_regions']) if result['extracted_regions'] else "None"
                f.write(f"| {result['test_case']} | {result['input_text'][:30]}... | {regions_str} | {result['remaining_text'][:30]}... | {result['confidence_score']:.2f} |\n")
            
            f.write(f"""
## Performance Analysis
- **Total Extractions:** {sum(len(r['extracted_regions']) for r in results)}
- **Average Confidence:** {sum(r['confidence_score'] for r in results) / len(results):.2f}
- **Processing Approach:** Database-driven pattern matching
- **Architecture Consistency:** ✅ Aligned with Scripts 01-03

## Next Steps
1. Expand testing to larger dataset (500-1000 titles)
2. Compare performance with original Script 04 approach
3. Validate >96% accuracy target
4. Integrate with full pipeline (01→02→03→04)

---
**Implementation:** Claude Code AI  
**Status:** Script 04 v2 Lean Approach Initial Test ✅
""")
        
        logger.info(f"Results saved to: {output_dir}")
        logger.info(f"Lean geographic extraction test completed successfully")
        
    except Exception as e:
        logger.error(f"Error during geographic extraction test: {e}")
        raise
    finally:
        # Close PatternLibraryManager connection
        if 'pattern_lib_manager' in locals():
            pattern_lib_manager.close_connection()

if __name__ == "__main__":
    test_geographic_extraction()