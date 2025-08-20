#!/usr/bin/env python3
"""
Report Description Analysis for Geographic Entity Discovery v1
Analyzes report_description_full fields to discover geographic entities that may appear in titles

Strategy:
1. Load documents with both report_title_short and report_description_full
2. Use spaCy LG model on descriptions (longer text = better context)
3. Cross-reference discovered entities with titles
4. Identify high-confidence patterns for library enhancement
"""

import os
import sys
import spacy
import time
import json
import logging
import re
from datetime import datetime
from typing import List, Dict, Set, Tuple
from collections import Counter, defaultdict
from dotenv import load_dotenv
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure
import html

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def get_timestamp():
    """Generate timestamp for Pacific Time."""
    from pytz import timezone
    pst = timezone('US/Pacific')
    utc = timezone('UTC')
    
    now_pst = datetime.now(pst)
    now_utc = datetime.now(utc)
    
    return {
        'pst': now_pst.strftime("%Y-%m-%d %H:%M:%S %Z"),
        'utc': now_utc.strftime("%Y-%m-%d %H:%M:%S %Z"),
        'filename': now_pst.strftime("%Y%m%d_%H%M%S")
    }

def connect_to_mongodb():
    """Connect to MongoDB Atlas."""
    try:
        mongodb_uri = os.getenv('MONGODB_URI')
        if not mongodb_uri:
            logger.error("MONGODB_URI not found in environment variables")
            return None, None, None
        
        client = MongoClient(mongodb_uri, serverSelectionTimeoutMS=10000)
        client.admin.command('ping')
        
        db = client['deathstar']
        markets_collection = db['markets_raw']
        patterns_collection = db['pattern_libraries']
        
        logger.info("Successfully connected to MongoDB Atlas")
        return client, markets_collection, patterns_collection
        
    except ConnectionFailure as e:
        logger.error(f"MongoDB connection failed: {e}")
        return None, None, None

def clean_html(text: str) -> str:
    """Clean HTML from text content."""
    if not text:
        return ""
    
    # Unescape HTML entities
    text = html.unescape(text)
    
    # Remove HTML tags
    text = re.sub(r'<[^>]+>', ' ', text)
    
    # Remove extra whitespace
    text = ' '.join(text.split())
    
    return text

def get_existing_patterns(patterns_collection):
    """Retrieve existing geographic patterns from MongoDB."""
    try:
        patterns = list(patterns_collection.find({"type": "geographic_entity", "active": True}))
        
        # Create comprehensive pattern set
        all_patterns = set()
        pattern_map = {}  # Map lowercase to original
        for pattern in patterns:
            term = pattern['term']
            all_patterns.add(term.lower())
            pattern_map[term.lower()] = term
            
            for alias in pattern.get('aliases', []):
                all_patterns.add(alias.lower())
                pattern_map[alias.lower()] = alias
        
        logger.info(f"Loaded {len(patterns)} geographic patterns with {len(all_patterns)} total terms")
        return all_patterns, pattern_map
        
    except Exception as e:
        logger.error(f"Error loading geographic patterns: {e}")
        return set(), {}

def analyze_description_for_entities(nlp, description: str, title: str) -> Dict:
    """
    Analyze a description for geographic entities and check if they appear in the title.
    """
    # Clean the description
    clean_desc = clean_html(description)
    
    if not clean_desc or len(clean_desc) < 50:
        return {
            'entities_found': [],
            'entities_in_title': [],
            'unique_entities': []
        }
    
    # Process description with spaCy
    doc = nlp(clean_desc[:10000])  # Limit to 10k chars for performance
    
    # Extract geographic entities
    entities_found = []
    for ent in doc.ents:
        if ent.label_ in ['GPE', 'LOC']:
            entities_found.append({
                'text': ent.text,
                'label': ent.label_,
                'start': ent.start_char,
                'end': ent.end_char
            })
    
    # Check which entities appear in the title
    entities_in_title = []
    title_lower = title.lower()
    
    for entity in entities_found:
        entity_text = entity['text']
        if entity_text.lower() in title_lower:
            entities_in_title.append(entity_text)
    
    return {
        'entities_found': entities_found,
        'entities_in_title': entities_in_title,
        'unique_entities': list(set(e['text'] for e in entities_found))
    }

