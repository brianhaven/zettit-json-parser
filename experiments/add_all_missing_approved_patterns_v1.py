#!/usr/bin/env python3
"""
Add All Missing Approved Patterns - Phase 3.6 Critical Fix
Adds all 251 missing patterns identified in the comprehensive audit.

This script addresses the critical issue: 99.6% of approved patterns are missing from database.
"""

import os
import re
import sys
from pymongo import MongoClient
from dotenv import load_dotenv
from datetime import datetime, timezone
from collections import defaultdict
import time

# Load environment variables
load_dotenv()

def get_pdt_timestamp():
    """Get current timestamp in PDT and UTC"""
    now_utc = datetime.now(timezone.utc)
    pdt_offset = -7 if datetime.now().month in range(3, 11) else -8  # Rough PDT/PST
    now_pdt = now_utc.replace(tzinfo=timezone.utc).astimezone(timezone.utc)
    
    pdt_str = now_pdt.strftime('%Y-%m-%d %H:%M:%S PDT')
    utc_str = now_utc.strftime('%Y-%m-%d %H:%M:%S UTC')
    return pdt_str, utc_str

def get_all_missing_approved_patterns():
    """Return all 251 missing approved patterns that need to be added"""
    
    # Tier 1: Basic Types (37 patterns)
    tier1 = [
        "Market Report", "Market Analysis", "Market Outlook", "Market Overview", 
        "Market Study", "Market Trends", "Market Research", "Market Insights", 
        "Market Statistics", "Market Survey", "Market Data", "Market Review", 
        "Market Intelligence", "Market Dynamics", "Market Assessment", 
        "Market Evaluation", "Market Summary", "Market Update", "Market Briefing", 
        "Market Information", "Market Profile", "Market Forecast", 
        "Market Projections", "Market Scenario", "Market Potential", 
        "Market Opportunity", "Market Size", "Market Share", "Market Growth", 
        "Market Value", "Market Volume", "Market Worth", "Market Revenue", 
        "Market Sales", "Market Demand", "Market Supply", "Market Status"
    ]
    
    # Tier 2: Size & Share Compounds (47 patterns - excluding the 1 we already have)
    tier2 = [
        "Market Size & Share Report", "Market Size And Share Report", 
        "Market Size, Share Report", "Market Size, Share & Trends Report", 
        "Market Size, Share, Industry Report", "Market Size & Share Analysis", 
        "Market Size And Share Analysis", "Market Size, Share Analysis", 
        "Market Size, Share & Trends Analysis", "Market Size, Share, Industry Analysis", 
        "Market Size & Share Study", "Market Size And Share Study", 
        "Market Size, Share Study", "Market Size, Share & Trends Study", 
        "Market Size, Share, Industry Study", "Market Size & Share Outlook", 
        "Market Size And Share Outlook", "Market Size, Share Outlook", 
        "Market Size, Share & Trends Outlook", "Market Size, Share, Industry Outlook", 
        "Market Size & Share Overview", "Market Size And Share Overview", 
        "Market Size, Share Overview", "Market Size, Share & Trends Overview", 
        "Market Size, Share, Industry Overview", "Market Size & Share Forecast", 
        "Market Size And Share Forecast", "Market Size, Share Forecast", 
        "Market Size, Share & Trends Forecast", "Market Size, Share, Industry Forecast", 
        "Market Size & Share Insights", "Market Size And Share Insights", 
        "Market Size, Share Insights", "Market Size, Share & Trends Insights", 
        "Market Size, Share, Industry Insights", "Market Size & Share Research", 
        "Market Size And Share Research", "Market Size, Share Research", 
        "Market Size, Share & Trends Research", "Market Size, Share, Industry Research", 
        "Market Size & Share Data", "Market Size And Share Data", 
        "Market Size, Share Data", "Market Size, Share & Trends Data", 
        "Market Size, Share, Industry Data", "Market Size, Share", 
        "Market Size, Share & Trends"
    ]
    
    # Tier 3: Industry & Trends (30 patterns)
    tier3 = [
        "Market Trends Report", "Market Trends Analysis", "Market Trends Study", 
        "Market Trends Outlook", "Market Trends Overview", "Market Trends Forecast", 
        "Market Trends Insights", "Market Trends Research", "Market Trends Data", 
        "Market Industry Report", "Market Industry Analysis", "Market Industry Study", 
        "Market Industry Outlook", "Market Industry Overview", "Market Industry Forecast", 
        "Market Industry Insights", "Market Industry Research", "Market Industry Data", 
        "Market Growth Report", "Market Growth Analysis", "Market Growth Study", 
        "Market Growth Outlook", "Market Growth Overview", "Market Growth Forecast", 
        "Market Growth Insights", "Market Growth Research", "Market Growth Data", 
        "Market & Industry Report", "Market & Industry Analysis", "Market & Industry Study"
    ]
    
    # Tier 4: Specialized & Technical (50 patterns)
    tier4 = [
        "Market Segmentation Report", "Market Segmentation Analysis", 
        "Market Competitive Analysis", "Market Competition Analysis", 
        "Market Landscape Report", "Market Landscape Analysis", 
        "Market Position Report", "Market Position Analysis", 
        "Market Performance Report", "Market Performance Analysis", 
        "Market Opportunity Report", "Market Opportunity Analysis", 
        "Market Risk Analysis", "Market Risk Assessment", 
        "Market Feasibility Study", "Market Feasibility Analysis", 
        "Market Entry Strategy", "Market Entry Analysis", 
        "Market Exit Strategy", "Market Exit Analysis", 
        "Market Penetration Analysis", "Market Development Analysis", 
        "Market Expansion Analysis", "Market Consolidation Analysis", 
        "Market Maturity Analysis", "Market Saturation Analysis", 
        "Market Disruption Analysis", "Market Innovation Analysis", 
        "Market Technology Analysis", "Market Digital Analysis", 
        "Market Regulatory Analysis", "Market Policy Analysis", 
        "Market Economic Analysis", "Market Financial Analysis", 
        "Market Investment Analysis", "Market Funding Analysis", 
        "Market Valuation Report", "Market Valuation Analysis", 
        "Market Due Diligence", "Market Benchmark Analysis", 
        "Market Comparison Analysis", "Market Gap Analysis", 
        "Market SWOT Analysis", "Market Porter Analysis", 
        "Market Strategic Analysis", "Market Tactical Analysis", 
        "Market Operational Analysis", "Market Supply Chain Analysis", 
        "Market Distribution Analysis", "Market Channel Analysis"
    ]
    
    # Tier 5: Additional Approved (48 patterns)
    tier5 = [
        "Market Drivers Analysis", "Market Barriers Analysis", 
        "Market Challenges Analysis", "Market Solutions Analysis", 
        "Market Recommendations Report", "Market Best Practices", 
        "Market Case Studies", "Market Success Stories", 
        "Market Failure Analysis", "Market Lessons Learned", 
        "Market White Paper", "Market Technical Report", 
        "Market Research Paper", "Market Academic Study", 
        "Market Thesis", "Market Dissertation", 
        "Market Executive Summary", "Market Management Summary", 
        "Market Investment Brief", "Market Business Case", 
        "Market Proposal", "Market RFP Response", 
        "Market Tender Document", "Market Specification", 
        "Market Requirements", "Market Standards", 
        "Market Guidelines", "Market Protocols", 
        "Market Procedures", "Market Methodologies", 
        "Market Framework", "Market Model", 
        "Market Template", "Market Blueprint", 
        "Market Roadmap", "Market Strategy", 
        "Market Plan", "Market Program", 
        "Market Initiative", "Market Project", 
        "Market Campaign", "Market Launch", 
        "Market Introduction", "Market Announcement", 
        "Market Press Release", "Market News", 
        "Market Update", "Market Alert", 
        "Market Bulletin", "Market Newsletter"
    ]
    
    # Tier 6: Geographic & Regional (37 patterns)
    tier6 = [
        "Market Regional Report", "Market Regional Analysis", 
        "Market Global Report", "Market Global Analysis", 
        "Market International Report", "Market International Analysis", 
        "Market Domestic Report", "Market Domestic Analysis", 
        "Market Local Report", "Market Local Analysis", 
        "Market National Report", "Market National Analysis", 
        "Market Cross-Border Analysis", "Market Multi-Country Analysis", 
        "Market Comparative Analysis", "Market Localization Report", 
        "Market Expansion Report", "Market Geographic Analysis", 
        "Market Territory Analysis", "Market Regional Outlook", 
        "Market Global Outlook", "Market International Outlook", 
        "Market Domestic Outlook", "Market Local Outlook", 
        "Market National Outlook", "Market Regional Forecast", 
        "Market Global Forecast", "Market International Forecast", 
        "Market Domestic Forecast", "Market Local Forecast", 
        "Market National Forecast", "Market Regional Trends", 
        "Market Global Trends", "Market International Trends", 
        "Market Domestic Trends", "Market Local Trends", 
        "Market National Trends"
    ]
    
    # Combine all patterns
    all_patterns = tier1 + tier2 + tier3 + tier4 + tier5 + tier6
    
    return all_patterns

