#!/usr/bin/env python3

"""
Market Term Classification System v1.0
Classifies market research titles into different categories based on market term patterns.
Created for Market Research Title Parser project.
"""

import re
import logging
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum
from datetime import datetime, timezone
import pytz

# Import Pattern Library Manager components
import importlib.util
import sys
import os

# Dynamic import for pattern library manager (filename starts with numbers)
try:
    pattern_manager_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '00b_pattern_library_manager_v1.py')
    spec = importlib.util.spec_from_file_location("pattern_library_manager_v1", pattern_manager_path)
    pattern_module = importlib.util.module_from_spec(spec)
    sys.modules["pattern_library_manager_v1"] = pattern_module
    spec.loader.exec_module(pattern_module)
    PatternLibraryManager = pattern_module.PatternLibraryManager
    PatternType = pattern_module.PatternType
except Exception as e:
    raise ImportError(f"Could not import PatternLibraryManager: {e}") from e

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class MarketTermType(Enum):
    """Enumeration of market term classification types."""
    MARKET_FOR = "market_for"
    MARKET_IN = "market_in"
    STANDARD = "standard"
    AMBIGUOUS = "ambiguous"

@dataclass
class ClassificationResult:
    """Result of market term classification."""
    title: str
    market_type: MarketTermType
    confidence: float
    matched_pattern: Optional[str]
    preprocessing_applied: List[str]
    notes: Optional[str] = None

@dataclass
class ClassificationStats:
    """Statistics for classification results."""
    total_classified: int
    market_for_count: int
    market_in_count: int
    standard_count: int
    ambiguous_count: int
    market_for_percentage: float
    market_in_percentage: float
    standard_percentage: float

