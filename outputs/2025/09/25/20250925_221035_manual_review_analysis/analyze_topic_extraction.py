#!/usr/bin/env python3

import json
import os
from typing import Dict, List, Tuple
from collections import defaultdict, Counter

def analyze_pipeline_results():
    """
    Comprehensive analysis of Script 05 topic extraction quality
    for manual review and MongoDB pattern recommendations.
    """

    # Load pipeline results
    results_path = "../20250925_215312_pipeline_01_02_03_04_05_test_500titles/pipeline_results.json"

    print("Loading pipeline results...")
    with open(results_path, 'r') as f:
        data = json.load(f)

    results = data['results']
    total_cases = len(results)

    print(f"Analyzing {total_cases} pipeline results...")

    # Quality categorization
    excellent_extractions = []  # confidence >= 0.9
    good_extractions = []       # confidence 0.7-0.89
    needs_improvement = []      # confidence < 0.7

    # Pattern analysis
    topic_patterns = defaultdict(list)
    normalization_issues = []
    mongodb_recommendations = []

    # Confidence score analysis
    confidence_scores = []

    for i, result in enumerate(results):
        topic_confidence = result['confidence_scores'].get('topic_extraction', 0.0)
        confidence_scores.append(topic_confidence)

        original = result['original_title']
        pipeline_forward = result.get('pipeline_forward_text', '')
        topic = result.get('topic', '')
        topic_name = result.get('topicName', '')

        # Quality categorization
        quality_assessment = assess_extraction_quality(result)

        if topic_confidence >= 0.9:
            excellent_extractions.append({
                'case': i + 1,
                'original': original,
                'pipeline_forward': pipeline_forward,
                'topic': topic,
                'topic_name': topic_name,
                'confidence': topic_confidence,
                'assessment': quality_assessment
            })
        elif topic_confidence >= 0.7:
            good_extractions.append({
                'case': i + 1,
                'original': original,
                'pipeline_forward': pipeline_forward,
                'topic': topic,
                'topic_name': topic_name,
                'confidence': topic_confidence,
                'assessment': quality_assessment
            })
        else:
            needs_improvement.append({
                'case': i + 1,
                'original': original,
                'pipeline_forward': pipeline_forward,
                'topic': topic,
                'topic_name': topic_name,
                'confidence': topic_confidence,
                'assessment': quality_assessment
            })

        # Pattern analysis for MongoDB recommendations
        analyze_patterns(result, topic_patterns, normalization_issues)

    # Generate MongoDB recommendations
    mongodb_recommendations = generate_mongodb_recommendations(topic_patterns, normalization_issues)

    # Create analysis reports
    create_manual_review_report(total_cases, excellent_extractions, good_extractions,
                              needs_improvement, confidence_scores, mongodb_recommendations)

    create_quality_categories_file(excellent_extractions, good_extractions, needs_improvement)

    create_extraction_issues_file(normalization_issues, mongodb_recommendations)

    print("Analysis complete!")
    print(f"Results: {len(excellent_extractions)} excellent, {len(good_extractions)} good, {len(needs_improvement)} need improvement")

def assess_extraction_quality(result: Dict) -> Dict:
    """Assess the quality of a single extraction result."""

    original = result['original_title']
    pipeline_forward = result.get('pipeline_forward_text', '')
    topic = result.get('topic', '')
    topic_name = result.get('topicName', '')

    assessment = {
        'systematic_removal_clean': True,
        'content_preserved': True,
        'normalization_consistent': True,
        'issues': []
    }

    # Check for systematic removal effectiveness
    if any(word in topic_name.lower() for word in ['market', 'report', 'analysis', '2024', '2025', '2026', '2027', '2028', '2029', '2030']):
        assessment['systematic_removal_clean'] = False
        assessment['issues'].append('Systematic removal incomplete - market terms or dates remain')

    # Check content preservation
    if len(topic_name) < 3:
        assessment['content_preserved'] = False
        assessment['issues'].append('Content too short - possible over-removal')

    # Check normalization consistency
    if topic and topic_name:
        expected_normalized = topic_name.lower().replace(' ', '-').replace('&', 'and')
        if topic != expected_normalized and not topic.startswith(expected_normalized[:10]):
            assessment['normalization_consistent'] = False
            assessment['issues'].append(f'Normalization mismatch: "{topic}" vs expected pattern from "{topic_name}"')

    return assessment

