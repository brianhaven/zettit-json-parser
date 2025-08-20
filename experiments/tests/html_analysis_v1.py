#!/usr/bin/env python3
"""
HTML Analysis v1
Enhanced geographic entity detection using report_description_html
with proper block-level separation and table extraction
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
    """
    if not html_content:
        return {"body_text": "", "table_text": "", "combined_text": ""}
    
    try:
        # Parse HTML with BeautifulSoup
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Extract table content specifically
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
        
        # Process body content with block-level awareness
        block_elements = ['div', 'p', 'li', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 
                         'section', 'article', 'blockquote', 'pre']
        
        # Add line breaks before block elements
        for tag_name in block_elements:
            for tag in soup.find_all(tag_name):
                if tag.string:
                    tag.string.replace_with(f"\n{tag.string}\n")
        
        # Extract text with preserved line breaks
        body_text = soup.get_text(separator='\n', strip=True)
        
        # Clean up the text
        body_text = html.unescape(body_text)
        body_text = re.sub(r'\n+', ' ; ', body_text)  # Convert line breaks to separators
        body_text = re.sub(r'\s+', ' ', body_text)    # Normalize whitespace
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
        # Fallback to simple cleaning
        clean_text = html.unescape(html_content)
        clean_text = re.sub(r'<[^>]+>', ' ; ', clean_text)
        clean_text = re.sub(r'\s+', ' ', clean_text)
        return {
            "body_text": clean_text,
            "table_text": "",
            "combined_text": clean_text
        }

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

def extract_geographic_entities(nlp, text: str, existing_patterns: Set[str]) -> Dict:
    """Extract geographic entities from text."""
    if not text or len(text) < 10:
        return {
            'total_entities': 0,
            'unique_entities': set(),
            'new_patterns': set(),
            'entity_counts': {}
        }
    
    # Limit text length to prevent memory issues
    text = text[:100000]
    
    try:
        doc = nlp(text)
        entities = []
        entity_counts = Counter()
        
        for ent in doc.ents:
            if ent.label_ in ['GPE', 'LOC']:
                entity_text = ent.text.strip()
                # Filter out obvious noise
                if (len(entity_text) >= 2 and 
                    not re.match(r'^[\d\.\s]+$', entity_text) and
                    not re.match(r'^[^\w\s]+$', entity_text)):
                    entities.append(entity_text)
                    entity_counts[entity_text] += 1
        
        unique_entities = set(entities)
        new_patterns = {ent for ent in unique_entities 
                       if ent.lower() not in existing_patterns}
        
        return {
            'total_entities': len(entities),
            'unique_entities': unique_entities,
            'new_patterns': new_patterns,
            'entity_counts': dict(entity_counts)
        }
        
    except Exception as e:
        logger.error(f"Entity extraction error: {e}")
        return {
            'total_entities': 0,
            'unique_entities': set(),
            'new_patterns': set(),
            'entity_counts': {}
        }

