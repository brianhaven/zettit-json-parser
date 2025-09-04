# Market Term Classifier Testing Report - Phase 1

**Analysis Date (PDT):** 2025-08-21 12:04:39 PDT  
**Analysis Date (UTC):** 2025-08-21 19:04:39 UTC

## Summary Statistics

| Metric | Count | Percentage |
|--------|-------|------------|
| Total Documents | 2,000 | 100% |
| Market For | 2 | 0.10% |
| Market In | 2 | 0.10% |
| Standard | 1996 | 99.80% |
| Ambiguous | 0 | 0.00% |

## Confidence Distribution

| Confidence Range | Count |
|-----------------|-------|
| high (>0.9) | 4 |
| medium (0.7-0.9) | 1996 |
| low (<0.7) | 0 |

## Pattern Variations Discovered

### Market In

- **Total Found:** 2
- **Unique Patterns:** 1
- **Sample Titles:**
  - Big Data Market In The Oil & Gas Sector, Global Industry Report, 2025
  - Material Handling Equipment Market In Biomass Power Plant Report, 2030

### Market For

- **Total Found:** 2
- **Unique Patterns:** 1
- **Sample Titles:**
  - Carbon Black Market For Textile Fibers Growth Report, 2020
  - Oman Industrial Salts Market For Oil & Gas Industry Report, 2020-2027

## Sample Results for Manual Review

### Market For Classifications

**1. Title:** Carbon Black Market For Textile Fibers Growth Report, 2020
   - **Confidence:** 0.950
   - **Pattern:** \bmarket\s+for\b
   - **Notes:** Requires concatenation processing

**2. Title:** Oman Industrial Salts Market For Oil & Gas Industry Report, 2020-2027
   - **Confidence:** 0.950
   - **Pattern:** \bmarket\s+for\b
   - **Notes:** Requires concatenation processing

### Market In Classifications

**1. Title:** Material Handling Equipment Market In Biomass Power Plant Report, 2030
   - **Confidence:** 0.950
   - **Pattern:** \bmarket\s+in\b
   - **Notes:** Requires context integration processing

**2. Title:** Big Data Market In The Oil & Gas Sector, Global Industry Report, 2025
   - **Confidence:** 0.950
   - **Pattern:** \bmarket\s+in\b
   - **Notes:** Requires context integration processing

### Standard Classifications

**1. Title:** France Digital Signage Market Size & Share Report, 2030
   - **Confidence:** 0.900
   - **Notes:** Standard processing - systematic pattern removal approach

**2. Title:** Passive Fire Protection Market Size & Share Report, 2030
   - **Confidence:** 0.900
   - **Notes:** Standard processing - systematic pattern removal approach

**3. Title:** Bare Die Shipping & Handling and Processing & Storage Market Report, 2030
   - **Confidence:** 0.900
   - **Notes:** Standard processing - systematic pattern removal approach

**4. Title:** Mining Equipment Rental Market Size, Industry Report, 2030
   - **Confidence:** 0.900
   - **Notes:** Standard processing - systematic pattern removal approach

**5. Title:** Organic Electronics Market Size & Share, Industry Report, 2019-2025
   - **Confidence:** 0.900
   - **Notes:** Standard processing - systematic pattern removal approach

**6. Title:** Lignin Market Size, Share And Growth Analysis Report, 2030
   - **Confidence:** 0.900
   - **Notes:** Standard processing - systematic pattern removal approach

**7. Title:** Wheelchair Accessible Vehicle Converters Market
   - **Confidence:** 0.900
   - **Notes:** Standard processing - systematic pattern removal approach

**8. Title:** Lithium-ion Battery Market Size, Share & Growth Report, 2030
   - **Confidence:** 0.900
   - **Notes:** Standard processing - systematic pattern removal approach

**9. Title:** Perforating Gun Market Size, Share & Growth Report, 2030
   - **Confidence:** 0.900
   - **Notes:** Standard processing - systematic pattern removal approach

**10. Title:** High Voltage Direct Current Power Supply Market Report, 2030
   - **Confidence:** 0.900
   - **Notes:** Standard processing - systematic pattern removal approach


## Recommendations

### Pattern Distribution Analysis

- ✅ **Market For** patterns (0.10%) are within expected range (~0.2%).
- ✅ **Market In** patterns (0.10%) are within expected range (~0.1%).

### Confidence Score Analysis


### Next Steps

1. Review sample results for misclassifications
2. Identify new pattern variations from the results
3. Update MongoDB pattern library with discovered patterns
4. Run iteration 2 tests to measure improvement
