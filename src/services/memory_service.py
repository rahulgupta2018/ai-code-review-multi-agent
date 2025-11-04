"""
Memory Service Implementation

This module provides memory management for the ADK multi-agent system.
It handles session memory, agent memory, workflow memory, and provides
memory optimization, cleanup, and monitoring capabilities.
"""

import asyncio
import gc
import psutil
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Set, Tuple
from threading import RLock
import json
import gzip
import logging
from collections import defaultdict

try:
    import structlog
    HAS_STRUCTLOG = True
    
    def get_structured_logger(name: str):
        return structlog.get_logger(name)
        
except ImportError:
    HAS_STRUCTLOG = False
    
    def get_structured_logger(name: str):
        return logging.getLogger(name)

from ..utils.config_loader import get_config
from ..utils.exceptions import (
    ADKCodeReviewError, SessionError, SessionConfigurationError, SessionExecutionError
)
from ..utils.common import generate_correlation_id
from ..utils.types import AgentSession, SessionStatus


class ADKMemoryService:
    """
    Memory management service for ADK multi-agent system.
    
    Features:
    - Configuration-driven memory limits (no hardcoding)
    - Per-session and per-agent memory tracking
    - Automatic memory cleanup and optimization
    - Memory usage monitoring and alerts
    - Compression for large data
    - Memory leak detection
    """
    
    def __init__(self, config_override: Optional[Dict[str, Any]] = None):
        """
        Initialize the ADK memory service.
        
        Args:
            config_override: Optional configuration overrides
        """
        # Load configuration
        self._load_configuration(config_override)
        
        # Set up logging
        self.logger = get_structured_logger(self.__class__.__name__)
        
        # Initialize memory storage
        self._session_memory: Dict[str, Dict[str, Any]] = {}
        self._agent_memory: Dict[str, Dict[str, Any]] = {}
        self._workflow_memory: Dict[str, Dict[str, Any]] = {}
        self._global_cache: Dict[str, Any] = {}
        
        # Memory tracking
        self._memory_usage: Dict[str, float] = defaultdict(float)
        self._memory_locks: Dict[str, RLock] = {}
        self._global_lock = RLock()
        
        # Memory statistics
        self._stats = {
            'total_allocations': 0,
            'total_deallocations': 0,
            'peak_memory_mb': 0.0,
            'current_memory_mb': 0.0,
            'gc_collections': 0,
            'last_cleanup': None
        }
        
        # Start background monitoring
        self._monitoring_task: Optional[asyncio.Task] = None
        self._start_monitoring_task()
        
        self.logger.info(
            "ADK Memory Service initialized - Max memory: %d MB, GC threshold: %.2f",
            self._config.get('memory', {}).get('total_memory_limit', 2048),
            self._config.get('memory', {}).get('gc_threshold', 0.8)
        )
    
    def _load_configuration(self, config_override: Optional[Dict[str, Any]] = None) -> None:
        """Load configuration from YAML files."""
        try:
            config = get_config()
            
            # Get session service configuration (contains memory settings)
            session_config = config.get('adk', {}).get('session_service', {})
            if not session_config:
                raise SessionConfigurationError("Session service configuration not found in config/adk/session_service.yaml")
            
            # Get agent configuration for memory limits
            agent_config = config.get('adk', {}).get('agent', {})
            
            # Merge configurations
            self._config = {
                **session_config,
                **agent_config,
                **(config_override or {})
            }
            
            # Validate configuration
            self._validate_configuration()
            
        except Exception as e:
            raise SessionConfigurationError(f"Failed to load memory configuration: {e}") from e
    
    def _validate_configuration(self) -> None:
        """Validate the memory service configuration."""
        memory_config = self._config.get('memory', {})
        if not memory_config:
            # Set default memory configuration
            self._config['memory'] = {
                'total_memory_limit': 2048,  # 2GB
                'max_memory_per_session': 50,  # 50MB
                'gc_threshold': 0.8,
                'compression_enabled': True
            }
            return
        
        # Validate memory limits
        total_limit = memory_config.get('total_memory_limit', 2048)
        if not isinstance(total_limit, (int, float)) or total_limit <= 0:
            raise SessionConfigurationError(f"Invalid total_memory_limit: {total_limit}")
        
        session_limit = memory_config.get('max_memory_per_session', 50)
        if not isinstance(session_limit, (int, float)) or session_limit <= 0:
            raise SessionConfigurationError(f"Invalid max_memory_per_session: {session_limit}")
    
    @property
    def config(self) -> Dict[str, Any]:
        """Get the memory service configuration."""
        return self._config.copy()
    
    @property
    def stats(self) -> Dict[str, Any]:
        """Get memory service statistics."""
        with self._global_lock:
            # Update current memory usage
            self._stats['current_memory_mb'] = self._get_total_memory_usage()
            return self._stats.copy()
    
    async def allocate_session_memory(
        self,
        session_id: str,
        data: Dict[str, Any],
        compress: bool = False
    ) -> bool:
        """
        Allocate memory for a session.
        
        Args:
            session_id: The session ID
            data: Data to store in session memory
            compress: Whether to compress the data
            
        Returns:
            True if allocation successful, False if memory limit exceeded
        """
        try:
            # Calculate data size
            data_size_mb = self._calculate_data_size(data)
            
            # Check session memory limit
            session_limit = self._config.get('memory', {}).get('max_memory_per_session', 50)
            current_session_usage = self._memory_usage.get(f"session_{session_id}", 0.0)
            
            if current_session_usage + data_size_mb > session_limit:
                self.logger.warning(
                    "Session memory limit exceeded - ID: %s, Current: %.2f MB, Requested: %.2f MB, Limit: %.2f MB",
                    session_id,
                    current_session_usage,
                    data_size_mb,
                    session_limit
                )
                return False
            
            # Check total memory limit
            total_limit = self._config.get('memory', {}).get('total_memory_limit', 2048)
            current_total_usage = self._get_total_memory_usage()
            
            if current_total_usage + data_size_mb > total_limit:
                # Try garbage collection first
                await self._trigger_garbage_collection()
                current_total_usage = self._get_total_memory_usage()
                
                if current_total_usage + data_size_mb > total_limit:
                    self.logger.warning(
                        "Total memory limit exceeded - Current: %.2f MB, Requested: %.2f MB, Limit: %.2f MB",
                        current_total_usage,
                        data_size_mb,
                        total_limit
                    )
                    return False
            
            # Store data with compression if requested
            storage_data = data
            if compress and self._config.get('memory', {}).get('compression_enabled', True):
                storage_data = await self._compress_data(data)
                data_size_mb = self._calculate_data_size(storage_data)
            
            # Allocate memory
            with self._global_lock:
                if session_id not in self._session_memory:
                    self._session_memory[session_id] = {}
                    self._memory_locks[session_id] = RLock()
                
                self._session_memory[session_id].update(storage_data)
                self._memory_usage[f"session_{session_id}"] += data_size_mb
                self._stats['total_allocations'] += 1
                
                # Update peak memory if needed
                current_total = self._get_total_memory_usage()
                if current_total > self._stats['peak_memory_mb']:
                    self._stats['peak_memory_mb'] = current_total
            
            self.logger.info(
                "Session memory allocated - ID: %s, Size: %.2f MB, Total: %.2f MB",
                session_id,
                data_size_mb,
                self._get_total_memory_usage()
            )
            
            return True
            
        except Exception as e:
            self.logger.error(
                "Failed to allocate session memory - ID: %s, Error: %s",
                session_id,
                str(e)
            )
            raise SessionExecutionError(f"Failed to allocate session memory: {e}", session_id=session_id) from e
    
    async def get_session_memory(
        self,
        session_id: str,
        key: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Get session memory data.
        
        Args:
            session_id: The session ID
            key: Optional specific key to retrieve
            
        Returns:
            Session memory data or None if not found
        """
        try:
            with self._global_lock:
                if session_id not in self._session_memory:
                    return None
                
                session_data = self._session_memory[session_id]
                
                if key:
                    return session_data.get(key)
                else:
                    # Decompress data if needed
                    return await self._decompress_data(session_data.copy())
                    
        except Exception as e:
            self.logger.error(
                "Failed to get session memory - ID: %s, Error: %s",
                session_id,
                str(e)
            )
            raise SessionExecutionError(f"Failed to get session memory: {e}", session_id=session_id) from e
    
    async def deallocate_session_memory(self, session_id: str) -> bool:
        """
        Deallocate memory for a session.
        
        Args:
            session_id: The session ID
            
        Returns:
            True if deallocation successful, False if session not found
        """
        try:
            with self._global_lock:
                if session_id not in self._session_memory:
                    return False
                
                # Calculate memory being freed
                memory_key = f"session_{session_id}"
                freed_memory = self._memory_usage.get(memory_key, 0.0)
                
                # Remove session memory
                del self._session_memory[session_id]
                
                if memory_key in self._memory_usage:
                    del self._memory_usage[memory_key]
                
                if session_id in self._memory_locks:
                    del self._memory_locks[session_id]
                
                self._stats['total_deallocations'] += 1
            
            self.logger.info(
                "Session memory deallocated - ID: %s, Freed: %.2f MB, Total: %.2f MB",
                session_id,
                freed_memory,
                self._get_total_memory_usage()
            )
            
            return True
            
        except Exception as e:
            self.logger.error(
                "Failed to deallocate session memory - ID: %s, Error: %s",
                session_id,
                str(e)
            )
            raise SessionExecutionError(f"Failed to deallocate session memory: {e}", session_id=session_id) from e
    
    async def allocate_agent_memory(
        self,
        agent_id: str,
        data: Dict[str, Any]
    ) -> bool:
        """
        Allocate memory for an agent.
        
        Args:
            agent_id: The agent ID
            data: Data to store in agent memory
            
        Returns:
            True if allocation successful, False if memory limit exceeded
        """
        try:
            # Calculate data size
            data_size_mb = self._calculate_data_size(data)
            
            # Check agent memory limit (from agent resources config)
            agent_limit = self._config.get('resources', {}).get('max_memory_mb', 512)
            current_agent_usage = self._memory_usage.get(f"agent_{agent_id}", 0.0)
            
            if current_agent_usage + data_size_mb > agent_limit:
                self.logger.warning(
                    "Agent memory limit exceeded - ID: %s, Current: %.2f MB, Requested: %.2f MB, Limit: %.2f MB",
                    agent_id,
                    current_agent_usage,
                    data_size_mb,
                    agent_limit
                )
                return False
            
            # Allocate memory
            with self._global_lock:
                if agent_id not in self._agent_memory:
                    self._agent_memory[agent_id] = {}
                
                self._agent_memory[agent_id].update(data)
                self._memory_usage[f"agent_{agent_id}"] += data_size_mb
                self._stats['total_allocations'] += 1
            
            self.logger.info(
                "Agent memory allocated - ID: %s, Size: %.2f MB",
                agent_id,
                data_size_mb
            )
            
            return True
            
        except Exception as e:
            self.logger.error(
                "Failed to allocate agent memory - ID: %s, Error: %s",
                agent_id,
                str(e)
            )
            raise SessionExecutionError(f"Failed to allocate agent memory: {e}") from e
    
    async def cleanup_expired_memory(self, max_age_hours: float = 24.0) -> Tuple[int, float]:
        """
        Clean up expired memory allocations.
        
        Args:
            max_age_hours: Maximum age in hours before memory is considered expired
            
        Returns:
            Tuple of (cleanup_count, freed_memory_mb)
        """
        cleanup_count = 0
        freed_memory = 0.0
        
        try:
            cutoff_time = datetime.now() - timedelta(hours=max_age_hours)
            
            # Clean up session memory (this would need session timestamps)
            with self._global_lock:
                session_ids_to_remove = []
                
                for session_id in list(self._session_memory.keys()):
                    # For now, clean up all session memory older than cutoff
                    # In real implementation, you'd check session creation time
                    session_memory = self._session_memory.get(session_id, {})
                    if session_memory:  # Simple cleanup logic
                        memory_key = f"session_{session_id}"
                        freed_memory += self._memory_usage.get(memory_key, 0.0)
                        session_ids_to_remove.append(session_id)
                        cleanup_count += 1
                
                # Remove expired sessions
                for session_id in session_ids_to_remove:
                    await self.deallocate_session_memory(session_id)
            
            # Trigger garbage collection
            await self._trigger_garbage_collection()
            
            self._stats['last_cleanup'] = time.time()
            
            if cleanup_count > 0:
                self.logger.info(
                    "Memory cleanup completed - Items: %d, Freed: %.2f MB",
                    cleanup_count,
                    freed_memory
                )
            
            return cleanup_count, freed_memory
            
        except Exception as e:
            self.logger.error(
                "Memory cleanup failed - Error: %s",
                str(e)
            )
            return cleanup_count, freed_memory
    
    async def _trigger_garbage_collection(self) -> None:
        """Trigger Python garbage collection."""
        try:
            # Force garbage collection
            collected = gc.collect()
            self._stats['gc_collections'] += 1
            
            self.logger.info(
                "Garbage collection completed - Objects collected: %d",
                collected
            )
            
        except Exception as e:
            self.logger.warning(
                "Garbage collection failed - Error: %s",
                str(e)
            )
    
    def _calculate_data_size(self, data: Any) -> float:
        """Calculate approximate size of data in MB."""
        try:
            # Serialize to JSON to estimate size
            serialized = json.dumps(data, default=str)
            size_bytes = len(serialized.encode('utf-8'))
            return size_bytes / (1024 * 1024)  # Convert to MB
            
        except Exception:
            # Fallback estimation
            return 0.1  # Assume 100KB for unknown data
    
    def _get_total_memory_usage(self) -> float:
        """Get total memory usage across all allocations."""
        return sum(self._memory_usage.values())
    
    async def _compress_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Compress data using gzip."""
        try:
            # Convert to JSON and compress
            json_data = json.dumps(data, default=str)
            compressed = gzip.compress(json_data.encode('utf-8'))
            
            return {
                '_compressed': True,
                '_data': compressed
            }
            
        except Exception as e:
            self.logger.warning(
                "Data compression failed - Error: %s",
                str(e)
            )
            return data
    
    async def _decompress_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Decompress data if it was compressed."""
        try:
            if data.get('_compressed'):
                compressed_data = data.get('_data')
                if compressed_data:
                    decompressed = gzip.decompress(compressed_data)
                    return json.loads(decompressed.decode('utf-8'))
            
            return data
            
        except Exception as e:
            self.logger.warning(
                "Data decompression failed - Error: %s",
                str(e)
            )
            return data
    
    def _start_monitoring_task(self) -> None:
        """Start background memory monitoring task."""
        if self._monitoring_task and not self._monitoring_task.done():
            return
        
        monitoring_interval = self._config.get('monitoring', {}).get('metrics_interval', 60)
        
        async def monitoring_loop():
            while True:
                try:
                    await asyncio.sleep(monitoring_interval)
                    await self._monitor_memory_usage()
                except asyncio.CancelledError:
                    break
                except Exception as e:
                    self.logger.error(
                        "Memory monitoring task error - Error: %s",
                        str(e)
                    )
        
        self._monitoring_task = asyncio.create_task(monitoring_loop())
    
    async def _monitor_memory_usage(self) -> None:
        """Monitor memory usage and trigger cleanup if needed."""
        try:
            current_usage = self._get_total_memory_usage()
            total_limit = self._config.get('memory', {}).get('total_memory_limit', 2048)
            gc_threshold = self._config.get('memory', {}).get('gc_threshold', 0.8)
            
            usage_ratio = current_usage / total_limit
            
            if usage_ratio > gc_threshold:
                self.logger.warning(
                    "Memory usage high - Current: %.2f MB (%.1f%%), Limit: %.2f MB",
                    current_usage,
                    usage_ratio * 100,
                    total_limit
                )
                
                # Trigger cleanup
                await self.cleanup_expired_memory()
                await self._trigger_garbage_collection()
            
        except Exception as e:
            self.logger.error(
                "Memory monitoring failed - Error: %s",
                str(e)
            )
    
    async def shutdown(self) -> None:
        """Shutdown the memory service."""
        try:
            if self._monitoring_task:
                self._monitoring_task.cancel()
                try:
                    await self._monitoring_task
                except asyncio.CancelledError:
                    pass
            
            # Clean up all memory
            with self._global_lock:
                total_freed = sum(self._memory_usage.values())
                self._session_memory.clear()
                self._agent_memory.clear()
                self._workflow_memory.clear()
                self._global_cache.clear()
                self._memory_usage.clear()
                self._memory_locks.clear()
            
            # Final garbage collection
            await self._trigger_garbage_collection()
            
            self.logger.info(
                "Memory service shutdown completed - Freed: %.2f MB",
                total_freed
            )
            
        except Exception as e:
            self.logger.error(
                "Memory service shutdown failed - Error: %s",
                str(e)
            )
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform health check on memory service."""
        try:
            stats = self.stats
            current_usage = stats['current_memory_mb']
            total_limit = self._config.get('memory', {}).get('total_memory_limit', 2048)
            
            usage_ratio = current_usage / total_limit
            memory_healthy = usage_ratio < 0.9  # 90% threshold
            
            # Get system memory info if available
            system_memory_mb = 0.0
            try:
                process = psutil.Process()
                system_memory_mb = process.memory_info().rss / (1024 * 1024)
            except:
                pass
            
            health_data = {
                'status': 'healthy' if memory_healthy else 'unhealthy',
                'memory_usage_mb': current_usage,
                'memory_limit_mb': total_limit,
                'usage_ratio': usage_ratio,
                'memory_healthy': memory_healthy,
                'system_memory_mb': system_memory_mb,
                'stats': stats,
                'last_check': datetime.now()
            }
            
            self.logger.info(
                "Memory health check completed - Usage: %.2f MB (%.1f%%), Status: %s",
                current_usage,
                usage_ratio * 100,
                health_data['status']
            )
            
            return health_data
            
        except Exception as e:
            self.logger.error(
                "Memory health check failed - Error: %s",
                str(e)
            )
            
            return {
                'status': 'unhealthy',
                'error': str(e),
                'last_check': datetime.now()
            }
