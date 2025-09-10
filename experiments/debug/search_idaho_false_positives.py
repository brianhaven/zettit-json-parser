#!/usr/bin/env python3
"""
Search for potential Idaho false positive matches in market titles.
"""

import os
import re
from pymongo import MongoClient
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Connect to MongoDB
client = MongoClient(os.getenv('MONGODB_URI'))
db = client['deathstar']
markets_collection = db['markets_raw']

def search_idaho_patterns():
    """Search for titles that might match ID incorrectly."""
    
    print("=" * 80)
    print("SEARCHING FOR POTENTIAL IDAHO FALSE POSITIVES")
    print("=" * 80)
    
    # Search for titles containing "ID" as a standalone word/abbreviation
    # but NOT actually referring to Idaho
    
    # Common patterns where ID might appear:
    patterns_to_check = [
        r'\bID\b',  # Standalone ID
        r'\bId\b',  # Mixed case
        r'ID[A-Z]',  # ID followed by capital (like IDC, IDF)
        r'[A-Z]ID',  # ID preceded by capital (like AID, BID)
    ]
    
    print("\n1. Searching for titles with standalone 'ID':")
    print("-" * 50)
    
    # Find titles with ID that might not be Idaho
    id_titles = markets_collection.find({
        "report_title_short": {"$regex": r"\bID\b", "$options": "i"}
    }).limit(30)
    
    count = 0
    for doc in id_titles:
        title = doc.get('report_title_short', '')
        if title:
            count += 1
            # Highlight ID occurrences
            highlighted = re.sub(r'(\bID\b)', r'**\1**', title, flags=re.IGNORECASE)
            print(f"{count:3}. {highlighted}")
    
    if count == 0:
        print("  No titles found with standalone 'ID'")
    
    print(f"\nTotal found with 'ID': {count}")
    
    # Search for compound ID patterns
    print("\n2. Searching for compound ID patterns (IDC, RFID, etc.):")
    print("-" * 50)
    
    compound_patterns = [
        r'RFID',
        r'IDC',
        r'IDF',
        r'IDE',
        r'IDS',
        r'IDM',
        r'IDN',
        r'IDaaS',
        r'ID Card',
        r'ID Management',
        r'User ID',
        r'Device ID',
        r'Product ID'
    ]
    
    for pattern in compound_patterns:
        count = markets_collection.count_documents({
            "report_title_short": {"$regex": pattern, "$options": "i"}
        })
        if count > 0:
            print(f"  {pattern}: {count} occurrences")
            # Show first example
            example = markets_collection.find_one({
                "report_title_short": {"$regex": pattern, "$options": "i"}
            })
            if example:
                title = example.get('report_title_short', '')[:100]
                highlighted = re.sub(f'({pattern})', r'**\1**', title, flags=re.IGNORECASE)
                print(f"    Example: {highlighted}...")
    
    # Search for Idaho (full word)
    print("\n3. Searching for 'Idaho' (full word):")
    print("-" * 50)
    
    idaho_titles = markets_collection.find({
        "report_title_short": {"$regex": r"\bIdaho\b", "$options": "i"}
    }).limit(10)
    
    count = 0
    for doc in idaho_titles:
        title = doc.get('report_title_short', '')
        if title:
            count += 1
            highlighted = re.sub(r'(\bIdaho\b)', r'**\1**', title, flags=re.IGNORECASE)
            print(f"{count:3}. {highlighted}")
    
    if count == 0:
        print("  No titles found with 'Idaho'")
    
    # Check for other potentially problematic state abbreviations
    print("\n4. Other problematic state abbreviations:")
    print("-" * 50)
    
    problematic = {
        'OR': 'Oregon',
        'IN': 'Indiana', 
        'ME': 'Maine',
        'IT': 'Italy',  # Not a state but similar issue
        'TO': 'Toronto',
        'BY': 'Belarus',
        'AT': 'Austria',
        'IS': 'Iceland',
        'IF': None,  # Common word
        'OF': None,  # Common word
        'ON': 'Ontario'
    }
    
    for abbrev, region in problematic.items():
        # Only check those that are actual geographic abbreviations
        if region:
            count = markets_collection.count_documents({
                "report_title_short": {"$regex": f"\\b{abbrev}\\b", "$options": "i"}
            })
            if count > 0:
                print(f"  '{abbrev}' ({region}): {count} potential matches")

if __name__ == "__main__":
    search_idaho_patterns()