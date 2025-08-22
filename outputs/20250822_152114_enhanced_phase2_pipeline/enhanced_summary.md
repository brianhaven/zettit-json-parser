# Enhanced Phase 2 Pipeline Test Results: Market Term Classifier → Enhanced Date Extractor

**Analysis Date (PDT):** 2025-08-22 15:21:14 PDT
**Analysis Date (UTC):** 2025-08-22 22:21:14 UTC
**Sample Size:** 1,000 documents
**Successfully Processed:** 1,000 documents

## Enhanced Pipeline Performance Summary

### Date Extraction Categorization
- **Successful Extractions**: 0 (0.0%)
- **No Dates Present**: 21 (2.1%)
- **Dates Missed**: 0 (0.0%)
- **Processing Errors**: 0 (0.0%)

### Key Insights

#### Actual Performance Metrics
- **Titles with Dates**: 0 (0.0%)
- **True Success Rate**: 0.0% (of titles with dates)
- **True Failure Rate**: 0.0% (dates missed / titles with dates)

#### Pattern Coverage Analysis
- **No Numeric Content**: Titles without any dates (correctly identified)
- **Dates Missed**: Titles with year-like numbers but no patterns matched
- **Success Rate Improvement**: Focus should be on the 0 titles in "dates_missed" category

### Next Steps
1. Review `titles_with_dates_missed.txt` for pattern gaps
2. Analyze `numeric_analysis.json` for pattern enhancement opportunities
3. Consider the 21 titles without dates as correctly processed (not failures)

## Files Generated
- `enhanced_summary.md` - This overview report
- `categorized_results.json` - Results organized by category
- `titles_with_dates_missed.txt` - Simple list of titles where dates were missed
- `titles_no_dates_present.txt` - Simple list of titles without dates
- `titles_successful_extractions.txt` - Simple list of successfully processed titles
- `numeric_analysis.json` - Detailed numeric content analysis
- `complete_results.json` - Complete pipeline results
