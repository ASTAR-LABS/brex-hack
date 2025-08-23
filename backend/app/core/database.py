from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy import Column, String, DateTime, JSON, Enum as SQLEnum
from app.models.action_state import ActionState
from datetime import datetime
import os

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./ultrathink.db")

engine = create_async_engine(DATABASE_URL, echo=False)
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

Base = declarative_base()

class IntegrationCredentials(Base):
    __tablename__ = "integration_credentials"
    
    id = Column(String, primary_key=True)
    session_token = Column(String, unique=True, index=True)
    github_token = Column(String, nullable=True)
    github_owner = Column(String, nullable=True)
    github_repo = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

class ActionRecord(Base):
    __tablename__ = "actions"
    
    id = Column(String, primary_key=True)
    session_token = Column(String, index=True)
    type = Column(String)
    description = Column(String)
    confidence = Column(String)
    state = Column(SQLEnum(ActionState), default=ActionState.EXTRACTED)
    created_at = Column(DateTime, default=datetime.now)
    executed_at = Column(DateTime, nullable=True)
    resolved_at = Column(DateTime, nullable=True)
    error = Column(String, nullable=True)
    result = Column(JSON, nullable=True)
    action_metadata = Column(JSON, default={})

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

async def get_db():
    async with AsyncSessionLocal() as session:
        yield session