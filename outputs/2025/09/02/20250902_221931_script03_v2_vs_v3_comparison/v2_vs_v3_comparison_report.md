# Script 03 v2 vs v3 Comprehensive Comparison Report

**Analysis Date (PDT):** 2025-09-02 22:19:31 PDT  
**Analysis Date (UTC):** 2025-09-03 05:19:31 UTC

## Executive Summary

**Test Cases:** 25 diverse market research titles
**v2 Success Rate:** 72.00% (18/25)
**v3 Success Rate:** 68.00% (17/25)
**Regression:** -4.00% with v3 dictionary approach ❌

## Detailed Performance Analysis

### Success/Failure Breakdown

| Metric | v2 (Pattern-Based) | v3 (Dictionary-Based) | Difference |
|--------|-------------------|----------------------|------------|
| Successful | 18 | 17 | -1 |
| Failed | 7 | 8 | +1 |
| Success Rate | 72.00% | 68.00% | -4.00% |

## Case-by-Case Detailed Analysis

| Case | Original Title | v2 Result | v3 Result | Status |
|------|---------------|-----------|-----------|--------|
| 1 | North America Endoscopy Devices Market F... | ❌ FAILED | ❌ FAILED | 🔴 Both Failed |
| 2 | Potassium Formate Market Insights, 2027 | ✅ SUCCESS | ✅ SUCCESS | 🟢 Both Success |
| 3 | High Pulsed Power Market in Well Interve... | ✅ SUCCESS | ❌ FAILED | 🟠 v3 Regression |
| 4 | Laboratory Temperature Control Units Mar... | ✅ SUCCESS | ✅ SUCCESS | 🟢 Both Success |
| 5 | Africa Polyvinylpyrrolidone Market for P... | ❌ FAILED | ❌ FAILED | 🔴 Both Failed |
| 6 | Hybrid Vehicles Market Insights, Forecas... | ✅ SUCCESS | ✅ SUCCESS | 🟢 Both Success |
| 7 | Artificial Urinary Sphincter Market Size... | ✅ SUCCESS | ✅ SUCCESS | 🟢 Both Success |
| 8 | Europe Legal Technology Market Size, Ind... | ❌ FAILED | ❌ FAILED | 🔴 Both Failed |
| 9 | Hydroxypropyl Methylcellulose Market Siz... | ✅ SUCCESS | ✅ SUCCESS | 🟢 Both Success |
| 10 | Wildlife Health Market Size, Share & Gro... | ✅ SUCCESS | ✅ SUCCESS | 🟢 Both Success |
| 11 | Mobile POS Terminals Market Size & Share... | ✅ SUCCESS | ✅ SUCCESS | 🟢 Both Success |
| 12 | Voice And Speech Recognition Market Size... | ✅ SUCCESS | ✅ SUCCESS | 🟢 Both Success |
| 13 | Intelligent Motor Control Centers Market... | ✅ SUCCESS | ✅ SUCCESS | 🟢 Both Success |
| 14 | Xylitol in Personal Care and Cosmetics M... | ✅ SUCCESS | ✅ SUCCESS | 🟢 Both Success |
| 15 | Global Aviation Security Market Size & T... | ❌ FAILED | ❌ FAILED | 🔴 Both Failed |
| 16 | Rubella Diagnostic Testing Market Size, ... | ❌ FAILED | ❌ FAILED | 🔴 Both Failed |
| 17 | Europe Hypodermics Market Size And Share... | ❌ FAILED | ❌ FAILED | 🔴 Both Failed |
| 18 | Aluminum Oxide Market Size, Share, Globa... | ❌ FAILED | ❌ FAILED | 🔴 Both Failed |
| 19 | Food Sorting Machines Market | ✅ SUCCESS | ✅ SUCCESS | 🟢 Both Success |
| 20 | Foam Protective Packaging Market | ✅ SUCCESS | ✅ SUCCESS | 🟢 Both Success |
| 21 | Sports Broadcasting Technology Market Si... | ✅ SUCCESS | ✅ SUCCESS | 🟢 Both Success |
| 22 | Animal Pregnancy Test Kit Market Size & ... | ✅ SUCCESS | ✅ SUCCESS | 🟢 Both Success |
| 23 | Electric Utility Vehicle Market | ✅ SUCCESS | ✅ SUCCESS | 🟢 Both Success |
| 24 | Cloud Native Applications Market Size & ... | ✅ SUCCESS | ✅ SUCCESS | 🟢 Both Success |
| 25 | Cone Beam Computed Tomography (CBCT) Mar... | ✅ SUCCESS | ✅ SUCCESS | 🟢 Both Success |

## Issues Requiring Attention

### v3 Dictionary Approach Issues

**Case 1:** North America Endoscopy Devices Market Forecast 2011 - 2017
- **Error:** 'GeographicExtractionResult' object has no attribute 'remaining_text'
- **Market Type:** None

**Case 3:** High Pulsed Power Market in Well Intervention
- **Error:** None
- **Market Type:** market_in

**Case 5:** Africa Polyvinylpyrrolidone Market for Pharmaceutical & Cosmetic Industries
- **Error:** 'GeographicExtractionResult' object has no attribute 'remaining_text'
- **Market Type:** None

**Case 8:** Europe Legal Technology Market Size, Industry Report, 2030
- **Error:** 'GeographicExtractionResult' object has no attribute 'remaining_text'
- **Market Type:** None

**Case 15:** Global Aviation Security Market Size & Trends, Industry Report, 2025
- **Error:** 'GeographicExtractionResult' object has no attribute 'remaining_text'
- **Market Type:** None

**Case 16:** Rubella Diagnostic Testing Market Size, Global Industry Report, 2025
- **Error:** 'GeographicExtractionResult' object has no attribute 'remaining_text'
- **Market Type:** None

**Case 17:** Europe Hypodermics Market Size And Share, Report, 2030
- **Error:** 'GeographicExtractionResult' object has no attribute 'remaining_text'
- **Market Type:** None

**Case 18:** Aluminum Oxide Market Size, Share, Global Industry Report, 2025
- **Error:** 'GeographicExtractionResult' object has no attribute 'remaining_text'
- **Market Type:** None

### Critical v3 Regressions (worked in v2, failed in v3)

**Case 3:** High Pulsed Power Market in Well Intervention
- **v2 extracted:** Market
- **v3 error:** None

## Recommendations

❌ **REGRESSION DETECTED**: v3 performs worse than v2
- Review dictionary algorithm implementation
- Analyze regression cases for pattern gaps
- Consider reverting to v2 approach until issues resolved

## Next Steps

1. **Address 8 failed cases** in v3 implementation
2. **Enhance dictionary patterns** based on failure analysis
3. **Re-run validation** to confirm 100% success rate
4. **Update GitHub Issue #20** with validation results

