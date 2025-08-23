import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import asyncio
import logging

logger = logging.getLogger(__name__)

class Session:
    def __init__(self, session_id: str, websocket: Any):
        self.session_id = session_id
        self.websocket = websocket
        self.connected_at = datetime.now()
        self.last_activity = datetime.now()
        self.full_transcript: List[str] = []
        self.current_buffer = ""
        self.audio_buffer = bytearray()
        self.metadata: Dict[str, Any] = {}
        self.is_active = True
        
    def update_activity(self):
        self.last_activity = datetime.now()
    
    def add_to_transcript(self, text: str, is_final: bool = False):
        if is_final and text.strip():
            self.full_transcript.append(text.strip())
            self.current_buffer = ""
        else:
            self.current_buffer = text
    
    def get_full_text(self) -> str:
        return " ".join(self.full_transcript) + (" " + self.current_buffer if self.current_buffer else "")
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "session_id": self.session_id,
            "connected_at": self.connected_at.isoformat(),
            "last_activity": self.last_activity.isoformat(),
            "full_transcript": self.full_transcript,
            "current_buffer": self.current_buffer,
            "metadata": self.metadata,
            "is_active": self.is_active
        }

class SessionManager:
    def __init__(self, session_timeout_minutes: int = 30):
        self.sessions: Dict[str, Session] = {}
        self.session_timeout = timedelta(minutes=session_timeout_minutes)
        self._cleanup_task: Optional[asyncio.Task] = None
        
    async def start(self):
        if not self._cleanup_task:
            self._cleanup_task = asyncio.create_task(self._cleanup_inactive_sessions())
    
    async def stop(self):
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
    
    def create_session(self, websocket: Any, metadata: Optional[Dict[str, Any]] = None) -> Session:
        session_id = str(uuid.uuid4())
        session = Session(session_id, websocket)
        if metadata:
            session.metadata = metadata
        self.sessions[session_id] = session
        logger.info(f"Created new session: {session_id}")
        return session
    
    def get_session(self, session_id: str) -> Optional[Session]:
        session = self.sessions.get(session_id)
        if session:
            session.update_activity()
        return session
    
    def get_session_by_websocket(self, websocket: Any) -> Optional[Session]:
        for session in self.sessions.values():
            if session.websocket == websocket:
                session.update_activity()
                return session
        return None
    
    def remove_session(self, session_id: str) -> bool:
        if session_id in self.sessions:
            session = self.sessions[session_id]
            session.is_active = False
            del self.sessions[session_id]
            logger.info(f"Removed session: {session_id}")
            return True
        return False
    
    def remove_session_by_websocket(self, websocket: Any) -> bool:
        for session_id, session in list(self.sessions.items()):
            if session.websocket == websocket:
                return self.remove_session(session_id)
        return False
    
    async def _cleanup_inactive_sessions(self):
        while True:
            try:
                await asyncio.sleep(60)
                now = datetime.now()
                inactive_sessions = []
                
                for session_id, session in self.sessions.items():
                    if now - session.last_activity > self.session_timeout:
                        inactive_sessions.append(session_id)
                
                for session_id in inactive_sessions:
                    session = self.sessions.get(session_id)
                    if session and session.websocket:
                        try:
                            await session.websocket.close(code=1000, reason="Session timeout")
                        except:
                            pass
                    self.remove_session(session_id)
                    logger.info(f"Cleaned up inactive session: {session_id}")
                    
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in session cleanup: {e}")
    
    def get_active_sessions_count(self) -> int:
        return len(self.sessions)
    
    def get_all_sessions(self) -> List[Dict[str, Any]]:
        return [session.to_dict() for session in self.sessions.values()]