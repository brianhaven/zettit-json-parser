# Phase 3 Pipeline Test Summary Report

**Analysis Date (PDT):** 2025-08-25 12:34:41 PDT  
**Analysis Date (UTC):** 2025-08-25 19:34:41 UTC

## Executive Summary

- **Total Titles Processed:** 1,000
- **Market Term Classification Rate:** 100.0%
- **Date Extraction Success:** 61.2% (612/1,000)
- **Titles with No Dates:** 38.8% (388/1,000)
- **Report Type Extraction Success:** 99.5% (995/1,000)
- **Special Market Cases Found:** 0.1% (1/1,000)

## Phase 1: Market Term Classification Results

- **standard:** 999 titles (99.9%)
- **market_in:** 1 titles (0.1%)


## Phase 2: Date Extraction Results

- **Successful Extractions:** 612 (61.2%)
- **No Dates Present:** 388 (38.8%)
- **Missed Dates:** 0 (0.0%)

## Phase 3: Report Type Extraction Results

- **Successful Extractions:** 995 (99.5%)
- **Failed Extractions:** 5 (0.5%)

### Most Common Report Types

- **Market:** 398 titles (39.8%)
- **Report:** 279 titles (27.9%)
- **Market Size & Share Report:** 59 titles (5.9%)
- **Market Size & Share, Industry Report:** 27 titles (2.7%)
- **Market Size, Share, Industry Report:** 17 titles (1.7%)
- **Market Size, Share Report:** 15 titles (1.5%)
- **Market Size, Share,:** 13 titles (1.3%)
- **Market Size, Share & Trends Report:** 13 titles (1.3%)
- **Market Size, Share And Growth Report:** 11 titles (1.1%)
- **Market Size And Share, Industry Report:** 10 titles (1.0%)


## Special Market Cases

- **Total Special Cases:** 1 (0.1%)

These are cases where 'Market' remains part of the topic rather than being extracted as a report type.

## Recommendations for Next Iteration

1. **Report Type Pattern Enhancement:** Review failed extractions to identify missing patterns
2. **Special Case Validation:** Verify special market case handling is working correctly
3. **Confidence Scoring:** Analyze low-confidence extractions for pattern improvements
4. **Edge Case Handling:** Review complex titles with multiple patterns