class MarketTermClassifier:
    """
    Market Term Classification System for market research titles.
    
    Classifies titles into three main categories:
    - Market for patterns (~0.2% of dataset)
    - Market in patterns (~0.1% of dataset)
    - Standard market patterns (~99.7% of dataset)
    """
    
    def __init__(self, pattern_library_manager=None):
        """
        Initialize the Market Term Classifier.
        
        Args:
            pattern_library_manager: PatternLibraryManager instance for pattern retrieval.
                                   If None, will create a new instance automatically.
        """
        # Initialize or use provided pattern library manager
        if pattern_library_manager is None:
            try:
                self.pattern_library_manager = PatternLibraryManager()
                logger.info("Created new PatternLibraryManager instance")
            except Exception as e:
                raise RuntimeError(f"Failed to initialize PatternLibraryManager: {e}. Ensure MongoDB is available and MONGODB_URI is set.") from e
        else:
            self.pattern_library_manager = pattern_library_manager
            
        self.classification_stats = {
            'total_processed': 0,
            'market_for': 0,
            'market_in': 0,
            'standard': 0,
            'ambiguous': 0
        }
        
        # Initialize pattern variables
        self.market_for_pattern = None
        self.market_in_pattern = None
        
        # Load patterns from MongoDB - REQUIRED
        self._load_library_patterns()
    
    def _load_library_patterns(self) -> None:
        """Load patterns from MongoDB pattern library - REQUIRED."""
        try:
            # Load market term patterns from MongoDB
            market_patterns = self.pattern_library_manager.get_patterns(PatternType.MARKET_TERM)
            
            if not market_patterns:
                raise RuntimeError("No market term patterns found in MongoDB pattern_libraries collection")
            
            patterns_loaded = 0
            for pattern in market_patterns:
                if pattern.get('term') == 'Market for' and pattern.get('pattern'):
                    # Remove double escaping from MongoDB storage
                    self.market_for_pattern = pattern['pattern'].replace('\\\\', '\\')
                    patterns_loaded += 1
                    logger.debug(f"Loaded Market For pattern: {self.market_for_pattern}")
                elif pattern.get('term') == 'Market in' and pattern.get('pattern'):
                    # Remove double escaping from MongoDB storage
                    self.market_in_pattern = pattern['pattern'].replace('\\\\', '\\')
                    patterns_loaded += 1
                    logger.debug(f"Loaded Market In pattern: {self.market_in_pattern}")
            
            if not self.market_for_pattern:
                logger.warning("Market For pattern not found in database")
            if not self.market_in_pattern:
                logger.warning("Market In pattern not found in database")
            
            if patterns_loaded == 0:
                raise RuntimeError("No valid market term patterns loaded from database")
            
            logger.info(f"Successfully loaded {patterns_loaded} market term patterns from MongoDB")
            
        except Exception as e:
            raise RuntimeError(f"Failed to load patterns from MongoDB: {e}") from e
    
    def _get_timestamps(self) -> tuple:
        """Generate PDT and UTC timestamps."""
        utc_now = datetime.now(timezone.utc)
        pdt_tz = pytz.timezone('America/Los_Angeles')
        pdt_now = utc_now.astimezone(pdt_tz)
        
        pdt_str = pdt_now.strftime('%Y-%m-%d %H:%M:%S %Z')
        utc_str = utc_now.strftime('%Y-%m-%d %H:%M:%S UTC')
        
        return pdt_str, utc_str, utc_now
    
    def _preprocess_title(self, title: str) -> Tuple[str, List[str]]:
        """
        Preprocess title for classification.
        
        Args:
            title: Raw title text
            
        Returns:
            Tuple of (processed_title, list_of_preprocessing_steps)
        """
        preprocessing_steps = []
        processed_title = title
        
        # Original title preservation
        original_title = title
        
        # Step 1: Strip whitespace
        processed_title = processed_title.strip()
        preprocessing_steps.append("whitespace_trimmed")
        
        # Step 2: Normalize multiple spaces
        processed_title = re.sub(r'\s+', ' ', processed_title)
        preprocessing_steps.append("spaces_normalized")
        
        # Step 3: Handle special characters that might interfere with matching
        # But preserve them for context
        
        # Step 4: Convert to lowercase for pattern matching (but preserve original case for output)
        processed_title_lower = processed_title.lower()
        
        preprocessing_steps.append("lowercased_for_matching")
        
        logger.debug(f"Preprocessed '{original_title}' -> '{processed_title}' (steps: {preprocessing_steps})")
        
        return processed_title_lower, preprocessing_steps
    
    def _calculate_confidence(self, title: str, market_type: MarketTermType, 
                             matched_pattern: Optional[str]) -> float:
        """
        Calculate confidence score for classification.
        
        Args:
            title: Original title
            market_type: Classified market type
            matched_pattern: Pattern that matched
            
        Returns:
            Confidence score between 0.0 and 1.0
        """
        confidence = 0.5  # Base confidence
        
        if market_type == MarketTermType.AMBIGUOUS:
            confidence = 0.2  # Very low confidence for ambiguous cases
        
        elif matched_pattern:
            # Higher confidence for specific pattern matches
            if market_type == MarketTermType.MARKET_FOR:
                # Check if pattern is very specific
                if re.search(r'\bmarket\s+for\s+[a-zA-Z]', title.lower()):
                    confidence = 0.95
                else:
                    confidence = 0.85
            
            elif market_type == MarketTermType.MARKET_IN:
                # Check if pattern is very specific
                if re.search(r'\bmarket\s+in\s+[a-zA-Z]', title.lower()):
                    confidence = 0.95
                else:
                    confidence = 0.85
            
            elif market_type == MarketTermType.STANDARD:
                # Higher confidence for common market research terms
                high_confidence_terms = [
                    'market size', 'market share', 'market analysis', 'market report',
                    'market outlook', 'market forecast', 'market trends'
                ]
                
                if any(term in title.lower() for term in high_confidence_terms):
                    confidence = 0.95
                else:
                    confidence = 0.8
        
        return round(confidence, 3)
    
    def is_market_for_pattern(self, title: str) -> Tuple[bool, Optional[str], float]:
        """
        Check if title matches 'Market for' pattern.
        
        Args:
            title: Title to check
            
        Returns:
            Tuple of (is_match, matched_pattern, confidence)
        """
        if not self.market_for_pattern:
            logger.debug("No Market For pattern available")
            return False, None, 0.0
            
        processed_title, _ = self._preprocess_title(title)
        
        # Check for market for pattern
        match = re.search(self.market_for_pattern, processed_title, re.IGNORECASE)
        if match:
            confidence = 0.95  # High confidence for exact pattern match
            logger.debug(f"Market for pattern matched in '{title}'")
            return True, self.market_for_pattern, confidence
        
        return False, None, 0.0
    
    def is_market_in_pattern(self, title: str) -> Tuple[bool, Optional[str], float]:
        """
        Check if title matches 'Market in' pattern.
        
        Args:
            title: Title to check
            
        Returns:
            Tuple of (is_match, matched_pattern, confidence)
        """
        if not self.market_in_pattern:
            logger.debug("No Market In pattern available")
            return False, None, 0.0
            
        processed_title, _ = self._preprocess_title(title)
        
        # Check for market in pattern
        match = re.search(self.market_in_pattern, processed_title, re.IGNORECASE)
        if match:
            confidence = 0.95  # High confidence for exact pattern match
            logger.debug(f"Market in pattern matched in '{title}'")
            return True, self.market_in_pattern, confidence
        
        return False, None, 0.0
    
    
    def classify(self, title: str) -> ClassificationResult:
        """
        Classify a market research title into market term categories.
        
        Simple classification:
        1. Check for "Market for" pattern (~0.2% of dataset)
        2. Check for "Market in" pattern (~0.1% of dataset)  
        3. Everything else goes to standard processing (~99.7% of dataset)
        
        Args:
            title: Title to classify
            
        Returns:
            ClassificationResult with classification details
        """
        if not title or not title.strip():
            return ClassificationResult(
                title=title,
                market_type=MarketTermType.STANDARD,
                confidence=0.9,
                matched_pattern=None,
                preprocessing_applied=[],
                notes="Empty title - routed to standard processing"
            )
        
        processed_title, preprocessing_steps = self._preprocess_title(title)
        
        # Track processing
        self.classification_stats['total_processed'] += 1
        
        # Check for specific patterns first
        is_market_for, for_pattern, for_confidence = self.is_market_for_pattern(title)
        is_market_in, in_pattern, in_confidence = self.is_market_in_pattern(title)
        
        # Determine classification
        if is_market_for and is_market_in:
            # Ambiguous case - both patterns match (very rare)
            self.classification_stats['ambiguous'] += 1
            return ClassificationResult(
                title=title,
                market_type=MarketTermType.AMBIGUOUS,
                confidence=0.2,
                matched_pattern=f"Both: {for_pattern}, {in_pattern}",
                preprocessing_applied=preprocessing_steps,
                notes="Title matches both 'market for' and 'market in' patterns - needs manual review"
            )
        
        elif is_market_for:
            # Market for pattern (~0.2% of dataset)
            self.classification_stats['market_for'] += 1
            return ClassificationResult(
                title=title,
                market_type=MarketTermType.MARKET_FOR,
                confidence=for_confidence,
                matched_pattern=for_pattern,
                preprocessing_applied=preprocessing_steps,
                notes="Requires concatenation processing"
            )
        
        elif is_market_in:
            # Market in pattern (~0.1% of dataset)
            self.classification_stats['market_in'] += 1
            return ClassificationResult(
                title=title,
                market_type=MarketTermType.MARKET_IN,
                confidence=in_confidence,
                matched_pattern=in_pattern,
                preprocessing_applied=preprocessing_steps,
                notes="Requires context integration processing"
            )
        
        else:
            # Everything else - standard processing (~99.7% of dataset)
            self.classification_stats['standard'] += 1
            return ClassificationResult(
                title=title,
                market_type=MarketTermType.STANDARD,
                confidence=0.9,
                matched_pattern=None,
                preprocessing_applied=preprocessing_steps,
                notes="Standard processing - systematic pattern removal approach"
            )
    
    def classify_batch(self, titles: List[str]) -> List[ClassificationResult]:
        """
        Classify a batch of titles.
        
        Args:
            titles: List of titles to classify
            
        Returns:
            List of ClassificationResult objects
        """
        results = []
        
        logger.info(f"Starting batch classification of {len(titles)} titles")
        
        for i, title in enumerate(titles):
            if i > 0 and i % 1000 == 0:
                logger.info(f"Processed {i}/{len(titles)} titles...")
            
            result = self.classify(title)
            results.append(result)
        
        logger.info(f"Completed batch classification of {len(titles)} titles")
        return results
    
    def get_classification_statistics(self) -> ClassificationStats:
        """
        Get current classification statistics.
        
        Returns:
            ClassificationStats object with current statistics
        """
        total = self.classification_stats['total_processed']
        
        if total == 0:
            return ClassificationStats(
                total_classified=0,
                market_for_count=0,
                market_in_count=0,
                standard_count=0,
                ambiguous_count=0,
                market_for_percentage=0.0,
                market_in_percentage=0.0,
                standard_percentage=0.0
            )
        
        return ClassificationStats(
            total_classified=total,
            market_for_count=self.classification_stats['market_for'],
            market_in_count=self.classification_stats['market_in'],
            standard_count=self.classification_stats['standard'],
            ambiguous_count=self.classification_stats['ambiguous'],
            market_for_percentage=round((self.classification_stats['market_for'] / total) * 100, 3),
            market_in_percentage=round((self.classification_stats['market_in'] / total) * 100, 3),
            standard_percentage=round((self.classification_stats['standard'] / total) * 100, 3)
        )
    
    def reset_statistics(self) -> None:
        """Reset classification statistics."""
        self.classification_stats = {
            'total_processed': 0,
            'market_for': 0,
            'market_in': 0,
            'standard': 0,
            'ambiguous': 0
        }
        logger.info("Classification statistics reset")
    
    def export_classification_report(self, filename: Optional[str] = None) -> str:
        """
        Export classification statistics to a formatted report.
        
        Args:
            filename: Optional filename to save report to
            
        Returns:
            Report content as string
        """
        pdt_time, utc_time, _ = self._get_timestamps()
        stats = self.get_classification_statistics()
        
        report = f"""Market Term Classification Report
{'='*50}
Analysis Date (PDT): {pdt_time}
Analysis Date (UTC): {utc_time}
{'='*50}

Classification Summary:
  Total Titles Processed: {stats.total_classified:,}
  
  Market Term Distribution:
    - Market For Patterns:    {stats.market_for_count:6,} ({stats.market_for_percentage:6.3f}%)
    - Market In Patterns:     {stats.market_in_count:6,} ({stats.market_in_percentage:6.3f}%)
    - Standard Processing:    {stats.standard_count:6,} ({stats.standard_percentage:6.3f}%)
    - Ambiguous Cases:        {stats.ambiguous_count:6,} ({(stats.ambiguous_count/stats.total_classified)*100:6.3f}%)

Expected vs Actual Distribution:
  Market For:  Expected ~0.2%, Actual {stats.market_for_percentage:.3f}%
  Market In:   Expected ~0.1%, Actual {stats.market_in_percentage:.3f}%
  Standard:    Expected ~99.7%, Actual {stats.standard_percentage:.3f}%

Classification Performance:
  Specific Patterns Detected: {stats.market_for_count + stats.market_in_count:,}
  Standard Processing Rate:   {stats.standard_percentage:.2f}%
  
Classification Quality:
  Ambiguous Cases:         {(stats.ambiguous_count/stats.total_classified)*100:.3f}%
  Standard Processing:     {stats.standard_percentage:.2f}%
"""
        
        if filename:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(report)
            logger.info(f"Classification report exported to {filename}")
        
        return report


