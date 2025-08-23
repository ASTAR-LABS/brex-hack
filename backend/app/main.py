from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.core.config import settings
from app.core.database import init_db
from app.api.v1.router import router as api_v1_router
from app.services.websocket_service import WebSocketService
from app.services.action_executor_service import ActionExecutorService
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize services
websocket_service = WebSocketService()
executor_service = ActionExecutorService()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting up services...")
    await init_db()
    await websocket_service.start()
    await executor_service.start()
    yield
    # Shutdown
    logger.info("Shutting down services...")
    await websocket_service.stop()
    await executor_service.stop()

# Create FastAPI app
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=settings.cors_allow_credentials,
    allow_methods=settings.cors_allow_methods,
    allow_headers=settings.cors_allow_headers,
)

# Include API router
app.include_router(api_v1_router, prefix=settings.api_v1_str)

# Root endpoint
@app.get("/")
async def root():
    return {
        "message": settings.app_name,
        "version": settings.app_version,
        "endpoints": {
            "websocket": f"ws://localhost:{settings.port}{settings.api_v1_str}/ws/audio",
            "health": "/health",
            "sessions": f"{settings.api_v1_str}/sessions"
        }
    }

# Health check endpoint
@app.get("/health")
async def health_check():
    return {"status": "healthy"}

# Sessions endpoint
@app.get(f"{settings.api_v1_str}/sessions")
async def get_sessions():
    return {
        "active_sessions": websocket_service.session_manager.get_active_sessions_count(),
        "sessions": websocket_service.session_manager.get_all_sessions()
    }