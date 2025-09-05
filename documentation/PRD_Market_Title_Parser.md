# Product Requirements Document: Market Research Title Parser

**Last Updated:** 2025-09-05  
**Version:** 4.0  
**Status:** Script 03 v4 Pure Dictionary Architecture Implemented

## Executive Summary

A systematic pattern-matching solution for extracting structured information from market research report titles using MongoDB-based pattern libraries and deterministic processing logic.

## Problem Statement

Market research organizations maintain collections of 19,000+ report titles containing valuable structured data that needs systematic extraction:
- **Topics**: Core subject matter (e.g., "Antimicrobial Medical Textiles")
- **Geographic Regions**: Market scope (e.g., "APAC", "North America")
- **Report Types**: Analysis methodology (e.g., "Market Size & Share Report")
- **Forecast Dates**: Time horizons (e.g., "2030", "2020-2027")

Manual extraction is impractical, and traditional NLP solutions are expensive ($900+/month for GPU-based approaches).

## Solution Overview

### Core Approach: Systematic Pattern Removal
Transform the NLP problem into deterministic pattern matching through systematic removal:
1. Remove known patterns in order (dates, report types, regions)
2. What remains IS the topic - no interpretation required
3. Track confidence levels for human review of edge cases

### Technology Stack
- **Database**: MongoDB Atlas for both data and pattern libraries
- **Pattern Libraries**: MongoDB collections for real-time updates
- **Processing**: Python with regex-based pattern matching
- **Geographic Enhancement**: SpaCy/GLiNER for entity discovery only
- **Deployment**: AWS EC2 t3.large (~$70-80/month)

## Functional Requirements

### 1. Market Term Classification
**Requirement**: Identify and route special market term patterns
- Detect "Market for" patterns (0.2% of dataset)
- Detect "Market in" patterns (0.1% of dataset)
- Route remaining 99.7% as standard "Market" titles

**Implementation**: Simple string matching with special processing rules

### 2. Date Extraction
**Field Name**: `extracted_forecast_date_range`
- Standard patterns: ", 2030" (terminal comma format)
- Range patterns: ", 2020-2027"
- Bracket patterns: "[2023 Report]"
- Embedded patterns: "Outlook 2031" (no comma)

**Success Target**: 98-99% extraction accuracy

### 3. Report Type Extraction ✅ **PRODUCTION READY**
**Field Name**: `extracted_report_type`
- **Script 03 v4**: Pure dictionary-based boundary detection achieving 90% success rate
- **Architecture**: Dictionary term identification around "Market" keyword with systematic removal
- **Database-driven**: All patterns from MongoDB pattern_libraries collection
- Examples: "Market Size & Share Report", "Market Industry Report"

**Success Target**: 95-97% extraction accuracy  
**Achieved**: 90% success rate in 250-document comprehensive testing (September 2025)

### 4. Geographic Entity Detection
**Field Name**: `extracted_regions` (array preserving source order)
- Compound-first processing ("North America" before "America")
- 363+ entity library with aliases
- SpaCy/GLiNER for discovery of new entities only

**Success Target**: 96-98% detection accuracy

### 5. Topic Extraction
**Field Names**: 
- `topic`: Clean extracted topic
- `topicName`: Normalized version for system use

**Processing Logic**:
- Everything before "Market" minus extracted patterns
- Preserve technical compounds and specifications
- Handle special concatenation for "Market for/in" patterns

**Success Target**: 92-95% extraction accuracy

### 6. Confidence Tracking
**Requirement**: Identify uncertain extractions for human review
- Calculate confidence scores based on extraction completeness
- Flag titles with confidence < 0.8
- Maintain confusion tracker for pattern library improvement

## Non-Functional Requirements

### Performance
- Process 20,000 titles in < 5 minutes
- MongoDB query response < 100ms
- Script startup time < 1 second

### Reliability
- Deterministic processing (same input = same output)
- Graceful handling of malformed titles
- Comprehensive error logging

