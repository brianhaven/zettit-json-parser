# Issue #31: Acronym Loss in Report Type Extraction - RTLS Case Study

## Executive Summary

**Issue:** Acronyms embedded within report type descriptions are being lost during extraction, causing incomplete topic extraction. The primary example is "RTLS" acronym being removed from "Real-Time Locating Systems" topics.

**Impact:** ~5-10% of titles with acronyms in report type sections lose important context/searchability.

**Root Cause:** Script 03 v4's dictionary-based removal identifies "RTLS" as part of the report type keywords and removes it completely without checking if it's an acronym for the main topic.

**Proposed Solution:** Implement acronym detection and preservation logic that identifies topic-related acronyms before report type removal.

## Problem Deep Dive

### Current Behavior

**Example Title:** `Real-Time Locating Systems Market Size, RTLS Industry Report, 2025`

**Current Pipeline Flow:**
1. **Script 01 (Market Classification):** → `standard` classification
2. **Script 02 (Date Extraction):** → Extracts `2025`, remaining: `Real-Time Locating Systems Market Size, RTLS Industry Report`
3. **Script 03 (Report Type):**
   - Detects keywords: `["Market", "Size", "RTLS", "Industry", "Report"]`
   - Reconstructs: `Market Size Industry Report`
   - Removes ALL detected keywords including `RTLS`
   - Remaining: `Real-Time Locating Systems`
4. **Script 04 (Geographic):** → No regions detected
5. **Script 05 (Topic):** → Final topic: `Real-Time Locating Systems` ❌ (RTLS lost)

### Root Cause Analysis

The issue occurs in **Script 03 v4** at line 759-803 in the `_clean_remaining_title()` method:

```python
def _clean_remaining_title(self, original_title: str, extracted_type: Optional[str], dictionary_result: DictionaryKeywordResult) -> str:
    # Line 782-785: Removes ALL keywords found after "Market"
    if pos_info['start'] >= market_pos or abs(pos_info['start'] - market_pos) < 50:
        if keyword in extracted_type:
            report_positions.append((pos_info['start'], pos_info['end']))
```

**Key Problems:**
1. **No Acronym Detection:** System doesn't recognize "RTLS" as an acronym for "Real-Time Locating Systems"
2. **Over-aggressive Removal:** All keywords detected in report type area are removed
3. **No Context Analysis:** Doesn't check if removed words relate to the main topic

### Impact Assessment

**Frequency:** Based on test data analysis:
- Affects ~5-10% of titles (those with acronyms in report sections)
- Common patterns: "AI Technology Report", "IoT Industry Analysis", "API Market Study"

**Business Impact:**
- **Search Functionality:** Users searching for "RTLS" won't find "Real-Time Locating Systems" results
- **Data Quality:** Loss of important context that links acronyms to full terms
- **User Experience:** Reduced accuracy in topic identification

## Solution Design

### Proposed Solution: Acronym Detection & Preservation

**Approach:** Implement a three-phase acronym handling system in Script 03 v4:

#### Phase 1: Acronym Detection (Pre-Removal)
```python
def _detect_acronyms(self, title: str) -> Dict[str, str]:
    """
    Detect potential acronyms and their expanded forms.
    Returns: {"RTLS": "Real-Time Locating Systems", ...}
    """
    acronyms = {}

    # Pattern 1: Parenthetical acronyms - "Real-Time Locating Systems (RTLS)"
    pattern1 = r'([A-Za-z\s\-]+)\s*\(([A-Z]{2,})\)'

    # Pattern 2: Comma-separated - "Real-Time Locating Systems, RTLS"
    pattern2 = r'([A-Za-z\s\-]+),\s*([A-Z]{2,})\b'

    # Pattern 3: Reverse order - "RTLS Real-Time Locating Systems"
    pattern3 = r'\b([A-Z]{2,})\s+([A-Za-z\s\-]+?)(?=\s+Market|\s+Industry|\s+Report|,|$)'

    # Check if acronym letters match expanded form
    # Example: RTLS -> Real-Time Locating Systems
    return acronyms
```

