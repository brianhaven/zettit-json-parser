#!/usr/bin/env python3
"""
GitHub Issue #17 Phase 2: Consolidation Preview & Backup Strategy
Shows exactly which documents would be affected and creates backup plan

Option A: Show specific documents that would be changed
Option B: Create backup/rollback strategy
"""

import os
import sys
import json
import logging
from datetime import datetime
import pytz
from typing import Dict, List, Any
from pymongo import MongoClient
from bson import ObjectId
from dotenv import load_dotenv

load_dotenv()

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def load_consolidation_plan(plan_file: str) -> Dict:
    """Load the consolidation plan from analysis results."""
    with open(plan_file, 'r') as f:
        return json.load(f)

def create_backup_collection(collection, backup_collection_name: str) -> bool:
    """Create a backup of all report_type patterns before consolidation."""
    try:
        db = collection.database
        backup_collection = db[backup_collection_name]
        
        # Copy all report_type documents to backup collection
        report_type_docs = list(collection.find({"type": "report_type"}))
        if report_type_docs:
            backup_collection.insert_many(report_type_docs)
            logger.info(f"✅ Backup created: {len(report_type_docs)} documents in '{backup_collection_name}'")
            return True
        else:
            logger.warning("No report_type documents found to backup")
            return False
            
    except Exception as e:
        logger.error(f"Backup creation failed: {e}")
        return False

def preview_category_c_changes(collection, c_remove_patterns: List[Dict]) -> Dict:
    """Preview Category C (REMOVE) changes - show exactly what would be deleted."""
    preview = {
        "category": "C_REMOVE",
        "description": "Exact duplicate removal - safest operations",
        "patterns": []
    }
    
    for pattern_analysis in c_remove_patterns:
        pattern_regex = pattern_analysis["pattern"]
        documents = pattern_analysis["documents"]
        
        # Sort by creation date to determine which to keep
        sorted_docs = sorted(documents, key=lambda x: x.get("created_date", datetime.min))
        keep_doc = sorted_docs[0]
        remove_docs = sorted_docs[1:]
        
        pattern_preview = {
            "pattern_regex": pattern_regex,
            "duplicate_count": len(documents),
            "action_summary": f"Keep oldest document, remove {len(remove_docs)} duplicates",
            "document_to_keep": {
                "id": keep_doc["id"],
                "term": keep_doc["term"],
                "priority": keep_doc["priority"],
                "format_type": keep_doc["format_type"],
                "created_date": str(keep_doc.get("created_date", "Unknown")),
                "reason": "Oldest document (most established)"
            },
            "documents_to_remove": []
        }
        
        for doc in remove_docs:
            pattern_preview["documents_to_remove"].append({
                "id": doc["id"],
                "term": doc["term"],
                "priority": doc["priority"],
                "format_type": doc["format_type"],
                "created_date": str(doc.get("created_date", "Unknown")),
                "reason": "Duplicate of older entry"
            })
        
        preview["patterns"].append(pattern_preview)
    
    return preview

