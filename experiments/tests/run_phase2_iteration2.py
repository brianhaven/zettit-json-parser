#!/usr/bin/env python3

"""
Phase 2 Iteration 2 Test - Enhanced Pattern Library
Runs the full Phase 2 pipeline test with enhanced date patterns.
"""

import os
import sys
import logging
from datetime import datetime, timezone
import pytz
from pathlib import Path
from dotenv import load_dotenv
import importlib.util

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def run_phase2_iteration2():
    """Run Phase 2 iteration 2 test with enhanced patterns."""
    
    logger.info("Starting Phase 2 Iteration 2 Test with Enhanced Patterns")
    
    # Import test harness
    try:
        test_harness_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'test_phase2_pipeline_01_02_harness.py')
        spec = importlib.util.spec_from_file_location("test_harness", test_harness_path)
        harness_module = importlib.util.module_from_spec(spec)
        sys.modules["test_harness"] = harness_module
        spec.loader.exec_module(harness_module)
        Phase2PipelineTestHarness = harness_module.Phase2PipelineTestHarness
    except Exception as e:
        logger.error(f"Failed to import test harness: {e}")
        return False
    
    try:
        # Create and run test harness
        test_harness = Phase2PipelineTestHarness()
        logger.info("Test harness initialized successfully")
        
        # Run the test
        test_harness.run_test_suite()
        logger.info("Pipeline test completed")
        
        # Generate reports
        output_dir = test_harness.generate_reports()
        logger.info(f"Reports generated in: {output_dir}")
        
        # Read and display summary
        summary_path = Path(output_dir) / "summary_report.md"
        if summary_path.exists():
            with open(summary_path, 'r') as f:
                content = f.read()
                # Extract key metrics
                lines = content.split('\n')
                for line in lines:
                    if 'Successful Extractions' in line:
                        print(f"📊 {line.strip()}")
                    elif 'Failed Extractions' in line:
                        print(f"📊 {line.strip()}")
                        
        print(f"✅ Phase 2 Iteration 2 Test Complete!")
        print(f"📁 Full results in: {output_dir}")
        return True
        
    except Exception as e:
        logger.error(f"Test failed: {e}")
        return False

if __name__ == "__main__":
    success = run_phase2_iteration2()
    exit(0 if success else 1)