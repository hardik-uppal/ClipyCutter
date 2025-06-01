# 🚀 Clippy v2 - Quick Start Guide

## **Ready to Run in 3 Commands!**

```bash
git clone https://github.com/dschwenk94/Clippyv2.git
cd Clippyv2
./first-run.sh
```

That's it! Your viral clip generator is ready at **http://localhost:3000**

---

## **What Just Happened?**

✅ **Docker services started:**
- Frontend (React): http://localhost:3000
- Backend (FastAPI): http://localhost:8000  
- Redis (Task Queue): Running internally
- API Documentation: http://localhost:8000/docs

✅ **Ready to use:**
- Download YouTube videos ✅
- Crop for shorts format ✅  
- Generate captions ✅
- Edit speakers ✅
- Preview videos ✅

⚠️ **YouTube upload disabled** (until you add API keys)

---

## **🎯 Try Your First Clip**

1. **Go to http://localhost:3000**

2. **Enter a YouTube URL** (try this one):
   ```
   https://www.youtube.com/watch?v=dQw4w9WgXcQ
   ```

3. **Set time range:**
   - Start: `00:00:10`
   - End: `00:00:30`

4. **Click "🚀 Create Clip"**

5. **Watch the magic happen:**
   - Downloads video segment
   - Crops to 9:16 ratio for shorts
   - Generates captions with speaker detection
   - Adds overlay text

6. **Edit captions** and speakers if needed

7. **Add title/description** (upload will show message about needing API keys)

---

## **🔧 Common First-Run Issues**

### **Port Already in Use**
```bash
# Kill processes using the ports
lsof -ti:3000 | xargs kill -9  # Frontend
lsof -ti:8000 | xargs kill -9  # Backend
docker-compose up
```

### **Docker Not Starting**
```bash
# Clean restart
docker-compose down
docker-compose up --build
```

### **Services Still Starting**
```bash
# Check status
docker-compose ps

# Watch logs
docker-compose logs -f backend
docker-compose logs -f frontend
```

### **Need to Stop Everything**
```bash
docker-compose down
```

---

## **🎬 Enable YouTube Upload (Optional)**

To enable the full YouTube upload feature:

1. **Get YouTube API credentials** (see `SETUP.md` for detailed steps):
   - Go to Google Cloud Console
   - Create project and enable YouTube Data API v3
   - Create OAuth 2.0 credentials
   - Download as `credentials.json`

2. **Add credentials:**
   ```bash
   # Place the file here:
   cp ~/Downloads/credentials.json backend/credentials.json
   ```

3. **Restart services:**
   ```bash
   docker-compose restart backend
   ```

4. **Test upload** - the app will walk you through OAuth setup on first upload

---

## **📊 Monitor Your System**

### **View Logs**
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f backend
docker-compose logs -f frontend
```

### **Check Service Status**
```bash
docker-compose ps
```

### **Resource Usage**
```bash
docker stats
```

---

## **🔄 Development Workflow**

### **Making Code Changes**

**Backend changes:**
```bash
# Backend auto-reloads, just edit files in backend/
# Changes appear immediately
```

**Frontend changes:**
```bash
# Frontend auto-reloads, just edit files in frontend/src/
# Changes appear immediately in browser
```

### **Adding Dependencies**

**Backend (Python):**
```bash
# Add to backend/requirements.txt
# Rebuild: docker-compose up --build backend
```

**Frontend (Node):**
```bash
# Add to frontend/package.json  
# Rebuild: docker-compose up --build frontend
```

### **Database Migration (Future)**
```bash
# When you add a database later:
# 1. Update docker-compose.yml
# 2. Add database models
# 3. Migrate file storage to DB
```

---

## **🎯 What's Next?**

### **Immediate Next Steps:**
1. ✅ **Test the basic workflow** with a YouTube video
2. ✅ **Experiment with different time ranges** 
3. ✅ **Try editing captions and speakers**
4. 🔧 **Set up YouTube API** for uploads (optional)

### **Development Ideas:**
- **Add batch processing** for multiple clips
- **Implement user accounts** and clip history  
- **Add more video platforms** (TikTok direct upload)
- **Enhanced AI features** (better speaker detection)
- **Analytics dashboard** for viral performance

### **Production Deployment:**
- Set up proper domain and HTTPS
- Use managed databases and file storage
- Add monitoring and logging
- Implement rate limiting and security

---

## **🆘 Need Help?**

1. **Check logs:** `docker-compose logs -f`
2. **Read setup guide:** `SETUP.md`
3. **Test system:** `./test-system.py`
4. **Clean restart:** `docker-compose down && docker-compose up --build`

**You're all set! Start creating viral content! 🎬✨**