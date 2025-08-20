#!/usr/bin/env python3

"""
Test script for Pattern Library Manager v1.0
Validates core CRUD operations and performance tracking.
"""

import sys
import logging
from pattern_library_manager_v1 import PatternLibraryManager, PatternType

# Configure logging for tests
logging.basicConfig(level=logging.WARNING)

def test_pattern_manager():
    """Run comprehensive tests for Pattern Library Manager."""
    
    print("Pattern Library Manager Tests")
    print("=" * 50)
    
    manager = PatternLibraryManager()
    test_results = []
    
    try:
        # Test 1: Get existing patterns
        print("\n1. Testing pattern retrieval...")
        geo_patterns = manager.get_patterns(PatternType.GEOGRAPHIC_ENTITY)
        market_patterns = manager.get_patterns(PatternType.MARKET_TERM)
        
        assert len(geo_patterns) > 0, "Should have geographic patterns"
        assert len(market_patterns) == 2, "Should have exactly 2 market terms"
        test_results.append("✅ Pattern retrieval")
        
        # Test 2: Add new test pattern
        print("2. Testing pattern addition...")
        test_pattern_id = manager.add_pattern(
            PatternType.GEOGRAPHIC_ENTITY,
            term="Test Region",
            aliases=["TR", "TestReg"],
            priority=9,  # Low priority for testing
            active=True
        )
        
        assert test_pattern_id, "Should return pattern ID"
        test_results.append("✅ Pattern addition")
        
        # Test 3: Search for the new pattern
        print("3. Testing pattern search...")
        search_results = manager.search_patterns("Test Region")
        assert len(search_results) == 1, "Should find exactly one test pattern"
        assert search_results[0]['term'] == "Test Region", "Should match term exactly"
        test_results.append("✅ Pattern search")
        
        # Test 4: Update pattern
        print("4. Testing pattern update...")
        update_success = manager.update_pattern(test_pattern_id, {
            "aliases": ["TR", "TestReg", "TestRegion"],
            "priority": 8
        })
        assert update_success, "Update should succeed"
        test_results.append("✅ Pattern update")
        
        # Test 5: Track success and failure
        print("5. Testing performance tracking...")
        success_track = manager.track_success(test_pattern_id)
        failure_track = manager.track_failure(test_pattern_id)
        assert success_track and failure_track, "Tracking should succeed"
        test_results.append("✅ Performance tracking")
        
        # Test 6: Get performance metrics
        print("6. Testing performance metrics...")
        metrics = manager.get_performance_metrics(PatternType.GEOGRAPHIC_ENTITY)
        assert "geographic_entity" in metrics, "Should have geographic entity metrics"
        test_results.append("✅ Performance metrics")
        
        # Test 7: Bulk operations
        print("7. Testing bulk operations...")
        bulk_updates = [
            {
                "filter": {"_id": manager.collection.find_one({"term": "Test Region"})["_id"]},
                "update": {"$set": {"active": False}}
            }
        ]
        updated_count = manager.bulk_update_patterns(bulk_updates)
        assert updated_count == 1, "Should update exactly one pattern"
        test_results.append("✅ Bulk operations")
        
        # Test 8: Validation
        print("8. Testing pattern validation...")
        invalid_pattern = {"aliases": "not a list"}  # Missing term, invalid aliases
        errors = manager.validate_pattern_format(PatternType.GEOGRAPHIC_ENTITY, invalid_pattern)
        assert len(errors) > 0, "Should find validation errors"
        test_results.append("✅ Pattern validation")
        
        # Test 9: Get patterns by priority
        print("9. Testing priority filtering...")
        priority_1_patterns = manager.get_patterns_by_priority(PatternType.GEOGRAPHIC_ENTITY, 1)
        assert len(priority_1_patterns) > 0, "Should have priority 1 patterns"
        test_results.append("✅ Priority filtering")
        
        # Cleanup: Delete test pattern
        print("10. Testing pattern deletion...")
        delete_success = manager.delete_pattern(test_pattern_id)
        assert delete_success, "Delete should succeed"
        test_results.append("✅ Pattern deletion")
        
        # Final verification
        search_after_delete = manager.search_patterns("Test Region")
        assert len(search_after_delete) == 0, "Pattern should be deleted"
        
        print(f"\n{'='*50}")
        print("TEST RESULTS:")
        for result in test_results:
            print(f"  {result}")
        
        print(f"\n✅ All {len(test_results)} tests passed successfully!")
        return True
        
    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
        return False
    except Exception as e:
        print(f"\n💥 Test error: {e}")
        return False
    finally:
        manager.close_connection()


if __name__ == "__main__":
    success = test_pattern_manager()
    sys.exit(0 if success else 1)