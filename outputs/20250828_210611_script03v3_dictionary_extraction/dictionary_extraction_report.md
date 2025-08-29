# Script 03v3 Dictionary Extraction Report

**Analysis Date (PDT):** 2025-08-28 21:06:12 PDT
**Analysis Date (UTC):** 2025-08-29 04:06:12 UTC
**Source Patterns:** 921 active report_type patterns
**Success Rate:** 100.0%

## Executive Summary

This analysis extracted keyword, separator, and punctuation dictionaries from 921 report type patterns to enable Script 03 v3 algorithmic detection approach.

## Primary Keywords (≥10% frequency)

- **Market**: 892 patterns (96.85%)
- **Size**: 523 patterns (56.79%)
- **Report**: 505 patterns (54.83%)
- **Share**: 404 patterns (43.87%)
- **Industry**: 294 patterns (31.92%)
- **Trends**: 234 patterns (25.41%)
- **Analysis**: 232 patterns (25.19%)
- **Growth**: 199 patterns (21.61%)
- **Global**: 98 patterns (10.64%)

## Secondary Keywords (<10% frequency)

Total secondary keywords found: 41

- And: 69 patterns (7.49%)
- Forecast: 64 patterns (6.95%)
- Research: 34 patterns (3.69%)
- Outlook: 26 patterns (2.82%)
- Trend: 26 patterns (2.82%)
- Study: 19 patterns (2.06%)
- Insights: 18 patterns (1.95%)
- Overview: 16 patterns (1.74%)
- Report]: 12 patterns (1.3%)
- Data: 10 patterns (1.09%)
- (Forecast: 6 patterns (0.65%)
- Companies: 6 patterns (0.65%)
- [ACRONYM]: 6 patterns (0.65%)
- Intelligence: 5 patterns (0.54%)
- Value: 5 patterns (0.54%)
- By: 5 patterns (0.54%)
- Regional: 5 patterns (0.54%)
- International: 5 patterns (0.54%)
- Domestic: 5 patterns (0.54%)
- Local: 5 patterns (0.54%)

## Separators Analysis

Common separators found in patterns:

- `" "`: 2718 patterns
- `","`: 882 patterns
- `"&"`: 264 patterns
- `", "`: 255 patterns

## Boundary Markers Analysis

Boundary markers found in patterns:

- **Market**: 891 patterns
- **compound_middle**: 604 patterns
- **Industry**: 294 patterns
- **terminal_end**: 280 patterns
- **Global**: 100 patterns
- **prefix_start**: 13 patterns

## Format Type Distribution

- **compound_type**: 604 patterns (65.6%)
- **terminal_type**: 280 patterns (30.4%)
- **embedded_type**: 18 patterns (2.0%)
- **prefix_type**: 13 patterns (1.4%)
- **acronym_embedded**: 6 patterns (0.7%)

## Implementation Recommendations

### Market Boundary Detection
- **Primary boundary word**: "Market" (found in 891 patterns)
- **Secondary boundaries**: Industry, Global

### Keyword Detection Priority
1. **High Priority** (≥10% frequency): 9 keywords
2. **Medium Priority** (<10% frequency): 41 keywords

### Separator Handling
- **Primary separators**: Space, comma+space, ampersand
- **Complex separators**: "And", "&" with surrounding spaces

### Algorithm Design
1. Use "Market" as primary boundary detection
2. Search for keywords in frequency order (primary first)
3. Detect separators between found keywords
4. Handle edge cases for non-dictionary words

## Next Steps

1. Implement keyword detection algorithm using primary keywords
2. Create separator detection between keyword boundaries
3. Build edge case detection for non-dictionary words
4. Test against current v2 implementation for accuracy validation

