"""Agent API endpoints"""
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import logging

from app.agent import chat, stream_response
from app.agent.tools import get_tool_descriptions

logger = logging.getLogger(__name__)

router = APIRouter()


class ChatRequest(BaseModel):
    """Request model for chat endpoint"""
    message: str
    categories: Optional[List[str]] = None
    model: Optional[str] = "gpt-oss-120b"
    system_prompt: Optional[str] = None
    session_token: Optional[str] = None
    user_role: Optional[str] = None
    stream: Optional[bool] = False


class ChatResponse(BaseModel):
    """Response model for chat endpoint"""
    response: str
    tools_used: List[str]
    session_token: Optional[str]
    success: bool
    error: Optional[str] = None


@router.post("/chat", response_model=ChatResponse)
async def process_chat(request: ChatRequest) -> ChatResponse:
    """Process a chat message using the agent.
    
    This endpoint accepts a text message and processes it using the configured
    LangGraph agent with access to various tools.
    """
    try:
        result = await chat(
            message=request.message,
            categories=request.categories,
            model=request.model,
            system_prompt=request.system_prompt,
            session_token=request.session_token,
            user_role=request.user_role
        )
        
        return ChatResponse(**result)
        
    except Exception as e:
        logger.error(f"Chat processing error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/chat/stream")
async def process_chat_stream(request: ChatRequest):
    """Stream chat responses token by token.
    
    Returns a Server-Sent Event stream for real-time responses.
    """
    async def generate():
        try:
            async for chunk in stream_response(
                message=request.message,
                categories=request.categories,
                model=request.model,
                system_prompt=request.system_prompt,
                session_token=request.session_token,
                user_role=request.user_role
            ):
                yield f"data: {chunk}\n\n"
        except Exception as e:
            logger.error(f"Stream error: {e}")
            yield f"data: Error: {str(e)}\n\n"
    
    return StreamingResponse(generate(), media_type="text/event-stream")


@router.get("/tools")
async def get_available_tools() -> Dict[str, Any]:
    """Get descriptions of all available tools organized by category."""
    try:
        return {
            "categories": get_tool_descriptions(),
            "total_categories": len(get_tool_descriptions()),
        }
    except Exception as e:
        logger.error(f"Error getting tools: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tools/{category}")
async def get_category_tools(category: str) -> Dict[str, Any]:
    """Get tools for a specific category."""
    try:
        all_tools = get_tool_descriptions()
        
        if category not in all_tools:
            raise HTTPException(status_code=404, detail=f"Category '{category}' not found")
        
        return all_tools[category]
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting category tools: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Simple endpoint for quick testing
@router.post("/quick")
async def quick_chat(message: str) -> Dict[str, str]:
    """Quick chat endpoint for simple testing.
    
    Just send a message string and get a response.
    Uses default settings with GitHub and utility tools.
    """
    try:
        result = await chat(
            message=message,
            categories=["github", "utility"],
            model="gpt-oss-120b"
        )
        
        return {
            "response": result["response"],
            "tools_used": ", ".join(result["tools_used"]) if result["tools_used"] else "none"
        }
        
    except Exception as e:
        logger.error(f"Quick chat error: {e}")
        return {
            "response": f"Error: {str(e)}",
            "tools_used": "none"
        }