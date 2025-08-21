#!/usr/bin/env python3

"""
Topic Extraction System v1.0
Final step in the systematic removal pipeline that extracts clean topics from market research titles
after all other patterns (dates, report types, geographic regions) have been removed.
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

class TopicExtractionFormat(Enum):
    """Enumeration of topic extraction format types."""
    STANDARD_MARKET = "standard_market"      # Standard "Topic Market" pattern
    MARKET_FOR = "market_for"                # "Market for Topic" pattern  
    MARKET_IN = "market_in"                  # "Topic Market in Region" pattern
    TECHNICAL_COMPOUND = "technical_compound" # Complex technical specifications
    UNKNOWN = "unknown"

@dataclass
class TopicExtractionResult:
    """Result of topic extraction."""
    title: str
    original_title: str
    market_term_type: str
    extracted_topic: Optional[str]
    normalized_topic_name: Optional[str]
    format_type: TopicExtractionFormat
    confidence: float
    technical_compounds_preserved: List[str]
    removed_patterns: Dict[str, Any]
    processing_notes: List[str]
    raw_remainder_before_processing: Optional[str] = None

@dataclass
class TopicExtractionStats:
    """Statistics for topic extraction results."""
    total_processed: int
    successful_extractions: int
    standard_market_count: int
    market_for_count: int
    market_in_count: int
    technical_compound_count: int
    failed_extractions: int
    success_rate: float

class TopicExtractor:
    """
    Topic Extraction System for market research titles.
    
    Final component in the systematic removal pipeline that:
    1. Receives titles with extracted elements (dates, report types, regions)
    2. Applies systematic removal: everything before 'Market' minus extracted patterns
    3. Handles three market term types with appropriate processing logic
    4. Preserves technical compounds and creates normalized topic names
    """
    
    def __init__(self, pattern_library_manager=None):
        """
        Initialize the Topic Extractor.
        
        Args:
            pattern_library_manager: Optional PatternLibraryManager for pattern storage
        """
        self.pattern_library_manager = pattern_library_manager
        self.extraction_stats = {
            'total_processed': 0,
            'successful_extractions': 0,
            'standard_market': 0,
            'market_for': 0,
            'market_in': 0,
            'technical_compound': 0,
            'failed_extractions': 0
        }
        
        # Technical compound patterns to preserve
        self._initialize_technical_patterns()
        
        logger.info("TopicExtractor initialized - ready for systematic removal processing")
    
    def _initialize_technical_patterns(self) -> None:
        """Initialize patterns for technical compound preservation."""
        # Common technical compound indicators to preserve
        self.technical_indicators = [
            r'\b\d+[A-Za-z]+\b',  # "5G", "4K", "8-bit"
            r'\b[A-Z]{2,4}\b',    # Acronyms like "AI", "IoT", "API", "HTML"
            r'\b\w*-\w*\b',       # Hyphenated terms
            r'\b\w+\d+\w*\b',     # Terms with embedded numbers
            r'\bIoT\b',           # Specific case for IoT
            r'\bAPI\b',           # Specific case for API
        ]
        
        # Common artifact patterns to clean
        self.artifact_patterns = [
            r'\s*,\s*$',          # Trailing commas
            r'\s*&\s*$',          # Trailing ampersands
            r'^\s*and\s+',        # Leading "and "
            r'^\s*the\s+',        # Leading "the "
            r'\s{2,}',            # Multiple spaces
        ]
        
        logger.debug("Technical compound patterns initialized")
    
    def _get_timestamps(self) -> tuple:
        """Generate PDT and UTC timestamps."""
        utc_now = datetime.now(timezone.utc)
        pdt_tz = pytz.timezone('America/Los_Angeles')
        pdt_now = utc_now.astimezone(pdt_tz)
        
        pdt_str = pdt_now.strftime('%Y-%m-%d %H:%M:%S %Z')
        utc_str = utc_now.strftime('%Y-%m-%d %H:%M:%S UTC')
        
        return pdt_str, utc_str, utc_now
    
    def extract(self, title: str, extracted_elements: Dict[str, Any]) -> TopicExtractionResult:
        """
        Main extraction method that coordinates topic extraction based on market term type.
        
        Args:
            title: Original title
            extracted_elements: Dictionary containing results from previous extractors:
                - market_term_type: "standard", "market_for", or "market_in"
                - extracted_forecast_date_range: Date/range string
                - extracted_report_type: Report type string
                - extracted_regions: List of geographic regions
                
        Returns:
            TopicExtractionResult with extracted topic and metadata
        """
        self.extraction_stats['total_processed'] += 1
        
        # Get market term type from previous extraction
        market_type = extracted_elements.get('market_term_type', 'standard')
        processing_notes = []
        
        logger.debug(f"Processing title '{title}' with market type '{market_type}'")
        
        # Route to appropriate processing method
        try:
            if market_type == "market_for":
                result = self.process_market_for(title, extracted_elements)
            elif market_type == "market_in":
                result = self.process_market_in(title, extracted_elements)
            else:
                result = self.process_standard_market(title, extracted_elements)
            
            if result.extracted_topic:
                self.extraction_stats['successful_extractions'] += 1
                logger.debug(f"Successfully extracted topic: '{result.extracted_topic}'")
            else:
                self.extraction_stats['failed_extractions'] += 1
                logger.warning(f"Failed to extract topic from: '{title}'")
            
            return result
            
        except Exception as e:
            self.extraction_stats['failed_extractions'] += 1
            logger.error(f"Topic extraction failed for '{title}': {e}")
            
            return TopicExtractionResult(
                title=title,
                original_title=title,
                market_term_type=market_type,
                extracted_topic=None,
                normalized_topic_name=None,
                format_type=TopicExtractionFormat.UNKNOWN,
                confidence=0.0,
                technical_compounds_preserved=[],
                removed_patterns=extracted_elements,
                processing_notes=[f"Extraction failed: {str(e)}"]
            )
    
    def process_standard_market(self, title: str, extracted_elements: Dict[str, Any]) -> TopicExtractionResult:
        """
        Handle standard market titles using systematic removal approach.
        
        Logic: Extract everything before 'Market' minus all extracted patterns
        
        Args:
            title: Original title
            extracted_elements: Previously extracted patterns to remove
            
        Returns:
            TopicExtractionResult for standard market processing
        """
        self.extraction_stats['standard_market'] += 1
        processing_notes = []
        
        # Step 1: Find the 'Market' keyword position
        market_match = re.search(r'\bmarket\b', title, re.IGNORECASE)
        if not market_match:
            processing_notes.append("No 'Market' keyword found - using full title")
            text_before_market = title
        else:
            text_before_market = title[:market_match.start()].strip()
            processing_notes.append(f"Extracted text before 'Market': '{text_before_market}'")
        
        # Step 2: Remove all previously extracted patterns
        topic_candidate = self._apply_systematic_removal(
            text_before_market, extracted_elements, processing_notes
        )
        
        # Step 3: Preserve technical compounds and clean artifacts
        final_topic = self.preserve_technical_compounds(topic_candidate)
        final_topic = self._clean_artifacts(final_topic)
        
        # Step 4: Generate normalized topic name
        normalized_name = self.normalize_topic(final_topic) if final_topic else None
        
        # Step 5: Calculate confidence
        confidence = self._calculate_confidence(final_topic, TopicExtractionFormat.STANDARD_MARKET)
        
        processing_notes.append(f"Final topic: '{final_topic}'")
        
        return TopicExtractionResult(
            title=title,
            original_title=title,
            market_term_type="standard",
            extracted_topic=final_topic,
            normalized_topic_name=normalized_name,
            format_type=TopicExtractionFormat.STANDARD_MARKET,
            confidence=confidence,
            technical_compounds_preserved=self._find_technical_compounds(final_topic or ""),
            removed_patterns=extracted_elements,
            processing_notes=processing_notes,
            raw_remainder_before_processing=text_before_market
        )
    
    def process_market_for(self, title: str, extracted_elements: Dict[str, Any]) -> TopicExtractionResult:
        """
        Handle 'Market for' pattern titles with concatenation processing.
        
        Logic: Extract topic after 'for' keyword, then remove extracted patterns
        
        Args:
            title: Original title  
            extracted_elements: Previously extracted patterns to remove
            
        Returns:
            TopicExtractionResult for market for processing
        """
        self.extraction_stats['market_for'] += 1
        processing_notes = []
        
        # Step 1: Find text after 'market for'
        market_for_match = re.search(r'\bmarket\s+for\s+(.+)', title, re.IGNORECASE)
        if not market_for_match:
            processing_notes.append("'Market for' pattern not found - falling back to standard processing")
            return self.process_standard_market(title, extracted_elements)
        
        text_after_for = market_for_match.group(1).strip()
        processing_notes.append(f"Extracted text after 'Market for': '{text_after_for}'")
        
        # Step 2: Remove extracted patterns from the topic area
        topic_candidate = self._apply_systematic_removal(
            text_after_for, extracted_elements, processing_notes
        )
        
        # Step 3: Handle special concatenation requirements for 'Market for' patterns
        final_topic = self._handle_market_for_concatenation(topic_candidate, processing_notes)
        
        # Step 4: Preserve technical compounds and clean artifacts
        final_topic = self.preserve_technical_compounds(final_topic)
        final_topic = self._clean_artifacts(final_topic)
        
        # Step 5: Generate normalized topic name
        normalized_name = self.normalize_topic(final_topic) if final_topic else None
        
        # Step 6: Calculate confidence
        confidence = self._calculate_confidence(final_topic, TopicExtractionFormat.MARKET_FOR)
        
        processing_notes.append(f"Final topic with concatenation: '{final_topic}'")
        
        return TopicExtractionResult(
            title=title,
            original_title=title,
            market_term_type="market_for",
            extracted_topic=final_topic,
            normalized_topic_name=normalized_name,
            format_type=TopicExtractionFormat.MARKET_FOR,
            confidence=confidence,
            technical_compounds_preserved=self._find_technical_compounds(final_topic or ""),
            removed_patterns=extracted_elements,
            processing_notes=processing_notes,
            raw_remainder_before_processing=text_after_for
        )
    
    def process_market_in(self, title: str, extracted_elements: Dict[str, Any]) -> TopicExtractionResult:
        """
        Handle 'Market in' pattern titles with context integration processing.
        
        Logic: Extract topic before 'market in' and integrate geographic context
        
        Args:
            title: Original title
            extracted_elements: Previously extracted patterns to remove
            
        Returns:
            TopicExtractionResult for market in processing
        """
        self.extraction_stats['market_in'] += 1
        processing_notes = []
        
        # Step 1: Find text before 'market in'
        market_in_match = re.search(r'(.+?)\s+market\s+in\s+', title, re.IGNORECASE)
        if not market_in_match:
            processing_notes.append("'Market in' pattern not found - falling back to standard processing")
            return self.process_standard_market(title, extracted_elements)
        
        text_before_market_in = market_in_match.group(1).strip()
        processing_notes.append(f"Extracted text before 'Market in': '{text_before_market_in}'")
        
        # Step 2: Remove extracted patterns (except regions which provide context)
        elements_without_regions = extracted_elements.copy()
        regions = elements_without_regions.pop('extracted_regions', [])
        
        topic_candidate = self._apply_systematic_removal(
            text_before_market_in, elements_without_regions, processing_notes
        )
        
        # Step 3: Handle context integration for 'Market in' patterns
        final_topic = self._handle_market_in_context(topic_candidate, regions, processing_notes)
        
        # Step 4: Preserve technical compounds and clean artifacts
        final_topic = self.preserve_technical_compounds(final_topic)
        final_topic = self._clean_artifacts(final_topic)
        
        # Step 5: Generate normalized topic name
        normalized_name = self.normalize_topic(final_topic) if final_topic else None
        
        # Step 6: Calculate confidence
        confidence = self._calculate_confidence(final_topic, TopicExtractionFormat.MARKET_IN)
        
        processing_notes.append(f"Final topic with context integration: '{final_topic}'")
        
        return TopicExtractionResult(
            title=title,
            original_title=title,
            market_term_type="market_in",
            extracted_topic=final_topic,
            normalized_topic_name=normalized_name,
            format_type=TopicExtractionFormat.MARKET_IN,
            confidence=confidence,
            technical_compounds_preserved=self._find_technical_compounds(final_topic or ""),
            removed_patterns=extracted_elements,
            processing_notes=processing_notes,
            raw_remainder_before_processing=text_before_market_in
        )
    
    def _apply_systematic_removal(self, text: str, extracted_elements: Dict[str, Any], 
                                 processing_notes: List[str]) -> str:
        """
        Apply systematic removal of all extracted patterns from the text.
        
        Args:
            text: Text to process
            extracted_elements: Dictionary of patterns to remove
            processing_notes: List to append processing notes to
            
        Returns:
            Text with patterns removed
        """
        remaining_text = text
        
        # Remove dates
        if extracted_elements.get('extracted_forecast_date_range'):
            date_pattern = extracted_elements['extracted_forecast_date_range']
            # Remove the actual date pattern and common date separators
            remaining_text = re.sub(rf'\b{re.escape(date_pattern)}\b', '', remaining_text, flags=re.IGNORECASE)
            remaining_text = re.sub(r',\s*$', '', remaining_text)  # Remove trailing comma
            processing_notes.append(f"Removed date pattern: '{date_pattern}'")
        
        # Remove report types
        if extracted_elements.get('extracted_report_type'):
            report_type = extracted_elements['extracted_report_type']
            # Remove report type and common connectors
            remaining_text = re.sub(rf'\b{re.escape(report_type)}\b', '', remaining_text, flags=re.IGNORECASE)
            remaining_text = re.sub(r'\s*&\s*share\b', '', remaining_text, flags=re.IGNORECASE)  # Common artifact
            processing_notes.append(f"Removed report type: '{report_type}'")
        
        # Remove geographic regions
        if extracted_elements.get('extracted_regions'):
            regions = extracted_elements['extracted_regions']
            for region in regions:
                remaining_text = re.sub(rf'\b{re.escape(region)}\b', '', remaining_text, flags=re.IGNORECASE)
                remaining_text = re.sub(r'\s*&\s*', ' ', remaining_text)  # Clean up ampersands
                processing_notes.append(f"Removed region: '{region}'")
        
        # Clean up extra whitespace and common connectors
        remaining_text = re.sub(r'\s*&\s*', ' ', remaining_text)
        remaining_text = re.sub(r'\s{2,}', ' ', remaining_text)
        remaining_text = remaining_text.strip()
        
        processing_notes.append(f"After systematic removal: '{remaining_text}'")
        return remaining_text
    
    def _handle_market_for_concatenation(self, topic: str, processing_notes: List[str]) -> str:
        """Handle special concatenation requirements for 'Market for' patterns."""
        if not topic:
            return topic
        
        # For 'Market for' patterns, concatenate components if multiple terms
        # This maintains the relationship between the market and its focus
        components = topic.split()
        if len(components) > 1:
            # Join with appropriate connectors for readability
            concatenated = " ".join(components)
            processing_notes.append(f"Applied market_for concatenation: '{concatenated}'")
            return concatenated
        
        return topic
    
    def _handle_market_in_context(self, topic: str, regions: List[str], 
                                 processing_notes: List[str]) -> str:
        """Handle context integration for 'Market in' patterns."""
        if not topic:
            return topic
        
        # For 'Market in' patterns, the topic is the core subject
        # Regions provide context but are handled separately
        # Just ensure the topic is clean and well-formed
        if regions:
            processing_notes.append(f"Context preserved for regions: {regions}")
        
        return topic
    
    def preserve_technical_compounds(self, topic: str) -> str:
        """
        Preserve technical compounds and specifications in topics.
        
        Args:
            topic: Topic text to process
            
        Returns:
            Topic with technical compounds preserved
        """
        if not topic:
            return topic
        
        # Preserve existing formatting for technical terms
        # This method ensures we don't accidentally break technical specifications
        preserved_topic = topic
        
        # Log technical compounds found
        technical_compounds = self._find_technical_compounds(topic)
        if technical_compounds:
            logger.debug(f"Preserved technical compounds: {technical_compounds}")
        
        return preserved_topic
    
    def _find_technical_compounds(self, text: str) -> List[str]:
        """Find technical compounds in text using predefined patterns."""
        if not text:
            return []
        
        compounds = []
        for pattern in self.technical_indicators:
            matches = re.findall(pattern, text)
            compounds.extend(matches)
        
        return list(set(compounds))  # Remove duplicates
    
    def normalize_topic(self, topic: str) -> Optional[str]:
        """
        Create standardized topic name for system use.
        
        Args:
            topic: Original topic text
            
        Returns:
            Normalized topic name (lowercase, hyphenated)
        """
        if not topic:
            return None
        
        # Convert to lowercase and replace spaces/special chars with hyphens
        normalized = topic.lower()
        normalized = re.sub(r'[^\w\s-]', '', normalized)  # Remove special chars except hyphens
        normalized = re.sub(r'[\s_]+', '-', normalized)   # Replace spaces/underscores with hyphens
        normalized = re.sub(r'-+', '-', normalized)       # Collapse multiple hyphens
        normalized = normalized.strip('-')                # Remove leading/trailing hyphens
        
        return normalized if normalized else None
    
    def _clean_artifacts(self, text: str) -> str:
        """Clean common artifacts from extracted topics."""
        if not text:
            return text
        
        cleaned = text
        for pattern in self.artifact_patterns:
            cleaned = re.sub(pattern, '', cleaned)
        
        return cleaned.strip()
    
    def _calculate_confidence(self, topic: str, format_type: TopicExtractionFormat) -> float:
        """
        Calculate confidence score for topic extraction.
        
        Args:
            topic: Extracted topic
            format_type: Type of extraction performed
            
        Returns:
            Confidence score between 0.0 and 1.0
        """
        if not topic:
            return 0.0
        
        confidence = 0.5  # Base confidence
        
        # Higher confidence for longer, more specific topics
        if len(topic.split()) >= 2:
            confidence += 0.2
        
        # Higher confidence for technical compounds
        if self._find_technical_compounds(topic):
            confidence += 0.15
        
        # Format-specific adjustments
        if format_type == TopicExtractionFormat.STANDARD_MARKET:
            confidence += 0.1  # Standard processing is most reliable
        elif format_type in [TopicExtractionFormat.MARKET_FOR, TopicExtractionFormat.MARKET_IN]:
            confidence += 0.05  # Special patterns are slightly less reliable
        
        # Penalize very short or suspicious topics
        if len(topic.strip()) < 3:
            confidence -= 0.3
        
        return round(min(max(confidence, 0.0), 1.0), 3)
    
    def get_confidence(self) -> Dict[str, float]:
        """Return confidence metrics for the extraction process."""
        total = self.extraction_stats['total_processed']
        if total == 0:
            return {'overall_confidence': 0.0, 'success_rate': 0.0}
        
        success_rate = self.extraction_stats['successful_extractions'] / total
        
        return {
            'overall_confidence': round(success_rate * 0.9, 3),  # Conservative estimate
            'success_rate': round(success_rate, 3)
        }
    
    def get_extraction_statistics(self) -> TopicExtractionStats:
        """Get current extraction statistics."""
        total = self.extraction_stats['total_processed']
        
        if total == 0:
            return TopicExtractionStats(
                total_processed=0,
                successful_extractions=0,
                standard_market_count=0,
                market_for_count=0,
                market_in_count=0,
                technical_compound_count=0,
                failed_extractions=0,
                success_rate=0.0
            )
        
        return TopicExtractionStats(
            total_processed=total,
            successful_extractions=self.extraction_stats['successful_extractions'],
            standard_market_count=self.extraction_stats['standard_market'],
            market_for_count=self.extraction_stats['market_for'],
            market_in_count=self.extraction_stats['market_in'],
            technical_compound_count=self.extraction_stats['technical_compound'],
            failed_extractions=self.extraction_stats['failed_extractions'],
            success_rate=round((self.extraction_stats['successful_extractions'] / total), 3)
        )
    
    def export_extraction_report(self, filename: Optional[str] = None) -> str:
        """
        Export topic extraction statistics to a formatted report.
        
        Args:
            filename: Optional filename to save report to
            
        Returns:
            Report content as string
        """
        pdt_time, utc_time, _ = self._get_timestamps()
        stats = self.get_extraction_statistics()
        confidence_metrics = self.get_confidence()
        
        report = f"""Topic Extraction System Report
{'='*50}
Analysis Date (PDT): {pdt_time}
Analysis Date (UTC): {utc_time}
{'='*50}

