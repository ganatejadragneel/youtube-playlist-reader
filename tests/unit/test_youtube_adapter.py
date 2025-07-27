import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

from src.adapters.youtube_adapter import YouTubeAPIAdapter
from src.core.models import Playlist, Video


class TestYouTubeAPIAdapter:
    @pytest.fixture
    def adapter_with_key(self):
        """Create adapter with API key."""
        with patch("src.adapters.youtube_adapter.build") as mock_build:
            mock_youtube = MagicMock()
            mock_build.return_value = mock_youtube
            adapter = YouTubeAPIAdapter(api_key="test_api_key")
            adapter._youtube = mock_youtube
            return adapter

    @pytest.fixture
    def adapter_without_key(self):
        """Create adapter without API key."""
        return YouTubeAPIAdapter()

    def test_extract_playlist_id_from_url(self, adapter_with_key):
        """Test extracting playlist ID from various URL formats."""
        test_cases = [
            (
                "https://www.youtube.com/playlist?list=PLtest123",
                "PLtest123",
            ),
            (
                "https://youtube.com/playlist?list=PLtest123&feature=share",
                "PLtest123",
            ),
            (
                "https://www.youtube.com/watch?v=xyz&list=PLtest123",
                "PLtest123",
            ),
        ]

        for url, expected_id in test_cases:
            assert adapter_with_key.extract_playlist_id(url) == expected_id

    def test_extract_playlist_id_invalid_url(self, adapter_with_key):
        """Test that invalid URLs raise ValueError."""
        with pytest.raises(ValueError):
            adapter_with_key.extract_playlist_id("https://www.youtube.com/watch?v=xyz")

    @pytest.mark.asyncio
    async def test_get_playlist_with_api_key(self, adapter_with_key):
        """Test fetching playlist metadata with API key."""
        mock_response = {
            "items": [
                {
                    "snippet": {
                        "title": "Test Playlist",
                        "description": "Test Description",
                        "channelTitle": "Test Channel",
                        "publishedAt": "2023-01-01T00:00:00Z",
                    },
                    "contentDetails": {"itemCount": 10},
                }
            ]
        }

        adapter_with_key._youtube.playlists().list().execute.return_value = (
            mock_response
        )

        playlist = await adapter_with_key.get_playlist("PLtest123")

        assert playlist.playlist_id == "PLtest123"
        assert playlist.title == "Test Playlist"
        assert playlist.description == "Test Description"
        assert playlist.channel_title == "Test Channel"
        assert playlist.video_count == 10

    @pytest.mark.asyncio
    async def test_get_playlist_not_found(self, adapter_with_key):
        """Test handling of non-existent playlist."""
        adapter_with_key._youtube.playlists().list().execute.return_value = {
            "items": []
        }

        with pytest.raises(ValueError, match="Playlist not found"):
            await adapter_with_key.get_playlist("PLnonexistent")

    @pytest.mark.asyncio
    async def test_get_playlist_without_api_key(self, adapter_without_key):
        """Test fallback behavior without API key."""
        playlist = await adapter_without_key.get_playlist("PLtest123")

        assert playlist.playlist_id == "PLtest123"
        assert playlist.title == "Playlist PLtest123"
        assert playlist.video_count == 0

    @pytest.mark.asyncio
    async def test_get_playlist_videos_with_api_key(self, adapter_with_key):
        """Test fetching videos from playlist with API key."""
        mock_response = {
            "items": [
                {
                    "snippet": {
                        "title": f"Video {i}",
                        "description": f"Description {i}",
                        "channelTitle": "Test Channel",
                        "publishedAt": "2023-01-01T00:00:00Z",
                        "thumbnails": {"medium": {"url": f"http://thumb{i}.jpg"}},
                    },
                    "contentDetails": {"videoId": f"video{i}"},
                }
                for i in range(3)
            ],
            "nextPageToken": None,
        }

        adapter_with_key._youtube.playlistItems().list().execute.return_value = (
            mock_response
        )

        videos = await adapter_with_key.get_playlist_videos("PLtest123")

        assert len(videos) == 3
        assert all(isinstance(v, Video) for v in videos)
        assert videos[0].video_id == "video0"
        assert videos[0].title == "Video 0"

    @pytest.mark.asyncio
    async def test_get_playlist_videos_with_max_results(self, adapter_with_key):
        """Test limiting number of videos fetched."""
        mock_response = {
            "items": [
                {
                    "snippet": {
                        "title": f"Video {i}",
                        "description": "",
                        "channelTitle": "Test Channel",
                        "publishedAt": "2023-01-01T00:00:00Z",
                    },
                    "contentDetails": {"videoId": f"video{i}"},
                }
                for i in range(10)
            ],
            "nextPageToken": None,
        }

        adapter_with_key._youtube.playlistItems().list().execute.return_value = (
            mock_response
        )

        videos = await adapter_with_key.get_playlist_videos("PLtest123", max_results=5)

        assert len(videos) == 5

    @pytest.mark.asyncio
    async def test_get_video_transcript(self, adapter_with_key):
        """Test fetching video transcript."""
        mock_transcript = [
            {"text": "Hello world", "start": 0.0, "duration": 2.0},
            {"text": "This is a test", "start": 2.0, "duration": 2.0},
        ]

        with patch(
            "src.adapters.youtube_adapter.YouTubeTranscriptApi"
        ) as mock_transcript_api:
            mock_transcript_list = MagicMock()
            mock_transcript_api.list_transcripts.return_value = mock_transcript_list
            
            mock_transcript_obj = MagicMock()
            mock_transcript_obj.fetch.return_value = mock_transcript
            mock_transcript_list.find_manually_created_transcript.return_value = (
                mock_transcript_obj
            )

            transcript = await adapter_with_key.get_video_transcript("video123")

            assert transcript == "Hello world This is a test"

    @pytest.mark.asyncio
    async def test_get_video_transcript_not_available(self, adapter_with_key):
        """Test handling when transcript is not available."""
        with patch(
            "src.adapters.youtube_adapter.YouTubeTranscriptApi"
        ) as mock_transcript_api:
            mock_transcript_api.list_transcripts.side_effect = Exception(
                "No transcript"
            )

            transcript = await adapter_with_key.get_video_transcript("video123")

            assert transcript is None

    @pytest.mark.asyncio
    async def test_get_video_details_with_api_key(self, adapter_with_key):
        """Test fetching video details with API key."""
        mock_response = {
            "items": [
                {
                    "snippet": {
                        "title": "Test Video",
                        "description": "Test Description",
                        "channelTitle": "Test Channel",
                        "publishedAt": "2023-01-01T00:00:00Z",
                        "thumbnails": {"medium": {"url": "http://thumb.jpg"}},
                    },
                    "contentDetails": {"duration": "PT10M30S"},
                }
            ]
        }

        adapter_with_key._youtube.videos().list().execute.return_value = mock_response

        video = await adapter_with_key.get_video_details("video123")

        assert video.video_id == "video123"
        assert video.title == "Test Video"
        assert video.duration == "PT10M30S"
        assert video.thumbnail_url == "http://thumb.jpg"

    @pytest.mark.asyncio
    async def test_get_video_details_not_found(self, adapter_with_key):
        """Test handling of non-existent video."""
        adapter_with_key._youtube.videos().list().execute.return_value = {"items": []}

        with pytest.raises(ValueError, match="Video not found"):
            await adapter_with_key.get_video_details("nonexistent")