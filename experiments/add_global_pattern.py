#!/usr/bin/env python3

"""
Add Global Pattern to MongoDB Library
Adds "Global" as a geographic entity pattern to the MongoDB pattern library.
Created for Market Research Title Parser project.
"""

import sys
import os
import logging
from datetime import datetime

# Add experiments directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from pattern_library_manager_v1 import PatternLibraryManager, PatternType

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def add_global_pattern():
    """Add Global as a geographic entity pattern."""
    
    print("Adding 'Global' Pattern to MongoDB Library")
    print("=" * 50)
    
    try:
        # Initialize pattern manager
        manager = PatternLibraryManager()
        
        # Check if Global pattern already exists
        existing_patterns = manager.search_patterns("Global", PatternType.GEOGRAPHIC_ENTITY)
        
        if existing_patterns:
            print(f"✅ 'Global' pattern already exists:")
            for pattern in existing_patterns:
                print(f"   - {pattern['term']} (priority: {pattern['priority']}, aliases: {pattern.get('aliases', [])})")
            return
        
        # Add Global pattern
        # Priority 3 to match other major scope indicators like "Europe", "Asia", etc.
        pattern_id = manager.add_pattern(
            pattern_type=PatternType.GEOGRAPHIC_ENTITY,
            term="Global",
            aliases=["Worldwide", "International"],
            priority=3,  # Same priority as Europe, Asia, etc.
            active=True
        )
        
        print(f"✅ Successfully added 'Global' pattern with ID: {pattern_id}")
        print(f"   - Term: Global")
        print(f"   - Aliases: ['Worldwide', 'International']")
        print(f"   - Priority: 3 (same as Europe, Asia)")
        
        # Verify the addition
        verification_patterns = manager.search_patterns("Global", PatternType.GEOGRAPHIC_ENTITY)
        if verification_patterns:
            print(f"\n✅ Verification successful - pattern found in database")
        else:
            print(f"\n❌ Verification failed - pattern not found")
        
        # Show updated pattern statistics
        geo_patterns = manager.get_patterns(PatternType.GEOGRAPHIC_ENTITY)
        print(f"\nUpdated Geographic Entity Library:")
        print(f"   Total patterns: {len(geo_patterns)}")
        
        # Group by priority
        priority_counts = {}
        for pattern in geo_patterns:
            priority = pattern['priority']
            priority_counts[priority] = priority_counts.get(priority, 0) + 1
        
        for priority in sorted(priority_counts.keys()):
            print(f"   Priority {priority}: {priority_counts[priority]} patterns")
        
        print("\n✅ Global pattern addition completed successfully!")
        
    except Exception as e:
        print(f"❌ Failed to add Global pattern: {e}")
        import traceback
        traceback.print_exc()

def test_global_detection():
    """Test that Global pattern is now detected."""
    
    print("\nTesting Global Pattern Detection")
    print("=" * 40)
    
    try:
        # Import the detector
        from geographic_entity_detector_v1 import GeographicEntityDetector
        
        # Create detector (will reload patterns from MongoDB)
        detector = GeographicEntityDetector(use_models=False)
        
        # Test titles with Global
        test_titles = [
            "Global Automotive Market Report",
            "Worldwide Technology Market Analysis", 
            "International Trade Market Study",
            "Global Market for Renewable Energy",
            "Global and Regional Market Outlook"
        ]
        
        print("Testing Global pattern detection:")
        
        for title in test_titles:
            result = detector.detect(title)
            entities = result.extracted_regions
            confidence = result.confidence_score
            
            print(f"Title: {title}")
            print(f"  Detected: {entities}")
            print(f"  Confidence: {confidence:.3f}")
            print()
        
        # Check if Global is being detected
        global_detected = False
        for title in test_titles:
            result = detector.detect(title)
            if any("Global" in entity or "Worldwide" in entity or "International" in entity 
                   for entity in result.extracted_regions):
                global_detected = True
                break
        
        if global_detected:
            print("✅ Global pattern detection is working!")
        else:
            print("❌ Global pattern detection not working yet. May need cache refresh.")
            print("   Try running the geographic detector demo again.")
        
    except Exception as e:
        print(f"❌ Testing failed: {e}")
        import traceback
        traceback.print_exc()

def main():
    """Main function to add Global pattern and test."""
    add_global_pattern()
    test_global_detection()

if __name__ == "__main__":
    main()