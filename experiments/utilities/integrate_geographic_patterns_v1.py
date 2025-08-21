#!/usr/bin/env python3
"""
Geographic Pattern Libraries Integration
Integrates merged geographic entities into MongoDB pattern_libraries collection
"""

import json
import os
from datetime import datetime
from collections import defaultdict
import pytz
from pymongo import MongoClient
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def get_timestamps():
    """Generate PDT and UTC timestamps"""
    utc_now = datetime.now(pytz.UTC)
    pdt_now = utc_now.astimezone(pytz.timezone('US/Pacific'))
    
    return {
        'pdt': pdt_now.strftime('%Y-%m-%d %H:%M:%S PDT'),
        'utc': utc_now.strftime('%Y-%m-%d %H:%M:%S UTC'),
        'filename': pdt_now.strftime('%Y%m%d_%H%M%S')
    }

def connect_mongodb():
    """Connect to MongoDB"""
    try:
        client = MongoClient(os.getenv('MONGODB_URI'))
        db = client['deathstar']
        # Test connection
        client.admin.command('ping')
        return db
    except Exception as e:
        print(f"Error connecting to MongoDB: {e}")
        return None

def load_merged_entities():
    """Load the merged geographic entities"""
    try:
        with open('/home/ec2-user/zettit/services/json-parser/resources/geographic_pattern_libraries_20250820_224347.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data['pattern_libraries_entries']
    except Exception as e:
        print(f"Error loading merged entities: {e}")
        return None

def get_existing_entities(db):
    """Get all existing geographic entities from database"""
    try:
        collection = db['pattern_libraries']
        existing = list(collection.find({"type": "geographic_entity"}))
        return existing
    except Exception as e:
        print(f"Error fetching existing entities: {e}")
        return []

def normalize_term(term):
    """Normalize term for comparison"""
    return term.lower().strip()

def analyze_overlap(existing_entities, merged_entities):
    """Analyze overlap between existing and merged entities"""
    existing_terms = {normalize_term(entity['term']): entity for entity in existing_entities}
    merged_terms = {normalize_term(entity['term']): entity for entity in merged_entities}
    
    overlap = []
    new_entities = []
    
    for norm_term, merged_entity in merged_terms.items():
        if norm_term in existing_terms:
            overlap.append({
                'existing': existing_terms[norm_term],
                'merged': merged_entity,
                'normalized_term': norm_term
            })
        else:
            new_entities.append(merged_entity)
    
    return overlap, new_entities

def enhance_existing_entity(existing, merged):
    """Enhance existing entity with merged data"""
    enhanced = existing.copy()
    
    # Add missing aliases
    existing_aliases = set(normalize_term(alias) for alias in existing.get('aliases', []))
    new_aliases = []
    
    for alias in merged.get('aliases', []):
        if normalize_term(alias) not in existing_aliases:
            new_aliases.append(alias)
    
    if new_aliases:
        enhanced['aliases'] = existing.get('aliases', []) + new_aliases
    
    # Add entity_type if missing
    if 'entity_type' not in enhanced:
        enhanced['entity_type'] = merged.get('entity_type', 'unknown')
    
    # Update source files
    existing_sources = existing.get('source_files', [])
    merged_sources = merged.get('source_files', [])
    all_sources = list(set(existing_sources + merged_sources))
    enhanced['source_files'] = all_sources
    
    # Update last_updated
    enhanced['last_updated'] = merged['last_updated']
    
    return enhanced, len(new_aliases)

def prepare_new_entity(merged_entity):
    """Prepare new entity for insertion"""
    new_entity = merged_entity.copy()
    
    # Remove the MongoDB-specific fields that will be auto-generated
    new_entity.pop('_id', None)
    
    return new_entity

def update_existing_entities(db, overlapping_entities):
    """Update existing entities with enhanced data"""
    collection = db['pattern_libraries']
    updates_count = 0
    aliases_added = 0
    
    print(f"\nUpdating {len(overlapping_entities)} existing entities...")
    
    for overlap in overlapping_entities:
        existing = overlap['existing']
        merged = overlap['merged']
        
        # Only update if we have meaningful enhancements
        enhanced, new_aliases_count = enhance_existing_entity(existing, merged)
        
        if new_aliases_count > 0 or 'entity_type' not in existing:
            try:
                result = collection.update_one(
                    {"_id": existing["_id"]},
                    {"$set": {
                        "aliases": enhanced['aliases'],
                        "entity_type": enhanced['entity_type'],
                        "source_files": enhanced['source_files'],
                        "last_updated": enhanced['last_updated']
                    }}
                )
                
                if result.modified_count > 0:
                    updates_count += 1
                    aliases_added += new_aliases_count
                    if new_aliases_count > 0:
                        print(f"  Enhanced '{existing['term']}': +{new_aliases_count} aliases")
                
            except Exception as e:
                print(f"  Error updating '{existing['term']}': {e}")
    
    return updates_count, aliases_added

def insert_new_entities(db, new_entities):
    """Insert new entities in batches"""
    collection = db['pattern_libraries']
    inserted_count = 0
    batch_size = 100
    
    print(f"\nInserting {len(new_entities)} new entities in batches of {batch_size}...")
    
    for i in range(0, len(new_entities), batch_size):
        batch = new_entities[i:i + batch_size]
        prepared_batch = [prepare_new_entity(entity) for entity in batch]
        
        try:
            result = collection.insert_many(prepared_batch)
            batch_inserted = len(result.inserted_ids)
            inserted_count += batch_inserted
            print(f"  Batch {i//batch_size + 1}: Inserted {batch_inserted} entities")
            
        except Exception as e:
            print(f"  Error inserting batch {i//batch_size + 1}: {e}")
    
    return inserted_count

def generate_integration_report(timestamps, existing_count, updates_count, aliases_added, inserted_count, total_merged):
    """Generate integration report"""
    report = {
        "integration_summary": {
            "analysis_date_pdt": timestamps['pdt'],
            "analysis_date_utc": timestamps['utc'],
            "existing_entities_before": existing_count,
            "entities_updated": updates_count,
            "aliases_added_to_existing": aliases_added,
            "new_entities_inserted": inserted_count,
            "total_entities_after": existing_count + inserted_count,
            "total_merged_entities_processed": total_merged,
            "integration_success_rate": f"{((updates_count + inserted_count) / total_merged * 100):.1f}%"
        }
    }
    
    # Save report
    report_path = f"/home/ec2-user/zettit/services/json-parser/outputs/geographic_integration_report_{timestamps['filename']}.json"
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    return report_path

def main():
    """Main execution function"""
    print("Geographic Pattern Libraries Integration - Starting...")
    timestamps = get_timestamps()
    print(f"Analysis Date (PDT): {timestamps['pdt']}")
    print(f"Analysis Date (UTC): {timestamps['utc']}")
    
    # Connect to MongoDB
    print("\nConnecting to MongoDB...")
    db = connect_mongodb()
    if db is None:
        return False
    
    # Load merged entities
    print("Loading merged geographic entities...")
    merged_entities = load_merged_entities()
    if not merged_entities:
        return False
    print(f"Loaded {len(merged_entities)} merged entities")
    
    # Get existing entities
    print("Fetching existing entities from database...")
    existing_entities = get_existing_entities(db)
    print(f"Found {len(existing_entities)} existing geographic entities")
    
    # Analyze overlap
    print("\nAnalyzing overlap between existing and merged entities...")
    overlapping_entities, new_entities = analyze_overlap(existing_entities, merged_entities)
    print(f"Overlap: {len(overlapping_entities)} entities")
    print(f"New entities to insert: {len(new_entities)}")
    
    # Update existing entities
    updates_count, aliases_added = update_existing_entities(db, overlapping_entities)
    
    # Insert new entities
    inserted_count = insert_new_entities(db, new_entities)
    
    # Generate report
    report_path = generate_integration_report(
        timestamps, len(existing_entities), updates_count, 
        aliases_added, inserted_count, len(merged_entities)
    )
    
    # Final summary
    print(f"\n{'='*60}")
    print("GEOGRAPHIC PATTERN LIBRARIES INTEGRATION COMPLETED")
    print(f"{'='*60}")
    print(f"Existing entities: {len(existing_entities)}")
    print(f"Entities updated: {updates_count}")
    print(f"Aliases added to existing: {aliases_added}")
    print(f"New entities inserted: {inserted_count}")
    print(f"Total entities after integration: {len(existing_entities) + inserted_count}")
    print(f"Integration success rate: {((updates_count + inserted_count) / len(merged_entities) * 100):.1f}%")
    print(f"\nIntegration report saved: {report_path}")
    
    return True

if __name__ == "__main__":
    success = main()
    if not success:
        exit(1)