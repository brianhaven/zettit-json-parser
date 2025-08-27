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
- **Primary data:** `markets_raw` collection (19,558+ titles) - field: `report_title_short`
- **Pattern libraries:** `pattern_libraries` collection with real-time updates
- **Processed results:** `markets_processed` collection for output tracking
- **Performance metrics:** Built-in success/failure tracking

### Claude Code MongoDB Integration
**IMPORTANT: Use MongoDB MCP Server for all database interactions**

#### **MongoDB MCP Server Commands**
The MongoDB MCP server provides efficient database access through Claude Code. **Always prefer MCP commands over bash scripts for database operations.**

**Core Database Operations:**
```bash
# List collections and databases
mcp__mongodb__list-databases                    # List all databases
mcp__mongodb__list-collections database         # List collections in database

# Query operations
mcp__mongodb__find database collection filter   # Find documents with filter
mcp__mongodb__count database collection query   # Count documents with query
mcp__mongodb__aggregate database collection pipeline  # Run aggregation pipeline

# Data modification
mcp__mongodb__insert-many database collection documents  # Insert documents
mcp__mongodb__update-many database collection filter update  # Update documents
mcp__mongodb__delete-many database collection filter  # Delete documents

# Schema and indexes
mcp__mongodb__collection-schema database collection     # Get collection schema
mcp__mongodb__collection-indexes database collection    # List indexes
mcp__mongodb__create-index database collection keys name  # Create index
```

**Pattern Library Management Examples:**
```bash
# Query report type patterns
mcp__mongodb__find deathstar pattern_libraries {"type": "report_type"}

# Count geographic patterns
mcp__mongodb__count deathstar pattern_libraries {"type": "geographic_entity"}

# Aggregate pattern statistics by type
mcp__mongodb__aggregate deathstar pattern_libraries '[{"$group": {"_id": "$type", "count": {"$sum": 1}}}]'

# Find high-priority patterns
mcp__mongodb__find deathstar pattern_libraries {"priority": {"$lte": 5}, "active": true}
```

**Market Data Analysis:**
```bash
# Query market research titles
mcp__mongodb__find deathstar markets_raw {"report_title_short": {"$regex": "Market", "$options": "i"}}

# Count processed results
mcp__mongodb__count deathstar markets_processed {}

# Analyze title patterns
mcp__mongodb__aggregate deathstar markets_raw '[{"$match": {"report_title_short": {"$regex": "2024"}}}, {"$count": "titles_with_2024"}]'
```

**For scripts:** Scripts use pymongo API directly
```python
from pymongo import MongoClient
client = MongoClient(os.getenv('MONGODB_URI'))
db = client['deathstar']
```

**Benefits of MongoDB MCP Server:**
- **Efficiency:** Direct database access without subprocess overhead
- **Error Handling:** Better error reporting and connection management  
- **Performance:** Optimized queries with proper connection pooling
- **Security:** Secure credential management through MCP configuration
- **Debugging:** Clear query results and structured error messages

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

**03_report_type_extractor_v2.py:** **MARKET-AWARE** Report Type Extraction ✅ **PRODUCTION READY**
- **DUAL PROCESSING LOGIC:** Handles market term and standard classifications differently
- **Market Term Processing:** Extraction, rearrangement, and reconstruction workflow
- **Standard Processing:** Direct database pattern matching
- **Acronym-Embedded Processing:** Special handling for acronym extraction with pipeline preservation
- **GitHub Issue #11 RESOLVED:** Fixed compound patterns matching before acronym_embedded
- **Performance:** Achieved 95-97% accuracy target with 355 validated patterns across 5 format types
- **Database Quality Assured:** Comprehensive pattern validation and malformed entry cleanup

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

#### **Component Initialization & Integration Standards**
**CRITICAL: Follow these mandatory patterns when creating test scripts and integrating pipeline components:**

**📋 Quick Reference:** See @experiments/tests/PIPELINE_INTEGRATION_REFERENCE.md for condensed integration patterns and class name verification commands.

##### **Script Component Initialization Patterns**

