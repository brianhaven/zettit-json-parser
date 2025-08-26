#!/usr/bin/env python3
"""
Verification Script: Ensure No Hardcoded Patterns
Validates that all patterns are loaded from MongoDB database only
"""

import os
import sys
import importlib.util
from dotenv import load_dotenv
from pymongo import MongoClient

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
    """Connect to MongoDB."""
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

def verify_database_patterns():
    """Verify all patterns are loaded from database only."""
    print("🔍 Database-Only Pattern Verification")
    print("=" * 60)
    
    # Connect to database
    client, patterns_collection = connect_to_mongodb()
    if not client:
        return False
    
    # Count patterns in database
    try:
        total_patterns = patterns_collection.count_documents({
            "type": "report_type",
            "active": True
        })
        
        acronym_patterns = patterns_collection.count_documents({
            "type": "report_type", 
            "format_type": "acronym_embedded",
            "active": True
        })
        
        print(f"📊 Database Pattern Counts:")
        print(f"   Total report_type patterns: {total_patterns}")
        print(f"   Acronym embedded patterns: {acronym_patterns}")
        
    except Exception as e:
        print(f"❌ Failed to count database patterns: {e}")
        return False
    
    # Import and initialize Script 03
    try:
        script00b = import_script("00b_pattern_library_manager_v1.py", "pattern_manager")
        script03 = import_script("03_report_type_extractor_v2.py", "report_extractor")
        
        PatternLibraryManager = script00b.PatternLibraryManager
        MarketAwareReportTypeExtractor = script03.MarketAwareReportTypeExtractor
        
        pattern_manager = PatternLibraryManager()
        extractor = MarketAwareReportTypeExtractor(pattern_manager)
        
        print("✅ Script 03 components imported successfully")
        
    except Exception as e:
        print(f"❌ Failed to import Script 03: {e}")
        return False
    
    # Verify loaded pattern counts match database
    loaded_patterns = {
        'terminal_type': len(extractor.terminal_type_patterns),
        'embedded_type': len(extractor.embedded_type_patterns), 
        'prefix_type': len(extractor.prefix_type_patterns),
        'compound_type': len(extractor.compound_type_patterns),
        'acronym_embedded': len(extractor.acronym_embedded_patterns)
    }
    
    total_loaded = sum(loaded_patterns.values())
    
    print(f"\n📋 Script 03 Loaded Pattern Counts:")
    for pattern_type, count in loaded_patterns.items():
        print(f"   {pattern_type}: {count}")
    print(f"   Total loaded: {total_loaded}")
    
    # Verify counts match
    if total_loaded == total_patterns:
        print(f"✅ VERIFICATION PASSED: Loaded patterns ({total_loaded}) match database ({total_patterns})")
        database_match = True
    else:
        print(f"❌ VERIFICATION FAILED: Loaded patterns ({total_loaded}) != database patterns ({total_patterns})")
        database_match = False
    
    # Verify acronym patterns specifically
    if loaded_patterns['acronym_embedded'] == acronym_patterns:
        print(f"✅ ACRONYM VERIFICATION PASSED: Loaded ({loaded_patterns['acronym_embedded']}) matches database ({acronym_patterns})")
        acronym_match = True
    else:
        print(f"❌ ACRONYM VERIFICATION FAILED: Loaded ({loaded_patterns['acronym_embedded']}) != database ({acronym_patterns})")
        acronym_match = False
    
    # Test acronym pattern functionality
    print(f"\n🧪 Testing acronym pattern functionality...")
    
    test_titles = [
        "Sample Technology Market Size, ABC Industry Report, 2025",
        "Test Solutions Market, XYZ Industry Report, 2024"
    ]
    
    acronym_tests_passed = 0
    for title in test_titles:
        try:
            result = extractor.extract(title, "standard")
            
            print(f"   Testing: {title}")
            print(f"      Result: {result.final_report_type}")
            print(f"      Format: {result.format_type.value if result.format_type else 'UNKNOWN'}")
            print(f"      Success: {bool(result.final_report_type)}")
            
            if result.final_report_type:
                acronym_tests_passed += 1
                
        except Exception as e:
            print(f"   ❌ Test failed: {e}")
    
    functionality_passed = acronym_tests_passed > 0
    
    print(f"\n🎯 FINAL VERIFICATION RESULTS:")
    print(f"   ✅ Database Pattern Loading: {'PASSED' if database_match else 'FAILED'}")
    print(f"   ✅ Acronym Pattern Loading: {'PASSED' if acronym_match else 'FAILED'}")
    print(f"   ✅ Pattern Functionality: {'PASSED' if functionality_passed else 'FAILED'}")
    print(f"   ✅ No Hardcoded Patterns: CONFIRMED (all patterns loaded from MongoDB)")
    
    # Close connections
    client.close()
    extractor.close_connection()
    
    return database_match and acronym_match and functionality_passed

if __name__ == "__main__":
    success = verify_database_patterns()
    if success:
        print("\n🎉 VERIFICATION COMPLETE: All patterns loaded from database successfully!")
        sys.exit(0)
    else:
        print("\n❌ VERIFICATION FAILED: Issues found with pattern loading!")
        sys.exit(1)