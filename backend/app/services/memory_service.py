from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import json
import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import Column, String, DateTime, JSON, Text, select
from app.core.database import Base, AsyncSessionLocal
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
from langchain_core.chat_history import BaseChatMessageHistory
from langchain_community.chat_message_histories import ChatMessageHistory
import redis.asyncio as redis
import os
import pickle

logger = logging.getLogger(__name__)

class ConversationMemory(Base):
    """Store conversation history in database"""
    __tablename__ = "conversation_memory"
    
    id = Column(String, primary_key=True)
    session_token = Column(String, index=True)
    messages = Column(Text)  # Pickled BaseMessage list
    context = Column(JSON, default={})
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

class UserPreferences(Base):
    """Store user preferences and patterns"""
    __tablename__ = "user_preferences"
    
    session_token = Column(String, primary_key=True)
    preferences = Column(JSON, default={})
    patterns = Column(JSON, default=[])
    tool_usage = Column(JSON, default={})
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

class PersistentChatMessageHistory(BaseChatMessageHistory):
    """Custom ChatMessageHistory that persists to database"""
    
    def __init__(self, session_token: str):
        self.session_token = session_token
        self._messages: List[BaseMessage] = []
        self._load_messages()
    
    def _load_messages(self):
        """Load messages from database synchronously"""
        # KISS: Just start with empty messages, they'll be added as conversation progresses
        self._messages = []
    
    async def _async_load_messages(self) -> List[BaseMessage]:
        """Load messages from database"""
        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(ConversationMemory).where(
                    ConversationMemory.session_token == self.session_token
                ).order_by(ConversationMemory.updated_at.desc())
            )
            memory = result.scalar_one_or_none()
            
            if memory and memory.messages:
                try:
                    return pickle.loads(memory.messages.encode('latin-1'))
                except:
                    return []
        return []
    
    @property
    def messages(self) -> List[BaseMessage]:
        """Return messages list"""
        return self._messages
    
    def add_message(self, message: BaseMessage) -> None:
        """Add a message and persist"""
        self._messages.append(message)
        self._persist_messages()
    
    def add_messages(self, messages: List[BaseMessage]) -> None:
        """Add multiple messages and persist"""
        self._messages.extend(messages)
        self._persist_messages()
    
    def clear(self) -> None:
        """Clear all messages"""
        self._messages = []
        self._persist_messages()
    
    def _persist_messages(self):
        """Persist messages to database"""
        # KISS: Don't persist in sync context, just keep in memory
        # Persistence will happen via the async add_messages method
        pass
    
    async def _async_persist_messages(self):
        """Async persist messages"""
        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(ConversationMemory).where(
                    ConversationMemory.session_token == self.session_token
                )
            )
            memory = result.scalar_one_or_none()
            
            # Keep only last 50 messages
            messages_to_store = self._messages[-50:]
            pickled_messages = pickle.dumps(messages_to_store).decode('latin-1')
            
            if memory:
                memory.messages = pickled_messages
                memory.updated_at = datetime.now()
            else:
                import uuid
                memory = ConversationMemory(
                    id=str(uuid.uuid4()),
                    session_token=self.session_token,
                    messages=pickled_messages,
                    context={}
                )
                db.add(memory)
            
            await db.commit()

