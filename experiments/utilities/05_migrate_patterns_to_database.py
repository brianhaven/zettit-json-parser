#!/usr/bin/env python3

"""
Script 05 Pattern Migration Utility
Migrate legitimate hardcoded patterns from Script 05 to MongoDB pattern_libraries collection.
This implements the DATABASE-FIRST architecture requirement.

NOTE: Technical indicator patterns are NOT migrated - they will be removed entirely.
"""

import os
import sys
import logging
from pymongo import MongoClient
from datetime import datetime, timezone
import pytz
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def get_timestamps():
    """Generate PDT and UTC timestamps."""
    utc_now = datetime.now(timezone.utc)
    pdt_tz = pytz.timezone('America/Los_Angeles')
    pdt_now = utc_now.astimezone(pdt_tz)

    pdt_str = pdt_now.strftime('%Y-%m-%d %H:%M:%S %Z')
    utc_str = utc_now.strftime('%Y-%m-%d %H:%M:%S UTC')

    return pdt_str, utc_str, utc_now

def migrate_script05_patterns():
    """Migrate legitimate hardcoded patterns from Script 05 to MongoDB."""

    print("Script 05 Pattern Migration to MongoDB")
    print("=" * 50)
    print("EXCLUDING: Technical indicator patterns (will be removed)")
    print("INCLUDING: Legitimate formatting and cleanup patterns")

    try:
        # Connect to MongoDB
        client = MongoClient(os.getenv('MONGODB_URI'))
        db = client['deathstar']
        collection = db.pattern_libraries

        pdt_time, utc_time, utc_timestamp = get_timestamps()

        # Only legitimate patterns - NO technical indicators
        patterns_to_migrate = [
            # Artifact Cleanup Patterns (lines 117-123)
            {
                "type": "topic_artifact_cleanup",
                "pattern": r"\s*,\s*$",
                "description": "Trailing commas at end of text",
                "category": "trailing_punctuation",
                "active": True,
                "priority": 1,
                "examples": ["text, ", "content,"],
                "success_count": 0,
                "failure_count": 0,
                "created_date": utc_timestamp,
                "last_updated": utc_timestamp,
                "notes": "Migrated from Script 05 artifact_patterns - line 118"
            },
            {
                "type": "topic_artifact_cleanup",
                "pattern": r"\s*&\s*$",
                "description": "Trailing ampersands at end of text",
                "category": "trailing_symbols",
                "active": True,
                "priority": 2,
                "examples": ["text & ", "content&"],
                "success_count": 0,
                "failure_count": 0,
                "created_date": utc_timestamp,
                "last_updated": utc_timestamp,
                "notes": "Migrated from Script 05 artifact_patterns - line 119"
            },
            {
                "type": "topic_artifact_cleanup",
                "pattern": r"^\s*and\s+",
                "description": "Leading 'and' at beginning of text",
                "category": "leading_connectors",
                "active": True,
                "priority": 3,
                "examples": ["and text", " and content"],
                "success_count": 0,
                "failure_count": 0,
                "created_date": utc_timestamp,
                "last_updated": utc_timestamp,
                "notes": "Migrated from Script 05 artifact_patterns - line 120"
            },
            {
                "type": "topic_artifact_cleanup",
                "pattern": r"^\s*the\s+",
                "description": "Leading 'the' at beginning of text",
                "category": "leading_articles",
                "active": True,
                "priority": 4,
                "examples": ["the text", " the content"],
                "success_count": 0,
                "failure_count": 0,
                "created_date": utc_timestamp,
                "last_updated": utc_timestamp,
                "notes": "Migrated from Script 05 artifact_patterns - line 121"
            },
            {
                "type": "topic_artifact_cleanup",
                "pattern": r"\s{2,}",
                "description": "Multiple consecutive spaces",
                "category": "whitespace_cleanup",
                "active": True,
                "priority": 5,
                "examples": ["text  space", "content   multiple"],
                "success_count": 0,
                "failure_count": 0,
                "created_date": utc_timestamp,
                "last_updated": utc_timestamp,
                "notes": "Migrated from Script 05 artifact_patterns - line 122"
            },

            # Date Artifact Cleanup Patterns (lines 436-448)
            {
                "type": "date_artifact_cleanup",
                "pattern": r"\[\s*\]",
                "description": "Empty square brackets left by date removal",
                "category": "empty_containers",
                "active": True,
                "priority": 1,
                "examples": ["text []", "content [ ]"],
                "success_count": 0,
                "failure_count": 0,
                "created_date": utc_timestamp,
                "last_updated": utc_timestamp,
                "notes": "Migrated from Script 05 _apply_systematic_removal method - line 437"
            },
            {
                "type": "date_artifact_cleanup",
                "pattern": r"\(\s*\)",
                "description": "Empty parentheses left by date removal",
                "category": "empty_containers",
                "active": True,
                "priority": 2,
                "examples": ["text ()", "content ( )"],
                "success_count": 0,
                "failure_count": 0,
                "created_date": utc_timestamp,
                "last_updated": utc_timestamp,
                "notes": "Migrated from Script 05 _apply_systematic_removal method - line 438"
            },
            {
                "type": "date_artifact_cleanup",
                "pattern": r",\s*Forecast\s+to\s*$",
                "description": "Orphaned forecast connectors after date removal",
                "category": "orphaned_connectors",
                "active": True,
                "priority": 3,
                "examples": [", Forecast to", ",Forecast to"],
                "success_count": 0,
                "failure_count": 0,
                "created_date": utc_timestamp,
                "last_updated": utc_timestamp,
                "notes": "Migrated from Script 05 _apply_systematic_removal method - line 441"
            },
            {
                "type": "date_artifact_cleanup",
                "pattern": r"\s+(to|through|till|until)\s*$",
                "description": "Orphaned temporal connectors after date removal",
                "category": "orphaned_connectors",
                "active": True,
                "priority": 4,
                "examples": [" to", " through", " till", " until"],
                "success_count": 0,
                "failure_count": 0,
                "created_date": utc_timestamp,
                "last_updated": utc_timestamp,
                "notes": "Migrated from Script 05 _apply_systematic_removal method - line 442"
            },

            # Systematic Removal Patterns (lines 408-430)
            {
                "type": "systematic_removal",
                "pattern": r",\s*$",
                "description": "Trailing comma removal after date extraction",
                "category": "date_separator_cleanup",
                "active": True,
                "priority": 1,
                "examples": ["text,", "content, "],
                "success_count": 0,
                "failure_count": 0,
                "created_date": utc_timestamp,
                "last_updated": utc_timestamp,
                "notes": "Migrated from Script 05 _apply_systematic_removal method - line 409"
            },
            {
                "type": "systematic_removal",
                "pattern": r"\s*&\s*share\b",
                "description": "Common 'share' artifact after report type removal",
                "category": "report_type_artifacts",
                "active": True,
                "priority": 2,
                "examples": [" & share", "&share"],
                "success_count": 0,
                "failure_count": 0,
                "created_date": utc_timestamp,
                "last_updated": utc_timestamp,
                "notes": "Migrated from Script 05 _apply_systematic_removal method - line 417"
            },
            {
                "type": "systematic_removal",
                "pattern": r"\s*&\s*",
                "description": "Ampersand cleanup during systematic removal",
                "category": "symbol_cleanup",
                "replacement": " ",
                "active": True,
                "priority": 3,
                "examples": ["text & content", "item&data"],
                "success_count": 0,
                "failure_count": 0,
                "created_date": utc_timestamp,
                "last_updated": utc_timestamp,
                "notes": "Migrated from Script 05 _apply_systematic_removal method - lines 425, 429"
            },

            # Topic Name Creation Patterns (lines 578-582)
            {
                "type": "topic_name_creation",
                "pattern": r"\s*&\s*",
                "description": "Ampersand to 'and' conversion for topic names",
                "replacement": " and ",
                "category": "symbol_conversion",
                "active": True,
                "priority": 1,
                "examples": ["AI & ML", "Risk & Security"],
                "success_count": 0,
                "failure_count": 0,
                "created_date": utc_timestamp,
                "last_updated": utc_timestamp,
                "notes": "Migrated from Script 05 _create_topic_name method - line 579"
            },
            {
                "type": "topic_name_creation",
                "pattern": r"\s+",
                "description": "Multiple spaces to single space cleanup",
                "replacement": " ",
                "category": "space_normalization",
                "active": True,
                "priority": 2,
                "examples": ["text  content", "multiple   spaces"],
                "success_count": 0,
                "failure_count": 0,
                "created_date": utc_timestamp,
                "last_updated": utc_timestamp,
                "notes": "Migrated from Script 05 _create_topic_name method - line 582"
            },

            # Topic Normalization Patterns (lines 604-625)
            {
                "type": "topic_normalization",
                "pattern": r"\([^)]*\)",
                "description": "Remove parentheses and their contents for normalized topics",
                "replacement": "",
                "category": "parentheses_removal",
                "active": True,
                "priority": 1,
                "examples": ["Text (info)", "AI (Artificial Intelligence)"],
                "success_count": 0,
                "failure_count": 0,
                "created_date": utc_timestamp,
                "last_updated": utc_timestamp,
                "notes": "Migrated from Script 05 _create_normalized_topic method - line 605"
            },
            {
                "type": "topic_normalization",
                "pattern": r"'s?\b",
                "description": "Remove apostrophes and possessive endings",
                "replacement": "",
                "category": "apostrophe_removal",
                "active": True,
                "priority": 2,
                "examples": ["Johnson's", "companies'"],
                "success_count": 0,
                "failure_count": 0,
                "created_date": utc_timestamp,
                "last_updated": utc_timestamp,
                "notes": "Migrated from Script 05 _create_normalized_topic method - line 608"
            },
            {
                "type": "topic_normalization",
                "pattern": r"[,;.!?]",
                "description": "Remove common punctuation marks",
                "replacement": "",
                "category": "punctuation_removal",
                "active": True,
                "priority": 3,
                "examples": ["text,", "content;", "item."],
                "success_count": 0,
                "failure_count": 0,
                "created_date": utc_timestamp,
                "last_updated": utc_timestamp,
                "notes": "Migrated from Script 05 _create_normalized_topic method - line 611"
            },
            {
                "type": "topic_normalization",
                "pattern": r"[/\\|]",
                "description": "Convert separators to dashes",
                "replacement": "-",
                "category": "separator_conversion",
                "active": True,
                "priority": 4,
                "examples": ["text/content", "item\\data", "option|choice"],
                "success_count": 0,
                "failure_count": 0,
                "created_date": utc_timestamp,
                "last_updated": utc_timestamp,
                "notes": "Migrated from Script 05 _create_normalized_topic method - line 614"
            },
            {
                "type": "topic_normalization",
                "pattern": r"\s+",
                "description": "Convert spaces to dashes",
                "replacement": "-",
                "category": "space_conversion",
                "active": True,
                "priority": 5,
                "examples": ["text content", "multiple word phrase"],
                "success_count": 0,
                "failure_count": 0,
                "created_date": utc_timestamp,
                "last_updated": utc_timestamp,
                "notes": "Migrated from Script 05 _create_normalized_topic method - line 617"
            },
            {
                "type": "topic_normalization",
                "pattern": r"-+",
                "description": "Collapse multiple dashes to single dash",
                "replacement": "-",
                "category": "dash_cleanup",
                "active": True,
                "priority": 6,
                "examples": ["text--content", "item---data"],
                "success_count": 0,
                "failure_count": 0,
                "created_date": utc_timestamp,
                "last_updated": utc_timestamp,
                "notes": "Migrated from Script 05 _create_normalized_topic method - line 620"
            },

            # Bracket-to-Parentheses Conversion (lines 553-554)
            {
                "type": "format_conversion",
                "pattern": r"\[([^\]]*)\]",
                "description": "Convert square brackets to parentheses",
                "replacement": r"(\1)",
                "category": "bracket_conversion",
                "active": True,
                "priority": 1,
                "examples": ["text [info]", "AI [ML]"],
                "success_count": 0,
                "failure_count": 0,
                "created_date": utc_timestamp,
                "last_updated": utc_timestamp,
                "notes": "Migrated from Script 05 _preserve_original_formatting method - lines 553-554"
            }
        ]

        # Check existing patterns to avoid duplicates
        print("\n1. Checking for existing patterns...")
        existing_count = 0
        new_count = 0

        for pattern_data in patterns_to_migrate:
            existing = collection.find_one({
                "type": pattern_data["type"],
                "pattern": pattern_data["pattern"]
            })

            if existing:
                existing_count += 1
                logger.debug(f"Pattern already exists: {pattern_data['pattern']}")
            else:
                # Insert new pattern
                result = collection.insert_one(pattern_data)
                new_count += 1
                logger.info(f"Inserted pattern: {pattern_data['pattern']} (ID: {result.inserted_id})")

        print(f"✓ Pattern migration completed:")
        print(f"  - Existing patterns: {existing_count}")
        print(f"  - New patterns added: {new_count}")
        print(f"  - Total patterns processed: {len(patterns_to_migrate)}")

        # Verify insertion
        print("\n2. Verification - Pattern counts by type:")
        pattern_counts = {}
        for pattern_data in patterns_to_migrate:
            pattern_type = pattern_data["type"]
            if pattern_type not in pattern_counts:
                count = collection.count_documents({"type": pattern_type})
                pattern_counts[pattern_type] = count
                print(f"  - {pattern_type}: {count:,} patterns")

        print("\n✅ Script 05 legitimate pattern migration completed successfully!")
        print("⚠️  Next step: Remove hardcoded patterns from Script 05 and implement database lookup")

        return True

    except Exception as e:
        logger.error(f"Pattern migration failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = migrate_script05_patterns()
    sys.exit(0 if success else 1)