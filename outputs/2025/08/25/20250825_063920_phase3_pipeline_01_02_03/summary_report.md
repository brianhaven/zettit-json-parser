# Phase 3 Pipeline Test Summary Report

**Analysis Date (PDT):** 2025-08-24 23:39:20 PDT  
**Analysis Date (UTC):** 2025-08-25 06:39:20 UTC

## Executive Summary

- **Total Titles Processed:** 1,000
- **Market Term Classification Rate:** 100.0%
- **Date Extraction Success:** 60.7% (607/1,000)
- **Titles with No Dates:** 39.3% (393/1,000)
- **Report Type Extraction Success:** 16.2% (162/1,000)
- **Special Market Cases Found:** 0.1% (1/1,000)

## Phase 1: Market Term Classification Results

- **standard:** 994 titles (99.4%)
- **market_for:** 6 titles (0.6%)


## Phase 2: Date Extraction Results

- **Successful Extractions:** 607 (60.7%)
- **No Dates Present:** 393 (39.3%)
- **Missed Dates:** 0 (0.0%)

## Phase 3: Report Type Extraction Results

- **Successful Extractions:** 162 (16.2%)
- **Failed Extractions:** 838 (83.8%)

### Most Common Report Types

- **Report:** 132 titles (13.2%)
- **Analysis:** 13 titles (1.3%)
- **Trends:** 8 titles (0.8%)
- **Outlook:** 4 titles (0.4%)
- **Forecast:** 3 titles (0.3%)
- **Insights:** 2 titles (0.2%)


## Special Market Cases

- **Total Special Cases:** 1 (0.1%)

These are cases where 'Market' remains part of the topic rather than being extracted as a report type.

## Recommendations for Next Iteration

1. **Report Type Pattern Enhancement:** Review failed extractions to identify missing patterns
2. **Special Case Validation:** Verify special market case handling is working correctly
3. **Confidence Scoring:** Analyze low-confidence extractions for pattern improvements
4. **Edge Case Handling:** Review complex titles with multiple patterns

