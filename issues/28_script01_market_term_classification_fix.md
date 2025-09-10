# Issue #28: Script 01 Market Term Classification 'Market in' Context Integration

## Executive Summary

Script 01 correctly identifies "market_in" classification but the pipeline fails to properly preserve and integrate geographic context during processing, resulting in incomplete topic extraction. The issue occurs when geographic entities that are part of the market term context (e.g., "Singapore" in "Market in Singapore") are incorrectly removed by Script 04, leaving an incomplete topic like "Retail in" instead of "Retail in Singapore" or "Retail".

## Problem Analysis

### Test Case
**Original Title:** "Retail Market in Singapore - Size, Outlook & Statistics"

### Current Processing Flow

1. **Script 01 (Market Classification):** ✅ Correctly identifies as `market_in`
   - Input: "Retail Market in Singapore - Size, Outlook & Statistics"
   - Output: market_type = "market_in", confidence = 0.95
   - Notes: "Requires context integration processing for market in"

2. **Script 02 (Date Extraction):** ✅ No dates to extract
   - Input: Same title
   - Output: No dates found, title unchanged

3. **Script 03v4 (Report Type Extraction):** ✅ Correctly extracts report type
   - Input: Title + market_type = "market_in"
   - Market term extracted: "Market"
   - Report type: "Market Size & Outlook & Statistics"
   - Pipeline forward text: "Retail in Singapore"

4. **Script 04 (Geographic Detection):** ❌ **INCORRECTLY removes "Singapore"**
   - Input: "Retail in Singapore"
   - Singapore detected and removed as geographic entity
   - Output: "Retail in" (incomplete)

5. **Final Topic:** ❌ "Retail in" (missing geographic context)

### Expected Behavior
- **Option 1:** Topic = "Retail in Singapore" (preserve full context)
- **Option 2:** Topic = "Retail" (remove "in" when geographic context is removed)

## Root Cause Analysis

### Primary Issue: Context Preservation Failure

The root cause is a **coordination failure** between Script 03v4 and Script 04:

1. **Script 03v4** correctly preserves "in Singapore" as part of the market context when processing "market_in" patterns
2. However, it doesn't mark or flag that "Singapore" is part of the market term context
3. **Script 04** treats all geographic entities uniformly and removes "Singapore" without knowing it's part of the market context
4. This leaves the orphaned "in" preposition, creating the incomplete "Retail in" topic

### Secondary Issues

1. **Missing Context Flag:** No mechanism to pass context preservation requirements between pipeline stages
2. **Preposition Handling:** When geographic context is removed, associated prepositions ("in", "for", "by") should also be removed
3. **Market Term Type Not Utilized:** Script 04 doesn't receive or use the market_term_type classification from Script 01

## Technical Investigation

### Database Analysis

```python
# MongoDB Pattern Analysis Results:
- Market term patterns: 3 ("Market for", "Market in", "Market by")
- "Market in" pattern: '\bmarket\s+in\b' (active: True)
- Singapore in geographic patterns: Yes (active: True)
- Total geographic patterns: 923
```

### Pipeline Test Results (250 documents)

```python
# Distribution:
- standard: 248 titles (99.2%)
- market_for: 1 title (0.4%) 
- market_in: 1 title (0.4%)

# Market IN example (Test #188):
Title: "Retail Market in Singapore - Size, Outlook & Statistics"
Topic: "Retail in" ❌ (Singapore incorrectly removed)
Report: "Market Size & Outlook & Statistics" ✅

# Market FOR example (Test #146):
Title: "Oman Industrial Salts Market For Oil & Gas Industry Report, 2020-2027"
Topic: "Industrial Salts for Oil Gas" ✅ (context preserved)
Report: "Market Industry Report" ✅
```

### Code Analysis

**Script 01 (lines 329-330):**
```python
elif market_type in ["market_in", "market_by"]:
    notes = f"Requires context integration processing for {term_name.lower()}"
```
- Correctly identifies need for context integration
- But no mechanism to enforce this downstream

