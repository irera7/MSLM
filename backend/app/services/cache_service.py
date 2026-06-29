"""
Caching service for prompt responses.
Reduces redundant computation by caching similar prompts.
"""

import logging
import hashlib
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from collections import OrderedDict
import threading

logger = logging.getLogger(__name__)


class CacheService:
    """
    LRU Cache for model responses.
    Caches responses based on prompt hash and generation config.
    """
    
    def __init__(self, max_size: int = 100, ttl_minutes: int = 60):
        """
        Initialize cache service.
        
        Args:
            max_size: Maximum number of cached items
            ttl_minutes: Time to live for cached items in minutes
        """
        self.max_size = max_size
        self.ttl = timedelta(minutes=ttl_minutes)
        self.cache: OrderedDict[str, Dict[str, Any]] = OrderedDict()
        self.lock = threading.Lock()
        self.logger = logging.getLogger(__name__)
        
        self.stats = {
            "hits": 0,
            "misses": 0,
            "evictions": 0
        }
    
    def _generate_key(
        self,
        model_id: int,
        prompt: str,
        config: Dict[str, Any]
    ) -> str:
        """
        Generate cache key from model, prompt, and config.
        
        Args:
            model_id: Model ID
            prompt: User prompt
            config: Generation configuration
            
        Returns:
            str: Cache key (hash)
        """
        # Create a string representation of all parameters
        key_string = f"{model_id}:{prompt}"
        
        # Add relevant config parameters
        relevant_params = ["temperature", "top_p", "top_k", "max_tokens"]
        for param in relevant_params:
            if param in config:
                key_string += f":{param}={config[param]}"
        
        # Generate hash
        return hashlib.sha256(key_string.encode()).hexdigest()
    
    def get(
        self,
        model_id: int,
        prompt: str,
        config: Dict[str, Any]
    ) -> Optional[str]:
        """
        Get cached response if available.
        
        Args:
            model_id: Model ID
            prompt: User prompt
            config: Generation configuration
            
        Returns:
            Optional[str]: Cached response or None
        """
        key = self._generate_key(model_id, prompt, config)
        
        with self.lock:
            if key in self.cache:
                entry = self.cache[key]
                
                # Check TTL
                if datetime.now() - entry["timestamp"] > self.ttl:
                    # Expired
                    del self.cache[key]
                    self.stats["misses"] += 1
                    self.logger.debug(f"Cache expired for key: {key[:8]}...")
                    return None
                
                # Move to end (LRU)
                self.cache.move_to_end(key)
                self.stats["hits"] += 1
                self.logger.debug(f"Cache hit for key: {key[:8]}...")
                return entry["response"]
            else:
                self.stats["misses"] += 1
                return None
    
    def set(
        self,
        model_id: int,
        prompt: str,
        config: Dict[str, Any],
        response: str
    ) -> None:
        """
        Cache a response.
        
        Args:
            model_id: Model ID
            prompt: User prompt
            config: Generation configuration
            response: Generated response
        """
        key = self._generate_key(model_id, prompt, config)
        
        with self.lock:
            # Check if we need to evict
            if len(self.cache) >= self.max_size and key not in self.cache:
                # Remove oldest item
                evicted_key = next(iter(self.cache))
                del self.cache[evicted_key]
                self.stats["evictions"] += 1
                self.logger.debug(f"Evicted cache entry: {evicted_key[:8]}...")
            
            # Add/update entry
            self.cache[key] = {
                "response": response,
                "timestamp": datetime.now(),
                "model_id": model_id,
                "prompt_length": len(prompt),
                "response_length": len(response)
            }
            
            self.logger.debug(f"Cached response for key: {key[:8]}...")
    
    def invalidate_model(self, model_id: int) -> int:
        """
        Invalidate all cache entries for a specific model.
        
        Args:
            model_id: Model ID
            
        Returns:
            int: Number of entries invalidated
        """
        with self.lock:
            keys_to_delete = [
                key for key, entry in self.cache.items()
                if entry["model_id"] == model_id
            ]
            
            for key in keys_to_delete:
                del self.cache[key]
            
            count = len(keys_to_delete)
            if count > 0:
                self.logger.info(f"Invalidated {count} cache entries for model {model_id}")
            
            return count
    
    def clear(self) -> None:
        """Clear all cache entries"""
        with self.lock:
            count = len(self.cache)
            self.cache.clear()
            self.logger.info(f"Cleared {count} cache entries")
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.
        
        Returns:
            Dict with cache stats
        """
        with self.lock:
            total_requests = self.stats["hits"] + self.stats["misses"]
            hit_rate = (self.stats["hits"] / total_requests * 100) if total_requests > 0 else 0
            
            return {
                "size": len(self.cache),
                "max_size": self.max_size,
                "hits": self.stats["hits"],
                "misses": self.stats["misses"],
                "evictions": self.stats["evictions"],
                "hit_rate": round(hit_rate, 2),
                "ttl_minutes": self.ttl.total_seconds() / 60
            }
    
    def cleanup_expired(self) -> int:
        """
        Remove expired entries.
        
        Returns:
            int: Number of entries removed
        """
        with self.lock:
            now = datetime.now()
            keys_to_delete = [
                key for key, entry in self.cache.items()
                if now - entry["timestamp"] > self.ttl
            ]
            
            for key in keys_to_delete:
                del self.cache[key]
            
            count = len(keys_to_delete)
            if count > 0:
                self.logger.info(f"Cleaned up {count} expired cache entries")
            
            return count


# Singleton instance
cache_service = CacheService()

