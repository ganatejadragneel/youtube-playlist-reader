from abc import ABC, abstractmethod
from typing import List, Optional

from src.core.models import Playlist, Video


class YouTubeRepository(ABC):
    """Abstract interface for YouTube data access."""

    @abstractmethod
    async def get_playlist(self, playlist_id: str) -> Playlist:
        """Fetch playlist metadata from YouTube."""
        pass

    @abstractmethod
    async def get_playlist_videos(
        self, playlist_id: str, max_results: Optional[int] = None
    ) -> List[Video]:
        """Fetch all videos from a playlist."""
        pass

    @abstractmethod
    async def get_video_transcript(self, video_id: str) -> Optional[str]:
        """Fetch transcript for a specific video."""
        pass

    @abstractmethod
    async def get_video_details(self, video_id: str) -> Video:
        """Fetch detailed information about a specific video."""
        pass