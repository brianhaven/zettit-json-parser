#!/usr/bin/env python3

"""
Pattern Library Manager v1.0
MongoDB-based pattern library management system with performance tracking.
Created for Market Research Title Parser project.
"""

import os
import logging
import time
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass
from enum import Enum
from dotenv import load_dotenv
from pymongo import MongoClient, ASCENDING, DESCENDING
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError, DuplicateKeyError
import pytz

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class PatternType(Enum):
    """Enumeration of pattern types in the library."""
    GEOGRAPHIC_ENTITY = "geographic_entity"
    MARKET_TERM = "market_term"
    DATE_PATTERN = "date_pattern"
    REPORT_TYPE = "report_type"
    CONFUSING_TERM = "confusing_term"

@dataclass
class PatternMetrics:
    """Pattern performance metrics data structure."""
    success_count: int
    failure_count: int
    success_rate: float
    last_used: Optional[datetime]
    total_uses: int

@dataclass
class Pattern:
    """Pattern data structure for library management."""
    id: Optional[str]
    type: PatternType
    term: str
    aliases: List[str]
    priority: int
    active: bool
    pattern: Optional[str] = None  # For regex patterns
    processing_type: Optional[str] = None  # For market terms
    exclude_from: Optional[str] = None  # For confusing terms
    success_count: int = 0
    failure_count: int = 0
    created_date: Optional[datetime] = None
    last_updated: Optional[datetime] = None

