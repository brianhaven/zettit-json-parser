#!/usr/bin/env python3

"""
Geographic Entity Detection System v1.0
Extracts geographic entities from market research titles using MongoDB pattern libraries
with compound-first processing and optional NLP model enhancement.
Created for Market Research Title Parser project.
"""

import os
import re
import logging
import time
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple, Any, Union
from dataclasses import dataclass
from enum import Enum
from collections import Counter, defaultdict
import pytz
from dotenv import load_dotenv
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError

# Import pattern library manager
try:
    from pattern_library_manager_v1 import PatternLibraryManager, PatternType
except ImportError:
    print("Warning: Could not import PatternLibraryManager. Some functionality may be limited.")
    PatternLibraryManager = None
    PatternType = None

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class EntityType(Enum):
    """Types of geographic entities."""
    COUNTRY = "country"
    REGION = "region"
    CITY = "city"
    ACRONYM = "acronym"
    COMPOUND = "compound"

@dataclass
class DetectedEntity:
    """Represents a detected geographic entity."""
    entity: str
    entity_type: EntityType
    start_pos: int
    end_pos: int
    confidence: float
    source: str  # 'mongodb', 'spacy', 'gliner'
    aliases_matched: List[str] = None
    priority: int = 5

@dataclass
class DetectionResult:
    """Result of geographic entity detection."""
    title: str
    entities: List[DetectedEntity]
    extracted_regions: List[str]  # Final extracted list preserving order
    confidence_score: float
    processing_notes: List[str]
    detection_method: str

@dataclass
class DetectionStats:
    """Statistics for detection results."""
    total_processed: int
    titles_with_entities: int
    titles_without_entities: int
    total_entities_detected: int
    average_entities_per_title: float
    detection_rate: float

