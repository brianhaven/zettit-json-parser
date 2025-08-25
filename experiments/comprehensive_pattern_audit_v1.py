#!/usr/bin/env python3
"""
Comprehensive Pattern Audit - Phase 3.6
Audits all approved patterns from user's manual review vs actual database patterns.

This script addresses the critical issue: "I want you to review the several hundred 
report types I approved, as well as those in the pattern_libraries collection and 
make sure everything was properly added"
"""

import os
import re
import sys
from pymongo import MongoClient
from dotenv import load_dotenv
from datetime import datetime, timezone
from collections import defaultdict
import json

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

def get_approved_patterns_from_user():
    """
    Return the comprehensive list of patterns approved by the user during manual review.
    This represents what SHOULD be in the database.
    """
    
    # Tier 1: Agreed - Basic report types (37 patterns)
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
    
    # Tier 2: Compound patterns (46 patterns)
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
        "Market Size, Share, Industry Data", "Market Size And Share", 
        "Market Size, Share", "Market Size, Share & Trends"
    ]
    
    # Tier 3: Industry & Trends combinations (30 patterns)
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
    
    # Tier 4: Specialized & Technical patterns (50 patterns)
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
    
    # Tier 5: Additional approved patterns (48 patterns)  
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
    
    # Tier 6: Geographic & Regional patterns (37 patterns)
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
    
    # Combine all approved patterns
    all_approved = tier1 + tier2 + tier3 + tier4 + tier5 + tier6
    
    # Create categorized structure
    approved_patterns = {
        'Tier 1 - Basic Types': tier1,
        'Tier 2 - Size & Share Compounds': tier2,
        'Tier 3 - Industry & Trends': tier3,
        'Tier 4 - Specialized & Technical': tier4,
        'Tier 5 - Additional Approved': tier5,
        'Tier 6 - Geographic & Regional': tier6
    }
    
    return all_approved, approved_patterns

def get_database_patterns():
    """Get all REPORT_TYPE patterns currently in the database"""
    
    client = MongoClient(os.getenv('MONGODB_URI'))
    db = client['deathstar']
    collection = db['pattern_libraries']
    
    # Get all report type patterns
    patterns = list(collection.find({
        'type': 'REPORT_TYPE',
        'active': True
    }))
    
    # Extract terms for comparison
    db_terms = [p['term'] for p in patterns]
    
    return patterns, db_terms

def audit_pattern_implementation():
    """Compare approved patterns with database patterns"""
    
    # Get approved patterns
    approved_list, approved_categories = get_approved_patterns_from_user()
    
    # Get database patterns  
    db_patterns, db_terms = get_database_patterns()
    
    # Analysis
    total_approved = len(approved_list)
    total_in_db = len(db_terms)
    
    # Find missing patterns (approved but not in DB)
    missing_patterns = [term for term in approved_list if term not in db_terms]
    
    # Find extra patterns (in DB but not approved)
    extra_patterns = [term for term in db_terms if term not in approved_list]
    
    # Find correctly implemented patterns
    implemented_patterns = [term for term in approved_list if term in db_terms]
    
    return {
        'total_approved': total_approved,
        'total_in_db': total_in_db,
        'implemented_count': len(implemented_patterns),
        'missing_count': len(missing_patterns),
        'extra_count': len(extra_patterns),
        'missing_patterns': missing_patterns,
        'extra_patterns': extra_patterns,
        'implemented_patterns': implemented_patterns,
        'approved_categories': approved_categories,
        'db_patterns': db_patterns
    }

