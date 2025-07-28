import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

from src.services.qa_service import YouTubeQAService, QAResponse
from src.core.models import Playlist, Video


class TestYouTubeQAService:
    @pytest.fixture
    def mock_youtube_repo(self):
        """Mock YouTube repository."""
        return AsyncMock()

    @pytest.fixture
    def mock_llm_repo(self):
        """Mock LLM repository."""
        return AsyncMock()

    @pytest.fixture
    def qa_service(self, mock_youtube_repo, mock_llm_repo):
        """Create QA service with mocked dependencies."""
        return YouTubeQAService(mock_youtube_repo, mock_llm_repo)

    @pytest.fixture
    def sample_playlist(self):
        """Sample playlist for testing."""
        return Playlist(
            playlist_id="PLtest123",
            title="Test Gaming Playlist",
            description="A playlist about gaming videos",
            channel_title="TestChannel",
            video_count=10,
            published_at=datetime(2023, 1, 1)
        )

    @pytest.fixture
    def sample_videos(self):
        """Sample videos for testing."""
        return [
            Video(
                video_id="video1",
                title="Epic Gaming Moment #1",
                description="Amazing gameplay with friends",
                channel_title="TestChannel",
                published_at=datetime(2023, 1, 1)
            ),
            Video(
                video_id="video2",
                title="Epic Gaming Moment #2",
                description="More epic gameplay",
                channel_title="TestChannel",
                published_at=datetime(2023, 1, 2)
            )
        ]

    @pytest.mark.asyncio
    async def test_answer_question_success(
        self, qa_service, mock_youtube_repo, mock_llm_repo, sample_playlist, sample_videos
    ):
        """Test successful question answering."""
        # Mock repository responses
        mock_youtube_repo.get_playlist.return_value = sample_playlist
        mock_youtube_repo.get_playlist_videos.return_value = sample_videos
        mock_llm_repo.generate_response.return_value = "This is a gaming playlist with epic moments."

        result = await qa_service.answer_question(
            "What is this playlist about?",
            "https://youtube.com/playlist?list=PLtest123"
        )

        assert isinstance(result, QAResponse)
        assert result.answer == "This is a gaming playlist with epic moments."
        assert len(result.sources) == 2
        assert result.confidence == 0.8
        assert "Epic Gaming Moment #1" in result.sources[0]

    @pytest.mark.asyncio
    async def test_answer_question_with_error(
        self, qa_service, mock_youtube_repo, mock_llm_repo
    ):
        """Test error handling in question answering."""
        # Mock an error
        mock_youtube_repo.get_playlist.side_effect = Exception("API Error")

        result = await qa_service.answer_question(
            "What is this about?",
            "https://youtube.com/playlist?list=PLtest123"
        )

        assert isinstance(result, QAResponse)
        assert "error" in result.answer.lower()
        assert result.confidence == 0.0
        assert len(result.sources) == 0

    def test_build_context(self, qa_service, sample_playlist, sample_videos):
        """Test context building from playlist and videos."""
        context = qa_service._build_playlist_context(sample_playlist, sample_videos)

        assert "PLAYLIST INFORMATION:" in context
        assert sample_playlist.title in context
        assert sample_playlist.channel_title in context
        assert "VIDEOS IN PLAYLIST" in context
        assert sample_videos[0].title in context
        assert sample_videos[1].title in context

    def test_build_context_with_long_description(self, qa_service):
        """Test context building with long video descriptions."""
        playlist = Playlist(
            playlist_id="PLtest",
            title="Test",
            description="Test playlist",
            channel_title="Test",
            video_count=1,
            published_at=datetime.now()
        )
        
        long_description = "A" * 300  # 300 character description
        video = Video(
            video_id="test",
            title="Test Video",
            description=long_description,
            channel_title="Test",
            published_at=datetime.now()
        )

        context = qa_service._build_playlist_context(playlist, [video])

        # Should truncate long descriptions
        assert len([line for line in context.split('\n') if 'Description:' in line][0]) < 250

    @pytest.mark.asyncio
    async def test_get_playlist_summary(
        self, qa_service, mock_youtube_repo, mock_llm_repo, sample_playlist, sample_videos
    ):
        """Test getting playlist summary."""
        # Mock repository responses
        mock_youtube_repo.get_playlist.return_value = sample_playlist
        mock_youtube_repo.get_playlist_videos.return_value = sample_videos
        mock_llm_repo.generate_response.return_value = "Gaming playlist summary"

        result = await qa_service.get_summary("https://youtube.com/playlist?list=PLtest123")

        assert isinstance(result, QAResponse)
        assert result.answer == "Gaming playlist summary"
        
        # Check that the LLM was called with a summary-specific prompt
        call_args = mock_llm_repo.generate_response.call_args
        prompt = call_args[1]['prompt']
        assert "summary" in prompt.lower()

    @pytest.mark.asyncio
    async def test_search_videos(
        self, qa_service, mock_youtube_repo, sample_videos
    ):
        """Test video searching functionality."""
        mock_youtube_repo.get_playlist_videos.return_value = sample_videos

        results = await qa_service.search_videos(
            "epic",
            "https://youtube.com/playlist?list=PLtest123"
        )

        assert len(results) == 2  # Both videos contain "epic"
        assert all("Epic" in video.title for video in results)

    @pytest.mark.asyncio
    async def test_search_videos_partial_match(
        self, qa_service, mock_youtube_repo, sample_videos
    ):
        """Test video searching with partial matches."""
        mock_youtube_repo.get_playlist_videos.return_value = sample_videos

        results = await qa_service.search_videos(
            "friends",
            "https://youtube.com/playlist?list=PLtest123"
        )

        assert len(results) == 1  # Only first video mentions "friends"
        assert "friends" in results[0].description.lower()

    @pytest.mark.asyncio
    async def test_search_videos_no_match(
        self, qa_service, mock_youtube_repo, sample_videos
    ):
        """Test video searching with no matches."""
        mock_youtube_repo.get_playlist_videos.return_value = sample_videos

        results = await qa_service.search_videos(
            "cooking",
            "https://youtube.com/playlist?list=PLtest123"
        )

        assert len(results) == 0

    @pytest.mark.asyncio
    async def test_search_videos_with_error(
        self, qa_service, mock_youtube_repo
    ):
        """Test video searching error handling."""
        mock_youtube_repo.get_playlist_videos.side_effect = Exception("Search error")

        results = await qa_service.search_videos(
            "test",
            "https://youtube.com/playlist?list=PLtest123"
        )

        assert len(results) == 0