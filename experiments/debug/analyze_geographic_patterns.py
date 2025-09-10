#!/usr/bin/env python3
"""
Analyze geographic patterns in MongoDB for Issue #18 resolution.
Identify problematic aliases and document pattern structure.
"""

import os
import json
from pymongo import MongoClient
from dotenv import load_dotenv
from collections import Counter

# Load environment variables
load_dotenv()

# Connect to MongoDB
client = MongoClient(os.getenv('MONGODB_URI'))
db = client['deathstar']
patterns_collection = db['pattern_libraries']

def analyze_geographic_patterns():
    """Analyze geographic patterns for problematic aliases."""
    
    print("=" * 80)
    print("GEOGRAPHIC PATTERN ANALYSIS FOR ISSUE #18")
    print("=" * 80)
    
    # 1. Count total geographic patterns
    total_geo = patterns_collection.count_documents({"type": "geographic_entity"})
    print(f"\nTotal geographic entity patterns: {total_geo}")
    
    # 2. Find Idaho pattern specifically
    print("\n" + "=" * 80)
    print("IDAHO PATTERN ANALYSIS")
    print("=" * 80)
    
    idaho = patterns_collection.find_one({"type": "geographic_entity", "term": "Idaho"})
    if idaho:
        print(f"Idaho pattern found:")
        print(f"  Term: {idaho.get('term')}")
        print(f"  Aliases: {idaho.get('aliases', [])}")
        print(f"  Priority: {idaho.get('priority')}")
        if 'abbreviation' in idaho:
            print(f"  Abbreviation field: {idaho.get('abbreviation')}")
        if 'excluded_aliases' in idaho:
            print(f"  Excluded aliases: {idaho.get('excluded_aliases')}")
        if 'problematic_terms' in idaho:
            print(f"  Problematic terms: {idaho.get('problematic_terms')}")
    
    # 3. Search for patterns with ID alias
    print("\n" + "=" * 80)
    print("PATTERNS WITH 'ID' ALIAS")
    print("=" * 80)
    
    id_patterns = patterns_collection.find({
        "type": "geographic_entity",
        "aliases": "ID"
    })
    
    for pattern in id_patterns:
        print(f"  {pattern.get('term')}: aliases = {pattern.get('aliases', [])}")
    
    # 4. Find patterns with separate fields for problematic terms
    print("\n" + "=" * 80)
    print("PATTERNS WITH SEGREGATED PROBLEMATIC TERMS")
    print("=" * 80)
    
    fields_to_check = [
        'abbreviation', 'excluded_aliases', 'problematic_terms', 
        'disabled_aliases', 'non_matching_aliases', 'context_required'
    ]
    
    for field in fields_to_check:
        count = patterns_collection.count_documents({
            "type": "geographic_entity",
            field: {"$exists": True}
        })
        if count > 0:
            print(f"\nPatterns with '{field}' field: {count}")
            examples = patterns_collection.find({
                "type": "geographic_entity",
                field: {"$exists": True}
            }).limit(5)
            for ex in examples:
                print(f"  {ex.get('term')}: {field} = {ex.get(field)}")
    
    # 5. Find short abbreviations that might be problematic
    print("\n" + "=" * 80)
    print("SHORT ABBREVIATIONS (1-3 CHARACTERS)")
    print("=" * 80)
    
    all_patterns = patterns_collection.find({"type": "geographic_entity"})
    short_aliases = {}
    
    for pattern in all_patterns:
        term = pattern.get('term', '')
        aliases = pattern.get('aliases', [])
        for alias in aliases:
            if isinstance(alias, str) and 1 <= len(alias) <= 3:
                if alias not in short_aliases:
                    short_aliases[alias] = []
                short_aliases[alias].append(term)
    
    print(f"\nFound {len(short_aliases)} short abbreviations:")
    for alias, terms in sorted(short_aliases.items()):
        if len(alias) <= 2:  # Focus on very short ones
            print(f"  '{alias}': {terms}")
    
    # 6. Find compound regions
    print("\n" + "=" * 80)
    print("COMPOUND REGIONS (with 'and', '&', or commas)")
    print("=" * 80)
    
    compound_patterns = patterns_collection.find({
        "type": "geographic_entity",
        "$or": [
            {"term": {"$regex": " and ", "$options": "i"}},
            {"term": {"$regex": " & ", "$options": "i"}},
            {"term": {"$regex": ",", "$options": "i"}}
        ]
    }).limit(20)
    
    for pattern in compound_patterns:
        print(f"  {pattern.get('term')} (priority: {pattern.get('priority', 999)})")
    
    # 7. Check for "North America and Europe" specifically
    print("\n" + "=" * 80)
    print("NORTH AMERICA AND EUROPE PATTERN")
    print("=" * 80)
    
    na_europe = patterns_collection.find_one({
        "type": "geographic_entity",
        "term": "North America and Europe"
    })
    
    if na_europe:
        print("Found 'North America and Europe' pattern:")
        print(f"  Term: {na_europe.get('term')}")
        print(f"  Priority: {na_europe.get('priority')}")
        print(f"  Aliases: {na_europe.get('aliases', [])}")
    else:
        print("'North America and Europe' pattern not found")
    
    # 8. Look for Ontario pattern as reference (mentioned in issue)
    print("\n" + "=" * 80)
    print("ONTARIO PATTERN (REFERENCE)")
    print("=" * 80)
    
    ontario = patterns_collection.find_one({
        "type": "geographic_entity",
        "term": "Ontario"
    })
    
    if ontario:
        print("Ontario pattern structure:")
        for key, value in ontario.items():
            if key != '_id':
                print(f"  {key}: {value}")
    
    # 9. Find all patterns with state/province abbreviations
    print("\n" + "=" * 80)
    print("US STATE ABBREVIATIONS ANALYSIS")
    print("=" * 80)
    
    state_abbrevs = ['AL', 'AK', 'AZ', 'AR', 'CA', 'CO', 'CT', 'DE', 'FL', 'GA',
                     'HI', 'ID', 'IL', 'IN', 'IA', 'KS', 'KY', 'LA', 'ME', 'MD',
                     'MA', 'MI', 'MN', 'MS', 'MO', 'MT', 'NE', 'NV', 'NH', 'NJ',
                     'NM', 'NY', 'NC', 'ND', 'OH', 'OK', 'OR', 'PA', 'RI', 'SC',
                     'SD', 'TN', 'TX', 'UT', 'VT', 'VA', 'WA', 'WV', 'WI', 'WY']
    
    problematic_abbrevs = []
    for abbrev in state_abbrevs:
        pattern = patterns_collection.find_one({
            "type": "geographic_entity",
            "aliases": abbrev
        })
        if pattern:
            # Check if this abbreviation could be problematic
            if abbrev in ['ID', 'IN', 'OR', 'ME', 'IT', 'TO', 'BY', 'AT', 'IS', 'IF', 'OF', 'ON']:
                problematic_abbrevs.append((abbrev, pattern.get('term')))
    
    if problematic_abbrevs:
        print("\nPotentially problematic state abbreviations (common words):")
        for abbrev, state in problematic_abbrevs:
            print(f"  '{abbrev}' -> {state}")

if __name__ == "__main__":
    analyze_geographic_patterns()