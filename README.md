# 🎬 Clippy v2 - YouTube Clip Generator

> Transform any YouTube video into viral shorts with AI-powered speaker tracking, transcription, and automatic cropping

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Docker](https://img.shields.io/badge/Docker-Ready-blue.svg)](https://docker.com)
[![FastAPI](https://img.shields.io/badge/FastAPI-Backend-green.svg)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-Frontend-blue.svg)](https://reactjs.org)

## 🚀 Quick Start

**Ready to run in 3 commands:**

```bash
git clone https://github.com/dschwenk94/Clippyv2.git
cd Clippyv2
./first-run.sh
```

**That's it!** Your viral clip generator is ready at **http://localhost:3000**

## ✨ Features

- 🎥 **YouTube Video Download** - Extract segments with precise timing
- 📱 **Auto-Crop for Shorts** - Perfect 9:16 aspect ratio for TikTok/YouTube Shorts
- 🎤 **AI Speaker Detection** - Automatically identify and track up to 3 speakers
- 📝 **Smart Transcription** - OpenAI Whisper-powered captions with timing
- ✏️ **Editable Captions** - Real-time caption editing with speaker assignment
- 📤 **YouTube Upload** - Direct upload with OAuth integration
- 🔄 **Real-time Progress** - Live updates throughout processing
- 🐳 **Docker Ready** - One-command setup for development teams

## 🎯 Perfect For

- **Content Creators** - Turn long-form content into viral shorts
- **Social Media Managers** - Quick clip creation for multiple platforms
- **Podcasters** - Extract highlights with speaker identification
- **Educators** - Create digestible content segments
- **Marketing Teams** - Generate engaging promotional clips

## 🛠 Technology Stack

- **Backend**: FastAPI (Python) + OpenCV + FFmpeg + Whisper
- **Frontend**: React (TypeScript) with responsive design
- **Video Processing**: AI-powered speaker tracking and cropping
- **Infrastructure**: Docker Compose + Redis for background tasks
- **APIs**: YouTube Data API v3 with OAuth 2.0

## 📸 Screenshots

### Input Screen
*Enter any YouTube URL and specify time segments*

### Preview & Edit
*AI-generated captions with speaker detection - fully editable*

### Upload & Share
*Direct upload to YouTube with auto-generated titles and descriptions*

## 🏁 Getting Started

### Prerequisites
- Docker Desktop
- Git
- Web browser

### Installation

1. **Clone and start:**
   ```bash
   git clone https://github.com/dschwenk94/Clippyv2.git
   cd Clippyv2
   ./first-run.sh
   ```

2. **Access the application:**
   - 🎬 **Main App**: http://localhost:3000
   - 🔧 **API Docs**: http://localhost:8000/docs
   - 📊 **Backend**: http://localhost:8000

3. **Try your first clip:**
   - Enter a YouTube URL
   - Set start/end times (e.g., `00:01:30` to `00:02:00`)
   - Watch AI process and generate your viral short!

### YouTube Upload Setup (Optional)

To enable YouTube uploads:

1. **Get YouTube API credentials** (see [SETUP.md](SETUP.md))
2. **Add credentials**: Place `credentials.json` in `backend/` directory
3. **Restart**: `docker-compose restart backend`

*Note: All features work without YouTube API - upload is optional*

## 📚 Documentation

- **[🚀 Quick Start Guide](QUICKSTART.md)** - Get running in minutes
- **[🔧 Setup Guide](SETUP.md)** - Detailed installation and YouTube API setup
- **[✅ Development Checklist](CHECKLIST.md)** - Verify everything works

## 🎮 Try It Now

**Test with this YouTube URL:**
```
https://www.youtube.com/watch?v=dQw4w9WgXcQ
```
- Start: `00:00:10`
- End: `00:00:30`

Watch the AI:
1. Download the video segment
2. Crop to perfect shorts format
3. Generate captions with speaker detection
4. Create a viral-ready clip!

## 🔧 Development

### Project Structure
```
Clippyv2/
├── 🐍 backend/          # FastAPI + AI processing
├── ⚛️ frontend/         # React UI
├── 🐳 docker-compose.yml # Full stack setup
├── 📁 clips/            # Processed videos
└── 📚 docs/             # Documentation
```

### Making Changes

**Backend** (auto-reloads):
```bash
# Edit files in backend/
# Changes appear immediately
```

**Frontend** (auto-reloads):
```bash
# Edit files in frontend/src/
# Changes appear in browser
```

### Common Commands

```bash
# View logs
docker-compose logs -f

# Restart services
docker-compose restart

# Stop everything
docker-compose down

# Clean rebuild
docker-compose down && docker-compose up --build
```

## 🚀 Production Deployment

1. **Environment**: Set `ENVIRONMENT=production` in `.env`
2. **Security**: Configure proper OAuth and HTTPS
3. **Storage**: Add database and cloud file storage
4. **Scaling**: Use container orchestration

See [SETUP.md](SETUP.md) for detailed production deployment guide.

## 🤝 Contributing

1. **Fork** the repository
2. **Create** feature branch: `git checkout -b feature/amazing-feature`
3. **Commit** changes: `git commit -m 'Add amazing feature'`
4. **Push** to branch: `git push origin feature/amazing-feature`
5. **Open** a Pull Request

## 🐛 Troubleshooting

**Services not starting?**
```bash
# Check Docker is running
docker --version

# Check ports are free
lsof -ti:3000,8000 | xargs kill -9

# Clean restart
docker-compose down && docker-compose up --build
```

**Processing errors?**
```bash
# Check backend logs
docker-compose logs -f backend

# Test with different video
# Ensure time format is HH:MM:SS
```

For more help, see [SETUP.md](SETUP.md) and [CHECKLIST.md](CHECKLIST.md)

## 📋 Roadmap

### ✅ Completed
- [x] YouTube video download and cropping
- [x] AI speaker detection and tracking
- [x] Real-time transcription with Whisper
- [x] Editable captions with speaker assignment
- [x] YouTube upload with OAuth
- [x] Docker containerization
- [x] Responsive React UI

### 🔄 In Progress
- [ ] User accounts and clip history
- [ ] Batch processing multiple clips
- [ ] Advanced speaker detection improvements

### 📅 Planned
- [ ] TikTok direct upload
- [ ] Instagram Reels integration
- [ ] Analytics dashboard
- [ ] Advanced video editing features
- [ ] Cloud deployment templates

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **OpenAI Whisper** for transcription
- **FFmpeg** for video processing
- **yt-dlp** for YouTube downloading
- **FastAPI** for the amazing backend framework
- **React** for the frontend framework

## 📞 Support

- 📖 **Documentation**: Check our comprehensive guides
- 🐛 **Issues**: [GitHub Issues](https://github.com/dschwenk94/Clippyv2/issues)
- 💬 **Discussions**: [GitHub Discussions](https://github.com/dschwenk94/Clippyv2/discussions)

---

**⭐ Star this repo if Clippy v2 helps you create viral content!**

*Made with ❤️ for content creators worldwide*
