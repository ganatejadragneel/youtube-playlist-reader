from typing import List, Optional
from dataclasses import dataclass

from loguru import logger

from src.core.models import Video, Playlist, Channel
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
        youtube_url: str,
        max_videos: Optional[int] = None
    ) -> QAResponse:
        """Answer a question about the playlist or channel content."""
        try:
            logger.info(f"Processing question: {question}")
            
            # Determine if it's a playlist or channel URL
            if self.youtube_repo.is_playlist_url(youtube_url):
                # Handle playlist
                playlist = await self.youtube_repo.get_playlist(youtube_url)
                logger.info(f"Loaded playlist: {playlist.title} ({playlist.video_count} videos)")
                
                # Get ALL videos with metadata for comprehensive analysis
                videos = await self.youtube_repo.get_playlist_videos(
                    youtube_url, 
                    max_results=max_videos  # None means get all videos
                )
                logger.info(f"Analyzing {len(videos)} videos (all videos in playlist)")
                
                # Build context from available video data
                context = self._build_playlist_context(playlist, videos)
            else:
                # Handle channel
                channel = await self.youtube_repo.get_channel(youtube_url)
                logger.info(f"Loaded channel: {channel.title} ({channel.video_count} videos)")
                
                # Search for videos related to the question in the channel
                videos = await self.youtube_repo.search_channel_videos(
                    youtube_url,
                    query=question,  # Use the question as search query
                    max_results=max_videos or 20,  # Limit for channel searches
                    include_transcripts=True
                )
                logger.info(f"Analyzing {len(videos)} relevant videos from channel")
                
                # Build context from channel and video data
                context = self._build_channel_context(channel, videos, question)
            
            # Generate answer using LLM
            answer = await self.llm_repo.generate_response(
                prompt=question,
                context=context,
                max_tokens=300
            )
            
            # Build source references from all videos
            sources = [f"{video.title} (Published: {video.published_at.strftime('%Y-%m-%d')})" 
                      for video in videos[:10]]  # Top 10 as sources for better context
            
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

    def _build_playlist_context(self, playlist: Playlist, videos: List[Video]) -> str:
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

    def _build_channel_context(self, channel: Channel, videos: List[Video], question: str) -> str:
        """Build context string from channel and video data."""
        context_parts = []
        
        # Channel overview
        context_parts.append(f"CHANNEL INFORMATION:")
        context_parts.append(f"Title: {channel.title}")
        context_parts.append(f"Description: {channel.description}")
        context_parts.append(f"Total Videos: {channel.video_count}")
        context_parts.append(f"Subscribers: {channel.subscriber_count}")
        context_parts.append("")
        
        # Relevant videos found for the question
        context_parts.append(f"RELEVANT VIDEOS FOR QUESTION '{question}' (showing {len(videos)} most relevant):")
        for i, video in enumerate(videos, 1):
            context_parts.append(f"{i}. {video.title}")
            context_parts.append(f"   Published: {video.published_at.strftime('%Y-%m-%d')}")
            
            if video.description and len(video.description.strip()) > 0:
                # Truncate long descriptions
                desc = video.description[:200] + "..." if len(video.description) > 200 else video.description
                context_parts.append(f"   Description: {desc}")
            
            # Include transcript if available
            if video.transcript and len(video.transcript.strip()) > 0:
                # Truncate long transcripts but include more than description
                transcript = video.transcript[:500] + "..." if len(video.transcript) > 500 else video.transcript
                context_parts.append(f"   Transcript: {transcript}")
            
            context_parts.append("")
        
        return "\n".join(context_parts)

    async def get_summary(self, youtube_url: str) -> QAResponse:
        """Get a summary of the playlist or channel content."""
        if self.youtube_repo.is_playlist_url(youtube_url):
            summary_question = (
                "Please provide a summary of this YouTube playlist. "
                "What type of content is it? What can viewers expect? "
                "Mention key themes, the creator, and overall style."
            )
        else:
            summary_question = (
                "Please provide a summary of this YouTube channel. "
                "What type of content does it create? What can viewers expect? "
                "Mention key themes, the creator's style, and main topics covered."
            )
        
        return await self.answer_question(summary_question, youtube_url)

    async def search_videos(
        self, 
        query: str, 
        youtube_url: str,
        max_results: Optional[int] = None
    ) -> List[Video]:
        """Search for videos in the playlist or channel that match a query."""
        try:
            if self.youtube_repo.is_playlist_url(youtube_url):
                # Get ALL videos from playlist for comprehensive search
                videos = await self.youtube_repo.get_playlist_videos(youtube_url)
                
                # Simple text matching for playlists
                query_lower = query.lower()
                matching_videos = []
                
                for video in videos:
                    title_match = query_lower in video.title.lower()
                    desc_match = query_lower in video.description.lower() if video.description else False
                    
                    if title_match or desc_match:
                        matching_videos.append(video)
                
                # Sort by publication date (newest first)
                matching_videos.sort(key=lambda v: v.published_at, reverse=True)
                
                # Apply limit if specified
                if max_results:
                    matching_videos = matching_videos[:max_results]
                
                logger.info(f"Found {len(matching_videos)} videos matching '{query}' out of {len(videos)} total videos in playlist")
                return matching_videos
            else:
                # For channels, use YouTube's search API
                videos = await self.youtube_repo.search_channel_videos(
                    youtube_url,
                    query=query,
                    max_results=max_results,
                    include_transcripts=False  # Don't include transcripts for search results
                )
                
                logger.info(f"Found {len(videos)} videos matching '{query}' in channel")
                return videos
            
        except Exception as e:
            logger.error(f"Error searching videos: {e}")
            return []