Processing Summary:
  Total Titles Processed: {stats.total_processed:,}
  Successful Extractions: {stats.successful_extractions:,}
  Success Rate:           {stats.success_rate:.1%}
  
Market Pattern Distribution:
  Standard Market:        {stats.standard_market_count:6,} ({(stats.standard_market_count/stats.total_processed)*100:6.2f}%)
  Market For Patterns:    {stats.market_for_count:6,} ({(stats.market_for_count/stats.total_processed)*100:6.2f}%)
  Market In Patterns:     {stats.market_in_count:6,} ({(stats.market_in_count/stats.total_processed)*100:6.2f}%)
  Technical Compounds:    {stats.technical_compound_count:6,} ({(stats.technical_compound_count/stats.total_processed)*100:6.2f}%)

Quality Metrics:
  Overall Confidence:     {confidence_metrics['overall_confidence']:.1%}
  Processing Success:     {stats.success_rate:.1%}
  Failed Extractions:     {stats.failed_extractions:,}

Systematic Removal Performance:
  Target Accuracy:        92-95%
  Current Success Rate:   {stats.success_rate:.1%}
  Performance Status:     {'✅ Within Target' if stats.success_rate >= 0.92 else '⚠️ Below Target'}
"""
        
        if filename:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(report)
            logger.info(f"Topic extraction report exported to {filename}")
        
        return report


def demo_topic_extraction():
    """Demonstrate TopicExtractor functionality."""
    
    print("Topic Extraction System Demo")
    print("=" * 50)
    
    # Sample titles with mock extracted elements
    sample_data = [
        {
            'title': "Global Artificial Intelligence Market Size & Share Report, 2030",
            'extracted_elements': {
                'market_term_type': 'standard',
                'extracted_forecast_date_range': '2030',
                'extracted_report_type': 'Market Size & Share Report',
                'extracted_regions': ['Global']
            }
        },
        {
            'title': "APAC Personal Protective Equipment Market Analysis",
            'extracted_elements': {
                'market_term_type': 'standard',
                'extracted_forecast_date_range': None,
                'extracted_report_type': 'Market Analysis',
                'extracted_regions': ['APAC']
            }
        },
        {
            'title': "Global Market for Advanced Materials in Aerospace, 2030",
            'extracted_elements': {
                'market_term_type': 'market_for',
                'extracted_forecast_date_range': '2030',
                'extracted_report_type': None,
                'extracted_regions': ['Global']
            }
        },
        {
            'title': "Pharmaceutical Market in North America Analysis",
            'extracted_elements': {
                'market_term_type': 'market_in',
                'extracted_forecast_date_range': None,
                'extracted_report_type': 'Analysis',
                'extracted_regions': ['North America']
            }
        }
    ]
    
    try:
        # Initialize extractor
        extractor = TopicExtractor()
        
        print("\n1. Topic Extraction Examples:")
        print("-" * 40)
        
        for i, sample in enumerate(sample_data, 1):
            title = sample['title']
            extracted_elements = sample['extracted_elements']
            
            result = extractor.extract(title, extracted_elements)
            
            print(f"\n{i}. Title: {title}")
            print(f"   Market Type: {result.market_term_type}")
            print(f"   Extracted Topic: '{result.extracted_topic}'")
            print(f"   Normalized Name: '{result.normalized_topic_name}'")
            print(f"   Confidence: {result.confidence:.3f}")
            print(f"   Format: {result.format_type.value}")
            if result.technical_compounds_preserved:
                print(f"   Technical Compounds: {result.technical_compounds_preserved}")
            print(f"   Notes: {'; '.join(result.processing_notes[-2:])}")  # Show last 2 notes
        
        # Get statistics
        print("\n2. Processing Statistics:")
        print("-" * 40)
        
        stats = extractor.get_extraction_statistics()
        confidence_metrics = extractor.get_confidence()
        
        print(f"Total Processed: {stats.total_processed}")
        print(f"Success Rate: {stats.success_rate:.1%}")
        print(f"Overall Confidence: {confidence_metrics['overall_confidence']:.1%}")
        print(f"Standard Market: {stats.standard_market_count}")
        print(f"Market For: {stats.market_for_count}")
        print(f"Market In: {stats.market_in_count}")
        
        # Export report
        print("\n3. Detailed Extraction Report:")
        print("-" * 40)
        
        report = extractor.export_extraction_report()
        print(report)
        
        print("✅ Topic Extraction System demo completed successfully!")
        
    except Exception as e:
        print(f"❌ Demo failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    demo_topic_extraction()