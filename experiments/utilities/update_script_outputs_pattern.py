#!/usr/bin/env python3
"""
Update existing scripts to use the new organized output directory structure.

This script finds all Python scripts in experiments/ and updates them to use
the new output_directory_manager module instead of manual directory creation.
"""

import os
import re
import glob
from pathlib import Path

def update_script_output_patterns(script_path: str) -> bool:
    """
    Update a single script to use the new organized output pattern.
    
    Args:
        script_path: Path to the script to update
        
    Returns:
        bool: True if script was updated, False if no changes needed
    """
    
    with open(script_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original_content = content
    updated = False
    
    # Pattern 1: Manual timestamped output directory creation
    # Look for patterns like: f"../outputs/{timestamp}_{script_name}"
    timestamp_pattern = r'f?"\.\.\/outputs\/\{timestamp\}_\{?[^}]+\}?"'
    if re.search(timestamp_pattern, content):
        print(f"  Found manual timestamp pattern in {script_path}")
        # Add import if not present
        if "from experiments.utilities.output_directory_manager import" not in content:
            import_line = "from experiments.utilities.output_directory_manager import create_organized_output_directory, create_output_file_header\n"
            # Insert after existing imports
            if "import" in content:
                import_pos = content.rfind("import")
                next_line = content.find("\n", import_pos)
                content = content[:next_line+1] + import_line + content[next_line+1:]
                updated = True
    
    # Pattern 2: os.makedirs with timestamp directories  
    makedirs_pattern = r'os\.makedirs\([^)]*timestamp[^)]*\)'
    if re.search(makedirs_pattern, content):
        print(f"  Found makedirs timestamp pattern in {script_path}")
        updated = True
    
    # Pattern 3: datetime.now().strftime('%Y%m%d_%H%M%S') patterns
    strftime_pattern = r'datetime\.now\([^)]*\)\.strftime\([\'"][^\'\"]*%Y%m%d_%H%M%S[^\'\"]*[\'\"]\)'
    if re.search(strftime_pattern, content):
        print(f"  Found strftime pattern in {script_path}")
        updated = True
        
    # If we found patterns to update, suggest the replacement
    if updated:
        print(f"    → Requires manual update to use create_organized_output_directory()")
        return True
    
    return False


def scan_scripts_for_output_patterns():
    """Scan all Python scripts in experiments/ for output directory patterns."""
    
    experiments_dir = Path("experiments")
    if not experiments_dir.exists():
        print("Error: experiments/ directory not found")
        return
    
    # Find all Python scripts
    python_scripts = []
    for pattern in ["*.py", "tests/*.py", "utilities/*.py"]:
        python_scripts.extend(glob.glob(str(experiments_dir / pattern)))
    
    print(f"Scanning {len(python_scripts)} Python scripts for output patterns...")
    print("="*60)
    
    needs_update = []
    
    for script_path in python_scripts:
        script_name = Path(script_path).name
        print(f"\nChecking {script_name}:")
        
        if update_script_output_patterns(script_path):
            needs_update.append(script_path)
            print(f"  ✅ Needs update")
        else:
            print(f"  ✅ No output patterns found")
    
    print("\n" + "="*60)
    print("SUMMARY:")
    print(f"Scripts checked: {len(python_scripts)}")
    print(f"Scripts needing updates: {len(needs_update)}")
    
    if needs_update:
        print(f"\nScripts requiring manual updates:")
        for script in needs_update:
            print(f"  - {script}")
        
        print(f"\nRecommended changes:")
        print(f"1. Add import: from experiments.utilities.output_directory_manager import create_organized_output_directory")
        print(f"2. Replace manual directory creation with: output_dir = create_organized_output_directory('script_name')")
        print(f"3. Use create_output_file_header() for consistent file headers")


if __name__ == "__main__":
    scan_scripts_for_output_patterns()