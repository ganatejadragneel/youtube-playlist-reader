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