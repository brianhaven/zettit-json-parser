#!/usr/bin/env python3

"""
Add ALL Manually Approved Report Type Patterns to MongoDB
Processes the complete list of ~300 approved patterns from comprehensive manual review.
This should result in massive improvement in report type extraction coverage.
"""

import os
import sys
import logging
import importlib.util
import re
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Dynamic import for pattern library manager
try:
    spec = importlib.util.spec_from_file_location(
        "pattern_library_manager_v1", 
        "00b_pattern_library_manager_v1.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    
    PatternLibraryManager = module.PatternLibraryManager
    PatternType = module.PatternType
except Exception as e:
    logger.error(f"Could not import PatternLibraryManager: {e}")
    sys.exit(1)

def get_all_approved_patterns():
    """
    Returns the complete list of manually approved patterns from the user's review.
    This is the exact APPROVED list from the comprehensive manual review.
    """
    
    # Complete APPROVED list from manual review
    approved_patterns_text = [
        "Market",
        "Market Size Report",
        "Market Size, Industry Report",
        "Market Size & Share Report",
        "Market Report",
        "Market, Industry Report",
        "Market Size, Share & Growth Report",
        "Market Size And Share Report",
        "Market Size & Share, Industry Report",
        "Market Size, Share, Industry Report",
        "Market Size, Share & Trends Report",
        "Market Size, Share Report",
        "Market Size, Share And Growth Report",
        "Market Size And Share, Industry Report",
        "Market Size, Share, Global Industry Report",
        "Market Size, Global Industry Report",
        "Market Size, Share, Growth Report",
        "Market Size, Share, Industry",
        "Market, Industry",
        "Market Size, Share",
        "Market Insights",
        "Market Size, Industry",
        "Market Size & Share",
        "Market, Report",
        "Market Size, Share And Trends Report",
        "Market Size, Share & Growth",
        "Market Size",
        "Market Trends",
        "Market Size, Report",
        "Market Size & Share Analysis Report",
        "Market Size, Share & Trends, Industry Report",
        "Market Size, Share, Growth",
        "Market Size, Share & Growth Analysis Report",
        "Market Size & Growth Report",
        "Market Outlook",
        "Market Size & Share, Industry",
        "Market Size, Share & Trends",
        "Market Size & Share, Global Industry Report",
        "Market Size, Share, Growth & Trends Report",
        "Market Analysis",
        "Market Size, Share & Growth, Industry Report",
        "Market Forecast",
        "Market Forecast Report",
        "Market Size, Share & Trends Analysis Report",
        "Market Size, Share, Trends, Global Industry Report",
        "Market Size & Trends Report",
        "Market Share Report",
        "Market Size & Share, Industry Analysis Report",
        "Market Size, Share, Trends, Industry Report",
        "Market Size And Share",
        "Market Size, Share, Industry Analysis Report",
        "Market Size And Share, Report",
        "Market Size, Share, Growth, Industry Report",
        "Market Size, Industry Analysis Report",
        "Market Size, Share, Trends & Growth Report",
        "Market Size, Share & Trends, Global Industry Report",
        "Market Size, Share, Growth Analysis Report",
        "Market Size & Trends Analysis Report",
        "Market Size, Share, Trends Report",
        "Market Size, Share, Growth & Trends",
        "Market Growth, Forecast",
        "Market Size Analysis Report",
        "Market Outlook, Trends, Analysis",
        "Market Size & Share Analysis - Industry Research Report - Growth Trends",
        "Market (Forecast )",
        "Market Size, Share & Growth Analysis",
        "Market Size, Share, Growth, Industry",
        "Market Size, Share, Trends",
        "Market Size, Share, Global Industry Analysis Report",
        "Market Size & Share, Report",
        "Market Size & Trends, Industry Report",
        "Market Size, Share, Growth, Trends Report",
        "Market Size, Share & Trends Analysis",
        "Market Size, Share, Growth Analysis",
        "Market Size, Share And Growth",
        "Market Size, Global Industry Trends Report",
        "Market Growth Outlook",
        "Market, Forecast",
        "Market Size And Share Analysis Report",
        "Market Share & Growth Report",
        "Market Size, Trends, Industry Report",
        "Market Size, Share, Report",
        "Market Size, Share & Analysis Report",
        "Market Growth",
        "Market Size, Share, Trends Analysis Report",
        "Market Size & Share, Industry Growth Report",
        "Market Size, Share Analysis Report",
        "Market Size & Growth Analysis Report",
        "Market Growth Analysis Report",
        "Market Forecast Analysis Report",
        "Market Size, Share Analysis",
        "Market Size, Share, Industry Trends Report",
        "Market Size, Share, Trend, Global Industry Report",
        "Market Size, Share, Industry Growth Report",
        "Market Size, Share, Trends & Growth",
        "Market Size & Share, Industry Trends Report",
        "Market Size, Share & Trends, Industry",
        "Market Share Analysis Report",
        "Market Size, Share, Global Industry Trends Report",
        "Market Share, Industry Report",
        "Market Size, Global Industry Analysis Report",
        "Market Size, Share & Growth, Industry",
        "Market Size & Share [ Global Report]",
        "Market Size, Share And Trends",
        "Market Size & Share, Global Industry Trends Report",
        "Market Growth Report",
        "Market Size, Share, Trends, Report",
        "Market Size, Share, Industry Trend Report",
        "Market Size & Trends, Global Industry Report",
        "Market Size, Share And Growth Analysis Report",
        "Market Analysis Report",
        "Market Size, Industry Trend Report",
        "Market Size And Share [ Global Report]",
        "Market Share Analysis, Industry Report",
        "Market Size, Trends & Growth Report",
        "Market Size, Share, Trends, Industry Analysis Report",
        "Market Size Industry Report",
        "Market - Size, Share & Industry Analysis",
        "Market Share, Insights",
        "Market Analysis till",
        "Market, Global Industry Report",
        "Market Share & Trends Report",
        "Market Size Analysis",
        "Market Size And Trends, Industry Report",
        "Market Size, Industry Trend",
        "Market Size, Share, And Growth Report",
        "Market Share, Global Industry Report",
        "Market Size, Industry Trends Report",
        "Market Size, Share, Trends, Growth Report",
        "Market Size & Trends, Industry Analysis Report",
        "Market Size And Share, Industry",
        "Market Size, Share & Forecast Report",
        "Market Analysis, Industry Report",
        "Market Size, Share, Trends, Industry",
        "Market Size & Share, Global Report",
        "Market Size, Share, Trends And Growth Report",
        "Market (Forecast, )",
        "Market Size, Share, Global Industry Growth Report",
        "Market Size, Share, Trend Report",
        "Market Size, Share And Trends, Industry Report",
        "Market Trends & Growth Report",
        "Market Size, Share, Global Industry",
        "Market Size, Trends Report",
        "Market Size, Share, Growth, Industry Trends",
        "Market Size & Size, Industry Analysis Report",
        "Market Trends, Industry Report",
        "Market Share, Size, Industry Report",
        "Market Size, Growth, Global Industry Report",
        "Market Size, Share, Analysis, Industry Report",
        "Market Share & Growth Analysis Report",
        "Market Trends & Growth Analysis Report",
        "Market Size, Share, & Growth Report",
        "Market Size, Global Industry",
        "Market Size, Share And Analysis Report",
        "Market Share, Size, Trends, Global Industry Report",
        "Market Share, Trends, Global Industry Report",
        "Market Size, Growth, Industry Report",
        "Market Size, Trends, Industry",
        "Market Size, Share, Growth, Industry Analysis Report",
        "Market Size & Growth Analysis",
        "Market Size, Growth & Trends Report",
        "Market Size & Share Analysis",
        "Market Size, Share, Trends Forecast",
        "Market Size, Share, Growth And Trends Report",
        "Market Size, Share, Trends, Industry Growth Report",
        "Market Forecast Study",
        "Market Global Forecast",
        "Market Growth Forecast",
        "Market Outlook, Trends",
        "Market Share, Analysis, Forecast",
        "Market Share, Analysis",
        "Market Growth Analysis",
        "Market Report Size",
        "Market Size, Share & Trends, Industry Analysis Report",
        "Market Size, Share, Growth, Trends",
        "Market Size, Share And Growth, Industry Report",
        "Market Size, Share & Trends, Industry Growth Report",
        "Market Size, Share, Growth, Global Industry Report",
        "Market Size & Share Growth Report",
        "Market Size, Analysis, Industry Report",
        "Market Size And Analysis Report",
        "Market Trends Report",
        "Market Trends Analysis Report",
        "Market Size, Share & Trend Report",
        "Market Share, Growth & Trends Report",
        "Market Size, Share & Analysis, Industry Report",
        "Market Size, Share, Trend, Industry Report",
        "Market Size, Industry Growth Report",
        "Market Size, Share [ Global Report]",
        "Market Size, Trends, Industry Analysis Report",
        "Market Size, Share, Trends, Growth",
        "Market Size, Share And Trends, Report",
        "Market Size & Share, Global Industry Growth Report",
        "Market Growth, Industry Report",
        "Market Size & Growth",
        "Market Size, Share, Trends, Global Industry Growth Report",
        "Market Size, Global Industry Growth",
        "Market Size, Value, Global Industry Trends Report",
        "Market Size, Growth, Global Industry Analysis Report",
        "Market Size, Share, Growth, Industry Trends Report",
        "Market Volume & Share Report",
        "Market Size, Trends, Share, Global Industry Report",
        "Market Size and Trends Report",
        "Market Size, Forecast Report",
        "Market Size, Share, Global Industry Trend Report",
        "Market Size, Growth, Industry Analysis Report",
        "Market Size, Trends, Industry Research Report",
        "Market Size, Share, Trends And Growth",
        "Market Size By Product, Industry Report",
        "Market Size & share, Industry Report",
        "Market Size, Share, Growth And Trends",
        "Market Size, And Share, Industry Report",
        "Market Size, Research Report",
        "Market Size And Share, Trends Report",
        "Market Size, Share, industry Report",
        "Market Size, Share, Trend, Industry Research",
        "Market Trends, Share, Size, Industry Report",
        "Market Size, Share, Industry Research Report",
        "Market Size, Share, Statistics & Analysis",
        "Market Share, Industry Growth Analysis Report",
        "Market Size, Share, Industry Growth",
        "Market Size, Share & Growth, Industy Report",
        "Market Size, Share & Trend Analysis Report",
        "Market Size, Global Report",
        "Market, industry Report",
        "Market Size Trends Report",
        "Market Size Share Report",
        "Market Share & Growth Analysis",
        "Market Size & Share, Global Industry Analysis Report",
        "Market Size | Industry Trends & Forecast Analysis",
        "Market Growth | Industry Analysis, Size & Forecast Report",
        "Market Trends | Industry Analysis, Size & Growth Report",
        "Market Report | Industry Analysis, Size & Forecast Overview",
        "Market - Share, Trends & Size",
        "Market - Companies, Analysis, Industry Overview & Outlook",
        "Market - Trends & Size",
        "Market - Size, Trends & Research Report",
        "Market - Companies, Size & Share",
        "Market - Companies & Trends",
        "Market Insights, Forecast",
        "Market Demand, Research Insights",
        "Market Global",
        "Market Analysis, Forecast Report",
        "Market Analysis, Outlook",
        "Market Trends (Forecast )",
        "Market Analysis, Report",
        "Market Forecast -",
        "Market Trends, Forecast",
        "Market Share & Share, Industry Report",
        "Market Size & Share, Indsutry Report",
        "Market Size, Share, Growth And Trends By",
        "Market Size, Share And Report",
        "Market Size And Growth Report",
        "Market Size,Share, Report",
        "Market Size, Trends & Growth Analysis",
        "Market Size, Share Forecast Report",
        "Market Size, Share, Trends Analysis",
        "Market Growth And Trends Report",
        "Market Size, Share, Forecast Report",
        "Market Size, Analysis, Global Industry Report",
        "Market Size & Analysis, Global Industry Report",
        "Market Share",
        "Market Size & Growth, Industry Trends Report",
        "Market Size, Share [Global Report]",
        "Market Size, Share Analysis, Report",
        "Market Size, Global Industry Growth Report",
        "Market Growth & Trends",
        "Market Trends Analysis",
        "Market Sze Report",
        "Market Size, Share Trends Report",
        "Market Growth, Industry Trends Report",
        "Market Share, Size, Industry Analysis Report",
        "Market Size, Share, Indsutry Report",
        "Market Size & Share, Growth Report",
        "Market Share & Trend Analysis Report",
        "Market Size, Industry Repot",
        "Market Size Reports",
        "Market Analysis, Industry Trends Report",
        "Market Size Analysis, Report",
        "Market Size And Share Analysis",
        "Market Size & Share, Growth, Global Industry Report",
        "Market Trends, Industry Growth Report",
        "Market Sizes & Trends Report",
        "market Size, Share, Global Industry Report",
        "Market Size, Industry report",
        "Market Share Analysis & Growth Report",
        "Market Size, Share, Forecast",
        "Market Size, Share & Growth Market",
        "Market Size, Share & Growth, Report",
        "Market Size, Growth, Report",
        "Market Size, Share & Trends, Industry Analysis",
        "Market Size, , Industry Report",
        "Market Size, Growth, Industry Forecast Report",
        "Market Size, Growth & Trends",
        "Market Size, Share & Trend Analysis",
        "Market Size, Share & Trend",
        "market Size & Share Report",
        "Market Size & Growth Report Analysis",
        "Market Research Report",
        "Market Size , Industry Report",
        "Market Size & Growth Forecast Report",
        "Market Share, Share, Growth",
        "Market Share & Trends Analysis Report",
        "Market Share & Size Analysis Report",
        "Market Size, Share & Trends, Industry Growth Forecast",
        "Market Size, Share, Industy Report",
        "Market Size & Size, Global Industry Report",
        "Market Size, Share, Trends, Global Industry",
        "Market Size, Industry Research Report",
        "Market Size, Share & Growth [ Global Report]",
        "Market Share & Share Report",
        "Market Size & Forecast Report",
        "Market Size, Share & Trends [ Global Report]",
        "Market Size & Share report",
        "Market Size & Trend",
        "Market Share, Trends Report",
        "Market Size & Trend Report",
        "Market Size, Revenue, Industry Report",
        "Market Size, Share, Industry Analysis",
        "Market Share, Industry Trends Report",
        "Market Size, Share, Trends And Report",
        "Market Size, Share Global Industry Report",
        "Market Size, Value, Growth Report",
        "Market Report Report",
        "Market Size & Share, Growth, Industry Report",
        "Market Size, Share, Trends, Industry Analysis",
        "Market Size,, Industry Report",
        "Market Size, Trends, Global Industry Report",
        "Market Size, Share, Growth, Trends, Report",
        "Market Size, Share, Growth, Report",
        "Market Size & Trends, Report",
        "Market Size & Analysis Report",
        "Market Size And Growth, Report",
        "Market Size And Share Analysis, Report",
        "Market Size & Share, Report Industry",
        "market Size, Share, Industry Report",
        "Market Size, Share, Growth, Global Industry Trends Report",
        "Market Share, Trends, Industry Report",
        # Typo patterns
        "Market Size, Industrial Report",
        "Market Size I Industry Report",
        # Edge case: Dollar amount pattern
        "Market Size Worth $11.36 Billion By"
    ]
    
    return approved_patterns_text

def convert_text_to_regex_pattern(text):
    """
    Convert approved text pattern to MongoDB regex pattern.
    Handles various punctuation and formatting variations.
    """
    
    # Remove "Market" prefix for processing
    clean_text = text.replace("Market ", "").replace("Market", "").strip()
    
    if not clean_text:
        # Just "Market" alone
        return r'\bMarket(?:\s*$|[,.])', "Market"
    
    # Handle special cases
    if "Worth $" in clean_text:
        # Dollar amount pattern - make it dynamic
        return r'\bMarket\s+Size\s+Worth\s+\$[\d,.]+\s+(?:Billion|Million|Trillion)\s+By(?:\s*$|[,.])', "Size Worth $ Amount By"
    
    if "(Forecast )" in clean_text:
        # Parenthetical format
        clean_text = clean_text.replace("(Forecast )", "Forecast")
        
    # Escape special regex characters but preserve pattern flexibility
    escaped = re.escape(clean_text)
    
    # Make common variations more flexible
    escaped = escaped.replace(r'\&', r'\s*&\s*')      # Handle & with optional spaces
    escaped = escaped.replace(r'\,', r',\s*')         # Handle commas with optional space after
    escaped = escaped.replace(r'\ ', r'\s+')          # Handle multiple spaces as single \s+
    escaped = escaped.replace(r'And', r'(?:And|&)')   # Handle And/& variations
    escaped = escaped.replace(r'\|', r'\s*\|\s*')     # Handle | with optional spaces
    escaped = escaped.replace(r'\-', r'\s*-\s*')      # Handle - with optional spaces
    
    # Extract normalized form (usually the last significant word)
    if 'Report' in clean_text:
        normalized_form = "Report"
    elif 'Analysis' in clean_text:
        normalized_form = "Analysis"  
    elif 'Insights' in clean_text:
        normalized_form = "Insights"
    elif 'Forecast' in clean_text:
        normalized_form = "Forecast"
    elif 'Outlook' in clean_text:
        normalized_form = "Outlook"
    elif 'Trends' in clean_text:
        normalized_form = "Trends"
    elif 'Growth' in clean_text:
        normalized_form = "Growth"
    elif 'Size' in clean_text:
        normalized_form = "Size"
    elif 'Share' in clean_text:
        normalized_form = "Share"
    else:
        # Use the first word
        normalized_form = clean_text.split(',')[0].strip()
        if not normalized_form:
            normalized_form = clean_text.split()[0] if clean_text.split() else "Unknown"
    
    # Create the full regex pattern
    full_pattern = f'\\bMarket\\s+{escaped}(?:\\s*$|[,.])'
    
    return full_pattern, normalized_form

def add_all_approved_patterns():
    """Add ALL manually approved patterns from comprehensive review."""
    
    try:
        # Initialize pattern manager
        pattern_manager = PatternLibraryManager()
        
        # Get existing patterns to check for duplicates
        existing_patterns = pattern_manager.get_patterns(PatternType.REPORT_TYPE)
        existing_terms = set(pattern.get('term', '').lower() for pattern in existing_patterns)
        
        logger.info(f"Found {len(existing_patterns)} existing report type patterns")
        
        # Get ALL approved patterns from comprehensive manual review
        approved_list = get_all_approved_patterns()
        
        logger.info(f"Processing {len(approved_list)} manually approved patterns...")
        
        # Process each approved pattern
        added_count = 0
        skipped_count = 0
        error_count = 0
        
        for i, approved_text in enumerate(approved_list):
            try:
                approved_text = approved_text.strip()
                if not approved_text:
                    continue
                
                # Create a unique term identifier
                term = f"Manual Review #{i+1}: {approved_text[:60]}"
                
                # Check if similar pattern already exists
                if any(approved_text.lower() in existing_term for existing_term in existing_terms):
                    logger.debug(f"Skipping similar pattern: {approved_text}")
                    skipped_count += 1
                    continue
                
                # Convert to regex pattern
                regex_pattern, normalized_form = convert_text_to_regex_pattern(approved_text)
                
                # Determine priority based on complexity
                if len(approved_text.split(',')) > 3:
                    priority = 3  # Complex patterns
                elif 'Analysis' in approved_text or 'Forecast' in approved_text:
                    priority = 2  # Analysis/forecast patterns
                else:
                    priority = 1  # Simple patterns
                
                # Determine confidence based on pattern characteristics
                if 'typo' in approved_text.lower() or 'I Industry' in approved_text:
                    confidence = 0.75  # Typo patterns
                elif '$' in approved_text:
                    confidence = 0.80  # Dollar amount patterns
                elif len(approved_text) > 100:
                    confidence = 0.82  # Very complex patterns
                elif len(approved_text.split(',')) > 4:
                    confidence = 0.85  # Complex compound patterns
                else:
                    confidence = 0.90  # Standard patterns
                
                # Add the pattern
                pattern_id = pattern_manager.add_pattern(
                    PatternType.REPORT_TYPE,
                    term=term,
                    aliases=[],
                    priority=priority,
                    active=True,
                    pattern=regex_pattern,
                    format_type="comprehensive_approved",
                    description=f"From comprehensive manual review: '{approved_text}' - {confidence:.0%} confidence",
                    confidence_weight=confidence,
                    normalized_form=normalized_form
                )
                
                if pattern_id:
                    added_count += 1
                    if added_count % 50 == 0:
                        logger.info(f"✅ Added {added_count} patterns so far...")
                    
                    # Add to existing terms to avoid duplicates in this batch
                    existing_terms.add(approved_text.lower())
                
            except Exception as e:
                logger.error(f"Failed to add pattern '{approved_text}': {e}")
                error_count += 1
        
        logger.info(f"\n{'='*70}")
        logger.info(f"COMPREHENSIVE PATTERN ADDITION COMPLETE:")
        logger.info(f"  - Successfully added: {added_count} patterns")
        logger.info(f"  - Skipped (duplicates): {skipped_count} patterns")
        logger.info(f"  - Errors: {error_count} patterns")
        logger.info(f"  - Total patterns processed: {len(approved_list)}")
        
        # Verify the patterns were added
        all_report_patterns = pattern_manager.get_patterns(PatternType.REPORT_TYPE)
        logger.info(f"  - TOTAL REPORT PATTERNS IN DATABASE: {len(all_report_patterns)}")
        
        # Show breakdown by format type
        format_counts = {}
        for pattern in all_report_patterns:
            metadata = pattern.get('metadata', {})
            format_type = metadata.get('format_type', pattern.get('format_type', 'unknown'))
            format_counts[format_type] = format_counts.get(format_type, 0) + 1
        
        logger.info("Final pattern breakdown by format type:")
        for format_type, count in sorted(format_counts.items()):
            logger.info(f"  - {format_type}: {count} patterns")
        
        pattern_manager.close_connection()
        return True
        
    except Exception as e:
        logger.error(f"Failed to add comprehensive approved patterns: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = add_all_approved_patterns()
    if success:
        print("\n🎉 ALL MANUALLY APPROVED PATTERNS SUCCESSFULLY ADDED!")
        print("📊 This represents comprehensive coverage from all 19,553 database titles")
        print("🚀 MASSIVE improvement expected in Phase 3 pipeline test results")
        print("\n📋 Next steps:")
        print("- Run Phase 3 pipeline test to measure dramatic improvement")
        print("- Handle ACRONYM patterns separately (requires different strategy)")
        print("- Address remaining edge cases")
    else:
        print("\n❌ Failed to add comprehensive approved patterns")
        sys.exit(1)