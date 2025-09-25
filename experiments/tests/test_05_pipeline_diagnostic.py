#!/usr/bin/env python3

"""
Script 05 Pipeline Diagnostic Test
Tests specific titles through the actual pipeline to diagnose content loss issues.
"""

import sys
import os
import importlib.util
from typing import List, Dict, Any

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def import_module_from_path(module_name: str, file_path: str):
    """Import a module from a file path."""
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

def create_output_directory(script_name: str) -> str:
    """Create timestamped output directory using absolute paths."""
    # Get absolute path to outputs directory (from /experiments/tests/ to /outputs/)
    script_dir = os.path.dirname(os.path.abspath(__file__))
    experiments_dir = os.path.dirname(script_dir)
    project_root = os.path.dirname(experiments_dir)

    # Import output manager from parent directory
    output_manager = import_module_from_path("output_manager",
                                           os.path.join(experiments_dir, "00c_output_directory_manager_v1.py"))

    return output_manager.create_organized_output_directory(script_name)

def create_file_header(script_name: str, description: str = "") -> str:
    """Create standardized file header with dual timestamps."""
    # Import output manager
    script_dir = os.path.dirname(os.path.abspath(__file__))
    experiments_dir = os.path.dirname(script_dir)
    output_manager = import_module_from_path("output_manager",
                                           os.path.join(experiments_dir, "00c_output_directory_manager_v1.py"))

    return output_manager.create_output_file_header(script_name, description)

