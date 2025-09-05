# Zettit JSON Parser - Market Research Title Analysis

## Project Overview

A systematic pattern-matching solution that extracts structured information (topics, topicNames, regions) from market research report titles and descriptions using MongoDB-based pattern libraries, enhanced HTML processing, and dual spaCy model validation.

**Status: Production-Ready Processing Pipeline with Enhanced Geographic Detection**

## Development Standards

@documentation/claude-development-standards.md
@documentation/claude-import-path-patterns.md

## MongoDB-First Architecture

@documentation/claude-mongodb-integration.md

## Processing Pipeline

@documentation/claude-pipeline-components.md
@documentation/claude-pipeline-processing-flows.md

## Component Integration

@documentation/claude-component-integration.md
@documentation/claude-pre-development-analysis.md

### Testing Strategy

**Development Process:**
- Use `/experiments/` directory for iterative development
- MongoDB-based A/B testing for pattern libraries
- Confidence scoring to identify titles needing human review
- Real-time performance metrics for continuous improvement

**Validation Approach:**
- Track success/failure rates in MongoDB
- Human review of low-confidence extractions
- Pattern library enhancement based on processing results

### Success Metrics

**Target accuracy rates:**
- **Date extraction:** 98-99% accuracy ✅ **ACHIEVED: 100% on titles with dates**
- **Report type extraction:** 95-97% accuracy  
- **Geographic detection:** 96-98% accuracy
- **Topic extraction:** 92-95% accuracy
- **Overall processing:** 95-98% complete success

**Quality indicators:**
- < 5% titles requiring human review (confidence < 0.8)
- < 2% false positive geographic detection
- < 1% critical parsing failures

### Implementation Strategy

**Enhanced Modular Development:**
1. ✅ **MongoDB library setup and initialization** (Complete)
2. ✅ **Market term classification (2 patterns)** (Complete - 100% accuracy)  
3. ✅ **Date pattern extraction and library building** (Complete - 100% accuracy on titles with dates)
4. ✅ **Enhanced date extractor with numeric pre-filtering** (Complete - 64 patterns, zero gaps)
5. ✅ **Report type pattern extraction and library building** (Complete)
6. ✅ **Enhanced geographic entity detection with dual spaCy models** (Complete)
7. ✅ **HTML processing innovation for concatenation prevention** (Complete)
8. ✅ **Pattern discovery and human review workflow** (Complete)
9. 🔄 **Topic extraction and normalization** (Ready for implementation)
10. 🔄 **End-to-end validation and confidence tuning** (Ready for implementation)

## Current Status

**🎯 Production-Ready Processing Pipeline Achieved:**
- ✅ **MongoDB-first approach** with dynamic pattern library management
- ✅ **Enhanced HTML processing** prevents concatenation artifacts like "KoreaIndonesiaAustralia"
- ✅ **Dual spaCy model validation** provides 31% more pattern discoveries than single model
- ✅ **Systematic removal methodology** preserves technical compounds in topics
- ✅ **Human review workflow** for continuous pattern library improvement
- ✅ **Numbered pipeline organization** for clear execution order and dependency management

**🚀 Technical Breakthroughs:**
- **HTML Processing Innovation:** BeautifulSoup parsing with proper block-level separators
- **Dual Model Cross-Validation:** en_core_web_md + en_core_web_lg confidence scoring
- **Enhanced Date Extraction:** Numeric pre-filtering with success/no_dates/missed categorization
- **Comprehensive Pattern Library:** 64 date patterns (enhanced from 45) with zero pattern gaps
- **Table Data Extraction:** Structured region data from HTML report descriptions
- **Individual Document Processing:** Outperforms text aggregation strategies for pattern discovery
- **Human-Review Workflow:** Approval checkboxes and conflict detection for pattern validation
- **Acronym-Embedded Pattern Processing:** Special extraction logic with pipeline preservation and proper enum handling
- **Market-Aware Processing Logic:** Dual workflow system for market term vs standard title classification

