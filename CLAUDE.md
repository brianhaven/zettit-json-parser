# Zettit JSON Parser - Market Research Title Analysis

## Project Overview

A systematic pattern-matching solution that extracts structured information (topics, topicNames, regions) from market research report titles and descriptions using MongoDB-based pattern libraries, enhanced HTML processing, and dual spaCy model validation.

**Status: Production-Ready Processing Pipeline with Enhanced Geographic Detection**

## Development Standards

### Script Organization & Directory Structure

**CRITICAL: All development follows this mandatory directory structure:**

#### **Main Processing Scripts (`/experiments/`)**
- **00-07 numbered scripts:** Main processing pipeline components in execution order
- **00a-03a initialization scripts:** Setup and pattern library management  
- **Pattern discovery scripts:** Human-review workflow for pattern enhancement
- **All main scripts must be developed in `/experiments/` directory**

#### **Test Scripts (`/experiments/tests/`)**
- **ALL test scripts must be stored in `/experiments/tests/` directory**
- Test scripts use systematic naming: `test_{script_name}_{version}.py`
- Test scripts must include proper import path handling for parent directory modules
- Examples: `test_03_market_aware_pipeline_v2.py`, `test_phase1_market_term_classifier_harness.py`

#### **Output Directory (`/outputs/`)**
- **ALL script outputs must be stored in `/outputs/` directory**
- Each script run creates a new timestamped subdirectory: `/outputs/{YYYYMMDD_HHMMSS}_{TYPE}/`
- Output files within subdirectory use descriptive names (no timestamp prefix needed)
- Examples: `/outputs/20250825_044253_phase3_pipeline_01_02_03/`, `/outputs/20250821_120439_phase1_market_term_classifier/`

#### **Supporting Directories:**
- **`/experiments/archive/`:** Legacy and experimental approaches
- **`/experiments/utilities/`:** One-time setup and migration scripts  
- **`/resources/`:** Static data files and mappings

### Import Path Management

**CRITICAL: All scripts must handle imports correctly based on their location:**

#### **For Test Scripts in `/experiments/tests/`:**
```python
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Dynamic import pattern for main scripts
import importlib.util

def import_module_from_path(module_name: str, file_path: str):
    """Import a module from a file path."""
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

# Import main scripts from parent directory
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
pattern_lib = import_module_from_path("pattern_library_manager_v1", 
                                    os.path.join(parent_dir, "00b_pattern_library_manager_v1.py"))
```

#### **For Main Scripts in `/experiments/`:**
```python
import importlib.util
import sys
import os

# Dynamic import for same-directory modules
try:
    pattern_manager_path = os.path.join(os.path.dirname(__file__), "00b_pattern_library_manager_v1.py")
    spec = importlib.util.spec_from_file_location("pattern_library_manager_v1", pattern_manager_path)
    pattern_module = importlib.util.module_from_spec(spec)
    sys.modules["pattern_library_manager_v1"] = pattern_module
    spec.loader.exec_module(pattern_module)
    PatternLibraryManager = pattern_module.PatternLibraryManager
except Exception as e:
    logger.error(f"Failed to import PatternLibraryManager: {e}")
```

### Output Directory Creation Standards

**CRITICAL: All scripts must create outputs using this standard pattern:**

#### **For Test Scripts:**
```python
import pytz
from datetime import datetime
from pathlib import Path

def create_output_directory(script_name: str) -> str:
    """Create timestamped output directory using absolute paths."""
    # Get absolute path to outputs directory (from /experiments/tests/ to /outputs/)
    script_dir = os.path.dirname(os.path.abspath(__file__))
    experiments_dir = os.path.dirname(script_dir)  
    project_root = os.path.dirname(experiments_dir)
    outputs_dir = os.path.join(project_root, 'outputs')
    
    # Create timestamp in Pacific Time
    pdt = pytz.timezone('America/Los_Angeles')
    timestamp = datetime.now(pdt).strftime('%Y%m%d_%H%M%S')
    
    # Create timestamped subdirectory
    output_dir = os.path.join(outputs_dir, f"{timestamp}_{script_name}")
    os.makedirs(output_dir, exist_ok=True)
    
    return output_dir
```

#### **For Main Scripts:**
```python
def create_output_directory(script_name: str) -> str:
    """Create timestamped output directory from experiments directory."""
    # Create outputs directory relative to current script location
    timestamp = datetime.now(pytz.timezone('America/Los_Angeles')).strftime('%Y%m%d_%H%M%S')
    output_dir = f"../outputs/{timestamp}_{script_name}"
    os.makedirs(output_dir, exist_ok=True)
    return output_dir
```