**Script 03v4 (lines 547-554):**
```python
if market_context:
    connector_word = market_phrase.split()[-1].lower()  # "for", "in", "by"
    pipeline_forward = f"{prefix_part} {connector_word} {market_context}"
else:
    pipeline_forward = market_context
```
- Correctly preserves "in Singapore" in pipeline_forward
- But no flag to indicate Singapore is part of market context

**Script 04 (lines 210-219):**
```python
for match, matched_text in reversed(pattern_matches):
    resolved_region = self.resolve_to_primary_term(matched_text, pattern)
    if resolved_region not in extracted_regions:
        extracted_regions.append(resolved_region)
    # Remove from working text with context cleanup
    working_text = self.remove_match_with_cleanup(working_text, match)
```
- Unconditionally removes all geographic entities
- No awareness of market term context

## Solution Design

### Approach 1: Context Preservation Flag (Recommended)

**Enhance pipeline to pass context preservation requirements:**

1. **Script 01 Enhancement:**
   - Add `context_preservation_needed` flag to ClassificationResult
   - Set to True for market_in, market_by patterns

2. **Script 03v4 Enhancement:**
   - Extract geographic entities from market context
   - Add `preserved_context_entities` list to result
   - Example: ["Singapore"] for "Market in Singapore"

3. **Script 04 Enhancement:**
   - Accept `preserved_entities` parameter
   - Skip removal of entities in preserved list
   - OR remove entity but also remove associated preposition

### Approach 2: Preposition Cleanup (Simpler)

**Clean up orphaned prepositions after geographic removal:**

1. **Script 04 Enhancement:**
   - After removing geographic entities, check for orphaned prepositions
   - Pattern: `\b(in|for|by|of|at)\s*$` at end of text
   - Remove orphaned prepositions

2. **Benefits:**
   - Simpler implementation
   - No cross-script coordination needed
   - Handles all cases uniformly

### Approach 3: Market Context Awareness (Most Comprehensive)

**Make Script 04 market-term-aware:**

1. **Script 04 Enhancement:**
   - Accept `market_term_type` parameter
   - For market_in/market_by: 
     - Either preserve first geographic entity after preposition
     - OR remove both entity and preposition together

2. **Implementation:**
   ```python
   def extract_geographic_entities(self, title: str, market_term_type: str = "standard"):
       # Special handling for market_in patterns
       if market_term_type == "market_in" and " in " in title.lower():
           # Handle "Retail in Singapore" specially
   ```

## Implementation Plan

### Phase 1: Quick Fix (Approach 2)
**Timeline: 1 hour**

1. Modify Script 04 to clean orphaned prepositions:
   ```python
   # After geographic removal
   working_text = re.sub(r'\b(in|for|by|of|at)\s*$', '', working_text).strip()
   ```

2. Test with known cases:
   - "Retail Market in Singapore" → "Retail" ✅
   - "Market for Oil & Gas" → "Oil & Gas" ✅

### Phase 2: Proper Context Integration (Approach 1)
**Timeline: 2-3 hours**

1. **Update data structures:**
   - Add context fields to result classes
   - Maintain backward compatibility

2. **Implement context passing:**
   - Script 01 → Script 03v4: market_term_type
   - Script 03v4 → Script 04: preserved_entities
   - Script 04: Honor preserved entities

3. **Comprehensive testing:**
   - All market term patterns
   - Edge cases with multiple geographic entities

### Phase 3: Full Market Awareness (Future)
**Timeline: 4-6 hours**

1. Redesign pipeline for full market term awareness
2. Each script receives and uses market classification
3. Context-specific processing rules

## Testing Strategy

### Test Cases

1. **Market in patterns:**
   ```
   "Retail Market in Singapore - Size, Outlook & Statistics"
   Expected: Topic = "Retail" or "Retail in Singapore"
   
   "Technology Market in Asia Pacific, 2025-2030"
   Expected: Topic = "Technology" or "Technology in Asia Pacific"
   ```

