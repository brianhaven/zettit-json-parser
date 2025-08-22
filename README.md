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
3. **Report Type Processing**: Extract descriptors after "Market" keyword (`extracted_report_type`)
4. **Geographic Entity Detection**: Compound-priority matching from MongoDB libraries (`extracted_regions`)
5. **Topic Extraction**: Preserve complete technical compounds (`topic` and `topicName`)

### MongoDB-Based Libraries
- **Pattern Libraries Collection**: Real-time updatable pattern storage with performance tracking
- **Geographic Entities**: 363+ regions, countries, acronyms with compound-first processing
- **Market Term Exceptions**: Handle "After Market", "Marketplace", edge cases
- **Date Pattern Recognition**: Standard, bracketed, and embedded date formats
- **Report Type Standardization**: Normalized classification system

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

### Output File Format
All analysis outputs include dual timestamps:
```
**Analysis Date (PDT):** 2025-08-19 15:30:45 PDT  
**Analysis Date (UTC):** 2025-08-19 22:30:45 UTC
```

### Processing Philosophy
**"Systematic Removal"**: Remove known patterns (dates, report types, regions) systematically using MongoDB-based libraries. What remains IS the topic, regardless of internal punctuation or special characters.

### Database Architecture
**MongoDB Atlas Collections:**
- `markets_raw`: Source data (19,558+ titles)
- `pattern_libraries`: Real-time pattern storage with performance tracking
- `markets_processed`: Extracted results with confidence scoring

## Performance Metrics

- **Dataset Size**: 19,558 market research titles
- **Phase 1 Complete**: Market classification with 100% accuracy
- **Phase 2 Complete**: Date extraction with 100% accuracy on titles with dates (979/979)
- **Enhanced Categorization**: 21 titles correctly identified as having no dates (not failures)
- **Pattern Library**: 64 date patterns across 4 format types (enhanced from 45)
- **Geographic Coverage**: ~9% of titles contain regional information  
- **Topic Preservation**: Complete technical compound retention
- **Overall Success Rate**: Exceeding 95-98% target accuracy

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
1. Identify new edge cases through analysis
2. Enhance libraries with discovered patterns  
3. Validate improvements against known datasets
4. Maintain backwards compatibility through versioning

## License

MIT License - See LICENSE file for details

## Contact

For questions about implementation or collaboration opportunities, please create an issue in this repository.