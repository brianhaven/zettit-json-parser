#!/usr/bin/env python3
"""
Test Script for Git Issue #21 - Missing Keywords in Report Type Extraction
============================================================================

Tests Script 03 v3 with the 25 provided sample titles to verify extraction accuracy.
Results must match the required output exactly to be considered successful.

Branch: fix/issue-21-missing-keywords
Issue: #21 - Missing Keywords in Report Type Extraction
"""

import os
import sys
import logging
from datetime import datetime
import pytz
from typing import List, Dict, Any
import importlib.util
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def import_module_from_path(module_name: str, file_path: str):
    """Import a module from a file path."""
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

def create_output_directory() -> str:
    """Create timestamped output directory."""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    experiments_dir = os.path.dirname(script_dir)  
    project_root = os.path.dirname(experiments_dir)
    outputs_dir = os.path.join(project_root, 'outputs')
    
    # Create timestamp in Pacific Time
    pdt = pytz.timezone('America/Los_Angeles')
    timestamp = datetime.now(pdt).strftime('%Y%m%d_%H%M%S')
    
    # Create timestamped subdirectory
    output_dir = os.path.join(outputs_dir, f"{timestamp}_issue_21_test_results")
    os.makedirs(output_dir, exist_ok=True)
    
    return output_dir

# Sample titles from Issue #21 requirements
SAMPLE_TITLES = [
    "Carbon Black Market For Textile Fibers Growth Report",
    "Material Handling Equipment Market In Biomass Power Plant Report", 
    "Amino Acids Market by Agronomic Applications",
    "Battery Pack Modules Market for EVs",
    "Advanced Nanomaterials Market for Environmental Detection and Remediation",
    "High Voltage Relays Market for EVs Growth Report",
    "Superabsorbent Polymer Market for Agriculture Industry Growth",
    "Telematics Market for Off-highway Vehicles",
    "Functional Cosmetics Market for Skin Care Application Trends & Analysis FCSC Outlook",
    "Impregnation Sealants Market for Electronics",
    "Sulfur, Arsine, and Mercury Remover Market in Oil & Gas Industry",
    "High Purity Quartz Sand Market for UVC Lighting Share and Size Outlook",
    "Cloud Computing Market in Healthcare Industy",
    "EMEA Industrial Coatings Market for Mining and Petrochemicals",
    "De-icing Systems Market for Power Transmission Cables",
    "Advanced Materials Market for Nuclear Fusion Technology",
    "Electric Tables Market for Physical Therapy, Examination, and Operating",
    "Paints Market for Non-Plastic Application",
    "Nanocapsules Market for Cosmetics Repot",
    "Electric Tables Market for Physical Therapy, Examination, and Operating",
    "Rice Straw Market for Silica Production",
    "High Pulsed Power Market in Well Intervention",
    "Lignin Market for Carbon Fiber and Carbon Nanofiber Industry Analysis",
    "PET Foam Market by Structural Composites",
    "Middle East & North Africa Diesel Generator Market in Telecom DG Industry"
]

