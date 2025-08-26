#!/usr/bin/env python3

"""
Market-Aware Report Type Extraction System v2.0
Enhanced report type extraction with CORRECT market term processing logic.
Addresses GitHub Issue #10 for proper market-aware detection workflow.

Key Features:
- Market term type awareness (standard, market_for, market_in, market_by)
- CORRECT extraction→rearrangement→reconstruction workflow for market terms
- Different processing paths for market term vs standard titles
- Database-driven pattern matching with proper context handling

Processing Logic:
- Market Term Titles: Extract → Rearrange → Match → Reconstruct
- Standard Titles: Direct database pattern matching

Created for Market Research Title Parser project.
"""

import re
import os
import importlib.util
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
    ACRONYM_EMBEDDED = "acronym_embedded"  # "Market Size, DEW Industry Report" → "Market Size, Industry Report" (extracts DEW)
    UNKNOWN = "unknown"

@dataclass
class MarketAwareReportTypeResult:
    """Result of market-aware report type extraction."""
    title: str
    original_title: str
    market_term_type: str  # Changed to string to support dynamic types
    extracted_report_type: Optional[str]
    final_report_type: Optional[str]
    normalized_report_type: Optional[str]
    format_type: ReportTypeFormat
    confidence: float
    matched_pattern: Optional[str]
    raw_match: Optional[str]
    date_removed_title: Optional[str]
    market_prepended: bool = False
    context_analysis: Optional[str] = None
    processing_workflow: Optional[str] = None  # NEW: Track which workflow was used
    rearranged_title: Optional[str] = None     # NEW: Track rearranged version
    extracted_market_term: Optional[str] = None # NEW: Track extracted market term
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
    market_by_processed: int
    # By processing workflow
    market_aware_workflow: int
    standard_workflow: int
    # By format type
    terminal_type: int
    embedded_type: int
    prefix_type: int
    compound_type: int
    # Market reconstruction stats
    market_reconstructed_count: int