class GeographicEntityDetector:
    """
    Geographic Entity Detection System for market research titles.
    
    Features:
    - MongoDB pattern library integration with 363+ entities
    - Compound-first processing (e.g., "North America" before "America")
    - Priority-based entity resolution
    - Optional spaCy and GLiNER model integration
    - Performance tracking and confidence scoring
    """
    
    def __init__(self, pattern_library_manager=None, use_models=False):
        """
        Initialize the Geographic Entity Detector.
        
        Args:
            pattern_library_manager: Optional PatternLibraryManager instance
            use_models: Whether to enable NLP model integration
        """
        self.pattern_library_manager = pattern_library_manager or self._create_pattern_manager()
        self.use_models = use_models
        
        # Detection statistics
        self.detection_stats = {
            'total_processed': 0,
            'titles_with_entities': 0,
            'total_entities_detected': 0,
            'compound_entities_detected': 0,
            'model_entities_detected': 0
        }
        
        # Entity cache for performance
        self._entity_cache = {}
        self._cache_ttl = 300  # 5 minutes
        self._cache_timestamps = {}
        
        # Load geographic entities from MongoDB
        self._load_geographic_patterns()
        
        # Initialize NLP models if requested
        self.spacy_model = None
        self.gliner_model = None
        if use_models:
            self._initialize_nlp_models()
    
    def _create_pattern_manager(self) -> Optional[PatternLibraryManager]:
        """Create pattern library manager if available."""
        if PatternLibraryManager:
            try:
                return PatternLibraryManager()
            except Exception as e:
                logger.warning(f"Could not create PatternLibraryManager: {e}")
        return None
    
    def _get_timestamps(self) -> tuple:
        """Generate PDT and UTC timestamps."""
        utc_now = datetime.now(timezone.utc)
        pdt_tz = pytz.timezone('America/Los_Angeles')
        pdt_now = utc_now.astimezone(pdt_tz)
        
        pdt_str = pdt_now.strftime('%Y-%m-%d %H:%M:%S %Z')
        utc_str = utc_now.strftime('%Y-%m-%d %H:%M:%S UTC')
        
        return pdt_str, utc_str, utc_now
    
    def _load_geographic_patterns(self) -> None:
        """Load geographic entity patterns from MongoDB."""
        if not self.pattern_library_manager:
            logger.warning("No pattern library manager available, using fallback patterns")
            self._load_fallback_patterns()
            return
        
        try:
            # Load geographic entities from MongoDB
            geo_patterns = self.pattern_library_manager.get_patterns(
                PatternType.GEOGRAPHIC_ENTITY, 
                active_only=True
            )
            
            # Organize by priority for compound-first processing
            self.geographic_entities = defaultdict(list)
            self.entity_aliases = {}
            self.entity_metadata = {}
            
            for pattern in geo_patterns:
                priority = pattern.get('priority', 5)
                entity = pattern['term']
                aliases = pattern.get('aliases', [])
                
                self.geographic_entities[priority].append(entity)
                
                # Store aliases mapping
                for alias in aliases:
                    self.entity_aliases[alias.lower()] = entity
                
                # Store metadata
                self.entity_metadata[entity] = {
                    'id': str(pattern['_id']),
                    'aliases': aliases,
                    'priority': priority,
                    'entity_type': self._determine_entity_type(entity)
                }
            
            # Sort priorities to ensure compound-first processing
            self.priority_order = sorted(self.geographic_entities.keys())
            
            total_entities = sum(len(entities) for entities in self.geographic_entities.values())
            logger.info(f"Loaded {total_entities} geographic entities from MongoDB with {len(self.priority_order)} priority levels")
            
        except Exception as e:
            logger.error(f"Failed to load geographic patterns from MongoDB: {e}")
            self._load_fallback_patterns()
    
    def _load_fallback_patterns(self) -> None:
        """Load fallback geographic patterns if MongoDB is unavailable."""
        logger.info("Loading fallback geographic patterns")
        
        # Basic geographic entities organized by priority
        fallback_patterns = {
            1: [  # Compound entities - highest priority
                'North America', 'South America', 'Latin America', 'Central America',
                'Middle East', 'Far East', 'Southeast Asia', 'South Asia', 'East Asia',
                'Eastern Europe', 'Western Europe', 'Central Europe', 'Northern Europe',
                'Sub-Saharan Africa', 'North Africa', 'West Africa', 'East Africa',
                'Asia Pacific', 'Asia-Pacific'
            ],
            2: [  # Regional acronyms
                'APAC', 'EMEA', 'MEA', 'ASEAN', 'NAFTA', 'GCC', 'LATAM', 'MENA', 'BRICS'
            ],
            3: [  # Major regions
                'Europe', 'Asia', 'Africa', 'America', 'Pacific', 'Caribbean', 'Scandinavia'
            ],
            4: [  # Countries
                'United States', 'United Kingdom', 'Germany', 'France', 'China', 'Japan', 
                'India', 'Brazil', 'Canada', 'Australia', 'Russia', 'Italy', 'Spain'
            ],
            5: [  # Country codes and abbreviations
                'USA', 'US', 'UK', 'EU'
            ]
        }
        
        self.geographic_entities = fallback_patterns
        self.priority_order = sorted(self.geographic_entities.keys())
        self.entity_aliases = {
            'usa': 'United States',
            'us': 'United States', 
            'uk': 'United Kingdom',
            'na': 'North America',
            'sa': 'South America'
        }
        self.entity_metadata = {}
        
        # Generate metadata for fallback patterns
        for priority, entities in fallback_patterns.items():
            for entity in entities:
                self.entity_metadata[entity] = {
                    'id': f'fallback_{entity.lower().replace(" ", "_")}',
                    'aliases': [],
                    'priority': priority,
                    'entity_type': self._determine_entity_type(entity)
                }
        
        total_entities = sum(len(entities) for entities in self.geographic_entities.values())
        logger.info(f"Loaded {total_entities} fallback geographic entities")
    
    def _determine_entity_type(self, entity: str) -> EntityType:
        """Determine the type of geographic entity."""
        entity_lower = entity.lower()
        
        if len(entity) <= 5 and entity.isupper():
            return EntityType.ACRONYM
        elif any(compound in entity_lower for compound in ['north', 'south', 'east', 'west', 'central', 'sub-']):
            return EntityType.COMPOUND
        elif entity_lower in ['europe', 'asia', 'africa', 'america', 'pacific', 'middle east', 'far east']:
            return EntityType.REGION
        elif entity_lower in ['united states', 'united kingdom', 'germany', 'france', 'china', 'japan', 'india']:
            return EntityType.COUNTRY
        else:
            return EntityType.REGION  # Default
    
    def _initialize_nlp_models(self) -> None:
        """Initialize spaCy and GLiNER models if available."""
        logger.info("Initializing NLP models...")
        
        # API configuration for Zettit Model Router (placeholder)
        self.use_api = os.getenv('USE_ZETTIT_MODEL_API', 'false').lower() == 'true'
        self.api_endpoint = os.getenv('ZETTIT_MODEL_API_ENDPOINT', 'https://api.zettit.com/models')
        self.api_key = os.getenv('ZETTIT_MODEL_API_KEY')
        
        # Initialize spaCy model
        try:
            import spacy
            # Try to load models in priority order: large -> medium -> small
            spacy_models_to_try = [
                ("en_core_web_lg", "large"),
                ("en_core_web_md", "medium"), 
                ("en_core_web_sm", "small")
            ]
            
            for model_name, model_size in spacy_models_to_try:
                try:
                    self.spacy_model = spacy.load(model_name)
                    logger.info(f"Loaded spaCy {model_name} ({model_size}) model successfully")
                    
                    # Configure spaCy for geographic entity detection only
                    # Focus on GPE (Geopolitical entities) and LOC (Locations)
                    self.target_entity_types = ['GPE', 'LOC']
                    logger.info(f"spaCy configured to detect entity types: {self.target_entity_types}")
                    break
                except OSError:
                    logger.debug(f"spaCy {model_name} not available, trying next...")
                    continue
            else:
                logger.warning("No spaCy model found. Install with: python -m spacy download en_core_web_md")
                self.spacy_model = None
                self.target_entity_types = []
        except ImportError:
            logger.warning("spaCy not installed. Install with: pip install spacy")
            self.spacy_model = None
            self.target_entity_types = []
        
        # Initialize GLiNER model (placeholder - skipped due to disk space)
        self.gliner_model = None
        logger.info("GLiNER integration skipped (disk space optimization)")
    
    def _detect_with_patterns(self, title: str) -> List[DetectedEntity]:
        """Detect geographic entities using MongoDB patterns with compound-first processing."""
        detected_entities = []
        processed_title = title.lower()
        
        # Track positions already matched to avoid overlaps
        matched_positions = set()
        
        # Process by priority (compound entities first)
        for priority in self.priority_order:
            entities = self.geographic_entities[priority]
            
            for entity in entities:
                # Create regex pattern with word boundaries
                pattern = r'\b' + re.escape(entity) + r'\b'
                
                for match in re.finditer(pattern, title, re.IGNORECASE):
                    start_pos = match.start()
                    end_pos = match.end()
                    
                    # Check for overlaps with higher priority matches
                    if any(pos in range(start_pos, end_pos) for pos in matched_positions):
                        continue
                    
                    # Add matched positions to avoid future overlaps
                    matched_positions.update(range(start_pos, end_pos))
                    
                    detected_entity = DetectedEntity(
                        entity=entity,
                        entity_type=self.entity_metadata.get(entity, {}).get('entity_type', EntityType.REGION),
                        start_pos=start_pos,
                        end_pos=end_pos,
                        confidence=0.9,  # High confidence for pattern matches
                        source='mongodb',
                        priority=priority
                    )
                    detected_entities.append(detected_entity)
                    
                    # Track success if pattern manager available
                    if self.pattern_library_manager and entity in self.entity_metadata:
                        pattern_id = self.entity_metadata[entity]['id']
                        if pattern_id.startswith('fallback_'):
                            continue  # Don't track fallback patterns
                        try:
                            self.pattern_library_manager.track_success(pattern_id)
                        except:
                            pass  # Ignore tracking errors
        
        # Check aliases
        for alias, canonical_entity in self.entity_aliases.items():
            pattern = r'\b' + re.escape(alias) + r'\b'
            
            for match in re.finditer(pattern, title, re.IGNORECASE):
                start_pos = match.start()
                end_pos = match.end()
                
                # Check for overlaps
                if any(pos in range(start_pos, end_pos) for pos in matched_positions):
                    continue
                
                matched_positions.update(range(start_pos, end_pos))
                
                detected_entity = DetectedEntity(
                    entity=canonical_entity,
                    entity_type=self.entity_metadata.get(canonical_entity, {}).get('entity_type', EntityType.REGION),
                    start_pos=start_pos,
                    end_pos=end_pos,
                    confidence=0.85,  # Slightly lower confidence for aliases
                    source='mongodb',
                    aliases_matched=[alias],
                    priority=self.entity_metadata.get(canonical_entity, {}).get('priority', 5)
                )
                detected_entities.append(detected_entity)
        
        # Sort by position to preserve source order
        detected_entities.sort(key=lambda x: x.start_pos)
        
        return detected_entities
    
    def _detect_with_spacy(self, title: str) -> List[DetectedEntity]:
        """Detect geographic entities using spaCy model (local or API)."""
        if self.use_api:
            return self._detect_with_spacy_api(title)
        
        if not self.spacy_model:
            return []
        
        detected_entities = []
        
        try:
            doc = self.spacy_model(title)
            
            for ent in doc.ents:
                # Focus only on geographic entities (GPE = Geopolitical entity, LOC = Location)
                if ent.label_ in self.target_entity_types:
                    # Calculate confidence based on entity length and context
                    confidence = min(0.85, 0.6 + (len(ent.text.split()) * 0.1))  # Longer entities = higher confidence
                    
                    detected_entity = DetectedEntity(
                        entity=ent.text,
                        entity_type=EntityType.REGION if ent.label_ == 'LOC' else EntityType.COUNTRY,
                        start_pos=ent.start_char,
                        end_pos=ent.end_char,
                        confidence=confidence,
                        source='spacy'
                    )
                    detected_entities.append(detected_entity)
        
        except Exception as e:
            logger.warning(f"spaCy detection failed for '{title}': {e}")
        
        return detected_entities
    
    def _detect_with_spacy_api(self, title: str) -> List[DetectedEntity]:
        """Detect geographic entities using Zettit Model Router API (placeholder)."""
        detected_entities = []
        
        try:
            # Placeholder for Zettit Model Router API integration
            # This would make an HTTP request to the Zettit Model Router
            # and parse the response to return DetectedEntity objects
            
            # Example API call structure (commented out):
            # import requests
            # headers = {'Authorization': f'Bearer {self.api_key}'}
            # payload = {
            #     'model': 'spacy_en_core_web_md',
            #     'text': title,
            #     'entity_types': ['GPE', 'LOC'],
            #     'task': 'named_entity_recognition'
            # }
            # response = requests.post(f"{self.api_endpoint}/spacy/ner", 
            #                         json=payload, headers=headers)
            # 
            # if response.status_code == 200:
            #     api_entities = response.json().get('entities', [])
            #     for entity in api_entities:
            #         detected_entity = DetectedEntity(
            #             entity=entity['text'],
            #             entity_type=EntityType.REGION if entity['label'] == 'LOC' else EntityType.COUNTRY,
            #             start_pos=entity['start'],
            #             end_pos=entity['end'],
            #             confidence=entity['confidence'],
            #             source='spacy_api'
            #         )
            #         detected_entities.append(detected_entity)
            
            logger.debug(f"API-based spaCy detection placeholder executed for: {title}")
        
        except Exception as e:
            logger.warning(f"spaCy API detection failed for '{title}': {e}")
        
        return detected_entities
    
    def _detect_with_gliner(self, title: str) -> List[DetectedEntity]:
        """Detect geographic entities using GLiNER model."""
        if not self.gliner_model:
            return []
        
        detected_entities = []
        
        try:
            # GLiNER implementation placeholder
            # entities = self.gliner_model.predict_entities(title, ["location", "country", "region"])
            # 
            # for entity in entities:
            #     detected_entity = DetectedEntity(
            #         entity=entity['text'],
            #         entity_type=EntityType.REGION,
            #         start_pos=entity['start'],
            #         end_pos=entity['end'],
            #         confidence=entity['score'],
            #         source='gliner'
            #     )
            #     detected_entities.append(detected_entity)
            
            logger.debug("GLiNER detection placeholder executed")
        
        except Exception as e:
            logger.warning(f"GLiNER detection failed for '{title}': {e}")
        
        return detected_entities
    
    def _merge_and_deduplicate_entities(self, pattern_entities: List[DetectedEntity], 
                                      spacy_entities: List[DetectedEntity], 
                                      gliner_entities: List[DetectedEntity]) -> List[DetectedEntity]:
        """Merge entities from different sources and remove duplicates."""
        all_entities = pattern_entities + spacy_entities + gliner_entities
        
        if not all_entities:
            return []
        
        # Group by normalized entity text
        entity_groups = defaultdict(list)
        for entity in all_entities:
            normalized_key = entity.entity.lower().strip()
            entity_groups[normalized_key].append(entity)
        
        merged_entities = []
        
        for normalized_entity, entity_list in entity_groups.items():
            if len(entity_list) == 1:
                # Single detection, keep as is
                merged_entities.append(entity_list[0])
            else:
                # Multiple detections, merge with priority
                # Priority: MongoDB patterns > spaCy > GLiNER
                best_entity = None
                best_priority = float('inf')
                
                for entity in entity_list:
                    priority_score = 0
                    if entity.source == 'mongodb':
                        priority_score = 1
                    elif entity.source == 'spacy':
                        priority_score = 2
                    elif entity.source == 'gliner':
                        priority_score = 3
                    
                    if priority_score < best_priority or (priority_score == best_priority and entity.confidence > best_entity.confidence):
                        best_priority = priority_score
                        best_entity = entity
                
                # Increase confidence if multiple sources agree
                if len(entity_list) > 1:
                    best_entity.confidence = min(0.95, best_entity.confidence + 0.1)
                
                merged_entities.append(best_entity)
        
        # Sort by position to preserve source order
        merged_entities.sort(key=lambda x: x.start_pos)
        
        return merged_entities
    
    def _calculate_confidence_score(self, entities: List[DetectedEntity], title: str) -> float:
        """Calculate overall confidence score for the detection result."""
        if not entities:
            return 0.9 if 'market' in title.lower() else 0.95  # High confidence for no entities
        
        # Base confidence from individual entity confidences
        individual_confidences = [entity.confidence for entity in entities]
        avg_confidence = sum(individual_confidences) / len(individual_confidences)
        
        # Bonus for multiple sources agreeing
        sources = set(entity.source for entity in entities)
        source_bonus = 0.05 * (len(sources) - 1) if len(sources) > 1 else 0
        
        # Penalty for too many entities (likely false positives)
        entity_penalty = 0.05 * max(0, len(entities) - 3)
        
        final_confidence = min(0.95, avg_confidence + source_bonus - entity_penalty)
        return round(final_confidence, 3)
    
    def detect(self, title: str) -> DetectionResult:
        """
        Detect geographic entities in a market research title.
        
        Args:
            title: Title to analyze
            
        Returns:
            DetectionResult with detected entities and metadata
        """
        if not title or not title.strip():
            return DetectionResult(
                title=title,
                entities=[],
                extracted_regions=[],
                confidence_score=0.95,
                processing_notes=["Empty title"],
                detection_method="none"
            )
        
        processing_notes = []
        
        # Track processing
        self.detection_stats['total_processed'] += 1
        
        # Pattern-based detection (always performed)
        pattern_entities = self._detect_with_patterns(title)
        processing_notes.append(f"Pattern detection: {len(pattern_entities)} entities")
        
        # Model-based detection (optional)
        spacy_entities = []
        gliner_entities = []
        
        if self.use_models:
            spacy_entities = self._detect_with_spacy(title)
            gliner_entities = self._detect_with_gliner(title)
            processing_notes.append(f"spaCy detection: {len(spacy_entities)} entities")
            processing_notes.append(f"GLiNER detection: {len(gliner_entities)} entities")
        
        # Merge and deduplicate entities
        final_entities = self._merge_and_deduplicate_entities(
            pattern_entities, spacy_entities, gliner_entities
        )
        
        # Extract final region list preserving source order
        extracted_regions = [entity.entity for entity in final_entities]
        
        # Calculate confidence score
        confidence_score = self._calculate_confidence_score(final_entities, title)
        
        # Determine detection method
        methods = []
        if pattern_entities:
            methods.append("patterns")
        if spacy_entities:
            methods.append("spacy") 
        if gliner_entities:
            methods.append("gliner")
        detection_method = "+".join(methods) if methods else "none"
        
        # Update statistics
        if final_entities:
            self.detection_stats['titles_with_entities'] += 1
            self.detection_stats['total_entities_detected'] += len(final_entities)
            self.detection_stats['compound_entities_detected'] += sum(
                1 for entity in final_entities if entity.entity_type == EntityType.COMPOUND
            )
            self.detection_stats['model_entities_detected'] += len(spacy_entities) + len(gliner_entities)
        
        return DetectionResult(
            title=title,
            entities=final_entities,
            extracted_regions=extracted_regions,
            confidence_score=confidence_score,
            processing_notes=processing_notes,
            detection_method=detection_method
        )
    
    def detect_batch(self, titles: List[str]) -> List[DetectionResult]:
        """
        Detect geographic entities in a batch of titles.
        
        Args:
            titles: List of titles to analyze
            
        Returns:
            List of DetectionResult objects
        """
        results = []
        
        logger.info(f"Starting batch detection of {len(titles)} titles")
        
        for i, title in enumerate(titles):
            if i > 0 and i % 1000 == 0:
                logger.info(f"Processed {i}/{len(titles)} titles...")
            
            result = self.detect(title)
            results.append(result)
        
        logger.info(f"Completed batch detection of {len(titles)} titles")
        return results
    
    def get_detection_statistics(self) -> DetectionStats:
        """
        Get current detection statistics.
        
        Returns:
            DetectionStats object with current statistics
        """
        total = self.detection_stats['total_processed']
        
        if total == 0:
            return DetectionStats(
                total_processed=0,
                titles_with_entities=0,
                titles_without_entities=0,
                total_entities_detected=0,
                average_entities_per_title=0.0,
                detection_rate=0.0
            )
        
        titles_with_entities = self.detection_stats['titles_with_entities']
        titles_without_entities = total - titles_with_entities
        total_entities = self.detection_stats['total_entities_detected']
        
        return DetectionStats(
            total_processed=total,
            titles_with_entities=titles_with_entities,
            titles_without_entities=titles_without_entities,
            total_entities_detected=total_entities,
            average_entities_per_title=round(total_entities / total, 2),
            detection_rate=round((titles_with_entities / total) * 100, 2)
        )
    
    def export_detection_report(self, filename: Optional[str] = None) -> str:
        """
        Export detection statistics to a formatted report.
        
        Args:
            filename: Optional filename to save report to
            
        Returns:
            Report content as string
        """
        pdt_time, utc_time, _ = self._get_timestamps()
        stats = self.get_detection_statistics()
        
        report = f"""Geographic Entity Detection Report
{'='*50}
Analysis Date (PDT): {pdt_time}
Analysis Date (UTC): {utc_time}
{'='*50}

Detection Summary:
  Total Titles Processed: {stats.total_processed:,}
  
  Geographic Detection:
    - Titles with Entities:    {stats.titles_with_entities:6,} ({stats.detection_rate:6.2f}%)
    - Titles without Entities: {stats.titles_without_entities:6,} ({(stats.titles_without_entities/stats.total_processed)*100:6.2f}%)
    - Total Entities Detected: {stats.total_entities_detected:6,}
    - Average per Title:       {stats.average_entities_per_title:6.2f}

Entity Type Distribution:
  Compound Entities:  {self.detection_stats['compound_entities_detected']:,}
  Model Entities:     {self.detection_stats['model_entities_detected']:,}

Detection Performance:
  Detection Rate:        {stats.detection_rate:.2f}%
  Entities per Title:    {stats.average_entities_per_title:.2f}
  
Configuration:
  MongoDB Patterns:      {'Yes' if self.pattern_library_manager else 'No (fallback)'}
  NLP Models Enabled:    {'Yes' if self.use_models else 'No'}
  spaCy Model:          {'Loaded' if self.spacy_model else 'Not available'}
  GLiNER Model:         {'Loaded' if self.gliner_model else 'Not available'}
"""
        
        if filename:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(report)
            logger.info(f"Detection report exported to {filename}")
        
        return report


