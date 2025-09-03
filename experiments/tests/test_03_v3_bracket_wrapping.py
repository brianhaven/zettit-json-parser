#!/usr/bin/env python3
"""
Test bracket and parentheses wrapping detection for Script 03 v3
"""

import sys
import os
from pymongo import MongoClient
from dotenv import load_dotenv
import importlib.util

# Load environment variables
load_dotenv()

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def import_module_from_path(module_name: str, file_path: str):
    """Import a module from a file path."""
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

# Import modules
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
pattern_manager = import_module_from_path("pattern_library_manager",
                                        os.path.join(parent_dir, "00b_pattern_library_manager_v1.py"))
script03v3 = import_module_from_path("report_extractor_v3",
                                   os.path.join(parent_dir, "03_report_type_extractor_v3.py"))

def test_bracket_wrapping_detection():
    """Test the bracket and parentheses wrapping detection functionality."""
    
    # Initialize components
    pattern_lib_manager = pattern_manager.PatternLibraryManager(os.getenv('MONGODB_URI'))
    report_extractor_v3 = script03v3.DictionaryBasedReportTypeExtractor(pattern_lib_manager)
    
    # Test cases with different wrapping scenarios
    test_cases = [
        {
            'title': 'Healthcare [Market Size & Share] Analysis Report 2025',
            'description': 'Normal bracketed phrase with multiple keywords'
        },
        {
            'title': 'Automotive (Market Growth) Trends Research 2025', 
            'description': 'Parenthetical phrase with keywords'
        },
        {
            'title': 'Global [Data Analytics] Market Overview Report',
            'description': 'Bracket-wrapped Data keyword'
        },
        {
            'title': 'AI (Market Research & Analysis) Industry Study',
            'description': 'Complex parenthetical phrase'
        },
        {
            'title': 'Mining Equipment Market [Size] Report 2024-2030',
            'description': 'Single bracketed keyword'
        },
        {
            'title': 'Technology (Report) Market Analysis',
            'description': 'Parenthetical single keyword'
        },
        {
            'title': 'Standard Market Analysis Report',
            'description': 'Control case - no wrapping'
        }
    ]
    
    print("Testing v3 bracket and parentheses wrapping detection:")
    print("=" * 70)
    
    for i, case in enumerate(test_cases, 1):
        title = case['title']
        description = case['description']
        
        print(f"\n{i}. {description}")
        print(f"Title: {title}")
        
        try:
            # Test the keyword detection
            keyword_result = report_extractor_v3.detect_keywords_in_title(title)
            
            print(f"Keywords found: {keyword_result.keywords_found}")
            print(f"Sequence: {keyword_result.sequence}")
            
            # Check for wrapped keywords
            wrapped_keywords = []
            for keyword in keyword_result.keywords_found:
                # Test the wrapping detection method directly
                match = report_extractor_v3._find_keyword_with_wrapping(keyword, title)
                if match and match.get('wrapped'):
                    wrapped_keywords.append({
                        'keyword': keyword,
                        'wrap_chars': match['wrap_chars'],
                        'wrapped_content': match.get('wrapped_content', ''),
                        'position': match['start']
                    })
            
            if wrapped_keywords:
                print("✅ WRAPPED KEYWORDS DETECTED:")
                for w in wrapped_keywords:
                    print(f"   - '{w['keyword']}' wrapped in {w['wrap_chars']} containing: '{w['wrapped_content']}'")
            else:
                print("📝 No wrapped keywords (normal detection)")
                
            # Now test full extraction
            result = report_extractor_v3.extract(title)
            print(f"Extracted Report Type: {result.extracted_report_type}")
            print(f"Final Topic: {result.title}")
            
        except Exception as e:
            print(f"❌ ERROR: {e}")
        
        print("-" * 50)

if __name__ == "__main__":
    test_bracket_wrapping_detection()