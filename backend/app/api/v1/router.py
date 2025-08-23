from fastapi import APIRouter, WebSocket
from app.api.v1.endpoints import actions

router = APIRouter()

# Include Actions endpoints
router.include_router(actions.router, prefix="/actions", tags=["actions"])

# Register WebSocket endpoint
@router.websocket("/ws/audio")
async def websocket_endpoint(websocket: WebSocket):
    # Import the service inside the function to avoid circular dependency
    from app.main import websocket_service
    await websocket_service.handle_audio_connection(websocket)
