# Processing Pipeline Components

## Enhanced systematic removal approach with dual validation and HTML processing:

### Stage 1: Setup and Initialization
- **00_pattern_discovery_for_review_v1.py:** Discover new patterns requiring human validation
  - Human-review workflow with approval checkboxes
  - Pattern classification (new terms, aliases, noise)
  - MongoDB conflict detection and resolution
- **00a_mongodb_setup_v1.py:** Initialize MongoDB collections and indexes
- **00b_pattern_library_manager_v1.py:** Manage pattern library operations

### Stage 2: Core Processing Pipeline

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

**03_report_type_extractor_v2.py:** **MARKET-AWARE** Report Type Extraction ✅ **PRODUCTION READY**
- **DUAL PROCESSING LOGIC:** Handles market term and standard classifications differently
- **Market Term Processing:** Extraction, rearrangement, and reconstruction workflow
- **Standard Processing:** Direct database pattern matching
- **Acronym-Embedded Processing:** Special handling for acronym extraction with pipeline preservation
- **GitHub Issue #11 RESOLVED:** Fixed compound patterns matching before acronym_embedded
- **Performance:** Achieved 95-97% accuracy target with 355 validated patterns across 5 format types
- **Database Quality Assured:** Comprehensive pattern validation and malformed entry cleanup

### Market Term vs Standard Processing Logic

**Market Term Classification Processing Logic:**
For titles classified as `market_for`, `market_in`, `market_by`, etc.:
1. **Extract "Market"** from the market term phrase ("Market in" → extract "Market")
2. **Preserve connector context** ("in Automotive" remains for pipeline)
3. **Search for report type patterns** in remaining text **excluding "Market" prefix**
4. **Reconstruct final report type** by prepending extracted "Market" to found pattern

**Standard Classification Processing Logic:**
For titles classified as `standard`:
1. **Direct pattern matching** using complete database patterns
2. **No rearrangement needed** - process title as-is after date removal

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

### Stage 3: Topic Extraction (Final step after geographic removal)
- **Systematic Removal:** Remove all known patterns (dates, report types, regions) in sequence
- **What remains IS the topic:** Preserves technical compounds regardless of internal punctuation
- **Normalization:** Create `topicName` while preserving original in `topic`
- **Confidence tracking:** Identify edge cases for human review

## Extracted Field Standards

**Required output fields:**
- `market_term_type`: "standard", "market_for", or "market_in"
- `extracted_forecast_date_range`: Date/range string
- `extracted_report_type`: Full report type including "Market"
- `extracted_regions`: Array preserving source order
- `topic`: Clean extracted topic
- `topicName`: Normalized topic for system use
- `confidence_score`: Float 0.0-1.0 for quality tracking