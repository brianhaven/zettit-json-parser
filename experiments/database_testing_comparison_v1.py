#!/usr/bin/env python3

"""
Database Testing Comparison v1.0
Tests 500 database titles with pattern matching vs spaCy detection
"""

import os
import re
import json
import logging
import spacy
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple, Any, Set
from collections import defaultdict
import pytz
from dotenv import load_dotenv
from pymongo import MongoClient

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def create_improved_pattern(text: str) -> str:
    """Create improved regex pattern that handles punctuation properly."""
    escaped = re.escape(text)
    
    # For patterns with periods, use lookahead/lookbehind for word boundaries
    if '.' in text:
        return r'(?<![a-zA-Z0-9])' + escaped + r'(?![a-zA-Z0-9])'
    else:
        # Use standard word boundaries for regular words
        return r'\b' + escaped + r'\b'

def load_geographic_patterns() -> List[Dict]:
    """Load all geographic patterns from MongoDB."""
    load_dotenv()
    client = MongoClient(os.getenv('MONGODB_URI'))
    db = client['deathstar']
    
    patterns = list(db.pattern_libraries.find({
        'type': 'geographic_entity',
        'active': True
    }))
    
    logger.info(f"Loaded {len(patterns)} geographic patterns from MongoDB")
    return patterns

def load_database_titles(limit: int = 500) -> List[str]:
    """Load titles from the database."""
    load_dotenv()
    client = MongoClient(os.getenv('MONGODB_URI'))
    db = client['deathstar']
    
    # Get titles from markets_raw collection
    titles_cursor = db.markets_raw.find({}, {'report_title_short': 1}).limit(limit)
    titles = [doc['report_title_short'] for doc in titles_cursor if 'report_title_short' in doc]
    
    logger.info(f"Loaded {len(titles)} titles from database")
    return titles

def pattern_matching_detection(patterns: List[Dict], titles: List[str]) -> Dict:
    """Perform pattern matching detection on titles."""
    
    results = {
        'method': 'pattern_matching',
        'total_titles': len(titles),
        'total_patterns': len(patterns),
        'detections': {},
        'titles_with_regions': {},
        'titles_without_regions': []
    }
    
    # Organize patterns by priority and prepare for testing
    terms_by_priority = defaultdict(list)
    all_aliases = {}
    
    for pattern in patterns:
        priority = pattern.get('priority', 5)
        term = pattern['term']
        aliases = pattern.get('aliases', [])
        
        terms_by_priority[priority].append(term)
        
        # Store aliases mapping
        for alias in aliases:
            all_aliases[alias] = term
        
        # Initialize results for this pattern
        results['detections'][term] = {
            'canonical_term': term,
            'aliases': aliases,
            'priority': priority,
            'titles_detected': [],
            'total_detections': 0
        }
    
    priority_order = sorted(terms_by_priority.keys())
    
    logger.info(f"Processing {len(titles)} titles with pattern matching")
    
    # Test each title against all patterns
    for title_idx, title in enumerate(titles):
        if title_idx > 0 and title_idx % 100 == 0:
            logger.info(f"Processed {title_idx}/{len(titles)} titles")
        
        title_regions = []
        title_extracted_regions = []
        matched_positions = set()
        
        # Test main terms by priority
        for priority in priority_order:
            terms = terms_by_priority[priority]
            
            for term in terms:
                pattern = create_improved_pattern(term)
                
                try:
                    for match in re.finditer(pattern, title, re.IGNORECASE):
                        start_pos = match.start()
                        end_pos = match.end()
                        
                        # Check for overlaps
                        if any(pos in range(start_pos, end_pos) for pos in matched_positions):
                            continue
                        
                        matched_positions.update(range(start_pos, end_pos))
                        
                        if term not in title_regions:
                            title_regions.append(term)
                        if match.group() not in title_extracted_regions:
                            title_extracted_regions.append(match.group())
                        
                        results['detections'][term]['titles_detected'].append(title)
                        results['detections'][term]['total_detections'] += 1
                
                except re.error as e:
                    logger.error(f"Regex error for term '{term}': {e}")
        
        # Test aliases
        for alias, canonical_term in all_aliases.items():
            pattern = create_improved_pattern(alias)
            
            try:
                for match in re.finditer(pattern, title, re.IGNORECASE):
                    start_pos = match.start()
                    end_pos = match.end()
                    
                    # Check for overlaps
                    if any(pos in range(start_pos, end_pos) for pos in matched_positions):
                        continue
                    
                    matched_positions.update(range(start_pos, end_pos))
                    
                    if canonical_term not in title_regions:
                        title_regions.append(canonical_term)
                    if match.group() not in title_extracted_regions:
                        title_extracted_regions.append(match.group())
                    
                    results['detections'][canonical_term]['titles_detected'].append(title)
                    results['detections'][canonical_term]['total_detections'] += 1
            
            except re.error as e:
                logger.error(f"Regex error for alias '{alias}': {e}")
        
        # Store title results
        if title_regions:
            results['titles_with_regions'][title] = {
                'regions': title_regions,
                'extracted_regions': title_extracted_regions
            }
        else:
            results['titles_without_regions'].append(title)
    
    # Clean up detection results - remove duplicates
    for term_data in results['detections'].values():
        term_data['titles_detected'] = list(set(term_data['titles_detected']))
        term_data['total_detections'] = len(term_data['titles_detected'])
    
    return results

