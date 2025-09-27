# 📚 Documentation Collection - Setup Guide

**Detailed installation and configuration guide**

## 🎯 Overview

This guide provides step-by-step instructions for setting up the Documentation Collection module as a standalone tool.

## 📋 Prerequisites

- **Operating System**: Linux, macOS, or Windows with WSL2
- **Python**: 3.8 or higher
- **PostgreSQL**: 12 or higher
- **Internet Connection**: For downloading dependencies and documents

## 🚀 Installation Steps

### Step 1: Install PostgreSQL

#### Ubuntu/Debian:
```bash
# Update package list
sudo apt update

# Install PostgreSQL
sudo apt install postgresql postgresql-contrib

# Start PostgreSQL service
sudo systemctl start postgresql
sudo systemctl enable postgresql

# Create database and user
sudo -u postgres psql
```

#### In PostgreSQL shell:
```sql
-- Create database
CREATE DATABASE doc_collection;

-- Create user
CREATE USER doc_user WITH PASSWORD 'your_password';

-- Grant privileges
GRANT ALL PRIVILEGES ON DATABASE doc_collection TO doc_user;

-- Exit
\q
```

### Step 2: Setup Python Environment

```bash
# Navigate to project directory
cd documentation-collection

# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Step 3: Configure Environment

```bash
# Copy environment template
cp .env.example .env

# Edit configuration
nano .env
```

#### Environment Variables:
```env
# Database Configuration
DATABASE_URL=postgresql://doc_user:your_password@localhost:5432/doc_collection

# Search Configuration
MAX_RESULTS_PER_ENGINE=10
REQUEST_DELAY=1.0
MAX_CONCURRENT_DOWNLOADS=5

# Storage Configuration
STORAGE_BASE_PATH=./storage
MAX_FILE_SIZE=52428800

# AI Configuration (Optional)
GEMINI_API_KEY=your_gemini_api_key

# Logging Configuration
LOG_LEVEL=INFO
LOG_FILE=./logs/documentation_collection.log
```

### Step 4: Create Required Directories

```bash
# Create storage directory
mkdir -p storage

# Create logs directory
mkdir -p logs

# Create temp directory
mkdir -p temp

# Set permissions
chmod 755 storage
chmod 755 logs
chmod 755 temp
```

### Step 5: Initialize Database

```bash
# Run database initialization script
python scripts/init_database.py
```

### Step 6: Verify Installation

```bash
# Test database connection
python scripts/test_connection.py

# Run basic functionality test
python scripts/test_basic.py
```

## 🎮 Usage

### Running Documentation Collection

#### Method 1: Direct execution
```bash
cd documentation-collection
source venv/bin/activate  # On Windows: venv\Scripts\activate
python main.py --help
```

#### Method 2: Interactive mode (Recommended)
```bash
python main.py --interactive
```

### Usage Modes

#### A. Interactive Mode (Recommended for beginners)
```bash
# Run interactive mode
python main.py --interactive
```

**How to use:**
1. Run the command above
2. System displays a beautiful interface with language and search engine information
3. Enter search query when prompted (e.g., "artificial intelligence")
4. Enter AI analysis criteria (optional, e.g., "technical documents, specifications, design")
5. Enter maximum results per engine (default: 10)
6. Confirm to start searching
7. System will:
   - Use original query directly (no AI optimization)
   - Search across 3 engines (Google, Bing, DuckDuckGo)
   - Download found documents
   - AI analyze results by criteria (if provided)
   - Display results and statistics
   - Automatically export CSV and Excel

#### B. Command Line Mode (For automation)
```bash
# Search with specific query (no AI optimization - default)
python main.py --query "machine learning" --max-results 5

# Search with AI query optimization (slower but potentially more optimized)
python main.py --query "artificial intelligence" --enable-ai-optimization

# Search with AI analysis criteria
python main.py --query "deep learning" --criteria "technical specifications, research papers, implementation details"

# Search with additional languages
python main.py --query "neural networks" --languages "vi,ja,ko" --max-results 3

# Combine AI optimization + AI analysis + multi-language
python main.py --query "computer vision" --enable-ai-optimization --criteria "algorithms, implementations" --languages "vi,ja"

# View results of specific session
python main.py --session-id 1

