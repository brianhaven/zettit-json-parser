#!/usr/bin/env python3

"""
Fix regex double-space errors in pattern_libraries collection.

The issue: Many patterns have \s+\s*&\s*\s+ instead of \s*&\s*
This prevents matching of patterns like "Market Size & Share Report"
"""

import os
import re
from pymongo import MongoClient
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def fix_regex_patterns():
    """Fix regex double-space errors in pattern_libraries collection."""
    client = MongoClient(os.getenv('MONGODB_URI'))
    db = client['deathstar']
    
    print("Fixing regex double-space errors in pattern_libraries...")
    
    # Find patterns with double-space errors
    patterns_to_fix = list(db.pattern_libraries.find({
        "type": "report_type",
        "active": True,
        "pattern": {"$regex": "\\\\s\\+.*\\\\s\\*.*\\\\s\\+", "$options": "i"}
    }))
    
    print(f"Found {len(patterns_to_fix)} patterns with double-space errors")
    
    fixed_count = 0
    
    for pattern_doc in patterns_to_fix:
        old_pattern = pattern_doc['pattern']
        
        # Fix the double space issues
        # Replace \s+\s*&\s*\s+ with \s*&\s*
        new_pattern = re.sub(r'\\s\+\\s\*&\\s\*\\s\+', r'\\s*&\\s*', old_pattern)
        
        # Also fix \s+\s*,\s+ patterns if they exist
        new_pattern = re.sub(r'\\s\+\\s\*,\\s\*\\s\+', r'\\s*,\\s*', new_pattern)
        
        # Fix other double spaces like \s+\s*
        new_pattern = re.sub(r'\\s\+\\s\*', r'\\s*', new_pattern)
        
        if new_pattern != old_pattern:
            print(f"\nFixing pattern: {pattern_doc['term']}")
            print(f"OLD: {old_pattern}")
            print(f"NEW: {new_pattern}")
            
            # Update the pattern in database
            db.pattern_libraries.update_one(
                {"_id": pattern_doc["_id"]},
                {
                    "$set": {
                        "pattern": new_pattern,
                        "last_updated": {"$date": "2025-08-26T03:50:00.000Z"},
                        "notes": "Fixed regex double-space errors for proper matching"
                    }
                }
            )
            fixed_count += 1
    
    print(f"\n✅ Fixed {fixed_count} patterns with regex double-space errors")
    
    # Also fix the specific "Market, Industry Report" pattern that has wrong comma spacing
    comma_pattern = db.pattern_libraries.find_one({
        "type": "report_type", 
        "active": True,
        "term": "Manual Review #6: Market, Industry Report"
    })
    
    if comma_pattern:
        old_comma_pattern = comma_pattern['pattern']
        # Fix \s+,\s+ to \s*,\s+
        new_comma_pattern = old_comma_pattern.replace(r'\bMarket\s+,\s+', r'\bMarket\s*,\s+')
        
        if new_comma_pattern != old_comma_pattern:
            print(f"\nFixing comma spacing pattern: {comma_pattern['term']}")
            print(f"OLD: {old_comma_pattern}")  
            print(f"NEW: {new_comma_pattern}")
            
            db.pattern_libraries.update_one(
                {"_id": comma_pattern["_id"]},
                {
                    "$set": {
                        "pattern": new_comma_pattern,
                        "last_updated": {"$date": "2025-08-26T03:50:00.000Z"},
                        "notes": "Fixed comma spacing regex for proper matching"
                    }
                }
            )
            fixed_count += 1
    
    print(f"\n🎯 TOTAL FIXED: {fixed_count} regex patterns")
    print("✅ All regex double-space errors have been corrected!")
    
    client.close()

if __name__ == "__main__":
    fix_regex_patterns()