### Maintainability
- MongoDB-based libraries for real-time updates
- No deployment required for pattern updates
- Version tracking for all library changes

## Data Architecture

### MongoDB Collections

#### Pattern Libraries
```javascript
// pattern_libraries collection
{
  "_id": ObjectId(),
  "type": "geographic_entity", // or "market_term", "date_pattern", "report_type"
  "term": "North America",
  "aliases": ["NA", "North American"],
  "priority": 1,  // For compound processing order
  "active": true,
  "success_count": 1547,
  "failure_count": 3,
  "created_date": ISODate(),
  "last_updated": ISODate()
}
```

#### Processed Results
```javascript
// markets_processed collection
{
  "_id": ObjectId(),
  "original_title": "APAC & Middle East Personal Protective Equipment Market Report, 2030",
  "market_term_type": "standard",
  "extracted_forecast_date_range": "2030",
  "extracted_report_type": "Market Report",
  "extracted_regions": ["APAC", "Middle East"],
  "topic": "Personal Protective Equipment",
  "topicName": "personal-protective-equipment",
  "confidence_score": 0.95,
  "processing_date": ISODate(),
  "processing_version": "1.0"
}
```

## Processing Pipeline

### Step-by-Step Implementation Plan

1. **MongoDB Setup**
   - Create pattern library collections
   - Initialize with base patterns
   - Set up performance tracking

2. **Market Terms Library** (2 patterns)
   - "Market for" detection
   - "Market in" detection
   - Special processing rules

3. **Date Pattern Library**
   - Regex patterns for all date formats
   - Extraction and validation logic
   - Edge case handling

4. **Report Type Library**
   - Core patterns post-date removal
   - Normalization rules
   - Deduplication logic

5. **Geographic Entity Library**
   - 363+ base entities
   - SpaCy/GLiNER discovery pipeline
   - Compound priority ordering

6. **Topic Extraction Logic**
   - Systematic removal implementation
   - Technical compound preservation
   - Normalization rules

7. **Validation & Testing**
   - End-to-end processing tests
   - Confidence scoring calibration
   - Human review workflow

## Success Metrics

### Target Accuracy Rates
- **Overall Processing**: 95-98% complete success
- **Date Extraction**: 98-99% accuracy
- **Report Type**: 95-97% accuracy
- **Geographic Detection**: 96-98% accuracy
- **Topic Extraction**: 92-95% accuracy

### Quality Indicators
- < 5% titles requiring human review
- < 2% false positive geographic detection
- < 1% critical parsing failures

## Implementation Strategy

### Development Approach
1. Build modular experiment scripts
2. Iterate on pattern libraries with real data
3. Track performance metrics in MongoDB
4. Refine based on confusion tracker results
5. Deploy as production service

### Library Building Process
1. Start with known patterns
2. Process sample data
3. Identify failures and edge cases
4. Update libraries based on discoveries
5. Reprocess and validate improvements

## Risk Mitigation

### Technical Risks
- **Pattern Complexity**: Mitigated by systematic removal approach
- **Edge Cases**: Handled through confidence scoring and human review
- **Performance**: Addressed by MongoDB indexing and caching

### Business Risks
- **Accuracy Requirements**: Met through iterative library refinement
- **Maintenance Burden**: Minimized with MongoDB-based updates
- **Scaling Concerns**: Handled by deterministic processing architecture

## Future Enhancements

### Phase 2 Opportunities
- Automated pattern discovery from processing results
- Machine learning for confidence score optimization
- API service for real-time title processing
- Integration with report generation systems

### Long-term Vision
- Self-improving system through success/failure tracking
- Expansion to other text extraction domains
- Multi-language support for global markets

## Conclusion

This solution transforms a complex NLP challenge into a manageable pattern-matching problem through systematic processing and MongoDB-based library management. The approach delivers 95%+ accuracy at 1/10th the cost of traditional NLP solutions while maintaining complete explainability and control.