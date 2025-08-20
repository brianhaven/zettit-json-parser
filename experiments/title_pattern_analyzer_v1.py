#!/usr/bin/env python3

import os
import logging
import re
import json
from datetime import datetime
from collections import defaultdict, Counter
from dotenv import load_dotenv
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
from pathlib import Path
import unicodedata

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def connect_to_mongodb():
    """Establish connection to MongoDB Atlas."""
    load_dotenv()
    
    mongodb_uri = os.getenv('MONGODB_URI')
    if not mongodb_uri:
        logger.error("MONGODB_URI not found in environment variables")
        return None, None, None
    
    try:
        client = MongoClient(mongodb_uri, serverSelectionTimeoutMS=10000)
        client.admin.command('ping')
        
        db = client['deathstar']
        collection = db['markets_raw']
        
        logger.info("Successfully connected to MongoDB Atlas")
        return client, db, collection
        
    except (ConnectionFailure, ServerSelectionTimeoutError) as e:
        logger.error(f"Connection failed: {e}")
        return None, None, None

def load_geographic_reference_data():
    """Load comprehensive geographic reference patterns for advanced analysis."""
    # Comprehensive country/region patterns for discovery
    geographic_patterns = {
        'countries': [
            'United States', 'U.S.', 'US', 'USA', 'U.S.A.',
            'United Kingdom', 'U.K.', 'UK', 'Britain', 'Great Britain',
            'Germany', 'France', 'Italy', 'Spain', 'Netherlands', 'Belgium',
            'Switzerland', 'Austria', 'Norway', 'Sweden', 'Denmark', 'Finland',
            'Poland', 'Czech Republic', 'Hungary', 'Romania', 'Bulgaria',
            'Russia', 'China', 'Japan', 'India', 'South Korea', 'Australia',
            'Canada', 'Mexico', 'Brazil', 'Argentina', 'Chile', 'Colombia',
            'South Africa', 'Egypt', 'Nigeria', 'Kenya', 'Morocco',
            'Saudi Arabia', 'UAE', 'Israel', 'Turkey', 'Iran', 'Iraq',
            'Thailand', 'Vietnam', 'Indonesia', 'Malaysia', 'Singapore',
            'Philippines', 'Taiwan', 'Hong Kong', 'New Zealand'
        ],
        'regions': [
            'Europe', 'European', 'North America', 'South America', 'Latin America',
            'Asia', 'Asian', 'Africa', 'African', 'Middle East', 'Far East',
            'Pacific', 'Asia Pacific', 'Asia-Pacific', 'Caribbean', 'Scandinavia',
            'Nordic', 'Baltic', 'Eastern Europe', 'Western Europe', 'Central Europe',
            'Southeast Asia', 'South Asia', 'East Asia', 'Central Asia',
            'North Africa', 'Sub-Saharan Africa', 'West Africa', 'East Africa'
        ],
        'regional_acronyms': [
            'APAC', 'EMEA', 'MEA', 'ASEAN', 'EU', 'NAFTA', 'GCC', 'LATAM',
            'MENA', 'BRICS', 'G7', 'G20', 'OECD', 'EFTA', 'MERCOSUR'
        ],
        'major_cities': [
            'New York', 'London', 'Paris', 'Berlin', 'Tokyo', 'Shanghai',
            'Beijing', 'Mumbai', 'Delhi', 'Bangkok', 'Singapore', 'Sydney',
            'Toronto', 'Vancouver', 'Los Angeles', 'Chicago', 'Houston',
            'Miami', 'Boston', 'San Francisco', 'Seattle', 'Frankfurt',
            'Munich', 'Milan', 'Rome', 'Madrid', 'Barcelona', 'Amsterdam',
            'Stockholm', 'Copenhagen', 'Oslo', 'Helsinki', 'Vienna',
            'Zurich', 'Geneva', 'Dubai', 'Abu Dhabi', 'Riyadh', 'Tel Aviv',
            'Istanbul', 'Cairo', 'Johannesburg', 'Cape Town', 'Lagos',
            'Nairobi', 'São Paulo', 'Buenos Aires', 'Mexico City', 'Bogotá'
        ]
    }
    return geographic_patterns

