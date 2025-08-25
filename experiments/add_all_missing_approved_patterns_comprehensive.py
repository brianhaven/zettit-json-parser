#!/usr/bin/env python3

"""
Add all missing approved patterns to the database and generate comprehensive reports.
Creates detailed output files for manual review of what was added and what extras exist.
"""

import os
import re
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
    timestamp = pdt_now.strftime('%Y%m%d_%H%M%S')
    
    return pdt_str, utc_str, timestamp

def determine_format_type(term):
    """Determine the most appropriate format_type for a pattern term."""
    # Clean term for analysis
    clean_term = term.lower().strip()
    
    # Terminal patterns - end with these keywords
    terminal_indicators = ['report', 'analysis', 'study', 'forecast', 'outlook', 'data', 'overview', 'research', 'insights']
    if any(clean_term.endswith(indicator) for indicator in terminal_indicators):
        return 'terminal_type'
    
    # Prefix patterns - start with these (dash patterns, etc.)
    if clean_term.startswith('-') or clean_term.startswith('market -'):
        return 'prefix_type'
    
    # Embedded patterns - simple terms that appear within titles
    simple_patterns = ['market', 'industry', 'share', 'size', 'growth', 'trends']
    if clean_term in simple_patterns or len(clean_term.split()) <= 2:
        return 'embedded_type'
    
    # Default to compound for complex multi-word patterns
    return 'compound_type'

