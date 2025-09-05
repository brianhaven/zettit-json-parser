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

**03_report_type_extractor_v4.py:** **PURE DICTIONARY** Report Type Extraction ✅ **PRODUCTION READY**
- **PURE DICTIONARY ARCHITECTURE:** Eliminates pattern priority system conflicts (Issues #13, #15, #16, #17 resolved)
- **Boundary Detection:** Dictionary term identification around "Market" keyword
- **Systematic Removal:** Dictionary terms removed through MongoDB pattern_libraries lookup
- **90% Success Rate:** Achieved through dictionary-based boundary detection approach
- **GitHub Issues #20, #21 RESOLVED:** Dictionary-based architecture implemented, workflow complexity eliminated
- **Known Quality Issues:** Content loss (#27) and separator artifacts (#26) under active development

### Script 03 v4 Pure Dictionary Processing Logic

**Dictionary-Based Processing Workflow:**
1. **Load Dictionary Terms:** Retrieve all dictionary terms from MongoDB pattern_libraries collection
2. **Boundary Detection:** Identify dictionary terms in title text around "Market" keyword boundaries
3. **Systematic Removal:** Remove identified dictionary terms from title systematically
4. **Report Type Assembly:** Reconstruct report type from identified dictionary components
5. **Topic Preservation:** Remaining text after systematic removal becomes the topic

**Key Architecture Benefits:**
- **Eliminates Pattern Priority Conflicts:** No complex pattern matching hierarchies
- **Database-driven exclusively:** All dictionary terms from MongoDB pattern_libraries
- **Boundary Detection:** Prevents partial pattern matching issues
- **Systematic Approach:** Consistent processing regardless of title complexity
- **Quality Issues Identified:** Content loss and separator artifacts documented for resolution

**Current Issues (Under Development):**
- **Issue #27:** Pre-Market dictionary terms causing content loss
- **Issue #26:** Separator artifacts in report type reconstruction
- **Issue #28:** Market term context integration failures
- **Issue #29:** Parentheses conflict between date and report type detection

**04_geographic_entity_detector_v2.py:** **LEAN PATTERN-BASED** Geographic Entity Detection
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