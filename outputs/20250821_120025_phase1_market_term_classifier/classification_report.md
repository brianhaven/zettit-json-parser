# Market Term Classifier Testing Report - Phase 1

**Analysis Date (PDT):** 2025-08-21 12:00:25 PDT  
**Analysis Date (UTC):** 2025-08-21 19:00:25 UTC

## Summary Statistics

| Metric | Count | Percentage |
|--------|-------|------------|
| Total Documents | 1,000 | 100% |
| Market For | 2 | 0.20% |
| Market In | 0 | 0.00% |
| Standard | 998 | 99.80% |
| Ambiguous | 0 | 0.00% |

## Confidence Distribution

| Confidence Range | Count |
|-----------------|-------|
| high (>0.9) | 2 |
| medium (0.7-0.9) | 998 |
| low (<0.7) | 0 |

## Pattern Variations Discovered

### Market For

- **Total Found:** 2
- **Unique Patterns:** 1
- **Sample Titles:**
  - Advanced Materials Market for Water and Wastewater Treatment
  - Oman Industrial Salts Market For Oil & Gas Industry Report, 2020-2027

## Sample Results for Manual Review

### Market For Classifications

**1. Title:** Advanced Materials Market for Water and Wastewater Treatment
   - **Confidence:** 0.950
   - **Pattern:** \bmarket\s+for\b
   - **Notes:** Requires concatenation processing

**2. Title:** Oman Industrial Salts Market For Oil & Gas Industry Report, 2020-2027
   - **Confidence:** 0.950
   - **Pattern:** \bmarket\s+for\b
   - **Notes:** Requires concatenation processing

### Standard Classifications

**1. Title:** U.S. 3D Imaging Distance Service Market Size Report, 2030
   - **Confidence:** 0.900
   - **Notes:** Standard processing - systematic pattern removal approach

**2. Title:** Blood-based Biomarker For Sports Medicine Market Report 2030
   - **Confidence:** 0.900
   - **Notes:** Standard processing - systematic pattern removal approach

**3. Title:** Packaging Inserts & Cushions Market Size, Industry Report, 2027
   - **Confidence:** 0.900
   - **Notes:** Standard processing - systematic pattern removal approach

**4. Title:** Quantum Computing Market Size, Industry Report, 2030
   - **Confidence:** 0.900
   - **Notes:** Standard processing - systematic pattern removal approach

**5. Title:** U.S. Ferritin Testing Market Size, Industry Report, 2033
   - **Confidence:** 0.900
   - **Notes:** Standard processing - systematic pattern removal approach

**6. Title:** Insight Engines Market Size & Share Analysis Report, 2030
   - **Confidence:** 0.900
   - **Notes:** Standard processing - systematic pattern removal approach

**7. Title:** Electric Bus Battery Pack Market Size, Industry Report, 2030
   - **Confidence:** 0.900
   - **Notes:** Standard processing - systematic pattern removal approach

**8. Title:** Medical Connectors Market
   - **Confidence:** 0.900
   - **Notes:** Standard processing - systematic pattern removal approach

**9. Title:** U.S. Specialty Printing Consumables Market
   - **Confidence:** 0.900
   - **Notes:** Standard processing - systematic pattern removal approach

**10. Title:** Asia Pacific Commercial Vacuum Cleaner Market Report, 2030
   - **Confidence:** 0.900
   - **Notes:** Standard processing - systematic pattern removal approach


## Recommendations

### Pattern Distribution Analysis

- ✅ **Market For** patterns (0.20%) are within expected range (~0.2%).
- ⚠️ **Market In** patterns (0.00%) are below expected ~0.1%. May need pattern enhancement.

### Confidence Score Analysis


### Next Steps

1. Review sample results for misclassifications
2. Identify new pattern variations from the results
3. Update MongoDB pattern library with discovered patterns
4. Run iteration 2 tests to measure improvement
