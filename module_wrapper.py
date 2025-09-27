"""
Module wrapper to implement ModuleInterface for documentation_collection
"""
import asyncio
import logging
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional

# Add current directory and parent directory to path for imports
current_dir = str(Path(__file__).parent)
parent_dir = str(Path(__file__).parent.parent)
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from lkwolfSAI_ablilities.module_interface import ModuleInterface, ModuleInfo
from module_info import get_module_info
from services.search_service import SearchService
from services.file_manager import FileManager
from utils.database import db_manager

logger = logging.getLogger(__name__)

class DocumentationCollectionModule(ModuleInterface):
    """Documentation Collection module implementation"""
    
    def __init__(self):
        self._module_info = get_module_info()
        self.search_service = SearchService()
        self.file_manager = FileManager()
        self._initialized = False
    
    @property
    def module_info(self) -> ModuleInfo:
        """Return module metadata"""
        return self._module_info
    
    async def initialize(self) -> bool:
        """Initialize module"""
        try:
            logger.info(f"Initializing {self.module_info.name}...")
            
            # Initialize database if required
            if "database" in self.module_info.required_services:
                # Test database connection
                if not db_manager.test_connection():
                    logger.error("Database connection failed")
                    return False
            
            # Initialize services
            # Note: SearchService and FileManager are initialized on demand
            
            self._initialized = True
            logger.info(f"✓ {self.module_info.name} initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize {self.module_info.name}: {e}")
            return False
    
    async def cleanup(self) -> bool:
        """Cleanup module resources"""
        try:
            logger.info(f"Cleaning up {self.module_info.name}...")
            
            # Close database connections
            if hasattr(db_manager, 'engine') and db_manager.engine:
                db_manager.engine.dispose()
            
            self._initialized = False
            logger.info(f"✓ {self.module_info.name} cleaned up successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to cleanup {self.module_info.name}: {e}")
            return False
    
    def get_cli_commands(self) -> List[Any]:
        """Return Click commands for CLI integration"""
        # Import the main CLI from the existing main.py
        try:
            from main import main as doc_main
            return [doc_main]
        except ImportError as e:
            logger.error(f"Failed to import CLI commands: {e}")
            return []
    
    async def health_check(self) -> Dict[str, Any]:
        """Return module health status"""
        health_status = {
            "module": self.module_info.name,
            "version": self.module_info.version,
            "status": "healthy" if self._initialized else "not_initialized",
            "services": {}
        }
        
        try:
            # Check database health
            if "database" in self.module_info.required_services:
                health_status["services"]["database"] = "healthy" if db_manager.test_connection() else "unhealthy"
            
            # Check file manager health
            storage_stats = self.file_manager.get_storage_stats()
            health_status["services"]["file_manager"] = "healthy" if storage_stats else "unhealthy"
            
            # Check search service health (basic check)
            health_status["services"]["search_service"] = "healthy"
            
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            health_status["services"]["error"] = str(e)
        
        return health_status
    
    def validate_config(self, config: Dict[str, Any]) -> List[str]:
        """Validate module configuration"""
        errors = []
        
        # Validate database URL
        if "DATABASE_URL" in config:
            db_url = config["DATABASE_URL"]
            if not db_url or not db_url.startswith(("postgresql://", "sqlite://")):
                errors.append("DATABASE_URL must be a valid database URL")
        
        # Validate numeric settings
        numeric_settings = ["MAX_RESULTS_PER_ENGINE", "REQUEST_DELAY"]
        for setting in numeric_settings:
            if setting in config:
                try:
                    value = float(config[setting])
                    if setting == "MAX_RESULTS_PER_ENGINE" and value < 1:
                        errors.append("MAX_RESULTS_PER_ENGINE must be positive")
                    elif setting == "REQUEST_DELAY" and value < 0:
                        errors.append("REQUEST_DELAY must be non-negative")
                except (ValueError, TypeError):
                    errors.append(f"{setting} must be a valid number")
        
        # Validate storage path
        if "STORAGE_BASE_PATH" in config:
            storage_path = config["STORAGE_BASE_PATH"]
            if not storage_path:
                errors.append("STORAGE_BASE_PATH cannot be empty")
        
        return errors

# For compatibility with the existing main.py
def get_module_class():
    """Get the module class for registration"""
    return DocumentationCollectionModule
