#!/usr/bin/env python3
"""
Test regex patterns manually
"""

import re

# Test text
test_text = "Wood Preservatives Market Size, Share, Growth Report"

# Pattern from the database
pattern = r'\bMarket\s+Size,\s+Share,\s+Growth\s+Report(?:\s*$|[,.])'

print(f"Test text: {test_text}")
print(f"Pattern: {pattern}")
print()

# Test the match
match = re.search(pattern, test_text)
if match:
    print(f"✅ MATCH: '{match.group()}'")
    print(f"   Start: {match.start()}, End: {match.end()}")
else:
    print("❌ NO MATCH")
    
# Test variations
print("\n=== Pattern Variations ===")

patterns_to_test = [
    r'\bMarket\s+Size,\s+Share,\s+Growth\s+Report(?:\s*$|[,.])',  # Original
    r'Market\s+Size,\s+Share,\s+Growth\s+Report(?:\s*$|[,.])',   # No word boundary
    r'\bMarket\s+Size,\s+Share,\s+Growth\s+Report',              # No terminator
    r'Market\s+Size,\s+Share,\s+Growth\s+Report',                # Simple
]

for i, pat in enumerate(patterns_to_test, 1):
    match = re.search(pat, test_text)
    status = "✅ MATCH" if match else "❌ NO MATCH"
    result = f"'{match.group()}'" if match else "None"
    print(f"{i}. {status}: {result}")
    print(f"   Pattern: {pat}")
    print()