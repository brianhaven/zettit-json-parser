#!/usr/bin/env python3

"""
spaCy Model Setup Script
Downloads and configures spaCy models for geographic entity detection.
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

def check_spacy_installation():
    """Check if spaCy is installed."""
    try:
        import spacy
        logger.info(f"spaCy version {spacy.__version__} is installed")
        return True
    except ImportError:
        logger.error("spaCy is not installed")
        return False

def install_spacy():
    """Install spaCy if not present."""
    try:
        logger.info("Installing spaCy...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "spacy"])
        logger.info("spaCy installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to install spaCy: {e}")
        return False

def download_spacy_model(model_name):
    """Download a specific spaCy model."""
    try:
        logger.info(f"Downloading spaCy model: {model_name}")
        subprocess.check_call([sys.executable, "-m", "spacy", "download", model_name])
        logger.info(f"Model {model_name} downloaded successfully")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to download model {model_name}: {e}")
        return False

def verify_model_installation(model_name):
    """Verify that a model is properly installed."""
    try:
        import spacy
        nlp = spacy.load(model_name)
        
        # Test with a simple geographic entity
        test_text = "North America technology market"
        doc = nlp(test_text)
        
        entities = [(ent.text, ent.label_) for ent in doc.ents]
        logger.info(f"Model {model_name} verification successful")
        logger.info(f"Test entities detected: {entities}")
        return True
        
    except Exception as e:
        logger.error(f"Model {model_name} verification failed: {e}")
        return False

def setup_spacy_models():
    """Set up spaCy models for geographic entity detection."""
    
    print("spaCy Model Setup for Geographic Entity Detection")
    print("=" * 60)
    
    # Check/install spaCy
    if not check_spacy_installation():
        if not install_spacy():
            print("❌ Failed to install spaCy")
            return False
    
    # Models to install (both options as requested)
    models_to_install = [
        "en_core_web_sm",  # Small model (faster, less accurate)
        "en_core_web_lg"   # Large model (slower, more accurate) - RECOMMENDED
    ]
    
    successful_installations = []
    failed_installations = []
    
    for model in models_to_install:
        print(f"\nInstalling {model}...")
        if download_spacy_model(model):
            if verify_model_installation(model):
                successful_installations.append(model)
                print(f"✅ {model} installed and verified")
            else:
                failed_installations.append(model)
                print(f"❌ {model} installed but verification failed")
        else:
            failed_installations.append(model)
            print(f"❌ {model} installation failed")
    
    # Summary
    print("\n" + "=" * 60)
    print("SPACY MODEL SETUP SUMMARY")
    print("=" * 60)
    print(f"Successfully installed: {len(successful_installations)} models")
    for model in successful_installations:
        print(f"  ✅ {model}")
    
    if failed_installations:
        print(f"Failed installations: {len(failed_installations)} models")
        for model in failed_installations:
            print(f"  ❌ {model}")
    
    # Recommendations
    print(f"\nRECOMMENDATIONS:")
    if "en_core_web_lg" in successful_installations:
        print("✅ Use 'en_core_web_lg' for best geographic entity detection accuracy")
    elif "en_core_web_sm" in successful_installations:
        print("⚠️  Use 'en_core_web_sm' for faster processing (lower accuracy)")
    else:
        print("❌ No models available - geographic detection will be pattern-only")
    
    return len(successful_installations) > 0

def create_model_config():
    """Create configuration file for spaCy models."""
    
    config_content = """# spaCy Model Configuration
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
"""
    
    config_path = Path(__file__).parent / "spacy_config.py"
    
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
    
    success = setup_spacy_models()
    
    if success:
        create_model_config()
        print("\n✅ spaCy setup completed successfully!")
        print("\nNext steps:")
        print("1. Models are ready for geographic entity detection")
        print("2. Use 'en_core_web_lg' for best accuracy")
        print("3. Configure API settings in spacy_config.py if needed")
    else:
        print("\n❌ spaCy setup failed")
        print("Please check your internet connection and try again")

if __name__ == "__main__":
    main()