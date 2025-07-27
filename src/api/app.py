from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pathlib import Path
from loguru import logger

from src.api.routes import router
from src.config import settings

# Create FastAPI app
app = FastAPI(
    title="YouTube Playlist Reader",
    description="AI-powered YouTube playlist analysis and Q&A system",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(router, prefix="/api")

# Serve static files
static_dir = Path(__file__).parent / "static"
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

@app.get("/")
async def serve_index():
    """Serve the main web interface."""
    static_dir = Path(__file__).parent / "static"
    index_file = static_dir / "index.html"
    
    if index_file.exists():
        return FileResponse(index_file)
    else:
        return {
            "message": "YouTube Playlist Reader API",
            "docs": "/api/docs",
            "health": "/api/health"
        }

@app.on_event("startup")
async def startup_event():
    """Initialize application on startup."""
    logger.info("Starting YouTube Playlist Reader API")
    logger.info(f"Ollama URL: {settings.ollama_base_url}")
    logger.info(f"Ollama Model: {settings.ollama_model}")
    logger.info(f"YouTube API Key: {'✅ Set' if settings.youtube_api_key else '❌ Not set'}")

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    logger.info("Shutting down YouTube Playlist Reader API")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "src.api.app:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )