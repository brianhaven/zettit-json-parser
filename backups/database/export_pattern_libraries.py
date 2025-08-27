#!/usr/bin/env python3

import json
import os
from datetime import datetime
import pytz
from pymongo import MongoClient
from dotenv import load_dotenv

def main():
    """Export pattern_libraries collection to JSON backup file."""
    
    # Load environment variables
    load_dotenv()
    
    # Connect to MongoDB
    mongodb_uri = os.getenv('MONGODB_URI')
    if not mongodb_uri:
        print("ERROR: MONGODB_URI not found in environment variables")
        return
    
    client = MongoClient(mongodb_uri)
    db = client['deathstar']
    collection = db['pattern_libraries']
    
    # Get timestamp for filename
    pdt = pytz.timezone('America/Los_Angeles')
    timestamp = datetime.now(pdt).strftime('%Y%m%d_%H%M%S')
    
    # Export all documents
    print("Exporting pattern_libraries collection...")
    documents = list(collection.find({}))
    
    # Create backup filename
    backup_filename = f"pattern_libraries_backup_{timestamp}.json"
    
    # Write to JSON file with proper formatting
    with open(backup_filename, 'w', encoding='utf-8') as f:
        json.dump(documents, f, indent=2, default=str, ensure_ascii=False)
    
    print(f"✅ Exported {len(documents)} documents to {backup_filename}")
    print(f"📍 File location: {os.path.abspath(backup_filename)}")
    
    # Create summary file
    summary_filename = f"export_summary_{timestamp}.txt"
    with open(summary_filename, 'w') as f:
        f.write(f"MongoDB Export Summary\n")
        f.write(f"====================\n\n")
        f.write(f"Export Date (PDT): {datetime.now(pdt).strftime('%Y-%m-%d %H:%M:%S PDT')}\n")
        f.write(f"Export Date (UTC): {datetime.now(pytz.UTC).strftime('%Y-%m-%d %H:%M:%S UTC')}\n")
        f.write(f"Database: deathstar\n")
        f.write(f"Collection: pattern_libraries\n")
        f.write(f"Total Documents: {len(documents)}\n")
        f.write(f"Backup File: {backup_filename}\n\n")
        
        # Document type breakdown
        type_counts = {}
        for doc in documents:
            doc_type = doc.get('type', 'unknown')
            type_counts[doc_type] = type_counts.get(doc_type, 0) + 1
        
        f.write("Document Type Breakdown:\n")
        for doc_type, count in sorted(type_counts.items()):
            f.write(f"  {doc_type}: {count} documents\n")
    
    print(f"📋 Summary written to {summary_filename}")

if __name__ == "__main__":
    main()