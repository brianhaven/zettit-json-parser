#!/usr/bin/env python3
"""Debug single title processing"""

import os
import sys
import importlib.util
from pymongo import MongoClient
from dotenv import load_dotenv

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Load environment variables
load_dotenv()

# Import modules dynamically
def import_module_from_path(module_name: str, file_path: str):
    """Import a module from a file path."""
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

# Import all required modules
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

pattern_manager = import_module_from_path("pattern_library_manager",
                                         os.path.join(parent_dir, "00b_pattern_library_manager_v1.py"))
script01 = import_module_from_path("market_classifier",
                                  os.path.join(parent_dir, "01_market_term_classifier_v1.py"))
script02 = import_module_from_path("date_extractor",
                                  os.path.join(parent_dir, "02_date_extractor_v1.py"))
script03 = import_module_from_path("report_extractor",
                                  os.path.join(parent_dir, "03_report_type_extractor_v4.py"))
script04 = import_module_from_path("geo_detector",
                                  os.path.join(parent_dir, "04_geographic_entity_detector_v2.py"))
script05 = import_module_from_path("topic_extractor",
                                  os.path.join(parent_dir, "05_topic_extractor_v1.py"))

# Initialize PatternLibraryManager
pattern_lib_manager = pattern_manager.PatternLibraryManager(os.getenv('MONGODB_URI'))

# Initialize all components
market_classifier = script01.MarketTermClassifier(pattern_lib_manager)
date_extractor = script02.EnhancedDateExtractor(pattern_lib_manager)
report_extractor = script03.PureDictionaryReportTypeExtractor(pattern_lib_manager)
geo_detector = script04.GeographicEntityDetector(pattern_lib_manager)
topic_extractor = script05.TopicExtractor(pattern_lib_manager)

# Test a single title
title = "Automotive Shielding Market Size And Share [2023 Report]"

print(f"Original Title: {title}")
print(f"Title repr: {repr(title)}")
print()

# Step 1: Market classification
market_result = market_classifier.classify(title)
print(f"Step 1 - Market Classification:")
print(f"  Result: {market_result.title}")
print(f"  Type: {market_result.market_type}")
print()

# Step 2: Date extraction
date_result = date_extractor.extract(market_result.title)
print(f"Step 2 - Date Extraction:")
print(f"  Result: {date_result.title}")
print(f"  Date: {date_result.extracted_date_range}")
print()

# Step 3: Report type extraction
report_result = report_extractor.extract(date_result.title, market_result.market_type)
print(f"Step 3 - Report Type Extraction:")
print(f"  Result: [{report_result.title}]")
print(f"  Result repr: {repr(report_result.title)}")
print(f"  Report Type: {report_result.extracted_report_type}")
print(f"  Report Type repr: {repr(report_result.extracted_report_type)}")
print()

# Step 4: Geographic detection
geo_result = geo_detector.extract_geographic_entities(report_result.title)
print(f"Step 4 - Geographic Detection:")
print(f"  Result: [{geo_result.title}]")
print(f"  Result repr: {repr(geo_result.title)}")
print(f"  Regions: {geo_result.extracted_regions}")
print()

# Step 5: Topic extraction
topic_result = topic_extractor.extract(
    geo_result.title,
    extracted_elements={
        'dates': [date_result.extracted_date_range] if date_result.extracted_date_range else [],
        'report_types': [report_result.extracted_report_type] if report_result.extracted_report_type else [],
        'regions': geo_result.extracted_regions,
        'market_type': market_result.market_type
    }
)
print(f"Step 5 - Topic Extraction:")
print(f"  Input: [{geo_result.title}]")
print(f"  Topic: [{topic_result.extracted_topic}]")
print(f"  Topic repr: {repr(topic_result.extracted_topic)}")
print(f"  Normalized: {topic_result.normalized_topic_name}")

# Check for double spaces
topic = topic_result.extracted_topic
print(f"\nDouble space check:")
print(f"  '  ' in topic: {'  ' in topic}")
print(f"  Topic chars: {[ord(c) for c in topic]}")

# Check processing notes
print(f"\nProcessing notes:")
for note in topic_result.processing_notes:
    print(f"  - {note}")