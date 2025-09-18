#!/usr/bin/env python3
"""
Test the _create_cleaned_title method directly
"""

import re

def _create_cleaned_title(title: str, raw_match: str, preserved_words: list) -> str:
    """
    Create a cleaned title with date pattern removed but important words preserved.
    Enhanced with Phase 2 fix for Issue #29: Better parentheses cleanup.

    Args:
        title: Original title
        raw_match: The matched date pattern text
        preserved_words: Words to preserve from the pattern

    Returns:
        Cleaned title with preserved words and proper parentheses handling
    """
    if not raw_match:
        cleaned = title
    else:
        # Remove the raw match
        cleaned = title.replace(raw_match, '').strip()

    # Add preserved words back
    if preserved_words:
        preserved_text = ' '.join(preserved_words)
        if cleaned:
            cleaned = f"{cleaned} {preserved_text}"
        else:
            cleaned = preserved_text

    # Phase 2 Enhancement for Issue #29: Comprehensive parentheses cleanup
    # Remove parentheses with content that has trailing or leading spaces
    cleaned = re.sub(r'\([^)]*?\s+\)', '', cleaned)  # Remove ( anything-space )
    cleaned = re.sub(r'\(\s+[^)]*?\)', '', cleaned)  # Remove ( space-anything )
    cleaned = re.sub(r'\(\s*\)', '', cleaned)  # Remove empty ()
    cleaned = re.sub(r'\[\s*\]', '', cleaned)  # Remove empty []

    # Balance parentheses if unmatched
    open_parens = cleaned.count('(')
    close_parens = cleaned.count(')')
    if open_parens != close_parens:
        # If unbalanced, remove all parentheses to avoid artifacts
        cleaned = re.sub(r'[()]', '', cleaned)

    # Balance brackets if unmatched
    open_brackets = cleaned.count('[')
    close_brackets = cleaned.count(']')
    if open_brackets != close_brackets:
        # If unbalanced, remove all brackets to avoid artifacts
        cleaned = re.sub(r'[\[\]]', '', cleaned)

    # Clean up spacing and punctuation
    cleaned = re.sub(r'\s+', ' ', cleaned).strip()
    cleaned = re.sub(r'[,\.]+$', '', cleaned)  # Remove trailing punctuation

    return cleaned

# Test cases
test_cases = [
    ("Battery Fuel Gauge Market (Forecast 2020-2030)", "2020-2030", []),
    ("Global Smart Grid Market (Analysis & Forecast 2024-2029)", "2024-2029", []),
    ("Electric Vehicle Market (2025-2035 Outlook)", "2025-2035", []),
    ("Digital Health Market (Industry Analysis 2023-2028)", "2023-2028", []),
]

for title, raw_match, preserved_words in test_cases:
    # Simulate what happens after date removal
    after_removal = title.replace(raw_match, '').strip()
    print(f"\nOriginal: {title}")
    print(f"Raw Match: {raw_match}")
    print(f"After Removal: {after_removal}")

    # Apply the cleanup function
    cleaned = _create_cleaned_title(title, raw_match, preserved_words)
    print(f"After Cleanup: {cleaned}")

    # Check for artifacts
    has_artifacts = any(char in cleaned for char in ['(', ')', '[', ']'])
    print(f"Has Artifacts: {has_artifacts}")