import time
from typing import List

from fastapi import APIRouter, HTTPException, Depends, Request, Form
from fastapi.responses import HTMLResponse
from loguru import logger

from src.api.models import (
    QuestionRequest, VideoSearchRequest, QAResponse as APIQAResponse,
    VideoResponse, PlaylistSummaryResponse, HealthResponse, ErrorResponse
)
from src.api.templates import (
    render_health_status, render_summary, render_qa_response, 
    render_video_list, render_error
)
from src.services.qa_service import YouTubeQAService
from src.adapters.youtube_adapter import YouTubeAPIAdapter
from src.adapters.ollama_adapter import OllamaAdapter
from src.config import settings

router = APIRouter()

# Global service instances (initialized once)
youtube_adapter = YouTubeAPIAdapter(api_key=settings.youtube_api_key)
ollama_adapter = OllamaAdapter(
    base_url=settings.ollama_base_url,
    model=settings.ollama_model
)
qa_service = YouTubeQAService(youtube_adapter, ollama_adapter)


@router.get("/health")
async def health_check(request: Request):
    """Check the health of all services."""
    try:
        # Check YouTube API (simple call)
        youtube_ok = bool(settings.youtube_api_key)
        
        # Check Ollama
        ollama_ok = await ollama_adapter.health_check()
        
        overall_status = "healthy" if youtube_ok and ollama_ok else "degraded"
        
        health_response = HealthResponse(
            status=overall_status,
            youtube_api=youtube_ok,
            ollama=ollama_ok,
            message="All services operational" if overall_status == "healthy" else "Some services may be unavailable"
        )
        
        # Return HTML for HTMX or JSON for API
        if "HX-Request" in request.headers:
            return HTMLResponse(render_health_status(health_response))
        else:
            return health_response
            
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        error_msg = "Health check failed"
        if "HX-Request" in request.headers:
            return HTMLResponse(render_error(error_msg))
        else:
            raise HTTPException(status_code=500, detail=error_msg)


@router.post("/ask")
async def ask_question(
    request: Request,
    question: str = Form(...),
    max_videos: int = Form(10)
):
    """Ask a question about the playlist content."""
    try:
        start_time = time.time()
        
        playlist_url = str(settings.youtube_playlist_url)
        
        logger.info(f"Processing question: {question}")
        
        response = await qa_service.answer_question(
            question=question,
            playlist_url=playlist_url,
            max_videos=max_videos
        )
        
        processing_time = time.time() - start_time
        
        api_response = APIQAResponse(
            answer=response.answer,
            sources=response.sources,
            confidence=response.confidence,
            processing_time=processing_time
        )
        
        # Return HTML for HTMX or JSON for API
        if "HX-Request" in request.headers:
            return HTMLResponse(render_qa_response(api_response))
        else:
            return api_response
        
    except Exception as e:
        logger.error(f"Error processing question: {e}")
        error_msg = f"Failed to process question: {str(e)}"
        if "HX-Request" in request.headers:
            return HTMLResponse(render_error(error_msg))
        else:
            raise HTTPException(status_code=500, detail=error_msg)


@router.post("/search")
async def search_videos(
    request: Request,
    query: str = Form(...),
    max_results: int = Form(5)
):
    """Search for videos in the playlist."""
    try:
        playlist_url = str(settings.youtube_playlist_url)
        
        logger.info(f"Searching videos for: {query}")
        
        videos = await qa_service.search_videos(
            query=query,
            playlist_url=playlist_url,
            max_results=max_results
        )
        
        video_responses = [
            VideoResponse(
                video_id=video.video_id,
                title=video.title,
                description=video.description,
                channel_title=video.channel_title,
                published_at=video.published_at.isoformat(),
                thumbnail_url=video.thumbnail_url
            )
            for video in videos
        ]
        
        # Return HTML for HTMX or JSON for API
        if "HX-Request" in request.headers:
            return HTMLResponse(render_video_list(video_responses))
        else:
            return video_responses
        
    except Exception as e:
        logger.error(f"Error searching videos: {e}")
        error_msg = f"Failed to search videos: {str(e)}"
        if "HX-Request" in request.headers:
            return HTMLResponse(render_error(error_msg))
        else:
            raise HTTPException(status_code=500, detail=error_msg)


@router.get("/summary")
async def get_playlist_summary(request: Request, playlist_url: str = None):
    """Get a summary of the playlist."""
    try:
        url = playlist_url if playlist_url else str(settings.youtube_playlist_url)
        
        logger.info(f"Getting summary for playlist: {url}")
        
        # Get playlist metadata
        playlist = await youtube_adapter.get_playlist(url)
        
        # Get AI-generated summary
        summary_response = await qa_service.get_playlist_summary(url)
        
        playlist_summary = PlaylistSummaryResponse(
            title=playlist.title,
            channel_title=playlist.channel_title,
            video_count=playlist.video_count,
            description=playlist.description,
            summary=APIQAResponse(
                answer=summary_response.answer,
                sources=summary_response.sources,
                confidence=summary_response.confidence
            )
        )
        
        # Return HTML for HTMX or JSON for API
        if "HX-Request" in request.headers:
            return HTMLResponse(render_summary(playlist_summary))
        else:
            return playlist_summary
        
    except Exception as e:
        logger.error(f"Error getting playlist summary: {e}")
        error_msg = f"Failed to get playlist summary: {str(e)}"
        if "HX-Request" in request.headers:
            return HTMLResponse(render_error(error_msg))
        else:
            raise HTTPException(status_code=500, detail=error_msg)


@router.get("/playlist/videos")
async def get_playlist_videos(request: Request, playlist_url: str = None, max_videos: int = 20):
    """Get videos from the playlist."""
    try:
        url = playlist_url if playlist_url else str(settings.youtube_playlist_url)
        
        logger.info(f"Getting videos from playlist: {url}")
        
        videos = await youtube_adapter.get_playlist_videos(url, max_results=max_videos)
        
        video_responses = [
            VideoResponse(
                video_id=video.video_id,
                title=video.title,
                description=video.description,
                channel_title=video.channel_title,
                published_at=video.published_at.isoformat(),
                thumbnail_url=video.thumbnail_url
            )
            for video in videos
        ]
        
        # Return HTML for HTMX or JSON for API
        if "HX-Request" in request.headers:
            return HTMLResponse(render_video_list(video_responses))
        else:
            return video_responses
        
    except Exception as e:
        logger.error(f"Error getting playlist videos: {e}")
        error_msg = f"Failed to get playlist videos: {str(e)}"
        if "HX-Request" in request.headers:
            return HTMLResponse(render_error(error_msg))
        else:
            raise HTTPException(status_code=500, detail=error_msg)