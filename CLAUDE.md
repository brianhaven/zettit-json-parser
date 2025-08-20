# Zettit JSON Parser - Market Research Title Analysis

## Project Overview

A systematic pattern-matching solution that extracts structured information (topics, topicNames, regions) from market research report titles using MongoDB-based pattern libraries and deterministic processing logic.

## Development Standards

### Script Organization
- **Official scripts:** Root directory
- **Development/testing scripts:** `/experiments/` directory with version numbers (e.g., `script_name_v1.py`)
- **Output files:** `/outputs/` directory with timestamp format `{YYYYMMDD_HHMMSS}_{TYPE}`
- **Documentation:** `/documentation/` directory for permanent docs only
- **Data files:** `/resources/` directory

### Output File Requirements

**All script outputs must include dual timestamps:**
```
**Analysis Date (PDT):** 2025-08-19 15:30:45 PDT  
**Analysis Date (UTC):** 2025-08-19 22:30:45 UTC
```

**Filename format:** `{YYYYMMDD_HHMMSS}_{TYPE}.{ext}`
- Use Pacific Time for timestamps in filenames
- Include both PDT/PST and UTC timestamps in file headers
- Examples: `20250819_153045_pattern_analysis.json`, `20250819_153045_processing_summary.md`

## MongoDB-First Architecture

### Database Strategy
**MongoDB Atlas serves as both data source and pattern library storage:**
- **Primary data:** `markets_raw` collection (19,558+ titles)
- **Pattern libraries:** `pattern_libraries` collection with real-time updates
- **Processed results:** `markets_processed` collection for output tracking
- **Performance metrics:** Built-in success/failure tracking

### Claude Code MongoDB Integration
**IMPORTANT: Use MongoDB MCP Server for all database interactions**

**For interactive database work:**
```bash
# List collections
/mcp:supabase list_tables  # Use MongoDB MCP equivalent

# Query titles 
/mcp:mongodb find markets_raw {}

# Update pattern libraries
/mcp:mongodb insert pattern_libraries {...}
```

**For scripts:** Scripts use pymongo API directly
```python
from pymongo import MongoClient
client = MongoClient(os.getenv('MONGODB_URI'))
db = client['deathstar']
```

### Processing Methodology

**Step-based systematic approach:**
1. **Market term classification:** Separate "Market for"/"Market in" from standard "Market" titles
2. **Date extraction:** Remove dates first (`extracted_forecast_date_range` field)
3. **Report type extraction:** Extract from "Market" onwards (`extracted_report_type` field)
4. **Geographic processing:** Compound entity detection (`extracted_regions` array, preserve order)
5. **Topic extraction:** Complete technical compound preservation (`topic` and `topicName` fields)

### Library-Based Processing Strategy

**MongoDB Pattern Libraries Structure:**
```javascript
// pattern_libraries collection
{
  "type": "geographic_entity", // or "market_term", "date_pattern", "report_type"
  "term": "North America",
  "aliases": ["NA", "North American"],
  "priority": 1,  // For compound processing order
  "active": true,
  "success_count": 1547,
  "failure_count": 3,
  "created_date": ISODate(),
  "last_updated": ISODate()
}
```

**Processing philosophy:** Systematic removal approach
- Remove known patterns in order (dates, report types, geographic regions)
- What remains IS the topic (regardless of internal punctuation)
- Track performance metrics in MongoDB for continuous improvement

### Extracted Field Standards

**Required output fields:**
- `market_term_type`: "standard", "market_for", or "market_in"
- `extracted_forecast_date_range`: Date/range string
- `extracted_report_type`: Full report type including "Market"
- `extracted_regions`: Array preserving source order
- `topic`: Clean extracted topic
- `topicName`: Normalized topic for system use
- `confidence_score`: Float 0.0-1.0 for quality tracking

### Code Standards

**MongoDB Integration:**
- Use environment variables from `.env` file for connection
- MongoDB collections for pattern libraries (not static files)
- Real-time library updates without deployment
- Performance tracking built into database operations

**Dependencies:**
- `pymongo` for MongoDB connectivity
- `python-dotenv` for environment variable management
- `spacy` for geographic entity discovery (optional)
- `gliner` for named entity recognition (optional)

**Script Requirements:**
- Comprehensive logging for debugging
- Graceful error handling with informative messages
- Progress indicators for large dataset processing
- Confidence tracking for edge case identification

### Testing Strategy

**Development Process:**
- Use `/experiments/` directory for iterative development
- MongoDB-based A/B testing for pattern libraries
- Confidence scoring to identify titles needing human review
- Real-time performance metrics for continuous improvement

**Validation Approach:**
- Track success/failure rates in MongoDB
- Human review of low-confidence extractions
- Pattern library enhancement based on processing results

### Success Metrics

**Target accuracy rates:**
- **Date extraction:** 98-99% accuracy
- **Report type extraction:** 95-97% accuracy  
- **Geographic detection:** 96-98% accuracy
- **Topic extraction:** 92-95% accuracy
- **Overall processing:** 95-98% complete success

**Quality indicators:**
- < 5% titles requiring human review (confidence < 0.8)
- < 2% false positive geographic detection
- < 1% critical parsing failures

### Implementation Strategy

**Modular Development:**
1. MongoDB library setup and initialization
2. Market term classification (2 patterns)
3. Date pattern extraction and library building
4. Report type pattern extraction and library building  
5. Geographic entity detection with SpaCy/GLiNER enhancement
6. Topic extraction and normalization
7. End-to-end validation and confidence tuning

**Script Architecture:**
- Single orchestrator script for complete processing
- MongoDB library manager for pattern access
- Confidence tracker for edge case identification
- Performance metrics integration

## Current Status

**Architecture Finalized:**
- MongoDB-first approach confirmed
- Step-by-step processing methodology defined
- Field naming standards established
- Library structure designed

**Next Steps:**
1. Set up MongoDB pattern library collections
2. Implement market term classification
3. Build date pattern extraction system
4. Develop report type library
5. Integrate geographic entity detection
6. Build topic extraction logic
7. Implement end-to-end validation

**Development Priority:**
Script-based implementation with deterministic pattern matching achieves 95%+ accuracy through systematic removal approach and MongoDB-based library management.

## Task Master AI Instructions
**Import Task Master's development workflow commands and guidelines, treat as if import is in the main CLAUDE.md file.**
@./.taskmaster/CLAUDE.md
