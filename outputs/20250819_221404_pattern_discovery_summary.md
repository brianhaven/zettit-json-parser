# Title Pattern Discovery Analysis
**Analysis Date:** 2025-08-19T22:14:04.985650
**Total Titles Analyzed:** 19,558

## Executive Summary

This analysis follows a systematic outside-in approach to title parsing:
**Date → Report Type → Market Terms → Geographic → Topic**

---

## 1. Market Term Classification

- **Market For:** 48 titles requiring special processing
- **Market In:** 17 titles requiring special processing
- **Standard Market:** 19454 titles for normal processing

### Compound Market Terms (Special Preservation)
- **Aftermarket:** 21 occurrences
- **Marketplace:** 3 occurrences
- **Other Compounds:** 1 occurrences

### Market For Examples:
1. Carbon Black Market For Textile Fibers Growth Report, 2020
2. Oman Industrial Salts Market For Oil & Gas Industry Report, 2020-2027
3. U.S. Windows & Patio Doors Market For Single Family Homes, Report, 2030
4. Advanced Nanomaterials Market for Environmental Detection and Remediation
5. Advanced Materials Market for Nuclear Fusion Technology

### Market In Examples:
1. Big Data Market In The Oil & Gas Sector, Global Industry Report, 2025
2. Material Handling Equipment Market In Biomass Power Plant Report, 2030
3. Retail Market in Singapore - Size, Outlook & Statistics
4. Artificial Intelligence (AI) Market in Automotive
5. Aviation Fuel Terminals Market in India

---

## 2. Date Pattern Discovery

- **Titles with Dates:** 11,963
- **Titles without Dates:** 7,595

### Top Single Year Patterns:
- **2030:** 9169 occurrences
- **2025:** 989 occurrences
- **2033:** 340 occurrences
- **2028:** 108 occurrences
- **2027:** 99 occurrences
- **2022:** 49 occurrences
- **2026:** 46 occurrences
- **2031:** 41 occurrences
- **2024:** 37 occurrences
- **2020:** 17 occurrences

### Top Year Range Patterns:
- **2019-2025:** 379 occurrences
- **2020-2027:** 147 occurrences
- **2022-2030:** 86 occurrences
- **2021-2031:** 85 occurrences
- **2021-2028:** 72 occurrences
- **2018-2025:** 49 occurrences
- **2019-2027:** 31 occurrences
- **2020-2030:** 29 occurrences
- **2016-2024:** 26 occurrences
- **2017-2025:** 18 occurrences

---

## 3. Report Type Pattern Discovery

**Total Unique Report Types Found:** 4419

### Top 20 Report Types:
- **Report:** 11,650 occurrences
- **Industry Report:** 4,251 occurrences
- **Share Report:** 2,081 occurrences
- **Size Report:** 1,408 occurrences
- **Growth Report:** 1,221 occurrences
- **Size & Share Report:** 1,146 occurrences
- **Market Report:** 1,138 occurrences
- **Size, Share & Growth Report:** 664 occurrences
- **_discovered_Share & Growth Report:** 664 occurrences
- **Trends Report:** 652 occurrences
- **Analysis:** 592 occurrences
- **Size and Share Report:** 560 occurrences
- **_discovered_Global Industry Report:** 481 occurrences
- **Analysis Report:** 429 occurrences
- **_discovered_Share & Trends Report:** 359 occurrences
- **Size, Share and Growth Report:** 243 occurrences
- **_discovered_Share And Growth Report:** 243 occurrences
- **Forecast:** 166 occurrences
- **Industry Analysis:** 113 occurrences
- **Insights:** 104 occurrences

---

## 4. Geographic Pattern Discovery

- **Titles with Geographic Content:** 1,765 (9.02%)
- **Titles without Geographic Content:** 17,793
- **Total Enhanced Geographic Entities:** 363

