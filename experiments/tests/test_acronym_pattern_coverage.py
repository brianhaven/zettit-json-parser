#!/usr/bin/env python3
"""
Acronym Pattern Coverage Test
Validates each of the 6 acronym_embedded patterns added to MongoDB individually
"""

import os
import json
import importlib.util
from datetime import datetime
from dotenv import load_dotenv
from pymongo import MongoClient

# Load environment variables
load_dotenv()

def connect_to_mongodb():
    """Connect to MongoDB and return patterns collection."""
    try:
        mongodb_uri = os.getenv('MONGODB_URI')
        client = MongoClient(mongodb_uri, serverSelectionTimeoutMS=10000)
        client.admin.command('ping')
        
        db = client['deathstar']
        patterns_collection = db['pattern_libraries']
        
        print("✅ Connected to MongoDB")
        return client, patterns_collection
        
    except Exception as e:
        print(f"❌ MongoDB connection failed: {e}")
        return None, None

def load_acronym_patterns(patterns_collection):
    """Load acronym_embedded patterns from MongoDB."""
    try:
        cursor = patterns_collection.find({
            "type": "report_type",
            "format_type": "acronym_embedded", 
            "active": True
        })
        
        patterns = list(cursor)
        print(f"✅ Loaded {len(patterns)} acronym_embedded patterns from database")
        return patterns
        
    except Exception as e:
        print(f"❌ Failed to load acronym patterns: {e}")
        return []

def create_test_cases_for_patterns(patterns):
    """Create test cases dynamically based on pattern structure from database."""
    test_cases = []
    
    for pattern in patterns:
        pattern_regex = pattern.get('pattern', '')
        base_type = pattern.get('base_type', 'Market Report')
        term = pattern.get('term', '')
        
        print(f"   📋 Creating test cases for pattern: {term}")
        print(f"      Regex: {pattern_regex}")
        
        # Generate test titles dynamically based on pattern structure
        generated_tests = []
        
        # Create test cases based on successful working examples
        if pattern_regex == r'\bMarket\s+Size,\s+([A-Z]{2,6})\s+Industry\s+Report(?:\s*$|[,.])':
            # "Market Size, (ACRONYM) Industry Report" structure
            generated_tests = [
                "Directed Energy Weapons Market Size, DEW Industry Report, 2025",
                "Fluorinated Ethylene Propylene Market Size, FEP Industry Report, 2025",
                "Test Technology Market Size, TTM Industry Report, 2025"
            ]
        elif pattern_regex == r'\bMarket,\s+([A-Z]{2,6})\s+Industry\s+Report(?:\s*$|[,.])':
            # "Market, (ACRONYM) Industry Report" structure  
            generated_tests = [
                "Dynamic Random Access Memory Market, DRAM Industry Report, 2025",
                "Fatty Methyl Ester Sulfonate Market, FMES Industry Report, 2025",
                "Test Technology Market, TTM Industry Report, 2025"
            ]
        elif pattern_regex == r'\bMarket\s+Size,\s+Share,\s+Global\s+([A-Z]{2,6})\s+Industry\s+Report(?:\s*$|[,.])':
            # "Market Size, Share, Global (ACRONYM) Industry Report"
            generated_tests = [
                "Gas To Liquids Market Size, Share, Global GTL Industry Report, 2025",
                "Test Technology Market Size, Share, Global TTM Industry Report, 2025"
            ]
        elif 'Market.*Size.*Share.*Industry Report' in pattern_regex:
            # "Market Size, Share, (ACRONYM) Industry Report" 
            generated_tests = [
                "Test Technology Market Size, Share, TTM Industry Report, 2025",
                "Sample Materials Market Size, Share, SMM Industry Report, 2024"
            ]
        elif 'Market.*Size.*&.*Share' in pattern_regex:
            # "Market Size & Share, (ACRONYM) Industry Report"
            generated_tests = [
                "Test Technology Market Size & Share, TTM Industry Report, 2025",
                "Sample Materials Market Size & Share, SMM Industry Report, 2024"
            ]
        else:
            # Generic test case based on pattern structure analysis
            generated_tests = [
                f"Test Technology Market Report, 2025, TTM Industry, 2025",
                f"Sample Business Market Report, 2024, SBM Industry, 2024"
            ]
        
        test_cases.append({
            'pattern_data': pattern,
            'test_titles': generated_tests,
            'expected_base_type': base_type
        })
        
        print(f"      Generated {len(generated_tests)} test cases")
    
    return test_cases