def generate_pattern_regex(term, format_type):
    """Generate appropriate regex pattern for the term and format type."""
    # Remove "Market " prefix and clean the term
    if term.startswith('Market '):
        clean_term = term[7:].strip()  # Remove "Market " prefix
    elif term.startswith('market '):
        clean_term = term[7:].strip()  # Remove "market " prefix
    else:
        clean_term = term.strip()
    
    # Handle special cases
    if not clean_term or clean_term.lower() == 'market':
        clean_term = term.strip()
    
    # Escape special regex characters
    escaped = re.escape(clean_term)
    
    # Replace escaped operators with flexible patterns
    escaped = escaped.replace(r'\&', r'\s*&\s*')
    escaped = escaped.replace(r'\,', r',\s*')
    escaped = escaped.replace(r'\-', r'\s*-\s*')
    escaped = escaped.replace(r'\|', r'\s*\|\s*')
    escaped = escaped.replace(r'\(', r'\s*\(\s*')
    escaped = escaped.replace(r'\)', r'\s*\)\s*')
    escaped = escaped.replace(r'\[', r'\s*\[\s*')
    escaped = escaped.replace(r'\]', r'\s*\]\s*')
    
    # Create pattern based on format type
    if format_type == 'terminal_type':
        if term.lower() == 'market':
            pattern = r'\bMarket(?:\s*$|[,.])'
        elif clean_term and clean_term != term:
            pattern = f'\\bMarket\\s+{escaped}(?:\\s*$|[,.])'
        else:
            pattern = f'\\b{escaped}(?:\\s*$|[,.])'
    elif format_type == 'embedded_type':
        if term.lower() == 'market':
            pattern = r'\bMarket\b'
        elif clean_term and clean_term != term:
            pattern = f'\\bMarket\\s+{escaped}\\b'
        else:
            pattern = f'\\b{escaped}\\b'
    elif format_type == 'prefix_type':
        if term.startswith('-') or term.startswith('Market -'):
            pattern = f'^\\s*{escaped}\\s+'
        else:
            pattern = f'^{escaped}\\s+'
    else:  # compound_type
        if term.lower() == 'market':
            pattern = r'\bMarket(?:\s*$|[,.])'
        elif clean_term and clean_term != term:
            pattern = f'\\bMarket\\s+{escaped}(?:\\s*$|[,.])'
        else:
            pattern = f'\\b{escaped}(?:\\s*$|[,.])'
    
    return pattern

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
    pdt_str, utc_str, timestamp = get_timestamps()
    
    print("Comprehensive Missing Pattern Addition")
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
    print(f"Total approved patterns to process: {len(approved_patterns)}")
    
    # Get existing database patterns
    existing_patterns = set()
    db_pattern_details = {}
    
    for pattern in collection.find({'type': 'REPORT_TYPE'}):
        term = pattern.get('term', '')
        existing_patterns.add(term)
        db_pattern_details[term] = {
            'format_type': pattern.get('format_type', 'unknown'),
            'pattern': pattern.get('pattern', ''),
            'notes': pattern.get('notes', '')
        }
    
    print(f"Existing database patterns: {len(existing_patterns)}")
    
    # Find missing patterns
    missing_patterns = approved_patterns - existing_patterns
    extra_patterns = existing_patterns - approved_patterns
    
    print(f"Missing patterns to add: {len(missing_patterns)}")
    print(f"Extra patterns in database: {len(extra_patterns)}")
    print()
    
    # Create output directory
    output_dir = f"../outputs/{timestamp}_comprehensive_pattern_addition"
    os.makedirs(output_dir, exist_ok=True)
    
    # Add missing patterns
    added_count = 0
    failed_count = 0
    
    if missing_patterns:
        print("Adding missing approved patterns...")
        print("-" * 40)
        
        # Prepare batch insert
        documents_to_insert = []
        
        for term in sorted(missing_patterns):
            try:
                format_type = determine_format_type(term)
                pattern_regex = generate_pattern_regex(term, format_type)
                
                doc = {
                    'type': 'REPORT_TYPE',
                    'term': term,
                    'pattern': pattern_regex,
                    'format_type': format_type,
                    'active': True,
                    'priority': 1,
                    'created_date': datetime.now(timezone.utc),
                    'last_updated': datetime.now(timezone.utc),
                    'success_count': 0,
                    'failure_count': 0,
                    'notes': 'Added from comprehensive approved pattern list (GitHub Issue #6)'
                }
                documents_to_insert.append(doc)
                
            except Exception as e:
                print(f"  ✗ Failed to prepare '{term}': {e}")
                failed_count += 1
        
        # Batch insert all documents
        if documents_to_insert:
            try:
                result = collection.insert_many(documents_to_insert)
                added_count = len(result.inserted_ids)
                print(f"✓ Successfully added {added_count} patterns to database")
            except Exception as e:
                print(f"✗ Batch insert failed: {e}")
                failed_count += len(documents_to_insert)
    
    # Generate comprehensive output files
    print("\nGenerating output files...")
    
    # 1. Added patterns report
    added_file = os.path.join(output_dir, "added_patterns.txt")
    with open(added_file, 'w') as f:
        f.write(f"Added Approved Patterns Report\n")
        f.write(f"Analysis Date (PDT): {pdt_str}\n")
        f.write(f"Analysis Date (UTC): {utc_str}\n")
        f.write("=" * 60 + "\n\n")
        f.write(f"Total patterns added: {added_count}\n")
        f.write(f"Failed additions: {failed_count}\n\n")
        
        if missing_patterns:
            f.write("Added Patterns:\n")
            f.write("-" * 40 + "\n")
            for i, term in enumerate(sorted(missing_patterns), 1):
                format_type = determine_format_type(term)
                f.write(f"{i:3}. {term} ({format_type})\n")
    
    # 2. Extra patterns report (detailed)
    extra_file = os.path.join(output_dir, "extra_patterns_in_database.txt")
    with open(extra_file, 'w') as f:
        f.write(f"Extra Patterns in Database (Not in Approved List)\n")
        f.write(f"Analysis Date (PDT): {pdt_str}\n")
        f.write(f"Analysis Date (UTC): {utc_str}\n")
        f.write("=" * 60 + "\n\n")
        f.write(f"Total extra patterns: {len(extra_patterns)}\n\n")
        
        if extra_patterns:
            # Group by format type for better organization
            by_format = {}
            for pattern in extra_patterns:
                fmt = db_pattern_details.get(pattern, {}).get('format_type', 'unknown')
                if fmt not in by_format:
                    by_format[fmt] = []
                by_format[fmt].append(pattern)
            
            for format_type in sorted(by_format.keys()):
                f.write(f"\n{format_type.upper()} PATTERNS:\n")
                f.write("-" * 40 + "\n")
                for i, pattern in enumerate(sorted(by_format[format_type]), 1):
                    f.write(f"{i:3}. {pattern}\n")
    
    # 3. One-line summary files for quick review
    patterns_added_file = os.path.join(output_dir, "patterns_added_oneline.txt")
    with open(patterns_added_file, 'w') as f:
        for pattern in sorted(missing_patterns):
            f.write(f"{pattern}\n")
    
    extra_patterns_file = os.path.join(output_dir, "extra_patterns_oneline.txt")
    with open(extra_patterns_file, 'w') as f:
        for pattern in sorted(extra_patterns):
            f.write(f"{pattern}\n")
    
    # 4. Summary statistics
    summary_file = os.path.join(output_dir, "pattern_addition_summary.md")
    with open(summary_file, 'w') as f:
        f.write(f"# Pattern Addition Summary\n\n")
        f.write(f"**Analysis Date (PDT):** {pdt_str}  \n")
        f.write(f"**Analysis Date (UTC):** {utc_str}\n\n")
        f.write(f"## Results\n\n")
        f.write(f"- **Approved patterns to process:** {len(approved_patterns)}\n")
        f.write(f"- **Patterns already in database:** {len(existing_patterns)}\n")
        f.write(f"- **Patterns successfully added:** {added_count}\n")
        f.write(f"- **Patterns that failed to add:** {failed_count}\n")
        f.write(f"- **Extra patterns in database:** {len(extra_patterns)}\n\n")
        
        # Get final count
        final_count = collection.count_documents({'type': 'REPORT_TYPE'})
        f.write(f"## Database Status\n\n")
        f.write(f"- **Total REPORT_TYPE patterns in database:** {final_count}\n")
        f.write(f"- **Coverage of approved patterns:** {((len(approved_patterns) - len(missing_patterns)) / len(approved_patterns) * 100):.1f}%\n\n")
        
        f.write(f"## Output Files\n\n")
        f.write(f"- `added_patterns.txt` - Detailed list of patterns added\n")
        f.write(f"- `extra_patterns_in_database.txt` - Patterns in database not in approved list\n")
        f.write(f"- `patterns_added_oneline.txt` - One pattern per line (added)\n")
        f.write(f"- `extra_patterns_oneline.txt` - One pattern per line (extra)\n")
    
    print(f"\n✓ Added patterns report: {added_file}")
    print(f"✓ Extra patterns report: {extra_file}")
    print(f"✓ One-line files: {patterns_added_file}, {extra_patterns_file}")
    print(f"✓ Summary report: {summary_file}")
    
    # Final database statistics
    final_count = collection.count_documents({'type': 'REPORT_TYPE'})
    print(f"\n" + "=" * 60)
    print("FINAL SUMMARY:")
    print("=" * 60)
    print(f"Patterns successfully added: {added_count}")
    print(f"Patterns that failed: {failed_count}")
    print(f"Total REPORT_TYPE patterns in database: {final_count}")
    print(f"Extra patterns in database: {len(extra_patterns)}")
    
    client.close()
    print(f"\n✅ All output files saved to: {output_dir}")
    print("✅ Comprehensive pattern addition complete!")

if __name__ == "__main__":
    main()