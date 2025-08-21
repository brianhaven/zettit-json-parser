# Market Term Classifier Testing Report - Phase 1

**Analysis Date (PDT):** 2025-08-21 11:43:31 PDT  
**Analysis Date (UTC):** 2025-08-21 18:43:31 UTC

## Summary Statistics

| Metric | Count | Percentage |
|--------|-------|------------|
| Total Documents | 1,000 | 100% |
| Market For | 0 | 0.00% |
| Market In | 2 | 0.20% |
| Standard | 998 | 99.80% |
| Ambiguous | 0 | 0.00% |

## Confidence Distribution

| Confidence Range | Count |
|-----------------|-------|
| high (>0.9) | 2 |
| medium (0.7-0.9) | 998 |
| low (<0.7) | 0 |

## Pattern Variations Discovered

### Market In

- **Total Found:** 2
- **Unique Patterns:** 1
- **Sample Titles:**
  - Nanoparticles - Metal & Metal Oxides Market In Healthcare Report, 2025
  - Middle East & North Africa Diesel Generator Market in Telecom Industry 2027

## Sample Results for Manual Review

### Market In Classifications

**1. Title:** Middle East & North Africa Diesel Generator Market in Telecom Industry 2027
   - **Confidence:** 0.950
   - **Pattern:** \bmarkets?\s+in\b
   - **Notes:** Requires context integration processing

**2. Title:** Nanoparticles - Metal & Metal Oxides Market In Healthcare Report, 2025
   - **Confidence:** 0.950
   - **Pattern:** \bmarkets?\s+in\b
   - **Notes:** Requires context integration processing

### Standard Classifications

**1. Title:** Glass Mat Market Size, Share, Growth & Trends Report 2030
   - **Confidence:** 0.900
   - **Notes:** Standard processing - systematic pattern removal approach

**2. Title:** Fluid Power Pump And Motor Market Size, Global Industry Report, 2025
   - **Confidence:** 0.900
   - **Notes:** Standard processing - systematic pattern removal approach

**3. Title:** Smart Grid Communications Market Size, Industry Report, 2022
   - **Confidence:** 0.900
   - **Notes:** Standard processing - systematic pattern removal approach

**4. Title:** AI In Revenue Cycle Management Market Size Report, 2030
   - **Confidence:** 0.900
   - **Notes:** Standard processing - systematic pattern removal approach

**5. Title:** Data Center Rack Market
   - **Confidence:** 0.900
   - **Notes:** Standard processing - systematic pattern removal approach

**6. Title:** Autonomous Underwater Vehicle Market Size [2023 Report]
   - **Confidence:** 0.900
   - **Notes:** Standard processing - systematic pattern removal approach

**7. Title:** Polyglyceryl-3 Methylglucose Distearate Market
   - **Confidence:** 0.900
   - **Notes:** Standard processing - systematic pattern removal approach

**8. Title:** Crushing and Screening Systems Market
   - **Confidence:** 0.900
   - **Notes:** Standard processing - systematic pattern removal approach

**9. Title:** Webtoons Market Size, Share & Trends Analysis Report 2030
   - **Confidence:** 0.900
   - **Notes:** Standard processing - systematic pattern removal approach

**10. Title:** 3D Animation Market
   - **Confidence:** 0.900
   - **Notes:** Standard processing - systematic pattern removal approach


## Recommendations

### Pattern Distribution Analysis

- ⚠️ **Market For** patterns (0.00%) are below expected ~0.2%. May need pattern enhancement.
- ✅ **Market In** patterns (0.20%) are within expected range (~0.1%).

### Confidence Score Analysis


### Next Steps

1. Review sample results for misclassifications
2. Identify new pattern variations from the results
3. Update MongoDB pattern library with discovered patterns
4. Run iteration 2 tests to measure improvement