def spacy_detection(titles: List[str]) -> Dict:
    """Perform spaCy-based geographic detection on titles."""
    
    # Load spaCy model using same approach as the working script
    nlp = None
    model_name = None
    
    try:
        import spacy
        # Try to load models in priority order (same as working script)
        spacy_models_to_try = [
            ("en_core_web_lg", "large"),
            ("en_core_web_md", "medium"), 
            ("en_core_web_sm", "small")
        ]
        
        for model_name_candidate, model_size in spacy_models_to_try:
            try:
                nlp = spacy.load(model_name_candidate)
                model_name = f"{model_name_candidate} ({model_size})"
                logger.info(f"Loaded spaCy {model_name_candidate} ({model_size}) model successfully")
                break
            except OSError:
                continue
        else:
            logger.warning("No spaCy model found")
            return None
    except ImportError:
        logger.warning("spaCy not installed")
        return None
    
    results = {
        'method': 'spacy',
        'model': model_name,
        'total_titles': len(titles),
        'detections': defaultdict(lambda: {
            'canonical_term': '',
            'entity_type': '',
            'titles_detected': [],
            'total_detections': 0
        }),
        'titles_with_regions': {},
        'titles_without_regions': []
    }
    
    logger.info(f"Processing {len(titles)} titles with spaCy model: {model_name}")
    
    for title_idx, title in enumerate(titles):
        if title_idx > 0 and title_idx % 100 == 0:
            logger.info(f"Processed {title_idx}/{len(titles)} titles")
        
        doc = nlp(title)
        title_regions = []
        title_extracted_regions = []
        
        # Extract geographic entities (GPE = Geopolitical entity, LOC = Location)
        for ent in doc.ents:
            if ent.label_ in ['GPE', 'LOC']:
                canonical_term = ent.text
                extracted_text = ent.text
                
                if canonical_term not in title_regions:
                    title_regions.append(canonical_term)
                if extracted_text not in title_extracted_regions:
                    title_extracted_regions.append(extracted_text)
                
                # Update detection results
                if canonical_term not in results['detections']:
                    results['detections'][canonical_term]['canonical_term'] = canonical_term
                    results['detections'][canonical_term]['entity_type'] = ent.label_
                
                results['detections'][canonical_term]['titles_detected'].append(title)
        
        # Store title results
        if title_regions:
            results['titles_with_regions'][title] = {
                'regions': title_regions,
                'extracted_regions': title_extracted_regions
            }
        else:
            results['titles_without_regions'].append(title)
    
    # Clean up detection results - remove duplicates
    for term_data in results['detections'].values():
        term_data['titles_detected'] = list(set(term_data['titles_detected']))
        term_data['total_detections'] = len(term_data['titles_detected'])
    
    # Convert defaultdict to regular dict for JSON serialization
    results['detections'] = dict(results['detections'])
    
    return results

