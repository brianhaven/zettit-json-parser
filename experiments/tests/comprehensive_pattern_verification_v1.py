#!/usr/bin/env python3

"""
Comprehensive Pattern Verification v1.0
Tests ALL geographic patterns from MongoDB to ensure proper detection
"""

import os
import re
import json
import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple, Any
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

def test_pattern_detection(patterns: List[Dict], test_titles: List[str]) -> Dict:
    """Test all patterns against test titles and return results."""
    
    results = {
        'total_patterns': len(patterns),
        'total_test_titles': len(test_titles),
        'pattern_results': {},
        'detection_summary': {},
        'problem_patterns': [],
        'title_extraction_results': {}  # New: per-title extraction results
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
        results['pattern_results'][term] = {
            'term': term,
            'aliases': aliases,
            'priority': priority,
            'detections': [],
            'alias_detections': {},
            'total_detections': 0,
            'titles_detected': set()
        }
    
    priority_order = sorted(terms_by_priority.keys())
    
    logger.info(f"Testing {len(patterns)} patterns across {len(test_titles)} titles")
    
    # Test each title against all patterns
    for title_idx, title in enumerate(test_titles):
        if title_idx > 0 and title_idx % 50 == 0:
            logger.info(f"Processed {title_idx}/{len(test_titles)} titles")
        
        title_detections = []
        matched_positions = set()
        
        # Initialize per-title results with dual extraction tracking
        results['title_extraction_results'][title] = {
            'regions': [],           # Resolved canonical terms
            'extracted_regions': [], # Literal detected text
            'detection_details': []  # Full detection metadata
        }
        
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
                        
                        detection = {
                            'term': term,
                            'matched_text': match.group(),
                            'start_pos': start_pos,
                            'end_pos': end_pos,
                            'source': 'term',
                            'priority': priority
                        }
                        
                        title_detections.append(detection)
                        
                        # Store in dual extraction format
                        if term not in results['title_extraction_results'][title]['regions']:
                            results['title_extraction_results'][title]['regions'].append(term)
                        if match.group() not in results['title_extraction_results'][title]['extracted_regions']:
                            results['title_extraction_results'][title]['extracted_regions'].append(match.group())
                        
                        results['title_extraction_results'][title]['detection_details'].append({
                            'canonical_term': term,
                            'detected_text': match.group(),
                            'source': 'term',
                            'priority': priority,
                            'start_pos': start_pos,
                            'end_pos': end_pos
                        })
                        
                        results['pattern_results'][term]['detections'].append({
                            'title': title,
                            'matched_text': match.group(),
                            'start_pos': start_pos,
                            'end_pos': end_pos
                        })
                        results['pattern_results'][term]['titles_detected'].add(title)
                        results['pattern_results'][term]['total_detections'] += 1
                
                except re.error as e:
                    logger.error(f"Regex error for term '{term}': {e}")
                    results['problem_patterns'].append({
                        'term': term,
                        'error': f"Regex error: {e}",
                        'pattern': pattern
                    })
        
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
                    
                    detection = {
                        'term': canonical_term,
                        'alias': alias,
                        'matched_text': match.group(),
                        'start_pos': start_pos,
                        'end_pos': end_pos,
                        'source': 'alias'
                    }
                    
                    title_detections.append(detection)
                    
                    # Store in dual extraction format
                    if canonical_term not in results['title_extraction_results'][title]['regions']:
                        results['title_extraction_results'][title]['regions'].append(canonical_term)
                    if match.group() not in results['title_extraction_results'][title]['extracted_regions']:
                        results['title_extraction_results'][title]['extracted_regions'].append(match.group())
                    
                    results['title_extraction_results'][title]['detection_details'].append({
                        'canonical_term': canonical_term,
                        'detected_text': match.group(),
                        'source': 'alias',
                        'alias_used': alias,
                        'start_pos': start_pos,
                        'end_pos': end_pos
                    })
                    
                    # Track alias detections
                    if alias not in results['pattern_results'][canonical_term]['alias_detections']:
                        results['pattern_results'][canonical_term]['alias_detections'][alias] = []
                    
                    results['pattern_results'][canonical_term]['alias_detections'][alias].append({
                        'title': title,
                        'matched_text': match.group(),
                        'start_pos': start_pos,
                        'end_pos': end_pos
                    })
                    results['pattern_results'][canonical_term]['titles_detected'].add(title)
                    results['pattern_results'][canonical_term]['total_detections'] += 1
            
            except re.error as e:
                logger.error(f"Regex error for alias '{alias}': {e}")
                results['problem_patterns'].append({
                    'alias': alias,
                    'canonical_term': canonical_term,
                    'error': f"Regex error: {e}",
                    'pattern': pattern
                })
    
    # Convert sets to lists for JSON serialization
    for term_result in results['pattern_results'].values():
        term_result['titles_detected'] = list(term_result['titles_detected'])
    
    # Generate summary statistics
    total_detections = 0
    patterns_with_detections = 0
    patterns_with_alias_detections = 0
    
    for term, data in results['pattern_results'].items():
        if data['total_detections'] > 0:
            patterns_with_detections += 1
        if data['alias_detections']:
            patterns_with_alias_detections += 1
        total_detections += data['total_detections']
    
    results['detection_summary'] = {
        'total_detections': total_detections,
        'patterns_with_detections': patterns_with_detections,
        'patterns_with_alias_detections': patterns_with_alias_detections,
        'patterns_without_detections': len(patterns) - patterns_with_detections,
        'detection_rate_by_pattern': round((patterns_with_detections / len(patterns)) * 100, 2),
        'avg_detections_per_pattern': round(total_detections / len(patterns), 2)
    }
    
    return results

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

def create_test_titles() -> List[str]:
    """Create comprehensive test titles covering various scenarios."""
    
    test_titles = [
        # Basic geographic terms
        "Global Technology Market Report 2025",
        "Europe Automotive Industry Analysis",
        "North America Healthcare Market Size",
        "Asia Pacific Manufacturing Report",
        "Middle East Energy Market Forecast",
        "Latin America Economic Overview",
        "Africa Development Report",
        "APAC Technology Trends",
        "EMEA Market Analysis",
        "MEA Regional Study",
        
        # Country-specific
        "United States Market Report",
        "U.S. Technology Sector Analysis",
        "U.S. Onshore Drilling Fluids Market Size, Industry Report, 2018-2025",
        "US Manufacturing Report",
        "USA Economic Forecast",
        "United Kingdom Market Study",
        "U.K. Financial Services Report",
        "UK Economic Analysis",
        "Germany Industrial Report",
        "France Market Overview",
        "China Technology Market",
        "India Economic Report",
        "Japan Manufacturing Study",
        "Canada Market Analysis",
        "Australia Resource Report",
        "Brazil Economic Forecast",
        "Mexico Market Study",
        "Saudi Arabia Energy Report",
        "UAE Financial Analysis",
        "U.A.E. Technology Report",
        "Indonesia Market Study",
        "South Korea Technology Report",
        "Singapore Financial Market",
        "Philippines Economic Report",
        "Malaysia Market Analysis",
        
        # Complex compound regions
        "Asia Pacific and India Market Report",
        "Europe, Middle East and Africa Analysis",
        "Middle East and Africa Economic Study",
        "Southern Europe and Middle East Report",
        "South East Asia Market Analysis",
        "Southeast Asia Economic Report",
        "Central America Market Study",
        "Eastern Europe Economic Report",
        "Western Europe Market Analysis",
        "Sub-Saharan Africa Development Report",
        "North Africa Economic Study",
        "West Africa Market Report",
        "East Africa Economic Analysis",
        
        # Acronyms and abbreviations
        "ASEAN Economic Community Report",
        "GCC Market Analysis",
        "MENA Regional Study",
        "EU Trade Report",
        "European Union Market Analysis",
        "European Trade Study",
        "Association of Southeast Asian Nations Report",
        "United Arab Emirates Market",
        
        # Multiple regions in one title
        "Europe and North America Market Comparison",
        "Asia Pacific, EMEA Market Analysis",
        "Global study covering USA, Europe, and Asia",
        "Multi-regional analysis: US, UK, Germany, France",
        "Worldwide report including China, India, Japan",
        
        # Edge cases and potential conflicts
        "America First Policy Report",  # Should detect "America" but not confuse with "North America"
        "European Union Trade with Asia Pacific",  # Multiple regions
        "Middle East conflicts with East Asia trade",  # "East" appears in both
        "North American and South American markets",  # Similar compound terms
        "Pacific Rim countries analysis",  # Should detect "Pacific"
        "Caribbean and Central America study",  # Multiple regions
        "Americas-wide economic report",  # "Americas" vs "America"
        
        # Titles without geographic references (should not detect anything)
        "Blockchain Technology Market Report",
        "Artificial Intelligence Industry Analysis",
        "Renewable Energy Sector Study",
        "Pharmaceutical Research Report",
        "Automotive Technology Trends",
        "Healthcare Innovation Report",
        "Financial Services Analysis",
        "E-commerce Market Study",
        "Cybersecurity Industry Report",
        "Clean Energy Technology Analysis"
    ]
    
    logger.info(f"Created {len(test_titles)} test titles")
    return test_titles

def run_comprehensive_verification():
    """Run comprehensive verification of all geographic patterns."""
    
    # Get timestamps
    utc_now = datetime.now(timezone.utc)
    pdt_tz = pytz.timezone('America/Los_Angeles')
    pdt_now = utc_now.astimezone(pdt_tz)
    
    pdt_str = pdt_now.strftime('%Y-%m-%d %H:%M:%S %Z')
    utc_str = utc_now.strftime('%Y-%m-%d %H:%M:%S UTC')
    filename_timestamp = pdt_now.strftime('%Y%m%d_%H%M%S')
    
    print("COMPREHENSIVE GEOGRAPHIC PATTERN VERIFICATION")
    print("=" * 70)
    print(f"Analysis Date (PDT): {pdt_str}")
    print(f"Analysis Date (UTC): {utc_str}")
    print("=" * 70)
    
    # Load patterns and create test titles
    patterns = load_geographic_patterns()
    test_titles = create_test_titles()
    
    print(f"\\nLoaded {len(patterns)} geographic patterns")
    print(f"Testing with {len(test_titles)} test titles")
    
    # Run verification
    results = test_pattern_detection(patterns, test_titles)
    
    # Display results
    print("\\nVERIFICATION RESULTS")
    print("-" * 50)
    print(f"Total Patterns Tested: {results['total_patterns']}")
    print(f"Patterns with Detections: {results['detection_summary']['patterns_with_detections']}")
    print(f"Patterns without Detections: {results['detection_summary']['patterns_without_detections']}")
    print(f"Pattern Detection Rate: {results['detection_summary']['detection_rate_by_pattern']}%")
    print(f"Total Detections: {results['detection_summary']['total_detections']}")
    print(f"Average Detections per Pattern: {results['detection_summary']['avg_detections_per_pattern']}")
    
    # Show patterns with most detections
    print("\\nTOP PERFORMING PATTERNS")
    print("-" * 50)
    pattern_performance = [(term, data['total_detections']) for term, data in results['pattern_results'].items()]
    pattern_performance.sort(key=lambda x: x[1], reverse=True)
    
    for i, (term, count) in enumerate(pattern_performance[:10]):
        print(f"{i+1:2d}. {term}: {count} detections")
    
    # Show problem patterns
    if results['problem_patterns']:
        print("\\nPROBLEM PATTERNS (REGEX ERRORS)")
        print("-" * 50)
        for problem in results['problem_patterns']:
            if 'term' in problem:
                print(f"Term: {problem['term']} - {problem['error']}")
            else:
                print(f"Alias: {problem['alias']} -> {problem['canonical_term']} - {problem['error']}")
    
    # Show patterns with no detections
    no_detection_patterns = [term for term, data in results['pattern_results'].items() if data['total_detections'] == 0]
    if no_detection_patterns:
        print(f"\\nPATTERNS WITH NO DETECTIONS ({len(no_detection_patterns)})")
        print("-" * 50)
        for term in no_detection_patterns[:20]:  # Show first 20
            aliases = results['pattern_results'][term]['aliases']
            alias_str = f" (aliases: {', '.join(aliases)})" if aliases else ""
            print(f"  {term}{alias_str}")
        if len(no_detection_patterns) > 20:
            print(f"  ... and {len(no_detection_patterns) - 20} more")
    
    # Show alias detection results
    print("\\nALIAS DETECTION RESULTS")
    print("-" * 50)
    alias_patterns = [term for term, data in results['pattern_results'].items() if data['alias_detections']]
    for term in alias_patterns[:10]:  # Show first 10
        data = results['pattern_results'][term]
        print(f"{term}:")
        for alias, detections in data['alias_detections'].items():
            print(f"  {alias}: {len(detections)} detections")
    
    # Show dual extraction examples
    print("\\nDUAL EXTRACTION EXAMPLES")
    print("-" * 50)
    titles_with_regions = [title for title, data in results['title_extraction_results'].items() 
                          if data['regions'] or data['extracted_regions']]
    
    for i, title in enumerate(titles_with_regions[:10]):  # Show first 10 examples
        data = results['title_extraction_results'][title]
        print(f"\\n{i+1}. Title: \"{title}\"")
        print(f"   Regions (canonical): {data['regions']}")
        print(f"   Extracted Regions (literal): {data['extracted_regions']}")
        
        # Show detection details for this title
        if data['detection_details']:
            print("   Detection Details:")
            for detail in data['detection_details']:
                if detail['source'] == 'alias':
                    print(f"     - Found '{detail['detected_text']}' → resolves to '{detail['canonical_term']}' (via alias '{detail['alias_used']}')")
                else:
                    print(f"     - Found '{detail['detected_text']}' → matches term '{detail['canonical_term']}' directly")
    
    # Summary of dual extraction statistics
    titles_with_extractions = len([t for t, d in results['title_extraction_results'].items() if d['regions']])
    total_canonical_regions = sum(len(d['regions']) for d in results['title_extraction_results'].values())
    total_literal_regions = sum(len(d['extracted_regions']) for d in results['title_extraction_results'].values())
    
    print(f"\\nDUAL EXTRACTION SUMMARY")
    print("-" * 50)
    print(f"Titles with Geographic Detections: {titles_with_extractions}/{len(test_titles)}")
    print(f"Total Canonical Regions Identified: {total_canonical_regions}")
    print(f"Total Literal Text Extractions: {total_literal_regions}")
    print(f"Average Regions per Title (with regions): {total_canonical_regions/max(titles_with_extractions,1):.2f}")
    print(f"Average Literal Extractions per Title (with regions): {total_literal_regions/max(titles_with_extractions,1):.2f}")
    
    # Test specific problematic patterns
    print("\\nTESTING SPECIFIC PROBLEM PATTERNS")
    print("-" * 50)
    
    # Test U.S. detection specifically with dual extraction
    us_test_title = "U.S. Onshore Drilling Fluids Market Size, Industry Report, 2018-2025"
    us_pattern = create_improved_pattern("U.S.")
    us_matches = list(re.finditer(us_pattern, us_test_title, re.IGNORECASE))
    print(f"U.S. dual extraction test:")
    print(f"  Title: '{us_test_title}'")
    print(f"  Pattern: '{us_pattern}'")
    print(f"  Matches: {len(us_matches)}")
    if us_matches:
        print(f"  Detected Text (literal): '{us_matches[0].group()}'")
        print(f"  Canonical Term (resolved): 'United States'")
        print(f"  Position: {us_matches[0].start()}-{us_matches[0].end()}")
        print(f"  Expected Result:")
        print(f"    - regions: ['United States']")
        print(f"    - extracted_regions: ['U.S.']")
    
    # Test EU detection
    eu_test_title = "EU Trade Policy Report"
    eu_pattern = create_improved_pattern("EU")
    eu_matches = list(re.finditer(eu_pattern, eu_test_title, re.IGNORECASE))
    print(f"\\nEU detection test:")
    print(f"  Title: '{eu_test_title}'")
    print(f"  Pattern: '{eu_pattern}'")
    print(f"  Matches: {len(eu_matches)}")
    if eu_matches:
        print(f"  Found: '{eu_matches[0].group()}' at {eu_matches[0].start()}-{eu_matches[0].end()}")
    
    # Save detailed results
    output_file = f"outputs/{filename_timestamp}_comprehensive_pattern_verification.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump({
            'experiment_info': {
                'timestamp_pdt': pdt_str,
                'timestamp_utc': utc_str,
                'total_patterns': len(patterns),
                'total_test_titles': len(test_titles)
            },
            'results': results
        }, f, indent=2, ensure_ascii=False)
    
    print(f"\\n✅ Detailed results saved to {output_file}")
    print("\\n" + "=" * 70)
    print("VERIFICATION COMPLETED")
    print("=" * 70)

if __name__ == "__main__":
    run_comprehensive_verification()