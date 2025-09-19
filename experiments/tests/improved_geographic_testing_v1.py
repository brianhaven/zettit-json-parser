#!/usr/bin/env python3

"""
Improved Geographic Entity Detection Testing v1.0
Tests geographic detection with:
1. MongoDB patterns only
2. spaCy only  
3. Combined patterns + spaCy
Only using original titles (no full text or normalized versions)
Focus on analyzing titles that HAVE regions vs those that don't
"""

import os
import re
import json
import logging
import time
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple, Any, Union
from dataclasses import dataclass, asdict
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
    source: str  # 'mongodb', 'spacy'
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

class TestMethod(Enum):
    """Test methods to compare"""
    PATTERNS_ONLY = "patterns_only"
    SPACY_ONLY = "spacy_only"
    PATTERNS_SPACY = "patterns_spacy"

class ImprovedGeographicDetector:
    """
    Improved Geographic Entity Detector with fixed U.S. detection.
    """
    
    def __init__(self, pattern_library_manager=None, use_spacy=False):
        """Initialize the detector."""
        self.pattern_library_manager = pattern_library_manager or self._create_pattern_manager()
        self.use_spacy = use_spacy
        
        # Detection statistics
        self.detection_stats = {
            'total_processed': 0,
            'titles_with_entities': 0,
            'total_entities_detected': 0
        }
        
        # Load geographic entities from MongoDB
        self._load_geographic_patterns()
        
        # Initialize spaCy model if requested
        self.spacy_model = None
        if use_spacy:
            self._initialize_spacy_model()
    
    def _create_pattern_manager(self) -> Optional[PatternLibraryManager]:
        """Create pattern library manager if available."""
        if PatternLibraryManager:
            try:
                return PatternLibraryManager()
            except Exception as e:
                logger.warning(f"Could not create PatternLibraryManager: {e}")
        return None
    
    def _create_improved_pattern(self, alias: str) -> str:
        """Create improved regex pattern that handles punctuation properly."""
        escaped = re.escape(alias)
        
        # For patterns with periods, use lookahead/lookbehind for word boundaries
        if '.' in alias:
            # Use negative lookbehind and lookahead for alphanumeric characters
            return r'(?<![a-zA-Z0-9])' + escaped + r'(?![a-zA-Z0-9])'
        else:
            # Use standard word boundaries for regular words
            return r'\b' + escaped + r'\b'
    
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
                
                # Store aliases mapping (DO NOT convert to lowercase - keep original case)
                for alias in aliases:
                    self.entity_aliases[alias] = entity
                
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
            total_aliases = len(self.entity_aliases)
            logger.info(f"Loaded {total_entities} geographic entities with {total_aliases} aliases from MongoDB")
            
        except Exception as e:
            logger.error(f"Failed to load geographic patterns from MongoDB: {e}")
            self._load_fallback_patterns()
    
    def _load_fallback_patterns(self) -> None:
        """Load fallback geographic patterns if MongoDB is unavailable."""
        logger.info("Loading fallback geographic patterns")
        
        # Basic fallback patterns
        fallback_patterns = {
            1: ['North America', 'South America', 'Latin America', 'Asia Pacific'],
            2: ['APAC', 'EMEA', 'MEA'], 
            3: ['Europe', 'Asia', 'Africa'],
            4: ['United States', 'China', 'Germany', 'France', 'India'],
            5: ['US', 'UK', 'EU']
        }
        
        self.geographic_entities = fallback_patterns
        self.priority_order = sorted(self.geographic_entities.keys())
        self.entity_aliases = {
            'U.S.': 'United States',
            'USA': 'United States',
            'US': 'United States',
            'UK': 'United Kingdom'
        }
        self.entity_metadata = {}
        
        total_entities = sum(len(entities) for entities in fallback_patterns.values())
        logger.info(f"Loaded {total_entities} fallback geographic entities")
    
    def _determine_entity_type(self, entity: str) -> EntityType:
        """Determine the type of geographic entity."""
        entity_lower = entity.lower()
        
        if len(entity) <= 5 and entity.isupper():
            return EntityType.ACRONYM
        elif any(compound in entity_lower for compound in ['north', 'south', 'east', 'west', 'central']):
            return EntityType.COMPOUND
        elif entity_lower in ['europe', 'asia', 'africa', 'america', 'pacific']:
            return EntityType.REGION
        elif entity_lower in ['united states', 'china', 'germany', 'france', 'india']:
            return EntityType.COUNTRY
        else:
            return EntityType.REGION  # Default
    
    def _initialize_spacy_model(self) -> None:
        """Initialize spaCy model if available."""
        try:
            import spacy
            # Try to load models in priority order
            spacy_models_to_try = [
                ("en_core_web_lg", "large"),
                ("en_core_web_md", "medium"), 
                ("en_core_web_sm", "small")
            ]
            
            for model_name, model_size in spacy_models_to_try:
                try:
                    self.spacy_model = spacy.load(model_name)
                    logger.info(f"Loaded spaCy {model_name} ({model_size}) model successfully")
                    self.target_entity_types = ['GPE', 'LOC']
                    break
                except OSError:
                    continue
            else:
                logger.warning("No spaCy model found")
                self.spacy_model = None
                self.target_entity_types = []
        except ImportError:
            logger.warning("spaCy not installed")
            self.spacy_model = None
            self.target_entity_types = []
    
    def detect_with_patterns_only(self, title: str) -> List[DetectedEntity]:
        """Detect geographic entities using MongoDB patterns only."""
        detected_entities = []
        matched_positions = set()
        
        # Process by priority (compound entities first)
        for priority in self.priority_order:
            entities = self.geographic_entities[priority]
            
            for entity in entities:
                pattern = self._create_improved_pattern(entity)
                
                for match in re.finditer(pattern, title, re.IGNORECASE):
                    start_pos = match.start()
                    end_pos = match.end()
                    
                    # Check for overlaps
                    if any(pos in range(start_pos, end_pos) for pos in matched_positions):
                        continue
                    
                    matched_positions.update(range(start_pos, end_pos))
                    
                    detected_entity = DetectedEntity(
                        entity=entity,
                        entity_type=self.entity_metadata.get(entity, {}).get('entity_type', EntityType.REGION),
                        start_pos=start_pos,
                        end_pos=end_pos,
                        confidence=0.9,
                        source='mongodb',
                        priority=priority
                    )
                    detected_entities.append(detected_entity)
        
        # Check aliases with improved patterns
        for alias, canonical_entity in self.entity_aliases.items():
            pattern = self._create_improved_pattern(alias)
            
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
                    confidence=0.85,
                    source='mongodb',
                    aliases_matched=[alias],
                    priority=self.entity_metadata.get(canonical_entity, {}).get('priority', 5)
                )
                detected_entities.append(detected_entity)
        
        # Sort by position to preserve source order
        detected_entities.sort(key=lambda x: x.start_pos)
        return detected_entities
    
    def detect_with_spacy_only(self, title: str) -> List[DetectedEntity]:
        """Detect geographic entities using spaCy only."""
        if not self.spacy_model:
            return []
        
        detected_entities = []
        
        try:
            doc = self.spacy_model(title)
            
            for ent in doc.ents:
                if ent.label_ in self.target_entity_types:
                    confidence = min(0.85, 0.6 + (len(ent.text.split()) * 0.1))
                    
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
    
    def detect_combined(self, title: str) -> List[DetectedEntity]:
        """Detect geographic entities using patterns + spaCy combined."""
        pattern_entities = self.detect_with_patterns_only(title)
        spacy_entities = self.detect_with_spacy_only(title)
        
        # Merge and deduplicate
        all_entities = pattern_entities + spacy_entities
        
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
                merged_entities.append(entity_list[0])
            else:
                # Priority: MongoDB patterns > spaCy
                best_entity = None
                best_priority = float('inf')
                
                for entity in entity_list:
                    priority_score = 1 if entity.source == 'mongodb' else 2
                    
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
    
    def detect(self, title: str, method: TestMethod) -> DetectionResult:
        """Detect geographic entities using specified method."""
        if not title or not title.strip():
            return DetectionResult(
                title=title,
                entities=[],
                extracted_regions=[],
                confidence_score=0.95,
                processing_notes=["Empty title"],
                detection_method="none"
            )
        
        # Get entities based on method
        if method == TestMethod.PATTERNS_ONLY:
            entities = self.detect_with_patterns_only(title)
            detection_method = "patterns_only"
        elif method == TestMethod.SPACY_ONLY:
            entities = self.detect_with_spacy_only(title)
            detection_method = "spacy_only"
        elif method == TestMethod.PATTERNS_SPACY:
            entities = self.detect_combined(title)
            detection_method = "patterns_spacy"
        else:
            entities = []
            detection_method = "unknown"
        
        # Extract final region list
        extracted_regions = [entity.entity for entity in entities]
        
        # Calculate confidence
        if not entities:
            confidence_score = 0.9
        else:
            individual_confidences = [entity.confidence for entity in entities]
            confidence_score = sum(individual_confidences) / len(individual_confidences)
        
        processing_notes = [f"{detection_method}: {len(entities)} entities"]
        
        return DetectionResult(
            title=title,
            entities=entities,
            extracted_regions=extracted_regions,
            confidence_score=round(confidence_score, 3),
            processing_notes=processing_notes,
            detection_method=detection_method
        )

