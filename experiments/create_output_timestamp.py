#!/usr/bin/env python3
"""
Create Output Timestamp Directory
==================================

Creates a timestamped output directory for saving test results.
"""

import os
import pytz
from datetime import datetime

def create_output_directory():
    """Create timestamped output directory."""
    # Get current directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    outputs_dir = os.path.join(project_root, 'outputs')
    
    # Create timestamp in Pacific Time
    pdt = pytz.timezone('America/Los_Angeles')
    timestamp = datetime.now(pdt).strftime('%Y%m%d_%H%M%S')
    
    # Create timestamped subdirectory
    output_dir = os.path.join(outputs_dir, f"{timestamp}_script03v3_25title_test_results")
    os.makedirs(output_dir, exist_ok=True)
    
    print(f"Created output directory: {output_dir}")
    return output_dir

if __name__ == "__main__":
    output_dir = create_output_directory()