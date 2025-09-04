#!/usr/bin/env python3
"""
Debug Market Term Extraction Logic
=====================================

Specifically debug the regex patterns and extraction logic to understand
why characters are being cut off in market term processing.
"""

import re

def debug_market_term_extraction():
    """Debug the specific regex patterns causing issues."""
    
    print("=== Market Term Extraction Debug ===\n")
    
    test_cases = [
        {
            "title": "Sulfur, Arsine, and Mercury Remover Market in Oil & Gas Industry",
            "market_pattern": r"\bmarket\s+in\b",
            "expected_entity": "Oil & Gas",
            "issue": "Stray 'n' character"
        },
        {
            "title": "Carbon Black Market For Textile Fibers Growth Report, 2020",
            "market_pattern": r"\bmarket\s+for\b",
            "expected_entity": "Textile Fibers",
            "issue": "'Te' missing from Textile"
        }
    ]
    
    for i, case in enumerate(test_cases, 1):
        title = case["title"]
        market_pattern = case["market_pattern"]
        expected_entity = case["expected_entity"]
        issue = case["issue"]
        
        print(f"Test {i}: {issue}")
        print(f"Original: '{title}'")
        print(f"Pattern: {market_pattern}")
        print()
        
        # Step 1: Find market term match
        match = re.search(market_pattern, title, re.IGNORECASE)
        if match:
            matched_text = match.group(0)
            match_start = match.start()
            match_end = match.end()
            
            print(f"Match found: '{matched_text}' at position {match_start}-{match_end}")
            
            # Step 2: Extract remaining part after market term
            remaining_part = title[match_end:].strip()
            print(f"Remaining after market term: '{remaining_part}'")
            
            # Step 3: Apply entity extraction pattern
            report_indicators = r'\b(Analysis|Report|Study|Forecast|Outlook|Trends|Market|Size|Share|Growth|Industry)\b'
            entity_pattern = rf'^(.*?)(?:\s+(?={report_indicators})|\s*,|$)'
            
            print(f"Entity pattern: {entity_pattern}")
            
            entity_match = re.search(entity_pattern, remaining_part, re.IGNORECASE)
            if entity_match:
                entity = entity_match.group(1).strip()
                print(f"Entity extracted: '{entity}'")
                print(f"Expected entity: '{expected_entity}'")
                
                # Step 4: Show what would be removed
                market_term_with_entity = f"{matched_text} {entity}"
                print(f"Will remove: '{market_term_with_entity}'")
                
                pattern_to_remove = re.escape(market_term_with_entity)
                print(f"Removal pattern: {pattern_to_remove}")
                
                # Step 5: Apply removal
                remaining_title = re.sub(rf'\b{pattern_to_remove}\b', '', title, count=1, flags=re.IGNORECASE).strip()
                print(f"After removal: '{remaining_title}'")
                
                # Step 6: Show character-by-character what happened
                print("\nCharacter-by-character analysis:")
                print(f"Original:  '{title}'")
                print(f"Removing:  '{market_term_with_entity}'")
                
                # Find where the problem occurs
                removal_start = title.lower().find(market_term_with_entity.lower())
                if removal_start != -1:
                    removal_end = removal_start + len(market_term_with_entity)
                    before = title[:removal_start]
                    removed = title[removal_start:removal_end]
                    after = title[removal_end:]
                    
                    print(f"Before:    '{before}'")
                    print(f"Removed:   '{removed}'")
                    print(f"After:     '{after}'")
                    print(f"Result:    '{before}{after}'.strip() = '{(before + after).strip()}'")
            
        print("-" * 80)
        print()

if __name__ == "__main__":
    debug_market_term_extraction()