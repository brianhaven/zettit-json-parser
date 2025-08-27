# Development Standards

## Script Organization & Directory Structure

**CRITICAL: All development follows this mandatory directory structure:**

### Main Processing Scripts (`/experiments/`)
- **00-07 numbered scripts:** Main processing pipeline components in execution order
- **00a-03a initialization scripts:** Setup and pattern library management  
- **Pattern discovery scripts:** Human-review workflow for pattern enhancement
- **All main scripts must be developed in `/experiments/` directory**

### Test Scripts (`/experiments/tests/`)
- **ALL test scripts must be stored in `/experiments/tests/` directory**
- Test scripts use systematic naming: `test_{script_name}_{version}.py`
- Test scripts must include proper import path handling for parent directory modules
- Examples: `test_03_market_aware_pipeline_v2.py`, `test_phase1_market_term_classifier_harness.py`

### Output Directory (`/outputs/`)
- **ALL script outputs must be stored in `/outputs/` directory**
- Each script run creates a new timestamped subdirectory: `/outputs/{YYYYMMDD_HHMMSS}_{TYPE}/`
- Output files within subdirectory use descriptive names (no timestamp prefix needed)

### Supporting Directories:
- **`/experiments/archive/`:** Legacy and experimental approaches
- **`/experiments/utilities/`:** One-time setup and migration scripts  
- **`/resources/`:** Static data files and mappings

## Python Command Requirements
**CRITICAL: Always use `python3` command, never `python`**
- All bash commands must use `python3` for script execution
- This ensures compatibility with the project's Python environment  

## Output File Requirements
**All script outputs must include dual timestamps:**
```
**Analysis Date (PDT):** 2025-08-19 15:30:45 PDT  
**Analysis Date (UTC):** 2025-08-19 22:30:45 UTC
```

**Filename format:** `{YYYYMMDD_HHMMSS}_{TYPE}.{ext}`
- Use Pacific Time for timestamps in filenames
- Include both PDT/PST and UTC timestamps in file headers

## Script Development Standards
**All scripts must follow these mandatory patterns:**

1. **Shebang Line:** Always include `#!/usr/bin/env python3` at the top
2. **Logging Configuration:** Include comprehensive logging setup
3. **Error Handling:** Implement try/catch blocks for all major operations
4. **Dynamic Imports:** Use `importlib.util` for cross-script imports (never static imports)
5. **Verified Integration:** Use only verified class names and initialization patterns
6. **Output Generation:** Always create timestamped output directories and files
7. **Documentation:** Include detailed docstrings and inline comments for complex logic

## Dependencies
- `pymongo` for MongoDB connectivity
- `python-dotenv` for environment variable management
- `spacy` for enhanced geographic entity discovery (en_core_web_md + en_core_web_lg)
- `beautifulsoup4` for HTML processing and concatenation prevention
- `gliner` for named entity recognition (optional)