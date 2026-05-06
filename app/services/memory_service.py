# Memory Service for persistent agent memory

import json
import sqlite3
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

class MemoryService:
    """Service for persisting agent memory to database."""

    def __init__(self):
        from app.database.db import get_connection
        self.get_connection = get_connection

    def load_session_memory(self, session_id: str, user_id: str) -> Optional[Dict[str, Any]]:
        """Load session memory from database."""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()

            cursor.execute("""
                SELECT memory_data FROM session_memory
                WHERE session_id = ? AND user_id = ?
            """, (session_id, user_id))

            row = cursor.fetchone()
            conn.close()

            if row:
                return json.loads(row[0])
            return None

        except Exception as e:
            logger.error(f"Failed to load session memory: {e}")
            return None

    def save_session_memory(self, session_id: str, user_id: str, data: Dict[str, Any]) -> None:
        """Save session memory to database."""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()

            # Insert or replace
            cursor.execute("""
                INSERT OR REPLACE INTO session_memory (session_id, user_id, memory_data, updated_at)
                VALUES (?, ?, ?, datetime('now'))
            """, (session_id, user_id, json.dumps(data)))

            conn.commit()
            conn.close()

        except Exception as e:
            logger.error(f"Failed to save session memory: {e}")

    def load_user_memory(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Load user-specific memory."""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()

            cursor.execute("""
                SELECT memory_data FROM user_memory
                WHERE user_id = ?
            """, (user_id,))

            row = cursor.fetchone()
            conn.close()

            if row:
                return json.loads(row[0])
            return None

        except Exception as e:
            logger.error(f"Failed to load user memory: {e}")
            return None

    def save_user_memory(self, user_id: str, data: Dict[str, Any]) -> None:
        """Save user-specific memory."""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()

            cursor.execute("""
                INSERT OR REPLACE INTO user_memory (user_id, memory_data, updated_at)
                VALUES (?, ?, datetime('now'))
            """, (user_id, json.dumps(data)))

            conn.commit()
            conn.close()

        except Exception as e:
            logger.error(f"Failed to save user memory: {e}")

    def delete_session_memory(self, session_id: str, user_id: str) -> None:
        """Delete session memory."""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()

            cursor.execute("""
                DELETE FROM session_memory
                WHERE session_id = ? AND user_id = ?
            """, (session_id, user_id))

            conn.commit()
            conn.close()

        except Exception as e:
            logger.error(f"Failed to delete session memory: {e}")