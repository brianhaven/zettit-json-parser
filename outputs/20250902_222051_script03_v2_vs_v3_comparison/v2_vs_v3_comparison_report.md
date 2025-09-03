# Script 03 v2 vs v3 Comprehensive Comparison Report

**Analysis Date (PDT):** 2025-09-02 22:20:51 PDT  
**Analysis Date (UTC):** 2025-09-03 05:20:51 UTC

## Executive Summary

**Test Cases:** 25 diverse market research titles
**v2 Success Rate:** 100.00% (25/25)
**v3 Success Rate:** 96.00% (24/25)
**Regression:** -4.00% with v3 dictionary approach ❌

## Detailed Performance Analysis

### Success/Failure Breakdown

| Metric | v2 (Pattern-Based) | v3 (Dictionary-Based) | Difference |
|--------|-------------------|----------------------|------------|
| Successful | 25 | 24 | -1 |
| Failed | 0 | 1 | +1 |
| Success Rate | 100.00% | 96.00% | -4.00% |

## Case-by-Case Detailed Analysis

| Case | Original Title | v2 Result | v3 Result | Status |
|------|---------------|-----------|-----------|--------|
| 1 | Rice Straw Market for Silica Production | ✅ SUCCESS | ❌ FAILED | 🟠 v3 Regression |
| 2 | Indonesia Self-adhesive Vinyl Films Mark... | ✅ SUCCESS | ✅ SUCCESS | 🟢 Both Success |
| 3 | Tablet Hardness Testers Market Forecast ... | ✅ SUCCESS | ✅ SUCCESS | 🟢 Both Success |
| 4 | EMEA Industrial Coatings Market for Mini... | ✅ SUCCESS | ✅ SUCCESS | 🟢 Both Success |
| 5 | Heel Incision Devices Market Insights, 2... | ✅ SUCCESS | ✅ SUCCESS | 🟢 Both Success |
| 6 | Ampoules and Syringes Market Forecast An... | ✅ SUCCESS | ✅ SUCCESS | 🟢 Both Success |
| 7 | Thin Film Material Market Size, Share, I... | ✅ SUCCESS | ✅ SUCCESS | 🟢 Both Success |
| 8 | Graphene Market Size, Share, Trends & Gr... | ✅ SUCCESS | ✅ SUCCESS | 🟢 Both Success |
| 9 | U.S. Atherectomy Devices Market Size, Sh... | ✅ SUCCESS | ✅ SUCCESS | 🟢 Both Success |
| 10 | Capsule Endoscopy Market Size, Industry ... | ✅ SUCCESS | ✅ SUCCESS | 🟢 Both Success |
| 11 | Power System Analysis Software Market Ou... | ✅ SUCCESS | ✅ SUCCESS | 🟢 Both Success |
| 12 | Switzerland Hearing Aid Retailers Market... | ✅ SUCCESS | ✅ SUCCESS | 🟢 Both Success |
| 13 | Propane Market Size, Share, Global Indus... | ✅ SUCCESS | ✅ SUCCESS | 🟢 Both Success |
| 14 | Viral Clearance Market Size, Share, Glob... | ✅ SUCCESS | ✅ SUCCESS | 🟢 Both Success |
| 15 | Spoil Detection Based Smart Label Market... | ✅ SUCCESS | ✅ SUCCESS | 🟢 Both Success |
| 16 | Rabies Diagnostics Market Size & Share, ... | ✅ SUCCESS | ✅ SUCCESS | 🟢 Both Success |
| 17 | Asset Management System Market Size, Glo... | ✅ SUCCESS | ✅ SUCCESS | 🟢 Both Success |
| 18 | Europe PGM Catalyst Market Size & Share ... | ✅ SUCCESS | ✅ SUCCESS | 🟢 Both Success |
| 19 | Toluene Diisocyanate Market Size & Share... | ✅ SUCCESS | ✅ SUCCESS | 🟢 Both Success |
| 20 | Solar District Heating Market Size & Sha... | ✅ SUCCESS | ✅ SUCCESS | 🟢 Both Success |
| 21 | Mining Equipment Market | ✅ SUCCESS | ✅ SUCCESS | 🟢 Both Success |
| 22 | Cable Management System Market Size, Sha... | ✅ SUCCESS | ✅ SUCCESS | 🟢 Both Success |
| 23 | B2B2C Insurance Market | ✅ SUCCESS | ✅ SUCCESS | 🟢 Both Success |
| 24 | Port Equipment Market | ✅ SUCCESS | ✅ SUCCESS | 🟢 Both Success |
| 25 | Voice Communication Control System Marke... | ✅ SUCCESS | ✅ SUCCESS | 🟢 Both Success |

## Issues Requiring Attention

### v3 Dictionary Approach Issues

**Case 1:** Rice Straw Market for Silica Production
- **Error:** None
- **Market Type:** market_for

### Critical v3 Regressions (worked in v2, failed in v3)

**Case 1:** Rice Straw Market for Silica Production
- **v2 extracted:** Market
- **v3 error:** None

## Recommendations

❌ **REGRESSION DETECTED**: v3 performs worse than v2
- Review dictionary algorithm implementation
- Analyze regression cases for pattern gaps
- Consider reverting to v2 approach until issues resolved

## Next Steps

1. **Address 1 failed cases** in v3 implementation
2. **Enhance dictionary patterns** based on failure analysis
3. **Re-run validation** to confirm 100% success rate
4. **Update GitHub Issue #20** with validation results

