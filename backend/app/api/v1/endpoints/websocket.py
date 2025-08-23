from fastapi import WebSocket, WebSocketDisconnect
import logging

logger = logging.getLogger(__name__)

async def audio_websocket_endpoint(websocket: WebSocket):
    from app.services.websocket_service import WebSocketService
    # Create a new instance for this connection
    websocket_service = WebSocketService()
    await websocket_service.handle_audio_connection(websocket)