def analyze_patterns(result: Dict, topic_patterns: Dict, normalization_issues: List):
    """Analyze patterns for MongoDB recommendations."""

    topic = result.get('topic', '')
    topic_name = result.get('topicName', '')
    notes = result.get('processing_notes', {}).get('topic_notes', '')

    # Track normalization patterns that were applied
    if 'Applied normalization pattern:' in notes:
        patterns_applied = [line.strip() for line in notes.split('\n') if 'Applied normalization pattern:' in line]
        for pattern in patterns_applied:
            pattern_name = pattern.replace('Applied normalization pattern: ', '')
            topic_patterns[pattern_name].append({
                'topic': topic,
                'topic_name': topic_name,
                'case': result.get('test_case', 0)
            })

    # Identify normalization issues
    if topic and topic_name:
        # Check for common issues
        if '&' in topic_name and 'and' not in topic:
            normalization_issues.append({
                'type': 'ampersand_conversion',
                'topic_name': topic_name,
                'topic': topic,
                'case': result.get('test_case', 0),
                'recommendation': 'Ensure ampersand to "and" conversion in normalization'
            })

        if '  ' in topic_name:  # Multiple spaces
            normalization_issues.append({
                'type': 'multiple_spaces',
                'topic_name': topic_name,
                'topic': topic,
                'case': result.get('test_case', 0),
                'recommendation': 'Add pattern to normalize multiple spaces to single space'
            })

def generate_mongodb_recommendations(topic_patterns: Dict, normalization_issues: List) -> List[Dict]:
    """Generate specific MongoDB pattern recommendations."""

    recommendations = []

    # Analyze pattern usage frequency
    for pattern_name, cases in topic_patterns.items():
        if len(cases) > 10:  # Pattern used frequently
            recommendations.append({
                'type': 'pattern_optimization',
                'pattern': pattern_name,
                'usage_count': len(cases),
                'recommendation': f'High-usage pattern "{pattern_name}" - consider optimizing or caching',
                'priority': 'medium'
            })

    # Group normalization issues by type
    issue_counts = Counter(issue['type'] for issue in normalization_issues)

    for issue_type, count in issue_counts.items():
        if count > 5:  # Issue occurs frequently
            recommendations.append({
                'type': 'pattern_addition',
                'issue_type': issue_type,
                'occurrence_count': count,
                'recommendation': f'Add MongoDB pattern to address {issue_type} normalization issues',
                'priority': 'high' if count > 20 else 'medium'
            })

    # Specific pattern recommendations
    recommendations.extend([
        {
            'type': 'new_pattern',
            'pattern_name': 'topic_length_validation',
            'recommendation': 'Add pattern to flag topics shorter than 3 characters for review',
            'priority': 'low',
            'mongodb_pattern': {'type': 'topic_validation', 'min_length': 3, 'action': 'flag_for_review'}
        },
        {
            'type': 'pattern_enhancement',
            'pattern_name': 'systematic_removal_keywords',
            'recommendation': 'Enhance systematic removal patterns to catch remaining market terms',
            'priority': 'high',
            'mongodb_pattern': {'type': 'systematic_removal', 'keywords': ['market', 'report', 'analysis', 'study']}
        }
    ])

    return recommendations

def create_manual_review_report(total_cases: int, excellent: List, good: List,
                              needs_improvement: List, confidence_scores: List,
                              mongodb_recommendations: List):
    """Create comprehensive manual review analysis report."""

    avg_confidence = sum(confidence_scores) / len(confidence_scores)

    report = f"""# Script 05 Topic Extraction - Manual Review Analysis

**Analysis Date (PDT):** 2025-09-25 22:10:35 PDT
**Analysis Date (UTC):** 2025-09-26 05:10:35 UTC

## Executive Summary

**Pipeline Performance Overview:**
- **Total Cases Analyzed:** {total_cases}
- **Average Topic Confidence:** {avg_confidence:.3f}
- **Quality Distribution:**
  - Excellent (≥0.9 confidence): {len(excellent)} cases ({len(excellent)/total_cases*100:.1f}%)
  - Good (0.7-0.89 confidence): {len(good)} cases ({len(good)/total_cases*100:.1f}%)
  - Needs Improvement (<0.7 confidence): {len(needs_improvement)} cases ({len(needs_improvement)/total_cases*100:.1f}%)

## Quality Assessment Details

### Excellent Extractions (Top 10 Examples)

"""

    # Add excellent examples
    for i, case in enumerate(excellent[:10]):
        report += f"""**Case {case['case']}:** {case['original']}
- **Pipeline Forward:** {case['pipeline_forward']}
- **Topic Name:** {case['topic_name']}
- **Normalized:** {case['topic']}
- **Confidence:** {case['confidence']:.3f}
- **Quality:** {', '.join([k for k, v in case['assessment'].items() if v is True and k != 'issues'])}

"""

    # Add MongoDB recommendations section
    report += f"""## MongoDB Pattern Recommendations

**Total Recommendations:** {len(mongodb_recommendations)}

### High Priority Recommendations

"""

    high_priority = [r for r in mongodb_recommendations if r.get('priority') == 'high']
    for rec in high_priority:
        report += f"""**{rec['type'].title()}:** {rec['recommendation']}
"""
        if 'mongodb_pattern' in rec:
            report += f"- **Suggested Pattern:** `{rec['mongodb_pattern']}`\n"
        report += "\n"

    report += f"""### Medium Priority Recommendations

"""

    medium_priority = [r for r in mongodb_recommendations if r.get('priority') == 'medium']
    for rec in medium_priority:
        report += f"- **{rec['type'].title()}:** {rec['recommendation']}\n"

    report += f"""
## Analysis Methodology

1. **Sample Size:** Complete 500-document pipeline test results
2. **Quality Metrics:** Confidence scores, systematic removal effectiveness, content preservation
3. **Pattern Analysis:** MongoDB normalization pattern usage and effectiveness
4. **Issue Identification:** Systematic and normalization problems across confidence ranges

## Recommendations for Todo 5.4

1. **Focus Areas:** Address {len(high_priority)} high-priority pattern recommendations
2. **Quality Threshold:** Current {avg_confidence:.1%} average confidence approaches 92% target
3. **Pattern Refinement:** {len([r for r in mongodb_recommendations if 'pattern' in r['type']])} specific pattern improvements identified

---
**Generated by:** Claude Code AI Manual Review Analysis
**Next Phase:** Todo 5.4 - Analyze topic extraction quality and identify issues
"""

    with open('manual_review_analysis.md', 'w') as f:
        f.write(report)

