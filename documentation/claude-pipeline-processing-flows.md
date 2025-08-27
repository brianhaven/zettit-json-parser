# Complete Pipeline Processing Flow

**CRITICAL:** The processing logic differs significantly between market term and standard classifications.

## Market Term Classification Pipeline Flow

**Example:** "Artificial Intelligence (AI) Market in Automotive Outlook & Trends, 2025-2035"

**Stage 1 - Market Term Classification (01_market_term_classifier_v1.py):**
- Input: "Artificial Intelligence (AI) Market in Automotive Outlook & Trends, 2025-2035"
- Detection: "Market in" pattern found in database
- Classification: `market_in`
- Output: Same title + `market_in` classification

**Stage 2 - Date Extraction (02_date_extractor_v1.py):**
- Input: "Artificial Intelligence (AI) Market in Automotive Outlook & Trends, 2025-2035"
- Detection: "2025-2035" matches date range patterns
- Extraction: Date = "2025-2035"
- Output: "Artificial Intelligence (AI) Market in Automotive Outlook & Trends" + date

**Stage 3 - Market-Aware Report Type Extraction (03_report_type_extractor_v2.py):**
- Input: "Artificial Intelligence (AI) Market in Automotive Outlook & Trends" + `market_in`
- **Market Term Processing Logic:**
  1. **Extract "Market"** from "Market in" phrase
  2. **Preserve "in Automotive"** for next pipeline stage
  3. **Search remaining text** for report patterns **without "Market" prefix**
  4. **Find "Outlook & Trends"** in database patterns (excluding Market prefix)
  5. **Reconstruct:** "Market" + "Outlook & Trends" = **"Market Outlook & Trends"**
- Output: Report type = "Market Outlook & Trends", Pipeline forward = "Artificial Intelligence (AI) in Automotive"

**Stage 4 - Geographic Entity Detection (04_geographic_entity_detector_v1.py):**
- Input: "Artificial Intelligence (AI) in Automotive"
- Detection: "Automotive" may be classified as industry/context (not geographic)
- Output: Pipeline forward = "Artificial Intelligence (AI) in Automotive" (no geographic regions found)

**Stage 5 - Topic Extraction (05_topic_extractor_v1.py):**
- Input: "Artificial Intelligence (AI) in Automotive"
- Processing: No dates, report types, or regions to remove
- Output: topic = "Artificial Intelligence (AI) in Automotive", topicName = "artificial-intelligence-ai-in-automotive"

## Standard Classification Pipeline Flow

**Example:** "APAC Personal Protective Equipment Market Analysis, 2024-2029"

**Stage 1 - Market Term Classification (01_market_term_classifier_v1.py):**
- Input: "APAC Personal Protective Equipment Market Analysis, 2024-2029"
- Detection: No market term patterns found ("Market Analysis" is standard)
- Classification: `standard`
- Output: Same title + `standard` classification

**Stage 2 - Date Extraction (02_date_extractor_v1.py):**
- Input: "APAC Personal Protective Equipment Market Analysis, 2024-2029"
- Detection: "2024-2029" matches date range patterns
- Extraction: Date = "2024-2029"
- Output: "APAC Personal Protective Equipment Market Analysis" + date

**Stage 3 - Standard Report Type Extraction (03_report_type_extractor_v2.py):**
- Input: "APAC Personal Protective Equipment Market Analysis" + `standard`
- **Standard Processing Logic:**
  1. **Direct pattern matching** on complete remaining title
  2. **Find "Market Analysis"** in database patterns (complete match)
  3. **No rearrangement needed**
- Output: Report type = "Market Analysis", Pipeline forward = "APAC Personal Protective Equipment"

**Stage 4 - Geographic Entity Detection (04_geographic_entity_detector_v1.py):**
- Input: "APAC Personal Protective Equipment"
- Detection: "APAC" found in geographic patterns
- Extraction: Region = "APAC"
- Output: Pipeline forward = "Personal Protective Equipment"

**Stage 5 - Topic Extraction (05_topic_extractor_v1.py):**
- Input: "Personal Protective Equipment"
- Processing: Systematic removal complete - this IS the topic
- Output: topic = "Personal Protective Equipment", topicName = "personal-protective-equipment"

## Processing Philosophy
- **Market terms:** Extraction, rearrangement, and reconstruction
- **Standard titles:** Systematic removal in sequence (dates, report types, regions)
- **What remains IS the topic** (regardless of internal punctuation)
- **Track performance metrics** in MongoDB for continuous improvement