def preview_category_b_changes(collection, b_consolidate_patterns: List[Dict]) -> Dict:
    """Preview Category B (CONSOLIDATE) changes - show priority resolution."""
    preview = {
        "category": "B_CONSOLIDATE", 
        "description": "Priority conflict resolution - lowest priority wins",
        "patterns": []
    }
    
    for pattern_analysis in b_consolidate_patterns:
        pattern_regex = pattern_analysis["pattern"]
        documents = pattern_analysis["documents"]
        unique_priorities = pattern_analysis["unique_priorities"]
        target_priority = min(unique_priorities)
        
        # Find document to keep (lowest priority, then oldest)
        target_docs = [doc for doc in documents if doc["priority"] == target_priority]
        if len(target_docs) > 1:
            target_docs = sorted(target_docs, key=lambda x: x.get("created_date", datetime.min))
        
        keep_doc = target_docs[0]
        remove_docs = [doc for doc in documents if doc["id"] != keep_doc["id"]]
        
        pattern_preview = {
            "pattern_regex": pattern_regex,
            "duplicate_count": len(documents),
            "priority_conflict": f"Priorities {unique_priorities} -> Consolidate to {target_priority}",
            "action_summary": f"Consolidate to priority {target_priority}, remove {len(remove_docs)} duplicates",
            "document_to_keep": {
                "id": keep_doc["id"],
                "term": keep_doc["term"],
                "current_priority": keep_doc["priority"],
                "consolidated_priority": target_priority,
                "format_type": keep_doc["format_type"],
                "created_date": str(keep_doc.get("created_date", "Unknown")),
                "changes": "Priority will be updated, notes will be added about consolidation"
            },
            "documents_to_remove": []
        }
        
        for doc in remove_docs:
            pattern_preview["documents_to_remove"].append({
                "id": doc["id"],
                "term": doc["term"],
                "priority": doc["priority"],
                "format_type": doc["format_type"],
                "created_date": str(doc.get("created_date", "Unknown")),
                "reason": f"Higher priority ({doc['priority']}) loses to {target_priority}"
            })
        
        preview["patterns"].append(pattern_preview)
    
    return preview

def create_rollback_plan(preview_data: Dict) -> Dict:
    """Create detailed rollback plan for undoing consolidation."""
    rollback_plan = {
        "rollback_method": "restore_from_backup",
        "backup_collection_name": f"pattern_libraries_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
        "alternative_rollback": {
            "method": "individual_document_restoration",
            "documents_to_restore": []
        },
        "validation_queries": [
            {
                "purpose": "Count report_type patterns",
                "query": {"type": "report_type"},
                "operation": "count"
            },
            {
                "purpose": "Find remaining duplicates",
                "aggregation": [
                    {"$match": {"type": "report_type"}},
                    {"$group": {"_id": "$pattern", "count": {"$sum": 1}}},
                    {"$match": {"count": {"$gt": 1}}}
                ]
            }
        ]
    }
    
    # Collect all documents that would be deleted for individual restoration
    for category_data in preview_data["previews"]:
        for pattern in category_data["patterns"]:
            for doc_to_remove in pattern["documents_to_remove"]:
                rollback_plan["alternative_rollback"]["documents_to_restore"].append({
                    "id": doc_to_remove["id"],
                    "term": doc_to_remove["term"],
                    "priority": doc_to_remove["priority"],
                    "format_type": doc_to_remove["format_type"],
                    "pattern_regex": pattern["pattern_regex"]
                })
    
    return rollback_plan

def create_output_directory(script_name: str) -> str:
    """Create timestamped output directory."""
    pdt = pytz.timezone('America/Los_Angeles')
    timestamp = datetime.now(pdt).strftime('%Y%m%d_%H%M%S')
    output_dir = f"../outputs/{timestamp}_{script_name}"
    os.makedirs(output_dir, exist_ok=True)
    return output_dir

