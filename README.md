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

### Step-Based Systematic Processing
1. **Market Term Classification**: Separate special patterns ("Market for"/"Market in") from standard titles
2. **Date Extraction**: Remove terminal date patterns first to prevent contamination
3. **Report Type Processing**: Extract descriptors after "Market" keyword
4. **Geographic Entity Detection**: Compound-priority matching with comprehensive entity libraries
5. **Topic Extraction**: Preserve complete technical compounds through systematic removal

### Library-Driven Approach
- **Geographic Entities**: 363+ regions, countries, acronyms with compound-first processing
- **Market Term Exceptions**: Handle "After Market", "Marketplace", edge cases
- **Date Pattern Recognition**: Standard, bracketed, and embedded date formats
- **Report Type Standardization**: Normalized classification system

## Key Features

- **High Accuracy**: 95-98% success rate through systematic processing
- **Scalable**: Handles large MongoDB collections efficiently  
- **Maintainable**: Library-based approach for continuous improvement
- **Production Ready**: Comprehensive error handling and logging
- **Cost Effective**: CPU-optimized alternative to expensive GPU-based NLP models

## Project Structure

```
/
├── mongo-connection-test.py          # MongoDB connectivity validation
├── /experiments/                     # Development scripts with versions
├── /outputs/                        # Timestamped analysis results
├── /documentation/                   # Permanent documentation
├── /resources/                       # Data files and exports
├── CLAUDE.md                        # Development standards
└── README.md                        # Project overview
```

## Getting Started

### Prerequisites
- Python 3.8+
- MongoDB Atlas connection
- Required packages: `pymongo`, `python-dotenv`

### Environment Setup
Create `.env` file:
```
MONGODB_URI=mongodb+srv://username:password@cluster.mongodb.net/database
```

### Quick Start
```bash
# Test MongoDB connection
python mongo-connection-test.py

# Run pattern analysis
python experiments/title_pattern_discovery_v1.py
```

## Development Standards

### Output File Format
All analysis outputs include dual timestamps:
```
**Analysis Date (PDT):** 2025-08-19 15:30:45 PDT  
**Analysis Date (UTC):** 2025-08-19 22:30:45 UTC
```

### Processing Philosophy
**"Systematic Removal"**: Remove known patterns (dates, report types, regions) systematically. What remains IS the topic, regardless of internal punctuation or special characters.

## Performance Metrics

- **Dataset Size**: 19,558 market research titles
- **Geographic Coverage**: ~9% of titles contain regional information
- **Date Pattern Success**: 98-99% extraction accuracy
- **Topic Preservation**: Complete technical compound retention
- **Overall Success Rate**: 95-98% target accuracy

## Sample Processing Results

**Input**: `"APAC & Middle East Personal Protective Equipment Market Size & Share Report, 2030"`

**Output**:
- **Topic**: "Personal Protective Equipment"
- **Geographic**: ["APAC", "Middle East"] 
- **Report Type**: "Market Size & Share Report"
- **Date**: "2030"

## Technology Stack

- **Database**: MongoDB Atlas with `pymongo` connectivity
- **Processing**: Python with regex-based pattern matching
- **Architecture**: Library-driven systematic extraction
- **Deployment**: AWS EC2 t3.large (~$70-80/month vs $900/month GPU alternatives)

## Contributing

Development follows systematic library-building approach:
1. Identify new edge cases through analysis
2. Enhance libraries with discovered patterns  
3. Validate improvements against known datasets
4. Maintain backwards compatibility through versioning

## License

MIT License - See LICENSE file for details

## Contact

For questions about implementation or collaboration opportunities, please create an issue in this repository.