#!/usr/bin/env python3

"""
GLiNER Model Setup Script
Downloads and configures GLiNER models for geographic entity detection.
Created for Market Research Title Parser project.
"""

import os
import sys
import subprocess
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def check_gliner_installation():
    """Check if GLiNER is installed."""
    try:
        import gliner
        logger.info(f"GLiNER is installed")
        return True
    except ImportError:
        logger.error("GLiNER is not installed")
        return False

def install_gliner():
    """Install GLiNER if not present."""
    try:
        logger.info("Installing GLiNER...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "gliner"])
        logger.info("GLiNER installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to install GLiNER: {e}")
        return False

def download_gliner_model(model_name):
    """Download and cache a GLiNER model."""
    try:
        logger.info(f"Loading GLiNER model: {model_name}")
        from gliner import GLiNER
        
        # Load model (this will download it if not cached)
        model = GLiNER.from_pretrained(model_name)
        
        # Test the model
        test_text = "North America technology market"
        test_labels = ["location", "region", "country"]
        
        entities = model.predict_entities(test_text, test_labels)
        logger.info(f"Model {model_name} loaded successfully")
        logger.info(f"Test entities detected: {entities}")
        
        return True
        
    except Exception as e:
        logger.error(f"Failed to load model {model_name}: {e}")
        return False

def setup_gliner_models():
    """Set up GLiNER models for geographic entity detection."""
    
    print("GLiNER Model Setup for Geographic Entity Detection")
    print("=" * 60)
    
    # Check/install GLiNER
    if not check_gliner_installation():
        if not install_gliner():
            print("❌ Failed to install GLiNER")
            return False
    
    # Models to install/cache
    models_to_install = [
        "urchade/gliner_base",           # Base model (good balance)
        "urchade/gliner_small",          # Smaller model (faster)
        "urchade/gliner_large",          # Larger model (more accurate)
    ]
    
    successful_installations = []
    failed_installations = []
    
    for model in models_to_install:
        print(f"\nLoading {model}...")
        if download_gliner_model(model):
            successful_installations.append(model)
            print(f"✅ {model} loaded and cached")
        else:
            failed_installations.append(model)
            print(f"❌ {model} loading failed")
    
    # Summary
    print("\n" + "=" * 60)
    print("GLINER MODEL SETUP SUMMARY")
    print("=" * 60)
    print(f"Successfully loaded: {len(successful_installations)} models")
    for model in successful_installations:
        print(f"  ✅ {model}")
    
    if failed_installations:
        print(f"Failed loadings: {len(failed_installations)} models")
        for model in failed_installations:
            print(f"  ❌ {model}")
    
    # Recommendations
    print(f"\nRECOMMENDATIONS:")
    if "urchade/gliner_base" in successful_installations:
        print("✅ Use 'urchade/gliner_base' for balanced performance")
    if "urchade/gliner_large" in successful_installations:
        print("✅ Use 'urchade/gliner_large' for highest accuracy")
    if "urchade/gliner_small" in successful_installations:
        print("✅ Use 'urchade/gliner_small' for fastest processing")
    
    if not successful_installations:
        print("❌ No models available - geographic detection will be pattern-only")
    
    return len(successful_installations) > 0

def create_model_config():
    """Create configuration file for GLiNER models."""
    
    config_content = """# GLiNER Model Configuration
# Geographic Entity Detection Settings

# Primary model for geographic entity recognition
# Options: urchade/gliner_small, urchade/gliner_base, urchade/gliner_large
PRIMARY_MODEL = "urchade/gliner_base"

# Fallback model if primary is not available
FALLBACK_MODEL = "urchade/gliner_small"

# Entity labels to use for geographic detection
GEOGRAPHIC_LABELS = [
    "location",
    "country", 
    "region",
    "city",
    "continent",
    "geographic entity",
    "place"
]

# Confidence threshold for model predictions
MIN_CONFIDENCE = 0.5

# Maximum number of entities to extract per text
MAX_ENTITIES = 10

# API Configuration (placeholder for Zettit Model Router)
# Set USE_API to True to use Zettit Model Router instead of local models
USE_API = False
API_ENDPOINT = "https://api.zettit.com/models/gliner"
API_KEY = None  # Set from environment variable

# Model performance settings
MODEL_SETTINGS = {
    "urchade/gliner_small": {
        "max_length": 384,
        "batch_size": 8,
        "description": "Fast processing, lower accuracy"
    },
    "urchade/gliner_base": {
        "max_length": 512,
        "batch_size": 4,
        "description": "Balanced performance and accuracy"
    },
    "urchade/gliner_large": {
        "max_length": 768,
        "batch_size": 2,
        "description": "Highest accuracy, slower processing"
    }
}
"""
    
    config_path = Path(__file__).parent / "gliner_config.py"
    
    try:
        with open(config_path, 'w') as f:
            f.write(config_content)
        logger.info(f"Configuration file created: {config_path}")
        print(f"✅ Configuration file created: {config_path}")
        return True
    except Exception as e:
        logger.error(f"Failed to create configuration file: {e}")
        print(f"❌ Failed to create configuration file: {e}")
        return False

def main():
    """Main setup function."""
    
    success = setup_gliner_models()
    
    if success:
        create_model_config()
        print("\n✅ GLiNER setup completed successfully!")
        print("\nNext steps:")
        print("1. Models are cached and ready for geographic entity detection")
        print("2. Use 'urchade/gliner_base' for balanced performance")
        print("3. Configure API settings in gliner_config.py if needed")
    else:
        print("\n❌ GLiNER setup failed")
        print("Please check your internet connection and try again")

if __name__ == "__main__":
    main()