def generate_human_readable_summary(results: Dict, timestamp: str, method: str) -> str:
    """Generate a clean, human-readable summary file."""
    
    summary_lines = []
    
    # Header
    summary_lines.append(f"GEOGRAPHIC ENTITY DETECTION SUMMARY - {method.upper()}")
    summary_lines.append("=" * 80)
    summary_lines.append(f"Analysis Date (PDT): {timestamp}")
    summary_lines.append(f"Method: {method}")
    if 'model' in results:
        summary_lines.append(f"spaCy Model: {results['model']}")
    summary_lines.append(f"Total Titles Analyzed: {results['total_titles']}")
    summary_lines.append("")
    
    # Overall statistics
    titles_with_regions = len(results['titles_with_regions'])
    titles_without_regions = len(results['titles_without_regions'])
    detection_rate = (titles_with_regions / results['total_titles']) * 100
    
    summary_lines.append("OVERALL STATISTICS")
    summary_lines.append("-" * 50)
    summary_lines.append(f"Titles with Geographic Entities: {titles_with_regions}")
    summary_lines.append(f"Titles without Geographic Entities: {titles_without_regions}")
    summary_lines.append(f"Detection Rate: {detection_rate:.2f}%")
    summary_lines.append("")
    
    # Entities found with their titles
    summary_lines.append("ENTITIES DETECTED")
    summary_lines.append("-" * 50)
    
    # Sort entities by detection count
    sorted_entities = sorted(
        [(term, data) for term, data in results['detections'].items() if data['total_detections'] > 0],
        key=lambda x: x[1]['total_detections'],
        reverse=True
    )
    
    for entity, data in sorted_entities:
        summary_lines.append(f"\n{entity} ({data['total_detections']} detections)")
        if method == 'spacy' and 'entity_type' in data:
            summary_lines.append(f"  Entity Type: {data['entity_type']}")
        if method == 'pattern_matching' and 'aliases' in data and data['aliases']:
            summary_lines.append(f"  Aliases: {', '.join(data['aliases'])}")
        
        # List titles (limit to first 10 if many)
        titles = data['titles_detected'][:10]
        for title in titles:
            summary_lines.append(f"    - {title}")
        if len(data['titles_detected']) > 10:
            summary_lines.append(f"    ... and {len(data['titles_detected']) - 10} more titles")
    
    # Titles without any entities
    summary_lines.append(f"\n\nTITLES WITHOUT GEOGRAPHIC ENTITIES ({len(results['titles_without_regions'])})")
    summary_lines.append("-" * 50)
    
    for title in results['titles_without_regions'][:50]:  # Show first 50
        summary_lines.append(f"  - {title}")
    
    if len(results['titles_without_regions']) > 50:
        summary_lines.append(f"  ... and {len(results['titles_without_regions']) - 50} more titles")
    
    return "\n".join(summary_lines)