def analyze_html_vs_plain_text(markets_collection, patterns_collection, limit=50):
    """Compare HTML vs plain text processing results."""
    timestamp = get_timestamp()
    
    # Load spaCy model
    logger.info("Loading spaCy model...")
    nlp = spacy.load("en_core_web_md", disable=["tagger", "parser", "attribute_ruler", "lemmatizer"])
    
    # Load existing patterns
    existing_patterns = load_existing_patterns(patterns_collection)
    
    # Check data availability
    html_count = markets_collection.count_documents({
        'report_description_html': {'$exists': True, '$ne': ''}
    })
    plain_count = markets_collection.count_documents({
        'report_description_full': {'$exists': True, '$ne': ''}
    })
    
    logger.info(f"Documents with HTML: {html_count}")
    logger.info(f"Documents with plain text: {plain_count}")
    
    # Load test documents
    logger.info(f"Loading {limit} documents for comparison...")
    cursor = markets_collection.find({
        'report_description_html': {'$exists': True, '$ne': ''},
        'report_description_full': {'$exists': True, '$ne': ''}
    }, {
        'report_description_html': 1,
        'report_description_full': 1,
        'report_title_short': 1
    }).limit(limit)
    
    results = {
        'timestamp_pst': timestamp['pst'],
        'timestamp_utc': timestamp['utc'],
        'total_documents': 0,
        'html_processing': {
            'body_entities': set(),
            'table_entities': set(),
            'combined_entities': set(),
            'total_entities': 0,
            'new_patterns': set(),
            'processing_time': 0
        },
        'plain_processing': {
            'entities': set(),
            'total_entities': 0,
            'new_patterns': set(),
            'processing_time': 0
        },
        'comparison_metrics': {},
        'sample_improvements': []
    }
    
    html_entities_all = set()
    plain_entities_all = set()
    
    for doc in cursor:
        results['total_documents'] += 1
        
        # Process HTML version
        start_time = time.time()
        html_data = enhanced_html_cleaning(doc.get('report_description_html', ''))
        
        # Extract from different HTML components
        body_results = extract_geographic_entities(nlp, html_data['body_text'], existing_patterns)
        table_results = extract_geographic_entities(nlp, html_data['table_text'], existing_patterns)
        combined_results = extract_geographic_entities(nlp, html_data['combined_text'], existing_patterns)
        
        html_time = time.time() - start_time
        results['html_processing']['processing_time'] += html_time
        
        # Accumulate HTML results
        results['html_processing']['body_entities'].update(body_results['unique_entities'])
        results['html_processing']['table_entities'].update(table_results['unique_entities'])
        results['html_processing']['combined_entities'].update(combined_results['unique_entities'])
        results['html_processing']['total_entities'] += combined_results['total_entities']
        results['html_processing']['new_patterns'].update(combined_results['new_patterns'])
        html_entities_all.update(combined_results['unique_entities'])
        
        # Process plain text version (existing method)
        start_time = time.time()
        plain_text = doc.get('report_description_full', '')
        # Simple cleaning for comparison
        plain_text = html.unescape(plain_text)
        plain_text = re.sub(r'<[^>]+>', ' ', plain_text)
        plain_text = ' '.join(plain_text.split())
        
        plain_results = extract_geographic_entities(nlp, plain_text, existing_patterns)
        plain_time = time.time() - start_time
        results['plain_processing']['processing_time'] += plain_time
        
        # Accumulate plain results
        results['plain_processing']['entities'].update(plain_results['unique_entities'])
        results['plain_processing']['total_entities'] += plain_results['total_entities']
        results['plain_processing']['new_patterns'].update(plain_results['new_patterns'])
        plain_entities_all.update(plain_results['unique_entities'])
        
        # Track improvements
        html_only = combined_results['unique_entities'] - plain_results['unique_entities']
        if html_only and len(results['sample_improvements']) < 10:
            results['sample_improvements'].append({
                'title': doc.get('report_title_short', '')[:100],
                'html_only_entities': list(html_only)[:5],
                'table_entities': list(table_results['unique_entities'])[:5]
            })
    
    # Calculate comparison metrics
    html_total = len(html_entities_all)
    plain_total = len(plain_entities_all)
    overlap = len(html_entities_all.intersection(plain_entities_all))
    html_only = len(html_entities_all - plain_entities_all)
    
    results['comparison_metrics'] = {
        'html_unique_entities': html_total,
        'plain_unique_entities': plain_total,
        'overlap_entities': overlap,
        'html_only_entities': html_only,
        'improvement_percentage': (html_only / plain_total * 100) if plain_total > 0 else 0,
        'table_only_entities': len(results['html_processing']['table_entities']),
        'body_only_entities': len(results['html_processing']['body_entities'] - results['html_processing']['table_entities'])
    }
    
    # Convert sets to lists for JSON serialization
    results['html_processing']['body_entities'] = list(results['html_processing']['body_entities'])[:100]
    results['html_processing']['table_entities'] = list(results['html_processing']['table_entities'])[:100]
    results['html_processing']['combined_entities'] = list(results['html_processing']['combined_entities'])[:100]
    results['html_processing']['new_patterns'] = list(results['html_processing']['new_patterns'])[:100]
    results['plain_processing']['entities'] = list(results['plain_processing']['entities'])[:100]
    results['plain_processing']['new_patterns'] = list(results['plain_processing']['new_patterns'])[:100]
    
    return results

