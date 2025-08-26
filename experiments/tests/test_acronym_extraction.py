#!/usr/bin/env python3
"""
Test script for acronym-embedded pattern detection
Tests enhanced Script 03 logic using patterns from MongoDB pattern_libraries collection
"""

import os
import re
import json
from typing import Dict, List
from dotenv import load_dotenv
from pymongo import MongoClient

# Load environment variables
load_dotenv()

def connect_to_mongodb():
    """Connect to MongoDB and return patterns collection."""
    try:
        mongodb_uri = os.getenv('MONGODB_URI')
        client = MongoClient(mongodb_uri, serverSelectionTimeoutMS=10000)
        client.admin.command('ping')
        
        db = client['deathstar']
        patterns_collection = db['pattern_libraries']
        
        print("✅ Connected to MongoDB")
        return client, patterns_collection
        
    except Exception as e:
        print(f"❌ MongoDB connection failed: {e}")
        return None, None

def load_acronym_patterns(patterns_collection):
    """Load acronym_embedded patterns from MongoDB."""
    try:
        cursor = patterns_collection.find({
            "type": "report_type",
            "format_type": "acronym_embedded",
            "active": True
        })
        
        patterns = list(cursor)
        print(f"✅ Loaded {len(patterns)} acronym patterns from database")
        return patterns
        
    except Exception as e:
        print(f"❌ Failed to load acronym patterns: {e}")
        return []

def test_acronym_extraction():
    """Test acronym extraction with real titles and database patterns."""
    
    # Connect to database
    client, patterns_collection = connect_to_mongodb()
    if not client:
        return
    
    # Load acronym patterns from database
    acronym_patterns = load_acronym_patterns(patterns_collection)
    if not acronym_patterns:
        print("No acronym patterns found in database")
        return
    
    # Test titles with acronyms (from actual database)
    test_titles = [
        "Directed Energy Weapons Market Size, DEW Industry Report, 2025",
        "Direct Methanol Fuel Cell Market Size, DMFC Industry Report, 2025", 
        "Dynamic Random Access Memory Market, DRAM Industry Report, 2025",
        "Fatty Methyl Ester Sulfonate Market, FMES Industry Report, 2018-2025",
        "Fluorinated Ethylene Propylene Market Size, FEP Industry Report, 2025",
        "Gas To Liquids Market Size, Share, Global GTL Industry Report, 2025",
        "Polyvinyl Chloride Membrane Market Size, PVC Industry Report, 2025",
        "Bio-Based PVC Market Size, Share, Global Industry Report, 2019-2025",  # No acronym
        "CMOS Image Sensor Market Size, Industry Report, 2030"  # No acronym
    ]
    
    results = []
    
    print(f"\n🧪 Testing {len(test_titles)} titles against {len(acronym_patterns)} acronym patterns...")
    
    for title in test_titles:
        print(f"\n🔍 Testing: {title}")
        
        # Simulate Script 02 date removal
        title_no_date = re.sub(r',?\s*\d{4}(?:-\d{4})?\s*$', '', title).strip()
        print(f"   After date removal: {title_no_date}")
        
        matched = False
        
        for pattern_data in acronym_patterns:
            pattern_regex = pattern_data["pattern"]
            match = re.search(pattern_regex, title_no_date)
            
            if match:
                acronym = match.group(1)  # Captured acronym
                base_report_type = pattern_data["base_type"]
                
                # Remove the matched report type from title for pipeline
                remaining_title = title_no_date.replace(match.group(0), '').strip()
                remaining_title = re.sub(r'^\s*[,\-–—]\s*', '', remaining_title)
                remaining_title = re.sub(r'\s*[,\-–—]\s*$', '', remaining_title)
                
                # Add acronym in parentheses to end of pipeline text
                pipeline_text = f"{remaining_title} ({acronym})" if remaining_title else f"({acronym})"
                
                result = {
                    "original_title": title,
                    "title_after_date_removal": title_no_date,
                    "matched_pattern_term": pattern_data["term"],
                    "extracted_acronym": acronym,
                    "base_report_type": base_report_type,
                    "pipeline_forward_text": pipeline_text,
                    "confidence": pattern_data["confidence_weight"]
                }
                
                results.append(result)
                
                print(f"   ✅ MATCH: {pattern_data['term']}")
                print(f"   📤 Report Type: {base_report_type}")
                print(f"   🔤 Acronym: {acronym}")
                print(f"   🚀 Pipeline Forward: {pipeline_text}")
                
                matched = True
                break
        
        if not matched:
            print(f"   ❌ No acronym pattern matched (likely normal report type)")
    
    print(f"\n📊 Summary: {len(results)} titles matched acronym patterns out of {len(test_titles)} tested")
    
    # Save results
    timestamp = "20250826_051500"
    output_file = f"outputs/{timestamp}_acronym_extraction_test.json"
    
    os.makedirs("outputs", exist_ok=True)
    with open(output_file, "w") as f:
        json.dump({
            "test_metadata": {
                "test_date": "2025-08-26 05:15:00 UTC",
                "titles_tested": len(test_titles),
                "acronym_patterns_loaded": len(acronym_patterns),
                "successful_matches": len(results)
            },
            "pattern_definitions": acronym_patterns,
            "test_results": results
        }, f, indent=2, default=str)
    
    print(f"💾 Results saved to {output_file}")
    
    client.close()
    return results

if __name__ == "__main__":
    test_acronym_extraction()