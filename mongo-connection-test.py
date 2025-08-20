#!/usr/bin/env python3

import os
import logging
from datetime import datetime
from dotenv import load_dotenv
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_mongodb_connection():
    """Test MongoDB Atlas connection and basic operations."""
    
    # Load environment variables
    load_dotenv()
    
    mongodb_uri = os.getenv('MONGODB_URI')
    if not mongodb_uri:
        logger.error("MONGODB_URI not found in environment variables")
        return False
    
    logger.info("Testing MongoDB connection...")
    
    try:
        # Create MongoDB client with shorter timeout for testing
        client = MongoClient(mongodb_uri, serverSelectionTimeoutMS=10000)
        
        # Test connection
        logger.info("Attempting to connect to MongoDB Atlas...")
        client.admin.command('ping')
        logger.info("✓ Successfully connected to MongoDB Atlas")
        
        # Access the database and collection
        db = client['deathstar']
        collection = db['markets_raw']
        
        # Test database access
        logger.info("Testing database access...")
        db_stats = db.command("dbstats")
        logger.info(f"✓ Database 'deathstar' accessible - Size: {db_stats.get('dataSize', 0)} bytes")
        
        # Test collection access
        logger.info("Testing collection access...")
        doc_count = collection.count_documents({})
        logger.info(f"✓ Collection 'markets_raw' accessible - Documents: {doc_count}")
        
        # Test write permissions with a test document
        logger.info("Testing write permissions...")
        test_doc = {
            "test_connection": True,
            "timestamp": datetime.utcnow().isoformat(),
            "test_id": "connection_test"
        }
        
        # Insert test document
        result = collection.insert_one(test_doc)
        logger.info(f"✓ Write test successful - Inserted document ID: {result.inserted_id}")
        
        # Clean up test document
        collection.delete_one({"_id": result.inserted_id})
        logger.info("✓ Cleanup successful - Test document removed")
        
        # Test index operations
        logger.info("Testing index information...")
        indexes = list(collection.list_indexes())
        logger.info(f"✓ Collection has {len(indexes)} indexes")
        
        # Close connection
        client.close()
        logger.info("✓ Connection closed successfully")
        
        print("\n" + "="*60)
        print("🎉 MongoDB CONNECTION TEST PASSED")
        print("="*60)
        print(f"Database: deathstar")
        print(f"Collection: markets_raw")
        print(f"Current documents: {doc_count}")
        print(f"Database size: {db_stats.get('dataSize', 0)} bytes")
        print(f"Indexes: {len(indexes)}")
        print("All operations (read/write/delete) working correctly!")
        print("="*60)
        
        return True
        
    except ConnectionFailure as e:
        logger.error(f"❌ Connection failed: {e}")
        return False
    except ServerSelectionTimeoutError as e:
        logger.error(f"❌ Server selection timeout: {e}")
        logger.error("Check your network connection and MongoDB URI")
        return False
    except Exception as e:
        logger.error(f"❌ Unexpected error: {e}")
        return False

def main():
    """Main function to run the connection test."""
    print("MongoDB Atlas Connection Test")
    print("="*40)
    
    success = test_mongodb_connection()
    
    if success:
        print("\n✅ Database is ready to receive data!")
        exit(0)
    else:
        print("\n❌ Database connection failed!")
        print("Please check:")
        print("- .env file contains valid MONGODB_URI")
        print("- Network connectivity")
        print("- MongoDB Atlas cluster status")
        print("- Database credentials and permissions")
        exit(1)

if __name__ == "__main__":
    main()