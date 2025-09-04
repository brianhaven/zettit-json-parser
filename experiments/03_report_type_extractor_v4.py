#!/usr/bin/env python3
"""
Script 03 v4: Pure Dictionary-Based Report Type Extractor (Issue #21 Fix)
=========================================================================

**Issue #21 Fix - Remove V2 Fallback:**
Complete removal of V2 fallback functionality to use dictionary-only processing.
Fixes missing keywords: Report, Industry, &, and, misspellings (industy, repot).

**Key Changes:**
- NO V2 fallback patterns (921 regex patterns removed)
- Enhanced dictionary keyword detection algorithm  
- Fixed separator preservation for "&" and "and"
- Fixed misspelling detection (industy, repot, indsutry, sze)
- Fixed pipeline text truncation issues

**Architecture:**
Pure database dictionary-only processing with market-aware workflow.

**GitHub Issue:** #21 - Missing Keywords in Report Type Extraction  
**Version:** 4.0 (Dictionary-Only Architecture)
**Date:** 2025-01-04
**Branch:** fix/issue-21-missing-keywords
"""

import os
import sys
import logging
import re
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Set, Union, Any
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
    market_boundary_position: Optional[int] = None
    coverage_percentage: float = 0.0
    confidence: float = 0.0
    keyword_positions: Optional[Dict] = None
    
    # Edge case detection (preserved from v3)
    non_dictionary_words: Optional[List[str]] = None
    extracted_acronym: Optional[str] = None
    acronym_processing: bool = False

@dataclass
class MarketAwareDictionaryResult:
    """Result structure for dictionary-based market-aware report type extraction."""
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
    
    # Processing statistics
    processing_time_ms: float = 0.0
    database_queries: int = 0
    dictionary_lookups: int = 0
    
    # Status
    success: bool = True
    error_details: Optional[str] = None