### Path Convention Guidelines

**CRITICAL: Follow these absolute path conventions to avoid errors:**

#### **Common Path Issues to Avoid:**
1. **Never use relative paths** like `../experiments/` from test scripts - use absolute paths  
2. **Never hardcode paths** - always calculate paths dynamically from `__file__`
3. **Always verify parent directory navigation** - test scripts need to go up 2 levels to reach project root
4. **Always create output directories** before writing files - use `os.makedirs(output_dir, exist_ok=True)`

#### **Standard Path Calculations:**
```python
# For test scripts in /experiments/tests/
script_dir = os.path.dirname(os.path.abspath(__file__))           # /experiments/tests/
experiments_dir = os.path.dirname(script_dir)                     # /experiments/  
project_root = os.path.dirname(experiments_dir)                   # /
outputs_dir = os.path.join(project_root, 'outputs')              # /outputs/

# For main scripts in /experiments/
script_dir = os.path.dirname(os.path.abspath(__file__))           # /experiments/
project_root = os.path.dirname(script_dir)                        # /
outputs_dir = os.path.join(project_root, 'outputs')              # /outputs/
```

#### **Validated Output Directory Patterns:**
- **From test scripts:** Use absolute path calculation (see code above)
- **From main scripts:** Use relative path `../outputs/` (validated working pattern)
- **Always include descriptive script name** in output directory name
- **Always include Pacific Time timestamp** for consistency

#### **File Organization Within Output Directories:**
```python
# Standard output file patterns
output_files = {
    'summary_report.md': 'Main analysis summary with dual timestamps',
    'detailed_results.json': 'Complete processing results data', 
    'failed_extractions.txt': 'Cases that failed processing',
    'pattern_analysis.txt': 'Pattern matching analysis',
    'pipeline_results.json': 'Full pipeline output data'
}
```

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

**02_date_extractor_v1.py:** **ENHANCED** Date Pattern Extraction
- **Terminal comma format:** "Market Report, 2030" → "2030"
- **Range format:** "Market Analysis, 2023-2030" → "2023-2030"
- **Bracket format:** "Market Study [2024]" → "2024"  
- **Embedded format:** "Market Outlook 2031" → "2031"
- **Numeric Pre-filtering:** Distinguishes "no dates present" vs "dates missed"
- **Enhanced Categorization:** Returns success/no_dates_present/dates_missed status
- **Comprehensive Pattern Library:** 64 patterns across 4 format types (enhanced from initial 45)
- **Year validation (2020-2040 range)** with confidence scoring
- **Performance:** 100% accuracy on titles with dates (exceeds 98-99% target)
- **Setup utilities:** `utilities/02a_initialize_date_patterns.py`, `utilities/02b_enhance_date_patterns_v1.py`

**03_report_type_extractor_v2.py:** **MARKET-AWARE** Report Type Extraction
- **DUAL PROCESSING LOGIC:** Handles market term and standard classifications differently
- **Market Term Processing:** Extraction, rearrangement, and reconstruction workflow
- **Standard Processing:** Direct database pattern matching
- **Performance:** 95-97% accuracy target for both classification types

**Market Term Classification Processing Logic:**
For titles classified as `market_for`, `market_in`, `market_by`, etc.:
1. **Extract "Market"** from the market term phrase ("Market in" → extract "Market")
2. **Preserve connector context** ("in Automotive" remains for pipeline)
3. **Search for report type patterns** in remaining text **excluding "Market" prefix**
4. **Reconstruct final report type** by prepending extracted "Market" to found pattern
5. **Example:** "AI Market in Automotive Outlook & Trends" becomes:
   - Extracted: "Market" + "Outlook & Trends" = **"Market Outlook & Trends"** (report type)
   - Pipeline forward: "AI in Automotive" (for geographic/topic extraction)

**Standard Classification Processing Logic:**
For titles classified as `standard`:
1. **Direct pattern matching** using complete database patterns
2. **No rearrangement needed** - process title as-is after date removal
3. **Example:** "APAC PPE Market Analysis" → **"Market Analysis"** (complete match)
4. **Pipeline forward:** "APAC PPE" (for geographic/topic extraction)

**Key Architecture:**
- **Database-driven patterns exclusively** - no hardcoded patterns
- **Dynamic market type loading** from MongoDB pattern_libraries collection
- **Market prefix handling** for non-Market patterns during market term processing
- **Confidence scoring** differentiated by processing type

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

### Complete Pipeline Processing Flow

**CRITICAL:** The processing logic differs significantly between market term and standard classifications.

#### **Market Term Classification Pipeline Flow**

