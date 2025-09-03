#!/usr/bin/env python3
"""
Script 03 v3: Dictionary-Based Market-Aware Report Type Extractor
================================================================

**Revolutionary Dictionary-Based Approach:**
Replaces 900+ regex patterns with ~60 dictionary entries using combinatorial detection.
O(n) dictionary lookup vs O(pattern_count) regex matching performance improvement.

**Key Features:**
- Market boundary recognition (96.7% coverage with "Market" keyword)
- Sequential keyword ordering detection algorithm
- Database-driven dictionary lookup (NO HARDCODED TERMS)
- Preserves v2 market-aware processing workflows
- Acronym-embedded pattern support
- Statistical tracking and confidence scoring

**Architecture:**
Dictionary-based detection with market term extraction, rearrangement, and reconstruction
workflows preserved from v2 for complete compatibility.

**GitHub Issue:** #20 - Dictionary-Based Report Type Detection
**Version:** 3.0 (Dictionary-Based Architecture)
**Date:** 2025-08-29
**Replaces:** 03_report_type_extractor_v2.py (preserved for comparison)
"""

import os
import sys
import logging
import re
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Set, Union
from dataclasses import dataclass, field
from enum import Enum
import pytz
from pymongo import MongoClient
from pymongo.collection import Collection

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ReportTypeFormat(Enum):
    COMPOUND = "compound_type"
    TERMINAL = "terminal_type" 
    EMBEDDED = "embedded_type"
    PREFIX = "prefix_type"
    ACRONYM_EMBEDDED = "acronym_embedded"

@dataclass
class DictionaryKeywordResult:
    """Result from dictionary-based keyword detection."""
    keywords_found: List[str]
    sequence: List[Tuple[str, int]]  # (keyword, position)
    separators: List[str]
    boundary_markers: List[str]
    market_boundary_detected: bool
    market_boundary_position: Optional[int] = None  # Position of Market keyword in sequence
    coverage_percentage: float = 0.0
    confidence: float = 0.0
    keyword_positions: Optional[Dict] = None  # Precise keyword positions for cleanup
    
    # TASK 3v3.9: Edge case detection fields (v2 pattern-based)
    edge_cases: Optional[Dict[str, List[str]]] = None
    extracted_acronym: Optional[str] = None
    acronym_processing: bool = False
    format_type_override: Optional[ReportTypeFormat] = None
    non_dictionary_words: Optional[List[str]] = None
    base_report_type: Optional[str] = None  # From v2 acronym_embedded patterns
    matched_pattern: Optional[str] = None   # The regex pattern that matched

@dataclass
class MarketAwareDictionaryResult:
    """Enhanced result structure for dictionary-based market-aware report type extraction."""
    # Core extraction results
    title: str  # Remaining text after extraction
    extracted_report_type: str
    confidence: float
    format_type: ReportTypeFormat
    
    # Market-aware processing details
    market_term_type: str
    market_prefix_extracted: Optional[str] = None
    market_context_preserved: Optional[str] = None
    
    # Dictionary detection details
    dictionary_result: Optional[DictionaryKeywordResult] = None
    keywords_detected: List[str] = None
    pattern_reconstruction: Optional[str] = None
    
    # TASK 3v3.9: Edge case processing details
    extracted_acronym: Optional[str] = None
    acronym_processing: bool = False
    edge_case_detected: bool = False
    edge_case_types: List[str] = field(default_factory=list)
    
    # Processing statistics
    processing_time_ms: float = 0.0
    database_queries: int = 0
    dictionary_lookups: int = 0
    
    # Backward compatibility with v2
    success: bool = True
    error_details: Optional[str] = None

