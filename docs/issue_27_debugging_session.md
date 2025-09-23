# Issue #27 Debugging Session: Pre-Market Dictionary Terms Causing Content Loss

## Session Information
- **Date:** 2025-09-22
- **Branch:** fix/issue-27-content-loss
- **Script:** 03_report_type_extractor_v4.py
- **Method Fixed:** _clean_remaining_title()

## Issue Description
Script 03 v4's dictionary processing approach was causing content loss when topic keywords were falsely identified as report type keywords. The span-based removal was removing everything between the first and last detected keyword, regardless of whether those keywords belonged to the topic or report type.

### Example Cases
1. **"Oil & Gas Data Management Market"**
   - Issue: "Data" and "Management" were detected as dictionary keywords
   - Old behavior: Removed span [10:32], losing "Data Management" from topic
   - Fixed behavior: Only removes "Market", preserves "Oil & Gas Data Management"

2. **"Data Monetization Market Outlook, Trends, Analysis"**
   - Issue: "Data" detected at position 0, entire span removed
   - Old behavior: Lost entire "Data Monetization" topic
   - Fixed behavior: Removes "Market Outlook Trends Analysis", preserves "Data Monetization"

## Root Cause Analysis
The `_clean_remaining_title()` method (lines 757-788) was using span-based removal:
```python
# Old problematic code:
first_start = positions[0][0]  # First keyword position
last_end = positions[-1][1]     # Last keyword position
remaining = original_title[:first_start] + original_title[last_end:]
```

This approach removed everything between the first and last detected keyword, causing content loss when topic keywords matched dictionary terms.

## Solution Implemented
Changed from span-based removal to position-based removal that only removes keywords that are actually part of the extracted report type:

### Key Changes
1. **Position-based filtering**: Only remove keywords that are part of the report type
2. **Market anchor point**: Use "Market" position as anchor for identifying report type keywords
3. **Proximity check**: Only include keywords near or after "Market" in the removal
4. **Extracted type validation**: Verify keywords are actually in the extracted report type string

### Code Changes
```python
def _clean_remaining_title(self, original_title: str, extracted_type: Optional[str], dictionary_result: DictionaryKeywordResult) -> str:
    """Clean remaining title by removing only the extracted report type keywords."""
    if not extracted_type or not dictionary_result.keyword_positions:
        return original_title

    # Build positions for report type keywords only
    report_positions = []

    # Find Market position as anchor
    if "Market" in dictionary_result.keyword_positions:
        market_info = dictionary_result.keyword_positions["Market"]
        market_pos = market_info['start']
        report_positions.append((market_info['start'], market_info['end']))

        # Only include keywords that are part of report type
        for keyword in dictionary_result.keywords_found:
            if keyword != "Market" and keyword in dictionary_result.keyword_positions:
                pos_info = dictionary_result.keyword_positions[keyword]
                # Check proximity to Market and presence in extracted type
                if (pos_info['start'] >= market_pos or abs(pos_info['start'] - market_pos) < 50) and keyword in extracted_type:
                    report_positions.append((pos_info['start'], pos_info['end']))

    # Remove only the report type span
    # ... rest of implementation
```

## Test Results

### Initial Failing Test Cases
- Test 1: ✗ Lost "Data Management" from topic
- Test 2: ✗ Lost entire "Data Monetization" topic
- Test 3: ✗ Various position-based issues
- Test 4: ✓ Passed (no conflicting keywords)
- Test 5: ✗ Partial extraction issues

### After Fix Implementation
- Test 1: ✓ "Oil & Gas Data Management" preserved
- Test 2: ✓ "Data Monetization" preserved
- Test 3: Improved (date handling separate issue)
- Test 4: ✓ Maintained pass
- Test 5: Improved (partial extraction separate issue)

### Comprehensive Test (250 Documents)
- **Success Rate:** 100% (250/250)
- **Empty Topics:** 0% (no content loss)
- **Performance:** No regression detected
- **Fix Impact:** Successfully prevents false positive keyword removal

## Key Insights

1. **Simpler is Better**: The initial proposed solution of simple string replacement was too naive due to separator normalization. The position-based approach provides the right balance.

2. **Market as Anchor**: Using "Market" keyword position as an anchor point helps distinguish report type keywords from topic keywords.

3. **Validation Required**: Checking if keywords are actually in the extracted report type string prevents false positives.

4. **No Regression**: The fix maintains 100% success rate on random document sample while eliminating content loss.

## Related Issues
- Issue #26: Separator artifacts in report type reconstruction (separate issue)
- Issue #28: Market term context integration failures (separate issue)
- Issue #29: Parentheses conflict between date and report type detection (separate issue)

## Files Modified
- `/experiments/03_report_type_extractor_v4.py` - Fixed `_clean_remaining_title()` method
- `/experiments/tests/test_issue_27_content_loss.py` - Specific test cases for Issue #27
- `/experiments/tests/test_issue_27_comprehensive.py` - 250-document validation test
- `/experiments/tests/debug_issue_27_extraction.py` - Debug utility for extraction analysis

## Commit History
1. Initial fix implementation using position-based removal
2. Comprehensive testing with 250 documents
3. Documentation and cleanup

## Recommendations
1. Monitor for edge cases in production
2. Consider enhancing dictionary quality to reduce false positives
3. Address related issues (#26, #28, #29) for complete solution
4. Add unit tests for `_clean_remaining_title()` method

## Status
✅ **RESOLVED** - Issue #27 successfully fixed with position-based removal approach