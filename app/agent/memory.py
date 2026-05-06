# Agent Memory Management

from app.services.memory_service import MemoryService
import json
from typing import Dict, Any, List

class SessionMemory:
    """Session memory for agent conversations."""

    def __init__(self):
        self.history: List[Dict[str, str]] = []
        self.uploaded_files: Dict[str, Dict[str, Any]] = {}
        self.document_drafts: Dict[str, Dict[str, Any]] = {}
        self.pending_action: Dict[str, Any] = None
        self.last_file_path: str = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "history": self.history,
            "uploaded_files": self.uploaded_files,
            "document_drafts": self.document_drafts,
            "pending_action": self.pending_action,
            "last_file_path": self.last_file_path,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SessionMemory':
        memory = cls()
        memory.history = data.get("history", [])
        memory.uploaded_files = data.get("uploaded_files", {})
        memory.document_drafts = data.get("document_drafts", {})
        memory.pending_action = data.get("pending_action")
        memory.last_file_path = data.get("last_file_path")
        return memory

class MemoryStore:
    """Memory store with persistence."""

    def __init__(self, memory_service: MemoryService):
        self.memory_service = memory_service
        self._cache: Dict[str, SessionMemory] = {}

    def get(self, session_id: str, user_id: str) -> SessionMemory:
        """Get session memory, load from persistence if needed."""
        key = f"{session_id}_{user_id}"
        if key not in self._cache:
            data = self.memory_service.load_session_memory(session_id, user_id)
            if data:
                self._cache[key] = SessionMemory.from_dict(data)
            else:
                self._cache[key] = SessionMemory()
        return self._cache[key]

    def save(self, session_id: str, user_id: str) -> None:
        """Save session memory to persistence."""
        key = f"{session_id}_{user_id}"
        if key in self._cache:
            data = self._cache[key].to_dict()
            self.memory_service.save_session_memory(session_id, user_id, data)

    def clear_pending_action(self, session_id: str, user_id: str) -> None:
        """Clear pending action for session."""
        memory = self.get(session_id, user_id)
        memory.pending_action = None