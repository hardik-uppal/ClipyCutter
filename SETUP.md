# Clippy v2 Development Setup

This document provides step-by-step instructions for developers to get Clippy v2 running locally.

## Prerequisites

- **Docker & Docker Compose** (Recommended)
- **Git** for version control
- **Node.js 18+** (if running frontend manually)
- **Python 3.11+** (if running backend manually)

## Quick Start (Docker - Recommended)

1. **Clone and enter the project**
   ```bash
   git clone https://github.com/dschwenk94/Clippyv2.git
   cd Clippyv2
   ```

2. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your API keys and configuration
   ```

3. **Start everything with Docker**
   ```bash
   docker-compose up --build
   ```

4. **Access the application**
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - API Documentation: http://localhost:8000/docs

## Manual Development Setup

### Backend Setup

1. **Create Python virtual environment**
   ```bash
   cd backend
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Install system dependencies**
   ```bash
   # On macOS
   brew install ffmpeg
   
   # On Ubuntu/Debian
   sudo apt update
   sudo apt install ffmpeg
   
   # On Windows
   # Download FFmpeg from https://ffmpeg.org/download.html
   ```

4. **Start Redis (required for task queue)**
   ```bash
   # On macOS
   brew install redis
   brew services start redis
   
   # On Ubuntu/Debian
   sudo apt install redis-server
   sudo systemctl start redis
   
   # Or use Docker
   docker run -d -p 6379:6379 redis:7-alpine
   ```

5. **Run the backend**
   ```bash
   uvicorn app.main:app --reload --port 8000
   ```

### Frontend Setup

1. **Install Node.js dependencies**
   ```bash
   cd frontend
   npm install
   ```

2. **Start the development server**
   ```bash
   npm start
   ```

## YouTube API Setup

1. **Create Google Cloud Project**
   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Create a new project or select existing one

2. **Enable YouTube Data API v3**
   - Go to APIs & Services > Library
   - Search for "YouTube Data API v3"
   - Click "Enable"

3. **Create OAuth 2.0 Credentials**
   - Go to APIs & Services > Credentials
   - Click "Create Credentials" > "OAuth 2.0 Client ID"
   - Choose "Desktop application"
   - Download the credentials JSON file
   - Rename it to `credentials.json` and place in the `backend/` directory

4. **Configure OAuth Consent Screen**
   - Go to APIs & Services > OAuth consent screen
   - Fill in required information
   - Add your email to test users

## Project Structure

```
Clippyv2/
├── backend/                    # FastAPI backend
│   ├── app/
│   │   ├── main.py            # Main API application
│   │   ├── config.py          # Configuration settings
│   │   ├── models/            # Pydantic models
│   │   └── services/          # Business logic
│   ├── Dockerfile
│   ├── requirements.txt
│   └── credentials.json       # YouTube API credentials (you create this)
├── frontend/                   # React frontend
│   ├── src/
│   │   ├── screens/           # Main application screens
│   │   ├── services/          # API communication
│   │   └── App.tsx           # Main React component
│   ├── Dockerfile
│   └── package.json
├── clips/                     # Processed video storage
├── docker-compose.yml         # Full stack setup
├── .env.example              # Environment template
└── README.md
```

## Development Workflow

1. **Feature Development**
   ```bash
   git checkout -b feature/your-feature-name
   # Make your changes
   git commit -m "Add your feature"
   git push origin feature/your-feature-name
   # Create pull request
   ```

2. **Testing Changes**
   - Backend: Visit http://localhost:8000/docs for API testing
   - Frontend: Use the web interface at http://localhost:3000
   - Check logs: `docker-compose logs -f backend` or `docker-compose logs -f frontend`

3. **Debugging**
   ```bash
   # View backend logs
   docker-compose logs -f backend
   
   # View frontend logs
   docker-compose logs -f frontend
   
   # Access backend container
   docker-compose exec backend bash
   
   # Restart services
   docker-compose restart backend
   ```

## Common Issues & Solutions

### FFmpeg Not Found
```bash
# Ensure FFmpeg is installed and accessible
ffmpeg -version

# On Docker, it's included in the image
```

### YouTube Upload Fails
- Check that `credentials.json` exists in backend directory
- Verify OAuth consent screen is configured
- Ensure test users are added if app is not published

### Port Already in Use
```bash
# Find and kill process using port
lsof -ti:3000 | xargs kill -9  # Frontend
lsof -ti:8000 | xargs kill -9  # Backend
```

### Docker Issues
```bash
# Clean rebuild
docker-compose down -v
docker-compose up --build

# Remove all containers and images
docker system prune -a
```

## Production Deployment

1. **Environment Configuration**
   - Set `ENVIRONMENT=production` in .env
   - Use strong `SECRET_KEY`
   - Configure proper YouTube OAuth for your domain

2. **Security Considerations**
   - Use HTTPS in production
   - Implement rate limiting
   - Secure Redis instance
   - Regular security updates

3. **Scaling**
   - Use external Redis cluster
   - Implement proper file storage (S3, etc.)
   - Add database for persistent storage
   - Use container orchestration (Kubernetes, etc.)

## Contributing

1. Follow the existing code style
2. Add tests for new features
3. Update documentation
4. Submit pull requests to `main` branch
5. Ensure all checks pass before merging

For questions or issues, please create an issue in the repository or contact the development team.