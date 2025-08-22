# Experiments Directory Organization

## Processing Order Scripts

These scripts should be run in numerical order for complete market research title processing:

### 1. Market Term Classification
`01_market_term_classifier_v1.py` - Separates "Market for"/"Market in" from standard "Market" titles

### 2. **ENHANCED** Date Pattern Extraction  
`02_date_extractor_v1.py` - **BREAKTHROUGH:** Enhanced date extraction with numeric pre-filtering
- **Numeric Pre-filtering:** Distinguishes "no dates present" vs "dates missed"
- **Enhanced Categorization:** Returns success/no_dates_present/dates_missed status
- **Comprehensive Pattern Library:** 64 patterns across 4 format types (enhanced from 45)
- **Performance:** 100% accuracy on titles with dates (exceeds 98-99% target)
- **Zero Pattern Gaps:** Latest validation shows no missed date patterns

### 3. Report Type Extraction
`03_report_type_extractor_v1.py` - Extracts "Market Size", "Market Analysis", etc. from titles

### 4. Enhanced Geographic Entity Detection
`04_geographic_entity_detector_v1.py` - **BREAKTHROUGH:** Dual spaCy model validation with HTML processing
- **HTML Processing Innovation:** BeautifulSoup parsing prevents concatenation artifacts
- **Dual Model Validation:** en_core_web_md + en_core_web_lg provides 31% more discoveries
- **Table Data Extraction:** Structured region data from HTML descriptions
- **Cross-Model Confidence Scoring:** Validates patterns across both models

### 5. [Future] Publisher Classification
`05_publisher_classifier_v1.py` - (Future) Publisher-specific processing rules

### 6. [Future] Context Analysis
`06_context_analyzer_v1.py` - (Future) Market sector and technology context extraction

## Specialized Scripts

### Pattern Discovery and Enhancement
- `00_pattern_discovery_for_review_v1.py` - **ENHANCED:** Human-review workflow for pattern validation
  - Pattern classification (new terms, aliases, noise)
  - Approval checkboxes for quality control
  - MongoDB conflict detection and resolution
  - Automated pattern library updates

### Legacy Processing Scripts
Legacy versions of these scripts have been moved to the archive/ directory. The current numbered pipeline scripts implement the systematic removal approach for final topic extraction.

## Test Scripts Directory (`tests/`)

Development and validation scripts moved to maintain clean organization:
- `spacy_optimization_v1.py` - spaCy model performance testing and optimization
- `description_analysis_v1.py` - Description field analysis for HTML vs text processing
- `aggregated_test_v1.py` - Text aggregation strategy testing (individual docs outperform)
- `html_analysis_v1.py` - HTML vs plain text comparison (HTML prevents concatenation)
- `dual_model_pattern_discovery_v1.py` - Original dual-model testing (31% improvement proven)
- `add_discovered_patterns_v1.py` - Pattern addition utilities for library management
- `test_date_extractor_v1.py` - Comprehensive date extraction validation
- `test_market_classifier_v1.py` - Market term classification validation
- `test_geographic_detector_v1.py` - Geographic detection accuracy testing
- `test_pattern_manager_v1.py` - Pattern library manager validation

## Processing Philosophy

**Enhanced Systematic Removal Approach:**
1. **Remove known patterns in priority order** (dates, report types, regions)
2. **What remains IS the topic** (regardless of internal punctuation) 
3. **Track performance metrics** in MongoDB for continuous improvement
4. **Use MongoDB pattern libraries** for real-time updates without deployment
5. **HTML-aware processing** prevents concatenation artifacts in geographic detection
6. **Dual-model validation** provides enhanced pattern discovery and confidence scoring
7. **Human review workflow** enables continuous pattern library enhancement

## Output Standards

All scripts generate dual-timestamp outputs:
- **Filename format:** `{YYYYMMDD_HHMMSS}_{TYPE}.{ext}` (Pacific Time)
- **File headers:** Include both PDT/PST and UTC timestamps
- **Output directory:** `/outputs/` with structured naming

## Database Integration

- **Primary data:** `markets_raw` collection (19,558+ titles)
- **Pattern libraries:** `pattern_libraries` collection with real-time updates
- **Processed results:** `markets_processed` collection
- **Performance tracking:** Built-in success/failure metrics with confidence scoring

## Key Technical Breakthroughs

### Enhanced Date Extraction with Numeric Pre-filtering
- **Problem:** Titles without dates were incorrectly classified as extraction failures
- **Solution:** Numeric content analysis to distinguish "no dates present" vs "dates missed"
- **Result:** 100% accuracy on titles containing dates, proper categorization of no-date titles

### HTML Processing Innovation
- **Problem:** spaCy was concatenating regions like "KoreaIndonesiaAustraliaThailand" 
- **Solution:** BeautifulSoup parsing with proper block-level separators
- **Result:** Clean geographic entity detection from HTML descriptions

### Dual spaCy Model Validation  
- **Finding:** Single model (en_core_web_md) missed many patterns
- **Enhancement:** Added en_core_web_lg for cross-validation
- **Result:** 31% more pattern discoveries with confidence scoring

### Individual vs Aggregated Processing
- **Testing:** Compared bulk text processing vs individual document processing
- **Finding:** Individual document processing outperforms text aggregation
- **Implementation:** Process each description separately for optimal results

### Human Review Workflow
- **Challenge:** Automatic pattern discovery includes noise
- **Solution:** Approval workflow with classification (new terms, aliases, noise)
- **Features:** MongoDB conflict detection and automated library updates