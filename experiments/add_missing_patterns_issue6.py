#!/usr/bin/env python3

"""
Add missing patterns identified from failed extractions (GitHub Issue #6)
Validates existing patterns and adds any missing ones.
"""

import os
import re
from datetime import datetime, timezone
import pytz
from pymongo import MongoClient
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def get_timestamps():
    """Generate PDT and UTC timestamps."""
    utc_now = datetime.now(timezone.utc)
    pdt_tz = pytz.timezone('America/Los_Angeles')
    pdt_now = utc_now.astimezone(pdt_tz)
    
    pdt_str = pdt_now.strftime('%Y-%m-%d %H:%M:%S PDT')
    utc_str = utc_now.strftime('%Y-%m-%d %H:%M:%S UTC')
    
    return pdt_str, utc_str

def check_pattern_exists(collection, term, format_type=None):
    """Check if a pattern exists in the database."""
    query = {
        'type': 'REPORT_TYPE',
        'term': term
    }
    if format_type:
        query['format_type'] = format_type
    return collection.find_one(query)

def add_pattern(collection, term, format_type, pattern=None):
    """Add a pattern to the database if it doesn't exist."""
    # Check if already exists
    existing = check_pattern_exists(collection, term, format_type)
    if existing:
        return False, f"Pattern already exists: {term} ({format_type})"
    
    # Generate pattern if not provided
    if not pattern:
        # Remove "Market " prefix and escape special chars
        clean_term = term.replace("Market ", "").strip()
        escaped = re.escape(clean_term)
        
        # Replace escaped operators with flexible patterns
        escaped = escaped.replace(r'\&', r'\s*&\s*')
        escaped = escaped.replace(r'\,', r',\s*')
        escaped = escaped.replace(r'\-', r'\s*-\s*')
        
        # Create full pattern based on format type
        if format_type == 'terminal_type':
            pattern = f'\\bMarket\\s+{escaped}(?:\\s*$|[,.])'
        elif format_type == 'embedded_type':
            pattern = f'\\bMarket\\s+{escaped}\\b'
        elif format_type == 'prefix_type':
            pattern = f'^{escaped}\\s+'
        else:  # compound_type
            pattern = f'\\bMarket\\s+{escaped}(?:\\s*$|[,.])'
    
    # Create document
    doc = {
        'type': 'REPORT_TYPE',
        'term': term,
        'pattern': pattern,
        'format_type': format_type,
        'active': True,
        'priority': 1,
        'created_date': datetime.now(timezone.utc),
        'last_updated': datetime.now(timezone.utc),
        'success_count': 0,
        'failure_count': 0,
        'notes': 'Added from Issue #6 pattern validation'
    }
    
    result = collection.insert_one(doc)
    return True, f"Added pattern: {term} ({format_type})"

def main():
    pdt_str, utc_str = get_timestamps()
    
    print("Missing Pattern Addition and Validation")
    print("=" * 60)
    print(f"Analysis Date (PDT): {pdt_str}")
    print(f"Analysis Date (UTC): {utc_str}")
    print("=" * 60)
    print()
    
    # Connect to MongoDB
    client = MongoClient(os.getenv('MONGODB_URI'))
    db = client['deathstar']
    collection = db['pattern_libraries']
    
    # Patterns to check and add based on failed extractions
    patterns_to_check = [
        # From failed extractions
        ('Market Size And Share', 'terminal_type'),
        ('Market Size And Share', 'embedded_type'),
        ('Market Size Trends Report', 'compound_type'),
        ('Industry in', 'embedded_type'),  # For "Industry in [Region]"
        ('- Analysis & Statistics', 'prefix_type'),  # Dash prefix pattern
        ('Market by', 'embedded_type'),  # For "Market by [attribute]"
        ('Market for', 'embedded_type'),  # Should already exist but check
        ('Market in', 'embedded_type'),  # Should already exist but check
        ('Report', 'terminal_type'),  # Basic report pattern
        ('Market Report', 'compound_type'),
    ]
    
    added_count = 0
    existing_count = 0
    
    print("Checking and adding patterns...")
    print("-" * 40)
    
    for term, format_type in patterns_to_check:
        success, message = add_pattern(collection, term, format_type)
        print(f"  {message}")
        if success:
            added_count += 1
        else:
            existing_count += 1
    
    print()
    print("Validation of specific patterns from failures:")
    print("-" * 40)
    
    # Check specific patterns that should match failed titles
    test_patterns = [
        ('Market Size And Share', 'China E-commerce Market Size And Share'),
        ('Market Size And Share', 'Agricultural Inoculants Market Size And Share'),
        ('Market Size And Share', 'Specialty Medical Chairs Market Size And Share'),
        ('- Analysis & Statistics', 'Retail Industry in Australia - Analysis & Statistics'),
        ('Market by', 'Emerging Lighting Technology Market by Color Temperature'),
    ]
    
    for pattern_term, test_title in test_patterns:
        pattern = check_pattern_exists(collection, pattern_term)
        if pattern:
            regex = pattern.get('pattern', '')
            if regex:
                try:
                    if re.search(regex, test_title, re.IGNORECASE):
                        print(f"  ✓ '{pattern_term}' matches '{test_title}'")
                    else:
                        print(f"  ✗ '{pattern_term}' DOES NOT match '{test_title}'")
                        print(f"    Pattern: {regex}")
                except Exception as e:
                    print(f"  ✗ Error testing '{pattern_term}': {e}")
            else:
                print(f"  ✗ No regex pattern for '{pattern_term}'")
        else:
            print(f"  ✗ Pattern '{pattern_term}' not found in database")
    
    print()
    print("Summary:")
    print(f"  Patterns added: {added_count}")
    print(f"  Patterns already existed: {existing_count}")
    print(f"  Total patterns checked: {len(patterns_to_check)}")
    
    # Get total count of report type patterns
    total_patterns = collection.count_documents({'type': 'REPORT_TYPE'})
    print(f"  Total REPORT_TYPE patterns in database: {total_patterns}")
    
    client.close()
    print("\n✅ Pattern validation and addition complete!")

if __name__ == "__main__":
    main()