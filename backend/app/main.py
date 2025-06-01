from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Optional, List
import os
import uuid
from datetime import datetime

from app.services.video_processor import VideoProcessor
from app.services.youtube_service import YouTubeService
from app.models.clip_models import ClipRequest, ClipResponse, CaptionUpdate, UploadRequest

app = FastAPI(title="Clippy v2 API", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount clips directory for serving processed videos
app.mount("/clips", StaticFiles(directory="clips"), name="clips")

# Initialize services
video_processor = VideoProcessor()
youtube_service = YouTubeService()

# In-memory storage for clips (will be replaced with database)
clips_storage = {}

@app.get("/")
async def root():
    return {"message": "Clippy v2 API is running!"}

@app.post("/api/process-clip", response_model=ClipResponse)
async def process_clip(request: ClipRequest, background_tasks: BackgroundTasks):
    """
    Process a YouTube video clip with the given parameters
    """
    try:
        clip_id = str(uuid.uuid4())
        
        # Store initial clip data
        clips_storage[clip_id] = {
            "id": clip_id,
            "status": "processing",
            "youtube_url": request.youtube_url,
            "start_time": request.start_time,
            "end_time": request.end_time,
            "duration": request.duration,
            "created_at": datetime.now().isoformat(),
            "video_path": None,
            "captions": [],
            "speakers": []
        }
        
        # Start background processing
        background_tasks.add_task(
            video_processor.process_video_clip,
            clip_id,
            request.youtube_url,
            request.start_time,
            request.end_time,
            clips_storage
        )
        
        return ClipResponse(
            clip_id=clip_id,
            status="processing",
            message="Video processing started"
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/clip/{clip_id}")
async def get_clip_status(clip_id: str):
    """
    Get the current status and data of a processing clip
    """
    if clip_id not in clips_storage:
        raise HTTPException(status_code=404, detail="Clip not found")
    
    return clips_storage[clip_id]

@app.post("/api/clip/{clip_id}/update-captions")
async def update_captions(clip_id: str, update: CaptionUpdate, background_tasks: BackgroundTasks):
    """
    Update captions and regenerate video with new overlays
    """
    if clip_id not in clips_storage:
        raise HTTPException(status_code=404, detail="Clip not found")
    
    clip_data = clips_storage[clip_id]
    
    # Update the captions in storage
    clip_data["captions"] = update.captions
    clip_data["speakers"] = update.speakers
    clip_data["status"] = "updating"
    
    # Regenerate video with new captions
    background_tasks.add_task(
        video_processor.regenerate_with_captions,
        clip_id,
        update.captions,
        update.speakers,
        clips_storage
    )
    
    return {"message": "Caption update started", "status": "updating"}

@app.post("/api/clip/{clip_id}/upload")
async def upload_to_youtube(clip_id: str, upload_request: UploadRequest):
    """
    Upload the processed clip to YouTube
    """
    if clip_id not in clips_storage:
        raise HTTPException(status_code=404, detail="Clip not found")
    
    clip_data = clips_storage[clip_id]
    
    if clip_data["status"] != "completed":
        raise HTTPException(status_code=400, detail="Clip processing not completed")
    
    try:
        upload_result = await youtube_service.upload_video(
            video_path=clip_data["video_path"],
            title=upload_request.title,
            description=upload_request.description
        )
        
        # Update clip data with upload info
        clip_data["youtube_upload"] = upload_result
        clip_data["uploaded_at"] = datetime.now().isoformat()
        
        return {
            "message": "Video uploaded successfully",
            "youtube_url": upload_result.get("youtube_url"),
            "video_id": upload_result.get("video_id")
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

@app.get("/api/clips")
async def list_clips():
    """
    Get list of all processed clips
    """
    return list(clips_storage.values())

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)