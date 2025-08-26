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
                    
            logger.info(f"Loaded {len(patterns)} report type patterns from database")
            logger.info(f"  Terminal: {len(self.terminal_type_patterns)}")
            logger.info(f"  Embedded: {len(self.embedded_type_patterns)}")
            logger.info(f"  Prefix: {len(self.prefix_type_patterns)}")
            logger.info(f"  Compound: {len(self.compound_type_patterns)}")
            
        except Exception as e:
            logger.error(f"Error loading patterns: {e}")
            # Initialize empty if load fails
            self.terminal_type_patterns = []
            self.embedded_type_patterns = []
            self.prefix_type_patterns = []
            self.compound_type_patterns = []
    
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
        # Try patterns in order of complexity (compound → prefix → embedded → terminal)
        pattern_groups = [
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
        # Clean title from confusing terms for matching
        temp_title, removed_terms = self._create_confusing_terms_free_text(title)
        
        # Try all pattern groups in order
        pattern_groups = [
            ('compound_type', self.compound_type_patterns),
            ('prefix_type', self.prefix_type_patterns),
            ('embedded_type', self.embedded_type_patterns),
            ('terminal_type', self.terminal_type_patterns)
        ]
        
        best_result = None
        for format_name, patterns in pattern_groups:
            for pattern_data in patterns:
                try:
                    pattern_text = pattern_data['pattern']
                    
                    # Create regex pattern (pattern_text is already a regex)
                    pattern = re.compile(pattern_text, re.IGNORECASE)
                    match = pattern.search(temp_title)
                    
                    if match:
                        extracted = match.group(0).strip()
                        confidence = pattern_data.get('confidence_weight', 0.9)
                        
                        best_result = {
                            'extracted_report_type': extracted,
                            'final_report_type': extracted,
                            'format_type': ReportTypeFormat(format_name),
                            'confidence': confidence,
                            'matched_pattern': pattern_text,
                            'raw_match': match.group(0),
                            'processing_workflow': 'standard',
                            'pipeline_forward_text': title,
                            'notes': f"Standard processing: Matched {format_name} pattern"
                        }
                        
                        # Update statistics
                        self.extraction_stats['standard_workflow'] += 1
                        self.extraction_stats[format_name] += 1
                        
                        return best_result
                        
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

if __name__ == "__main__":
    # Test the corrected market-aware extractor
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
    
    # Initialize components
    pattern_library_manager = PatternLibraryManager()
    extractor = MarketAwareReportTypeExtractor(pattern_library_manager)
    
    print("🎯 Market-Aware Report Type Extractor v2.0 - CORRECTED Implementation")
    print("=" * 70)
    
    # Test cases demonstrating proper workflow
    test_cases = [
        # Market In examples
        ("AI Market in Automotive Outlook & Trends", "market_in"),
        ("Retail Market in Singapore - Size, Outlook & Statistics", "market_in"),
        
        # Market For examples  
        ("Veterinary Vaccine Market for Livestock Analysis", "market_for"),
        ("Global Market for Advanced Materials Report", "market_for"),
        
        # Standard examples
        ("Electric Vehicle Market Size Report", "standard"),
        ("Healthcare Technology Market Analysis", "standard"),
        ("APAC Personal Protective Equipment Market Analysis", "standard"),
    ]
    
    for title, market_type in test_cases:
        result = extractor.extract(title, market_type)
        
        print(f"\n📊 Title: {title}")
        print(f"   Market Type: {market_type}")
        print(f"   Processing Workflow: {result.processing_workflow}")
        if result.extracted_market_term:
            print(f"   Extracted Market Term: {result.extracted_market_term}")
        if result.rearranged_title:
            print(f"   Rearranged Title: {result.rearranged_title}")
        print(f"   Extracted Report Type: {result.extracted_report_type}")
        print(f"   Final Report Type: {result.final_report_type}")
        print(f"   Pipeline Forward: {result.title}")
        print(f"   Confidence: {result.confidence:.2f}")
        print(f"   Notes: {result.notes}")
    
    print("\n" + "=" * 70)
    print("📈 Statistics:")
    stats = extractor.get_stats()
    print(f"   Total Processed: {stats.total_processed}")
    print(f"   Successful: {stats.successful_extractions}")
    print(f"   Failed: {stats.failed_extractions}")
    print(f"   Market-Aware Workflow: {stats.market_aware_workflow}")
    print(f"   Standard Workflow: {stats.standard_workflow}")
    print(f"   Market Reconstructed: {stats.market_reconstructed_count}")
    
    extractor.close_connection()