#!/usr/bin/env python3
"""
Add Discovered Geographic Patterns to MongoDB v1
Adds high-confidence geographic patterns discovered from description analysis
"""

import os
import logging
from datetime import datetime
from dotenv import load_dotenv
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, DuplicateKeyError

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def connect_to_mongodb():
    """Connect to MongoDB Atlas."""
    try:
        mongodb_uri = os.getenv('MONGODB_URI')
        if not mongodb_uri:
            logger.error("MONGODB_URI not found in environment variables")
            return None, None
        
        client = MongoClient(mongodb_uri, serverSelectionTimeoutMS=10000)
        client.admin.command('ping')
        
        db = client['deathstar']
        patterns_collection = db['pattern_libraries']
        
        logger.info("Successfully connected to MongoDB Atlas")
        return client, patterns_collection
        
    except ConnectionFailure as e:
        logger.error(f"MongoDB connection failed: {e}")
        return None, None

def add_geographic_patterns(patterns_collection):
    """Add discovered high-confidence geographic patterns."""
    
    # High-confidence patterns discovered from analysis
    new_patterns = [
        {
            "type": "geographic_entity",
            "term": "New Zealand",
            "aliases": ["NZ"],
            "priority": 2,
            "active": True,
            "success_count": 0,
            "failure_count": 0,
            "source": "description_analysis_v1",
            "confidence": 0.95,
            "created_date": datetime.utcnow(),
            "last_updated": datetime.utcnow()
        },
        {
            "type": "geographic_entity",
            "term": "Saudi Arabia",
            "aliases": ["KSA", "Kingdom of Saudi Arabia"],
            "priority": 2,
            "active": True,
            "success_count": 0,
            "failure_count": 0,
            "source": "description_analysis_v1",
            "confidence": 0.90,
            "created_date": datetime.utcnow(),
            "last_updated": datetime.utcnow()
        },
        {
            "type": "geographic_entity",
            "term": "Spain",
            "aliases": ["ES"],
            "priority": 2,
            "active": True,
            "success_count": 0,
            "failure_count": 0,
            "source": "description_analysis_v1",
            "confidence": 0.85,
            "created_date": datetime.utcnow(),
            "last_updated": datetime.utcnow()
        },
        {
            "type": "geographic_entity",
            "term": "Argentina",
            "aliases": ["AR"],
            "priority": 2,
            "active": True,
            "success_count": 0,
            "failure_count": 0,
            "source": "description_analysis_v1",
            "confidence": 0.85,
            "created_date": datetime.utcnow(),
            "last_updated": datetime.utcnow()
        },
        {
            "type": "geographic_entity",
            "term": "Russia",
            "aliases": ["Russian Federation", "RU"],
            "priority": 2,
            "active": True,
            "success_count": 0,
            "failure_count": 0,
            "source": "description_analysis_v1",
            "confidence": 0.85,
            "created_date": datetime.utcnow(),
            "last_updated": datetime.utcnow()
        },
        {
            "type": "geographic_entity",
            "term": "Thailand",
            "aliases": ["TH"],
            "priority": 2,
            "active": True,
            "success_count": 0,
            "failure_count": 0,
            "source": "description_analysis_v1",
            "confidence": 0.85,
            "created_date": datetime.utcnow(),
            "last_updated": datetime.utcnow()
        },
        {
            "type": "geographic_entity",
            "term": "South Africa",
            "aliases": ["ZA", "RSA"],
            "priority": 2,
            "active": True,
            "success_count": 0,
            "failure_count": 0,
            "source": "description_analysis_v1",
            "confidence": 0.85,
            "created_date": datetime.utcnow(),
            "last_updated": datetime.utcnow()
        },
        {
            "type": "geographic_entity",
            "term": "Vietnam",
            "aliases": ["VN"],
            "priority": 2,
            "active": True,
            "success_count": 0,
            "failure_count": 0,
            "source": "description_analysis_v1",
            "confidence": 0.80,
            "created_date": datetime.utcnow(),
            "last_updated": datetime.utcnow()
        },
        {
            "type": "geographic_entity",
            "term": "Netherlands",
            "aliases": ["NL", "Holland"],
            "priority": 2,
            "active": True,
            "success_count": 0,
            "failure_count": 0,
            "source": "description_analysis_v1",
            "confidence": 0.80,
            "created_date": datetime.utcnow(),
            "last_updated": datetime.utcnow()
        },
        {
            "type": "geographic_entity",
            "term": "Norway",
            "aliases": ["NO"],
            "priority": 2,
            "active": True,
            "success_count": 0,
            "failure_count": 0,
            "source": "description_analysis_v1",
            "confidence": 0.80,
            "created_date": datetime.utcnow(),
            "last_updated": datetime.utcnow()
        },
        {
            "type": "geographic_entity",
            "term": "Egypt",
            "aliases": ["EG"],
            "priority": 2,
            "active": True,
            "success_count": 0,
            "failure_count": 0,
            "source": "description_analysis_v1",
            "confidence": 0.80,
            "created_date": datetime.utcnow(),
            "last_updated": datetime.utcnow()
        },
        {
            "type": "geographic_entity",
            "term": "Sweden",
            "aliases": ["SE"],
            "priority": 2,
            "active": True,
            "success_count": 0,
            "failure_count": 0,
            "source": "description_analysis_v1",
            "confidence": 0.80,
            "created_date": datetime.utcnow(),
            "last_updated": datetime.utcnow()
        },
        {
            "type": "geographic_entity",
            "term": "Taiwan",
            "aliases": ["TW", "Chinese Taipei"],
            "priority": 2,
            "active": True,
            "success_count": 0,
            "failure_count": 0,
            "source": "description_analysis_v1",
            "confidence": 0.80,
            "created_date": datetime.utcnow(),
            "last_updated": datetime.utcnow()
        },
        {
            "type": "geographic_entity",
            "term": "Turkey",
            "aliases": ["TR", "Türkiye"],
            "priority": 2,
            "active": True,
            "success_count": 0,
            "failure_count": 0,
            "source": "description_analysis_v1",
            "confidence": 0.80,
            "created_date": datetime.utcnow(),
            "last_updated": datetime.utcnow()
        },
        {
            "type": "geographic_entity",
            "term": "Chile",
            "aliases": ["CL"],
            "priority": 2,
            "active": True,
            "success_count": 0,
            "failure_count": 0,
            "source": "description_analysis_v1",
            "confidence": 0.80,
            "created_date": datetime.utcnow(),
            "last_updated": datetime.utcnow()
        },
        {
            "type": "geographic_entity",
            "term": "Central and South America",
            "aliases": ["Central & South America", "LATAM", "Latin America"],
            "priority": 1,  # Higher priority for compound regions
            "active": True,
            "success_count": 0,
            "failure_count": 0,
            "source": "description_analysis_v1",
            "confidence": 0.80,
            "created_date": datetime.utcnow(),
            "last_updated": datetime.utcnow()
        },
        {
            "type": "geographic_entity",
            "term": "Asia-Pacific",
            "aliases": ["Asia Pacific", "APAC", "the Asia Pacific"],
            "priority": 1,  # Higher priority for compound regions
            "active": True,
            "success_count": 0,
            "failure_count": 0,
            "source": "description_analysis_v1",
            "confidence": 0.90,
            "created_date": datetime.utcnow(),
            "last_updated": datetime.utcnow()
        },
        {
            "type": "geographic_entity",
            "term": "Belgium",
            "aliases": ["BE"],
            "priority": 2,
            "active": True,
            "success_count": 0,
            "failure_count": 0,
            "source": "description_analysis_v1",
            "confidence": 0.75,
            "created_date": datetime.utcnow(),
            "last_updated": datetime.utcnow()
        },
        {
            "type": "geographic_entity",
            "term": "Poland",
            "aliases": ["PL"],
            "priority": 2,
            "active": True,
            "success_count": 0,
            "failure_count": 0,
            "source": "description_analysis_v1",
            "confidence": 0.75,
            "created_date": datetime.utcnow(),
            "last_updated": datetime.utcnow()
        },
        {
            "type": "geographic_entity",
            "term": "Indonesia",
            "aliases": ["ID"],
            "priority": 2,
            "active": True,
            "success_count": 0,
            "failure_count": 0,
            "source": "description_analysis_v1",
            "confidence": 0.75,
            "created_date": datetime.utcnow(),
            "last_updated": datetime.utcnow()
        },
        {
            "type": "geographic_entity",
            "term": "Malaysia",
            "aliases": ["MY"],
            "priority": 2,
            "active": True,
            "success_count": 0,
            "failure_count": 0,
            "source": "description_analysis_v1",
            "confidence": 0.75,
            "created_date": datetime.utcnow(),
            "last_updated": datetime.utcnow()
        },
        {
            "type": "geographic_entity",
            "term": "Philippines",
            "aliases": ["PH"],
            "priority": 2,
            "active": True,
            "success_count": 0,
            "failure_count": 0,
            "source": "description_analysis_v1",
            "confidence": 0.75,
            "created_date": datetime.utcnow(),
            "last_updated": datetime.utcnow()
        }
    ]
    
    # Add patterns to MongoDB
    added_count = 0
    skipped_count = 0
    error_count = 0
    
    for pattern in new_patterns:
        try:
            # Check if pattern already exists
            existing = patterns_collection.find_one({
                "type": "geographic_entity",
                "term": pattern["term"]
            })
            
            if existing:
                logger.info(f"Pattern already exists: {pattern['term']}")
                skipped_count += 1
            else:
                result = patterns_collection.insert_one(pattern)
                logger.info(f"Added pattern: {pattern['term']} with ID: {result.inserted_id}")
                added_count += 1
                
        except DuplicateKeyError:
            logger.warning(f"Duplicate key error for pattern: {pattern['term']}")
            skipped_count += 1
        except Exception as e:
            logger.error(f"Error adding pattern {pattern['term']}: {e}")
            error_count += 1
    
    # Summary
    logger.info(f"\nPattern Addition Summary:")
    logger.info(f"  Added: {added_count}")
    logger.info(f"  Skipped (already exists): {skipped_count}")
    logger.info(f"  Errors: {error_count}")
    logger.info(f"  Total processed: {len(new_patterns)}")
    
    return added_count, skipped_count, error_count

def main():
    """Main execution function."""
    logger.info("Starting pattern addition process")
    
    # Connect to MongoDB
    client, patterns_collection = connect_to_mongodb()
    if not client:
        logger.error("Failed to connect to MongoDB")
        return
    
    try:
        # Add patterns
        added, skipped, errors = add_geographic_patterns(patterns_collection)
        
        # Verify current pattern count
        total_patterns = patterns_collection.count_documents({
            "type": "geographic_entity",
            "active": True
        })
        
        logger.info(f"\nTotal active geographic patterns in database: {total_patterns}")
        
    except Exception as e:
        logger.error(f"Pattern addition failed: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        if client:
            client.close()
            logger.info("MongoDB connection closed")

if __name__ == "__main__":
    main()