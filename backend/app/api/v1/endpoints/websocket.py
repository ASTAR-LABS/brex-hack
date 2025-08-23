from fastapi import WebSocket, WebSocketDisconnect
from app.services.websocket_service import WebSocketService
import logging

logger = logging.getLogger(__name__)

websocket_service = WebSocketService()

async def audio_websocket_endpoint(websocket: WebSocket):
    await websocket_service.handle_audio_connection(websocket)