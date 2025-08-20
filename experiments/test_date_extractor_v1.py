#!/usr/bin/env python3

"""
Test script for Date Extractor v1.0
Validates date extraction accuracy and performance.
"""

import sys
import logging
from date_extractor_v1 import DateExtractor, DateFormat

# Configure logging for tests
logging.basicConfig(level=logging.WARNING)

def test_date_extractor():
    """Run comprehensive tests for Date Extractor."""
    
    print("Date Extractor Tests")
    print("=" * 50)
    
    # Initialize extractor with pattern library manager (REQUIRED)
    from pattern_library_manager_v1 import PatternLibraryManager
    pattern_manager = PatternLibraryManager()
    extractor = DateExtractor(pattern_manager)
    print("✅ Using MongoDB pattern library for testing")
    
    test_results = []
    
    try:
        # Test 1: Terminal comma format detection
        print("\n1. Testing Terminal Comma format...")
        terminal_comma_titles = [
            ("Global AI Market Report, 2030", "2030"),
            ("Healthcare Analysis, 2025", "2025"),
            ("Technology Study, 2031.", "2031"),
            ("Market Research, 2028", "2028"),
        ]
        
        for title, expected_date in terminal_comma_titles:
            result = extractor.extract(title)
            assert result.format_type == DateFormat.TERMINAL_COMMA, f"Failed to detect terminal comma in: {title}"
            assert result.extracted_date_range == expected_date, f"Wrong date extracted from: {title}"
            assert result.confidence >= 0.9, f"Low confidence for terminal comma: {title}"
        
        test_results.append("✅ Terminal Comma format detection")
        
        # Test 2: Range format detection
        print("2. Testing Range format...")
        range_format_titles = [
            ("Market Trends, 2020-2027", "2020-2027"),
            ("Industry Analysis, 2023–2030", "2023-2030"),
            ("Research Study, 2024 to 2029", "2024-2029"),
            ("Market Report, 2023-27", "2023-2027"),  # Abbreviated end year
        ]
        
        for title, expected_date in range_format_titles:
            result = extractor.extract(title)
            assert result.format_type == DateFormat.RANGE_FORMAT, f"Failed to detect range format in: {title}"
            assert result.extracted_date_range == expected_date, f"Wrong date range extracted from: {title}"
            assert result.confidence >= 0.95, f"Low confidence for range format: {title}"
        
        test_results.append("✅ Range format detection")
        
        # Test 3: Bracket format detection
        print("3. Testing Bracket format...")
        bracket_format_titles = [
            ("Market Analysis [2024 Report]", "2024"),
            ("Industry Study [2023]", "2023"),
            ("Research Overview (2025 Update)", "2025"),
            ("Technology Report (2026)", "2026"),
        ]
        
        for title, expected_date in bracket_format_titles:
            result = extractor.extract(title)
            assert result.format_type == DateFormat.BRACKET_FORMAT, f"Failed to detect bracket format in: {title}"
            assert result.extracted_date_range == expected_date, f"Wrong date extracted from: {title}"
            assert result.confidence >= 0.85, f"Low confidence for bracket format: {title}"
        
        test_results.append("✅ Bracket format detection")
        
        # Test 4: Embedded format detection
        print("4. Testing Embedded format...")
        embedded_format_titles = [
            ("Technology Market Outlook 2031", "2031"),
            ("AI Industry Forecast 2030", "2030"),
            ("Market Projections 2028", "2028"),
            ("Industry Growth by 2029", "2029"),
            ("2030 Technology Outlook", "2030"),
        ]
        
        for title, expected_date in embedded_format_titles:
            result = extractor.extract(title)
            assert result.format_type == DateFormat.EMBEDDED_FORMAT, f"Failed to detect embedded format in: {title}"
            assert result.extracted_date_range == expected_date, f"Wrong date extracted from: {title}"
            assert result.confidence >= 0.8, f"Low confidence for embedded format: {title}"
        
        test_results.append("✅ Embedded format detection")
        
        # Test 5: Year validation
        print("5. Testing year validation...")
        invalid_year_titles = [
            "Market Report, 1990",  # Too old
            "Industry Analysis, 2050",  # Too far in future
            "Technology Study, 2010",  # Too old
        ]
        
        for title in invalid_year_titles:
            result = extractor.extract(title)
            # Should either fail extraction or have very low confidence
            assert result.extracted_date_range is None or result.confidence < 0.5, f"Should reject invalid year in: {title}"
        
        test_results.append("✅ Year validation")
        
        # Test 6: Edge cases
        print("6. Testing edge cases...")
        edge_cases = [
            ("", None),  # Empty string
            ("   ", None),  # Whitespace only
            ("No dates here", None),  # No dates
            ("Multiple 2023 and 2024 and 2025 years", "2025"),  # Multiple dates - should pick latest
        ]
        
        for title, expected_date in edge_cases:
            result = extractor.extract(title)
            if expected_date is None:
                assert result.extracted_date_range is None, f"Should not extract date from: '{title}'"
            else:
                assert result.extracted_date_range == expected_date, f"Wrong handling of edge case: '{title}'"
        
        test_results.append("✅ Edge case handling")
        
        # Test 7: Confidence scoring
        print("7. Testing confidence scoring...")
        high_conf_title = "Market Research, 2020-2027"  # Range format - highest confidence
        medium_conf_title = "Market Outlook 2030"  # Embedded format - medium confidence
        
        high_result = extractor.extract(high_conf_title)
        medium_result = extractor.extract(medium_conf_title)
        
        assert high_result.confidence > medium_result.confidence, "Range format should have higher confidence than embedded"
        assert high_result.confidence >= 0.95, "Range format should have very high confidence"
        
        test_results.append("✅ Confidence scoring")
        
        # Test 8: Batch processing
        print("8. Testing batch processing...")
        batch_titles = [title for title, _ in terminal_comma_titles + range_format_titles]
        batch_results = extractor.extract_batch(batch_titles)
        
        assert len(batch_results) == len(batch_titles), "Batch processing length mismatch"
        assert all(r.extracted_date_range is not None for r in batch_results), "Batch processing failed for some titles"
        
        test_results.append("✅ Batch processing")
        
        # Test 9: Statistics tracking
        print("9. Testing statistics tracking...")
        stats = extractor.get_extraction_statistics()
        assert stats.total_processed > 0, "Statistics not tracking total processed"
        assert stats.successful_extractions > 0, "Statistics not tracking successful extractions"
        assert stats.success_rate > 0, "Statistics not calculating success rate"
        
        test_results.append("✅ Statistics tracking")
        
        # Test 10: Report generation
        print("10. Testing report generation...")
        report = extractor.export_extraction_report()
        assert "Date Extraction Report" in report, "Report generation failed"
        assert "Total Titles Processed:" in report, "Report missing key information"
        assert "Success Rate:" in report, "Report missing success rate"
        
        test_results.append("✅ Report generation")
        
        print(f"\n{'='*50}")
        print("TEST RESULTS:")
        for result in test_results:
            print(f"  {result}")
        
        print(f"\n✅ All {len(test_results)} tests passed successfully!")
        
        # Close pattern manager if used
        if 'pattern_manager' in locals():
            pattern_manager.close_connection()
        
        return True
        
    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
        # Close pattern manager if used
        if 'pattern_manager' in locals():
            pattern_manager.close_connection()
        return False
    except Exception as e:
        print(f"\n💥 Test error: {e}")
        import traceback
        traceback.print_exc()
        # Close pattern manager if used
        if 'pattern_manager' in locals():
            pattern_manager.close_connection()
        return False


