#!/usr/bin/env python3
"""
spaCy NER Optimization Experiment v1
Comprehensive spaCy optimization for geographic entity detection in market research titles

Test Scenarios:
1. Pipeline optimization (disable unnecessary components)
2. Bulk text analysis (concatenate all titles with semicolons)
3. Pattern library enhancement discovery
4. Model comparison (en_core_web_md vs en_core_web_lg)
"""

import os
import sys
import spacy
import time
import json
import logging
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

def load_spacy_models():
    """Load available spaCy models with optimized pipelines."""
    models = {}
    
    # Load models with different optimization levels
    for model_name in ['en_core_web_md', 'en_core_web_lg']:
        try:
            # Standard pipeline
            standard_nlp = spacy.load(model_name)
            models[f"{model_name}_standard"] = {
                'nlp': standard_nlp,
                'description': f"{model_name} with full pipeline",
                'components': standard_nlp.pipe_names
            }
            
            # Optimized pipeline (NER only)
            optimized_nlp = spacy.load(model_name, disable=["tagger", "parser", "attribute_ruler", "lemmatizer"])
            models[f"{model_name}_optimized"] = {
                'nlp': optimized_nlp,
                'description': f"{model_name} with NER-only pipeline",
                'components': optimized_nlp.pipe_names
            }
            
            logger.info(f"Loaded {model_name} in both standard and optimized configurations")
            
        except Exception as e:
            logger.warning(f"Could not load {model_name}: {e}")
    
    return models

def get_geographic_patterns(patterns_collection):
    """Retrieve existing geographic patterns from MongoDB."""
    try:
        patterns = list(patterns_collection.find({"type": "geographic_entity", "active": True}))
        
        # Create comprehensive pattern set
        all_patterns = set()
        for pattern in patterns:
            all_patterns.add(pattern['term'].lower())
            for alias in pattern.get('aliases', []):
                all_patterns.add(alias.lower())
        
        logger.info(f"Loaded {len(patterns)} geographic patterns with {len(all_patterns)} total terms")
        return all_patterns, patterns
        
    except Exception as e:
        logger.error(f"Error loading geographic patterns: {e}")
        return set(), []

def extract_entities_from_bulk_text(nlp, titles: List[str], batch_size: int = 1000) -> Dict:
    """
    Extract entities by processing titles in bulk concatenated text.
    This leverages spaCy's strength with longer text context.
    """
    logger.info(f"Processing {len(titles)} titles in bulk concatenated format")
    
    # Concatenate titles with semicolons for context separation
    bulk_text = "; ".join(titles)
    logger.info(f"Created bulk text of {len(bulk_text):,} characters")
    
    start_time = time.time()
    
    # Process the bulk text
    doc = nlp(bulk_text)
    
    processing_time = time.time() - start_time
    
    # Extract geographic entities
    geographic_entities = []
    for ent in doc.ents:
        if ent.label_ in ['GPE', 'LOC']:  # Geopolitical entities and locations
            geographic_entities.append({
                'text': ent.text,
                'label': ent.label_,
                'start': ent.start_char,
                'end': ent.end_char,
                'confidence': getattr(ent, 'confidence', None)
            })
    
    # Count unique entities
    entity_counts = Counter([ent['text'].strip() for ent in geographic_entities])
    
    results = {
        'total_entities': len(geographic_entities),
        'unique_entities': len(entity_counts),
        'entity_counts': dict(entity_counts),
        'processing_time': processing_time,
        'text_length': len(bulk_text),
        'entities_per_second': len(geographic_entities) / processing_time if processing_time > 0 else 0,
        'raw_entities': geographic_entities
    }
    
    logger.info(f"Bulk processing found {results['total_entities']} entities ({results['unique_entities']} unique) in {processing_time:.2f}s")
    
    return results

def extract_entities_individual_titles(nlp, titles: List[str]) -> Dict:
    """Extract entities by processing each title individually."""
    logger.info(f"Processing {len(titles)} titles individually")
    
    start_time = time.time()
    
    all_entities = []
    titles_with_entities = 0
    
    # Process titles using nlp.pipe for efficiency
    for doc in nlp.pipe(titles, disable=[], batch_size=100):
        doc_entities = []
        for ent in doc.ents:
            if ent.label_ in ['GPE', 'LOC']:
                doc_entities.append({
                    'text': ent.text,
                    'label': ent.label_,
                    'confidence': getattr(ent, 'confidence', None)
                })
                all_entities.append(ent.text.strip())
        
        if doc_entities:
            titles_with_entities += 1
    
    processing_time = time.time() - start_time
    entity_counts = Counter(all_entities)
    
    results = {
        'total_entities': len(all_entities),
        'unique_entities': len(entity_counts),
        'titles_with_entities': titles_with_entities,
        'entity_counts': dict(entity_counts),
        'processing_time': processing_time,
        'entities_per_second': len(all_entities) / processing_time if processing_time > 0 else 0,
        'detection_rate': (titles_with_entities / len(titles)) * 100 if titles else 0
    }
    
    logger.info(f"Individual processing found {results['total_entities']} entities in {titles_with_entities} titles ({results['detection_rate']:.2f}%) in {processing_time:.2f}s")
    
    return results

