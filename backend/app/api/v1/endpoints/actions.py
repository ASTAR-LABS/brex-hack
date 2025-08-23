from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from app.services.action_extraction_service import ActionExtractionService
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

class TextInput(BaseModel):
    text: str

class ActionResponse(BaseModel):
    type: str
    description: str
    confidence: float

class ExtractActionsResponse(BaseModel):
    actions: List[ActionResponse]
    error: Optional[str] = None

action_service = ActionExtractionService()

@router.post("/extract", response_model=ExtractActionsResponse)
async def extract_actions(input_data: TextInput):
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
        
        return ExtractActionsResponse(
            actions=result.get("actions", []),
            error=None
        )
        
    except Exception as e:
        logger.error(f"Endpoint error: {e}")
        raise HTTPException(status_code=500, detail=str(e))