def batch_analyze_descriptions(markets_collection, patterns_collection, sample_size: int = 500):
    """
    Analyze report descriptions to discover geographic entities.
    Focus on entities that appear in both description and title.
    """
    timestamp = get_timestamp()
    
    logger.info(f"Starting description analysis with sample size: {sample_size}")
    
    # Load spaCy model (use LG for better accuracy on longer text)
    logger.info("Loading spaCy en_core_web_lg model...")
    nlp = spacy.load("en_core_web_lg", disable=["tagger", "parser", "attribute_ruler", "lemmatizer"])
    
    # Load existing patterns
    existing_patterns, pattern_map = get_existing_patterns(patterns_collection)
    
    # Query documents with both title and description
    logger.info("Querying documents with descriptions...")
    cursor = markets_collection.find(
        {
            "report_title_short": {"$exists": True, "$ne": ""},
            "report_description_full": {"$exists": True, "$ne": ""}
        },
        {
            "report_title_short": 1,
            "report_description_full": 1,
            "publisherID": 1
        }
    ).limit(sample_size)
    
    # Process documents
    results = {
        'timestamp_pst': timestamp['pst'],
        'timestamp_utc': timestamp['utc'],
        'total_documents': 0,
        'documents_with_entities': 0,
        'documents_with_title_entities': 0,
        'all_entities': Counter(),
        'title_entities': Counter(),
        'new_discoveries': Counter(),
        'publisher_breakdown': defaultdict(lambda: {
            'total': 0,
            'with_entities': 0,
            'with_title_entities': 0
        }),
        'high_confidence_patterns': [],
        'processing_time': 0
    }
    
    start_time = time.time()
    
    logger.info("Processing documents...")
    for doc in cursor:
        results['total_documents'] += 1
        
        title = doc.get('report_title_short', '')
        description = doc.get('report_description_full', '')
        publisher = doc.get('publisherID', 'unknown')
        
        # Analyze description
        analysis = analyze_description_for_entities(nlp, description, title)
        
        # Update publisher stats
        results['publisher_breakdown'][publisher]['total'] += 1
        
        if analysis['unique_entities']:
            results['documents_with_entities'] += 1
            results['publisher_breakdown'][publisher]['with_entities'] += 1
            
            # Count all entities found in descriptions
            for entity in analysis['unique_entities']:
                results['all_entities'][entity] += 1
                
                # Check if it's a new discovery
                if entity.lower() not in existing_patterns:
                    results['new_discoveries'][entity] += 1
        
        if analysis['entities_in_title']:
            results['documents_with_title_entities'] += 1
            results['publisher_breakdown'][publisher]['with_title_entities'] += 1
            
            # Count entities that appear in titles
            for entity in analysis['entities_in_title']:
                results['title_entities'][entity] += 1
        
        if results['total_documents'] % 50 == 0:
            logger.info(f"Processed {results['total_documents']} documents...")
    
    results['processing_time'] = time.time() - start_time
    
    # Identify high-confidence patterns (appear in multiple title-description pairs)
    for entity, count in results['title_entities'].items():
        if count >= 3 and entity.lower() not in existing_patterns:
            results['high_confidence_patterns'].append({
                'entity': entity,
                'count_in_titles': count,
                'total_count': results['all_entities'][entity],
                'confidence': count / results['all_entities'][entity] if results['all_entities'][entity] > 0 else 0
            })
    
    # Sort high-confidence patterns by count
    results['high_confidence_patterns'].sort(key=lambda x: x['count_in_titles'], reverse=True)
    
    # Convert Counters to dicts for JSON serialization
    results['all_entities'] = dict(results['all_entities'].most_common(100))
    results['title_entities'] = dict(results['title_entities'].most_common(50))
    results['new_discoveries'] = dict(results['new_discoveries'].most_common(50))
    
    logger.info(f"Analysis completed in {results['processing_time']:.2f} seconds")
    logger.info(f"Processed {results['total_documents']} documents")
    logger.info(f"Found entities in {results['documents_with_entities']} descriptions")
    logger.info(f"Found title-matching entities in {results['documents_with_title_entities']} documents")
    logger.info(f"Discovered {len(results['new_discoveries'])} potential new patterns")
    logger.info(f"Identified {len(results['high_confidence_patterns'])} high-confidence patterns")
    
    return results

