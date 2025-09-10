# Issue #19: Market Term Symbol Preservation Fix

## Executive Summary

**Issue:** Ampersand (&) symbols are lost during market term extraction in Script 03 v4, causing technical inaccuracy in terminology.

**Root Cause:** The regex pattern in `_extract_market_term_from_title` uses a negative lookahead that fails when commas appear before database keywords, causing extraction failures and subsequently symbol loss during fallback processing.

**Solution:** Modify the extraction pattern to handle comma-separated keywords correctly while preserving all special characters including ampersands.

## Problem Analysis

### Affected Examples

1. **"U.S. Windows & Patio Doors Market For Single Family Homes, Report, 2030"**
   - Expected: "Windows & Patio Doors for Single Family Homes"
   - Actual: "Windows Patio Doors for Single Family Homes" (missing "&")
   - Issue: Pattern fails to match due to ", Report" structure

2. **"Oman Industrial Salts Market For Oil & Gas Industry Report, 2020-2027"**
   - Expected: "Industrial Salts for Oil & Gas Industry"
   - Actual: "Industrial Salts for Oil Gas Industry" (missing "&")
   - Issue: Pattern matches but "Industry" keyword causes truncation

### Technical Root Cause

The current regex pattern in line 524 of `03_report_type_extractor_v4.py`:

```python
pattern = rf'\b{re.escape(market_phrase)}\s+([^,]*?)(?=\s+(?:{all_keywords_pattern})|$)'
```

This pattern has two critical issues:

1. **Lookahead Failure:** The `(?=\s+(?:{all_keywords_pattern}))` lookahead fails when a comma precedes a keyword (e.g., ", Report")
2. **Premature Termination:** The pattern stops capturing when it encounters a keyword, even if that keyword is part of the market context

### Symbol Preservation Analysis

Testing reveals that ampersands ARE preserved when the pattern matches correctly:
- The `[^,]*?` character class does NOT exclude ampersands
- The issue is pattern matching failure, not character class exclusion
- When extraction fails, the fallback processing loses symbols

## Detailed Solution

### 1. Enhanced Extraction Pattern

Replace the current pattern with a more robust version that handles comma-separated keywords:

```python
def _extract_market_term_from_title(self, title: str, market_type: str) -> Tuple[str, str, str]:
    """
    Extract market term from title with enhanced symbol preservation.
    
    Issue #19 Fix: Properly handle ampersands and comma-separated keywords.
    """
    # Convert market_type to phrase: "market_for" -> "Market for"
    market_phrase = market_type.replace('_', ' ').title()
    
    # ISSUE #19 FIX: Enhanced pattern that handles commas before keywords
    # First try: capture up to comma followed by keyword
    pattern1 = rf'\b{re.escape(market_phrase)}\s+(.+?)(?:,\s*(?:{all_keywords_pattern})|$)'
    
    # Second try: capture everything up to first standalone keyword
    # (keywords that appear after whitespace/punctuation, not within words)
    all_keywords_pattern = '|'.join([rf'\b{re.escape(kw)}\b' for kw in self.all_keywords if kw != 'Market'])
    pattern2 = rf'\b{re.escape(market_phrase)}\s+(.+?)(?=[\s,]+(?:{all_keywords_pattern})|$)'
    
    # Try first pattern (handles comma-keyword sequences)
    match = re.search(pattern1, title, re.IGNORECASE)
    
    if not match:
        # Try second pattern (handles direct keyword sequences)
        match = re.search(pattern2, title, re.IGNORECASE)
    
    if match:
        # Extract the market term phrase with symbols preserved
        full_market_term = match.group(0).strip()
        market_context = match.group(1).strip()
        
        # Validate that ampersands are preserved
        if '&' in title and '&' not in market_context and '&' in title[match.start():match.end()]:
            logger.warning(f"Ampersand lost during extraction: '{title}'")
        
        # Continue with existing extraction logic...
```

### 2. Symbol Validation Layer

Add validation to ensure symbols are preserved:

