#!/usr/bin/env python3
"""
Basic functionality test script
"""
import sys
import os
import asyncio
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from utils.config import config
from utils.database import db_manager
from core.simple_translator import SimpleTranslationService
from core.search_engine import MultiSearchEngine
from services.file_manager import FileManager
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_translation():
    """Test translation service"""
    print("Testing translation service...")
    try:
        translator = SimpleTranslationService()
        
        # Test single translation
        result = translator.translate_text("Hello world", "vi")
        if result:
            print(f"✓ Translation test passed: {result}")
        else:
            print("✗ Translation test failed")
            return False
        
        # Test multi-language translation
        translations = translator.translate_to_all_languages("artificial intelligence")
        if len(translations) > 0:
            print(f"✓ Multi-language translation test passed: {len(translations)} languages")
        else:
            print("✗ Multi-language translation test failed")
            return False
        
        return True
        
    except Exception as e:
        print(f"✗ Translation test error: {e}")
        return False

async def test_search_engine():
    """Test search engine"""
    print("Testing search engine...")
    try:
        search_engine = MultiSearchEngine()
        
        # Test search
        results = await search_engine.search_all_engines("artificial intelligence", 3)
        if results:
            print(f"✓ Search engine test passed: {len(results)} results")
        else:
            print("✗ Search engine test failed")
            return False
        
        return True
        
    except Exception as e:
        print(f"✗ Search engine test error: {e}")
        return False

def test_file_manager():
    """Test file manager"""
    print("Testing file manager...")
    try:
        file_manager = FileManager()
        
        # Test directory creation
        test_session_id = 999
        session_dir = file_manager.create_session_directory(test_session_id)
        if session_dir.exists():
            print(f"✓ File manager test passed: {session_dir}")
            
            # Cleanup
            import shutil
            shutil.rmtree(session_dir)
            return True
        else:
            print("✗ File manager test failed")
            return False
        
    except Exception as e:
        print(f"✗ File manager test error: {e}")
        return False

async def run_tests():
    """Run all tests"""
    print("Running basic functionality tests...\n")
    
    # Test database connection
    print("Testing database connection...")
    if not db_manager.test_connection():
        print("✗ Database connection failed!")
        return False
    print("✓ Database connection successful!")
    
    # Test translation
    if not await test_translation():
        return False
    
    # Test search engine
    if not await test_search_engine():
        return False
    
    # Test file manager
    if not test_file_manager():
        return False
    
    print("\n✓ All tests passed!")
    return True

if __name__ == "__main__":
    success = asyncio.run(run_tests())
    sys.exit(0 if success else 1)