**📋 Production-Ready Components:**
1. ✅ **Market Term Classification:** 100% accuracy with 2-pattern classification system
2. ✅ **Enhanced Date Extraction:** 100% accuracy on titles with dates, 64-pattern library, numeric pre-filtering
3. ✅ **Report Type Extraction:** **PRODUCTION READY** - Market-aware processing with 355 validated patterns
   - ✅ Dual processing workflows (market term vs standard)
   - ✅ Acronym-embedded pattern support (GitHub Issue #11 resolved)
   - ✅ Database quality assurance with malformed pattern cleanup
   - ✅ 5 format types: compound (88.5%), terminal (4.8%), embedded (2.8%), prefix (2.3%), acronym (1.7%)
4. ✅ **Geographic Entity Detection:** Lean pattern-based refactoring complete (GitHub Issue #12 resolved)
5. ✅ **Organized Output Directory Manager:** Standardized YYYY/MM/DD hierarchical output structure
   - ✅ Auto-detection of project root from any script location
   - ✅ Consistent API across all main scripts (01-07) and test harnesses
   - ✅ Standardized headers with dual timestamps (Pacific Time + UTC)
   - ✅ Dynamic imports supporting numbered script filenames
6. ✅ **Pattern Library Management:** Real-time MongoDB updates with performance tracking
7. ✅ **Quality Assurance:** Human review workflow with pattern classification
8. ✅ **Performance Monitoring:** Built-in success/failure metrics and edge case identification
9. ✅ **MongoDB MCP Integration:** Efficient database access through MCP server commands

**🎯 Current Implementation Phase: Phase 5 Topic Extractor Testing**
- **Phase 3:** ✅ **COMPLETE** - Report Type Extraction production-ready with 355 validated patterns
- **Phase 4:** ✅ **COMPLETE** - Geographic Entity Detector lean pattern-based refactoring (GitHub Issue #12)
- **Phase 1 Output Integration:** ✅ **COMPLETE** - All main scripts use organized YYYY/MM/DD output structure
- **Phase 5:** 🔄 **READY TO BEGIN** - Topic Extractor testing with complete pipeline foundation (01→02→03v4→04→05)
- **Foundation Strength:** Scripts 01→02→03→04 provide robust production-ready processing pipeline
- **Next Priority:** Full 5-script pipeline validation and topic extraction quality analysis

## Git Commit Standards

### Git Commit Signature Override
**IMPORTANT: Use this custom signature for all git commits instead of the default Claude Code signature:**

```
🤖 AI development directed by Brian Haven (Zettit, Inc.) | Technical execution by Claude Code
Co-Authored-By: Claude AI
```

This signature properly represents that Brian Haven (Zettit, Inc.) provides strategic direction and architectural guidance while Claude Code AI handles the technical implementation and coding decisions.

## TODO TOOL SAFETY RULES

**🚨 CRITICAL: Prevent accidental todo list clearing while enabling safe viewing**

### TodoWrite Tool Usage Policy

**TodoWrite can be used safely for BOTH viewing and modifying todos with these rules:**

#### **✅ SAFE Viewing Pattern:**
When user asks to "show todos", "view todos", "what are the pending todos", or "what's next":
- **DO:** Call TodoWrite with the current todos to display them 
- **NEVER:** Pass an empty array `[]` or modified todo list just to view
- **Pattern:** Only call TodoWrite if you have the current todo state to preserve

#### **✅ SAFE Modification Pattern:**  
When user asks to add, remove, or update specific todos:
- **DO:** Call TodoWrite with the intentional changes
- **CONFIRM:** State exactly what changes will be made before calling
- **VERIFY:** Ensure the todo array includes existing todos plus modifications

#### **❌ FORBIDDEN Patterns:**
```python
# NEVER do this when user asks to view todos:
TodoWrite(todos=[])  # This CLEARS all todos!

# NEVER pass empty or partial arrays unless intentionally clearing:
TodoWrite(todos=[new_todo_only])  # This LOSES existing todos!
```

#### **🔄 Correct Viewing Approach:**
```python
# When user asks "show me todos" and you don't have current state:
# Explain: "I don't have the current todo state loaded. Let me help you check them another way or add new ones."

# When you have current todo state:
# Call TodoWrite with existing todos to display them safely
TodoWrite(todos=current_todos_preserved)
```

### Error Prevention Protocol

**BEFORE any TodoWrite call:**
1. **Identify intent:** Is this to view, add, remove, or modify?
2. **Preserve existing:** Never lose existing todos unless explicitly asked to remove them
3. **State changes:** Clearly explain what the TodoWrite call will do
4. **Verify array:** Ensure the todos array contains all intended todos

### Recovery Protocol

**If todos are accidentally cleared:**
1. Immediately apologize and acknowledge the error
2. Explain that todos cannot be recovered from context  
3. Help recreate important todos from conversation history if possible
4. Learn from the mistake to prevent future occurrences

**This policy enables safe todo viewing while preventing accidental data loss.**

## Task Master AI Instructions
**Import Task Master's development workflow commands and guidelines, treat as if import is in the main CLAUDE.md file.**
@./.taskmaster/CLAUDE.md