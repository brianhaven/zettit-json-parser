#!/usr/bin/env python3

import os
import logging
from datetime import datetime, timezone
from dotenv import load_dotenv
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
import pytz

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def get_timestamps():
    """Generate PDT and UTC timestamps for output files."""
    utc_now = datetime.now(timezone.utc)
    pdt_tz = pytz.timezone('America/Los_Angeles')
    pdt_now = utc_now.astimezone(pdt_tz)
    
    pdt_str = pdt_now.strftime('%Y-%m-%d %H:%M:%S %Z')
    utc_str = utc_now.strftime('%Y-%m-%d %H:%M:%S UTC')
    
    return pdt_str, utc_str

def connect_to_mongodb():
    """Establish connection to MongoDB Atlas."""
    load_dotenv()
    
    mongodb_uri = os.getenv('MONGODB_URI')
    if not mongodb_uri:
        logger.error("MONGODB_URI not found in environment variables")
        return None, None
    
    try:
        client = MongoClient(mongodb_uri, serverSelectionTimeoutMS=10000)
        client.admin.command('ping')
        
        db = client['deathstar']
        logger.info("Successfully connected to MongoDB Atlas")
        return client, db
        
    except (ConnectionFailure, ServerSelectionTimeoutError) as e:
        logger.error(f"Connection failed: {e}")
        return None, None

