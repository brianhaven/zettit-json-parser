#!/usr/bin/env python3

import os
import re
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Manual cleanup mappings for comprehensive term standardization
MANUAL_REVIEW_PATTERNS = {
    # Pattern: remove "Manual Review #X: " prefix
    "manual_review_prefix": r"^Manual Review #\d+:\s*"
}

TECHNICAL_SUFFIX_PATTERNS = {
    # Patterns to remove technical suffixes
    "terminal_suffix": r"\s+Terminal\d*$",
    "embedded_suffix": r"\s+Embedded$",
    "prefix_suffix": r"\s+Prefix$"
}

# Specific term corrections based on patterns
SPECIFIC_CORRECTIONS = {
    "Market Size Share Terminal2": "Market Size, Share",  # Based on pattern analysis
    "Market Report Terminal": "Market Report",
    "Analysis Terminal": "Analysis", 
    "Study Terminal": "Study",
    "Research Terminal": "Research",
    "Outlook Terminal": "Outlook",
    "Forecast Terminal": "Forecast",
    "Market Research Embedded": "Market Research",
    "Industry Analysis Embedded": "Industry Analysis",
    "Market Intelligence Embedded": "Market Intelligence", 
    "Market Insights Embedded": "Market Insights",
    "Market Assessment Embedded": "Market Assessment",
    "Report Prefix": "Report",
    "Analysis Prefix": "Analysis",
    "Study Prefix": "Study", 
    "Research Prefix": "Research",
    "Market Report Prefix": "Market Report"
}

def clean_term(term):
    """Clean a single term by removing prefixes and suffixes"""
    cleaned = term
    
    # Step 1: Remove Manual Review prefixes
    cleaned = re.sub(MANUAL_REVIEW_PATTERNS["manual_review_prefix"], "", cleaned, flags=re.IGNORECASE)
    
    # Step 2: Remove technical suffixes
    for suffix_pattern in TECHNICAL_SUFFIX_PATTERNS.values():
        cleaned = re.sub(suffix_pattern, "", cleaned, flags=re.IGNORECASE)
    
    # Step 3: Apply specific corrections
    if cleaned in SPECIFIC_CORRECTIONS:
        cleaned = SPECIFIC_CORRECTIONS[cleaned]
    
    # Clean up extra whitespace
    cleaned = re.sub(r'\s+', ' ', cleaned).strip()
    
    return cleaned

def print_sample_transformations():
    """Print sample transformations for verification"""
    print("Sample Term Transformations:")
    print("=" * 60)
    
    samples = [
        "Manual Review #3: Market Size, Industry Report",
        "Manual Review #4: Market Size & Share Report", 
        "Market Report Terminal",
        "Analysis Terminal",
        "Market Size Share Terminal2",
        "Market Research Embedded",
        "Report Prefix"
    ]
    
    for term in samples:
        cleaned = clean_term(term)
        print(f'"{term}" -> "{cleaned}"')
    
    print("=" * 60)

if __name__ == "__main__":
    print_sample_transformations()
    print(f"\nThis script will clean {len(SPECIFIC_CORRECTIONS) + 251} estimated terms")
    print("Run this with MongoDB connection to apply changes")