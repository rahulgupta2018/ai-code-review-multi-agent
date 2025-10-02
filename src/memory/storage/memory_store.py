"""
Memory Store

SQLite persistent and Redis transient storage for the memory system.
Provides dual-storage architecture for analysis memory and real-time coordination.
"""
import sqlite3
import json
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class MemoryType(Enum):
    """Types of memory entries."""
    FINDING = "finding"
    PATTERN = "pattern"
    EXPERIENCE = "experience"
    THRESHOLD = "threshold"
    INSIGHT = "insight"
    FEEDBACK = "feedback"


@dataclass
class MemoryEntry:
    """Represents a memory entry in the system."""
    id: str
    memory_type: MemoryType
    agent_name: str
    content: Dict[str, Any]
    context: Dict[str, Any]
    confidence: float
    created_at: str
    updated_at: str
    metadata: Dict[str, Any]


class MemoryStore:
    """Manages persistent memory storage using SQLite."""
    
    def __init__(self, db_path: str = "data/memory.db"):
        """Initialize the memory store."""
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Initialize database
        self._init_database()
        
    def _init_database(self):
        """Initialize the SQLite database schema."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS memory_entries (
                    id TEXT PRIMARY KEY,
                    memory_type TEXT NOT NULL,
                    agent_name TEXT NOT NULL,
                    content TEXT NOT NULL,
                    context TEXT NOT NULL,
                    confidence REAL NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    metadata TEXT NOT NULL
                )
            """)
            
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_memory_type 
                ON memory_entries(memory_type)
            """)
            
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_agent_name 
                ON memory_entries(agent_name)
            """)
            
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_created_at 
                ON memory_entries(created_at)
            """)
            
            conn.commit()
    
    def store_memory(self, entry: MemoryEntry) -> bool:
        """Store a memory entry."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT OR REPLACE INTO memory_entries 
                    (id, memory_type, agent_name, content, context, confidence, 
                     created_at, updated_at, metadata)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    entry.id,
                    entry.memory_type.value,
                    entry.agent_name,
                    json.dumps(entry.content),
                    json.dumps(entry.context),
                    entry.confidence,
                    entry.created_at,
                    entry.updated_at,
                    json.dumps(entry.metadata)
                ))
                conn.commit()
                
            logger.debug(f"Stored memory entry: {entry.id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to store memory entry {entry.id}: {e}")
            return False
    
    def retrieve_memory(self, memory_id: str) -> Optional[MemoryEntry]:
        """Retrieve a specific memory entry by ID."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("""
                    SELECT id, memory_type, agent_name, content, context, 
                           confidence, created_at, updated_at, metadata
                    FROM memory_entries WHERE id = ?
                """, (memory_id,))
                
                row = cursor.fetchone()
                if row:
                    return self._row_to_entry(row)
                    
        except Exception as e:
            logger.error(f"Failed to retrieve memory {memory_id}: {e}")
            
        return None
    
    def query_memory(self, 
                    agent_name: Optional[str] = None,
                    memory_type: Optional[MemoryType] = None,
                    limit: int = 100) -> List[MemoryEntry]:
        """Query memory entries with filters."""
        try:
            query = """
                SELECT id, memory_type, agent_name, content, context, 
                       confidence, created_at, updated_at, metadata
                FROM memory_entries WHERE 1=1
            """
            params = []
            
            if agent_name:
                query += " AND agent_name = ?"
                params.append(agent_name)
                
            if memory_type:
                query += " AND memory_type = ?"
                params.append(memory_type.value)
                
            query += " ORDER BY created_at DESC LIMIT ?"
            params.append(limit)
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute(query, params)
                rows = cursor.fetchall()
                
                return [self._row_to_entry(row) for row in rows]
                
        except Exception as e:
            logger.error(f"Failed to query memory: {e}")
            return []
    
    def search_memory_by_content(self, search_term: str, limit: int = 50) -> List[MemoryEntry]:
        """Search memory entries by content."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("""
                    SELECT id, memory_type, agent_name, content, context, 
                           confidence, created_at, updated_at, metadata
                    FROM memory_entries 
                    WHERE content LIKE ? OR context LIKE ?
                    ORDER BY confidence DESC, created_at DESC
                    LIMIT ?
                """, (f"%{search_term}%", f"%{search_term}%", limit))
                
                rows = cursor.fetchall()
                return [self._row_to_entry(row) for row in rows]
                
        except Exception as e:
            logger.error(f"Failed to search memory: {e}")
            return []
    
    def update_memory_confidence(self, memory_id: str, new_confidence: float) -> bool:
        """Update the confidence score of a memory entry."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("""
                    UPDATE memory_entries 
                    SET confidence = ?, updated_at = ?
                    WHERE id = ?
                """, (new_confidence, self._get_timestamp(), memory_id))
                
                return cursor.rowcount > 0
                
        except Exception as e:
            logger.error(f"Failed to update memory confidence {memory_id}: {e}")
            return False
    
    def delete_memory(self, memory_id: str) -> bool:
        """Delete a memory entry."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("DELETE FROM memory_entries WHERE id = ?", (memory_id,))
                return cursor.rowcount > 0
                
        except Exception as e:
            logger.error(f"Failed to delete memory {memory_id}: {e}")
            return False
    
    def get_memory_stats(self) -> Dict[str, Any]:
        """Get statistics about stored memory."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Total count
                total_cursor = conn.execute("SELECT COUNT(*) FROM memory_entries")
                total_count = total_cursor.fetchone()[0]
                
                # Count by type
                type_cursor = conn.execute("""
                    SELECT memory_type, COUNT(*) 
                    FROM memory_entries 
                    GROUP BY memory_type
                """)
                type_counts = dict(type_cursor.fetchall())
                
                # Count by agent
                agent_cursor = conn.execute("""
                    SELECT agent_name, COUNT(*) 
                    FROM memory_entries 
                    GROUP BY agent_name
                """)
                agent_counts = dict(agent_cursor.fetchall())
                
                return {
                    "total_entries": total_count,
                    "entries_by_type": type_counts,
                    "entries_by_agent": agent_counts
                }
                
        except Exception as e:
            logger.error(f"Failed to get memory stats: {e}")
            return {}
    
    def _row_to_entry(self, row: tuple) -> MemoryEntry:
        """Convert database row to MemoryEntry."""
        return MemoryEntry(
            id=row[0],
            memory_type=MemoryType(row[1]),
            agent_name=row[2],
            content=json.loads(row[3]),
            context=json.loads(row[4]),
            confidence=row[5],
            created_at=row[6],
            updated_at=row[7],
            metadata=json.loads(row[8])
        )
    
    def _get_timestamp(self) -> str:
        """Get current timestamp string."""
        from datetime import datetime
        return datetime.now().isoformat()


class RedisStateManager:
    """Manages real-time state using Redis."""
    
    def __init__(self, redis_url: str = "redis://localhost:6379"):
        """Initialize Redis state manager."""
        self.redis_url = redis_url
        self._redis_client = None
        
    def _get_redis_client(self):
        """Get Redis client (lazy initialization)."""
        if self._redis_client is None:
            try:
                import redis
                self._redis_client = redis.from_url(self.redis_url)
                # Test connection
                self._redis_client.ping()
                logger.info("Connected to Redis")
            except Exception as e:
                logger.warning(f"Redis not available: {e}")
                self._redis_client = None
        return self._redis_client
    
    def set_session_state(self, session_id: str, state: Dict[str, Any], ttl: int = 3600) -> bool:
        """Set session state with TTL."""
        client = self._get_redis_client()
        if not client:
            return False
            
        try:
            client.setex(f"session:{session_id}", ttl, json.dumps(state))
            return True
        except Exception as e:
            logger.error(f"Failed to set session state: {e}")
            return False
    
    def get_session_state(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get session state."""
        client = self._get_redis_client()
        if not client:
            return None
            
        try:
            data = client.get(f"session:{session_id}")
            return json.loads(data) if data else None
        except Exception as e:
            logger.error(f"Failed to get session state: {e}")
            return None
    
    def publish_progress(self, session_id: str, progress_data: Dict[str, Any]) -> bool:
        """Publish progress update."""
        client = self._get_redis_client()
        if not client:
            return False
            
        try:
            client.publish(f"progress:{session_id}", json.dumps(progress_data))
            return True
        except Exception as e:
            logger.error(f"Failed to publish progress: {e}")
            return False


# Global instances
memory_store = MemoryStore()
redis_state_manager = RedisStateManager()