**Example:** "Artificial Intelligence (AI) Market in Automotive Outlook & Trends, 2025-2035"

**Stage 1 - Market Term Classification (01_market_term_classifier_v1.py):**
- Input: "Artificial Intelligence (AI) Market in Automotive Outlook & Trends, 2025-2035"
- Detection: "Market in" pattern found in database
- Classification: `market_in`
- Output: Same title + `market_in` classification

**Stage 2 - Date Extraction (02_date_extractor_v1.py):**
- Input: "Artificial Intelligence (AI) Market in Automotive Outlook & Trends, 2025-2035"
- Detection: "2025-2035" matches date range patterns
- Extraction: Date = "2025-2035"
- Output: "Artificial Intelligence (AI) Market in Automotive Outlook & Trends" + date

**Stage 3 - Market-Aware Report Type Extraction (03_report_type_extractor_v2.py):**
- Input: "Artificial Intelligence (AI) Market in Automotive Outlook & Trends" + `market_in`
- **Market Term Processing Logic:**
  1. **Extract "Market"** from "Market in" phrase
  2. **Preserve "in Automotive"** for next pipeline stage
  3. **Search remaining text** for report patterns **without "Market" prefix**
  4. **Find "Outlook & Trends"** in database patterns (excluding Market prefix)
  5. **Reconstruct:** "Market" + "Outlook & Trends" = **"Market Outlook & Trends"**
- Output: Report type = "Market Outlook & Trends", Pipeline forward = "Artificial Intelligence (AI) in Automotive"

**Stage 4 - Geographic Entity Detection (04_geographic_entity_detector_v1.py):**
- Input: "Artificial Intelligence (AI) in Automotive"
- Detection: "Automotive" may be classified as industry/context (not geographic)
- Output: Pipeline forward = "Artificial Intelligence (AI) in Automotive" (no geographic regions found)

**Stage 5 - Topic Extraction (05_topic_extractor_v1.py):**
- Input: "Artificial Intelligence (AI) in Automotive"
- Processing: No dates, report types, or regions to remove
- Output: topic = "Artificial Intelligence (AI) in Automotive", topicName = "artificial-intelligence-ai-in-automotive"

#### **Standard Classification Pipeline Flow**

**Example:** "APAC Personal Protective Equipment Market Analysis, 2024-2029"

**Stage 1 - Market Term Classification (01_market_term_classifier_v1.py):**
- Input: "APAC Personal Protective Equipment Market Analysis, 2024-2029"
- Detection: No market term patterns found ("Market Analysis" is standard)
- Classification: `standard`
- Output: Same title + `standard` classification

**Stage 2 - Date Extraction (02_date_extractor_v1.py):**
- Input: "APAC Personal Protective Equipment Market Analysis, 2024-2029"
- Detection: "2024-2029" matches date range patterns
- Extraction: Date = "2024-2029"
- Output: "APAC Personal Protective Equipment Market Analysis" + date

**Stage 3 - Standard Report Type Extraction (03_report_type_extractor_v2.py):**
- Input: "APAC Personal Protective Equipment Market Analysis" + `standard`
- **Standard Processing Logic:**
  1. **Direct pattern matching** on complete remaining title
  2. **Find "Market Analysis"** in database patterns (complete match)
  3. **No rearrangement needed**
- Output: Report type = "Market Analysis", Pipeline forward = "APAC Personal Protective Equipment"

**Stage 4 - Geographic Entity Detection (04_geographic_entity_detector_v1.py):**
- Input: "APAC Personal Protective Equipment"
- Detection: "APAC" found in geographic patterns
- Extraction: Region = "APAC"
- Output: Pipeline forward = "Personal Protective Equipment"

**Stage 5 - Topic Extraction (05_topic_extractor_v1.py):**
- Input: "Personal Protective Equipment"
- Processing: Systematic removal complete - this IS the topic
- Output: topic = "Personal Protective Equipment", topicName = "personal-protective-equipment"

**Processing philosophy:** 
- **Market terms:** Extraction, rearrangement, and reconstruction
- **Standard titles:** Systematic removal in sequence (dates, report types, regions)
- **What remains IS the topic** (regardless of internal punctuation)
- **Track performance metrics** in MongoDB for continuous improvement

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

#### **Python Command Requirements**
**CRITICAL: Always use `python3` command, never `python`**
- All bash commands must use `python3` for script execution
- This ensures compatibility with the project's Python environment  
- Examples: `python3 test_03_market_aware_pipeline_v2.py`, `python3 01_market_term_classifier_v1.py`

#### **Script Development Standards**
**All scripts must follow these mandatory patterns:**

