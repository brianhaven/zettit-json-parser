#!/usr/bin/env python3

"""
Phase 2 Test with Explicit Report Generation
Ensures reports are created and output directory exists.
"""

import os
import sys
import logging
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

def test_phase2_with_reports():
    """Run Phase 2 test with explicit report generation."""
    
    logger.info("Starting Phase 2 Test with Explicit Report Generation")
    
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
        # Create test harness
        test_harness = Phase2PipelineTestHarness()
        logger.info("Test harness created successfully")
        
        # Run the test suite (processes documents)
        test_harness.run_test_suite()
        logger.info("Test suite completed")
        
        # Explicitly generate reports
        output_dir = test_harness.generate_reports()
        logger.info(f"Reports generated in: {output_dir}")
        
        # Verify output directory exists
        from pathlib import Path
        output_path = Path(output_dir)
        if output_path.exists():
            logger.info(f"✅ Output directory confirmed: {output_path.absolute()}")
            
            # List files in output directory
            files = list(output_path.iterdir())
            logger.info(f"Files created: {[f.name for f in files]}")
            
            # Check for summary report
            summary_file = output_path / "summary_report.md"
            if summary_file.exists():
                logger.info("✅ Summary report created")
                
                # Read and display key metrics
                with open(summary_file, 'r') as f:
                    content = f.read()
                    lines = content.split('\n')
                    for line in lines:
                        if 'Successful Extractions' in line:
                            print(f"📊 {line.strip()}")
                        elif 'Failed Extractions' in line:
                            print(f"📊 {line.strip()}")
                            
                print(f"✅ Phase 2 Test Complete with Reports!")
                print(f"📁 Output directory: {output_path.absolute()}")
                return True
            else:
                logger.error("❌ Summary report not found")
                return False
        else:
            logger.error(f"❌ Output directory not found: {output_path.absolute()}")
            return False
            
    except Exception as e:
        logger.error(f"Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_phase2_with_reports()
    exit(0 if success else 1)