def convert_term_to_pattern(term: str):
    """Convert a term like 'Market Analysis' to regex pattern"""
    
    # Remove "Market " prefix for processing
    clean_term = term.replace("Market ", "").strip()
    
    # Escape special regex characters
    escaped = re.escape(clean_term)
    
    # Handle common punctuation flexibly
    escaped = escaped.replace(r'\&', r'\s*&\s*')  # & with optional spaces
    escaped = escaped.replace(r'\,', r',\s*')      # comma with optional space
    escaped = escaped.replace(r'\ ', r'\s+')       # spaces become flexible whitespace
    
    # Create full pattern that matches "Market" + term with flexible ending
    full_pattern = f'\\bMarket\\s+{escaped}(?:\\s*$|[,.])'
    
    return full_pattern

def categorize_format_type(term: str) -> str:
    """Categorize pattern into format type based on term characteristics"""
    
    # Terminal types - single word after Market
    simple_terminals = [
        'Market Report', 'Market Analysis', 'Market Outlook', 'Market Overview',
        'Market Study', 'Market Research', 'Market Insights', 'Market Data',
        'Market Size', 'Market Share', 'Market Growth', 'Market Trends'
    ]
    
    if term in simple_terminals:
        return 'terminal_type'
    
    # Embedded types - market term appears in middle
    if 'Market' in term and not term.startswith('Market '):
        return 'embedded_type'
    
    # Prefix types - market at beginning but complex structure
    if term.startswith('Market ') and any(word in term for word in ['&', 'And', ',', 'Size', 'Share']):
        return 'compound_type'
    
    # Default to compound for complex patterns
    return 'compound_type'

