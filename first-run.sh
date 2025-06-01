#!/bin/bash

# Clippy v2 - First Run Setup Guide
# Run this in your terminal to get started

echo "🎬 Welcome to Clippy v2 First Run Setup!"
echo "========================================"
echo ""

# Check current directory
if [[ ! -f "docker-compose.yml" ]]; then
    echo "❌ Please run this script from the 'Clippyv2' directory"
    echo "   cd Clippyv2"
    echo "   ./first-run.sh"
    exit 1
fi

echo "✅ Found Clippy v2 project files"

# Check Docker
if ! command -v docker &> /dev/null; then
    echo "❌ Docker not found. Please install Docker Desktop first:"
    echo "   https://www.docker.com/products/docker-desktop"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose not found. Please install Docker Compose"
    exit 1
fi

echo "✅ Docker and Docker Compose are available"

# Initialize Git if needed
if [[ ! -d ".git" ]]; then
    echo "📝 Initializing Git repository..."
    git init
    git add .
    git commit -m "Initial commit: Clippy v2 YouTube Clip Generator"
    echo "✅ Git repository initialized"
else
    echo "✅ Git repository already exists"
fi

# Create clips directory
mkdir -p clips
echo "✅ Created clips directory for processed videos"

# Set up environment file
if [[ ! -f ".env" ]]; then
    echo "📝 Creating .env file from template..."
    cp .env.example .env
    echo "✅ Environment file created"
else
    echo "✅ Environment file already exists"
fi

echo ""
echo "🚀 Starting Clippy v2 services..."
echo "   This will download Docker images and may take a few minutes..."
echo ""

# Pull images first to show progress
docker-compose pull

echo ""
echo "🔨 Building and starting services..."

# Build and start services
docker-compose up --build -d

echo ""
echo "⏳ Waiting for services to start..."
sleep 15

# Check service status
if docker-compose ps | grep -q "Up"; then
    echo ""
    echo "🎉 SUCCESS! Clippy v2 is now running!"
    echo ""
    echo "🌐 Open your browser and go to:"
    echo "   📱 Frontend:  http://localhost:3000"
    echo "   🔧 Backend:   http://localhost:8000"
    echo "   📚 API Docs:  http://localhost:8000/docs"
    echo ""
    echo "🔍 To check service status:"
    echo "   docker-compose ps"
    echo ""
    echo "📋 To view logs:"
    echo "   docker-compose logs -f backend"
    echo "   docker-compose logs -f frontend"
    echo ""
    echo "🛑 To stop services:"
    echo "   docker-compose down"
    echo ""
    echo "⚠️  Note: YouTube upload is disabled until you configure API credentials"
    echo "   See SETUP.md for YouTube API setup instructions"
    echo ""
    echo "🎯 Ready to create viral clips! Go to http://localhost:3000"
else
    echo ""
    echo "❌ Some services failed to start. Checking logs..."
    docker-compose logs --tail=50
    echo ""
    echo "💡 Common solutions:"
    echo "   - Make sure ports 3000 and 8000 are not in use"
    echo "   - Try: docker-compose down && docker-compose up --build"
    echo "   - Check Docker Desktop is running"
fi

echo ""
echo "📖 For detailed setup and YouTube API configuration, see SETUP.md"
echo "🎬 Happy clipping!"
