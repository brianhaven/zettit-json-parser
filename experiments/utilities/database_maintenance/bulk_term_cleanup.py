#!/usr/bin/env python3

import os
import re
from pymongo import MongoClient
from dotenv import load_dotenv
import json

# Load environment variables
load_dotenv()

def bulk_cleanup_terms():
    """Perform bulk cleanup of report_type terms"""
    
    # Connect to MongoDB Atlas (not localhost)
    mongodb_uri = os.getenv('MONGODB_URI')
    if not mongodb_uri:
        print("ERROR: MONGODB_URI not found in environment")
        return False
        
    client = MongoClient(mongodb_uri)
    db = client['deathstar']
    collection = db['pattern_libraries']
    
    print("Connected to MongoDB Atlas")
    print("Starting bulk term cleanup for report_type documents...")
    
    # Get all report_type documents
    report_docs = list(collection.find({"type": "report_type"}))
    print(f"Found {len(report_docs)} report_type documents to process")
    
    updates_made = 0
    
    for doc in report_docs:
        original_term = doc['term']
        cleaned_term = clean_term(original_term)
        
        # Only update if term actually changed
        if cleaned_term != original_term:
            try:
                collection.update_one(
                    {"_id": doc['_id']}, 
                    {"$set": {"term": cleaned_term}}
                )
                updates_made += 1
                
                if updates_made <= 10:  # Show first 10 examples
                    print(f"Updated: \"{original_term}\" -> \"{cleaned_term}\"")
                elif updates_made == 11:
                    print("... (showing first 10 examples)")
                    
            except Exception as e:
                print(f"Error updating {doc['_id']}: {e}")
    
    print(f"\nBulk cleanup complete!")
    print(f"Total documents updated: {updates_made}")
    print(f"Documents unchanged: {len(report_docs) - updates_made}")
    
    client.close()
    return True

def clean_term(term):
    """Clean a single term by removing prefixes and suffixes"""
    if not term:
        return term
        
    cleaned = term
    
    # Step 1: Remove Manual Review prefixes
    cleaned = re.sub(r'^Manual Review #\d+:\s*', '', cleaned, flags=re.IGNORECASE)
    
    # Step 2: Remove technical suffixes
    cleaned = re.sub(r'\s+Terminal\d*$', '', cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r'\s+Embedded$', '', cleaned, flags=re.IGNORECASE) 
    cleaned = re.sub(r'\s+Prefix$', '', cleaned, flags=re.IGNORECASE)
    
    # Step 3: Specific corrections based on pattern analysis
    specific_corrections = {
        "Market Size Share": "Market Size, Share",  # Fix missing comma
        "Market Size Share Terminal2": "Market Size, Share",
    }
    
    if cleaned in specific_corrections:
        cleaned = specific_corrections[cleaned]
    
    # Clean up extra whitespace
    cleaned = re.sub(r'\s+', ' ', cleaned).strip()
    
    return cleaned

if __name__ == "__main__":
    print("MongoDB Report Type Term Cleanup Script")
    print("=" * 50)
    
    # Test cleanup function first
    test_terms = [
        "Manual Review #3: Market Size, Industry Report",
        "Manual Review #15: Market Analysis Report", 
        "Market Report Terminal",
        "Analysis Terminal",
        "Market Size Share Terminal2",
        "Market Research Embedded",
        "Report Prefix"
    ]
    
    print("\nTesting cleanup transformations:")
    for term in test_terms:
        cleaned = clean_term(term)
        print(f"  \"{term}\" -> \"{cleaned}\"")
    
    print(f"\nProceeding with bulk update...")
    success = bulk_cleanup_terms()
    
    if success:
        print("\n✅ All term cleanups completed successfully!")
    else:
        print("\n❌ Bulk cleanup failed - check MongoDB connection")