#!/usr/bin/env python3
"""
Debug Report Type Extraction Issues

Analyzes specific cases where report type extraction is failing or partial.
Identifies root cause: priority ordering and pattern matching logic.
"""

import json
import os
import sys
import re
import logging
import importlib.util
from typing import Dict, List, Tuple
from datetime import datetime
import pytz
from pymongo import MongoClient
from dotenv import load_dotenv

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

load_dotenv()

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Import modules dynamically
def import_module_from_path(module_name: str, file_path: str):
    """Import a module from a file path."""
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

# Import main scripts from parent directory  
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
pattern_lib = import_module_from_path("pattern_library_manager_v1", 
                                    os.path.join(parent_dir, "00b_pattern_library_manager_v1.py"))
script_03 = import_module_from_path("report_type_extractor_v2", 
                                   os.path.join(parent_dir, "03_report_type_extractor_v2.py"))

def create_output_directory() -> str:
    """Create timestamped output directory."""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    experiments_dir = os.path.dirname(script_dir)  
    project_root = os.path.dirname(experiments_dir)
    outputs_dir = os.path.join(project_root, 'outputs')
    
    pdt = pytz.timezone('America/Los_Angeles')
    timestamp = datetime.now(pdt).strftime('%Y%m%d_%H%M%S')
    
    output_dir = os.path.join(outputs_dir, f"{timestamp}_debug_report_type_issues")
    os.makedirs(output_dir, exist_ok=True)
    
    return output_dir

class ReportTypeDebugger:
    """Debug report type extraction issues."""
    
    def __init__(self):
        # Test cases from pipeline results showing issues
        self.problematic_cases = [
            {
                "original": "Graphite Market Size, Share, Growth, Industry Report, 2030",
                "after_date_removal": "Graphite Market Size, Share, Growth, Industry Report",
                "expected_report": "Market Size, Share, Growth, Industry Report", 
                "actual_report": "Industry Report",
                "actual_topic": "Graphite Market Size, Share, Growth"
            },
            {
                "original": "Isophorone Market Size, Share, Growth Analysis Report, 2030", 
                "after_date_removal": "Isophorone Market Size, Share, Growth Analysis Report",
                "expected_report": "Market Size, Share, Growth Analysis Report",
                "actual_report": "Market Size, Share,",
                "actual_topic": "Isophorone  Growth Analysis Report"
            },
            {
                "original": "High-speed Camera Market Size, Share, Growth Report 2030",
                "after_date_removal": "High-speed Camera Market Size, Share, Growth Report", 
                "expected_report": "Market Size, Share, Growth Report",
                "actual_report": "Market Size, Share,",
                "actual_topic": "High-speed Camera  Growth"
            },
            {
                "original": "Hydraulic Fracturing Market Analysis, Industry Report, 2024",
                "after_date_removal": "Hydraulic Fracturing Market Analysis, Industry Report",
                "expected_report": "Market Analysis, Industry Report", 
                "actual_report": "Market Analysis,",
                "actual_topic": "Hydraulic Fracturing  Industry Report"
            }
        ]
    
    def debug_single_case(self, case: Dict, pattern_manager: pattern_lib.PatternLibraryManager) -> Dict:
        """Debug a single problematic case."""
        logger.info(f"\\nDebugging: {case['original']}")
        
        # Get all report type patterns
        patterns = pattern_manager.get_patterns(pattern_lib.PatternType.REPORT_TYPE)
        logger.info(f"Found {len(patterns)} report type patterns")
        
        # Test what patterns match
        text = case['after_date_removal']
        matches = []
        
        for pattern in patterns:
            if not pattern.get('active', True):
                continue
                
            pattern_regex = pattern.get('pattern', '')
            if not pattern_regex:
                continue
                
            try:
                match = re.search(pattern_regex, text, re.IGNORECASE)
                if match:
                    matches.append({
                        'term': pattern['term'],
                        'priority': pattern.get('priority', 5),
                        'pattern': pattern_regex,
                        'match_text': match.group(0),
                        'groups': match.groups() if match.groups() else []
                    })
            except re.error as e:
                logger.warning(f"Regex error for pattern {pattern['term']}: {e}")
                continue
        
        # Sort by priority (lower number = higher priority)
        matches.sort(key=lambda x: x['priority'])
        
        return {
            'case': case,
            'text_analyzed': text,
            'total_matches': len(matches),
            'matches': matches[:10],  # Top 10 matches
            'first_match': matches[0] if matches else None
        }
    
    def run_debug_analysis(self):
        """Run complete debug analysis."""
        logger.info("Starting Report Type Extraction Debug Analysis")
        
        output_dir = create_output_directory()
        logger.info(f"Output directory: {output_dir}")
        
        # Initialize pattern manager
        pattern_manager = pattern_lib.PatternLibraryManager()
        
        # Debug each problematic case
        results = []
        for case in self.problematic_cases:
            debug_result = self.debug_single_case(case, pattern_manager)
            results.append(debug_result)
        
        # Generate debug report
        self.generate_debug_report(output_dir, results)
        
        logger.info(f"Debug analysis complete! Results saved to: {output_dir}")
    
    def generate_debug_report(self, output_dir: str, results: List[Dict]):
        """Generate comprehensive debug report."""
        pdt = pytz.timezone('America/Los_Angeles')
        timestamp = datetime.now(pdt).strftime('%Y-%m-%d %H:%M:%S PDT')
        
        # Generate markdown report
        report_file = os.path.join(output_dir, "report_type_debug_analysis.md")
        with open(report_file, 'w') as f:
            f.write("# Report Type Extraction Debug Analysis\\n\\n")
            f.write(f"**Analysis Date (PDT):** {timestamp}\\n")
            f.write(f"**Analysis Date (UTC):** {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}\\n\\n")
            
            f.write("## Problem Summary\\n\\n")
            f.write("Report type extraction is matching shorter patterns instead of longer, more complete ones.\\n")
            f.write("This results in partial report types and incomplete topic extraction.\\n\\n")
            
            f.write("## Detailed Case Analysis\\n\\n")
            
            for i, result in enumerate(results, 1):
                case = result['case']
                f.write(f"### Case {i}: {case['original']}\\n\\n")
                f.write(f"**Text Analyzed:** `{result['text_analyzed']}`\\n")
                f.write(f"**Expected Report Type:** `{case['expected_report']}`\\n")
                f.write(f"**Actual Report Type:** `{case['actual_report']}`\\n")
                f.write(f"**Actual Topic:** `{case['actual_topic']}`\\n\\n")
                
                f.write(f"**Total Matching Patterns:** {result['total_matches']}\\n\\n")
                
                if result['first_match']:
                    first = result['first_match']
                    f.write(f"**First Match (Priority {first['priority']}):**\\n")
                    f.write(f"- Pattern: `{first['term']}`\\n")
                    f.write(f"- Regex: `{first['pattern']}`\\n")
                    f.write(f"- Matched Text: `{first['match_text']}`\\n\\n")
                
                f.write("**Top Matching Patterns:**\\n")
                for j, match in enumerate(result['matches'][:5], 1):
                    f.write(f"{j}. **{match['term']}** (Priority {match['priority']})\\n")
                    f.write(f"   - Matched: `{match['match_text']}`\\n")
                
                f.write("\\n" + "-" * 60 + "\\n\\n")
        
        # Generate JSON details
        json_file = os.path.join(output_dir, "debug_results_detailed.json")
        with open(json_file, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        logger.info(f"Debug report generated: {report_file}")

if __name__ == "__main__":
    debugger = ReportTypeDebugger()
    debugger.run_debug_analysis()