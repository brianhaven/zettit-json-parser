```
╔═══════════════════════════════════════════════════════════════════════════════╗
║                                                                               ║
║                                                                               ║
║                                        ███                                    ║
║                                            █                                  ║
║                         █  █         █   █   █        █                       ║
║                        ██     █ █   █         ██       █                      ║
║                               █   ██   █  █      █ █    █                     ║
║                       █    █   █  █  █       █   █ █    ██                    ║
║                        ███               █     █  █  █                        ║
║                ██      █                   ███   █     █ █                    ║
║           █      ████████  ██████████████████████████      █                  ║
║             █ █   █        ██████████████████████████     █████████           ║
║            █  █ █  █       ██████████████████████████  █         █ █          ║
║                            █████████████████████████      ██     █            ║
║            █      █    █  █         █     █████████ █     █   █   █           ║
║          █       █ █   █  █          █   █████████   █ █    █  █              ║
║                      █ █            █   █████████  █  █      █   █   █        ║
║       █  ██  █  █      █       █     █ █████████       █     █      █         ║
║        █ █       ██    ██    █        █████████         █      ███  █         ║
║             █ ██    █    ███        █████████            ██   █   █           ║
║           █        █     █  █      █████████    █    █    █     █             ║
║          █ █   █ ██               █████████     █          █   █              ║
║           █  █   █  █            █████████        █  █      █       █         ║
║            █    █           █   █████████  █     █        █  █  █    █        ║
║             █  █  █      █    █████████     █            █    █   █           ║
║                 █            █████████           ██    █    █  █ █  █         ║
║               █   █   ██    █████████                █         ██             ║
║            █   █  ██  █    █████████    █     █    █      ██     █            ║
║           █  █ █  █ █ █   ███████████████████████████ █           █           ║
║            ██   █     █   ███████████████████████████     █      ██           ║
║                  ███  ██  ███████████████████████████     ██  █               ║
║                         █ ███████████████████████████    ██                   ║
║                     █    █      █   █     █ ███  █   ██                       ║
║                                 ██   ████        ██     █                     ║
║                        █   ██ ██ █   █        █    █  █                       ║
║                      █ ██    █            █          ██        Zettit         ║
║                                   ██  █                                       ║
║                                  ██                                           ║
║                                                                               ║
║                                                                               ║
╚═══════════════════════════════════════════════════════════════════════════════╝
╔═══════════════════════════════════════════════════════════════════════════════╗
║                                                                               ║
║  ███████╗ ███████╗ ████████╗ ████████╗ ██╗ ████████╗                          ║
║  ╚══███╔╝ ██╔════╝ ╚══██╔══╝ ╚══██╔══╝ ██║ ╚══██╔══╝                          ║
║    ███╔╝  █████╗      ██║       ██║    ██║    ██║                             ║
║   ███╔╝   ██╔══╝      ██║       ██║    ██║    ██║                             ║
║  ███████╗ ███████╗    ██║       ██║    ██║    ██║                             ║
║  ╚══════╝ ╚══════╝    ╚═╝       ╚═╝    ╚═╝    ╚═╝                             ║
║                                                                               ║
║            JSON Parser                                                        ║
║            ────────────                                                       ║
║                                                                               ║
║                                                          www.zettit.com       ║
║                                                                               ║
╚═══════════════════════════════════════════════════════════════════════════════╝
```
# Zettit JSON Parser

## Overview

An AI-powered market research title parser that extracts structured information (topics, geographic regions, report types, dates) from MongoDB collections containing market research report titles.

## Problem Statement

Market research report titles contain valuable structured data that needs to be extracted systematically:
- **Topics**: Product/industry focus (e.g., "Antimicrobial Medical Textiles")
- **Geographic Regions**: Market scope (e.g., "APAC", "North America")  
- **Report Types**: Analysis type (e.g., "Market Size & Share Report")
- **Dates**: Publication/forecast years (e.g., "2030", "2020-2027")

**Challenge**: Manual extraction from 19,558+ titles is impractical, and existing NLP solutions are costly and complex.

## Solution Architecture

