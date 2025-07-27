from typing import List, Optional
from dataclasses import dataclass

from loguru import logger

from src.core.models import Video, Playlist
from src.interfaces.youtube_repository import YouTubeRepository
from src.interfaces.llm_repository import LLMRepository


@dataclass
class QAResponse:
    """Response from the Q&A system."""
    answer: str
    sources: List[str]
    confidence: float = 0.0


class YouTubeQAService:
    """Service for answering questions about YouTube playlist content."""

    def __init__(
        self,
        youtube_repo: YouTubeRepository,
        llm_repo: LLMRepository,
    ):
        self.youtube_repo = youtube_repo
        self.llm_repo = llm_repo

    async def answer_question(
        self, 
        question: str, 
        playlist_url: str,
        max_videos: Optional[int] = 10
    ) -> QAResponse:
        """Answer a question about the playlist content."""
        try:
            logger.info(f"Processing question: {question}")
            
            # Get playlist information
            playlist = await self.youtube_repo.get_playlist(playlist_url)
            logger.info(f"Loaded playlist: {playlist.title} ({playlist.video_count} videos)")
            
            # Get videos with metadata
            videos = await self.youtube_repo.get_playlist_videos(
                playlist_url, 
                max_results=max_videos
            )
            logger.info(f"Analyzing {len(videos)} videos")
            
            # Build context from available video data
            context = self._build_context(playlist, videos)
            
            # Generate answer using LLM
            answer = await self.llm_repo.generate_response(
                prompt=question,
                context=context,
                max_tokens=300
            )
            
            # Build source references
            sources = [f"{video.title} (Published: {video.published_at.strftime('%Y-%m-%d')})" 
                      for video in videos[:5]]  # Top 5 as sources
            
            logger.info(f"Generated answer: {len(answer)} characters")
            
            return QAResponse(
                answer=answer.strip(),
                sources=sources,
                confidence=0.8  # Base confidence for video metadata
            )
            
        except Exception as e:
            logger.error(f"Error processing question: {e}")
            return QAResponse(
                answer=f"I encountered an error while processing your question: {str(e)}",
                sources=[],
                confidence=0.0
            )

    def _build_context(self, playlist: Playlist, videos: List[Video]) -> str:
        """Build context string from playlist and video data."""
        context_parts = []
        
        # Playlist overview
        context_parts.append(f"PLAYLIST INFORMATION:")
        context_parts.append(f"Title: {playlist.title}")
        context_parts.append(f"Channel: {playlist.channel_title}")
        context_parts.append(f"Total Videos: {playlist.video_count}")
        context_parts.append(f"Description: {playlist.description}")
        context_parts.append("")
        
        # Video information
        context_parts.append(f"VIDEOS IN PLAYLIST (showing first {len(videos)}):")
        for i, video in enumerate(videos, 1):
            context_parts.append(f"{i}. {video.title}")
            context_parts.append(f"   Published: {video.published_at.strftime('%Y-%m-%d')}")
            context_parts.append(f"   Channel: {video.channel_title}")
            
            if video.description and len(video.description.strip()) > 0:
                # Truncate long descriptions
                desc = video.description[:200] + "..." if len(video.description) > 200 else video.description
                context_parts.append(f"   Description: {desc}")
            
            context_parts.append("")
        
        return "\n".join(context_parts)

    async def get_playlist_summary(self, playlist_url: str) -> QAResponse:
        """Get a summary of the playlist content."""
        summary_question = (
            "Please provide a summary of this YouTube playlist. "
            "What type of content is it? What can viewers expect? "
            "Mention key themes, the creator, and overall style."
        )
        
        return await self.answer_question(summary_question, playlist_url)

    async def search_videos(
        self, 
        query: str, 
        playlist_url: str,
        max_results: int = 5
    ) -> List[Video]:
        """Search for videos in the playlist that match a query."""
        try:
            videos = await self.youtube_repo.get_playlist_videos(playlist_url)
            
            # Simple text matching for now
            query_lower = query.lower()
            matching_videos = []
            
            for video in videos:
                title_match = query_lower in video.title.lower()
                desc_match = query_lower in video.description.lower() if video.description else False
                
                if title_match or desc_match:
                    matching_videos.append(video)
                
                if len(matching_videos) >= max_results:
                    break
            
            return matching_videos
            
        except Exception as e:
            logger.error(f"Error searching videos: {e}")
            return []