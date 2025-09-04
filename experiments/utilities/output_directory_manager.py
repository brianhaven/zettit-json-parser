#!/usr/bin/env python3
"""
Standardized output directory management for all scripts.

This module provides utilities for creating organized output directories
with YYYY/MM/DD structure and consistent naming conventions.
"""

import os
import pytz
from datetime import datetime
from pathlib import Path
from typing import Optional


def create_organized_output_directory(
    script_name: str, 
    base_outputs_dir: str = "outputs",
    custom_root_dir: Optional[str] = None
) -> str:
    """
    Create timestamped output directory with organized YYYY/MM/DD structure.
    
    Args:
        script_name: Descriptive name for the script/test (e.g., "phase1_market_term_classifier")
        base_outputs_dir: Base outputs directory name (default: "outputs")  
        custom_root_dir: Custom root directory path (for test scripts in subdirectories)
        
    Returns:
        str: Absolute path to created output directory
        
    Example:
        For script_name="phase1_test" on 2025-08-21 11:33:48 PDT:
        Returns: "/path/to/project/outputs/2025/08/21/20250821_113348_phase1_test/"
    """
    
    # Determine project root directory
    if custom_root_dir:
        project_root = Path(custom_root_dir)
    else:
        # Auto-detect based on current script location
        current_file = Path(__file__).resolve()
        if "experiments" in current_file.parts:
            # Script is in experiments/ or experiments/tests/ or experiments/utilities/
            experiments_idx = current_file.parts.index("experiments")
            project_root = Path(*current_file.parts[:experiments_idx])
        else:
            # Fallback to current directory
            project_root = Path.cwd()
    
    # Create timestamp in Pacific Time (as per project standards)
    pdt = pytz.timezone('America/Los_Angeles')
    now = datetime.now(pdt)
    
    # Format: YYYYMMDD_HHMMSS
    timestamp = now.strftime('%Y%m%d_%H%M%S')
    
    # Extract date components for directory structure
    year = now.strftime('%Y')
    month = now.strftime('%m')
    day = now.strftime('%d')
    
    # Build organized directory path
    outputs_base = project_root / base_outputs_dir
    date_structure = outputs_base / year / month / day
    output_dir_name = f"{timestamp}_{script_name}"
    full_output_dir = date_structure / output_dir_name
    
    # Create the directory structure
    full_output_dir.mkdir(parents=True, exist_ok=True)
    
    return str(full_output_dir)


def create_output_file_header(script_name: str, description: str = "") -> str:
    """
    Create standardized output file header with dual timestamps.
    
    Args:
        script_name: Name of the script generating the output
        description: Optional description of the output
        
    Returns:
        str: Formatted header string with PDT and UTC timestamps
    """
    pdt = pytz.timezone('America/Los_Angeles')
    utc = pytz.timezone('UTC')
    
    now_pdt = datetime.now(pdt)
    now_utc = datetime.now(utc)
    
    header_lines = [
        f"# {script_name} Output",
        f"",
        f"**Analysis Date (PDT):** {now_pdt.strftime('%Y-%m-%d %H:%M:%S %Z')}",
        f"**Analysis Date (UTC):** {now_utc.strftime('%Y-%m-%d %H:%M:%S %Z')}",
        f"",
    ]
    
    if description:
        header_lines.extend([
            f"**Description:** {description}",
            f"",
        ])
    
    header_lines.append("="*80)
    header_lines.append("")
    
    return "\n".join(header_lines)


def get_latest_output_directory(
    script_name_pattern: str = "*",
    base_outputs_dir: str = "outputs",
    custom_root_dir: Optional[str] = None
) -> Optional[str]:
    """
    Find the most recent output directory matching a pattern.
    
    Args:
        script_name_pattern: Glob pattern for script name (e.g., "phase1*", "*pipeline*")
        base_outputs_dir: Base outputs directory name
        custom_root_dir: Custom root directory path
        
    Returns:
        str: Path to most recent matching directory, or None if not found
    """
    # Determine project root
    if custom_root_dir:
        project_root = Path(custom_root_dir)
    else:
        current_file = Path(__file__).resolve()
        if "experiments" in current_file.parts:
            experiments_idx = current_file.parts.index("experiments")
            project_root = Path(*current_file.parts[:experiments_idx])
        else:
            project_root = Path.cwd()
    
    outputs_base = project_root / base_outputs_dir
    
    # Search through organized date structure
    matching_dirs = []
    for year_dir in outputs_base.glob("*/"):
        if not year_dir.name.isdigit() or len(year_dir.name) != 4:
            continue
        for month_dir in year_dir.glob("*/"):
            if not month_dir.name.isdigit() or len(month_dir.name) != 2:
                continue
            for day_dir in month_dir.glob("*/"):
                if not day_dir.name.isdigit() or len(day_dir.name) != 2:
                    continue
                # Look for matching directories in this date folder
                for output_dir in day_dir.glob(f"*{script_name_pattern}"):
                    if output_dir.is_dir():
                        matching_dirs.append(output_dir)
    
    if not matching_dirs:
        return None
        
    # Sort by timestamp (directory name starts with YYYYMMDD_HHMMSS)
    matching_dirs.sort(key=lambda d: d.name, reverse=True)
    return str(matching_dirs[0])


# Legacy compatibility function for existing scripts
def create_output_directory(script_name: str) -> str:
    """
    Legacy function for backwards compatibility.
    Redirects to create_organized_output_directory.
    """
    return create_organized_output_directory(script_name)


if __name__ == "__main__":
    # Test the functions
    print("Testing organized output directory creation:")
    
    test_dir = create_organized_output_directory("test_output_manager")
    print(f"Created: {test_dir}")
    
    header = create_output_file_header("test_script", "Testing output manager")
    print("\nGenerated header:")
    print(header)
    
    # Test finding latest directory
    latest = get_latest_output_directory("test*")
    print(f"\nLatest test directory: {latest}")