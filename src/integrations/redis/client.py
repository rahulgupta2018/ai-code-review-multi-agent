"""
Redis Client Implementation for AI Code Review Multi-Agent System
Provides async Redis connection and utilities following GADK patterns
"""

import os
import json
import asyncio
from typing import Dict, Any, Optional, List
from contextlib import asynccontextmanager

import redis


class RedisClient:
    """Redis client with connection pooling for multi-agent coordination"""
    
    def __init__(self):
        self.client = None
        self._initialized = False
    
    async def initialize(self):
        """Initialize Redis connection"""
        if self._initialized:
            return
        
        # Get configuration from environment
        redis_host = os.getenv('REDIS_HOST', 'redis')
        redis_port = int(os.getenv('REDIS_PORT', '6379'))
        redis_db = int(os.getenv('REDIS_DB', '0'))
        redis_password = os.getenv('REDIS_PASSWORD', None) or None
        
        # Connection settings
        max_connections = int(os.getenv('REDIS_MAX_CONNECTIONS', '100'))
        socket_timeout = int(os.getenv('REDIS_SOCKET_TIMEOUT', '5'))
        socket_connect_timeout = int(os.getenv('REDIS_SOCKET_CONNECT_TIMEOUT', '5'))
        
        try:
            # Create Redis client using correct import pattern for redis v5.0.1
            redis_url = f"redis://{redis_host}:{redis_port}/{redis_db}"
            if redis_password:
                redis_url = f"redis://:{redis_password}@{redis_host}:{redis_port}/{redis_db}"
            
            self.client = redis.Redis.from_url(
                redis_url,
                decode_responses=True,
                socket_timeout=socket_timeout,
                socket_connect_timeout=socket_connect_timeout,
                retry_on_timeout=True,
                max_connections=max_connections
            )
            
            # Test connection
            self.client.ping()
            self._initialized = True
            print(f"✅ Redis connection established: {redis_host}:{redis_port}")
            
        except Exception as e:
            print(f"❌ Redis connection failed: {e}")
            raise
    
    def close(self):
        """Close Redis connection"""
        if self.client:
            self.client.close()
        self._initialized = False
    
    def health_check(self) -> bool:
        """Check Redis health"""
        try:
            if not self.client:
                return False
            self.client.ping()
            return True
        except Exception:
            return False
    
    # Session Management Methods
    def set_session(self, session_id: str, data: Dict[str, Any], ttl: int = 3600):
        """Store session data with TTL"""
        if not self.client:
            raise RuntimeError("Redis client not initialized")
        
        prefix = os.getenv('SESSION_REDIS_PREFIX', 'gadk:session:')
        key = f"{prefix}{session_id}"
        
        self.client.setex(key, ttl, json.dumps(data))
    
    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve session data"""
        if not self.client:
            raise RuntimeError("Redis client not initialized")
        
        prefix = os.getenv('SESSION_REDIS_PREFIX', 'gadk:session:')
        key = f"{prefix}{session_id}"
        
        data = self.client.get(key)
        return json.loads(data) if data else None
    
    def delete_session(self, session_id: str) -> bool:
        """Delete session data"""
        if not self.client:
            raise RuntimeError("Redis client not initialized")
        
        prefix = os.getenv('SESSION_REDIS_PREFIX', 'gadk:session:')
        key = f"{prefix}{session_id}"
        
        result = self.client.delete(key)
        return result > 0
    
    def extend_session_ttl(self, session_id: str, ttl: int = 3600) -> bool:
        """Extend session TTL"""
        if not self.client:
            raise RuntimeError("Redis client not initialized")
        
        prefix = os.getenv('SESSION_REDIS_PREFIX', 'gadk:session:')
        key = f"{prefix}{session_id}"
        
        result = self.client.expire(key, ttl)
        return bool(result)
    
    # Caching Methods
    def cache_set(self, key: str, value: Any, ttl: int = 300):
        """Set cached value with TTL"""
        if not self.client:
            raise RuntimeError("Redis client not initialized")
        
        cache_key = f"cache:{key}"
        if isinstance(value, (dict, list)):
            value = json.dumps(value)
        
        self.client.setex(cache_key, ttl, value)
    
    def cache_get(self, key: str) -> Optional[Any]:
        """Get cached value"""
        if not self.client:
            raise RuntimeError("Redis client not initialized")
        
        cache_key = f"cache:{key}"
        value = self.client.get(cache_key)
        
        if value:
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                return value
        return None
    
    def cache_delete(self, key: str) -> bool:
        """Delete cached value"""
        if not self.client:
            raise RuntimeError("Redis client not initialized")
        
        cache_key = f"cache:{key}"
        result = self.client.delete(cache_key)
        return result > 0
    
    # Pub/Sub Methods for Real-time Updates
    def publish(self, channel: str, message: Dict[str, Any]):
        """Publish message to channel"""
        if not self.client:
            raise RuntimeError("Redis client not initialized")
        
        self.client.publish(channel, json.dumps(message))
    
    def subscribe(self, *channels: str):
        """Subscribe to channels and return pubsub object"""
        if not self.client:
            raise RuntimeError("Redis client not initialized")
        
        pubsub = self.client.pubsub()
        pubsub.subscribe(*channels)
        return pubsub
    
    # Multi-Agent Coordination Methods
    def set_agent_status(self, agent_id: str, status: str, ttl: int = 300):
        """Set agent status for coordination"""
        if not self.client:
            raise RuntimeError("Redis client not initialized")
        
        key = f"agent:status:{agent_id}"
        self.client.setex(key, ttl, status)
    
    def get_agent_status(self, agent_id: str) -> Optional[str]:
        """Get agent status"""
        if not self.client:
            raise RuntimeError("Redis client not initialized")
        
        key = f"agent:status:{agent_id}"
        return self.client.get(key)
    
    def acquire_lock(self, lock_name: str, timeout: int = 10, ttl: int = 30) -> bool:
        """Acquire distributed lock"""
        if not self.client:
            raise RuntimeError("Redis client not initialized")
        
        lock_key = f"lock:{lock_name}"
        identifier = f"{os.getpid()}:{id(asyncio.current_task() or 'sync')}"
        
        # Try to acquire lock
        result = self.client.set(lock_key, identifier, nx=True, ex=ttl)
        return bool(result)
    
    def release_lock(self, lock_name: str) -> bool:
        """Release distributed lock"""
        if not self.client:
            raise RuntimeError("Redis client not initialized")
        
        lock_key = f"lock:{lock_name}"
        identifier = f"{os.getpid()}:{id(asyncio.current_task() or 'sync')}"
        
        # Use Lua script for atomic lock release
        lua_script = """
        if redis.call("GET", KEYS[1]) == ARGV[1] then
            return redis.call("DEL", KEYS[1])
        else
            return 0
        end
        """
        
        try:
            result = self.client.eval(lua_script, 1, lock_key, identifier)
            return result == 1
        except Exception:
            # Fallback to simple delete
            return self.client.delete(lock_key) > 0
    
    # Analysis Progress Tracking
    def set_analysis_progress(self, analysis_id: str, progress: Dict[str, Any]):
        """Set analysis progress"""
        if not self.client:
            raise RuntimeError("Redis client not initialized")
        
        key = f"analysis:progress:{analysis_id}"
        self.client.setex(key, 3600, json.dumps(progress))
    
    def get_analysis_progress(self, analysis_id: str) -> Optional[Dict[str, Any]]:
        """Get analysis progress"""
        if not self.client:
            raise RuntimeError("Redis client not initialized")
        
        key = f"analysis:progress:{analysis_id}"
        data = self.client.get(key)
        return json.loads(data) if data else None
    
    def cleanup_expired_data(self):
        """Cleanup expired data (background task)"""
        if not self.client:
            return
        
        # Find and delete expired keys
        patterns = [
            'gadk:session:*',
            'cache:*',
            'agent:status:*',
            'analysis:progress:*'
        ]
        
        for pattern in patterns:
            try:
                keys = self.client.keys(pattern)
                expired_keys = []
                
                for key in keys:
                    ttl = self.client.ttl(key)
                    if ttl == -2:  # Key doesn't exist
                        expired_keys.append(key)
                
                if expired_keys:
                    self.client.delete(*expired_keys)
            except Exception as e:
                print(f"Warning: Cleanup failed for pattern {pattern}: {e}")


# Async wrapper for Redis operations
class AsyncRedisClient:
    """Async wrapper for Redis client operations"""
    
    def __init__(self):
        self.sync_client = RedisClient()
    
    async def initialize(self):
        """Initialize Redis connection"""
        await asyncio.get_event_loop().run_in_executor(None, self.sync_client.initialize)
    
    async def close(self):
        """Close Redis connection"""
        await asyncio.get_event_loop().run_in_executor(None, self.sync_client.close)
    
    async def health_check(self) -> bool:
        """Check Redis health"""
        return await asyncio.get_event_loop().run_in_executor(None, self.sync_client.health_check)
    
    # Session Management Methods
    async def set_session(self, session_id: str, data: Dict[str, Any], ttl: int = 3600):
        """Store session data with TTL"""
        await asyncio.get_event_loop().run_in_executor(
            None, self.sync_client.set_session, session_id, data, ttl
        )
    
    async def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve session data"""
        return await asyncio.get_event_loop().run_in_executor(
            None, self.sync_client.get_session, session_id
        )
    
    async def delete_session(self, session_id: str) -> bool:
        """Delete session data"""
        return await asyncio.get_event_loop().run_in_executor(
            None, self.sync_client.delete_session, session_id
        )
    
    async def extend_session_ttl(self, session_id: str, ttl: int = 3600) -> bool:
        """Extend session TTL"""
        return await asyncio.get_event_loop().run_in_executor(
            None, self.sync_client.extend_session_ttl, session_id, ttl
        )
    
    # Caching Methods
    async def cache_set(self, key: str, value: Any, ttl: int = 300):
        """Set cached value with TTL"""
        await asyncio.get_event_loop().run_in_executor(
            None, self.sync_client.cache_set, key, value, ttl
        )
    
    async def cache_get(self, key: str) -> Optional[Any]:
        """Get cached value"""
        return await asyncio.get_event_loop().run_in_executor(
            None, self.sync_client.cache_get, key
        )
    
    async def cache_delete(self, key: str) -> bool:
        """Delete cached value"""
        return await asyncio.get_event_loop().run_in_executor(
            None, self.sync_client.cache_delete, key
        )
    
    # Pub/Sub Methods
    async def publish(self, channel: str, message: Dict[str, Any]):
        """Publish message to channel"""
        await asyncio.get_event_loop().run_in_executor(
            None, self.sync_client.publish, channel, message
        )
    
    # Agent coordination
    async def set_agent_status(self, agent_id: str, status: str, ttl: int = 300):
        """Set agent status for coordination"""
        await asyncio.get_event_loop().run_in_executor(
            None, self.sync_client.set_agent_status, agent_id, status, ttl
        )
    
    async def get_agent_status(self, agent_id: str) -> Optional[str]:
        """Get agent status"""
        return await asyncio.get_event_loop().run_in_executor(
            None, self.sync_client.get_agent_status, agent_id
        )
    
    async def acquire_lock(self, lock_name: str, timeout: int = 10, ttl: int = 30) -> bool:
        """Acquire distributed lock"""
        return await asyncio.get_event_loop().run_in_executor(
            None, self.sync_client.acquire_lock, lock_name, timeout, ttl
        )
    
    async def release_lock(self, lock_name: str) -> bool:
        """Release distributed lock"""
        return await asyncio.get_event_loop().run_in_executor(
            None, self.sync_client.release_lock, lock_name
        )
    
    # Analysis progress
    async def set_analysis_progress(self, analysis_id: str, progress: Dict[str, Any]):
        """Set analysis progress"""
        await asyncio.get_event_loop().run_in_executor(
            None, self.sync_client.set_analysis_progress, analysis_id, progress
        )
    
    async def get_analysis_progress(self, analysis_id: str) -> Optional[Dict[str, Any]]:
        """Get analysis progress"""
        return await asyncio.get_event_loop().run_in_executor(
            None, self.sync_client.get_analysis_progress, analysis_id
        )


# Global Redis client instance
_redis_client: Optional[AsyncRedisClient] = None


async def get_redis_client() -> AsyncRedisClient:
    """Get or create Redis client singleton"""
    global _redis_client
    
    if _redis_client is None:
        _redis_client = AsyncRedisClient()
        await _redis_client.initialize()
    
    return _redis_client


async def close_redis_client():
    """Close Redis client connection"""
    global _redis_client
    
    if _redis_client:
        await _redis_client.close()
        _redis_client = None


# Context manager for Redis operations
@asynccontextmanager
async def redis_session():
    """Context manager for Redis operations"""
    client = await get_redis_client()
    try:
        yield client
    finally:
        # Keep connection alive (managed by singleton)
        pass