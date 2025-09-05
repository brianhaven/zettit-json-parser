#!/usr/bin/env python3
"""
Debug Regex Pattern for Market Term Extraction
===============================================

Test the regex pattern to understand why it's extracting too much.
"""

import re

def debug_market_regex():
    """Debug the market term extraction regex pattern."""
    
    print("=== Debugging Market Term Regex Pattern ===\n")
    
    test_cases = [
        {
            "title": "Sulfur, Arsine, and Mercury Remover Market in Oil & Gas Industry",
            "market_type": "market_in",
            "expected_market_term": "Market in Oil & Gas",
            "expected_remaining": "Sulfur, Arsine, and Mercury Remover Industry"
        },
        {
            "title": "Carbon Black Market For Textile Fibers Growth Report",
            "market_type": "market_for", 
            "expected_market_term": "Market For Textile Fibers",
            "expected_remaining": "Carbon Black Growth Report"
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        title = test_case["title"]
        market_type = test_case["market_type"]
        expected_market_term = test_case["expected_market_term"]
        expected_remaining = test_case["expected_remaining"]
        
        print(f"=== Test {i}: {market_type} ===")
        print(f"Title: '{title}'")
        print(f"Expected Market Term: '{expected_market_term}'")
        print(f"Expected Remaining: '{expected_remaining}'")
        print()
        
        # Convert market_type back to phrase
        market_phrase = market_type.replace('_', ' ').title()
        print(f"Market Phrase: '{market_phrase}'")
        
        # Test the current regex pattern
        pattern = rf'\b{re.escape(market_phrase)}\s+([^,]+?)(?:[,]|$)'
        print(f"Regex Pattern: {pattern}")
        
        match = re.search(pattern, title, re.IGNORECASE)
        if match:
            print(f"✓ Pattern matched")
            print(f"  Full match (group 0): '{match.group(0)}'")
            print(f"  Market context (group 1): '{match.group(1)}'")
            print(f"  Match start: {match.start()}")
            print(f"  Match end: {match.end()}")
            
            # Show what gets extracted
            full_market_term = match.group(0).rstrip(',\-–— ')
            market_context = match.group(1).strip()
            
            print(f"  Extracted full market term: '{full_market_term}'")
            print(f"  Extracted market context: '{market_context}'")
            
            # Show remaining title calculation
            remaining_title = title[:match.start()] + title[match.end():]
            remaining_title = remaining_title.strip(' ,\-–—')
            print(f"  Calculated remaining title: '{remaining_title}'")
            
            # Show pipeline forward calculation
            prefix_part = title[:match.start()].strip()
            print(f"  Prefix part: '{prefix_part}'")
            
            if prefix_part:
                connector_word = market_phrase.split()[-1].lower()
                pipeline_forward = f"{prefix_part} {connector_word} {market_context}"
            else:
                pipeline_forward = market_context
            print(f"  Pipeline forward: '{pipeline_forward}'")
            
        else:
            print(f"❌ Pattern did not match")
        
        print()
        
        # Try alternative patterns
        print("Alternative Pattern Tests:")
        
        # Pattern 1: Stop at first space followed by uppercase word (potential report type)
        alt_pattern1 = rf'\b{re.escape(market_phrase)}\s+(\w+(?:\s+&\s+\w+)?(?:\s+\w+)?)'
        match1 = re.search(alt_pattern1, title, re.IGNORECASE)
        if match1:
            print(f"  Alt Pattern 1: '{alt_pattern1}' → '{match1.group(0)}' | context: '{match1.group(1)}'")
        
        # Pattern 2: Stop at certain keywords that indicate report types
        report_keywords = r'(?:Analysis|Report|Study|Forecast|Outlook|Trends|Market|Size|Share|Growth|Industry)'
        alt_pattern2 = rf'\b{re.escape(market_phrase)}\s+([^,]*?)(?=\s+{report_keywords}|,|$)'
        match2 = re.search(alt_pattern2, title, re.IGNORECASE)
        if match2:
            print(f"  Alt Pattern 2: '{alt_pattern2}' → '{match2.group(0)}' | context: '{match2.group(1)}'")
        
        print("-" * 80)
        print()

if __name__ == "__main__":
    debug_market_regex()