2. **Market for patterns:**
   ```
   "Global Market for Advanced Materials in Aerospace, 2030"
   Expected: Topic = "Advanced Materials for Aerospace" (preserve context)
   ```

3. **Standard patterns:**
   ```
   "APAC Personal Protective Equipment Market Analysis"
   Expected: Topic = "Personal Protective Equipment" (current behavior)
   ```

### Validation Metrics

- Market_in patterns: 100% should have complete topics (no orphaned prepositions)
- Market_for patterns: Context should be preserved
- Standard patterns: No regression in current behavior
- Overall pipeline success rate: Maintain or improve current 90%

## Risk Assessment

### Low Risk (Approach 2)
- Simple regex cleanup
- No structural changes
- Easy to test and rollback

### Medium Risk (Approach 1)
- Requires coordination between scripts
- Data structure changes
- More complex testing needed

### Considerations
- Only ~0.8% of titles have market term patterns (2 out of 250)
- But these represent important use cases
- Solution should be robust for future pattern additions

## Success Criteria

1. **Immediate:** No orphaned prepositions in final topics
2. **Short-term:** Proper context handling for all market term patterns
3. **Long-term:** Full market-aware pipeline with context preservation

## Recommended Solution

**Implement Approach 2 (Preposition Cleanup) immediately** as it:
- Solves the immediate issue
- Requires minimal code changes
- Has low risk of breaking existing functionality
- Can be deployed quickly

**Plan for Approach 1 (Context Preservation)** as a follow-up to:
- Properly handle complex market term patterns
- Provide better control over context preservation
- Enable more sophisticated processing rules

## Code Modifications

### Script 04 Enhancement (Immediate Fix)

```python
def cleanup_remaining_text(self, text: str) -> str:
    """Clean up remaining text after extraction."""
    if not text:
        return ""
    
    # Existing cleanup
    text = re.sub(r'\s+', ' ', text)
    text = re.sub(r'^[-–—\s,;&|]+|[-–—\s,;&|]+$', '', text)
    
    # NEW: Remove orphaned prepositions at end
    # Handles cases like "Retail in" → "Retail"
    text = re.sub(r'\s+(in|for|by|of|at|to|with|from)\s*$', '', text, flags=re.IGNORECASE)
    
    # NEW: Remove orphaned prepositions at start
    # Handles cases like "in Technology" → "Technology"
    text = re.sub(r'^(in|for|by|of|at|to|with|from)\s+', '', text, flags=re.IGNORECASE)
    
    return text.strip()
```

## Conclusion

Issue #28 represents a coordination failure between pipeline stages where market term context is not properly preserved through geographic entity extraction. The recommended immediate fix is to clean up orphaned prepositions in Script 04, with a planned enhancement to implement proper context preservation flags for more sophisticated handling of market term patterns.

## UPDATE: Approach 2 Recommended as Immediate Solution (CHOSEN APPROACH)

After comprehensive analysis, **Approach 2 (Preposition Cleanup)** has been identified as the optimal immediate solution. See GitHub Issue #28 comment: https://github.com/brianhaven/zettit-json-parser/issues/28#issuecomment-3273467944

**Chosen Implementation Approach:**
1. **Immediate Fix**: Modify `cleanup_remaining_text()` method in Script 04 to remove orphaned prepositions  
2. **Target Patterns**: `\s+(in|for|by|of|at|to|with|from)\s*$` at end and `^(in|for|by|of|at|to|with|from)\s+` at start
3. **Expected Results**: "Retail Market in Singapore" → Topic: "Retail" (clean, no artifacts)
4. **Timeline**: 30 minutes implementation, minimal risk, immediate impact

**Rationale**: This approach directly addresses the root cause (orphaned prepositions) with a simple, targeted fix that handles all orphaned preposition cases from any source, not just market_in patterns. Maintains consistency with the simple solution philosophy used for Issues #26, #27, and #29.