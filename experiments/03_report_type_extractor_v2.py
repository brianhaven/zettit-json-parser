#!/usr/bin/env python3

"""
Market-Aware Report Type Extraction System v1.0
Enhanced report type extraction with market term context awareness.
Addresses GitHub Issue #3 for market-aware detection.

Key Features:
- Market term type awareness (standard, market_for, market_in)
- Context-specific pattern matching based on market type
- Automatic "Market" prepending for market_for and market_in types
- Enhanced word order handling for different market contexts

Created for Market Research Title Parser project.
"""

import re
import logging
from typing import Dict, List, Optional, Tuple, Any, Union
from dataclasses import dataclass
from enum import Enum
from datetime import datetime, timezone
import pytz

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class MarketTermType(Enum):
    """Market term classification types - base types only."""
    STANDARD = "standard"
    AMBIGUOUS = "ambiguous"
    
    @classmethod
    def create_dynamic_type(cls, term_name: str) -> str:
        """Create a dynamic market term type from database term."""
        # Convert "Market for" -> "market_for", "Market by" -> "market_by", etc.
        return term_name.lower().replace(" ", "_")

class ReportTypeFormat(Enum):
    """Enumeration of report type format types."""
    TERMINAL_TYPE = "terminal_type"        # "Market Report, 2030" → "Report"
    EMBEDDED_TYPE = "embedded_type"        # "Global Market Analysis" → "Analysis"  
    PREFIX_TYPE = "prefix_type"            # "Market Size Report" → "Report"
    COMPOUND_TYPE = "compound_type"        # "Market Research Report" → "Research Report"
    UNKNOWN = "unknown"

@dataclass
class MarketAwareReportTypeResult:
    """Result of market-aware report type extraction."""
    title: str
    original_title: str
    market_term_type: str  # Changed to string to support dynamic types
    extracted_report_type: Optional[str]
    final_report_type: Optional[str]  # With Market prepended if needed
    normalized_report_type: Optional[str]
    format_type: ReportTypeFormat
    confidence: float
    matched_pattern: Optional[str]
    raw_match: Optional[str]
    date_removed_title: Optional[str]
    market_prepended: bool = False  # NEW: Track if Market was prepended
    context_analysis: Optional[str] = None  # NEW: Context-specific analysis
    notes: Optional[str] = None

@dataclass
class MarketAwareExtractionStats:
    """Statistics for market-aware report type extraction results."""
    total_processed: int
    successful_extractions: int
    failed_extractions: int
    # By market type
    standard_processed: int
    market_for_processed: int
    market_in_processed: int
    # By format type
    terminal_type: int
    embedded_type: int
    prefix_type: int
    compound_type: int
    # Market prepending stats
    market_prepended_count: int
    market_for_prepended: int
    market_in_prepended: int