def test_pattern_coverage():
    """Test each acronym pattern individually."""
    print("🔤 Acronym Pattern Coverage Test")
    print("=" * 60)
    
    # Connect to database
    client, patterns_collection = connect_to_mongodb()
    if not client:
        return
    
    # Load acronym patterns
    acronym_patterns = load_acronym_patterns(patterns_collection)
    if not acronym_patterns:
        print("❌ No acronym patterns found in database")
        return
    
    # Import Script 03 components for testing
    try:
        script_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '00b_pattern_library_manager_v1.py')
        spec = importlib.util.spec_from_file_location("pattern_manager", script_path)
        pattern_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(pattern_module)
        PatternLibraryManager = pattern_module.PatternLibraryManager
        
        script_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '03_report_type_extractor_v2.py')
        spec = importlib.util.spec_from_file_location("report_extractor", script_path)
        extractor_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(extractor_module)
        MarketAwareReportTypeExtractor = extractor_module.MarketAwareReportTypeExtractor
        
        pattern_manager = PatternLibraryManager()
        extractor = MarketAwareReportTypeExtractor(pattern_manager)
        
        print("✅ Imported Script 03 components successfully")
        
    except Exception as e:
        print(f"❌ Failed to import components: {e}")
        return
    
    # Create test cases
    test_cases = create_test_cases_for_patterns(acronym_patterns)
    print(f"🧪 Generated {len(test_cases)} pattern-specific test cases")
    
    # Test each pattern
    results = []
    successful_patterns = 0
    
    for i, test_case in enumerate(test_cases, 1):
        pattern_data = test_case['pattern_data']
        test_titles = test_case['test_titles']
        expected_base_type = test_case['expected_base_type']
        
        print(f"\n[{i}/{len(test_cases)}] Testing Pattern: {pattern_data.get('term', 'Unknown')}")
        print(f"   Pattern Regex: {pattern_data.get('pattern', 'N/A')}")
        print(f"   Expected Base Type: {expected_base_type}")
        
        pattern_successful = False
        pattern_results = []
        
        for title in test_titles:
            print(f"   Testing Title: {title}")
            
            try:
                # Remove dates for processing (simulate Script 02)
                import re
                title_no_date = re.sub(r',?\s*\d{4}(?:-\d{4})?\s*$', '', title).strip()
                
                # Test extraction
                result = extractor.extract(title_no_date, "standard")
                
                test_result = {
                    'original_title': title,
                    'title_no_date': title_no_date,
                    'extracted_report_type': result.extracted_report_type,
                    'final_report_type': result.final_report_type,
                    'pipeline_forward_text': result.title,  # Use title field which contains pipeline forward text
                    'extracted_acronym': getattr(result, 'extracted_acronym', None),
                    'confidence': result.confidence,
                    'format_type': result.format_type.value if result.format_type else "UNKNOWN",
                    'success': bool(result.final_report_type),
                    'is_acronym_match': result.format_type.value == 'acronym_embedded' if result.format_type else False
                }
                
                if test_result['is_acronym_match']:
                    pattern_successful = True
                    print(f"      ✅ MATCH: Acronym '{test_result['extracted_acronym']}' -> '{test_result['pipeline_forward_text']}'")
                else:
                    print(f"      ❌ NO MATCH: {test_result.get('notes', 'Pattern not matched')}")
                    print(f"      Format detected: {test_result['format_type']}")
                
                pattern_results.append(test_result)
                
            except Exception as e:
                print(f"      ❌ ERROR: {e}")
                pattern_results.append({
                    'original_title': title,
                    'error': str(e),
                    'success': False,
                    'is_acronym_match': False
                })
        
        if pattern_successful:
            successful_patterns += 1
        
        results.append({
            'pattern_info': pattern_data,
            'expected_base_type': expected_base_type,
            'test_results': pattern_results,
            'pattern_successful': pattern_successful
        })
    
    # Generate output
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    timestamp_readable_pdt = datetime.now().strftime("%Y-%m-%d %H:%M:%S PDT")
    timestamp_readable_utc = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
    
    output_dir = os.path.join(os.path.dirname(__file__), "../outputs")
    os.makedirs(output_dir, exist_ok=True)
    
    # Generate JSON results
    json_output = {
        "analysis_metadata": {
            "analysis_date_pdt": timestamp_readable_pdt,
            "analysis_date_utc": timestamp_readable_utc,
            "test_type": "acronym_pattern_coverage_validation",
            "total_patterns_tested": len(test_cases),
            "successful_patterns": successful_patterns
        },
        "pattern_coverage_results": results,
        "summary": {
            "patterns_loaded": len(acronym_patterns),
            "patterns_tested": len(test_cases),
            "patterns_successful": successful_patterns,
            "coverage_rate": f"{(successful_patterns / len(test_cases) * 100):.1f}%" if test_cases else "0%"
        }
    }
    
    json_file = os.path.join(output_dir, f"{timestamp}_acronym_pattern_coverage.json")
    with open(json_file, 'w') as f:
        json.dump(json_output, f, indent=2, default=str)
    
    # Generate summary
    summary_file = os.path.join(output_dir, f"{timestamp}_acronym_pattern_coverage_summary.txt")
    with open(summary_file, 'w') as f:
        f.write("Acronym Pattern Coverage Test Results\n")
        f.write(f"Analysis Date (PDT): {timestamp_readable_pdt}\n")
        f.write(f"Analysis Date (UTC): {timestamp_readable_utc}\n")
        f.write("=" * 60 + "\n\n")
        
        f.write("📊 PATTERN COVERAGE SUMMARY:\n")
        f.write(f"• Patterns Loaded from Database: {len(acronym_patterns)}\n")
        f.write(f"• Patterns Tested: {len(test_cases)}\n")
        f.write(f"• Patterns Successful: {successful_patterns}\n")
        f.write(f"• Coverage Rate: {(successful_patterns / len(test_cases) * 100):.1f}%\n\n")
        
        f.write("🔤 INDIVIDUAL PATTERN RESULTS:\n")
        for i, result in enumerate(results, 1):
            pattern_info = result['pattern_info']
            status = "✅ SUCCESS" if result['pattern_successful'] else "❌ FAILED"
            
            f.write(f"{i}. {status}: {pattern_info.get('term', 'Unknown Pattern')}\n")
            f.write(f"   Pattern: {pattern_info.get('pattern', 'N/A')}\n")
            f.write(f"   Base Type: {result['expected_base_type']}\n")
            
            successful_tests = [t for t in result['test_results'] if t.get('is_acronym_match', False)]
            if successful_tests:
                f.write(f"   Successful Test Cases:\n")
                for test in successful_tests:
                    f.write(f"     • {test['original_title']}\n")
                    f.write(f"       → Acronym: {test.get('extracted_acronym', 'N/A')}\n")
            f.write("\n")
    
    print(f"\n🎯 PATTERN COVERAGE TEST COMPLETE:")
    print(f"   📄 JSON Results: {json_file}")
    print(f"   📋 Summary Report: {summary_file}")
    print(f"   🏆 Coverage Rate: {(successful_patterns / len(test_cases) * 100):.1f}%")
    print(f"   ✅ Successful Patterns: {successful_patterns}/{len(test_cases)}")
    
    # Close connections
    client.close()
    extractor.close_connection()

if __name__ == "__main__":
    test_pattern_coverage()