### MongoDB-First Systematic Processing
1. ✅ **Market Term Classification**: Separate special patterns ("Market for"/"Market in") from standard titles - **100% accuracy**
2. ✅ **Enhanced Date Extraction**: Numeric pre-filtering with 64-pattern library (`extracted_forecast_date_range`) - **100% accuracy on titles with dates**
3. **Report Type Processing**: ✅ **PRODUCTION READY** - Market-aware processing with 355 validated patterns (`extracted_report_type`)
4. **Geographic Entity Detection**: Compound-priority matching from MongoDB libraries (`extracted_regions`)
5. **Topic Extraction**: Preserve complete technical compounds (`topic` and `topicName`)

### MongoDB-Based Libraries & MCP Integration
- **Pattern Libraries Collection**: Real-time updatable pattern storage with performance tracking
- **MongoDB MCP Server**: Efficient database access through Claude Code MCP commands
  - `mcp__mongodb__find`, `mcp__mongodb__aggregate`, `mcp__mongodb__count` for queries
  - `mcp__mongodb__insert-many`, `mcp__mongodb__update-many` for data modification
  - Direct access to pattern libraries without subprocess overhead
- **Geographic Entities**: 363+ regions, countries, acronyms with compound-first processing
- **Market Term Exceptions**: Handle "After Market", "Marketplace", edge cases
- **Date Pattern Recognition**: Standard, bracketed, and embedded date formats
- **Report Type Standardization**: 355 validated patterns across 5 format types

## Key Features

- **High Accuracy**: 100% success rate on date extraction (exceeds 95-98% target)
- **Enhanced Categorization**: Distinguishes "no dates present" vs "dates missed" for precise analytics
- **Real-time Updates**: MongoDB-based libraries update without deployment
- **Scalable**: Handles large MongoDB collections efficiently  
- **Self-Improving**: Performance tracking and automated pattern learning
- **Production Ready**: Comprehensive error handling and confidence scoring
- **Cost Effective**: CPU-optimized alternative to expensive GPU-based NLP models (~$70/month vs $900/month)

## Project Structure

```
/
├── mongo-connection-test.py          # MongoDB connectivity validation
├── /experiments/                     # Development scripts with versions
│   ├── README.md                    # Pipeline scripts documentation
│   ├── 01_market_term_classifier_v1.py
│   ├── 02_date_extractor_v1.py      
│   ├── 03_report_type_extractor_v2.py
│   ├── 04_geographic_entity_detector_v2.py
│   ├── 05_topic_extractor_v1.py
│   └── /tests/                      # Validation and test scripts
├── /outputs/                        # Timestamped analysis results
├── /documentation/                   # Modular documentation system
│   ├── claude-component-integration.md      # Integration patterns
│   ├── claude-pre-development-analysis.md  # Error prevention guides
│   ├── claude-mongodb-integration.md       # Database architecture
│   ├── claude-pipeline-components.md       # Component details
│   └── claude-development-standards.md     # Coding standards
├── /resources/                       # Data files and exports
├── CLAUDE.md                        # Main development guide (optimized)
└── README.md                        # Project overview
```

## Getting Started

### Prerequisites
- Python 3.8+
- MongoDB Atlas connection
- Required packages: `pymongo`, `python-dotenv`

### Environment Setup
Create `.env` file:
```bash
# Replace with your actual MongoDB Atlas connection string
MONGODB_URI=mongodb+srv://YOUR_USERNAME:YOUR_PASSWORD@YOUR_CLUSTER.mongodb.net/YOUR_DATABASE
```

### Quick Start
```bash
# Test MongoDB connection
python mongo-connection-test.py

# Run pattern analysis
python experiments/title_pattern_discovery_v1.py
```

## Development Standards

**For detailed development guidelines, see the modular documentation system:**
- **Main Guide**: `CLAUDE.md` - Optimized overview with @ references to modular docs
- **Component Integration**: `documentation/claude-component-integration.md` - Current class names and method signatures
- **Pre-Development Analysis**: `documentation/claude-pre-development-analysis.md` - Error prevention patterns
- **MongoDB Integration**: `documentation/claude-mongodb-integration.md` - Database architecture and MCP commands

