#!/usr/bin/env python3
"""
GitHub Issue #17 Phase 2: Evidence-Based Pattern Consolidation Implementation
Analyzes duplicate patterns and applies A/B/C/D categorization framework

Based on 1000-title test findings with expanded scope for comprehensive consolidation.
"""

import os
import sys
import json
import logging
from datetime import datetime
import pytz
from typing import Dict, List, Any, Tuple
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def create_output_directory(script_name: str) -> str:
    """Create timestamped output directory."""
    pdt = pytz.timezone('America/Los_Angeles')
    timestamp = datetime.now(pdt).strftime('%Y%m%d_%H%M%S')
    output_dir = f"../outputs/{timestamp}_{script_name}"
    os.makedirs(output_dir, exist_ok=True)
    return output_dir

def get_duplicate_patterns(collection) -> List[Dict]:
    """Find all patterns with duplicates and analyze them."""
    pipeline = [
        {"$match": {"type": "report_type"}},
        {"$group": {
            "_id": "$pattern",
            "count": {"$sum": 1},
            "documents": {"$push": {
                "id": "$_id",
                "term": "$term",
                "format_type": "$format_type",
                "priority": "$priority",
                "active": "$active",
                "success_count": "$success_count",
                "failure_count": "$failure_count",
                "notes": "$notes",
                "created_date": "$created_date"
            }}
        }},
        {"$match": {"count": {"$gt": 1}}},
        {"$sort": {"count": -1}}
    ]
    
    return list(collection.aggregate(pipeline))

def categorize_duplicate_pattern(pattern_data: Dict) -> Dict:
    """
    Apply A/B/C/D categorization framework to duplicate pattern.
    
    A: PRESERVE - Keep all instances (different legitimate use cases)
    B: CONSOLIDATE - Merge similar patterns with priority resolution
    C: REMOVE - Remove obvious duplicates/noise patterns
    D: INVESTIGATE - Complex cases requiring deeper analysis
    """
    pattern = pattern_data["_id"]
    docs = pattern_data["documents"]
    count = pattern_data["count"]
    
    # Analyze the documents
    terms = [doc["term"] for doc in docs]
    format_types = [doc["format_type"] for doc in docs]
    priorities = [doc["priority"] for doc in docs]
    active_statuses = [doc["active"] for doc in docs]
    notes = [doc.get("notes", "") for doc in docs]
    
    # Unique values
    unique_terms = list(set(terms))
    unique_format_types = list(set(format_types))
    unique_priorities = list(set(priorities))
    unique_active = list(set(active_statuses))
    
    analysis = {
        "pattern": pattern,
        "duplicate_count": count,
        "terms": terms,
        "unique_terms": unique_terms,
        "format_types": format_types,
        "unique_format_types": unique_format_types,
        "priorities": priorities,
        "unique_priorities": unique_priorities,
        "active_statuses": active_statuses,
        "unique_active": unique_active,
        "notes": notes,
        "documents": docs
    }
    
    # Apply categorization logic
    if len(unique_terms) == 1 and len(unique_format_types) == 1:
        if len(unique_priorities) == 1 and len(unique_active) == 1:
            # Exact duplicates - Category C: REMOVE
            analysis["category"] = "C"
            analysis["category_reason"] = "Exact duplicates - same term, format_type, priority, active status"
            analysis["action"] = "Remove duplicate entries, keep one"
            
        elif len(unique_priorities) > 1:
            # Same term/format but different priorities - Category B: CONSOLIDATE
            analysis["category"] = "B"
            analysis["category_reason"] = "Same pattern with conflicting priorities - consolidation needed"
            analysis["action"] = f"Consolidate to single entry with priority {min(priorities)} (lowest wins)"
            
        else:
            # Different active statuses - Category B: CONSOLIDATE
            analysis["category"] = "B" 
            analysis["category_reason"] = "Same pattern with different active statuses"
            analysis["action"] = "Consolidate to active=true (unless explicitly deactivated)"
            
    elif len(unique_terms) > 1 and len(unique_format_types) == 1:
        # Different terms, same format - Category D: INVESTIGATE
        analysis["category"] = "D"
        analysis["category_reason"] = "Different terms sharing same regex pattern - may indicate pattern collision"
        analysis["action"] = "Investigate if pattern is too broad or terms should be separate patterns"
        
    elif len(unique_format_types) > 1:
        # Different format types - Category A: PRESERVE or D: INVESTIGATE
        if len(unique_terms) == 1:
            # Same term, different formats - Category A: PRESERVE
            analysis["category"] = "A"
            analysis["category_reason"] = "Same term with different format types - legitimate variations"
            analysis["action"] = "Preserve all entries - different format types serve different matching purposes"
        else:
            # Different terms AND formats - Category D: INVESTIGATE
            analysis["category"] = "D"
            analysis["category_reason"] = "Complex case with multiple terms and format types"
            analysis["action"] = "Deep investigation required - possible pattern design issues"
    else:
        # Edge cases - Category D: INVESTIGATE
        analysis["category"] = "D"
        analysis["category_reason"] = "Complex duplicate pattern requiring manual review"
        analysis["action"] = "Manual analysis required"
    
    return analysis

