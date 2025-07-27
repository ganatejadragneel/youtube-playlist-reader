#!/usr/bin/env python3
"""
Simple script to run the web server.
"""
import uvicorn
from src.api.app import app

if __name__ == "__main__":
    print("🎬 Starting YouTube Playlist Reader Web Interface")
    print("=" * 50)
    print("📍 Server: http://localhost:8000")
    print("📚 API Docs: http://localhost:8000/api/docs")
    print("🏥 Health Check: http://localhost:8000/api/health")
    print("=" * 50)
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        reload=False,
        log_level="info"
    )