def demo_classification():
    """Demonstrate Market Term Classifier functionality."""
    
    print("Market Term Classification System Demo")
    print("=" * 50)
    
    # Sample titles for testing
    sample_titles = [
        # Market for patterns
        "Global Market for Advanced Materials in Aerospace, 2030",
        "Asia Pacific Market for Electric Vehicles Report",
        "Market for Renewable Energy Systems in Europe",
        
        # Market in patterns
        "Pharmaceutical Market in North America Analysis",
        "Technology Market in Asia Pacific, 2025-2030",
        "Market in China for Consumer Electronics",
        
        # Standard market patterns
        "Global Artificial Intelligence Market Size & Share Report, 2030",
        "APAC Personal Protective Equipment Market Analysis",
        "Automotive Battery Market Outlook 2031",
        "Blockchain Technology Market Trends Report",
        "Healthcare Market Research and Insights",
        
        # Non-market titles
        "Annual Financial Report 2023",
        "Technology Innovation Trends",
        "Global Economic Outlook",
        
        # Confusing patterns that should be excluded
        "After Market Services Industry Report",
        "Marketplace Platform Analysis",
        "Stock Market Performance Review",
        "Farmers Market Local Analysis",
    ]
    
    try:
        # Initialize classifier
        classifier = MarketTermClassifier()
        
        print("\n1. Individual Classification Examples:")
        print("-" * 40)
        
        for title in sample_titles[:6]:  # Show first 6 examples
            result = classifier.classify(title)
            print(f"Title: {title[:60]}...")
            print(f"  Type: {result.market_type.value}")
            print(f"  Confidence: {result.confidence:.3f}")
            print(f"  Pattern: {result.matched_pattern}")
            print(f"  Notes: {result.notes}")
            print()
        
        # Batch classification
        print("2. Batch Classification Results:")
        print("-" * 40)
        
        batch_results = classifier.classify_batch(sample_titles)
        
        # Get statistics
        stats = classifier.get_classification_statistics()
        
        print(f"Total Processed: {stats.total_classified}")
        print(f"Market For: {stats.market_for_count} ({stats.market_for_percentage:.2f}%)")
        print(f"Market In: {stats.market_in_count} ({stats.market_in_percentage:.2f}%)")
        print(f"Standard: {stats.standard_count} ({stats.standard_percentage:.2f}%)")
        print(f"Ambiguous: {stats.ambiguous_count} ({(stats.ambiguous_count/stats.total_classified)*100:.2f}%)")
        
        # Export report
        print("\n3. Detailed Classification Report:")
        print("-" * 40)
        
        report = classifier.export_classification_report()
        print(report)
        
        print("✅ Market Term Classification demo completed successfully!")
        
    except Exception as e:
        print(f"❌ Demo failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    demo_classification()