```python
def _validate_symbol_preservation(self, original: str, extracted: str, symbols: List[str] = None):
    """
    Validate that special symbols are preserved during extraction.
    
    Args:
        original: Original text
        extracted: Extracted/processed text
        symbols: List of symbols to check (default: ['&', '+', '-', '/'])
    
    Returns:
        bool: True if all symbols preserved, False otherwise
    """
    if symbols is None:
        symbols = ['&', '+', '-', '/', '|']
    
    for symbol in symbols:
        if symbol in original:
            # Check if symbol should be in extracted text
            if symbol not in extracted:
                logger.warning(f"Symbol '{symbol}' lost during extraction")
                return False
    
    return True
```

### 3. Enhanced Market Context Extraction

Improve the market context extraction to handle complex patterns:

```python
def _extract_market_context_with_symbols(self, title: str, market_phrase: str) -> Optional[str]:
    """
    Extract market context while preserving all special symbols.
    
    Issue #19 Fix: Enhanced extraction that preserves ampersands and other symbols.
    """
    # Pattern 1: Capture up to comma + keyword (most common)
    # Pattern 2: Capture up to end of string
    # Pattern 3: Capture up to standalone keyword
    
    patterns = [
        # Comma before keyword
        rf'\b{re.escape(market_phrase)}\s+(.+?)(?:,\s*\b(?:Report|Industry|Analysis|Study|Market)\b)',
        # End of relevant context (before date/year)
        rf'\b{re.escape(market_phrase)}\s+(.+?)(?:,\s*\d{4}|$)',
        # Direct keyword boundary
        rf'\b{re.escape(market_phrase)}\s+([^,]+?)(?:\s+\b(?:Report|Industry|Analysis|Study)\b|$)'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, title, re.IGNORECASE)
        if match:
            context = match.group(1).strip()
            # Validate symbol preservation
            if self._validate_symbol_preservation(title[match.start():match.end()], context):
                return context
    
    return None
```

### 4. Fallback Symbol Recovery

If symbols are lost during primary extraction, implement recovery:

```python
def _recover_lost_symbols(self, original: str, processed: str) -> str:
    """
    Recover lost symbols by comparing original and processed text.
    
    Issue #19 Fix: Restore ampersands and other symbols that were lost.
    """
    # Find segments that match between original and processed
    # but may have lost symbols
    
    # Common pattern: "A & B" becomes "A B"
    if ' & ' in original and ' & ' not in processed:
        # Try to restore based on word positions
        original_words = original.split()
        processed_words = processed.split()
        
        # Find where & should be inserted
        for i, word in enumerate(original_words):
            if word == '&' and i > 0 and i < len(original_words) - 1:
                # Found & between two words
                word_before = original_words[i-1]
                word_after = original_words[i+1]
                
                # Find these words in processed text
                processed_with_symbol = processed.replace(
                    f"{word_before} {word_after}",
                    f"{word_before} & {word_after}"
                )
                if processed_with_symbol != processed:
                    logger.info(f"Recovered lost ampersand in: '{processed}'")
                    return processed_with_symbol
    
    return processed
```

## Implementation Steps

### Phase 1: Pattern Enhancement (Priority: HIGH)
1. Modify `_extract_market_term_from_title` with enhanced patterns
2. Add proper handling for comma-separated keywords
3. Implement symbol preservation validation

### Phase 2: Validation Layer (Priority: MEDIUM)
1. Add `_validate_symbol_preservation` method
2. Integrate validation into extraction workflow
3. Log warnings when symbols are lost

### Phase 3: Recovery Mechanism (Priority: LOW)
1. Implement `_recover_lost_symbols` for fallback scenarios
2. Add recovery to pipeline forward text generation
3. Test with various symbol combinations

## Testing Strategy

### Test Cases

```python
test_cases = [
    # Ampersand preservation
    {
        "title": "U.S. Windows & Patio Doors Market For Single Family Homes, Report, 2030",
        "expected_market": "Market For Single Family Homes",
        "expected_pipeline": "U.S. Windows & Patio Doors for Single Family Homes",
        "symbols_preserved": ["&"]
    },
    {
        "title": "Oil & Gas Market In Energy & Power Sector Analysis",
        "expected_market": "Market In Energy & Power Sector",
        "expected_pipeline": "Oil & Gas in Energy & Power Sector",
        "symbols_preserved": ["&"]
    },
    # Other symbols
    {
        "title": "Food + Beverage Market For Hotels/Restaurants Industry Report",
        "expected_market": "Market For Hotels/Restaurants",
        "expected_pipeline": "Food + Beverage for Hotels/Restaurants",
        "symbols_preserved": ["+", "/"]
    }
]
```

