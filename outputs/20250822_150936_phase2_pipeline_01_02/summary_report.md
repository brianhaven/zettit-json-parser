# Phase 2 Pipeline Test Results: Market Term Classifier → Date Extractor

**Analysis Date (PDT):** 2025-08-22 15:09:36 PDT
**Analysis Date (UTC):** 2025-08-22 22:09:36 UTC
**Sample Size:** 1,000 documents
**Successfully Processed:** 1,000 documents

## Pipeline Performance Summary

### Market Term Classification Results
- **Standard**: 996 (99.60%)
- **Market For**: 4 (0.40%)

### Date Extraction Results
- **Successful Extractions**: 600 (60.00%)
- **Failed Extractions**: 400 (40.00%)

### Date Format Distribution
- **Terminal Comma**: 479 (79.83%)
- **Range Format**: 33 (5.50%)
- **Embedded Format**: 85 (14.17%)
- **Bracket Format**: 3 (0.50%)

## Key Insights

### Date Pattern Discovery
- **Terminal Comma**: 479 patterns found (avg confidence: 0.950)
- **Range Format**: 33 patterns found (avg confidence: 0.980)
- **Embedded Format**: 85 patterns found (avg confidence: 0.850)
- **Bracket Format**: 3 patterns found (avg confidence: 0.900)

### Edge Cases Identified
- **Total Edge Cases**: 400
- **Primary Issue**: No date patterns found in titles

## Recommendations

### Pattern Library Enhancement
1. Analyze date format variations in detailed patterns report
2. Build comprehensive date pattern library in MongoDB
3. Focus on edge cases for pattern discovery

### Accuracy Improvement Opportunities
1. **Current Date Extraction Rate**: 60.00%
2. **Target**: >98% accuracy
3. **Gap to Close**: 38.00 percentage points

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
