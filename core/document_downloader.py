"""
Document downloader for various file types
"""
import asyncio
import aiohttp
import aiofiles
import logging
import os
from typing import Optional, Tuple
from urllib.parse import urlparse, unquote
from pathlib import Path
import mimetypes
from utils.config import config

logger = logging.getLogger(__name__)

class DocumentDownloader:
    """Document downloader with support for multiple file types"""
    
    def __init__(self):
        self.supported_types = config.SUPPORTED_FILE_TYPES
        self.max_file_size = config.MAX_FILE_SIZE
        self.session = None
    
    async def __aenter__(self):
        """Async context manager entry"""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30),
            headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()
    
    async def download_document(self, url: str, save_path: str) -> Tuple[bool, Optional[str], Optional[int]]:
        """
        Download document from URL
        
        Args:
            url: Document URL
            save_path: Path to save the file
        
        Returns:
            Tuple of (success, file_path, file_size)
        """
        try:
            logger.info(f"Downloading document from: {url}")
            
            # Validate URL
            if not self._is_valid_url(url):
                logger.error(f"Invalid URL: {url}")
                return False, None, None
            
            # Check if file type is supported
            file_type = self._get_file_type(url)
            if file_type not in self.supported_types:
                logger.warning(f"Unsupported file type: {file_type}")
                return False, None, None
            
            # Create directory if not exists
            os.makedirs(os.path.dirname(save_path), exist_ok=True)
            
            # Download file
            async with self.session.get(url, allow_redirects=True) as response:
                if response.status != 200:
                    logger.error(f"HTTP {response.status} for URL: {url}")
                    return False, None, None
                
                # Check content length
                content_length = response.headers.get('content-length')
                if content_length and int(content_length) > self.max_file_size:
                    logger.warning(f"File too large: {content_length} bytes")
                    return False, None, None
                
                # Download with size limit
                file_size = 0
                async with aiofiles.open(save_path, 'wb') as f:
                    async for chunk in response.content.iter_chunked(8192):
                        file_size += len(chunk)
                        if file_size > self.max_file_size:
                            logger.warning(f"File size exceeded limit during download")
                            return False, None, None
                        await f.write(chunk)
                
                logger.info(f"Downloaded {file_size} bytes to: {save_path}")
                
                # Simple file validation - just check if file exists and has content
                if file_size == 0:
                    logger.warning(f"Downloaded file is empty: {save_path}")
                    try:
                        os.remove(save_path)
                        logger.info(f"Removed empty file: {save_path}")
                    except Exception as e:
                        logger.error(f"Failed to remove empty file {save_path}: {e}")
                    return False, None, None
                
                # Check for common error pages (basic check)
                try:
                    with open(save_path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read(1000).lower()  # Read first 1000 chars
                        if any(indicator in content for indicator in ['incapsula', 'cloudflare', 'access denied', 'error 403', 'error 404']):
                            logger.warning(f"Downloaded file appears to be an error page: {save_path}")
                            try:
                                os.remove(save_path)
                                logger.info(f"Removed error page file: {save_path}")
                            except Exception as e:
                                logger.error(f"Failed to remove error page file {save_path}: {e}")
                            return False, None, None
                except Exception as e:
                    logger.warning(f"Could not validate file content: {e}")
                
                logger.info(f"File download successful: {save_path}")
                return True, save_path, file_size
                
        except asyncio.TimeoutError:
            logger.error(f"Download timeout for URL: {url}")
            return False, None, None
        except Exception as e:
            logger.error(f"Download failed for URL {url}: {e}")
            return False, None, None
    
    def _is_valid_url(self, url: str) -> bool:
        """Check if URL is valid"""
        try:
            result = urlparse(url)
            return all([result.scheme, result.netloc])
        except Exception:
            return False
    
    def _get_file_type(self, url: str) -> str:
        """Get file type from URL"""
        parsed_url = urlparse(url)
        path = unquote(parsed_url.path)
        
        # Get extension
        _, ext = os.path.splitext(path.lower())
        
        # If no extension, try to get from content type
        if not ext:
            # This would require a HEAD request, simplified for now
            return '.html'  # Default to HTML
        
        return ext
    
    def _get_content_type(self, url: str) -> Optional[str]:
        """Get content type from URL (requires HEAD request)"""
        try:
            # This would require a HEAD request
            # Simplified implementation
            return None
        except Exception:
            return None
    
    def generate_filename(self, url: str, title: str = "") -> str:
        """
        Generate filename from URL and title
        
        Args:
            url: Document URL
            title: Document title
        
        Returns:
            Generated filename
        """
        parsed_url = urlparse(url)
        path = unquote(parsed_url.path)
        
        # Try to get filename from URL path
        filename = os.path.basename(path)
        
        # If no filename in URL, use title
        if not filename or '.' not in filename:
            if title:
                # Clean title for filename
                clean_title = "".join(c for c in title if c.isalnum() or c in (' ', '-', '_')).rstrip()
                clean_title = clean_title[:50]  # Limit length
                filename = f"{clean_title}.html"
            else:
                filename = "document.html"
        
        # Ensure filename has extension
        if '.' not in filename:
            file_type = self._get_file_type(url)
            filename += file_type
        
        return filename
    
    async def download_multiple(self, urls: list, base_path: str) -> list:
        """
        Download multiple documents concurrently
        
        Args:
            urls: List of URLs to download
            base_path: Base path for saving files
        
        Returns:
            List of download results
        """
        if not urls:
            return []
        
        # Limit concurrent downloads
        semaphore = asyncio.Semaphore(config.MAX_CONCURRENT_DOWNLOADS)
        
        async def download_with_semaphore(url_info):
            async with semaphore:
                if isinstance(url_info, dict):
                    url = url_info.get('url', '')
                    title = url_info.get('title', '')
                else:
                    url = str(url_info)
                    title = ""
                
                filename = self.generate_filename(url, title)
                save_path = os.path.join(base_path, filename)
                
                success, file_path, file_size = await self.download_document(url, save_path)
                
                return {
                    'url': url,
                    'title': title,
                    'success': success,
                    'file_path': file_path,
                    'file_size': file_size
                }
        
        # Create tasks
        tasks = [download_with_semaphore(url) for url in urls]
        
        # Run downloads concurrently
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Handle exceptions
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Download task {i} failed: {result}")
                processed_results.append({
                    'url': urls[i] if i < len(urls) else '',
                    'success': False,
                    'error': str(result)
                })
            else:
                processed_results.append(result)
        
        return processed_results
