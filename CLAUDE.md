# Zettit JSON Parser - Market Research Title Analysis

## Project Overview

This project extracts structured information (topics, topicNames, regions) from market research report titles in MongoDB's markets_raw collection using systematic pattern analysis and library-based processing.

## Development Standards

### Script Organization
- **Official scripts:** Root directory
- **Development/testing scripts:** `/experiments/` directory with version numbers (e.g., `script_name_v1.py`)
- **Output files:** `/outputs/` directory with timestamp format `{YYYYMMDD_HHMMSS}_{TYPE}`
- **Documentation:** `/documentation/` directory for permanent docs only
- **Data files:** `/resources/` directory

### Output File Requirements

**All script outputs must include dual timestamps:**
```
**Analysis Date (PDT):** 2025-08-19 15:30:45 PDT  
**Analysis Date (UTC):** 2025-08-19 22:30:45 UTC
```

**Filename format:** `{YYYYMMDD_HHMMSS}_{TYPE}.{ext}`
- Use Pacific Time for timestamps in filenames
- Include both PDT/PST and UTC timestamps in file headers
- Examples: `20250819_153045_pattern_analysis.json`, `20250819_153045_processing_summary.md`

### Processing Methodology

**Step-based systematic approach:**
1. **Market term classification:** Separate "Market for"/"Market in" from standard "Market" titles
2. **Date extraction:** Remove dates first to prevent report type contamination
3. **Report type extraction:** Extract from "Market" onwards (include "Market" for standard titles)
4. **Geographic processing:** Compound entity detection with priority (e.g., "North America" before "America")
5. **Topic extraction:** Preserve complete technical compounds and specifications

### Library-Based Processing Strategy

**Core principle:** Build comprehensive libraries for:
- Confusing market terms ("After Market", "Marketplace", "Farmers Market")
- Date patterns (bracketed formats, non-comma patterns)
- Geographic entities (compound-first priority)
- Report type variations

**Processing philosophy:** Systematic removal approach
- Remove dates/suffixes, report types, geographic regions
- What remains IS the topic (regardless of internal punctuation)
- Handle edge cases through library expansion, not complex parsing

### Code Standards

- **MongoDB connection:** Use environment variables from `.env` file
- **Logging:** Include comprehensive logging for debugging
- **Error handling:** Graceful handling with informative error messages
- **Performance:** Process large datasets efficiently with progress indicators
- **Validation:** Include success rate tracking and failure analysis

### Environment Setup

**Required environment variables:**
```
MONGODB_URI=mongodb+srv://...
```

**Dependencies:**
- `pymongo` for MongoDB connectivity
- `python-dotenv` for environment variable management
- Standard libraries: `json`, `re`, `datetime`, `collections`

### Testing Strategy

- Use `/experiments/` directory for development and testing
- Set aside confusing titles for manual review and library improvement
- Continuous validation against known patterns
- User feedback integration for library enhancement

### Success Metrics

**Target success rates:**
- Standard titles (99.7% of dataset): 95-98% processing success
- Special market terms (0.3% of dataset): 85-90% processing success
- Overall dataset: 95-97% complete processing success

### Library Maintenance

- Expandable libraries for continuous improvement
- User-guided enhancement of edge case handling
- Pattern discovery from real data for library updates
- Version control for library changes and improvements

## Current Status

**Completed Analysis:**
- Pattern discovery across 19,558 titles
- AI analysis of processing strategies
- Failure case identification and solutions
- Processing architecture design

**Next Steps:**
- Library building and systematic removal implementation
- Production script development
- Validation and testing framework
- Deployment preparation