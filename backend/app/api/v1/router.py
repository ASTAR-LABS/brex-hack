from fastapi import APIRouter, WebSocket
from app.api.v1.endpoints import actions

router = APIRouter()

# WebSocket endpoint will be handled directly
# Include Actions endpoints
router.include_router(actions.router, prefix="/actions", tags=["actions"])