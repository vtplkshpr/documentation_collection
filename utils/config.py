"""
Configuration management for documentation collection module
"""
import os
from typing import List, Dict, Any
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    """Configuration class for documentation collection"""
    
    # Database Configuration
    DATABASE_URL = os.getenv('DATABASE_URL')
    
    # Search Configuration
    MAX_RESULTS_PER_ENGINE = int(os.getenv('MAX_RESULTS_PER_ENGINE', '10'))
    REQUEST_DELAY = float(os.getenv('REQUEST_DELAY', '1.0'))
    MAX_CONCURRENT_DOWNLOADS = int(os.getenv('MAX_CONCURRENT_DOWNLOADS', '5'))
    
    # Storage Configuration
    STORAGE_BASE_PATH = os.getenv('STORAGE_BASE_PATH', '/home/lkshpr/ownpr/lkwolfSAI/lkwolfSAI_storage/lkwolfSAI_abilities/documentation_collection')
    MAX_FILE_SIZE = int(os.getenv('MAX_FILE_SIZE', '52428800'))  # 50MB
    
    # Logging Configuration
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FILE = os.getenv('LOG_FILE', './logs/documentation_collection.log')
    
    # Translation Configuration
    TRANSLATION_SERVICE = os.getenv('TRANSLATION_SERVICE', 'googletrans')
    TRANSLATION_CACHE = os.getenv('TRANSLATION_CACHE', 'True').lower() == 'true'
    
    # Search Engines Configuration
    ENABLED_SEARCH_ENGINES = os.getenv('ENABLED_SEARCH_ENGINES', 'google,bing,duckduckgo,baidu').split(',')
    GOOGLE_SEARCH_DELAY = float(os.getenv('GOOGLE_SEARCH_DELAY', '1.0'))
    BING_SEARCH_DELAY = float(os.getenv('BING_SEARCH_DELAY', '1.5'))
    DUCKDUCKGO_SEARCH_DELAY = float(os.getenv('DUCKDUCKGO_SEARCH_DELAY', '1.0'))
    BAIDU_SEARCH_DELAY = float(os.getenv('BAIDU_SEARCH_DELAY', '1.5'))
    
    # Supported Languages
    SUPPORTED_LANGUAGES = ['en', 'vi', 'ja', 'ko', 'ru', 'fa', 'zh']
    LANGUAGE_NAMES = {
        'en': 'English',
        'vi': 'Vietnamese', 
        'ja': 'Japanese',
        'ko': 'Korean',
        'ru': 'Russian',
        'fa': 'Persian',
        'zh': 'Chinese (Simplified)'
    }
    
    # File Types
    SUPPORTED_FILE_TYPES = ['.pdf', '.doc', '.docx', '.txt', '.html', '.htm', '.rtf']
    
    # Search Engine Delays
    SEARCH_DELAYS = {
        'google': GOOGLE_SEARCH_DELAY,
        'bing': BING_SEARCH_DELAY,
        'duckduckgo': DUCKDUCKGO_SEARCH_DELAY,
        'baidu': BAIDU_SEARCH_DELAY
    }
    
    @classmethod
    def get_search_delay(cls, engine: str) -> float:
        """Get delay for specific search engine"""
        return cls.SEARCH_DELAYS.get(engine, cls.REQUEST_DELAY)
    
    @classmethod
    def validate_config(cls) -> List[str]:
        """Validate configuration and return list of errors"""
        errors = []
        
        if not cls.DATABASE_URL:
            errors.append("DATABASE_URL is required")
        
        if cls.MAX_RESULTS_PER_ENGINE <= 0:
            errors.append("MAX_RESULTS_PER_ENGINE must be positive")
        
        if cls.REQUEST_DELAY < 0:
            errors.append("REQUEST_DELAY must be non-negative")
        
        if cls.MAX_CONCURRENT_DOWNLOADS <= 0:
            errors.append("MAX_CONCURRENT_DOWNLOADS must be positive")
        
        if not cls.STORAGE_BASE_PATH:
            errors.append("STORAGE_BASE_PATH is required")
        
        return errors

# Global config instance
config = Config()