def test_with_real_data():
    """Test extractor with real MongoDB data if available."""
    
    print("\n" + "="*50)
    print("Testing with Real MongoDB Data")
    print("="*50)
    
    try:
        import os
        from dotenv import load_dotenv
        from pymongo import MongoClient
        from pattern_library_manager_v1 import PatternLibraryManager
        
        # Load environment variables
        load_dotenv()
        mongodb_uri = os.getenv('MONGODB_URI')
        
        if not mongodb_uri:
            print("⚠️  MONGODB_URI not found, skipping real data test")
            return True
        
        # Connect to MongoDB
        client = MongoClient(mongodb_uri, serverSelectionTimeoutMS=5000)
        db = client['deathstar']
        
        # Get sample titles from markets_raw
        sample_titles = list(db.markets_raw.find().limit(200))
        
        if not sample_titles:
            print("⚠️  No data in markets_raw collection, skipping real data test")
            return True
        
        print(f"Testing with {len(sample_titles)} real titles from MongoDB...")
        
        # Initialize extractor with pattern library manager (REQUIRED)
        pattern_manager = PatternLibraryManager()
        extractor = DateExtractor(pattern_manager)
        print("✅ Using MongoDB pattern library for real data testing")
        
        # Extract title text
        title_texts = [title.get('report_title_short', '') for title in sample_titles if title.get('report_title_short')]
        
        if not title_texts:
            print("⚠️  No valid titles found in sample data")
            return True
        
        # Test with first 100 titles
        test_titles = title_texts[:100]
        results = extractor.extract_batch(test_titles)
        
        # Get statistics
        stats = extractor.get_extraction_statistics()
        
        print(f"\nReal Data Extraction Results:")
        print(f"  Total Processed: {stats.total_processed}")
        print(f"  Successful Extractions: {stats.successful_extractions} ({stats.success_rate:.2f}%)")
        print(f"  Terminal Comma: {stats.terminal_comma_count}")
        print(f"  Range Format: {stats.range_format_count}")
        print(f"  Bracket Format: {stats.bracket_format_count}")
        print(f"  Embedded Format: {stats.embedded_format_count}")
        print(f"  Multiple Dates: {stats.multiple_dates_count}")
        print(f"  Failed: {stats.failed_extractions}")
        
        # Check if success rate meets target
        if stats.success_rate >= 98:
            print("✅ SUCCESS: Meets 98-99% target success rate!")
        elif stats.success_rate >= 95:
            print("⚠️  GOOD: Close to target, needs minor improvement")
        else:
            print("❌ NEEDS WORK: Below target success rate")
        
        # Show some examples
        print(f"\nSample Extractions:")
        successful_results = [r for r in results if r.extracted_date_range][:5]
        for i, result in enumerate(successful_results):
            print(f"  {i+1}. {result.title[:60]}...")
            print(f"     Date: {result.extracted_date_range}, Format: {result.format_type.value}")
        
        if stats.failed_extractions > 0:
            print(f"\nSample Failed Extractions:")
            failed_results = [r for r in results if not r.extracted_date_range][:3]
            for i, result in enumerate(failed_results):
                print(f"  {i+1}. {result.title[:60]}...")
                print(f"     Reason: {result.notes}")
        
        print("✅ Real data test completed successfully!")
        
        # Close connections
        client.close()
        if 'pattern_manager' in locals():
            pattern_manager.close_connection()
        return True
        
    except Exception as e:
        print(f"⚠️  Real data test failed: {e}")
        return True  # Don't fail the whole test suite for this


if __name__ == "__main__":
    # Run main tests
    success = test_date_extractor()
    
    # Run real data test if possible
    test_with_real_data()
    
    sys.exit(0 if success else 1)