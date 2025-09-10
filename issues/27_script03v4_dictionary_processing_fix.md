# Issue #27: Script 03 v4 Dictionary Processing Fix - Content Loss Resolution

## Executive Summary

Script 03 v4 is experiencing critical content loss when dictionary keywords appear in topic content before the "Market" keyword. This affects approximately 0.8-2% of titles but represents a complete failure when it occurs. The root cause is the algorithm's approach of removing the entire text span from the first detected keyword to the last detected keyword, regardless of whether those keywords are part of the report type or the topic.

## Problem Analysis

### Current Behavior

The script uses a dictionary-based approach that:
1. Scans the entire title for ALL dictionary keywords
2. Records positions of all found keywords
3. Reconstructs report type from detected keywords after "Market"
4. **CRITICAL FLAW:** Removes the entire span from first keyword position to last keyword position

### Failing Examples

#### Example 1: "Data Monetization Market Outlook, Trends, Analysis"
- **Keywords Detected:** Data (0-4), Market (18-24), Outlook (25-32), Trends (34-40), Analysis (42-50)
- **Report Type Built:** "Market Outlook Trends Analysis" (correct)
- **Span Removed:** [0:50] - THE ENTIRE TITLE
- **Result:** Empty topic (FAILURE)

#### Example 2: "Data Brokers Market"
- **Keywords Detected:** Data (0-4), Market (13-19)
- **Report Type Built:** "Market" (incorrect - missing "Data")
- **Span Removed:** [0:19] - THE ENTIRE TITLE
- **Result:** Empty topic (FAILURE)

#### Example 3: "Oil & Gas Data Management Market"
- **Keywords Detected:** Data (10-14), Market (26-32)
- **Report Type Built:** "Market" (incorrect - missing "Data Management")
- **Span Removed:** [10:32] - "Data Management Market"
- **Result:** Topic = "Oil & Gas" (partial loss - missing "Management")

## Root Cause Analysis

### Issue 1: Over-Inclusive Keyword Detection
The script detects "Data" as a report type keyword because it exists in the secondary keywords dictionary. However, "Data" can appear in three contexts:
1. **As part of topic:** "Data Monetization" (should NOT be removed)
2. **As part of report type:** "Data Management Market" (should be included in report type)
3. **Standalone:** "Data Market" (ambiguous)

### Issue 2: Span-Based Removal Algorithm
The current `_clean_remaining_title` method removes the entire span from the first detected keyword to the last detected keyword:
```python
# Current flawed logic
first_start = positions[0][0]  # First keyword start
last_end = positions[-1][1]     # Last keyword end
remaining = original_title[:first_start] + original_title[last_end:]
```

This approach assumes ALL text between keywords is part of the report type, which is incorrect when keywords appear in the topic portion.

### Issue 3: Reconstruction Logic Limitations
The reconstruction method only includes keywords that appear after "Market" in the sequence, but:
- It doesn't preserve non-dictionary words between keywords
- It doesn't handle pre-Market keywords that might be part of the report type
- It loses context about which keywords are actually part of the report type pattern

## Proposed Solution: Reverse Dictionary Processing

### Algorithm Overview

Instead of scanning the entire title and removing a span, we should:
1. **Find "Market" keyword first** as the primary anchor point
2. **Scan backwards from "Market"** to identify report type boundaries
3. **Scan forwards from "Market"** to complete the report type
4. **Only remove the identified report type phrase**, preserving everything else

### Detailed Implementation

#### Phase 1: Market-Anchored Boundary Detection
```python
def find_report_type_boundaries(self, title: str, keyword_positions: Dict) -> Tuple[int, int]:
    """Find the actual boundaries of the report type phrase."""
    
    # Find Market position (primary anchor)
    market_pos = keyword_positions.get('Market')
    if not market_pos:
        return None, None
    
    market_start = market_pos['start']
    market_end = market_pos['end']
    
    # Scan backwards from Market to find report type start
    report_start = market_start
    for keyword, pos in keyword_positions.items():
        if keyword == 'Market':
            continue
        
        # Check if keyword is immediately before current report_start
        if pos['end'] <= market_start:
            # Check if there's only whitespace/punctuation between
            between = title[pos['end']:report_start].strip()
            if not between or between in [',', '&', 'and', '-']:
                # This keyword is part of the report type
                report_start = pos['start']
    
    # Scan forwards from Market to find report type end
    report_end = market_end
    for keyword, pos in keyword_positions.items():
        if keyword == 'Market':
            continue
            
        # Check if keyword is immediately after current report_end
        if pos['start'] >= market_end:
            # Check if there's only whitespace/punctuation between
            between = title[report_end:pos['start']].strip()
            if not between or between in [',', '&', 'and', '-']:
                # This keyword is part of the report type
                report_end = pos['end']
    
    return report_start, report_end
```

#### Phase 2: Context-Aware Keyword Classification
```python
def classify_keywords_by_context(self, title: str, keyword_positions: Dict) -> Dict:
    """Classify keywords as report_type or topic based on context."""
    
    classifications = {
        'report_type': [],
        'topic': [],
        'ambiguous': []
    }
    
    # Find report type boundaries
    report_start, report_end = self.find_report_type_boundaries(title, keyword_positions)
    
    for keyword, pos in keyword_positions.items():
        keyword_start = pos['start']
        keyword_end = pos['end']
        
        # Check if keyword is within report type boundaries
        if report_start <= keyword_start and keyword_end <= report_end:
            classifications['report_type'].append(keyword)
        elif keyword_end <= report_start or keyword_start >= report_end:
            # Keyword is outside report type boundaries
            classifications['topic'].append(keyword)
        else:
            # Keyword overlaps boundaries (shouldn't happen)
            classifications['ambiguous'].append(keyword)
    
    return classifications
```