# Required output for success
REQUIRED_OUTPUT = [
    ("Carbon Black Market For Textile Fibers Growth Report", "Market Growth Report", "Carbon Black For Textile Fibers"),
    ("Material Handling Equipment Market In Biomass Power Plant Report", "Market Report", "Material Handling Equipment In Biomass Power Plant"),
    ("Amino Acids Market by Agronomic Applications", "Market", "Amino Acids by Agronomic Applications"),
    ("Battery Pack Modules Market for EVs", "Market", "Battery Pack Modules for EVs"),
    ("Advanced Nanomaterials Market for Environmental Detection and Remediation", "Market", "Advanced Nanomaterials for Environmental Detection and Remediation"),
    ("High Voltage Relays Market for EVs Growth Report", "Market Growth Report", "High Voltage Relays for EVs"),
    ("Superabsorbent Polymer Market for Agriculture Industry Growth", "Market Industry Growth", "Superabsorbent Polymer for Agriculture"),
    ("Telematics Market for Off-highway Vehicles", "Market", "Telematics for Off-highway Vehicles"),
    ("Functional Cosmetics Market for Skin Care Application Trends & Analysis FCSC Outlook", "Market Trends & Analysis Outlook", "Functional Cosmetics for Skin Care Application FCSC"),
    ("Impregnation Sealants Market for Electronics", "Market", "Impregnation Sealants for Electronics"),
    ("Sulfur, Arsine, and Mercury Remover Market in Oil & Gas Industry", "Market Industry", "Sulfur, Arsine, and Mercury Remover in Oil & Gas"),
    ("High Purity Quartz Sand Market for UVC Lighting Share and Size Outlook", "Market Share and Size Outlook", "High Purity Quartz Sand for UVC Lighting"),
    ("Cloud Computing Market in Healthcare Industy", "Market Industy", "Cloud Computing in Healthcare"),
    ("EMEA Industrial Coatings Market for Mining and Petrochemicals", "Market", "EMEA Industrial Coatings for Mining and Petrochemicals"),
    ("De-icing Systems Market for Power Transmission Cables", "Market", "De-icing Systems for Power Transmission Cables"),
    ("Advanced Materials Market for Nuclear Fusion Technology", "Market", "Advanced Materials for Nuclear Fusion Technology"),
    ("Electric Tables Market for Physical Therapy, Examination, and Operating", "Market", "Electric Tables for Physical Therapy, Examination, and Operating"),
    ("Paints Market for Non-Plastic Application", "Market", "Paints for Non-Plastic Application"),
    ("Nanocapsules Market for Cosmetics Repot", "Market Repot", "Nanocapsules for Cosmetics"),
    ("Electric Tables Market for Physical Therapy, Examination, and Operating", "Market", "Electric Tables for Physical Therapy, Examination, and Operating"),
    ("Rice Straw Market for Silica Production", "Market", "Rice Straw for Silica Production"),
    ("High Pulsed Power Market in Well Intervention", "Market", "High Pulsed Power in Well Intervention"),
    ("Lignin Market for Carbon Fiber and Carbon Nanofiber Industry Analysis", "Market Industry Analysis", "Lignin for Carbon Fiber and Carbon Nanofiber"),
    ("PET Foam Market by Structural Composites", "Market", "PET Foam by Structural Composites"),
    ("Middle East & North Africa Diesel Generator Market in Telecom DG Industry", "Market Industry", "Middle East & North Africa Diesel Generator in Telecom DG")
]

def classify_market_term_type(title: str) -> str:
    """Simple market term classification for testing."""
    title_lower = title.lower()
    if "market for" in title_lower:
        return "market_for"
    elif "market in" in title_lower:
        return "market_in" 
    elif "market by" in title_lower:
        return "market_by"
    else:
        return "standard"

