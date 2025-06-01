import os
import subprocess
import whisper
import cv2
import numpy as np
from typing import List, Dict, Any
import yt_dlp
from datetime import datetime
import json

from app.models.clip_models import Caption

class VideoProcessor:
    def __init__(self):
        self.whisper_model = whisper.load_model("base")
        self.clips_dir = "clips"
        os.makedirs(self.clips_dir, exist_ok=True)
        
    async def process_video_clip(self, clip_id: str, youtube_url: str, start_time: str, end_time: str, clips_storage: dict):
        """
        Main processing pipeline for video clips
        """
        try:
            # Update status
            clips_storage[clip_id]["status"] = "downloading"
            
            # Step 1: Download video segment
            video_path = await self._download_video_segment(clip_id, youtube_url, start_time, end_time)
            clips_storage[clip_id]["video_path"] = video_path
            
            # Step 2: Track speakers and crop for shorts
            clips_storage[clip_id]["status"] = "processing_video"
            cropped_video_path = await self._crop_for_shorts(video_path, clip_id)
            
            # Step 3: Transcribe and identify speakers
            clips_storage[clip_id]["status"] = "transcribing"
            captions, speakers = await self._transcribe_and_identify_speakers(cropped_video_path)
            
            clips_storage[clip_id]["captions"] = [caption.dict() for caption in captions]
            clips_storage[clip_id]["speakers"] = speakers
            
            # Step 4: Generate final video with captions
            clips_storage[clip_id]["status"] = "finalizing"
            final_video_path = await self._add_captions_to_video(cropped_video_path, captions, clip_id)
            
            clips_storage[clip_id]["video_path"] = final_video_path
            clips_storage[clip_id]["status"] = "completed"
            clips_storage[clip_id]["completed_at"] = datetime.now().isoformat()
            
        except Exception as e:
            clips_storage[clip_id]["status"] = "error"
            clips_storage[clip_id]["error"] = str(e)
            print(f"Error processing clip {clip_id}: {e}")
    
    async def _download_video_segment(self, clip_id: str, youtube_url: str, start_time: str, end_time: str) -> str:
        """
        Download specific segment from YouTube video
        """
        output_path = os.path.join(self.clips_dir, f"{clip_id}_original.mp4")
        
        # Convert time format to seconds
        start_seconds = self._time_to_seconds(start_time)
        end_seconds = self._time_to_seconds(end_time)
        duration = end_seconds - start_seconds
        
        ydl_opts = {
            'format': 'best[height<=1080]',
            'outtmpl': output_path,
            'external_downloader': 'ffmpeg',
            'external_downloader_args': [
                '-ss', str(start_seconds),
                '-t', str(duration)
            ]
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([youtube_url])
        
        return output_path
    
    async def _crop_for_shorts(self, video_path: str, clip_id: str) -> str:
        """
        Crop video for YouTube Shorts/TikTok aspect ratio (9:16) with speaker tracking
        """
        output_path = os.path.join(self.clips_dir, f"{clip_id}_cropped.mp4")
        
        # Use FFmpeg to crop to 9:16 aspect ratio, focusing on center
        # This is a basic implementation - can be enhanced with face detection
        cmd = [
            'ffmpeg', '-i', video_path,
            '-vf', 'crop=ih*9/16:ih',  # Crop to 9:16 aspect ratio
            '-c:a', 'copy',
            '-y', output_path
        ]
        
        subprocess.run(cmd, check=True, capture_output=True)
        return output_path
    
    async def _transcribe_and_identify_speakers(self, video_path: str) -> tuple[List[Caption], List[str]]:
        """
        Transcribe audio and attempt basic speaker identification
        """
        # Extract audio for transcription
        audio_path = video_path.replace('.mp4', '_audio.wav')
        cmd = ['ffmpeg', '-i', video_path, '-vn', '-acodec', 'pcm_s16le', '-ar', '16000', '-ac', '1', '-y', audio_path]
        subprocess.run(cmd, check=True, capture_output=True)
        
        # Transcribe with Whisper
        result = self.whisper_model.transcribe(audio_path)
        
        captions = []
        speakers_found = set()
        
        # Basic speaker identification (simplified - can be enhanced)
        current_speaker = "Speaker 1"
        speaker_count = 1
        
        for segment in result['segments']:
            # Simple speaker change detection based on silence gaps
            # In a more advanced version, this would use speaker diarization
            if segment['start'] > 0 and len(captions) > 0:
                prev_end = captions[-1].end_time
                if segment['start'] - prev_end > 2.0:  # 2 second gap suggests speaker change
                    speaker_count = min(speaker_count + 1, 3)  # Max 3 speakers as per requirements
                    current_speaker = f"Speaker {speaker_count}"
            
            caption = Caption(
                start_time=segment['start'],
                end_time=segment['end'],
                text=segment['text'].strip(),
                speaker=current_speaker
            )
            captions.append(caption)
            speakers_found.add(current_speaker)
        
        # Clean up audio file
        os.remove(audio_path)
        
        return captions, list(speakers_found)
    
    async def _add_captions_to_video(self, video_path: str, captions: List[Caption], clip_id: str) -> str:
        """
        Add captions overlay to video
        """
        output_path = os.path.join(self.clips_dir, f"{clip_id}_final.mp4")
        
        # Create subtitle file
        srt_path = os.path.join(self.clips_dir, f"{clip_id}.srt")
        self._create_srt_file(captions, srt_path)
        
        # Add subtitles to video using FFmpeg
        cmd = [
            'ffmpeg', '-i', video_path,
            '-vf', f"subtitles={srt_path}:force_style='Fontsize=20,PrimaryColour=&Hffffff,OutlineColour=&H000000,Outline=2'",
            '-c:a', 'copy',
            '-y', output_path
        ]
        
        subprocess.run(cmd, check=True, capture_output=True)
        
        # Clean up subtitle file
        os.remove(srt_path)
        
        return output_path
    
    async def regenerate_with_captions(self, clip_id: str, captions: List[dict], speakers: List[str], clips_storage: dict):
        """
        Regenerate video with updated captions
        """
        try:
            clip_data = clips_storage[clip_id]
            original_video_path = clip_data["video_path"].replace("_final.mp4", "_cropped.mp4")
            
            # Convert dict captions back to Caption objects
            caption_objects = [Caption(**caption) for caption in captions]
            
            # Generate new video with updated captions
            final_video_path = await self._add_captions_to_video(original_video_path, caption_objects, f"{clip_id}_updated")
            
            clips_storage[clip_id]["video_path"] = final_video_path
            clips_storage[clip_id]["status"] = "completed"
            clips_storage[clip_id]["updated_at"] = datetime.now().isoformat()
            
        except Exception as e:
            clips_storage[clip_id]["status"] = "error"
            clips_storage[clip_id]["error"] = f"Caption update failed: {str(e)}"
    
    def _create_srt_file(self, captions: List[Caption], srt_path: str):
        """
        Create SRT subtitle file from captions
        """
        with open(srt_path, 'w', encoding='utf-8') as f:
            for i, caption in enumerate(captions, 1):
                start_time = self._seconds_to_srt_time(caption.start_time)
                end_time = self._seconds_to_srt_time(caption.end_time)
                
                f.write(f"{i}\n")
                f.write(f"{start_time} --> {end_time}\n")
                f.write(f"[{caption.speaker}] {caption.text}\n\n")
    
    def _time_to_seconds(self, time_str: str) -> float:
        """Convert HH:MM:SS to seconds"""
        parts = time_str.split(':')
        return int(parts[0]) * 3600 + int(parts[1]) * 60 + float(parts[2])
    
    def _seconds_to_srt_time(self, seconds: float) -> str:
        """Convert seconds to SRT time format"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = seconds % 60
        return f"{hours:02d}:{minutes:02d}:{secs:06.3f}".replace('.', ',')