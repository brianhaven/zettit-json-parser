#!/usr/bin/env python3
"""
Debug compound pattern matching issue for EMEA.
Test specific case: "Europe, Middle East and Africa Financial Services"
Should match "Europe, Middle East and Africa" as single unit.
"""

import os
import re
import sys
from dotenv import load_dotenv
from pymongo import MongoClient

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

load_dotenv()

def test_compound_pattern():
    # Connect to MongoDB
    client = MongoClient(os.getenv('MONGODB_URI'))
    db = client['deathstar']
    patterns_collection = db['pattern_libraries']
    
    # Test text
    test_text = "Europe, Middle East and Africa Financial Services"
    print(f"Testing: '{test_text}'")
    print("-" * 60)
    
    # Get relevant patterns
    patterns = list(patterns_collection.find({
        "type": "geographic_entity",
        "active": True,
        "$or": [
            {"term": "Europe, Middle East and Africa"},
            {"term": "Europe"},
            {"term": "Middle East"},
            {"term": "Africa"},
            {"term": "EMEA"}
        ]
    }).sort("priority", 1))
    
    print("Found patterns:")
    for p in patterns:
        print(f"  - '{p['term']}' (priority {p['priority']})")
    print()
    
    # Test each pattern individually
    for pattern in patterns:
        term = pattern['term']
        aliases = pattern.get('aliases', [])
        priority = pattern['priority']
        
        # Build regex like the script does
        terms = [term] + aliases
        escaped_terms = []
        
        for t in terms:
            if t and t.strip():
                if ',' in t or ' and ' in t or ' & ' in t:
                    escaped_term = re.escape(t.strip())
                    escaped_term = escaped_term.replace(r'\,', r'\s*,\s*')
                    escaped_term = escaped_term.replace(r'\ and\ ', r'\s+(?:and|&)\s+')
                    escaped_term = escaped_term.replace(r'\ \&\ ', r'\s*&\s*')
                    escaped_terms.append(f"\\b{escaped_term}\\b")
                else:
                    escaped_term = re.escape(t.strip())
                    escaped_terms.append(f"\\b{escaped_term}\\b")
        
        escaped_terms.sort(key=len, reverse=True)
        regex_pattern = f"({'|'.join(escaped_terms)})"
        
        print(f"Pattern: '{term}' (priority {priority})")
        print(f"  Regex: {regex_pattern}")
        
        # Test the pattern
        matches = list(re.finditer(regex_pattern, test_text, re.IGNORECASE))
        if matches:
            for match in matches:
                print(f"  ✓ MATCH: '{match.group()}' at position {match.span()}")
        else:
            print(f"  ✗ No match")
        print()
    
    client.close()

if __name__ == "__main__":
    test_compound_pattern()