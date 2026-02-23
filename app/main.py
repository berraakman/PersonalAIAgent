"""Main FastAPI application entry point."""

import os

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from app.routers import auth, chat

# Create the FastAPI app
app = FastAPI(
    title="BerrAI – Personal AI Agent",
    description="Google ekosistemi ile entegre kişisel AI asistanı",
    version="1.0.0",
)

# Include routers
app.include_router(auth.router)
app.include_router(chat.router)

# Serve static files
STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/")
async def serve_index():
    """Serve the main SPA."""
    return FileResponse(os.path.join(STATIC_DIR, "index.html"))


@app.get("/health")
async def health():
    return {"status": "ok", "service": " BerrAI Assistant"}


if __name__ == "__main__":
    import uvicorn
    from app.config import settings

    uvicorn.run(
        "app.main:app",
        host=settings.APP_HOST,
        port=settings.APP_PORT,
        reload=True,
    )