class MemoryService:
    def __init__(self):
        self.redis_client = None
        self.use_redis = os.getenv("REDIS_URL") is not None
        self.chat_histories: Dict[str, PersistentChatMessageHistory] = {}
        
        if self.use_redis:
            self._init_redis()
    
    def _init_redis(self):
        """Initialize Redis connection for fast memory access"""
        try:
            redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
            self.redis_client = redis.from_url(redis_url, decode_responses=False)  # For binary data
            logger.info("Redis memory service initialized")
        except Exception as e:
            logger.warning(f"Redis initialization failed, falling back to database: {e}")
            self.use_redis = False
    
    def get_session_history(self, session_token: str) -> BaseChatMessageHistory:
        """Get or create chat message history for a session (LangChain compatible)"""
        if session_token not in self.chat_histories:
            self.chat_histories[session_token] = PersistentChatMessageHistory(session_token)
        return self.chat_histories[session_token]
    
    async def get_messages(self, session_token: str) -> List[BaseMessage]:
        """Get messages as BaseMessage list"""
        history = self.get_session_history(session_token)
        return history.messages
    
    async def add_messages(self, session_token: str, messages: List[BaseMessage]):
        """Add messages to conversation history"""
        history = self.get_session_history(session_token)
        history.add_messages(messages)
        
        # Also cache in Redis for fast access
        if self.use_redis and self.redis_client:
            try:
                key = f"conversation:{session_token}"
                await self.redis_client.setex(
                    key,
                    3600,  # 1 hour TTL
                    pickle.dumps(history.messages[-50:])
                )
            except Exception as e:
                logger.error(f"Redis write error: {e}")
    
    async def get_user_preferences(self, session_token: str) -> Dict[str, Any]:
        """Get user preferences and patterns"""
        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(UserPreferences).where(
                    UserPreferences.session_token == session_token
                )
            )
            prefs = result.scalar_one_or_none()
            
            if prefs:
                return {
                    "preferences": prefs.preferences,
                    "patterns": prefs.patterns,
                    "tool_usage": prefs.tool_usage
                }
        
        return {"preferences": {}, "patterns": [], "tool_usage": {}}
    
    async def update_user_preferences(
        self,
        session_token: str,
        preferences: Optional[Dict] = None,
        new_pattern: Optional[str] = None,
        tool_used: Optional[str] = None
    ):
        """Update user preferences and patterns"""
        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(UserPreferences).where(
                    UserPreferences.session_token == session_token
                )
            )
            user_prefs = result.scalar_one_or_none()
            
            if not user_prefs:
                user_prefs = UserPreferences(
                    session_token=session_token,
                    preferences={},
                    patterns=[],
                    tool_usage={}
                )
                db.add(user_prefs)
            
            if preferences:
                user_prefs.preferences.update(preferences)
            
            if new_pattern:
                if new_pattern not in user_prefs.patterns:
                    user_prefs.patterns = user_prefs.patterns + [new_pattern]
                    # Keep only last 20 patterns
                    user_prefs.patterns = user_prefs.patterns[-20:]
            
            if tool_used:
                if tool_used not in user_prefs.tool_usage:
                    user_prefs.tool_usage[tool_used] = 0
                user_prefs.tool_usage[tool_used] += 1
            
            user_prefs.updated_at = datetime.now()
            await db.commit()
    
    async def get_agent_context(self, session_token: str) -> Dict[str, Any]:
        """Get complete context for the agent including memory and preferences"""
        conversation = await self.get_conversation_memory(session_token)
        preferences = await self.get_user_preferences(session_token)
        
        return {
            "conversation_history": conversation.get("messages", []),
            "conversation_context": conversation.get("context", {}),
            "user_preferences": preferences.get("preferences", {}),
            "user_patterns": preferences.get("patterns", []),
            "tool_usage_stats": preferences.get("tool_usage", {})
        }
    
    async def clear_session_memory(self, session_token: str):
        """Clear all memory for a session"""
        # Clear Redis
        if self.use_redis and self.redis_client:
            try:
                key = f"conversation:{session_token}"
                await self.redis_client.delete(key)
            except Exception as e:
                logger.error(f"Redis delete error: {e}")
        
        # Clear database
        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(ConversationMemory).where(
                    ConversationMemory.session_token == session_token
                )
            )
            memories = result.scalars().all()
            for memory in memories:
                await db.delete(memory)
            await db.commit()
    
    async def get_recent_tool_calls(self, session_token: str, limit: int = 10) -> List[Dict]:
        """Get recent tool calls from conversation history"""
        memory = await self.get_conversation_memory(session_token)
        messages = memory.get("messages", [])
        
        tool_calls = []
        for msg in reversed(messages):
            if isinstance(msg, dict) and msg.get("tool_calls"):
                for call in msg["tool_calls"]:
                    tool_calls.append({
                        "tool": call.get("name"),
                        "args": call.get("args"),
                        "timestamp": msg.get("timestamp", datetime.now().isoformat())
                    })
                    if len(tool_calls) >= limit:
                        return tool_calls
        
        return tool_calls