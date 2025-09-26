"""
Video window generation with scene boundary detection.
Creates 90-second windows with 15-second stride, snapping to scene boundaries.
"""

import cv2
import numpy as np
from typing import List, Dict, Any, Tuple
from pathlib import Path
import logging
from scenedetect import VideoManager, SceneManager
from scenedetect.detectors import ContentDetector
import json

logger = logging.getLogger(__name__)


class VideoWindow:
    """Represents a video window with timing and metadata."""
    
    def __init__(self, start_time: float, end_time: float, window_id: str = None):
        self.start_time = start_time
        self.end_time = end_time
        self.duration = end_time - start_time
        self.window_id = window_id or f"window_{start_time:.1f}_{end_time:.1f}"
        self.scene_cuts = []
        self.transcript_segments = []
        self.features = {}
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert window to dictionary representation."""
        return {
            'window_id': self.window_id,
            'start_time': self.start_time,
            'end_time': self.end_time,
            'duration': self.duration,
            'scene_cuts': self.scene_cuts,
            'transcript_segments': self.transcript_segments,
            'features': self.features
        }


class SceneDetector:
    """Detect scene boundaries in video using PySceneDetect."""
    
    def __init__(self, threshold: float = 30.0):
        self.threshold = threshold
    
    def detect_scenes(self, video_path: str) -> List[Tuple[float, float]]:
        """
        Detect scene boundaries in video.
        
        Args:
            video_path: Path to video file
            
        Returns:
            List of (start_time, end_time) tuples for each scene
        """
        try:
            # Create video manager and scene manager
            video_manager = VideoManager([video_path])
            scene_manager = SceneManager()
            
            # Add content detector with threshold
            scene_manager.add_detector(ContentDetector(threshold=self.threshold))
            
            # Start video manager
            video_manager.start()
            
            # Detect scenes
            scene_manager.detect_scenes(frame_source=video_manager)
            
            # Get scene list
            scene_list = scene_manager.get_scene_list()
            
            # Convert to time tuples
            scenes = []
            for scene in scene_list:
                start_time = scene[0].get_seconds()
                end_time = scene[1].get_seconds()
                scenes.append((start_time, end_time))
            
            logger.info(f"Detected {len(scenes)} scenes in video")
            return scenes
            
        except Exception as e:
            logger.error(f"Error detecting scenes: {e}")
            return []
        finally:
            if 'video_manager' in locals():
                video_manager.release()
    
    def get_scene_cuts(self, video_path: str) -> List[float]:
        """
        Get list of scene cut timestamps.
        
        Args:
            video_path: Path to video file
            
        Returns:
            List of scene cut timestamps in seconds
        """
        scenes = self.detect_scenes(video_path)
        cuts = []
        
        for i, (start, end) in enumerate(scenes):
            if i > 0:  # Skip first scene start
                cuts.append(start)
        
        return cuts


class WindowGenerator:
    """Generate video windows with scene boundary alignment."""
    
    def __init__(self, window_duration: float = 90.0, stride: float = 15.0):
        self.window_duration = window_duration
        self.stride = stride
        self.scene_detector = SceneDetector()
    
    def generate_windows(
        self, 
        video_path: str, 
        video_duration: float,
        transcription: Dict[str, Any] = None
    ) -> List[VideoWindow]:
        """
        Generate video windows with scene boundary snapping.
        
        Args:
            video_path: Path to video file
            video_duration: Total video duration in seconds
            transcription: Optional transcription data to align
            
        Returns:
            List of VideoWindow objects
        """
        try:
            # Detect scene boundaries
            scene_cuts = self.scene_detector.get_scene_cuts(video_path)
            logger.info(f"Found {len(scene_cuts)} scene cuts")
            
            windows = []
            current_start = 0.0
            window_id = 0
            
            while current_start < video_duration - self.window_duration:
                # Calculate initial window end
                window_end = current_start + self.window_duration
                
                # Snap to nearest scene boundary if within threshold
                snapped_start, snapped_end = self._snap_to_scene_boundaries(
                    current_start, window_end, scene_cuts
                )
                
                # Ensure window doesn't exceed video duration
                snapped_end = min(snapped_end, video_duration)
                
                # Create window
                window = VideoWindow(
                    start_time=snapped_start,
                    end_time=snapped_end,
                    window_id=f"window_{window_id:03d}"
                )
                
                # Add scene cuts within this window
                window.scene_cuts = [
                    cut for cut in scene_cuts 
                    if snapped_start <= cut <= snapped_end
                ]
                
                # Add transcript segments if available
                if transcription:
                    window.transcript_segments = self._get_transcript_segments(
                        transcription, snapped_start, snapped_end
                    )
                
                windows.append(window)
                
                # Move to next window
                current_start += self.stride
                window_id += 1
            
            logger.info(f"Generated {len(windows)} windows")
            return windows
            
        except Exception as e:
            logger.error(f"Error generating windows: {e}")
            return []
    
    def _snap_to_scene_boundaries(
        self, 
        start: float, 
        end: float, 
        scene_cuts: List[float],
        snap_threshold: float = 5.0
    ) -> Tuple[float, float]:
        """
        Snap window boundaries to nearby scene cuts.
        
        Args:
            start: Window start time
            end: Window end time
            scene_cuts: List of scene cut timestamps
            snap_threshold: Maximum distance to snap (seconds)
            
        Returns:
            Tuple of (snapped_start, snapped_end)
        """
        snapped_start = start
        snapped_end = end
        
        # Find nearest scene cut to start
        for cut in scene_cuts:
            if abs(cut - start) <= snap_threshold:
                snapped_start = cut
                break
        
        # Find nearest scene cut to end
        for cut in scene_cuts:
            if abs(cut - end) <= snap_threshold:
                snapped_end = cut
                break
        
        # Ensure minimum window duration
        if snapped_end - snapped_start < self.window_duration * 0.8:
            # If snapping made window too short, revert to original end
            snapped_end = snapped_start + self.window_duration
        
        return snapped_start, snapped_end
    
    def _get_transcript_segments(
        self, 
        transcription: Dict[str, Any], 
        start_time: float, 
        end_time: float
    ) -> List[Dict[str, Any]]:
        """
        Get transcript segments that overlap with window timeframe.
        
        Args:
            transcription: Transcription data with sentences
            start_time: Window start time
            end_time: Window end time
            
        Returns:
            List of transcript segments within the window
        """
        segments = []
        
        for sentence in transcription.get('sentences', []):
            sentence_start = sentence.get('start', 0)
            sentence_end = sentence.get('end', 0)
            
            # Check if sentence overlaps with window
            if (sentence_start < end_time and sentence_end > start_time):
                # Calculate overlap
                overlap_start = max(sentence_start, start_time)
                overlap_end = min(sentence_end, end_time)
                overlap_duration = overlap_end - overlap_start
                
                # Only include if significant overlap (>50% of sentence)
                sentence_duration = sentence_end - sentence_start
                if overlap_duration > sentence_duration * 0.5:
                    segment = {
                        'text': sentence.get('text', ''),
                        'start': sentence_start,
                        'end': sentence_end,
                        'words': sentence.get('words', []),
                        'overlap_start': overlap_start,
                        'overlap_end': overlap_end,
                        'overlap_duration': overlap_duration
                    }
                    segments.append(segment)
        
        return segments
    
    def calculate_window_features(self, window: VideoWindow) -> Dict[str, Any]:
        """
        Calculate basic features for a window.
        
        Args:
            window: VideoWindow object
            
        Returns:
            Dictionary of calculated features
        """
        features = {
            'scene_cut_count': len(window.scene_cuts),
            'scene_cut_penalty': len(window.scene_cuts) * 0.1,  # Penalty for scene cuts
            'transcript_word_count': 0,
            'transcript_char_count': 0,
            'speech_duration': 0.0,
            'silence_duration': 0.0
        }
        
        # Calculate transcript features
        for segment in window.transcript_segments:
            text = segment.get('text', '')
            features['transcript_word_count'] += len(text.split())
            features['transcript_char_count'] += len(text)
            features['speech_duration'] += segment.get('overlap_duration', 0)
        
        # Calculate silence duration
        features['silence_duration'] = window.duration - features['speech_duration']
        
        # Speech ratio
        features['speech_ratio'] = features['speech_duration'] / window.duration if window.duration > 0 else 0
        
        # Words per minute
        features['words_per_minute'] = (
            features['transcript_word_count'] * 60 / window.duration 
            if window.duration > 0 else 0
        )
        
        window.features = features
        return features


def save_windows_to_json(windows: List[VideoWindow], output_path: str):
    """Save windows to JSON file."""
    windows_data = [window.to_dict() for window in windows]
    
    with open(output_path, 'w') as f:
        json.dump(windows_data, f, indent=2)
    
    logger.info(f"Saved {len(windows)} windows to {output_path}")


def load_windows_from_json(input_path: str) -> List[VideoWindow]:
    """Load windows from JSON file."""
    with open(input_path, 'r') as f:
        windows_data = json.load(f)
    
    windows = []
    for data in windows_data:
        window = VideoWindow(
            start_time=data['start_time'],
            end_time=data['end_time'],
            window_id=data['window_id']
        )
        window.scene_cuts = data.get('scene_cuts', [])
        window.transcript_segments = data.get('transcript_segments', [])
        window.features = data.get('features', {})
        windows.append(window)
    
    logger.info(f"Loaded {len(windows)} windows from {input_path}")
    return windows


if __name__ == "__main__":
    # Test window generation
    generator = WindowGenerator()
    
    # Test with sample video (you'll need to provide this)
    test_video = "test_video.mp4"
    
    if Path(test_video).exists():
        try:
            # Get video duration using OpenCV
            cap = cv2.VideoCapture(test_video)
            fps = cap.get(cv2.CAP_PROP_FPS)
            frame_count = cap.get(cv2.CAP_PROP_FRAME_COUNT)
            duration = frame_count / fps
            cap.release()
            
            print(f"Video duration: {duration:.2f}s")
            
            # Generate windows
            windows = generator.generate_windows(test_video, duration)
            
            print(f"Generated {len(windows)} windows:")
            for window in windows[:5]:  # Show first 5
                print(f"  {window.window_id}: {window.start_time:.1f}s - {window.end_time:.1f}s")
                print(f"    Scene cuts: {len(window.scene_cuts)}")
                
                # Calculate features
                features = generator.calculate_window_features(window)
                print(f"    Words: {features['transcript_word_count']}")
                print(f"    Speech ratio: {features['speech_ratio']:.2f}")
            
        except Exception as e:
            print(f"Error: {e}")
    else:
        print(f"Test video file not found: {test_video}")