def analyze_market_terms(titles):
    """Analyze market-related terms and patterns."""
    market_patterns = {
        'standard_market': r'\bmarket\b',
        'market_for': r'\bmarket\s+for\b',
        'market_in': r'\bmarket\s+in\b',
        'market_size': r'\bmarket\s+size\b',
        'market_share': r'\bmarket\s+share\b',
        'market_report': r'\bmarket\s+report\b',
        'market_analysis': r'\bmarket\s+analysis\b',
        'market_trends': r'\bmarket\s+trends\b',
        'market_forecast': r'\bmarket\s+forecast\b',
        'market_outlook': r'\bmarket\s+outlook\b',
        'aftermarket': r'\baftermarket\b',
        'marketplace': r'\bmarketplace\b',
        'market_study': r'\bmarket\s+study\b',
        'market_research': r'\bmarket\s+research\b'
    }
    
    market_analysis = {}
    for pattern_name, pattern in market_patterns.items():
        matches = []
        for title in titles:
            if re.search(pattern, title, re.IGNORECASE):
                matches.append(title)
        market_analysis[pattern_name] = {
            'count': len(matches),
            'examples': matches[:10]  # Store first 10 examples
        }
    
    return market_analysis

def analyze_geographic_entities(titles):
    """Advanced geographic entity analysis using comprehensive pattern matching."""
    geo_data = load_geographic_reference_data()
    
    # Track found entities by category
    geographic_analysis = {
        'countries': defaultdict(list),
        'regions': defaultdict(list), 
        'regional_acronyms': defaultdict(list),
        'major_cities': defaultdict(list),
        'non_geographic_titles': defaultdict(list)
    }
    
    # Country and region boundary patterns for advanced detection
    boundary_patterns = [
        r'\b(?:market\s+(?:for|in)\s+)([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',  # Market for/in X
        r'^([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s*,',  # Leading geographic prefix
        r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+market\b',  # X market
        r'\(([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\)',  # Parenthetical regions
    ]
    
    logger.info("Analyzing geographic entities with advanced pattern matching...")
    
    for i, title in enumerate(titles):
        if i % 1000 == 0:
            logger.info(f"Processed {i}/{len(titles)} titles")
        
        title_lower = title.lower()
        
        # Check known geographic entities
        for category, entities in geo_data.items():
            for entity in entities:
                # Case-insensitive word boundary matching
                pattern = r'\b' + re.escape(entity) + r'\b'
                if re.search(pattern, title, re.IGNORECASE):
                    geographic_analysis[category][entity].append(title)
        
        # Check if title has any geographic content
        has_geographic_content = False
        for category, entities in geo_data.items():
            for entity in entities:
                if re.search(r'\b' + re.escape(entity) + r'\b', title, re.IGNORECASE):
                    has_geographic_content = True
                    break
            if has_geographic_content:
                break
        
        # If no geographic content found, categorize as non-geographic
        if not has_geographic_content:
            geographic_analysis['non_geographic_titles']['no_geographic_content'].append(title)
    
    # Convert to analysis format and count occurrences
    geo_analysis = {}
    entity_counts = Counter()
    
    for category, entities_dict in geographic_analysis.items():
        geo_analysis[category] = {}
        for entity, titles_list in entities_dict.items():
            count = len(titles_list)
            geo_analysis[category][entity] = {
                'count': count,
                'examples': titles_list[:5]
            }
            entity_counts[entity] = count
    
    return geo_analysis, entity_counts

def analyze_regional_acronyms(titles):
    """Analyze regional acronyms and abbreviations."""
    regional_patterns = {
        'APAC': r'\bAPAC\b',
        'EMEA': r'\bEMEA\b',
        'MEA': r'\bMEA\b',
        'ASEAN': r'\bASEAN\b',
        'EU': r'\bEU\b',
        'US': r'\bUS\b',
        'U.S.': r'\bU\.S\.\b',
        'USA': r'\bUSA\b',
        'U.S.A.': r'\bU\.S\.A\.\b',
        'UK': r'\bUK\b',
        'U.K.': r'\bU\.K\.\b',
        'NA': r'\bNA\b(?!\w)',  # Negative lookahead to avoid matching words like "NAnotechnology"
        'LATAM': r'\bLATAM\b',
        'GCC': r'\bGCC\b'
    }
    
    regional_analysis = {}
    for acronym, pattern in regional_patterns.items():
        matches = []
        for title in titles:
            if re.search(pattern, title):
                matches.append(title)
        regional_analysis[acronym] = {
            'count': len(matches),
            'examples': matches[:10]
        }
    
    return regional_analysis