def initialize_pattern_libraries(db):
    """Initialize pattern libraries with base geographic entities and market terms."""
    
    logger.info("Initializing pattern libraries...")
    
    # Base geographic entities from our analysis
    geographic_entities = [
        # Compound regions (priority 1 - highest)
        {"type": "geographic_entity", "term": "North America", "aliases": ["NA"], "priority": 1, "active": True},
        {"type": "geographic_entity", "term": "South America", "aliases": [], "priority": 1, "active": True},
        {"type": "geographic_entity", "term": "Latin America", "aliases": ["LATAM"], "priority": 1, "active": True},
        {"type": "geographic_entity", "term": "Middle East", "aliases": ["ME"], "priority": 1, "active": True},
        {"type": "geographic_entity", "term": "Asia Pacific", "aliases": ["APAC", "Asia-Pacific"], "priority": 1, "active": True},
        {"type": "geographic_entity", "term": "Southeast Asia", "aliases": [], "priority": 1, "active": True},
        {"type": "geographic_entity", "term": "South Asia", "aliases": [], "priority": 1, "active": True},
        {"type": "geographic_entity", "term": "East Asia", "aliases": [], "priority": 1, "active": True},
        {"type": "geographic_entity", "term": "Central Asia", "aliases": [], "priority": 1, "active": True},
        {"type": "geographic_entity", "term": "Eastern Europe", "aliases": [], "priority": 1, "active": True},
        {"type": "geographic_entity", "term": "Western Europe", "aliases": [], "priority": 1, "active": True},
        {"type": "geographic_entity", "term": "Central Europe", "aliases": [], "priority": 1, "active": True},
        {"type": "geographic_entity", "term": "North Africa", "aliases": [], "priority": 1, "active": True},
        {"type": "geographic_entity", "term": "Sub-Saharan Africa", "aliases": [], "priority": 1, "active": True},
        {"type": "geographic_entity", "term": "West Africa", "aliases": [], "priority": 1, "active": True},
        {"type": "geographic_entity", "term": "East Africa", "aliases": [], "priority": 1, "active": True},
        
        # Regional acronyms (priority 2)
        {"type": "geographic_entity", "term": "EMEA", "aliases": [], "priority": 2, "active": True},
        {"type": "geographic_entity", "term": "MEA", "aliases": [], "priority": 2, "active": True},
        {"type": "geographic_entity", "term": "ASEAN", "aliases": [], "priority": 2, "active": True},
        {"type": "geographic_entity", "term": "GCC", "aliases": [], "priority": 2, "active": True},
        {"type": "geographic_entity", "term": "MENA", "aliases": [], "priority": 2, "active": True},
        
        # Continents (priority 3)
        {"type": "geographic_entity", "term": "Europe", "aliases": ["European"], "priority": 3, "active": True},
        {"type": "geographic_entity", "term": "Asia", "aliases": ["Asian"], "priority": 3, "active": True},
        {"type": "geographic_entity", "term": "Africa", "aliases": ["African"], "priority": 3, "active": True},
        {"type": "geographic_entity", "term": "Pacific", "aliases": [], "priority": 3, "active": True},
        {"type": "geographic_entity", "term": "America", "aliases": [], "priority": 3, "active": True},
        
        # Countries (priority 4)
        {"type": "geographic_entity", "term": "United States", "aliases": ["U.S.", "US", "USA", "U.S.A."], "priority": 4, "active": True},
        {"type": "geographic_entity", "term": "United Kingdom", "aliases": ["U.K.", "UK", "Britain", "Great Britain"], "priority": 4, "active": True},
        {"type": "geographic_entity", "term": "China", "aliases": [], "priority": 4, "active": True},
        {"type": "geographic_entity", "term": "India", "aliases": [], "priority": 4, "active": True},
        {"type": "geographic_entity", "term": "Japan", "aliases": [], "priority": 4, "active": True},
        {"type": "geographic_entity", "term": "Germany", "aliases": [], "priority": 4, "active": True},
        {"type": "geographic_entity", "term": "France", "aliases": [], "priority": 4, "active": True},
        {"type": "geographic_entity", "term": "Italy", "aliases": [], "priority": 4, "active": True},
        {"type": "geographic_entity", "term": "Canada", "aliases": [], "priority": 4, "active": True},
        {"type": "geographic_entity", "term": "Australia", "aliases": [], "priority": 4, "active": True},
        {"type": "geographic_entity", "term": "Brazil", "aliases": [], "priority": 4, "active": True},
        {"type": "geographic_entity", "term": "Mexico", "aliases": [], "priority": 4, "active": True},
        {"type": "geographic_entity", "term": "Saudi Arabia", "aliases": [], "priority": 4, "active": True},
        {"type": "geographic_entity", "term": "UAE", "aliases": [], "priority": 4, "active": True},
        {"type": "geographic_entity", "term": "Singapore", "aliases": [], "priority": 4, "active": True},
        {"type": "geographic_entity", "term": "South Korea", "aliases": ["Korea"], "priority": 4, "active": True},
        {"type": "geographic_entity", "term": "Indonesia", "aliases": [], "priority": 4, "active": True},
    ]
    
    # Market terms for special processing
    market_terms = [
        {"type": "market_term", "term": "Market for", "pattern": r"\\bmarket\\s+for\\b", "processing_type": "concatenation", "active": True},
        {"type": "market_term", "term": "Market in", "pattern": r"\\bmarket\\s+in\\b", "processing_type": "context_integration", "active": True}
    ]
    
    # Confusing market terms to exclude from detection
    confusing_terms = [
        {"type": "confusing_term", "term": "After Market", "pattern": r"\\bafter\\s+market\\b", "exclude_from": "market_detection", "active": True},
        {"type": "confusing_term", "term": "Marketplace", "pattern": r"\\bmarketplace\\b", "exclude_from": "market_detection", "active": True},
        {"type": "confusing_term", "term": "Market Place", "pattern": r"\\bmarket\\s+place\\b", "exclude_from": "market_detection", "active": True},
        {"type": "confusing_term", "term": "Farmers Market", "pattern": r"\\bfarmers\\s+market\\b", "exclude_from": "market_detection", "active": True}
    ]
    
    # Add timestamp to all entries
    current_time = datetime.now(timezone.utc)
    for item in geographic_entities + market_terms + confusing_terms:
        item.update({
            "success_count": 0,
            "failure_count": 0,
            "created_date": current_time,
            "last_updated": current_time
        })
    
    # Insert into MongoDB
    try:
        # Insert geographic entities
        result_geo = db.pattern_libraries.insert_many(geographic_entities)
        logger.info(f"Inserted {len(result_geo.inserted_ids)} geographic entities")
        
        # Insert market terms  
        result_market = db.pattern_libraries.insert_many(market_terms)
        logger.info(f"Inserted {len(result_market.inserted_ids)} market terms")
        
        # Insert confusing terms
        result_confusing = db.pattern_libraries.insert_many(confusing_terms)
        logger.info(f"Inserted {len(result_confusing.inserted_ids)} confusing terms")
        
        total_inserted = len(result_geo.inserted_ids) + len(result_market.inserted_ids) + len(result_confusing.inserted_ids)
        logger.info(f"Total pattern library entries created: {total_inserted}")
        
        return True
        
    except Exception as e:
        logger.error(f"Failed to insert pattern libraries: {e}")
        return False

