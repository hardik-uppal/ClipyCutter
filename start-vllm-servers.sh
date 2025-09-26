#!/bin/bash

# ClipyCutter vLLM Server Startup Script
# Starts the dual vLLM server architecture for local GPU processing

set -e

echo "🎬 ClipyCutter - Starting vLLM Servers"
echo "======================================"

# Check for NVIDIA GPU
if ! command -v nvidia-smi &> /dev/null; then
    echo "❌ NVIDIA GPU not detected. This system requires CUDA-capable GPU."
    exit 1
fi

echo "✅ NVIDIA GPU detected:"
nvidia-smi --query-gpu=name,memory.total --format=csv,noheader,nounits

# Check for Docker and Docker Compose
if ! command -v docker &> /dev/null; then
    echo "❌ Docker not found. Please install Docker first."
    exit 1
fi

if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    echo "❌ Docker Compose not found. Please install Docker Compose first."
    exit 1
fi

# Check for NVIDIA Container Toolkit
if ! docker run --rm --gpus all nvidia/cuda:12.1-base-ubuntu22.04 nvidia-smi &> /dev/null; then
    echo "❌ NVIDIA Container Toolkit not properly configured."
    echo "Please install nvidia-container-toolkit and restart Docker."
    exit 1
fi

echo "✅ Docker and NVIDIA Container Toolkit ready"

# Create necessary directories
mkdir -p temp_downloads rendered_clips logs

# Set permissions
chmod 755 temp_downloads rendered_clips logs

echo ""
echo "🚀 Starting vLLM servers..."
echo "This may take several minutes on first run (downloading models)"
echo ""

# Start the vLLM servers
if docker compose version &> /dev/null; then
    COMPOSE_CMD="docker compose"
else
    COMPOSE_CMD="docker-compose"
fi

# Start core services (Whisper + Chat)
echo "Starting Whisper and Chat servers..."
$COMPOSE_CMD -f docker-compose.vllm.yml up -d vllm-whisper vllm-chat

# Wait for services to be healthy
echo ""
echo "⏳ Waiting for services to start..."

# Function to wait for service health
wait_for_service() {
    local service=$1
    local port=$2
    local max_attempts=60
    local attempt=1
    
    echo "Waiting for $service on port $port..."
    
    while [ $attempt -le $max_attempts ]; do
        if curl -s -f "http://localhost:$port/health" > /dev/null 2>&1; then
            echo "✅ $service is ready!"
            return 0
        fi
        
        echo "  Attempt $attempt/$max_attempts - $service not ready yet..."
        sleep 10
        ((attempt++))
    done
    
    echo "❌ $service failed to start within timeout"
    return 1
}

# Wait for Whisper server
if ! wait_for_service "Whisper Server" 8000; then
    echo "❌ Failed to start Whisper server"
    $COMPOSE_CMD -f docker-compose.vllm.yml logs vllm-whisper
    exit 1
fi

# Wait for Chat server
if ! wait_for_service "Chat Server" 8001; then
    echo "❌ Failed to start Chat server"
    $COMPOSE_CMD -f docker-compose.vllm.yml logs vllm-chat
    exit 1
fi

echo ""
echo "🎉 All vLLM servers are ready!"
echo ""
echo "📊 Server Status:"
echo "  • Whisper Server (ASR):     http://localhost:8000"
echo "  • Chat Server (LLM):        http://localhost:8001"
echo ""
echo "🔧 Available Commands:"
echo "  • Health Check:              python3 backend/cli.py --health-check"
echo "  • Process Video:             python3 backend/cli.py --url <YOUTUBE_URL> --k 3"
echo "  • Stop Servers:              $COMPOSE_CMD -f docker-compose.vllm.yml down"
echo "  • View Logs:                 $COMPOSE_CMD -f docker-compose.vllm.yml logs -f"
echo ""
echo "💡 Optional: Start reranker server with:"
echo "     $COMPOSE_CMD -f docker-compose.vllm.yml --profile reranker up -d vllm-reranker"
echo ""
echo "🎬 Ready to process videos! Try the health check first:"
echo "     cd backend && python3 cli.py --health-check"