**ALL Scripts (01-07) - Consistent Architecture:**
- **MANDATORY: All scripts must use PatternLibraryManager** for database consistency
- **Initialization Pattern:**
```python
# Import PatternLibraryManager
pattern_manager = import_module_from_path("pattern_library_manager",
                                        os.path.join(parent_dir, "00b_pattern_library_manager_v1.py"))

# Initialize with connection string (not collection)
pattern_lib_manager = pattern_manager.PatternLibraryManager(os.getenv('MONGODB_URI'))

# Initialize ALL components with PatternLibraryManager
market_classifier = script01.MarketTermClassifier(pattern_lib_manager)
date_extractor = script02.EnhancedDateExtractor(pattern_lib_manager)
report_extractor = script03.MarketAwareReportTypeExtractor(pattern_lib_manager)
geo_detector = script04.GeographicEntityDetector(pattern_lib_manager)  # UPDATED: Must use PatternLibraryManager
topic_extractor = script05.TopicExtractor(pattern_lib_manager)         # ALL scripts follow this pattern
```

**DEPRECATED Approach (DO NOT USE):**
```python
# ❌ WRONG: Direct MongoDB collection usage
client = MongoClient(os.getenv('MONGODB_URI'))
patterns_collection = client['deathstar']['pattern_libraries']
geo_detector = script04.GeographicEntityDetector(patterns_collection)
```

##### **Current Component Class Names (MANDATORY REFERENCE)**
**ALWAYS verify class names before creating test scripts:**

| Script | Current Class Name | Legacy/Incorrect Names |
|--------|-------------------|------------------------|
| 01 | `MarketTermClassifier` | ✓ (unchanged) |
| 02 | `EnhancedDateExtractor` | ❌ `DateExtractor` |
| 03 | `MarketAwareReportTypeExtractor` | ❌ `ReportTypeExtractor` |
| 04 v2 | `GeographicEntityDetector` | ✓ (lean architecture) |
| 05 | `TopicExtractor` | (to be confirmed) |

##### **Common Integration Errors to Avoid**

**❌ NEVER DO:**
```python
# Wrong: Raw collection to Scripts 01-03
market_classifier = script01.MarketTermClassifier(patterns_collection)

# Wrong: Collection to PatternLibraryManager
pattern_lib_manager = pattern_manager.PatternLibraryManager(patterns_collection)

# Wrong: Outdated class names
date_extractor = script02.DateExtractor(pattern_lib_manager)
report_extractor = script03.ReportTypeExtractor(pattern_lib_manager)
```

**✅ CORRECT PATTERNS:**
```python
# Correct: PatternLibraryManager for Scripts 01-03
pattern_lib_manager = pattern_manager.PatternLibraryManager(os.getenv('MONGODB_URI'))
market_classifier = script01.MarketTermClassifier(pattern_lib_manager)

# Correct: Current class names
date_extractor = script02.EnhancedDateExtractor(pattern_lib_manager)
report_extractor = script03.MarketAwareReportTypeExtractor(pattern_lib_manager)

# Correct: Raw collection for Script 04+
geo_detector = script04.GeographicEntityDetector(patterns_collection)
```

##### **Test Script Development Checklist**
**Before running any pipeline test, verify:**

1. ✅ **Component Initialization**: Scripts 01-03 use PatternLibraryManager, Scripts 04+ use raw collection
2. ✅ **Class Name Verification**: Use `grep "^class " script_name.py` to verify current class names  
3. ✅ **Import Path Validation**: Ensure all module imports use correct absolute paths
4. ✅ **MongoDB Connection**: Use connection string for PatternLibraryManager, collection for lean components
5. ✅ **Architecture Consistency**: Don't mix initialization patterns within same script

##### **Pipeline Component Architecture Summary**
```
Scripts 01-03 (Legacy): MongoDB URI → PatternLibraryManager → Component
Script 04+ (Lean):      MongoDB URI → Raw Collection → Component
```

#### **Python Command Requirements**
**CRITICAL: Always use `python3` command, never `python`**
- All bash commands must use `python3` for script execution
- This ensures compatibility with the project's Python environment  
- Examples: `python3 test_03_market_aware_pipeline_v2.py`, `python3 01_market_term_classifier_v1.py`

#### **Pre-Development Analysis Requirements**
**MANDATORY: Before creating or modifying any scripts, Claude Code MUST perform this analysis sequence:**

