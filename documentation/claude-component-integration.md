# Component Initialization & Integration Standards

**CRITICAL: Follow these mandatory patterns when creating test scripts and integrating pipeline components:**

**📋 Quick Reference:** See @experiments/tests/PIPELINE_INTEGRATION_REFERENCE.md for condensed integration patterns and class name verification commands.

## Script Component Initialization Patterns

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
report_extractor = script03.PureDictionaryReportTypeExtractor(pattern_lib_manager)
geo_detector = script04.GeographicEntityDetector(patterns_collection)  # Script 04 v2 uses raw collection
topic_extractor = script05.TopicExtractor(pattern_lib_manager)         # ALL scripts follow this pattern
```

**DEPRECATED Approach (DO NOT USE):**
```python
# ❌ WRONG: Direct MongoDB collection usage
client = MongoClient(os.getenv('MONGODB_URI'))
patterns_collection = client['deathstar']['pattern_libraries']
geo_detector = script04.GeographicEntityDetector(patterns_collection)
```

## Current Component Class Names (UPDATED 2025-09-05)
**ALWAYS verify class names before creating test scripts:**

| Script | Current Class Name | Initialization | Main Method | Status | Recent Updates |
|--------|-------------------|---------------|-------------|--------|----------------|
| 01 | `MarketTermClassifier` | `(pattern_library_manager=None)` | `classify(title)` | ✅ PRODUCTION | Enhanced "market_in" context integration (Issue #28) |
| 02 | `EnhancedDateExtractor` | `(pattern_library_manager)` REQUIRED | `extract(title)` | ✅ PRODUCTION | Enhanced parentheses boundary detection (Issue #29) |
| 03 v4 | `PureDictionaryReportTypeExtractor` | `(pattern_library_manager)` REQUIRED | `extract(title)` | ✅ PRODUCTION | Content preservation, separator cleanup, symbol preservation (Issues #19, #24, #26, #27) |
| 04 v2 | `GeographicEntityDetector` | `(patterns_collection)` RAW | `extract_geographic_entities(text)` | ✅ PRODUCTION | Pattern curation, attribute standardization, orphaned preposition cleanup (Issues #18, #19, #22, #28) |
| 05 | `TopicExtractor` | `(pattern_library_manager)` | `extract(title)` | 🔄 READY | Awaiting Phase 5 implementation |

### CRITICAL METHOD AND ATTRIBUTE CORRECTIONS:

**Wrong Method Names (Common Errors):**
- ❌ `extract_report_type()` → ✅ `extract()` (Script 03)
- ❌ `extract_date()` → ✅ `extract()` (Script 02)  
- ❌ `classify_market_term()` → ✅ `classify()` (Script 01)

**Wrong Result Attributes (Common Errors):**
- ❌ `result.remaining_text` → ✅ `result.title` (cleaned remaining text)
- ❌ `result.final_report_type` → ✅ `result.extracted_report_type`
- ❌ `result.extracted_forecast_date_range` → ✅ `result.extracted_date_range`

## Common Integration Errors to Avoid

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

## Test Script Development Checklist
**Before running any pipeline test, verify:**

1. ✅ **Component Initialization**: Scripts 01-03 use PatternLibraryManager, Scripts 04+ use raw collection
2. ✅ **Class Name Verification**: Use `grep "^class.*Classifier\|^class.*Extractor\|^class.*Detector" script_name.py` 
3. ✅ **Method Name Verification**: Use `grep -n "def [^_]" script_name.py` to see public methods
4. ✅ **Import Path Validation**: Ensure all module imports use correct absolute paths
5. ✅ **MongoDB Connection**: Use connection string for PatternLibraryManager, collection for lean components
6. ✅ **Architecture Consistency**: Don't mix initialization patterns within same script
7. ✅ **Result Object Verification**: Check actual result class attributes before accessing them

### COMPLETE CORRECT INTEGRATION EXAMPLE:

```python
# VERIFIED WORKING PATTERN (2025-08-27)
import os
import sys
from pymongo import MongoClient
import importlib.util

# Dynamic imports
def import_module_from_path(module_name: str, file_path: str):
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

# Import modules
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
pattern_manager = import_module_from_path("pattern_library_manager",
                                        os.path.join(parent_dir, "00b_pattern_library_manager_v1.py"))
script01 = import_module_from_path("market_classifier", 
                                 os.path.join(parent_dir, "01_market_term_classifier_v1.py"))
script02 = import_module_from_path("date_extractor",
                                 os.path.join(parent_dir, "02_date_extractor_v1.py"))
script03 = import_module_from_path("report_extractor",
                                 os.path.join(parent_dir, "03_report_type_extractor_v2.py"))

# Initialize PatternLibraryManager
pattern_lib_manager = pattern_manager.PatternLibraryManager(os.getenv('MONGODB_URI'))

# Initialize components with CORRECT class names
market_classifier = script01.MarketTermClassifier(pattern_lib_manager)  # optional param
date_extractor = script02.EnhancedDateExtractor(pattern_lib_manager)     # required param
report_extractor = script03.MarketAwareReportTypeExtractor(pattern_lib_manager)  # required param

# Process with CORRECT method names and attributes
title = "APAC Personal Protective Equipment Market Analysis, 2024-2029"

# Step 1: Market classification
market_result = market_classifier.classify(title)  # NOT classify_market_term()
print(f"Market Type: {market_result.market_term_type}")

# Step 2: Date extraction  
date_result = date_extractor.extract(market_result.title)  # NOT extract_date(), use .title
print(f"Date: {date_result.extracted_date_range}")

# Step 3: Report type extraction
report_result = report_extractor.extract(date_result.title, market_result.market_term_type)  # NOT extract_report_type()
print(f"Report Type: {report_result.extracted_report_type}")  # NOT .final_report_type
print(f"Remaining: {report_result.title}")  # NOT .remaining_text
```

## Pipeline Component Architecture Summary

### ✅ Production-Ready Architecture (2025-09-23)
```
Scripts 01-03 (Enhanced): MongoDB URI → PatternLibraryManager → Component
Script 04+ (Lean):        MongoDB URI → Raw Collection → Component
```

### All Foundation Issues Resolved:
- **Phase 1:** ✅ Foundation Issues (Critical infrastructure)
- **Phase 2:** ✅ Integration Issues (Cross-script coordination)
- **Phase 3:** ✅ Complex Issues (Advanced logic and edge cases)
- **Phase 4:** ✅ Geographic Entity Detection (Lean pattern-based)

### GitHub Issues Closed (14 total):
✅ #13, #15, #16, #17, #18, #19, #20, #21, #22, #24, #25, #26, #27, #28, #29

### Production Status:
- **Pipeline:** 01→02→03v4→04 fully operational and production-ready
- **Success Metrics:** All target accuracy rates achieved or exceeded
- **Quality Assurance:** Comprehensive testing with 250+ real database titles
- **Next Phase:** Script 05 (Topic Extractor) Testing & Refinement