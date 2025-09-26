"""
YouTube video download and processing module.
Downloads video/audio from YouTube URLs using yt-dlp.
"""

import os
import yt_dlp
import tempfile
from pathlib import Path
from typing import Tuple, Dict, Any
import logging

logger = logging.getLogger(__name__)


class YouTubeDownloader:
    """Handle YouTube video downloads with yt-dlp."""
    
    def __init__(self, output_dir: str = "temp_downloads"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
    def download_video(self, youtube_url: str) -> Tuple[str, str, Dict[str, Any]]:
        """
        Download video and audio from YouTube URL.
        
        Args:
            youtube_url: YouTube video URL
            
        Returns:
            Tuple of (video_path, audio_path, metadata)
        """
        try:
            # Create temporary directory for this download
            temp_dir = tempfile.mkdtemp(dir=self.output_dir)
            
            # Configure yt-dlp options
            ydl_opts = {
                'format': 'best[height<=1080]',  # Limit to 1080p for processing efficiency
                'outtmpl': os.path.join(temp_dir, '%(title)s.%(ext)s'),
                'writesubtitles': True,
                'writeautomaticsub': True,
                'subtitleslangs': ['en'],
                'extractflat': False,
                'writethumbnail': True,
            }
            
            # Download video
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(youtube_url, download=True)
                video_path = ydl.prepare_filename(info)
                
            # Download audio separately for better quality transcription
            audio_opts = {
                'format': 'bestaudio/best',
                'outtmpl': os.path.join(temp_dir, '%(title)s_audio.%(ext)s'),
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'wav',
                    'preferredquality': '192',
                }],
            }
            
            with yt_dlp.YoutubeDL(audio_opts) as ydl:
                ydl.download([youtube_url])
                # Find the audio file
                audio_files = list(Path(temp_dir).glob("*_audio.wav"))
                audio_path = str(audio_files[0]) if audio_files else None
                
            # Extract metadata
            metadata = {
                'video_id': info.get('id'),
                'title': info.get('title'),
                'duration': info.get('duration'),
                'uploader': info.get('uploader'),
                'upload_date': info.get('upload_date'),
                'view_count': info.get('view_count'),
                'description': info.get('description', ''),
                'tags': info.get('tags', []),
                'thumbnail': info.get('thumbnail'),
                'webpage_url': info.get('webpage_url'),
            }
            
            logger.info(f"Successfully downloaded: {metadata['title']}")
            logger.info(f"Video: {video_path}")
            logger.info(f"Audio: {audio_path}")
            
            return video_path, audio_path, metadata
            
        except Exception as e:
            logger.error(f"Error downloading YouTube video: {e}")
            raise
    
    def cleanup_temp_files(self, video_path: str, audio_path: str):
        """Clean up temporary downloaded files."""
        try:
            if video_path and os.path.exists(video_path):
                os.remove(video_path)
            if audio_path and os.path.exists(audio_path):
                os.remove(audio_path)
            
            # Remove parent directory if empty
            parent_dir = Path(video_path).parent if video_path else None
            if parent_dir and parent_dir.exists() and not any(parent_dir.iterdir()):
                parent_dir.rmdir()
                
        except Exception as e:
            logger.warning(f"Error cleaning up temp files: {e}")
    
    def get_video_info(self, youtube_url: str) -> Dict[str, Any]:
        """
        Get video information without downloading.
        
        Args:
            youtube_url: YouTube video URL
            
        Returns:
            Video metadata dictionary
        """
        try:
            ydl_opts = {
                'quiet': True,
                'no_warnings': True,
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(youtube_url, download=False)
                
            return {
                'video_id': info.get('id'),
                'title': info.get('title'),
                'duration': info.get('duration'),
                'uploader': info.get('uploader'),
                'upload_date': info.get('upload_date'),
                'view_count': info.get('view_count'),
                'description': info.get('description', ''),
                'tags': info.get('tags', []),
                'thumbnail': info.get('thumbnail'),
                'webpage_url': info.get('webpage_url'),
            }
            
        except Exception as e:
            logger.error(f"Error extracting video info: {e}")
            raise


def extract_video_id(youtube_url: str) -> str:
    """Extract video ID from YouTube URL."""
    import re
    
    patterns = [
        r'(?:youtube\.com\/watch\?v=|youtu\.be\/|youtube\.com\/embed\/)([^&\n?#]+)',
        r'youtube\.com\/v\/([^&\n?#]+)',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, youtube_url)
        if match:
            return match.group(1)
    
    raise ValueError(f"Could not extract video ID from URL: {youtube_url}")


if __name__ == "__main__":
    # Test the downloader
    downloader = YouTubeDownloader()
    
    # Test URL (Rick Roll for testing)
    test_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    
    try:
        video_path, audio_path, metadata = downloader.download_video(test_url)
        print(f"Downloaded: {metadata['title']}")
        print(f"Duration: {metadata['duration']} seconds")
        
        # Clean up
        downloader.cleanup_temp_files(video_path, audio_path)
        
    except Exception as e:
        print(f"Error: {e}")
