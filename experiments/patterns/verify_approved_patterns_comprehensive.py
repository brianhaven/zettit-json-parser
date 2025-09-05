#!/usr/bin/env python3

"""
Comprehensive verification of approved patterns vs database patterns.
Checks which approved patterns are missing and which database patterns are not approved.
"""

import os
from datetime import datetime, timezone
import pytz
from pymongo import MongoClient
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def get_timestamps():
    """Generate PDT and UTC timestamps."""
    utc_now = datetime.now(timezone.utc)
    pdt_tz = pytz.timezone('America/Los_Angeles')
    pdt_now = utc_now.astimezone(pdt_tz)
    
    pdt_str = pdt_now.strftime('%Y-%m-%d %H:%M:%S PDT')
    utc_str = utc_now.strftime('%Y-%m-%d %H:%M:%S UTC')
    
    return pdt_str, utc_str

# Your complete approved patterns list
APPROVED_PATTERNS = """Market
Market Size Report
Market Size, Industry Report
Market Size & Share Report
Market Report
Market, Industry Report
Market Size, Share & Growth Report
Market Size And Share Report
Market Size & Share, Industry Report
Market Size, Share, Industry Report
Market Size, Share & Trends Report
Market Size, Share Report
Market Size, Share And Growth Report
Market Size And Share, Industry Report
Market Size, Share, Global Industry Report
Market Size, Global Industry Report
Market Size, Share, Growth Report
Market Size, Share, Industry
Market, Industry
Market Size, Share
Market Insights
Market Size, Industry
Market Size & Share
Market, Report
Market Size, Share And Trends Report
Market Size, Share & Growth
Market Size
Market Trends
Market Size, Report
Market Size & Share Analysis Report
Market Size, Share & Trends, Industry Report
Market Size, Share, Growth
Market Size, Share & Growth Analysis Report
Market Size & Growth Report
Market Outlook
Market Size & Share, Industry
Market Size, Share & Trends
Market Size & Share, Global Industry Report
Market Size, Share, Growth & Trends Report
Market Analysis
Market Size, Share & Growth, Industry Report
Market Forecast
Market Forecast Report
Market Size, Share & Trends Analysis Report
Market Size, Share, Trends, Global Industry Report
Market Size & Trends Report
Market Share Report
Market Size & Share, Industry Analysis Report
Market Size, Share, Trends, Industry Report
Market Size And Share
Market Size, Share, Industry Analysis Report
Market Size And Share, Report
Market Size, Share, Growth, Industry Report
Market Size, Industry Analysis Report
Market Size, Share, Trends & Growth Report
Market Size, Share & Trends, Global Industry Report
Market Size, Share, Growth Analysis Report
Market Size & Trends Analysis Report
Market Size, Share, Trends Report
Market Size, Share, Growth & Trends
Market Growth, Forecast
Market Size Analysis Report
Market Outlook, Trends, Analysis
Market Size & Share Analysis - Industry Research Report - Growth Trends
Market (Forecast )
Market Size, Share & Growth Analysis
Market Size, Share, Growth, Industry
Market Size, Share, Trends
Market Size, Share, Global Industry Analysis Report
Market Size & Share, Report
Market Size & Trends, Industry Report
Market Size, Share, Growth, Trends Report
Market Size, Share & Trends Analysis
Market Size, Share, Growth Analysis
Market Size, Share And Growth
Market Size, Global Industry Trends Report
Market Growth Outlook
Market, Forecast
Market Size And Share Analysis Report
Market Share & Growth Report
Market Size, Trends, Industry Report
Market Size, Share, Report
Market Size, Share & Analysis Report
Market Growth
Market Size, Share, Trends Analysis Report
Market Size & Share, Industry Growth Report
Market Size, Share Analysis Report
Market Size & Growth Analysis Report
Market Growth Analysis Report
Market Forecast Analysis Report
Market Size, Share Analysis
Market Size, Share, Industry Trends Report
Market Size, Share, Trend, Global Industry Report
Market Size, Share, Industry Growth Report
Market Size, Share, Trends & Growth
Market Size & Share, Industry Trends Report
Market Size, Share & Trends, Industry
Market Share Analysis Report
Market Size, Share, Global Industry Trends Report
Market Share, Industry Report
Market Size, Global Industry Analysis Report
Market Size, Share & Growth, Industry
Market Size & Share [ Global Report]
Market Size, Share And Trends
Market Size & Share, Global Industry Trends Report
Market Growth Report
Market Size, Share, Trends, Report
Market Size, Share, Industry Trend Report
Market Size & Trends, Global Industry Report
Market Size, Share And Growth Analysis Report
Market Analysis Report
Market Size, Industry Trend Report
Market Size And Share [ Global Report]
Market Share Analysis, Industry Report
Market Size, Trends & Growth Report
Market Size, Share, Trends, Industry Analysis Report
Market Size Industry Report
Market - Size, Share & Industry Analysis
Market Share, Insights
Market Analysis till
Market, Global Industry Report
Market Share & Trends Report
Market Size Analysis
Market Size And Trends, Industry Report
Market Size, Industry Trend
Market Size, Share, And Growth Report
Market Share, Global Industry Report
Market Size, Industry Trends Report
Market Size, Share, Trends, Growth Report
Market Size & Trends, Industry Analysis Report
Market Size And Share, Industry
Market Size, Share & Forecast Report
Market Analysis, Industry Report
Market Size, Share, Trends, Industry
Market Size & Share, Global Report
Market Size, Share, Trends And Growth Report
Market (Forecast, )
Market Size, Share, Global Industry Growth Report
Market Size, Share, Trend Report
Market Size, Share And Trends, Industry Report
Market Trends & Growth Report
Market Size, Share, Global Industry
Market Size, Trends Report
Market Size, Share, Growth, Industry Trends
Market Size & Size, Industry Analysis Report
Market Trends, Industry Report
Market Share, Size, Industry Report
Market Size, Growth, Global Industry Report
Market Size, Share, Analysis, Industry Report
Market Share & Growth Analysis Report
Market Trends & Growth Analysis Report
Market Size, Share, & Growth Report
Market Size, Global Industry
Market Size, Share And Analysis Report
Market Share, Size, Trends, Global Industry Report
Market Share, Trends, Global Industry Report
Market Size, Growth, Industry Report
Market Size, Trends, Industry
Market Size, Share, Growth, Industry Analysis Report
Market Size & Growth Analysis
Market Size, Growth & Trends Report
Market Size & Share Analysis
Market Size, Share, Trends Forecast
Market Size, Share, Growth And Trends Report
Market Size, Share, Trends, Industry Growth Report
Market Forecast Study
Market Global Forecast
Market Growth Forecast
Market Outlook, Trends
Market Share, Analysis, Forecast
Market Share, Analysis
Market Growth Analysis
Market Report Size
Market Size, Share & Trends, Industry Analysis Report
Market Size, Share, Growth, Trends
Market Size, Share And Growth, Industry Report
Market Size, Share & Trends, Industry Growth Report
Market Size, Share, Growth, Global Industry Report
Market Size & Share Growth Report
Market Size, Analysis, Industry Report
Market Size And Analysis Report
Market Trends Report
Market Trends Analysis Report
Market Size, Share & Trend Report
Market Share, Growth & Trends Report
Market Size, Share & Analysis, Industry Report
Market Size, Share, Trend, Industry Report
Market Size, Industry Growth Report
Market Size, Share [ Global Report]
Market Size, Trends, Industry Analysis Report
Market Size, Share, Trends, Growth
Market Size, Share And Trends, Report
Market Size & Share, Global Industry Growth Report
Market Growth, Industry Report
Market Size & Growth
Market Size, Share, Trends, Global Industry Growth Report
Market Size, Global Industry Growth
Market Size, Value, Global Industry Trends Report
Market Size, Growth, Global Industry Analysis Report
Market Size, Share, Growth, Industry Trends Report
Market Volume & Share Report
Market Size, Trends, Share, Global Industry Report
Market Size and Trends Report
Market Size, Forecast Report
Market Size, Share, Global Industry Trend Report
Market Size, Growth, Industry Analysis Report
Market Size, Trends, Industry Research Report
Market Size, Share, Trends And Growth
Market Size By Product, Industry Report
Market Size & share, Industry Report
Market Size, Share, Growth And Trends
Market Size, And Share, Industry Report
Market Size, Research Report
Market Size And Share, Trends Report
Market Size, Share, industry Report
Market Size, Share, Trend, Industry Research
Market Trends, Share, Size, Industry Report
Market Size, Share, Industry Research Report
Market Size, Share, Statistics & Analysis
Market Share, Industry Growth Analysis Report
Market Size, Share, Industry Growth
Market Size, Share & Growth, Industy Report
Market Size, Share & Trend Analysis Report
Market Size, Global Report
Market, industry Report
Market Size Trends Report
Market Size Share Report
Market Share & Growth Analysis
Market Size & Share, Global Industry Analysis Report
Market Size | Industry Trends & Forecast Analysis
Market Growth | Industry Analysis, Size & Forecast Report
Market Trends | Industry Analysis, Size & Growth Report
Market Report | Industry Analysis, Size & Forecast Overview
Market - Share, Trends & Size
Market - Companies, Analysis, Industry Overview & Outlook
Market - Trends & Size
Market - Size, Trends & Research Report
Market - Companies, Size & Share
Market - Companies & Trends
Market Insights, Forecast
Market Demand, Research Insights
Market Global
Market Analysis, Forecast Report
Market Analysis, Outlook
Market Trends (Forecast )
Market Analysis, Report
Market Forecast -
Market Trends, Forecast
Market Share & Share, Industry Report
Market Size & Share, Indsutry Report
Market Size, Share, Growth And Trends By
Market Size, Share And Report
Market Size And Growth Report
Market Size,Share, Report
Market Size, Trends & Growth Analysis
Market Size, Share Forecast Report
Market Size, Share, Trends Analysis
Market Growth And Trends Report
Market Size, Share, Forecast Report
Market Size, Analysis, Global Industry Report
Market Size & Analysis, Global Industry Report
Market Share
Market Size & Growth, Industry Trends Report
Market Size, Share [Global Report]
Market Size, Share Analysis, Report
Market Size, Global Industry Growth Report
Market Growth & Trends
Market Trends Analysis
Market Sze Report
Market Size, Share Trends Report
Market Growth, Industry Trends Report
Market Share, Size, Industry Analysis Report
Market Size, Share, Indsutry Report
Market Size & Share, Growth Report
Market Share & Trend Analysis Report
Market Size, Industry Repot
Market Size Reports
Market Analysis, Industry Trends Report
Market Size Analysis, Report
Market Size And Share Analysis
Market Size & Share, Growth, Global Industry Report
Market Trends, Industry Growth Report
Market Sizes & Trends Report
market Size, Share, Global Industry Report
Market Size, Industry report
Market Share Analysis & Growth Report
Market Size, Share, Forecast
Market Size, Share & Growth Market
Market Size, Share & Growth, Report
Market Size, Growth, Report
Market Size, Share & Trends, Industry Analysis
Market Size, , Industry Report
Market Size, Growth, Industry Forecast Report
Market Size, Growth & Trends
Market Size, Share & Trend Analysis
Market Size, Share & Trend
market Size & Share Report
Market Size & Growth Report Analysis
Market Research Report
Market Size , Industry Report
Market Size & Growth Forecast Report
Market Share, Share, Growth
Market Share & Trends Analysis Report
Market Share & Size Analysis Report
Market Size, Share & Trends, Industry Growth Forecast
Market Size, Share, Industy Report
Market Size & Size, Global Industry Report
Market Size, Share, Trends, Global Industry
Market Size, Industry Research Report
Market Size, Share & Growth [ Global Report]
Market Share & Share Report
Market Size & Forecast Report
Market Size, Share & Trends [ Global Report]
Market Size & Share report
Market Size & Trend
Market Share, Trends Report
Market Size & Trend Report
Market Size, Revenue, Industry Report
Market Size, Share, Industry Analysis
Market Share, Industry Trends Report
Market Size, Share, Trends And Report
Market Size, Share Global Industry Report
Market Size, Value, Growth Report
Market Report Report
Market Size & Share, Growth, Industry Report
Market Size, Share, Trends, Industry Analysis
Market Size,, Industry Report
Market Size, Trends, Global Industry Report
Market Size, Share, Growth, Trends, Report
Market Size, Share, Growth, Report
Market Size & Trends, Report
Market Size & Analysis Report
Market Size And Growth, Report
Market Size And Share Analysis, Report
Market Size & Share, Report Industry
market Size, Share, Industry Report
Market Size, Share, Growth, Global Industry Trends Report
Market Share, Trends, Industry Report"""

