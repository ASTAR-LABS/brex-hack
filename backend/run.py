import os
# Disable uvloop to avoid conflicts with asyncio event loop patching
os.environ["UVLOOP_DISABLE"] = "1"

import uvicorn
from app.core.config import settings

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.reload,
        loop="asyncio"  # Use asyncio instead of uvloop to avoid nest_asyncio conflicts
    )