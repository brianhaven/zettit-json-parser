# spaCy Model Configuration
# Geographic Entity Detection Settings

# Primary model for geographic entity recognition
# Options: en_core_web_sm, en_core_web_lg
PRIMARY_MODEL = "en_core_web_lg"

# Fallback model if primary is not available
FALLBACK_MODEL = "en_core_web_sm"

# Entity types to extract for geographic detection
# GPE = Geopolitical entities (countries, cities, states)
# LOC = Locations (mountain ranges, bodies of water)
GEOGRAPHIC_ENTITY_TYPES = ["GPE", "LOC"]

# Confidence threshold for model predictions
MIN_CONFIDENCE = 0.7

# API Configuration (placeholder for Zettit Model Router)
# Set USE_API to True to use Zettit Model Router instead of local models
USE_API = False
API_ENDPOINT = "https://api.zettit.com/models/spacy"
API_KEY = None  # Set from environment variable
