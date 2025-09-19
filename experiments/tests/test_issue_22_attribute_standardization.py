#!/usr/bin/env python3
"""
Test harness for GitHub Issue #22: Geographic Detector Attribute Naming Standardization

This test validates that the geographic detector uses standardized attribute names:
- confidence (not confidence_score)
- notes (not processing_notes)
- extracted_regions (kept unchanged - domain appropriate)

Author: Claude Code AI
Date: 2025-09-19
"""

import os
import sys
import json
import logging
from datetime import datetime
from typing import Dict, List
import importlib.util
from dotenv import load_dotenv

# Add parent directory for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import organized output directory manager
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
spec_output = importlib.util.spec_from_file_location("output_dir_manager",
                                                      os.path.join(parent_dir, "00c_output_directory_manager_v1.py"))
output_module = importlib.util.module_from_spec(spec_output)
spec_output.loader.exec_module(output_module)
create_organized_output_directory = output_module.create_organized_output_directory
create_output_file_header = output_module.create_output_file_header

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def import_module_from_path(module_name: str, file_path: str):
    """Import a module from a file path."""
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

def test_attribute_standardization():
    """Test that geographic detector uses standardized attribute names."""

    logger.info("=" * 80)
    logger.info("GitHub Issue #22: Geographic Detector Attribute Standardization Test")
    logger.info("=" * 80)

    # Import required modules
    pattern_manager = import_module_from_path("pattern_library_manager",
                                             os.path.join(parent_dir, "00b_pattern_library_manager_v1.py"))
    script04 = import_module_from_path("geographic_detector",
                                       os.path.join(parent_dir, "04_geographic_entity_detector_v2.py"))

    # Initialize components
    pattern_lib_manager = pattern_manager.PatternLibraryManager(os.getenv('MONGODB_URI'))
    geo_detector = script04.GeographicEntityDetector(pattern_lib_manager)

    # Test cases covering various scenarios
    test_cases = [
        {
            "title": "APAC Personal Protective Equipment",
            "description": "Single region extraction"
        },
        {
            "title": "North America and Europe Automotive Technology",
            "description": "Multiple regions with conjunction"
        },
        {
            "title": "Europe, Middle East and Africa Healthcare Systems",
            "description": "Compound region (EMEA)"
        },
        {
            "title": "Global Semiconductor Manufacturing",
            "description": "Global region"
        },
        {
            "title": "United States Canada Mexico Trade Analysis",
            "description": "Multiple individual countries"
        },
        {
            "title": "Asia Pacific and Latin America Energy Solutions",
            "description": "Two major regions"
        },
        {
            "title": "Industrial Automation Technology",
            "description": "No geographic regions"
        }
    ]

    results = []
    attribute_validation_results = []

    logger.info("\nTesting attribute standardization on geographic extraction results...")
    logger.info("-" * 80)

    for i, test in enumerate(test_cases, 1):
        logger.info(f"\nTest Case {i}: {test['title']}")
        logger.info(f"Description: {test['description']}")

        # Extract geographic entities
        result = geo_detector.extract_geographic_entities(test['title'])

        # Validate that result has standardized attributes
        validation = {
            "test_case": i,
            "title": test['title'],
            "has_confidence": hasattr(result, 'confidence'),
            "has_notes": hasattr(result, 'notes'),
            "has_extracted_regions": hasattr(result, 'extracted_regions'),
            "has_title": hasattr(result, 'title'),
            # Check that old names are NOT present
            "has_old_confidence_score": hasattr(result, 'confidence_score'),
            "has_old_processing_notes": hasattr(result, 'processing_notes'),
            "has_old_remaining_text": hasattr(result, 'remaining_text')
        }

        # Log attribute validation
        logger.info(f"  ✓ confidence attribute: {validation['has_confidence']}")
        logger.info(f"  ✓ notes attribute: {validation['has_notes']}")
        logger.info(f"  ✓ extracted_regions attribute: {validation['has_extracted_regions']}")
        logger.info(f"  ✓ title attribute: {validation['has_title']}")

        # Check for old attributes (should be False)
        if validation['has_old_confidence_score']:
            logger.error(f"  ✗ OLD confidence_score attribute still present!")
        if validation['has_old_processing_notes']:
            logger.error(f"  ✗ OLD processing_notes attribute still present!")
        if validation['has_old_remaining_text']:
            logger.error(f"  ✗ OLD remaining_text attribute still present!")

        # Store results
        attribute_validation_results.append(validation)

        # Store extraction results with new attribute names
        results.append({
            "test_case": i,
            "input": test['title'],
            "description": test['description'],
            "extracted_regions": result.extracted_regions,
            "title": result.title,
            "confidence": result.confidence,  # New standardized name
            "notes": result.notes  # New standardized name
        })

        logger.info(f"  Regions: {result.extracted_regions}")
        logger.info(f"  Remaining: {result.title}")
        logger.info(f"  Confidence: {result.confidence:.3f}")
        if result.notes:
            logger.info(f"  Notes: {result.notes}")

    # Generate summary report
    logger.info("\n" + "=" * 80)
    logger.info("ATTRIBUTE VALIDATION SUMMARY")
    logger.info("=" * 80)

    all_pass = True
    for validation in attribute_validation_results:
        test_pass = (
            validation['has_confidence'] and
            validation['has_notes'] and
            validation['has_extracted_regions'] and
            validation['has_title'] and
            not validation['has_old_confidence_score'] and
            not validation['has_old_processing_notes'] and
            not validation['has_old_remaining_text']
        )

        status = "✅ PASS" if test_pass else "❌ FAIL"
        logger.info(f"Test Case {validation['test_case']}: {status}")

        if not test_pass:
            all_pass = False
            if validation['has_old_confidence_score']:
                logger.error(f"  - Still has old 'confidence_score' attribute")
            if validation['has_old_processing_notes']:
                logger.error(f"  - Still has old 'processing_notes' attribute")
            if not validation['has_confidence']:
                logger.error(f"  - Missing standardized 'confidence' attribute")
            if not validation['has_notes']:
                logger.error(f"  - Missing standardized 'notes' attribute")

    # Save results to output directory
    output_dir = create_organized_output_directory("test_issue_22_fix")

    # Save detailed results
    results_file = os.path.join(output_dir, "attribute_standardization_results.json")
    with open(results_file, 'w') as f:
        json.dump({
            "test_name": "Issue #22 Attribute Standardization Test",
            "timestamp": datetime.now().isoformat(),
            "all_tests_passed": all_pass,
            "attribute_validation": attribute_validation_results,
            "extraction_results": results
        }, f, indent=2)

    # Save summary report
    summary_file = os.path.join(output_dir, "test_summary.md")
    with open(summary_file, 'w') as f:
        f.write(create_output_file_header("Issue #22 Fix Validation",
                                          "Geographic Detector Attribute Standardization"))
        f.write("\n\n")
        f.write("# GitHub Issue #22: Attribute Standardization Test Results\n\n")
        f.write("## Objective\n")
        f.write("Validate that Script 04 (Geographic Entity Detector) uses standardized attribute names:\n")
        f.write("- `confidence` (not `confidence_score`)\n")
        f.write("- `notes` (not `processing_notes`)\n")
        f.write("- `extracted_regions` (unchanged - domain appropriate)\n\n")

        f.write("## Test Results\n\n")
        f.write(f"**Overall Status:** {'✅ ALL TESTS PASSED' if all_pass else '❌ SOME TESTS FAILED'}\n\n")

        f.write("### Attribute Validation\n\n")
        f.write("| Test Case | Title | confidence | notes | extracted_regions | Old Attrs Present |\n")
        f.write("|-----------|-------|------------|-------|-------------------|-------------------|\n")

        for val in attribute_validation_results:
            old_attrs = []
            if val['has_old_confidence_score']:
                old_attrs.append('confidence_score')
            if val['has_old_processing_notes']:
                old_attrs.append('processing_notes')
            if val['has_old_remaining_text']:
                old_attrs.append('remaining_text')

            old_attrs_str = ', '.join(old_attrs) if old_attrs else 'None'

            f.write(f"| {val['test_case']} | {val['title'][:30]}... | ")
            f.write(f"{'✅' if val['has_confidence'] else '❌'} | ")
            f.write(f"{'✅' if val['has_notes'] else '❌'} | ")
            f.write(f"{'✅' if val['has_extracted_regions'] else '❌'} | ")
            f.write(f"{old_attrs_str} |\n")

        f.write("\n### Extraction Results (with new attributes)\n\n")
        f.write("| Test | Input | Regions | Remaining | Confidence | Notes |\n")
        f.write("|------|-------|---------|-----------|------------|-------|\n")

        for r in results:
            regions_str = ', '.join(r['extracted_regions']) if r['extracted_regions'] else 'None'
            notes_str = r['notes'][:30] + '...' if len(r['notes']) > 30 else r['notes']
            f.write(f"| {r['test_case']} | {r['input'][:25]}... | {regions_str} | ")
            f.write(f"{r['title'][:20]}... | {r['confidence']:.3f} | {notes_str} |\n")

        f.write("\n## Implementation Summary\n\n")
        f.write("### Changes Made:\n")
        f.write("1. ✅ Changed `confidence_score` → `confidence` in `GeographicExtractionResult` class\n")
        f.write("2. ✅ Changed `processing_notes` → `notes` in `GeographicExtractionResult` class\n")
        f.write("3. ✅ Kept `extracted_regions` unchanged (domain-appropriate naming)\n")
        f.write("4. ✅ Updated all references throughout the script\n\n")

        f.write("### Benefits:\n")
        f.write("- **Consistency:** All extractors now use `confidence` attribute\n")
        f.write("- **Developer Experience:** Standardized naming reduces confusion\n")
        f.write("- **Low Risk:** Only 2 attributes changed, minimal impact\n")
        f.write("- **Domain Preservation:** Keeps business-appropriate 'regions' terminology\n\n")

        f.write("### Files Modified:\n")
        f.write("- `04_geographic_entity_detector_v2.py`: Main implementation\n\n")

        f.write("### Next Steps:\n")
        f.write("1. Update test files that reference old attribute names\n")
        f.write("2. Run full pipeline integration tests\n")
        f.write("3. Update documentation if needed\n\n")

        f.write("---\n")
        f.write("**Implementation:** Claude Code AI\n")
        f.write(f"**Status:** {'✅ Issue #22 Resolved' if all_pass else '⚠️ Further fixes needed'}\n")

    # Print final status
    logger.info("\n" + "=" * 80)
    if all_pass:
        logger.info("✅ SUCCESS: All attribute standardization tests passed!")
        logger.info("Issue #22 fix has been successfully implemented.")
    else:
        logger.error("❌ FAILURE: Some attribute standardization tests failed.")
        logger.error("Please review the results and fix any remaining issues.")
    logger.info("=" * 80)

    logger.info(f"\nResults saved to: {output_dir}")

    # Close database connection
    pattern_lib_manager.close_connection()

    return all_pass

if __name__ == "__main__":
    success = test_attribute_standardization()
    sys.exit(0 if success else 1)