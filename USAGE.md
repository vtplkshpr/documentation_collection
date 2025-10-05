# 📖 Usage Guide - Documentation Collection

Complete guide for using the Documentation Collection plugin with aggressive search capabilities.

## 🎯 Getting Started

### Quick Start

```bash
# Basic search
python main.py --plugin documentation_collection --query "artificial intelligence" --max-results 5

# Aggressive search (recommended)
python main.py --plugin documentation_collection --query "machine learning" --aggressive-search --max-results 10

# Multi-language search
python main.py --plugin documentation_collection --query "neural networks" --languages "vi,ja,ko" --aggressive-search
```

### Interactive Mode

```bash
python main.py --plugin documentation_collection --interactive
```

**Step-by-step process:**
1. **Welcome screen** - Displays supported languages and search engines
2. **Enter search query** - Type your search topic
3. **Choose search mode** - Standard or aggressive search
4. **Configure results** - Set maximum results per engine
5. **Confirm and start** - Review settings and begin search
6. **Monitor progress** - Watch real-time progress and statistics
7. **View results** - Browse downloaded documents and analysis

### Command Line Mode

Perfect for scripts and automated workflows:

```bash
# Basic search
python main.py --plugin documentation_collection --query "machine learning" --max-results 5

# Aggressive search with AI analysis
python main.py --plugin documentation_collection --query "deep learning" --aggressive-search --criteria "technical specifications, research papers"

# Multi-language aggressive search
python main.py --plugin documentation_collection --query "neural networks" --languages "vi,ja,ko" --aggressive-search --max-results 3

# View previous session results
python main.py --plugin documentation_collection --session-id 1

# Export results
python main.py --plugin documentation_collection --session-id 1 --export-format both
```

## 🔧 Advanced Configuration

### Environment Variables

Create a `.env` file for custom configuration:

```env
# Database
DATABASE_URL=postgresql://user:password@localhost:5432/doc_collection

# Search Behavior
MAX_RESULTS_PER_ENGINE=20
REQUEST_DELAY=1.0
MAX_CONCURRENT_DOWNLOADS=5

# AI Features
GEMINI_API_KEY=your_api_key_here
ENABLE_AI_ANALYSIS=true

# Storage
STORAGE_BASE_PATH=./my_storage
MAX_FILE_SIZE=104857600  # 100MB

# Performance
SEARCH_PAGES=2  # Number of search result pages
AGGRESSIVE_SEARCH=false
```

### Command Line Options

```bash
python main.py --plugin documentation_collection [OPTIONS]

Options:
  --query, -q TEXT           Search topic/subject
  --aggressive-search        Enable aggressive search mode
  --criteria, -c TEXT        Filter criteria for AI analysis
  --max-results, -m INTEGER  Max results per engine (default: 20)
  --languages, -l TEXT       Additional languages (comma-separated)
  --session-id, -s INTEGER   View results from specific session
  --export-format, -f TEXT   Export format: csv, excel, both
  --interactive, -i          Interactive mode
  --stats                    Show storage statistics
  --help                     Show help message
```

## 🌍 Multi-Language Search

### Supported Languages
- **English (en)** - Default
- **Vietnamese (vi)**
- **Japanese (ja)**
- **Korean (ko)**
- **Russian (ru)**
- **Persian (fa)**

### Language Usage Examples

```bash
# Search in original language only
python main.py --plugin documentation_collection --query "artificial intelligence"

# Aggressive search in multiple languages
python main.py --plugin documentation_collection --query "machine learning" --languages "vi,ja,ko" --aggressive-search

# AI-powered query optimization with aggressive search
python main.py --plugin documentation_collection --query "neural networks" --aggressive-search --enable-ai-optimization
```

## 🤖 AI Features

### AI Content Analysis

Analyze downloaded documents against specific criteria:

```bash
# Aggressive search with analysis criteria
python main.py --plugin documentation_collection --query "computer vision" --aggressive-search --criteria "algorithms, implementations, performance metrics"

# The AI will:
# 1. Analyze each downloaded document
# 2. Score relevance against your criteria
# 3. Provide summaries and key points
# 4. Filter out irrelevant documents
```

### AI Query Optimization

Improve search queries for better results:

```bash
# Enable AI query optimization with aggressive search
python main.py --plugin documentation_collection --query "deep learning frameworks" --aggressive-search --enable-ai-optimization

# Note: This feature is slower but may provide better search results
```

### Disable AI Features

```bash
# Disable all AI analysis
python main.py --plugin documentation_collection --query "machine learning" --no-ai

# AI analysis disabled, faster processing
```

## 📊 Result Management

### Viewing Results

```bash
# List all search sessions
python main.py --plugin documentation_collection --stats

# View specific session details
python main.py --plugin documentation_collection --session-id 1

# View with export options
python main.py --plugin documentation_collection --session-id 1 --export-format csv
```

### Export Options

