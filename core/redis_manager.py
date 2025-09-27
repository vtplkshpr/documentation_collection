"""
Redis manager for deduplication and caching
"""
import redis
import json
import logging
import hashlib
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class RedisManager:
    """Redis manager for deduplication and temporary data storage"""
    
    def __init__(self, host='localhost', port=6379, db=0, password=None):
        """
        Initialize Redis connection
        
        Args:
            host: Redis host
            port: Redis port
            db: Redis database number
            password: Redis password
        """
        try:
            self.redis_client = redis.Redis(
                host=host,
                port=port,
                db=db,
                password=password,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5
            )
            # Test connection
            self.redis_client.ping()
            logger.info("Redis connection established successfully")
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            self.redis_client = None
    
    def is_available(self) -> bool:
        """Check if Redis is available"""
        if not self.redis_client:
            return False
        try:
            self.redis_client.ping()
            return True
        except Exception:
            return False
    
    def _generate_url_key(self, url: str) -> str:
        """Generate Redis key for URL"""
        # Normalize URL for consistent key generation
        normalized_url = url.lower().strip()
        # Remove common variations
        if normalized_url.endswith('/'):
            normalized_url = normalized_url[:-1]
        if normalized_url.startswith('https://'):
            normalized_url = normalized_url[8:]
        elif normalized_url.startswith('http://'):
            normalized_url = normalized_url[7:]
        
        # Create hash for consistent key
        url_hash = hashlib.md5(normalized_url.encode()).hexdigest()
        return f"url:{url_hash}"
    
    def check_duplicate(self, url: str, session_id: int) -> Optional[Dict[str, Any]]:
        """
        Check if URL is duplicate within session
        
        Args:
            url: URL to check
            session_id: Current session ID
            
        Returns:
            Existing result data if duplicate, None if unique
        """
        if not self.is_available():
            return None
        
        try:
            url_key = self._generate_url_key(url)
            session_key = f"session:{session_id}:{url_key}"
            
            # Check if URL exists in this session
            existing_data = self.redis_client.get(session_key)
            if existing_data:
                return json.loads(existing_data)
            
            return None
        except Exception as e:
            logger.error(f"Error checking duplicate: {e}")
            return None
    
    def mark_url_processed(self, url: str, session_id: int, result_data: Dict[str, Any], ttl: int = 3600):
        """
        Mark URL as processed in session
        
        Args:
            url: URL that was processed
            session_id: Current session ID
            result_data: Result data to store
            ttl: Time to live in seconds (default: 1 hour)
        """
        if not self.is_available():
            return
        
        try:
            url_key = self._generate_url_key(url)
            session_key = f"session:{session_id}:{url_key}"
            
            # Store result data with TTL
            self.redis_client.setex(
                session_key,
                ttl,
                json.dumps(result_data, default=str)
            )
            
            # Also store in global URL tracking (for cross-session deduplication)
            global_key = f"global:{url_key}"
            self.redis_client.setex(global_key, ttl, json.dumps({
                'url': url,
                'session_id': session_id,
                'processed_at': datetime.now().isoformat()
            }, default=str))
            
        except Exception as e:
            logger.error(f"Error marking URL as processed: {e}")
    
    def get_session_stats(self, session_id: int) -> Dict[str, Any]:
        """
        Get deduplication statistics for session
        
        Args:
            session_id: Session ID
            
        Returns:
            Statistics dictionary
        """
        if not self.is_available():
            return {'total_urls': 0, 'unique_urls': 0, 'duplicates': 0}
        
        try:
            pattern = f"session:{session_id}:*"
            keys = self.redis_client.keys(pattern)
            
            return {
                'total_urls': len(keys),
                'unique_urls': len(keys),
                'duplicates': 0  # Will be calculated during processing
            }
        except Exception as e:
            logger.error(f"Error getting session stats: {e}")
            return {'total_urls': 0, 'unique_urls': 0, 'duplicates': 0}
    
    def cleanup_session(self, session_id: int):
        """
        Clean up session data from Redis
        
        Args:
            session_id: Session ID to clean up
        """
        if not self.is_available():
            return
        
        try:
            pattern = f"session:{session_id}:*"
            keys = self.redis_client.keys(pattern)
            if keys:
                self.redis_client.delete(*keys)
                logger.info(f"Cleaned up {len(keys)} keys for session {session_id}")
        except Exception as e:
            logger.error(f"Error cleaning up session {session_id}: {e}")
    
    def get_duplicate_stats(self) -> Dict[str, Any]:
        """
        Get global duplicate statistics
        
        Returns:
            Statistics dictionary
        """
        if not self.is_available():
            return {'total_processed': 0, 'unique_urls': 0}
        
        try:
            # Count global URL keys
            global_keys = self.redis_client.keys("global:*")
            session_keys = self.redis_client.keys("session:*")
            
            return {
                'total_processed': len(global_keys),
                'active_sessions': len(set(key.split(':')[1] for key in session_keys)),
                'unique_urls': len(global_keys)
            }
        except Exception as e:
            logger.error(f"Error getting duplicate stats: {e}")
            return {'total_processed': 0, 'unique_urls': 0}
    
    def clear_all_data(self):
        """Clear all deduplication data (use with caution)"""
        if not self.is_available():
            return
        
        try:
            # Clear all session and global keys
            session_keys = self.redis_client.keys("session:*")
            global_keys = self.redis_client.keys("global:*")
            
            all_keys = session_keys + global_keys
            if all_keys:
                self.redis_client.delete(*all_keys)
                logger.info(f"Cleared {len(all_keys)} keys from Redis")
        except Exception as e:
            logger.error(f"Error clearing all data: {e}")

# Global Redis manager instance
redis_manager = None

def get_redis_manager() -> RedisManager:
    """Get global Redis manager instance"""
    global redis_manager
    if redis_manager is None:
        redis_manager = RedisManager()
    return redis_manager