# View storage statistics
python main.py --stats
```

#### C. Export Results
```bash
# Export session 1 results to CSV
python main.py --session-id 1 --export-format csv

# Export session 1 results to Excel
python main.py --session-id 1 --export-format excel

# Export both CSV and Excel
python main.py --session-id 1 --export-format both
```

### Real-world Usage Examples

#### Example 1: Search AI documents with specific criteria
```bash
# Interactive mode with AI analysis
python main.py --interactive
# Enter query: "artificial intelligence"
# Enter criteria: "technical specifications, research papers, implementation guides"
# Result: Search "artificial intelligence" across 3 engines, AI analyzes results by criteria
```

#### Example 2: Multi-language search
```bash
# Command line mode with multiple languages
python main.py --query "machine learning" --languages "vi,ja,ko" --max-results 5
```

#### Example 3: Technical search with AI optimization
```bash
# Search technical documents with AI optimization (slower but potentially more optimized)
python main.py --query "056型 护卫舰 燃油 系统 原理图" --enable-ai-optimization --criteria "technical specifications, system diagrams, fuel system documentation"
```

#### Example 4: View and export results
```bash
# View session 1 results
python main.py --session-id 1

# Export results (CSV with proper UTF-8 encoding)
python main.py --session-id 1 --export-format both
```

### Output Structure

#### Database Tables:
- `search_sessions`: Search session information
- `search_results`: Detailed search results
- `translation_cache`: Translation cache

#### File Storage:
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
    └── 003/
```

#### Export Files:
- `results_X.csv`: Results in CSV format
- `results_X.xlsx`: Results in Excel format
- Both files contain: title, url, language, search_engine, file_path, download_status, created_at

## 🛠️ Troubleshooting

### Database Connection Issues
```bash
# Check database connection
python scripts/test_connection.py

# Reinitialize database
python scripts/init_database.py
```

### Import Issues
```bash
# Check virtual environment
which python
# Should show your venv path

# Reinstall dependencies
pip install -r requirements.txt --force-reinstall
```

### Permission Issues
```bash
# Set directory permissions
chmod -R 755 .
chmod -R 755 logs/
chmod -R 755 storage/
```

### Usage Tips

1. **Effective Queries**: Use specific keywords, avoid overly general terms
2. **AI Analysis**: Use `--criteria` for AI to analyze results by specific criteria
3. **Multi-language**: Use `--languages` to search in multiple languages
4. **Max Results**: Start with 5-10 results per engine for testing
5. **Interactive Mode**: Best for beginners, has beautiful interface
6. **Command Line**: Good for automation and scripts
7. **Export**: Always export results for storage and analysis (CSV supports UTF-8)
8. **Storage**: Check storage directory to see downloaded files
9. **Logs**: Check log files for debugging if errors occur
10. **Speed**: System no longer has AI query optimization by default, faster searching

### Common Issues

#### Database Connection Errors:
- Check PostgreSQL is running: `sudo systemctl status postgresql`
- Check connection string in .env
- Check firewall: `sudo ufw status`

#### Permission Errors:
- Set directory permissions: `chmod -R 755 .`
- Check user permissions: `ls -la`

#### Import Errors:
- Check virtual environment: `which python`
- Reinstall dependencies: `pip install -r requirements.txt --force-reinstall`

#### CSV Encoding Errors:
- CSV exported with UTF-8 BOM, compatible with Excel
- If encoding still fails, open with UTF-8 supporting text editor
- Check system locale: `locale`

#### AI Analysis Issues:
- AI analysis only works when Gemini API key is provided
- If API key not available, search still runs normally
- No more timeouts from AI optimization (unless manually enabled)

## 🔧 Advanced Configuration

### Search Engine Configuration:
- Edit `utils/config.py` file
- Add API keys if needed

### Translation Configuration:
- Install Google Translate API key
- Or use free library (already included)

### Storage Configuration:
- Change storage path in .env
- Configure cleanup policy for old files

## 📚 Additional Resources

- **[Usage Guide](USAGE.md)**: Complete usage instructions
- **[API Reference](API.md)**: Programmatic API documentation
- **[README](README.md)**: Module overview and quick start

---

**Documentation Collection Setup Guide - Ready to start collecting documents!** 🚀
