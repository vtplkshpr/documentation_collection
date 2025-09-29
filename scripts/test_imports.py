#!/usr/bin/env python3
"""
Simple test to check if new search engines can be imported
"""
import sys
from pathlib import Path

# Add the parent directory to the path
sys.path.append(str(Path(__file__).parent.parent))

def test_imports():
    """Test if new modules can be imported"""
    print("🧪 Testing imports...")
    
    try:
        from utils.config import config
        print("✅ Config imported successfully")
        print(f"   Enabled engines: {config.ENABLED_SEARCH_ENGINES}")
        print(f"   Supported languages: {config.SUPPORTED_LANGUAGES}")
    except Exception as e:
        print(f"❌ Config import failed: {e}")
        return False
    
    
    try:
        from core.baidu_search_handler import BaiduSearchHandler
        print("✅ BaiduSearchHandler imported successfully")
    except Exception as e:
        print(f"❌ BaiduSearchHandler import failed: {e}")
        return False
    
    return True

if __name__ == "__main__":
    success = test_imports()
    if success:
        print("\n🎉 All imports successful! New search engines are ready.")
    else:
        print("\n⚠️  Some imports failed. Check dependencies.")
    sys.exit(0 if success else 1)
