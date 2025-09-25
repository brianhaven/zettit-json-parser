#!/usr/bin/env python3
"""
Geographic Entity Detection System v3 - Enhanced Regional Separator Cleanup
Database-driven systematic removal solution with cohesive regional group processing.

Enhancement for Git Issue #33: Properly handles separator words between regional entities
(e.g., "U.S. And Europe" → removes entire group including "And")

Features:
1. MongoDB-driven pattern matching (926 geographic entities)
2. Priority-based processing (complex → simple patterns)
3. Comprehensive alias resolution system
4. Multi-region extraction capabilities
5. Enhanced regional group detection with separator handling
6. Cohesive removal of regional groups including connectors

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

@dataclass
class RegionalGroup:
    """Represents a group of regional entities with separators."""
    regions: List[Tuple[int, int, str]]  # (start, end, region_name) tuples
    separators: List[Tuple[int, int, str]]  # (start, end, separator_word) tuples
    full_start: int  # Start of entire group
    full_end: int  # End of entire group
    full_text: str  # Complete text of group including separators

class GeographicEntityDetector:
    """
    Enhanced pattern-based geographic entity detector with regional group processing.
    Fixes Git Issue #33: Properly handles separator words between regional entities.
    """

    # Common separator words between regions
    REGIONAL_SEPARATORS = {'and', 'And', 'AND', '&', 'plus', 'Plus', 'PLUS', ','}

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

    def detect_regional_groups(self, text: str) -> List[RegionalGroup]:
        """
        Detect groups of regional entities connected by separator words.

        Git Issue #33 Fix: This method identifies regional groups like "U.S. And Europe"
        that should be removed as cohesive units including the separator word.

        Args:
            text: Text to analyze for regional groups

        Returns:
            List of RegionalGroup objects representing connected regions
        """
        regional_groups = []

        # Find all regional entity matches
        all_matches = []
        for pattern in self.geographic_patterns:
            try:
                matches = list(re.finditer(pattern.pattern, text, re.IGNORECASE))
                for match in matches:
                    # Skip hyphenated word parts
                    if not self.is_part_of_hyphenated_word(text, match):
                        all_matches.append((match.start(), match.end(), match.group(), pattern))
            except Exception as e:
                logger.debug(f"Error in pattern matching: {e}")
                continue

        # Sort matches by position
        all_matches.sort(key=lambda x: x[0])

        if len(all_matches) < 2:
            return regional_groups

        # Look for regional groups with separators
        i = 0
        while i < len(all_matches) - 1:
            current_match = all_matches[i]
            next_match = all_matches[i + 1]

            # Check if there's a separator between current and next match
            between_text = text[current_match[1]:next_match[0]].strip()

            # Check if the text between matches is just a separator word
            if between_text in self.REGIONAL_SEPARATORS:
                # Found a regional group!
                group_regions = [(current_match[0], current_match[1], current_match[2])]
                group_separators = [(current_match[1], next_match[0], between_text)]

                # Check if we can extend the group further
                j = i + 1
                while j < len(all_matches) - 1:
                    current = all_matches[j]
                    next = all_matches[j + 1]
                    between = text[current[1]:next[0]].strip()

                    if between in self.REGIONAL_SEPARATORS:
                        group_regions.append((current[0], current[1], current[2]))
                        group_separators.append((current[1], next[0], between))
                        j += 1
                    else:
                        break

                # Add the last region in the group
                group_regions.append((all_matches[j][0], all_matches[j][1], all_matches[j][2]))

                # Create RegionalGroup object
                full_start = group_regions[0][0]
                full_end = group_regions[-1][1]
                full_text = text[full_start:full_end]

                regional_group = RegionalGroup(
                    regions=group_regions,
                    separators=group_separators,
                    full_start=full_start,
                    full_end=full_end,
                    full_text=full_text
                )

                regional_groups.append(regional_group)

                # Skip the processed matches
                i = j + 1
            else:
                i += 1

        return regional_groups

    def extract_geographic_entities(self, title: str) -> GeographicExtractionResult:
        """
        Extract geographic entities from title with enhanced regional group processing.

        Git Issue #33 Fix: Properly removes regional groups including separator words.

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

        # First, detect and remove regional groups (Issue #33 fix)
        regional_groups = self.detect_regional_groups(working_text)

        if regional_groups:
            # Sort groups by position (reverse order for removal)
            regional_groups.sort(key=lambda x: x.full_start, reverse=True)

            for group in regional_groups:
                # Extract all regions from this group
                for region_tuple in group.regions:
                    region_name = region_tuple[2]
                    # Resolve to primary term
                    for pattern in self.geographic_patterns:
                        if re.search(pattern.pattern, region_name, re.IGNORECASE):
                            resolved_region = self.resolve_to_primary_term(region_name, pattern)
                            if resolved_region not in extracted_regions:
                                extracted_regions.append(resolved_region)
                            break

                # Remove the entire group including separators
                before = working_text[:group.full_start]
                after = working_text[group.full_end:]

                # Clean up any trailing/leading punctuation
                before = before.rstrip(' ,;-')
                after = after.lstrip(' ,;-')

                working_text = (before + " " + after).strip()

                processing_notes.append(f"Removed regional group: {group.full_text}")
                logger.debug(f"Removed regional group: {group.full_text}")

        # Now process remaining text for individual regions (not in groups)
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

                        # Remove from working text with context cleanup
                        working_text = self.remove_match_with_cleanup(working_text, match)

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

        # Clean up remaining text
        working_text = self.cleanup_remaining_text(working_text)

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

    def remove_match_with_cleanup(self, text: str, match) -> str:
        """Remove matched text with surrounding punctuation and whitespace cleanup."""
        start, end = match.span()

        # For compound patterns, extend removal more aggressively
        extended_start = start
        extended_end = end

        # Look backwards for punctuation/whitespace to include in removal
        # ISSUE #19 FIX: Remove '&' from cleanup characters to preserve ampersands in titles
        while extended_start > 0 and text[extended_start - 1] in ' ,;-()[]{}':
            extended_start -= 1

        # Look forwards for punctuation/whitespace to include in removal
        # ISSUE #19 FIX: Remove '&' from cleanup characters to preserve ampersands in titles
        while extended_end < len(text) and text[extended_end] in ' ,;-()[]{}':
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
            r'\b(and|&)\s*$',  # Ends with dangling connector
            r'^\s*(and|&)\b',  # Starts with dangling connector
            r'\b\w{1}\b',      # Single letter words (likely artifacts)
            r'\b(Plus|plus)\b',  # Leftover "Plus" separator
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
        # ISSUE #19 FIX: Only remove '&' and '+' if they're truly isolated, not between words
        # Check if '&' or '+' are between words before removing
        has_ampersand_between_words = re.search(r'\w\s*&\s*\w', text)
        has_plus_between_words = re.search(r'\w\s*\+\s*\w', text)

        # Build pattern based on what we can safely remove
        if has_ampersand_between_words and has_plus_between_words:
            # Both & and + are between words, preserve both
            text = re.sub(r'^\s*(and|,|;|-)\s*', '', text, flags=re.IGNORECASE)
            text = re.sub(r'\s*(and|,|;|-)\s*$', '', text, flags=re.IGNORECASE)
        elif has_ampersand_between_words:
            # & is between words, preserve it but + can be removed if isolated
            text = re.sub(r'^\s*(and|\+|,|;|-)\s*', '', text, flags=re.IGNORECASE)
            text = re.sub(r'\s*(and|\+|,|;|-)\s*$', '', text, flags=re.IGNORECASE)
        elif has_plus_between_words:
            # + is between words, preserve it but & can be removed if isolated
            text = re.sub(r'^\s*(and|&|,|;|-)\s*', '', text, flags=re.IGNORECASE)
            text = re.sub(r'\s*(and|&|,|;|-)\s*$', '', text, flags=re.IGNORECASE)
        else:
            # Neither & nor + are between words, safe to remove if isolated
            text = re.sub(r'^\s*(and|&|\+|,|;|-)\s*', '', text, flags=re.IGNORECASE)
            text = re.sub(r'\s*(and|&|\+|,|;|-)\s*$', '', text, flags=re.IGNORECASE)

        # Issue #28 Fix: Remove orphaned prepositions after geographic removal
        # Handles "Retail in" → "Retail" after removing "Singapore" from "Retail in Singapore"
        text = re.sub(r'\s+(in|for|by|of|at|to|with|from)\s*$', '', text, flags=re.IGNORECASE)

        # Also handle orphaned prepositions at start
        # Handles "in Technology" → "Technology"
        text = re.sub(r'^(in|for|by|of|at|to|with|from)\s+', '', text, flags=re.IGNORECASE)

        # Issue #33 Enhancement: Remove orphaned separator words
        # Remove standalone "Plus" that might remain after regional group removal
        text = re.sub(r'^\s*(Plus|plus|PLUS)\s+', '', text)
        text = re.sub(r'\s+(Plus|plus|PLUS)\s*$', '', text)

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
    """Test the enhanced geographic extraction with sample data."""
    logger.info("Starting enhanced geographic entity extraction test (v3)...")

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
            "U.S. And Europe Digital Pathology",  # Issue #33 test case
            "APAC Personal Protective Equipment",
            "North America Europe Automotive Technology",
            "Middle East & Africa Healthcare Systems",
            "Asia Pacific and Latin America Energy Solutions",
            "Europe, Middle East and Africa Financial Services",
            "Global Semiconductor Manufacturing",
            "United States Canada Mexico Trade",
            "Southeast Asia Manufacturing Trends",
            "Latin America Plus Asia Pacific Services",  # Issue #33 test case
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
        output_dir = create_output_directory("04_geographic_detector_v3_test")

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

    except Exception as e:
        logger.error(f"Test failed: {e}")
        raise

if __name__ == "__main__":
    test_geographic_extraction()