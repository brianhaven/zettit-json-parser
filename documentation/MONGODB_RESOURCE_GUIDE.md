# MongoDB Atlas Connection Resource Guide
# JSON Parser Service

## Database Configuration

### Connection Details
- **MongoDB URI**: From `.env` file (`MONGODB_URI`)
- **Database**: `deathstar` 
- **Collection**: `markets_raw`
- **Connection String Format**: 
  ```
  mongodb+srv://username:password@cluster.mongodb.net/deathstar?retryWrites=true&w=majority
  ```

### Required Dependencies
```python
# From requirements.txt in json-splitter
pymongo>=4.0.0
python-dotenv>=0.19.0
pytz>=2021.3
tqdm>=4.62.0
```

## MongoDB Connection Pattern

### Standard Connection Setup
```python
import os
import logging
from dotenv import load_dotenv
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError

def connect_to_mongodb():
    """Establish connection to MongoDB Atlas."""
    # Load environment variables
    load_dotenv()
    
    mongodb_uri = os.getenv('MONGODB_URI')
    if not mongodb_uri:
        logger.error("MONGODB_URI not found in environment variables")
        return None, None, None
    
    try:
        # Create MongoDB client
        client = MongoClient(mongodb_uri, serverSelectionTimeoutMS=10000)
        
        # Test connection
        client.admin.command('ping')
        
        # Access database and collection
        db = client['deathstar']
        collection = db['markets_raw']
        
        logger.info("Successfully connected to MongoDB Atlas")
        return client, db, collection
        
    except (ConnectionFailure, ServerSelectionTimeoutError) as e:
        logger.error(f"Connection failed: {e}")
        return None, None, None
```

### Connection Test Pattern
```python
def test_mongodb_connection():
    """Test MongoDB Atlas connection and basic operations."""
    client, db, collection = connect_to_mongodb()
    
    if not client:
        return False
    
    try:
        # Test database access
        db_stats = db.command("dbstats")
        logger.info(f"Database 'deathstar' accessible - Size: {db_stats.get('dataSize', 0)} bytes")
        
        # Test collection access  
        doc_count = collection.count_documents({})
        logger.info(f"Collection 'markets_raw' accessible - Documents: {doc_count}")
        
        # Test write permissions
        test_doc = {
            "test_connection": True,
            "timestamp": datetime.utcnow().isoformat(),
            "test_id": "connection_test"
        }
        
        # Insert and cleanup test document
        result = collection.insert_one(test_doc)
        collection.delete_one({"_id": result.inserted_id})
        
        client.close()
        return True
        
    except Exception as e:
        logger.error(f"Database test failed: {e}")
        client.close()
        return False
```

## Document Structure Analysis

### Expected Document Schema
Based on json-splitter analysis, documents contain:

```python
# Core document structure from markets_raw collection
{
    "uuid": "unique-identifier",
    "filename": "source-filename.json", 
    "publisherID": "GVR|TMR|MDR",
    "created_pst": "timestamp",
    "insertion_date_utc": "timestamp",
    "insertion_date_pt": "timestamp",
    
    # Report content fields
    "report_title": "string",
    "report_slug": "string", 
    "report_url": "string",
    "report_content": "html/text content",
    
    # Additional metadata fields vary by publisher
    # ... other report-specific fields
}
```

### Common Query Patterns
```python
# Find documents by publisher
gvr_docs = collection.find({"publisherID": "GVR"})

# Find documents with specific content
docs_with_tables = collection.find({
    "report_content": {"$regex": "<table", "$options": "i"}
})

# Count documents by publisher
publisher_counts = collection.aggregate([
    {"$group": {"_id": "$publisherID", "count": {"$sum": 1}}}
])

# Find documents with empty fields
empty_title_docs = collection.find({
    "$or": [
        {"report_title": {"$exists": False}},
        {"report_title": ""},
        {"report_title": None}
    ]
})
```

## Batch Processing Patterns

### Progressive Batch Insertion
```python
class MongoDBConnection:
    def __init__(self, uri: str):
        self.uri = uri
        self.client = None
        self.db = None
        self.collection = None
        self.batch_sizes = [100, 200, 300, 400, 1000]  # Progressive batch sizes
        self.current_batch_size_index = 0
        self.max_retries = 3

    def insert_documents_batch(self, documents):
        """Insert documents using progressive batch sizing."""
        inserted_count = 0
        current_batch_size = self.batch_sizes[0]
        
        for start_idx in range(0, len(documents), current_batch_size):
            batch = documents[start_idx:start_idx + current_batch_size]
            
            for retry in range(self.max_retries):
                try:
                    # Check for existing documents first
                    new_docs = [doc for doc in batch 
                              if self.collection.count_documents({'uuid': doc['uuid']}) == 0]
                    
                    if new_docs:
                        result = self.collection.insert_many(new_docs)
                        inserted_count += len(result.inserted_ids)
                    
                    # Increase batch size on success
                    if retry == 0 and len(batch) == current_batch_size:
                        current_batch_size = self.get_next_batch_size()
                    
                    break
                    
                except Exception as e:
                    logger.error(f"Batch insertion error: {e}")
                    if retry == self.max_retries - 1:
                        # Skip failed batch
                        continue
        
        return inserted_count
```

