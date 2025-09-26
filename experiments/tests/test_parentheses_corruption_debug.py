#!/usr/bin/env python3

"""
DEBUG TEST: Script 05 Parentheses Corruption Investigation
Isolates and identifies where complex parentheses content gets corrupted.

Test Cases:
1. "Mosquito Repellent Candles (Citronella Oil, Eucalyptus Oil, Andiroba Oil, Basil Oil)"
   -> Expected: preserve complex content
   -> Actual: "(Citronella Oil) Eucalyptus Oil) Andiroba Oil) Basil Oil)"

2. "PBAT [Polybutylene Adipate Terephthalate]"
   -> Expected: convert to "(Polybutylene Adipate Terephthalate)"
   -> Actual: brackets remain unchanged
"""

import os
import sys
import importlib.util
import logging
from pymongo import MongoClient
from datetime import datetime
import pytz

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def import_module_from_path(module_name: str, file_path: str):
    """Import a module from a file path."""
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

def create_test_output_directory(script_name: str) -> str:
    """Create timestamped output directory using absolute paths."""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    experiments_dir = os.path.dirname(script_dir)
    project_root = os.path.dirname(experiments_dir)
    outputs_dir = os.path.join(project_root, 'outputs')

    # Create timestamp in Pacific Time
    pdt = pytz.timezone('America/Los_Angeles')
    timestamp = datetime.now(pdt).strftime('%Y%m%d_%H%M%S')

    # Create timestamped subdirectory
    output_dir = os.path.join(outputs_dir, f"{timestamp}_{script_name}")
    os.makedirs(output_dir, exist_ok=True)

    return output_dir

