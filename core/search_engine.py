"""
Search engine handlers for multiple search providers
"""
import asyncio
import aiohttp
import logging
from typing import List, Dict, Any, Optional
from googlesearch import search as google_search
try:
    from ddgs import DDGS
except ImportError:
    from duckduckgo_search import DDGS
import time
from utils.config import config

logger = logging.getLogger(__name__)

class SearchResult:
    """Search result data class"""
    def __init__(self, title: str, url: str, snippet: str = "", search_engine: str = ""):
        self.title = title
        self.url = url
        self.snippet = snippet
        self.search_engine = search_engine

class SearchEngineHandler:
    """Base class for search engine handlers"""
    
    def __init__(self, name: str, delay: float = 1.0):
        self.name = name
        self.delay = delay
    
    async def search(self, query: str, max_results: int = 10) -> List[SearchResult]:
        """Search for documents"""
        raise NotImplementedError
    
    async def _rate_limit(self):
        """Apply rate limiting"""
        if self.delay > 0:
            await asyncio.sleep(self.delay)

class GoogleSearchHandler(SearchEngineHandler):
    """Google Search handler"""
    
    def __init__(self):
        super().__init__("google", config.get_search_delay("google"))
    
    async def search(self, query: str, max_results: int = 10) -> List[SearchResult]:
        """Search using Google"""
        results = []
        try:
            logger.info(f"Searching Google for: {query}")
            
            # Google search is synchronous, so we run it in executor
            loop = asyncio.get_event_loop()
            search_results = await loop.run_in_executor(
                None, 
                lambda: list(google_search(query, num_results=max_results, sleep_interval=0.5))
            )
            
            for url in search_results:
                if url:
                    result = SearchResult(
                        title=f"Document from {url}",
                        url=url,
                        search_engine=self.name
                    )
                    results.append(result)
            
            await self._rate_limit()
            logger.info(f"Google search completed: {len(results)} results")
            
        except Exception as e:
            logger.error(f"Google search failed: {e}")
        
        return results