def test_pipeline_diagnostic():
    """Test specific titles through actual pipeline to diagnose content preservation."""

    print("Script 05 Pipeline Diagnostic - Content Preservation Testing")
    print("=" * 65)

    try:
        # Import all pipeline components
        parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

        # Import pattern library manager
        pattern_manager = import_module_from_path("pattern_library_manager",
                                                os.path.join(parent_dir, "00b_pattern_library_manager_v1.py"))

        # Import pipeline scripts
        script01 = import_module_from_path("market_classifier",
                                         os.path.join(parent_dir, "01_market_term_classifier_v1.py"))
        script02 = import_module_from_path("date_extractor",
                                         os.path.join(parent_dir, "02_date_extractor_v1.py"))
        script03 = import_module_from_path("report_extractor",
                                         os.path.join(parent_dir, "03_report_type_extractor_v4.py"))
        script04 = import_module_from_path("geo_detector",
                                         os.path.join(parent_dir, "04_geographic_entity_detector_v3.py"))

        # Initialize components
        pattern_lib_manager = pattern_manager.PatternLibraryManager(os.getenv('MONGODB_URI'))

        # Initialize all scripts with pattern library manager (consistent architecture)
        market_classifier = script01.MarketTermClassifier(pattern_lib_manager)
        date_extractor = script02.EnhancedDateExtractor(pattern_lib_manager)
        report_extractor = script03.PureDictionaryReportTypeExtractor(pattern_lib_manager)
        geo_detector = script04.GeographicEntityDetector(pattern_lib_manager)

        # Test cases with specific content preservation issues
        test_cases = [
            {
                'name': "Ampersand Preservation Test",
                'title': "AI Trust, Risk & Security Management Market",
                'expected_symbols': ["&"],
                'issue': "Ampersand (&) should be preserved through pipeline"
            },
            {
                'name': "Bracket/Acronym Preservation Test",
                'title': "Fecal Immunochemical Test [FIT] Market Analysis",
                'expected_symbols': ["[FIT]"],
                'issue': "[FIT] should be preserved through pipeline"
            },
            {
                'name': "Parentheses Acronym Test",
                'title': "Natural Language Processing (NLP) Market Growth Report, 2030",
                'expected_symbols': ["(NLP)"],
                'issue': "(NLP) should be preserved through pipeline"
            }
        ]

        print("\n1. Pipeline Processing Results:")
        print("-" * 45)

        results = []

        for i, test_case in enumerate(test_cases, 1):
            print(f"\n{i}. {test_case['name']}:")
            print(f"   Original: {test_case['title']}")

            current_title = test_case['title']
            stages = []

            # Stage 1: Market Classification
            market_result = market_classifier.classify(current_title)
            current_title = market_result.title
            stages.append({
                'stage': 'Market Classification',
                'title': current_title,
                'classification': market_result.market_type,
                'confidence': market_result.confidence
            })

            # Stage 2: Date Extraction
            date_result = date_extractor.extract(current_title)
            current_title = date_result.title
            stages.append({
                'stage': 'Date Extraction',
                'title': current_title,
                'extracted': date_result.extracted_date_range,
                'confidence': date_result.confidence
            })

            # Stage 3: Report Type Extraction
            report_result = report_extractor.extract(current_title, market_result.market_type)
            current_title = report_result.title
            stages.append({
                'stage': 'Report Type Extraction',
                'title': current_title,
                'extracted': report_result.extracted_report_type,
                'confidence': report_result.confidence
            })

            # Stage 4: Geographic Detection
            geo_result = geo_detector.extract_geographic_entities(current_title)
            current_title = geo_result.title if geo_result.title else current_title
            stages.append({
                'stage': 'Geographic Detection',
                'title': current_title,
                'extracted': geo_result.extracted_regions,
                'confidence': geo_result.confidence
            })

            # Check for content preservation
            symbols_preserved = []
            symbols_lost = []

            for symbol in test_case['expected_symbols']:
                if symbol in current_title:
                    symbols_preserved.append(symbol)
                else:
                    symbols_lost.append(symbol)

            # Display stage-by-stage results
            for stage in stages:
                print(f"   {stage['stage']}: '{stage['title']}'")
                if 'extracted' in stage:
                    print(f"     → Extracted: {stage['extracted']}")
                if 'classification' in stage:
                    print(f"     → Classification: {stage['classification']}")

            print(f"   Final Pipeline Result: '{current_title}'")
            print(f"   Symbols Preserved: {symbols_preserved}")
            print(f"   Symbols Lost: {symbols_lost}")
            print(f"   Content Loss Issue: {'YES' if symbols_lost else 'NO'}")

            results.append({
                'test_case': test_case,
                'final_title': current_title,
                'stages': stages,
                'symbols_preserved': symbols_preserved,
                'symbols_lost': symbols_lost,
                'has_content_loss': bool(symbols_lost)
            })

        # Generate summary
        print("\n2. Content Preservation Analysis:")
        print("-" * 40)

        total_tests = len(test_cases)
        content_loss_count = sum(1 for r in results if r['has_content_loss'])

        print(f"Total Tests: {total_tests}")
        print(f"Content Loss Issues: {content_loss_count}/{total_tests}")
        print(f"Content Preservation Rate: {((total_tests - content_loss_count) / total_tests) * 100:.1f}%")

        if content_loss_count > 0:
            print(f"\n❌ ACTUAL PIPELINE ISSUES DETECTED:")
            for result in results:
                if result['has_content_loss']:
                    print(f"   - {result['test_case']['name']}: Lost {result['symbols_lost']}")
        else:
            print(f"\n✅ NO CONTENT LOSS: All symbols properly preserved through pipeline")

        # Save detailed report
        print("\n3. Saving Diagnostic Report:")
        print("-" * 35)

        output_dir = create_output_directory("script05_pipeline_diagnostic")

        report_content = f"""{create_file_header("script05_pipeline_diagnostic", "Pipeline content preservation diagnostic results")}

Script 05 Pipeline Diagnostic Results
{"=" * 50}

Content Preservation Analysis:
  Total Test Cases:         {total_tests}
  Content Loss Issues:      {content_loss_count}/{total_tests}
  Content Preservation:     {((total_tests - content_loss_count) / total_tests) * 100:.1f}%

Detailed Pipeline Processing Results:
{"=" * 40}
"""

        for i, result in enumerate(results, 1):
            test_case = result['test_case']
            report_content += f"""
Test {i}: {test_case['name']}
  Original Title: {test_case['title']}
  Expected Symbols: {test_case['expected_symbols']}
  Issue Description: {test_case['issue']}

  Stage-by-Stage Processing:"""

            for stage in result['stages']:
                report_content += f"""
    {stage['stage']}: '{stage['title']}'"""
                if 'extracted' in stage:
                    report_content += f"""
      → Extracted: {stage['extracted']}"""
                if 'classification' in stage:
                    report_content += f"""
      → Classification: {stage['classification']}"""

            report_content += f"""

  Final Pipeline Result: '{result['final_title']}'
  Symbols Preserved: {result['symbols_preserved']}
  Symbols Lost: {result['symbols_lost']}
  Content Loss Issue: {'YES - REQUIRES FIXING' if result['has_content_loss'] else 'NO'}
"""

        if content_loss_count > 0:
            report_content += f"""

RECOMMENDATIONS FOR GIT ISSUES:
{"=" * 30}"""

            for result in results:
                if result['has_content_loss']:
                    # Determine which stage likely caused the loss
                    original = result['test_case']['title']
                    lost_symbols = result['symbols_lost']

                    report_content += f"""

Issue: {result['test_case']['name']}
  Problem: Lost symbols {lost_symbols}
  Stage Analysis:"""

                    for j, stage in enumerate(result['stages']):
                        still_present = all(symbol in stage['title'] for symbol in lost_symbols)
                        if j > 0:  # Check if symbols were lost in this stage
                            prev_stage = result['stages'][j-1]
                            prev_present = all(symbol in prev_stage['title'] for symbol in lost_symbols)
                            if prev_present and not still_present:
                                report_content += f"""
    → CONTENT LOSS OCCURRED IN: {stage['stage']}
    → Previous stage had: {lost_symbols}
    → This stage lost: {[s for s in lost_symbols if s not in stage['title']]}"""

        else:
            report_content += f"""

CONCLUSION:
{"=" * 12}
✅ NO PIPELINE ISSUES DETECTED
All content preservation tests passed. The issues in the Script 05 test cases
were likely test data discrepancies rather than actual pipeline bugs.
"""

        # Save report
        report_file = os.path.join(output_dir, "pipeline_diagnostic_results.txt")
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report_content)

        print(f"✓ Diagnostic report saved to: {report_file}")

        # Return results for further analysis
        return {
            'total_tests': total_tests,
            'content_loss_count': content_loss_count,
            'results': results,
            'has_pipeline_issues': content_loss_count > 0
        }

    except Exception as e:
        print(f"❌ Diagnostic failed: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    diagnostic_results = test_pipeline_diagnostic()
    if diagnostic_results and diagnostic_results['has_pipeline_issues']:
        print(f"\n🔍 PIPELINE ISSUES CONFIRMED: {diagnostic_results['content_loss_count']} problems detected")
        sys.exit(1)  # Exit with error code if issues found
    else:
        print(f"\n✅ PIPELINE HEALTHY: No content preservation issues detected")
        sys.exit(0)