#### Phase 2: Acronym Preservation During Removal
```python
def _clean_remaining_title_with_acronym_preservation(self, original_title: str, extracted_type: str,
                                                    dictionary_result: DictionaryKeywordResult) -> str:
    # Detect acronyms first
    acronyms = self._detect_acronyms(original_title)

    # Perform standard removal
    remaining = self._clean_remaining_title(original_title, extracted_type, dictionary_result)

    # Check if any detected acronyms were removed
    for acronym, expanded in acronyms.items():
        if acronym not in remaining and expanded in remaining:
            # Re-append the acronym to its expanded form
            remaining = f"{expanded} ({acronym})"

    return remaining
```

#### Phase 3: Post-Processing Validation
```python
def _validate_acronym_preservation(self, original: str, final_topic: str) -> str:
    """
    Final check to ensure important acronyms weren't lost.
    """
    # If original had an acronym that matches the topic, preserve it
    # This catches edge cases missed by earlier phases
    return final_topic
```

### Alternative Solutions Considered

#### Option 2: Pattern Library Enhancement
- **Approach:** Add acronym patterns to MongoDB pattern_libraries
- **Pros:** Database-driven, no code changes to core logic
- **Cons:** Requires pattern library updates for each acronym

#### Option 3: Topic-First Processing
- **Approach:** Extract topic before report type
- **Pros:** Natural preservation of topic-related content
- **Cons:** Major pipeline architecture change, high risk

## Implementation Plan

### Step 1: Add Acronym Detection (Low Risk)
**Location:** Script 03 v4, new method after line 237
**Changes:**
- Add `_detect_acronyms()` method
- Add `acronym_mappings` to DictionaryKeywordResult dataclass
- No changes to existing logic

### Step 2: Integrate with Cleaning Logic (Medium Risk)
**Location:** Script 03 v4, modify `_clean_remaining_title()` at line 759
**Changes:**
- Call acronym detection before removal
- Check removed content for acronyms
- Preserve topic-related acronyms

### Step 3: Add Test Cases
**Test Scenarios:**
```python
test_cases = [
    # Standard acronym cases
    ("Real-Time Locating Systems Market Size, RTLS Industry Report, 2025",
     "Real-Time Locating Systems (RTLS)"),

    # Multiple acronyms
    ("Artificial Intelligence & Machine Learning Market, AI/ML Report, 2030",
     "Artificial Intelligence (AI) & Machine Learning (ML)"),

    # Reverse order
    ("IoT Internet of Things Market Analysis, 2025",
     "Internet of Things (IoT)"),
]
```

### Step 4: Validation
- Run on 50-document test set
- Verify no regressions in existing functionality
- Check acronym preservation rate

## Risk Assessment

### Risks
1. **False Positives:** May incorrectly identify non-acronyms (e.g., "USA" as acronym for "United States of America")
2. **Performance Impact:** Additional regex processing per title
3. **Complexity:** Adds logic to already complex extraction

### Mitigations
1. **Conservative Matching:** Only preserve acronyms with clear topic correlation
2. **Caching:** Cache acronym patterns for performance
3. **Feature Flag:** Add enable/disable flag for gradual rollout

## Success Metrics

**Target Metrics:**
- **Acronym Preservation Rate:** >95% of topic-related acronyms preserved
- **False Positive Rate:** <2% incorrect acronym associations
- **Performance Impact:** <5ms additional processing time per title
- **No Regressions:** 100% of existing tests still pass

## Recommendation

**Recommended Approach:** Implement Phase 1 solution (Acronym Detection & Preservation)

**Rationale:**
- **Minimal Risk:** Additive changes, doesn't modify core logic
- **High Value:** Resolves the issue for majority of cases
- **Simple Implementation:** ~100 lines of code
- **Testable:** Easy to validate with clear test cases

**Timeline:**
- Implementation: 2-3 hours
- Testing: 1-2 hours
- Validation: 1 hour
- Total: ~6 hours

## Code Reference Points

**Files to Modify:**
- `/experiments/03_report_type_extractor_v4.py` (Primary changes)
- `/experiments/tests/test_03_acronym_preservation.py` (New test file)

**Key Methods:**
- `_clean_remaining_title()` - Line 759-803
- `DictionaryKeywordResult` dataclass - Line 58-73
- `extract()` method - Line 687-757

## Next Steps

1. Review and approve solution approach
2. Implement acronym detection logic
3. Add test cases
4. Run validation on test dataset
5. Deploy with monitoring