from typing import List, Optional
from pydantic import BaseModel, HttpUrl


class QuestionRequest(BaseModel):
    """Request model for asking questions."""
    question: str
    playlist_url: Optional[HttpUrl] = None
    max_videos: Optional[int] = 10


class VideoSearchRequest(BaseModel):
    """Request model for searching videos."""
    query: str
    playlist_url: Optional[HttpUrl] = None
    max_results: Optional[int] = 5


class VideoResponse(BaseModel):
    """Response model for video information."""
    video_id: str
    title: str
    description: str
    channel_title: str
    published_at: str
    thumbnail_url: Optional[str] = None


class QAResponse(BaseModel):
    """Response model for Q&A answers."""
    answer: str
    sources: List[str]
    confidence: float
    processing_time: Optional[float] = None


class PlaylistSummaryResponse(BaseModel):
    """Response model for playlist summary."""
    title: str
    channel_title: str
    video_count: int
    description: str
    summary: QAResponse


class HealthResponse(BaseModel):
    """Response model for health check."""
    status: str
    youtube_api: bool
    ollama: bool
    message: str


class ErrorResponse(BaseModel):
    """Response model for errors."""
    error: str
    detail: Optional[str] = None


class ChannelResponse(BaseModel):
    """Response model for channel information."""
    channel_id: str
    title: str
    description: str
    subscriber_count: Optional[int] = None
    video_count: Optional[int] = None
    playlist_count: Optional[int] = None
    published_at: Optional[str] = None
    thumbnail_url: Optional[str] = None
    custom_url: Optional[str] = None


class PlaylistResponse(BaseModel):
    """Response model for playlist information."""
    playlist_id: str
    title: str
    description: str
    channel_title: str
    video_count: int
    published_at: str


class ChannelSearchRequest(BaseModel):
    """Request model for searching videos in a channel."""
    query: str
    channel_url: Optional[HttpUrl] = None
    max_results: Optional[int] = 10
    include_transcripts: bool = True


class URLAnalysisRequest(BaseModel):
    """Request model for analyzing a URL to determine if it's channel or playlist."""
    url: HttpUrl


class URLAnalysisResponse(BaseModel):
    """Response model for URL analysis."""
    url_type: str  # 'channel' or 'playlist'
    identifier: str  # channel_id or playlist_id
    is_valid: bool
    error: Optional[str] = None