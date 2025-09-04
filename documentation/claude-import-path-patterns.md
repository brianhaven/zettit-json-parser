# Import Path Management Patterns

## CRITICAL: All scripts must handle imports correctly based on their location:

### For Test Scripts in `/experiments/tests/`:
```python
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Dynamic import pattern for main scripts
import importlib.util

def import_module_from_path(module_name: str, file_path: str):
    """Import a module from a file path."""
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

# Import main scripts from parent directory
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
pattern_lib = import_module_from_path("pattern_library_manager_v1", 
                                    os.path.join(parent_dir, "00b_pattern_library_manager_v1.py"))
```

### For Main Scripts in `/experiments/`:
```python
import importlib.util
import sys
import os

# Dynamic import for same-directory modules
try:
    pattern_manager_path = os.path.join(os.path.dirname(__file__), "00b_pattern_library_manager_v1.py")
    spec = importlib.util.spec_from_file_location("pattern_library_manager_v1", pattern_manager_path)
    pattern_module = importlib.util.module_from_spec(spec)
    sys.modules["pattern_library_manager_v1"] = pattern_module
    spec.loader.exec_module(pattern_module)
    PatternLibraryManager = pattern_module.PatternLibraryManager
except Exception as e:
    logger.error(f"Failed to import PatternLibraryManager: {e}")
```

## Output Directory Creation Standards

### NEW ORGANIZED APPROACH (2025-09+):
**ALL scripts should now use the standardized output directory manager:**

```python
from experiments.utilities.output_directory_manager import create_organized_output_directory, create_output_file_header

def create_output_directory(script_name: str) -> str:
    """Create organized output directory with YYYY/MM/DD structure."""
    return create_organized_output_directory(script_name)

def create_file_header(script_name: str, description: str = "") -> str:
    """Create standardized file header with dual timestamps."""
    return create_output_file_header(script_name, description)
```

**Benefits of New Approach:**
- **Organized Structure**: `outputs/YYYY/MM/DD/YYYYMMDD_HHMMSS_script_name/`
- **Auto-Detection**: Automatically detects project root from any script location
- **Consistent Timestamps**: Pacific Time with dual PDT/UTC headers
- **Legacy Compatibility**: Works from main scripts, test scripts, and utilities

### LEGACY PATTERNS (Pre-2025-09):
**These patterns are deprecated but documented for reference:**

### For Test Scripts (DEPRECATED):
```python
import pytz
from datetime import datetime
from pathlib import Path

def create_output_directory(script_name: str) -> str:
    """Create timestamped output directory using absolute paths."""
    # Get absolute path to outputs directory (from /experiments/tests/ to /outputs/)
    script_dir = os.path.dirname(os.path.abspath(__file__))
    experiments_dir = os.path.dirname(script_dir)  
    project_root = os.path.dirname(experiments_dir)
    outputs_dir = os.path.join(project_root, 'outputs')
    
    # Create timestamp in Pacific Time
    pdt = pytz.timezone('America/Los_Angeles')
    timestamp = datetime.now(pdt).strftime('%Y%m%d_%H%M%S')
    
    # Create timestamped subdirectory
    output_dir = os.path.join(outputs_dir, f"{timestamp}_{script_name}")
    os.makedirs(output_dir, exist_ok=True)
    
    return output_dir
```

### For Main Scripts (DEPRECATED):
```python
def create_output_directory(script_name: str) -> str:
    """Create timestamped output directory from experiments directory."""
    # Create outputs directory relative to current script location
    timestamp = datetime.now(pytz.timezone('America/Los_Angeles')).strftime('%Y%m%d_%H%M%S')
    output_dir = f"../outputs/{timestamp}_{script_name}"
    os.makedirs(output_dir, exist_ok=True)
    return output_dir
```

## Path Convention Guidelines

**CRITICAL: Follow these absolute path conventions to avoid errors:**

### Common Path Issues to Avoid:
1. **Never use relative paths** like `../experiments/` from test scripts - use absolute paths  
2. **Never hardcode paths** - always calculate paths dynamically from `__file__`
3. **Always verify parent directory navigation** - test scripts need to go up 2 levels to reach project root
4. **Always create output directories** before writing files - use `os.makedirs(output_dir, exist_ok=True)`

### Standard Path Calculations:
```python
# For test scripts in /experiments/tests/
script_dir = os.path.dirname(os.path.abspath(__file__))           # /experiments/tests/
experiments_dir = os.path.dirname(script_dir)                     # /experiments/  
project_root = os.path.dirname(experiments_dir)                   # /
outputs_dir = os.path.join(project_root, 'outputs')              # /outputs/

# For main scripts in /experiments/
script_dir = os.path.dirname(os.path.abspath(__file__))           # /experiments/
project_root = os.path.dirname(script_dir)                        # /
outputs_dir = os.path.join(project_root, 'outputs')              # /outputs/
```

### Module Import Standards
```python
# CORRECT: Dynamic imports using importlib.util
import importlib.util

def import_module_from_path(module_name: str, file_path: str):
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

# INCORRECT: Static imports (will fail due to directory structure)
# from experiments.01_market_term_classifier_v1 import MarketTermClassifier
```