def generate_consolidation_plan(duplicate_analyses: List[Dict]) -> Dict:
    """Generate specific consolidation actions for each category."""
    plan = {
        "summary": {
            "total_duplicates": len(duplicate_analyses),
            "category_a_preserve": 0,
            "category_b_consolidate": 0, 
            "category_c_remove": 0,
            "category_d_investigate": 0
        },
        "actions": {
            "A_PRESERVE": [],
            "B_CONSOLIDATE": [],
            "C_REMOVE": [],
            "D_INVESTIGATE": []
        }
    }
    
    for analysis in duplicate_analyses:
        category = analysis["category"]
        
        # Count by category
        if category == "A":
            plan["summary"]["category_a_preserve"] += 1
        elif category == "B":
            plan["summary"]["category_b_consolidate"] += 1
        elif category == "C":
            plan["summary"]["category_c_remove"] += 1
        elif category == "D":
            plan["summary"]["category_d_investigate"] += 1
            
        # Group by action type
        if category == "A":
            plan["actions"]["A_PRESERVE"].append(analysis)
        elif category == "B":
            plan["actions"]["B_CONSOLIDATE"].append(analysis)
        elif category == "C":
            plan["actions"]["C_REMOVE"].append(analysis)
        elif category == "D":
            plan["actions"]["D_INVESTIGATE"].append(analysis)
    
    return plan