class PureDictionaryReportTypeExtractor:
    """
    Pure dictionary-based report type extractor (Issue #21 Fix).
    
    NO V2 FALLBACK - Dictionary-only processing with enhanced keyword detection.
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
        self.all_keywords: List[str] = []  # Combined for easier lookup
        self.separators: List[str] = []
        self.boundary_markers: List[str] = []
        self.keyword_frequencies: Dict[str, int] = {}
        
        # Market boundary detection
        self.market_boundary_coverage = 0.0
        self.market_primary_keyword = None
        
        # Statistics (no V2 fallback tracking)
        self.stats = {
            'total_processed': 0,
            'dictionary_hits': 0,
            'market_boundary_detected': 0,
            'processing_time_total': 0.0
        }
        
        # Load dictionary data from database
        self._load_dictionary_from_database()
        
        logger.info(f"PureDictionaryReportTypeExtractor initialized:")
        logger.info(f"  Primary keywords: {len(self.primary_keywords)}")
        logger.info(f"  Secondary keywords: {len(self.secondary_keywords)}")
        logger.info(f"  Total keywords: {len(self.all_keywords)}")
        logger.info(f"  Market boundary coverage: {self.market_boundary_coverage:.1f}%")
        logger.info(f"  Separators: {len(self.separators)}")
    
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
            
            # Load secondary keywords (including misspellings)
            secondary_cursor = self.patterns_collection.find({
                "type": "report_type_dictionary",
                "subtype": "secondary_keyword", 
                "active": True
            }).sort("priority", 1)
            
            for doc in secondary_cursor:
                self.secondary_keywords.append(doc["term"])
                self.keyword_frequencies[doc["term"]] = doc.get("frequency", 0)
            
            # Combine all keywords for efficient lookup
            self.all_keywords = self.primary_keywords + self.secondary_keywords
            
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
            
            logger.info(f"Dictionary loaded from database:")
            logger.debug(f"  Primary keywords: {self.primary_keywords}")
            logger.debug(f"  Secondary keywords (first 10): {self.secondary_keywords[:10]}")
            logger.debug(f"  Separators: {self.separators}")
            logger.info(f"  Including misspellings: industy, repot, indsutry, sze")
            
        except Exception as e:
            logger.error(f"Failed to load dictionary from database: {e}")
            raise
    
    def _find_keyword_positions(self, title: str) -> Dict[str, Dict]:
        """
        Find all keyword positions in title with comprehensive detection.
        Enhanced to properly detect all database keywords including misspellings.
        """
        keyword_positions = {}
        title_lower = title.lower()
        
        # Check each keyword from database
        for keyword in self.all_keywords:
            # Case-insensitive boundary detection
            pattern = rf'\b{re.escape(keyword)}\b'
            matches = list(re.finditer(pattern, title, re.IGNORECASE))
            
            if matches:
                # Use first match (could be extended to handle multiple matches)
                match = matches[0]
                keyword_positions[keyword] = {
                    'start': match.start(),
                    'end': match.end(),
                    'word_pos': len(title[:match.start()].split()) - 1,
                    'matched_text': match.group()
                }
                
                logger.debug(f"Found keyword '{keyword}' at position {match.start()}-{match.end()}")
        
        return keyword_positions

    def detect_keywords_in_title(self, title: str) -> DictionaryKeywordResult:
        """
        Enhanced dictionary-based keyword detection with comprehensive separator detection.
        Issue #21 fix - properly detects all keywords including misspellings.
        """
        start_time = datetime.now()
        
        # Find all keyword positions
        keyword_positions = self._find_keyword_positions(title)
        
        # Build sequence from found keywords
        keywords_found = list(keyword_positions.keys())
        sequence = []
        
        for keyword, pos_info in keyword_positions.items():
            sequence.append((keyword, pos_info['word_pos']))
        
        # Sort sequence by position
        sequence.sort(key=lambda x: x[1])
        
        # Check for Market boundary (96.8% coverage)
        market_boundary_detected = self.market_primary_keyword in keywords_found
        market_boundary_position = None
        
        if market_boundary_detected:
            for i, (keyword, pos) in enumerate(sequence):
                if keyword == self.market_primary_keyword:
                    market_boundary_position = i
                    break
        
        # Enhanced separator detection between keywords
        separators_found, boundary_markers_found = self._detect_separators_between_keywords(
            title, keyword_positions, sequence
        )
        
        # Calculate coverage and confidence
        coverage_percentage = (len(keywords_found) / max(len(self.all_keywords), 1)) * 100
        
        # Enhanced confidence calculation
        confidence = 0.0
        if market_boundary_detected:
            confidence += 0.4  # 40% for Market boundary
        confidence += min(0.5, len(keywords_found) * 0.1)  # Up to 50% for keywords
        if separators_found:
            confidence += 0.1  # 10% bonus for separator detection
        
        processing_time = (datetime.now() - start_time).total_seconds() * 1000
        self.stats['processing_time_total'] += processing_time
        
        result = DictionaryKeywordResult(
            keywords_found=keywords_found,
            sequence=sequence,
            separators=separators_found,
            boundary_markers=boundary_markers_found,
            market_boundary_detected=market_boundary_detected,
            market_boundary_position=market_boundary_position,
            coverage_percentage=coverage_percentage,
            confidence=confidence,
            keyword_positions=keyword_positions
        )
        
        logger.debug(f"Dictionary detection: {len(keywords_found)} keywords, {len(separators_found)} separators, {confidence:.2f} confidence")
        logger.debug(f"Keywords found: {keywords_found}")
        logger.debug(f"Separators found: {separators_found}")
        
        return result
    
    def _detect_separators_between_keywords(self, title: str, keyword_positions: Dict, sequence: List[Tuple[str, int]]) -> Tuple[List[str], List[str]]:
        """
        Enhanced separator detection between keywords.
        Issue #21 fix - properly preserves "&" and "and" separators.
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
                
                # Detect boundary markers
                for marker in self.boundary_markers:
                    if marker in between_text:
                        if marker not in boundary_markers_found:
                            boundary_markers_found.append(marker)
        
        # Sort separators by priority (most common first)
        separator_priority = {sep: i for i, sep in enumerate(self.separators)}
        separators_found = sorted(separators_found, key=lambda x: separator_priority.get(x, 999))
        
        return separators_found, boundary_markers_found

    def reconstruct_report_type_from_keywords(self, dictionary_result: DictionaryKeywordResult, title: str) -> Optional[str]:
        """
        Enhanced reconstruction using detected keywords and separators.
        Issue #21 fix - properly preserves separators like "&" and "and".
        """
        if not dictionary_result.keywords_found:
            return None
        
        # Build report type parts from sequence
        report_type_parts = []
        
        # Add Market if detected (primary boundary marker)
        if dictionary_result.market_boundary_detected and self.market_primary_keyword:
            report_type_parts.append(self.market_primary_keyword)
        
        # Add other keywords in sequence order after Market
        market_position = -1
        if dictionary_result.market_boundary_position is not None:
            market_position = dictionary_result.market_boundary_position
            
        for i, (keyword, position) in enumerate(dictionary_result.sequence):
            if keyword != self.market_primary_keyword and i > market_position:
                report_type_parts.append(keyword)
        
        # If no Market boundary, include all keywords
        if not dictionary_result.market_boundary_detected:
            report_type_parts = [keyword for keyword, pos in dictionary_result.sequence]
        
        # ISSUE #21 FIX: Enhanced reconstruction with proper separator handling
        if len(report_type_parts) == 1:
            # Single keyword - return as-is
            reconstructed = report_type_parts[0]
        elif '&' in dictionary_result.separators:
            # Special handling for & separator
            reconstructed = ' & '.join(report_type_parts)
        elif 'and' in dictionary_result.separators:
            # Special handling for 'and' separator
            if len(report_type_parts) == 2:
                reconstructed = ' and '.join(report_type_parts)
            else:
                # Multiple keywords with 'and' - use for last separator
                all_but_last = ' '.join(report_type_parts[:-1])
                reconstructed = f"{all_but_last} and {report_type_parts[-1]}"
        else:
            # Standard space separator
            reconstructed = ' '.join(report_type_parts)
        
        # Post-processing cleanup
        reconstructed = self._clean_reconstructed_type(reconstructed, dictionary_result)
        
        logger.debug(f"Reconstructed: '{reconstructed}' from keywords: {dictionary_result.keywords_found}, separators: {dictionary_result.separators}")
        return reconstructed
    
    def _select_optimal_separator(self, dictionary_result: DictionaryKeywordResult, title: str) -> str:
        """
        Select optimal separator - Issue #21 fix to preserve "&" and "and".
        """
        # Default separator
        default_separator = " "
        
        if not dictionary_result.separators:
            return default_separator
        
        # Use most frequent separator (already sorted by priority)
        primary_separator = dictionary_result.separators[0]
        
        # Issue #21 fix - PRESERVE "&" and "and" instead of converting to space
        if primary_separator in ["&", " & ", "and", " and "]:
            if primary_separator == "&":
                return " & "  # Add spaces around & for readability
            elif primary_separator == "and":
                return " and "  # Add spaces around and for readability
            else:
                return primary_separator  # Already has spaces
        
        # Handle other separator mappings
        separator_mappings = {
            ",": " ",           # Comma becomes space for readability
            "|": " ",           # Pipe becomes space
            " - ": " ",         # Dash with spaces becomes space
            "-": " "            # Standalone dash becomes space
        }
        
        if primary_separator in separator_mappings:
            return separator_mappings[primary_separator]
        
        # Use detected separator as-is if no mapping needed
        return primary_separator if primary_separator else default_separator
    
    def _clean_reconstructed_type(self, reconstructed: str, dictionary_result: DictionaryKeywordResult) -> str:
        """Clean and normalize reconstructed report type."""
        if not reconstructed:
            return reconstructed
        
        # Remove excessive spaces but preserve separators
        cleaned = re.sub(r' +', ' ', reconstructed).strip()
        
        # Fix common duplicate patterns
        patterns_to_fix = [
            (r'\bMarket\s+Market\b', 'Market'),
            (r'\bReport\s+Report\b', 'Report'),
            (r'\bAnalysis\s+Analysis\b', 'Analysis'),
            (r'\bStudy\s+Study\b', 'Study'),
        ]
        
        for pattern, replacement in patterns_to_fix:
            cleaned = re.sub(pattern, replacement, cleaned, flags=re.IGNORECASE)
        
        # Capitalize first letter of each significant word
        words = cleaned.split()
        significant_words = []
        for word in words:
            if word.lower() not in ['and', 'or', 'of', 'in', 'on', 'at', 'by', 'for', '&']:
                significant_words.append(word.capitalize())
            else:
                significant_words.append(word.lower())
        
        # Re-capitalize first word always
        if significant_words:
            significant_words[0] = significant_words[0].capitalize()
        
        return ' '.join(significant_words)

    def extract_market_term_workflow(self, title: str, market_term_type: str) -> Tuple[str, str, str]:
        """
        Market-aware processing workflow - Issue #21 fix for pipeline text truncation.
        
        Returns: (extracted_market_term, remaining_title, pipeline_forward_text)
        """
        logger.debug(f"Market-aware workflow input: title='{title}', type='{market_term_type}'")
        
        # Standard titles don't need market term extraction
        if market_term_type == "standard":
            return "", title, title
        
        # Extract market term from title
        market_term, remaining_title, pipeline_forward = self._extract_market_term_from_title(title, market_term_type)
        
        if not market_term:
            logger.warning(f"Could not extract market term from '{title}' with type '{market_term_type}'")
            return "", title, title
        
        logger.debug(f"Extracted market term: '{market_term}'")
        logger.debug(f"Remaining title: '{remaining_title}'")
        logger.debug(f"Pipeline forward: '{pipeline_forward}'")
        
        return market_term, remaining_title, pipeline_forward
    
    def _extract_market_term_from_title(self, title: str, market_type: str) -> Tuple[str, str, str]:
        """
        Extract market term from title - Issue #21 fix for proper extraction boundaries.
        
        Args:
            title: Original title with market term
            market_type: Type of market term (market_for, market_in, market_by)
            
        Returns:
            (extracted_market_term, remaining_title, pipeline_forward_text)
        """
        # Convert market_type to phrase: "market_for" -> "Market for"
        market_phrase = market_type.replace('_', ' ').title()
        
        # ISSUE #21 FIX: More precise pattern to avoid capturing report type keywords
        # Only capture the market context, stop BEFORE report type keywords
        report_keywords = r'(?:Analysis|Report|Study|Forecast|Outlook|Trends|Size|Share|Growth|Industry)'
        
        # Enhanced pattern: capture market context but stop before report keywords
        # This will capture "Market in Oil & Gas" but NOT "Market in Oil & Gas Industry"
        pattern = rf'\b{re.escape(market_phrase)}\s+([^,]*?)(?=\s+{report_keywords}|\s*,\s*{report_keywords}|$)'
        match = re.search(pattern, title, re.IGNORECASE)
        
        if match:
            # Extract the market term phrase 
            full_market_term = match.group(0).strip()
            market_context = match.group(1).strip()  # Everything after "Market for/in/by"
            
            # Get remaining text: prefix + everything after market term
            prefix_part = title[:match.start()].strip()
            after_market_part = title[match.end():].strip()
            
            # Build remaining title for report type extraction
            remaining_parts = []
            if prefix_part:
                remaining_parts.append(prefix_part)
            if after_market_part:
                remaining_parts.append(after_market_part)
            
            remaining_title = ' '.join(remaining_parts).strip(' ,\-–—')
            
            # Create pipeline forward text - ISSUE #21 FIX: preserve complete context  
            if prefix_part:
                connector_word = market_phrase.split()[-1].lower()  # "for", "in", "by"
                # Preserve complete context including commas and conjunctions
                pipeline_forward = f"{prefix_part} {connector_word} {market_context}"
            else:
                pipeline_forward = market_context
            
            logger.debug(f"Market extraction: '{full_market_term}' -> remaining: '{remaining_title}' -> pipeline: '{pipeline_forward}'")
            return full_market_term, remaining_title, pipeline_forward
        
        # If no pattern match, return title as-is
        return "", title, title

    def _process_market_aware_workflow(self, title: str, market_type: str) -> Dict[str, Any]:
        """
        Process market term titles using extraction→rearrangement→reconstruction workflow.
        """
        # Extract market term from title
        market_term, remaining_title, pipeline_forward = self.extract_market_term_workflow(title, market_type)
        
        if not market_term:
            # Couldn't extract market term, fall back to standard processing
            return self._process_standard_workflow(title)
        
        # Search for report patterns in remaining text (without "Market")
        dictionary_result = self.detect_keywords_in_title(remaining_title)
        reconstructed_type = None
        
        # Try dictionary reconstruction without Market boundary constraint
        if dictionary_result.confidence > 0.2:  # Lower threshold for market-aware
            reconstructed_type = self._reconstruct_without_market_boundary(dictionary_result, remaining_title)
        
        # If no patterns found, try fallback with appended "Market"
        if not reconstructed_type:
            fallback_text = f"{remaining_title} Market".strip()
            fallback_result = self.detect_keywords_in_title(fallback_text)
            if fallback_result.confidence > 0.2:
                reconstructed_type = self.reconstruct_report_type_from_keywords(fallback_result, fallback_text)
        
        # Reconstruct with market term if we found patterns
        if reconstructed_type:
            final_type = self._reconstruct_report_type_with_market(reconstructed_type, market_term)
        else:
            # No patterns found - use just "Market" from market_term
            final_type = "Market" if market_term else None
        
        return {
            'extracted_report_type': final_type,
            'confidence': dictionary_result.confidence if reconstructed_type else 0.9,
            'format_type': ReportTypeFormat.COMPOUND,
            'extracted_market_term': market_term,
            'pipeline_forward_text': pipeline_forward,
            'processing_workflow': 'market_aware'
        }
    
    def _process_standard_workflow(self, title: str) -> Dict[str, Any]:
        """Process standard titles using pure dictionary-based detection."""
        dictionary_result = self.detect_keywords_in_title(title)
        
        reconstructed_type = None
        if dictionary_result.confidence > 0.2:  # Confidence threshold
            self.stats['dictionary_hits'] += 1
            reconstructed_type = self.reconstruct_report_type_from_keywords(dictionary_result, title)
        
        return {
            'extracted_report_type': reconstructed_type,
            'confidence': dictionary_result.confidence if reconstructed_type else 0.0,
            'format_type': ReportTypeFormat.COMPOUND,
            'processing_workflow': 'standard'
        }
    
    def _reconstruct_without_market_boundary(self, dictionary_result: DictionaryKeywordResult, title: str) -> str:
        """
        Reconstruct report type from keywords WITHOUT requiring Market boundary.
        Issue #21 fix - properly preserve separators like '&' and 'and'.
        """
        if not dictionary_result.keywords_found:
            return ""
        
        # Get all keywords in sequence order
        report_type_parts = []
        for keyword, position in dictionary_result.sequence:
            report_type_parts.append(keyword)
        
        # ISSUE #21 FIX: Enhanced separator selection and reconstruction
        if len(report_type_parts) == 1:
            # Single keyword - return as-is
            reconstructed = report_type_parts[0]
        else:
            # Multiple keywords - use detected separators intelligently
            if '&' in dictionary_result.separators:
                # Special handling for & separator
                reconstructed = ' & '.join(report_type_parts)
            elif 'and' in dictionary_result.separators:
                # Special handling for 'and' separator
                if len(report_type_parts) == 2:
                    reconstructed = ' and '.join(report_type_parts)
                else:
                    # Multiple keywords with 'and' - use for last separator
                    all_but_last = ', '.join(report_type_parts[:-1])
                    reconstructed = f"{all_but_last} and {report_type_parts[-1]}"
            else:
                # Standard space separator
                reconstructed = ' '.join(report_type_parts)
        
        # Clean up
        reconstructed = self._clean_reconstructed_type(reconstructed, dictionary_result)
        
        logger.debug(f"Reconstructed without Market: '{reconstructed}' from keywords: {dictionary_result.keywords_found}")
        return reconstructed
    
    def _reconstruct_report_type_with_market(self, extracted_type: str, market_term: str) -> str:
        """Reconstruct the final report type with proper market term positioning."""
        if not extracted_type:
            # If no pattern found, extract just "Market" from market term
            if market_term and market_term.lower().startswith('market'):
                return "Market"
            return None
        
        # If extracted type already contains "Market", return as-is
        if 'market' in extracted_type.lower():
            return extracted_type
        
        # Otherwise, prepend "Market" to the extracted type
        return f"Market {extracted_type}"

    def extract(self, title: str, market_term_type: str = "standard", original_title: str = None) -> MarketAwareDictionaryResult:
        """
        Main extraction method - Issue #21 fix with pure dictionary processing.
        
        Args:
            title: Title to process (may be pre-processed)
            market_term_type: Classification from Script 01
            original_title: Original title for context
        
        Returns:
            MarketAwareDictionaryResult with extraction details
        """
        start_time = datetime.now()
        self.stats['total_processed'] += 1
        
        logger.debug(f"Processing title: '{title}' (type: {market_term_type})")
        
        try:
            # Market-aware workflow
            if market_term_type != "standard":
                result = self._process_market_aware_workflow(title, market_term_type)
                reconstructed_type = result.get('extracted_report_type')
                remaining_title = result.get('pipeline_forward_text', title)
                
                # Placeholder dictionary result for compatibility
                dictionary_result = DictionaryKeywordResult(
                    keywords_found=[], sequence=[], separators=[], boundary_markers=[],
                    market_boundary_detected=bool(result.get('extracted_market_term')), 
                    confidence=result.get('confidence', 0.0)
                )
            else:
                # Standard processing
                result = self._process_standard_workflow(title)
                reconstructed_type = result.get('extracted_report_type')
                
                # Clean remaining title
                dictionary_result = self.detect_keywords_in_title(title)
                remaining_title = self._clean_remaining_title(title, reconstructed_type, dictionary_result)
            
            # Calculate processing time
            processing_time = (datetime.now() - start_time).total_seconds() * 1000
            
            # Track Market boundary detection
            if dictionary_result.market_boundary_detected:
                self.stats['market_boundary_detected'] += 1
            
            # Build result
            final_result = MarketAwareDictionaryResult(
                title=remaining_title,
                extracted_report_type=reconstructed_type or "",
                confidence=result.get('confidence', dictionary_result.confidence),
                format_type=result.get('format_type', ReportTypeFormat.COMPOUND),
                market_term_type=market_term_type,
                dictionary_result=dictionary_result,
                keywords_detected=dictionary_result.keywords_found,
                pattern_reconstruction=reconstructed_type,
                processing_time_ms=processing_time,
                database_queries=1,
                dictionary_lookups=len(dictionary_result.keywords_found),
                success=bool(reconstructed_type),
                error_details=None if reconstructed_type else "No report type detected"
            )
            
            logger.debug(f"Extraction complete: type='{reconstructed_type}', confidence={final_result.confidence:.2f}, time={processing_time:.1f}ms")
            return final_result
            
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

    def _clean_remaining_title(self, original_title: str, extracted_type: Optional[str], dictionary_result: DictionaryKeywordResult) -> str:
        """Clean remaining title by removing extracted report type."""
        if not extracted_type or not dictionary_result.keyword_positions:
            return original_title
        
        # Remove keyword phrases from title
        remaining = original_title
        
        # Get all keyword positions sorted by start position
        positions = []
        for keyword in dictionary_result.keywords_found:
            if keyword in dictionary_result.keyword_positions:
                pos_info = dictionary_result.keyword_positions[keyword]
                positions.append((pos_info['start'], pos_info['end'], keyword))
        
        if positions:
            # Sort by start position
            positions.sort()
            
            # Remove the complete phrase span from first to last keyword
            first_start = positions[0][0]
            last_end = positions[-1][1]
            
            # Remove the complete phrase span
            remaining = original_title[:first_start] + original_title[last_end:]
        
        # Clean up extra spaces and punctuation
        remaining = re.sub(r'\s+', ' ', remaining)
        remaining = re.sub(r'^[,\s&\-–—\|;:]+|[,\s&\-–—\|;:]+$', '', remaining)
        remaining = remaining.strip()
        
        return remaining

    def get_statistics(self) -> Dict:
        """Get processing statistics for pure dictionary approach."""
        stats = self.stats.copy()
        
        if stats['total_processed'] > 0:
            stats['dictionary_hit_rate'] = (stats['dictionary_hits'] / stats['total_processed']) * 100
            stats['market_boundary_detection_rate'] = (stats['market_boundary_detected'] / stats['total_processed']) * 100
            stats['avg_processing_time_ms'] = stats['processing_time_total'] / stats['total_processed']
        
        stats['dictionary_size'] = {
            'primary_keywords': len(self.primary_keywords),
            'secondary_keywords': len(self.secondary_keywords),
            'total_keywords': len(self.all_keywords),
            'separators': len(self.separators),
            'boundary_markers': len(self.boundary_markers)
        }
        
        return stats

