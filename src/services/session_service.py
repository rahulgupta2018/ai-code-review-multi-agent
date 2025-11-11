"""
Session Service Implementation

This module provides session management for the ADK multi-agent system.
It implements ADK's InMemorySessionService pattern with comprehensive
session lifecycle management, persistence, and monitoring.
"""

import asyncio
import time
import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Set
from threading import RLock
import json
import gzip
import logging

try:
    import structlog
    HAS_STRUCTLOG = True
    
    def get_structured_logger(name: str):
        return structlog.get_logger(name)
        
except ImportError:
    HAS_STRUCTLOG = False
    
    def get_structured_logger(name: str):
        return logging.getLogger(name)

try:
    from google.adk.core import InMemorySessionService as ADKInMemorySessionService
    HAS_ADK = True
except ImportError:
    # Fallback base class when ADK is not available - provides minimal interface
    class ADKInMemorySessionService:
        def __init__(self):
            pass
            
        async def create_session(self, session_id: str, data: Dict[str, Any]):
            pass
            
        async def get_session(self, session_id: str):
            return {}
            
        async def update_session(self, session_id: str, data: Dict[str, Any]):
            pass
            
        async def delete_session(self, session_id: str):
            pass
    HAS_ADK = False

from utils.config_loader import get_config
from utils.exceptions import (
    ADKCodeReviewError, SessionError, SessionConfigurationError, SessionExecutionError
)
from utils.common import generate_correlation_id
from utils.types import AgentSession, SessionStatus


