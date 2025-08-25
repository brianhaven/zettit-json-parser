#!/usr/bin/env python3

"""
Add Special Market Case Patterns to MongoDB
Handles special cases like "Aftermarket", "Farmer's Market", etc.
These patterns identify when "Market" should remain in the topic, not be extracted as report type.
"""

import os
import sys
import logging
import importlib.util
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Dynamic import for pattern library manager
try:
    spec = importlib.util.spec_from_file_location(
        "pattern_library_manager_v1", 
        "00b_pattern_library_manager_v1.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    
    PatternLibraryManager = module.PatternLibraryManager
    PatternType = module.PatternType
except Exception as e:
    logger.error(f"Could not import PatternLibraryManager: {e}")
    sys.exit(1)

def add_special_market_patterns():
    """Add special market case patterns to MongoDB pattern_libraries collection."""
    
    try:
        # Initialize pattern manager
        pattern_manager = PatternLibraryManager()
        
        # Define special market case patterns
        # These are cases where "Market" is part of the topic, not a report type
        special_market_patterns = [
            {
                "type": "special_market_case",
                "term": "Aftermarket",
                "pattern": r'\bAftermarket\b',
                "description": "Automotive/parts aftermarket - 'market' is part of the topic",
                "priority": 1,
                "active": True,
                "preserve_in_topic": True,
                "notes": "Common in automotive industry - refers to replacement parts market"
            },
            {
                "type": "special_market_case",
                "term": "Farmer's Market",
                "pattern": r"\bFarmer'?s?\s+Market\b",
                "description": "Farmer's market - 'market' is part of the topic name",
                "priority": 1,
                "active": True,
                "preserve_in_topic": True,
                "notes": "Physical marketplace, not a report type"
            },
            {
                "type": "special_market_case",
                "term": "Supermarket",
                "pattern": r'\bSupermarket\b',
                "description": "Supermarket - 'market' is part of the business type",
                "priority": 1,
                "active": True,
                "preserve_in_topic": True,
                "notes": "Retail business type, not a report type"
            },
            {
                "type": "special_market_case",
                "term": "Hypermarket",
                "pattern": r'\bHypermarket\b',
                "description": "Hypermarket - 'market' is part of the business type",
                "priority": 1,
                "active": True,
                "preserve_in_topic": True,
                "notes": "Large retail store format"
            },
            {
                "type": "special_market_case",
                "term": "Stock Market",
                "pattern": r'\bStock\s+Market\b',
                "description": "Stock market - specific financial market",
                "priority": 1,
                "active": True,
                "preserve_in_topic": True,
                "notes": "Financial market type, not a report type"
            },
            {
                "type": "special_market_case",
                "term": "Black Market",
                "pattern": r'\bBlack\s+Market\b',
                "description": "Black market - underground economy",
                "priority": 1,
                "active": True,
                "preserve_in_topic": True,
                "notes": "Economic concept, not a report type"
            },
            {
                "type": "special_market_case",
                "term": "Flea Market",
                "pattern": r'\bFlea\s+Market\b',
                "description": "Flea market - type of marketplace",
                "priority": 1,
                "active": True,
                "preserve_in_topic": True,
                "notes": "Physical marketplace type"
            },
            {
                "type": "special_market_case",
                "term": "Mass Market",
                "pattern": r'\bMass\s+Market\b',
                "description": "Mass market - market segment descriptor",
                "priority": 2,
                "active": True,
                "preserve_in_topic": True,
                "notes": "Market segment, could be part of topic"
            },
            {
                "type": "special_market_case",
                "term": "Niche Market",
                "pattern": r'\bNiche\s+Market\b',
                "description": "Niche market - market segment descriptor",
                "priority": 2,
                "active": True,
                "preserve_in_topic": True,
                "notes": "Market segment type"
            },
            {
                "type": "special_market_case",
                "term": "Secondary Market",
                "pattern": r'\bSecondary\s+Market\b',
                "description": "Secondary market - resale market",
                "priority": 2,
                "active": True,
                "preserve_in_topic": True,
                "notes": "Market type in finance or resale"
            },
            {
                "type": "special_market_case",
                "term": "Primary Market",
                "pattern": r'\bPrimary\s+Market\b',
                "description": "Primary market - initial sale market",
                "priority": 2,
                "active": True,
                "preserve_in_topic": True,
                "notes": "Market type in finance"
            },
            {
                "type": "special_market_case",
                "term": "Grey Market",
                "pattern": r'\bGr[ea]y\s+Market\b',
                "description": "Grey/Gray market - parallel import market",
                "priority": 2,
                "active": True,
                "preserve_in_topic": True,
                "notes": "Unofficial distribution channel"
            }
        ]
        
        # Add each pattern to MongoDB
        success_count = 0
        for pattern in special_market_patterns:
            try:
                # Check if pattern already exists
                existing = pattern_manager.search_patterns(
                    search_term=pattern['term'],
                    pattern_type='special_market_case'
                )
                
                if existing:
                    logger.info(f"Pattern '{pattern['term']}' already exists, skipping...")
                    continue
                
                # Add the pattern
                pattern_manager.add_pattern(
                    pattern_type='special_market_case',
                    term=pattern['term'],
                    pattern=pattern['pattern'],
                    description=pattern.get('description', ''),
                    priority=pattern.get('priority', 3),
                    active=pattern.get('active', True),
                    metadata={
                        'preserve_in_topic': pattern.get('preserve_in_topic', True),
                        'notes': pattern.get('notes', '')
                    }
                )
                success_count += 1
                logger.info(f"✅ Added special market case: {pattern['term']}")
                
            except Exception as e:
                logger.error(f"Failed to add pattern '{pattern['term']}': {e}")
        
        logger.info(f"\n{'='*50}")
        logger.info(f"Successfully added {success_count}/{len(special_market_patterns)} special market case patterns")
        
        # Show current special market patterns
        special_patterns = pattern_manager.get_patterns('special_market_case')
        logger.info(f"Total special market case patterns in database: {len(special_patterns)}")
        
        # Close connection
        pattern_manager.close_connection()
        
    except Exception as e:
        logger.error(f"Failed to add special market patterns: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

if __name__ == "__main__":
    success = add_special_market_patterns()
    if success:
        print("\n✅ Special market case patterns successfully added to MongoDB")
    else:
        print("\n❌ Failed to add special market case patterns")
        sys.exit(1)