# Zettit JSON Parser - Market Research Title Analysis

## Project Overview

A systematic pattern-matching solution that extracts structured information (topics, topicNames, regions) from market research report titles and descriptions using MongoDB-based pattern libraries, enhanced HTML processing, and dual spaCy model validation.

**Status: Production-Ready Processing Pipeline with Enhanced Geographic Detection**

## Development Standards

### Script Organization

**Processing Pipeline (`/experiments/`):**
- **00-04 numbered scripts:** Main processing pipeline in execution order
- **00a-03a initialization scripts:** Setup and pattern library management
- **Pattern discovery:** Human-review workflow for pattern enhancement

**Supporting Directories:**
- **`/experiments/tests/`:** Development, testing, and validation scripts
- **`/experiments/archive/`:** Legacy and experimental approaches
- **`/experiments/utilities/`:** One-time setup and migration scripts
- **`/outputs/`:** All script outputs with timestamp format `{YYYYMMDD_HHMMSS}_{TYPE}`
- **`/resources/`:** Static data files and mappings

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

### Processing Pipeline Methodology

**Enhanced systematic removal approach with dual validation and HTML processing:**

#### **Stage 1: Setup and Initialization**
- **00_pattern_discovery_for_review_v1.py:** Discover new patterns requiring human validation
  - Human-review workflow with approval checkboxes
  - Pattern classification (new terms, aliases, noise)
  - MongoDB conflict detection and resolution
- **00a_mongodb_setup_v1.py:** Initialize MongoDB collections and indexes
- **00b_pattern_library_manager_v1.py:** Manage pattern library operations

#### **Stage 2: Core Processing Pipeline**

**01_market_term_classifier_v1.py:** Market Term Classification
- Identifies "Market for" vs "Market in" vs standard processing patterns
- Routes titles to appropriate processing pathways
- Confidence scoring for classification accuracy
- Performance: 95%+ classification accuracy

**02_date_extractor_v1.py:** Date Pattern Extraction
- **Terminal comma format:** "Market Report, 2030" → "2030"
- **Range format:** "Market Analysis, 2023-2030" → "2023-2030"
- **Bracket format:** "Market Study [2024]" → "2024"  
- **Embedded format:** "Market Outlook 2031" → "2031"
- Year validation (2020-2040 range) with confidence scoring
- Performance: 98-99% accuracy target
- **02a_initialize_date_patterns.py:** Setup date pattern library

**03_report_type_extractor_v1.py:** Report Type Extraction
- Extracts complete report type phrases including "Market"
- Pattern library approach with MongoDB storage
- Systematic pattern matching for "Market Size", "Market Analysis", etc.
- Performance: 95-97% accuracy target
- **03a_initialize_report_patterns.py:** Setup report type pattern library

**04_geographic_entity_detector_v1.py:** **ENHANCED** Geographic Entity Detection
- **HTML Processing Innovation:** BeautifulSoup parsing prevents concatenation artifacts
- **Dual spaCy Model Validation:** en_core_web_md + en_core_web_lg for 31% more discoveries
- **Enhanced HTML Cleaning:** Proper block-level separators prevent "KoreaIndonesiaAustralia" errors
- **Table Data Extraction:** Structured region data from HTML tables
- **Cross-Model Confidence Scoring:** Validates patterns across both models
- **Individual Document Processing:** Outperforms text aggregation strategies
- **Performance:** 96-98% accuracy target with enhanced pattern discovery

**Key Innovation: HTML-Aware Processing**
```python
def enhanced_html_cleaning(html_content: str) -> Dict[str, str]:
    # Parse HTML with BeautifulSoup to prevent concatenation
    soup = BeautifulSoup(html_content, 'html.parser')
    # Add separators before block elements
    # Extract table content for structured regions
    # Preserve geographic entity boundaries
```

**Dual spaCy Model Benefits:**
- en_core_web_md: Faster processing, good baseline coverage
- en_core_web_lg: Higher accuracy, better compound entity detection
- Combined approach: 31% more pattern discoveries than single model
- Cross-validation: Confidence scoring for pattern quality

#### **Stage 3: Topic Extraction** (Final step after geographic removal)
- **Systematic Removal:** Remove all known patterns (dates, report types, regions) in sequence
- **What remains IS the topic:** Preserves technical compounds regardless of internal punctuation
- **Normalization:** Create `topicName` while preserving original in `topic`
- **Confidence tracking:** Identify edge cases for human review

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
- `spacy` for enhanced geographic entity discovery (en_core_web_md + en_core_web_lg)
- `beautifulsoup4` for HTML processing and concatenation prevention
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

**Enhanced Modular Development:**
1. ✅ **MongoDB library setup and initialization** (Complete)
2. ✅ **Market term classification (2 patterns)** (Complete)  
3. ✅ **Date pattern extraction and library building** (Complete)
4. ✅ **Report type pattern extraction and library building** (Complete)
5. ✅ **Enhanced geographic entity detection with dual spaCy models** (Complete)
6. ✅ **HTML processing innovation for concatenation prevention** (Complete)
7. ✅ **Pattern discovery and human review workflow** (Complete)
8. 🔄 **Topic extraction and normalization** (Ready for implementation)
9. 🔄 **End-to-end validation and confidence tuning** (Ready for implementation)

**Enhanced Script Architecture:**
- **Numbered processing pipeline:** 00-04 for systematic execution
- **MongoDB pattern library manager:** Real-time updates without deployment
- **Dual-model validation:** Enhanced accuracy and confidence scoring
- **HTML-aware processing:** Prevents data corruption from concatenated entities
- **Human review workflow:** Pattern validation and library enhancement
- **Performance metrics integration:** MongoDB-based success/failure tracking

## Current Status

**🎯 Production-Ready Processing Pipeline Achieved:**
- ✅ **MongoDB-first approach** with dynamic pattern library management
- ✅ **Enhanced HTML processing** prevents concatenation artifacts like "KoreaIndonesiaAustralia"
- ✅ **Dual spaCy model validation** provides 31% more pattern discoveries than single model
- ✅ **Systematic removal methodology** preserves technical compounds in topics
- ✅ **Human review workflow** for continuous pattern library improvement
- ✅ **Numbered pipeline organization** for clear execution order and dependency management

**🚀 Technical Breakthroughs:**
- **HTML Processing Innovation:** BeautifulSoup parsing with proper block-level separators
- **Dual Model Cross-Validation:** en_core_web_md + en_core_web_lg confidence scoring
- **Table Data Extraction:** Structured region data from HTML report descriptions
- **Individual Document Processing:** Outperforms text aggregation strategies for pattern discovery
- **Human-Review Workflow:** Approval checkboxes and conflict detection for pattern validation

**📋 Ready for Production Implementation:**
1. **Core Processing Pipeline:** Market classification → Date extraction → Report type → Geographic detection
2. **Enhanced Geographic Detection:** HTML-aware dual-model processing with confidence scoring
3. **Pattern Library Management:** Real-time MongoDB updates with performance tracking
4. **Quality Assurance:** Human review workflow with pattern classification
5. **Performance Monitoring:** Built-in success/failure metrics and edge case identification

**🎯 Final Implementation Phase:**
- Topic extraction logic integration using systematic removal approach
- End-to-end validation pipeline with confidence thresholds
- Production deployment preparation with performance optimization
- Comprehensive testing suite validation

## Task Master AI Instructions
**Import Task Master's development workflow commands and guidelines, treat as if import is in the main CLAUDE.md file.**
@./.taskmaster/CLAUDE.md
