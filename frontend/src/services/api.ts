const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

export interface ClipRequest {
  youtube_url: string;
  start_time: string;
  end_time: string;
  duration?: number;
}

export interface Caption {
  start_time: number;
  end_time: number;
  text: string;
  speaker: string;
}

export interface ClipData {
  id: string;
  status: string;
  youtube_url: string;
  start_time: string;
  end_time: string;
  duration?: number;
  created_at: string;
  video_path?: string;
  captions: Caption[];
  speakers: string[];
  error?: string;
}

export interface UploadRequest {
  title: string;
  description: string;
}

class ApiService {
  private baseURL: string;

  constructor() {
    this.baseURL = API_BASE_URL;
  }

  async processClip(request: ClipRequest): Promise<{ clip_id: string; status: string; message: string }> {
    const response = await fetch(`${this.baseURL}/api/process-clip`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(request),
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    return response.json();
  }

  async getClipStatus(clipId: string): Promise<ClipData> {
    const response = await fetch(`${this.baseURL}/api/clip/${clipId}`);
    
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    return response.json();
  }

  async updateCaptions(clipId: string, captions: Caption[], speakers: string[]): Promise<{ message: string; status: string }> {
    const response = await fetch(`${this.baseURL}/api/clip/${clipId}/update-captions`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        captions,
        speakers,
      }),
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    return response.json();
  }

  async uploadToYouTube(clipId: string, uploadRequest: UploadRequest): Promise<{ message: string; youtube_url?: string; video_id?: string }> {
    const response = await fetch(`${this.baseURL}/api/clip/${clipId}/upload`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(uploadRequest),
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    return response.json();
  }

  getVideoUrl(videoPath: string): string {
    return `${this.baseURL}/${videoPath}`;
  }
}

export const apiService = new ApiService();