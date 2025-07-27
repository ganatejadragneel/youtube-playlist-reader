from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional


@dataclass(frozen=True)
class Video:
    """Domain model for a YouTube video."""

    video_id: str
    title: str
    description: str
    channel_title: str
    published_at: datetime
    duration: Optional[str] = None
    thumbnail_url: Optional[str] = None
    transcript: Optional[str] = None


@dataclass(frozen=True)
class Playlist:
    """Domain model for a YouTube playlist."""

    playlist_id: str
    title: str
    description: str
    channel_title: str
    video_count: int
    published_at: datetime
    videos: List[Video] = None