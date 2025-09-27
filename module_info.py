"""
Module metadata and configuration for Documentation Collection Module
"""
import sys
from pathlib import Path
from typing import Dict, Any, List

# Add parent directory to path for imports
parent_dir = str(Path(__file__).parent.parent)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from lkwolfSAI_ablilities.module_interface import ModuleInfo, ModuleStatus

def get_module_info() -> ModuleInfo:
    """Return module metadata"""
    return ModuleInfo(
        name="documentation_collection",
        version="1.0.0",
        description="Tìm kiếm và thu thập tài liệu online đa ngôn ngữ",
        author="lkwolfSAI Team",
        status=ModuleStatus.ACTIVE,
        dependencies=[
            "click>=8.0.0",
            "rich>=13.0.0",
            "asyncio",
            "aiohttp",
            "aiofiles",
            "beautifulsoup4",
            "pandas",
            "openpyxl",
            "PyPDF2",
            "python-docx",
            "sqlalchemy",
            "psycopg2-binary"
        ],
        supported_languages=["en", "vi", "ja", "ko", "ru", "fa"],
        required_services=["database"],  # database, redis, ollama, etc.
        config_schema={
            "DATABASE_URL": {
                "type": "string",
                "default": "postgresql://lkwolf:admin!23$%@localhost:5432/lkwolfsai",
                "description": "Database connection URL"
            },
            "MAX_RESULTS_PER_ENGINE": {
                "type": "integer",
                "default": 10,
                "description": "Maximum results per search engine"
            },
            "REQUEST_DELAY": {
                "type": "float",
                "default": 1.0,
                "description": "Delay between requests in seconds"
            },
            "STORAGE_BASE_PATH": {
                "type": "string",
                "default": "/home/lkshpr/ownpr/lkwolfSAI/lkwolfSAI_storage/lkwolfSAI_abilities/documentation_collection",
                "description": "Base path for file storage"
            }
        },
        commands=[
            {
                "name": "search",
                "description": "Search and collect documents",
                "options": [
                    {
                        "name": "--query",
                        "type": "string",
                        "required": True,
                        "help": "Search query"
                    },
                    {
                        "name": "--max-results",
                        "type": "integer",
                        "required": False,
                        "help": "Maximum results per engine"
                    },
                    {
                        "name": "--criteria",
                        "type": "string",
                        "required": False,
                        "help": "Filter criteria for AI analysis"
                    }
                ]
            },
            {
                "name": "interactive",
                "description": "Interactive search mode",
                "options": []
            },
            {
                "name": "session",
                "description": "View session results",
                "options": [
                    {
                        "name": "--session-id",
                        "type": "integer",
                        "required": True,
                        "help": "Session ID to view"
                    }
                ]
            },
            {
                "name": "stats",
                "description": "Show storage statistics",
                "options": []
            }
        ]
    )
