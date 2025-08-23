from fastapi import APIRouter, HTTPException, Depends, Header
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from app.services.action_extraction_service import ActionExtractionService
from app.services.action_executor_service import ActionExecutorService
from app.core.database import get_db, IntegrationCredentials, ActionRecord
from app.models.action_state import ActionState
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import uuid
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

class TextInput(BaseModel):
    text: str

class ActionResponse(BaseModel):
    id: Optional[str] = None
    type: str
    description: str
    confidence: float

class ExtractActionsResponse(BaseModel):
    actions: List[ActionResponse]
    error: Optional[str] = None

action_service = ActionExtractionService()
executor_service = ActionExecutorService()

@router.post("/extract", response_model=ExtractActionsResponse)
async def extract_actions(
    input_data: TextInput,
    session_token: Optional[str] = Header(None, alias="X-Session-Token"),
    db: AsyncSession = Depends(get_db)
):
    """
    Extract actionable items from text using Cerebras AI.
    
    Example input:
    {
        "text": "I need to create a PR for the new feature and schedule a meeting with the team tomorrow at 3pm"
    }
    
    Returns a list of extracted actions with types and confidence scores.
    """
    try:
        if not input_data.text:
            raise HTTPException(status_code=400, detail="Text input cannot be empty")
        
        result = await action_service.extract_actions(input_data.text)
        
        if "error" in result and result["error"]:
            logger.error(f"Action extraction error: {result['error']}")
            return ExtractActionsResponse(
                actions=[],
                error=result["error"]
            )
        
        # Store extracted actions in database
        actions = result.get("actions", [])
        stored_actions = []
        
        for action in actions:
            action_id = str(uuid.uuid4())
            action_record = ActionRecord(
                id=action_id,
                session_token=session_token or "anonymous",
                type=action["type"],
                description=action["description"],
                confidence=str(action["confidence"]),
                state=ActionState.EXTRACTED,
                action_metadata={}
            )
            db.add(action_record)
            
            # Add ID to response
            action["id"] = action_id
            stored_actions.append(action)
        
        await db.commit()
        
        return ExtractActionsResponse(
            actions=stored_actions,
            error=None
        )
        
    except Exception as e:
        logger.error(f"Endpoint error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/execute/{action_id}")
async def execute_action(
    action_id: str,
    session_token: Optional[str] = Header(None, alias="X-Session-Token"),
    db: AsyncSession = Depends(get_db)
):
    """
    Execute a specific action using stored integration credentials.
    """
    try:
        integration_config = {}
        
        if session_token:
            result = await db.execute(
                select(IntegrationCredentials).where(
                    IntegrationCredentials.session_token == session_token
                )
            )
            creds = result.scalar_one_or_none()
            
            if creds:
                integration_config = {
                    "github_token": creds.github_token,
                    "github_owner": creds.github_owner,
                    "github_repo": creds.github_repo
                }
        
        action = await executor_service.execute_action(action_id, integration_config)
        
        action_record = ActionRecord(
            id=action.id,
            session_token=session_token or "anonymous",
            type=action.type,
            description=action.description,
            confidence=str(action.confidence),
            state=action.state,
            executed_at=action.executed_at,
            resolved_at=action.resolved_at,
            error=action.error,
            result=action.result,
            action_metadata=action.metadata
        )
        db.add(action_record)
        await db.commit()
        
        return action
        
    except Exception as e:
        logger.error(f"Execution error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/status/{action_id}")
async def get_action_status(
    action_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Get the status of an action.
    """
    try:
        result = await db.execute(
            select(ActionRecord).where(ActionRecord.id == action_id)
        )
        action = result.scalar_one_or_none()
        
        if not action:
            raise HTTPException(status_code=404, detail="Action not found")
        
        return {
            "id": action.id,
            "state": action.state,
            "type": action.type,
            "description": action.description,
            "error": action.error,
            "result": action.result,
            "created_at": action.created_at,
            "executed_at": action.executed_at,
            "resolved_at": action.resolved_at
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Status check error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/integrations/connect")
async def connect_integration(
    credentials: Dict[str, Any],
    db: AsyncSession = Depends(get_db)
):
    """
    Store integration credentials and return a session token.
    """
    try:
        session_token = str(uuid.uuid4())
        
        creds = IntegrationCredentials(
            id=str(uuid.uuid4()),
            session_token=session_token,
            github_token=credentials.get("github_token"),
            github_owner=credentials.get("github_owner"),
            github_repo=credentials.get("github_repo")
        )
        
        db.add(creds)
        await db.commit()
        
        return {"session_token": session_token}
        
    except Exception as e:
        logger.error(f"Integration connection error: {e}")
        raise HTTPException(status_code=500, detail=str(e))