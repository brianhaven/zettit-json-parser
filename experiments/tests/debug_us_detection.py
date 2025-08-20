#!/usr/bin/env python3

"""
Debug script to test U.S. detection issue
"""

import re

def test_us_detection():
    """Test U.S. detection with current approach"""
    
    # Current approach (converting to lowercase)
    alias = "U.S."
    alias_lower = alias.lower()  # becomes "u.s."
    
    title = "U.S. Vital Signs Monitoring Devices Market"
    
    # Current regex approach
    pattern = r'\b' + re.escape(alias_lower) + r'\b'
    print(f"Testing alias: '{alias}' -> lowercase: '{alias_lower}'")
    print(f"Title: '{title}'")
    print(f"Pattern: '{pattern}'")
    
    # Test case-insensitive match
    matches = list(re.finditer(pattern, title, re.IGNORECASE))
    print(f"Matches found: {len(matches)}")
    for match in matches:
        print(f"  Match: '{match.group()}' at positions {match.start()}-{match.end()}")
    
    print("\n" + "="*60)
    
    # Better approach (keep original case for pattern)
    pattern_original = r'\b' + re.escape(alias) + r'\b'
    print(f"Testing with original case pattern: '{pattern_original}'")
    
    matches_original = list(re.finditer(pattern_original, title, re.IGNORECASE))
    print(f"Matches found: {len(matches_original)}")
    for match in matches_original:
        print(f"  Match: '{match.group()}' at positions {match.start()}-{match.end()}")
    
    print("\n" + "="*60)
    
    # Test other variations
    test_cases = [
        "U.S. Market Report",
        "The U.S. automotive industry",
        "US Market Analysis", 
        "USA Economic Report",
        "United States data"
    ]
    
    aliases = ["U.S.", "US", "USA", "United States"]
    
    print("Testing multiple aliases and titles:")
    for test_title in test_cases:
        print(f"\nTitle: '{test_title}'")
        for test_alias in aliases:
            pattern = r'\b' + re.escape(test_alias) + r'\b'
            matches = list(re.finditer(pattern, test_title, re.IGNORECASE))
            if matches:
                print(f"  ✅ '{test_alias}' found: {matches[0].group()}")
            else:
                print(f"  ❌ '{test_alias}' not found")

if __name__ == "__main__":
    test_us_detection()