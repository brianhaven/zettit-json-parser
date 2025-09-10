#!/usr/bin/env python3
"""
Comprehensive analysis of problematic geographic abbreviations.
Identify all candidates for pattern library restructuring.
"""

import os
import re
from pymongo import MongoClient
from dotenv import load_dotenv
from collections import defaultdict

# Load environment variables
load_dotenv()

# Connect to MongoDB
client = MongoClient(os.getenv('MONGODB_URI'))
db = client['deathstar']
patterns_collection = db['pattern_libraries']
markets_collection = db['markets_raw']

def analyze_problematic_abbreviations():
    """Comprehensive analysis of problematic geographic abbreviations."""
    
    print("=" * 80)
    print("COMPREHENSIVE PROBLEMATIC ABBREVIATION ANALYSIS")
    print("=" * 80)
    
    # Define potentially problematic abbreviations (common words or tech terms)
    problematic_candidates = {
        # US States
        'ID': ('Idaho', 'ID card, IDentity, IDC, IDE, IDS'),
        'IN': ('Indiana', 'IN (preposition), India (IN)'),
        'OR': ('Oregon', 'OR (conjunction)'),
        'ME': ('Maine', 'ME (pronoun), Middle East'),
        'IT': ('Italy', 'IT (Information Technology)'),
        'TO': ('Toronto/Tonga', 'TO (preposition)'),
        'BY': ('Belarus', 'BY (preposition)'),
        'AT': ('Austria', 'AT (preposition)'),
        'IS': ('Iceland', 'IS (verb)'),
        'ON': ('Ontario', 'ON (preposition)'),
        'OH': ('Ohio', 'OH (interjection)'),
        'OK': ('Oklahoma', 'OK/okay'),
        'HI': ('Hawaii', 'HI (greeting)'),
        'NO': ('Norway', 'NO (negative)'),
        'SO': ('Somalia', 'SO (conjunction)'),
        'US': ('United States', 'US (pronoun)'),
        'AS': ('American Samoa', 'AS (conjunction)'),
        'IF': (None, 'IF (conjunction)'),
        'OF': (None, 'OF (preposition)'),
        'BE': ('Belgium', 'BE (verb)'),
        'DO': ('Dominican Republic', 'DO (verb)'),
        'GO': ('Goiás', 'GO (verb)'),
        'UP': ('Uttar Pradesh', 'UP (direction)'),
        
        # Canadian Provinces  
        'BC': ('British Columbia', 'Before Christ'),
        'AB': ('Alberta', 'AB (abbreviation)'),
        'PE': ('Prince Edward Island', 'PE (Physical Education)'),
        'NT': ('Northwest Territories', 'NT (Windows NT)'),
        
        # Other regions
        'AM': ('Armenia', 'AM (morning)'),
        'PM': (None, 'PM (afternoon)'),
        'AD': ('Andorra', 'AD (Anno Domini)'),
        'AI': ('Anguilla', 'AI (Artificial Intelligence)'),
        'CD': ('Democratic Republic of Congo', 'CD (Compact Disc)'),
        'CM': ('Cameroon', 'CM (centimeter)'),
        'DM': ('Dominica', 'DM (Direct Message)'),
        'FM': ('Micronesia', 'FM (Frequency Modulation)'),
        'GM': ('Gambia', 'GM (General Motors)'),
        'HR': ('Croatia', 'HR (Human Resources)'),
        'IO': ('British Indian Ocean Territory', 'IO (Input/Output)'),
        'IP': (None, 'IP (Intellectual Property)'),
        'IR': ('Iran', 'IR (Infrared)'),
        'LA': ('Laos/Louisiana', 'LA (Los Angeles)'),
        'LI': ('Liechtenstein', 'LI (List Item)'),
        'MA': ('Morocco/Massachusetts', 'MA (Master of Arts)'),
        'MD': ('Moldova/Maryland', 'MD (Doctor, Maryland)'),
        'MO': ('Macau/Missouri', 'MO (Missouri, Month)'),
        'MS': ('Montserrat/Mississippi', 'MS (Microsoft, Master of Science)'),
        'MT': ('Malta/Montana', 'MT (Mountain, Montana)'),
        'NC': ('New Caledonia/North Carolina', 'NC (North Carolina)'),
        'NE': ('Niger/Nebraska', 'NE (Northeast)'),
        'PA': ('Panama/Pennsylvania', 'PA (Pennsylvania, Personal Assistant)'),
        'PR': ('Puerto Rico/Paraná', 'PR (Public Relations)'),
        'RE': ('Réunion', 'RE (Regarding)'),
        'SA': ('Saudi Arabia', 'SA (South America, South Africa)'),
        'SC': ('Seychelles/South Carolina', 'SC (South Carolina)'),
        'SE': ('Sweden', 'SE (Southeast)'),
        'TV': ('Tuvalu', 'TV (Television)'),
        'VA': ('Vatican City/Virginia', 'VA (Virginia, Veterans Affairs)'),
        'VC': ('Saint Vincent and the Grenadines', 'VC (Venture Capital)'),
    }
    
    # Check each problematic abbreviation
    results = []
    
    for abbrev, (region, conflicts) in problematic_candidates.items():
        # Check if this abbreviation exists in pattern library
        pattern = patterns_collection.find_one({
            "type": "geographic_entity",
            "aliases": abbrev
        })
        
        if pattern:
            # Count potential false positives in titles
            regex = f"\\b{re.escape(abbrev)}\\b"
            count = markets_collection.count_documents({
                "report_title_short": {"$regex": regex, "$options": "i"}
            })
            
            # Get sample titles
            samples = []
            docs = markets_collection.find({
                "report_title_short": {"$regex": regex, "$options": "i"}
            }).limit(3)
            
            for doc in docs:
                title = doc.get('report_title_short', '')
                if title:
                    # Highlight the abbreviation
                    highlighted = re.sub(f'(\\b{re.escape(abbrev)}\\b)', 
                                        f'**\\1**', title, flags=re.IGNORECASE)
                    samples.append(highlighted[:100])
            
            results.append({
                'abbrev': abbrev,
                'region': pattern.get('term'),
                'conflicts': conflicts,
                'count': count,
                'samples': samples,
                'has_archived': 'archived_aliases' in pattern
            })
    
    # Sort by count of potential issues
    results.sort(key=lambda x: x['count'], reverse=True)
    
    # Print analysis
    print("\n" + "=" * 80)
    print("HIGH PRIORITY PROBLEMATIC ABBREVIATIONS (>10 potential false positives)")
    print("=" * 80)
    
    high_priority = [r for r in results if r['count'] > 10]
    for r in high_priority:
        print(f"\n'{r['abbrev']}' -> {r['region']}")
        print(f"  Potential false positives: {r['count']}")
        print(f"  Conflicts with: {r['conflicts']}")
        print(f"  Already archived: {'Yes' if r['has_archived'] else 'No'}")
        if r['samples']:
            print("  Sample matches:")
            for s in r['samples']:
                print(f"    - {s}")
    
    print("\n" + "=" * 80)
    print("MEDIUM PRIORITY PROBLEMATIC ABBREVIATIONS (1-10 potential false positives)")
    print("=" * 80)
    
    medium_priority = [r for r in results if 1 <= r['count'] <= 10]
    for r in medium_priority:
        print(f"\n'{r['abbrev']}' -> {r['region']} ({r['count']} matches)")
        print(f"  Conflicts: {r['conflicts']}")
    
    print("\n" + "=" * 80)
    print("ALREADY RESOLVED PATTERNS (archived_aliases field exists)")
    print("=" * 80)
    
    # Check which patterns already have archived_aliases
    archived_patterns = patterns_collection.find({
        "type": "geographic_entity",
        "archived_aliases": {"$exists": True}
    })
    
    for pattern in archived_patterns:
        print(f"\n{pattern.get('term')}:")
        print(f"  Archived aliases: {pattern.get('archived_aliases')}")
    
    print("\n" + "=" * 80)
    print("COMPOUND REGIONS TO SPLIT")
    print("=" * 80)
    
    # Find compound regions that should be split
    compound_to_split = [
        "North America and Europe",
        "North and South America", 
        "Europe and Asia",
        "Asia and Middle East",
        "North and Central America"
    ]
    
    for compound in compound_to_split:
        pattern = patterns_collection.find_one({
            "type": "geographic_entity",
            "term": compound
        })
        if pattern:
            print(f"\n'{compound}' EXISTS in pattern library (should be removed)")
            print(f"  Priority: {pattern.get('priority')}")
        else:
            print(f"\n'{compound}' NOT FOUND (already removed or never existed)")
    
    print("\n" + "=" * 80)
    print("RECOMMENDATIONS")
    print("=" * 80)
    
    print("\n1. IMMEDIATE ACTIONS (High Impact):")
    print("   - Move 'ID' from Idaho aliases to archived_aliases")
    print("   - Move 'IN' from Indiana aliases to archived_aliases")
    print("   - Move 'OR' from Oregon aliases to archived_aliases")
    print("   - Move 'IT' from Italy aliases to archived_aliases")
    print("   - Move 'TO' from Toronto/Tonga aliases to archived_aliases")
    print("   - Move 'BY' from Belarus aliases to archived_aliases")
    print("   - Move 'ON' from Ontario aliases to archived_aliases (ALREADY DONE)")
    
    print("\n2. COMPOUND REGION CLEANUP:")
    print("   - Remove 'North America and Europe' pattern")
    print("   - Verify other compound patterns are legitimate (countries with 'and')")
    
    print("\n3. PATTERN LIBRARY STRUCTURE:")
    print("   - Use 'archived_aliases' field for problematic abbreviations")
    print("   - Keep full names and unambiguous aliases in 'aliases' field")
    print("   - Document reason for archiving in pattern notes")

if __name__ == "__main__":
    analyze_problematic_abbreviations()