def main():
    """Test Script 03 v3 with sample titles for Issue #21."""
    print("\n" + "="*80)
    print("TESTING SCRIPT 03 V3 - GIT ISSUE #21 SAMPLE TITLES")
    print("="*80)
    
    # Setup imports
    parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    # Load pattern library manager
    try:
        pattern_manager = import_module_from_path("pattern_library_manager",
                                                os.path.join(parent_dir, "00b_pattern_library_manager_v1.py"))
        
        # Load Script 03 v3
        script03_v3 = import_module_from_path("report_type_extractor_v3",
                                            os.path.join(parent_dir, "03_report_type_extractor_v3.py"))
        
        print("✓ Successfully imported required modules")
        
    except Exception as e:
        print(f"✗ Failed to import modules: {e}")
        return
    
    # Initialize components
    try:
        from dotenv import load_dotenv
        load_dotenv()
        
        pattern_lib_manager = pattern_manager.PatternLibraryManager(os.getenv('MONGODB_URI'))
        report_extractor = script03_v3.DictionaryBasedReportTypeExtractor(pattern_lib_manager)
        
        print("✓ Successfully initialized Script 03 v3 DictionaryBasedReportTypeExtractor")
        
    except Exception as e:
        print(f"✗ Failed to initialize components: {e}")
        return
    
    # Create output directory
    output_dir = create_output_directory()
    results_file = os.path.join(output_dir, "test_results.md")
    
    print(f"✓ Output directory created: {output_dir}")
    
    # Test each title
    results = []
    success_count = 0
    total_tests = len(SAMPLE_TITLES)
    
    with open(results_file, 'w') as f:
        f.write("# Git Issue #21 - Script 03 v3 Test Results\n\n")
        f.write(f"**Test Date:** {datetime.now(pytz.timezone('America/Los_Angeles')).strftime('%Y-%m-%d %H:%M:%S PDT')}\n")
        f.write(f"**Test Date (UTC):** {datetime.now(pytz.UTC).strftime('%Y-%m-%d %H:%M:%S UTC')}\n\n")
        f.write(f"**Total Tests:** {total_tests}\n\n")
        
        for i, (title, expected_report_type, expected_pipeline) in enumerate(REQUIRED_OUTPUT, 1):
            print(f"\n[{i:2d}/{total_tests}] Testing: {title}")
            
            # Classify market term type
            market_type = classify_market_term_type(title)
            
            # Extract using Script 03 v3
            try:
                result = report_extractor.extract(title, market_type)
                
                actual_report_type = result.extracted_report_type
                actual_pipeline = result.title
                
                # Check if results match expectations
                report_type_match = actual_report_type == expected_report_type
                pipeline_match = actual_pipeline == expected_pipeline
                test_success = report_type_match and pipeline_match
                
                if test_success:
                    success_count += 1
                    status = "✓ PASS"
                else:
                    status = "✗ FAIL"
                
                print(f"    {status} - Report Type: '{actual_report_type}' | Pipeline: '{actual_pipeline}'")
                
                # Log to results file
                f.write(f"## Test {i}: {title}\n\n")
                f.write(f"**Market Type:** {market_type}\n")
                f.write(f"**Expected Report Type:** {expected_report_type}\n")
                f.write(f"**Actual Report Type:** {actual_report_type}\n")
                f.write(f"**Expected Pipeline:** {expected_pipeline}\n")
                f.write(f"**Actual Pipeline:** {actual_pipeline}\n")
                f.write(f"**Status:** {status}\n")
                f.write(f"**Confidence:** {result.confidence:.3f}\n")
                f.write(f"**Processing Time:** {result.processing_time_ms:.1f}ms\n")
                
                if not test_success:
                    f.write("**Issues:**\n")
                    if not report_type_match:
                        f.write(f"- Report type mismatch: expected '{expected_report_type}', got '{actual_report_type}'\n")
                    if not pipeline_match:
                        f.write(f"- Pipeline text mismatch: expected '{expected_pipeline}', got '{actual_pipeline}'\n")
                
                f.write("\n---\n\n")
                
                results.append({
                    'title': title,
                    'expected_report_type': expected_report_type,
                    'actual_report_type': actual_report_type,
                    'expected_pipeline': expected_pipeline,
                    'actual_pipeline': actual_pipeline,
                    'success': test_success,
                    'confidence': result.confidence
                })
                
            except Exception as e:
                print(f"    ✗ ERROR - Exception: {e}")
                f.write(f"## Test {i}: {title}\n\n")
                f.write(f"**Status:** ✗ ERROR\n")
                f.write(f"**Exception:** {str(e)}\n\n---\n\n")
                
                results.append({
                    'title': title,
                    'success': False,
                    'error': str(e)
                })
    
    # Final summary
    success_rate = (success_count / total_tests) * 100
    print(f"\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    print(f"Total Tests: {total_tests}")
    print(f"Passed: {success_count}")
    print(f"Failed: {total_tests - success_count}")
    print(f"Success Rate: {success_rate:.1f}%")
    
    if success_count == total_tests:
        print("🎉 ALL TESTS PASSED - Issue #21 is RESOLVED!")
    else:
        print(f"❌ {total_tests - success_count} tests failed - Issue #21 needs more work")
    
    print(f"\nDetailed results saved to: {results_file}")
    
    # Append summary to results file
    with open(results_file, 'a') as f:
        f.write("# Test Summary\n\n")
        f.write(f"**Total Tests:** {total_tests}\n")
        f.write(f"**Passed:** {success_count}\n") 
        f.write(f"**Failed:** {total_tests - success_count}\n")
        f.write(f"**Success Rate:** {success_rate:.1f}%\n\n")
        
        if success_count == total_tests:
            f.write("🎉 **ALL TESTS PASSED** - Git Issue #21 is RESOLVED!\n")
        else:
            f.write(f"❌ **{total_tests - success_count} tests failed** - Git Issue #21 needs more work\n")
    
    return success_count == total_tests

if __name__ == "__main__":
    main()