def compare_detection_methods(pattern_results: Dict, spacy_results: Dict, timestamp: str) -> str:
    """Generate comparative analysis between pattern matching and spaCy."""
    
    analysis_lines = []
    
    # Header
    analysis_lines.append("GEOGRAPHIC DETECTION COMPARISON ANALYSIS")
    analysis_lines.append("=" * 80)
    analysis_lines.append(f"Analysis Date (PDT): {timestamp}")
    analysis_lines.append("")
    
    # Overall comparison
    pattern_detection_rate = (len(pattern_results['titles_with_regions']) / pattern_results['total_titles']) * 100
    spacy_detection_rate = (len(spacy_results['titles_with_regions']) / spacy_results['total_titles']) * 100
    
    analysis_lines.append("OVERALL PERFORMANCE COMPARISON")
    analysis_lines.append("-" * 50)
    analysis_lines.append(f"Pattern Matching Detection Rate: {pattern_detection_rate:.2f}%")
    analysis_lines.append(f"spaCy Detection Rate: {spacy_detection_rate:.2f}%")
    analysis_lines.append(f"Difference: {abs(pattern_detection_rate - spacy_detection_rate):.2f}% {'(Pattern Better)' if pattern_detection_rate > spacy_detection_rate else '(spaCy Better)'}")
    analysis_lines.append("")
    
    # Entity overlap analysis
    pattern_entities = {term for term, data in pattern_results['detections'].items() if data['total_detections'] > 0}
    spacy_entities = {term for term, data in spacy_results['detections'].items() if data['total_detections'] > 0}
    
    common_entities = pattern_entities & spacy_entities
    pattern_only = pattern_entities - spacy_entities
    spacy_only = spacy_entities - pattern_entities
    
    analysis_lines.append("ENTITY DETECTION OVERLAP")
    analysis_lines.append("-" * 50)
    analysis_lines.append(f"Entities found by both methods: {len(common_entities)}")
    analysis_lines.append(f"Entities found only by Pattern Matching: {len(pattern_only)}")
    analysis_lines.append(f"Entities found only by spaCy: {len(spacy_only)}")
    analysis_lines.append("")
    
    # Common entities
    if common_entities:
        analysis_lines.append("ENTITIES FOUND BY BOTH METHODS")
        analysis_lines.append("-" * 30)
        for entity in sorted(common_entities):
            pattern_count = pattern_results['detections'][entity]['total_detections']
            spacy_count = spacy_results['detections'][entity]['total_detections']
            analysis_lines.append(f"  {entity}: Pattern({pattern_count}) vs spaCy({spacy_count})")
        analysis_lines.append("")
    
    # Pattern-only entities
    if pattern_only:
        analysis_lines.append("ENTITIES FOUND ONLY BY PATTERN MATCHING")
        analysis_lines.append("-" * 30)
        for entity in sorted(pattern_only):
            count = pattern_results['detections'][entity]['total_detections']
            analysis_lines.append(f"  {entity}: {count} detections")
        analysis_lines.append("")
    
    # spaCy-only entities
    if spacy_only:
        analysis_lines.append("ENTITIES FOUND ONLY BY SPACY")
        analysis_lines.append("-" * 30)
        for entity in sorted(spacy_only):
            count = spacy_results['detections'][entity]['total_detections']
            analysis_lines.append(f"  {entity}: {count} detections")
        analysis_lines.append("")
    
    # Title-level comparison
    pattern_titles_with_regions = set(pattern_results['titles_with_regions'].keys())
    spacy_titles_with_regions = set(spacy_results['titles_with_regions'].keys())
    
    common_titles = pattern_titles_with_regions & spacy_titles_with_regions
    pattern_only_titles = pattern_titles_with_regions - spacy_titles_with_regions
    spacy_only_titles = spacy_titles_with_regions - pattern_titles_with_regions
    
    analysis_lines.append("TITLE-LEVEL DETECTION COMPARISON")
    analysis_lines.append("-" * 50)
    analysis_lines.append(f"Titles with regions detected by both: {len(common_titles)}")
    analysis_lines.append(f"Titles with regions only by Pattern: {len(pattern_only_titles)}")
    analysis_lines.append(f"Titles with regions only by spaCy: {len(spacy_only_titles)}")
    analysis_lines.append("")
    
    # Show examples of differences
    if pattern_only_titles:
        analysis_lines.append("EXAMPLE TITLES DETECTED ONLY BY PATTERN MATCHING")
        analysis_lines.append("-" * 30)
        for title in list(pattern_only_titles)[:10]:
            regions = pattern_results['titles_with_regions'][title]['regions']
            analysis_lines.append(f"  \"{title}\"")
            analysis_lines.append(f"    Regions: {regions}")
        analysis_lines.append("")
    
    if spacy_only_titles:
        analysis_lines.append("EXAMPLE TITLES DETECTED ONLY BY SPACY")
        analysis_lines.append("-" * 30)
        for title in list(spacy_only_titles)[:10]:
            regions = spacy_results['titles_with_regions'][title]['regions']
            analysis_lines.append(f"  \"{title}\"")
            analysis_lines.append(f"    Regions: {regions}")
        analysis_lines.append("")
    
    return "\n".join(analysis_lines)

