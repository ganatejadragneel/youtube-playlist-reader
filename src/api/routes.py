import time
import asyncio
import json
from typing import List

from fastapi import APIRouter, HTTPException, Depends, Request, Form
from fastapi.responses import HTMLResponse
from loguru import logger

from src.api.models import (
    QuestionRequest, VideoSearchRequest, QAResponse as APIQAResponse,
    VideoResponse, PlaylistSummaryResponse, HealthResponse, ErrorResponse,
    ChannelResponse, PlaylistResponse, ChannelSearchRequest, 
    URLAnalysisRequest, URLAnalysisResponse
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


@router.get("/config")
async def get_config(request: Request):
    """Get application configuration."""
    try:
        config_data = {
            "default_youtube_url": str(settings.youtube_url),
            "is_playlist": youtube_adapter.is_playlist_url(str(settings.youtube_url)),
            "is_channel": youtube_adapter.is_channel_url(str(settings.youtube_url)),
            "default_channel_url": "https://www.youtube.com/@jordanhasnolife5163",
            "default_playlist_url": "https://www.youtube.com/playlist?list=PLjTveVh7FakJOoY6GPZGWHHl4shhDT8iV"
        }
        
        # Return HTML for HTMX or JSON for API
        if "HX-Request" in request.headers:
            return HTMLResponse(f'<script>window.appConfig = {json.dumps(config_data)};</script>')
        else:
            return config_data
            
    except Exception as e:
        logger.error(f"Error getting config: {e}")
        if "HX-Request" in request.headers:
            return HTMLResponse('<script>window.appConfig = {};</script>')
        else:
            return {}


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
    playlist_url: str = Form(None),
    max_videos: int = Form(None)  # None means analyze all videos
):
    """Ask a question about the playlist content."""
    try:
        start_time = time.time()
        
        # Use provided playlist_url or fall back to settings
        youtube_url = playlist_url if playlist_url else str(settings.youtube_url)
        
        logger.info(f"Processing question: {question} for URL: {youtube_url}")
        
        response = await qa_service.answer_question(
            question=question,
            youtube_url=youtube_url,
            max_videos=None  # Analyze all videos for comprehensive answers
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
    playlist_url: str = Form(None),
    max_results: int = Form(None)  # None means return all matching videos
):
    """Search for videos in the playlist."""
    try:
        # Use provided playlist_url or fall back to settings
        youtube_url = playlist_url if playlist_url else str(settings.youtube_url)
        
        logger.info(f"Searching videos for: {query} in URL: {youtube_url}")
        
        videos = await qa_service.search_videos(
            query=query,
            youtube_url=youtube_url,
            max_results=max_results  # Pass through the limit, None means all
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
async def get_summary(request: Request, url: str = None):
    """Get a summary of the playlist or channel."""
    try:
        target_url = url if url else str(settings.youtube_url)
        
        logger.info(f"Getting summary for: {target_url}")
        
        # Determine if it's a playlist or channel URL
        if youtube_adapter.is_playlist_url(target_url):
            # Get playlist metadata
            playlist = await youtube_adapter.get_playlist(target_url)
            
            # Get AI-generated summary
            summary_response = await qa_service.get_summary(target_url)
        else:
            # Handle channel URL - get channel info
            channel = await youtube_adapter.get_channel(target_url)
            
            # Get AI-generated summary
            summary_response = await qa_service.get_summary(target_url)
        
        if youtube_adapter.is_playlist_url(target_url):
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
        else:
            # For channels, create a similar response structure
            playlist_summary = PlaylistSummaryResponse(
                title=channel.title,
                channel_title=channel.title,
                video_count=channel.video_count or 0,
                description=channel.description,
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
        logger.error(f"Error getting summary: {e}")
        error_msg = f"Failed to get summary: {str(e)}"
        if "HX-Request" in request.headers:
            return HTMLResponse(render_error(error_msg))
        else:
            raise HTTPException(status_code=500, detail=error_msg)


@router.get("/videos")
async def get_videos(request: Request, url: str = None, max_videos: int = 20):
    """Get videos from the playlist or recent videos from channel."""
    try:
        target_url = url if url else str(settings.youtube_url)
        
        logger.info(f"Getting videos from: {target_url}")
        
        if youtube_adapter.is_playlist_url(target_url):
            videos = await youtube_adapter.get_playlist_videos(target_url, max_results=max_videos)
        else:
            # For channels, get recent videos by searching with empty query
            videos = await youtube_adapter.search_channel_videos(
                target_url, 
                query="", 
                max_results=max_videos,
                include_transcripts=False
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
        logger.error(f"Error getting videos: {e}")
        error_msg = f"Failed to get videos: {str(e)}"
        if "HX-Request" in request.headers:
            return HTMLResponse(render_error(error_msg))
        else:
            raise HTTPException(status_code=500, detail=error_msg)


# New channel-specific endpoints
@router.post("/analyze-url")
async def analyze_url(request: Request, url: str = Form(...)):
    """Analyze a URL to determine if it's a channel or playlist."""
    try:
        logger.info(f"Analyzing URL: {url}")
        
        is_channel = youtube_adapter.is_channel_url(url)
        is_playlist = youtube_adapter.is_playlist_url(url)
        
        if is_playlist:
            playlist_id = youtube_adapter.extract_playlist_id(url)
            response = URLAnalysisResponse(
                url_type="playlist",
                identifier=playlist_id,
                is_valid=True
            )
        elif is_channel:
            channel_id = youtube_adapter.extract_channel_id(url)
            response = URLAnalysisResponse(
                url_type="channel", 
                identifier=channel_id,
                is_valid=True
            )
        else:
            response = URLAnalysisResponse(
                url_type="unknown",
                identifier="",
                is_valid=False,
                error="URL is not a valid YouTube channel or playlist URL"
            )
        
        # Return HTML for HTMX or JSON for API
        if "HX-Request" in request.headers:
            return HTMLResponse(f"""
                <div class="p-4 bg-gray-100 rounded-lg">
                    <p><strong>URL Type:</strong> {response.url_type}</p>
                    <p><strong>Valid:</strong> {response.is_valid}</p>
                    {f'<p><strong>Error:</strong> {response.error}</p>' if response.error else ''}
                </div>
            """)
        else:
            return response
            
    except Exception as e:
        logger.error(f"Error analyzing URL: {e}")
        error_msg = f"Failed to analyze URL: {str(e)}"
        if "HX-Request" in request.headers:
            return HTMLResponse(render_error(error_msg))
        else:
            raise HTTPException(status_code=500, detail=error_msg)


@router.get("/channel/playlists")
async def get_channel_playlists(request: Request, channel_url: str, max_results: int = None):
    """Get playlists from a channel."""
    try:
        logger.info(f"Getting playlists from channel: {channel_url}")
        
        # Add timeout to prevent hanging requests
        try:
            playlists = await asyncio.wait_for(
                youtube_adapter.get_channel_playlists(channel_url, max_results=max_results),
                timeout=30.0  # 30 second timeout
            )
        except asyncio.TimeoutError:
            logger.warning(f"Timeout getting playlists for channel: {channel_url}")
            playlists = []
        
        playlist_responses = [
            PlaylistResponse(
                playlist_id=playlist.playlist_id,
                title=playlist.title,
                description=playlist.description,
                channel_title=playlist.channel_title,
                video_count=playlist.video_count,
                published_at=playlist.published_at.isoformat()
            )
            for playlist in playlists
        ]
        
        # Return HTML for HTMX or JSON for API  
        if "HX-Request" in request.headers:
            playlist_html = ""
            for playlist in playlist_responses:
                playlist_html += f"""
                    <div class="bg-white p-4 rounded-lg shadow mb-4 cursor-pointer hover:bg-gray-50" 
                         onclick="selectPlaylist('{playlist.playlist_id}', '{playlist.title}')">
                        <h3 class="font-bold text-lg">{playlist.title}</h3>
                        <p class="text-gray-600">{playlist.video_count} videos</p>
                        <p class="text-gray-500 text-sm">{playlist.description[:100]}...</p>
                    </div>
                """
            return HTMLResponse(playlist_html)
        else:
            return playlist_responses
            
    except Exception as e:
        logger.error(f"Error getting channel playlists: {e}")
        error_msg = f"Failed to get channel playlists: {str(e)}"
        if "HX-Request" in request.headers:
            return HTMLResponse(render_error(error_msg))
        else:
            raise HTTPException(status_code=500, detail=error_msg)


@router.get("/channel/info")
async def get_channel_info(request: Request, channel_url: str):
    """Get channel information."""
    try:
        logger.info(f"Getting channel info: {channel_url}")
        
        channel = await youtube_adapter.get_channel(channel_url)
        
        # Try to get playlist count by fetching first page of playlists
        playlist_count = None
        try:
            # Just get the first page to get total count
            playlists_response = youtube_adapter._youtube.playlists().list(
                part="id",
                channelId=channel.channel_id,
                maxResults=1
            ).execute() if youtube_adapter._youtube else None
            
            if playlists_response:
                playlist_count = playlists_response.get("pageInfo", {}).get("totalResults", None)
        except Exception as e:
            logger.warning(f"Could not fetch playlist count: {e}")
        
        channel_response = ChannelResponse(
            channel_id=channel.channel_id,
            title=channel.title,
            description=channel.description,
            subscriber_count=channel.subscriber_count,
            video_count=channel.video_count,
            playlist_count=playlist_count,
            published_at=channel.published_at.isoformat() if channel.published_at else None,
            thumbnail_url=channel.thumbnail_url,
            custom_url=channel.custom_url
        )
        
        # Return HTML for HTMX or JSON for API
        if "HX-Request" in request.headers:
            return HTMLResponse(f"""
                <div class="bg-white p-6 rounded-lg shadow">
                    <div class="flex items-center space-x-4 mb-4">
                        {f'<img src="{channel.thumbnail_url}" alt="{channel.title}" class="w-16 h-16 rounded-full">' if channel.thumbnail_url else ''}
                        <div>
                            <h2 class="text-xl font-bold">{channel.title}</h2>
                            <p class="text-gray-600">{channel.subscriber_count:,} subscribers</p>
                        </div>
                    </div>
                    <p class="text-gray-700 mb-4">{channel.description[:200]}...</p>
                    <div class="grid grid-cols-2 gap-4">
                        <div>
                            <p class="font-semibold">Videos: {channel.video_count:,}</p>
                        </div>
                        <div>
                            <p class="font-semibold">Playlists: {playlist_count if playlist_count is not None else 'N/A'}</p>
                        </div>
                    </div>
                </div>
            """)
        else:
            return channel_response
            
    except Exception as e:
        logger.error(f"Error getting channel info: {e}")
        error_msg = f"Failed to get channel info: {str(e)}"
        if "HX-Request" in request.headers:
            return HTMLResponse(render_error(error_msg))
        else:
            raise HTTPException(status_code=500, detail=error_msg)


@router.post("/channel/search")
async def search_channel_videos(
    request: Request,
    query: str = Form(...),
    channel_url: str = Form(None),
    max_results: int = Form(10),
    include_transcripts: bool = Form(True)
):
    """Search for videos in a channel."""
    try:
        target_url = channel_url if channel_url else str(settings.youtube_url)
        
        logger.info(f"Searching channel videos for: {query} in {target_url}")
        
        videos = await youtube_adapter.search_channel_videos(
            target_url,
            query=query,
            max_results=max_results,
            include_transcripts=include_transcripts
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
        logger.error(f"Error searching channel videos: {e}")
        error_msg = f"Failed to search channel videos: {str(e)}"
        if "HX-Request" in request.headers:
            return HTMLResponse(render_error(error_msg))
        else:
            raise HTTPException(status_code=500, detail=error_msg)