#!/usr/bin/env python3
"""
Test script for new search engines (Baidu)
"""
import asyncio
import sys
import os
import logging
from pathlib import Path

# Add the parent directory to the path
sys.path.append(str(Path(__file__).parent.parent))

from core.search_engine import MultiSearchEngine
from core.baidu_search_handler import BaiduSearchHandler
from utils.config import config

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_baidu_search():
    """Test Baidu search functionality with translation"""
    print("\n🔍 Testing Baidu Search Engine")
    print("=" * 50)
    
    try:
        handler = BaiduSearchHandler()
        query = "technical documentation"
        max_results = 5
        
        print(f"Searching for: '{query}' (will be translated to Chinese)")
        results = await handler.search(query, max_results)
        
        print(f"Found {len(results)} results:")
        for i, result in enumerate(results, 1):
            print(f"{i}. {result.title}")
            print(f"   URL: {result.url}")
            print(f"   Snippet: {result.snippet[:100]}...")
            print()
        
        return len(results) > 0
        
    except Exception as e:
        print(f"❌ Baidu test failed: {e}")
        return False

async def test_multi_engine():
    """Test multi-engine search with new engines"""
    print("\n🔍 Testing Multi-Engine Search")
    print("=" * 50)
    
    try:
        multi_engine = MultiSearchEngine()
        query = "machine learning"
        max_results = 3
        
        print(f"Searching all engines for: '{query}'")
        print(f"Available engines: {multi_engine.get_available_engines()}")
        
        results = await multi_engine.search_all_engines(query, max_results)
        
        print(f"Found {len(results)} total results:")
        for i, result in enumerate(results, 1):
            print(f"{i}. [{result.search_engine}] {result.title}")
            print(f"   URL: {result.url}")
            print()
        
        return len(results) > 0
        
    except Exception as e:
        print(f"❌ Multi-engine test failed: {e}")
        return False

async def test_baidu_translation():
    """Test Baidu translation functionality"""
    print("\n🔍 Testing Baidu Translation")
    print("=" * 50)
    
    try:
        handler = BaiduSearchHandler()
        
        test_queries = [
            "artificial intelligence",
            "machine learning algorithms", 
            "deep learning neural networks"
        ]
        
        for query in test_queries:
            print(f"Original: '{query}'")
            translated = await handler._translate_to_chinese(query)
            print(f"Translated: '{translated}'")
            print()
        
        return True
        
    except Exception as e:
        print(f"❌ Translation test failed: {e}")
        return False

async def run_all_tests():
    """Run all tests"""
    print("🚀 Starting New Search Engines Tests")
    print("=" * 60)
    
    tests = [
        ("Baidu Search", test_baidu_search),
        ("Baidu Translation", test_baidu_translation),
        ("Multi-Engine Search", test_multi_engine),
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        print(f"\n🧪 Running {test_name}...")
        try:
            result = await test_func()
            results[test_name] = result
            status = "✅ PASSED" if result else "❌ FAILED"
            print(f"{status}: {test_name}")
        except Exception as e:
            print(f"❌ ERROR in {test_name}: {e}")
            results[test_name] = False
    
    # Summary
    print("\n📊 Test Summary")
    print("=" * 30)
    passed = sum(results.values())
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅" if result else "❌"
        print(f"{status} {test_name}")
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! New search engines are working correctly.")
    else:
        print("⚠️  Some tests failed. Check the logs above for details.")
    
    return passed == total

if __name__ == "__main__":
    # Run tests
    success = asyncio.run(run_all_tests())
    sys.exit(0 if success else 1)