def generate_html_comparison_report(results: Dict, filename: str):
    """Generate comparison report between HTML and plain text processing."""
    with open(filename, 'w') as f:
        f.write("HTML vs Plain Text Processing Comparison Report\n")
        f.write("=" * 60 + "\n\n")
        
        f.write(f"**Analysis Date (PST):** {results['timestamp_pst']}\n")
        f.write(f"**Analysis Date (UTC):** {results['timestamp_utc']}\n")
        f.write(f"**Documents Analyzed:** {results['total_documents']}\n\n")
        
        metrics = results['comparison_metrics']
        
        f.write("## Processing Results Comparison\n\n")
        f.write("| Method | Unique Entities | New Patterns | Processing Time (s) |\n")
        f.write("|--------|----------------|--------------|--------------------|\n")
        f.write(f"| HTML Processing | {metrics['html_unique_entities']} | "
               f"{len(results['html_processing']['new_patterns'])} | "
               f"{results['html_processing']['processing_time']:.1f} |\n")
        f.write(f"| Plain Text | {metrics['plain_unique_entities']} | "
               f"{len(results['plain_processing']['new_patterns'])} | "
               f"{results['plain_processing']['processing_time']:.1f} |\n")
        
        f.write(f"\n## Key Improvements\n\n")
        f.write(f"- **HTML-only discoveries:** {metrics['html_only_entities']} entities\n")
        f.write(f"- **Improvement rate:** {metrics['improvement_percentage']:.1f}% more entities\n")
        f.write(f"- **Table-specific entities:** {metrics['table_only_entities']} entities\n")
        f.write(f"- **Body-specific entities:** {metrics['body_only_entities']} entities\n")
        
        f.write(f"\n## Sample Improvements\n\n")
        for i, sample in enumerate(results['sample_improvements'][:5], 1):
            f.write(f"**Example {i}:** {sample['title']}\n")
            f.write(f"- HTML-only entities: {', '.join(sample['html_only_entities'])}\n")
            f.write(f"- Table entities: {', '.join(sample['table_entities'])}\n\n")
        
        f.write(f"\n## Recommendations\n\n")
        if metrics['improvement_percentage'] > 10:
            f.write("✅ **HTML processing provides significant improvement** (>10% more entities)\n")
            f.write("- Recommend switching to HTML processing for production\n")
            f.write("- Table extraction provides additional structured data\n")
        else:
            f.write("⚠️ **Marginal improvement** (<10% more entities)\n")
            f.write("- Consider cost/benefit of implementation complexity\n")
        
        if metrics['table_only_entities'] > 10:
            f.write("- **Table extraction is valuable** - captures structured region lists\n")
        
        f.write(f"\n### Next Steps\n")
        f.write("1. Implement HTML processing for batch pattern discovery\n")
        f.write("2. Focus on table extraction for structured region data\n")
        f.write("3. Test on larger dataset if results are promising\n")

def main():
    """Main execution function."""
    logger.info("Starting HTML vs Plain Text analysis")
    
    # Connect to MongoDB
    client, markets_collection, patterns_collection = connect_to_mongodb()
    if not client:
        logger.error("Failed to connect to MongoDB")
        return
    
    try:
        # Run analysis
        results = analyze_html_vs_plain_text(markets_collection, patterns_collection, limit=50)
        
        # Save results
        timestamp = get_timestamp()
        output_file = f"outputs/{timestamp['filename']}_html_analysis_results.json"
        report_file = f"outputs/{timestamp['filename']}_html_analysis_report.txt"
        
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        generate_html_comparison_report(results, report_file)
        
        logger.info(f"\nResults saved to: {output_file}")
        logger.info(f"Report saved to: {report_file}")
        
        # Print summary
        metrics = results['comparison_metrics']
        print("\n" + "="*60)
        print("HTML vs PLAIN TEXT ANALYSIS COMPLETE")
        print("="*60)
        print(f"HTML entities: {metrics['html_unique_entities']}")
        print(f"Plain entities: {metrics['plain_unique_entities']}")
        print(f"HTML improvement: +{metrics['html_only_entities']} entities ({metrics['improvement_percentage']:.1f}%)")
        print(f"Table entities: {metrics['table_only_entities']}")
    
    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        if client:
            client.close()
            logger.info("MongoDB connection closed")

if __name__ == "__main__":
    main()