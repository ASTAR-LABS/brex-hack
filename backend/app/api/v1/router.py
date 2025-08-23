from fastapi import APIRouter, WebSocket
from app.api.v1.endpoints import websocket, actions

router = APIRouter()

# Include WebSocket endpoint
@router.websocket("/ws/audio")
async def audio_websocket(ws: WebSocket):
    await websocket.audio_websocket_endpoint(ws)

# Include Actions endpoints
router.include_router(actions.router, prefix="/actions", tags=["actions"])