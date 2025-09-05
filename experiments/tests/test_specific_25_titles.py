#!/usr/bin/env python3
"""
Test Specific 25 Titles - Script 03 v3 Validation
=================================================

Test Script 03 v3 with the specific 25 titles provided by the user.
"""

import os
import sys
from dotenv import load_dotenv
import importlib.util

load_dotenv()
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def import_module_from_path(module_name: str, file_path: str):
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

def test_specific_titles():
    """Test Script 03 v3 with specific titles provided by user."""
    
    # Import required modules
    current_dir = os.path.dirname(os.path.abspath(__file__))
    pattern_manager = import_module_from_path("pattern_library_manager", 
                                            os.path.join(current_dir, "00b_pattern_library_manager_v1.py"))
    script01 = import_module_from_path("market_classifier", 
                                     os.path.join(current_dir, "01_market_term_classifier_v1.py"))
    script03v3 = import_module_from_path("report_extractor_v3",
                                       os.path.join(current_dir, "03_report_type_extractor_v3.py"))
    
    # Initialize components
    pattern_lib_manager = pattern_manager.PatternLibraryManager(os.getenv('MONGODB_URI'))
    market_classifier = script01.MarketTermClassifier(pattern_lib_manager)
    report_extractor = script03v3.DictionaryBasedReportTypeExtractor(pattern_lib_manager)
    
    # Specific test titles provided by user
    test_titles = [
        "Carbon Black Market For Textile Fibers Growth Report",
        "Material Handling Equipment Market In Biomass Power Plant Report",
        "Amino Acids Market for Agronomic Applications",
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
        "Electric Tables Market for Physical Therapy, Examination, and Operating",  # Duplicate
        "Rice Straw Market for Silica Production",
        "High Pulsed Power Market in Well Intervention",
        "Lignin Market for Carbon Fiber and Carbon Nanofiber Industry Anaalysis",
        "PET Foam Market for Structural Composites",
        "Middle East & North Africa Diesel Generator Market in Telecom DG Industry"
    ]
    
    print("=" * 80)
    print("SCRIPT 03 v3 TEST - USER-PROVIDED 25 TITLES")
    print("=" * 80)
    print()
    
    for i, title in enumerate(test_titles, 1):
        print(f"Title {i:2d}: {title}")
        
        try:
            # Step 1: Market classification
            market_result = market_classifier.classify(title)
            market_type = market_result.market_type
            
            # Step 2: Report type extraction
            report_result = report_extractor.extract(title, market_type)
            
            # Display results
            print(f"  Market Type: {market_type}")
            print(f"  Report Type: '{report_result.extracted_report_type}'")
            print(f"  Pipeline Forward: '{report_result.title}'")
            print()
            
        except Exception as e:
            print(f"  ERROR: {e}")
            print()
    
    print("=" * 80)
    print("TEST COMPLETE")
    print("=" * 80)

if __name__ == "__main__":
    test_specific_titles()