def load_test_data(limit: int = 200) -> List[Dict]:
    """Load test data from MongoDB."""
    load_dotenv()
    client = MongoClient(os.getenv('MONGODB_URI'))
    db = client['deathstar']
    
    # Sample titles from the database
    pipeline = [
        {'$sample': {'size': limit}},
        {'$project': {
            'report_title_short': 1,
            '_id': 1
        }}
    ]
    
    titles = list(db.markets_raw.aggregate(pipeline))
    logger.info(f"Loaded {len(titles)} test titles from MongoDB")
    
    return titles

def run_geographic_detection_tests():
    """Run comprehensive geographic detection tests."""
    
    # Get timestamps
    utc_now = datetime.now(timezone.utc)
    pdt_tz = pytz.timezone('America/Los_Angeles')
    pdt_now = utc_now.astimezone(pdt_tz)
    
    pdt_str = pdt_now.strftime('%Y-%m-%d %H:%M:%S %Z')
    utc_str = utc_now.strftime('%Y-%m-%d %H:%M:%S UTC')
    filename_timestamp = pdt_now.strftime('%Y%m%d_%H%M%S')
    
    print("IMPROVED GEOGRAPHIC DETECTION TESTING")
    print("=" * 70)
    print(f"Analysis Date (PDT): {pdt_str}")
    print(f"Analysis Date (UTC): {utc_str}")
    print("=" * 70)
    
    # Load test data
    test_data = load_test_data(200)
    
    # Initialize detectors
    print("\\nInitializing detectors...")
    detector_with_spacy = ImprovedGeographicDetector(use_spacy=True)
    detector_patterns_only = ImprovedGeographicDetector(use_spacy=False)
    
    # Test methods
    test_methods = [
        TestMethod.PATTERNS_ONLY,
        TestMethod.SPACY_ONLY, 
        TestMethod.PATTERNS_SPACY
    ]
    
    all_results = {}
    
    for method in test_methods:
        print(f"\\nTesting method: {method.value}")
        print("-" * 50)
        
        # Choose appropriate detector
        detector = detector_with_spacy if method in [TestMethod.SPACY_ONLY, TestMethod.PATTERNS_SPACY] else detector_patterns_only
        
        results = []
        start_time = time.time()
        
        for i, data in enumerate(test_data):
            if i > 0 and i % 50 == 0:
                print(f"  Processed {i}/{len(test_data)} titles...")
            
            title = data['report_title_short']
            result = detector.detect(title, method)
            
            # Store result with metadata
            result_dict = {
                'title_id': str(data['_id']),
                'title': title,
                'entities_found': result.extracted_regions,
                'entity_details': [{
                    'entity': entity.entity,
                    'entity_type': entity.entity_type.value,
                    'start_pos': entity.start_pos,
                    'end_pos': entity.end_pos,
                    'confidence': entity.confidence,
                    'source': entity.source,
                    'aliases_matched': entity.aliases_matched,
                    'priority': entity.priority
                } for entity in result.entities],
                'confidence': result.confidence,
                'detection_method': result.detection_method,
                'notes': result.notes,
                'has_regions': len(result.extracted_regions) > 0
            }
            results.append(result_dict)
        
        processing_time = time.time() - start_time
        
        # Analyze results
        total_processed = len(results)
        titles_with_entities = sum(1 for r in results if r['has_regions'])
        titles_without_entities = total_processed - titles_with_entities
        total_entities = sum(len(r['entities_found']) for r in results)
        
        detection_rate = (titles_with_entities / total_processed) * 100
        avg_entities_per_title = total_entities / total_processed if total_processed > 0 else 0
        
        # Store results
        method_results = {
            'method': method.value,
            'total_processed': total_processed,
            'titles_with_entities': titles_with_entities,
            'titles_without_entities': titles_without_entities,
            'detection_rate': round(detection_rate, 2),
            'total_entities_detected': total_entities,
            'avg_entities_per_title': round(avg_entities_per_title, 2),
            'processing_time_seconds': round(processing_time, 2),
            'sample_results': results[:10],  # First 10 for preview
            'all_results': results  # Full results for analysis
        }
        all_results[method.value] = method_results
        
        # Print summary
        print(f"  Detection Rate: {detection_rate:.2f}%")
        print(f"  Titles with entities: {titles_with_entities}")
        print(f"  Titles without entities: {titles_without_entities}")
        print(f"  Total entities detected: {total_entities}")
        print(f"  Average entities per title: {avg_entities_per_title:.2f}")
        print(f"  Processing time: {processing_time:.2f}s")
    
    # Create comprehensive output
    output_data = {
        'experiment_info': {
            'timestamp_pdt': pdt_str,
            'timestamp_utc': utc_str,
            'dataset_size': len(test_data),
            'methods_tested': [method.value for method in test_methods]
        },
        'results_summary': {
            method: {
                'detection_rate': all_results[method]['detection_rate'],
                'titles_with_entities': all_results[method]['titles_with_entities'],
                'total_entities': all_results[method]['total_entities_detected'],
                'processing_time': all_results[method]['processing_time_seconds']
            }
            for method in all_results.keys()
        },
        'detailed_results': all_results
    }
    
    # Save to JSON file
    json_filename = f"outputs/{filename_timestamp}_improved_geographic_detection_results.json"
    with open(json_filename, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)
    
    print(f"\\n✅ Results saved to {json_filename}")
    
    # Analysis and recommendations
    print("\\nCOMPARATIVE ANALYSIS")
    print("-" * 50)
    
    best_detection_rate = max(all_results.values(), key=lambda x: x['detection_rate'])
    print(f"Best Detection Rate: {best_detection_rate['method']} ({best_detection_rate['detection_rate']}%)")
    
    most_entities = max(all_results.values(), key=lambda x: x['total_entities_detected'])
    print(f"Most Entities Detected: {most_entities['method']} ({most_entities['total_entities_detected']} entities)")
    
    # Focus on titles WITH regions for meaningful analysis
    print("\\nTITLES WITH REGIONS ANALYSIS")
    print("-" * 50)
    
    for method in test_methods:
        method_data = all_results[method.value]
        titles_with_regions = [r for r in method_data['all_results'] if r['has_regions']]
        
        if titles_with_regions:
            print(f"{method.value}:")
            print(f"  Titles with regions detected: {len(titles_with_regions)}")
            
            # Show some examples
            print("  Examples:")
            for example in titles_with_regions[:3]:
                print(f"    '{example['title']}' -> {example['entities_found']}")
    
    print("\\n" + "=" * 70)
    print("TESTING COMPLETED")
    print("=" * 70)

if __name__ == "__main__":
    run_geographic_detection_tests()