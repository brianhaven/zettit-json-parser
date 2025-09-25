# Issue #26 Regression Fix Test Report Output
# Validation of enhanced separator cleanup functionality
# Analysis Date (PDT): 2025-09-24 21:25:31 PDT
# Analysis Date (UTC): 2025-09-25 04:25:31 UTC
================================================================================


## TEST SUMMARY

### Real-World Examples Test
- Total Tests: 6
- Passed: 4 ✅
- Failed: 2 ❌
- Success Rate: 66.7%

### Comprehensive Scenarios Test
- Total Tests: 13
- Passed: 12 ✅
- Failed: 1 ❌
- Success Rate: 92.3%

### Overall Results
- Total Tests Run: 19
- Total Passed: 16
- Total Failed: 3
- Overall Success Rate: 84.2%

================================================================================

## REAL-WORLD EXAMPLES TEST DETAILS

These test cases are taken directly from the 200-document pipeline test that revealed the regression.


### Test #1: word_separator_And
- **Status:** ❌ FAIL
- **Input:** `Timing Relay Market Size, Share And Growth Report, 2024-2030`
- **Expected:** `Market Size, Share Growth Report`
- **Actual:** `Market Size Share Growth Report`


### Test #2: word_separator_And
- **Status:** ✅ PASS
- **Input:** `Polymeric Biomaterials Market Size And Share Report, 2025`
- **Expected:** `Market Size Share Report`
- **Actual:** `Market Size Share Report`


### Test #3: word_separator_And
- **Status:** ✅ PASS
- **Input:** `Gift Wrapping Products Market Size And Share Report, 2024-2029`
- **Expected:** `Market Size Share Report`
- **Actual:** `Market Size Share Report`


### Test #4: word_separator_And
- **Status:** ❌ FAIL
- **Input:** `Aviation IoT Market Size, Share And Growth Report, 2024`
- **Expected:** `Market Size, Share Growth Report`
- **Actual:** `Market Size Share Growth Report`


### Test #5: word_separator_Plus
- **Status:** ✅ PASS
- **Input:** `Market Analysis Plus Forecast Report, 2025`
- **Expected:** `Market Analysis Forecast Report`
- **Actual:** `Market Analysis Forecast Report`


### Test #6: word_separator_Or
- **Status:** ✅ PASS
- **Input:** `Market Trends Or Outlook Report, 2024-2030`
- **Expected:** `Market Trends Outlook Report`
- **Actual:** `Market Trends Outlook Report`


================================================================================

## COMPREHENSIVE SCENARIOS TEST DETAILS

These test cases cover all separator types and edge cases to ensure robust functionality.


### Test #1: symbol_ampersand
- **Status:** ✅ PASS
- **Input:** `Market & Size & Share & Report`
- **Expected:** `Market Size Share Report`
- **Actual:** `Market Size Share Report`


### Test #2: symbol_ampersand
- **Status:** ✅ PASS
- **Input:** `Market & Trends & Analysis`
- **Expected:** `Market Trends Analysis`
- **Actual:** `Market Trends Analysis`


### Test #3: word_and
- **Status:** ✅ PASS
- **Input:** `Market Size And Share Report`
- **Expected:** `Market Size Share Report`
- **Actual:** `Market Size Share Report`


### Test #4: word_and
- **Status:** ✅ PASS
- **Input:** `Market Analysis And Forecast Report`
- **Expected:** `Market Analysis Forecast Report`
- **Actual:** `Market Analysis Forecast Report`


### Test #5: word_plus
- **Status:** ✅ PASS
- **Input:** `Market Growth Plus Trends Report`
- **Expected:** `Market Growth Trends Report`
- **Actual:** `Market Growth Trends Report`


### Test #6: word_or
- **Status:** ❌ FAIL
- **Input:** `Market Overview Or Summary Report`
- **Expected:** `Market Overview Summary Report`
- **Actual:** `Market Overview Report`


### Test #7: mixed_ampersand_and
- **Status:** ✅ PASS
- **Input:** `Market & Size And Share Report`
- **Expected:** `Market Size Share Report`
- **Actual:** `Market Size Share Report`


### Test #8: mixed_ampersand_plus
- **Status:** ✅ PASS
- **Input:** `Market Size & Trends Plus Growth Report`
- **Expected:** `Market Size Trends Growth Report`
- **Actual:** `Market Size Trends Growth Report`


### Test #9: uppercase_AND
- **Status:** ✅ PASS
- **Input:** `Market Size AND Share Report`
- **Expected:** `Market Size Share Report`
- **Actual:** `Market Size Share Report`


### Test #10: lowercase_and
- **Status:** ✅ PASS
- **Input:** `Market Analysis and Forecast Report`
- **Expected:** `Market Analysis Forecast Report`
- **Actual:** `Market Analysis Forecast Report`


### Test #11: uppercase_PLUS
- **Status:** ✅ PASS
- **Input:** `Market Growth PLUS Trends Report`
- **Expected:** `Market Growth Trends Report`
- **Actual:** `Market Growth Trends Report`


### Test #12: edge_orlando
- **Status:** ✅ PASS
- **Input:** `Orlando Market Analysis Report`
- **Expected:** `Market Analysis Report`
- **Actual:** `Market Analysis Report`


### Test #13: edge_portland
- **Status:** ✅ PASS
- **Input:** `Portland Market Study Report`
- **Expected:** `Market Study Report`
- **Actual:** `Market Study Report`


================================================================================

## CONCLUSION


⚠️ **TESTS FAILED!** 3 test(s) did not pass.

Please review the failed test cases above and adjust the implementation accordingly.
