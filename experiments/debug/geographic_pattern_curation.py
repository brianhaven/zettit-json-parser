#!/usr/bin/env python3
"""
Geographic Pattern Curation Script for Issue #18
Moves problematic abbreviations to archived_aliases field and removes invalid compound regions.
"""

import os
from pymongo import MongoClient
from dotenv import load_dotenv
from datetime import datetime

# Load environment variables
load_dotenv()

# Connect to MongoDB
client = MongoClient(os.getenv('MONGODB_URI'))
db = client['deathstar']
patterns_collection = db['pattern_libraries']

def curate_geographic_patterns(dry_run=True):
    """
    Curate geographic patterns to resolve false positives.
    
    Args:
        dry_run: If True, only show what would be changed without modifying database
    """
    
    print("=" * 80)
    print("GEOGRAPHIC PATTERN CURATION FOR ISSUE #18")
    print(f"Mode: {'DRY RUN' if dry_run else 'LIVE UPDATE'}")
    print("=" * 80)
    
    updates_made = []
    
    # 1. Move problematic abbreviations to archived_aliases
    abbreviations_to_archive = [
        ('Idaho', 'ID', 'Conflicts with ID card, IDentity, IDC'),
        ('Indiana', 'IN', 'Conflicts with preposition IN'),
        ('Oregon', 'OR', 'Conflicts with conjunction OR'),
        ('Italy', 'IT', 'Conflicts with Information Technology'),
        ('Belarus', 'BY', 'Conflicts with preposition BY (already archived)'),
        ('Mississippi', 'MS', 'Conflicts with Microsoft, Master of Science'),
        ('Goiás', 'GO', 'Conflicts with verb GO'),
    ]
    
    print("\n1. ARCHIVING PROBLEMATIC ABBREVIATIONS")
    print("-" * 50)
    
    for region, abbrev, reason in abbreviations_to_archive:
        # Find the pattern
        pattern = patterns_collection.find_one({
            "type": "geographic_entity",
            "term": region
        })
        
        if pattern:
            # Check if abbreviation is in aliases
            if abbrev in pattern.get('aliases', []):
                print(f"\n{region}:")
                print(f"  Moving '{abbrev}' from aliases to archived_aliases")
                print(f"  Reason: {reason}")
                
                if not dry_run:
                    # Remove from aliases and add to archived_aliases
                    result = patterns_collection.update_one(
                        {"_id": pattern["_id"]},
                        {
                            "$pull": {"aliases": abbrev},
                            "$addToSet": {"archived_aliases": abbrev},
                            "$set": {
                                "last_updated": datetime.utcnow(),
                                "curation_notes": f"Archived '{abbrev}': {reason}"
                            }
                        }
                    )
                    if result.modified_count > 0:
                        updates_made.append(f"Archived '{abbrev}' for {region}")
                        print(f"  ✓ Updated successfully")
                    else:
                        print(f"  ⚠ No changes made")
                else:
                    print(f"  [DRY RUN] Would archive '{abbrev}'")
            
            elif abbrev in pattern.get('archived_aliases', []):
                print(f"\n{region}: '{abbrev}' already archived ✓")
            
            else:
                print(f"\n{region}: '{abbrev}' not found in aliases")
    
    # 2. Remove invalid compound regions
    compound_regions_to_remove = [
        'North America and Europe',  # Should be two separate regions
        'North and South America',   # Should be two separate regions
        'Europe and Asia',           # Should be two separate regions
        'Asia and Middle East',      # Should be two separate regions
        'North and Central America', # Should be two separate regions
    ]
    
    # Valid compound regions to keep
    valid_compounds = [
        'Bosnia and Herzegovina',    # Single country
        'Antigua and Barbuda',       # Single country
        'Saint Kitts and Nevis',     # Single country
        'Saint Vincent and the Grenadines',  # Single country
        'Sao Tome and Principe',     # Single country
        'Trinidad and Tobago',       # Single country
        'Australia and New Zealand', # Common regional grouping (ANZ)
        'U.S. and Canada',          # Common regional grouping
        'Europe, Middle East and Africa',  # Common business region (EMEA)
        'Asia Pacific and India',    # Common business region
    ]
    
    print("\n2. REMOVING INVALID COMPOUND REGIONS")
    print("-" * 50)
    
    for compound in compound_regions_to_remove:
        pattern = patterns_collection.find_one({
            "type": "geographic_entity",
            "term": compound
        })
        
        if pattern:
            print(f"\n'{compound}':")
            print(f"  Priority: {pattern.get('priority')}")
            print(f"  Status: Should be removed (not a valid single region)")
            
            if not dry_run:
                result = patterns_collection.delete_one({"_id": pattern["_id"]})
                if result.deleted_count > 0:
                    updates_made.append(f"Removed compound region '{compound}'")
                    print(f"  ✓ Removed successfully")
                else:
                    print(f"  ⚠ Could not remove")
            else:
                print(f"  [DRY RUN] Would remove this pattern")
        else:
            print(f"\n'{compound}': Not found (already removed or never existed)")
    
    # 3. Verify valid compound regions are preserved
    print("\n3. VERIFYING VALID COMPOUND REGIONS")
    print("-" * 50)
    
    for compound in valid_compounds:
        pattern = patterns_collection.find_one({
            "type": "geographic_entity",
            "term": compound
        })
        
        if pattern:
            print(f"'{compound}': ✓ Exists (valid compound)")
        else:
            print(f"'{compound}': ⚠ Missing (should exist)")
    
    # Summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    
    if dry_run:
        print("\nDRY RUN COMPLETE - No changes made to database")
        print("Run with dry_run=False to apply changes")
    else:
        print(f"\nUpdates made: {len(updates_made)}")
        for update in updates_made:
            print(f"  - {update}")
    
    # Verification queries
    print("\n" + "=" * 80)
    print("VERIFICATION QUERIES")
    print("=" * 80)
    
    print("\nTo verify changes in MongoDB:")
    print("1. Check Idaho pattern:")
    print('   db.pattern_libraries.findOne({type: "geographic_entity", term: "Idaho"})')
    print("\n2. Check archived aliases:")
    print('   db.pattern_libraries.find({type: "geographic_entity", archived_aliases: {$exists: true}}).count()')
    print("\n3. Verify compound region removal:")
    print('   db.pattern_libraries.findOne({type: "geographic_entity", term: "North America and Europe"})')
    
    return updates_made

if __name__ == "__main__":
    import sys
    
    # Check command line arguments
    if len(sys.argv) > 1 and sys.argv[1] == '--apply':
        print("APPLYING CHANGES TO DATABASE...")
        curate_geographic_patterns(dry_run=False)
    else:
        print("Running in DRY RUN mode (no changes will be made)")
        print("To apply changes, run: python3 geographic_pattern_curation.py --apply")
        curate_geographic_patterns(dry_run=True)