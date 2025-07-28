import os
import pytest
from src.adapters.youtube_adapter import YouTubeAPIAdapter
from src.config import settings


@pytest.mark.skipif(
    not os.getenv("YOUTUBE_API_KEY"),
    reason="YouTube API key not provided",
)
class TestYouTubeAPIAdapterIntegration:
    """Integration tests that hit the real YouTube API."""

    @pytest.fixture
    async def adapter(self):
        """Create adapter with real API key."""
        return YouTubeAPIAdapter(api_key=os.getenv("YOUTUBE_API_KEY"))

    @pytest.mark.asyncio
    async def test_real_playlist_fetch(self, adapter):
        """Test fetching the actual playlist from the configuration."""
        playlist = await adapter.get_playlist(str(settings.youtube_url))
        
        assert playlist.playlist_id
        assert playlist.title
        assert playlist.video_count > 0

    @pytest.mark.asyncio
    async def test_real_playlist_videos_fetch(self, adapter):
        """Test fetching videos from the actual playlist."""
        videos = await adapter.get_playlist_videos(
            str(settings.youtube_url), max_results=3
        )
        
        assert len(videos) <= 3
        assert all(v.video_id for v in videos)
        assert all(v.title for v in videos)

    @pytest.mark.asyncio
    async def test_real_transcript_fetch(self, adapter):
        """Test fetching transcript from a real video."""
        # First get a video from the playlist
        videos = await adapter.get_playlist_videos(
            str(settings.youtube_url), max_results=1
        )
        
        if videos:
            video = videos[0]
            transcript = await adapter.get_video_transcript(video.video_id)
            # Transcript might not be available for all videos
            assert transcript is None or isinstance(transcript, str)


class TestYouTubeAPIAdapterNoKey:
    """Tests for adapter behavior without API key."""

    @pytest.fixture
    async def adapter(self):
        """Create adapter without API key."""
        return YouTubeAPIAdapter()

    @pytest.mark.asyncio
    async def test_playlist_without_key(self, adapter):
        """Test that adapter handles missing API key gracefully."""
        playlist = await adapter.get_playlist(str(settings.youtube_url))
        
        # Should return minimal data
        assert playlist.playlist_id
        assert playlist.title  # Will be generic
        assert playlist.video_count == 0

    @pytest.mark.asyncio
    async def test_transcript_without_key(self, adapter):
        """Test that transcript fetching works without API key."""
        # This should work as youtube-transcript-api doesn't need API key
        transcript = await adapter.get_video_transcript("dQw4w9WgXcQ")  # Well-known video
        # May or may not have transcript
        assert transcript is None or isinstance(transcript, str)