#!/usr/bin/env python3

import os
import re
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def generate_update_commands():
    """Generate MongoDB update commands for term cleanup"""
    
    # Define transformations
    transformations = []
    
    # Manual Review patterns - generate regex-based updates  
    print("# Step 1: Remove Manual Review prefixes (estimated 251 documents)")
    print('db.pattern_libraries.updateMany(')
    print('  {"type": "report_type", "term": {"$regex": "^Manual Review #\\\\d+:\\\\s*", "$options": "i"}},')
    print('  [{"$set": {"term": {"$replaceOne": {"input": "$term", "find": "Manual Review #", "replacement": ""}}}}]')
    print(')')
    print()
    
    # Technical suffix removals
    suffix_updates = [
        ('Terminal', 'Terminal'),
        ('Terminal2', 'Terminal2'), 
        ('Embedded', 'Embedded'),
        ('Prefix', 'Prefix')
    ]
    
    print("# Step 2: Remove technical suffixes")
    for find_text, desc in suffix_updates:
        print(f'# Remove {desc} suffix')
        print(f'db.pattern_libraries.updateMany(')
        print(f'  {{"type": "report_type", "term": {{"$regex": "\\\\s+{find_text}\\\\d*$", "$options": "i"}}}},')
        print(f'  [{{"$set": {{"term": {{"$replaceOne": {{"input": "$term", "find": " {find_text}", "replacement": ""}}}}}}}}]')
        print(f')')
        print()
    
    # Specific corrections
    specific_fixes = {
        "Market Size Share Terminal2": "Market Size, Share"
    }
    
    print("# Step 3: Specific term corrections")
    for old_term, new_term in specific_fixes.items():
        print(f'db.pattern_libraries.updateOne(')
        print(f'  {{"type": "report_type", "term": "{old_term}"}},')
        print(f'  {{"$set": {{"term": "{new_term}"}}}}')
        print(f')')
        print()

if __name__ == "__main__":
    generate_update_commands()