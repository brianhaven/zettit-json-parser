# Pipeline Integration Reference Card

**Quick reference for creating test scripts and integrating pipeline components**

## Component Initialization Patterns

### Scripts 01-03 (Legacy Architecture)
```python
# Import PatternLibraryManager
pattern_manager = import_module_from_path("pattern_library_manager",
                                        os.path.join(parent_dir, "00b_pattern_library_manager_v1.py"))

# Initialize with connection string
pattern_lib_manager = pattern_manager.PatternLibraryManager(os.getenv('MONGODB_URI'))

# Initialize components
market_classifier = script01.MarketTermClassifier(pattern_lib_manager)
date_extractor = script02.EnhancedDateExtractor(pattern_lib_manager)
report_extractor = script03.MarketAwareReportTypeExtractor(pattern_lib_manager)
```

### Script 04+ (Lean Architecture)
```python
# Connect to MongoDB
client = MongoClient(os.getenv('MONGODB_URI'))
patterns_collection = client['deathstar']['pattern_libraries']

# Initialize with raw collection
geo_detector = script04.GeographicEntityDetector(patterns_collection)
```

## Current Class Names (VERIFY BEFORE USE)

| Script | Class Name | Command to Verify |
|--------|------------|------------------|
| 01 | `MarketTermClassifier` | `grep "^class " 01_market_term_classifier_v1.py` |
| 02 | `EnhancedDateExtractor` | `grep "^class " 02_date_extractor_v1.py` |
| 03 | `MarketAwareReportTypeExtractor` | `grep "^class " 03_report_type_extractor_v2.py` |
| 04 v2 | `GeographicEntityDetector` | `grep "^class " 04_geographic_entity_detector_v2.py` |

## Common Errors to Avoid

❌ **WRONG:**
- `market_classifier = script01.MarketTermClassifier(patterns_collection)`
- `pattern_lib_manager = pattern_manager.PatternLibraryManager(patterns_collection)`
- `date_extractor = script02.DateExtractor(pattern_lib_manager)`

✅ **CORRECT:**
- Use `PatternLibraryManager` with connection string for Scripts 01-03
- Use raw collection for Script 04+
- Always verify current class names with `grep`

## Pre-Test Checklist

1. ✅ Verify component initialization patterns
2. ✅ Check class names with grep commands
3. ✅ Validate import paths are correct
4. ✅ Ensure MongoDB connection method matches architecture
5. ✅ Test in experiments/tests/ directory

## Architecture Summary
```
Scripts 01-03: MongoDB URI → PatternLibraryManager → Component
Script 04+:    MongoDB URI → Raw Collection → Component
```

---
**Created:** 2025-08-26  
**Purpose:** Prevent common integration errors in pipeline testing