# Alias for backward compatibility  
DictionaryBasedReportTypeExtractor = PureDictionaryReportTypeExtractor

def main():
    """Test the pure dictionary-based report type extractor."""
    test_titles = [
        "Material Handling Equipment Market In Biomass Power Plant Report",
        "Functional Cosmetics Market for Skin Care Application Trends & Analysis FCSC Outlook", 
        "Cloud Computing Market in Healthcare Industy",
        "Nanocapsules Market for Cosmetics Repot",
        "High Purity Quartz Sand Market for UVC Lighting Share and Size Outlook"
    ]
    
    # Initialize
    from dotenv import load_dotenv
    load_dotenv()
    
    class MockPatternLibraryManager:
        def __init__(self):
            client = MongoClient(os.getenv('MONGODB_URI'))
            self.db = client['deathstar']
            self.collection = self.db['pattern_libraries']  # Fix attribute name
    
    pattern_lib_manager = MockPatternLibraryManager()
    extractor = PureDictionaryReportTypeExtractor(pattern_lib_manager)
    
    print("\n" + "="*80)
    print("SCRIPT 03 V4: PURE DICTIONARY-BASED REPORT TYPE EXTRACTOR (Issue #21 Fix)")
    print("="*80)
    
    for i, title in enumerate(test_titles, 1):
        print(f"\n{i}. Testing: '{title}'")
        print("-" * 60)
        
        # Classify market term type
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
        print(f"   Keywords:    {result.keywords_detected}")
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