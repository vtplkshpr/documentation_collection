"""
Baidu Search handler with Chinese translation support
"""
import asyncio
import aiohttp
import logging
import re
from typing import List, Dict, Any, Optional
from urllib.parse import quote_plus
from bs4 import BeautifulSoup
from .search_engine import SearchEngineHandler, SearchResult
from utils.config import config

logger = logging.getLogger(__name__)

class BaiduSearchHandler(SearchEngineHandler):
    """Baidu Search handler with Chinese translation support"""
    
    def __init__(self):
        super().__init__("baidu", config.get_search_delay("baidu"))
        self.base_url = "https://www.baidu.com/s"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }
        self.translation_service = None
        self._setup_translation()
    
    def _setup_translation(self):
        """Setup translation service for Chinese conversion"""
        try:
            # Try to use existing translation service
            from core.simple_translator import SimpleTranslationService
            self.translation_service = SimpleTranslationService()
            logger.info("Translation service initialized for Baidu")
        except Exception as e:
            logger.warning(f"Translation service not available: {e}")
            self.translation_service = None
    
    async def _translate_to_chinese(self, query: str) -> str:
        """Translate query to Simplified Chinese with fallback"""
        try:
            # If already in Chinese, return as is
            if self._is_chinese_text(query):
                logger.info("Query is already in Chinese")
                return query
            
            # Try translation service first
            if self.translation_service:
                try:
                    # Check if the service has translate_text method
                    if hasattr(self.translation_service, 'translate_text'):
                        translated = await self.translation_service.translate_text(query, 'zh-cn')
                    else:
                        # Use simple translation method
                        translated = self.translation_service._simple_translate(query, 'zh-cn')
                    
                    if translated and translated != query:
                        logger.info(f"Translated '{query}' to '{translated}'")
                        return translated
                except Exception as e:
                    logger.warning(f"Translation service failed: {e}")
            
            # Fallback: simple keyword mapping for common technical terms
            simple_translations = {
                'machine learning': '机器学习',
                'artificial intelligence': '人工智能',
                'deep learning': '深度学习',
                'neural network': '神经网络',
                'computer vision': '计算机视觉',
                'natural language processing': '自然语言处理',
                'data science': '数据科学',
                'big data': '大数据',
                'algorithm': '算法',
                'programming': '编程',
                'software': '软件',
                'hardware': '硬件',
                'database': '数据库',
                'documentation': '文档',
                'tutorial': '教程',
                'guide': '指南',
                'manual': '手册',
                'specification': '规范',
                'technical': '技术',
                'research': '研究',
                'paper': '论文',
                'article': '文章'
            }
            
            # Check for simple translations
            query_lower = query.lower()
            for eng, chn in simple_translations.items():
                if eng in query_lower:
                    translated = query_lower.replace(eng, chn)
                    logger.info(f"Used simple translation: '{query}' -> '{translated}'")
                    return translated
            
            logger.warning("Translation not available, using original query")
            return query
                
        except Exception as e:
            logger.error(f"Translation failed: {e}")
            return query
    
    async def search(self, query: str, max_results: int = 10) -> List[SearchResult]:
        """Search using Baidu with Chinese translation"""
        results = []
        try:
            logger.info(f"Searching Baidu for: {query}")
            
            # Translate query to Chinese if needed
            translated_query = await self._translate_to_chinese(query)
            logger.info(f"Translated query: {translated_query}")
            
            # Encode query for Chinese characters
            encoded_query = quote_plus(translated_query)
            search_url = f"{self.base_url}?wd={encoded_query}"
            
            async with aiohttp.ClientSession(headers=self.headers) as session:
                try:
                    async with session.get(search_url, timeout=aiohttp.ClientTimeout(total=30)) as response:
                        if response.status == 200:
                            html = await response.text()
                            results = self._parse_search_results(html, max_results, original_query=query)
                        else:
                            logger.warning(f"Baidu returned status {response.status}")
                            
                except asyncio.TimeoutError:
                    logger.error("Baidu search timeout")
                except Exception as e:
                    logger.error(f"Baidu search request failed: {e}")
            
            await self._rate_limit()
            logger.info(f"Baidu search completed: {len(results)} results")
            
        except Exception as e:
            logger.error(f"Baidu search failed: {e}")
        
        return results
    
    
    def _is_chinese_text(self, text: str) -> bool:
        """Check if text contains Chinese characters"""
        chinese_chars = 0
        total_chars = len(text)
        
        for char in text:
            # Check for Chinese character ranges
            if '\u4e00' <= char <= '\u9fff':  # CJK Unified Ideographs
                chinese_chars += 1
            elif '\u3400' <= char <= '\u4dbf':  # CJK Extension A
                chinese_chars += 1
            elif '\u20000' <= char <= '\u2a6df':  # CJK Extension B
                chinese_chars += 1
        
        # Consider text Chinese if more than 30% are Chinese characters
        return (chinese_chars / total_chars) > 0.3 if total_chars > 0 else False
    
    def _parse_search_results(self, html: str, max_results: int, original_query: str = "") -> List[SearchResult]:
        """Parse Baidu search results from HTML"""
        results = []
        try:
            # Clean HTML - remove excessive whitespace and comments
            html = html.replace('\n', ' ').replace('\r', ' ').replace('\t', ' ')
            while '  ' in html:
                html = html.replace('  ', ' ')
            
            soup = BeautifulSoup(html, 'html.parser')
            
            # Baidu uses multiple possible selectors - try them in order of preference
            result_selectors = [
                # Modern Baidu selectors (2024+)
                'div[class*="result"]',
                'div.c-container',
                'div[class*="c-container"]',
                'div[class*="result-item"]',
                'div[class*="search-result"]',
                'div[class*="c-result"]',
                'div[class*="content"]',
                # Legacy selectors
                'div.result',
                'li[class*="result"]',
                'div[class*="web"]',
                'div[class*="item"]',
                # Generic fallbacks
                'div[class*="link"]',
                'div[class*="title"]'
            ]
            
            found_results = []
            for selector in result_selectors:
                elements = soup.select(selector)
                if elements:
                    # Filter out elements that don't contain links and have meaningful content
                    valid_elements = []
                    for elem in elements:
                        link = elem.find('a', href=True)
                        if link and link.get('href') and len(link.get_text(strip=True)) > 3:
                            # Additional validation - check if it looks like a search result
                            href = link.get('href', '')
                            if (not href.startswith('javascript:') and 
                                not href.startswith('#') and
                                'baidu.com' not in href.lower()):
                                valid_elements.append(elem)
                    
                    if valid_elements:
                        found_results = valid_elements
                        logger.info(f"Found {len(valid_elements)} results using selector: {selector}")
                        break
            
            # Parse structured results
            for element in found_results[:max_results]:
                try:
                    result = self._parse_single_result(element, original_query)
                    if result:
                        results.append(result)
                        
                except Exception as e:
                    logger.debug(f"Error parsing result element: {e}")
                    continue
            
            # If no structured results found, try aggressive parsing
            if not results:
                logger.warning("No structured results found, trying aggressive parsing")
                results = self._aggressive_parse(html, max_results, original_query)
            
            # If still no results, try finding any links that look like search results
            if not results:
                logger.warning("No results found with standard parsing, trying link extraction")
                results = self._extract_links_from_page(html, max_results, original_query)
            
        except Exception as e:
            logger.error(f"Error parsing Baidu results: {e}")
        
        return results[:max_results]
    
    def _parse_single_result(self, element, original_query: str = "") -> Optional[SearchResult]:
        """Parse a single search result element"""
        try:
            # Find title link
            title_link = element.find('a', href=True)
            if not title_link:
                return None
            
            title = title_link.get_text(strip=True)
            url = title_link.get('href', '')
            
            # Clean up URL (Baidu sometimes uses redirect URLs)
            url = self._clean_baidu_url(url)
            
            # Extract snippet with improved selectors
            snippet = ""
            snippet_selectors = [
                # Modern Baidu snippet selectors
                'span[class*="content"]',
                'div[class*="content"]',
                'span[class*="abstract"]',
                'div[class*="abstract"]',
                'span[class*="summary"]',
                'div[class*="summary"]',
                'div[class*="desc"]',
                'span[class*="desc"]',
                # Legacy selectors
                'div.c-span-last span.content-right_8Zs40',
                'div.c-span-last',
                'div[class*="c-span"]'
            ]
            
            for selector in snippet_selectors:
                snippet_elem = element.select_one(selector)
                if snippet_elem:
                    snippet = snippet_elem.get_text(strip=True)
                    if len(snippet) > 10:  # Only use if it has meaningful content
                        break
            
            # If no snippet found, try to get text from the element itself
            if not snippet:
                all_text = element.get_text(strip=True)
                if len(all_text) > len(title) + 10:  # More than just title
                    snippet = all_text[:200] + "..." if len(all_text) > 200 else all_text
            
            # Validate result
            if not self._is_valid_result_url(url) or not title:
                return None
            
            return SearchResult(
                title=title,
                url=url,
                snippet=snippet,
                search_engine=self.name
            )
            
        except Exception as e:
            logger.debug(f"Error parsing single result: {e}")
            return None
    
    def _clean_baidu_url(self, url: str) -> str:
        """Clean Baidu redirect URLs"""
        try:
            if not url:
                return url
            
            # Baidu often uses redirect URLs like: /link?url=...
            if '/link?url=' in url:
                # Extract the actual URL from Baidu redirect
                import urllib.parse
                parsed = urllib.parse.parse_qs(urllib.parse.urlparse(url).query)
                if 'url' in parsed:
                    extracted_url = parsed['url'][0]
                    # Decode URL if it's encoded
                    if '%' in extracted_url:
                        extracted_url = urllib.parse.unquote(extracted_url)
                    return extracted_url
            
            # Handle other Baidu redirect patterns
            if 'baidu.com/link?url=' in url:
                import urllib.parse
                parsed = urllib.parse.parse_qs(urllib.parse.urlparse(url).query)
                if 'url' in parsed:
                    extracted_url = parsed['url'][0]
                    if '%' in extracted_url:
                        extracted_url = urllib.parse.unquote(extracted_url)
                    return extracted_url
            
            # If it's a relative URL, make it absolute (but only for Baidu internal links)
            if url.startswith('/') and 'baidu.com' in url:
                return f"https://www.baidu.com{url}"
            
            # Remove Baidu tracking parameters
            if 'baidu.com' in url:
                import urllib.parse
                parsed = urllib.parse.urlparse(url)
                if parsed.query:
                    # Remove common tracking parameters
                    query_params = urllib.parse.parse_qs(parsed.query)
                    filtered_params = {}
                    for key, values in query_params.items():
                        if key not in ['tn', 'wd', 'ie', 'f', 'rsp', 'src']:
                            filtered_params[key] = values
                    
                    if filtered_params:
                        new_query = urllib.parse.urlencode(filtered_params, doseq=True)
                        new_url = urllib.parse.urlunparse((parsed.scheme, parsed.netloc, parsed.path, 
                                                          parsed.params, new_query, parsed.fragment))
                        return new_url
            
            return url
            
        except Exception as e:
            logger.debug(f"Error cleaning Baidu URL: {e}")
            return url
    
    def _aggressive_parse(self, html: str, max_results: int, original_query: str = "") -> List[SearchResult]:
        """Aggressive parsing when standard methods fail"""
        results = []
        try:
            soup = BeautifulSoup(html, 'html.parser')
            
            # First, try to find all links with meaningful text
            all_links = soup.find_all('a', href=True)
            
            for link in all_links[:max_results * 5]:  # Check more links than needed
                href = link.get('href', '')
                title = link.get_text(strip=True)
                
                # Skip if no meaningful title
                if len(title) < 5:
                    continue
                
                # Clean URL
                href = self._clean_baidu_url(href)
                
                # Validate URL and title
                if (self._is_valid_result_url(href) and 
                    title and 
                    not any(domain in href.lower() for domain in ['baidu.com', 'baidu.cn', 'bdstatic.com'])):
                    
                    # Try to find snippet from parent element
                    snippet = ""
                    parent = link.parent
                    if parent:
                        parent_text = parent.get_text(strip=True)
                        if len(parent_text) > len(title) + 10:
                            snippet = parent_text[:200] + "..." if len(parent_text) > 200 else parent_text
                    
                    result = SearchResult(
                        title=title,
                        url=href,
                        snippet=snippet,
                        search_engine=self.name
                    )
                    results.append(result)
                    
                    if len(results) >= max_results:
                        break
            
            # If still no results, use regex fallback
            if not results:
                logger.info("Trying regex-based URL extraction")
                url_pattern = r'href="(https?://[^"]+)"'
                urls = re.findall(url_pattern, html)
                
                for url in urls[:max_results * 2]:
                    url = self._clean_baidu_url(url)
                    if self._is_valid_result_url(url) and not any(domain in url.lower() for domain in ['baidu.com', 'baidu.cn', 'bdstatic.com']):
                        title = self._extract_title_from_context(html, url)
                        if not title:
                            title = f"Document from {url}"
                        
                        result = SearchResult(
                            title=title,
                            url=url,
                            snippet="",
                            search_engine=self.name
                        )
                        results.append(result)
                        
                        if len(results) >= max_results:
                            break
                    
        except Exception as e:
            logger.error(f"Aggressive parsing failed: {e}")
        
        return results
    
    def _extract_links_from_page(self, html: str, max_results: int, original_query: str = "") -> List[SearchResult]:
        """Extract links from the entire page as a fallback"""
        results = []
        try:
            soup = BeautifulSoup(html, 'html.parser')
            
            # Find all links on the page
            all_links = soup.find_all('a', href=True)
            
            for link in all_links[:max_results * 3]:  # Check more links than needed
                href = link.get('href', '')
                title = link.get_text(strip=True)
                
                # Clean URL
                href = self._clean_baidu_url(href)
                
                # Validate URL and title
                if (self._is_valid_result_url(href) and 
                    title and 
                    len(title) > 3 and 
                    not any(domain in href.lower() for domain in ['baidu.com', 'baidu.cn'])):
                    
                    result = SearchResult(
                        title=title,
                        url=href,
                        snippet="",
                        search_engine=self.name
                    )
                    results.append(result)
                    
                    if len(results) >= max_results:
                        break
            
            logger.info(f"Extracted {len(results)} links from page")
            
        except Exception as e:
            logger.error(f"Link extraction failed: {e}")
        
        return results
    
    def _is_valid_result_url(self, url: str) -> bool:
        """Check if URL is a valid search result"""
        if not url or len(url) < 10:
            return False
        
        # Filter out Baidu internal URLs and common non-content sites
        internal_domains = [
            'baidu.com', 'baidu.cn',
            'google.com', 'bing.com', 'duckduckgo.com',
            'facebook.com', 'youtube.com', 'twitter.com',
            'weibo.com', 'zhihu.com', 'douban.com'
        ]
        
        for domain in internal_domains:
            if domain in url.lower():
                return False
        
        # Must be HTTP/HTTPS
        if not url.startswith(('http://', 'https://')):
            return False
        
        return True
    
    def _extract_title_from_context(self, html: str, url: str) -> str:
        """Extract title from HTML context around URL"""
        try:
            # Find the URL in the HTML
            url_index = html.find(url)
            if url_index == -1:
                return ""
            
            # Look for title in surrounding context
            context_start = max(0, url_index - 300)
            context_end = min(len(html), url_index + 300)
            context = html[context_start:context_end]
            
            # Try to find title tag or text near the URL
            title_patterns = [
                r'<title[^>]*>([^<]+)</title>',
                r'title="([^"]+)"',
                r'>([^<]{10,100})<',
            ]
            
            for pattern in title_patterns:
                matches = re.findall(pattern, context, re.IGNORECASE)
                if matches:
                    title = matches[0].strip()
                    if len(title) > 5 and len(title) < 200:
                        return title
            
        except Exception as e:
            logger.debug(f"Error extracting title from context: {e}")
        
        return ""
