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
    STANDARD = "standard"
    AMBIGUOUS = "ambiguous"
    
    @classmethod
    def create_dynamic_type(cls, term_name: str) -> str:
        """Create a dynamic market term type from database term."""
        # Convert "Market for" -> "market_for", "Market by" -> "market_by", etc.
        return term_name.lower().replace(" ", "_")

@dataclass
class ClassificationResult:
    """Result of market term classification."""
    title: str
    market_type: str  # Changed to string to support dynamic types
    confidence: float
    matched_pattern: Optional[str]
    preprocessing_applied: List[str]
    notes: Optional[str] = None

@dataclass
class ClassificationStats:
    """Statistics for classification results."""
    total_classified: int
    standard_count: int
    ambiguous_count: int
    standard_percentage: float
    market_term_stats: Dict[str, Dict[str, Any]]  # Dynamic market term statistics

class MarketTermClassifier:
    """
    Market Term Classification System for market research titles.
    
    Dynamically loads market term patterns from database and classifies titles:
    - Market-specific patterns (market_for, market_in, market_by, etc.) - loaded from database
    - Standard market patterns (everything else) - ~99% of dataset
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
            
        # Dynamic market term patterns loaded from database
        self.market_term_patterns = {}  # {term_name: pattern_regex}
        self.available_market_types = set()  # Dynamic set of available types
        
        # Initialize statistics with standard and ambiguous, market terms added dynamically
        self.classification_stats = {
            'total_processed': 0,
            'standard': 0,
            'ambiguous': 0
        }
        
        # Load patterns from MongoDB - REQUIRED
        self._load_library_patterns()
    
    def _load_library_patterns(self) -> None:
        """Load patterns from MongoDB pattern library dynamically - REQUIRED."""
        try:
            # Load market term patterns from MongoDB
            market_patterns = self.pattern_library_manager.get_patterns(PatternType.MARKET_TERM)
            
            if not market_patterns:
                raise RuntimeError("No market term patterns found in MongoDB pattern_libraries collection")
            
            patterns_loaded = 0
            for pattern in market_patterns:
                term = pattern.get('term')
                pattern_regex = pattern.get('pattern')
                active = pattern.get('active', True)
                
                if term and pattern_regex and active:
                    # Remove double escaping from MongoDB storage
                    clean_pattern = pattern_regex.replace('\\\\', '\\')
                    
                    # Store pattern with term name as key
                    self.market_term_patterns[term] = clean_pattern
                    
                    # Create dynamic market type and add to available types
                    market_type = MarketTermType.create_dynamic_type(term)
                    self.available_market_types.add(market_type)
                    
                    # Initialize statistics counter for this market type
                    self.classification_stats[market_type] = 0
                    
                    patterns_loaded += 1
                    logger.debug(f"Loaded pattern '{term}': {clean_pattern} -> {market_type}")
            
            if patterns_loaded == 0:
                raise RuntimeError("No valid market term patterns loaded from database")
            
            logger.info(f"Successfully loaded {patterns_loaded} market term patterns from MongoDB")
            logger.info(f"Available market types: {sorted(self.available_market_types)}")
            
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
    
    def _calculate_confidence(self, title: str, market_type: str, 
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
        
        if market_type == "ambiguous":
            confidence = 0.2  # Very low confidence for ambiguous cases
        
        elif matched_pattern:
            # Higher confidence for specific pattern matches
            if market_type in self.available_market_types:
                # Market-specific pattern match (market_for, market_in, market_by, etc.)
                # Check if pattern has context after the market term
                market_term_match = re.search(r'\bmarket\s+\w+\s+[a-zA-Z]', title.lower())
                if market_term_match:
                    confidence = 0.95
                else:
                    confidence = 0.85
            
            elif market_type == "standard":
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
    
    def check_market_term_patterns(self, title: str) -> List[Tuple[str, str, float]]:
        """
        Check title against all loaded market term patterns.
        
        Args:
            title: Title to check
            
        Returns:
            List of tuples: (term_name, market_type, confidence) for all matches
        """
        matches = []
        processed_title, _ = self._preprocess_title(title)
        
        for term_name, pattern in self.market_term_patterns.items():
            match = re.search(pattern, processed_title, re.IGNORECASE)
            if match:
                market_type = MarketTermType.create_dynamic_type(term_name)
                confidence = 0.95  # High confidence for exact pattern match
                matches.append((term_name, market_type, confidence))
                logger.debug(f"Pattern '{term_name}' matched in '{title}' -> {market_type}")
        
        return matches
    
    
    def classify(self, title: str) -> ClassificationResult:
        """
        Classify a market research title into market term categories.
        
        Dynamic classification:
        1. Check against all loaded market term patterns from database
        2. Handle multiple matches as ambiguous cases
        3. Everything else goes to standard processing (~99% of dataset)
        
        Args:
            title: Title to classify
            
        Returns:
            ClassificationResult with classification details
        """
        if not title or not title.strip():
            return ClassificationResult(
                title=title,
                market_type="standard",
                confidence=0.9,
                matched_pattern=None,
                preprocessing_applied=[],
                notes="Empty title - routed to standard processing"
            )
        
        processed_title, preprocessing_steps = self._preprocess_title(title)
        
        # Track processing
        self.classification_stats['total_processed'] += 1
        
        # Check against all loaded market term patterns
        pattern_matches = self.check_market_term_patterns(title)
        
        # Determine classification based on matches
        if len(pattern_matches) > 1:
            # Ambiguous case - multiple patterns match (very rare)
            self.classification_stats['ambiguous'] += 1
            matched_terms = [match[0] for match in pattern_matches]
            return ClassificationResult(
                title=title,
                market_type="ambiguous",
                confidence=0.2,
                matched_pattern=f"Multiple: {', '.join(matched_terms)}",
                preprocessing_applied=preprocessing_steps,
                notes=f"Title matches multiple market term patterns - needs manual review: {matched_terms}"
            )
        
        elif len(pattern_matches) == 1:
            # Single market term pattern match
            term_name, market_type, confidence = pattern_matches[0]
            self.classification_stats[market_type] += 1
            
            # Determine processing notes based on market type
            if market_type == "market_for":
                notes = "Requires concatenation processing"
            elif market_type in ["market_in", "market_by"]:
                notes = f"Requires context integration processing for {term_name.lower()}"
            else:
                notes = f"Market term pattern detected: {term_name}"
            
            return ClassificationResult(
                title=title,
                market_type=market_type,
                confidence=confidence,
                matched_pattern=self.market_term_patterns[term_name],
                preprocessing_applied=preprocessing_steps,
                notes=notes
            )
        
        else:
            # No market term patterns match - standard processing (~99% of dataset)
            self.classification_stats['standard'] += 1
            return ClassificationResult(
                title=title,
                market_type="standard",
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
                standard_count=0,
                ambiguous_count=0,
                standard_percentage=0.0,
                market_term_stats={}
            )
        
        # Build dynamic market term statistics
        market_term_stats = {}
        for market_type in self.available_market_types:
            count = self.classification_stats.get(market_type, 0)
            percentage = round((count / total) * 100, 3) if total > 0 else 0.0
            market_term_stats[market_type] = {
                'count': count,
                'percentage': percentage
            }
        
        return ClassificationStats(
            total_classified=total,
            standard_count=self.classification_stats['standard'],
            ambiguous_count=self.classification_stats['ambiguous'],
            standard_percentage=round((self.classification_stats['standard'] / total) * 100, 3),
            market_term_stats=market_term_stats
        )
    
    def reset_statistics(self) -> None:
        """Reset classification statistics."""
        self.classification_stats = {
            'total_processed': 0,
            'standard': 0,
            'ambiguous': 0
        }
        
        # Reset counters for all dynamic market types
        for market_type in self.available_market_types:
            self.classification_stats[market_type] = 0
            
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
        
        # Build market term distribution section dynamically
        market_term_lines = []
        total_market_terms = 0
        for market_type, data in stats.market_term_stats.items():
            count = data['count']
            percentage = data['percentage']
            term_name = market_type.replace('_', ' ').title()
            market_term_lines.append(f"    - {term_name:<20} {count:6,} ({percentage:6.3f}%)")
            total_market_terms += count
        
        market_term_section = '\n'.join(market_term_lines) if market_term_lines else "    - No market term patterns detected"
        
        report = f"""Market Term Classification Report
{'='*50}
Analysis Date (PDT): {pdt_time}
Analysis Date (UTC): {utc_time}
{'='*50}