class MarketAwareReportTypeExtractor:
    """
    Market-Aware Report Type Extraction System.
    
    Enhanced version that:
    1. Accepts market_term_type context
    2. Adapts pattern matching based on market type
    3. Prepends 'Market' for market_for and market_in types
    4. Handles different word orders in market contexts
    """
    
    def __init__(self, pattern_library_manager):
        """
        Initialize the Market-Aware Report Type Extractor.
        
        Args:
            pattern_library_manager: PatternLibraryManager instance (REQUIRED)
        """
        if not pattern_library_manager:
            raise ValueError("PatternLibraryManager is required")
        
        self.pattern_library_manager = pattern_library_manager
        
        # Enhanced statistics tracking
        self.extraction_stats = {
            'total_processed': 0,
            'successful_extractions': 0,
            'failed_extractions': 0,
            # By market type
            'standard_processed': 0,
            'market_for_processed': 0,
            'market_in_processed': 0,
            # By format type
            'terminal_type': 0,
            'embedded_type': 0,
            'prefix_type': 0,
            'compound_type': 0,
            # Market prepending stats
            'market_prepended_count': 0,
            'market_for_prepended': 0,
            'market_in_prepended': 0
        }
        
        # Initialize pattern lists
        self.terminal_type_patterns = []
        self.embedded_type_patterns = []
        self.prefix_type_patterns = []
        self.compound_type_patterns = []
        self.confusing_term_patterns = []  # NEW: Confusing term patterns
        
        # Load patterns from database
        self._load_library_patterns()
        
        # Market context patterns - special handling for market types
        self.market_context_indicators = {
            'market_in_separators': [' in ', ' In '],  # "Market in Singapore"
            'market_for_separators': [' for ', ' For '],  # "Market for Advanced Materials"
            'report_indicators': ['report', 'analysis', 'study', 'outlook', 'statistics', 'trends', 'size', 'share'],
            'dash_patterns': [' - ', ' – ', ' — '],  # "- Size, Outlook & Statistics"
        }
        
        # Context-specific patterns for market_for and market_in
        self.context_patterns = {
            # Patterns that work well on isolated context regions
            'standalone_report_words': [
                r'\banalysis\b',
                r'\breport\b', 
                r'\bstudy\b',
                r'\boutlook\b',
                r'\bstatistics\b',
                r'\btrends\b'
            ],
            'dash_suffix_patterns': [
                r'[-–—]\s*size[,\s]*outlook[,\s]*&?\s*statistics',
                r'[-–—]\s*size[,\s]*share[,\s]*&?\s*trends',
                r'[-–—]\s*analysis[,\s]*&?\s*outlook',
                r'[-–—]\s*market\s+size[,\s]*&?\s*share'
            ],
            'compound_context_patterns': [
                r'\bsize\s*[,&]\s*share\b',
                r'\bsize\s*[,&]\s*outlook\b',
                r'\boutlook\s*[,&]\s*statistics\b'
            ]
        }
        
        # Report type normalizations
        self.report_type_normalizations = {}
        self._load_normalizations()
        
        # Cache available market types to prevent repeated database queries
        self._available_market_types_cache = None
        
        logger.info(f"Market-Aware Report Type Extractor initialized")
        logger.info(f"Loaded {len(self.compound_type_patterns)} compound patterns")
        logger.info(f"Loaded {len(self.terminal_type_patterns)} terminal patterns")
        logger.info(f"Market context indicators: {len(self.market_context_indicators)} categories")
    
    def _load_library_patterns(self) -> None:
        """Load report type patterns from MongoDB pattern library."""
        try:
            # Import PatternType dynamically
            import importlib.util
            import sys
            import os
            
            # Dynamic import for pattern library manager (filename starts with numbers)
            pattern_manager_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '00b_pattern_library_manager_v1.py')
            spec = importlib.util.spec_from_file_location("pattern_library_manager_v1", pattern_manager_path)
            pattern_module = importlib.util.module_from_spec(spec)
            sys.modules["pattern_library_manager_v1"] = pattern_module
            spec.loader.exec_module(pattern_module)
            PatternType = pattern_module.PatternType
            
            # Load report type patterns from MongoDB by category
            report_patterns = self.pattern_library_manager.get_patterns(PatternType.REPORT_TYPE)
            
            if not report_patterns:
                raise RuntimeError("No report type patterns found in MongoDB pattern_libraries collection.")
            
            # Load confusing term patterns from MongoDB
            confusing_patterns = self.pattern_library_manager.get_patterns(PatternType.CONFUSING_TERM)
            
            # Organize report type patterns by format type
            for pattern in report_patterns:
                if not pattern.get('active', True):
                    continue
                    
                format_type = pattern.get('format_type', '')
                pattern_regex = pattern.get('pattern', '')
                
                if not pattern_regex:
                    continue
                
                try:
                    # Test pattern compilation
                    re.compile(pattern_regex)
                    
                    # Add to appropriate category
                    if format_type == 'terminal_type':
                        self.terminal_type_patterns.append(pattern)
                    elif format_type == 'embedded_type':
                        self.embedded_type_patterns.append(pattern)
                    elif format_type == 'prefix_type':
                        self.prefix_type_patterns.append(pattern)
                    elif format_type == 'compound_type':
                        self.compound_type_patterns.append(pattern)
                        
                except re.error as e:
                    logger.warning(f"Invalid regex pattern '{pattern_regex}': {e}")
                    continue
            
            # Organize confusing term patterns
            for pattern in confusing_patterns:
                if not pattern.get('active', True):
                    continue
                    
                pattern_regex = pattern.get('pattern', '')
                
                if not pattern_regex:
                    continue
                
                try:
                    # Test pattern compilation
                    re.compile(pattern_regex, re.IGNORECASE)
                    self.confusing_term_patterns.append(pattern)
                        
                except re.error as e:
                    logger.warning(f"Invalid confusing term regex pattern '{pattern_regex}': {e}")
                    continue
            
            logger.info(f"Successfully loaded patterns from MongoDB:")
            logger.info(f"  - Terminal type: {len(self.terminal_type_patterns)} patterns")
            logger.info(f"  - Embedded type: {len(self.embedded_type_patterns)} patterns")
            logger.info(f"  - Prefix type: {len(self.prefix_type_patterns)} patterns")
            logger.info(f"  - Compound type: {len(self.compound_type_patterns)} patterns")
            logger.info(f"  - Confusing terms: {len(self.confusing_term_patterns)} patterns")
            
        except Exception as e:
            logger.error(f"Failed to load report type patterns: {e}")
            raise RuntimeError(f"Could not initialize report type patterns: {e}")
    
    def _load_normalizations(self) -> None:
        """Load report type normalizations (fallback for now)."""
        # Basic normalizations - could be loaded from database later
        self.report_type_normalizations = {
            'analysis': 'Analysis',
            'report': 'Report', 
            'study': 'Study',
            'outlook': 'Outlook',
            'trends': 'Trends',
            'statistics': 'Statistics'
        }
    
    def _create_confusing_terms_free_text(self, title: str) -> Tuple[str, List[str]]:
        """
        Create a temporary version of the title with confusing terms removed for report type extraction.
        
        IMPORTANT: This does NOT modify the original title - it creates a temporary version
        for report type pattern matching only. The original title with confusing terms 
        is preserved for downstream pipeline steps (especially topic extraction).
        
        Args:
            title: Title to create confusing-terms-free version from
            
        Returns:
            (temp_title_for_extraction, removed_confusing_terms)
        """
        if not title or not self.confusing_term_patterns:
            return title, []
        
        temp_title = title
        removed_terms = []
        
        for pattern_data in self.confusing_term_patterns:
            try:
                term_name = pattern_data.get('term', 'Unknown')
                pattern_regex = pattern_data.get('pattern', '')
                
                if not pattern_regex:
                    continue
                
                # Compile pattern with case-insensitive flag
                pattern = re.compile(pattern_regex, re.IGNORECASE)
                matches = pattern.findall(temp_title)
                
                if matches:
                    # Remove all matches of this confusing term from temp version only
                    temp_title = pattern.sub('', temp_title)
                    
                    # Track what was removed for logging
                    if isinstance(matches[0], tuple):
                        # Patterns with groups - take first group or full match
                        removed_terms.extend([match[0] if match[0] else str(match) for match in matches])
                    else:
                        removed_terms.extend(matches)
                    
            except re.error as e:
                logger.debug(f"Confusing term pattern error for '{pattern_data.get('term', 'Unknown')}': {e}")
                continue
        
        # Clean up extra whitespace and punctuation after removals in temp version
        if removed_terms:
            temp_title = re.sub(r'\s+', ' ', temp_title).strip()
            temp_title = re.sub(r'^[,\s-]+|[,\s-]+$', '', temp_title)  # Remove leading/trailing punctuation
            temp_title = re.sub(r'\s+', ' ', temp_title).strip()  # Final cleanup
        
        return temp_title, removed_terms
    
    def _get_available_market_types(self) -> set:
        """
        Get available market term types from database dynamically with caching.
        
        Returns:
            Set of available market types (e.g., {"market_for", "market_in", "market_by"})
        """
        # Return cached result if available
        if self._available_market_types_cache is not None:
            return self._available_market_types_cache
        
        try:
            # Import PatternType here to avoid circular imports
            import importlib.util
            import sys
            import os
            
            # Dynamic import for pattern library manager
            pattern_manager_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '00b_pattern_library_manager_v1.py')
            spec = importlib.util.spec_from_file_location("pattern_library_manager_v1", pattern_manager_path)
            pattern_module = importlib.util.module_from_spec(spec)
            sys.modules["pattern_library_manager_v1"] = pattern_module
            spec.loader.exec_module(pattern_module)
            PatternType = pattern_module.PatternType
            
            # FIXED: Use shared pattern manager instead of creating new connection
            market_patterns = self.pattern_library_manager.get_patterns(PatternType.MARKET_TERM)
            
            available_types = set()
            for pattern in market_patterns:
                term = pattern.get('term')
                active = pattern.get('active', True)
                
                if term and active:
                    # Convert "Market for" -> "market_for", etc.
                    market_type = MarketTermType.create_dynamic_type(term)
                    available_types.add(market_type)
            
            logger.debug(f"Loaded market types from database: {available_types}")
            # Cache the result for future calls
            self._available_market_types_cache = available_types
            return available_types
            
        except Exception as e:
            logger.error(f"Failed to load market types from database: {e}")
            # Fallback to empty set - will treat everything as standard
            # Cache the fallback result too
            self._available_market_types_cache = set()
            return set()
    
    def _try_standard_pattern_extraction(self, text: str) -> Dict:
        """
        Try to extract report type using standard database patterns.
        First tries patterns as-is, then tries patterns without "Market" prefix as fallback.
        
        Args:
            text: Text to extract from
            
        Returns:
            Dictionary with extraction results
        """
        extraction_methods = [
            ('compound_type', self.compound_type_patterns),
            ('terminal_type', self.terminal_type_patterns),
            ('prefix_type', self.prefix_type_patterns),
            ('embedded_type', self.embedded_type_patterns),
        ]
        
        # First pass: Try patterns as-is
        for format_name, patterns in extraction_methods:
            for pattern_data in patterns:
                try:
                    pattern = re.compile(pattern_data['pattern'])
                    match = pattern.search(text)
                    
                    if match:
                        # Extract the report type from the match
                        # Extract the report type from full match (not captured group)
                        # This ensures we get "Market Size Report" not just "Report"
                        extracted = match.group(0).strip()
                        
                        confidence = pattern_data.get('confidence_weight', 0.8)
                        
                        # Return first successful match (highest priority patterns first)
                        return {
                            'extracted_report_type': extracted,
                            'format_type': ReportTypeFormat(format_name),
                            'confidence': confidence,
                            'matched_pattern': pattern_data['pattern'],
                            'raw_match': match.group(0),
                            'notes': f"Matched {format_name} pattern"
                        }
                        
                except (re.error, ValueError) as e:
                    logger.debug(f"Pattern error: {e}")
                    continue
        
        # Second pass: Try Market-prefixed patterns without the Market requirement
        # This handles cases like "Aftermarket Size & Share Report" where "Aftermarket" is removed
        # and we want to match "Size & Share Report" against "Market Size & Share Report" patterns
        # IMPORTANT: Process compound patterns first to match more complex phrases before simple ones
        reordered_methods = [
            ('compound_type', self.compound_type_patterns),  # Most complex first
            ('prefix_type', self.prefix_type_patterns),
            ('embedded_type', self.embedded_type_patterns),
            ('terminal_type', self.terminal_type_patterns),  # Simplest last
        ]
        
        for format_name, patterns in reordered_methods:
            for pattern_data in patterns:
                try:
                    pattern_regex = pattern_data['pattern']
                    
                    # Check if this pattern starts with Market requirement
                    if '\\bMarket\\s+' in pattern_regex or '\\bmarket\\s+' in pattern_regex:
                        # Create a variant without the Market prefix requirement
                        modified_pattern = pattern_regex.replace('\\bMarket\\s+', '', 1)
                        modified_pattern = modified_pattern.replace('\\bmarket\\s+', '', 1)
                        
                        pattern = re.compile(modified_pattern, re.IGNORECASE)
                        match = pattern.search(text)
                        
                        if match:
                            # Extract the report type from the match
                            groups = match.groups()
                            if groups:
                                extracted = groups[0].strip()
                            else:
                                extracted = match.group(0).strip()
                            
                            # Slightly lower confidence for fallback matches
                            confidence = pattern_data.get('confidence_weight', 0.8) * 0.9
                            
                            return {
                                'extracted_report_type': extracted,
                                'format_type': ReportTypeFormat(format_name),
                                'confidence': confidence,
                                'matched_pattern': f"{pattern_data['pattern']} (without Market prefix)",
                                'raw_match': match.group(0),
                                'notes': f"Matched {format_name} pattern (Market prefix removed for confusing term handling)"
                            }
                        
                except (re.error, ValueError) as e:
                    logger.debug(f"Pattern error (Market fallback): {e}")
                    continue
        
        # No patterns matched
        return {
            'extracted_report_type': None,
            'format_type': ReportTypeFormat.UNKNOWN,
            'confidence': 0.0,
            'matched_pattern': None,
            'raw_match': None,
            'notes': 'No patterns matched (including Market prefix fallback)'
        }
    
    def _analyze_market_context(self, title: str, market_term_type: MarketTermType) -> Tuple[str, str]:
        """
        Analyze title based on market term type context.
        
        Args:
            title: Title to analyze
            market_term_type: Market term classification
            
        Returns:
            (analysis_region, context_notes)
        """
        context_notes = []
        analysis_region = title
        
        if market_term_type == MarketTermType.MARKET_IN:
            # For "Market in X" - look for patterns after the region
            context_notes.append("market_in type: analyzing post-region patterns")
            for separator in self.market_context_indicators['market_in_separators']:
                if separator in title.lower():
                    parts = title.split(separator, 1)
                    if len(parts) == 2:
                        analysis_region = parts[1].strip()
                        context_notes.append(f"Focusing on region portion: '{analysis_region}'")
                        break
                        
        elif market_term_type == MarketTermType.MARKET_FOR:
            # For "Market for X" - look for patterns after the topic
            context_notes.append("market_for type: analyzing post-topic patterns")
            for separator in self.market_context_indicators['market_for_separators']:
                if separator in title.lower():
                    parts = title.split(separator, 1)
                    if len(parts) == 2:
                        analysis_region = parts[1].strip()
                        context_notes.append(f"Focusing on topic portion: '{analysis_region}'")
                        break
        else:
            context_notes.append("standard type: analyzing full title")
        
        return analysis_region, "; ".join(context_notes)
    
    def _should_prepend_market(self, market_term_type: MarketTermType, extracted_type: str) -> bool:
        """
        Determine if 'Market' should be prepended to extracted report type.
        
        Args:
            market_term_type: Market term classification
            extracted_type: The extracted report type
            
        Returns:
            True if 'Market' should be prepended
        """
        if not extracted_type:
            return False
        
        # Only prepend for market_for and market_in types
        if market_term_type not in [MarketTermType.MARKET_FOR, MarketTermType.MARKET_IN]:
            return False
        
        # Don't prepend if 'Market' is already present
        if 'market' in extracted_type.lower():
            return False
        
        return True
    
    def _create_final_report_type(self, extracted_type: str, market_term_type: MarketTermType) -> Tuple[str, bool]:
        """
        Create the final report type with Market prepending if needed.
        
        Args:
            extracted_type: The extracted report type
            market_term_type: Market term classification
            
        Returns:
            (final_report_type, was_prepended)
        """
        if not extracted_type:
            return extracted_type, False
        
        should_prepend = self._should_prepend_market(market_term_type, extracted_type)
        
        if should_prepend:
            # Prepend 'Market' with proper spacing
            if extracted_type.startswith(('-', '–', '—')):
                final_type = f"Market {extracted_type}"
            else:
                final_type = f"Market {extracted_type}"
            return final_type, True
        
        return extracted_type, False
    
    def extract(self, title: str, market_term_type: str = "standard", 
                original_title: str = None, date_extractor=None) -> MarketAwareReportTypeResult:
        """
        Extract report type with market term context awareness.
        
        CORRECTED APPROACH based on user feedback:
        - For market_in, market_for, market_by: "Market" IS the report type
        - For standard titles: use database pattern matching
        
        Args:
            title: Title to extract from (potentially with dates already removed)
            market_term_type: Market term classification (string: "standard", "market_for", "market_in", "market_by", etc.)
            original_title: Original title before date removal (for reference)
            date_extractor: Optional DateExtractor instance for smart date removal
            
        Returns:
            MarketAwareReportTypeResult with context-aware extraction
        """
        if not title or not title.strip():
            return MarketAwareReportTypeResult(
                title=title,
                original_title=original_title or title,
                market_term_type=market_term_type,
                extracted_report_type=None,
                final_report_type=None,
                normalized_report_type=None,
                format_type=ReportTypeFormat.UNKNOWN,
                confidence=0.0,
                matched_pattern=None,
                raw_match=None,
                date_removed_title=None,
                market_prepended=False,
                context_analysis="Empty or whitespace-only title",
                notes="Empty or whitespace-only title"
            )
        
        # Track processing stats
        self.extraction_stats['total_processed'] += 1
        
        # CORRECTED LOGIC: Check if this is a market term context
        available_market_types = self._get_available_market_types()  # Load from database
        
        if market_term_type in available_market_types:
            # For market_in, market_for, market_by: "Market" IS the report type
            extracted_report_type = "Market"
            final_report_type = "Market"
            normalized_report_type = "Market"
            confidence = 0.95  # High confidence for direct market term extraction
            context_analysis = f"Market term context: {market_term_type} -> Market is the report type"
            notes = f"Market type: {market_term_type}; Direct Market extraction"
            
            self.extraction_stats['successful_extractions'] += 1
            
            return MarketAwareReportTypeResult(
                title=title,
                original_title=original_title or title,
                market_term_type=market_term_type,
                extracted_report_type=extracted_report_type,
                final_report_type=final_report_type,
                normalized_report_type=normalized_report_type,
                format_type=ReportTypeFormat.EMBEDDED_TYPE,  # Market is embedded in the classification
                confidence=confidence,
                matched_pattern=f"Market term classification: {market_term_type}",
                raw_match="Market",
                date_removed_title=title,
                market_prepended=False,  # Not prepended, it IS the report type
                context_analysis=context_analysis,
                notes=notes
            )
        
        else:
            # For standard titles: use database pattern matching with confusing terms excluded
            
            # CRITICAL: Create confusing-terms-free version for pattern matching only
            # The original title is preserved for downstream pipeline steps
            temp_title_for_extraction, removed_confusing_terms = self._create_confusing_terms_free_text(title)
            
            # Use the temporary cleaned version for report type pattern matching
            best_result = self._try_standard_pattern_extraction(temp_title_for_extraction)
            
            if best_result.get('extracted_report_type'):
                self.extraction_stats['successful_extractions'] += 1
            else:
                self.extraction_stats['failed_extractions'] += 1
            
            # Create normalized version
            final_type = best_result.get('extracted_report_type')
            normalized_type = self._normalize_report_type(final_type) if final_type else None
            
            # Build context analysis with confusing terms info
            context_analysis = f"Standard processing: pattern matching"
            if removed_confusing_terms:
                context_analysis += f" (confusing terms excluded: {', '.join(removed_confusing_terms)})"
            
            notes = f"Market type: {market_term_type}; {best_result.get('notes', 'Standard pattern matching')}"
            if removed_confusing_terms:
                notes += f"; Confusing terms excluded from extraction: {', '.join(removed_confusing_terms)}"
            
            return MarketAwareReportTypeResult(
                title=title,  # IMPORTANT: Return original title, not temp version
                original_title=original_title or title,
                market_term_type=market_term_type,
                extracted_report_type=best_result.get('extracted_report_type'),
                final_report_type=final_type,
                normalized_report_type=normalized_type,
                format_type=best_result.get('format_type', ReportTypeFormat.UNKNOWN),
                confidence=best_result.get('confidence', 0.0),
                matched_pattern=best_result.get('matched_pattern'),
                raw_match=best_result.get('raw_match'),
                date_removed_title=title,  # IMPORTANT: Preserve original title for downstream steps
                market_prepended=False,
                context_analysis=context_analysis,
                notes=notes
            )
    
    def _try_pattern_extraction(self, text: str, market_term_type: MarketTermType = MarketTermType.STANDARD) -> Dict:
        """
        Try to extract report type using all pattern categories with market context awareness.
        
        Args:
            text: Text to extract from
            market_term_type: Market term context for specialized handling
            
        Returns:
            Dictionary with extraction results
        """
        # First try context-specific patterns for market_for and market_in
        if market_term_type in [MarketTermType.MARKET_FOR, MarketTermType.MARKET_IN]:
            context_result = self._try_context_patterns(text)
            if context_result['extracted_report_type']:
                return context_result
        
        # Fallback to standard database patterns
        extraction_methods = [
            ('compound_type', self.compound_type_patterns),
            ('terminal_type', self.terminal_type_patterns),
            ('prefix_type', self.prefix_type_patterns),
            ('embedded_type', self.embedded_type_patterns),
        ]
        
        best_result = {
            'extracted_report_type': None,
            'format_type': ReportTypeFormat.UNKNOWN,
            'confidence': 0.0,
            'matched_pattern': None,
            'raw_match': None,
            'notes': 'No patterns matched'
        }
        
        for format_name, patterns in extraction_methods:
            for pattern_data in patterns:
                try:
                    pattern = re.compile(pattern_data['pattern'])
                    match = pattern.search(text)
                    
                    if match:
                        # Extract the report type from the match
                        # Extract the report type from full match (not captured group)
                        # This ensures we get "Market Size Report" not just "Report"
                        extracted = match.group(0).strip()
                        
                        confidence = pattern_data.get('confidence_weight', 0.8)
                        
                        # Return first successful match (highest priority patterns first)
                        self.extraction_stats[format_name] += 1
                        return {
                            'extracted_report_type': extracted,
                            'format_type': ReportTypeFormat(format_name),
                            'confidence': confidence,
                            'matched_pattern': pattern_data['pattern'],
                            'raw_match': match.group(0),
                            'notes': f"Matched {format_name} pattern"
                        }
                        
                except (re.error, ValueError) as e:
                    logger.debug(f"Pattern error: {e}")
                    continue
        
        return best_result
    
    def _try_context_patterns(self, text: str) -> Dict:
        """
        Try context-specific patterns for market_for and market_in types.
        
        Args:
            text: Text to extract from (focused region)
            
        Returns:
            Dictionary with extraction results
        """
        # Try dash suffix patterns first (most specific)
        for pattern_text in self.context_patterns['dash_suffix_patterns']:
            try:
                pattern = re.compile(pattern_text, re.IGNORECASE)
                match = pattern.search(text)
                
                if match:
                    # Extract and clean the matched text
                    raw_match = match.group(0)
                    # Remove leading dash and clean up
                    extracted = re.sub(r'^[-–—]\s*', '', raw_match)
                    extracted = re.sub(r'[,&]\s*', ' & ', extracted)  # Normalize separators
                    extracted = extracted.strip().title()
                    
                    return {
                        'extracted_report_type': extracted,
                        'format_type': ReportTypeFormat.EMBEDDED_TYPE,
                        'confidence': 0.85,
                        'matched_pattern': pattern_text,
                        'raw_match': raw_match,
                        'notes': 'Matched context dash pattern'
                    }
                    
            except re.error:
                continue
        
        # Try compound context patterns
        for pattern_text in self.context_patterns['compound_context_patterns']:
            try:
                pattern = re.compile(pattern_text, re.IGNORECASE)
                match = pattern.search(text)
                
                if match:
                    extracted = match.group(0)
                    # Normalize the compound pattern
                    extracted = re.sub(r'[,&]\s*', ' & ', extracted)
                    extracted = extracted.strip().title()
                    
                    return {
                        'extracted_report_type': extracted,
                        'format_type': ReportTypeFormat.COMPOUND_TYPE,
                        'confidence': 0.80,
                        'matched_pattern': pattern_text,
                        'raw_match': match.group(0),
                        'notes': 'Matched context compound pattern'
                    }
                    
            except re.error:
                continue
        
        # Try standalone report words
        for pattern_text in self.context_patterns['standalone_report_words']:
            try:
                pattern = re.compile(pattern_text, re.IGNORECASE)
                match = pattern.search(text)
                
                if match:
                    extracted = match.group(0).strip().title()
                    
                    return {
                        'extracted_report_type': extracted,
                        'format_type': ReportTypeFormat.EMBEDDED_TYPE,
                        'confidence': 0.75,
                        'matched_pattern': pattern_text,
                        'raw_match': match.group(0),
                        'notes': 'Matched standalone report word'
                    }
                    
            except re.error:
                continue
        
        # No context patterns matched
        return {
            'extracted_report_type': None,
            'format_type': ReportTypeFormat.UNKNOWN,
            'confidence': 0.0,
            'matched_pattern': None,
            'raw_match': None,
            'notes': 'No context patterns matched'
        }
    
    def _normalize_report_type(self, report_type: str) -> str:
        """Normalize report type using loaded normalizations."""
        if not report_type:
            return report_type
        
        # Apply normalizations
        normalized = report_type
        for key, value in self.report_type_normalizations.items():
            if key.lower() in report_type.lower():
                normalized = normalized.replace(key, value)
                break
        
        return normalized
    
    def get_stats(self) -> MarketAwareExtractionStats:
        """Get market-aware extraction statistics."""
        stats = self.extraction_stats
        return MarketAwareExtractionStats(
            total_processed=stats['total_processed'],
            successful_extractions=stats['successful_extractions'],
            failed_extractions=stats['failed_extractions'],
            standard_processed=stats['standard_processed'],
            market_for_processed=stats['market_for_processed'],
            market_in_processed=stats['market_in_processed'],
            terminal_type=stats['terminal_type'],
            embedded_type=stats['embedded_type'],
            prefix_type=stats['prefix_type'],
            compound_type=stats['compound_type'],
            market_prepended_count=stats['market_prepended_count'],
            market_for_prepended=stats['market_for_prepended'],
            market_in_prepended=stats['market_in_prepended']
        )
    
    def close_connection(self):
        """Close database connection."""
        if self.pattern_library_manager:
            self.pattern_library_manager.close_connection()