1. **Shebang Line:** Always include `#!/usr/bin/env python3` at the top
2. **Logging Configuration:** Include comprehensive logging setup
3. **Error Handling:** Implement try/catch blocks for all major operations
4. **Dynamic Imports:** Use `importlib.util` for cross-script imports (never static imports)
5. **Output Generation:** Always create timestamped output directories and files
6. **Documentation:** Include detailed docstrings and inline comments for complex logic

#### **Module Import Standards**
```python
# CORRECT: Dynamic imports using importlib.util
import importlib.util

def import_module_from_path(module_name: str, file_path: str):
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

# INCORRECT: Static imports (will fail due to directory structure)
# from experiments.01_market_term_classifier_v1 import MarketTermClassifier
```

#### **Database Connection Management**
**CRITICAL: Use shared PatternLibraryManager instances**
- All components must share a single PatternLibraryManager instance
- Never create multiple MongoDB connections in the same script
- Use database connection caching for performance
- Follow the proven pattern from working test scripts

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
- **Date extraction:** 98-99% accuracy ✅ **ACHIEVED: 100% on titles with dates**
- **Report type extraction:** 95-97% accuracy  
- **Geographic detection:** 96-98% accuracy
- **Topic extraction:** 92-95% accuracy
- **Overall processing:** 95-98% complete success

**Quality indicators:**
- < 5% titles requiring human review (confidence < 0.8)
- < 2% false positive geographic detection
- < 1% critical parsing failures

**Phase 2 Validation Results (Latest Test):**
- **Sample Size:** 1,000 documents (2025-08-22)
- **Date Extraction Performance:** 100% accuracy on 979 titles containing dates
- **Proper Categorization:** 21 titles correctly identified as having no dates (not failures)
- **Pattern Coverage:** 0 missed dates (no pattern gaps identified)

### Implementation Strategy

**Enhanced Modular Development:**
1. ✅ **MongoDB library setup and initialization** (Complete)
2. ✅ **Market term classification (2 patterns)** (Complete - 100% accuracy)  
3. ✅ **Date pattern extraction and library building** (Complete - 100% accuracy on titles with dates)
4. ✅ **Enhanced date extractor with numeric pre-filtering** (Complete - 64 patterns, zero gaps)
5. ✅ **Report type pattern extraction and library building** (Complete)
6. ✅ **Enhanced geographic entity detection with dual spaCy models** (Complete)
7. ✅ **HTML processing innovation for concatenation prevention** (Complete)
8. ✅ **Pattern discovery and human review workflow** (Complete)
9. 🔄 **Topic extraction and normalization** (Ready for implementation)
10. 🔄 **End-to-end validation and confidence tuning** (Ready for implementation)

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
- **Enhanced Date Extraction:** Numeric pre-filtering with success/no_dates/missed categorization
- **Comprehensive Pattern Library:** 64 date patterns (enhanced from 45) with zero pattern gaps
- **Table Data Extraction:** Structured region data from HTML report descriptions
- **Individual Document Processing:** Outperforms text aggregation strategies for pattern discovery
- **Human-Review Workflow:** Approval checkboxes and conflict detection for pattern validation

**📋 Production-Ready Components:**
1. ✅ **Market Term Classification:** 100% accuracy with 2-pattern classification system
2. ✅ **Enhanced Date Extraction:** 100% accuracy on titles with dates, 64-pattern library, numeric pre-filtering
3. **Report Type Extraction:** Pattern library approach ready for Phase 3 testing
4. **Enhanced Geographic Detection:** HTML-aware dual-model processing with confidence scoring
5. **Pattern Library Management:** Real-time MongoDB updates with performance tracking
6. **Quality Assurance:** Human review workflow with pattern classification
7. **Performance Monitoring:** Built-in success/failure metrics and edge case identification

**🎯 Final Implementation Phase:**
- Topic extraction logic integration using systematic removal approach
- End-to-end validation pipeline with confidence thresholds
- Production deployment preparation with performance optimization
- Comprehensive testing suite validation

## Git Commit Standards

### Git Commit Signature Override
**IMPORTANT: Use this custom signature for all git commits instead of the default Claude Code signature:**

```
🤖 AI development directed by Brian Haven (Zettit, Inc.) | Technical execution by Claude Code
Co-Authored-By: Claude AI
```

This signature properly represents that Brian Haven (Zettit, Inc.) provides strategic direction and architectural guidance while Claude Code AI handles the technical implementation and coding decisions.

## Task Master AI Instructions
**Import Task Master's development workflow commands and guidelines, treat as if import is in the main CLAUDE.md file.**
@./.taskmaster/CLAUDE.md