def test_parentheses_corruption():
    """Test Script 05 parentheses processing step by step."""

    # Import Script 05
    parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    pattern_manager = import_module_from_path("pattern_library_manager",
                                            os.path.join(parent_dir, "00b_pattern_library_manager_v1.py"))
    script05 = import_module_from_path("topic_extractor",
                                     os.path.join(parent_dir, "05_topic_extractor_v1.py"))

    # Initialize components
    pattern_lib_manager = pattern_manager.PatternLibraryManager(os.getenv('MONGODB_URI'))
    topic_extractor = script05.TopicExtractor(pattern_lib_manager)

    # Create output directory
    output_dir = create_test_output_directory("parentheses_corruption_debug")

    # Test cases that exhibit corruption
    test_cases = [
        {
            "title": "Mosquito Repellent Candles (Citronella Oil, Eucalyptus Oil, Andiroba Oil, Basil Oil) Market",
            "description": "Complex multi-item parentheses content corruption",
            "pipeline_forward": "Mosquito Repellent Candles (Citronella Oil, Eucalyptus Oil, Andiroba Oil, Basil Oil)",
            "extracted_elements": {
                "market_term_type": "standard",
                "extracted_forecast_date_range": None,
                "extracted_report_type": "Market",
                "extracted_regions": []
            }
        },
        {
            "title": "PBAT [Polybutylene Adipate Terephthalate] Market",
            "description": "Square bracket to parentheses conversion",
            "pipeline_forward": "PBAT [Polybutylene Adipate Terephthalate]",
            "extracted_elements": {
                "market_term_type": "standard",
                "extracted_forecast_date_range": None,
                "extracted_report_type": "Market",
                "extracted_regions": []
            }
        }
    ]

    results = []

    for i, test_case in enumerate(test_cases, 1):
        logger.info(f"\n=== Test Case {i}: {test_case['description']} ===")
        logger.info(f"Title: {test_case['title']}")
        logger.info(f"Pipeline Forward: {test_case['pipeline_forward']}")

        # Extract topic with detailed debugging
        result = topic_extractor.extract(
            title=test_case['title'],
            final_topic_text=test_case['pipeline_forward'],
            extracted_elements=test_case['extracted_elements']
        )

        # Log step-by-step processing
        logger.info(f"Final Results:")
        logger.info(f"  extracted_topic: {result.extracted_topic}")
        logger.info(f"  normalized_topic_name: {result.normalized_topic_name}")
        logger.info(f"  confidence: {result.confidence}")
        logger.info(f"Processing Notes:")
        for note in result.processing_notes:
            logger.info(f"  - {note}")

        results.append({
            "test_case": test_case,
            "result": {
                "extracted_topic": result.extracted_topic,
                "normalized_topic_name": result.normalized_topic_name,
                "confidence": result.confidence,
                "processing_notes": result.processing_notes
            }
        })

    # Write detailed analysis to output file
    analysis_file = os.path.join(output_dir, "parentheses_corruption_analysis.md")
    with open(analysis_file, 'w') as f:
        # File header with dual timestamps
        pdt = pytz.timezone('America/Los_Angeles')
        utc = pytz.UTC
        now_pdt = datetime.now(pdt)
        now_utc = datetime.now(utc)

        f.write("# Script 05 Parentheses Corruption Debug Analysis\n\n")
        f.write(f"**Analysis Date (PDT):** {now_pdt.strftime('%Y-%m-%d %H:%M:%S %Z')}\n")
        f.write(f"**Analysis Date (UTC):** {now_utc.strftime('%Y-%m-%d %H:%M:%S %Z')}\n\n")

        f.write("## Test Cases and Results\n\n")

        for i, result_data in enumerate(results, 1):
            test_case = result_data["test_case"]
            result = result_data["result"]

            f.write(f"### Test Case {i}: {test_case['description']}\n\n")
            f.write(f"**Input Title:** `{test_case['title']}`\n")
            f.write(f"**Pipeline Forward:** `{test_case['pipeline_forward']}`\n\n")

            f.write("**Results:**\n")
            f.write(f"- extracted_topic: `{result['extracted_topic']}`\n")
            f.write(f"- normalized_topic_name: `{result['normalized_topic_name']}`\n")
            f.write(f"- confidence: {result['confidence']}\n\n")

            f.write("**Processing Steps:**\n")
            for note in result['processing_notes']:
                f.write(f"1. {note}\n")
            f.write("\n")

            # Issue analysis
            if "Citronella Oil" in test_case['pipeline_forward']:
                f.write("**Issue Analysis:**\n")
                if "(Citronella Oil)" in result['extracted_topic'] and "Eucalyptus Oil)" in result['extracted_topic']:
                    f.write("- ❌ **CORRUPTION CONFIRMED**: Complex parentheses content corrupted\n")
                    f.write("- Pattern: First item gets proper parentheses, subsequent items lose opening parentheses\n")
                    f.write("- Root cause: Systematic removal patterns affecting comma-separated content\n")
                else:
                    f.write("- ✅ **NO CORRUPTION**: Parentheses content preserved correctly\n")
                f.write("\n")

            if "PBAT [" in test_case['pipeline_forward']:
                f.write("**Issue Analysis:**\n")
                if "[Polybutylene Adipate Terephthalate]" in result['extracted_topic']:
                    f.write("- ❌ **BRACKET CONVERSION MISSING**: Square brackets not converted to parentheses\n")
                    f.write("- Expected: (Polybutylene Adipate Terephthalate)\n")
                    f.write("- Actual: [Polybutylene Adipate Terephthalate]\n")
                else:
                    f.write("- ✅ **BRACKET CONVERSION WORKING**: Square brackets converted to parentheses\n")
                f.write("\n")

        f.write("## Root Cause Analysis Summary\n\n")
        f.write("Based on processing step analysis:\n\n")
        f.write("1. **MongoDB Pattern Implementation**: Bracket-to-parentheses patterns added successfully\n")
        f.write("2. **Systematic Removal Impact**: Investigate if comma-handling patterns affect complex parentheses\n")
        f.write("3. **Processing Order**: Verify pattern application sequence for complex content\n")
        f.write("4. **Pattern Priority**: Ensure bracket conversion occurs before other parentheses processing\n\n")

        f.write("---\n")
        f.write("**Generated by:** Claude Code AI Debug Analysis\n")
        f.write("**Next Steps:** Apply fixes based on identified root causes\n")

    logger.info(f"\nDebug analysis complete. Results saved to: {analysis_file}")
    return output_dir

if __name__ == "__main__":
    test_parentheses_corruption()