```bash
# Export to CSV (UTF-8 encoded)
python main.py --plugin documentation_collection --session-id 1 --export-format csv

# Export to Excel
python main.py --plugin documentation_collection --session-id 1 --export-format excel

# Export both formats
python main.py --plugin documentation_collection --session-id 1 --export-format both
```

### Storage Management

```bash
# Check storage statistics
python main.py --plugin documentation_collection --stats

# Clean up old files (via script)
python scripts/cleanup.py --days 30

# Show detailed storage info
python scripts/cleanup.py --stats
```

## 🔍 Search Engines

### Supported Engines
- **Google** - Comprehensive web search
- **Bing** - Microsoft's search engine
- **DuckDuckGo** - Privacy-focused search

### Engine Configuration

```env
# Enable/disable specific engines
ENABLED_SEARCH_ENGINES=google,bing,duckduckgo

# Configure delays (seconds)
GOOGLE_SEARCH_DELAY=1.0
BING_SEARCH_DELAY=1.5
DUCKDUCKGO_SEARCH_DELAY=1.0
```

## 📁 File Types & Storage

### Supported File Types
- **PDF** - Adobe Portable Document Format
- **DOCX** - Microsoft Word documents
- **HTML** - Web pages
- **TXT** - Plain text files
- **CSV** - Comma-separated values
- **XLSX** - Microsoft Excel files

### Storage Organization

```
storage/
├── YYYY-MM-DD/              # Date-based folders
│   ├── 001/                 # Session folders
│   │   ├── document1.pdf    # Downloaded files
│   │   ├── document2.html
│   │   ├── results_1.csv    # Export files
│   │   └── results_1.xlsx
│   └── 002/
└── YYYY-MM-DD/
```

## 🎯 Best Practices

### Effective Search Queries

**Good queries:**
```bash
# Specific and descriptive
"machine learning algorithms for image recognition"
"Python web scraping best practices"
"PostgreSQL performance optimization"

# Technical and precise
"REST API design patterns"
"microservices architecture patterns"
"Kubernetes deployment strategies"
```

**Avoid:**
```bash
# Too vague
"AI"
"programming"
"tutorial"
```

### AI Analysis Criteria

**Effective criteria:**
```bash
# Specific technical requirements
"technical specifications, API documentation, code examples"
"performance benchmarks, scalability analysis"
"security considerations, best practices"

# Content type focused
"research papers, academic publications"
"tutorials, step-by-step guides"
"case studies, real-world examples"
```

### Performance Optimization

1. **Use aggressive search** - Enable `--aggressive-search` for better results
2. **Start small** - Begin with 5-10 results per engine
3. **Use specific queries** - More precise searches yield better results
4. **Configure delays** - Balance speed vs. rate limiting
5. **Monitor storage** - Regular cleanup of old files
6. **Selective AI** - Use AI analysis only when needed

## 🛠️ Troubleshooting

### Common Issues

**Database connection errors:**
```bash
# Test database connection
python scripts/test_connection.py

# Check PostgreSQL status
sudo systemctl status postgresql
```

**Import errors:**
```bash
# Check virtual environment
which python
# Should show your venv path

# Reinstall dependencies
pip install -r requirements.txt --force-reinstall
```

**Storage permission errors:**
```bash
# Fix permissions
chmod -R 755 storage/
chmod -R 755 logs/

# Check ownership
ls -la storage/
```

**AI analysis not working:**
```bash
# Check API key
echo $GEMINI_API_KEY

# Test without AI
python main.py --plugin documentation_collection --query "test" --no-ai
```

### Performance Issues

**Slow downloads:**
- Increase `REQUEST_DELAY` in configuration
- Reduce `MAX_CONCURRENT_DOWNLOADS`
- Check network connectivity

**High memory usage:**
- Reduce `MAX_RESULTS_PER_ENGINE`
- Use `--no-ai` for faster processing
- Clean up old storage files

**Storage full:**
```bash
# Check storage usage
python main.py --plugin documentation_collection --stats

# Clean old files
python scripts/cleanup.py --days 7
```

## 📈 Advanced Usage

### Batch Processing

```bash
# Process multiple queries with aggressive search
for query in "machine learning" "deep learning" "neural networks"; do
    python main.py --plugin documentation_collection --query "$query" --aggressive-search --max-results 5 --no-ai
done
```

### Integration with Scripts

```python
# Example Python integration
import subprocess
import json

def search_documents(query, max_results=10):
    cmd = [
        "python", "main.py",
        "--plugin", "documentation_collection",
        "--query", query,
        "--aggressive-search",
        "--max-results", str(max_results),
        "--export-format", "csv"
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    return result.returncode == 0
```

### Monitoring and Logging

```bash
# View logs
tail -f logs/documentation_collection.log

# Monitor storage
watch -n 5 'python main.py --plugin documentation_collection --stats'
```

---

**Ready to start? Try the interactive mode: `python main.py --plugin documentation_collection --interactive`** 🚀
