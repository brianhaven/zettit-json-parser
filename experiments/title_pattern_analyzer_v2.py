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
    """Load comprehensive geographic reference patterns."""
    return {
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

def analyze_geographic_content(titles):
    """Analyze geographic content in titles with proper detection."""
    logger.info("Analyzing geographic content...")
    
    geo_data = load_geographic_reference_data()
    all_geo_entities = []
    for entities in geo_data.values():
        all_geo_entities.extend(entities)
    
    geographic_analysis = {
        'titles_with_geography': [],
        'titles_without_geography': [],
        'geographic_entity_counts': Counter(),
        'multiple_regions_analysis': Counter(),
        'geographic_patterns': {
            'leading_geographic': [],  # "Europe, Market Name"
            'embedded_geographic': [], # "Market Name in Asia"
            'trailing_geographic': [], # "Market Name - North America"
        }
    }
    
    for title in titles:
        found_entities = []
        
        # Find all geographic entities in this title
        for entity in all_geo_entities:
            # Use word boundaries and case-insensitive matching
            pattern = r'\b' + re.escape(entity) + r'\b'
            if re.search(pattern, title, re.IGNORECASE):
                found_entities.append(entity)
                geographic_analysis['geographic_entity_counts'][entity] += 1
        
        if found_entities:
            geographic_analysis['titles_with_geography'].append({
                'title': title,
                'entities': found_entities,
                'entity_count': len(found_entities)
            })
            
            # Count multiple regions
            geographic_analysis['multiple_regions_analysis'][len(found_entities)] += 1
            
            # Analyze geographic patterns
            if title.split(',')[0].strip() in all_geo_entities:
                geographic_analysis['geographic_patterns']['leading_geographic'].append(title)
            elif re.search(r'\bin\s+(' + '|'.join(re.escape(e) for e in all_geo_entities) + r')\b', title, re.IGNORECASE):
                geographic_analysis['geographic_patterns']['embedded_geographic'].append(title)
            elif re.search(r'-\s*(' + '|'.join(re.escape(e) for e in all_geo_entities) + r')\s*$', title, re.IGNORECASE):
                geographic_analysis['geographic_patterns']['trailing_geographic'].append(title)
        else:
            geographic_analysis['titles_without_geography'].append(title)
    
    return geographic_analysis

def analyze_topic_extraction_patterns(titles):
    """Analyze topic extraction patterns with proper logic."""
    logger.info("Analyzing topic extraction patterns...")
    
    # Common suffixes that should be removed to extract topic
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
    
    # Common prefixes that should be removed
    prefix_patterns = [
        r'^global\s+',
        r'^worldwide\s+',
        r'^international\s+',
        r'^[^,]+,\s+'  # Geographic prefix like "Europe, "
    ]
    
    topic_analysis = {
        'extraction_examples': [],
        'common_prefixes': Counter(),
        'common_suffixes': Counter(),
        'extraction_challenges': []
    }
    
    for i, title in enumerate(titles[:500]):  # Sample for performance
        original_title = title
        working_title = title
        
        # Remove geographic prefixes
        detected_prefix = None
        for prefix_pattern in prefix_patterns:
            match = re.search(prefix_pattern, working_title, re.IGNORECASE)
            if match:
                detected_prefix = match.group().strip()
                if detected_prefix not in ['Global', 'Worldwide', 'International']:  # Only count actual geographic prefixes
                    topic_analysis['common_prefixes'][detected_prefix] += 1
                working_title = re.sub(prefix_pattern, '', working_title, flags=re.IGNORECASE).strip()
                break
        
        # Remove market-related suffixes
        detected_suffix = None
        for suffix_pattern in suffix_patterns:
            match = re.search(suffix_pattern, working_title, re.IGNORECASE)
            if match:
                detected_suffix = match.group().strip()
                topic_analysis['common_suffixes'][detected_suffix] += 1
                working_title = re.sub(suffix_pattern, '', working_title, flags=re.IGNORECASE).strip()
                break
        
        # Clean up the extracted topic
        extracted_topic = working_title.strip(' ,')
        
        # Determine if extraction was successful
        is_successful = (
            len(extracted_topic) > 2 and
            not any(word in extracted_topic.lower() for word in ['market', 'industry', 'report', 'size', 'share']) and
            not extracted_topic.isdigit() and
            extracted_topic.lower() not in ['global', 'worldwide', 'international']
        )
        
        result = {
            'original': original_title,
            'extracted_topic': extracted_topic,
            'detected_prefix': detected_prefix,
            'detected_suffix': detected_suffix,
            'successful': is_successful
        }
        
        if is_successful:
            topic_analysis['extraction_examples'].append(result)
        else:
            topic_analysis['extraction_challenges'].append(result)
    
    return topic_analysis

def analyze_market_term_patterns(titles):
    """Analyze market-related term patterns."""
    logger.info("Analyzing market term patterns...")
    
    market_patterns = {
        'standard_market': r'\bmarket\b',
        'market_for': r'\bmarket\s+for\b',
        'market_in': r'\bmarket\s+in\b',
        'aftermarket': r'\baftermarket\b',
        'marketplace': r'\bmarketplace\b',
        'market_size': r'\bmarket\s+size\b',
        'market_share': r'\bmarket\s+share\b'
    }
    
    market_analysis = {}
    for pattern_name, pattern in market_patterns.items():
        matches = []
        for title in titles:
            if re.search(pattern, title, re.IGNORECASE):
                matches.append(title)
        market_analysis[pattern_name] = {
            'count': len(matches),
            'examples': matches[:5]
        }
    
    return market_analysis

def analyze_complex_patterns(titles):
    """Analyze complex patterns that need special handling."""
    logger.info("Analyzing complex patterns...")
    
    geo_data = load_geographic_reference_data()
    all_geo_entities = []
    for entities in geo_data.values():
        all_geo_entities.extend(entities)
    
    complex_patterns = {
        'multiple_geographic_entities': {
            'description': 'Titles with multiple geographic entities',
            'examples': []
        },
        'geographic_conjunctions': {
            'description': 'Geographic entities connected with and/or/&',
            'examples': []
        },
        'market_for_geographic': {
            'description': 'Market for [geographic region] patterns',
            'examples': []
        },
        'market_in_geographic': {
            'description': 'Market in [geographic region] patterns',
            'examples': []
        },
        'parenthetical_regions': {
            'description': 'Geographic information in parentheses',
            'examples': []
        }
    }
    
    for title in titles:
        # Find all geographic entities in title
        found_entities = []
        for entity in all_geo_entities:
            if re.search(r'\b' + re.escape(entity) + r'\b', title, re.IGNORECASE):
                found_entities.append(entity)
        
        if len(found_entities) > 1:
            if len(complex_patterns['multiple_geographic_entities']['examples']) < 10:
                complex_patterns['multiple_geographic_entities']['examples'].append({
                    'title': title,
                    'entities': found_entities
                })
        
        # Geographic conjunctions
        geo_conjunction_pattern = r'(' + '|'.join(re.escape(e) for e in all_geo_entities) + r')\s+(?:and|&|or)\s+(' + '|'.join(re.escape(e) for e in all_geo_entities) + r')'
        if re.search(geo_conjunction_pattern, title, re.IGNORECASE):
            if len(complex_patterns['geographic_conjunctions']['examples']) < 10:
                complex_patterns['geographic_conjunctions']['examples'].append({
                    'title': title,
                    'entities': found_entities
                })
        
        # Market for geographic
        market_for_pattern = r'\bmarket\s+for\s+.*?(' + '|'.join(re.escape(e) for e in all_geo_entities) + r')'
        if re.search(market_for_pattern, title, re.IGNORECASE):
            if len(complex_patterns['market_for_geographic']['examples']) < 10:
                complex_patterns['market_for_geographic']['examples'].append({
                    'title': title,
                    'entities': found_entities
                })
        
        # Market in geographic
        market_in_pattern = r'\bmarket\s+in\s+(' + '|'.join(re.escape(e) for e in all_geo_entities) + r')'
        if re.search(market_in_pattern, title, re.IGNORECASE):
            if len(complex_patterns['market_in_geographic']['examples']) < 10:
                complex_patterns['market_in_geographic']['examples'].append({
                    'title': title,
                    'entities': found_entities
                })
        
        # Parenthetical regions
        paren_pattern = r'\(.*?(' + '|'.join(re.escape(e) for e in all_geo_entities) + r').*?\)'
        if re.search(paren_pattern, title, re.IGNORECASE):
            if len(complex_patterns['parenthetical_regions']['examples']) < 10:
                complex_patterns['parenthetical_regions']['examples'].append({
                    'title': title,
                    'entities': found_entities
                })
    
    return complex_patterns

def analyze_business_terminology(titles):
    """Analyze business terminology frequency."""
    logger.info("Analyzing business terminology...")
    
    business_terms = {
        'size_terms': ['size', 'sizing'],
        'share_terms': ['share', 'shares'],
        'growth_terms': ['growth', 'growing'],
        'analysis_terms': ['analysis', 'analytics'],
        'forecast_terms': ['forecast', 'forecasting'],
        'trend_terms': ['trends', 'trending'],
        'report_terms': ['report', 'reporting'],
        'industry_terms': ['industry', 'industrial'],
        'market_descriptors': ['global', 'regional', 'local', 'domestic', 'international']
    }
    
    terminology_analysis = {}
    for category, terms in business_terms.items():
        category_counts = Counter()
        for term in terms:
            count = sum(1 for title in titles if re.search(r'\b' + re.escape(term) + r'\b', title, re.IGNORECASE))
            if count > 0:
                category_counts[term] = count
        terminology_analysis[category] = category_counts
    
    return terminology_analysis

def generate_analysis_report(client, collection):
    """Generate comprehensive analysis report."""
    logger.info("Starting improved title pattern analysis...")
    
    # Get titles for analysis
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
    
    # Perform analyses
    geographic_analysis = analyze_geographic_content(titles)
    topic_analysis = analyze_topic_extraction_patterns(titles)
    market_analysis = analyze_market_term_patterns(titles)
    complex_patterns = analyze_complex_patterns(titles)
    business_terminology = analyze_business_terminology(titles)
    
    # Compile analysis report
    analysis_report = {
        'metadata': {
            'analysis_date': datetime.utcnow().isoformat(),
            'total_documents': total_docs,
            'titles_analyzed': len(titles),
            'analysis_version': 'v2_corrected'
        },
        'geographic_analysis': {
            'titles_with_geography': len(geographic_analysis['titles_with_geography']),
            'titles_without_geography': len(geographic_analysis['titles_without_geography']),
            'geographic_percentage': round(len(geographic_analysis['titles_with_geography']) / len(titles) * 100, 2),
            'top_geographic_entities': dict(geographic_analysis['geographic_entity_counts'].most_common(20)),
            'multiple_regions_distribution': dict(geographic_analysis['multiple_regions_analysis']),
            'geographic_patterns': {
                'leading_geographic_count': len(geographic_analysis['geographic_patterns']['leading_geographic']),
                'embedded_geographic_count': len(geographic_analysis['geographic_patterns']['embedded_geographic']),
                'trailing_geographic_count': len(geographic_analysis['geographic_patterns']['trailing_geographic']),
                'examples': {
                    'leading_geographic': geographic_analysis['geographic_patterns']['leading_geographic'][:5],
                    'embedded_geographic': geographic_analysis['geographic_patterns']['embedded_geographic'][:5],
                    'trailing_geographic': geographic_analysis['geographic_patterns']['trailing_geographic'][:5]
                }
            }
        },
        'topic_extraction_analysis': {
            'successful_extractions': len([e for e in topic_analysis['extraction_examples'] if e['successful']]),
            'challenging_extractions': len(topic_analysis['extraction_challenges']),
            'success_rate': round(len([e for e in topic_analysis['extraction_examples'] if e['successful']]) / 
                                (len(topic_analysis['extraction_examples']) + len(topic_analysis['extraction_challenges'])) * 100, 2) if topic_analysis['extraction_examples'] or topic_analysis['extraction_challenges'] else 0,
            'common_prefixes': dict(topic_analysis['common_prefixes'].most_common(10)),
            'common_suffixes': dict(topic_analysis['common_suffixes'].most_common(10)),
            'extraction_examples': topic_analysis['extraction_examples'][:10],
            'challenging_examples': topic_analysis['extraction_challenges'][:10]
        },
        'market_term_analysis': market_analysis,
        'complex_pattern_analysis': complex_patterns,
        'business_terminology_analysis': business_terminology,
        'sample_titles': titles[:20]
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

def main():
    """Main function to run the analysis."""
    print("MongoDB Title Pattern Analysis v2 (Corrected)")
    print("=" * 60)
    
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
        output_file = output_dir / f"title_pattern_analysis_v2_{timestamp}.json"
        
        save_analysis_report(report, output_file)
        
        # Print summary
        print("\n" + "=" * 60)
        print("📊 ANALYSIS SUMMARY")
        print("=" * 60)
        print(f"Total documents analyzed: {report['metadata']['total_documents']}")
        print(f"Titles with content: {report['metadata']['titles_analyzed']}")
        print(f"Titles with geography: {report['geographic_analysis']['titles_with_geography']} ({report['geographic_analysis']['geographic_percentage']}%)")
        print(f"Titles without geography: {report['geographic_analysis']['titles_without_geography']}")
        print(f"Topic extraction success rate: {report['topic_extraction_analysis']['success_rate']}%")
        print(f"Analysis saved to: {output_file}")
        print("\n✅ Corrected title pattern analysis completed successfully!")
        
    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        print(f"❌ Analysis failed: {e}")
    
    finally:
        if client:
            client.close()

if __name__ == "__main__":
    main()