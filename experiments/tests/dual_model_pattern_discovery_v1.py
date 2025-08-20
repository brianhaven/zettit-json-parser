#!/usr/bin/env python3
"""
Dual-Model Pattern Discovery Script v1
Analyzes report_description_full fields using both spaCy models to discover geographic patterns

Features:
1. Uses both en_core_web_md and en_core_web_lg models
2. Compares results between models
3. Deduplicates findings
4. Identifies truly new patterns vs existing ones
5. Provides comprehensive comparison statistics
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

def load_existing_patterns(patterns_collection) -> Tuple[Set[str], Dict[str, str]]:
    """Load all existing geographic patterns from MongoDB."""
    try:
        patterns = list(patterns_collection.find({
            "type": "geographic_entity",
            "active": True
        }))
        
        # Create comprehensive pattern set (lowercase for comparison)
        all_patterns = set()
        pattern_map = {}  # Map lowercase to original term
        
        for pattern in patterns:
            term = pattern['term']
            all_patterns.add(term.lower())
            pattern_map[term.lower()] = term
            
            for alias in pattern.get('aliases', []):
                all_patterns.add(alias.lower())
                if alias.lower() not in pattern_map:
                    pattern_map[alias.lower()] = term  # Map alias to main term
        
        logger.info(f"Loaded {len(patterns)} geographic patterns with {len(all_patterns)} total terms/aliases")
        return all_patterns, pattern_map
        
    except Exception as e:
        logger.error(f"Error loading geographic patterns: {e}")
        return set(), {}

def extract_entities_with_model(nlp, text: str, model_name: str) -> Dict:
    """Extract geographic entities using a specific spaCy model."""
    if not text or len(text) < 50:
        return {
            'entities': [],
            'unique_entities': set(),
            'entity_counts': Counter(),
            'processing_time': 0,
            'model': model_name,
            'total_entities': 0,
            'unique_count': 0
        }
    
    start_time = time.time()
    
    # Process text (limit to 100k chars for performance)
    doc = nlp(text[:100000])
    
    # Extract geographic entities
    entities = []
    for ent in doc.ents:
        if ent.label_ in ['GPE', 'LOC']:
            entities.append({
                'text': ent.text,
                'label': ent.label_,
                'start': ent.start_char,
                'end': ent.end_char
            })
    
    # Create unique entity set and count occurrences
    entity_texts = [e['text'].strip() for e in entities]
    unique_entities = set(entity_texts)
    entity_counts = Counter(entity_texts)
    
    processing_time = time.time() - start_time
    
    return {
        'entities': entities,
        'unique_entities': unique_entities,
        'entity_counts': entity_counts,
        'processing_time': processing_time,
        'model': model_name,
        'total_entities': len(entities),
        'unique_count': len(unique_entities)
    }

def compare_model_results(md_results: Dict, lg_results: Dict, existing_patterns: Set[str]) -> Dict:
    """Compare results from both models and identify new patterns."""
    
    # Get unique entities from each model
    md_entities = md_results['unique_entities']
    lg_entities = lg_results['unique_entities']
    
    # Calculate overlaps and differences
    both_models = md_entities.intersection(lg_entities)
    md_only = md_entities - lg_entities
    lg_only = lg_entities - md_entities
    all_entities = md_entities.union(lg_entities)
    
    # Identify new patterns (not in existing patterns)
    new_from_both = set()
    new_from_md_only = set()
    new_from_lg_only = set()
    
    for entity in both_models:
        if entity.lower() not in existing_patterns:
            new_from_both.add(entity)
    
    for entity in md_only:
        if entity.lower() not in existing_patterns:
            new_from_md_only.add(entity)
    
    for entity in lg_only:
        if entity.lower() not in existing_patterns:
            new_from_lg_only.add(entity)
    
    all_new = new_from_both.union(new_from_md_only).union(new_from_lg_only)
    
    # Combine counts from both models
    combined_counts = Counter()
    for entity, count in md_results['entity_counts'].items():
        combined_counts[entity] += count
    for entity, count in lg_results['entity_counts'].items():
        if entity not in md_results['entity_counts']:
            combined_counts[entity] = count
    
    return {
        'both_models': both_models,
        'md_only': md_only,
        'lg_only': lg_only,
        'all_entities': all_entities,
        'new_from_both': new_from_both,
        'new_from_md_only': new_from_md_only,
        'new_from_lg_only': new_from_lg_only,
        'all_new': all_new,
        'combined_counts': combined_counts,
        'overlap_percentage': (len(both_models) / len(all_entities) * 100) if all_entities else 0,
        'md_precision': (len(both_models) / len(md_entities) * 100) if md_entities else 0,
        'lg_precision': (len(both_models) / len(lg_entities) * 100) if lg_entities else 0
    }

def analyze_documents_dual_model(
    markets_collection,
    patterns_collection,
    sample_size: int = 1000,
    aggregation_size: int = 0  # 0 = individual, >0 = aggregate that many docs
) -> Dict:
    """
    Analyze documents using both spaCy models and compare results.
    
    Args:
        sample_size: Number of documents to analyze
        aggregation_size: If >0, aggregate this many documents into blocks
    """
    timestamp = get_timestamp()
    
    logger.info(f"Starting dual-model analysis with sample size: {sample_size}")
    if aggregation_size > 0:
        logger.info(f"Using aggregation blocks of {aggregation_size} documents")
    
    # Load both spaCy models
    logger.info("Loading spaCy models...")
    nlp_md = spacy.load("en_core_web_md", disable=["tagger", "parser", "attribute_ruler", "lemmatizer"])
    nlp_lg = spacy.load("en_core_web_lg", disable=["tagger", "parser", "attribute_ruler", "lemmatizer"])
    
    # Load existing patterns
    existing_patterns, pattern_map = load_existing_patterns(patterns_collection)
    
    # Query documents with descriptions
    logger.info("Querying documents...")
    cursor = markets_collection.find(
        {"report_description_full": {"$exists": True, "$ne": ""}},
        {"report_description_full": 1, "report_title_short": 1, "publisherID": 1}
    ).limit(sample_size)
    
    # Collect documents
    documents = list(cursor)
    logger.info(f"Retrieved {len(documents)} documents")
    
    # Initialize results
    results = {
        'timestamp_pst': timestamp['pst'],
        'timestamp_utc': timestamp['utc'],
        'sample_size': len(documents),
        'aggregation_size': aggregation_size,
        'existing_patterns_count': len(existing_patterns),
        'md_results': {
            'total_entities': 0,
            'unique_entities': set(),
            'entity_counts': Counter(),
            'processing_time': 0
        },
        'lg_results': {
            'total_entities': 0,
            'unique_entities': set(),
            'entity_counts': Counter(),
            'processing_time': 0
        },
        'comparison': {},
        'high_confidence_new': []  # Patterns found by both models
    }
    
    # Process documents
    if aggregation_size == 0:
        # Individual document processing
        logger.info("Processing documents individually...")
        
        for i, doc in enumerate(documents):
            if (i + 1) % 100 == 0:
                logger.info(f"Processed {i + 1} documents...")
            
            description = clean_html(doc.get('report_description_full', ''))
            
            # Process with MD model
            md_result = extract_entities_with_model(nlp_md, description, 'md')
            results['md_results']['total_entities'] += md_result['total_entities']
            results['md_results']['unique_entities'].update(md_result['unique_entities'])
            results['md_results']['entity_counts'].update(md_result['entity_counts'])
            results['md_results']['processing_time'] += md_result['processing_time']
            
            # Process with LG model
            lg_result = extract_entities_with_model(nlp_lg, description, 'lg')
            results['lg_results']['total_entities'] += lg_result['total_entities']
            results['lg_results']['unique_entities'].update(lg_result['unique_entities'])
            results['lg_results']['entity_counts'].update(lg_result['entity_counts'])
            results['lg_results']['processing_time'] += lg_result['processing_time']
    
    else:
        # Aggregated processing
        logger.info(f"Processing documents in blocks of {aggregation_size}...")
        
        for block_start in range(0, len(documents), aggregation_size):
            block_end = min(block_start + aggregation_size, len(documents))
            block_docs = documents[block_start:block_end]
            
            logger.info(f"Processing block {block_start//aggregation_size + 1} (docs {block_start+1}-{block_end})...")
            
            # Aggregate descriptions
            aggregated_text = " ".join([
                clean_html(doc.get('report_description_full', ''))
                for doc in block_docs
            ])
            
            # Process with MD model
            md_result = extract_entities_with_model(nlp_md, aggregated_text, 'md')
            results['md_results']['total_entities'] += md_result['total_entities']
            results['md_results']['unique_entities'].update(md_result['unique_entities'])
            results['md_results']['entity_counts'].update(md_result['entity_counts'])
            results['md_results']['processing_time'] += md_result['processing_time']
            
            # Process with LG model
            lg_result = extract_entities_with_model(nlp_lg, aggregated_text, 'lg')
            results['lg_results']['total_entities'] += lg_result['total_entities']
            results['lg_results']['unique_entities'].update(lg_result['unique_entities'])
            results['lg_results']['entity_counts'].update(lg_result['entity_counts'])
            results['lg_results']['processing_time'] += lg_result['processing_time']
    
    # Compare results
    logger.info("Comparing model results...")
    comparison = compare_model_results(
        {
            'unique_entities': results['md_results']['unique_entities'],
            'entity_counts': results['md_results']['entity_counts']
        },
        {
            'unique_entities': results['lg_results']['unique_entities'],
            'entity_counts': results['lg_results']['entity_counts']
        },
        existing_patterns
    )
    
    results['comparison'] = comparison
    
    # Identify high-confidence new patterns (found by both models with count >= 3)
    for entity in comparison['new_from_both']:
        count = comparison['combined_counts'][entity]
        if count >= 3:
            results['high_confidence_new'].append({
                'entity': entity,
                'count': count,
                'confidence': 'HIGH (both models)'
            })
    
    # Add medium confidence patterns (found by one model with count >= 5)
    for entity in comparison['new_from_md_only']:
        count = results['md_results']['entity_counts'][entity]
        if count >= 5:
            results['high_confidence_new'].append({
                'entity': entity,
                'count': count,
                'confidence': 'MEDIUM (MD only)'
            })
    
    for entity in comparison['new_from_lg_only']:
        count = results['lg_results']['entity_counts'][entity]
        if count >= 5:
            results['high_confidence_new'].append({
                'entity': entity,
                'count': count,
                'confidence': 'MEDIUM (LG only)'
            })
    
    # Sort by count
    results['high_confidence_new'].sort(key=lambda x: x['count'], reverse=True)
    
    # Convert sets to lists for JSON serialization
    results['md_results']['unique_entities'] = list(results['md_results']['unique_entities'])
    results['lg_results']['unique_entities'] = list(results['lg_results']['unique_entities'])
    results['md_results']['entity_counts'] = dict(results['md_results']['entity_counts'].most_common(100))
    results['lg_results']['entity_counts'] = dict(results['lg_results']['entity_counts'].most_common(100))
    
    # Convert comparison sets to lists
    for key in ['both_models', 'md_only', 'lg_only', 'all_entities', 
                'new_from_both', 'new_from_md_only', 'new_from_lg_only', 'all_new']:
        if key in comparison:
            comparison[key] = list(comparison[key])
    comparison['combined_counts'] = dict(comparison['combined_counts'].most_common(100))
    
    return results

def generate_comparison_report(results: Dict, filename: str):
    """Generate a detailed comparison report."""
    with open(filename, 'w') as f:
        f.write("Dual-Model Pattern Discovery Analysis Report\n")
        f.write("=" * 60 + "\n\n")
        
        f.write(f"**Analysis Date (PST):** {results['timestamp_pst']}\n")
        f.write(f"**Analysis Date (UTC):** {results['timestamp_utc']}\n")
        f.write(f"**Documents Analyzed:** {results['sample_size']}\n")
        
        if results['aggregation_size'] > 0:
            f.write(f"**Aggregation Size:** {results['aggregation_size']} documents per block\n")
        else:
            f.write("**Processing Mode:** Individual documents\n")
        
        f.write(f"**Existing Patterns in DB:** {results['existing_patterns_count']}\n\n")
        
        # Model Performance Comparison
        f.write("## Model Performance Comparison\n\n")
        f.write("| Metric | en_core_web_md | en_core_web_lg |\n")
        f.write("|--------|----------------|----------------|\n")
        f.write(f"| Total Entities Found | {results['md_results']['total_entities']} | {results['lg_results']['total_entities']} |\n")
        f.write(f"| Unique Entities | {len(results['md_results']['unique_entities'])} | {len(results['lg_results']['unique_entities'])} |\n")
        f.write(f"| Processing Time (s) | {results['md_results']['processing_time']:.2f} | {results['lg_results']['processing_time']:.2f} |\n")
        f.write(f"| Entities/Second | {results['md_results']['total_entities']/results['md_results']['processing_time']:.1f} | {results['lg_results']['total_entities']/results['lg_results']['processing_time']:.1f} |\n\n")
        
        # Agreement Analysis
        comp = results['comparison']
        f.write("## Model Agreement Analysis\n\n")
        f.write(f"- **Entities found by both models:** {len(comp['both_models'])}\n")
        f.write(f"- **Entities found by MD only:** {len(comp['md_only'])}\n")
        f.write(f"- **Entities found by LG only:** {len(comp['lg_only'])}\n")
        f.write(f"- **Total unique entities:** {len(comp['all_entities'])}\n")
        f.write(f"- **Model overlap:** {comp['overlap_percentage']:.1f}%\n")
        f.write(f"- **MD precision (vs overlap):** {comp['md_precision']:.1f}%\n")
        f.write(f"- **LG precision (vs overlap):** {comp['lg_precision']:.1f}%\n\n")
        
        # New Pattern Discovery
        f.write("## New Pattern Discovery\n\n")
        f.write(f"- **New patterns (both models):** {len(comp['new_from_both'])}\n")
        f.write(f"- **New patterns (MD only):** {len(comp['new_from_md_only'])}\n")
        f.write(f"- **New patterns (LG only):** {len(comp['new_from_lg_only'])}\n")
        f.write(f"- **Total new patterns:** {len(comp['all_new'])}\n\n")
        
        # High Confidence Recommendations
        f.write("## High-Confidence Pattern Recommendations\n\n")
        if results['high_confidence_new']:
            f.write("| Entity | Count | Confidence |\n")
            f.write("|--------|-------|------------|\n")
            for pattern in results['high_confidence_new'][:30]:
                f.write(f"| {pattern['entity']} | {pattern['count']} | {pattern['confidence']} |\n")
        else:
            f.write("No high-confidence patterns found.\n")
        
        # Top Entities by Model
        f.write("\n## Top 20 Entities by Model\n\n")
        f.write("### en_core_web_md\n")
        for entity, count in list(results['md_results']['entity_counts'].items())[:20]:
            f.write(f"- {entity}: {count}\n")
        
        f.write("\n### en_core_web_lg\n")
        for entity, count in list(results['lg_results']['entity_counts'].items())[:20]:
            f.write(f"- {entity}: {count}\n")
        
        # Recommendations
        f.write("\n## Recommendations\n\n")
        
        if comp['overlap_percentage'] > 70:
            f.write("✅ **High model agreement (>70%)**: Either model can be used reliably.\n")
            if results['md_results']['processing_time'] < results['lg_results']['processing_time']:
                f.write("   Recommend using **en_core_web_md** for better speed.\n")
            else:
                f.write("   Recommend using **en_core_web_lg** for potentially better accuracy.\n")
        else:
            f.write("⚠️ **Low model agreement (<70%)**: Consider using both models for comprehensive coverage.\n")
        
        if results['aggregation_size'] > 0:
            f.write(f"\n📊 **Aggregation Impact**: Processing {results['aggregation_size']} documents at once.\n")
            f.write("   Consider testing different aggregation sizes for optimal results.\n")
        
        f.write("\n### Next Steps\n")
        f.write("1. Review high-confidence patterns for addition to pattern library\n")
        f.write("2. Validate patterns with counts >= 3 from both models\n")
        f.write("3. Consider running on full dataset if results are promising\n")

def main():
    """Main execution function."""
    logger.info("Starting dual-model pattern discovery analysis")
    
    # Connect to MongoDB
    client, markets_collection, patterns_collection = connect_to_mongodb()
    if not client:
        logger.error("Failed to connect to MongoDB")
        return
    
    try:
        timestamp = get_timestamp()
        
        # Test 1: Individual document processing (200 docs for initial test)
        logger.info("\n" + "="*60)
        logger.info("TEST 1: Individual Document Processing (200 docs)")
        logger.info("="*60)
        
        results_individual = analyze_documents_dual_model(
            markets_collection,
            patterns_collection,
            sample_size=200,  # Reduced for faster initial test
            aggregation_size=0
        )
        
        # Save results
        output_individual = f"outputs/{timestamp['filename']}_dual_model_individual.json"
        report_individual = f"outputs/{timestamp['filename']}_dual_model_individual_report.txt"
        
        with open(output_individual, 'w') as f:
            json.dump(results_individual, f, indent=2, default=str)
        
        generate_comparison_report(results_individual, report_individual)
        
        logger.info(f"Individual results saved to: {output_individual}")
        logger.info(f"Individual report saved to: {report_individual}")
        
        # Print summary
        print("\n" + "="*60)
        print("INDIVIDUAL PROCESSING SUMMARY")
        print("="*60)
        print(f"MD Model: {results_individual['md_results']['total_entities']} entities, "
              f"{len(results_individual['md_results']['unique_entities'])} unique")
        print(f"LG Model: {results_individual['lg_results']['total_entities']} entities, "
              f"{len(results_individual['lg_results']['unique_entities'])} unique")
        print(f"Model Agreement: {results_individual['comparison']['overlap_percentage']:.1f}%")
        print(f"New Patterns Discovered: {len(results_individual['comparison']['all_new'])}")
        print(f"High-Confidence Patterns: {len(results_individual['high_confidence_new'])}")
        
        # Ask user if they want to test aggregation
        print("\n" + "="*60)
        print("Individual processing complete. Results show:")
        print(f"- MD model found {len(results_individual['md_results']['unique_entities'])} unique entities")
        print(f"- LG model found {len(results_individual['lg_results']['unique_entities'])} unique entities")
        print(f"- Model agreement: {results_individual['comparison']['overlap_percentage']:.1f}%")
        print("\nWould you like to test aggregated processing (50 docs per block)?")
        print("This may provide better context for entity recognition.")
        
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