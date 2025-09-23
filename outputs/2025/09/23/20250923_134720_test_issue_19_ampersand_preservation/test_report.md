# Issue #19 Ampersand Preservation Test Output

**Analysis Date (PDT):** 2025-09-23 13:47:21 PDT
**Analysis Date (UTC):** 2025-09-23 20:47:21 UTC

**Description:** Validation of symbol preservation during market term extraction

================================================================================


# GitHub Issue #19: Ampersand Preservation Test Report

## Summary

- **Total Tests:** 8
- **Passed:** 8
- **Failed:** 0
- **Success Rate:** 100.0%

## Test Results

| # | Category | Title | Symbol | Status | Result |
|---|----------|-------|--------|--------|--------|
| 1 | Ampersand in market term | U.S. Windows & Patio Doors Market For Single Famil... | & | PASSED | Windows & Patio Doors for Single Family Homes |
| 2 | Ampersand in context | Oman Industrial Salts Market For Oil & Gas Industr... | & | PASSED | Industrial Salts for Oil & Gas |
| 3 | Multiple symbols (&, /) | Global Food & Beverage Market For Hotels/Restauran... | & | PASSED | Food & Beverage for Hotels/Restaurants |
| 4 | Complex symbols (&, +) | Asia-Pacific R&D Market For Pharmaceuticals + Biot... | & | PASSED | R&D for Pharmaceuticals + Biotech |
| 5 | Market In pattern with & | European Mergers & Acquisitions Market In Banking/... | & | PASSED | Mergers & Acquisitions in Banking/Finance |
| 6 | Standard pattern with & | Oil & Gas Market Analysis and Trends, 2025... | & | PASSED | Oil & Gas |
| 7 | Plus symbol preservation | Food + Beverages Market Research Report, 2030... | + | PASSED | Food + Beverages |
| 8 | Slash symbol preservation | Telecom/Media Market Outlook & Forecast, 2025-2035... | / | PASSED | Telecom/Media |

## Detailed Analysis

### Test Case 1: Ampersand in market term

**Original Title:** U.S. Windows & Patio Doors Market For Single Family Homes, Report, 2030

**Processing Steps:**
1. Market Type: market_for
2. Date Extracted: 2030
3. Report Type: Market
4. Regions: ['United States']
5. Final Topic: Windows & Patio Doors for Single Family Homes

**Expected:** Windows & Patio Doors for Single Family Homes
**Symbol Preserved:** ✅ Yes

### Test Case 2: Ampersand in context

**Original Title:** Oman Industrial Salts Market For Oil & Gas Industry Report, 2020-2027

**Processing Steps:**
1. Market Type: market_for
2. Date Extracted: 2020-2027
3. Report Type: Market Report
4. Regions: ['Oman']
5. Final Topic: Industrial Salts for Oil & Gas

**Expected:** Industrial Salts for Oil & Gas Industry
**Symbol Preserved:** ✅ Yes

### Test Case 3: Multiple symbols (&, /)

**Original Title:** Global Food & Beverage Market For Hotels/Restaurants Industry Analysis, 2025

**Processing Steps:**
1. Market Type: market_for
2. Date Extracted: 2025
3. Report Type: Market Analysis
4. Regions: ['Global']
5. Final Topic: Food & Beverage for Hotels/Restaurants

**Expected:** Food & Beverage for Hotels/Restaurants
**Symbol Preserved:** ✅ Yes

### Test Case 4: Complex symbols (&, +)

**Original Title:** Asia-Pacific R&D Market For Pharmaceuticals + Biotech Outlook, 2024-2030

**Processing Steps:**
1. Market Type: market_for
2. Date Extracted: 2024-2030
3. Report Type: Market
4. Regions: ['Asia Pacific']
5. Final Topic: R&D for Pharmaceuticals + Biotech

**Expected:** R&D for Pharmaceuticals + Biotech
**Symbol Preserved:** ✅ Yes

### Test Case 5: Market In pattern with &

**Original Title:** European Mergers & Acquisitions Market In Banking/Finance Report

**Processing Steps:**
1. Market Type: market_in
2. Date Extracted: None
3. Report Type: Market
4. Regions: ['European Union']
5. Final Topic: Mergers & Acquisitions in Banking/Finance

**Expected:** Mergers & Acquisitions in Banking/Finance
**Symbol Preserved:** ✅ Yes

### Test Case 6: Standard pattern with &

**Original Title:** Oil & Gas Market Analysis and Trends, 2025

**Processing Steps:**
1. Market Type: standard
2. Date Extracted: 2025
3. Report Type: Market Analysis and Trends
4. Regions: []
5. Final Topic: Oil & Gas

**Expected:** Oil & Gas
**Symbol Preserved:** ✅ Yes

### Test Case 7: Plus symbol preservation

**Original Title:** Food + Beverages Market Research Report, 2030

**Processing Steps:**
1. Market Type: standard
2. Date Extracted: 2030
3. Report Type: Market Research Report
4. Regions: []
5. Final Topic: Food + Beverages

**Expected:** Food + Beverages
**Symbol Preserved:** ✅ Yes

### Test Case 8: Slash symbol preservation

**Original Title:** Telecom/Media Market Outlook & Forecast, 2025-2035

**Processing Steps:**
1. Market Type: standard
2. Date Extracted: 2025-2035
3. Report Type: Market Outlook Forecast
4. Regions: []
5. Final Topic: Telecom/Media

**Expected:** Telecom/Media
**Symbol Preserved:** ✅ Yes