def analyze_title_structures(titles):
    """Analyze common title structures and patterns."""
    patterns = {
        'year_range': r'\b\d{4}[-–]\d{4}\b',
        'single_year': r'\b\d{4}\b',
        'parentheses': r'\([^)]+\)',
        'ampersand': r'\s&\s',
        'comma_separated': r',\s+',
        'hyphenated': r'-\w+',
        'size_and_share': r'\bsize\s+(&|and)\s+share\b',
        'trends_and_analysis': r'\btrends\s+(&|and)\s+analysis\b',
        'forecast_period': r'\bforecast\s+(?:period|to)\b',
        'global_prefix': r'^\s*global\s+',
        'regional_prefix': r'^[^,]+,\s+',  # Captures regional prefixes like "Europe, "
        'industry_suffix': r'\bindustry\b',
        'segment_analysis': r'\bsegment\b',
        'competitive_landscape': r'\bcompetitive\s+landscape\b'
    }
    
    structure_analysis = {}
    for pattern_name, pattern in patterns.items():
        matches = []
        for title in titles:
            if re.search(pattern, title, re.IGNORECASE):
                matches.append(title)
        structure_analysis[pattern_name] = {
            'count': len(matches),
            'percentage': round((len(matches) / len(titles)) * 100, 2),
            'examples': matches[:5]
        }
    
    return structure_analysis

def analyze_topic_indicators(titles):
    """Analyze patterns that indicate the main topic/product."""
    # Common suffixes that typically come after the main topic
    suffix_patterns = [
        r'\bmarket\b.*',
        r'\bindustry\b.*',
        r'\bsize\b.*',
        r'\bshare\b.*',
        r'\banalysis\b.*',
        r'\bforecast\b.*',
        r'\btrends\b.*',
        r'\boutlook\b.*',
        r'\breport\b.*',
        r'\bstudy\b.*',
        r'\bresearch\b.*'
    ]
    
    topic_extraction_examples = []
    
    for title in titles[:100]:  # Analyze first 100 titles as examples
        potential_topic = title
        
        # Try to extract topic by removing common suffixes
        for suffix_pattern in suffix_patterns:
            match = re.search(suffix_pattern, title, re.IGNORECASE)
            if match:
                potential_topic = title[:match.start()].strip()
                break
        
        # Clean up potential topic
        potential_topic = re.sub(r'[,\s]+$', '', potential_topic)  # Remove trailing commas/spaces
        potential_topic = re.sub(r'^\s*global\s+', '', potential_topic, flags=re.IGNORECASE)  # Remove "Global" prefix
        
        topic_extraction_examples.append({
            'original': title,
            'extracted_topic': potential_topic
        })
    
    return topic_extraction_examples

