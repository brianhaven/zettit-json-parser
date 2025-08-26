#!/usr/bin/env python3
"""
Comprehensive Pipeline Validation for Acronym Processing
Tests acronym functionality through full pipeline (01→02→03) with real database sampling
"""

import os
import sys
import json
import importlib.util
from datetime import datetime
from typing import Dict, List, Tuple
from dotenv import load_dotenv
from pymongo import MongoClient

# Load environment variables
load_dotenv()

def import_script(script_name: str, module_name: str):
    """Import a script as a module."""
    script_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), script_name)
    spec = importlib.util.spec_from_file_location(module_name, script_path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module

def connect_to_mongodb():
    """Connect to MongoDB and return relevant collections."""
    try:
        mongodb_uri = os.getenv('MONGODB_URI')
        client = MongoClient(mongodb_uri, serverSelectionTimeoutMS=10000)
        client.admin.command('ping')
        
        db = client['deathstar']
        markets_raw = db['markets_raw']
        patterns_collection = db['pattern_libraries']
        
        print("✅ Connected to MongoDB")
        return client, markets_raw, patterns_collection
        
    except Exception as e:
        print(f"❌ MongoDB connection failed: {e}")
        return None, None, None

def get_acronym_test_cases(patterns_collection) -> List[Tuple[str, str]]:
    """Generate test cases dynamically based on acronym patterns in database."""
    try:
        # Load acronym patterns from database
        cursor = patterns_collection.find({
            "type": "report_type",
            "format_type": "acronym_embedded",
            "active": True
        })
        
        acronym_patterns = list(cursor)
        print(f"✅ Found {len(acronym_patterns)} acronym patterns in database")
        
        # Generate test cases based on patterns
        test_cases = []
        
        for pattern in acronym_patterns:
            pattern_regex = pattern.get('pattern', '')
            base_type = pattern.get('base_type', 'Market Report')
            term = pattern.get('term', 'Unknown')
            
            print(f"   📋 Generating test case for pattern: {term}")
            
            # Create test titles that should match this pattern
            # Use placeholder acronyms that fit the pattern structure
            if 'Market Size' in pattern_regex:
                test_cases.extend([
                    (f"Test Technology Market Size, ABC Industry Report, 2025", "standard"),
                    (f"Sample Materials Market Size, XYZ Industry Report, 2024", "standard")
                ])
            elif 'Market.*Industry Report' in pattern_regex:
                test_cases.extend([
                    (f"Example Technology Market, DEF Industry Report, 2025", "standard"),
                    (f"Test Solutions Market, GHI Industry Report, 2024", "standard")
                ])
            else:
                # Generic test case based on base type
                test_cases.append((f"Generic {base_type}, JKL Industry Report, 2025", "standard"))
        
        # Add a few market term test cases for cross-workflow validation
        test_cases.extend([
            ("Test Market in Technology Analysis, 2025", "market_in"),
            ("Sample Market for Healthcare Report, 2024", "market_for"),
        ])
        
        # Add edge cases without acronyms to ensure no false positives
        test_cases.extend([
            ("Standard Market Analysis Report, 2025", "standard"),
            ("Regular Market Research Study, 2024", "standard"),
        ])
        
        print(f"✅ Generated {len(test_cases)} test cases from database patterns")
        return test_cases
        
    except Exception as e:
        print(f"❌ Failed to generate test cases from database: {e}")
        # Minimal fallback test cases
        return [
            ("Test Market Analysis Report, 2025", "standard"),
            ("Sample Market Research Study, 2024", "standard"),
        ]

def sample_database_titles(markets_raw, sample_size: int = 100) -> List[Tuple[str, str]]:
    """Sample real titles from database that historically have high success rates."""
    try:
        # Get a sample of titles that typically work well
        sample_pipeline = [
            {"$match": {
                "report_title": {"$regex": "Market.*Report|Market.*Analysis|Market.*Study", "$options": "i"},
                "report_title": {"$not": {"$regex": "DEW|DMFC|DRAM|FMES|FEP|GTL|PVC", "$options": "i"}}  # Exclude existing acronyms
            }},
            {"$sample": {"size": sample_size}},
            {"$project": {"report_title": 1, "_id": 0}}
        ]
        
        cursor = markets_raw.aggregate(sample_pipeline)
        sample_titles = []
        
        for doc in cursor:
            title = doc.get('report_title', '').strip()
            if title:
                # Classify market type based on patterns
                market_type = "standard"  # Default
                if "market in " in title.lower():
                    market_type = "market_in"
                elif "market for " in title.lower():
                    market_type = "market_for"
                elif "market by " in title.lower():
                    market_type = "market_by"
                    
                sample_titles.append((title, market_type))
        
        print(f"✅ Sampled {len(sample_titles)} titles from database")
        return sample_titles
        
    except Exception as e:
        print(f"❌ Failed to sample database titles: {e}")
        return []

def run_full_pipeline_test(title: str, market_type: str, components: Dict) -> Dict:
    """Run a title through the full pipeline (01→02→03)."""
    try:
        # Stage 1: Market Term Classification (01)
        market_classifier = components['market_classifier']
        classification_result = market_classifier.classify_title(title)
        classified_type = classification_result.get('classification', market_type)
        
        # Stage 2: Date Extraction (02) 
        date_extractor = components['date_extractor']
        date_result = date_extractor.extract_date(title)
        title_no_date = date_result.get('title_without_date', title)
        extracted_date = date_result.get('extracted_date', '')
        
        # Stage 3: Report Type Extraction (03)
        report_extractor = components['report_extractor']
        report_result = report_extractor.extract(title_no_date, classified_type)
        
        # Compile full result
        pipeline_result = {
            'original_title': title,
            'expected_market_type': market_type,
            'classified_market_type': classified_type,
            'extracted_date': extracted_date,
            'title_after_date_removal': title_no_date,
            'extracted_report_type': report_result.extracted_report_type,
            'final_report_type': report_result.final_report_type,
            'pipeline_forward_text': report_result.title,  # Use title field which contains pipeline forward text
            'confidence': report_result.confidence,
            'format_type': report_result.format_type.value if report_result.format_type else "UNKNOWN",
            'processing_workflow': report_result.processing_workflow,
            'extracted_acronym': getattr(report_result, 'extracted_acronym', None),
            'is_acronym_match': bool(getattr(report_result, 'extracted_acronym', None)),
            'success': bool(report_result.final_report_type),
            'notes': report_result.notes
        }
        
        return pipeline_result
        
    except Exception as e:
        return {
            'original_title': title,
            'expected_market_type': market_type,
            'error': str(e),
            'success': False,
            'notes': f"Pipeline processing failed: {e}"
        }

def main():
    """Run comprehensive pipeline validation."""
    print("🧪 Comprehensive Pipeline Validation for Acronym Processing")
    print("=" * 80)
    
    # Connect to database
    client, markets_raw, patterns_collection = connect_to_mongodb()
    if not client:
        return
    
    # Import required components
    print("\n📦 Importing pipeline components...")
    try:
        # Import Script 01 (Market Term Classifier)
        script01 = import_script("01_market_term_classifier_v1.py", "market_classifier")
        
        # Import Script 02 (Date Extractor) 
        script02 = import_script("02_date_extractor_v1.py", "date_extractor")
        
        # Import Script 03 components
        script00b = import_script("00b_pattern_library_manager_v1.py", "pattern_manager")
        script03 = import_script("03_report_type_extractor_v2.py", "report_extractor")
        
        # Initialize components
        PatternLibraryManager = script00b.PatternLibraryManager
        MarketTermClassifier = script01.MarketTermClassifier
        DateExtractor = script02.DateExtractor
        MarketAwareReportTypeExtractor = script03.MarketAwareReportTypeExtractor
        
        pattern_manager = PatternLibraryManager()
        market_classifier = MarketTermClassifier(pattern_manager)
        date_extractor = DateExtractor(pattern_manager)
        report_extractor = MarketAwareReportTypeExtractor(pattern_manager)
        
        components = {
            'pattern_manager': pattern_manager,
            'market_classifier': market_classifier,
            'date_extractor': date_extractor,
            'report_extractor': report_extractor
        }
        
        print("✅ All pipeline components imported successfully")
        
    except Exception as e:
        print(f"❌ Failed to import pipeline components: {e}")
        return
    
    # Generate test cases
    print("\n📋 Generating test cases...")
    
    # Phase 1: Curated acronym test cases from database patterns
    acronym_test_cases = get_acronym_test_cases(patterns_collection)
    print(f"✅ Generated {len(acronym_test_cases)} database-driven acronym test cases")
    
    # Phase 2: Sample real database titles
    database_sample = sample_database_titles(markets_raw, sample_size=50)  # Smaller sample for testing
    print(f"✅ Sampled {len(database_sample)} database titles")
    
    # Combine test cases
    all_test_cases = acronym_test_cases + database_sample
    print(f"📊 Total test cases: {len(all_test_cases)} ({len(acronym_test_cases)} acronym + {len(database_sample)} database)")
    
    # Run pipeline tests
    print(f"\n🚀 Running full pipeline tests...")
    results = []
    acronym_results = []
    successful_results = 0
    
    for i, (title, market_type) in enumerate(all_test_cases, 1):
        print(f"\n[{i}/{len(all_test_cases)}] Testing: {title[:80]}...")
        
        result = run_full_pipeline_test(title, market_type, components)
        results.append(result)
        
        if result.get('success', False):
            successful_results += 1
            
        if result.get('is_acronym_match', False):
            acronym_results.append(result)
            print(f"   ✅ ACRONYM: {result.get('extracted_acronym')} -> '{result.get('pipeline_forward_text')}'")
        elif result.get('success', False):
            print(f"   ✅ SUCCESS: {result.get('final_report_type')} -> '{result.get('pipeline_forward_text')}'")
        else:
            print(f"   ❌ FAILED: {result.get('notes', 'Unknown error')}")
    
    # Generate comprehensive output
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
            "test_type": "full_pipeline_acronym_validation",
            "total_test_cases": len(all_test_cases),
            "acronym_test_cases": len(acronym_test_cases),
            "database_sample_size": len(database_sample),
            "acronym_matches_found": len(acronym_results)
        },
        "pipeline_performance": {
            "total_processed": len(all_test_cases),
            "successful_extractions": successful_results,
            "success_rate": f"{(successful_results / len(all_test_cases) * 100):.1f}%",
            "acronym_processing_count": len(acronym_results)
        },
        "test_results": results,
        "acronym_specific_results": acronym_results
    }
    
    json_file = os.path.join(output_dir, f"{timestamp}_full_pipeline_acronym_validation.json")
    with open(json_file, 'w') as f:
        json.dump(json_output, f, indent=2, default=str)
    
    # Generate human-readable summary
    summary_file = os.path.join(output_dir, f"{timestamp}_full_pipeline_acronym_validation_summary.txt")
    with open(summary_file, 'w') as f:
        f.write("Full Pipeline Acronym Validation Results\n")
        f.write(f"Analysis Date (PDT): {timestamp_readable_pdt}\n")
        f.write(f"Analysis Date (UTC): {timestamp_readable_utc}\n")
        f.write("=" * 80 + "\n\n")
        
        f.write("📊 PIPELINE PERFORMANCE SUMMARY:\n")
        f.write(f"• Total Test Cases: {len(all_test_cases)}\n")
        f.write(f"• Successful Extractions: {successful_results}\n")
        f.write(f"• Success Rate: {(successful_results / len(all_test_cases) * 100):.1f}%\n")
        f.write(f"• Acronym Matches Found: {len(acronym_results)}\n")
        f.write(f"• Database Regression Check: {len(database_sample)} titles validated\n\n")
        
        if acronym_results:
            f.write("🔤 ACRONYM PROCESSING RESULTS:\n")
            for result in acronym_results:
                f.write(f"• {result['original_title']}\n")
                f.write(f"  → Acronym: {result.get('extracted_acronym', 'N/A')}\n")
                f.write(f"  → Report Type: {result['final_report_type']}\n")
                f.write(f"  → Pipeline Forward: {result['pipeline_forward_text']}\n\n")
        
        # Failed cases analysis
        failed_results = [r for r in results if not r.get('success', False)]
        if failed_results:
            f.write(f"❌ FAILED CASES ANALYSIS ({len(failed_results)} cases):\n")
            for result in failed_results:
                f.write(f"• {result['original_title']}\n")
                f.write(f"  → Error: {result.get('notes', 'Unknown')}\n\n")
    
    # Print final summary
    print(f"\n🎯 VALIDATION COMPLETE:")
    print(f"   📄 JSON Results: {json_file}")
    print(f"   📋 Summary Report: {summary_file}")
    print(f"   🏆 Success Rate: {(successful_results / len(all_test_cases) * 100):.1f}%")
    print(f"   🔤 Acronym Matches: {len(acronym_results)}")
    print(f"   📊 Database Regression: {successful_results - len([r for r in acronym_results if r.get('success')])}/{len(database_sample)} database titles successful")
    
    # Close connections
    client.close()
    for component in components.values():
        if hasattr(component, 'close_connection'):
            component.close_connection()

if __name__ == "__main__":
    main()