Classification Summary:
  Total Titles Processed: {stats.total_classified:,}
  
  Market Term Distribution:
{market_term_section}
    - Standard Processing:    {stats.standard_count:6,} ({stats.standard_percentage:6.3f}%)
    - Ambiguous Cases:        {stats.ambiguous_count:6,} ({(stats.ambiguous_count/stats.total_classified)*100:6.3f}%)

Expected vs Actual Distribution:
  Market Terms: Expected ~0.3%, Actual {(total_market_terms/stats.total_classified)*100:.3f}%
  Standard:     Expected ~99.7%, Actual {stats.standard_percentage:.3f}%

Classification Performance:
  Specific Patterns Detected: {total_market_terms:,}
  Standard Processing Rate:   {stats.standard_percentage:.2f}%
  
Classification Quality:
  Ambiguous Cases:         {(stats.ambiguous_count/stats.total_classified)*100:.3f}%
  Standard Processing:     {stats.standard_percentage:.2f}%

Available Market Term Patterns:
{chr(10).join(f"  - {term}: {pattern}" for term, pattern in self.market_term_patterns.items())}
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
        
        # Market by patterns
        "Emerging Lighting Technology Market by Color Temperature",
        "Global Software Market by Deployment Type",
        "Healthcare Market by Service Type Analysis",
        
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
        
        for title in sample_titles[:9]:  # Show first 9 examples (3 each type)
            result = classifier.classify(title)
            print(f"Title: {title[:60]}...")
            print(f"  Type: {result.market_type}")
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
        
        # Show dynamic market term statistics
        for market_type, data in stats.market_term_stats.items():
            term_name = market_type.replace('_', ' ').title()
            print(f"{term_name}: {data['count']} ({data['percentage']:.2f}%)")
            
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