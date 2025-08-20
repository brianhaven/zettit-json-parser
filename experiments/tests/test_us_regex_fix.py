#!/usr/bin/env python3

"""
Test improved regex patterns for U.S. detection
"""

import re

def test_improved_us_detection():
    """Test improved U.S. detection patterns"""
    
    test_cases = [
        "U.S. Market Report",
        "The U.S. automotive industry", 
        "US Market Analysis",
        "USA Economic Report",
        "United States data",
        "U.S.A. exports",
        "North America U.S. region"
    ]
    
    aliases = ["U.S.", "US", "USA", "U.S.A.", "United States"]
    
    def create_improved_pattern(alias):
        """Create improved regex pattern that handles punctuation properly"""
        escaped = re.escape(alias)
        
        # For patterns with periods, use lookahead/lookbehind for word boundaries
        if '.' in alias:
            # Use negative lookbehind and lookahead for alphanumeric characters
            return r'(?<![a-zA-Z0-9])' + escaped + r'(?![a-zA-Z0-9])'
        else:
            # Use standard word boundaries for regular words
            return r'\b' + escaped + r'\b'
    
    print("Testing improved regex patterns:")
    print("="*70)
    
    for test_title in test_cases:
        print(f"\nTitle: '{test_title}'")
        for alias in aliases:
            pattern = create_improved_pattern(alias)
            matches = list(re.finditer(pattern, test_title, re.IGNORECASE))
            if matches:
                print(f"  ✅ '{alias}' found: '{matches[0].group()}' (pattern: {pattern})")
            else:
                print(f"  ❌ '{alias}' not found (pattern: {pattern})")

if __name__ == "__main__":
    test_improved_us_detection()