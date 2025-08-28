#!/usr/bin/env python3

import os
import json
from pymongo import MongoClient
from dotenv import load_dotenv
from collections import defaultdict

# Load environment variables
load_dotenv()

def analyze_all_duplicates():
    """Complete analysis of all duplicate report type patterns"""
    
    # Connect to MongoDB Atlas
    mongodb_uri = os.getenv('MONGODB_URI')
    if not mongodb_uri:
        print("ERROR: MONGODB_URI not found in environment")
        return False
        
    client = MongoClient(mongodb_uri)
    db = client['deathstar']
    collection = db['pattern_libraries']
    
    print("=== COMPLETE DUPLICATE PATTERN ANALYSIS ===")
    print("GitHub Issue #16 - Systematic Audit\n")
    
    # Get all report_type documents grouped by term
    pipeline = [
        {"$match": {"type": "report_type"}},
        {"$group": {
            "_id": "$term",
            "count": {"$sum": 1},
            "docs": {"$push": {
                "id": "$_id",
                "pattern": "$pattern", 
                "format_type": "$format_type",
                "priority": "$priority",
                "active": "$active",
                "created": "$created_date",
                "notes": "$notes"
            }}
        }},
        {"$match": {"count": {"$gt": 1}}},
        {"$sort": {"count": -1}}
    ]
    
    duplicates = list(collection.aggregate(pipeline))
    
    print(f"Found {len(duplicates)} terms with duplicate patterns")
    print(f"Total duplicate documents: {sum(dup['count'] for dup in duplicates)}")
    print("=" * 80)
    
    analysis_results = {
        "total_duplicate_terms": len(duplicates),
        "total_duplicate_documents": sum(dup['count'] for dup in duplicates),
        "groups": []
    }
    
    for i, dup_group in enumerate(duplicates, 1):
        term = dup_group['_id']
        count = dup_group['count']
        docs = dup_group['docs']
        
        print(f"\n{i}. \"{term}\" ({count} duplicates)")
        print("-" * 60)
        
        group_analysis = {
            "term": term,
            "count": count,
            "patterns": [],
            "issues": [],
            "recommendations": []
        }
        
        # Analyze each document in the group
        patterns_seen = {}
        format_conflicts = {}
        
        for j, doc in enumerate(docs):
            pattern = doc['pattern']
            format_type = doc['format_type']
            priority = doc['priority']
            active = doc['active']
            
            print(f"  {j+1}. ID: {str(doc['id'])[-6:]}")
            print(f"     Pattern: {pattern}")
            print(f"     Format: {format_type}, Priority: {priority}, Active: {active}")
            if doc.get('notes'):
                print(f"     Notes: {doc['notes'][:100]}...")
            print()
            
            # Track patterns for duplicate detection
            if pattern in patterns_seen:
                if format_type != patterns_seen[pattern]:
                    conflict_key = f"{pattern}"
                    if conflict_key not in format_conflicts:
                        format_conflicts[conflict_key] = []
                    format_conflicts[conflict_key].append((str(doc['id']), format_type))
                    group_analysis['issues'].append(f"Format conflict: Same pattern with different format_types")
                else:
                    group_analysis['issues'].append(f"Exact duplicate: Same pattern and format_type")
            else:
                patterns_seen[pattern] = format_type
            
            group_analysis['patterns'].append({
                "id": str(doc['id']),
                "pattern": pattern,
                "format_type": format_type,
                "priority": priority,
                "active": active
            })
        
        # Generate recommendations
        if len(format_conflicts) > 0:
            group_analysis['recommendations'].append("Resolve format_type conflicts for identical patterns")
        
        if len([d for d in docs if d['priority'] == 1]) > 1:
            group_analysis['recommendations'].append("Fix priority conflicts - multiple priority=1 patterns")
            
        unique_patterns = len(set(doc['pattern'] for doc in docs))
        if unique_patterns < count:
            group_analysis['recommendations'].append(f"Remove {count - unique_patterns} exact duplicate patterns")
            
        # Specific recommendations by term
        if term == "Market Report":
            group_analysis['recommendations'].append("CRITICAL: Remove exact duplicate with wrong format_type")
        elif "Market" in term and count >= 3:
            group_analysis['recommendations'].append("Consolidate similar terminal patterns, keep distinct format variations")
            
        analysis_results['groups'].append(group_analysis)
        
        print(f"Issues: {len(group_analysis['issues'])}")
        for issue in group_analysis['issues']:
            print(f"  ⚠️  {issue}")
        print(f"Recommendations: {len(group_analysis['recommendations'])}")  
        for rec in group_analysis['recommendations']:
            print(f"  ✅ {rec}")
        print("=" * 60)
    
    # Summary and action plan
    print(f"\n=== SUMMARY ===")
    total_issues = sum(len(group['issues']) for group in analysis_results['groups'])
    print(f"Total Issues Found: {total_issues}")
    print(f"Total Recommendations: {sum(len(group['recommendations']) for group in analysis_results['groups'])}")
    
    # Save detailed analysis
    with open('duplicate_pattern_analysis_complete.json', 'w') as f:
        json.dump(analysis_results, f, indent=2, default=str)
    
    print(f"\nDetailed analysis saved to: duplicate_pattern_analysis_complete.json")
    print("\nNext Steps:")
    print("1. Review analysis results")
    print("2. Create consolidation plan") 
    print("3. Implement pattern deduplication")
    print("4. Test Script 03 priority system")
    
    client.close()
    return True

if __name__ == "__main__":
    analyze_all_duplicates()