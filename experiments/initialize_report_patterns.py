#!/usr/bin/env python3

"""
Initialize Report Type Patterns in MongoDB
Populates the pattern_libraries collection with report type extraction patterns.
"""

import os
import logging
from dotenv import load_dotenv
from pattern_library_manager_v1 import PatternLibraryManager, PatternType

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def initialize_report_patterns():
    """Initialize report type extraction patterns in MongoDB pattern_libraries collection."""
    
    # Load environment variables
    load_dotenv()
    
    try:
        # Initialize pattern manager
        pattern_manager = PatternLibraryManager()
        
        # Define core report type patterns by format type
        # NOTE: These are CORE patterns without dates - smart combination logic handles date variations
        report_patterns = [
            # Terminal type patterns (at end of title, after dates removed)
            {
                "type": "report_type",
                "term": "Market Report Terminal",
                "pattern": r'\bMarket\s+(Report)\s*$',
                "format_type": "terminal_type",
                "description": "Market Report at end: 'Global AI Market Report'",
                "priority": 1,
                "active": True,
                "confidence_weight": 0.92,
                "normalized_form": "Report"
            },
            {
                "type": "report_type",
                "term": "Analysis Terminal",
                "pattern": r'\b(Analysis)\s*$',
                "format_type": "terminal_type",
                "description": "Analysis at end: 'Healthcare Technology Analysis'",
                "priority": 2,
                "active": True,
                "confidence_weight": 0.90,
                "normalized_form": "Analysis"
            },
            {
                "type": "report_type",
                "term": "Study Terminal",
                "pattern": r'\b(Study)\s*$',
                "format_type": "terminal_type",
                "description": "Study at end: 'Consumer Electronics Study'",
                "priority": 3,
                "active": True,
                "confidence_weight": 0.90,
                "normalized_form": "Study"
            },
            {
                "type": "report_type",
                "term": "Research Terminal",
                "pattern": r'\b(Research)\s*$',
                "format_type": "terminal_type",
                "description": "Research at end: 'Market Research'",
                "priority": 4,
                "active": True,
                "confidence_weight": 0.88,
                "normalized_form": "Research"
            },
            {
                "type": "report_type",
                "term": "Outlook Terminal",
                "pattern": r'\b(Outlook)\s*$',
                "format_type": "terminal_type",
                "description": "Outlook at end: 'Technology Outlook'",
                "priority": 5,
                "active": True,
                "confidence_weight": 0.88,
                "normalized_form": "Outlook"
            },
            {
                "type": "report_type",
                "term": "Forecast Terminal",
                "pattern": r'\b(Forecast)\s*$',
                "format_type": "terminal_type",
                "description": "Forecast at end: 'Industry Forecast'",
                "priority": 6,
                "active": True,
                "confidence_weight": 0.87,
                "normalized_form": "Forecast"
            },
            
            # Embedded type patterns (within title text)
            {
                "type": "report_type",
                "term": "Market Research Embedded",
                "pattern": r'\bMarket\s+(Research)\b',
                "format_type": "embedded_type",
                "description": "Market Research within text: 'Global Market Research Overview'",
                "priority": 1,
                "active": True,
                "confidence_weight": 0.85,
                "normalized_form": "Research"
            },
            {
                "type": "report_type",
                "term": "Industry Analysis Embedded",
                "pattern": r'\bIndustry\s+(Analysis)\b',
                "format_type": "embedded_type",
                "description": "Industry Analysis within text: 'Healthcare Industry Analysis Report'",
                "priority": 2,
                "active": True,
                "confidence_weight": 0.84,
                "normalized_form": "Analysis"
            },
            {
                "type": "report_type",
                "term": "Market Intelligence Embedded",
                "pattern": r'\bMarket\s+(Intelligence)\b',
                "format_type": "embedded_type",
                "description": "Market Intelligence within text: 'Digital Market Intelligence'",
                "priority": 3,
                "active": True,
                "confidence_weight": 0.83,
                "normalized_form": "Intelligence"
            },
            {
                "type": "report_type",
                "term": "Market Insights Embedded",
                "pattern": r'\bMarket\s+(Insights)\b',
                "format_type": "embedded_type",
                "description": "Market Insights within text: 'AI Market Insights'",
                "priority": 4,
                "active": True,
                "confidence_weight": 0.82,
                "normalized_form": "Insights"
            },
            {
                "type": "report_type",
                "term": "Market Assessment Embedded",
                "pattern": r'\bMarket\s+(Assessment)\b',
                "format_type": "embedded_type",
                "description": "Market Assessment within text: 'Technology Market Assessment'",
                "priority": 5,
                "active": True,
                "confidence_weight": 0.81,
                "normalized_form": "Assessment"
            },
            
            # Prefix type patterns (at start of title)
            {
                "type": "report_type",
                "term": "Report Prefix",
                "pattern": r'^(Report):\s*',
                "format_type": "prefix_type",
                "description": "Report prefix: 'Report: Global Semiconductors'",
                "priority": 1,
                "active": True,
                "confidence_weight": 0.90,
                "normalized_form": "Report"
            },
            {
                "type": "report_type",
                "term": "Analysis Prefix",
                "pattern": r'^(Analysis):\s*',
                "format_type": "prefix_type",
                "description": "Analysis prefix: 'Analysis: 5G Technology'",
                "priority": 2,
                "active": True,
                "confidence_weight": 0.89,
                "normalized_form": "Analysis"
            },
            {
                "type": "report_type",
                "term": "Study Prefix",
                "pattern": r'^(Study):\s*',
                "format_type": "prefix_type",
                "description": "Study prefix: 'Study: Electric Vehicles'",
                "priority": 3,
                "active": True,
                "confidence_weight": 0.88,
                "normalized_form": "Study"
            },
            {
                "type": "report_type",
                "term": "Research Prefix",
                "pattern": r'^(Research):\s*',
                "format_type": "prefix_type",
                "description": "Research prefix: 'Research: AI Technology'",
                "priority": 4,
                "active": True,
                "confidence_weight": 0.87,
                "normalized_form": "Research"
            },
            {
                "type": "report_type",
                "term": "Market Report Prefix",
                "pattern": r'^Market\s+(Report):\s*',
                "format_type": "prefix_type",
                "description": "Market Report prefix: 'Market Report: Global AI'",
                "priority": 5,
                "active": True,
                "confidence_weight": 0.91,
                "normalized_form": "Report"
            },
            
            # Compound type patterns (multiple word report types)
            {
                "type": "report_type",
                "term": "Market Research Report",
                "pattern": r'\bMarket\s+(Research\s+Report)\b',
                "format_type": "compound_type",
                "description": "Market Research Report: 'Global Market Research Report'",
                "priority": 1,
                "active": True,
                "confidence_weight": 0.95,
                "normalized_form": "Research Report"
            },
            {
                "type": "report_type",
                "term": "Industry Intelligence Report",
                "pattern": r'\bIndustry\s+(Intelligence\s+Report)\b',
                "format_type": "compound_type",
                "description": "Industry Intelligence Report: 'Healthcare Industry Intelligence Report'",
                "priority": 2,
                "active": True,
                "confidence_weight": 0.94,
                "normalized_form": "Intelligence Report"
            },
            {
                "type": "report_type",
                "term": "Market Size Report",
                "pattern": r'\bMarket\s+Size\s+(Report)\b',
                "format_type": "compound_type",
                "description": "Market Size Report: 'Global Market Size Report'",
                "priority": 3,
                "active": True,
                "confidence_weight": 0.93,
                "normalized_form": "Size Report"
            },
            {
                "type": "report_type",
                "term": "Market Share Analysis",
                "pattern": r'\bMarket\s+Share\s+(Analysis)\b',
                "format_type": "compound_type",
                "description": "Market Share Analysis: 'Industry Market Share Analysis'",
                "priority": 4,
                "active": True,
                "confidence_weight": 0.92,
                "normalized_form": "Share Analysis"
            },
            {
                "type": "report_type",
                "term": "Research Study",
                "pattern": r'\b(Research\s+Study)\b',
                "format_type": "compound_type",
                "description": "Research Study: 'Technology Research Study'",
                "priority": 5,
                "active": True,
                "confidence_weight": 0.91,
                "normalized_form": "Research Study"
            },
            {
                "type": "report_type",
                "term": "Market Overview",
                "pattern": r'\bMarket\s+(Overview)\b',
                "format_type": "compound_type",
                "description": "Market Overview: 'Global Market Overview'",
                "priority": 6,
                "active": True,
                "confidence_weight": 0.90,
                "normalized_form": "Overview"
            },
            
            # Additional embedded patterns for common variations
            {
                "type": "report_type",
                "term": "Market Trends Embedded",
                "pattern": r'\bMarket\s+(Trends)\b',
                "format_type": "embedded_type",
                "description": "Market Trends within text: 'AI Market Trends'",
                "priority": 6,
                "active": True,
                "confidence_weight": 0.80,
                "normalized_form": "Trends"
            },
            {
                "type": "report_type",
                "term": "Market Overview Embedded",
                "pattern": r'\bMarket\s+(Overview)\b',
                "format_type": "embedded_type",
                "description": "Market Overview within text: 'Technology Market Overview'",
                "priority": 7,
                "active": True,
                "confidence_weight": 0.79,
                "normalized_form": "Overview"
            },
            
            # Terminal patterns for standalone report types
            {
                "type": "report_type",
                "term": "Intelligence Terminal",
                "pattern": r'\b(Intelligence)\s*$',
                "format_type": "terminal_type",
                "description": "Intelligence at end: 'Market Intelligence'",
                "priority": 7,
                "active": True,
                "confidence_weight": 0.86,
                "normalized_form": "Intelligence"
            },
            {
                "type": "report_type",
                "term": "Insights Terminal",
                "pattern": r'\b(Insights)\s*$',
                "format_type": "terminal_type",
                "description": "Insights at end: 'Market Insights'",
                "priority": 8,
                "active": True,
                "confidence_weight": 0.85,
                "normalized_form": "Insights"
            },
            {
                "type": "report_type",
                "term": "Assessment Terminal",
                "pattern": r'\b(Assessment)\s*$',
                "format_type": "terminal_type",
                "description": "Assessment at end: 'Technology Assessment'",
                "priority": 9,
                "active": True,
                "confidence_weight": 0.84,
                "normalized_form": "Assessment"
            },
            {
                "type": "report_type",
                "term": "Overview Terminal",
                "pattern": r'\b(Overview)\s*$',
                "format_type": "terminal_type",
                "description": "Overview at end: 'Industry Overview'",
                "priority": 10,
                "active": True,
                "confidence_weight": 0.83,
                "normalized_form": "Overview"
            }
        ]
        
        logger.info(f"Initializing {len(report_patterns)} core report type patterns...")
        
        # Add each report pattern to the collection
        added_count = 0
        skipped_count = 0
        
        for pattern_data in report_patterns:
            try:
                # Check if pattern already exists
                existing = pattern_manager.search_patterns(pattern_data["term"])
                if existing:
                    logger.debug(f"Skipping existing pattern: {pattern_data['term']}")
                    skipped_count += 1
                    continue
                
                # Add the pattern
                pattern_id = pattern_manager.add_pattern(
                    PatternType.REPORT_TYPE,
                    term=pattern_data["term"],
                    aliases=[],
                    priority=pattern_data["priority"],
                    active=pattern_data["active"],
                    pattern=pattern_data["pattern"],
                    format_type=pattern_data["format_type"],
                    description=pattern_data["description"],
                    confidence_weight=pattern_data["confidence_weight"],
                    normalized_form=pattern_data["normalized_form"]
                )
                
                if pattern_id:
                    added_count += 1
                    logger.debug(f"Added pattern: {pattern_data['term']} ({pattern_data['format_type']})")
                
            except Exception as e:
                logger.error(f"Failed to add pattern {pattern_data['term']}: {e}")
        
        logger.info(f"Report pattern initialization complete:")
        logger.info(f"  - Added: {added_count} patterns")
        logger.info(f"  - Skipped (existing): {skipped_count} patterns")
        logger.info(f"  - Total patterns defined: {len(report_patterns)}")
        
        # Verify the patterns were added
        all_report_patterns = pattern_manager.get_patterns(PatternType.REPORT_TYPE)
        logger.info(f"  - Total report patterns in database: {len(all_report_patterns)}")
        
        # Show breakdown by format type
        format_counts = {}
        for pattern in all_report_patterns:
            format_type = pattern.get('format_type', 'unknown')
            format_counts[format_type] = format_counts.get(format_type, 0) + 1
        
        logger.info("Report patterns by format type:")
        for format_type, count in format_counts.items():
            logger.info(f"  - {format_type}: {count} patterns")
        
        pattern_manager.close_connection()
        print("✅ Report pattern initialization completed successfully!")
        return True
        
    except Exception as e:
        logger.error(f"Failed to initialize report patterns: {e}")
        print(f"❌ Report pattern initialization failed: {e}")
        return False


if __name__ == "__main__":
    success = initialize_report_patterns()
    exit(0 if success else 1)