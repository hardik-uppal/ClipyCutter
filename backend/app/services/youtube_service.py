import os
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from typing import Dict, Any
import json

class YouTubeService:
    def __init__(self):
        self.SCOPES = ['https://www.googleapis.com/auth/youtube.upload']
        self.credentials = None
        self.youtube = None
        self._initialize_youtube_service()
    
    def _initialize_youtube_service(self):
        """
        Initialize YouTube API service with OAuth credentials
        """
        creds = None
        
        # Token file stores the user's access and refresh tokens
        if os.path.exists('token.json'):
            creds = Credentials.from_authorized_user_file('token.json', self.SCOPES)
        
        # If there are no (valid) credentials available, let the user log in
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                # You'll need to create credentials.json from Google Cloud Console
                if os.path.exists('credentials.json'):
                    flow = InstalledAppFlow.from_client_secrets_file(
                        'credentials.json', self.SCOPES)
                    creds = flow.run_local_server(port=0)
                else:
                    print("Warning: credentials.json not found. YouTube upload will not work.")
                    return
            
            # Save the credentials for the next run
            with open('token.json', 'w') as token:
                token.write(creds.to_json())
        
        if creds:
            self.youtube = build('youtube', 'v3', credentials=creds)
    
    async def upload_video(self, video_path: str, title: str, description: str) -> Dict[str, Any]:
        """
        Upload video to YouTube
        """
        if not self.youtube:
            raise Exception("YouTube service not initialized. Check credentials.")
        
        # Video metadata
        body = {
            'snippet': {
                'title': title,
                'description': description,
                'tags': ['shorts', 'viral', 'clip'],
                'categoryId': '22'  # People & Blogs category
            },
            'status': {
                'privacyStatus': 'public',  # Can be 'private', 'public', or 'unlisted'
                'madeForKids': False
            }
        }
        
        # Create media upload object
        media = MediaFileUpload(
            video_path,
            chunksize=-1,  # Upload in a single chunk
            resumable=True,
            mimetype='video/mp4'
        )
        
        # Execute upload
        insert_request = self.youtube.videos().insert(
            part=','.join(body.keys()),
            body=body,
            media_body=media
        )
        
        response = None
        error = None
        retry = 0
        
        while response is None:
            try:
                status, response = insert_request.next_chunk()
                if response is not None:
                    if 'id' in response:
                        video_id = response['id']
                        youtube_url = f"https://www.youtube.com/watch?v={video_id}"
                        return {
                            'video_id': video_id,
                            'youtube_url': youtube_url,
                            'status': 'uploaded',
                            'response': response
                        }
                    else:
                        raise Exception(f"Upload failed: {response}")
            except Exception as e:
                error = e
                retry += 1
                if retry > 3:
                    raise Exception(f"Upload failed after {retry} retries: {error}")
        
        return response
    
    def get_video_info(self, video_id: str) -> Dict[str, Any]:
        """
        Get information about an uploaded video
        """
        if not self.youtube:
            raise Exception("YouTube service not initialized")
        
        request = self.youtube.videos().list(
            part="snippet,statistics,status",
            id=video_id
        )
        
        response = request.execute()
        return response