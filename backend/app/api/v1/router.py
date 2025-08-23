from fastapi import APIRouter, WebSocket
from app.api.v1.endpoints import actions, mcp, agent, auth

router = APIRouter()

# Include Actions endpoints
router.include_router(actions.router, prefix="/actions", tags=["actions"])

# Include MCP endpoints
router.include_router(mcp.router, prefix="/mcp", tags=["mcp"])

# Include Agent endpoints
router.include_router(agent.router, prefix="/agent", tags=["agent"])

# Include Auth endpoints
router.include_router(auth.router, prefix="/auth", tags=["auth"])

# Register WebSocket endpoint
@router.websocket("/ws/audio")
async def websocket_endpoint(websocket: WebSocket):
    # Import the service inside the function to avoid circular dependency
    from app.main import websocket_service
    await websocket_service.handle_audio_connection(websocket)
