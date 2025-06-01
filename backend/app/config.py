# Backend configuration
from pydantic import BaseSettings
from typing import Optional
import os

class Settings(BaseSettings):
    # Environment
    environment: str = "development"
    
    # API Configuration
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    
    # YouTube API
    youtube_client_id: Optional[str] = None
    youtube_client_secret: Optional[str] = None
    
    # OpenAI
    openai_api_key: Optional[str] = None
    
    # Redis
    redis_url: str = "redis://localhost:6379"
    
    # Security
    secret_key: str = "dev-secret-key-change-in-production"
    
    # File processing
    max_video_duration: int = 300  # 5 minutes
    max_file_size: int = 500  # 500 MB
    whisper_model: str = "base"
    
    # Directories
    clips_directory: str = "clips"
    
    class Config:
        env_file = ".env"

settings = Settings()