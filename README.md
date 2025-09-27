# 📚 Documentation Collection

**Multi-language document search and collection tool with AI-powered analysis**

## 🎯 Overview

Documentation Collection is a powerful tool for searching, downloading, and analyzing documents from multiple sources across different languages. It supports intelligent search across multiple engines, automatic document download, and AI-powered content analysis.

## ✨ Features

- **🌍 Multi-language Search**: Search in 6 languages (EN, VI, JA, KO, RU, FA)
- **🔍 Multi-engine Search**: Google, Bing, DuckDuckGo support
- **🤖 AI Translation**: Automatic query translation
- **📥 Document Download**: PDF, DOCX, HTML, TXT, CSV, Excel
- **🗄️ Database Storage**: PostgreSQL with full metadata
- **📊 Export System**: CSV and Excel export
- **🎨 Beautiful CLI**: Rich terminal interface
- **🛡️ Error Handling**: Robust error handling and logging

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- PostgreSQL database
- Virtual environment

### Installation

1. **Clone or download this module**
```bash
# If standalone installation
git clone <your-repo-url> documentation-collection
cd documentation-collection
```

2. **Create virtual environment**
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Setup database**
```bash
# Install PostgreSQL and create database
sudo apt install postgresql postgresql-contrib
sudo -u postgres psql
```

In PostgreSQL shell:
```sql
CREATE DATABASE doc_collection;
CREATE USER doc_user WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE doc_collection TO doc_user;
\q
```

5. **Configure environment**
```bash
cp .env.example .env
# Edit .env with your database credentials
```

6. **Initialize database**
```bash
python scripts/init_database.py
```

### Usage

#### Interactive Mode (Recommended)
```bash
python main.py --interactive
```

#### Command Line Mode
```bash
# Search with specific query
python main.py --query "artificial intelligence" --max-results 5

# View previous results
python main.py --session-id 1

# Export results
python main.py --session-id 1 --export-format both
```

## 📖 Detailed Documentation

- **[Setup Guide](SETUP.md)** - Detailed installation and configuration
- **[Usage Guide](USAGE.md)** - Complete usage instructions
- **[API Reference](API.md)** - Programmatic API documentation

## 🏗️ Architecture

```
documentation_collection/
├── main.py                    # CLI entry point
├── core/                      # Core business logic
│   ├── ai_analyzer.py        # AI content analysis
│   ├── search_engine.py      # Search engine handlers
│   ├── document_downloader.py # Document download logic
│   └── query_optimizer.py    # Query optimization
├── services/                  # Business services
│   ├── search_service.py     # Main search orchestration
│   └── file_manager.py       # File management
├── models/                    # Database models
│   └── search_session.py     # SQLAlchemy models
├── utils/                     # Utilities
│   ├── config.py             # Configuration management
│   └── database.py           # Database connection
└── scripts/                   # Helper scripts
    ├── init_database.py      # Database initialization
    └── test_connection.py    # Connection testing
```

## 🔧 Configuration

### Environment Variables

```env
# Database Configuration
DATABASE_URL=postgresql://user:password@localhost:5432/doc_collection

# Search Configuration
MAX_RESULTS_PER_ENGINE=10
REQUEST_DELAY=1.0
MAX_CONCURRENT_DOWNLOADS=5

# Storage Configuration
STORAGE_BASE_PATH=./storage
MAX_FILE_SIZE=52428800

# AI Configuration (Optional)
GEMINI_API_KEY=your_gemini_api_key

# Logging
LOG_LEVEL=INFO
LOG_FILE=./logs/documentation_collection.log
```

## 📊 Output Structure

### Database Tables
- `search_sessions`: Search session metadata
- `search_results`: Individual search results
- `translation_cache`: Translation cache

### File Storage
```
storage/
├── 2025-01-20/
│   ├── 001/
│   │   ├── document1.pdf
│   │   ├── document2.html
│   │   ├── results_1.csv
│   │   └── results_1.xlsx
│   └── 002/
└── 2025-01-21/
```

### Export Files
- `results_X.csv`: CSV export with UTF-8 encoding
- `results_X.xlsx`: Excel export with formatting

## 🛠️ Troubleshooting

### Database Connection Issues
```bash
python scripts/test_connection.py
```

### Permission Issues
```bash
chmod -R 755 storage/
chmod -R 755 logs/
```

### Import Errors
```bash
# Check virtual environment
which python
# Should show your venv path

# Reinstall dependencies
pip install -r requirements.txt --force-reinstall
```

## 🧪 Testing

```bash
# Test basic functionality
python scripts/test_basic.py

# Test database connection
python scripts/test_connection.py

# Run full test suite
python -m pytest tests/
```

## 📈 Performance Tips

1. **Start with smaller result sets** (5-10 results per engine)
2. **Use interactive mode** for better user experience
3. **Configure appropriate delays** between requests
4. **Monitor storage usage** regularly
5. **Use AI analysis selectively** to save processing time

## 🔒 Security Considerations

- **Database credentials**: Store securely in environment variables
- **API keys**: Never commit API keys to version control
- **File permissions**: Ensure proper file permissions for storage
- **Network security**: Use HTTPS for external API calls

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

- **Issues**: Report bugs and feature requests on GitHub Issues
- **Documentation**: Check the documentation files in this repository
- **Community**: Join our community discussions

---

**Ready to start collecting documents? Run `python main.py --interactive` and begin your search!** 🚀
