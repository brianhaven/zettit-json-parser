#!/usr/bin/env python3
"""
Reorganize outputs directory from flat structure to YYYY/MM/DD hierarchy.

This script moves existing output directories from:
  outputs/YYYYMMDD_HHMMSS_description/
To:
  outputs/YYYY/MM/DD/YYYYMMDD_HHMMSS_description/

Usage: python3 experiments/utilities/reorganize_outputs.py [--dry-run]
"""

import os
import re
import shutil
import argparse
from pathlib import Path
from datetime import datetime
import pytz
from typing import Optional, Tuple


def parse_timestamp_from_dirname(dirname: str) -> Optional[Tuple[str, str, str]]:
    """Extract YYYY, MM, DD from directory name starting with YYYYMMDD_HHMMSS."""
    pattern = r'^(\d{4})(\d{2})(\d{2})_\d{6}_.*$'
    match = re.match(pattern, dirname)
    if match:
        return match.group(1), match.group(2), match.group(3)
    return None


def reorganize_outputs(outputs_dir: Path, dry_run: bool = False) -> None:
    """Reorganize outputs directory structure."""
    print(f"{'DRY RUN: ' if dry_run else ''}Reorganizing outputs directory: {outputs_dir}")
    
    # Get all directories in outputs/
    if not outputs_dir.exists():
        print(f"Error: {outputs_dir} does not exist")
        return
        
    directories = [d for d in outputs_dir.iterdir() if d.is_dir()]
    
    # Special directories to skip (keep at root level)
    skip_dirs = {'archive'}  # Only skip archive directory
    
    moved_count = 0
    skipped_count = 0
    error_count = 0
    
    for dir_path in directories:
        dir_name = dir_path.name
        
        # Skip special directories
        if dir_name in skip_dirs:
            print(f"SKIP: {dir_name} (special directory)")
            skipped_count += 1
            continue
            
        # Parse timestamp from directory name
        timestamp_parts = parse_timestamp_from_dirname(dir_name)
        if not timestamp_parts:
            print(f"SKIP: {dir_name} (no valid timestamp)")
            skipped_count += 1
            continue
            
        year, month, day = timestamp_parts
        
        # Create target directory structure
        target_parent = outputs_dir / year / month / day
        target_path = target_parent / dir_name
        
        print(f"{'WOULD MOVE' if dry_run else 'MOVING'}: {dir_name}")
        print(f"  FROM: {dir_path}")
        print(f"  TO:   {target_path}")
        
        if not dry_run:
            try:
                # Create parent directories if they don't exist
                target_parent.mkdir(parents=True, exist_ok=True)
                
                # Move the directory
                shutil.move(str(dir_path), str(target_path))
                moved_count += 1
                
            except Exception as e:
                print(f"ERROR moving {dir_name}: {e}")
                error_count += 1
        else:
            moved_count += 1  # Count for dry run
        
        print()
    
    # Summary
    print("="*60)
    print(f"SUMMARY ({'DRY RUN' if dry_run else 'COMPLETED'}):")
    print(f"  Moved: {moved_count}")
    print(f"  Skipped: {skipped_count}")
    if error_count > 0:
        print(f"  Errors: {error_count}")
    print(f"  Total processed: {moved_count + skipped_count + error_count}")


def main():
    parser = argparse.ArgumentParser(description="Reorganize outputs directory structure")
    parser.add_argument("--dry-run", action="store_true", 
                       help="Show what would be done without making changes")
    parser.add_argument("--outputs-dir", default="outputs",
                       help="Path to outputs directory (default: outputs)")
    
    args = parser.parse_args()
    
    outputs_dir = Path(args.outputs_dir)
    reorganize_outputs(outputs_dir, args.dry_run)


if __name__ == "__main__":
    main()