def generate_audit_report(audit_results, output_dir):
    """Generate comprehensive audit report"""
    
    pdt_time, utc_time = get_pdt_timestamp()
    
    # Main report
    report_content = f"""# Comprehensive Pattern Audit Report - Phase 3.6

**Analysis Date (PDT):** {pdt_time}  
**Analysis Date (UTC):** {utc_time}

## Executive Summary

- **Total Approved Patterns:** {audit_results['total_approved']}
- **Total Database Patterns:** {audit_results['total_in_db']}
- **Successfully Implemented:** {audit_results['implemented_count']} ({audit_results['implemented_count']/audit_results['total_approved']*100:.1f}%)
- **Missing from Database:** {audit_results['missing_count']} ({audit_results['missing_count']/audit_results['total_approved']*100:.1f}%)
- **Extra in Database:** {audit_results['extra_count']}

## Implementation Status

### ✅ Successfully Implemented Patterns ({len(audit_results['implemented_patterns'])})

These approved patterns are correctly present in the database:

"""
    
    # Group implemented patterns by category
    for category, patterns in audit_results['approved_categories'].items():
        implemented_in_category = [p for p in patterns if p in audit_results['implemented_patterns']]
        if implemented_in_category:
            report_content += f"\n**{category}:** {len(implemented_in_category)}/{len(patterns)} patterns\n"
            for pattern in implemented_in_category:
                report_content += f"- {pattern}\n"
    
    # Missing patterns
    if audit_results['missing_patterns']:
        report_content += f"\n\n### ❌ Missing from Database ({len(audit_results['missing_patterns'])})\n\n"
        report_content += "These approved patterns are NOT in the database and need to be added:\n\n"
        
        for category, patterns in audit_results['approved_categories'].items():
            missing_in_category = [p for p in patterns if p in audit_results['missing_patterns']]
            if missing_in_category:
                report_content += f"\n**{category}:** {len(missing_in_category)} missing\n"
                for pattern in missing_in_category:
                    report_content += f"- ❌ {pattern}\n"
    
    # Extra patterns
    if audit_results['extra_patterns']:
        report_content += f"\n\n### ⚠️ Extra Patterns in Database ({len(audit_results['extra_patterns'])})\n\n"
        report_content += "These patterns are in the database but were not in the approved list:\n\n"
        for pattern in audit_results['extra_patterns']:
            report_content += f"- {pattern}\n"
    
    # Recommendations
    report_content += f"\n\n## Recommendations\n\n"
    
    if audit_results['missing_patterns']:
        report_content += f"1. **CRITICAL:** Add {len(audit_results['missing_patterns'])} missing approved patterns to database\n"
    
    if audit_results['extra_patterns']:
        report_content += f"2. **Review:** Evaluate {len(audit_results['extra_patterns'])} extra patterns for relevance\n"
    
    if audit_results['implemented_count'] == audit_results['total_approved']:
        report_content += "✅ **All approved patterns successfully implemented!**\n"
    
    # Save main report
    report_file = os.path.join(output_dir, 'comprehensive_pattern_audit.md')
    with open(report_file, 'w') as f:
        f.write(report_content)
    
    # Save detailed JSON data
    json_file = os.path.join(output_dir, 'pattern_audit_data.json')
    with open(json_file, 'w') as f:
        json.dump({
            'audit_summary': {
                'total_approved': audit_results['total_approved'],
                'total_in_db': audit_results['total_in_db'],
                'implemented_count': audit_results['implemented_count'],
                'missing_count': audit_results['missing_count'],
                'extra_count': audit_results['extra_count']
            },
            'missing_patterns': audit_results['missing_patterns'],
            'extra_patterns': audit_results['extra_patterns'],
            'implemented_patterns': audit_results['implemented_patterns'],
            'approved_categories': audit_results['approved_categories'],
            'analysis_date_pdt': pdt_time,
            'analysis_date_utc': utc_time
        }, f, indent=2)
    
    # Save missing patterns for easy import
    if audit_results['missing_patterns']:
        missing_file = os.path.join(output_dir, 'missing_patterns_to_add.txt')
        with open(missing_file, 'w') as f:
            f.write(f"# Missing Patterns to Add - {len(audit_results['missing_patterns'])} patterns\n")
            f.write(f"# Generated: {pdt_time}\n\n")
            for pattern in audit_results['missing_patterns']:
                f.write(f"{pattern}\n")
    
    return report_file, json_file

def main():
    """Main execution"""
    pdt_time, utc_time = get_pdt_timestamp()
    
    print("=" * 80)
    print("COMPREHENSIVE PATTERN AUDIT - Phase 3.6")
    print(f"Analysis Date (PDT): {pdt_time}")
    print(f"Analysis Date (UTC): {utc_time}")
    print("=" * 80)
    print()
    print("This audit addresses the critical requirement:")
    print("'I want you to review the several hundred report types I approved,")
    print("as well as those in the pattern_libraries collection and make sure")
    print("everything was properly added'")
    print()
    
    # Create output directory
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_dir = f"outputs/{timestamp}_comprehensive_audit"
    os.makedirs(output_dir, exist_ok=True)
    
    print("1. Loading approved patterns from user manual review...")
    approved_list, approved_categories = get_approved_patterns_from_user()
    print(f"   ✅ Loaded {len(approved_list)} approved patterns in {len(approved_categories)} categories")
    
    print("\n2. Querying database patterns...")
    db_patterns, db_terms = get_database_patterns()
    print(f"   ✅ Found {len(db_terms)} REPORT_TYPE patterns in database")
    
    print("\n3. Performing comprehensive audit...")
    audit_results = audit_pattern_implementation()
    
    print(f"\n4. Generating audit reports...")
    report_file, json_file = generate_audit_report(audit_results, output_dir)
    
    print(f"\n{'='*80}")
    print("AUDIT RESULTS SUMMARY")
    print(f"{'='*80}")
    print(f"Total Approved Patterns: {audit_results['total_approved']}")
    print(f"Total Database Patterns: {audit_results['total_in_db']}")
    print(f"Successfully Implemented: {audit_results['implemented_count']} ({audit_results['implemented_count']/audit_results['total_approved']*100:.1f}%)")
    print(f"Missing from Database:   {audit_results['missing_count']} ({audit_results['missing_count']/audit_results['total_approved']*100:.1f}%)")
    print(f"Extra in Database:       {audit_results['extra_count']}")
    
    if audit_results['missing_patterns']:
        print(f"\n❌ CRITICAL ISSUE: {audit_results['missing_count']} approved patterns are missing!")
        print("These must be added to resolve extraction failures.")
        
    if audit_results['implemented_count'] == audit_results['total_approved']:
        print("\n✅ SUCCESS: All approved patterns are properly implemented!")
    
    print(f"\nReports saved to:")
    print(f"  - Main Report: {report_file}")
    print(f"  - Data: {json_file}")
    if audit_results['missing_patterns']:
        missing_file = os.path.join(output_dir, 'missing_patterns_to_add.txt')
        print(f"  - Missing Patterns: {missing_file}")

if __name__ == "__main__":
    main()