##### **1. Script Component Discovery & Analysis**
**Before writing any code, ALWAYS:**
```bash
# Discover available scripts and their purposes
ls experiments/*.py | grep -E "^[0-9]"

# Analyze class structures in target scripts
grep "^class " experiments/01_market_term_classifier_v1.py
grep "^class " experiments/02_date_extractor_v1.py
grep "^class " experiments/03_report_type_extractor_v2.py
grep "^class " experiments/04_geographic_entity_detector_v2.py

# Identify key methods and initialization patterns
grep "def __init__" experiments/script_name.py
grep "def extract\|def classify\|def process" experiments/script_name.py
```

##### **2. Architecture Pattern Identification**
**Determine which architecture pattern each script follows:**
- **Scripts 01-03:** Legacy architecture requiring `PatternLibraryManager`
- **Script 04+:** Lean architecture using raw MongoDB collections
- **Mixed Scripts:** Verify initialization requirements before integration

##### **3. Method Signature Analysis**
**Before calling any methods, verify signatures:**
```python
# Check method parameters and return types
# Read method docstrings and parameter expectations
# Identify required vs optional parameters
```

##### **4. Integration Compatibility Check**
**Before integrating multiple scripts:**
- Verify all components use compatible initialization patterns
- Check that output from one script matches input expectations of the next
- Validate that all required dependencies are available

##### **5. Pattern Library Dependencies**
**Identify what patterns each script requires:**
```bash
# Check pattern types used by each script
grep "PatternType\|pattern.*type\|get_patterns" experiments/script_name.py
```

##### **6. Pipeline Data Flow Analysis**
**Before integrating pipeline components, understand the data contracts:**
```python
# Analyze input/output data structures
# Example: What does each script expect as input?
market_result = classifier.classify_market_term(title)  # Returns: dict with 'market_term_type', 'confidence'
date_result = extractor.extract_date(remaining_title)   # Returns: dict with 'extracted_forecast_date_range', 'remaining_title'
report_result = extractor.extract_report_type(text, market_type)  # Returns: dict with 'extracted_report_type', 'pipeline_forward_text'
geo_result = detector.extract_geographic_entities(text)  # Returns: GeographicExtractionResult object with .extracted_regions, .remaining_text

# Understand the pipeline flow
# Title → Market Classification → Date Extraction → Report Type → Geographic → Topic
# Each stage removes its component and passes remaining text to next stage
```

##### **7. Method Contract Verification**
**Before calling methods, verify expected parameters and return values:**
```bash
# Read method docstrings to understand contracts
grep -A 10 "def extract_geographic_entities" experiments/04_geographic_entity_detector_v2.py
grep -A 10 "def classify_market_term" experiments/01_market_term_classifier_v1.py
grep -A 10 "def extract_report_type" experiments/03_report_type_extractor_v2.py

# Check return type patterns
grep -A 5 "return " experiments/script_name.py
```

#### **Mandatory Pre-Development Analysis Protocol**
**Claude Code MUST demonstrate completion of the 7-step analysis above before creating or modifying any scripts. This includes:**

- **Documentation of Findings:** Show output of grep commands and analysis results
- **Architecture Decision Justification:** Explain which patterns to use and why
- **Integration Plan:** Document how components will interact and data will flow
- **Risk Identification:** Highlight potential compatibility issues before coding

**❌ DO NOT:** Write code first and fix errors through trial-and-error
**✅ DO:** Understand the system architecture, then write correct code from the start

#### **Script Development Standards**
**All scripts must follow these mandatory patterns AFTER completing pre-development analysis:**

1. **Pre-Analysis Completion:** Must complete all 7 steps above before coding
2. **Shebang Line:** Always include `#!/usr/bin/env python3` at the top
3. **Logging Configuration:** Include comprehensive logging setup
4. **Error Handling:** Implement try/catch blocks for all major operations
5. **Dynamic Imports:** Use `importlib.util` for cross-script imports (never static imports)
6. **Verified Integration:** Use only verified class names and initialization patterns
7. **Output Generation:** Always create timestamped output directories and files
8. **Documentation:** Include detailed docstrings and inline comments for complex logic

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
- **Acronym-Embedded Pattern Processing:** Special extraction logic with pipeline preservation and proper enum handling
- **Market-Aware Processing Logic:** Dual workflow system for market term vs standard title classification

