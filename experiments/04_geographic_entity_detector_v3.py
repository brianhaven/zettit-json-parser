#!/usr/bin/env python3
"""
Geographic Entity Detection System v3 - Enhanced Regional Separator Cleanup
Database-driven systematic removal solution with improved separator handling.

Git Issue #33 Fix: Enhanced cleanup to handle regional separator words that appear
between geographic entities (e.g., "U.S. And Europe" → removes "U.S.", "And", "Europe")

This is a minimal enhancement of v2 that adds smarter cleanup for separator words
without disrupting the proven priority-based pattern matching system.

Features:
1. MongoDB-driven pattern matching (926 geographic entities)
2. Priority-based processing (complex → simple patterns)
3. Comprehensive alias resolution system
4. Multi-region extraction capabilities
5. Enhanced separator word cleanup (Issue #33 fix)
6. Consistent with Scripts 01-03 lean architecture

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

# Import organized output directory manager
_spec_output = importlib.util.spec_from_file_location("output_dir_manager", os.path.join(os.path.dirname(__file__), "00c_output_directory_manager_v1.py"))
_output_module = importlib.util.module_from_spec(_spec_output)
_spec_output.loader.exec_module(_output_module)
create_organized_output_directory = _output_module.create_organized_output_directory
create_output_file_header = _output_module.create_output_file_header

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
                 confidence: float = 0.0, notes: str = ""):
        self.extracted_regions = extracted_regions or []
        self.title = title  # Standardized: changed from remaining_text to title for consistency
        self.confidence = confidence  # Standardized: changed from confidence_score to confidence
        self.notes = notes  # Standardized: changed from processing_notes to notes

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
    Enhanced pattern-based geographic entity detector with improved separator cleanup.
    Fixes Git Issue #33: Better handles separator words between regional entities.
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
            # Get geographic entity patterns from MongoDB
            patterns = self.pattern_library_manager.get_patterns(PatternType.GEOGRAPHIC_ENTITY)

            if not patterns:
                logger.warning("No geographic entity patterns found in database")
                return

            # Convert to GeographicPattern objects
            for pattern_doc in patterns:
                # Create regex pattern for matching
                term = pattern_doc.get('term', '')
                aliases = pattern_doc.get('aliases', [])

                # Build comprehensive pattern with all aliases
                pattern_parts = [re.escape(term)]
                pattern_parts.extend([re.escape(alias) for alias in aliases])

                # Create pattern with word boundaries (case-insensitive)
                pattern_regex = r'\b(?:' + '|'.join(pattern_parts) + r')\b'

                geographic_pattern = GeographicPattern(
                    term=term,
                    aliases=aliases,
                    priority=pattern_doc.get('priority', 999),
                    pattern=pattern_regex,
                    active=pattern_doc.get('active', True),
                    success_count=pattern_doc.get('success_count', 0),
                    failure_count=pattern_doc.get('failure_count', 0)
                )

                if geographic_pattern.active:
                    self.geographic_patterns.append(geographic_pattern)

            # Sort by priority (lower number = higher priority)
            self.geographic_patterns.sort(key=lambda x: x.priority)

            logger.info(f"Loaded {len(self.geographic_patterns)} geographic patterns")

            # Log first few patterns for verification
            if self.geographic_patterns:
                top_patterns = [(p.term, p.priority) for p in self.geographic_patterns[:5]]
                logger.info(f"First 5 patterns (highest priority): {top_patterns}")

        except Exception as e:
            logger.error(f"Failed to load geographic patterns: {e}")
            raise

    def extract_geographic_entities(self, title: str) -> GeographicExtractionResult:
        """
        Extract geographic entities from title with database patterns.

        Git Issue #33 Enhancement: Improved cleanup of separator words between regions.

        Args:
            title: Title text after report type extraction

        Returns:
            GeographicExtractionResult with extracted regions and cleaned title
        """
        if not title:
            return GeographicExtractionResult([], "", 1.0, "Empty input")

        logger.info(f"Processing text: {title[:100]}...")

        # Track extracted regions and processing notes
        extracted_regions = []
        processing_notes = []
        working_text = title

        # Process patterns by priority (prevents partial matches)
        for pattern in self.geographic_patterns:
            if not pattern.active:
                continue

            try:
                # Find all matches for this pattern
                pattern_matches = []
                matches = list(re.finditer(pattern.pattern, working_text, re.IGNORECASE))

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

                        # Remove from working text with enhanced cleanup
                        working_text = self.remove_match_with_enhanced_cleanup(working_text, match)

                    processing_notes.append(f"Pattern '{pattern.term}': {len(pattern_matches)} matches")
                    logger.debug(f"Found {len(pattern_matches)} matches for pattern: {pattern.term}")

            except Exception as e:
                logger.warning(f"Error processing pattern '{pattern.term}': {e}")
                continue

        # Calculate confidence score
        confidence = self.calculate_confidence_score(
            original_text=title,
            extracted_regions=extracted_regions,
            remaining_text=working_text
        )

        # Clean up remaining text with enhanced separator removal
        working_text = self.cleanup_remaining_text_enhanced(working_text)

        result = GeographicExtractionResult(
            extracted_regions=extracted_regions,
            title=working_text,
            confidence=confidence,
            notes="; ".join(processing_notes)
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

    def remove_match_with_enhanced_cleanup(self, text: str, match) -> str:
        """
        Remove matched text with enhanced cleanup for separator words.

        Git Issue #33 Enhancement: Better detection and removal of separator words
        that appear between geographic entities.
        """
        start, end = match.span()

        # Look for separator words before the match
        before_text = text[:start].rstrip()
        after_text = text[end:].lstrip()

        # Check if there's a separator word immediately before this match
        # that should be removed (e.g., "And" in "U.S. And Europe")
        separator_before_pattern = r'\b(and|And|AND|plus|Plus|PLUS)\s*$'
        separator_before_match = re.search(separator_before_pattern, before_text)

        if separator_before_match:
            # Check if this separator is between two regions
            # Look for a region pattern before the separator
            region_before_separator = False
            for pattern in self.geographic_patterns[:20]:  # Check top patterns
                if re.search(pattern.pattern + r'\s+' + separator_before_pattern,
                           text[:start], re.IGNORECASE):
                    region_before_separator = True
                    break

            if region_before_separator:
                # Remove the separator as well
                before_text = before_text[:separator_before_match.start()].rstrip()

        # Check if there's a separator word immediately after this match
        separator_after_pattern = r'^\s*(and|And|AND|plus|Plus|PLUS)\b'
        separator_after_match = re.search(separator_after_pattern, after_text)

        if separator_after_match:
            # Check if this separator is between two regions
            # Look for a region pattern after the separator
            region_after_separator = False
            remaining_after = after_text[separator_after_match.end():]
            for pattern in self.geographic_patterns[:20]:  # Check top patterns
                if re.search(r'^\s*' + pattern.pattern, remaining_after, re.IGNORECASE):
                    region_after_separator = True
                    break

            if region_after_separator:
                # Remove the separator as well
                after_text = after_text[separator_after_match.end():].lstrip()

        # Reconstruct text without the match and potentially the separators
        cleaned_text = before_text + " " + after_text

        # Standard cleanup of artifacts
        cleaned_text = re.sub(r'\s*,\s*,\s*', ', ', cleaned_text)    # Double commas
        cleaned_text = re.sub(r'\s*&\s*&\s*', ' & ', cleaned_text)   # Double ampersands
        cleaned_text = re.sub(r'\s*,\s*and\s*,\s*', ' ', cleaned_text) # Comma-and-comma artifacts
        cleaned_text = re.sub(r'\s*and\s*and\s*', ' ', cleaned_text) # Double "and" connectors
        cleaned_text = re.sub(r'\s+', ' ', cleaned_text)             # Multiple spaces

        # ISSUE #19 FIX: Don't remove & if it's between words
        if not re.search(r'\w\s*&\s*\w', cleaned_text):
            cleaned_text = re.sub(r'^\s*[,;&-]\s*', '', cleaned_text)    # Leading punctuation
            cleaned_text = re.sub(r'\s*[,;&-]\s*$', '', cleaned_text)    # Trailing punctuation
        else:
            cleaned_text = re.sub(r'^\s*[,;-]\s*', '', cleaned_text)    # Leading punctuation (preserve &)
            cleaned_text = re.sub(r'\s*[,;-]\s*$', '', cleaned_text)    # Trailing punctuation (preserve &)

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
            r'\b(and|And|AND)\s*$',  # Ends with dangling "And"
            r'^\s*(and|And|AND)\b',  # Starts with dangling "And"
            r'\b(plus|Plus|PLUS)\s*$',  # Ends with dangling "Plus"
            r'^\s*(plus|Plus|PLUS)\b',  # Starts with dangling "Plus"
            r'\b(in|In|IN)\s*$',  # Ends with dangling "In"
            r'^\s*(&)\b',  # Starts with dangling "&"
            r'\b\w{1}\b',      # Single letter words (likely artifacts)
        ]

        for pattern in suspicious_patterns:
            if re.search(pattern, remaining_text):
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

    def cleanup_remaining_text_enhanced(self, text: str) -> str:
        """
        Enhanced final cleanup of remaining text after geographic extraction.

        Git Issue #33 Enhancement: More aggressive cleanup of separator words.
        """
        if not text:
            return ""

        # Issue #33 Fix: Remove standalone separator words more aggressively
        # These patterns catch separator words that might be left between removed regions
        text = re.sub(r'^\s*(and|And|AND|plus|Plus|PLUS)\s+', '', text)  # At start
        text = re.sub(r'\s+(and|And|AND|plus|Plus|PLUS)\s*$', '', text)  # At end
        text = re.sub(r'\s+(and|And|AND|plus|Plus|PLUS)\s+', ' ', text)  # In middle (isolated)

        # Remove dangling connectors and artifacts
        # ISSUE #19 FIX: Only remove '&' and '+' if they're truly isolated, not between words
        has_ampersand_between_words = re.search(r'\w\s*&\s*\w', text)
        has_plus_between_words = re.search(r'\w\s*\+\s*\w', text)

        # Build pattern based on what we can safely remove
        if has_ampersand_between_words and has_plus_between_words:
            # Both & and + are between words, preserve both
            text = re.sub(r'^\s*(,|;|-)\s*', '', text)
            text = re.sub(r'\s*(,|;|-)\s*$', '', text)
        elif has_ampersand_between_words:
            # & is between words, preserve it but + can be removed if isolated
            text = re.sub(r'^\s*(\+|,|;|-)\s*', '', text)
            text = re.sub(r'\s*(\+|,|;|-)\s*$', '', text)
        elif has_plus_between_words:
            # + is between words, preserve it but & can be removed if isolated
            text = re.sub(r'^\s*(&|,|;|-)\s*', '', text)
            text = re.sub(r'\s*(&|,|;|-)\s*$', '', text)
        else:
            # Neither & nor + are between words, safe to remove if isolated
            text = re.sub(r'^\s*(&|\+|,|;|-)\s*', '', text)
            text = re.sub(r'\s*(&|\+|,|;|-)\s*$', '', text)

        # Issue #28 Fix: Remove orphaned prepositions after geographic removal
        text = re.sub(r'\s+(in|for|by|of|at|to|with|from)\s*$', '', text, flags=re.IGNORECASE)
        text = re.sub(r'^(in|for|by|of|at|to|with|from)\s+', '', text, flags=re.IGNORECASE)

        # Clean up multiple spaces and normalize
        text = re.sub(r'\s+', ' ', text)

        # Remove single character artifacts
        # ISSUE #19 FIX: Preserve & and + symbols even though they're single characters
        words = text.split()
        cleaned_words = [word for word in words if len(word.strip('.,;:-()[]{}')) > 1 or word in ['&', '+']]

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
    """Create organized output directory with YYYY/MM/DD structure."""
    return create_organized_output_directory(script_name)

def test_geographic_extraction(limit=50):
    """Test the enhanced geographic extraction with Issue #33 fixes."""
    logger.info("Starting enhanced geographic entity extraction test (v3 fixed)...")

    try:
        # Initialize PatternLibraryManager (consistent with Scripts 01-03)
        pattern_lib_manager = PatternLibraryManager(os.getenv('MONGODB_URI'))

        # Initialize detector with PatternLibraryManager
        detector = GeographicEntityDetector(pattern_lib_manager)

        if not detector.geographic_patterns:
            logger.error("No geographic patterns loaded")
            return

        # Test with sample titles including Issue #33 cases
        test_cases = [
            "U.S. And Europe Digital Pathology",  # Issue #33 primary test case
            "APAC Personal Protective Equipment",
            "North America Europe Automotive Technology",
            "Middle East & Africa Healthcare Systems",
            "Asia Pacific and Latin America Energy Solutions",
            "Europe, Middle East and Africa Financial Services",
            "Global Semiconductor Manufacturing",
            "United States Canada Mexico Trade",
            "Southeast Asia Manufacturing Trends",
            "Latin America Plus Asia Pacific Services",  # Issue #33 "Plus" test case
        ]

        timestamp = get_timestamp()
        results = []

        logger.info(f"Processing {len(test_cases)} test cases...")

        for i, test_text in enumerate(test_cases, 1):
            logger.info(f"\n--- Test Case {i} ---")
            logger.info(f"Input: {test_text}")

            # Extract geographic entities
            result = detector.extract_geographic_entities(test_text)

            logger.info(f"Extracted Regions: {result.extracted_regions}")
            logger.info(f"Remaining Text: {result.title}")
            logger.info(f"Confidence: {result.confidence:.3f}")

            results.append({
                'test_number': i,
                'input': test_text,
                'extracted_regions': result.extracted_regions,
                'remaining_text': result.title,
                'confidence': result.confidence,
                'notes': result.notes
            })

        # Create output directory and save results
        output_dir = create_output_directory("04_geographic_detector_v3_fixed_test")

        # Save results to JSON
        output_file = os.path.join(output_dir, f"geographic_extraction_test_results.json")
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump({
                'timestamp': timestamp,
                'total_tests': len(results),
                'results': results
            }, f, indent=2, ensure_ascii=False)

        logger.info(f"\nResults saved to: {output_file}")

        # Print summary
        logger.info(f"\n{'='*60}")
        logger.info("TEST SUMMARY")
        logger.info(f"{'='*60}")
        logger.info(f"Total test cases: {len(results)}")
        logger.info(f"Successful extractions: {sum(1 for r in results if r['extracted_regions'])}")
        logger.info(f"Average confidence: {sum(r['confidence'] for r in results) / len(results):.3f}")

        # Check Issue #33 specific cases
        issue_33_cases = {
            "U.S. And Europe Digital Pathology": "Digital Pathology",
            "Latin America Plus Asia Pacific Services": "Services"
        }

        issue_33_passed = 0
        for r in results:
            if r['input'] in issue_33_cases:
                expected = issue_33_cases[r['input']]
                if r['remaining_text'] == expected:
                    logger.info(f"✅ Issue #33 case passed: '{r['input']}' → '{r['remaining_text']}'")
                    issue_33_passed += 1
                else:
                    logger.info(f"❌ Issue #33 case failed: '{r['input']}' → '{r['remaining_text']}' (expected: '{expected}')")

        if issue_33_passed == len(issue_33_cases):
            logger.info("\n🎉 Git Issue #33 RESOLVED! All test cases passed!")
        else:
            logger.info(f"\n⚠️  Git Issue #33: {issue_33_passed}/{len(issue_33_cases)} cases passed")

    except Exception as e:
        logger.error(f"Test failed: {e}")
        raise

if __name__ == "__main__":
    test_geographic_extraction()