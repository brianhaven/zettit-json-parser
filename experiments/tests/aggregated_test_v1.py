#!/usr/bin/env python3
"""
Aggregated Text Block Test v1
Tests spaCy models on aggregated text blocks of different sizes
"""

import os
import sys
import spacy
import time
import json
import logging
import re
import html
from datetime import datetime
from typing import List, Dict, Set, Tuple
from collections import Counter
from dotenv import load_dotenv
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure

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

def load_existing_patterns(patterns_collection) -> Set[str]:
    """Load existing geographic patterns."""
    try:
        patterns = list(patterns_collection.find({
            "type": "geographic_entity",
            "active": True
        }))
        
        all_patterns = set()
        for pattern in patterns:
            all_patterns.add(pattern['term'].lower())
            for alias in pattern.get('aliases', []):
                all_patterns.add(alias.lower())
        
        logger.info(f"Loaded {len(patterns)} patterns with {len(all_patterns)} terms")
        return all_patterns
        
    except Exception as e:
        logger.error(f"Error loading patterns: {e}")
        return set()

def test_aggregation_sizes(markets_collection, patterns_collection):
    """Test different aggregation sizes for entity extraction."""
    timestamp = get_timestamp()
    
    # Load documents
    logger.info("Loading 1000 documents for testing...")
    cursor = markets_collection.find(
        {"report_description_full": {"$exists": True, "$ne": ""}},
        {"report_description_full": 1}
    ).limit(1000)
    
    documents = []
    for doc in cursor:
        desc = clean_html(doc.get('report_description_full', ''))
        if desc and len(desc) > 100:
            documents.append(desc)
    
    logger.info(f"Loaded {len(documents)} valid documents")
    
    # Load spaCy models
    logger.info("Loading spaCy models...")
    nlp_md = spacy.load("en_core_web_md", disable=["tagger", "parser", "attribute_ruler", "lemmatizer"])
    nlp_lg = spacy.load("en_core_web_lg", disable=["tagger", "parser", "attribute_ruler", "lemmatizer"])
    
    # Load existing patterns
    existing_patterns = load_existing_patterns(patterns_collection)
    
    # Test different aggregation sizes
    aggregation_sizes = [1, 10, 50]
    results = {
        'timestamp_pst': timestamp['pst'],
        'timestamp_utc': timestamp['utc'],
        'total_documents': len(documents),
        'tests': []
    }
    
    for agg_size in aggregation_sizes:
        logger.info(f"\n{'='*60}")
        logger.info(f"Testing aggregation size: {agg_size}")
        logger.info(f"{'='*60}")
        
        test_result = {
            'aggregation_size': agg_size,
            'blocks_processed': 0,
            'md_results': {
                'total_entities': 0,
                'unique_entities': set(),
                'new_patterns': set(),
                'processing_time': 0
            },
            'lg_results': {
                'total_entities': 0,
                'unique_entities': set(),
                'new_patterns': set(),
                'processing_time': 0
            }
        }
        
        # Process documents in blocks
        for i in range(0, min(100, len(documents)), agg_size):  # Test on first 100 docs
            block = documents[i:i+agg_size]
            if agg_size == 1:
                text = block[0]
            else:
                # Aggregate with semicolons for better context separation
                text = "; ".join(block)
            
            test_result['blocks_processed'] += 1
            
            # Process with MD model
            start_time = time.time()
            doc_md = nlp_md(text[:100000])  # Limit to 100k chars
            md_time = time.time() - start_time
            test_result['md_results']['processing_time'] += md_time
            
            for ent in doc_md.ents:
                if ent.label_ in ['GPE', 'LOC']:
                    test_result['md_results']['total_entities'] += 1
                    entity_text = ent.text.strip()
                    test_result['md_results']['unique_entities'].add(entity_text)
                    if entity_text.lower() not in existing_patterns:
                        test_result['md_results']['new_patterns'].add(entity_text)
            
            # Process with LG model
            start_time = time.time()
            doc_lg = nlp_lg(text[:100000])
            lg_time = time.time() - start_time
            test_result['lg_results']['processing_time'] += lg_time
            
            for ent in doc_lg.ents:
                if ent.label_ in ['GPE', 'LOC']:
                    test_result['lg_results']['total_entities'] += 1
                    entity_text = ent.text.strip()
                    test_result['lg_results']['unique_entities'].add(entity_text)
                    if entity_text.lower() not in existing_patterns:
                        test_result['lg_results']['new_patterns'].add(entity_text)
        
        # Calculate metrics
        test_result['md_results']['unique_count'] = len(test_result['md_results']['unique_entities'])
        test_result['md_results']['new_count'] = len(test_result['md_results']['new_patterns'])
        test_result['md_results']['entities_per_second'] = (
            test_result['md_results']['total_entities'] / test_result['md_results']['processing_time']
            if test_result['md_results']['processing_time'] > 0 else 0
        )
        
        test_result['lg_results']['unique_count'] = len(test_result['lg_results']['unique_entities'])
        test_result['lg_results']['new_count'] = len(test_result['lg_results']['new_patterns'])
        test_result['lg_results']['entities_per_second'] = (
            test_result['lg_results']['total_entities'] / test_result['lg_results']['processing_time']
            if test_result['lg_results']['processing_time'] > 0 else 0
        )
        
        # Calculate overlap
        both = test_result['md_results']['unique_entities'].intersection(test_result['lg_results']['unique_entities'])
        all_unique = test_result['md_results']['unique_entities'].union(test_result['lg_results']['unique_entities'])
        test_result['model_overlap'] = (len(both) / len(all_unique) * 100) if all_unique else 0
        
        # Convert sets to lists for JSON
        test_result['md_results']['unique_entities'] = list(test_result['md_results']['unique_entities'])[:50]
        test_result['md_results']['new_patterns'] = list(test_result['md_results']['new_patterns'])[:50]
        test_result['lg_results']['unique_entities'] = list(test_result['lg_results']['unique_entities'])[:50]
        test_result['lg_results']['new_patterns'] = list(test_result['lg_results']['new_patterns'])[:50]
        
        results['tests'].append(test_result)
        
        # Print summary
        logger.info(f"Aggregation size {agg_size}:")
        logger.info(f"  MD: {test_result['md_results']['total_entities']} entities, "
                   f"{test_result['md_results']['unique_count']} unique, "
                   f"{test_result['md_results']['new_count']} new")
        logger.info(f"  LG: {test_result['lg_results']['total_entities']} entities, "
                   f"{test_result['lg_results']['unique_count']} unique, "
                   f"{test_result['lg_results']['new_count']} new")
        logger.info(f"  Model overlap: {test_result['model_overlap']:.1f}%")
    
    return results