def run_database_comparison():
    """Run comprehensive comparison between pattern matching and spaCy detection."""
    
    # Get timestamps
    utc_now = datetime.now(timezone.utc)
    pdt_tz = pytz.timezone('America/Los_Angeles')
    pdt_now = utc_now.astimezone(pdt_tz)
    
    pdt_str = pdt_now.strftime('%Y-%m-%d %H:%M:%S %Z')
    utc_str = utc_now.strftime('%Y-%m-%d %H:%M:%S UTC')
    filename_timestamp = pdt_now.strftime('%Y%m%d_%H%M%S')
    
    print("DATABASE GEOGRAPHIC DETECTION COMPARISON")
    print("=" * 70)
    print(f"Analysis Date (PDT): {pdt_str}")
    print(f"Analysis Date (UTC): {utc_str}")
    print("=" * 70)
    
    # Load data
    patterns = load_geographic_patterns()
    titles = load_database_titles(500)
    
    print(f"\nLoaded {len(patterns)} geographic patterns")
    print(f"Testing with {len(titles)} database titles")
    
    # Run pattern matching detection
    print("\n🔍 Running Pattern Matching Detection...")
    pattern_results = pattern_matching_detection(patterns, titles)
    
    # Save pattern matching results
    pattern_output_file = f"outputs/{filename_timestamp}_pattern_matching_results.json"
    with open(pattern_output_file, 'w', encoding='utf-8') as f:
        json.dump({
            'experiment_info': {
                'timestamp_pdt': pdt_str,
                'timestamp_utc': utc_str,
                'method': 'pattern_matching',
                'total_patterns': len(patterns),
                'total_titles': len(titles)
            },
            'results': pattern_results
        }, f, indent=2, ensure_ascii=False)
    
    # Generate pattern matching summary
    pattern_summary = generate_human_readable_summary(pattern_results, pdt_str, 'pattern_matching')
    pattern_summary_file = f"outputs/{filename_timestamp}_pattern_matching_summary.md"
    with open(pattern_summary_file, 'w', encoding='utf-8') as f:
        f.write(pattern_summary)
    
    print(f"✅ Pattern matching results saved to {pattern_output_file}")
    print(f"✅ Pattern matching summary saved to {pattern_summary_file}")
    
    # Run spaCy detection
    print("\n🧠 Running spaCy Detection...")
    spacy_results = spacy_detection(titles)
    
    if spacy_results:
        # Save spaCy results
        spacy_output_file = f"outputs/{filename_timestamp}_spacy_results.json"
        with open(spacy_output_file, 'w', encoding='utf-8') as f:
            json.dump({
                'experiment_info': {
                    'timestamp_pdt': pdt_str,
                    'timestamp_utc': utc_str,
                    'method': 'spacy',
                    'model': spacy_results['model'],
                    'total_titles': len(titles)
                },
                'results': spacy_results
            }, f, indent=2, ensure_ascii=False)
        
        # Generate spaCy summary
        spacy_summary = generate_human_readable_summary(spacy_results, pdt_str, 'spacy')
        spacy_summary_file = f"outputs/{filename_timestamp}_spacy_summary.md"
        with open(spacy_summary_file, 'w', encoding='utf-8') as f:
            f.write(spacy_summary)
        
        print(f"✅ spaCy results saved to {spacy_output_file}")
        print(f"✅ spaCy summary saved to {spacy_summary_file}")
        
        # Generate comparative analysis
        print("\n📊 Generating Comparative Analysis...")
        comparison_analysis = compare_detection_methods(pattern_results, spacy_results, pdt_str)
        comparison_file = f"outputs/{filename_timestamp}_detection_comparison_analysis.md"
        with open(comparison_file, 'w', encoding='utf-8') as f:
            f.write(comparison_analysis)
        
        print(f"✅ Comparative analysis saved to {comparison_file}")
    
    print("\n" + "=" * 70)
    print("DATABASE COMPARISON COMPLETED")
    print("=" * 70)

if __name__ == "__main__":
    run_database_comparison()