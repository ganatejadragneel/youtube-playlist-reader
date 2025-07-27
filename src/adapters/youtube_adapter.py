import re
from datetime import datetime
from typing import List, Optional

from googleapiclient.discovery import build
from loguru import logger
from pytube import YouTube as PyTube
from youtube_transcript_api import YouTubeTranscriptApi

from src.core.models import Playlist, Video
from src.interfaces.youtube_repository import YouTubeRepository
from src.adapters.transcript_extractor import TranscriptExtractor


class YouTubeAPIAdapter(YouTubeRepository):
    """Concrete implementation of YouTube repository using YouTube API v3."""

    def __init__(self, api_key: Optional[str] = None):
        self._api_key = api_key
        self._youtube = None
        if api_key:
            self._youtube = build("youtube", "v3", developerKey=api_key)

    def extract_playlist_id(self, url: str) -> str:
        """Extract playlist ID from YouTube URL."""
        match = re.search(r"list=([a-zA-Z0-9_-]+)", url)
        if match:
            return match.group(1)
        raise ValueError(f"Invalid YouTube playlist URL: {url}")

    async def get_playlist(self, playlist_url_or_id: str) -> Playlist:
        """Fetch playlist metadata from YouTube."""
        playlist_id = (
            playlist_url_or_id
            if not playlist_url_or_id.startswith("http")
            else self.extract_playlist_id(playlist_url_or_id)
        )

        if self._youtube:
            response = self._youtube.playlists().list(
                part="snippet,contentDetails", id=playlist_id
            ).execute()

            if not response.get("items"):
                raise ValueError(f"Playlist not found: {playlist_id}")

            item = response["items"][0]
            snippet = item["snippet"]
            
            return Playlist(
                playlist_id=playlist_id,
                title=snippet["title"],
                description=snippet.get("description", ""),
                channel_title=snippet["channelTitle"],
                video_count=item["contentDetails"]["itemCount"],
                published_at=datetime.fromisoformat(
                    snippet["publishedAt"].replace("Z", "+00:00")
                ),
            )
        else:
            # Fallback approach without API key
            logger.warning("No API key provided, using limited functionality")
            # For now, return minimal data
            return Playlist(
                playlist_id=playlist_id,
                title=f"Playlist {playlist_id}",
                description="",
                channel_title="Unknown",
                video_count=0,
                published_at=datetime.now(),
            )

    async def get_playlist_videos(
        self, playlist_url_or_id: str, max_results: Optional[int] = None
    ) -> List[Video]:
        """Fetch all videos from a playlist."""
        playlist_id = (
            playlist_url_or_id
            if not playlist_url_or_id.startswith("http")
            else self.extract_playlist_id(playlist_url_or_id)
        )

        videos = []
        
        if self._youtube:
            next_page_token = None
            while True:
                response = self._youtube.playlistItems().list(
                    part="snippet,contentDetails",
                    playlistId=playlist_id,
                    maxResults=50,  # API limit
                    pageToken=next_page_token,
                ).execute()

                for item in response.get("items", []):
                    snippet = item["snippet"]
                    video_id = item["contentDetails"]["videoId"]
                    
                    video = Video(
                        video_id=video_id,
                        title=snippet["title"],
                        description=snippet.get("description", ""),
                        channel_title=snippet["channelTitle"],
                        published_at=datetime.fromisoformat(
                            snippet["publishedAt"].replace("Z", "+00:00")
                        ),
                        thumbnail_url=snippet.get("thumbnails", {})
                        .get("medium", {})
                        .get("url"),
                    )
                    videos.append(video)

                    if max_results and len(videos) >= max_results:
                        return videos[:max_results]

                next_page_token = response.get("nextPageToken")
                if not next_page_token:
                    break
        else:
            # Fallback: try to extract from playlist URL using pytube
            try:
                playlist_url = f"https://www.youtube.com/playlist?list={playlist_id}"
                from pytube import Playlist as PyTubePlaylist
                
                p = PyTubePlaylist(playlist_url)
                for url in p.video_urls[:max_results] if max_results else p.video_urls:
                    video_id = url.split("v=")[1].split("&")[0]
                    videos.append(
                        Video(
                            video_id=video_id,
                            title=f"Video {video_id}",
                            description="",
                            channel_title="Unknown",
                            published_at=datetime.now(),
                        )
                    )
            except Exception as e:
                logger.error(f"Error fetching playlist videos: {e}")

        return videos

    async def get_video_transcript(self, video_id: str) -> Optional[str]:
        """Fetch transcript for a specific video."""
        try:
            transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
            
            # Try different transcript sources in order of preference
            transcript = None
            
            # 1. Try manual English transcript
            try:
                transcript = transcript_list.find_manually_created_transcript(['en'])
                logger.info(f"Found manual English transcript for {video_id}")
            except:
                pass
            
            # 2. Try auto-generated English transcript
            if not transcript:
                try:
                    transcript = transcript_list.find_generated_transcript(['en'])
                    logger.info(f"Found auto-generated English transcript for {video_id}")
                except:
                    pass
            
            # 3. Try any available transcript in any language
            if not transcript:
                try:
                    available_transcripts = list(transcript_list)
                    if available_transcripts:
                        transcript = available_transcripts[0]
                        logger.info(f"Using transcript in {transcript.language} for {video_id}")
                except:
                    pass
            
            if not transcript:
                logger.warning(f"No transcripts available for video {video_id}")
                return None
            
            # Fetch transcript data with retry logic
            try:
                transcript_data = transcript.fetch()
                
                # Combine all text segments
                full_transcript = " ".join(
                    segment.get("text", "").strip() 
                    for segment in transcript_data 
                    if segment.get("text")
                )
                
                if full_transcript.strip():
                    logger.info(f"Successfully extracted transcript for {video_id}: {len(full_transcript)} characters")
                    return full_transcript
                else:
                    logger.warning(f"Empty transcript for video {video_id}")
                    return None
                    
            except Exception as fetch_error:
                logger.warning(f"Failed to fetch transcript data for {video_id}: {fetch_error}")
                # Try alternative method with yt-dlp
                logger.info(f"Trying alternative transcript extraction for {video_id}")
                return await TranscriptExtractor.extract_transcript(video_id)
                
        except Exception as e:
            logger.warning(f"Could not access transcripts for video {video_id}: {e}")
            # Try alternative method with yt-dlp as final fallback
            logger.info(f"Trying alternative transcript extraction for {video_id}")
            return await TranscriptExtractor.extract_transcript(video_id)

    async def get_video_details(self, video_id: str) -> Video:
        """Fetch detailed information about a specific video."""
        if self._youtube:
            response = self._youtube.videos().list(
                part="snippet,contentDetails", id=video_id
            ).execute()

            if not response.get("items"):
                raise ValueError(f"Video not found: {video_id}")

            item = response["items"][0]
            snippet = item["snippet"]
            
            return Video(
                video_id=video_id,
                title=snippet["title"],
                description=snippet.get("description", ""),
                channel_title=snippet["channelTitle"],
                published_at=datetime.fromisoformat(
                    snippet["publishedAt"].replace("Z", "+00:00")
                ),
                duration=item["contentDetails"]["duration"],
                thumbnail_url=snippet.get("thumbnails", {})
                .get("medium", {})
                .get("url"),
            )
        else:
            # Fallback using pytube
            try:
                yt = PyTube(f"https://www.youtube.com/watch?v={video_id}")
                return Video(
                    video_id=video_id,
                    title=yt.title,
                    description=yt.description or "",
                    channel_title=yt.author,
                    published_at=yt.publish_date or datetime.now(),
                    duration=f"PT{yt.length}S" if yt.length else None,
                    thumbnail_url=yt.thumbnail_url,
                )
            except Exception as e:
                logger.error(f"Error fetching video details: {e}")
                raise