## Content Analysis Patterns

### HTML Table Detection
```python
def find_html_tables(content):
    """Find HTML tables in document content."""
    import re
    
    table_pattern = r'<table[^>]*>.*?</table>'
    tables = re.findall(table_pattern, content, re.DOTALL | re.IGNORECASE)
    return tables

def extract_table_data(table_html):
    """Extract data from HTML table."""
    from bs4 import BeautifulSoup
    
    soup = BeautifulSoup(table_html, 'html.parser')
    
    headers = []
    rows = []
    
    # Extract headers
    header_row = soup.find('tr')
    if header_row:
        headers = [th.get_text(strip=True) for th in header_row.find_all(['th', 'td'])]
    
    # Extract data rows
    for row in soup.find_all('tr')[1:]:  # Skip header row
        row_data = [td.get_text(strip=True) for td in row.find_all(['td', 'th'])]
        rows.append(row_data)
    
    return headers, rows
```

### Content Parsing Utilities
```python
def extract_countries_regions(title):
    """Extract country and region information from title."""
    import re
    
    # Common country patterns
    countries = []
    regions = []
    
    # Country patterns
    country_patterns = [
        r'\b(United States|USA|US)\b',
        r'\b(United Kingdom|UK|Britain)\b', 
        r'\b(China|Japan|India|Germany|France|Brazil)\b',
        # Add more country patterns
    ]
    
    # Region patterns  
    region_patterns = [
        r'\b(North America|Europe|Asia Pacific|APAC|Latin America)\b',
        r'\b(Middle East|Africa|MEA)\b',
        # Add more region patterns
    ]
    
    for pattern in country_patterns:
        matches = re.findall(pattern, title, re.IGNORECASE)
        countries.extend(matches)
    
    for pattern in region_patterns:
        matches = re.findall(pattern, title, re.IGNORECASE)
        regions.extend(matches)
    
    return list(set(countries)), list(set(regions))

def identify_topic_from_title(title):
    """Identify topic and topic name from document title."""
    import re
    
    # Market research topic patterns
    topic_patterns = {
        'technology': [r'\b(AI|artificial intelligence|software|digital|tech)\b', r'\bmarket\b'],
        'healthcare': [r'\b(medical|pharmaceutical|healthcare|drug|medicine)\b', r'\bmarket\b'], 
        'automotive': [r'\b(automotive|vehicle|car|transport)\b', r'\bmarket\b'],
        'energy': [r'\b(energy|oil|gas|renewable|solar|wind)\b', r'\bmarket\b'],
        'chemicals': [r'\b(chemical|polymer|material)\b', r'\bmarket\b']
    }
    
    for topic, patterns in topic_patterns.items():
        if all(re.search(pattern, title, re.IGNORECASE) for pattern in patterns):
            # Extract specific topic name (e.g., "AI Software Market" -> "AI Software")
            topic_match = re.search(r'(.+?)\s+market', title, re.IGNORECASE)
            topic_name = topic_match.group(1).strip() if topic_match else title
            return topic, topic_name
    
    return 'general', title
```

## Error Handling Best Practices

### Connection Error Handling
```python
def safe_mongodb_operation(operation_func, *args, **kwargs):
    """Safely execute MongoDB operations with error handling."""
    max_retries = 3
    
    for attempt in range(max_retries):
        try:
            return operation_func(*args, **kwargs)
            
        except ConnectionFailure as e:
            logger.warning(f"Connection failed on attempt {attempt + 1}: {e}")
            if attempt == max_retries - 1:
                raise
            time.sleep(2 ** attempt)  # Exponential backoff
            
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            raise
```

### Document Validation
```python
def validate_document(doc):
    """Validate document structure before insertion."""
    required_fields = ['uuid', 'publisherID', 'filename']
    
    for field in required_fields:
        if field not in doc or doc[field] is None:
            return False, f"Missing required field: {field}"
    
    # Validate UUID format
    import uuid
    try:
        uuid.UUID(doc['uuid'])
    except ValueError:
        return False, "Invalid UUID format"
    
    # Validate publisher ID
    if doc['publisherID'] not in ['GVR', 'TMR', 'MDR']:
        return False, f"Invalid publisherID: {doc['publisherID']}"
    
    return True, "Valid"
```

## Logging Configuration

### Standard Logging Setup
```python
import logging
from datetime import datetime

# Configure logging for JSON parser scripts
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'json_parser_{datetime.now().strftime("%Y%m%d")}.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)
```

## Summary

This resource guide provides all the necessary patterns and configurations for building JSON parser scripts that will:

1. **Connect reliably** to the MongoDB Atlas `deathstar.markets_raw` collection
2. **Process documents** using established patterns from the json-splitter service  
3. **Handle errors gracefully** with comprehensive error handling
4. **Parse content effectively** using proven content analysis techniques
5. **Insert data safely** using batch processing with duplicate prevention

The patterns are derived from the working json-splitter codebase and should provide a solid foundation for implementing the document analysis and parsing scripts requested.