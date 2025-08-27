# Pre-Development Analysis Requirements

**MANDATORY: Before creating or modifying any scripts, Claude Code MUST perform this analysis sequence:**

## 1. Script Component Discovery & Analysis
**Before writing any code, ALWAYS:**
```bash
# Discover available scripts and their purposes
ls experiments/*.py | grep -E "0[0-9]_.*\.py$" | sort

# Analyze class structures in target scripts (VERIFY CURRENT CLASS NAMES)
grep "^class " experiments/01_market_term_classifier_v1.py
grep "^class " experiments/02_date_extractor_v1.py
grep "^class " experiments/03_report_type_extractor_v2.py
grep "^class " experiments/04_geographic_entity_detector_v2.py

# CRITICAL: Identify exact class names for components
grep "^class.*Classifier" experiments/01_market_term_classifier_v1.py
grep "^class.*Extractor" experiments/02_date_extractor_v1.py
grep "^class.*Extractor" experiments/03_report_type_extractor_v2.py
grep "^class.*Detector" experiments/04_geographic_entity_detector_v2.py

# Verify initialization signatures
grep -A 5 "def __init__" experiments/01_market_term_classifier_v1.py
grep -A 5 "def __init__" experiments/02_date_extractor_v1.py
grep -A 5 "def __init__" experiments/03_report_type_extractor_v2.py

# Check public method names (avoid private methods starting with _)
grep -n "def [^_]" experiments/01_market_term_classifier_v1.py
grep -n "def [^_]" experiments/02_date_extractor_v1.py
grep -n "def [^_]" experiments/03_report_type_extractor_v2.py
```

### CURRENT VERIFIED COMPONENT INFORMATION (AS OF 2025-08-27):

**Script 01 - Market Term Classifier:**
- **Class:** `MarketTermClassifier`
- **Initialization:** `MarketTermClassifier(pattern_library_manager=None)` (optional parameter)
- **Main Method:** `classify(title: str) -> ClassificationResult`
- **Result Attributes:** `market_term_type`, `confidence`, etc.

**Script 02 - Date Extractor:**  
- **Class:** `EnhancedDateExtractor` (NOT `DateExtractor`)
- **Initialization:** `EnhancedDateExtractor(pattern_library_manager)` (required parameter)
- **Main Method:** `extract(title: str) -> EnhancedDateExtractionResult`
- **Result Attributes:** `title`, `extracted_date_range`, `confidence`, etc.

**Script 03 - Report Type Extractor:**
- **Class:** `MarketAwareReportTypeExtractor` (NOT `ReportTypeExtractor`)  
- **Initialization:** `MarketAwareReportTypeExtractor(pattern_library_manager)` (required parameter)
- **Main Method:** `extract(title: str, market_term_type: str = "standard", ...) -> MarketAwareReportTypeResult`
- **Result Attributes:** `title`, `extracted_report_type`, `confidence`, etc.

**PatternLibraryManager:**
- **Class:** `PatternLibraryManager`
- **Initialization:** `PatternLibraryManager(connection_string: Optional[str] = None, database_name: str = "deathstar")`
- **Connection:** Requires MongoDB connection string (from env if not provided)

## 2. Architecture Pattern Identification
**Determine which architecture pattern each script follows:**
- **Scripts 01-03:** Legacy architecture requiring `PatternLibraryManager`
- **Script 04+:** Lean architecture using raw MongoDB collections
- **Mixed Scripts:** Verify initialization requirements before integration

## 3. Method Signature Analysis
**Before calling any methods, verify signatures:**
```python
# Check method parameters and return types
# Read method docstrings and parameter expectations
# Identify required vs optional parameters
```

## 4. Integration Compatibility Check
**Before integrating multiple scripts:**
- Verify all components use compatible initialization patterns
- Check that output from one script matches input expectations of the next
- Validate that all required dependencies are available

## 5. Pattern Library Dependencies
**Identify what patterns each script requires:**
```bash
# Check pattern types used by each script
grep "PatternType\|pattern.*type\|get_patterns" experiments/script_name.py
```

## 6. Pipeline Data Flow Analysis
**Before integrating pipeline components, understand the data contracts:**

### VERIFIED METHOD SIGNATURES AND RETURN VALUES:

```python
# Script 01 - MarketTermClassifier
market_classifier = MarketTermClassifier(pattern_library_manager)  # optional param
result = market_classifier.classify(title)  # Returns: ClassificationResult object
# Access attributes: result.market_term_type, result.confidence

# Script 02 - EnhancedDateExtractor  
date_extractor = EnhancedDateExtractor(pattern_library_manager)  # required param
result = date_extractor.extract(title)  # Returns: EnhancedDateExtractionResult object
# Access attributes: result.title, result.extracted_date_range, result.confidence

# Script 03 - MarketAwareReportTypeExtractor
report_extractor = MarketAwareReportTypeExtractor(pattern_library_manager)  # required param
result = report_extractor.extract(title, market_term_type="standard")  # Returns: MarketAwareReportTypeResult object
# Access attributes: result.title, result.extracted_report_type, result.confidence

# CRITICAL: All methods use .extract() NOT extract_report_type() or extract_date()
# CRITICAL: All return objects use .title NOT .remaining_text for remaining text
# CRITICAL: Access report type via .extracted_report_type NOT .final_report_type
```

### Common Errors to Avoid in Test Scripts:
1. **Wrong Method Names:**
   - ❌ `extractor.extract_report_type()` → ✅ `extractor.extract()`
   - ❌ `extractor.extract_date()` → ✅ `extractor.extract()`

2. **Wrong Class Names:**  
   - ❌ `ReportTypeExtractor` → ✅ `MarketAwareReportTypeExtractor`
   - ❌ `DateExtractor` → ✅ `EnhancedDateExtractor`

3. **Wrong Result Attributes:**
   - ❌ `result.remaining_text` → ✅ `result.title` (cleaned title)
   - ❌ `result.final_report_type` → ✅ `result.extracted_report_type`

4. **Wrong Initialization:**
   - ❌ `PatternLibraryManager()` → ✅ `PatternLibraryManager(connection_string)`
   - ❌ Missing required parameters in component initialization

### Pipeline Flow with Correct Attribute Names:
```python  
# Title → Market Classification → Date Extraction → Report Type → Geographic → Topic
market_result = classifier.classify(title)
date_result = extractor.extract(market_result.title)  # Use .title not .remaining_text
report_result = extractor.extract(date_result.title, market_result.market_term_type)
# Each stage passes result.title to next stage
```

## 7. Method Contract Verification
**Before calling methods, verify expected parameters and return values:**
```bash
# Read method docstrings to understand contracts
grep -A 10 "def extract_geographic_entities" experiments/04_geographic_entity_detector_v2.py
grep -A 10 "def classify_market_term" experiments/01_market_term_classifier_v1.py
grep -A 10 "def extract_report_type" experiments/03_report_type_extractor_v2.py

# Check return type patterns
grep -A 5 "return " experiments/script_name.py
```

## Mandatory Pre-Development Analysis Protocol
**Claude Code MUST demonstrate completion of the 7-step analysis above before creating or modifying any scripts. This includes:**

- **Documentation of Findings:** Show output of grep commands and analysis results
- **Architecture Decision Justification:** Explain which patterns to use and why
- **Integration Plan:** Document how components will interact and data will flow
- **Risk Identification:** Highlight potential compatibility issues before coding

**❌ DO NOT:** Write code first and fix errors through trial-and-error
**✅ DO:** Understand the system architecture, then write correct code from the start