#!/usr/bin/env python3
"""
Test regex patterns with full title including date
"""

import re

# Test text WITH date (what the debug shows is being processed)
test_text = "Wood Preservatives Market Size, Share, Growth Report 2030"
test_text2 = "Wood Preservatives Market Size, Share, Growth Report"  # Without date

# Pattern from the database
pattern = r'\bMarket\s+Size,\s+Share,\s+Growth\s+Report(?:\s*$|[,.])'

print(f"Test text WITH date: {test_text}")
print(f"Test text WITHOUT date: {test_text2}")
print(f"Pattern: {pattern}")
print()

# Test both versions
for i, text in enumerate([test_text, test_text2], 1):
    match = re.search(pattern, text)
    status = "✅ MATCH" if match else "❌ NO MATCH"
    result = f"'{match.group()}'" if match else "None"
    print(f"{i}. {status}: {result}")
    print(f"   Text: {text}")
    print()

print("=== Issue Analysis ===")
print("The pattern expects the report type to be at the END: (?:\\s*$|[,.])")
print("But 'Growth Report 2030' has text after 'Report', so \\s*$ doesn't match")
print("And there's no comma or period after 'Report', so [,.] doesn't match either")
print()
print("This is why the longer pattern fails and the shorter 'Market Size, Share,' succeeds.")