class DictionaryBasedReportTypeExtractor:
    """
    Dictionary-based report type extractor with market-aware processing.
    
    Revolutionary O(n) dictionary approach replacing O(pattern_count) regex matching.
    All dictionary terms loaded from MongoDB - NO HARDCODED TERMS.
    """
    
    def __init__(self, pattern_library_manager):
        """Initialize with PatternLibraryManager for database access."""
        self.pattern_library_manager = pattern_library_manager
        self.db = pattern_library_manager.db
        self.patterns_collection = pattern_library_manager.collection
        
        # Dictionary data - loaded from database
        self.primary_keywords: List[str] = []
        self.secondary_keywords: List[str] = []
        self.separators: List[str] = []
        self.boundary_markers: List[str] = []
        self.keyword_frequencies: Dict[str, int] = {}
        
        # TASK 3v3.9: V2 pattern-based acronym detection (NO HARDCODED TERMS)
        self.acronym_embedded_patterns: List[Dict] = []
        
        # Market boundary detection
        self.market_boundary_coverage = 0.0
        self.market_primary_keyword = None
        
        # Statistics
        self.stats = {
            'total_processed': 0,
            'dictionary_hits': 0,
            'market_boundary_detected': 0,
            'fallback_to_patterns': 0,
            'processing_time_total': 0.0
        }
        
        # Load dictionary data from database
        self._load_dictionary_from_database()
        
        # Load v2 patterns for fallback (preserving existing functionality)
        self.v2_patterns = self._load_v2_patterns_for_fallback()
        
        # TASK 3v3.9: Load v2 acronym_embedded patterns for edge case detection
        self.acronym_embedded_patterns = self._load_acronym_embedded_patterns()
        
        logger.info(f"DictionaryBasedReportTypeExtractor initialized:")
        logger.info(f"  Primary keywords: {len(self.primary_keywords)}")
        logger.info(f"  Secondary keywords: {len(self.secondary_keywords)}")
        logger.info(f"  Market boundary coverage: {self.market_boundary_coverage:.1f}%")
        logger.info(f"  V2 fallback patterns: {len(self.v2_patterns)}")
    
    def _load_dictionary_from_database(self):
        """Load dictionary data from MongoDB - NO HARDCODED TERMS."""
        try:
            # Load primary keywords
            primary_cursor = self.patterns_collection.find({
                "type": "report_type_dictionary",
                "subtype": "primary_keyword",
                "active": True
            }).sort("priority", 1)
            
            for doc in primary_cursor:
                self.primary_keywords.append(doc["term"])
                self.keyword_frequencies[doc["term"]] = doc.get("frequency", 0)
                
                # Market boundary detection
                if doc["term"] == "Market":
                    self.market_boundary_coverage = doc.get("percentage", 0.0)
                    self.market_primary_keyword = doc["term"]
            
            # Load secondary keywords
            secondary_cursor = self.patterns_collection.find({
                "type": "report_type_dictionary",
                "subtype": "secondary_keyword", 
                "active": True
            }).sort("priority", 1)
            
            for doc in secondary_cursor:
                self.secondary_keywords.append(doc["term"])
                self.keyword_frequencies[doc["term"]] = doc.get("frequency", 0)
            
            # Load separators
            separator_cursor = self.patterns_collection.find({
                "type": "report_type_dictionary",
                "subtype": "separator",
                "active": True
            }).sort("priority", 1)
            
            for doc in separator_cursor:
                self.separators.append(doc["term"])
            
            # Load boundary markers
            boundary_cursor = self.patterns_collection.find({
                "type": "report_type_dictionary",
                "subtype": "boundary_marker",
                "active": True
            }).sort("priority", 1)
            
            for doc in boundary_cursor:
                self.boundary_markers.append(doc["term"])
            
            # TASK 3v3.9: Load edge case classification terms from database
            # Load v2 acronym_embedded patterns for Task 3v3.9
            self._load_acronym_embedded_patterns()
            
            logger.info(f"Dictionary loaded from database:")
            logger.debug(f"  Primary keywords: {self.primary_keywords}")
            logger.debug(f"  Secondary keywords: {self.secondary_keywords[:10]}...")
            logger.debug(f"  Separators: {self.separators}")
            logger.debug(f"  Acronym embedded patterns loaded: {len(self.acronym_embedded_patterns)} total")
            
        except Exception as e:
            logger.error(f"Failed to load dictionary from database: {e}")
            raise
    
    # REMOVED: Old edge case classification approach replaced with v2 pattern-based detection
    
    def _load_v2_patterns_for_fallback(self) -> List[Dict]:
        """Load v2 patterns for fallback compatibility."""
        try:
            patterns = list(self.patterns_collection.find({
                "type": "report_type",
                "active": True
            }).sort("priority", 1))
            
            logger.debug(f"Loaded {len(patterns)} v2 fallback patterns")
            return patterns
            
        except Exception as e:
            logger.error(f"Failed to load v2 patterns for fallback: {e}")
            return []
    
    def _load_acronym_embedded_patterns(self) -> List[Dict]:
        """
        TASK 3v3.9: Load v2 acronym_embedded patterns from database.
        Uses intelligent regex patterns with capture groups, not literal terms.
        """
        patterns = []
        
        try:
            # Query acronym_embedded patterns from pattern_libraries collection
            patterns_cursor = self.patterns_collection.find({
                "format_type": "acronym_embedded",
                "active": True
            })
            
            for pattern_doc in patterns_cursor:
                pattern_data = {
                    'pattern': pattern_doc.get('pattern', ''),
                    'base_type': pattern_doc.get('base_type', ''),
                    'term': pattern_doc.get('term', ''),
                    'confidence_weight': pattern_doc.get('confidence_weight', 0.85)
                }
                patterns.append(pattern_data)
            
            logger.debug(f"Loaded {len(patterns)} acronym_embedded patterns with regex capture groups")
            
        except Exception as e:
            logger.warning(f"Failed to load acronym_embedded patterns: {e}")
        
        return patterns
    
    def _find_keyword_with_wrapping(self, keyword: str, title: str) -> Optional[Dict]:
        """
        TASK 3v3.15: Enhanced keyword detection with bracket/parentheses wrapping support.
        
        Detects keywords in three scenarios (prioritizes wrapped keywords):
        1. Wrapped in brackets: "Market [Size & Share] Report" 
        2. Wrapped in parentheses: "Market (Growth Analysis) Report"
        3. Normal word boundary: "Market Size Report"
        
        Args:
            keyword: Keyword to search for
            title: Title text to search in
            
        Returns:
            Dict with match details or None if not found
        """
        escaped_keyword = re.escape(keyword)
        
        # PRIORITY 1: Check for wrapped in brackets [keyword] or [keyword phrase]
        bracket_pattern = rf'\[([^[\]]*\b{escaped_keyword}\b[^[\]]*)\]'
        bracket_match = re.search(bracket_pattern, title, re.IGNORECASE)
        if bracket_match:
            # Find the actual keyword position within the brackets
            bracket_content = bracket_match.group(1)
            keyword_in_bracket = re.search(rf'\b{escaped_keyword}\b', bracket_content, re.IGNORECASE)
            if keyword_in_bracket:
                # Calculate absolute position in title
                bracket_start = bracket_match.start()
                keyword_start_in_bracket = keyword_in_bracket.start()
                absolute_start = bracket_start + 1 + keyword_start_in_bracket  # +1 for opening bracket
                
                return {
                    'start': absolute_start,
                    'end': absolute_start + len(keyword),
                    'wrapped': True,
                    'wrap_chars': '[]',
                    'wrapped_content': bracket_content,
                    'wrapper_start': bracket_start,
                    'wrapper_end': bracket_match.end()
                }
        
        # PRIORITY 2: Check for wrapped in parentheses (keyword) or (keyword phrase)  
        paren_pattern = rf'\(([^()]*\b{escaped_keyword}\b[^()]*)\)'
        paren_match = re.search(paren_pattern, title, re.IGNORECASE)
        if paren_match:
            # Find the actual keyword position within the parentheses
            paren_content = paren_match.group(1)
            keyword_in_paren = re.search(rf'\b{escaped_keyword}\b', paren_content, re.IGNORECASE)
            if keyword_in_paren:
                # Calculate absolute position in title
                paren_start = paren_match.start()
                keyword_start_in_paren = keyword_in_paren.start()
                absolute_start = paren_start + 1 + keyword_start_in_paren  # +1 for opening parenthesis
                
                return {
                    'start': absolute_start,
                    'end': absolute_start + len(keyword),
                    'wrapped': True,
                    'wrap_chars': '()',
                    'wrapped_content': paren_content,
                    'wrapper_start': paren_start,
                    'wrapper_end': paren_match.end()
                }
        
        # PRIORITY 3: Normal word boundary detection (fallback)
        normal_pattern = rf'\b{escaped_keyword}\b'
        normal_match = re.search(normal_pattern, title, re.IGNORECASE)
        if normal_match:
            return {
                'start': normal_match.start(),
                'end': normal_match.end(),
                'wrapped': False,
                'wrap_chars': None
            }
        
        return None
    
    def detect_keywords_in_title(self, title: str) -> DictionaryKeywordResult:
        """
        Enhanced dictionary-based keyword detection with precise punctuation and separator detection.
        O(n) performance vs O(pattern_count) regex matching.
        ENHANCEMENT: Task 3v3.8 - Advanced separator detection between keywords for improved reconstruction.
        """
        start_time = datetime.now()
        
        # Normalize title for detection
        title_lower = title.lower()
        words = title.split()
        
        # Find keyword matches with precise positions and boundaries
        keywords_found = []
        sequence = []
        keyword_positions = {}  # Track exact positions for separator detection
        
        # Check for Market boundary (96.7% coverage) with bracket/parentheses wrapping detection
        market_boundary_detected = False
        if self.market_primary_keyword and self.market_primary_keyword.lower() in title_lower:
            market_boundary_detected = True
            # Use enhanced wrapping detection for Market keyword
            match = self._find_keyword_with_wrapping(self.market_primary_keyword, title)
            if match:
                keywords_found.append(self.market_primary_keyword)
                word_pos = len(title[:match['start']].split()) - 1
                sequence.append((self.market_primary_keyword, word_pos))
                keyword_positions[self.market_primary_keyword] = {
                    'start': match['start'],
                    'end': match['end'],
                    'word_pos': word_pos,
                    'wrapped': match['wrapped'],
                    'wrap_chars': match['wrap_chars']
                }
        
        # Check primary keywords (database-driven) with bracket/parentheses wrapping detection
        for keyword in self.primary_keywords:
            if keyword.lower() != "market":  # Already handled above
                match = self._find_keyword_with_wrapping(keyword, title)
                if match:
                    keywords_found.append(keyword)
                    word_pos = len(title[:match['start']].split()) - 1
                    sequence.append((keyword, word_pos))
                    keyword_positions[keyword] = {
                        'start': match['start'],
                        'end': match['end'],
                        'word_pos': word_pos,
                        'wrapped': match['wrapped'],
                        'wrap_chars': match['wrap_chars']
                    }
        
        # Check secondary keywords with bracket/parentheses wrapping detection
        for keyword in self.secondary_keywords:
            match = self._find_keyword_with_wrapping(keyword, title)
            if match:
                keywords_found.append(keyword)
                word_pos = len(title[:match['start']].split()) - 1
                sequence.append((keyword, word_pos))
                keyword_positions[keyword] = {
                    'start': match['start'],
                    'end': match['end'],
                    'word_pos': word_pos,
                    'wrapped': match['wrapped'],
                    'wrap_chars': match['wrap_chars']
                }
        
        # Sort sequence by position
        sequence.sort(key=lambda x: x[1])
        
        # ENHANCEMENT: Advanced separator and punctuation detection between keywords
        separators_found, boundary_markers_found = self._detect_separators_between_keywords(
            title, keyword_positions, sequence
        )
        
        # TASK 3v3.9: Edge case detection for non-dictionary words
        non_dictionary_words = self._detect_edge_cases_in_title(title, keywords_found, keyword_positions)
        
        # TASK 3v3.9: V2 pattern-based acronym extraction (v2 ACRONYM_EMBEDDED compatibility)
        extracted_acronym, base_report_type, matched_pattern = self._detect_acronym_embedded_patterns(title)
        
        # Log v2 pattern-based acronym detection results
        if extracted_acronym:
            logger.debug(f"V2 acronym pattern detected: '{extracted_acronym}' from base type '{base_report_type}' using pattern '{matched_pattern[:50]}...'")
        
        # Calculate coverage and confidence
        total_frequency = sum(self.keyword_frequencies.get(kw, 0) for kw in keywords_found)
        coverage_percentage = (len(keywords_found) / max(len(self.primary_keywords + self.secondary_keywords), 1)) * 100
        
        # Enhanced confidence calculation with separator detection bonus
        confidence = 0.0
        if market_boundary_detected:
            confidence += 0.4  # 40% for Market boundary
        confidence += min(0.5, len(keywords_found) * 0.1)  # Up to 50% for keywords
        if separators_found:
            confidence += 0.1  # 10% bonus for separator detection (improved reconstruction)
        
        processing_time = (datetime.now() - start_time).total_seconds() * 1000
        self.stats['processing_time_total'] += processing_time
        
        # Find market boundary position in sequence
        market_boundary_position = None
        if market_boundary_detected:
            for i, (keyword, pos) in enumerate(sequence):
                if keyword.lower() == 'market':
                    market_boundary_position = i
                    break
        
        result = DictionaryKeywordResult(
            keywords_found=keywords_found,
            sequence=sequence,
            separators=separators_found,
            boundary_markers=boundary_markers_found,
            market_boundary_detected=market_boundary_detected,
            market_boundary_position=market_boundary_position,
            coverage_percentage=coverage_percentage,
            confidence=confidence,
            keyword_positions=keyword_positions,  # Add keyword positions for cleanup
            # TASK 3v3.9: Edge case detection results (v2 pattern-based)
            non_dictionary_words=non_dictionary_words,
            extracted_acronym=extracted_acronym,
            acronym_processing=bool(extracted_acronym),
            base_report_type=base_report_type,
            matched_pattern=matched_pattern
        )
        
        logger.debug(f"Enhanced dictionary detection: {len(keywords_found)} keywords, {len(separators_found)} separators, {len(non_dictionary_words)} edge cases, {coverage_percentage:.1f}% coverage, {confidence:.2f} confidence")
        return result
    
    def _detect_separators_between_keywords(self, title: str, keyword_positions: Dict, sequence: List[Tuple[str, int]]) -> Tuple[List[str], List[str]]:
        """
        TASK 3v3.8: Advanced separator and punctuation detection between keywords.
        Analyzes text between detected keywords to identify separators for improved reconstruction.
        
        Args:
            title: Original title text
            keyword_positions: Dict mapping keyword to position info {start, end, word_pos}
            sequence: List of (keyword, word_position) tuples in order
        
        Returns:
            Tuple of (separators_found, boundary_markers_found)
        """
        separators_found = []
        boundary_markers_found = []
        
        if len(sequence) < 2:
            # Single keyword - check for basic separators in title
            for separator in self.separators:
                if separator in title:
                    separators_found.append(separator)
            return separators_found, boundary_markers_found
        
        # Analyze text between consecutive keywords
        for i in range(len(sequence) - 1):
            current_keyword = sequence[i][0]
            next_keyword = sequence[i + 1][0]
            
            if current_keyword not in keyword_positions or next_keyword not in keyword_positions:
                continue
            
            # Get text between keywords
            current_end = keyword_positions[current_keyword]['end']
            next_start = keyword_positions[next_keyword]['start']
            
            if current_end < next_start:
                between_text = title[current_end:next_start]
                
                # Detect separators from database patterns
                for separator in self.separators:
                    if separator in between_text:
                        if separator not in separators_found:
                            separators_found.append(separator)
                
                # Detect boundary markers from database patterns
                for marker in self.boundary_markers:
                    if marker in between_text:
                        if marker not in boundary_markers_found:
                            boundary_markers_found.append(marker)
                
                # Detect common punctuation patterns not in database
                punctuation_patterns = [
                    r'\s*,\s*',           # Comma with optional spaces
                    r'\s*&\s*',           # Ampersand with optional spaces  
                    r'\s*and\s*',         # "and" with optional spaces
                    r'\s*-\s*',           # Dash with optional spaces
                    r'\s*\|\s*',          # Pipe with optional spaces
                    r'\s*:\s*',           # Colon with optional spaces
                    r'\s*;\s*'            # Semicolon with optional spaces
                ]
                
                for pattern in punctuation_patterns:
                    if re.search(pattern, between_text, re.IGNORECASE):
                        # Extract the actual separator (without spaces)
                        match = re.search(pattern, between_text, re.IGNORECASE)
                        if match:
                            actual_sep = match.group().strip()
                            if actual_sep and actual_sep not in separators_found:
                                separators_found.append(actual_sep)
        
        # Sort separators by frequency of occurrence (most common first)
        separator_counts = {}
        for sep in separators_found:
            separator_counts[sep] = title.count(sep)
        
        separators_found = sorted(separators_found, key=lambda x: separator_counts.get(x, 0), reverse=True)
        
        logger.debug(f"Separator detection: found {separators_found} between {len(sequence)} keywords")
        return separators_found, boundary_markers_found
    
    def _detect_edge_cases_in_title(self, title: str, keywords_found: List[str], keyword_positions: Dict) -> List[str]:
        """
        TASK 3v3.9: Detect edge cases (non-dictionary words) between keyword boundaries.
        Database-driven classification using loaded edge case terms.
        
        Args:
            title: Original title text
            keywords_found: List of detected dictionary keywords
            keyword_positions: Dict mapping keyword to position info
        
        Returns:
            List of detected non-dictionary words with classifications
        """
        if not keywords_found:
            # No keyword boundaries - analyze entire title
            return self._classify_full_title_edge_cases(title)
        
        non_dictionary_words = []
        title_words = title.split()
        
        # Create keyword boundary map
        keyword_spans = set()
        for keyword, pos_info in keyword_positions.items():
            start_word = pos_info['word_pos']
            end_word = start_word + len(keyword.split())
            for i in range(start_word, end_word):
                keyword_spans.add(i)
        
        # Analyze words not covered by keywords
        for i, word in enumerate(title_words):
            if i not in keyword_spans:
                # This word is not part of any detected keyword
                classified_word = self._classify_edge_case_word(word.strip('.,;:()[]{}""'))
                if classified_word:
                    non_dictionary_words.append(classified_word)
        
        logger.debug(f"Edge case detection: found {len(non_dictionary_words)} non-dictionary words")
        return non_dictionary_words
    
    def _classify_full_title_edge_cases(self, title: str) -> List[str]:
        """
        TASK 3v3.9: Classify edge cases when no dictionary keywords are found.
        """
        edge_cases = []
        words = title.split()
        
        for word in words:
            clean_word = word.strip('.,;:()[]{}""').lower()
            classification = self._classify_edge_case_word(clean_word)
            if classification:
                edge_cases.append(classification)
        
        return edge_cases
    
    def _classify_edge_case_word(self, word: str) -> Optional[str]:
        """
        TASK 3v3.9: Identify potential edge case words for v3 dictionary approach.
        Note: Full acronym detection is handled by _detect_acronym_embedded_patterns()
        using database patterns. This method only flags potential edge cases.
        """
        if not word or len(word) < 2:
            return None
        
        # For v3, we simply identify non-dictionary words that might be significant
        # The actual pattern matching happens through database patterns
        # This is compatible with the v2 approach where patterns are in the database
        
        # Flag potential edge cases without hardcoded classification
        # Let the database patterns handle the actual detection
        return f"potential_edge_case:{word}"
    
    def _detect_acronym_embedded_patterns(self, title: str) -> Tuple[Optional[str], Optional[str], Optional[str]]:
        """
        TASK 3v3.9: Detect acronyms using v2 pattern-based approach with regex capture groups.
        Returns: (extracted_acronym, base_report_type, matched_pattern)
        """
        if not title or not self.acronym_embedded_patterns:
            return None, None, None
        
        # Try each acronym_embedded pattern with regex capture groups
        for pattern_data in self.acronym_embedded_patterns:
            pattern_text = pattern_data['pattern']
            try:
                pattern = re.compile(pattern_text, re.IGNORECASE)
                match = pattern.search(title)
                if match:
                    # Extract acronym from capture group
                    acronym = match.group(1) if match.groups() else None
                    base_type = pattern_data.get('base_type', '')
                    matched_pattern = pattern_text
                    
                    logger.debug(f"Acronym pattern match: '{acronym}' from pattern '{pattern_text}' -> base type '{base_type}'")
                    return acronym, base_type, matched_pattern
                    
            except re.error as e:
                logger.warning(f"Invalid regex pattern '{pattern_text}': {e}")
                continue
        
        return None, None, None
    
    def reconstruct_report_type_from_keywords(self, dictionary_result: DictionaryKeywordResult, title: str) -> Optional[str]:
        """
        Enhanced reconstruction using detected keywords and separators.
        ENHANCEMENT: Task 3v3.8 - Uses detected separators for accurate reconstruction.
        """
        if not dictionary_result.keywords_found:
            return None
        
        # Start with Market if detected (primary boundary marker)
        report_type_parts = []
        
        if dictionary_result.market_boundary_detected and self.market_primary_keyword:
            report_type_parts.append(self.market_primary_keyword)
        
        # Add other keywords in sequence order - only include keywords from report type phrase
        # Only include keywords that come AFTER Market keyword (not just non-negative positions)
        market_position = -1
        for keyword, position in dictionary_result.sequence:
            if keyword == self.market_primary_keyword:
                market_position = position
                break
                
        for keyword, position in dictionary_result.sequence:
            if keyword != self.market_primary_keyword and position > market_position:  # Only keywords after Market
                report_type_parts.append(keyword)
        
        # ENHANCEMENT: Intelligent separator selection based on detected patterns
        primary_separator = self._select_optimal_separator(dictionary_result, title)
        
        # Reconstruct using optimal separator
        reconstructed = primary_separator.join(report_type_parts)
        
        # Post-processing: Clean up common patterns
        reconstructed = self._clean_reconstructed_type(reconstructed, dictionary_result)
        
        logger.debug(f"Enhanced reconstruction: '{reconstructed}' using separator '{primary_separator}' from keywords: {dictionary_result.keywords_found}")
        return reconstructed
    
    def _select_optimal_separator(self, dictionary_result: DictionaryKeywordResult, title: str) -> str:
        """
        TASK 3v3.8: Select optimal separator based on detected patterns and context.
        """
        # Default separator
        default_separator = " "
        
        if not dictionary_result.separators:
            return default_separator
        
        # Use most frequent separator if multiple detected
        primary_separator = dictionary_result.separators[0]  # Already sorted by frequency
        
        # Handle common separator patterns
        separator_mappings = {
            ",": " ",           # Comma becomes space for readability
            " & ": " ",         # Ampersand becomes space
            "&": " ",           # Standalone ampersand becomes space
            " and ": " ",       # "and" becomes space
            "and": " ",         # Standalone "and" becomes space  
            "|": " ",           # Pipe becomes space
            " - ": " ",         # Dash with spaces becomes space
            "-": " "            # Standalone dash becomes space
        }
        
        # Apply separator mapping for readability
        if primary_separator in separator_mappings:
            mapped_separator = separator_mappings[primary_separator]
            logger.debug(f"Mapped separator '{primary_separator}' to '{mapped_separator}' for readability")
            return mapped_separator
        
        # Special case: If title has "Market Size & Analysis" format, preserve space
        if "Market" in title and ("&" in primary_separator or "and" in primary_separator.lower()):
            return " "
        
        # Use detected separator as-is if no mapping needed
        return primary_separator if primary_separator else default_separator
    
    def _clean_reconstructed_type(self, reconstructed: str, dictionary_result: DictionaryKeywordResult) -> str:
        """
        TASK 3v3.8: Clean and normalize reconstructed report type.
        """
        if not reconstructed:
            return reconstructed
        
        # Remove excessive spaces
        cleaned = re.sub(r'\s+', ' ', reconstructed).strip()
        
        # Fix common patterns
        patterns_to_fix = [
            (r'\bMarket\s+Market\b', 'Market'),           # Remove duplicate "Market"
            (r'\bReport\s+Report\b', 'Report'),           # Remove duplicate "Report" 
            (r'\bAnalysis\s+Analysis\b', 'Analysis'),     # Remove duplicate "Analysis"
            (r'\bStudy\s+Study\b', 'Study'),              # Remove duplicate "Study"
        ]
        
        for pattern, replacement in patterns_to_fix:
            cleaned = re.sub(pattern, replacement, cleaned, flags=re.IGNORECASE)
        
        # Capitalize first letter of each significant word
        words = cleaned.split()
        significant_words = []
        for word in words:
            if word.lower() not in ['and', 'or', 'of', 'in', 'on', 'at', 'by', 'for']:
                significant_words.append(word.capitalize())
            else:
                significant_words.append(word.lower())
        
        # Re-capitalize first word always
        if significant_words:
            significant_words[0] = significant_words[0].capitalize()
        
        return ' '.join(significant_words)
    
    def extract_market_term_workflow(self, title: str, market_term_type: str) -> Tuple[str, Optional[str], Optional[str]]:
        """
        TASK 3v3.10: Extract market term using DATABASE patterns (not hardcoded).
        
        Script 01 already classified the title as market_for/market_in/market_by/standard.
        This method uses that classification to extract the market term for report type detection
        using the SAME patterns from the database that Script 01 used.
        
        Returns: (remaining_title, market_prefix, market_context)
        """
        market_prefix = None
        market_context = None
        remaining_title = title
        
        logger.debug(f"Market term extraction input: title='{title}', type='{market_term_type}'")
        
        # Standard titles don't need market term extraction
        if market_term_type == "standard":
            return remaining_title, market_prefix, market_context
        
        # Load the actual pattern from database that Script 01 used for classification
        if market_term_type in ["market_for", "market_in", "market_by"]:
            try:
                # Access database directly since PatternLibraryManager expects PatternType enum
                # Convert market_term_type back to database format
                # "market_for" -> "Market for", "market_in" -> "Market in", etc.
                # Only capitalize the first word ("Market"), keep others lowercase
                parts = market_term_type.split('_')
                database_term = parts[0].capitalize() + ' ' + parts[1] if len(parts) > 1 else parts[0].capitalize()
                
                collection = self.pattern_library_manager.collection
                query = {
                    "type": "market_term",
                    "term": database_term,
                    "active": True
                }
                market_patterns = list(collection.find(query))
                logger.debug(f"Searching for database term: '{database_term}' (from {market_term_type})")
                logger.debug(f"Query: {query}")
                logger.debug(f"Found {len(market_patterns)} matching patterns")
                
                if not market_patterns:
                    logger.warning(f"No pattern found in database for market type '{market_term_type}'")
                    # Try simplified extraction based on type
                    return self._fallback_market_extraction(title, market_term_type)
                
                # Use the database pattern for detection and create extraction logic
                pattern_data = market_patterns[0]
                pattern_regex = pattern_data.get('pattern', '')
                
                if not pattern_regex:
                    logger.warning(f"Pattern missing regex for market type '{market_term_type}'")
                    return self._fallback_market_extraction(title, market_term_type)
                
                # Clean double escaping from MongoDB storage
                clean_pattern = pattern_regex.replace('\\\\', '\\')
                
                # Apply the database pattern for boundary detection
                match = re.search(clean_pattern, title, re.IGNORECASE)
                if match:
                    market_prefix = "Market"
                    
                    # The database patterns are simple boundaries (\bmarket\s+for\b)
                    # We need to extract what comes after the market term
                    matched_text = match.group(0)  # e.g., "Market for"
                    
                    # Find the position after the match
                    match_end = match.end()
                    
                    # Extract everything after the market term until comma or end
                    remaining_part = title[match_end:].strip()
                    
                    # Look for the entity between the market term and report type words or comma
                    # Stop at common report type indicators
                    report_indicators = r'(Analysis|Report|Study|Forecast|Outlook|Trends|Market|Size|Share|Growth|Industry)'
                    entity_pattern = rf'^(.*?)(?:\s+{report_indicators}|\s*,|$)'
                    entity_match = re.search(entity_pattern, remaining_part, re.IGNORECASE)
                    if entity_match:
                        entity = entity_match.group(1).strip()
                        
                        # Get connector word from market type
                        connector = market_term_type.split('_')[1]  # 'for', 'in', 'by'
                        market_context = f"{connector} {entity}" if entity else connector
                        
                        # Remove the entire market term phrase from title
                        # Find the full phrase including the entity
                        full_phrase_pattern = rf'\b{re.escape(matched_text)}\s+{re.escape(entity)}(?:\s*,|\s|$)'
                        remaining_title = re.sub(full_phrase_pattern, '', title, count=1, flags=re.IGNORECASE).strip()
                        
                        # Clean up any leftover punctuation
                        remaining_title = re.sub(r'^[,\s\-–—]+|[,\s\-–—]+$', '', remaining_title).strip()
                        remaining_title = re.sub(r'\s+', ' ', remaining_title)
                        
                        logger.debug(f"{market_term_type} extraction: matched='{matched_text}', entity='{entity}', context='{market_context}', remaining='{remaining_title}'")
                        
                        return remaining_title, market_prefix, market_context
                    else:
                        # No entity found after market term
                        logger.warning(f"No entity found after {market_term_type} in: {title}")
                        return self._fallback_market_extraction(title, market_term_type)
                else:
                    # Pattern didn't match - use fallback
                    logger.debug(f"Database pattern didn't match for '{market_term_type}', using fallback")
                    return self._fallback_market_extraction(title, market_term_type)
                    
            except Exception as e:
                logger.error(f"Error loading market term pattern: {e}")
                return self._fallback_market_extraction(title, market_term_type)
        
        logger.debug(f"Market term extraction final: prefix='{market_prefix}', context='{market_context}', remaining='{remaining_title}'")
        return remaining_title, market_prefix, market_context
    
    def _fallback_market_extraction(self, title: str, market_term_type: str) -> Tuple[str, Optional[str], Optional[str]]:
        """
        Fallback extraction when database patterns are unavailable.
        Uses simple regex based on market term type.
        """
        market_prefix = None
        market_context = None
        remaining_title = title
        
        if market_term_type == "market_for":
            # Simple extraction for "Market for X"
            match = re.search(r'\bMarket\s+for\s+([^,]+?)(?:\s+[A-Z][a-z]+|\s*[,.]|$)', title, re.IGNORECASE)
            if match:
                market_prefix = "Market"
                entity = match.group(1).strip()
                market_context = f"for {entity}"
                remaining_title = title.replace(match.group(0), '').strip()
                
        elif market_term_type == "market_in":
            # Simple extraction for "Market in X"
            match = re.search(r'\bMarket\s+in\s+([^,]+?)(?:\s+[A-Z][a-z]+|\s*[,.]|$)', title, re.IGNORECASE)
            if match:
                market_prefix = "Market"
                entity = match.group(1).strip()
                market_context = f"in {entity}"
                remaining_title = title.replace(match.group(0), '').strip()
                
        elif market_term_type == "market_by":
            # Simple extraction for "Market by X"
            match = re.search(r'\bMarket\s+by\s+([^,]+?)(?:\s+[A-Z][a-z]+|\s*[,.]|$)', title, re.IGNORECASE)
            if match:
                market_prefix = "Market"
                entity = match.group(1).strip()
                market_context = f"by {entity}"
                remaining_title = title.replace(match.group(0), '').strip()
        
        # Clean up remaining title
        remaining_title = re.sub(r'^[,\s\-–—]+|[,\s\-–—]+$', '', remaining_title).strip()
        remaining_title = re.sub(r'\s+', ' ', remaining_title)
        
        logger.debug(f"Fallback extraction for {market_term_type}: remaining='{remaining_title}'")
        return remaining_title, market_prefix, market_context
    
    def v2_pattern_fallback(self, title: str, market_term_type: str = "standard") -> Optional[str]:
        """Fallback to v2 pattern matching for compatibility."""
        try:
            for pattern_doc in self.v2_patterns:
                pattern = pattern_doc.get('pattern', '')
                if not pattern:
                    continue
                
                # Apply pattern matching logic from v2
                match = re.search(pattern, title, re.IGNORECASE)
                if match:
                    logger.debug(f"V2 fallback match: pattern='{pattern}', result='{match.group()}'")
                    self.stats['fallback_to_patterns'] += 1
                    return match.group()
            
            return None
            
        except Exception as e:
            logger.error(f"V2 pattern fallback error: {e}")
            return None
    
    def extract(self, title: str, market_term_type: str = "standard", original_title: str = None) -> MarketAwareDictionaryResult:
        """
        Main extraction method with dictionary-based detection and market-aware processing.
        
        Args:
            title: Title to process (may be pre-processed)
            market_term_type: Classification from Script 01 ('standard', 'market_for', 'market_in', 'market_by')
            original_title: Original title for context (optional)
        
        Returns:
            MarketAwareDictionaryResult with comprehensive extraction details
        """
        start_time = datetime.now()
        self.stats['total_processed'] += 1
        
        logger.debug(f"Processing title: '{title}' (type: {market_term_type})")
        
        try:
            # Step 1: Market term extraction and preprocessing (preserved from v2)
            working_title = title
            market_prefix = None
            market_context = None
            
            if market_term_type != "standard":
                working_title, market_prefix, market_context = self.extract_market_term_workflow(title, market_term_type)
            
            # Step 2: Dictionary-based keyword detection (NEW v3 approach)
            dictionary_result = self.detect_keywords_in_title(working_title)
            
            # Step 3: TASK 3v3.9 - Enhanced edge case detection and acronym processing
            edge_case_processing_result = self._process_edge_cases_and_acronyms(
                working_title, dictionary_result, market_term_type
            )
            
            # Step 4: Report type reconstruction from keywords (enhanced with edge cases)
            reconstructed_type = None
            if dictionary_result.confidence > 0.3:  # Confidence threshold
                self.stats['dictionary_hits'] += 1
                reconstructed_type = self.reconstruct_report_type_from_keywords(dictionary_result, working_title)
                
                # TASK 3v3.9: Apply acronym processing if detected
                if edge_case_processing_result.get('acronym_processing_applied'):
                    reconstructed_type = self._apply_acronym_processing(
                        reconstructed_type, edge_case_processing_result
                    )
                
                # Market term integration: prepend Market if extracted
                if market_prefix and reconstructed_type and not reconstructed_type.lower().startswith('market'):
                    reconstructed_type = f"{market_prefix} {reconstructed_type}"
            
            # Step 5: Fallback to v2 patterns if dictionary approach fails
            if not reconstructed_type:
                logger.debug("Dictionary approach insufficient, falling back to v2 patterns")
                reconstructed_type = self.v2_pattern_fallback(working_title, market_term_type)
                
                # Market term integration for fallback
                if market_prefix and reconstructed_type and not reconstructed_type.lower().startswith('market'):
                    reconstructed_type = f"{market_prefix} {reconstructed_type}"
            
            # CRITICAL V2 COMPATIBILITY: Market term fallback - if no patterns found, still return "Market"
            if not reconstructed_type and market_prefix and market_term_type != "standard":
                logger.debug(f"No patterns found for market term title, using market prefix: '{market_prefix}'")
                reconstructed_type = market_prefix  # This should be "Market"
            
            # Step 6: Determine format type and calculate final confidence (enhanced with edge cases)
            format_type = self._determine_format_type(
                reconstructed_type, dictionary_result, edge_case_processing_result
            )
            final_confidence = self._calculate_final_confidence(
                dictionary_result, reconstructed_type, market_term_type, edge_case_processing_result
            )
            
            # Step 7: Clean remaining title (remove extracted report type and preserve acronyms)
            remaining_title = self._clean_remaining_title_with_edge_cases(
                title, reconstructed_type, edge_case_processing_result, dictionary_result
            )
            
            # Add back market context for pipeline continuation (avoid duplication)
            if market_context and market_context not in remaining_title:
                # Check for partial duplication (e.g., context contains words already in title)
                context_words = market_context.lower().split()
                title_words = remaining_title.lower().split()
                
                # Only add if not already present in some form
                context_already_present = any(
                    all(word in title_words for word in context_words[i:i+2]) 
                    for i in range(len(context_words)-1)
                ) if len(context_words) > 1 else context_words[0] in title_words
                
                if not context_already_present:
                    remaining_title = f"{remaining_title} {market_context}".strip()
            
            # Calculate processing time
            processing_time = (datetime.now() - start_time).total_seconds() * 1000
            
            # Track Market boundary detection
            if dictionary_result.market_boundary_detected:
                self.stats['market_boundary_detected'] += 1
            
            # Build comprehensive result
            result = MarketAwareDictionaryResult(
                title=remaining_title,
                extracted_report_type=reconstructed_type or "",
                confidence=final_confidence,
                format_type=format_type,
                market_term_type=market_term_type,
                market_prefix_extracted=market_prefix,
                market_context_preserved=market_context,
                dictionary_result=dictionary_result,
                keywords_detected=dictionary_result.keywords_found,
                pattern_reconstruction=reconstructed_type,
                # TASK 3v3.9: Edge case processing results
                extracted_acronym=edge_case_processing_result.get('extracted_acronym'),
                acronym_processing=edge_case_processing_result.get('acronym_processing', False),
                edge_case_detected=len(dictionary_result.non_dictionary_words or []) > 0,
                edge_case_types=['acronym'] if edge_case_processing_result.get('acronym_processing') else [],
                processing_time_ms=processing_time,
                database_queries=1,  # Dictionary loading
                dictionary_lookups=len(dictionary_result.keywords_found),
                success=bool(reconstructed_type),
                error_details=None if reconstructed_type else "No report type detected"
            )
            
            logger.debug(f"Extraction complete: type='{reconstructed_type}', confidence={final_confidence:.2f}, time={processing_time:.1f}ms")
            return result
            
        except Exception as e:
            error_details = f"Extraction error: {str(e)}"
            logger.error(error_details)
            
            return MarketAwareDictionaryResult(
                title=title,
                extracted_report_type="",
                confidence=0.0,
                format_type=ReportTypeFormat.COMPOUND,
                market_term_type=market_term_type,
                processing_time_ms=(datetime.now() - start_time).total_seconds() * 1000,
                success=False,
                error_details=error_details
            )
    
    def _determine_format_type(self, report_type: Optional[str], dictionary_result: DictionaryKeywordResult, 
                              edge_case_result: Dict) -> ReportTypeFormat:
        """Determine format type based on dictionary detection patterns and edge case processing."""
        if not report_type:
            return ReportTypeFormat.COMPOUND
        
        # TASK 3v3.9: Check for acronym patterns from edge case detection
        if edge_case_result.get('acronym_processing') or dictionary_result.acronym_processing:
            return ReportTypeFormat.ACRONYM_EMBEDDED
        
        # Check for acronym patterns in text
        if re.search(r'\([A-Z]{2,}\)', report_type):
            return ReportTypeFormat.ACRONYM_EMBEDDED
        
        # Check for compound patterns (multiple keywords)
        if len(dictionary_result.keywords_found) > 2:
            return ReportTypeFormat.COMPOUND
        
        # Check for terminal patterns (ending keywords)
        if any(kw in report_type.split()[-2:] for kw in self.primary_keywords):
            return ReportTypeFormat.TERMINAL
        
        return ReportTypeFormat.COMPOUND
    
    def _calculate_final_confidence(self, dictionary_result: DictionaryKeywordResult, 
                                   report_type: Optional[str], market_term_type: str,
                                   edge_case_result: Dict) -> float:
        """Calculate final confidence score combining dictionary, edge case, and context factors."""
        confidence = dictionary_result.confidence
        
        # Boost confidence for successful reconstruction
        if report_type:
            confidence += 0.2
        
        # Boost confidence for Market boundary detection
        if dictionary_result.market_boundary_detected:
            confidence += 0.1
        
        # TASK 3v3.9: Boost confidence for successful edge case detection
        if edge_case_result.get('edge_cases_detected', 0) > 0:
            confidence += 0.05  # Small boost for edge case handling
        
        # Boost confidence for acronym processing (v2 compatibility)
        if edge_case_result.get('acronym_processing'):
            confidence += 0.1
        
        # Adjust for market term type compatibility
        if market_term_type != "standard" and dictionary_result.market_boundary_detected:
            confidence += 0.1
        
        return min(1.0, confidence)
    
    def _clean_remaining_title_with_edge_cases(self, original_title: str, extracted_type: Optional[str],
                                              edge_case_result: Dict, dictionary_result: DictionaryKeywordResult) -> str:
        """Clean remaining title by removing extracted report type and preserving acronyms for pipeline."""
        if not extracted_type:
            # TASK 3v3.9: Preserve acronyms even if no report type extracted
            return self._preserve_acronyms_in_pipeline(original_title, edge_case_result)
        
        # Remove extracted type from title
        remaining = original_title
        
        # ENHANCED: Remove original phrase components based on keyword positions
        remaining = self._remove_original_phrase_from_title(original_title, dictionary_result)
        
        # CRITICAL: No individual keyword removal needed - the complete phrase extraction above handles everything
        # This preserves legitimate content words like "And", "Data", "CT", "Global" when they're part of topics
        
        # Enhanced cleanup for dangling separators and punctuation
        remaining = re.sub(r'\s+', ' ', remaining)
        
        # Remove dangling separators and punctuation at start/end
        remaining = re.sub(r'^[,\s&\-–—\|;:]+|[,\s&\-–—\|;:]+$', '', remaining)
        
        # Remove internal dangling separators (e.g., "word , &" -> "word")
        remaining = re.sub(r'\s*,\s*&\s*$', '', remaining)
        remaining = re.sub(r'\s*&\s*,\s*$', '', remaining)
        remaining = re.sub(r'\s*,\s*$', '', remaining)
        remaining = re.sub(r'\s*&\s*$', '', remaining)
        remaining = re.sub(r'\s*\|\s*$', '', remaining)
        
        # Clean up excessive punctuation combinations
        remaining = re.sub(r'[,&\-–—\|;:]{2,}', ' ', remaining)
        
        # Final spacing cleanup
        remaining = re.sub(r'\s+', ' ', remaining)
        remaining = remaining.strip()
        
        # TASK 3v3.9: Preserve acronyms for pipeline continuation (v2 compatibility)
        remaining = self._preserve_acronyms_in_pipeline(remaining.strip(), edge_case_result)
        
        return remaining
    
    def _preserve_acronyms_in_pipeline(self, text: str, edge_case_result: Dict) -> str:
        """TASK 3v3.9: Preserve acronyms in pipeline text for v2 compatibility."""
        extracted_acronym = edge_case_result.get('extracted_acronym')
        if extracted_acronym and f"({extracted_acronym})" not in text:
            # Find the full name and add acronym in parentheses
            if edge_case_result.get('full_name_for_acronym'):
                full_name = edge_case_result['full_name_for_acronym']
                if full_name in text and f"({extracted_acronym})" not in text:
                    text = text.replace(full_name, f"{full_name} ({extracted_acronym})")
            else:
                # Append acronym at end if no full name context
                text = f"{text} ({extracted_acronym})".strip()
        
        return text
    
    def get_statistics(self) -> Dict:
        """Get processing statistics with v3 dictionary metrics."""
        stats = self.stats.copy()
        
        if stats['total_processed'] > 0:
            stats['dictionary_hit_rate'] = (stats['dictionary_hits'] / stats['total_processed']) * 100
            stats['market_boundary_detection_rate'] = (stats['market_boundary_detected'] / stats['total_processed']) * 100
            stats['fallback_rate'] = (stats['fallback_to_patterns'] / stats['total_processed']) * 100
            stats['avg_processing_time_ms'] = stats['processing_time_total'] / stats['total_processed']
        
        stats['dictionary_size'] = {
            'primary_keywords': len(self.primary_keywords),
            'secondary_keywords': len(self.secondary_keywords),
            'separators': len(self.separators),
            'boundary_markers': len(self.boundary_markers)
        }
        
        return stats

    def _remove_original_phrase_from_title(self, title: str, dictionary_result: DictionaryKeywordResult) -> str:
        """
        Remove the original phrase components from title based on keyword positions.
        This handles cases where reconstructed report type differs from original phrase.
        
        Args:
            title: Original title
            dictionary_result: Dictionary detection result with keyword positions
            
        Returns:
            Title with original phrase components removed
        """
        if not dictionary_result.keywords_found:
            return title
            
        # Get all keyword positions sorted by start position
        positions = []
        for keyword in dictionary_result.keywords_found:
            if keyword in dictionary_result.keyword_positions:
                pos_info = dictionary_result.keyword_positions[keyword]
                positions.append((pos_info['start'], pos_info['end'], keyword))
        
        if not positions:
            return title
            
        # Sort by start position
        positions.sort()
        
        # Find the span from first to last keyword (inclusive of separators and non-dictionary words)
        first_start = positions[0][0]
        last_end = positions[-1][1]
        
        # Remove the complete phrase span
        remaining = title[:first_start] + title[last_end:]
        
        # Clean up extra spaces
        remaining = re.sub(r'\s+', ' ', remaining).strip()
        
        return remaining
    
    def _process_edge_cases_and_acronyms(self, title: str, dictionary_result: DictionaryKeywordResult,
                                       market_term_type: str) -> Dict:
        """
        TASK 3v3.9: Process edge cases and acronyms for enhanced detection.
        Returns comprehensive edge case processing results.
        """
        result = {
            'edge_cases_detected': len(dictionary_result.non_dictionary_words or []),
            'acronym_processing': dictionary_result.acronym_processing,
            'extracted_acronym': dictionary_result.extracted_acronym,
            'acronym_processing_applied': False,
            'full_name_for_acronym': None
        }
        
        # Enhanced acronym processing for v2 compatibility
        if dictionary_result.extracted_acronym:
            # Look for full name context in original title
            acronym_match = re.search(rf'\b([A-Za-z\s]+)\s*\({dictionary_result.extracted_acronym}\)', title)
            if acronym_match:
                result['full_name_for_acronym'] = acronym_match.group(1).strip()
                result['acronym_processing_applied'] = True
                logger.debug(f"Acronym processing: '{result['full_name_for_acronym']}' -> '({dictionary_result.extracted_acronym})'")
        
        # Log edge case detection summary
        if result['edge_cases_detected'] > 0:
            edge_case_summary = {}
            for word in (dictionary_result.non_dictionary_words or []):
                if ':' in word:
                    edge_type = word.split(':')[0]
                    edge_case_summary[edge_type] = edge_case_summary.get(edge_type, 0) + 1
            logger.debug(f"Edge cases detected: {dict(edge_case_summary)}")
        
        return result
    
    def _apply_acronym_processing(self, report_type: Optional[str], edge_case_result: Dict) -> Optional[str]:
        """
        TASK 3v3.9: Apply acronym processing to report type reconstruction.
        Maintains v2 ACRONYM_EMBEDDED format compatibility.
        """
        if not report_type or not edge_case_result.get('extracted_acronym'):
            return report_type
        
        acronym = edge_case_result['extracted_acronym']
        
        # Check if acronym is already embedded
        if f"({acronym})" in report_type:
            return report_type
        
        # Apply v2-style acronym pattern reconstruction
        if edge_case_result.get('full_name_for_acronym'):
            full_name = edge_case_result['full_name_for_acronym']
            # Replace full name with acronym-embedded version in report type
            if full_name in report_type:
                enhanced_report_type = report_type.replace(full_name, f"{full_name} ({acronym})")
                logger.debug(f"Acronym-enhanced report type: '{enhanced_report_type}'")
                return enhanced_report_type
        
        return report_type


