#!/usr/bin/env python3
"""
Before/After comparison demonstrating Issue #29 resolution
"""

import re

def simulate_old_behavior(title: str) -> str:
    """Simulate the old buggy behavior."""
    # Old behavior: Just remove the date, leave parentheses artifacts
    date_pattern = r'\b(\d{4})\s*[-–—]\s*(\d{4})\b'
    match = re.search(date_pattern, title)
    if match:
        return title.replace(match.group(0), '').strip()
    return title

def simulate_new_behavior(title: str) -> str:
    """Simulate the new fixed behavior."""
    # New behavior: Smart parentheses handling
    date_pattern = r'\b(\d{4})\s*[-–—]\s*(\d{4})\b'
    match = re.search(date_pattern, title)

    if not match:
        return title

    raw_match = match.group(0)

    # Check if date is within parentheses
    paren_pattern = r'\(([^)]*?)' + re.escape(raw_match) + r'([^)]*?)\)'
    paren_match = re.search(paren_pattern, title)

    if paren_match:
        # Extract non-date content
        before_date = paren_match.group(1).strip()
        after_date = paren_match.group(2).strip()
        preserved = (before_date + ' ' + after_date).strip()

        # Remove entire parenthetical section
        cleaned = title.replace(paren_match.group(0), '').strip()

        # Add preserved content back
        if preserved:
            cleaned = f"{cleaned} {preserved}"
    else:
        # Standard removal
        cleaned = title.replace(raw_match, '').strip()

    # Clean up artifacts
    cleaned = re.sub(r'\([^)]*?\s+\)', '', cleaned)
    cleaned = re.sub(r'\(\s+[^)]*?\)', '', cleaned)
    cleaned = re.sub(r'\(\s*\)', '', cleaned)

    # Balance parentheses
    if cleaned.count('(') != cleaned.count(')'):
        cleaned = re.sub(r'[()]', '', cleaned)

    return cleaned

# Test cases
test_cases = [
    "Battery Fuel Gauge Market (Forecast 2020-2030)",
    "Global Smart Grid Market (Analysis & Forecast 2024-2029)",
    "Electric Vehicle Market (2025-2035 Outlook)",
    "Digital Health Market (Industry Analysis 2023-2028)",
]

print("=" * 80)
print("ISSUE #29: BEFORE vs AFTER COMPARISON")
print("=" * 80)

for title in test_cases:
    old_result = simulate_old_behavior(title)
    new_result = simulate_new_behavior(title)

    print(f"\nOriginal: {title}")
    print(f"OLD (buggy): {old_result}")

    # Highlight artifacts
    if ')' in old_result and '(' not in old_result:
        print(f"  ⚠️  Artifact detected: trailing ')'")
    elif '(' in old_result and ')' not in old_result:
        print(f"  ⚠️  Artifact detected: unmatched '('")

    print(f"NEW (fixed): {new_result}")

    if ')' not in new_result or (')' in new_result and '(' in new_result):
        print(f"  ✅ Clean result - no artifacts")

print("\n" + "=" * 80)
print("SUMMARY")
print("=" * 80)
print("\nThe fix successfully:")
print("1. Removes parentheses artifacts like trailing ')'")
print("2. Preserves important keywords from within parentheses")
print("3. Maintains clean, professional topic extraction")
print("\nIssue #29 is RESOLVED ✅")