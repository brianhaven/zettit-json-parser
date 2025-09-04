# MongoDB-First Architecture

## ⚠️ CRITICAL DATABASE-FIRST RULE

**🚫 NEVER HARDCODE KEYWORDS, TERMS, OR PATTERNS IN SCRIPTS**

**✅ ALL KEYWORDS, TERMS, AND PATTERNS MUST BE STORED IN AND RETRIEVED FROM THE DATABASE**

This is a **mandatory architectural requirement** for the Zettit JSON Parser project:

- **NO hardcoded lists** of keywords in Python scripts
- **NO static pattern arrays** or dictionaries in code
- **NO inline regex patterns** for business logic
- **ALL pattern data** must come from `pattern_libraries` collection
- **ALL business rules** must be database-driven and configurable
- **ALL keyword matching** must query MongoDB collections

**Rationale:**
- **Real-time updates:** Pattern libraries can be updated without code deployment
- **A/B testing:** Different pattern sets can be tested dynamically
- **Performance tracking:** Database tracks success/failure rates per pattern
- **Maintainability:** Business logic separated from implementation code
- **Scalability:** New patterns added through database, not code changes

## Database Strategy
**MongoDB Atlas serves as both data source and pattern library storage:**
- **Primary data:** `markets_raw` collection (19,558+ titles) - field: `report_title_short`
- **Pattern libraries:** `pattern_libraries` collection with real-time updates
- **Processed results:** `markets_processed` collection for output tracking
- **Performance metrics:** Built-in success/failure tracking

## Claude Code MongoDB Integration
**IMPORTANT: Use MongoDB MCP Server for all database interactions**

### MongoDB MCP Server Commands
The MongoDB MCP server provides efficient database access through Claude Code. **Always prefer MCP commands over bash scripts for database operations.**

**Core Database Operations:**
```bash
# List collections and databases
mcp__mongodb__list-databases                    # List all databases
mcp__mongodb__list-collections database         # List collections in database

# Query operations
mcp__mongodb__find database collection filter   # Find documents with filter
mcp__mongodb__count database collection query   # Count documents with query
mcp__mongodb__aggregate database collection pipeline  # Run aggregation pipeline

# Data modification
mcp__mongodb__insert-many database collection documents  # Insert documents
mcp__mongodb__update-many database collection filter update  # Update documents
mcp__mongodb__delete-many database collection filter  # Delete documents

# Schema and indexes
mcp__mongodb__collection-schema database collection     # Get collection schema
mcp__mongodb__collection-indexes database collection    # List indexes
mcp__mongodb__create-index database collection keys name  # Create index
```

**Pattern Library Management Examples:**
```bash
# Query report type patterns
mcp__mongodb__find deathstar pattern_libraries {"type": "report_type"}

# Count geographic patterns
mcp__mongodb__count deathstar pattern_libraries {"type": "geographic_entity"}

# Aggregate pattern statistics by type
mcp__mongodb__aggregate deathstar pattern_libraries '[{"$group": {"_id": "$type", "count": {"$sum": 1}}}]'

# Find high-priority patterns
mcp__mongodb__find deathstar pattern_libraries {"priority": {"$lte": 5}, "active": true}
```

**Market Data Analysis:**
```bash
# Query market research titles
mcp__mongodb__find deathstar markets_raw {"report_title_short": {"$regex": "Market", "$options": "i"}}

# Count processed results
mcp__mongodb__count deathstar markets_processed {}

# Analyze title patterns
mcp__mongodb__aggregate deathstar markets_raw '[{"$match": {"report_title_short": {"$regex": "2024"}}}, {"$count": "titles_with_2024"}]'
```

**For scripts:** Scripts use pymongo API directly
```python
from pymongo import MongoClient
client = MongoClient(os.getenv('MONGODB_URI'))
db = client['deathstar']
```

## Library-Based Processing Strategy

**MongoDB Pattern Libraries Structure:**
```javascript
// pattern_libraries collection
{
  "type": "geographic_entity", // or "market_term", "date_pattern", "report_type"
  "term": "North America",
  "aliases": ["NA", "North American"],
  "priority": 1,  // For compound processing order
  "active": true,
  "success_count": 1547,
  "failure_count": 3,
  "created_date": ISODate(),
  "last_updated": ISODate()
}
```

## Database Connection Management
**CRITICAL: Use shared PatternLibraryManager instances**
- All components must share a single PatternLibraryManager instance
- Never create multiple MongoDB connections in the same script
- Use database connection caching for performance
- Follow the proven pattern from working test scripts

**MongoDB Integration:**
- Use environment variables from `.env` file for connection
- MongoDB collections for pattern libraries (not static files)
- Real-time library updates without deployment
- Performance tracking built into database operations

## Benefits of MongoDB MCP Server:
- **Efficiency:** Direct database access without subprocess overhead
- **Error Handling:** Better error reporting and connection management  
- **Performance:** Optimized queries with proper connection pooling
- **Security:** Secure credential management through MCP configuration
- **Debugging:** Clear query results and structured error messages