def main():
    """Create consolidation preview and backup strategy."""
    
    logger.info("Starting GitHub Issue #17 Phase 2: Consolidation Preview & Backup")
    
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
    output_dir = create_output_directory("issue17_phase2_consolidation_preview")
    logger.info(f"Output directory: {output_dir}")
    
    # Load consolidation plan
    plan_file = "../outputs/20250827_214431_issue17_phase2_pattern_consolidation/consolidation_plan.json"
    
    if not os.path.exists(plan_file):
        logger.error(f"Consolidation plan file not found: {plan_file}")
        return
        
    consolidation_plan = load_consolidation_plan(plan_file)
    logger.info("Loaded consolidation plan")
    
    # Get current timestamps
    pdt = pytz.timezone('America/Los_Angeles')
    utc = pytz.timezone('UTC')
    current_time_pdt = datetime.now(pdt)
    current_time_utc = datetime.now(utc)
    
    # OPTION A: Preview exactly what would be changed
    logger.info("\n" + "="*60)
    logger.info("OPTION A: DETAILED CONSOLIDATION PREVIEW")
    logger.info("="*60)
    
    preview_data = {
        "preview_time_pdt": current_time_pdt.strftime('%Y-%m-%d %H:%M:%S %Z'),
        "preview_time_utc": current_time_utc.strftime('%Y-%m-%d %H:%M:%S %Z'),
        "plan_summary": consolidation_plan["summary"],
        "previews": []
    }
    
    # Preview Category C changes
    c_remove_patterns = consolidation_plan["actions"]["C_REMOVE"]
    if c_remove_patterns:
        c_preview = preview_category_c_changes(collection, c_remove_patterns)
        preview_data["previews"].append(c_preview)
        logger.info(f"Category C Preview: {len(c_preview['patterns'])} patterns with exact duplicates")
    
    # Preview Category B changes  
    b_consolidate_patterns = consolidation_plan["actions"]["B_CONSOLIDATE"]
    if b_consolidate_patterns:
        b_preview = preview_category_b_changes(collection, b_consolidate_patterns)
        preview_data["previews"].append(b_preview)
        logger.info(f"Category B Preview: {len(b_preview['patterns'])} patterns with priority conflicts")
    
    # Save detailed preview
    preview_file = os.path.join(output_dir, "consolidation_preview_detailed.json")
    with open(preview_file, 'w') as f:
        json.dump(preview_data, f, indent=2, default=str)
    logger.info(f"Detailed preview saved to: {preview_file}")
    
    # OPTION B: Create backup strategy
    logger.info("\n" + "="*60)
    logger.info("OPTION B: BACKUP STRATEGY CREATION")
    logger.info("="*60)
    
    # Create backup collection name
    backup_collection_name = f"pattern_libraries_backup_{current_time_pdt.strftime('%Y%m%d_%H%M%S')}"
    
    # Create actual backup
    backup_success = create_backup_collection(collection, backup_collection_name)
    
    # Create rollback plan
    rollback_plan = create_rollback_plan(preview_data)
    rollback_plan["backup_collection_name"] = backup_collection_name
    rollback_plan["backup_created"] = backup_success
    rollback_plan["backup_timestamp"] = current_time_pdt.strftime('%Y-%m-%d %H:%M:%S %Z')
    
    # Save rollback plan
    rollback_file = os.path.join(output_dir, "rollback_plan.json")
    with open(rollback_file, 'w') as f:
        json.dump(rollback_plan, f, indent=2, default=str)
    logger.info(f"Rollback plan saved to: {rollback_file}")
    
    # Count total documents that would be affected
    total_removes = sum(len(pattern["documents_to_remove"]) for preview in preview_data["previews"] for pattern in preview["patterns"])
    total_updates = sum(1 for preview in preview_data["previews"] if preview["category"] == "B_CONSOLIDATE" for pattern in preview["patterns"])
    
    # Generate human-readable summary
    summary_report = f"""# GitHub Issue #17 Phase 2: Consolidation Preview & Backup

**Preview Date (PDT):** {current_time_pdt.strftime('%Y-%m-%d %H:%M:%S %Z')}  
**Preview Date (UTC):** {current_time_utc.strftime('%Y-%m-%d %H:%M:%S %Z')}

## OPTION A: What Would Be Changed

### Summary of Database Operations
- **Documents to Delete:** {total_removes}
- **Documents to Update:** {total_updates}  
- **Backup Created:** {"✅ YES" if backup_success else "❌ NO"}
- **Rollback Available:** {"✅ YES" if backup_success else "⚠️ LIMITED"}

### Category C (REMOVE) - Exact Duplicates
**Safe Operations:** Remove duplicate entries, keep oldest canonical version.

**Patterns Affected:**
{chr(10).join([f"- `{pattern['pattern_regex']}`: Keep 1, remove {len(pattern['documents_to_remove'])}" for preview in preview_data["previews"] if preview["category"] == "C_REMOVE" for pattern in preview["patterns"]])}

### Category B (CONSOLIDATE) - Priority Resolution
**Priority Operations:** Resolve conflicting priorities using lowest-priority-wins rule.

**Patterns Affected:**
{chr(10).join([f"- `{pattern['pattern_regex']}`: Priority {pattern['priority_conflict']}" for preview in preview_data["previews"] if preview["category"] == "B_CONSOLIDATE" for pattern in preview["patterns"]])}

## OPTION B: Backup & Rollback Strategy

### Backup Details
- **Backup Collection:** `{backup_collection_name}`
- **Backup Status:** {"✅ CREATED" if backup_success else "❌ FAILED"}
- **Documents Backed Up:** {collection.count_documents({"type": "report_type"})} report_type patterns
- **Backup Method:** Complete collection copy before any modifications

### Rollback Options

#### Option 1: Complete Restoration (Recommended)
```javascript
// MongoDB commands to restore from backup
use deathstar
db.pattern_libraries.deleteMany({{"type": "report_type"}})
db.{backup_collection_name}.find({{}}).forEach(function(doc) {{
    delete doc._id;
    db.pattern_libraries.insertOne(doc);
}})
```

#### Option 2: Individual Document Restoration
- **Documents that can be restored:** {len(rollback_plan["alternative_rollback"]["documents_to_restore"])}
- **Method:** Re-insert specific deleted documents with original IDs

### Validation Queries
After consolidation OR rollback, run these queries to validate:

```javascript
// Count total report_type patterns
db.pattern_libraries.countDocuments({{"type": "report_type"}})

// Check for remaining duplicates  
db.pattern_libraries.aggregate([
    {{"$match": {{"type": "report_type"}}}},
    {{"$group": {{"_id": "$pattern", "count": {{"$sum": 1}}}}}},
    {{"$match": {{"count": {{"$gt": 1}}}}}}
])
```

## Risk Assessment

### Low Risk Operations ✅
- **Category C removals:** Deleting exact duplicates is safe
- **Backup available:** Complete restoration possible

### Medium Risk Operations ⚠️  
- **Category B consolidations:** Priority changes affect matching logic
- **Pipeline impact:** May change Script 03 behavior slightly

### Mitigation Strategies
1. **Backup created** before any changes
2. **Detailed preview** shows exactly what changes
3. **Rollback plan** available for quick restoration  
4. **Post-change validation** using pipeline testing

## Next Steps Decision Points

**Option C: Proceed with Consolidation**
- Execute database changes with backup safety net
- Validate results with pipeline testing
- Monitor for any performance impacts

**Option D: Alternative Approach**
- Modify consolidation strategy based on preview
- Test on subset of patterns first
- Use different consolidation criteria

---
**Implementation:** Claude Code AI  
**GitHub Issue:** #17 Phase 2 - Pattern Consolidation Preview  
**Status:** {"Ready for Execution" if backup_success else "Backup Required Before Execution"}
"""
    
    summary_file = os.path.join(output_dir, "consolidation_preview_summary.md")
    with open(summary_file, 'w') as f:
        f.write(summary_report)
    logger.info(f"Human-readable summary saved to: {summary_file}")
    
    # Final summary
    logger.info("\n" + "="*60)
    logger.info("PREVIEW & BACKUP COMPLETE")
    logger.info("="*60)
    logger.info(f"Documents to Delete: {total_removes}")
    logger.info(f"Documents to Update: {total_updates}")
    logger.info(f"Backup Status: {'✅ CREATED' if backup_success else '❌ FAILED'}")
    logger.info(f"Rollback Available: {'✅ YES' if backup_success else '⚠️ LIMITED'}")
    logger.info(f"Output Directory: {output_dir}")
    logger.info(f"Ready for your decision on Option C or D")
    
    client.close()

if __name__ == "__main__":
    main()