### Validation Metrics
- Symbol preservation rate: % of titles where all symbols are preserved
- Extraction success rate: % of market term titles successfully extracted
- Pattern match coverage: % of titles matched by primary vs fallback patterns

## Expected Outcomes

### Immediate Benefits
1. **100% ampersand preservation** in market term extraction
2. **Improved technical accuracy** in terminology
3. **Better handling of comma-separated keywords**

### Long-term Benefits
1. **Extensible to other symbols** (+, -, /, |, etc.)
2. **Reduced need for manual correction**
3. **Higher confidence scores** for symbol-containing titles

## Integration with Other Issues

### Related Issues
- **Issue #26:** Separator artifacts - solution complements separator handling
- **Issue #27:** Content loss - pattern enhancement reduces content loss
- **Issue #28:** Market term context - improved extraction preserves context
- **Issue #29:** Parentheses conflicts - pattern robustness helps with complex punctuation

### Compatibility
- Solution is backward compatible with existing extraction logic
- No changes to public API or result structure
- Enhanced patterns work with current dictionary-based approach

## Success Criteria

### Quantitative Metrics
1. **Symbol Preservation Rate:** ≥ 99% for ampersands
2. **Extraction Success Rate:** ≥ 95% for market term titles
3. **No Regression:** Maintain current 90% overall success rate

### Qualitative Metrics
1. Correct technical terminology in extracted topics
2. Proper industry term preservation (e.g., "Oil & Gas", "R&D")
3. Clear logging of symbol preservation status

## Risk Assessment

### Low Risk
- Pattern changes are isolated to market term extraction
- Validation layer is non-intrusive (logging only)
- Recovery mechanism is optional fallback

### Mitigation
- Extensive testing with production data
- Gradual rollout with monitoring
- Fallback to original pattern if new patterns fail

## Conclusion

The ampersand preservation issue stems from regex pattern limitations rather than intentional symbol removal. The proposed solution enhances pattern matching to handle comma-separated keywords while preserving all special characters. This fix improves technical accuracy without compromising the existing dictionary-based architecture.

## UPDATE: Simple Pattern Enhancement Recommended (CHOSEN APPROACH)

After comprehensive analysis, a **simple single-line pattern fix** has been identified as the optimal solution. See GitHub Issue #19 comment: https://github.com/brianhaven/zettit-json-parser/issues/19#issuecomment-3273482651

**Chosen Implementation Approach:**
1. **Single Line Fix**: Modify Line 524 in Script 03v4 to enhance the regex pattern
2. **Pattern Change**: Replace `([^,]*?)` with `(.+?)` to capture all symbols including `&`, `+`, `-`, `/`
3. **Comma Handling**: Enhance lookahead with `(?:,\s*(?:{keywords})|` to handle comma-separated keywords
4. **Expected Results**: "Windows & Patio Doors Market For Single Family Homes" → "Windows & Patio Doors for Single Family Homes" ✅

**Rationale**: This simple approach addresses the root cause (pattern matching failure) with minimal risk and complexity. The enhanced pattern naturally preserves all special characters without requiring validation layers, symbol recovery mechanisms, or multiple pattern attempts. Maintains consistency with the simple solution philosophy used for Issues #26, #27, #28, and #29.

## Code References

**File:** `/experiments/03_report_type_extractor_v4.py`
- **Line 524:** Current problematic pattern
- **Line 503-557:** `_extract_market_term_from_title` method requiring enhancement
- **Line 478-501:** `extract_market_term_workflow` method for integration
- **Line 545-551:** Pipeline forward text generation needing symbol validation

**Test File:** `/experiments/tests/test_issue19_ampersand_loss.py`
- Demonstrates current behavior and validates fix

## MongoDB Patterns Affected

### Separators Collection
- `&` separator (priority: 3) - properly configured
- `and` separator (priority: 5) - properly configured

### Report Type Patterns
- Multiple patterns contain `&` in terms (e.g., "Market Size & Share Report")
- These patterns work correctly when symbols are preserved in extraction