def add_patterns_to_database(patterns):
    """Add all patterns to MongoDB database"""
    
    client = MongoClient(os.getenv('MONGODB_URI'))
    db = client['deathstar']
    collection = db['pattern_libraries']
    
    added_count = 0
    skipped_count = 0
    failed_count = 0
    
    print(f"\nAdding {len(patterns)} patterns to database...")
    
    for i, term in enumerate(patterns, 1):
        try:
            # Check if pattern already exists
            existing = collection.find_one({
                'type': 'REPORT_TYPE',
                'term': term,
                'active': True
            })
            
            if existing:
                print(f"  [{i:3d}] SKIP - {term} (already exists)")
                skipped_count += 1
                continue
            
            # Create pattern document
            pattern_data = {
                'type': 'REPORT_TYPE',
                'term': term,
                'pattern': convert_term_to_pattern(term),
                'format_type': categorize_format_type(term),
                'priority': 1,
                'active': True,
                'success_count': 0,
                'failure_count': 0,
                'created_date': datetime.now(timezone.utc),
                'last_updated': datetime.now(timezone.utc),
                'notes': f'Added from comprehensive approved pattern audit - Phase 3.6'
            }
            
            # Insert pattern
            result = collection.insert_one(pattern_data)
            
            if result.inserted_id:
                print(f"  [{i:3d}] ✅ - {term} ({pattern_data['format_type']})")
                added_count += 1
            else:
                print(f"  [{i:3d}] ❌ - {term} (insert failed)")
                failed_count += 1
            
            # Small delay to avoid overwhelming database
            if i % 50 == 0:
                time.sleep(0.1)
                
        except Exception as e:
            print(f"  [{i:3d}] ❌ - {term} (error: {str(e)})")
            failed_count += 1
    
    return added_count, skipped_count, failed_count

def verify_database_state():
    """Verify final database state after additions"""
    
    client = MongoClient(os.getenv('MONGODB_URI'))
    db = client['deathstar']
    collection = db['pattern_libraries']
    
    patterns = list(collection.find({
        'type': 'REPORT_TYPE',
        'active': True
    }))
    
    print(f"\n📊 Final Database State:")
    print(f"   Total REPORT_TYPE patterns: {len(patterns)}")
    
    # Group by format type
    format_counts = defaultdict(int)
    for p in patterns:
        format_type = p.get('format_type', 'unknown')
        format_counts[format_type] += 1
    
    print(f"   Format type breakdown:")
    for format_type, count in sorted(format_counts.items()):
        print(f"     - {format_type}: {count} patterns")
    
    return len(patterns)

def main():
    """Main execution"""
    pdt_time, utc_time = get_pdt_timestamp()
    
    print("=" * 80)
    print("ADDING ALL MISSING APPROVED PATTERNS - Phase 3.6 Critical Fix")
    print(f"Analysis Date (PDT): {pdt_time}")
    print(f"Analysis Date (UTC): {utc_time}")
    print("=" * 80)
    print()
    print("This script addresses the critical finding from the comprehensive audit:")
    print("251 out of 252 approved patterns (99.6%) are missing from the database!")
    print()
    
    # Get all missing patterns
    print("1. Loading all 251 missing approved patterns...")
    missing_patterns = get_all_missing_approved_patterns()
    print(f"   ✅ Loaded {len(missing_patterns)} patterns to add")
    
    # Verify current state
    print("\n2. Checking current database state...")
    initial_count = verify_database_state()
    
    # Add all patterns
    print(f"\n3. Adding all {len(missing_patterns)} missing patterns...")
    added_count, skipped_count, failed_count = add_patterns_to_database(missing_patterns)
    
    # Verify final state
    print(f"\n4. Verifying final database state...")
    final_count = verify_database_state()
    
    # Summary
    print(f"\n{'='*80}")
    print("PATTERN ADDITION RESULTS")
    print(f"{'='*80}")
    print(f"Initial Database Patterns:  {initial_count}")
    print(f"Patterns Added:             {added_count}")
    print(f"Patterns Skipped:           {skipped_count}")
    print(f"Patterns Failed:            {failed_count}")
    print(f"Final Database Patterns:    {final_count}")
    print(f"Expected Final Count:       252 (all approved patterns)")
    
    if final_count == 252:
        print(f"\n✅ SUCCESS: All 252 approved patterns now in database!")
        print("This should dramatically improve report type extraction accuracy.")
    else:
        print(f"\n⚠️  WARNING: Expected 252 patterns, got {final_count}")
        print("Some patterns may need manual review.")

if __name__ == "__main__":
    main()