def demo_detection():
    """Demonstrate Geographic Entity Detector functionality."""
    
    print("Geographic Entity Detection System Demo")
    print("=" * 60)
    
    # Sample titles for testing
    sample_titles = [
        # Geographic patterns - should detect
        "Global Artificial Intelligence Market Size & Share Report, 2030",
        "APAC Personal Protective Equipment Market Analysis",
        "North America Automotive Battery Market Outlook 2031",
        "Europe & Asia Pacific Blockchain Technology Market",
        "Middle East Healthcare Market Research Report",
        
        # Complex geographic patterns
        "Asia Pacific & North America Solar Energy Market, 2025-2030",
        "EMEA Pharmaceutical Market in Germany and France",
        "Latin America Market for Renewable Energy Systems",
        
        # Non-geographic patterns - should not detect
        "Blockchain Technology Market Trends Report",
        "Healthcare Market Research and Insights",
        "Annual Financial Technology Report 2023",
        
        # Edge cases
        "Farmers Market Analysis (Not Geographic)",
        "After Market Services in North America",
        "Stock Market Performance Review - Global"
    ]
    
    try:
        # Test without models first
        print("\n1. Pattern-Based Detection (MongoDB only):")
        print("-" * 50)
        
        detector = GeographicEntityDetector(use_models=False)
        
        for title in sample_titles[:5]:  # Show first 5 examples
            result = detector.detect(title)
            print(f"Title: {title}")
            print(f"  Entities: {result.extracted_regions}")
            print(f"  Confidence: {result.confidence_score:.3f}")
            print(f"  Method: {result.detection_method}")
            print(f"  Notes: {'; '.join(result.processing_notes)}")
            print()
        
        # Batch detection
        print("2. Batch Detection Results:")
        print("-" * 50)
        
        batch_results = detector.detect_batch(sample_titles)
        
        # Get statistics
        stats = detector.get_detection_statistics()
        
        print(f"Total Processed: {stats.total_processed}")
        print(f"With Entities: {stats.titles_with_entities} ({stats.detection_rate:.2f}%)")
        print(f"Average Entities per Title: {stats.average_entities_per_title:.2f}")
        print(f"Total Entities Detected: {stats.total_entities_detected}")
        
        # Show entity distribution
        print("\n3. Entity Analysis:")
        print("-" * 50)
        
        all_entities = []
        for result in batch_results:
            all_entities.extend(result.entities)
        
        entity_types = Counter(entity.entity_type.value for entity in all_entities)
        sources = Counter(entity.source for entity in all_entities)
        
        print("Entity Types:")
        for entity_type, count in entity_types.most_common():
            print(f"  {entity_type}: {count}")
        
        print("\nDetection Sources:")
        for source, count in sources.most_common():
            print(f"  {source}: {count}")
        
        # Export report
        print("\n4. Detailed Detection Report:")
        print("-" * 50)
        
        report = detector.export_detection_report()
        print(report)
        
        print("✅ Geographic Entity Detection demo completed successfully!")
        
    except Exception as e:
        print(f"❌ Demo failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    demo_detection()