class BingSearchHandler(SearchEngineHandler):
    """Bing Search handler"""
    
    def __init__(self):
        super().__init__("bing", config.get_search_delay("bing"))
    
    async def search(self, query: str, max_results: int = 10) -> List[SearchResult]:
        """Search using Bing"""
        results = []
        try:
            logger.info(f"Searching Bing for: {query}")
            
            # Use aiohttp for async requests
            async with aiohttp.ClientSession() as session:
                # Try multiple pages to get more results
                for page in range(0, min(3, max_results // 10 + 1)):  # Try up to 3 pages
                    start = page * 10
                    search_url = f"https://www.bing.com/search?q={query}&first={start}&count=10"
                    headers = {
                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
                    }
                    
                    try:
                        async with session.get(search_url, headers=headers) as response:
                            if response.status == 200:
                                html = await response.text()
                                # Simple URL extraction from Bing results
                                import re
                                # Look for URLs in the HTML (basic pattern)
                                url_pattern = r'href="(https?://[^"]+)"'
                                found_urls = re.findall(url_pattern, html)
                                
                                for url in found_urls[:10]:  # Limit to 10 per page
                                    if len(results) >= max_results:
                                        break
                                    # Filter out Bing internal URLs
                                    if not any(domain in url for domain in ['bing.com', 'microsoft.com', 'live.com']):
                                        results.append(SearchResult(
                                            title=f"Document from {url}",
                                            url=url,
                                            search_engine=self.name
                                        ))
                                
                                if len(results) >= max_results:
                                    break
                                    
                    except Exception as e:
                        logger.warning(f"Bing page {page} failed: {e}")
                        continue
            
            await self._rate_limit()
            logger.info(f"Bing search completed: {len(results)} results")
            
        except Exception as e:
            logger.error(f"Bing search failed: {e}")
        
        return results

class DuckDuckGoSearchHandler(SearchEngineHandler):
    """DuckDuckGo Search handler"""
    
    def __init__(self):
        super().__init__("duckduckgo", config.get_search_delay("duckduckgo"))
    
    async def search(self, query: str, max_results: int = 10) -> List[SearchResult]:
        """Search using DuckDuckGo"""
        results = []
        try:
            logger.info(f"Searching DuckDuckGo for: {query}")
            
            # DuckDuckGo search is synchronous, so we run it in executor
            loop = asyncio.get_event_loop()
            search_results = await loop.run_in_executor(
                None,
                lambda: list(DDGS().text(query, max_results=max_results))
            )
            
            for result_data in search_results:
                if result_data and 'href' in result_data:
                    result = SearchResult(
                        title=result_data.get('title', f"Document from {result_data['href']}"),
                        url=result_data['href'],
                        snippet=result_data.get('body', ''),
                        search_engine=self.name
                    )
                    results.append(result)
            
            await self._rate_limit()
            logger.info(f"DuckDuckGo search completed: {len(results)} results")
            
        except Exception as e:
            logger.error(f"DuckDuckGo search failed: {e}")
        
        return results

class MultiSearchEngine:
    """Multi-search engine coordinator"""
    
    def __init__(self):
        self.handlers = {}
        self._setup_handlers()
    
    def _setup_handlers(self):
        """Setup available search handlers"""
        if "google" in config.ENABLED_SEARCH_ENGINES:
            self.handlers["google"] = GoogleSearchHandler()
        
        if "bing" in config.ENABLED_SEARCH_ENGINES:
            self.handlers["bing"] = BingSearchHandler()
        
        if "duckduckgo" in config.ENABLED_SEARCH_ENGINES:
            self.handlers["duckduckgo"] = DuckDuckGoSearchHandler()
    
    async def search_all_engines(self, query: str, max_results_per_engine: int = 10) -> List[SearchResult]:
        """
        Search all enabled engines concurrently
        
        Args:
            query: Search query
            max_results_per_engine: Maximum results per engine
        
        Returns:
            Combined list of search results
        """
        if not self.handlers:
            logger.warning("No search engines enabled")
            return []
        
        logger.info(f"Searching {len(self.handlers)} engines for: {query}")
        
        # Create tasks for all engines
        tasks = []
        for handler in self.handlers.values():
            task = handler.search(query, max_results_per_engine)
            tasks.append(task)
        
        # Run all searches concurrently
        try:
            results_lists = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Combine results
            all_results = []
            for i, results in enumerate(results_lists):
                if isinstance(results, Exception):
                    logger.error(f"Search engine {list(self.handlers.keys())[i]} failed: {results}")
                else:
                    all_results.extend(results)
            
            # Filter and rank results
            filtered_results = self._filter_results(all_results)
            
            logger.info(f"Multi-search completed: {len(filtered_results)} total results")
            return filtered_results
            
        except Exception as e:
            logger.error(f"Multi-search failed: {e}")
            return []
    
    async def search_single_engine(self, engine_name: str, query: str, max_results: int = 10, search_pages: int = 1) -> List[SearchResult]:
        """Search using single engine with multiple pages support"""
        if engine_name not in self.handlers:
            logger.error(f"Search engine {engine_name} not available")
            return []
        
        try:
            handler = self.handlers[engine_name]
            
            # For single page search
            if search_pages == 1:
                results = await handler.search(query, max_results)
            else:
                # Multi-page search
                results = []
                results_per_page = max_results // search_pages
                
                for page in range(search_pages):
                    try:
                        # For engines that support pagination, we'll use the existing search method
                        # and let the engine handle multiple pages internally
                        page_results = await handler.search(query, results_per_page)
                        results.extend(page_results)
                        
                        # Add delay between pages to avoid rate limiting
                        if page < search_pages - 1:
                            await asyncio.sleep(1.0)
                            
                    except Exception as e:
                        logger.warning(f"Page {page + 1} search failed: {e}")
                        continue
            
            logger.info(f"{engine_name.capitalize()} search completed: {len(results)} results from {search_pages} page(s)")
            return results
        except Exception as e:
            logger.error(f"{engine_name.capitalize()} search failed: {e}")
            return []
    
    def get_available_engines(self) -> List[str]:
        """Get list of available search engines"""
        return list(self.handlers.keys())
    
    def _filter_results(self, results: List[SearchResult]) -> List[SearchResult]:
        """Filter and clean search results with improved relevance scoring"""
        if not results:
            return []
        
        # Remove duplicates based on URL
        seen_urls = set()
        unique_results = []
        for result in results:
            url = result.url
            if url and url not in seen_urls:
                seen_urls.add(url)
                unique_results.append(result)
        
        # Calculate relevance scores
        scored_results = []
        for result in unique_results:
            score = self._calculate_relevance_score(result)
            scored_results.append((score, result))
        
        # Sort by relevance score (higher is better)
        scored_results.sort(key=lambda x: x[0], reverse=True)
        
        # Return top results
        return [result for score, result in scored_results]
    
    def _calculate_relevance_score(self, result: SearchResult) -> float:
        """Calculate relevance score for a search result"""
        score = 0.0
        title = result.title.lower() if result.title else ''
        url = result.url.lower() if result.url else ''
        
        # Penalize certain domains that are often irrelevant
        spam_domains = [
            'support.google.com', 'google.com/search', 'google.com/intl',
            'baomoi.com', 'anninhthudo.vn', 'soha.vn'  # Vietnamese news sites often not relevant
        ]
        
        for domain in spam_domains:
            if domain in url:
                score -= 2.0
        
        # Boost academic and official sources
        academic_domains = [
            'wikipedia.org', 'edu', 'gov', 'org', 'research', 'academic'
        ]
        
        for domain in academic_domains:
            if domain in url:
                score += 1.0
        
        # Boost document formats
        doc_extensions = ['.pdf', '.doc', '.docx', '.ppt', '.pptx', '.txt']
        for ext in doc_extensions:
            if ext in url:
                score += 1.5
        
        # Penalize very short titles (likely spam)
        if len(title) < 10:
            score -= 1.0
        
        # Boost results with more descriptive titles
        if len(title) > 50:
            score += 0.5
        
        # Penalize results with generic titles
        generic_titles = [
            'document from', 'search results', 'web search', 'google search'
        ]
        
        for generic in generic_titles:
            if generic in title:
                score -= 1.5
        
        return score
