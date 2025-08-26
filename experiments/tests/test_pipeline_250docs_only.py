#!/usr/bin/env python3

"""
Quick 250 Documents Pipeline Test
Test pipeline with 250 documents after fixing MongoDB memory issue.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from test_pipeline_progressive_validation import PipelineValidator

def main():
    """Run 250 documents test only."""
    validator = PipelineValidator()
    
    print("🚀 Starting 250 documents pipeline validation test...")
    
    try:
        results = validator.run_validation_test(250)
        validator.save_output_files(results, 250)
        
        print(f"\n✅ Test completed successfully!")
        print(f"📊 Results:")
        print(f"  - Market Classification: {results['success_rates']['market_classification']:.1f}%")
        print(f"  - Date Extraction: {results['success_rates']['date_extraction']:.1f}%")
        print(f"  - Report Type Extraction: {results['success_rates']['report_type_extraction']:.1f}%")
        print(f"  - Full Pipeline: {results['success_rates']['full_pipeline']:.1f}%")
        print(f"\n📁 Files saved in: {validator.timestamp}_pipeline_validation_250docs/")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()