### Quick Reference - Current Components (2025-08-27):
| Script | Class Name | Method | Initialization |
|--------|------------|--------|----------------|
| 01 | `MarketTermClassifier` | `classify(title)` | `PatternLibraryManager` (optional) |
| 02 | `EnhancedDateExtractor` | `extract(title)` | `PatternLibraryManager` (required) |
| 03 | `MarketAwareReportTypeExtractor` | `extract(title, market_term_type)` | `PatternLibraryManager` (required) |
| 04 v2 | `GeographicEntityDetector` | `extract_geographic_entities(text)` | Raw collection |
| 05 | `TopicExtractor` | `extract(title)` | `PatternLibraryManager` |

### Processing Philosophy
**"Systematic Removal"**: Remove known patterns (dates, report types, regions) systematically using MongoDB-based libraries. What remains IS the topic, regardless of internal punctuation or special characters.

### Database Architecture
**MongoDB Atlas Collections:**
- `markets_raw`: Source data (19,558+ titles)
- `pattern_libraries`: Real-time pattern storage with performance tracking
- `markets_processed`: Extracted results with confidence scoring

## Performance Metrics

- **Dataset Size**: 19,558 market research titles
- **Phase 1 Complete**: ✅ Market classification with 100% accuracy
- **Phase 2 Complete**: ✅ Date extraction with 100% accuracy on titles with dates (979/979)
- **Phase 3 Complete**: ✅ Report type extraction production-ready with 355 validated patterns
  - **GitHub Issue #11 Resolved**: Fixed acronym-embedded pattern processing
  - **Market-Aware Processing**: Dual workflows for different title classifications
  - **Database Quality Assured**: Comprehensive pattern validation and cleanup
- **Phase 4 Ready**: 🔄 Geographic Entity Detection ready for lean pattern-based refactoring
- **Enhanced Categorization**: 21 titles correctly identified as having no dates (not failures)
- **Pattern Libraries**: 64 date patterns + 355 report type patterns across multiple format types
- **Geographic Coverage**: ~9% of titles contain regional information  
- **Topic Preservation**: Complete technical compound retention
- **Overall Success Rate**: Exceeding 95-98% target accuracy (89% complete processing foundation)

### Latest Improvements (August 27, 2025):
- **Documentation Optimization**: CLAUDE.md reduced from 866 to 182 lines (79% reduction)
- **Modular Documentation**: 7 focused documentation files with @ reference system
- **Integration Error Prevention**: Comprehensive guides to prevent common debugging cycles
- **Component Verification**: Current class names and method signatures validated
- **Pre-Development Analysis**: Enhanced error prevention patterns and verification commands

## Sample Processing Results

**Input**: `"APAC & Middle East Personal Protective Equipment Market Size & Share Report, 2030"`

**Output**:
- **market_term_type**: "standard"
- **extracted_forecast_date_range**: "2030"
- **extracted_report_type**: "Market Size & Share Report"
- **extracted_regions**: ["APAC", "Middle East"] 
- **topic**: "Personal Protective Equipment"
- **topicName**: "personal-protective-equipment"
- **confidence_score**: 0.95

## Technology Stack

- **Database**: MongoDB Atlas with `pymongo` connectivity
- **Processing**: Python with regex-based pattern matching
- **Architecture**: Library-driven systematic extraction
- **Deployment**: AWS EC2 t3.large (~$70-80/month vs $900/month GPU alternatives)

## Contributing

Development follows systematic library-building approach:
1. **Follow Pre-Development Analysis**: Reference `documentation/claude-pre-development-analysis.md` to verify current class names and method signatures before creating scripts
2. **Use Component Integration Guide**: Reference `documentation/claude-component-integration.md` for correct initialization patterns and common error prevention
3. **Identify new edge cases** through analysis and testing
4. **Enhance libraries** with discovered patterns through MongoDB pattern_libraries collection
5. **Validate improvements** against known datasets with comprehensive test coverage
6. **Maintain backwards compatibility** through versioning and proper migration paths

### Development Workflow:
1. **Review current documentation** (CLAUDE.md and modular @ references)
2. **Verify component signatures** using provided grep commands
3. **Follow integration patterns** from verified examples
4. **Test thoroughly** before committing changes
5. **Update documentation** as needed to maintain accuracy

## License

MIT License - See LICENSE file for details

## Contact

For questions about implementation or collaboration opportunities, please create an issue in this repository.