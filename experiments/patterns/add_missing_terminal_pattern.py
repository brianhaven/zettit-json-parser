#!/usr/bin/env python3
"""
Add Missing Terminal Pattern - Market Size And Share
Adds the specific terminal pattern that caused the failure in test results.
"""

import os
import re
import sys
from pymongo import MongoClient
from dotenv import load_dotenv
from datetime import datetime, timezone

# Load environment variables
load_dotenv()

def get_pdt_timestamp():
    """Get current timestamp in PDT and UTC"""
    now_utc = datetime.now(timezone.utc)
    pdt_offset = -7 if datetime.now().month in range(3, 11) else -8  # Rough PDT/PST
    now_pdt = now_utc.replace(tzinfo=timezone.utc).astimezone(timezone.utc)
    
    pdt_str = now_pdt.strftime('%Y-%m-%d %H:%M:%S PDT')
    utc_str = now_utc.strftime('%Y-%m-%d %H:%M:%S UTC')
    return pdt_str, utc_str

def add_missing_pattern():
    """Add the missing 'Market Size And Share' terminal pattern"""
    
    # Connect to MongoDB
    client = MongoClient(os.getenv('MONGODB_URI'))
    db = client['deathstar']
    collection = db['pattern_libraries']
    
    # The missing pattern that caused the failure
    pattern_data = {
        'type': 'REPORT_TYPE',
        'term': 'Market Size And Share',
        'pattern': r'\bMarket\s+Size\s+(?:And|&)\s+Share(?:\s*$|[,.])',
        'format_type': 'terminal_type',
        'priority': 1,
        'active': True,
        'success_count': 0,
        'failure_count': 0,
        'created_date': datetime.now(timezone.utc),
        'last_updated': datetime.now(timezone.utc),
        'notes': 'Added to fix failing extraction for "Automatic Weapons Market Size And Share"'
    }
    
    # Check if pattern already exists
    existing = collection.find_one({
        'type': 'REPORT_TYPE',
        'term': pattern_data['term']
    })
    
    if existing:
        print(f"Pattern '{pattern_data['term']}' already exists")
        return False
    
    # Insert the pattern
    result = collection.insert_one(pattern_data)
    
    if result.inserted_id:
        print(f"✅ Successfully added pattern: '{pattern_data['term']}'")
        print(f"   Pattern: {pattern_data['pattern']}")
        print(f"   Format: {pattern_data['format_type']}")
        return True
    else:
        print("❌ Failed to add pattern")
        return False

def verify_pattern():
    """Test the pattern against the failing title"""
    test_title = "Automatic Weapons Market Size And Share"
    pattern = r'\bMarket\s+Size\s+(?:And|&)\s+Share(?:\s*$|[,.])'
    
    match = re.search(pattern, test_title, re.IGNORECASE)
    if match:
        print(f"✅ Pattern test successful:")
        print(f"   Title: '{test_title}'")
        print(f"   Match: '{match.group()}'")
        print(f"   Position: {match.span()}")
        return True
    else:
        print(f"❌ Pattern test failed for: '{test_title}'")
        return False

def main():
    """Main execution"""
    pdt_time, utc_time = get_pdt_timestamp()
    
    print("=" * 80)
    print("Adding Missing Terminal Pattern: Market Size And Share")
    print(f"Analysis Date (PDT): {pdt_time}")
    print(f"Analysis Date (UTC): {utc_time}")
    print("=" * 80)
    
    # Test pattern first
    print("\n1. Testing pattern against failing title...")
    if not verify_pattern():
        print("❌ Pattern verification failed - aborting")
        return
    
    # Add to database
    print("\n2. Adding pattern to MongoDB...")
    if add_missing_pattern():
        print("\n✅ Missing pattern successfully added!")
        print("\nThis should resolve the failure on: 'Automatic Weapons Market Size And Share'")
    else:
        print("\n❌ Failed to add missing pattern")

if __name__ == "__main__":
    main()