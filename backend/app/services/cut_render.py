"""
Video cutting and rendering with NVENC acceleration.
Handles ffmpeg operations for extracting clips and adding captions.
"""

import os
import subprocess
import tempfile
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import json
import cv2

from .windows import VideoWindow

logger = logging.getLogger(__name__)


class VideoRenderer:
    """Handle video cutting and rendering with ffmpeg."""
    
    def __init__(self, output_dir: str = "rendered_clips"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        # Check for NVENC support
        self.has_nvenc = self._check_nvenc_support()
        logger.info(f"NVENC support: {'Available' if self.has_nvenc else 'Not available'}")
    
    def _check_nvenc_support(self) -> bool:
        """Check if NVENC hardware encoding is available."""
        try:
            result = subprocess.run(
                ['ffmpeg', '-hide_banner', '-encoders'],
                capture_output=True,
                text=True,
                timeout=10
            )
            return 'h264_nvenc' in result.stdout
        except Exception as e:
            logger.warning(f"Could not check NVENC support: {e}")
            return False
    
    def extract_clip(
        self, 
        video_path: str, 
        start_time: float, 
        end_time: float, 
        output_path: str,
        crop_to_shorts: bool = True,
        quality: str = "high"
    ) -> str:
        """
        Extract video clip using ffmpeg with optional cropping.
        
        Args:
            video_path: Path to source video
            start_time: Start time in seconds
            end_time: End time in seconds
            output_path: Output file path
            crop_to_shorts: Whether to crop to 9:16 aspect ratio
            quality: Quality preset ("high", "medium", "fast")
            
        Returns:
            Path to extracted clip
        """
        try:
            # Build ffmpeg command
            cmd = ['ffmpeg', '-y', '-hide_banner', '-loglevel', 'warning']
            
            # Input
            cmd.extend(['-ss', str(start_time), '-i', video_path])
            cmd.extend(['-t', str(end_time - start_time)])
            
            # Video encoding
            if self.has_nvenc:
                cmd.extend(['-c:v', 'h264_nvenc'])
                if quality == "high":
                    cmd.extend(['-preset', 'slow', '-cq', '18'])
                elif quality == "medium":
                    cmd.extend(['-preset', 'medium', '-cq', '23'])
                else:  # fast
                    cmd.extend(['-preset', 'fast', '-cq', '28'])
            else:
                cmd.extend(['-c:v', 'libx264'])
                if quality == "high":
                    cmd.extend(['-preset', 'slow', '-crf', '18'])
                elif quality == "medium":
                    cmd.extend(['-preset', 'medium', '-crf', '23'])
                else:  # fast
                    cmd.extend(['-preset', 'fast', '-crf', '28'])
            
            # Audio encoding
            cmd.extend(['-c:a', 'aac', '-b:a', '128k'])
            
            # Cropping for shorts format
            if crop_to_shorts:
                crop_filter = self._get_shorts_crop_filter(video_path)
                if crop_filter:
                    cmd.extend(['-vf', crop_filter])
            
            # Output
            cmd.append(output_path)
            
            # Execute ffmpeg
            logger.info(f"Extracting clip: {start_time:.1f}s - {end_time:.1f}s")
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            
            if result.returncode != 0:
                logger.error(f"ffmpeg error: {result.stderr}")
                raise Exception(f"ffmpeg failed: {result.stderr}")
            
            logger.info(f"Clip extracted successfully: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Error extracting clip: {e}")
            raise
    
    def _get_shorts_crop_filter(self, video_path: str) -> Optional[str]:
        """
        Generate crop filter for 9:16 shorts format.
        
        Args:
            video_path: Path to video file
            
        Returns:
            ffmpeg crop filter string or None
        """
        try:
            # Get video dimensions
            cap = cv2.VideoCapture(video_path)
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            cap.release()
            
            if width == 0 or height == 0:
                logger.warning("Could not get video dimensions")
                return None
            
            # Calculate crop dimensions for 9:16 aspect ratio
            target_aspect = 9.0 / 16.0
            current_aspect = width / height
            
            if abs(current_aspect - target_aspect) < 0.01:
                # Already correct aspect ratio
                return None
            
            if current_aspect > target_aspect:
                # Video is wider, crop width
                new_width = int(height * target_aspect)
                x_offset = (width - new_width) // 2
                crop_filter = f"crop={new_width}:{height}:{x_offset}:0"
            else:
                # Video is taller, crop height
                new_height = int(width / target_aspect)
                y_offset = (height - new_height) // 2
                crop_filter = f"crop={width}:{new_height}:0:{y_offset}"
            
            # Scale to standard shorts resolution (1080x1920)
            crop_filter += ",scale=1080:1920"
            
            return crop_filter
            
        except Exception as e:
            logger.error(f"Error calculating crop filter: {e}")
            return None
    
    def add_captions_to_video(
        self, 
        video_path: str, 
        captions: List[Dict[str, Any]], 
        output_path: str,
        style: Dict[str, Any] = None
    ) -> str:
        """
        Add burned-in captions to video.
        
        Args:
            video_path: Path to input video
            captions: List of caption dictionaries with text, start, end
            output_path: Output file path
            style: Caption styling options
            
        Returns:
            Path to video with captions
        """
        if not captions:
            # No captions, just copy the video
            import shutil
            shutil.copy2(video_path, output_path)
            return output_path
        
        try:
            # Default caption style
            default_style = {
                'font': 'Arial',
                'fontsize': 48,
                'fontcolor': 'white',
                'box': 1,
                'boxcolor': 'black@0.5',
                'boxborderw': 5,
                'x': '(w-text_w)/2',  # Center horizontally
                'y': 'h-th-50'  # Near bottom
            }
            
            if style:
                default_style.update(style)
            
            # Create subtitle file
            srt_path = self._create_srt_file(captions)
            
            # Build ffmpeg command
            cmd = ['ffmpeg', '-y', '-hide_banner', '-loglevel', 'warning']
            cmd.extend(['-i', video_path])
            
            # Subtitle filter
            subtitle_filter = (
                f"subtitles={srt_path}:force_style='"
                f"FontName={default_style['font']},"
                f"FontSize={default_style['fontsize']},"
                f"PrimaryColour=&H{self._color_to_hex(default_style['fontcolor'])},"
                f"BackColour=&H{self._color_to_hex(default_style['boxcolor'])},"
                f"Bold=1,Alignment=2'"
            )
            
            cmd.extend(['-vf', subtitle_filter])
            
            # Video encoding (same as extract_clip)
            if self.has_nvenc:
                cmd.extend(['-c:v', 'h264_nvenc', '-preset', 'medium', '-cq', '23'])
            else:
                cmd.extend(['-c:v', 'libx264', '-preset', 'medium', '-crf', '23'])
            
            cmd.extend(['-c:a', 'copy'])  # Copy audio without re-encoding
            cmd.append(output_path)
            
            # Execute ffmpeg
            logger.info(f"Adding captions to video: {len(captions)} captions")
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
            
            if result.returncode != 0:
                logger.error(f"ffmpeg caption error: {result.stderr}")
                raise Exception(f"ffmpeg caption failed: {result.stderr}")
            
            # Clean up temporary SRT file
            os.unlink(srt_path)
            
            logger.info(f"Captions added successfully: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Error adding captions: {e}")
            raise
    
    def _create_srt_file(self, captions: List[Dict[str, Any]]) -> str:
        """Create SRT subtitle file from captions."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.srt', delete=False) as f:
            for i, caption in enumerate(captions, 1):
                start_time = self._seconds_to_srt_time(caption['start'])
                end_time = self._seconds_to_srt_time(caption['end'])
                text = caption['text'].strip()
                
                f.write(f"{i}\n")
                f.write(f"{start_time} --> {end_time}\n")
                f.write(f"{text}\n\n")
            
            return f.name
    
    def _seconds_to_srt_time(self, seconds: float) -> str:
        """Convert seconds to SRT time format (HH:MM:SS,mmm)."""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millisecs = int((seconds % 1) * 1000)
        
        return f"{hours:02d}:{minutes:02d}:{secs:02d},{millisecs:03d}"
    
    def _color_to_hex(self, color: str) -> str:
        """Convert color name to hex for ffmpeg."""
        color_map = {
            'white': 'FFFFFF',
            'black': '000000',
            'red': 'FF0000',
            'green': '00FF00',
            'blue': '0000FF',
            'yellow': 'FFFF00',
            'cyan': '00FFFF',
            'magenta': 'FF00FF'
        }
        
        if color.startswith('#'):
            return color[1:]
        
        return color_map.get(color.lower(), 'FFFFFF')
    
    def render_clip_with_captions(
        self, 
        video_path: str, 
        window: VideoWindow, 
        transcript_segments: List[Dict[str, Any]],
        output_filename: str = None
    ) -> str:
        """
        Complete pipeline: extract clip and add captions.
        
        Args:
            video_path: Path to source video
            window: VideoWindow object with timing
            transcript_segments: Transcript segments for captions
            output_filename: Custom output filename
            
        Returns:
            Path to final rendered clip
        """
        try:
            # Generate output filename
            if not output_filename:
                output_filename = f"{window.window_id}_clip.mp4"
            
            temp_clip_path = self.output_dir / f"temp_{output_filename}"
            final_clip_path = self.output_dir / output_filename
            
            # Step 1: Extract clip
            self.extract_clip(
                video_path=video_path,
                start_time=window.start_time,
                end_time=window.end_time,
                output_path=str(temp_clip_path),
                crop_to_shorts=True
            )
            
            # Step 2: Prepare captions (adjust timing relative to clip start)
            captions = []
            for segment in transcript_segments:
                # Adjust timing relative to clip start
                caption_start = max(0, segment['start'] - window.start_time)
                caption_end = min(window.duration, segment['end'] - window.start_time)
                
                if caption_end > caption_start:
                    captions.append({
                        'text': segment['text'],
                        'start': caption_start,
                        'end': caption_end
                    })
            
            # Step 3: Add captions
            self.add_captions_to_video(
                video_path=str(temp_clip_path),
                captions=captions,
                output_path=str(final_clip_path)
            )
            
            # Clean up temporary file
            if temp_clip_path.exists():
                temp_clip_path.unlink()
            
            logger.info(f"Clip rendered successfully: {final_clip_path}")
            return str(final_clip_path)
            
        except Exception as e:
            logger.error(f"Error rendering clip: {e}")
            raise
    
    def get_video_info(self, video_path: str) -> Dict[str, Any]:
        """Get video information using ffprobe."""
        try:
            cmd = [
                'ffprobe', '-v', 'quiet', '-print_format', 'json',
                '-show_format', '-show_streams', video_path
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode != 0:
                raise Exception(f"ffprobe failed: {result.stderr}")
            
            info = json.loads(result.stdout)
            
            # Extract video stream info
            video_stream = None
            for stream in info['streams']:
                if stream['codec_type'] == 'video':
                    video_stream = stream
                    break
            
            if not video_stream:
                raise Exception("No video stream found")
            
            return {
                'duration': float(info['format']['duration']),
                'width': int(video_stream['width']),
                'height': int(video_stream['height']),
                'fps': eval(video_stream['r_frame_rate']),  # Fraction like "30/1"
                'codec': video_stream['codec_name'],
                'bitrate': int(info['format'].get('bit_rate', 0)),
                'size_bytes': int(info['format']['size'])
            }
            
        except Exception as e:
            logger.error(f"Error getting video info: {e}")
            raise


class ClipBatch:
    """Handle batch processing of multiple clips."""
    
    def __init__(self, renderer: VideoRenderer):
        self.renderer = renderer
    
    def render_top_clips(
        self, 
        video_path: str, 
        ranked_windows: List[Tuple[VideoWindow, Dict[str, Any]]],
        output_prefix: str = "clip"
    ) -> List[Dict[str, Any]]:
        """
        Render multiple top-ranked clips.
        
        Args:
            video_path: Path to source video
            ranked_windows: List of (window, scores) tuples
            output_prefix: Prefix for output filenames
            
        Returns:
            List of clip information dictionaries
        """
        rendered_clips = []
        
        for i, (window, scores) in enumerate(ranked_windows):
            try:
                # Generate filename
                filename = f"{output_prefix}_{i+1:02d}_{window.window_id}.mp4"
                
                # Render clip
                clip_path = self.renderer.render_clip_with_captions(
                    video_path=video_path,
                    window=window,
                    transcript_segments=window.transcript_segments,
                    output_filename=filename
                )
                
                # Collect clip info
                clip_info = {
                    'rank': i + 1,
                    'window_id': window.window_id,
                    'start_time': window.start_time,
                    'end_time': window.end_time,
                    'duration': window.duration,
                    'file_path': clip_path,
                    'filename': filename,
                    'score': scores['final_score'],
                    'components': scores['components'],
                    'text': scores['text']
                }
                
                rendered_clips.append(clip_info)
                logger.info(f"Rendered clip {i+1}: {filename} (score: {scores['final_score']:.3f})")
                
            except Exception as e:
                logger.error(f"Error rendering clip {i+1}: {e}")
                continue
        
        return rendered_clips


if __name__ == "__main__":
    # Test the renderer
    renderer = VideoRenderer()
    
    # Test with sample video (you'll need to provide this)
    test_video = "test_video.mp4"
    
    if Path(test_video).exists():
        try:
            # Get video info
            info = renderer.get_video_info(test_video)
            print(f"Video info: {info['width']}x{info['height']}, {info['duration']:.1f}s")
            
            # Test clip extraction
            test_window = VideoWindow(10.0, 100.0, "test_window")
            test_segments = [
                {'text': 'This is a test caption', 'start': 15.0, 'end': 20.0},
                {'text': 'Another test caption', 'start': 25.0, 'end': 30.0}
            ]
            
            output_path = renderer.render_clip_with_captions(
                video_path=test_video,
                window=test_window,
                transcript_segments=test_segments,
                output_filename="test_clip.mp4"
            )
            
            print(f"Test clip rendered: {output_path}")
            
        except Exception as e:
            print(f"Error: {e}")
    else:
        print(f"Test video file not found: {test_video}")