### Top 30 Geographic Entities Found:
- **America:** 426 occurrences
- **Europe:** 378 occurrences
- **North America:** 365 occurrences
- **Asia:** 255 occurrences
- **Pacific:** 213 occurrences
- **Asia Pacific:** 211 occurrences
- **India:** 118 occurrences
- **Africa:** 68 occurrences
- **Middle East:** 65 occurrences
- **China:** 59 occurrences
- **Latin America:** 50 occurrences
- **Australia:** 35 occurrences
- **Germany:** 34 occurrences
- **Canada:** 33 occurrences
- **Japan:** 33 occurrences
- **UK:** 32 occurrences
- **Southeast Asia:** 25 occurrences
- **Brazil:** 24 occurrences
- **Saudi Arabia:** 21 occurrences
- **UAE:** 20 occurrences
- **GCC:** 18 occurrences
- **Mexico:** 17 occurrences
- **France:** 16 occurrences
- **Italy:** 16 occurrences
- **ASEAN:** 15 occurrences
- **MEA:** 15 occurrences
- **Korea:** 15 occurrences
- **Singapore:** 14 occurrences
- **South Korea:** 13 occurrences
- **Indonesia:** 12 occurrences

---

## 5. Suffix Pattern Analysis

**Total Unique Suffixes After 'Market':** 1024

### Top 20 Suffix Patterns:
- **"Size Report, 2030":** 1093 occurrences
- **"Size, Industry Report, 2030":** 958 occurrences
- **"Size & Share Report, 2030":** 893 occurrences
- **"Report, 2030":** 820 occurrences
- **"Industry Report, 2030":** 591 occurrences
- **"Size, Share & Growth Report, 2030":** 580 occurrences
- **"Size And Share Report, 2030":** 545 occurrences
- **"Size & Share, Industry Report, 2030":** 417 occurrences
- **"Size, Share & Trends Report, 2030":** 294 occurrences
- **"Size, Share And Growth Report, 2030":** 238 occurrences
- **"Size, Share, Industry Report, 2030":** 228 occurrences
- **"Size, Share Report, 2030":** 217 occurrences
- **"Size And Share, Industry Report, 2030":** 214 occurrences
- **"Report 2030":** 192 occurrences
- **"Size, Share, Global Industry Report, 2025":** 119 occurrences
- **"Size, Share, Growth Report, 2030":** 118 occurrences
- **"Size, Global Industry Report, 2025":** 113 occurrences
- **"Size, Industry Report, 2025":** 106 occurrences
- **"Size, Industry Report, 2033":** 102 occurrences
- **"Industry Report 2030":** 96 occurrences

---

## 6. Processing Order Analysis Sample

Sample analysis demonstrates the systematic processing approach:

### Topic Extraction Examples (After Processing):

**Example 1:**
- Original: "Antimicrobial Medical Textiles Market, Industry Report, 2030"
- Extracted Topic: "Antimicrobial"
- Market Category: standard_market
- Had Date: True
- Had Report Type: True
- Had Regions: False

**Example 2:**
- Original: "Automotive Steel Wheels Market Size & Share Report, 2030"
- Extracted Topic: "Automotive"
- Market Category: standard_market
- Had Date: True
- Had Report Type: True
- Had Regions: False

**Example 3:**
- Original: "APAC & Middle East Personal Protective Equipment Market Report, 2030"
- Extracted Topic: ""
- Market Category: standard_market
- Had Date: True
- Had Report Type: True
- Had Regions: True

**Example 4:**
- Original: "Aerostructure Materials Market Size & Share Report, 2030"
- Extracted Topic: "Aerostructure"
- Market Category: standard_market
- Had Date: True
- Had Report Type: True
- Had Regions: False

**Example 5:**
- Original: "Ammunition Market Size, Share And Growth Report, 2030"
- Extracted Topic: "Ammunition"
- Market Category: standard_market
- Had Date: True
- Had Report Type: True
- Had Regions: False

---

## Key Insights for Implementation

1. **Market Term Distribution:** Vast majority are standard market patterns, with <1% requiring special handling
2. **Date Patterns:** Clear patterns identified for systematic removal
3. **Report Types:** Comprehensive list of report type variations discovered
4. **Geographic Coverage:** ~8-9% of titles contain geographic information
5. **Processing Order:** Outside-in approach successfully isolates topics in most cases

## Next Steps

1. Review and refine pattern lists
2. Implement processing algorithm based on discovered patterns
3. Test algorithm effectiveness on full dataset
4. Iterate and improve based on results