class ADKSessionService(ADKInMemorySessionService):
    """
    ADK-compatible session service with enhanced functionality.
    
    Features:
    - Configuration-driven setup (no hardcoding)
    - Memory management and cleanup
    - Session validation and security
    - Performance monitoring
    - Compression and serialization
    - Thread-safe operations
    """
    
    def __init__(self, config_override: Optional[Dict[str, Any]] = None):
        """
        Initialize the ADK session service.
        
        Args:
            config_override: Optional configuration overrides
        """
        super().__init__()
        
        # Load configuration
        self._load_configuration(config_override)
        
        # Set up logging
        self.logger = get_structured_logger(self.__class__.__name__)
        
        # Initialize session storage - using Dict[str, Any] for flexibility
        self._sessions: Dict[str, Dict[str, Any]] = {}
        self._session_locks: Dict[str, RLock] = {}
        self._global_lock = RLock()
        
        # Initialize metrics
        self._metrics = {
            'total_sessions': 0,
            'active_sessions': 0,
            'completed_sessions': 0,
            'failed_sessions': 0,
            'memory_usage_mb': 0.0,
            'last_cleanup': None
        }
        
        # Start background cleanup task
        self._cleanup_task: Optional[asyncio.Task] = None
        self._start_cleanup_task()
        
        self.logger.info(
            "ADK Session Service initialized - Max sessions: %d, TTL: %ds",
            self._config.get('storage', {}).get('max_sessions', 1000),
            self._config.get('storage', {}).get('session_ttl', 7200)
        )
    
    def _load_configuration(self, config_override: Optional[Dict[str, Any]] = None) -> None:
        """Load configuration from YAML files."""
        try:
            config = get_config()
            
            # Get session service configuration
            session_config = config.get('adk', {}).get('session_service', {})
            if not session_config:
                raise SessionConfigurationError("Session service configuration not found in config/adk/session_service.yaml")
            
            # Merge with overrides
            self._config = {
                **session_config,
                **(config_override or {})
            }
            
            # Validate configuration
            self._validate_configuration()
            
        except Exception as e:
            raise SessionConfigurationError(f"Failed to load session configuration: {e}") from e
    
    def _validate_configuration(self) -> None:
        """Validate the session service configuration."""
        storage_config = self._config.get('storage', {})
        required_fields = ['max_sessions', 'session_ttl', 'cleanup_interval']
        
        missing_fields = [field for field in required_fields if field not in storage_config]
        if missing_fields:
            raise SessionConfigurationError(f"Missing required storage configuration: {missing_fields}")
        
        # Validate numeric values
        max_sessions = storage_config.get('max_sessions')
        if not isinstance(max_sessions, int) or max_sessions <= 0:
            raise SessionConfigurationError(f"Invalid max_sessions value: {max_sessions}")
        
        session_ttl = storage_config.get('session_ttl')
        if not isinstance(session_ttl, (int, float)) or session_ttl <= 0:
            raise SessionConfigurationError(f"Invalid session_ttl value: {session_ttl}")
    
    @property
    def config(self) -> Dict[str, Any]:
        """Get the session service configuration."""
        return self._config.copy()
    
    @property
    def metrics(self) -> Dict[str, Any]:
        """Get session service metrics."""
        with self._global_lock:
            # Update memory usage
            self._metrics['memory_usage_mb'] = self._calculate_memory_usage()
            self._metrics['active_sessions'] = len(self._sessions)
            return self._metrics.copy()
    
    async def create_session(
        self,
        session_id: Optional[str] = None,
        correlation_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Create a new session.
        
        Args:
            session_id: Optional session ID (will generate if not provided)
            correlation_id: Optional correlation ID for tracking
            metadata: Optional session metadata
            
        Returns:
            The session ID
        """
        if not session_id:
            session_id = str(uuid.uuid4())
        
        if not correlation_id:
            correlation_id = generate_correlation_id()
        
        self.logger.info(
            "Creating session - ID: %s, Correlation: %s",
            session_id,
            correlation_id
        )
        
        try:
            # Check session limits
            await self._check_session_limits()
            
            # Create session data as regular dict for flexibility
            session_data = {
                'session_id': session_id,
                'correlation_id': correlation_id,
                'status': SessionStatus.ACTIVE.value,  # Store as string value
                'created_at': datetime.now(),
                'updated_at': datetime.now(),
                'metadata': metadata or {}
            }
            
            # Store session with thread safety
            with self._global_lock:
                if session_id in self._sessions:
                    raise SessionError(f"Session {session_id} already exists", session_id=session_id)
                
                self._sessions[session_id] = session_data
                self._session_locks[session_id] = RLock()
                self._metrics['total_sessions'] += 1
            
            self.logger.info(
                "Session created successfully - ID: %s",
                session_id
            )
            
            return session_id
            
        except Exception as e:
            self.logger.error(
                "Session creation failed - ID: %s, Error: %s",
                session_id,
                str(e)
            )
            
            if isinstance(e, SessionError):
                raise
            else:
                raise SessionExecutionError(f"Failed to create session: {e}", session_id=session_id) from e
    
    async def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Get session data by ID.
        
        Args:
            session_id: The session ID
            
        Returns:
            Session data or None if not found
        """
        try:
            with self._global_lock:
                if session_id not in self._sessions:
                    return None
                
                # Check if session is expired
                session_data = self._sessions[session_id]
                if await self._is_session_expired(session_data):
                    await self._expire_session(session_id)
                    return None
                
                # Update access time
                session_data['updated_at'] = datetime.now()
                
                return session_data.copy()
                
        except Exception as e:
            self.logger.error(
                "Failed to get session - ID: %s, Error: %s",
                session_id,
                str(e)
            )
            raise SessionExecutionError(f"Failed to get session: {e}", session_id=session_id) from e
    
    async def update_session(
        self,
        session_id: str,
        data: Dict[str, Any],
        status: Optional[SessionStatus] = None
    ) -> bool:
        """
        Update session data.
        
        Args:
            session_id: The session ID
            data: Data to update
            status: Optional new status
            
        Returns:
            True if updated successfully, False if session not found
        """
        try:
            with self._global_lock:
                if session_id not in self._sessions:
                    return False
                
                session_lock = self._session_locks.get(session_id)
                if not session_lock:
                    return False
            
            with session_lock:
                session_data = self._sessions[session_id]
                
                # Update metadata
                session_data['metadata'].update(data)
                session_data['updated_at'] = datetime.now()
                
                # Update status if provided
                if status:
                    session_data['status'] = status
                
                self.logger.info(
                    "Session updated successfully - ID: %s",
                    session_id
                )
                
                return True
                
        except Exception as e:
            self.logger.error(
                "Failed to update session - ID: %s, Error: %s",
                session_id,
                str(e)
            )
            raise SessionExecutionError(f"Failed to update session: {e}", session_id=session_id) from e
    
    async def delete_session(self, session_id: str) -> bool:
        """
        Delete a session.
        
        Args:
            session_id: The session ID
            
        Returns:
            True if deleted successfully, False if session not found
        """
        try:
            with self._global_lock:
                if session_id not in self._sessions:
                    return False
                
                del self._sessions[session_id]
                
                if session_id in self._session_locks:
                    del self._session_locks[session_id]
                
                self._metrics['completed_sessions'] += 1
            
            self.logger.info(
                "Session deleted successfully - ID: %s",
                session_id
            )
            
            return True
            
        except Exception as e:
            self.logger.error(
                "Failed to delete session - ID: %s, Error: %s",
                session_id,
                str(e)
            )
            raise SessionExecutionError(f"Failed to delete session: {e}", session_id=session_id) from e
    
    async def list_sessions(
        self,
        status: Optional[SessionStatus] = None,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        List sessions with optional filtering.
        
        Args:
            status: Optional status filter
            limit: Optional limit on results
            
        Returns:
            List of session data
        """
        try:
            with self._global_lock:
                sessions = list(self._sessions.values())
            
            # Filter by status if specified
            if status:
                sessions = [s for s in sessions if s['status'] == status]
            
            # Sort by created_at (newest first)
            sessions.sort(key=lambda x: x['created_at'], reverse=True)
            
            # Apply limit if specified
            if limit:
                sessions = sessions[:limit]
            
            return [session.copy() for session in sessions]
            
        except Exception as e:
            self.logger.error(
                "Failed to list sessions - Error: %s",
                str(e)
            )
            raise SessionExecutionError(f"Failed to list sessions: {e}") from e
    
    async def cleanup_expired_sessions(self) -> int:
        """
        Clean up expired sessions.
        
        Returns:
            Number of sessions cleaned up
        """
        cleanup_count = 0
        
        try:
            with self._global_lock:
                session_ids = list(self._sessions.keys())
            
            for session_id in session_ids:
                try:
                    session_data = self._sessions.get(session_id)
                    if session_data and await self._is_session_expired(session_data):
                        await self._expire_session(session_id)
                        cleanup_count += 1
                        
                except Exception as e:
                    self.logger.warning(
                        "Failed to cleanup session - ID: %s, Error: %s",
                        session_id,
                        str(e)
                    )
            
            self._metrics['last_cleanup'] = time.time()
            
            if cleanup_count > 0:
                self.logger.info(
                    "Cleanup completed - Sessions removed: %d",
                    cleanup_count
                )
            
            return cleanup_count
            
        except Exception as e:
            self.logger.error(
                "Cleanup failed - Error: %s",
                str(e)
            )
            return cleanup_count
    
    async def _check_session_limits(self) -> None:
        """Check if session limits allow creating new session."""
        max_sessions = self._config.get('storage', {}).get('max_sessions', 1000)
        
        with self._global_lock:
            current_count = len(self._sessions)
        
        if current_count >= max_sessions:
            # Try cleanup first
            await self.cleanup_expired_sessions()
            
            with self._global_lock:
                current_count = len(self._sessions)
            
            if current_count >= max_sessions:
                raise SessionExecutionError(f"Session limit exceeded: {current_count}/{max_sessions}")
    
    async def _is_session_expired(self, session_data: Dict[str, Any]) -> bool:
        """Check if a session is expired."""
        session_ttl = self._config.get('storage', {}).get('session_ttl', 7200)
        updated_at = session_data['updated_at']
        
        if isinstance(updated_at, str):
            updated_at = datetime.fromisoformat(updated_at)
        
        expiry_time = updated_at + timedelta(seconds=session_ttl)
        return datetime.now() > expiry_time
    
    async def _expire_session(self, session_id: str) -> None:
        """Expire a session."""
        try:
            with self._global_lock:
                if session_id in self._sessions:
                    self._sessions[session_id]['status'] = SessionStatus.TIMEOUT
                    await self.delete_session(session_id)
                    
        except Exception as e:
            self.logger.warning(
                "Failed to expire session - ID: %s, Error: %s",
                session_id,
                str(e)
            )
    
    def _calculate_memory_usage(self) -> float:
        """Calculate approximate memory usage in MB."""
        try:
            total_size = 0
            
            for session_data in self._sessions.values():
                # Serialize to estimate size
                serialized = json.dumps(session_data, default=str)
                total_size += len(serialized.encode('utf-8'))
            
            return total_size / (1024 * 1024)  # Convert to MB
            
        except Exception:
            return 0.0
    
    def _start_cleanup_task(self) -> None:
        """Start background cleanup task."""
        if self._cleanup_task and not self._cleanup_task.done():
            return
        
        cleanup_interval = self._config.get('storage', {}).get('cleanup_interval', 300)
        
        async def cleanup_loop():
            while True:
                try:
                    await asyncio.sleep(cleanup_interval)
                    await self.cleanup_expired_sessions()
                except asyncio.CancelledError:
                    break
                except Exception as e:
                    self.logger.error(
                        "Cleanup task error - Error: %s",
                        str(e)
                    )
        
        self._cleanup_task = asyncio.create_task(cleanup_loop())
    
    async def shutdown(self) -> None:
        """Shutdown the session service."""
        try:
            if self._cleanup_task:
                self._cleanup_task.cancel()
                try:
                    await self._cleanup_task
                except asyncio.CancelledError:
                    pass
            
            # Clear all sessions
            with self._global_lock:
                session_count = len(self._sessions)
                self._sessions.clear()
                self._session_locks.clear()
            
            self.logger.info(
                "Session service shutdown completed - Sessions cleared: %d",
                session_count
            )
            
        except Exception as e:
            self.logger.error(
                "Session service shutdown failed - Error: %s",
                str(e)
            )
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform health check on session service."""
        try:
            metrics = self.metrics
            
            # Check memory usage
            memory_limit = self._config.get('memory', {}).get('total_memory_limit', 2048)
            memory_usage_mb = metrics['memory_usage_mb']
            memory_healthy = memory_usage_mb < (memory_limit * 0.8)  # 80% threshold
            
            # Check session count
            max_sessions = self._config.get('storage', {}).get('max_sessions', 1000)
            active_sessions = metrics['active_sessions']
            sessions_healthy = active_sessions < (max_sessions * 0.9)  # 90% threshold
            
            status = 'healthy' if memory_healthy and sessions_healthy else 'unhealthy'
            
            health_data = {
                'status': status,
                'memory_usage_mb': memory_usage_mb,
                'memory_limit_mb': memory_limit,
                'memory_healthy': memory_healthy,
                'active_sessions': active_sessions,
                'max_sessions': max_sessions,
                'sessions_healthy': sessions_healthy,
                'last_check': datetime.now(),
                'metrics': metrics
            }
            
            self.logger.info(
                "Health check completed - Status: %s, Memory: %.2f MB, Sessions: %d",
                status,
                memory_usage_mb,
                active_sessions
            )
            
            return health_data
            
        except Exception as e:
            self.logger.error(
                "Health check failed - Error: %s",
                str(e)
            )
            
            return {
                'status': 'unhealthy',
                'error': str(e),
                'last_check': datetime.now()
            }