if __name__ == "__main__":
    # Test the market-aware extractor
    import os
    import sys
    import importlib.util
    from dotenv import load_dotenv
    
    load_dotenv()
    
    # Import pattern library manager
    try:
        pattern_manager_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '00b_pattern_library_manager_v1.py')
        spec = importlib.util.spec_from_file_location("pattern_library_manager_v1", pattern_manager_path)
        pattern_module = importlib.util.module_from_spec(spec)
        sys.modules["pattern_library_manager_v1"] = pattern_module
        spec.loader.exec_module(pattern_module)
        PatternLibraryManager = pattern_module.PatternLibraryManager
    except Exception as e:
        print(f"Could not import PatternLibraryManager: {e}")
        sys.exit(1)
    
    # Test cases from GitHub Issue #3
    extractor = MarketAwareReportTypeExtractor(pattern_library_manager)
    
    test_cases = [
        # Market In examples
        ("Retail Market in Singapore - Size, Outlook & Statistics", MarketTermType.MARKET_IN),
        ("Artificial Intelligence (AI) Market in Automotive", MarketTermType.MARKET_IN),
        
        # Market For examples  
        ("Global Market for Advanced Materials Analysis, 2030", MarketTermType.MARKET_FOR),
        ("Market for Electric Vehicles Report", MarketTermType.MARKET_FOR),
        
        # Standard examples
        ("Electric Vehicle Market Size Report, 2025", MarketTermType.STANDARD),
        ("Healthcare Technology Market Analysis", MarketTermType.STANDARD),
    ]
    
    print("🎯 Market-Aware Report Type Extractor Test Results")
    print("=" * 70)
    
    for title, market_type in test_cases:
        result = extractor.extract(title, market_type)
        
        print(f"Title: {title}")
        print(f"  Market Type: {market_type.value}")
        print(f"  Extracted: {result.extracted_report_type}")
        print(f"  Final: {result.final_report_type}")
        print(f"  Market Prepended: {result.market_prepended}")
        print(f"  Context: {result.context_analysis}")
        print(f"  Confidence: {result.confidence}")
        print()
    
    print("Statistics:")
    stats = extractor.get_stats()
    print(f"  Total Processed: {stats.total_processed}")
    print(f"  Successful: {stats.successful_extractions}")
    print(f"  Market Prepended: {stats.market_prepended_count}")
    print(f"  Market For Prepended: {stats.market_for_prepended}")
    print(f"  Market In Prepended: {stats.market_in_prepended}")
    
    extractor.close_connection()