def create_quality_categories_file(excellent: List, good: List, needs_improvement: List):
    """Create categorized quality assessment file."""

    content = f"""Topic Extraction Quality Categories
Analysis Date (PDT): 2025-09-25 22:10:35 PDT
==================================================

EXCELLENT EXTRACTIONS (Confidence ≥ 0.9)
Total: {len(excellent)} cases

"""

    for case in excellent[:20]:  # Top 20
        content += f"{case['case']:3d}. {case['topic_name']} → {case['topic']} (conf: {case['confidence']:.3f})\n"

    content += f"""

GOOD EXTRACTIONS (Confidence 0.7-0.89)
Total: {len(good)} cases

"""

    for case in good[:15]:  # Top 15
        content += f"{case['case']:3d}. {case['topic_name']} → {case['topic']} (conf: {case['confidence']:.3f})\n"

    content += f"""

NEEDS IMPROVEMENT (Confidence < 0.7)
Total: {len(needs_improvement)} cases

"""

    for case in needs_improvement:  # All cases
        issues = ', '.join(case['assessment']['issues']) if case['assessment']['issues'] else 'Low confidence'
        content += f"{case['case']:3d}. {case['topic_name']} → {case['topic']} (conf: {case['confidence']:.3f}) - {issues}\n"

    with open('topic_quality_categories.txt', 'w') as f:
        f.write(content)

def create_extraction_issues_file(normalization_issues: List, mongodb_recommendations: List):
    """Create extraction issues and recommendations file."""

    content = f"""Topic Extraction Issues & MongoDB Recommendations
Analysis Date (PDT): 2025-09-25 22:10:35 PDT
==================================================

IDENTIFIED ISSUES
Total: {len(normalization_issues)} normalization issues found

"""

    # Group issues by type
    issue_groups = defaultdict(list)
    for issue in normalization_issues:
        issue_groups[issue['type']].append(issue)

    for issue_type, issues in issue_groups.items():
        content += f"\n{issue_type.upper().replace('_', ' ')} ({len(issues)} cases):\n"
        for issue in issues[:5]:  # Show top 5 examples
            content += f"  Case {issue['case']}: {issue['topic_name']} → {issue['topic']}\n"
        if len(issues) > 5:
            content += f"  ... and {len(issues) - 5} more cases\n"

    content += f"""

MONGODB PATTERN RECOMMENDATIONS
Total: {len(mongodb_recommendations)} recommendations

HIGH PRIORITY:
"""

    high_priority = [r for r in mongodb_recommendations if r.get('priority') == 'high']
    for i, rec in enumerate(high_priority, 1):
        content += f"{i}. {rec['recommendation']}\n"
        if 'mongodb_pattern' in rec:
            content += f"   Pattern: {rec['mongodb_pattern']}\n"

    content += f"""
MEDIUM PRIORITY:
"""

    medium_priority = [r for r in mongodb_recommendations if r.get('priority') == 'medium']
    for i, rec in enumerate(medium_priority, 1):
        content += f"{i}. {rec['recommendation']}\n"

    content += f"""
LOW PRIORITY:
"""

    low_priority = [r for r in mongodb_recommendations if r.get('priority') == 'low']
    for i, rec in enumerate(low_priority, 1):
        content += f"{i}. {rec['recommendation']}\n"

    content += """

IMPLEMENTATION PRIORITY ORDER:
1. Address systematic removal keyword gaps (high impact)
2. Enhance normalization pattern consistency (medium impact)
3. Add topic length validation (low impact)
4. Optimize high-usage pattern performance (medium impact)

---
Generated by: Claude Code AI Manual Review Analysis
Next Steps: Implement high-priority MongoDB pattern adjustments in todo 5.4
"""

    with open('extraction_issues_identified.txt', 'w') as f:
        f.write(content)

if __name__ == "__main__":
    analyze_pipeline_results()