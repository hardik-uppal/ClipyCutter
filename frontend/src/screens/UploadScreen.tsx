import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { apiService, ClipData, UploadRequest } from '../services/api';

const UploadScreen: React.FC = () => {
  const { clipId } = useParams<{ clipId: string }>();
  const navigate = useNavigate();
  const [clipData, setClipData] = useState<ClipData | null>(null);
  const [uploadData, setUploadData] = useState<UploadRequest>({
    title: '',
    description: ''
  });
  const [isUploading, setIsUploading] = useState(false);
  const [uploadResult, setUploadResult] = useState<{ youtube_url?: string; video_id?: string } | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!clipId) return;

    const fetchClipData = async () => {
      try {
        const data = await apiService.getClipStatus(clipId);
        setClipData(data);
        
        if (data.status !== 'completed') {
          setError('Clip is not ready for upload. Please go back and complete processing.');
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to fetch clip data');
      }
    };

    fetchClipData();
  }, [clipId]);

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    const { name, value } = e.target;
    setUploadData(prev => ({
      ...prev,
      [name]: value
    }));
  };

  const generateSuggestedTitle = () => {
    if (!clipData) return '';
    
    // Extract some text from captions for title suggestion
    const firstFewWords = clipData.captions
      .slice(0, 2)
      .map(caption => caption.text)
      .join(' ')
      .split(' ')
      .slice(0, 6)
      .join(' ');
    
    return `${firstFewWords}... #Shorts`;
  };

  const generateSuggestedDescription = () => {
    if (!clipData) return '';
    
    const fullTranscript = clipData.captions
      .map(caption => `${caption.speaker}: ${caption.text}`)
      .join('\n');
    
    return `🎬 Viral clip created with Clippy v2!\n\nTranscript:\n${fullTranscript}\n\n#Shorts #Viral #ClippyV2`;
  };

  const handleSuggestTitle = () => {
    setUploadData(prev => ({
      ...prev,
      title: generateSuggestedTitle()
    }));
  };

  const handleSuggestDescription = () => {
    setUploadData(prev => ({
      ...prev,
      description: generateSuggestedDescription()
    }));
  };

  const validateForm = (): boolean => {
    if (!uploadData.title.trim()) {
      setError('Please enter a title for your video');
      return false;
    }

    if (!uploadData.description.trim()) {
      setError('Please enter a description for your video');
      return false;
    }

    if (uploadData.title.length > 100) {
      setError('Title must be 100 characters or less');
      return false;
    }

    if (uploadData.description.length > 5000) {
      setError('Description must be 5000 characters or less');
      return false;
    }

    return true;
  };

  const handleUpload = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!clipId || !clipData) {
      setError('Clip data not available');
      return;
    }

    setError(null);

    if (!validateForm()) {
      return;
    }

    setIsUploading(true);

    try {
      const result = await apiService.uploadToYouTube(clipId, uploadData);
      setUploadResult(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to upload video');
    } finally {
      setIsUploading(false);
    }
  };

  if (!clipData) {
    return (
      <div className="screen-container">
        <div className="loading-spinner"></div>
        <p>Loading clip data...</p>
      </div>
    );
  }

  if (uploadResult) {
    return (
      <div className="screen-container">
        <h2>🎉 Upload Successful!</h2>
        
        <div className="status-message status-completed">
          Your video has been uploaded to YouTube!
        </div>

        {uploadResult.youtube_url && (
          <div style={{ textAlign: 'center', margin: '2rem 0' }}>
            <p>Your video is now live:</p>
            <a 
              href={uploadResult.youtube_url} 
              target="_blank" 
              rel="noopener noreferrer"
              className="btn btn-primary"
              style={{ textDecoration: 'none' }}
            >
              🎬 View on YouTube
            </a>
          </div>
        )}

        {clipData.video_path && (
          <div className="video-container">
            <h3>Final Video Preview:</h3>
            <video className="video-preview" controls>
              <source src={apiService.getVideoUrl(clipData.video_path)} type="video/mp4" />
              Your browser does not support the video tag.
            </video>
          </div>
        )}

        <div style={{ textAlign: 'center', marginTop: '2rem' }}>
          <button 
            onClick={() => navigate('/')}
            className="btn btn-primary"
          >
            🚀 Create Another Clip
          </button>
        </div>

        <div style={{ marginTop: '2rem', fontSize: '0.9rem', color: 'rgba(255, 255, 255, 0.7)' }}>
          <h4>Next Steps:</h4>
          <ul style={{ textAlign: 'left', paddingLeft: '1rem' }}>
            <li>Share your video on social media platforms</li>
            <li>Engage with comments to boost engagement</li>
            <li>Create more clips from the same source video</li>
            <li>Monitor analytics in YouTube Studio</li>
          </ul>
        </div>
      </div>
    );
  }

  return (
    <div className="screen-container">
      <h2>📤 Upload to YouTube</h2>
      <p>Add a catchy title and description to maximize your video's viral potential</p>

      {error && (
        <div className="status-message status-error">
          {error}
        </div>
      )}

      {clipData.video_path && (
        <div className="video-container">
          <h3>Final Preview:</h3>
          <video className="video-preview" controls>
            <source src={apiService.getVideoUrl(clipData.video_path)} type="video/mp4" />
            Your browser does not support the video tag.
          </video>
        </div>
      )}

      <form onSubmit={handleUpload}>
        <div className="form-group">
          <label htmlFor="title">YouTube Short Title</label>
          <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'flex-end' }}>
            <input
              type="text"
              id="title"
              name="title"
              value={uploadData.title}
              onChange={handleInputChange}
              placeholder="Enter a catchy title for your short..."
              maxLength={100}
              required
              style={{ flex: 1 }}
            />
            <button 
              type="button" 
              onClick={handleSuggestTitle}
              className="btn btn-secondary"
              style={{ minWidth: 'auto', padding: '0.5rem 1rem' }}
            >
              💡 Suggest
            </button>
          </div>
          <small style={{ color: 'rgba(255, 255, 255, 0.6)' }}>
            {uploadData.title.length}/100 characters
          </small>
        </div>

        <div className="form-group">
          <label htmlFor="description">YouTube Short Description</label>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
            <textarea
              id="description"
              name="description"
              value={uploadData.description}
              onChange={handleInputChange}
              placeholder="Describe your video, add hashtags, and include relevant keywords..."
              rows={8}
              maxLength={5000}
              required
            />
            <button 
              type="button" 
              onClick={handleSuggestDescription}
              className="btn btn-secondary"
              style={{ alignSelf: 'flex-start' }}
            >
              💡 Generate Description
            </button>
          </div>
          <small style={{ color: 'rgba(255, 255, 255, 0.6)' }}>
            {uploadData.description.length}/5000 characters
          </small>
        </div>

        <div style={{ textAlign: 'center', marginTop: '2rem' }}>
          <button 
            onClick={() => navigate(`/preview/${clipId}`)}
            className="btn btn-secondary"
            style={{ marginRight: '1rem' }}
          >
            ← Back to Preview
          </button>
          
          <button 
            type="submit" 
            className="btn btn-primary"
            disabled={isUploading}
          >
            {isUploading ? (
              <>
                <div className="loading-spinner" style={{ display: 'inline-block', width: '20px', height: '20px', marginRight: '10px' }}></div>
                Uploading...
              </>
            ) : (
              '🚀 Upload to YouTube'
            )}
          </button>
        </div>
      </form>

      <div style={{ marginTop: '2rem', fontSize: '0.9rem', color: 'rgba(255, 255, 255, 0.7)' }}>
        <h4>Upload Tips:</h4>
        <ul style={{ textAlign: 'left', paddingLeft: '1rem' }}>
          <li>Use trending hashtags relevant to your content</li>
          <li>Include keywords that describe the video content</li>
          <li>Keep titles under 60 characters for mobile optimization</li>
          <li>Add timestamps or quotes from the video in description</li>
          <li>Tag original video creator if appropriate</li>
        </ul>
      </div>
    </div>
  );
};

export default UploadScreen;