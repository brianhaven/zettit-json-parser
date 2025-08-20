#!/usr/bin/env python3
"""
Pattern Discovery for Human Review v1
Specialized script for discovering new geographic patterns that require human validation.

Features:
1. Enhanced HTML processing with table extraction
2. Dual spaCy model analysis for confidence validation
3. Human-readable output with approval checkboxes
4. Safe pattern addition with term vs alias detection
5. Conflict resolution for existing patterns

Usage:
1. Run script to discover patterns
2. Review generated approval file
3. Uncheck patterns that shouldn't be added
4. Run pattern addition script with approved list
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
from collections import Counter, defaultdict
from dotenv import load_dotenv
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure
from bs4 import BeautifulSoup

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

def enhanced_html_cleaning(html_content: str) -> Dict[str, str]:
    """Enhanced HTML processing with table extraction and proper block separation."""
    if not html_content:
        return {"body_text": "", "table_text": "", "combined_text": ""}
    
    try:
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Extract table content for structured region data
        tables = soup.find_all(['table', 'tbody', 'thead'])
        table_texts = []
        
        for table in tables:
            rows = table.find_all(['tr', 'td', 'th'])
            for row in rows:
                cell_text = row.get_text(separator=' | ', strip=True)
                if cell_text and len(cell_text) > 3:
                    table_texts.append(cell_text)
        
        table_text = " ; ".join(table_texts)
        
        # Remove tables for body processing
        for table in soup.find_all(['table', 'tbody', 'thead']):
            table.decompose()
        
        # Process body with block awareness
        block_elements = ['div', 'p', 'li', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 
                         'section', 'article', 'blockquote', 'pre']
        
        for tag_name in block_elements:
            for tag in soup.find_all(tag_name):
                if tag.string:
                    tag.string.replace_with(f" ; {tag.string} ; ")
        
        body_text = soup.get_text(separator=' ; ', strip=True)
        body_text = html.unescape(body_text)
        body_text = re.sub(r'\s*;\s*', ' ; ', body_text)
        body_text = re.sub(r'\s+', ' ', body_text)
        body_text = body_text.strip()
        
        combined_text = f"{body_text} ; {table_text}".strip()
        
        return {
            "body_text": body_text,
            "table_text": table_text,
            "combined_text": combined_text
        }
        
    except Exception as e:
        logger.warning(f"HTML parsing error: {e}")
        clean_text = html.unescape(html_content)
        clean_text = re.sub(r'<[^>]+>', ' ; ', clean_text)
        clean_text = re.sub(r'\s+', ' ', clean_text)
        return {
            "body_text": clean_text,
            "table_text": "",
            "combined_text": clean_text
        }

def load_existing_patterns(patterns_collection) -> Dict[str, Dict]:
    """Load existing patterns with detailed information for conflict detection."""
    try:
        patterns = list(patterns_collection.find({
            "type": "geographic_entity",
            "active": True
        }))
        
        pattern_map = {}
        all_terms = set()
        
        for pattern in patterns:
            term = pattern['term'].lower()
            aliases = [alias.lower() for alias in pattern.get('aliases', [])]
            
            pattern_map[term] = {
                'id': pattern['_id'],
                'term': pattern['term'],
                'aliases': pattern.get('aliases', []),
                'priority': pattern.get('priority', 2)
            }
            
            all_terms.add(term)
            all_terms.update(aliases)
        
        logger.info(f"Loaded {len(patterns)} patterns with {len(all_terms)} total terms")
        return pattern_map, all_terms
        
    except Exception as e:
        logger.error(f"Error loading patterns: {e}")
        return {}, set()

def extract_geographic_entities_with_context(nlp, text: str, source_type: str) -> Dict:
    """Extract geographic entities with source context."""
    if not text or len(text) < 10:
        return {
            'entities': [],
            'entity_counts': {},
            'source_type': source_type
        }
    
    text = text[:150000]
    
    try:
        doc = nlp(text)
        entities = []
        entity_counts = Counter()
        
        for ent in doc.ents:
            if ent.label_ in ['GPE', 'LOC']:
                entity_text = ent.text.strip()
                # Enhanced filtering
                if (len(entity_text) >= 2 and 
                    not re.match(r'^[\d\.\s\-\_]+$', entity_text) and
                    not re.match(r'^[^\w\s]+$', entity_text) and
                    not entity_text.lower().startswith('scope') and
                    not re.search(r'\d{4}', entity_text) and
                    len(entity_text) < 100 and
                    not entity_text.lower() in ['region', 'country', 'market', 'analysis']):
                    
                    entities.append({
                        'text': entity_text,
                        'start': ent.start_char,
                        'end': ent.end_char,
                        'label': ent.label_
                    })
                    entity_counts[entity_text] += 1
        
        return {
            'entities': entities,
            'entity_counts': dict(entity_counts),
            'source_type': source_type
        }
        
    except Exception as e:
        logger.error(f"Entity extraction error: {e}")
        return {
            'entities': [],
            'entity_counts': {},
            'source_type': source_type
        }

def classify_potential_patterns(discovered_entities: Dict, existing_patterns: Dict, existing_terms: Set) -> Dict:
    """Classify discovered entities as new terms, potential aliases, or existing patterns."""
    classification = {
        'new_terms': [],
        'potential_aliases': [],
        'existing_patterns': [],
        'noise_candidates': []
    }
    
    for entity, count in discovered_entities.items():
        entity_lower = entity.lower()
        
        if entity_lower in existing_terms:
            classification['existing_patterns'].append({
                'entity': entity,
                'count': count,
                'reason': 'already_exists'
            })
        elif any(entity_lower in existing_pattern['term'].lower() or 
                any(entity_lower in alias.lower() for alias in existing_pattern['aliases'])
                for existing_pattern in existing_patterns.values()):
            # Potential alias for existing pattern
            classification['potential_aliases'].append({
                'entity': entity,
                'count': count,
                'confidence': 'high' if count >= 5 else 'medium'
            })
        elif count >= 3:
            # Likely new geographic term
            classification['new_terms'].append({
                'entity': entity,
                'count': count,
                'confidence': 'high' if count >= 10 else 'medium'
            })
        else:
            # Low frequency - might be noise
            classification['noise_candidates'].append({
                'entity': entity,
                'count': count,
                'confidence': 'low'
            })
    
    return classification

def discover_patterns_for_review(markets_collection, patterns_collection, limit=1000):
    """Main pattern discovery function with human review preparation."""
    timestamp = get_timestamp()
    
    # Load spaCy models
    logger.info("Loading spaCy models...")
    nlp_md = spacy.load("en_core_web_md", disable=["tagger", "parser", "attribute_ruler", "lemmatizer"])
    nlp_lg = spacy.load("en_core_web_lg", disable=["tagger", "parser", "attribute_ruler", "lemmatizer"])
    
    # Load existing patterns
    existing_patterns, existing_terms = load_existing_patterns(patterns_collection)
    
    # Load documents
    logger.info(f"Loading {limit} documents for pattern discovery...")
    pipeline = [
        {"$match": {
            "$or": [
                {"report_description_html": {"$exists": True, "$ne": ""}},
                {"report_description_full": {"$exists": True, "$ne": ""}}
            ]
        }},
        {"$project": {
            "report_description_html": 1,
            "report_description_full": 1,
            "report_title_short": 1
        }},
        {"$limit": limit}
    ]
    
    cursor = markets_collection.aggregate(pipeline)
    
    # Collect all entities
    all_md_entities = Counter()
    all_lg_entities = Counter()
    documents_processed = 0
    html_processed = 0
    
    for doc in cursor:
        documents_processed += 1
        
        # Process description
        description_html = doc.get('report_description_html', '')
        description_plain = doc.get('report_description_full', '')
        
        if description_html:
            html_data = enhanced_html_cleaning(description_html)
            text_to_process = html_data['combined_text']
            html_processed += 1
        elif description_plain:
            text_to_process = html.unescape(description_plain)
            text_to_process = re.sub(r'<[^>]+>', ' ; ', text_to_process)
            text_to_process = re.sub(r'\s+', ' ', text_to_process)
        else:
            continue
        
        # Extract with both models
        md_results = extract_geographic_entities_with_context(nlp_md, text_to_process, 'description')
        lg_results = extract_geographic_entities_with_context(nlp_lg, text_to_process, 'description')
        
        all_md_entities.update(md_results['entity_counts'])
        all_lg_entities.update(lg_results['entity_counts'])
        
        if documents_processed % 100 == 0:
            logger.info(f"Processed {documents_processed} documents...")
    
    # Combine and classify results
    combined_entities = all_md_entities + all_lg_entities
    
    # Classify patterns
    classification = classify_potential_patterns(dict(combined_entities), existing_patterns, existing_terms)
    
    # Create model agreement analysis
    md_set = set(all_md_entities.keys())
    lg_set = set(all_lg_entities.keys())
    
    both_models = md_set.intersection(lg_set)
    agreement_analysis = {
        'total_md_entities': len(md_set),
        'total_lg_entities': len(lg_set),
        'both_models': len(both_models),
        'overlap_percentage': (len(both_models) / len(md_set.union(lg_set)) * 100) if md_set.union(lg_set) else 0
    }
    
    results = {
        'timestamp_pst': timestamp['pst'],
        'timestamp_utc': timestamp['utc'],
        'documents_processed': documents_processed,
        'html_processed': html_processed,
        'existing_patterns_count': len(existing_patterns),
        'classification': classification,
        'agreement_analysis': agreement_analysis,
        'model_results': {
            'md_entities': dict(all_md_entities),
            'lg_entities': dict(all_lg_entities),
            'combined_entities': dict(combined_entities)
        }
    }
    
    return results

def generate_approval_file(results: Dict, filename: str):
    """Generate human-readable approval file with checkboxes."""
    with open(filename, 'w') as f:
        f.write("# Geographic Pattern Discovery - Human Approval Required\n\n")
        f.write(f"**Discovery Date:** {results['timestamp_pst']}\n")
        f.write(f"**Documents Analyzed:** {results['documents_processed']}\n")
        f.write(f"**HTML Documents:** {results['html_processed']}\n\n")
        
        f.write("## Instructions\n")
        f.write("1. Review each pattern below\n")
        f.write("2. Uncheck (remove ☑) patterns that are NOT geographic regions\n")
        f.write("3. Leave checked (☑) patterns that should be added to the database\n")
        f.write("4. Save this file and run the pattern addition script\n\n")
        
        classification = results['classification']
        
        # High confidence new terms
        f.write("## High Confidence New Terms\n")
        f.write("*These appear to be new geographic regions (≥10 occurrences)*\n\n")
        for item in sorted(classification['new_terms'], key=lambda x: x['count'], reverse=True):
            if item['confidence'] == 'high':
                f.write(f"☑ **{item['entity']}** (count: {item['count']}) - NEW_TERM\n")
        
        f.write("\n## Medium Confidence New Terms\n")
        f.write("*These might be new geographic regions (3-9 occurrences)*\n\n")
        for item in sorted(classification['new_terms'], key=lambda x: x['count'], reverse=True):
            if item['confidence'] == 'medium':
                f.write(f"☑ **{item['entity']}** (count: {item['count']}) - NEW_TERM\n")
        
        f.write("\n## Potential Aliases\n")
        f.write("*These might be abbreviations or alternative names for existing regions*\n\n")
        for item in sorted(classification['potential_aliases'], key=lambda x: x['count'], reverse=True):
            f.write(f"☑ **{item['entity']}** (count: {item['count']}) - POTENTIAL_ALIAS\n")
        
        f.write("\n## Low Confidence Candidates\n")
        f.write("*These have low occurrence counts - review carefully*\n\n")
        for item in sorted(classification['noise_candidates'], key=lambda x: x['count'], reverse=True):
            if item['count'] >= 2:  # Only show items with at least 2 occurrences
                f.write(f"☑ **{item['entity']}** (count: {item['count']}) - LOW_CONFIDENCE\n")
        
        f.write(f"\n## Summary Statistics\n")
        f.write(f"- New terms: {len(classification['new_terms'])}\n")
        f.write(f"- Potential aliases: {len(classification['potential_aliases'])}\n")
        f.write(f"- Low confidence: {len([x for x in classification['noise_candidates'] if x['count'] >= 2])}\n")
        f.write(f"- Already exists: {len(classification['existing_patterns'])}\n")
        
        agreement = results['agreement_analysis']
        f.write(f"- Model agreement: {agreement['overlap_percentage']:.1f}%\n")

def generate_pattern_summary(results: Dict, filename: str):
    """Generate technical summary for developers."""
    with open(filename, 'w') as f:
        f.write("Geographic Pattern Discovery Technical Summary\n")
        f.write("=" * 60 + "\n\n")
        
        f.write(f"**Analysis Date (PST):** {results['timestamp_pst']}\n")
        f.write(f"**Analysis Date (UTC):** {results['timestamp_utc']}\n")
        f.write(f"**Documents Processed:** {results['documents_processed']}\n")
        f.write(f"**HTML Documents:** {results['html_processed']}\n")
        f.write(f"**Existing Patterns:** {results['existing_patterns_count']}\n\n")
        
        classification = results['classification']
        agreement = results['agreement_analysis']
        
        f.write("## Discovery Results\n\n")
        f.write(f"| Category | Count |\n")
        f.write(f"|----------|-------|\n")
        f.write(f"| High Confidence New Terms | {len([x for x in classification['new_terms'] if x['confidence'] == 'high'])} |\n")
        f.write(f"| Medium Confidence New Terms | {len([x for x in classification['new_terms'] if x['confidence'] == 'medium'])} |\n")
        f.write(f"| Potential Aliases | {len(classification['potential_aliases'])} |\n")
        f.write(f"| Low Confidence | {len([x for x in classification['noise_candidates'] if x['count'] >= 2])} |\n")
        f.write(f"| Already Existing | {len(classification['existing_patterns'])} |\n\n")
        
        f.write("## Model Agreement Analysis\n\n")
        f.write(f"- MD model entities: {agreement['total_md_entities']}\n")
        f.write(f"- LG model entities: {agreement['total_lg_entities']}\n")
        f.write(f"- Found by both models: {agreement['both_models']}\n")
        f.write(f"- Agreement percentage: {agreement['overlap_percentage']:.1f}%\n\n")
        
        f.write("## Recommendations\n\n")
        if agreement['overlap_percentage'] > 50:
            f.write("✅ High model agreement - reliable discoveries\n")
        else:
            f.write("⚠️ Lower model agreement - careful review needed\n")
        
        high_conf_count = len([x for x in classification['new_terms'] if x['confidence'] == 'high'])
        if high_conf_count > 10:
            f.write(f"✅ {high_conf_count} high-confidence patterns ready for addition\n")
        
        f.write("\n## Next Steps\n")
        f.write("1. Review approval file for human validation\n")
        f.write("2. Run pattern addition script with approved patterns\n")
        f.write("3. Update existing patterns with new aliases if applicable\n")

def main():
    """Main execution function."""
    logger.info("Starting Pattern Discovery for Human Review")
    
    # Connect to MongoDB
    client, markets_collection, patterns_collection = connect_to_mongodb()
    if not client:
        logger.error("Failed to connect to MongoDB")
        return
    
    try:
        # Run pattern discovery
        results = discover_patterns_for_review(markets_collection, patterns_collection, limit=1000)
        
        # Save results
        timestamp = get_timestamp()
        results_file = f"outputs/{timestamp['filename']}_pattern_discovery_results.json"
        approval_file = f"outputs/{timestamp['filename']}_patterns_for_approval.md"
        summary_file = f"outputs/{timestamp['filename']}_pattern_discovery_summary.txt"
        
        with open(results_file, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        generate_approval_file(results, approval_file)
        generate_pattern_summary(results, summary_file)
        
        logger.info(f"\nResults saved to: {results_file}")
        logger.info(f"Approval file: {approval_file}")
        logger.info(f"Summary file: {summary_file}")
        
        # Print summary
        classification = results['classification']
        print("\n" + "="*60)
        print("PATTERN DISCOVERY FOR REVIEW COMPLETE")
        print("="*60)
        print(f"Documents processed: {results['documents_processed']}")
        print(f"High confidence new terms: {len([x for x in classification['new_terms'] if x['confidence'] == 'high'])}")
        print(f"Medium confidence new terms: {len([x for x in classification['new_terms'] if x['confidence'] == 'medium'])}")
        print(f"Potential aliases: {len(classification['potential_aliases'])}")
        print(f"Low confidence candidates: {len([x for x in classification['noise_candidates'] if x['count'] >= 2])}")
        print(f"\n👤 HUMAN REVIEW REQUIRED: Check {approval_file}")
    
    except Exception as e:
        logger.error(f"Pattern discovery failed: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        if client:
            client.close()
            logger.info("MongoDB connection closed")

if __name__ == "__main__":
    main()