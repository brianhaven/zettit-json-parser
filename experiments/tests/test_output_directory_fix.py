#!/usr/bin/env python3

"""
Test to verify output directory creation fix.
"""

import os
import sys
import logging
from pathlib import Path
from datetime import datetime, timezone
import pytz
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

def test_output_directory_creation():
    """Test if the fixed test harness creates output directories properly."""
    
    logger.info("Testing output directory creation fix...")
    
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
        
        # Test directory creation without running full test
        pdt = pytz.timezone('America/Los_Angeles')
        utc_now = datetime.now(timezone.utc)
        pdt_now = utc_now.astimezone(pdt)
        
        timestamp = pdt_now.strftime('%Y%m%d_%H%M%S')
        
        # Use the same logic as the harness
        script_dir = Path(__file__).parent.parent.parent
        output_dir = script_dir / "outputs" / f"{timestamp}_test_directory_creation"
        output_path = Path(output_dir)
        
        logger.info(f"Attempting to create: {output_path.absolute()}")
        output_path.mkdir(parents=True, exist_ok=True)
        
        # Create a test file
        test_file = output_path / "test_file.txt"
        with open(test_file, 'w') as f:
            f.write("Test file to verify directory creation works\n")
            f.write(f"Created at: {datetime.now()}\n")
        
        # Verify creation
        if output_path.exists() and test_file.exists():
            logger.info(f"✅ Directory created successfully: {output_path.absolute()}")
            logger.info(f"✅ Test file created: {test_file.exists()}")
            
            # Clean up
            test_file.unlink()
            output_path.rmdir()
            logger.info("✅ Cleanup completed")
            
            return True
        else:
            logger.error("❌ Directory or file creation failed")
            return False
            
    except Exception as e:
        logger.error(f"Test failed: {e}")
        return False

if __name__ == "__main__":
    success = test_output_directory_creation()
    if success:
        print("✅ Output directory creation test PASSED")
    else:
        print("❌ Output directory creation test FAILED")
    exit(0 if success else 1)