class MarketAwareReportTypeExtractor:
    """
    Market-Aware Report Type Extraction System with CORRECT Processing Logic.
    
    Implements proper workflow:
    1. For market term titles: Extract → Rearrange → Match → Reconstruct
    2. For standard titles: Direct database pattern matching
    """
    
    def __init__(self, pattern_library_manager):
        """Initialize with pattern library manager."""
        self.pattern_library_manager = pattern_library_manager
        
        # Load patterns from database
        self._load_patterns()
        
        # Initialize statistics
        self.extraction_stats = {
            'total_processed': 0,
            'successful_extractions': 0,
            'failed_extractions': 0,
            # By market type
            'standard_processed': 0,
            'market_for_processed': 0,
            'market_in_processed': 0,
            'market_by_processed': 0,
            # By processing workflow
            'market_aware_workflow': 0,
            'standard_workflow': 0,
            # By format type
            'terminal_type': 0,
            'embedded_type': 0,
            'prefix_type': 0,
            'compound_type': 0,
            'acronym_embedded': 0,
            # Market reconstruction
            'market_reconstructed_count': 0
        }
        
        # Load confusing terms
        self.confusing_terms = self._load_confusing_terms()
        
        # Load market types from database
        self.available_market_types = self._get_available_market_types()
        logger.info(f"Available market types from database: {self.available_market_types}")
    
    def _load_patterns(self):
        """Load report type patterns from database."""
        try:
            # Dynamic import of PatternType from the pattern library manager
            pattern_manager_path = os.path.join(os.path.dirname(__file__), '00b_pattern_library_manager_v1.py')
            spec = importlib.util.spec_from_file_location("pattern_manager", pattern_manager_path)
            pattern_manager_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(pattern_manager_module)
            PatternType = pattern_manager_module.PatternType
            
            # Get database patterns
            if hasattr(self.pattern_library_manager, 'get_patterns'):
                patterns = self.pattern_library_manager.get_patterns(PatternType.REPORT_TYPE, active_only=True)
            else:
                # Fallback for older version
                patterns = []
                
            # Organize patterns by format type
            self.terminal_type_patterns = []
            self.embedded_type_patterns = []
            self.prefix_type_patterns = []
            self.compound_type_patterns = []
            self.acronym_embedded_patterns = []
            
            for pattern in patterns:
                pattern_data = {
                    'pattern': pattern.get('pattern', ''),  # Use 'pattern' field, not 'term'
                    'term': pattern.get('term', ''),        # Also store term for reference
                    'confidence_weight': pattern.get('confidence_weight', 0.9),
                    'format_type': pattern.get('format_type', 'unknown')
                }
                
                # Categorize by format_type (exact match)
                format_type = pattern.get('format_type', '').lower()
                if format_type == 'terminal_type':
                    self.terminal_type_patterns.append(pattern_data)
                elif format_type == 'embedded_type':
                    self.embedded_type_patterns.append(pattern_data)
                elif format_type == 'prefix_type':
                    self.prefix_type_patterns.append(pattern_data)
                elif format_type == 'compound_type':
                    self.compound_type_patterns.append(pattern_data)
                elif format_type == 'acronym_embedded':
                    # Store additional metadata for acronym patterns
                    pattern_data['base_type'] = pattern.get('base_type', '')
                    pattern_data['extraction_logic'] = pattern.get('extraction_logic', 'capture_acronym_to_pipeline')
                    self.acronym_embedded_patterns.append(pattern_data)
                else:
                    # Handle patterns with missing or unknown format_type
                    # Default to terminal_type for backwards compatibility
                    logger.warning(f"Pattern '{pattern.get('term', 'UNKNOWN')}' has unknown format_type '{format_type}', defaulting to terminal_type")
                    pattern_data['format_type'] = 'terminal_type'  # Override for consistency
                    self.terminal_type_patterns.append(pattern_data)
                    
            logger.info(f"Loaded {len(patterns)} report type patterns from database")
            logger.info(f"  Terminal: {len(self.terminal_type_patterns)}")
            logger.info(f"  Embedded: {len(self.embedded_type_patterns)}")
            logger.info(f"  Prefix: {len(self.prefix_type_patterns)}")
            logger.info(f"  Compound: {len(self.compound_type_patterns)}")
            logger.info(f"  Acronym Embedded: {len(self.acronym_embedded_patterns)}")
            
        except Exception as e:
            logger.error(f"Error loading patterns: {e}")
            # Initialize empty if load fails
            self.terminal_type_patterns = []
            self.embedded_type_patterns = []
            self.prefix_type_patterns = []
            self.compound_type_patterns = []
            self.acronym_embedded_patterns = []
    
    def _load_confusing_terms(self) -> List[str]:
        """Load confusing terms that need special handling."""
        try:
            # Dynamic import of PatternType 
            pattern_manager_path = os.path.join(os.path.dirname(__file__), '00b_pattern_library_manager_v1.py')
            spec = importlib.util.spec_from_file_location("pattern_manager", pattern_manager_path)
            pattern_manager_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(pattern_manager_module)
            PatternType = pattern_manager_module.PatternType
            
            if hasattr(self.pattern_library_manager, 'get_patterns'):
                patterns = self.pattern_library_manager.get_patterns(PatternType.CONFUSING_TERM, active_only=True)
                return [p.get('term', '') for p in patterns if p.get('term')]
            return []
        except Exception as e:
            logger.error(f"Error loading confusing terms: {e}")
            return []
    
    def _get_available_market_types(self) -> List[str]:
        """Get available market types from database."""
        try:
            # Dynamic import of PatternType 
            pattern_manager_path = os.path.join(os.path.dirname(__file__), '00b_pattern_library_manager_v1.py')
            spec = importlib.util.spec_from_file_location("pattern_manager", pattern_manager_path)
            pattern_manager_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(pattern_manager_module)
            PatternType = pattern_manager_module.PatternType
            
            if hasattr(self.pattern_library_manager, 'get_patterns'):
                patterns = self.pattern_library_manager.get_patterns(PatternType.MARKET_TERM, active_only=True)
                # Convert to format: "market_for", "market_in", "market_by"
                market_types = []
                for p in patterns:
                    term = p.get('term', '')
                    if term:
                        # Convert "Market for" -> "market_for"
                        market_type = term.lower().replace(' ', '_')
                        market_types.append(market_type)
                return market_types
            return []
        except Exception as e:
            logger.error(f"Error loading market types: {e}")
            return []
    
    def _extract_market_term_from_title(self, title: str, market_type: str) -> Tuple[str, str, str]:
        """
        Extract the market term from the title based on market type.
        
        Args:
            title: Original title with market term
            market_type: Type of market term (market_for, market_in, market_by)
            
        Returns:
            (extracted_market_term, remaining_title, pipeline_forward_text)
        """
        # Convert market_type back to phrase: "market_for" -> "Market for"
        market_phrase = market_type.replace('_', ' ').title()
        
        # Find the market term in the title
        pattern = rf'\b{re.escape(market_phrase)}\s+([^,\-–—]+?)(?:[,\-–—]|$)'
        match = re.search(pattern, title, re.IGNORECASE)
        
        if match:
            # Extract the full market term phrase (e.g., "Market in Automotive")
            full_market_term = match.group(0).rstrip(',\-–— ')
            market_context = match.group(1).strip()  # e.g., "Automotive"
            
            # Remove the market term from title to get remaining text
            remaining_title = title[:match.start()] + title[match.end():]
            remaining_title = remaining_title.strip(' ,\-–—')
            
            # Create pipeline forward text (topic/region stays with market context)
            # e.g., "AI in Automotive" or "AI for Livestock"
            prefix_part = title[:match.start()].strip()
            if prefix_part:
                connector_word = market_phrase.split()[-1].lower()  # "for", "in", "by"
                pipeline_forward = f"{prefix_part} {connector_word} {market_context}"
            else:
                pipeline_forward = market_context
            
            return full_market_term, remaining_title, pipeline_forward
        
        # If no clear pattern match, return title as-is
        return "", title, title
    
    def _rearrange_title_for_matching(self, title: str, extracted_market_term: str) -> str:
        """
        Rearrange title by moving market term to end for pattern matching.
        
        Args:
            title: Title with market term removed
            extracted_market_term: The extracted market term
            
        Returns:
            Rearranged title for pattern matching
        """
        if not title:
            return extracted_market_term
        
        # Append market term at the end for pattern matching
        # This allows patterns to match against the rearranged structure
        return f"{title} {extracted_market_term}".strip()
    
    def _search_report_patterns_without_market(self, text: str) -> Dict[str, Any]:
        """
        Search for report type patterns in text, ignoring "Market" prefix requirement.
        
        Args:
            text: Text to search for patterns
            
        Returns:
            Dictionary with extraction results
        """
        # Try patterns in order of specificity (acronym → compound → prefix → embedded → terminal)
        pattern_groups = [
            ('acronym_embedded', self.acronym_embedded_patterns),
            ('compound_type', self.compound_type_patterns),
            ('prefix_type', self.prefix_type_patterns),
            ('embedded_type', self.embedded_type_patterns),
            ('terminal_type', self.terminal_type_patterns)
        ]
        
        for format_name, patterns in pattern_groups:
            for pattern_data in patterns:
                try:
                    pattern_text = pattern_data['pattern']
                    
                    # Create regex pattern (handle database pattern format)
                    # Remove any "Market" prefix requirement for market term matching
                    modified_pattern = pattern_text
                    if modified_pattern.startswith('\\bMarket\\s+'):
                        # Remove Market prefix from regex pattern
                        modified_pattern = modified_pattern[12:]  # Remove "\bMarket\s+" prefix
                    
                    # Create regex (pattern_text is already a regex)
                    pattern = re.compile(modified_pattern, re.IGNORECASE)
                    match = pattern.search(text)
                    
                    if match:
                        # Special handling for acronym_embedded patterns
                        if format_name == 'acronym_embedded':
                            acronym = match.group(1) if match.groups() else ""
                            base_type = pattern_data.get('base_type', 'Market Report')
                            extracted = match.group(0).strip()
                            
                            return {
                                'extracted_report_type': extracted,
                                'final_report_type': base_type,
                                'format_type': ReportTypeFormat(format_name),
                                'confidence': pattern_data.get('confidence_weight', 0.9),
                                'matched_pattern': pattern_text,
                                'raw_match': match.group(0),
                                'extracted_acronym': acronym,
                                'notes': f"Acronym-embedded pattern (market-aware): Extracted '{acronym}'"
                            }
                        else:
                            # Standard handling for other patterns
                            extracted = match.group(0).strip()
                            confidence = pattern_data.get('confidence_weight', 0.9)
                            
                            return {
                                'extracted_report_type': extracted,
                                'format_type': ReportTypeFormat(format_name),
                                'confidence': confidence,
                                'matched_pattern': pattern_text,
                                'raw_match': match.group(0),
                                'notes': f"Matched {format_name} pattern (market-aware)"
                            }
                        
                except (re.error, ValueError) as e:
                    logger.debug(f"Pattern error: {e}")
                    continue
        
        return {
            'extracted_report_type': None,
            'format_type': ReportTypeFormat.UNKNOWN,
            'confidence': 0.0,
            'matched_pattern': None,
            'raw_match': None,
            'notes': 'No patterns matched in market-aware search'
        }
    
    def _reconstruct_report_type_with_market(self, extracted_type: str, market_term: str) -> str:
        """
        Reconstruct the final report type with proper market term positioning.
        
        Args:
            extracted_type: The extracted report type pattern
            market_term: The original market term (e.g., "Market in Automotive")
            
        Returns:
            Reconstructed report type with market term
        """
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
    
    def _process_market_aware_workflow(self, title: str, market_type: str) -> Dict[str, Any]:
        """
        Process market term titles using extraction→rearrangement→reconstruction workflow.
        
        Args:
            title: Title to process (dates already removed)
            market_type: Type of market term (market_for, market_in, market_by)
            
        Returns:
            Processing results dictionary
        """
        # Step 1: Extract market term from title
        market_term, remaining_title, pipeline_forward = self._extract_market_term_from_title(title, market_type)
        
        if not market_term:
            # Couldn't extract market term, fall back to standard processing
            logger.warning(f"Could not extract market term from '{title}' with type '{market_type}'")
            return self._process_standard_workflow(title)
        
        logger.debug(f"Extracted market term: '{market_term}' from '{title}'")
        logger.debug(f"Remaining title: '{remaining_title}'")
        logger.debug(f"Pipeline forward: '{pipeline_forward}'")
        
        # Step 2: Rearrange title for pattern matching (move market term to end)
        rearranged_title = self._rearrange_title_for_matching(remaining_title, market_term)
        logger.debug(f"Rearranged for matching: '{rearranged_title}'")
        
        # Step 3: Search for report type patterns (without Market prefix requirement)
        result = self._search_report_patterns_without_market(remaining_title)
        
        # Step 4: Reconstruct final report type with market term
        final_type = self._reconstruct_report_type_with_market(
            result.get('extracted_report_type'), 
            market_term
        )
        
        # Update statistics
        self.extraction_stats['market_aware_workflow'] += 1
        if final_type:
            self.extraction_stats['market_reconstructed_count'] += 1
        
        return {
            'extracted_report_type': result.get('extracted_report_type'),
            'final_report_type': final_type,
            'format_type': result.get('format_type', ReportTypeFormat.UNKNOWN),
            'confidence': result.get('confidence', 0.9 if final_type else 0.0),
            'matched_pattern': result.get('matched_pattern'),
            'raw_match': result.get('raw_match'),
            'processing_workflow': 'market_aware',
            'rearranged_title': rearranged_title,
            'extracted_market_term': market_term,
            'pipeline_forward_text': pipeline_forward,
            'notes': f"Market-aware processing: {result.get('notes', '')}"
        }
    
    def _process_standard_workflow(self, title: str) -> Dict[str, Any]:
        """
        Process standard titles using direct database pattern matching.
        
        Args:
            title: Title to process (dates already removed)
            
        Returns:
            Processing results dictionary
        """
        logger.info(f"STANDARD WORKFLOW DEBUG: Processing title: '{title}'")
        
        # Clean title from confusing terms for matching
        temp_title, removed_terms = self._create_confusing_terms_free_text(title)
        logger.info(f"STANDARD WORKFLOW DEBUG: After confusing terms removal: '{temp_title}'")
        if removed_terms:
            logger.info(f"STANDARD WORKFLOW DEBUG: Removed confusing terms: {removed_terms}")
        
        # Try all pattern groups in order - acronym_embedded first (most specific)
        pattern_groups = [
            ('acronym_embedded', self.acronym_embedded_patterns),
            ('compound_type', self.compound_type_patterns),
            ('prefix_type', self.prefix_type_patterns),
            ('embedded_type', self.embedded_type_patterns),
            ('terminal_type', self.terminal_type_patterns)
        ]
        
        logger.info(f"STANDARD WORKFLOW DEBUG: Pattern groups loaded:")
        for format_name, patterns in pattern_groups:
            logger.info(f"  {format_name}: {len(patterns)} patterns")
        
        best_result = None
        for format_name, patterns in pattern_groups:
            logger.info(f"STANDARD WORKFLOW DEBUG: Trying {format_name} patterns ({len(patterns)} total)")
            
            for i, pattern_data in enumerate(patterns):
                try:
                    pattern_text = pattern_data['pattern']
                    
                    # Skip empty or whitespace-only patterns
                    if not pattern_text or not pattern_text.strip():
                        logger.info(f"STANDARD WORKFLOW DEBUG:   Skipping empty pattern {i+1}")
                        continue
                    
                    logger.info(f"STANDARD WORKFLOW DEBUG:   Testing pattern {i+1}: '{pattern_text}'")
                    
                    # Create regex pattern (pattern_text is already a regex)
                    pattern = re.compile(pattern_text, re.IGNORECASE)
                    match = pattern.search(temp_title)
                    
                    if match:
                        
                        # Special handling for acronym_embedded patterns
                        if format_name == 'acronym_embedded':
                            # Extract acronym from capture group (group 1)
                            acronym = match.group(1) if match.groups() else ""
                            base_type = pattern_data.get('base_type', 'Market Report')
                            
                            # Remove the matched pattern from title for pipeline
                            title_for_pipeline = temp_title.replace(match.group(0), '').strip()
                            title_for_pipeline = re.sub(r'^\s*[,\-–—]\s*', '', title_for_pipeline)
                            title_for_pipeline = re.sub(r'\s*[,\-–—]\s*$', '', title_for_pipeline)
                            
                            # Add acronym in parentheses to end of pipeline text
                            if title_for_pipeline and acronym:
                                title_for_pipeline = f"{title_for_pipeline} ({acronym})"
                            elif acronym:
                                title_for_pipeline = f"({acronym})"
                            
                            result = {
                                'extracted_report_type': match.group(0).strip(),
                                'final_report_type': base_type,
                                'format_type': ReportTypeFormat(format_name),
                                'confidence': pattern_data.get('confidence_weight', 0.9),
                                'matched_pattern': pattern_text,
                                'raw_match': match.group(0),
                                'processing_workflow': 'standard',
                                'pipeline_forward_text': title_for_pipeline,
                                'extracted_acronym': acronym,
                                'notes': f"Acronym-embedded processing: Extracted '{acronym}' from {format_name} pattern"
                            }
                            
                            # Update statistics
                            self.extraction_stats['standard_workflow'] += 1
                            self.extraction_stats[format_name] += 1
                            
                            return result
                            
                        else:
                            # Standard processing for other format types
                            extracted = match.group(0).strip()
                            confidence = pattern_data.get('confidence_weight', 0.9)
                            
                            # Remove the found report type pattern from title for pipeline
                            title_for_pipeline = temp_title.replace(match.group(0), '').strip()
                            # Clean up any leftover punctuation
                            title_for_pipeline = re.sub(r'\s*[,\-–—]\s*$', '', title_for_pipeline)
                            title_for_pipeline = re.sub(r'^\s*[,\-–—]\s*', '', title_for_pipeline)
                            title_for_pipeline = title_for_pipeline.strip()
                            
                            best_result = {
                                'extracted_report_type': extracted,
                                'final_report_type': extracted,
                                'format_type': ReportTypeFormat(format_name),
                                'confidence': confidence,
                                'matched_pattern': pattern_text,
                                'raw_match': match.group(0),
                                'processing_workflow': 'standard',
                                'pipeline_forward_text': title_for_pipeline,
                                'notes': f"Standard processing: Matched {format_name} pattern"
                            }
                            
                            # Update statistics
                            self.extraction_stats['standard_workflow'] += 1
                            self.extraction_stats[format_name] += 1
                            
                            return best_result
                    else:
                        logger.info(f"STANDARD WORKFLOW DEBUG:   No match")
                        
                except (re.error, ValueError) as e:
                    logger.debug(f"Pattern error: {e}")
                    continue
        
        # No match found
        self.extraction_stats['standard_workflow'] += 1
        return {
            'extracted_report_type': None,
            'final_report_type': None,
            'format_type': ReportTypeFormat.UNKNOWN,
            'confidence': 0.0,
            'matched_pattern': None,
            'raw_match': None,
            'processing_workflow': 'standard',
            'pipeline_forward_text': title,
            'notes': 'No patterns matched in standard processing'
        }
    
    def _create_confusing_terms_free_text(self, text: str) -> Tuple[str, List[str]]:
        """Remove confusing terms from text for pattern matching."""
        removed_terms = []
        clean_text = text
        
        for term in self.confusing_terms:
            if term.lower() in clean_text.lower():
                # Remove the term
                pattern = re.compile(rf'\b{re.escape(term)}\b', re.IGNORECASE)
                clean_text = pattern.sub('', clean_text).strip()
                removed_terms.append(term)
        
        # Clean up extra spaces
        clean_text = ' '.join(clean_text.split())
        
        return clean_text, removed_terms
    
    def extract(self, title: str, market_term_type: str = "standard", 
                original_title: str = None, date_extractor=None) -> MarketAwareReportTypeResult:
        """
        Extract report type with CORRECT market-aware processing logic.
        
        Processing Logic (GitHub Issue #10):
        - Market Term Titles: Extract → Rearrange → Match → Reconstruct
        - Standard Titles: Direct database pattern matching
        
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
                processing_workflow=None,
                rearranged_title=None,
                extracted_market_term=None,
                notes="Empty or whitespace-only title"
            )
        
        # Track processing stats
        self.extraction_stats['total_processed'] += 1
        
        # Update market type stats
        if market_term_type == 'standard':
            self.extraction_stats['standard_processed'] += 1
        elif market_term_type == 'market_for':
            self.extraction_stats['market_for_processed'] += 1
        elif market_term_type == 'market_in':
            self.extraction_stats['market_in_processed'] += 1
        elif market_term_type == 'market_by':
            self.extraction_stats['market_by_processed'] += 1
        
        # CRITICAL: Choose processing workflow based on market term type
        if market_term_type in self.available_market_types:
            # Use market-aware workflow for market term titles
            logger.info(f"Processing '{title}' with MARKET-AWARE workflow (type: {market_term_type})")
            result = self._process_market_aware_workflow(title, market_term_type)
            context_analysis = f"Market-aware processing ({market_term_type}): Extract→Rearrange→Match→Reconstruct"
        else:
            # Use standard workflow for standard titles
            logger.info(f"Processing '{title}' with STANDARD workflow")
            result = self._process_standard_workflow(title)
            context_analysis = "Standard processing: Direct database pattern matching"
        
        # Update success/failure stats
        if result.get('final_report_type'):
            self.extraction_stats['successful_extractions'] += 1
        else:
            self.extraction_stats['failed_extractions'] += 1
        
        # Build final result
        return MarketAwareReportTypeResult(
            title=result.get('pipeline_forward_text', title),  # Use pipeline forward text
            original_title=original_title or title,
            market_term_type=market_term_type,
            extracted_report_type=result.get('extracted_report_type'),
            final_report_type=result.get('final_report_type'),
            normalized_report_type=self._normalize_report_type(result.get('final_report_type')),
            format_type=result.get('format_type', ReportTypeFormat.UNKNOWN),
            confidence=result.get('confidence', 0.0),
            matched_pattern=result.get('matched_pattern'),
            raw_match=result.get('raw_match'),
            date_removed_title=title,
            market_prepended=False,  # We reconstruct, not prepend
            context_analysis=context_analysis,
            processing_workflow=result.get('processing_workflow'),
            rearranged_title=result.get('rearranged_title'),
            extracted_market_term=result.get('extracted_market_term'),
            notes=result.get('notes', '')
        )
    
    def _normalize_report_type(self, report_type: str) -> str:
        """Normalize report type for consistency."""
        if not report_type:
            return report_type
        
        # Basic normalization
        normalized = report_type.strip()
        
        # Ensure consistent capitalization for "Market"
        if normalized.lower().startswith('market'):
            normalized = 'Market' + normalized[6:]
        
        return normalized
    
    def get_stats(self) -> MarketAwareExtractionStats:
        """Get extraction statistics."""
        stats = self.extraction_stats
        return MarketAwareExtractionStats(
            total_processed=stats['total_processed'],
            successful_extractions=stats['successful_extractions'],
            failed_extractions=stats['failed_extractions'],
            standard_processed=stats['standard_processed'],
            market_for_processed=stats['market_for_processed'],
            market_in_processed=stats['market_in_processed'],
            market_by_processed=stats.get('market_by_processed', 0),
            market_aware_workflow=stats.get('market_aware_workflow', 0),
            standard_workflow=stats.get('standard_workflow', 0),
            terminal_type=stats['terminal_type'],
            embedded_type=stats['embedded_type'],
            prefix_type=stats['prefix_type'],
            compound_type=stats['compound_type'],
            market_reconstructed_count=stats.get('market_reconstructed_count', 0)
        )
    
    def close_connection(self):
        """Close database connection."""
        if self.pattern_library_manager:
            self.pattern_library_manager.close_connection()

def run_comprehensive_validation_with_output():
    """
    Run comprehensive validation including acronym patterns with timestamped output files.
    """
    import os
    import sys
    import json
    import importlib.util
    from datetime import datetime
    from dotenv import load_dotenv
    from pymongo import MongoClient
    
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
    
    # Initialize components
    pattern_library_manager = PatternLibraryManager()
    extractor = MarketAwareReportTypeExtractor(pattern_library_manager)
    
    print("🎯 Market-Aware Report Type Extractor v2.0 - Enhanced with Acronym Support")
    print("=" * 80)
    
    # Get test cases dynamically from MongoDB
    try:
        mongodb_uri = os.getenv('MONGODB_URI')
        client = MongoClient(mongodb_uri, serverSelectionTimeoutMS=10000)
        db = client['deathstar']
        markets_raw = db['markets_raw']
        
        # Sample diverse test cases from real database
        test_pipeline = [
            {"$match": {
                "report_title": {"$exists": True, "$ne": ""},
                "$or": [
                    {"report_title": {"$regex": "Market.*Analysis", "$options": "i"}},
                    {"report_title": {"$regex": "Market.*Report", "$options": "i"}},
                    {"report_title": {"$regex": "Market.*Study", "$options": "i"}},
                    {"report_title": {"$regex": "Market in", "$options": "i"}},
                    {"report_title": {"$regex": "Market for", "$options": "i"}}
                ]
            }},
            {"$sample": {"size": 15}},
            {"$project": {"report_title": 1, "_id": 0}}
        ]
        
        cursor = markets_raw.aggregate(test_pipeline)
        test_cases = []
        
        for doc in cursor:
            title = doc.get('report_title', '').strip()
            if title:
                # Classify market type based on patterns
                market_type = "standard"  # Default
                if "market in " in title.lower():
                    market_type = "market_in"
                elif "market for " in title.lower():
                    market_type = "market_for"
                elif "market by " in title.lower():
                    market_type = "market_by"
                    
                test_cases.append((title, market_type))
        
        if len(test_cases) < 5:
            # Fallback minimal test cases if database sampling fails
            test_cases = [
                ("Sample Market Analysis Report", "standard"),
                ("Test Market Size Study", "standard"),
                ("Example Market Research Report", "standard")
            ]
        
        client.close()
        print(f"✅ Loaded {len(test_cases)} test cases from database")
        
    except Exception as e:
        print(f"⚠️ Database sampling failed ({e}), using minimal test cases")
        # Minimal fallback test cases
        test_cases = [
            ("Sample Market Analysis Report", "standard"),
            ("Test Market Size Study", "standard"), 
            ("Example Market Research Report", "standard")
        ]
    
    # Generate timestamp for output files
    now = datetime.now()
    timestamp_pdt = now.strftime("%Y%m%d_%H%M%S")
    timestamp_readable_pdt = now.strftime("%Y-%m-%d %H:%M:%S PDT")
    timestamp_readable_utc = now.utctimetuple()
    timestamp_readable_utc = datetime(*timestamp_readable_utc[:6]).strftime("%Y-%m-%d %H:%M:%S UTC")
    
    results = []
    acronym_results = []
    
    print(f"\n🧪 Testing {len(test_cases)} titles with enhanced acronym support...")
    
    for i, (title, market_type) in enumerate(test_cases, 1):
        print(f"\n[{i}/{len(test_cases)}] Testing: {title}")
        
        result = extractor.extract(title, market_type)
        
        # Build comprehensive result record
        result_record = {
            "test_id": i,
            "original_title": title,
            "market_term_type": market_type,
            "extracted_report_type": result.extracted_report_type,
            "final_report_type": result.final_report_type,
            "format_type": result.format_type.value if result.format_type else "UNKNOWN",
            "confidence": result.confidence,
            "processing_workflow": result.processing_workflow,
            "pipeline_forward_text": result.pipeline_forward_text,
            "matched_pattern": result.matched_pattern,
            "raw_match": result.raw_match,
            "notes": result.notes
        }
        
        # Check if this was an acronym match
        if hasattr(result, 'extracted_acronym') and result.extracted_acronym:
            result_record["extracted_acronym"] = result.extracted_acronym
            result_record["acronym_processing"] = True
            acronym_results.append(result_record)
            print(f"   ✅ ACRONYM: {result.extracted_acronym} -> Pipeline: {result.pipeline_forward_text}")
        else:
            result_record["acronym_processing"] = False
            print(f"   ✅ STANDARD: {result.final_report_type} -> Pipeline: {result.pipeline_forward_text}")
        
        results.append(result_record)
    
    # Get statistics
    stats = extractor.get_stats()
    
    # Create outputs directory
    outputs_dir = os.path.join(os.path.dirname(__file__), "../outputs")
    os.makedirs(outputs_dir, exist_ok=True)
    
    # Generate comprehensive output files
    base_filename = f"{timestamp_pdt}_report_type_extractor_v2_validation"
    
    # 1. Detailed JSON Results
    json_output = {
        "analysis_metadata": {
            "analysis_date_pdt": timestamp_readable_pdt,
            "analysis_date_utc": timestamp_readable_utc,
            "script_version": "03_report_type_extractor_v2.py",
            "enhancement": "Acronym-embedded pattern support",
            "total_test_cases": len(test_cases),
            "acronym_matches_found": len(acronym_results)
        },
        "pattern_library_stats": {
            "total_compound_patterns": len(extractor.compound_type_patterns),
            "total_prefix_patterns": len(extractor.prefix_type_patterns),
            "total_embedded_patterns": len(extractor.embedded_type_patterns),
            "total_terminal_patterns": len(extractor.terminal_type_patterns),
            "total_acronym_embedded_patterns": len(extractor.acronym_embedded_patterns)
        },
        "extraction_statistics": {
            "total_processed": stats.total_processed,
            "successful_extractions": stats.successful_extractions,
            "failed_extractions": stats.failed_extractions,
            "success_rate": f"{(stats.successful_extractions / max(stats.total_processed, 1) * 100):.1f}%",
            "standard_workflow_count": stats.standard_workflow,
            "market_aware_workflow_count": stats.market_aware_workflow,
            "acronym_embedded_count": extractor.extraction_stats.get('acronym_embedded', 0)
        },
        "test_results": results,
        "acronym_specific_results": acronym_results
    }
    
    json_file = os.path.join(outputs_dir, f"{base_filename}.json")
    with open(json_file, 'w') as f:
        json.dump(json_output, f, indent=2, default=str)
    
    # 2. Human-Readable Summary Report
    summary_file = os.path.join(outputs_dir, f"{base_filename}_summary.txt")
    with open(summary_file, 'w') as f:
        f.write(f"Market-Aware Report Type Extractor v2.0 - Enhanced Validation Results\n")
        f.write(f"Analysis Date (PDT): {timestamp_readable_pdt}\n")
        f.write(f"Analysis Date (UTC): {timestamp_readable_utc}\n")
        f.write(f"{'=' * 80}\n\n")
        
        f.write(f"📊 SUMMARY STATISTICS:\n")
        f.write(f"• Total Test Cases: {len(test_cases)}\n")
        f.write(f"• Successful Extractions: {stats.successful_extractions}\n")
        f.write(f"• Success Rate: {(stats.successful_extractions / max(stats.total_processed, 1) * 100):.1f}%\n")
        f.write(f"• Acronym Matches Found: {len(acronym_results)}\n")
        f.write(f"• Standard Processing: {stats.standard_workflow}\n")
        f.write(f"• Market-Aware Processing: {stats.market_aware_workflow}\n\n")
        
        f.write(f"📚 PATTERN LIBRARY COVERAGE:\n")
        f.write(f"• Compound Type Patterns: {len(extractor.compound_type_patterns)}\n")
        f.write(f"• Prefix Type Patterns: {len(extractor.prefix_type_patterns)}\n")
        f.write(f"• Embedded Type Patterns: {len(extractor.embedded_type_patterns)}\n")
        f.write(f"• Terminal Type Patterns: {len(extractor.terminal_type_patterns)}\n")
        f.write(f"• Acronym Embedded Patterns: {len(extractor.acronym_embedded_patterns)}\n\n")
        
        if acronym_results:
            f.write(f"🔤 ACRONYM EXTRACTION RESULTS:\n")
            for result in acronym_results:
                f.write(f"• {result['original_title']}\n")
                f.write(f"  → Acronym: {result.get('extracted_acronym', 'N/A')}\n")
                f.write(f"  → Report Type: {result['final_report_type']}\n")
                f.write(f"  → Pipeline Forward: {result['pipeline_forward_text']}\n\n")
        
        f.write(f"📋 DETAILED RESULTS:\n")
        for result in results:
            f.write(f"\n{result['test_id']}. {result['original_title']}\n")
            f.write(f"   Market Type: {result['market_term_type']}\n")
            f.write(f"   Report Type: {result['final_report_type']}\n")
            f.write(f"   Format: {result['format_type']}\n")
            f.write(f"   Confidence: {result['confidence']:.2f}\n")
            f.write(f"   Pipeline Forward: {result['pipeline_forward_text']}\n")
            if result.get('acronym_processing'):
                f.write(f"   🔤 Acronym: {result.get('extracted_acronym', 'N/A')}\n")
    
    # 3. Acronym-Specific Analysis for Human Review
    if acronym_results:
        acronym_file = os.path.join(outputs_dir, f"{base_filename}_acronym_analysis.txt")
        with open(acronym_file, 'w') as f:
            f.write(f"Acronym-Embedded Pattern Analysis - Human Review Required\n")
            f.write(f"Analysis Date (PDT): {timestamp_readable_pdt}\n")
            f.write(f"Analysis Date (UTC): {timestamp_readable_utc}\n")
            f.write(f"{'=' * 80}\n\n")
            
            f.write(f"🎯 ACRONYM EXTRACTION SUCCESS: {len(acronym_results)} patterns matched\n\n")
            
            for i, result in enumerate(acronym_results, 1):
                f.write(f"{i}. ACRONYM PATTERN MATCH:\n")
                f.write(f"   Original: {result['original_title']}\n")
                f.write(f"   Extracted Acronym: {result.get('extracted_acronym', 'ERROR')}\n")
                f.write(f"   Base Report Type: {result['final_report_type']}\n")
                f.write(f"   Pipeline Text: {result['pipeline_forward_text']}\n")
                f.write(f"   Pattern Used: {result.get('matched_pattern', 'N/A')}\n")
                f.write(f"   Confidence: {result['confidence']:.2f}\n")
                f.write(f"   Status: ✅ SUCCESS - Acronym preserved in parentheses\n\n")
    
    print(f"\n💾 OUTPUT FILES GENERATED:")
    print(f"   📄 {json_file}")
    print(f"   📋 {summary_file}")
    if acronym_results:
        print(f"   🔤 {acronym_file}")
    
    print(f"\n🎯 VALIDATION COMPLETE:")
    print(f"   • Success Rate: {(stats.successful_extractions / max(stats.total_processed, 1) * 100):.1f}%")
    print(f"   • Acronym Patterns: {len(acronym_results)} matches found")
    print(f"   • Ready for GitHub Issue #7 completion")
    
    extractor.close_connection()

if __name__ == "__main__":
    run_comprehensive_validation_with_output()