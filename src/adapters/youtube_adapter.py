import re
from datetime import datetime
from typing import List, Optional

from googleapiclient.discovery import build
from loguru import logger
from pytube import YouTube as PyTube
from youtube_transcript_api import YouTubeTranscriptApi

from src.core.models import Playlist, Video, Channel
from src.interfaces.youtube_repository import YouTubeRepository
from src.adapters.transcript_extractor import TranscriptExtractor


class YouTubeAPIAdapter(YouTubeRepository):
    """Concrete implementation of YouTube repository using YouTube API v3."""

    def __init__(self, api_key: Optional[str] = None):
        self._api_key = api_key
        self._youtube = None
        if api_key:
            self._youtube = build("youtube", "v3", developerKey=api_key)
    
    def _parse_datetime(self, date_string: str) -> datetime:
        """Parse YouTube datetime strings with various formats."""
        if not date_string:
            return datetime.now()
        
        # Handle different datetime formats from YouTube API
        try:
            # Try standard ISO format with Z
            if date_string.endswith('Z'):
                return datetime.fromisoformat(date_string.replace('Z', '+00:00'))
            # Try with microseconds that might have extra digits
            elif '+' in date_string and '.' in date_string:
                # Split into main part and timezone
                main_part, tz_part = date_string.rsplit('+', 1)
                # Ensure microseconds are exactly 6 digits
                if '.' in main_part:
                    date_part, micro_part = main_part.rsplit('.', 1)
                    micro_part = micro_part[:6].ljust(6, '0')  # Pad or truncate to 6 digits
                    normalized = f"{date_part}.{micro_part}+{tz_part}"
                    return datetime.fromisoformat(normalized)
            # Try standard ISO format
            return datetime.fromisoformat(date_string)
        except Exception as e:
            logger.warning(f"Failed to parse datetime '{date_string}': {e}, using current time")
            return datetime.now()

    def extract_playlist_id(self, url: str) -> str:
        """Extract playlist ID from YouTube URL."""
        match = re.search(r"list=([a-zA-Z0-9_-]+)", url)
        if match:
            return match.group(1)
        raise ValueError(f"Invalid YouTube playlist URL: {url}")

    def extract_channel_id(self, url: str) -> str:
        """Extract channel ID or handle from YouTube URL."""
        logger.info(f"Extracting channel ID from URL: {url}")
        
        # Handle different channel URL formats
        patterns = [
            r"youtube\.com/channel/([a-zA-Z0-9_-]+)",  # /channel/UCxxxxx
            r"youtube\.com/c/([a-zA-Z0-9_-]+)",        # /c/channelname
            r"youtube\.com/user/([a-zA-Z0-9_-]+)",     # /user/username
            r"youtube\.com/@([a-zA-Z0-9_-]+)",         # /@handle
            r"youtube\.com/([a-zA-Z0-9_-]+)/?$"        # /channelname (end of string)
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                extracted = match.group(1)
                logger.info(f"Pattern '{pattern}' matched, extracted: '{extracted}'")
                return extracted
        
        logger.error(f"No pattern matched for URL: {url}")
        raise ValueError(f"Invalid YouTube channel URL: {url}")

    def is_channel_url(self, url: str) -> bool:
        """Check if URL is a channel URL."""
        channel_patterns = [
            r"youtube\.com/channel/",
            r"youtube\.com/c/",
            r"youtube\.com/user/",
            r"youtube\.com/@",
            r"youtube\.com/[^/]+$"  # Handle direct channel names like youtube.com/sidemen
        ]
        return any(re.search(pattern, url) for pattern in channel_patterns)

    def is_playlist_url(self, url: str) -> bool:
        """Check if URL is a playlist URL."""
        return "list=" in url

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
                published_at=self._parse_datetime(snippet["publishedAt"]),
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
                        published_at=self._parse_datetime(snippet["publishedAt"]),
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
            
            # Sort videos by publication date (newest first)
            videos.sort(key=lambda v: v.published_at, reverse=True)
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

        # Final sort by publication date (newest first) and apply limit if specified
        videos.sort(key=lambda v: v.published_at, reverse=True)
        
        if max_results:
            videos = videos[:max_results]
            
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
                published_at=self._parse_datetime(snippet["publishedAt"]),
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

    async def get_channel(self, channel_url_or_id: str) -> Channel:
        """Fetch channel metadata from YouTube."""
        if not self._youtube:
            raise ValueError("YouTube API key required for channel operations")

        logger.info(f"Getting channel info for: {channel_url_or_id}")
        
        channel_identifier = (
            channel_url_or_id
            if not channel_url_or_id.startswith("http")
            else self.extract_channel_id(channel_url_or_id)
        )
        
        logger.info(f"Extracted channel identifier: {channel_identifier}")

        # Try different methods to get channel info
        response = None
        
        # Method 1: Try as channel ID (UCxxxxx format)
        if channel_identifier.startswith("UC"):
            try:
                response = self._youtube.channels().list(
                    part="snippet,statistics,contentDetails",
                    id=channel_identifier
                ).execute()
            except Exception:
                pass

        # Method 2: Try as username (forUsername instead of forHandle)
        if not response or not response.get("items"):
            try:
                username = channel_identifier.replace("@", "")  # Remove @ if present
                logger.info(f"Trying forUsername lookup with: {username}")
                response = self._youtube.channels().list(
                    part="snippet,statistics,contentDetails",
                    forUsername=username
                ).execute()
                logger.info(f"ForUsername response: {response.get('items', [])}")
            except Exception as e:
                logger.warning(f"ForUsername lookup failed: {e}")
                pass

        # Method 3: Try searching by name
        if not response or not response.get("items"):
            try:
                search_response = self._youtube.search().list(
                    part="snippet",
                    q=channel_identifier,
                    type="channel",
                    maxResults=1
                ).execute()
                
                if search_response.get("items"):
                    channel_id = search_response["items"][0]["snippet"]["channelId"]
                    response = self._youtube.channels().list(
                        part="snippet,statistics,contentDetails",
                        id=channel_id
                    ).execute()
            except Exception:
                pass

        if not response or not response.get("items"):
            raise ValueError(f"Channel not found: {channel_identifier}")

        item = response["items"][0]
        snippet = item["snippet"]
        statistics = item.get("statistics", {})
        
        # Get playlist count from contentDetails
        content_details = item.get("contentDetails", {})
        related_playlists = content_details.get("relatedPlaylists", {})
        
        # YouTube API doesn't directly provide playlist count, so we'll leave it as None
        # and fetch it separately if needed
        
        return Channel(
            channel_id=item["id"],
            title=snippet["title"],
            description=snippet.get("description", ""),
            subscriber_count=int(statistics.get("subscriberCount", 0)) if statistics.get("subscriberCount") else None,
            video_count=int(statistics.get("videoCount", 0)) if statistics.get("videoCount") else None,
            playlist_count=None,  # Will be fetched separately if needed
            published_at=self._parse_datetime(snippet["publishedAt"]) if snippet.get("publishedAt") else None,
            thumbnail_url=snippet.get("thumbnails", {}).get("medium", {}).get("url"),
            custom_url=snippet.get("customUrl")
        )

    async def get_channel_playlists(self, channel_url_or_id: str, max_results: Optional[int] = None) -> List[Playlist]:
        """Fetch playlists from a channel with limits to prevent timeouts."""
        if not self._youtube:
            raise ValueError("YouTube API key required for channel operations")

        # First get the channel to get its ID
        channel = await self.get_channel(channel_url_or_id)
        channel_id = channel.channel_id

        playlists = []
        next_page_token = None
        max_pages = 10  # Increased limit to 10 pages (500 playlists max)
        pages_fetched = 0

        logger.info(f"Fetching playlists for channel {channel_id}, max_results: {max_results}")

        while pages_fetched < max_pages:
            try:
                response = self._youtube.playlists().list(
                    part="snippet,contentDetails",
                    channelId=channel_id,
                    maxResults=50,  # API limit per page
                    pageToken=next_page_token,
                ).execute()

                pages_fetched += 1
                logger.info(f"Fetched page {pages_fetched}, got {len(response.get('items', []))} playlists")

                for i, item in enumerate(response.get("items", [])):
                    try:
                        snippet = item["snippet"]
                        
                        playlist = Playlist(
                            playlist_id=item["id"],
                            title=snippet["title"],
                            description=snippet.get("description", ""),
                            channel_title=snippet["channelTitle"],
                            video_count=item["contentDetails"]["itemCount"],
                            published_at=self._parse_datetime(snippet["publishedAt"]),
                        )
                        playlists.append(playlist)
                        logger.debug(f"Successfully processed playlist {i+1}: {playlist.title}")
                    except Exception as e:
                        logger.error(f"Error processing playlist item {i+1}: {e}")
                        logger.error(f"Item data: {item}")
                        continue

                    # Stop if we've reached max_results
                    if max_results and len(playlists) >= max_results:
                        logger.info(f"Reached max_results limit: {max_results}")
                        playlists = playlists[:max_results]
                        break

                # Stop if we've reached max_results
                if max_results and len(playlists) >= max_results:
                    break

                next_page_token = response.get("nextPageToken")
                if not next_page_token:
                    logger.info("No more pages available")
                    break

            except Exception as e:
                logger.error(f"Error fetching playlists page {pages_fetched}: {e}")
                # Don't break on error - we've already processed some playlists
                logger.info(f"Continuing with {len(playlists)} playlists collected so far")
                break

        # Sort playlists by creation date (newest first)
        try:
            playlists.sort(key=lambda p: p.published_at, reverse=True)
        except Exception as e:
            logger.warning(f"Error sorting playlists by date: {e}, returning unsorted")
        
        logger.info(f"Returning {len(playlists)} playlists")
        return playlists

    async def search_channel_videos(
        self, 
        channel_url_or_id: str, 
        query: str,
        max_results: Optional[int] = None,
        include_transcripts: bool = True
    ) -> List[Video]:
        """Search for videos in a channel that match a query."""
        if not self._youtube:
            raise ValueError("YouTube API key required for channel operations")

        # Get channel ID
        channel = await self.get_channel(channel_url_or_id)
        channel_id = channel.channel_id

        videos = []
        next_page_token = None

        while True:
            response = self._youtube.search().list(
                part="snippet",
                channelId=channel_id,
                q=query,
                type="video",
                maxResults=50,  # API limit
                pageToken=next_page_token,
                order="relevance"  # Most relevant first
            ).execute()

            for item in response.get("items", []):
                try:
                    snippet = item["snippet"]
                    # Handle different response formats
                    logger.debug(f"Processing search item: {item.get('id')}")
                    if isinstance(item["id"], dict):
                        video_id = item["id"]["videoId"]
                    else:
                        video_id = item["id"]
                    
                    logger.debug(f"Extracted video_id: {video_id}")
                except Exception as e:
                    logger.error(f"Error processing search item: {item}, error: {e}")
                    continue
                
                video = Video(
                    video_id=video_id,
                    title=snippet["title"],
                    description=snippet.get("description", ""),
                    channel_title=snippet["channelTitle"],
                    published_at=self._parse_datetime(snippet["publishedAt"]),
                    thumbnail_url=snippet.get("thumbnails", {}).get("medium", {}).get("url"),
                )

                # Optionally include transcript
                if include_transcripts:
                    try:
                        transcript = await self.get_video_transcript(video_id)
                        if transcript:
                            # Create new video with transcript
                            video = Video(
                                video_id=video.video_id,
                                title=video.title,
                                description=video.description,
                                channel_title=video.channel_title,
                                published_at=video.published_at,
                                duration=video.duration,
                                thumbnail_url=video.thumbnail_url,
                                transcript=transcript
                            )
                    except Exception as e:
                        logger.warning(f"Could not get transcript for {video_id}: {e}")

                videos.append(video)

                if max_results and len(videos) >= max_results:
                    return videos[:max_results]

            next_page_token = response.get("nextPageToken")
            if not next_page_token:
                break

        # Sort by publication date (newest first)
        videos.sort(key=lambda v: v.published_at, reverse=True)
        return videos