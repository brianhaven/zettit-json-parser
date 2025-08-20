#!/usr/bin/env python3

"""
Update Geographic Patterns from Region Mappings
Updates MongoDB pattern library with comprehensive geographic entities from region_mappings.json.
Created for Market Research Title Parser project.
"""

import sys
import os
import json
import logging
from datetime import datetime
from typing import Dict, List, Set

# Add experiments directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from pattern_library_manager_v1 import PatternLibraryManager, PatternType

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_region_mappings() -> Dict:
    """Load region mappings from JSON file."""
    mappings_file = "../resources/region_mappings.json"
    
    try:
        with open(mappings_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        logger.error(f"Region mappings file not found: {mappings_file}")
        raise
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in region mappings file: {e}")
        raise

def determine_priority(standardized: str) -> int:
    """Determine priority based on entity type and complexity."""
    
    # Priority 1: Complex compound entities (highest specificity)
    priority_1_patterns = [
        "Europe, Middle East and Africa",  # EMEA
        "Middle East and Africa",  # MEA
        "Asia Pacific and India",
        "Southern Europe and Middle East",
        "Association of Southeast Asian Nations"  # ASEAN
    ]
    
    # Priority 2: Regional compound entities
    priority_2_patterns = [
        "North America",
        "South America", 
        "Central America",
        "Latin America",
        "Middle East",
        "Asia Pacific",
        "South East Asia",
        "East Asia"
    ]
    
    # Priority 3: Major regions and global scopes
    priority_3_patterns = [
        "Europe",
        "European Union", 
        "Asia",
        "Africa",
        "Global",
        "Americas",
        "Caribbean",
        "Oceania"
    ]
    
    # Priority 4: Individual countries
    priority_4_patterns = [
        "United States",
        "Brazil",
        "Malaysia", 
        "Saudi Arabia",
        "United Arab Emirates",
        "Philippines"
    ]
    
    if standardized in priority_1_patterns:
        return 1
    elif standardized in priority_2_patterns:
        return 2
    elif standardized in priority_3_patterns:
        return 3
    elif standardized in priority_4_patterns:
        return 4
    else:
        # Default priority for new entities
        return 3

def clean_aliases(variants: List[str], standardized: str) -> List[str]:
    """Clean and filter aliases, removing problematic ones."""
    cleaned_aliases = []
    
    for variant in variants:
        # Skip the standardized term itself
        if variant == standardized:
            continue
            
        # Skip variants with special characters that might cause regex issues
        if any(char in variant for char in ['-', '(', ')', '.']):
            # Only keep simple forms
            if variant in ["U.S.", "US", "USA", "U.S.A.", "EU", "UAE", "U.A.E.", "APAC", "MEA", "EMEA", "ASEAN"]:
                cleaned_aliases.append(variant)
            continue
        
        # Skip overly long variants
        if len(variant) > 50:
            continue
            
        # Skip variants that are just the standardized term with punctuation
        if variant.replace('.', '').replace('-', '').replace(' ', '') == standardized.replace(' ', ''):
            continue
            
        cleaned_aliases.append(variant)
    
    # Remove duplicates while preserving order
    seen = set()
    unique_aliases = []
    for alias in cleaned_aliases:
        if alias not in seen:
            seen.add(alias)
            unique_aliases.append(alias)
    
    return unique_aliases

def update_geographic_patterns():
    """Update MongoDB patterns with comprehensive geographic entities."""
    
    print("Updating Geographic Patterns from Region Mappings")
    print("=" * 60)
    
    try:
        # Load region mappings
        mappings = load_region_mappings()
        regions = mappings.get('regions', [])
        
        print(f"Loaded {len(regions)} region mappings from JSON file")
        
        # Initialize pattern manager
        manager = PatternLibraryManager()
        
        # Get existing patterns to avoid duplicates
        existing_patterns = manager.get_patterns(PatternType.GEOGRAPHIC_ENTITY)
        existing_terms = {pattern['term'] for pattern in existing_patterns}
        
        print(f"Found {len(existing_patterns)} existing geographic patterns in MongoDB")
        
        # Track what we're adding
        added_patterns = []
        updated_patterns = []
        skipped_patterns = []
        
        for region in regions:
            standardized = region['standardized']
            variants = region.get('variants', [])
            
            # Determine priority
            priority = determine_priority(standardized)
            
            # Clean aliases
            aliases = clean_aliases(variants, standardized)
            
            if standardized in existing_terms:
                # Check if we need to update aliases
                existing_pattern = next(p for p in existing_patterns if p['term'] == standardized)
                existing_aliases = set(existing_pattern.get('aliases', []))
                new_aliases = set(aliases)
                
                if new_aliases != existing_aliases:
                    # Update aliases
                    try:
                        manager.update_pattern(
                            str(existing_pattern['_id']),
                            {'aliases': aliases}
                        )
                        updated_patterns.append({
                            'term': standardized,
                            'old_aliases': list(existing_aliases),
                            'new_aliases': aliases
                        })
                        print(f"Updated aliases for: {standardized}")
                    except Exception as e:
                        logger.warning(f"Failed to update {standardized}: {e}")
                else:
                    skipped_patterns.append(standardized)
            else:
                # Add new pattern
                try:
                    pattern_id = manager.add_pattern(
                        pattern_type=PatternType.GEOGRAPHIC_ENTITY,
                        term=standardized,
                        aliases=aliases,
                        priority=priority,
                        active=True
                    )
                    added_patterns.append({
                        'term': standardized,
                        'aliases': aliases,
                        'priority': priority,
                        'id': pattern_id
                    })
                    print(f"Added: {standardized} (priority {priority}, {len(aliases)} aliases)")
                except Exception as e:
                    logger.warning(f"Failed to add {standardized}: {e}")
        
        # Summary
        print("\n" + "=" * 60)
        print("UPDATE SUMMARY")
        print("=" * 60)
        print(f"Added new patterns: {len(added_patterns)}")
        print(f"Updated existing patterns: {len(updated_patterns)}")
        print(f"Skipped (no changes): {len(skipped_patterns)}")
        
        if added_patterns:
            print(f"\nNEW PATTERNS ADDED:")
            for pattern in added_patterns:
                print(f"  ✅ {pattern['term']} (P{pattern['priority']}) - {len(pattern['aliases'])} aliases")
        
        if updated_patterns:
            print(f"\nPATTERNS UPDATED:")
            for pattern in updated_patterns:
                print(f"  🔄 {pattern['term']} - aliases updated")
        
        # Show final statistics
        final_patterns = manager.get_patterns(PatternType.GEOGRAPHIC_ENTITY)
        print(f"\nFINAL LIBRARY STATUS:")
        print(f"  Total patterns: {len(final_patterns)}")
        
        # Group by priority
        priority_counts = {}
        for pattern in final_patterns:
            priority = pattern['priority']
            priority_counts[priority] = priority_counts.get(priority, 0) + 1
        
        for priority in sorted(priority_counts.keys()):
            print(f"  Priority {priority}: {priority_counts[priority]} patterns")
        
        print("\n✅ Geographic pattern update completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Failed to update geographic patterns: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_updated_patterns():
    """Test the updated patterns with representative titles."""
    
    print("\nTesting Updated Geographic Pattern Detection")
    print("=" * 50)
    
    try:
        # Import the detector
        from geographic_entity_detector_v1 import GeographicEntityDetector
        
        # Create fresh detector (will reload patterns from MongoDB)
        detector = GeographicEntityDetector(use_models=False)
        
        # Test titles covering various patterns from the mappings
        test_titles = [
            # Existing patterns
            "Global Automotive Market Report",
            "North America Healthcare Market",
            "APAC Technology Analysis",
            "EMEA Financial Services Market",
            
            # New patterns from mappings
            "European Union Trade Market Report",
            "UAE Energy Market Analysis", 
            "Brazil Manufacturing Market Study",
            "ASEAN Economic Market Outlook",
            "South East Asia Technology Report",
            "Caribbean Tourism Market Analysis",
            "Middle East and Africa Mining Report",
            "Americas Regional Market Study",
            "East Asia Semiconductor Market",
            "Oceania Agriculture Market Report",
            
            # Multiple entities
            "North America and Europe Market Analysis",
            "Asia Pacific, Middle East and Africa Study",
            "Global and Regional Market Outlook",
            
            # Should not detect (non-geographic)
            "Blockchain Technology Market Trends",
            "After Market Services Analysis"
        ]
        
        print("Testing comprehensive geographic pattern detection:\n")
        
        detected_entities_summary = []
        
        for title in test_titles:
            result = detector.detect(title)
            entities = result.extracted_regions
            confidence = result.confidence_score
            
            print(f"Title: {title}")
            print(f"  Detected: {entities}")
            print(f"  Confidence: {confidence:.3f}")
            print()
            
            detected_entities_summary.extend(entities)
        
        # Summary statistics
        unique_entities = list(set(detected_entities_summary))
        
        print("=" * 50)
        print("DETECTION SUMMARY")
        print("=" * 50)
        print(f"Test titles: {len(test_titles)}")
        print(f"Titles with entities: {sum(1 for title in test_titles if detector.detect(title).extracted_regions)}")
        print(f"Total entities detected: {len(detected_entities_summary)}")
        print(f"Unique entities detected: {len(unique_entities)}")
        
        print(f"\nUnique entities found:")
        for entity in sorted(unique_entities):
            print(f"  - {entity}")
        
        print("\n✅ Geographic pattern testing completed!")
        
    except Exception as e:
        print(f"❌ Testing failed: {e}")
        import traceback
        traceback.print_exc()

def main():
    """Main function to update patterns and test."""
    success = update_geographic_patterns()
    
    if success:
        test_updated_patterns()
    else:
        print("❌ Skipping tests due to update failure")

if __name__ == "__main__":
    main()