from pydantic import BaseModel, HttpUrl
from typing import List, Optional
from datetime import datetime

class ClipRequest(BaseModel):
    youtube_url: str
    start_time: str  # Format: HH:MM:SS
    end_time: str    # Format: HH:MM:SS
    duration: Optional[float] = None  # Calculated duration in seconds

class ClipResponse(BaseModel):
    clip_id: str
    status: str  # processing, completed, error
    message: str
    video_path: Optional[str] = None

class Caption(BaseModel):
    start_time: float  # Seconds
    end_time: float    # Seconds
    text: str
    speaker: str       # Speaker 1, Speaker 2, Speaker 3

class CaptionUpdate(BaseModel):
    captions: List[Caption]
    speakers: List[str]  # List of identified speakers

class UploadRequest(BaseModel):
    title: str
    description: str

class ClipData(BaseModel):
    id: str
    status: str
    youtube_url: str
    start_time: str
    end_time: str
    duration: Optional[float]
    created_at: str
    video_path: Optional[str]
    captions: List[Caption]
    speakers: List[str]
    youtube_upload: Optional[dict] = None
    uploaded_at: Optional[str] = None