# Phase 3 Pipeline Test Summary Report

**Analysis Date (PDT):** 2025-08-24 21:42:53 PDT  
**Analysis Date (UTC):** 2025-08-25 04:42:53 UTC

## Executive Summary

- **Total Titles Processed:** 1,000
- **Market Term Classification Rate:** 100.0%
- **Date Extraction Success:** 62.7% (627/1,000)
- **Titles with No Dates:** 37.3% (373/1,000)
- **Report Type Extraction Success:** 15.7% (157/1,000)
- **Special Market Cases Found:** 0.1% (1/1,000)

## Phase 1: Market Term Classification Results

- **standard:** 999 titles (99.9%)
- **market_for:** 1 titles (0.1%)


## Phase 2: Date Extraction Results

- **Successful Extractions:** 627 (62.7%)
- **No Dates Present:** 373 (37.3%)
- **Missed Dates:** 0 (0.0%)

## Phase 3: Report Type Extraction Results

- **Successful Extractions:** 157 (15.7%)
- **Failed Extractions:** 843 (84.3%)

### Most Common Report Types

- **Report:** 126 titles (12.6%)
- **Analysis:** 19 titles (1.9%)
- **Trends:** 4 titles (0.4%)
- **Outlook:** 4 titles (0.4%)
- **Insights:** 4 titles (0.4%)


## Special Market Cases

- **Total Special Cases:** 1 (0.1%)

These are cases where 'Market' remains part of the topic rather than being extracted as a report type.

## Recommendations for Next Iteration

1. **Report Type Pattern Enhancement:** Review failed extractions to identify missing patterns
2. **Special Case Validation:** Verify special market case handling is working correctly
3. **Confidence Scoring:** Analyze low-confidence extractions for pattern improvements
4. **Edge Case Handling:** Review complex titles with multiple patterns