def main():
    pdt_str, utc_str = get_timestamps()
    
    print("Comprehensive Pattern Verification")
    print("=" * 60)
    print(f"Analysis Date (PDT): {pdt_str}")
    print(f"Analysis Date (UTC): {utc_str}")
    print("=" * 60)
    print()
    
    # Connect to MongoDB
    client = MongoClient(os.getenv('MONGODB_URI'))
    db = client['deathstar']
    collection = db['pattern_libraries']
    
    # Parse approved patterns
    approved_patterns = set(line.strip() for line in APPROVED_PATTERNS.strip().split('\n') if line.strip())
    print(f"Total approved patterns: {len(approved_patterns)}")
    
    # Get all REPORT_TYPE patterns from database
    db_patterns = collection.find({'type': 'REPORT_TYPE'})
    db_pattern_terms = set()
    db_pattern_dict = {}
    
    for pattern in db_patterns:
        term = pattern.get('term', '')
        db_pattern_terms.add(term)
        db_pattern_dict[term] = pattern
    
    print(f"Total database patterns: {len(db_pattern_terms)}")
    print()
    
    # Find missing patterns (in approved but not in database)
    missing_patterns = approved_patterns - db_pattern_terms
    
    # Find extra patterns (in database but not in approved)
    extra_patterns = db_pattern_terms - approved_patterns
    
    # Find common patterns
    common_patterns = approved_patterns & db_pattern_terms
    
    print("=" * 60)
    print("PATTERNS MISSING FROM DATABASE (Need to Add):")
    print("=" * 60)
    if missing_patterns:
        for i, pattern in enumerate(sorted(missing_patterns), 1):
            print(f"{i:3}. {pattern}")
    else:
        print("✓ All approved patterns are in the database!")
    
    print()
    print("=" * 60)
    print("EXTRA PATTERNS IN DATABASE (Not in Approved List):")
    print("=" * 60)
    if extra_patterns:
        for i, pattern in enumerate(sorted(extra_patterns), 1):
            format_type = db_pattern_dict[pattern].get('format_type', 'unknown')
            print(f"{i:3}. {pattern} ({format_type})")
    else:
        print("✓ No extra patterns found in database!")
    
    print()
    print("=" * 60)
    print("SUMMARY:")
    print("=" * 60)
    print(f"Approved patterns: {len(approved_patterns)}")
    print(f"Database patterns: {len(db_pattern_terms)}")
    print(f"Common patterns: {len(common_patterns)}")
    print(f"Missing patterns: {len(missing_patterns)}")
    print(f"Extra patterns: {len(extra_patterns)}")
    
    # Create output files for review
    output_dir = "../outputs"
    os.makedirs(output_dir, exist_ok=True)
    
    timestamp = datetime.now(pytz.timezone('America/Los_Angeles')).strftime('%Y%m%d_%H%M%S')
    
    # Write missing patterns to file
    if missing_patterns:
        missing_file = os.path.join(output_dir, f"{timestamp}_missing_patterns.txt")
        with open(missing_file, 'w') as f:
            f.write(f"Missing Patterns from Database\n")
            f.write(f"Analysis Date (PDT): {pdt_str}\n")
            f.write(f"Analysis Date (UTC): {utc_str}\n")
            f.write("=" * 60 + "\n\n")
            for pattern in sorted(missing_patterns):
                f.write(f"{pattern}\n")
        print(f"\n✓ Missing patterns written to: {missing_file}")
    
    # Write extra patterns to file
    if extra_patterns:
        extra_file = os.path.join(output_dir, f"{timestamp}_extra_patterns.txt")
        with open(extra_file, 'w') as f:
            f.write(f"Extra Patterns in Database (Not Approved)\n")
            f.write(f"Analysis Date (PDT): {pdt_str}\n")
            f.write(f"Analysis Date (UTC): {utc_str}\n")
            f.write("=" * 60 + "\n\n")
            for pattern in sorted(extra_patterns):
                format_type = db_pattern_dict[pattern].get('format_type', 'unknown')
                f.write(f"{pattern} ({format_type})\n")
        print(f"✓ Extra patterns written to: {extra_file}")
    
    client.close()
    print("\n✅ Verification complete!")

if __name__ == "__main__":
    main()