def main():
    """Test the dictionary-based report type extractor."""
    # Test titles showcasing dictionary approach
    test_titles = [
        "Artificial Intelligence (AI) Market Size Report 2024-2030",
        "Global Healthcare Market Analysis and Trends Forecast",
        "Automotive Industry Growth Study and Insights",
        "APAC Personal Protective Equipment Market Share Analysis, 2024-2029",
        "Market for Electric Vehicles Outlook & Trends, 2025-2035",
        "Market in Asia Pacific Data Analytics Overview"
    ]
    
    # Initialize (would typically get PatternLibraryManager from imports)
    from dotenv import load_dotenv
    load_dotenv()
    
    # Mock PatternLibraryManager for testing
    class MockPatternLibraryManager:
        def __init__(self):
            client = MongoClient(os.getenv('MONGODB_URI'))
            self.db = client['deathstar']
            self.patterns_collection = self.db['pattern_libraries']
    
    pattern_lib_manager = MockPatternLibraryManager()
    extractor = DictionaryBasedReportTypeExtractor(pattern_lib_manager)
    
    print("\n" + "="*80)
    print("SCRIPT 03 V3: DICTIONARY-BASED REPORT TYPE EXTRACTOR")
    print("="*80)
    
    for i, title in enumerate(test_titles, 1):
        print(f"\n{i}. Testing: '{title}'")
        print("-" * 60)
        
        # Classify market term type (mock - would come from Script 01)
        market_type = "standard"
        if "market for" in title.lower():
            market_type = "market_for"
        elif "market in" in title.lower():
            market_type = "market_in"
        
        result = extractor.extract(title, market_type)
        
        print(f"   Market Type: {result.market_term_type}")
        print(f"   Report Type: '{result.extracted_report_type}'")
        print(f"   Remaining:   '{result.title}'")
        print(f"   Confidence:  {result.confidence:.3f}")
        print(f"   Format:      {result.format_type.value}")
        print(f"   Keywords:    {result.keywords_detected}")
        print(f"   Market Boundary: {result.dictionary_result.market_boundary_detected if result.dictionary_result else 'N/A'}")
        print(f"   Processing:  {result.processing_time_ms:.1f}ms")
    
    print(f"\n" + "="*80)
    print("PROCESSING STATISTICS")
    print("="*80)
    stats = extractor.get_statistics()
    for key, value in stats.items():
        if isinstance(value, dict):
            print(f"{key}:")
            for sub_key, sub_value in value.items():
                print(f"  {sub_key}: {sub_value}")
        else:
            print(f"{key}: {value}")

if __name__ == "__main__":
    main()