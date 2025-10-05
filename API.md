# 🔌 API Reference - Documentation Collection

Programmatic API for integrating Documentation Collection plugin with aggressive search capabilities.

## 📋 Overview

The Documentation Collection plugin provides both CLI and programmatic interfaces. This document covers the programmatic API for developers who want to integrate document search and collection functionality with aggressive optimization into their applications.

## 🏗️ Architecture

```
Your Application
       ↓
DocumentationCollectionCLI
       ↓
SearchService
       ↓
┌─────────────────┬─────────────────┬─────────────────┐
│   SearchEngine  │ DocumentDownload│   AI Analyzer   │
│   (Google, etc) │     Service     │  (Gemini/Ollama)│
└─────────────────┴─────────────────┴─────────────────┘
       ↓
Database + File Storage
```

## 🚀 Quick Start

### Basic Integration

```python
import sys
from pathlib import Path

# Add module to path
sys.path.append(str(Path(__file__).parent / "lkwolfSAI_ablilities" / "documentation_collection"))

from services.search_service import SearchService

# Initialize service
search_service = SearchService()

# Perform aggressive search
async def search_documents():
    session_id = await search_service.search_documents(
        query="artificial intelligence",
        aggressive_search=True,
        search_criteria={"type": "research papers"}
    )
    return session_id

# Get results
async def get_results(session_id):
    results = await search_service.get_search_results(session_id)
    return results
```

## 🔧 Core Classes

### SearchService

Main service class for document search and collection.

```python
class SearchService:
    """Main search service for documentation collection"""
    
    async def search_documents(
        self, 
        query: str, 
        aggressive_search: bool = False,
        search_criteria: Dict[str, Any] = None
    ) -> int:
        """
        Search for documents and return session ID
        
        Args:
            query: Search query string
            aggressive_search: Enable aggressive search mode
            search_criteria: Optional criteria for AI analysis
            
        Returns:
            session_id: Unique session identifier
        """
    
    async def get_search_results(self, session_id: int) -> Dict[str, Any]:
        """
        Get search results for a session
        
        Args:
            session_id: Session identifier
            
        Returns:
            Dictionary with results and metadata
        """
    
    async def export_results(
        self, 
        session_id: int, 
        format: str = 'csv'
    ) -> Optional[str]:
        """
        Export results to file
        
        Args:
            session_id: Session identifier
            format: Export format ('csv', 'excel', 'both')
            
        Returns:
            Path to exported file(s)
        """
```

### FileManager

Manages file storage and organization.

```python
class FileManager:
    """File manager for organizing downloaded documents"""
    
    def create_session_directory(self, session_id: int) -> Path:
        """Create directory for session files"""
    
    def get_storage_stats(self) -> Dict[str, Any]:
        """Get storage statistics"""
    
    def export_session_to_csv(self, session_id: int) -> Optional[Path]:
        """Export session results to CSV"""
    
    def export_session_to_excel(self, session_id: int) -> Optional[Path]:
        """Export session results to Excel"""
```

### SearchEngine Classes

Individual search engine handlers.

```python
class GoogleSearchHandler(SearchEngineHandler):
    """Google Search handler"""
    
    async def search(self, query: str, max_results: int = 10) -> List[SearchResult]:
        """Search Google for documents"""

class BingSearchHandler(SearchEngineHandler):
    """Bing Search handler"""
    
    async def search(self, query: str, max_results: int = 10) -> List[SearchResult]:
        """Search Bing for documents"""

class DuckDuckGoSearchHandler(SearchEngineHandler):
    """DuckDuckGo Search handler"""
    
    async def search(self, query: str, max_results: int = 10) -> List[SearchResult]:
        """Search DuckDuckGo for documents"""
```

## 📊 Data Models

### SearchResult

```python
@dataclass
class SearchResult:
    """Search result data class"""
    title: str
    url: str
    snippet: str = ""
    search_engine: str = ""
    language: str = "en"
    translated_query: str = ""
```

### SearchSession (Database Model)

```python
class SearchSession(Base):
    """Search session database model"""
    __tablename__ = 'search_sessions'
    
    id = Column(Integer, primary_key=True)
    original_query = Column(Text, nullable=False)
    search_criteria = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    status = Column(Enum(SearchStatus), default=SearchStatus.PENDING)
    total_results = Column(Integer, default=0)
    storage_path = Column(String(500), nullable=True)
```

### SearchResult (Database Model)

```python
class SearchResult(Base):
    """Search result database model"""
    __tablename__ = 'search_results'
    
    id = Column(Integer, primary_key=True)
    session_id = Column(Integer, ForeignKey('search_sessions.id'))
    language = Column(String(10), nullable=False)
    translated_query = Column(Text, nullable=False)
    search_engine = Column(String(50), nullable=False)
    url = Column(Text, nullable=False)
    title = Column(Text, nullable=True)
    file_path = Column(String(500), nullable=True)
    file_type = Column(String(20), nullable=True)
    file_size = Column(Integer, nullable=True)
    download_status = Column(Enum(DownloadStatus), default=DownloadStatus.PENDING)
```

