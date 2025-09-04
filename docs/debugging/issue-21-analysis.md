# Git Issue #21 Analysis - Missing Keywords in Report Type Extraction

**Issue Date:** 2025-01-04  
**Branch:** fix/issue-21-missing-keywords  
**Status:** In Progress

## Issue Summary

Script 03 v3 Market-Aware Workflow is missing critical keywords in report type extraction, affecting 36% of test cases (9/25 titles). The database contains all required patterns, indicating algorithm logic bugs rather than missing data.

## Root Cause Analysis

### Database Status ✅ CONFIRMED CORRECT
All critical keywords ARE present in the database:

```
Primary Keywords (8 total):
1: Market (freq: 892)
2: Size (freq: 523) 
3: Report (freq: 505) ✓ PRESENT
4: Share (freq: 404)
5: Industry (freq: 294) ✓ PRESENT
6: Trends (freq: 234)
7: Analysis (freq: 232)
8: Growth (freq: 199)

Secondary Keywords: 39 total including misspellings
- 'repot' (freq: 1) ✓ PRESENT
- 'industy' (freq: 1) ✓ PRESENT  
- 'indsutry' (freq: 1) ✓ PRESENT

Separators: 14 total including
- '&' (priority 3) ✓ PRESENT
- 'and' (priority 5) ✓ PRESENT
```

### Actual Root Cause: Algorithm Logic Bugs

1. **Keyword Detection Issues**: Dictionary lookup not finding all keywords properly
2. **Boundary Detection Problems**: Not identifying complete keyword sequences  
3. **Phrase Extraction Incomplete**: Missing text between first/last keywords
4. **Separator Stripping**: Removing "&" and "and" during reconstruction
5. **V2 Fallback Masking**: Hybrid approach hiding dictionary failures

## Key Implementation Issues Identified

### 1. Market-Aware Workflow Problems
The 7-step market-aware workflow has bugs in:
- **Step 2**: Market boundary detection using only "Market" 
- **Step 3-4**: Keyword sequence detection and phrase extraction
- **Step 5**: Report type reconstruction missing separators
- **Step 7**: V2 fallback providing "acceptable" but incomplete results

### 2. Architecture Complexity
Current dual approach (dictionary + V2 fallback) masks issues:
- Dictionary failures fall back to V2 patterns
- Lower confidence scores (0.3-0.95) indicate fallback usage  
- Pure dictionary approach not properly debugged

## Solution Strategy

### Phase 1: Remove V2 Fallback ✅ REQUIRED
According to issue comments, **V2 fallback must be completely removed**:
- Force database dictionary-only processing
- Eliminate 921 V2 regex patterns from workflow
- Remove dual confidence scoring paths
- Expose exact algorithm failures for debugging

### Phase 2: Fix Dictionary Algorithm
Focus on core dictionary detection issues:
1. **Database Connection Testing**: Verify MongoDB queries work correctly
2. **Keyword Detection Logic**: Fix boundary detection algorithm
3. **Phrase Extraction Logic**: Capture complete text between keywords  
4. **Separator Preservation**: Ensure "&", "and", "," are maintained
5. **Sequence Processing**: Proper ordering and reconstruction

### Phase 3: Preserve Misspelled Keywords Strategy
**Intentional misspellings should be RETAINED** per issue comments:
- Real-world data contains OCR errors and typos
- System should handle imperfect input gracefully  
- All 4 misspellings already in database and should work with fixed algorithm

## Failing Test Cases Analysis

| Issue Type | Count | Examples |
|------------|-------|----------|
| Missing "Report" keyword | 1 | "Material Handling Equipment Market In... **Report**" |
| Missing "&" separator | 1 | "Trends **&** Analysis" → "Trends Analysis" |  
| Missing "Industry" keyword | 2 | "Oil & Gas **Industry**", "Carbon Fiber **Industry** Analysis" |
| Missing "and" separator | 1 | "Share **and** Size" → "Share Size" |
| Missing misspellings | 2 | "Healthcare **Industy**", "Cosmetics **Repot**" |
| Truncated pipeline text | 2 | "Physical Therapy**, Examination, and Operating**" |

**Expected Success Rate After Fix**: 100% (25/25 titles)

## Implementation Plan

### Immediate Actions
1. ✅ Create branch `fix/issue-21-missing-keywords`
2. ✅ Document analysis in `/docs/debugging/`
3. 🔄 Remove V2 fallback functionality from Script 03 v3
4. 🔄 Fix dictionary keyword detection algorithm
5. 🔄 Test with provided 25-title sample
6. 🔄 Validate misspelled keyword detection works

### Testing Requirements
Must pass all 25 provided test titles with exact output matching:
- Extracted Report Type must match expected results
- Pipeline Forward Text must match expected results  
- No truncation or missing keywords allowed

## Files to Modify

### Primary Script
- `experiments/03_report_type_extractor_v3.py` - Remove V2 fallback, fix algorithm

### Test Scripts  
- Create new test script in `experiments/tests/` for 25-title validation
- Output results to timestamped `outputs/` directory

### Documentation
- `docs/debugging/issue-21-analysis.md` - This analysis document  
- `docs/debugging/issue-21-solution.md` - Implementation details and results