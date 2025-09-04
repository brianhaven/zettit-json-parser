# Outputs Directory Organization

## Structure Overview

This directory is organized in a hierarchical date-based structure for better organization and navigation:

```
outputs/
├── 2025/
│   ├── 08/                      # August 2025
│   │   ├── 21/                  # August 21, 2025
│   │   │   ├── 20250821_113348_phase1_market_term_classifier/
│   │   │   └── 20250821_120439_phase1_market_term_classifier/
│   │   ├── 22/                  # August 22, 2025
│   │   │   ├── 20250822_134931_phase2_pipeline_01_02/
│   │   │   └── ...
│   │   ├── 25-28/               # August 25-28, 2025
│   │   └── ...
│   └── 09/                      # September 2025
│       ├── 02-04/               # September 2-4, 2025
│       └── ...
├── archive/                     # Special directory - legacy outputs
└── README.md                    # This file
```

## Directory Naming Convention

**Individual Output Directories:**
- Format: `YYYYMMDD_HHMMSS_description`
- Timezone: Pacific Time (PDT/PST)
- Example: `20250821_113348_phase1_market_term_classifier`

**Date Hierarchy:**
- Year: `YYYY` (e.g., `2025`)
- Month: `MM` (e.g., `08` for August)
- Day: `DD` (e.g., `21` for 21st)

## Benefits of This Organization

1. **Easy Navigation**: Find outputs by date without scrolling through hundreds of directories
2. **Clear Chronology**: Natural chronological organization shows project progression
3. **IDE Friendly**: Most IDEs can collapse/expand date folders for focused work
4. **Archive Safety**: `archive/` directory preserved for legacy content
5. **Scalability**: Structure works for years of development output

## How Scripts Create Output Directories

**NEW APPROACH (September 2025+):**
All scripts should use the standardized output directory manager:

```python
from experiments.utilities.output_directory_manager import create_organized_output_directory

output_dir = create_organized_output_directory("my_script_name")
```

This automatically creates the organized structure: `outputs/2025/09/04/20250904_143022_my_script_name/`

**LEGACY APPROACH (Pre-September 2025):**
Old scripts used flat structure: `outputs/20250904_143022_my_script_name/`

## Reorganization History

- **September 4, 2025**: Reorganized 103 existing directories from flat structure to hierarchical YYYY/MM/DD structure
- **Special Handling**: Fixed 3 directories with incorrect timestamp suffixes
- **Preserved**: `archive/` directory kept at root level
- **Scripts Updated**: 22 scripts identified for update to use new organized structure

## Finding Outputs

**By Date:**
- Today's outputs: `outputs/2025/09/04/`
- August outputs: `outputs/2025/08/`
- Specific day: `outputs/2025/08/21/`

**By Test Type:**
- Phase 1 tests: Search for `phase1` in directory names
- Pipeline tests: Search for `pipeline` in directory names
- Script-specific: Search for script number (e.g., `03v3`)

**Latest Output:**
Use the utility function:
```python
from experiments.utilities.output_directory_manager import get_latest_output_directory
latest = get_latest_output_directory("pipeline*")
```

## Working with Organized Outputs

**IDE Navigation:**
1. Expand only current month for active work
2. Collapse older months to reduce clutter
3. Use search functionality to find specific test types

**Command Line:**
```bash
# Find today's outputs
ls outputs/2025/09/04/

# Find all Phase 1 tests
find outputs/ -name "*phase1*" -type d

# Count outputs by date
find outputs/2025/08/ -name "202508*" -type d | wc -l
```

**Scripts and Tests:**
- All new scripts automatically use organized structure
- Legacy scripts gradually updated to new pattern
- Both patterns supported during transition period

This organization significantly improves project maintainability and makes it easier to focus on current work while preserving historical test results.