class PatternLibraryManager:
    """
    MongoDB-based pattern library manager with CRUD operations and performance tracking.
    
    Provides comprehensive pattern management for the Market Research Title Parser,
    including geographic entities, market terms, date patterns, and report types.
    """
    
    def __init__(self, connection_string: Optional[str] = None, database_name: str = "deathstar"):
        """
        Initialize the Pattern Library Manager.
        
        Args:
            connection_string: MongoDB connection string (from env if not provided)
            database_name: Name of the MongoDB database
        """
        self.connection_string = connection_string or self._get_connection_string()
        self.database_name = database_name
        self.client = None
        self.db = None
        self.collection = None
        self._cache = {}
        self._cache_ttl = 300  # 5 minutes TTL
        self._cache_timestamps = {}
        
        self._connect()
    
    def _get_connection_string(self) -> str:
        """Get MongoDB connection string from environment variables."""
        load_dotenv()
        mongodb_uri = os.getenv('MONGODB_URI')
        if not mongodb_uri:
            raise ValueError("MONGODB_URI not found in environment variables")
        return mongodb_uri
    
    def _connect(self) -> None:
        """Establish connection to MongoDB."""
        try:
            self.client = MongoClient(self.connection_string, serverSelectionTimeoutMS=10000)
            self.client.admin.command('ping')
            self.db = self.client[self.database_name]
            self.collection = self.db.pattern_libraries
            logger.info(f"Connected to MongoDB database: {self.database_name}")
        except (ConnectionFailure, ServerSelectionTimeoutError) as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            raise
    
    def _get_timestamps(self) -> tuple:
        """Generate PDT and UTC timestamps."""
        utc_now = datetime.now(timezone.utc)
        pdt_tz = pytz.timezone('America/Los_Angeles')
        pdt_now = utc_now.astimezone(pdt_tz)
        
        pdt_str = pdt_now.strftime('%Y-%m-%d %H:%M:%S %Z')
        utc_str = utc_now.strftime('%Y-%m-%d %H:%M:%S UTC')
        
        return pdt_str, utc_str, utc_now
    
    def _is_cache_valid(self, cache_key: str) -> bool:
        """Check if cached data is still valid based on TTL."""
        if cache_key not in self._cache_timestamps:
            return False
        
        cache_time = self._cache_timestamps[cache_key]
        return time.time() - cache_time < self._cache_ttl
    
    def _cache_data(self, cache_key: str, data: Any) -> None:
        """Cache data with timestamp."""
        self._cache[cache_key] = data
        self._cache_timestamps[cache_key] = time.time()
    
    def _invalidate_cache(self, pattern_type: Optional[PatternType] = None) -> None:
        """Invalidate cache for specific pattern type or all cache."""
        if pattern_type:
            cache_key = f"patterns_{pattern_type.value}"
            self._cache.pop(cache_key, None)
            self._cache_timestamps.pop(cache_key, None)
        else:
            self._cache.clear()
            self._cache_timestamps.clear()
        logger.debug(f"Cache invalidated for: {pattern_type.value if pattern_type else 'all'}")
    
    def get_patterns(self, pattern_type: PatternType, active_only: bool = True, 
                    use_cache: bool = True) -> List[Dict[str, Any]]:
        """
        Retrieve patterns by type with optional caching.
        
        Args:
            pattern_type: Type of patterns to retrieve
            active_only: If True, only return active patterns
            use_cache: If True, use cached data when available
            
        Returns:
            List of pattern documents
        """
        cache_key = f"patterns_{pattern_type.value}_{active_only}"
        
        # Check cache first
        if use_cache and self._is_cache_valid(cache_key):
            logger.debug(f"Returning cached patterns for {pattern_type.value}")
            return self._cache[cache_key]
        
        try:
            query = {"type": pattern_type.value}
            if active_only:
                query["active"] = True
            
            patterns = list(self.collection.find(query).sort("priority", ASCENDING))
            
            # Cache the results
            if use_cache:
                self._cache_data(cache_key, patterns)
            
            logger.info(f"Retrieved {len(patterns)} {pattern_type.value} patterns")
            return patterns
            
        except Exception as e:
            logger.error(f"Failed to retrieve patterns: {e}")
            raise
    
    def get_patterns_by_priority(self, pattern_type: PatternType, 
                                priority: int, active_only: bool = True) -> List[Dict[str, Any]]:
        """
        Retrieve patterns by type and priority level.
        
        Args:
            pattern_type: Type of patterns to retrieve
            priority: Priority level to filter by
            active_only: If True, only return active patterns
            
        Returns:
            List of pattern documents
        """
        try:
            query = {
                "type": pattern_type.value,
                "priority": priority
            }
            if active_only:
                query["active"] = True
            
            patterns = list(self.collection.find(query).sort("term", ASCENDING))
            logger.info(f"Retrieved {len(patterns)} {pattern_type.value} patterns with priority {priority}")
            return patterns
            
        except Exception as e:
            logger.error(f"Failed to retrieve patterns by priority: {e}")
            raise
    
    def add_pattern(self, pattern_type: PatternType, term: str, aliases: List[str] = None,
                   priority: int = 5, active: bool = True, **kwargs) -> str:
        """
        Add a new pattern to the library.
        
        Args:
            pattern_type: Type of pattern to add
            term: Primary term/pattern text
            aliases: List of alternative terms
            priority: Priority level (1=highest, 5=default)
            active: Whether pattern is active
            **kwargs: Additional pattern-specific fields
            
        Returns:
            String ID of created pattern
        """
        try:
            pdt_time, utc_time, current_time = self._get_timestamps()
            
            pattern_doc = {
                "type": pattern_type.value,
                "term": term,
                "aliases": aliases or [],
                "priority": priority,
                "active": active,
                "success_count": 0,
                "failure_count": 0,
                "created_date": current_time,
                "last_updated": current_time
            }
            
            # Add pattern-specific fields
            pattern_doc.update(kwargs)
            
            result = self.collection.insert_one(pattern_doc)
            pattern_id = str(result.inserted_id)
            
            # Invalidate cache
            self._invalidate_cache(pattern_type)
            
            logger.info(f"Added new {pattern_type.value} pattern: {term} (ID: {pattern_id})")
            return pattern_id
            
        except DuplicateKeyError:
            logger.error(f"Pattern already exists: {term}")
            raise
        except Exception as e:
            logger.error(f"Failed to add pattern: {e}")
            raise
    
    def update_pattern(self, pattern_id: str, updates: Dict[str, Any]) -> bool:
        """
        Update an existing pattern.
        
        Args:
            pattern_id: ObjectId string of pattern to update
            updates: Dictionary of fields to update
            
        Returns:
            True if pattern was updated successfully
        """
        try:
            from bson import ObjectId
            
            pdt_time, utc_time, current_time = self._get_timestamps()
            updates["last_updated"] = current_time
            
            result = self.collection.update_one(
                {"_id": ObjectId(pattern_id)},
                {"$set": updates}
            )
            
            if result.modified_count > 0:
                # Invalidate all cache since we don't know the pattern type
                self._invalidate_cache()
                logger.info(f"Updated pattern {pattern_id}")
                return True
            else:
                logger.warning(f"No pattern found with ID {pattern_id}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to update pattern: {e}")
            raise
    
    def delete_pattern(self, pattern_id: str) -> bool:
        """
        Delete a pattern from the library.
        
        Args:
            pattern_id: ObjectId string of pattern to delete
            
        Returns:
            True if pattern was deleted successfully
        """
        try:
            from bson import ObjectId
            
            result = self.collection.delete_one({"_id": ObjectId(pattern_id)})
            
            if result.deleted_count > 0:
                # Invalidate all cache since we don't know the pattern type
                self._invalidate_cache()
                logger.info(f"Deleted pattern {pattern_id}")
                return True
            else:
                logger.warning(f"No pattern found with ID {pattern_id}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to delete pattern: {e}")
            raise
    
    def track_success(self, pattern_id: str) -> bool:
        """
        Increment success count for a pattern.
        
        Args:
            pattern_id: ObjectId string of pattern
            
        Returns:
            True if tracking was successful
        """
        try:
            from bson import ObjectId
            
            pdt_time, utc_time, current_time = self._get_timestamps()
            
            result = self.collection.update_one(
                {"_id": ObjectId(pattern_id)},
                {
                    "$inc": {"success_count": 1},
                    "$set": {"last_updated": current_time}
                }
            )
            
            if result.modified_count > 0:
                logger.debug(f"Tracked success for pattern {pattern_id}")
                return True
            else:
                logger.warning(f"No pattern found with ID {pattern_id}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to track success: {e}")
            return False
    
    def track_failure(self, pattern_id: str) -> bool:
        """
        Increment failure count for a pattern.
        
        Args:
            pattern_id: ObjectId string of pattern
            
        Returns:
            True if tracking was successful
        """
        try:
            from bson import ObjectId
            
            pdt_time, utc_time, current_time = self._get_timestamps()
            
            result = self.collection.update_one(
                {"_id": ObjectId(pattern_id)},
                {
                    "$inc": {"failure_count": 1},
                    "$set": {"last_updated": current_time}
                }
            )
            
            if result.modified_count > 0:
                logger.debug(f"Tracked failure for pattern {pattern_id}")
                return True
            else:
                logger.warning(f"No pattern found with ID {pattern_id}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to track failure: {e}")
            return False
    
    def get_performance_metrics(self, pattern_type: Optional[PatternType] = None) -> Dict[str, Any]:
        """
        Get performance statistics for patterns.
        
        Args:
            pattern_type: If provided, metrics for specific type only
            
        Returns:
            Dictionary containing performance metrics
        """
        try:
            match_stage = {}
            if pattern_type:
                match_stage["type"] = pattern_type.value
            
            pipeline = []
            if match_stage:
                pipeline.append({"$match": match_stage})
            
            pipeline.extend([
                {
                    "$group": {
                        "_id": "$type",
                        "total_patterns": {"$sum": 1},
                        "active_patterns": {
                            "$sum": {"$cond": [{"$eq": ["$active", True]}, 1, 0]}
                        },
                        "total_successes": {"$sum": "$success_count"},
                        "total_failures": {"$sum": "$failure_count"},
                        "avg_success_rate": {
                            "$avg": {
                                "$cond": [
                                    {"$eq": [{"$add": ["$success_count", "$failure_count"]}, 0]},
                                    0,
                                    {"$divide": ["$success_count", {"$add": ["$success_count", "$failure_count"]}]}
                                ]
                            }
                        }
                    }
                }
            ])
            
            results = list(self.collection.aggregate(pipeline))
            
            # Format results
            metrics = {}
            for result in results:
                pattern_type_name = result["_id"]
                metrics[pattern_type_name] = {
                    "total_patterns": result["total_patterns"],
                    "active_patterns": result["active_patterns"],
                    "total_successes": result["total_successes"],
                    "total_failures": result["total_failures"],
                    "average_success_rate": round(result["avg_success_rate"], 4) if result["avg_success_rate"] else 0
                }
            
            logger.info(f"Retrieved performance metrics for {len(results)} pattern types")
            return metrics
            
        except Exception as e:
            logger.error(f"Failed to get performance metrics: {e}")
            raise
    
    def bulk_update_patterns(self, updates: List[Dict[str, Any]]) -> int:
        """
        Perform bulk updates on multiple patterns.
        
        Args:
            updates: List of update operations, each containing 'filter' and 'update' keys
            
        Returns:
            Number of patterns updated
        """
        try:
            from pymongo import UpdateOne
            
            pdt_time, utc_time, current_time = self._get_timestamps()
            
            operations = []
            for update_op in updates:
                update_op["update"]["$set"]["last_updated"] = current_time
                operations.append(UpdateOne(update_op["filter"], update_op["update"]))
            
            result = self.collection.bulk_write(operations)
            
            # Invalidate all cache
            self._invalidate_cache()
            
            logger.info(f"Bulk updated {result.modified_count} patterns")
            return result.modified_count
            
        except Exception as e:
            logger.error(f"Failed to perform bulk update: {e}")
            raise
    
    def search_patterns(self, search_term: str, pattern_type: Optional[PatternType] = None,
                       active_only: bool = True) -> List[Dict[str, Any]]:
        """
        Search patterns by term or aliases.
        
        Args:
            search_term: Text to search for
            pattern_type: Optional pattern type filter
            active_only: If True, only search active patterns
            
        Returns:
            List of matching patterns
        """
        try:
            query = {
                "$or": [
                    {"term": {"$regex": search_term, "$options": "i"}},
                    {"aliases": {"$regex": search_term, "$options": "i"}}
                ]
            }
            
            if pattern_type:
                query["type"] = pattern_type.value
            if active_only:
                query["active"] = True
            
            patterns = list(self.collection.find(query).sort("priority", ASCENDING))
            logger.info(f"Found {len(patterns)} patterns matching '{search_term}'")
            return patterns
            
        except Exception as e:
            logger.error(f"Failed to search patterns: {e}")
            raise
    
    def get_top_performing_patterns(self, pattern_type: PatternType, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get top performing patterns by success rate.
        
        Args:
            pattern_type: Type of patterns to analyze
            limit: Maximum number of patterns to return
            
        Returns:
            List of top performing patterns
        """
        try:
            pipeline = [
                {"$match": {"type": pattern_type.value, "active": True}},
                {
                    "$addFields": {
                        "success_rate": {
                            "$cond": [
                                {"$eq": [{"$add": ["$success_count", "$failure_count"]}, 0]},
                                0,
                                {"$divide": ["$success_count", {"$add": ["$success_count", "$failure_count"]}]}
                            ]
                        },
                        "total_uses": {"$add": ["$success_count", "$failure_count"]}
                    }
                },
                {"$match": {"total_uses": {"$gt": 0}}},
                {"$sort": {"success_rate": -1, "total_uses": -1}},
                {"$limit": limit}
            ]
            
            patterns = list(self.collection.aggregate(pipeline))
            logger.info(f"Retrieved top {len(patterns)} performing {pattern_type.value} patterns")
            return patterns
            
        except Exception as e:
            logger.error(f"Failed to get top performing patterns: {e}")
            raise
    
    def validate_pattern_format(self, pattern_type: PatternType, pattern_data: Dict[str, Any]) -> List[str]:
        """
        Validate pattern data format and return any errors.
        
        Args:
            pattern_type: Type of pattern being validated
            pattern_data: Pattern data to validate
            
        Returns:
            List of validation error messages
        """
        errors = []
        
        # Common validation
        if not pattern_data.get("term"):
            errors.append("Pattern term is required")
        
        if "priority" in pattern_data and not isinstance(pattern_data["priority"], int):
            errors.append("Priority must be an integer")
        
        if "aliases" in pattern_data and not isinstance(pattern_data["aliases"], list):
            errors.append("Aliases must be a list")
        
        # Pattern-specific validation
        if pattern_type == PatternType.MARKET_TERM:
            if not pattern_data.get("pattern"):
                errors.append("Market terms require a regex pattern")
            if not pattern_data.get("processing_type"):
                errors.append("Market terms require a processing_type")
        
        if pattern_type == PatternType.CONFUSING_TERM:
            if not pattern_data.get("exclude_from"):
                errors.append("Confusing terms require exclude_from field")
        
        return errors
    
    def close_connection(self) -> None:
        """Close the MongoDB connection."""
        if self.client:
            self.client.close()
            logger.info("MongoDB connection closed")


def demo_usage():
    """Demonstrate Pattern Library Manager functionality."""
    
    print("Pattern Library Manager Demo")
    print("=" * 50)
    
    try:
        # Initialize manager
        manager = PatternLibraryManager()
        
        # Get performance metrics
        print("\n1. Current Performance Metrics:")
        metrics = manager.get_performance_metrics()
        for pattern_type, stats in metrics.items():
            print(f"  {pattern_type}: {stats['active_patterns']} active patterns, "
                  f"{stats['average_success_rate']:.2%} success rate")
        
        # Get geographic entities by priority
        print("\n2. Compound Geographic Entities (Priority 1):")
        compound_entities = manager.get_patterns_by_priority(PatternType.GEOGRAPHIC_ENTITY, 1)
        for entity in compound_entities[:5]:
            print(f"  - {entity['term']} (aliases: {entity['aliases']})")
        
        # Search for patterns
        print("\n3. Search for 'America' patterns:")
        america_patterns = manager.search_patterns("America", PatternType.GEOGRAPHIC_ENTITY)
        for pattern in america_patterns:
            print(f"  - {pattern['term']} (priority: {pattern['priority']})")
        
        # Get market terms
        print("\n4. Market Term Patterns:")
        market_terms = manager.get_patterns(PatternType.MARKET_TERM)
        for term in market_terms:
            print(f"  - {term['term']}: {term['pattern']} ({term['processing_type']})")
        
        # Get top performing patterns
        print("\n5. Top Performing Geographic Entities:")
        top_geo = manager.get_top_performing_patterns(PatternType.GEOGRAPHIC_ENTITY, 3)
        for pattern in top_geo:
            success_rate = pattern.get('success_rate', 0)
            total_uses = pattern.get('total_uses', 0)
            print(f"  - {pattern['term']}: {success_rate:.2%} success rate ({total_uses} uses)")
        
        print("\n✅ Pattern Library Manager demo completed successfully!")
        
    except Exception as e:
        print(f"❌ Demo failed: {e}")
    
    finally:
        if 'manager' in locals():
            manager.close_connection()


if __name__ == "__main__":
    demo_usage()