def analyze_complex_patterns(titles):
    """Analyze complex patterns that require special handling."""
    complex_patterns = {
        'multiple_regions': {
            'pattern': r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s*,\s*([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s*(?:,\s*(?:and\s+)?([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*))?',
            'description': 'Titles with multiple comma-separated regions',
            'examples': []
        },
        'region_and_conjunction': {
            'pattern': r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+and\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
            'description': 'Regions connected with "and"',
            'examples': []
        },
        'region_ampersand': {
            'pattern': r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+&\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
            'description': 'Regions connected with "&"',
            'examples': []
        },
        'parenthetical_acronyms': {
            'pattern': r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s*\(([A-Z]+)\)',
            'description': 'Terms with acronyms in parentheses',
            'examples': []
        },
        'market_for_pattern': {
            'pattern': r'([^,]+?)\s+market\s+for\s+([^,]+)',
            'description': 'Market for X pattern requiring special handling',
            'examples': []
        },
        'market_in_pattern': {
            'pattern': r'([^,]+?)\s+market\s+in\s+([^,]+)',
            'description': 'Market in X pattern requiring special handling',
            'examples': []
        }
    }
    
    for title in titles:
        for pattern_name, pattern_info in complex_patterns.items():
            matches = re.findall(pattern_info['pattern'], title, re.IGNORECASE)
            if matches and len(pattern_info['examples']) < 10:
                pattern_info['examples'].append({
                    'title': title,
                    'matches': matches
                })
    
    return complex_patterns

def analyze_topic_extraction_patterns(titles):
    """Advanced topic extraction pattern analysis."""
    logger.info("Analyzing topic extraction patterns...")
    
    # Common market report suffixes to remove
    suffix_patterns = [
        r'\s+market\s+.*$',
        r'\s+industry\s+.*$', 
        r'\s+size\s+.*$',
        r'\s+share\s+.*$',
        r'\s+analysis\s+.*$',
        r'\s+forecast\s+.*$',
        r'\s+trends\s+.*$',
        r'\s+outlook\s+.*$',
        r'\s+report\s+.*$',
        r'\s+study\s+.*$',
        r'\s+research\s+.*$'
    ]
    
    topic_extraction_results = {
        'successful_extractions': [],
        'challenging_cases': [],
        'prefix_patterns': Counter(),
        'suffix_patterns': Counter(),
        'topic_complexity_analysis': {},
        'potential_topics': Counter()
    }
    
    for i, title in enumerate(titles[:500]):  # Analyze sample for performance
        original_title = title
        
        # Remove leading geographic indicators
        geographic_prefixes = [
            r'^\s*global\s+',
            r'^[^,]+,\s+',  # Regional prefix like "Europe, "
            r'^\s*worldwide\s+',
            r'^\s*international\s+'
        ]
        
        cleaned_title = title
        detected_prefix = None
        for prefix_pattern in geographic_prefixes:
            match = re.search(prefix_pattern, cleaned_title, re.IGNORECASE)
            if match:
                detected_prefix = match.group()
                topic_extraction_results['prefix_patterns'][detected_prefix.strip()] += 1
                cleaned_title = re.sub(prefix_pattern, '', cleaned_title, flags=re.IGNORECASE).strip()
                break
        
        # Extract topic by removing suffixes
        potential_topic = cleaned_title
        detected_suffix = None
        for suffix_pattern in suffix_patterns:
            match = re.search(suffix_pattern, potential_topic, re.IGNORECASE)
            if match:
                detected_suffix = match.group()
                topic_extraction_results['suffix_patterns'][detected_suffix.strip()] += 1
                potential_topic = re.sub(suffix_pattern, '', potential_topic, flags=re.IGNORECASE).strip()
                break
        
        # Clean up extracted topic
        potential_topic = re.sub(r'[,\s]+$', '', potential_topic)  # Remove trailing commas/spaces
        potential_topic = re.sub(r'^\s*', '', potential_topic)  # Remove leading spaces
        
        # Analyze complexity
        complexity_score = 0
        complexity_factors = []
        
        if '(' in potential_topic and ')' in potential_topic:
            complexity_score += 1
            complexity_factors.append('parenthetical_content')
        
        if '&' in potential_topic or ' and ' in potential_topic.lower():
            complexity_score += 1
            complexity_factors.append('compound_topic')
        
        if len(potential_topic.split()) > 5:
            complexity_score += 1
            complexity_factors.append('long_topic')
        
        if re.search(r'\d+', potential_topic):
            complexity_score += 1
            complexity_factors.append('contains_numbers')
        
        result = {
            'original': original_title,
            'detected_prefix': detected_prefix,
            'detected_suffix': detected_suffix,
            'extracted_topic': potential_topic,
            'complexity_score': complexity_score,
            'complexity_factors': complexity_factors
        }
        
        topic_extraction_results['potential_topics'][potential_topic] += 1
        
        if complexity_score <= 1 and len(potential_topic) > 0:
            topic_extraction_results['successful_extractions'].append(result)
        else:
            topic_extraction_results['challenging_cases'].append(result)
    
    return topic_extraction_results

def analyze_business_terminology(titles):
    """Analyze business and industry terminology patterns."""
    logger.info("Analyzing business terminology patterns...")
    
    # Business term categories
    business_terms = {
        'industry_types': [
            'automotive', 'healthcare', 'pharmaceutical', 'technology', 'financial',
            'telecommunications', 'energy', 'oil', 'gas', 'mining', 'agriculture',
            'food', 'beverage', 'retail', 'fashion', 'textile', 'construction',
            'aerospace', 'defense', 'marine', 'shipping', 'logistics', 'transportation'
        ],
        'product_categories': [
            'software', 'hardware', 'equipment', 'machinery', 'devices', 'systems',
            'solutions', 'services', 'components', 'materials', 'chemicals',
            'pharmaceuticals', 'drugs', 'vaccines', 'instruments', 'tools'
        ],
        'market_descriptors': [
            'global', 'regional', 'local', 'domestic', 'international', 'worldwide',
            'emerging', 'developing', 'mature', 'niche', 'mainstream', 'premium',
            'budget', 'high-end', 'mid-range', 'enterprise', 'consumer', 'commercial'
        ],
        'business_metrics': [
            'size', 'share', 'growth', 'revenue', 'sales', 'volume', 'value',
            'demand', 'supply', 'capacity', 'production', 'consumption',
            'penetration', 'adoption', 'utilization'
        ]
    }
    
    terminology_analysis = {}
    
    for category, terms in business_terms.items():
        terminology_analysis[category] = {}
        for term in terms:
            matches = []
            pattern = r'\b' + re.escape(term) + r'\b'
            for title in titles:
                if re.search(pattern, title, re.IGNORECASE):
                    matches.append(title)
            
            if matches:
                terminology_analysis[category][term] = {
                    'count': len(matches),
                    'examples': matches[:3]
                }
    
    return terminology_analysis

def analyze_title_complexity_distribution(titles):
    """Analyze the complexity distribution of titles for processing strategy."""
    logger.info("Analyzing title complexity distribution...")
    
    complexity_analysis = {
        'length_distribution': Counter(),
        'word_count_distribution': Counter(),
        'punctuation_complexity': Counter(),
        'pattern_complexity': {
            'simple': [],       # Basic "X Market" patterns
            'moderate': [],     # Regional prefix + topic + market
            'complex': [],      # Multiple regions, complex conjunctions
            'very_complex': []  # Nested parentheses, multiple conjunctions
        }
    }
    
    for title in titles:
        # Basic metrics
        char_length = len(title)
        word_count = len(title.split())
        
        complexity_analysis['length_distribution'][f"{char_length//20*20}-{char_length//20*20+19}"] += 1
        complexity_analysis['word_count_distribution'][word_count] += 1
        
        # Punctuation complexity
        punct_score = 0
        punct_score += title.count(',')
        punct_score += title.count('&') * 2
        punct_score += title.count('(') + title.count(')')
        punct_score += title.count('-') if title.count('-') > 2 else 0
        
        complexity_analysis['punctuation_complexity'][min(punct_score, 10)] += 1
        
        # Pattern complexity assessment
        complexity_score = 0
        
        # Geographic complexity
        geographic_indicators = len(re.findall(r'\b(?:market\s+(?:for|in)|^[^,]+,)', title, re.IGNORECASE))
        complexity_score += geographic_indicators
        
        # Conjunction complexity  
        conjunctions = len(re.findall(r'\b(?:and|&|or)\b', title, re.IGNORECASE))
        complexity_score += conjunctions
        
        # Parenthetical complexity
        parentheses = title.count('(')
        complexity_score += parentheses
        
        # Categorize by complexity
        if complexity_score == 0:
            complexity_analysis['pattern_complexity']['simple'].append(title)
        elif complexity_score <= 2:
            complexity_analysis['pattern_complexity']['moderate'].append(title)
        elif complexity_score <= 4:
            complexity_analysis['pattern_complexity']['complex'].append(title)
        else:
            complexity_analysis['pattern_complexity']['very_complex'].append(title)
    
    # Limit examples for output size
    for category in complexity_analysis['pattern_complexity']:
        examples = complexity_analysis['pattern_complexity'][category]
        complexity_analysis['pattern_complexity'][category] = {
            'count': len(examples),
            'percentage': round(len(examples) / len(titles) * 100, 2),
            'examples': examples[:10]
        }
    
    return complexity_analysis

def analyze_extraction_challenges(titles):
    """Identify specific extraction challenges that need special handling."""
    logger.info("Analyzing extraction challenges...")
    
    challenge_patterns = {
        'ambiguous_market_terms': {
            'description': 'Titles where "market" could be part of topic or descriptor',
            'pattern': r'\b\w+market\b',  # e.g., "Aftermarket", "Supermarket"
            'examples': []
        },
        'nested_geographic_info': {
            'description': 'Multiple levels of geographic specification',
            'pattern': r'([A-Z][a-z]+)\s*,\s*([A-Z][a-z]+)\s*,\s*([A-Z][a-z]+)',
            'examples': []
        },
        'technical_acronyms_vs_regions': {
            'description': 'Acronyms that could be technical terms or regions',
            'pattern': r'\b([A-Z]{2,6})\b',
            'examples': []
        },
        'compound_topics_with_conjunctions': {
            'description': 'Topics with multiple parts connected by and/or',
            'pattern': r'([A-Za-z\s]+)\s+(?:and|&|or)\s+([A-Za-z\s]+)\s+market',
            'examples': []
        },
        'market_for_in_disambiguation': {
            'description': 'Market for/in patterns requiring context analysis',
            'pattern': r'market\s+(?:for|in)\s+([^,]+)',
            'examples': []
        },
        'regional_economic_blocks': {
            'description': 'Economic/trade regions vs geographic regions',
            'pattern': r'\b(ASEAN|NAFTA|EU|MERCOSUR|GCC|BRICS)\b',
            'examples': []
        }
    }
    
    for title in titles:
        for challenge_name, challenge_info in challenge_patterns.items():
            matches = re.findall(challenge_info['pattern'], title, re.IGNORECASE)
            if matches and len(challenge_info['examples']) < 15:
                challenge_info['examples'].append({
                    'title': title,
                    'matches': matches
                })
    
    # Add counts
    for challenge_name, challenge_info in challenge_patterns.items():
        challenge_info['total_examples'] = len(challenge_info['examples'])
    
    return challenge_patterns

def generate_analysis_report(client, collection):
    """Generate comprehensive analysis report."""
    logger.info("Starting title pattern analysis...")
    
    # Get sample of titles for analysis
    logger.info("Fetching report_title_short values...")
    cursor = collection.find({}, {"report_title_short": 1, "_id": 0})
    
    titles = []
    total_docs = 0
    
    for doc in cursor:
        total_docs += 1
        if "report_title_short" in doc and doc["report_title_short"]:
            titles.append(doc["report_title_short"])
    
    logger.info(f"Found {len(titles)} non-empty titles out of {total_docs} total documents")
    
    if not titles:
        logger.error("No titles found for analysis")
        return None
    
    # Perform comprehensive analyses
    logger.info("Analyzing market terms...")
    market_analysis = analyze_market_terms(titles)
    
    logger.info("Analyzing geographic entities...")
    geo_analysis, geo_counts = analyze_geographic_entities(titles)
    
    logger.info("Analyzing regional acronyms...")
    regional_analysis = analyze_regional_acronyms(titles)
    
    logger.info("Analyzing title structures...")
    structure_analysis = analyze_title_structures(titles)
    
    logger.info("Analyzing basic topic extraction patterns...")
    topic_examples = analyze_topic_indicators(titles)
    
    logger.info("Analyzing advanced topic extraction patterns...")
    advanced_topic_analysis = analyze_topic_extraction_patterns(titles)
    
    logger.info("Analyzing business terminology...")
    business_terminology = analyze_business_terminology(titles)
    
    logger.info("Analyzing title complexity distribution...")
    complexity_distribution = analyze_title_complexity_distribution(titles)
    
    logger.info("Analyzing extraction challenges...")
    extraction_challenges = analyze_extraction_challenges(titles)
    
    logger.info("Analyzing complex patterns...")
    complex_patterns = analyze_complex_patterns(titles)
    
    # Compile comprehensive analysis report
    analysis_report = {
        'metadata': {
            'analysis_date': datetime.utcnow().isoformat(),
            'total_documents': total_docs,
            'titles_analyzed': len(titles),
            'analysis_method': 'advanced_pattern_matching',
            'geographic_reference_entities': sum(len(entities) for entities in load_geographic_reference_data().values())
        },
        'market_term_analysis': market_analysis,
        'geographic_entity_analysis': {
            'total_categories': len(geo_analysis),
            'entities_by_category': {cat: len(entities) for cat, entities in geo_analysis.items()},
            'top_entities': dict(geo_counts.most_common(50)),
            'detailed_analysis': geo_analysis
        },
        'regional_acronym_analysis': regional_analysis,
        'title_structure_analysis': structure_analysis,
        'basic_topic_extraction_examples': topic_examples,
        'advanced_topic_extraction_analysis': advanced_topic_analysis,
        'business_terminology_analysis': business_terminology,
        'title_complexity_distribution': complexity_distribution,
        'extraction_challenges': extraction_challenges,
        'complex_pattern_analysis': complex_patterns,
        'sample_titles': titles[:50]  # Store sample titles for reference
    }
    
    logger.info("Analysis complete")
    return analysis_report

def save_analysis_report(report, output_file):
    """Save analysis report to JSON file."""
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        logger.info(f"Analysis report saved to {output_file}")
    except Exception as e:
        logger.error(f"Failed to save report: {e}")

def create_human_readable_summary(report, output_file):
    """Create a human-readable markdown summary of the analysis."""
    summary_lines = [
        "# Title Pattern Analysis Summary",
        f"**Analysis Date:** {report['metadata']['analysis_date']}",
        f"**Total Documents:** {report['metadata']['total_documents']}",
        f"**Titles Analyzed:** {report['metadata']['titles_analyzed']}",
        f"**Analysis Method:** {report['metadata']['analysis_method']}",
        "",
        "## Market Term Analysis",
        ""
    ]
    
    # Market terms summary
    for term, data in report['market_term_analysis'].items():
        if data['count'] > 0:
            summary_lines.append(f"- **{term}**: {data['count']} occurrences")
            if data['examples']:
                summary_lines.append(f"  - Example: \"{data['examples'][0]}\"")
    
    summary_lines.extend([
        "",
        "## Geographic Entity Analysis",
        f"**Total unique entities found:** {report['geographic_entity_analysis']['entities_found']}",
        "",
        "**Top 20 Geographic Entities:**"
    ])
    
    # Top geographic entities
    for entity, count in list(report['geographic_entity_analysis']['top_entities'].items())[:20]:
        summary_lines.append(f"- {entity}: {count} occurrences")
    
    summary_lines.extend([
        "",
        "## Regional Acronym Analysis",
        ""
    ])
    
    # Regional acronyms
    for acronym, data in report['regional_acronym_analysis'].items():
        if data['count'] > 0:
            summary_lines.append(f"- **{acronym}**: {data['count']} occurrences")
    
    summary_lines.extend([
        "",
        "## Title Structure Analysis",
        ""
    ])
    
    # Structure patterns
    for pattern, data in report['title_structure_analysis'].items():
        summary_lines.append(f"- **{pattern}**: {data['count']} occurrences ({data['percentage']}%)")
    
    summary_lines.extend([
        "",
        "## Complex Pattern Analysis",
        ""
    ])
    
    # Complex patterns
    for pattern_name, pattern_data in report['complex_pattern_analysis'].items():
        example_count = len(pattern_data['examples'])
        if example_count > 0:
            summary_lines.append(f"- **{pattern_name}**: {example_count} examples found")
            summary_lines.append(f"  - Description: {pattern_data['description']}")
            if pattern_data['examples']:
                summary_lines.append(f"  - Example: \"{pattern_data['examples'][0]['title']}\"")
    
    # Write summary to file
    summary_content = "\n".join(summary_lines)
    summary_file = output_file.replace('.json', '_summary.md')
    
    try:
        with open(summary_file, 'w', encoding='utf-8') as f:
            f.write(summary_content)
        logger.info(f"Human-readable summary saved to {summary_file}")
    except Exception as e:
        logger.error(f"Failed to save summary: {e}")

def main():
    """Main function to run the analysis."""
    print("MongoDB Title Pattern Analysis")
    print("=" * 50)
    
    # Connect to MongoDB
    client, db, collection = connect_to_mongodb()
    if not client:
        print("❌ Failed to connect to MongoDB")
        return
    
    try:
        # Generate analysis report
        report = generate_analysis_report(client, collection)
        if not report:
            print("❌ Failed to generate analysis report")
            return
        
        # Save report
        output_dir = Path("documentation")
        output_dir.mkdir(exist_ok=True)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_file = output_dir / f"title_pattern_analysis_{timestamp}.json"
        
        save_analysis_report(report, output_file)
        create_human_readable_summary(report, str(output_file))
        
        # Print summary
        print("\n" + "=" * 60)
        print("📊 ANALYSIS SUMMARY")
        print("=" * 60)
        print(f"Total documents analyzed: {report['metadata']['total_documents']}")
        print(f"Titles with content: {report['metadata']['titles_analyzed']}")
        print(f"Geographic categories analyzed: {report['geographic_entity_analysis']['total_categories']}")
        print(f"Business terminology categories: {len(report['business_terminology_analysis'])}")
        print(f"Extraction challenges identified: {len(report['extraction_challenges'])}")
        print(f"Analysis saved to: {output_file}")
        print(f"Summary saved to: {str(output_file).replace('.json', '_summary.md')}")
        print("\n✅ Advanced title pattern analysis completed successfully!")
        
    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        print(f"❌ Analysis failed: {e}")
    
    finally:
        if client:
            client.close()

if __name__ == "__main__":
    main()