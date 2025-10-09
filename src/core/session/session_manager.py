"""
ADK + Redis Session Management Implementation
Enhanced session management with Redis backend for persistence and pub/sub
"""

import json
import asyncio
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta

import redis.asyncio as aioredis
from google.adk.core.session import InMemorySessionService, Session
from google.adk.core import types

from ..integrations.redis.client import get_redis_client


class CodeReviewSessionManager:
    """Enhanced session management with Redis backend following ADK patterns"""
    
    def __init__(self):
        self.session_service = InMemorySessionService()
        self.redis_client: Optional[aioredis.Redis] = None
        self.app_name = "ai_code_review_multi_agent"
        self.session_ttl = 3600  # 1 hour default
    
    async def initialize(self):
        """Initialize Redis connection"""
        self.redis_client = await get_redis_client()
    
    async def create_analysis_session(self, 
                                    user_id: str, 
                                    session_id: str,
                                    files: List[str], 
                                    options: Dict[str, Any] = None) -> Session:
        """Create a new analysis session with Redis persistence"""
        
        # Create ADK session
        session = await self.session_service.create_session(
            app_name=self.app_name,
            user_id=user_id,
            session_id=session_id
        )
        
        # Initialize session state
        session_state = {
            'analysis_request': {
                'files': files,
                'analysis_domains': options.get('agents', []) if options else [],
                'options': options or {},
                'user_preferences': {
                    'detail_level': 'standard',
                    'priority_focus': 'security',
                    'output_format': 'json'
                }
            },
            'analysis_progress': {
                'current_phase': 'initialization',
                'completed_agents': [],
                'failed_agents': [],
                'progress_percentage': 0
            },
            'agent_results': {},
            'session_metadata': {
                'start_time': datetime.now().isoformat(),
                'created_by': user_id,
                'session_version': '1.0'
            }
        }
        
        # Store in Redis for persistence
        if self.redis_client:
            await self.redis_client.setex(
                f"session:{session_id}",
                self.session_ttl,
                json.dumps(session_state)
            )
        
        # Store in ADK session
        await session.store_data("session_state", session_state)
        
        return session
    
    async def update_session_progress(self, 
                                    user_id: str, 
                                    session_id: str,
                                    phase: str, 
                                    agent: str, 
                                    status: str):
        """Update session progress with Redis sync"""
        
        # Get current session
        session = await self.session_service.get_session(
            app_name=self.app_name,
            user_id=user_id, 
            session_id=session_id
        )
        
        if not session:
            raise ValueError(f"Session {session_id} not found")
        
        # Update progress
        session_state = await session.get_data("session_state") or {}
        
        if 'analysis_progress' not in session_state:
            session_state['analysis_progress'] = {
                'current_phase': phase,
                'completed_agents': [],
                'failed_agents': []
            }
        
        session_state['analysis_progress']['current_phase'] = phase
        
        if status == 'completed':
            if agent not in session_state['analysis_progress']['completed_agents']:
                session_state['analysis_progress']['completed_agents'].append(agent)
        elif status == 'failed':
            if agent not in session_state['analysis_progress']['failed_agents']:
                session_state['analysis_progress']['failed_agents'].append(agent)
        
        # Calculate progress percentage
        total_agents = 9  # Based on our 9 specialized agents
        completed = len(session_state['analysis_progress']['completed_agents'])
        session_state['analysis_progress']['progress_percentage'] = (completed / total_agents) * 100
        
        # Update both ADK session and Redis
        await session.store_data("session_state", session_state)
        
        if self.redis_client:
            await self.redis_client.setex(
                f"session:{session_id}",
                self.session_ttl,
                json.dumps(session_state)
            )
            
            # Publish progress update
            await self.redis_client.publish(
                f"session:progress:{session_id}",
                json.dumps({
                    'phase': phase,
                    'agent': agent,
                    'status': status,
                    'progress': session_state['analysis_progress']['progress_percentage'],
                    'timestamp': datetime.now().isoformat()
                })
            )
    
    async def store_agent_results(self, 
                                user_id: str, 
                                session_id: str,
                                agent_name: str, 
                                results: Dict[str, Any]):
        """Store agent analysis results"""
        
        session = await self.session_service.get_session(
            app_name=self.app_name,
            user_id=user_id,
            session_id=session_id
        )
        
        if not session:
            raise ValueError(f"Session {session_id} not found")
        
        session_state = await session.get_data("session_state") or {}
        
        if 'agent_results' not in session_state:
            session_state['agent_results'] = {}
        
        session_state['agent_results'][agent_name] = results
        
        # Update both stores
        await session.store_data("session_state", session_state)
        
        if self.redis_client:
            await self.redis_client.setex(
                f"session:{session_id}",
                self.session_ttl,
                json.dumps(session_state)
            )
    
    async def get_session_state(self, user_id: str, session_id: str) -> Optional[Dict[str, Any]]:
        """Get complete session state"""
        
        # Try Redis first for persistence
        if self.redis_client:
            redis_data = await self.redis_client.get(f"session:{session_id}")
            if redis_data:
                return json.loads(redis_data)
        
        # Fallback to ADK session
        session = await self.session_service.get_session(
            app_name=self.app_name,
            user_id=user_id,
            session_id=session_id
        )
        
        if session:
            return await session.get_data("session_state")
        
        return None
    
    async def cleanup_expired_sessions(self):
        """Cleanup expired sessions (background task)"""
        
        if not self.redis_client:
            return
        
        # Redis handles TTL automatically, but we can cleanup ADK sessions
        # This would be run as a background task
        pass
