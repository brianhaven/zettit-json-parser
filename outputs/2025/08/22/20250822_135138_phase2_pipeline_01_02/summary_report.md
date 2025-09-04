# Phase 2 Pipeline Test Results: Market Term Classifier → Date Extractor

**Analysis Date (PDT):** 2025-08-22 13:51:38 PDT
**Analysis Date (UTC):** 2025-08-22 20:51:38 UTC
**Sample Size:** 1,000 documents
**Successfully Processed:** 1,000 documents

## Pipeline Performance Summary

### Market Term Classification Results
- **Standard**: 995 (99.50%)
- **Market For**: 3 (0.30%)
- **Market In**: 2 (0.20%)

### Date Extraction Results
- **Successful Extractions**: 584 (58.40%)
- **Failed Extractions**: 416 (41.60%)

### Date Format Distribution
- **Terminal Comma**: 505 (86.47%)
- **Embedded Format**: 57 (9.76%)
- **Range Format**: 20 (3.42%)
- **Bracket Format**: 2 (0.34%)

## Key Insights

### Date Pattern Discovery
- **Terminal Comma**: 505 patterns found (avg confidence: 0.950)
- **Embedded Format**: 57 patterns found (avg confidence: 0.850)
- **Range Format**: 20 patterns found (avg confidence: 0.980)
- **Bracket Format**: 2 patterns found (avg confidence: 0.900)

### Edge Cases Identified
- **Total Edge Cases**: 416
- **Primary Issue**: No date patterns found in titles

## Recommendations

### Pattern Library Enhancement
1. Analyze date format variations in detailed patterns report
2. Build comprehensive date pattern library in MongoDB
3. Focus on edge cases for pattern discovery

### Accuracy Improvement Opportunities
1. **Current Date Extraction Rate**: 58.40%
2. **Target**: >98% accuracy
3. **Gap to Close**: 39.60 percentage points

## Next Steps
1. Review detailed date pattern analysis
2. Enhance date pattern library in MongoDB
3. Run iteration 2 with improved patterns
4. Continue until >98% accuracy achieved

## Files Generated
- `summary_report.md` - This overview report
- `detailed_results.json` - Complete pipeline results
- `date_pattern_analysis.json` - Date format pattern analysis
- `edge_cases.json` - Titles requiring pattern enhancement
- `sample_data.json` - Random sample for manual review (50 titles)
