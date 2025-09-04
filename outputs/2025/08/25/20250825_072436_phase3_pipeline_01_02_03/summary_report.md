# Phase 3 Pipeline Test Summary Report

**Analysis Date (PDT):** 2025-08-25 00:24:36 PDT  
**Analysis Date (UTC):** 2025-08-25 07:24:36 UTC

## Executive Summary

- **Total Titles Processed:** 1,000
- **Market Term Classification Rate:** 100.0%
- **Date Extraction Success:** 62.4% (624/1,000)
- **Titles with No Dates:** 37.6% (376/1,000)
- **Report Type Extraction Success:** 99.7% (997/1,000)
- **Special Market Cases Found:** 0.2% (2/1,000)

## Phase 1: Market Term Classification Results

- **standard:** 999 titles (99.9%)
- **market_in:** 1 titles (0.1%)


## Phase 2: Date Extraction Results

- **Successful Extractions:** 624 (62.4%)
- **No Dates Present:** 376 (37.6%)
- **Missed Dates:** 0 (0.0%)

## Phase 3: Report Type Extraction Results

- **Successful Extractions:** 997 (99.7%)
- **Failed Extractions:** 3 (0.3%)

### Most Common Report Types

- **Market:** 382 titles (38.2%)
- **Report:** 311 titles (31.1%)
- **Market Size & Share Report:** 52 titles (5.2%)
- **Market Size & Share, Industry Report:** 31 titles (3.1%)
- **Market Size, Share Report:** 16 titles (1.6%)
- **Market Size, Share & Trends Report:** 16 titles (1.6%)
- **Market, Industry:** 10 titles (1.0%)
- **Market Size, Share, Industry Report:** 10 titles (1.0%)
- **Market Size, Share,:** 9 titles (0.9%)
- **Market Size And Share, Industry Report:** 9 titles (0.9%)


## Special Market Cases

- **Total Special Cases:** 2 (0.2%)

These are cases where 'Market' remains part of the topic rather than being extracted as a report type.

## Recommendations for Next Iteration

1. **Report Type Pattern Enhancement:** Review failed extractions to identify missing patterns
2. **Special Case Validation:** Verify special market case handling is working correctly
3. **Confidence Scoring:** Analyze low-confidence extractions for pattern improvements
4. **Edge Case Handling:** Review complex titles with multiple patterns