def main():
    """Execute GitHub Issue #17 Phase 2 evidence-based pattern consolidation."""
    
    logger.info("Starting GitHub Issue #17 Phase 2: Evidence-Based Pattern Consolidation")
    
    # Connect to MongoDB
    try:
        client = MongoClient(os.getenv('MONGODB_URI'))
        db = client['deathstar']
        collection = db['pattern_libraries']
        logger.info("Connected to MongoDB successfully")
    except Exception as e:
        logger.error(f"Failed to connect to MongoDB: {e}")
        return
    
    # Create output directory
    output_dir = create_output_directory("issue17_phase2_pattern_consolidation")
    logger.info(f"Output directory: {output_dir}")
    
    # Get current timestamps
    pdt = pytz.timezone('America/Los_Angeles')
    utc = pytz.timezone('UTC')
    current_time_pdt = datetime.now(pdt)
    current_time_utc = datetime.now(utc)
    
    # Find all duplicate patterns
    logger.info("Analyzing duplicate patterns...")
    duplicate_patterns = get_duplicate_patterns(collection)
    logger.info(f"Found {len(duplicate_patterns)} patterns with duplicates")
    
    # Categorize each duplicate pattern using A/B/C/D framework
    logger.info("Applying A/B/C/D categorization framework...")
    duplicate_analyses = []
    for pattern_data in duplicate_patterns:
        analysis = categorize_duplicate_pattern(pattern_data)
        duplicate_analyses.append(analysis)
        logger.info(f"Pattern '{analysis['pattern'][:50]}...' -> Category {analysis['category']}: {analysis['action']}")
    
    # Generate consolidation plan
    logger.info("Generating consolidation plan...")
    consolidation_plan = generate_consolidation_plan(duplicate_analyses)
    
    # Write detailed analysis report
    analysis_file = os.path.join(output_dir, "duplicate_pattern_analysis.json")
    with open(analysis_file, 'w') as f:
        json.dump(duplicate_analyses, f, indent=2, default=str)
    logger.info(f"Detailed analysis saved to: {analysis_file}")
    
    # Write consolidation plan
    plan_file = os.path.join(output_dir, "consolidation_plan.json")
    with open(plan_file, 'w') as f:
        json.dump(consolidation_plan, f, indent=2, default=str)
    logger.info(f"Consolidation plan saved to: {plan_file}")
    
    # Generate summary report
    summary_report = f"""# GitHub Issue #17 Phase 2: Evidence-Based Pattern Consolidation Analysis

**Analysis Date (PDT):** {current_time_pdt.strftime('%Y-%m-%d %H:%M:%S %Z')}  
**Analysis Date (UTC):** {current_time_utc.strftime('%Y-%m-%d %H:%M:%S %Z')}

## Executive Summary

Evidence-based analysis of duplicate patterns in MongoDB pattern_libraries collection using A/B/C/D categorization framework validated through 1000-title pipeline testing.

## Duplicate Pattern Analysis Results

- **Total Duplicate Patterns:** {len(duplicate_patterns)}
- **Category A (PRESERVE):** {consolidation_plan['summary']['category_a_preserve']} patterns with legitimate variations
- **Category B (CONSOLIDATE):** {consolidation_plan['summary']['category_b_consolidate']} patterns requiring consolidation  
- **Category C (REMOVE):** {consolidation_plan['summary']['category_c_remove']} exact duplicate patterns
- **Category D (INVESTIGATE):** {consolidation_plan['summary']['category_d_investigate']} complex cases requiring manual review

## Categorization Framework Applied

### Category A: PRESERVE
Patterns with different legitimate use cases (different format types for same term).
**Action:** Keep all instances - serve different matching purposes.

### Category B: CONSOLIDATE  
Similar patterns with priority conflicts or status differences.
**Action:** Merge with consistent priority (lowest wins) and active status resolution.

### Category C: REMOVE
Exact duplicates with identical term, format_type, priority, and active status.
**Action:** Remove duplicate entries, preserve one canonical entry.

### Category D: INVESTIGATE
Complex cases with pattern collisions or design issues.
**Action:** Manual analysis and pattern refinement required.

## Implementation Readiness

✅ **Analysis Complete:** All {len(duplicate_patterns)} duplicate patterns categorized  
✅ **Consolidation Plan Generated:** Specific actions defined for each category  
✅ **Evidence-Based Approach:** Validated through 1000-title testing results  
⏳ **Ready for Implementation:** Database consolidation operations prepared

## Next Steps

1. **Review Category D patterns** for pattern collision issues
2. **Execute Category C removals** (safest operations first)
3. **Implement Category B consolidations** with priority resolution
4. **Validate Category A preservation** decisions
5. **Run post-consolidation validation** using pipeline testing

---
**Implementation:** Claude Code AI  
**GitHub Issue:** #17 Phase 2 - Evidence-Based Pattern Consolidation  
**Status:** Analysis Complete, Ready for Database Operations
"""
    
    summary_file = os.path.join(output_dir, "summary_report.md")
    with open(summary_file, 'w') as f:
        f.write(summary_report)
    logger.info(f"Summary report saved to: {summary_file}")
    
    # Display summary statistics
    logger.info("\n" + "="*60)
    logger.info("GITHUB ISSUE #17 PHASE 2 ANALYSIS COMPLETE")
    logger.info("="*60)
    logger.info(f"Total Duplicate Patterns Analyzed: {len(duplicate_patterns)}")
    logger.info(f"Category A (PRESERVE): {consolidation_plan['summary']['category_a_preserve']}")
    logger.info(f"Category B (CONSOLIDATE): {consolidation_plan['summary']['category_b_consolidate']}")
    logger.info(f"Category C (REMOVE): {consolidation_plan['summary']['category_c_remove']}")
    logger.info(f"Category D (INVESTIGATE): {consolidation_plan['summary']['category_d_investigate']}")
    logger.info(f"\nOutput Directory: {output_dir}")
    logger.info(f"Ready for database consolidation operations.")
    
    client.close()

if __name__ == "__main__":
    main()