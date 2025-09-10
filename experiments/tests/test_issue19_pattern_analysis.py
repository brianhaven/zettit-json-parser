#!/usr/bin/env python3
"""
Analyze the regex pattern issue for market term extraction with ampersands.
"""

import re
import os
import sys
from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv()

# Connect to MongoDB
client = MongoClient(os.getenv('MONGODB_URI'))
db = client['deathstar']

# Get all keywords from database
keywords_cursor = db['pattern_libraries'].find({
    "type": "report_type_dictionary",
    "$or": [
        {"subtype": "primary_keyword"},
        {"subtype": "secondary_keyword"}
    ],
    "active": True
})

all_keywords = [doc["term"] for doc in keywords_cursor if doc["term"] != "Market"]

print("Total keywords (excluding Market):", len(all_keywords))
print("Sample keywords:", all_keywords[:10])

# Test patterns
test_titles = [
    "U.S. Windows & Patio Doors Market For Single Family Homes, Report, 2030",
    "Oman Industrial Salts Market For Oil & Gas Industry Report, 2020-2027"
]

print("\n" + "="*80)
print("PATTERN ANALYSIS FOR MARKET TERM EXTRACTION")
print("="*80)

for title in test_titles:
    print(f"\nAnalyzing: {title}")
    print("-" * 60)
    
    market_phrase = "Market For"
    
    # Original pattern from Script 03 v4
    all_keywords_pattern = '|'.join([re.escape(kw) for kw in all_keywords])
    pattern1 = rf'\b{re.escape(market_phrase)}\s+([^,]*?)(?=\s+(?:{all_keywords_pattern})|$)'
    
    print(f"\nPattern 1 (original): Uses [^,]*? to capture up to comma or keyword")
    match1 = re.search(pattern1, title, re.IGNORECASE)
    if match1:
        print(f"  ✓ Match found:")
        print(f"    Full match: '{match1.group(0)}'")
        print(f"    Market context (group 1): '{match1.group(1)}'")
        print(f"    Ampersand preserved: {'&' in match1.group(1)}")
    else:
        print(f"  ✗ No match found")
    
    # Alternative pattern - more greedy to capture everything
    pattern2 = rf'\b{re.escape(market_phrase)}\s+(.+?)(?=,\s*(?:{all_keywords_pattern})|$)'
    
    print(f"\nPattern 2 (alternative): Uses .+? to capture any character")
    match2 = re.search(pattern2, title, re.IGNORECASE)
    if match2:
        print(f"  ✓ Match found:")
        print(f"    Full match: '{match2.group(0)}'")
        print(f"    Market context (group 1): '{match2.group(1)}'")
        print(f"    Ampersand preserved: {'&' in match2.group(1)}")
    else:
        print(f"  ✗ No match found")
    
    # Check what happens without lookahead
    pattern3 = rf'\b{re.escape(market_phrase)}\s+([^,]+)'
    
    print(f"\nPattern 3 (simple): Capture everything up to comma")
    match3 = re.search(pattern3, title, re.IGNORECASE)
    if match3:
        print(f"  ✓ Match found:")
        print(f"    Full match: '{match3.group(0)}'")
        print(f"    Market context (group 1): '{match3.group(1)}'")
        print(f"    Ampersand preserved: {'&' in match3.group(1)}")
    else:
        print(f"  ✗ No match found")

print("\n" + "="*80)
print("ANALYSIS SUMMARY")
print("="*80)
print("\nThe issue is NOT with the regex pattern itself - [^,]*? correctly captures '&'")
print("The problem is that the pattern doesn't match the first test case at all!")
print("\nReason: 'Report' appears in the keywords list, so the lookahead (?=\\s+Report)")
print("stops the match at 'Homes' before capturing ', Report'")
print("\nFor 'U.S. Windows & Patio Doors Market For Single Family Homes, Report, 2030':")
print("- The pattern stops at 'Homes' because 'Report' is next")
print("- This means it fails to match properly")
print("\nSolution: Adjust the pattern to handle commas before keywords better")