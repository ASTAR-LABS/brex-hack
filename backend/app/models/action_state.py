from enum import Enum
from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime

class ActionState(str, Enum):
    EXTRACTED = "extracted"
    QUEUED = "queued"
    EXECUTING = "executing"
    RESOLVED = "resolved"
    FAILED = "failed"

class Action(BaseModel):
    id: str
    type: str
    description: str
    confidence: float
    state: ActionState = ActionState.EXTRACTED
    created_at: datetime = datetime.now()
    updated_at: datetime = datetime.now()
    executed_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None
    error: Optional[str] = None
    result: Optional[Dict[str, Any]] = None
    metadata: Dict[str, Any] = {}