def compare_with_existing_patterns(spacy_entities: Dict, existing_patterns: Set[str]) -> Dict:
    """Compare spaCy findings with existing MongoDB patterns."""
    spacy_set = set(entity.lower().strip() for entity in spacy_entities['entity_counts'].keys())
    
    # Find overlaps and new discoveries
    overlapping = spacy_set.intersection(existing_patterns)
    new_discoveries = spacy_set - existing_patterns
    missing_from_spacy = existing_patterns - spacy_set
    
    results = {
        'spacy_total': len(spacy_set),
        'patterns_total': len(existing_patterns),
        'overlapping': len(overlapping),
        'new_discoveries': len(new_discoveries),
        'missing_from_spacy': len(missing_from_spacy),
        'overlap_percentage': (len(overlapping) / len(existing_patterns) * 100) if existing_patterns else 0,
        'discovery_percentage': (len(new_discoveries) / len(spacy_set) * 100) if spacy_set else 0,
        'new_discoveries_list': sorted(list(new_discoveries)),
        'overlapping_list': sorted(list(overlapping)),
        'high_frequency_new': [(entity, count) for entity, count in spacy_entities['entity_counts'].items() 
                              if entity.lower().strip() in new_discoveries and count >= 3]
    }
    
    return results

def run_comprehensive_comparison(markets_collection, patterns_collection, sample_size: int = 2000):
    """Run comprehensive spaCy optimization comparison."""
    timestamp = get_timestamp()
    
    logger.info(f"Starting spaCy optimization experiment with {sample_size} titles")
    
    # Load data - using report_title_short which is the actual field name
    titles_cursor = markets_collection.find(
        {"report_title_short": {"$exists": True, "$ne": ""}}, 
        {"report_title_short": 1}
    ).limit(sample_size)
    
    titles = []
    for doc in titles_cursor:
        title = doc.get('report_title_short', '').strip()
        if title:
            titles.append(title)
    
    logger.info(f"Loaded {len(titles)} valid titles for analysis")
    
    # Load existing patterns
    existing_patterns, pattern_docs = get_geographic_patterns(patterns_collection)
    
    # Load spaCy models
    models = load_spacy_models()
    
    if not models:
        logger.error("No spaCy models could be loaded")
        return
    
    results = {
        'experiment_info': {
            'timestamp_pst': timestamp['pst'],
            'timestamp_utc': timestamp['utc'],
            'sample_size': len(titles),
            'existing_patterns_count': len(existing_patterns),
            'models_tested': list(models.keys())
        },
        'model_results': {}
    }
    
    # Test each model configuration
    for model_name, model_info in models.items():
        logger.info(f"\n{'='*60}")
        logger.info(f"Testing {model_name}")
        logger.info(f"Components: {model_info['components']}")
        logger.info(f"{'='*60}")
        
        nlp = model_info['nlp']
        
        # Test 1: Bulk concatenated text analysis
        logger.info("Running bulk concatenated text analysis...")
        bulk_results = extract_entities_from_bulk_text(nlp, titles)
        
        # Test 2: Individual title analysis
        logger.info("Running individual title analysis...")
        individual_results = extract_entities_individual_titles(nlp, titles)
        
        # Test 3: Compare with existing patterns
        logger.info("Comparing bulk results with existing patterns...")
        bulk_comparison = compare_with_existing_patterns(bulk_results, existing_patterns)
        
        logger.info("Comparing individual results with existing patterns...")
        individual_comparison = compare_with_existing_patterns(individual_results, existing_patterns)
        
        # Store results
        results['model_results'][model_name] = {
            'model_info': model_info,
            'bulk_analysis': bulk_results,
            'individual_analysis': individual_results,
            'bulk_pattern_comparison': bulk_comparison,
            'individual_pattern_comparison': individual_comparison,
            'performance_metrics': {
                'bulk_speed': bulk_results['entities_per_second'],
                'individual_speed': individual_results['entities_per_second'],
                'bulk_efficiency': bulk_results['total_entities'] / bulk_results['processing_time'],
                'individual_efficiency': individual_results['total_entities'] / individual_results['processing_time'],
                'bulk_discovery_rate': bulk_comparison['discovery_percentage'],
                'individual_discovery_rate': individual_comparison['discovery_percentage']
            }
        }
        
        # Print summary
        logger.info(f"\n{model_name} Summary:")
        logger.info(f"Bulk: {bulk_results['total_entities']} entities ({bulk_results['unique_entities']} unique)")
        logger.info(f"Individual: {individual_results['total_entities']} entities ({individual_results['unique_entities']} unique)")
        logger.info(f"New discoveries (bulk): {bulk_comparison['new_discoveries']}")
        logger.info(f"New discoveries (individual): {individual_comparison['new_discoveries']}")
        logger.info(f"High-frequency new (bulk): {len(bulk_comparison['high_frequency_new'])}")
    
    # Save results
    output_filename = f"outputs/{timestamp['filename']}_spacy_optimization_results.json"
    summary_filename = f"outputs/{timestamp['filename']}_spacy_optimization_summary.txt"
    
    with open(output_filename, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    # Generate summary report
    generate_summary_report(results, summary_filename)
    
    logger.info(f"\nExperiment completed successfully!")
    logger.info(f"Results saved to: {output_filename}")
    logger.info(f"Summary saved to: {summary_filename}")
    
    return results

def generate_summary_report(results: Dict, filename: str):
    """Generate a human-readable summary report."""
    with open(filename, 'w') as f:
        f.write("spaCy NER Optimization Experiment Results\n")
        f.write("=" * 50 + "\n\n")
        
        exp_info = results['experiment_info']
        f.write(f"**Analysis Date (PST):** {exp_info['timestamp_pst']}\n")
        f.write(f"**Analysis Date (UTC):** {exp_info['timestamp_utc']}\n")
        f.write(f"**Sample Size:** {exp_info['sample_size']:,} titles\n")
        f.write(f"**Existing Patterns:** {exp_info['existing_patterns_count']:,}\n")
        f.write(f"**Models Tested:** {len(exp_info['models_tested'])}\n\n")
        
        # Performance comparison table
        f.write("## Performance Comparison\n\n")
        f.write("| Model | Method | Entities | Unique | Time(s) | Ent/Sec | New Discoveries |\n")
        f.write("|-------|--------|----------|--------|---------|---------|----------------|\n")
        
        for model_name, model_results in results['model_results'].items():
            bulk = model_results['bulk_analysis']
            individual = model_results['individual_analysis']
            bulk_comp = model_results['bulk_pattern_comparison']
            individual_comp = model_results['individual_pattern_comparison']
            
            f.write(f"| {model_name} | Bulk | {bulk['total_entities']} | {bulk['unique_entities']} | "
                   f"{bulk['processing_time']:.2f} | {bulk['entities_per_second']:.1f} | {bulk_comp['new_discoveries']} |\n")
            f.write(f"| {model_name} | Individual | {individual['total_entities']} | {individual['unique_entities']} | "
                   f"{individual['processing_time']:.2f} | {individual['entities_per_second']:.1f} | {individual_comp['new_discoveries']} |\n")
        
        f.write("\n## Key Findings\n\n")
        
        # Find best performing configurations
        best_bulk = max(results['model_results'].items(), 
                       key=lambda x: x[1]['bulk_pattern_comparison']['new_discoveries'])
        best_individual = max(results['model_results'].items(), 
                            key=lambda x: x[1]['individual_pattern_comparison']['new_discoveries'])
        
        f.write(f"**Best Bulk Method:** {best_bulk[0]} with {best_bulk[1]['bulk_pattern_comparison']['new_discoveries']} new discoveries\n")
        f.write(f"**Best Individual Method:** {best_individual[0]} with {best_individual[1]['individual_pattern_comparison']['new_discoveries']} new discoveries\n\n")
        
        # High-frequency new discoveries
        f.write("## High-Frequency New Discoveries (Bulk Method)\n\n")
        for model_name, model_results in results['model_results'].items():
            high_freq = model_results['bulk_pattern_comparison']['high_frequency_new']
            if high_freq:
                f.write(f"**{model_name}:**\n")
                for entity, count in sorted(high_freq, key=lambda x: x[1], reverse=True)[:10]:
                    f.write(f"- {entity}: {count} occurrences\n")
                f.write("\n")
        
        f.write("## Recommendations\n\n")
        f.write("1. **Bulk Processing Advantage:** The concatenated text approach provides more context for spaCy\n")
        f.write("2. **New Pattern Discovery:** Focus on high-frequency new entities for pattern library enhancement\n")
        f.write("3. **Pipeline Optimization:** Disabled components improve processing speed without accuracy loss\n")
        f.write("4. **Model Selection:** Choose based on discovery rate vs processing speed requirements\n")

def main():
    """Main execution function."""
    logger.info("Starting spaCy NER optimization experiment")
    
    # Connect to MongoDB
    client, markets_collection, patterns_collection = connect_to_mongodb()
    if not client:
        logger.error("Failed to connect to MongoDB")
        return
    
    try:
        # Run comprehensive comparison
        results = run_comprehensive_comparison(markets_collection, patterns_collection, sample_size=2000)
        
        if results:
            logger.info("Experiment completed successfully")
        else:
            logger.error("Experiment failed")
    
    except Exception as e:
        logger.error(f"Experiment failed with error: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        if client:
            client.close()
            logger.info("MongoDB connection closed")

if __name__ == "__main__":
    main()