def generate_pattern_enhancement_report(results: Dict, filename: str):
    """Generate a report with pattern enhancement recommendations."""
    with open(filename, 'w') as f:
        f.write("Geographic Entity Discovery from Description Analysis\n")
        f.write("=" * 60 + "\n\n")
        
        f.write(f"**Analysis Date (PST):** {results['timestamp_pst']}\n")
        f.write(f"**Analysis Date (UTC):** {results['timestamp_utc']}\n")
        f.write(f"**Documents Analyzed:** {results['total_documents']}\n")
        f.write(f"**Processing Time:** {results['processing_time']:.2f} seconds\n\n")
        
        f.write("## Summary Statistics\n\n")
        f.write(f"- Documents with geographic entities: {results['documents_with_entities']} "
               f"({results['documents_with_entities']/results['total_documents']*100:.1f}%)\n")
        f.write(f"- Documents with entities in titles: {results['documents_with_title_entities']} "
               f"({results['documents_with_title_entities']/results['total_documents']*100:.1f}%)\n")
        f.write(f"- Unique entities discovered: {len(results['all_entities'])}\n")
        f.write(f"- New patterns discovered: {len(results['new_discoveries'])}\n")
        f.write(f"- High-confidence patterns: {len(results['high_confidence_patterns'])}\n\n")
        
        f.write("## Publisher Breakdown\n\n")
        f.write("| Publisher | Total | With Entities | With Title Entities |\n")
        f.write("|-----------|-------|---------------|--------------------|\n")
        for publisher, stats in results['publisher_breakdown'].items():
            f.write(f"| {publisher} | {stats['total']} | {stats['with_entities']} | {stats['with_title_entities']} |\n")
        
        f.write("\n## High-Confidence Pattern Recommendations\n\n")
        f.write("These entities appear in both descriptions and titles with high frequency:\n\n")
        for pattern in results['high_confidence_patterns'][:20]:
            f.write(f"- **{pattern['entity']}**: {pattern['count_in_titles']} titles, "
                   f"{pattern['total_count']} total occurrences, "
                   f"{pattern['confidence']*100:.1f}% title appearance rate\n")
        
        f.write("\n## Top New Discoveries\n\n")
        f.write("Entities not in current pattern library:\n\n")
        for entity, count in list(results['new_discoveries'].items())[:20]:
            f.write(f"- {entity}: {count} occurrences\n")
        
        f.write("\n## Most Common Entities in Titles\n\n")
        for entity, count in list(results['title_entities'].items())[:20]:
            f.write(f"- {entity}: {count} titles\n")
        
        f.write("\n## Recommendations\n\n")
        f.write("1. **Add High-Confidence Patterns**: Entities appearing in 3+ title-description pairs\n")
        f.write("2. **Review New Discoveries**: Validate entities with 5+ occurrences\n")
        f.write("3. **Publisher-Specific Patterns**: Consider publisher-specific geographic focus\n")
        f.write("4. **Incremental Updates**: Run this analysis on new documents periodically\n")

def main():
    """Main execution function."""
    logger.info("Starting description analysis for geographic entity discovery")
    
    # Connect to MongoDB
    client, markets_collection, patterns_collection = connect_to_mongodb()
    if not client:
        logger.error("Failed to connect to MongoDB")
        return
    
    try:
        # Run analysis
        results = batch_analyze_descriptions(markets_collection, patterns_collection, sample_size=500)
        
        # Generate timestamp for filenames
        timestamp = get_timestamp()
        
        # Save results
        output_filename = f"outputs/{timestamp['filename']}_description_analysis_results.json"
        report_filename = f"outputs/{timestamp['filename']}_pattern_enhancement_report.txt"
        
        with open(output_filename, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        generate_pattern_enhancement_report(results, report_filename)
        
        logger.info(f"Results saved to: {output_filename}")
        logger.info(f"Report saved to: {report_filename}")
        
        # Print summary
        print("\n" + "="*60)
        print("ANALYSIS COMPLETE")
        print("="*60)
        print(f"Documents analyzed: {results['total_documents']}")
        print(f"High-confidence patterns found: {len(results['high_confidence_patterns'])}")
        print(f"New discoveries: {len(results['new_discoveries'])}")
        print(f"\nTop 5 High-Confidence Patterns:")
        for pattern in results['high_confidence_patterns'][:5]:
            print(f"  - {pattern['entity']}: {pattern['count_in_titles']} titles")
    
    except Exception as e:
        logger.error(f"Analysis failed with error: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        if client:
            client.close()
            logger.info("MongoDB connection closed")

if __name__ == "__main__":
    main()