## 🔧 Configuration

### Environment Variables

```python
# Database Configuration
DATABASE_URL = os.getenv('DATABASE_URL')

# Search Configuration
MAX_RESULTS_PER_ENGINE = int(os.getenv('MAX_RESULTS_PER_ENGINE', '10'))
REQUEST_DELAY = float(os.getenv('REQUEST_DELAY', '1.0'))
MAX_CONCURRENT_DOWNLOADS = int(os.getenv('MAX_CONCURRENT_DOWNLOADS', '5'))

# Storage Configuration
STORAGE_BASE_PATH = os.getenv('STORAGE_BASE_PATH', './storage')
MAX_FILE_SIZE = int(os.getenv('MAX_FILE_SIZE', '52428800'))

# AI Configuration
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
ENABLE_AI_ANALYSIS = os.getenv('ENABLE_AI_ANALYSIS', 'True').lower() == 'true'

# Search Engines
ENABLED_SEARCH_ENGINES = os.getenv('ENABLED_SEARCH_ENGINES', 'google,bing,duckduckgo').split(',')
```

### Configuration Class

```python
from utils.config import Config

# Access configuration
config = Config()

# Get search delay for specific engine
delay = config.get_search_delay("google")

# Validate configuration
errors = config.validate_config()
if errors:
    print(f"Configuration errors: {errors}")
```

## 🎯 Usage Examples

### Basic Search

```python
import asyncio
from services.search_service import SearchService

async def basic_search():
    search_service = SearchService()
    
    # Perform aggressive search
    session_id = await search_service.search_documents(
        query="machine learning algorithms",
        aggressive_search=True
    )
    
    # Get results
    results = await search_service.get_search_results(session_id)
    
    print(f"Found {results['total_results']} results")
    for result in results['results']:
        print(f"- {result['title']}: {result['url']}")

# Run the search
asyncio.run(basic_search())
```

### Advanced Search with AI Analysis

```python
async def advanced_search():
    search_service = SearchService()
    
    # Search with AI analysis criteria and aggressive search
    session_id = await search_service.search_documents(
        query="deep learning frameworks",
        aggressive_search=True,
        search_criteria={
            "type": "technical documentation",
            "focus": "performance, scalability, ease of use",
            "format": "official documentation, tutorials"
        }
    )
    
    # Export results
    csv_path = await search_service.export_results(session_id, 'csv')
    excel_path = await search_service.export_results(session_id, 'excel')
    
    print(f"Results exported to: {csv_path}, {excel_path}")

asyncio.run(advanced_search())
```

### Multi-Language Search

```python
async def multilingual_search():
    search_service = SearchService()
    
    # Search in multiple languages
    queries = [
        "artificial intelligence",
        "inteligencia artificial",  # Spanish
        "intelligence artificielle",  # French
        "trí tuệ nhân tạo"  # Vietnamese
    ]
    
    sessions = []
    for query in queries:
        session_id = await search_service.search_documents(query, aggressive_search=True)
        sessions.append(session_id)
    
    # Process all sessions
    for session_id in sessions:
        results = await search_service.get_search_results(session_id)
        print(f"Session {session_id}: {results['total_results']} results")

asyncio.run(multilingual_search())
```

### Custom Search Engine Integration

```python
from core.search_engine import SearchEngineHandler, SearchResult

class CustomSearchHandler(SearchEngineHandler):
    """Custom search engine handler"""
    
    def __init__(self):
        super().__init__("custom", delay=1.0)
    
    async def search(self, query: str, max_results: int = 10) -> List[SearchResult]:
        """Implement custom search logic"""
        results = []
        
        # Your custom search implementation
        # ...
        
        return results

# Register custom handler
from core.search_engine import MultiSearchEngine

multi_engine = MultiSearchEngine()
multi_engine.handlers["custom"] = CustomSearchHandler()
```

### File Management

```python
from services.file_manager import FileManager

def manage_files():
    file_manager = FileManager()
    
    # Get storage statistics
    stats = file_manager.get_storage_stats()
    print(f"Total files: {stats['total_files']}")
    print(f"Total size: {stats['total_size']} bytes")
    
    # Export specific session
    csv_path = file_manager.export_session_to_csv(session_id=1)
    if csv_path:
        print(f"Exported to: {csv_path}")
    
    # Clean up old files
    cleaned = file_manager.cleanup_old_files(days_to_keep=30)
    print(f"Cleaned {cleaned} old files")

manage_files()
```

## 🔍 AI Integration

### AI Content Analyzer