#### Phase 3: Precise Removal and Reconstruction
```python
def extract_with_precise_removal(self, title: str, keyword_positions: Dict) -> Dict:
    """Extract report type with precise removal of only report type text."""
    
    # Find report type boundaries
    report_start, report_end = self.find_report_type_boundaries(title, keyword_positions)
    
    if report_start is None:
        return {'report_type': '', 'remaining': title}
    
    # Extract report type text
    report_type_text = title[report_start:report_end]
    
    # Build remaining title (topic)
    remaining = title[:report_start].strip() + ' ' + title[report_end:].strip()
    remaining = remaining.strip()
    
    # Clean up extra spaces and punctuation
    remaining = re.sub(r'\s+', ' ', remaining)
    remaining = re.sub(r'^[,\s&\-–—\|;:]+|[,\s&\-–—\|;:]+$', '', remaining)
    
    return {
        'report_type': report_type_text,
        'remaining': remaining
    }
```

### Alternative Solution: Keyword Exclusion List

A simpler interim solution could be to maintain an exclusion list for ambiguous keywords:

```python
# Keywords that should NOT be treated as report type keywords when they appear before "Market"
TOPIC_PRIORITY_KEYWORDS = ['Data', 'Digital', 'Software', 'Hardware', 'Service', 'Solution']

def should_exclude_keyword(self, keyword: str, position: int, market_position: int) -> bool:
    """Determine if a keyword should be excluded from report type extraction."""
    
    # If keyword appears before Market and is in the exclusion list
    if position < market_position and keyword in self.TOPIC_PRIORITY_KEYWORDS:
        return True
    
    return False
```

## Implementation Plan

### Step 1: Refactor Boundary Detection (Priority: CRITICAL)
- Implement `find_report_type_boundaries` method
- Use Market as primary anchor point
- Scan bidirectionally from Market position
- **Estimated effort:** 2-3 hours

### Step 2: Update Removal Logic (Priority: CRITICAL)
- Replace span-based removal with boundary-based removal
- Implement `extract_with_precise_removal` method
- Preserve non-report-type content
- **Estimated effort:** 1-2 hours

### Step 3: Enhance Keyword Classification (Priority: HIGH)
- Implement context-aware keyword classification
- Distinguish between report type and topic keywords
- Handle edge cases for ambiguous keywords
- **Estimated effort:** 2-3 hours

### Step 4: Add Safeguards (Priority: MEDIUM)
- Implement minimum topic length validation
- Add empty topic detection and recovery
- Log warnings for suspicious extractions
- **Estimated effort:** 1 hour

### Step 5: Testing and Validation (Priority: CRITICAL)
- Test with all failing examples
- Validate no regression on successful cases
- Run 250-document test suite
- **Estimated effort:** 2 hours

## Testing Strategy

### Test Cases for Validation

#### Critical Failure Cases (Must Pass)
1. "Data Monetization Market Outlook, Trends, Analysis"
   - Expected: Report="Market Outlook Trends Analysis", Topic="Data Monetization"

2. "Data Brokers Market"
   - Expected: Report="Market", Topic="Data Brokers"

3. "Oil & Gas Data Management Market"
   - Expected: Report="Data Management Market", Topic="Oil & Gas"

#### Edge Cases to Validate
4. "Market Data Analytics Platform Market Analysis"
   - Expected: Report="Market Analysis", Topic="Market Data Analytics Platform"

5. "Big Data Market Research Report"
   - Expected: Report="Market Research Report", Topic="Big Data"

6. "Data Center Infrastructure Management Market Size"
   - Expected: Report="Market Size", Topic="Data Center Infrastructure Management"

### Success Metrics
- **Zero empty topics** in 250-document test
- **Maintain 90% success rate** for report type extraction
- **100% preservation** of topic content (no partial loss)
- **Correct handling** of pre-Market dictionary terms

## Risk Assessment

### Potential Risks
1. **Performance Impact:** More complex boundary detection may increase processing time
   - Mitigation: Optimize with early termination conditions

2. **Over-correction:** May miss legitimate report type keywords
   - Mitigation: Comprehensive testing with diverse examples

3. **Edge Case Complexity:** Titles with multiple "Market" instances
   - Mitigation: Use first "Market" as primary anchor, validate with tests

## Rollback Plan

If the new algorithm causes unexpected issues:
1. Revert to original span-based removal
2. Implement keyword exclusion list as temporary fix
3. Mark problematic titles for manual review
4. Iterate on algorithm with expanded test cases

## Conclusion

The current span-based removal approach in Script 03 v4 causes critical content loss when dictionary keywords appear in topic content. The proposed reverse dictionary processing solution addresses this by:
1. Using "Market" as an anchor point for boundary detection
2. Scanning bidirectionally to identify true report type boundaries
3. Removing only the identified report type text
4. Preserving all topic content regardless of dictionary keyword presence

This solution will eliminate the 0.8-2% complete failure rate while maintaining the current 90% success rate for report type extraction.

## Implementation Priority

**IMMEDIATE ACTION REQUIRED**
- This issue blocks production deployment
- Affects data quality and pipeline reliability
- Simple fix with high impact

**Recommended approach:**
1. Implement boundary-based detection first (Phase 1)
2. Test with failing examples
3. Deploy if successful
4. Iterate with enhancements (Phases 2-4)

---

**Document Version:** 1.0
**Date:** 2025-01-10
**Author:** Claude Code AI (Analysis for Brian Haven, Zettit Inc.)
**Issue:** GitHub Issue #27 (includes merged Issue #30)