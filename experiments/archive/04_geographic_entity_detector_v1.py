#!/usr/bin/env python3
"""
Geographic Entity Detection System v1
Systematic pattern-matching solution for extracting geographic regions from market research titles and descriptions.

Features:
1. Enhanced HTML processing with proper block separation
2. Dual spaCy model analysis (en_core_web_md and en_core_web_lg)
3. Table extraction for structured region data
4. Cross-model validation and confidence scoring
5. MongoDB pattern library integration

Processing Order: Run after report type extraction (03) to clean geographic regions from remaining text.
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
    """
    Enhanced HTML processing with proper block separation and table extraction.
    Fixes concatenation issues from missing line breaks in HTML content.
    """
    if not html_content:
        return {"body_text": "", "table_text": "", "combined_text": ""}
    
    try:
        # Parse HTML with BeautifulSoup
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Extract table content specifically for structured region data
        tables = soup.find_all(['table', 'tbody', 'thead'])
        table_texts = []
        
        for table in tables:
            # Extract all text from table cells, preserving row/cell boundaries
            rows = table.find_all(['tr', 'td', 'th'])
            for row in rows:
                cell_text = row.get_text(separator=' | ', strip=True)
                if cell_text and len(cell_text) > 3:  # Filter out empty/tiny cells
                    table_texts.append(cell_text)
        
        table_text = " ; ".join(table_texts)
        
        # Remove tables from soup for body processing
        for table in soup.find_all(['table', 'tbody', 'thead']):
            table.decompose()
        
        # Process body content with block-level awareness to prevent concatenation
        block_elements = ['div', 'p', 'li', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 
                         'section', 'article', 'blockquote', 'pre']
        
        # Add separators before block elements to prevent region concatenation
        for tag_name in block_elements:
            for tag in soup.find_all(tag_name):
                if tag.string:
                    tag.string.replace_with(f" ; {tag.string} ; ")
        
        # Extract text with preserved separations
        body_text = soup.get_text(separator=' ; ', strip=True)
        
        # Clean up the text
        body_text = html.unescape(body_text)
        body_text = re.sub(r'\s*;\s*', ' ; ', body_text)  # Normalize separators
        body_text = re.sub(r'\s+', ' ', body_text)        # Normalize whitespace
        body_text = body_text.strip()
        
        # Combine both sources
        combined_text = f"{body_text} ; {table_text}".strip()
        
        return {
            "body_text": body_text,
            "table_text": table_text,
            "combined_text": combined_text
        }
        
    except Exception as e:
        logger.warning(f"HTML parsing error: {e}")
        # Fallback to enhanced simple cleaning
        clean_text = html.unescape(html_content)
        clean_text = re.sub(r'<[^>]+>', ' ; ', clean_text)  # Replace tags with separators
        clean_text = re.sub(r'\s+', ' ', clean_text)
        return {
            "body_text": clean_text,
            "table_text": "",
            "combined_text": clean_text
        }

def load_existing_patterns(patterns_collection) -> Set[str]:
    """Load existing geographic patterns from MongoDB."""
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

def extract_geographic_entities(nlp, text: str, existing_patterns: Set[str]) -> Dict:
    """Extract geographic entities from text using spaCy NER."""
    if not text or len(text) < 10:
        return {
            'total_entities': 0,
            'unique_entities': set(),
            'new_patterns': set(),
            'entity_counts': {},
            'processing_time': 0
        }
    
    # Limit text length to prevent memory issues
    text = text[:150000]
    
    start_time = time.time()
    
    try:
        doc = nlp(text)
        entities = []
        entity_counts = Counter()
        
        for ent in doc.ents:
            if ent.label_ in ['GPE', 'LOC']:
                entity_text = ent.text.strip()
                # Enhanced filtering to remove obvious noise and artifacts
                if (len(entity_text) >= 2 and 
                    not re.match(r'^[\d\.\s\-\_]+$', entity_text) and
                    not re.match(r'^[^\w\s]+$', entity_text) and
                    not entity_text.lower().startswith('scope') and
                    not re.search(r'\d{4}', entity_text) and  # Filter years
                    len(entity_text) < 100):  # Filter very long strings
                    entities.append(entity_text)
                    entity_counts[entity_text] += 1
        
        unique_entities = set(entities)
        new_patterns = {ent for ent in unique_entities 
                       if ent.lower() not in existing_patterns}
        
        processing_time = time.time() - start_time
        
        return {
            'total_entities': len(entities),
            'unique_entities': unique_entities,
            'new_patterns': new_patterns,
            'entity_counts': dict(entity_counts),
            'processing_time': processing_time
        }
        
    except Exception as e:
        logger.error(f"Entity extraction error: {e}")
        return {
            'total_entities': 0,
            'unique_entities': set(),
            'new_patterns': set(),
            'entity_counts': {},
            'processing_time': time.time() - start_time
        }

def dual_model_geographic_detection(markets_collection, patterns_collection, limit=500):
    """
    Main geographic entity detection using dual spaCy models with enhanced HTML processing.
    """
    timestamp = get_timestamp()
    
    # Load spaCy models with optimized pipeline
    logger.info("Loading spaCy models...")
    nlp_md = spacy.load("en_core_web_md", disable=["tagger", "parser", "attribute_ruler", "lemmatizer"])
    nlp_lg = spacy.load("en_core_web_lg", disable=["tagger", "parser", "attribute_ruler", "lemmatizer"])
    
    # Load existing patterns
    existing_patterns = load_existing_patterns(patterns_collection)
    
    # Prefer HTML descriptions if available, fallback to plain text
    logger.info(f"Loading {limit} documents with description data...")
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
    
    results = {
        'timestamp_pst': timestamp['pst'],
        'timestamp_utc': timestamp['utc'],
        'processing_config': {
            'use_html': True,
            'dual_model': True,
            'document_limit': limit
        },
        'md_results': {
            'total_entities': 0,
            'unique_entities': set(),
            'new_patterns': set(),
            'entity_counts': Counter(),
            'processing_time': 0
        },
        'lg_results': {
            'total_entities': 0,
            'unique_entities': set(),
            'new_patterns': set(),
            'entity_counts': Counter(),
            'processing_time': 0
        },
        'comparison_metrics': {},
        'documents_processed': 0,
        'html_processed': 0,
        'plain_processed': 0
    }
    
    for doc in cursor:
        results['documents_processed'] += 1
        
        # Enhanced text processing - prefer HTML, fallback to plain
        description_html = doc.get('report_description_html', '')
        description_plain = doc.get('report_description_full', '')
        
        if description_html:
            # Process HTML with enhanced cleaning
            html_data = enhanced_html_cleaning(description_html)
            text_to_process = html_data['combined_text']
            results['html_processed'] += 1
        elif description_plain:
            # Process plain text with basic cleaning
            text_to_process = html.unescape(description_plain)
            text_to_process = re.sub(r'<[^>]+>', ' ; ', text_to_process)
            text_to_process = re.sub(r'\s+', ' ', text_to_process)
            results['plain_processed'] += 1
        else:
            continue
        
        # Process with both models
        md_doc_results = extract_geographic_entities(nlp_md, text_to_process, existing_patterns)
        lg_doc_results = extract_geographic_entities(nlp_lg, text_to_process, existing_patterns)
        
        # Accumulate results
        results['md_results']['total_entities'] += md_doc_results['total_entities']
        results['md_results']['unique_entities'].update(md_doc_results['unique_entities'])
        results['md_results']['new_patterns'].update(md_doc_results['new_patterns'])
        results['md_results']['entity_counts'].update(md_doc_results['entity_counts'])
        results['md_results']['processing_time'] += md_doc_results['processing_time']
        
        results['lg_results']['total_entities'] += lg_doc_results['total_entities']
        results['lg_results']['unique_entities'].update(lg_doc_results['unique_entities'])
        results['lg_results']['new_patterns'].update(lg_doc_results['new_patterns'])
        results['lg_results']['entity_counts'].update(lg_doc_results['entity_counts'])
        results['lg_results']['processing_time'] += lg_doc_results['processing_time']
        
        # Progress logging
        if results['documents_processed'] % 100 == 0:
            logger.info(f"Processed {results['documents_processed']} documents...")
    
    # Calculate comparison metrics
    md_entities = results['md_results']['unique_entities']
    lg_entities = results['lg_results']['unique_entities']
    
    both_models = md_entities.intersection(lg_entities)
    md_only = md_entities - lg_entities
    lg_only = lg_entities - md_entities
    all_unique = md_entities.union(lg_entities)
    
    results['comparison_metrics'] = {
        'total_unique_entities': len(all_unique),
        'md_unique_entities': len(md_entities),
        'lg_unique_entities': len(lg_entities),
        'both_models_entities': len(both_models),
        'md_only_entities': len(md_only),
        'lg_only_entities': len(lg_only),
        'model_overlap_percentage': (len(both_models) / len(all_unique) * 100) if all_unique else 0,
        'md_new_patterns': len(results['md_results']['new_patterns']),
        'lg_new_patterns': len(results['lg_results']['new_patterns']),
        'total_new_patterns': len(results['md_results']['new_patterns'].union(results['lg_results']['new_patterns']))
    }
    
    # Convert sets to lists for JSON serialization
    results['md_results']['unique_entities'] = list(results['md_results']['unique_entities'])
    results['md_results']['new_patterns'] = list(results['md_results']['new_patterns'])
    results['md_results']['entity_counts'] = dict(results['md_results']['entity_counts'])
    
    results['lg_results']['unique_entities'] = list(results['lg_results']['unique_entities'])
    results['lg_results']['new_patterns'] = list(results['lg_results']['new_patterns'])
    results['lg_results']['entity_counts'] = dict(results['lg_results']['entity_counts'])
    
    return results

def generate_geographic_detection_report(results: Dict, filename: str):
    """Generate comprehensive geographic entity detection report."""
    with open(filename, 'w') as f:
        f.write("Geographic Entity Detection System Report\n")
        f.write("=" * 60 + "\n\n")
        
        f.write(f"**Analysis Date (PST):** {results['timestamp_pst']}\n")
        f.write(f"**Analysis Date (UTC):** {results['timestamp_utc']}\n")
        f.write(f"**Documents Processed:** {results['documents_processed']}\n")
        f.write(f"**HTML Processed:** {results['html_processed']}\n")
        f.write(f"**Plain Text Processed:** {results['plain_processed']}\n\n")
        
        metrics = results['comparison_metrics']
        
        f.write("## Model Performance Comparison\n\n")
        f.write("| Metric | en_core_web_md | en_core_web_lg |\n")
        f.write("|--------|----------------|----------------|\n")
        f.write(f"| Total Entities Found | {results['md_results']['total_entities']} | {results['lg_results']['total_entities']} |\n")
        f.write(f"| Unique Entities | {metrics['md_unique_entities']} | {metrics['lg_unique_entities']} |\n")
        f.write(f"| New Patterns | {metrics['md_new_patterns']} | {metrics['lg_new_patterns']} |\n")
        f.write(f"| Processing Time (s) | {results['md_results']['processing_time']:.1f} | {results['lg_results']['processing_time']:.1f} |\n\n")
        
        f.write("## Cross-Model Analysis\n\n")
        f.write(f"- **Total unique entities discovered:** {metrics['total_unique_entities']}\n")
        f.write(f"- **Entities found by both models:** {metrics['both_models_entities']}\n")
        f.write(f"- **MD model only:** {metrics['md_only_entities']}\n")
        f.write(f"- **LG model only:** {metrics['lg_only_entities']}\n")
        f.write(f"- **Model overlap:** {metrics['model_overlap_percentage']:.1f}%\n")
        f.write(f"- **Total new patterns:** {metrics['total_new_patterns']}\n\n")
        
        # Top entities by frequency
        f.write("## Most Frequent Entities (MD Model)\n\n")
        md_sorted = sorted(results['md_results']['entity_counts'].items(), 
                          key=lambda x: x[1], reverse=True)
        for entity, count in md_sorted[:20]:
            f.write(f"- {entity}: {count}\n")
        
        f.write("\n## Most Frequent Entities (LG Model)\n\n")
        lg_sorted = sorted(results['lg_results']['entity_counts'].items(), 
                          key=lambda x: x[1], reverse=True)
        for entity, count in lg_sorted[:20]:
            f.write(f"- {entity}: {count}\n")
        
        f.write(f"\n## Processing Summary\n\n")
        if results['html_processed'] > 0:
            f.write("✅ **Enhanced HTML processing enabled** - prevents region concatenation\n")
        f.write(f"✅ **Dual model validation** - {metrics['model_overlap_percentage']:.1f}% agreement\n")
        f.write(f"✅ **Pattern discovery** - {metrics['total_new_patterns']} new patterns identified\n\n")
        
        f.write("## Recommendations\n\n")
        if metrics['model_overlap_percentage'] > 50:
            f.write("- High model agreement suggests reliable pattern discovery\n")
        else:
            f.write("- Lower model agreement - manual review recommended for new patterns\n")
        
        f.write("- Use high-confidence patterns (found by both models) for immediate addition\n")
        f.write("- Review medium-confidence patterns (single model, high frequency) manually\n")

def main():
    """Main execution function."""
    logger.info("Starting Geographic Entity Detection System")
    
    # Connect to MongoDB
    client, markets_collection, patterns_collection = connect_to_mongodb()
    if not client:
        logger.error("Failed to connect to MongoDB")
        return
    
    try:
        # Run dual-model geographic detection
        results = dual_model_geographic_detection(markets_collection, patterns_collection, limit=1000)
        
        # Save results
        timestamp = get_timestamp()
        output_file = f"outputs/{timestamp['filename']}_geographic_detection_results.json"
        report_file = f"outputs/{timestamp['filename']}_geographic_detection_report.txt"
        
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        generate_geographic_detection_report(results, report_file)
        
        logger.info(f"\nResults saved to: {output_file}")
        logger.info(f"Report saved to: {report_file}")
        
        # Print summary
        metrics = results['comparison_metrics']
        print("\n" + "="*60)
        print("GEOGRAPHIC ENTITY DETECTION COMPLETE")
        print("="*60)
        print(f"Documents processed: {results['documents_processed']}")
        print(f"Total unique entities: {metrics['total_unique_entities']}")
        print(f"MD model entities: {metrics['md_unique_entities']}")
        print(f"LG model entities: {metrics['lg_unique_entities']}")
        print(f"Model overlap: {metrics['model_overlap_percentage']:.1f}%")
        print(f"New patterns discovered: {metrics['total_new_patterns']}")
    
    except Exception as e:
        logger.error(f"Geographic detection failed: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        if client:
            client.close()
            logger.info("MongoDB connection closed")

if __name__ == "__main__":
    main()