def generate_aggregation_report(results: Dict, filename: str):
    """Generate comparison report for aggregation sizes."""
    with open(filename, 'w') as f:
        f.write("Aggregation Size Comparison Report\n")
        f.write("=" * 60 + "\n\n")
        
        f.write(f"**Analysis Date (PST):** {results['timestamp_pst']}\n")
        f.write(f"**Analysis Date (UTC):** {results['timestamp_utc']}\n")
        f.write(f"**Documents Available:** {results['total_documents']}\n\n")
        
        f.write("## Performance by Aggregation Size\n\n")
        f.write("| Size | Model | Total Ent | Unique | New | Ent/Sec | Overlap% |\n")
        f.write("|------|-------|-----------|--------|-----|---------|----------|\n")
        
        for test in results['tests']:
            size = test['aggregation_size']
            f.write(f"| {size} | MD | {test['md_results']['total_entities']} | "
                   f"{test['md_results']['unique_count']} | {test['md_results']['new_count']} | "
                   f"{test['md_results']['entities_per_second']:.1f} | "
                   f"{test['model_overlap']:.1f} |\n")
            f.write(f"| {size} | LG | {test['lg_results']['total_entities']} | "
                   f"{test['lg_results']['unique_count']} | {test['lg_results']['new_count']} | "
                   f"{test['lg_results']['entities_per_second']:.1f} | - |\n")
        
        f.write("\n## Key Findings\n\n")
        
        # Find best performing configuration
        best_md = max(results['tests'], key=lambda x: x['md_results']['new_count'])
        best_lg = max(results['tests'], key=lambda x: x['lg_results']['new_count'])
        best_overlap = max(results['tests'], key=lambda x: x['model_overlap'])
        
        f.write(f"- **Best MD discovery:** Size {best_md['aggregation_size']} with {best_md['md_results']['new_count']} new patterns\n")
        f.write(f"- **Best LG discovery:** Size {best_lg['aggregation_size']} with {best_lg['lg_results']['new_count']} new patterns\n")
        f.write(f"- **Best model agreement:** Size {best_overlap['aggregation_size']} with {best_overlap['model_overlap']:.1f}% overlap\n\n")
        
        f.write("## Recommendations\n\n")
        if best_md['aggregation_size'] >= 10:
            f.write("✅ **Aggregation improves discovery**: Larger text blocks provide better context.\n")
        else:
            f.write("⚠️ **Individual processing preferred**: Aggregation may lose entity boundaries.\n")
        
        f.write("\n### Optimal Strategy\n")
        if best_md['aggregation_size'] == best_lg['aggregation_size']:
            f.write(f"Use aggregation size of {best_md['aggregation_size']} for both models.\n")
        else:
            f.write(f"Consider different strategies: MD performs best at size {best_md['aggregation_size']}, "
                   f"LG at size {best_lg['aggregation_size']}.\n")

def main():
    """Main execution function."""
    logger.info("Starting aggregation size comparison test")
    
    # Connect to MongoDB
    client, markets_collection, patterns_collection = connect_to_mongodb()
    if not client:
        logger.error("Failed to connect to MongoDB")
        return
    
    try:
        # Run tests
        results = test_aggregation_sizes(markets_collection, patterns_collection)
        
        # Save results
        timestamp = get_timestamp()
        output_file = f"outputs/{timestamp['filename']}_aggregation_test_results.json"
        report_file = f"outputs/{timestamp['filename']}_aggregation_test_report.txt"
        
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        generate_aggregation_report(results, report_file)
        
        logger.info(f"\nResults saved to: {output_file}")
        logger.info(f"Report saved to: {report_file}")
        
        # Print final summary
        print("\n" + "="*60)
        print("AGGREGATION TEST COMPLETE")
        print("="*60)
        for test in results['tests']:
            print(f"Size {test['aggregation_size']:3}: MD={test['md_results']['unique_count']:3} unique, "
                  f"LG={test['lg_results']['unique_count']:3} unique, "
                  f"Overlap={test['model_overlap']:.1f}%")
    
    except Exception as e:
        logger.error(f"Test failed: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        if client:
            client.close()
            logger.info("MongoDB connection closed")

if __name__ == "__main__":
    main()