**📋 Production-Ready Components:**
1. ✅ **Market Term Classification:** 100% accuracy with 2-pattern classification system
2. ✅ **Enhanced Date Extraction:** 100% accuracy on titles with dates, 64-pattern library, numeric pre-filtering
3. ✅ **Report Type Extraction:** **PRODUCTION READY** - Market-aware processing with 355 validated patterns
   - ✅ Dual processing workflows (market term vs standard)
   - ✅ Acronym-embedded pattern support (GitHub Issue #11 resolved)
   - ✅ Database quality assurance with malformed pattern cleanup
   - ✅ 5 format types: compound (88.5%), terminal (4.8%), embedded (2.8%), prefix (2.3%), acronym (1.7%)
4. 🔄 **Geographic Entity Detection:** Ready for Phase 4 lean pattern-based refactoring
5. ✅ **Pattern Library Management:** Real-time MongoDB updates with performance tracking
6. ✅ **Quality Assurance:** Human review workflow with pattern classification
7. ✅ **Performance Monitoring:** Built-in success/failure metrics and edge case identification
8. ✅ **MongoDB MCP Integration:** Efficient database access through MCP server commands

**🎯 Current Implementation Phase: Phase 4 Refactoring & Phase 5 Preparation**
- **Phase 3:** ✅ **COMPLETE** - Report Type Extraction production-ready with 355 validated patterns
- **Phase 4:** 🔄 **READY TO BEGIN** - Geographic Entity Detector lean pattern-based refactoring (GitHub Issue #12)
- **Phase 5:** ⏳ **QUEUED** - Topic Extractor testing with corrected pipeline foundation  
- **Foundation Strength:** Scripts 01→02→03 provide robust 89% complete production-ready processing capability
- **Next Priority:** Archive Script 04 and implement lean database-driven approach

## Git Commit Standards

### Git Commit Signature Override
**IMPORTANT: Use this custom signature for all git commits instead of the default Claude Code signature:**

```
🤖 AI development directed by Brian Haven (Zettit, Inc.) | Technical execution by Claude Code
Co-Authored-By: Claude AI
```

This signature properly represents that Brian Haven (Zettit, Inc.) provides strategic direction and architectural guidance while Claude Code AI handles the technical implementation and coding decisions.

## TODO TOOL SAFETY RULES

**🚨 CRITICAL: Prevent accidental todo list clearing while enabling safe viewing**

### TodoWrite Tool Usage Policy

**TodoWrite can be used safely for BOTH viewing and modifying todos with these rules:**

#### **✅ SAFE Viewing Pattern:**
When user asks to "show todos", "view todos", "what are the pending todos", or "what's next":
- **DO:** Call TodoWrite with the current todos to display them 
- **NEVER:** Pass an empty array `[]` or modified todo list just to view
- **Pattern:** Only call TodoWrite if you have the current todo state to preserve

#### **✅ SAFE Modification Pattern:**  
When user asks to add, remove, or update specific todos:
- **DO:** Call TodoWrite with the intentional changes
- **CONFIRM:** State exactly what changes will be made before calling
- **VERIFY:** Ensure the todo array includes existing todos plus modifications

#### **❌ FORBIDDEN Patterns:**
```python
# NEVER do this when user asks to view todos:
TodoWrite(todos=[])  # This CLEARS all todos!

# NEVER pass empty or partial arrays unless intentionally clearing:
TodoWrite(todos=[new_todo_only])  # This LOSES existing todos!
```

#### **🔄 Correct Viewing Approach:**
```python
# When user asks "show me todos" and you don't have current state:
# Explain: "I don't have the current todo state loaded. Let me help you check them another way or add new ones."

# When you have current todo state:
# Call TodoWrite with existing todos to display them safely
TodoWrite(todos=current_todos_preserved)
```

### Error Prevention Protocol

**BEFORE any TodoWrite call:**
1. **Identify intent:** Is this to view, add, remove, or modify?
2. **Preserve existing:** Never lose existing todos unless explicitly asked to remove them
3. **State changes:** Clearly explain what the TodoWrite call will do
4. **Verify array:** Ensure the todos array contains all intended todos

### Recovery Protocol

**If todos are accidentally cleared:**
1. Immediately apologize and acknowledge the error
2. Explain that todos cannot be recovered from context  
3. Help recreate important todos from conversation history if possible
4. Learn from the mistake to prevent future occurrences

**This policy enables safe todo viewing while preventing accidental data loss.**

## Task Master AI Instructions
**Import Task Master's development workflow commands and guidelines, treat as if import is in the main CLAUDE.md file.**
@./.taskmaster/CLAUDE.md
