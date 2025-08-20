THREE-METHOD GEOGRAPHIC DETECTION COMPARISON
================================================================================
Analysis Date (PDT): 2025-08-20 13:20:43 PDT

OVERALL PERFORMANCE COMPARISON
--------------------------------------------------
Pattern Matching Detection Rate: 23.60%
spaCy en_core_web_md Detection Rate: 1.40%
spaCy en_core_web_lg Detection Rate: 1.40%

PERFORMANCE RANKING
------------------------------
1. Pattern Matching: 23.60%
2. spaCy MD: 1.40%
3. spaCy LG: 1.40%

ENTITY DETECTION OVERLAP ANALYSIS
--------------------------------------------------
Entities found by all three methods: 5
Entities found by Pattern + MD only: 2
Entities found by Pattern + LG only: 0
Entities found by MD + LG only: 1
Entities found only by Pattern Matching: 4
Entities found only by spaCy MD: 0
Entities found only by spaCy LG: 0

ENTITIES FOUND BY ALL THREE METHODS
----------------------------------------
  Americas: Pattern(8) | MD(1) | LG(1)
  Asia: Pattern(1) | MD(1) | LG(1)
  Asia Pacific: Pattern(43) | MD(1) | LG(2)
  Australia: Pattern(4) | MD(2) | LG(3)
  Middle East: Pattern(2) | MD(1) | LG(1)

ENTITIES FOUND ONLY BY PATTERN MATCHING
----------------------------------------
  ASEAN: 1 detections
  Europe: 2 detections
  Global: 54 detections
  United States: 1 detections

TITLE-LEVEL DETECTION COMPARISON
--------------------------------------------------
Titles with regions detected by all three: 5
Titles detected only by Pattern Matching: 109
Titles detected only by spaCy MD: 0
Titles detected only by spaCy LG: 0

EXAMPLE TITLES DETECTED ONLY BY PATTERN MATCHING
--------------------------------------------------
  "Anti Glare Glass Market Size & Share, Global Industry Report, 2025"
    Regions: ['Global']
  "Asia Pacific Disposable Gloves Market, Industry Report, 2030"
    Regions: ['Asia Pacific']
  "Aerosol Refrigerants Market Size, Share, Global Industry Report, 2025"
    Regions: ['Global']
  "Ambient Energy Harvester Market Size, Global Industry Report, 2025"
    Regions: ['Global']
  "Advanced Energy Market Size & Trends, Global Industry Report, 2025"
    Regions: ['Global']

SPACY MODEL COMPARISON (MD vs LG)
--------------------------------------------------
MD Detection Rate: 1.40%
LG Detection Rate: 1.40%
Both spaCy models perform equally