def create_indexes(db):
    """Create indexes for optimal query performance."""
    
    logger.info("Creating indexes for pattern libraries...")
    
    try:
        # Index on type and active status for fast filtering
        db.pattern_libraries.create_index([("type", 1), ("active", 1)])
        
        # Index on priority for geographic entities (compound-first processing)
        db.pattern_libraries.create_index([("type", 1), ("priority", 1), ("active", 1)])
        
        # Text index on term for fast pattern matching
        db.pattern_libraries.create_index([("term", "text")])
        
        # Index for performance tracking
        db.pattern_libraries.create_index([("success_count", -1)])
        
        # Index for markets_processed collection (to be used later)
        db.markets_processed.create_index([("processing_date", -1)])
        db.markets_processed.create_index([("confidence_score", -1)])
        db.markets_processed.create_index([("market_term_type", 1)])
        
        logger.info("Indexes created successfully")
        return True
        
    except Exception as e:
        logger.error(f"Failed to create indexes: {e}")
        return False

def verify_setup(db):
    """Verify the MongoDB setup is working correctly."""
    
    logger.info("Verifying MongoDB setup...")
    
    try:
        # Check pattern_libraries collection
        total_patterns = db.pattern_libraries.count_documents({})
        active_patterns = db.pattern_libraries.count_documents({"active": True})
        
        geo_count = db.pattern_libraries.count_documents({"type": "geographic_entity"})
        market_count = db.pattern_libraries.count_documents({"type": "market_term"})
        confusing_count = db.pattern_libraries.count_documents({"type": "confusing_term"})
        
        logger.info(f"Pattern libraries verification:")
        logger.info(f"  Total patterns: {total_patterns}")
        logger.info(f"  Active patterns: {active_patterns}")
        logger.info(f"  Geographic entities: {geo_count}")
        logger.info(f"  Market terms: {market_count}")
        logger.info(f"  Confusing terms: {confusing_count}")
        
        # Check markets_raw collection
        markets_count = db.markets_raw.count_documents({})
        logger.info(f"  Markets raw data: {markets_count} titles")
        
        # Test query performance
        sample_geo = list(db.pattern_libraries.find(
            {"type": "geographic_entity", "priority": 1, "active": True}
        ).limit(5))
        
        logger.info(f"  Sample compound regions: {[item['term'] for item in sample_geo]}")
        
        return True
        
    except Exception as e:
        logger.error(f"Verification failed: {e}")
        return False

def main():
    """Main function to set up MongoDB Atlas environment."""
    
    pdt_time, utc_time = get_timestamps()
    
    print("MongoDB Atlas Environment Setup")
    print("=" * 50)
    print(f"Analysis Date (PDT): {pdt_time}")
    print(f"Analysis Date (UTC): {utc_time}")
    print("=" * 50)
    
    # Connect to MongoDB
    client, db = connect_to_mongodb()
    if not client:
        print("❌ Failed to connect to MongoDB Atlas")
        return
    
    try:
        # Check if pattern libraries are already initialized
        existing_count = db.pattern_libraries.count_documents({})
        if existing_count > 0:
            logger.warning(f"Pattern libraries already contain {existing_count} entries")
            response = input("Do you want to clear existing data and reinitialize? (y/N): ")
            if response.lower() == 'y':
                db.pattern_libraries.delete_many({})
                logger.info("Cleared existing pattern libraries")
            else:
                logger.info("Keeping existing data, skipping initialization")
                verify_setup(db)
                return
        
        # Initialize pattern libraries
        if not initialize_pattern_libraries(db):
            print("❌ Failed to initialize pattern libraries")
            return
        
        # Create indexes
        if not create_indexes(db):
            print("❌ Failed to create indexes")
            return
        
        # Verify setup
        if not verify_setup(db):
            print("❌ Setup verification failed")
            return
        
        print("✅ MongoDB Atlas environment setup completed successfully!")
        print("\nNext steps:")
        print("1. Pattern libraries initialized with base geographic entities")
        print("2. Market term patterns configured")
        print("3. Performance indexes created")
        print("4. Ready for pattern library manager implementation (Task 2)")
        
    except Exception as e:
        logger.error(f"Setup failed: {e}")
        print(f"❌ Setup failed: {e}")
    
    finally:
        if client:
            client.close()

if __name__ == "__main__":
    main()