```python
from core.ai_analyzer import AIContentAnalyzer

async def analyze_documents():
    analyzer = AIContentAnalyzer()
    
    # Analyze single document
    analysis = await analyzer.analyze_content(
        file_path="./storage/document.pdf",
        search_criteria="technical specifications, API documentation"
    )
    
    print(f"Relevance: {analysis['score']}")
    print(f"Summary: {analysis['summary']}")
    
    # Batch analysis
    file_paths = ["./storage/doc1.pdf", "./storage/doc2.html"]
    batch_results = await analyzer.batch_analyze(
        file_paths=file_paths,
        search_criteria="research papers, academic content"
    )
    
    for result in batch_results:
        print(f"{result['file_path']}: {result['score']}")

asyncio.run(analyze_documents())
```

### Query Optimization

```python
from core.query_optimizer import QueryOptimizer

async def optimize_queries():
    from core.ai_analyzer import AIContentAnalyzer
    
    analyzer = AIContentAnalyzer()
    optimizer = QueryOptimizer(analyzer)
    
    # Optimize query for different engines
    optimized_queries = await optimizer.optimize_query_for_search(
        original_query="machine learning",
        target_language="vi",
        search_engine="google",
        max_queries=3
    )
    
    for query_info in optimized_queries:
        print(f"Query: {query_info['query']}")
        print(f"Confidence: {query_info['confidence']}")

asyncio.run(optimize_queries())
```

## 🛠️ Error Handling

### Exception Handling

```python
import logging
from services.search_service import SearchService

async def robust_search():
    search_service = SearchService()
    
    try:
        session_id = await search_service.search_documents("test query", aggressive_search=True)
        results = await search_service.get_search_results(session_id)
        return results
        
    except DatabaseError as e:
        logging.error(f"Database error: {e}")
        return None
        
    except NetworkError as e:
        logging.error(f"Network error: {e}")
        return None
        
    except Exception as e:
        logging.error(f"Unexpected error: {e}")
        return None

asyncio.run(robust_search())
```

### Validation

```python
from utils.config import Config

def validate_setup():
    config = Config()
    errors = config.validate_config()
    
    if errors:
        print("Configuration errors:")
        for error in errors:
            print(f"- {error}")
        return False
    
    print("Configuration is valid")
    return True

validate_setup()
```

## 📈 Performance Optimization

### Async Best Practices

```python
import asyncio
import aiohttp

async def concurrent_searches():
    """Perform multiple searches concurrently"""
    
    queries = [
        "machine learning",
        "deep learning", 
        "neural networks"
    ]
    
    # Create tasks
    tasks = []
    for query in queries:
        task = search_service.search_documents(query, aggressive_search=True)
        tasks.append(task)
    
    # Run concurrently
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # Handle results
    for i, result in enumerate(results):
        if isinstance(result, Exception):
            print(f"Query {queries[i]} failed: {result}")
        else:
            print(f"Query {queries[i]} completed: session {result}")

asyncio.run(concurrent_searches())
```

### Resource Management

```python
from contextlib import asynccontextmanager

@asynccontextmanager
async def search_service_context():
    """Context manager for search service"""
    service = SearchService()
    try:
        yield service
    finally:
        await service.cleanup()

async def use_service():
    async with search_service_context() as service:
        session_id = await service.search_documents("test", aggressive_search=True)
        return session_id

asyncio.run(use_service())
```

## 🧪 Testing

### Unit Testing

```python
import pytest
import asyncio
from services.search_service import SearchService

@pytest.mark.asyncio
async def test_search_service():
    service = SearchService()
    
    # Test search
    session_id = await service.search_documents("test query", aggressive_search=True)
    assert isinstance(session_id, int)
    assert session_id > 0
    
    # Test results
    results = await service.get_search_results(session_id)
    assert 'total_results' in results
    assert 'results' in results

# Run tests
pytest.main([__file__])
```

### Integration Testing

```python
async def test_full_workflow():
    """Test complete search and export workflow"""
    
    service = SearchService()
    
    # Search
    session_id = await service.search_documents("machine learning", aggressive_search=True)
    
    # Wait for completion
    await asyncio.sleep(5)
    
    # Get results
    results = await service.get_search_results(session_id)
    assert results['total_results'] > 0
    
    # Export
    csv_path = await service.export_results(session_id, 'csv')
    assert csv_path is not None
    assert Path(csv_path).exists()

asyncio.run(test_full_workflow())
```

## 📚 Additional Resources

- **[Setup Guide](SETUP.md)** - Installation and configuration
- **[Usage Guide](USAGE.md)** - Command-line usage
- **[README](README.md)** - Module overview

## 🆘 Support

For API-related issues:
1. Check the error logs in `logs/documentation_collection.log`
2. Verify configuration with `python scripts/test_connection.py`
3. Test basic functionality with `python scripts/test_basic.py`
4. Report issues with detailed error messages and configuration

---

**Ready to integrate? Start with the basic search example above!** 🚀
