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
from typing import Dict, List, Optional, Tuple, Set
from dataclasses import dataclass
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
    coverage_percentage: float
    confidence: float

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
        self.patterns_collection = pattern_library_manager.patterns_collection
        
        # Dictionary data - loaded from database
        self.primary_keywords: List[str] = []
        self.secondary_keywords: List[str] = []
        self.separators: List[str] = []
        self.boundary_markers: List[str] = []
        self.keyword_frequencies: Dict[str, int] = {}
        
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
            
            logger.info(f"Dictionary loaded from database:")
            logger.debug(f"  Primary keywords: {self.primary_keywords}")
            logger.debug(f"  Secondary keywords: {self.secondary_keywords[:10]}...")
            logger.debug(f"  Separators: {self.separators}")
            
        except Exception as e:
            logger.error(f"Failed to load dictionary from database: {e}")
            raise
    
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
    
    def detect_keywords_in_title(self, title: str) -> DictionaryKeywordResult:
        """
        Dictionary-based keyword detection with Market boundary recognition.
        O(n) performance vs O(pattern_count) regex matching.
        """
        start_time = datetime.now()
        
        # Normalize title for detection
        title_lower = title.lower()
        words = title.split()
        
        # Find keyword matches with positions
        keywords_found = []
        sequence = []
        
        # Check for Market boundary (96.7% coverage)
        market_boundary_detected = False
        if self.market_primary_keyword and self.market_primary_keyword.lower() in title_lower:
            market_boundary_detected = True
            # Find position
            for i, word in enumerate(words):
                if word.lower() == self.market_primary_keyword.lower():
                    keywords_found.append(self.market_primary_keyword)
                    sequence.append((self.market_primary_keyword, i))
                    break
        
        # Check primary keywords (database-driven)
        for keyword in self.primary_keywords:
            if keyword.lower() != "market":  # Already handled above
                if keyword.lower() in title_lower:
                    keywords_found.append(keyword)
                    # Find position
                    for i, word in enumerate(words):
                        if keyword.lower() in word.lower():
                            sequence.append((keyword, i))
                            break
        
        # Check secondary keywords
        for keyword in self.secondary_keywords:
            if keyword.lower() in title_lower:
                keywords_found.append(keyword)
                # Find position  
                for i, word in enumerate(words):
                    if keyword.lower() in word.lower():
                        sequence.append((keyword, i))
                        break
        
        # Sort sequence by position
        sequence.sort(key=lambda x: x[1])
        
        # Detect separators between keywords
        separators_found = []
        for separator in self.separators:
            if separator in title:
                separators_found.append(separator)
        
        # Calculate coverage and confidence
        total_frequency = sum(self.keyword_frequencies.get(kw, 0) for kw in keywords_found)
        coverage_percentage = (len(keywords_found) / max(len(self.primary_keywords + self.secondary_keywords), 1)) * 100
        
        # Base confidence on Market boundary detection and keyword density
        confidence = 0.0
        if market_boundary_detected:
            confidence += 0.4  # 40% for Market boundary
        confidence += min(0.6, len(keywords_found) * 0.1)  # Up to 60% for keywords
        
        processing_time = (datetime.now() - start_time).total_seconds() * 1000
        self.stats['processing_time_total'] += processing_time
        
        result = DictionaryKeywordResult(
            keywords_found=keywords_found,
            sequence=sequence,
            separators=separators_found,
            boundary_markers=[],  # TODO: Implement in next task
            market_boundary_detected=market_boundary_detected,
            coverage_percentage=coverage_percentage,
            confidence=confidence
        )
        
        logger.debug(f"Dictionary detection: {len(keywords_found)} keywords, {coverage_percentage:.1f}% coverage, {confidence:.2f} confidence")
        return result
    
    def reconstruct_report_type_from_keywords(self, dictionary_result: DictionaryKeywordResult, title: str) -> Optional[str]:
        """
        Reconstruct report type from detected keywords and separators.
        Implements sequential keyword ordering detection algorithm.
        """
        if not dictionary_result.keywords_found:
            return None
        
        # Start with Market if detected (primary boundary marker)
        report_type_parts = []
        
        if dictionary_result.market_boundary_detected and self.market_primary_keyword:
            report_type_parts.append(self.market_primary_keyword)
        
        # Add other keywords in sequence order
        for keyword, position in dictionary_result.sequence:
            if keyword != self.market_primary_keyword:  # Avoid duplicates
                report_type_parts.append(keyword)
        
        # Join with most common separator (space by default)
        primary_separator = " "
        if dictionary_result.separators:
            # Use most common separator from title
            primary_separator = dictionary_result.separators[0]
        
        reconstructed = primary_separator.join(report_type_parts)
        
        logger.debug(f"Reconstructed report type: '{reconstructed}' from keywords: {dictionary_result.keywords_found}")
        return reconstructed
    
    def extract_market_term_workflow(self, title: str, market_term_type: str) -> Tuple[str, Optional[str], Optional[str]]:
        """
        Extract market term and preserve context (from v2 compatibility).
        Returns: (remaining_title, market_prefix, market_context)
        """
        market_prefix = None
        market_context = None
        remaining_title = title
        
        logger.debug(f"Market term extraction input: title='{title}', type='{market_term_type}'")
        
        # Market term extraction logic (preserved from v2)
        if market_term_type in ["market_for", "market_in", "market_by"]:
            # Extract "Market" and preserve connector context
            if market_term_type == "market_for":
                # Look for "Market for X" pattern - be more specific about what constitutes the entity
                # Pattern to match: Market for [Entity] where Entity is usually 2-3 words max
                market_match = re.search(r'\bMarket\s+for\s+([A-Za-z\s]{2,30})(?=\s+[A-Z][a-z]+|,|\s+[0-9]|$)', title, re.IGNORECASE)
                if not market_match:
                    # Fallback: simpler pattern for short entities
                    market_match = re.search(r'\bMarket\s+for\s+([A-Za-z\s]+?)(?=\s+[A-Z][a-z]+.*[A-Z]|,|$)', title, re.IGNORECASE)
                
                if market_match:
                    market_prefix = "Market"
                    entity = market_match.group(1).strip()
                    market_context = f"for {entity}"
                    # Remove only "Market for Entity" part, preserve the rest
                    pattern_to_remove = f"Market\\s+for\\s+{re.escape(entity)}"
                    remaining_title = re.sub(pattern_to_remove, '', title, flags=re.IGNORECASE).strip()
                    logger.debug(f"market_for match: entity='{entity}', context='{market_context}', remaining='{remaining_title}'")
                    
            elif market_term_type == "market_in":
                # Look for "Market in X" pattern - be specific about entity boundaries
                market_match = re.search(r'\bMarket\s+in\s+([A-Za-z\s]{2,30})(?=\s+[A-Z][a-z]+|,|\s+[0-9]|$)', title, re.IGNORECASE)
                if not market_match:
                    # Fallback pattern
                    market_match = re.search(r'\bMarket\s+in\s+([A-Za-z\s]+?)(?=\s+[A-Z][a-z]+.*[A-Z]|,|$)', title, re.IGNORECASE)
                
                if market_match:
                    market_prefix = "Market"
                    entity = market_match.group(1).strip()
                    market_context = f"in {entity}"
                    # Remove only "Market in Entity" part, preserve the rest
                    pattern_to_remove = f"Market\\s+in\\s+{re.escape(entity)}"
                    remaining_title = re.sub(pattern_to_remove, '', title, flags=re.IGNORECASE).strip()
                    logger.debug(f"market_in match: entity='{entity}', context='{market_context}', remaining='{remaining_title}'")
                    
            elif market_term_type == "market_by":
                market_match = re.search(r'\bMarket\s+by\s+([^,]+?)(\s+[A-Z][a-z]+.*)?(?:,|$)', title, re.IGNORECASE)
                if not market_match:
                    market_match = re.search(r'\bMarket\s+by\s+(.+)', title, re.IGNORECASE)
                
                if market_match:
                    market_prefix = "Market"
                    market_context = f"by {market_match.group(1).strip()}"
                    # Remove the entire "Market by X" phrase, keep the rest
                    remaining_title = re.sub(r'\bMarket\s+by\s+[^,]+,?\s*', '', title, flags=re.IGNORECASE).strip()
                    logger.debug(f"market_by match: context='{market_context}', remaining after removal='{remaining_title}'")
            
            # Clean multiple spaces and punctuation
            remaining_title = re.sub(r'\s+', ' ', remaining_title).strip()
            remaining_title = re.sub(r'^[,\s]+|[,\s]+$', '', remaining_title)
        
        logger.debug(f"Market term extraction final: prefix='{market_prefix}', context='{market_context}', remaining='{remaining_title}'")
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
            
            # Step 3: Report type reconstruction from keywords
            reconstructed_type = None
            if dictionary_result.confidence > 0.3:  # Confidence threshold
                self.stats['dictionary_hits'] += 1
                reconstructed_type = self.reconstruct_report_type_from_keywords(dictionary_result, working_title)
                
                # Market term integration: prepend Market if extracted
                if market_prefix and reconstructed_type and not reconstructed_type.lower().startswith('market'):
                    reconstructed_type = f"{market_prefix} {reconstructed_type}"
            
            # Step 4: Fallback to v2 patterns if dictionary approach fails
            if not reconstructed_type:
                logger.debug("Dictionary approach insufficient, falling back to v2 patterns")
                reconstructed_type = self.v2_pattern_fallback(working_title, market_term_type)
                
                # Market term integration for fallback
                if market_prefix and reconstructed_type and not reconstructed_type.lower().startswith('market'):
                    reconstructed_type = f"{market_prefix} {reconstructed_type}"
            
            # Step 5: Determine format type and calculate final confidence
            format_type = self._determine_format_type(reconstructed_type, dictionary_result)
            final_confidence = self._calculate_final_confidence(dictionary_result, reconstructed_type, market_term_type)
            
            # Step 6: Clean remaining title (remove extracted report type)
            remaining_title = self._clean_remaining_title(title, reconstructed_type)
            
            # Add back market context for pipeline continuation (avoid duplication)
            if market_context and market_context not in remaining_title:
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
    
    def _determine_format_type(self, report_type: Optional[str], dictionary_result: DictionaryKeywordResult) -> ReportTypeFormat:
        """Determine format type based on dictionary detection patterns."""
        if not report_type:
            return ReportTypeFormat.COMPOUND
        
        # Check for acronym patterns
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
                                   report_type: Optional[str], market_term_type: str) -> float:
        """Calculate final confidence score combining dictionary and context factors."""
        confidence = dictionary_result.confidence
        
        # Boost confidence for successful reconstruction
        if report_type:
            confidence += 0.2
        
        # Boost confidence for Market boundary detection
        if dictionary_result.market_boundary_detected:
            confidence += 0.1
        
        # Adjust for market term type compatibility
        if market_term_type != "standard" and dictionary_result.market_boundary_detected:
            confidence += 0.1
        
        return min(1.0, confidence)
    
    def _clean_remaining_title(self, original_title: str, extracted_type: Optional[str]) -> str:
        """Clean remaining title by removing extracted report type."""
        if not extracted_type:
            return original_title
        
        # Remove extracted type from title
        remaining = original_title
        
        # Remove exact matches
        remaining = re.sub(re.escape(extracted_type), '', remaining, flags=re.IGNORECASE)
        
        # Remove individual keywords
        for keyword in self.primary_keywords + self.secondary_keywords:
            remaining = re.sub(rf'\b{re.escape(keyword)}\b', '', remaining, flags=re.IGNORECASE)
        
        # Clean up spacing and punctuation
        remaining = re.sub(r'\s+', ' ', remaining)
        remaining = re.sub(r'^[,\s]+|[,\s]+$', '', remaining)
        
        return remaining.strip()
    
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