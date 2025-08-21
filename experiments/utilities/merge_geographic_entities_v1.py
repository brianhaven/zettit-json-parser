#!/usr/bin/env python3
"""
Geographic Entity Merger for Pattern Libraries Collection
Merges region-candidates.json into regions.json and formats for MongoDB pattern_libraries
"""

import json
import os
from datetime import datetime
from collections import defaultdict
import pytz

def get_timestamps():
    """Generate PDT and UTC timestamps"""
    utc_now = datetime.now(pytz.UTC)
    pdt_now = utc_now.astimezone(pytz.timezone('US/Pacific'))
    
    return {
        'pdt': pdt_now.strftime('%Y-%m-%d %H:%M:%S PDT'),
        'utc': utc_now.strftime('%Y-%m-%d %H:%M:%S UTC'),
        'filename': pdt_now.strftime('%Y%m%d_%H%M%S')
    }

def load_json_file(filepath):
    """Load JSON file with error handling"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading {filepath}: {e}")
        return None

def normalize_term(term):
    """Normalize term for comparison (lowercase, strip spaces)"""
    return term.lower().strip()

def collect_all_entities(regions_data, candidates_data):
    """Collect all entities from both files"""
    all_entities = {}
    entity_sources = {}
    
    # Process existing regions.json
    print("Processing existing regions.json...")
    for entity in regions_data.get('geographic_entities', []):
        term = entity['term']
        norm_term = normalize_term(term)
        
        if norm_term not in all_entities:
            all_entities[norm_term] = {
                'term': term,
                'aliases': list(entity.get('aliases', [])),
                'type': entity.get('type', 'unknown'),
                'sources': ['regions.json']
            }
            entity_sources[norm_term] = ['regions.json']
        
    print(f"Loaded {len(all_entities)} entities from regions.json")
    
    # Process candidates
    print("Processing region-candidates.json...")
    candidates_added = 0
    aliases_added = 0
    
    for category in candidates_data.get('geographic_entities', []):
        category_name = category.get('category', 'unknown')
        print(f"  Processing category: {category_name}")
        
        for entity in category.get('entities', []):
            term = entity['term']
            norm_term = normalize_term(term)
            
            if norm_term not in all_entities:
                # New entity
                all_entities[norm_term] = {
                    'term': term,
                    'aliases': list(entity.get('aliases', [])),
                    'type': entity.get('type', 'unknown'),
                    'sources': [f'candidates:{category_name}']
                }
                entity_sources[norm_term] = [f'candidates:{category_name}']
                candidates_added += 1
            else:
                # Merge aliases and update sources
                existing = all_entities[norm_term]
                new_aliases = entity.get('aliases', [])
                
                for alias in new_aliases:
                    norm_alias = normalize_term(alias)
                    # Check if alias already exists as term or alias
                    alias_exists = False
                    
                    if norm_alias == norm_term:
                        continue  # Skip if alias same as term
                    
                    if norm_alias in [normalize_term(a) for a in existing['aliases']]:
                        alias_exists = True
                    
                    if not alias_exists:
                        existing['aliases'].append(alias)
                        aliases_added += 1
                
                # Update sources
                if f'candidates:{category_name}' not in entity_sources[norm_term]:
                    entity_sources[norm_term].append(f'candidates:{category_name}')
                    existing['sources'].append(f'candidates:{category_name}')
    
    print(f"Added {candidates_added} new entities from candidates")
    print(f"Added {aliases_added} new aliases to existing entities")
    print(f"Total entities: {len(all_entities)}")
    
    return all_entities, entity_sources

def detect_term_alias_conflicts(all_entities):
    """Detect when aliases should be promoted to primary terms"""
    conflicts = []
    alias_to_terms = defaultdict(list)
    
    # Build reverse mapping: alias -> terms that use it
    for norm_term, entity in all_entities.items():
        for alias in entity['aliases']:
            norm_alias = normalize_term(alias)
            alias_to_terms[norm_alias].append(norm_term)
    
    # Check for conflicts
    for norm_alias, terms in alias_to_terms.items():
        if len(terms) > 1:
            conflicts.append({
                'alias': norm_alias,
                'terms': terms,
                'entities': [all_entities[term] for term in terms]
            })
    
    return conflicts

def resolve_conflicts(all_entities, conflicts):
    """Resolve term/alias conflicts"""
    print(f"\nResolving {len(conflicts)} conflicts...")
    
    for conflict in conflicts:
        alias = conflict['alias']
        terms = conflict['terms']
        entities = conflict['entities']
        
        print(f"\nConflict: '{alias}' appears as alias for multiple terms:")
        for i, entity in enumerate(entities):
            print(f"  {i+1}. {entity['term']} (type: {entity['type']})")
        
        # Simple resolution strategy: keep alias with most specific entity type
        type_priority = {
            'country': 10,
            'us_state': 9,
            'major_city': 8,
            'canadian_province': 7,
            'chinese_region': 6,
            'indian_state': 6,
            'brazilian_state': 6,
            'german_state': 6,
            'french_region': 6,
            'japanese_region': 6,
            'uk_region': 6,
            'metropolitan_area': 5,
            'tech_region': 4,
            'census_region': 3,
            'sub_regional': 2,
            'multi_regional': 1,
            'unknown': 0
        }
        
        # Find entity with highest priority
        best_entity = None
        best_score = -1
        
        for entity in entities:
            score = type_priority.get(entity['type'], 0)
            if score > best_score:
                best_score = score
                best_entity = entity
        
        # Remove alias from other entities
        for entity in entities:
            if entity != best_entity:
                entity['aliases'] = [a for a in entity['aliases'] if normalize_term(a) != alias]
        
        print(f"  Resolved: kept alias '{alias}' with '{best_entity['term']}'")
    
    return all_entities

def format_for_pattern_libraries(all_entities):
    """Format entities for MongoDB pattern_libraries collection"""
    timestamps = get_timestamps()
    pattern_entities = []
    
    print("\nFormatting for pattern_libraries collection...")
    
    for norm_term, entity in all_entities.items():
        # Create primary term entry
        primary_entry = {
            "type": "geographic_entity",
            "term": entity['term'],
            "aliases": entity['aliases'],
            "priority": get_priority_for_type(entity['type']),
            "active": True,
            "success_count": 0,
            "failure_count": 0,
            "created_date": timestamps['utc'],
            "last_updated": timestamps['utc'],
            "source_files": entity['sources'],
            "entity_type": entity['type']
        }
        pattern_entities.append(primary_entry)
    
    print(f"Created {len(pattern_entities)} pattern library entries")
    return pattern_entities, timestamps

def get_priority_for_type(entity_type):
    """Get priority based on entity type"""
    priority_map = {
        'country': 10,
        'us_state': 9,
        'major_city': 8,
        'canadian_province': 7,
        'chinese_region': 6,
        'indian_state': 6,
        'brazilian_state': 6,
        'german_state': 6,
        'french_region': 6,
        'japanese_region': 6,
        'uk_region': 6,
        'metropolitan_area': 5,
        'tech_region': 4,
        'census_region': 3,
        'sub_regional': 2,
        'multi_regional': 1,
        'trade_bloc': 5,
        'market_designation': 3,
        'global': 8,
        'continental': 7,
        'oceanic': 4,
        'designation': 2,
        'historical_country': 5,
        'us_territory': 7,
        'us_city': 6,
        'us_regional': 4
    }
    return priority_map.get(entity_type, 1)

def save_results(merged_regions, pattern_entities, timestamps):
    """Save all result files"""
    base_path = "/home/ec2-user/zettit/services/json-parser/resources/"
    
    # Save merged regions.json
    merged_regions_data = {
        "geographic_entities": list(merged_regions.values())
    }
    
    with open(f"{base_path}regions_merged.json", 'w', encoding='utf-8') as f:
        json.dump(merged_regions_data, f, indent=2, ensure_ascii=False)
    
    # Save pattern libraries format
    pattern_data = {
        "analysis_date_pdt": timestamps['pdt'],
        "analysis_date_utc": timestamps['utc'],
        "total_entities": len(pattern_entities),
        "pattern_libraries_entries": pattern_entities
    }
    
    with open(f"{base_path}geographic_pattern_libraries_{timestamps['filename']}.json", 'w', encoding='utf-8') as f:
        json.dump(pattern_data, f, indent=2, ensure_ascii=False)
    
    # Save summary report
    summary = {
        "merge_summary": {
            "analysis_date_pdt": timestamps['pdt'],
            "analysis_date_utc": timestamps['utc'],
            "total_entities_merged": len(merged_regions),
            "pattern_libraries_entries_created": len(pattern_entities),
            "entity_type_breakdown": {}
        }
    }
    
    # Count by type
    type_counts = defaultdict(int)
    for entity in merged_regions.values():
        type_counts[entity['type']] += 1
    
    summary["merge_summary"]["entity_type_breakdown"] = dict(type_counts)
    
    with open(f"{base_path}geographic_merge_summary_{timestamps['filename']}.json", 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
    
    return {
        'merged_regions': f"{base_path}regions_merged.json",
        'pattern_libraries': f"{base_path}geographic_pattern_libraries_{timestamps['filename']}.json",
        'summary': f"{base_path}geographic_merge_summary_{timestamps['filename']}.json"
    }

def main():
    """Main execution function"""
    print("Geographic Entity Merger - Starting...")
    timestamps = get_timestamps()
    print(f"Analysis Date (PDT): {timestamps['pdt']}")
    print(f"Analysis Date (UTC): {timestamps['utc']}")
    
    base_path = "/home/ec2-user/zettit/services/json-parser/resources/"
    
    # Load source files
    print("\nLoading source files...")
    regions_data = load_json_file(f"{base_path}regions.json")
    candidates_data = load_json_file(f"{base_path}region-candidates.json")
    
    if not regions_data or not candidates_data:
        print("Error: Could not load source files")
        return False
    
    # Collect and merge all entities
    all_entities, entity_sources = collect_all_entities(regions_data, candidates_data)
    
    # Detect and resolve conflicts
    conflicts = detect_term_alias_conflicts(all_entities)
    if conflicts:
        all_entities = resolve_conflicts(all_entities, conflicts)
    
    # Format for pattern libraries
    pattern_entities, timestamps = format_for_pattern_libraries(all_entities)
    
    # Save results
    print("\nSaving results...")
    file_paths = save_results(all_entities, pattern_entities, timestamps)
    
    print(f"\nMerge completed successfully!")
    print(f"Files created:")
    for name, path in file_paths.items():
        print(f"  {name}: {path}")
    
    print(f"\nSummary:")
    print(f"  Total entities: {len(all_entities)}")
    print(f"  Pattern library entries: {len(pattern_entities)}")
    print(f"  Conflicts resolved: {len(conflicts)}")
    
    return True

if __name__ == "__main__":
    success = main()
    if not success:
        exit(1)