import subprocess
import json
import tempfile
from pathlib import Path
from typing import Optional
from loguru import logger


class TranscriptExtractor:
    """Alternative transcript extractor using yt-dlp."""

    @staticmethod
    async def extract_transcript(video_id: str) -> Optional[str]:
        """Extract transcript using yt-dlp as fallback method."""
        try:
            video_url = f"https://www.youtube.com/watch?v={video_id}"
            
            # Use yt-dlp to extract subtitle information
            cmd = [
                "yt-dlp",
                "--write-auto-subs",
                "--write-subs", 
                "--sub-langs", "en",
                "--skip-download",
                "--output", "%(id)s.%(ext)s",
                video_url
            ]
            
            # Run yt-dlp in a temporary directory
            with tempfile.TemporaryDirectory() as temp_dir:
                temp_path = Path(temp_dir)
                
                result = subprocess.run(
                    cmd,
                    cwd=temp_path,
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                
                if result.returncode != 0:
                    logger.warning(f"yt-dlp failed for {video_id}: {result.stderr}")
                    return None
                
                # Look for subtitle files
                subtitle_files = list(temp_path.glob(f"{video_id}*.vtt"))
                if not subtitle_files:
                    subtitle_files = list(temp_path.glob(f"{video_id}*.srt"))
                
                if not subtitle_files:
                    logger.info(f"No subtitle files found for {video_id}")
                    return None
                
                # Read the subtitle file
                subtitle_file = subtitle_files[0]
                with open(subtitle_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Parse VTT or SRT format to extract text
                return TranscriptExtractor._parse_subtitle_content(content)
                
        except subprocess.TimeoutExpired:
            logger.warning(f"yt-dlp timeout for video {video_id}")
            return None
        except Exception as e:
            logger.warning(f"Error extracting transcript with yt-dlp for {video_id}: {e}")
            return None

    @staticmethod
    def _parse_subtitle_content(content: str) -> str:
        """Parse VTT or SRT subtitle content to extract plain text."""
        lines = content.split('\n')
        text_lines = []
        
        for line in lines:
            line = line.strip()
            # Skip empty lines, timestamps, and VTT headers
            if (not line or 
                line.startswith('WEBVTT') or 
                '-->' in line or 
                line.isdigit() or
                line.startswith('NOTE') or
                line.startswith('<')):
                continue
            
            # Remove VTT styling tags
            import re
            line = re.sub(r'<[^>]+>', '', line)
            
            if line:
                text_lines.append(line)
        
        return ' '.join(text_lines)