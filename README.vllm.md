# 🎬 ClipyCutter - Local GPU-First Clip Ranking System

> Transform YouTube videos into viral shorts using local vLLM servers, hybrid AI scoring, and NVENC acceleration

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![vLLM](https://img.shields.io/badge/vLLM-Powered-blue.svg)](https://vllm.readthedocs.io/)
[![CUDA](https://img.shields.io/badge/CUDA-Required-green.svg)](https://developer.nvidia.com/cuda-toolkit)

## 🚀 Quick Start

**Ready to run in 3 commands:**

```bash
git clone <this-repo>
cd ClipyCutter
./start-vllm-servers.sh
```

**Process your first video:**

```bash
cd backend
python3 cli.py --url "https://www.youtube.com/watch?v=dQw4w9WgXcQ" --k 3
```

## ✨ Features

- 🎥 **YouTube Video Processing** - Download and process any YouTube video
- 🎤 **vLLM Whisper Transcription** - Word-level timestamps with Whisper-Large-V3
- 🪟 **Smart Window Generation** - 90s windows with scene boundary detection
- 🧠 **Hybrid AI Ranking** - Keyphrases + info density + LLM cogency scoring
- 📱 **Auto-Crop for Shorts** - Perfect 9:16 aspect ratio with NVENC acceleration
- 📝 **Burned-in Captions** - Professional subtitle rendering
- 🏆 **Top-K Clip Selection** - Automatically rank and extract best moments
- 📊 **Detailed Analytics** - CSV logs with scoring breakdowns
- 🐳 **Docker Ready** - Containerized vLLM servers for easy deployment

## 🏗️ Architecture

### Single-Machine, Dual vLLM Setup

```
┌─────────────────────────────────────────────────────────────┐
│                    RTX 4090 GPU Memory                     │
├─────────────────────┬───────────────────┬───────────────────┤
│   vLLM Server A     │   vLLM Server B   │   Processing      │
│   (Port 8000)       │   (Port 8001)     │   Pipeline        │
│                     │                   │                   │
│ Whisper-Large-V3    │ Llama-3.1-8B      │ • YouTube DL      │
│ • Transcription     │ • Cogency Grading │ • Window Gen      │
│ • Word Timestamps   │ • Quote Extraction│ • Ranking         │
│ • /v1/audio/trans   │ • /v1/chat/comp   │ • NVENC Render    │
└─────────────────────┴───────────────────┴───────────────────┘
```

### Processing Pipeline

1. **YouTube Download** (`io_youtube.py`) - yt-dlp extraction
2. **ASR Transcription** (`asr_vllm.py`) - vLLM Whisper API client
3. **Window Generation** (`windows.py`) - 90s windows + scene detection
4. **Hybrid Ranking** (`rank_text.py`) - Multi-factor scoring
5. **Video Rendering** (`cut_render.py`) - NVENC cutting + captions
6. **CLI Interface** (`cli.py`) - Complete workflow orchestration

## 🛠 Technology Stack

- **AI Models**: vLLM (Whisper-Large-V3, Llama-3.1-8B-Instruct)
- **Video Processing**: FFmpeg with NVENC, OpenCV, PySceneDetect
- **Text Analysis**: KeyBERT, YAKE, scikit-learn TF-IDF
- **Infrastructure**: Docker, CUDA, NVIDIA Container Toolkit
- **Languages**: Python 3.8+, AsyncIO for concurrent processing

## 📋 Prerequisites

### Hardware Requirements
- **GPU**: NVIDIA RTX 4090 (24GB VRAM) or equivalent
- **RAM**: 32GB+ system RAM recommended
- **Storage**: 50GB+ free space for models and processing

### Software Requirements
- **OS**: Linux (Ubuntu 22.04+ recommended) or Windows with WSL2
- **CUDA**: 12.1+ with compatible drivers
- **Docker**: 24.0+ with NVIDIA Container Toolkit
- **Python**: 3.8+ (for local development)

## 🔧 Installation

### 1. Clone Repository
```bash
git clone <this-repo>
cd ClipyCutter
```

### 2. Install NVIDIA Container Toolkit
```bash
# Ubuntu/Debian
curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey | sudo gpg --dearmor -o /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg
curl -s -L https://nvidia.github.io/libnvidia-container/stable/deb/nvidia-container-toolkit.list | \
  sed 's#deb https://#deb [signed-by=/usr/share/keyrings/nvidia-container-toolkit-keyring.gpg] https://#g' | \
  sudo tee /etc/apt/sources.list.d/nvidia-container-toolkit.list

sudo apt-get update
sudo apt-get install -y nvidia-container-toolkit
sudo systemctl restart docker
```

### 3. Start vLLM Servers
```bash
./start-vllm-servers.sh
```

This will:
- Download required models (Whisper-Large-V3, Llama-3.1-8B-Instruct)
- Start containerized vLLM servers
- Perform health checks
- Display server status

### 4. Install Python Dependencies (for local CLI)
```bash
cd backend
pip install -r requirements.txt
```

## 🎮 Usage

### Basic Usage
```bash
cd backend
python3 cli.py --url "https://www.youtube.com/watch?v=VIDEO_ID" --k 5
```

### Advanced Options
```bash
# Custom output directory
python3 cli.py --url "https://youtu.be/VIDEO_ID" --k 3 --output-dir /path/to/clips

# Verbose logging
python3 cli.py --url "https://youtu.be/VIDEO_ID" --k 5 --verbose

# Health check
python3 cli.py --health-check

# Custom configuration
python3 cli.py --url "https://youtu.be/VIDEO_ID" --config custom_config.json
```

### Configuration File Example
```json
{
  "whisper_server_url": "http://localhost:8000",
  "chat_server_url": "http://localhost:8001",
  "window_duration": 90.0,
  "window_stride": 15.0,
  "render_quality": "high",
  "output_dir": "custom_clips"
}
```

## 📊 Scoring Algorithm

### Hybrid Ranking Formula
```
final_score = 0.35×keyphrase_coverage + 0.20×info_density + 0.25×llm_cogency
              + 0.10×quote_bonus - 0.05×scene_cut_penalty - 0.05×filler_penalty
```

### Components
- **Keyphrase Coverage**: KeyBERT + YAKE extraction with TF-IDF weighting
- **Information Density**: Lexical diversity, entropy, content word ratio
- **LLM Cogency**: Llama-3.1-8B grades clarity and structure (1-5 scale)
- **Quote Bonus**: Extractable quotable sentences
- **Scene Cut Penalty**: Reduces score for jarring transitions
- **Filler Penalty**: Penalizes "um", "uh", excessive hedging

### LLM Grading Prompt
```
You grade a 90-second transcript chunk for a short.
Criteria: clear claim → brief reason → one example; minimal dangling pronouns; quote-worthiness.
Output: { "cogency": 1-5, "quotes": [up to 3 concise sentences], "salient_terms": [up to 8 non-stopwords] }
```

## 📈 Output

### Generated Files
- **Rendered Clips**: `{video_id}_clip_01.mp4`, `{video_id}_clip_02.mp4`, etc.
- **CSV Log**: `{video_id}_clips_log.csv` with detailed scoring breakdown
- **Processing Log**: `clipycutter.log` with pipeline execution details

### CSV Log Columns
- `video_id`, `rank`, `window_id`, `start_time`, `end_time`
- `keyphrase_score`, `density_score`, `cogency_score`, `final_score`
- `quotes`, `salient_terms`, `keyphrases`, `scene_cuts`
- `file_path`, `text_preview`

## 🔧 Management Commands

### Server Management
```bash
# Start servers
./start-vllm-servers.sh

# Stop servers
docker-compose -f docker-compose.vllm.yml down

# View logs
docker-compose -f docker-compose.vllm.yml logs -f

# Restart specific service
docker-compose -f docker-compose.vllm.yml restart vllm-whisper
```

### Optional Reranker Server
```bash
# Start with reranker (BAAI/bge-reranker-large)
docker-compose -f docker-compose.vllm.yml --profile reranker up -d vllm-reranker
```

### Resource Monitoring
```bash
# GPU utilization
nvidia-smi -l 1

# Container stats
docker stats clipycutter-whisper clipycutter-chat

# Disk usage
du -sh temp_downloads/ rendered_clips/
```

## 🐛 Troubleshooting

### Common Issues

**GPU Memory Issues**
```bash
# Check available memory
nvidia-smi

# Reduce GPU memory utilization in docker-compose.vllm.yml
--gpu-memory-utilization 0.3  # Reduce from 0.4/0.5
```

**Model Download Failures**
```bash
# Pre-download models
docker run --rm -v ~/.cache/huggingface:/root/.cache/huggingface \
  huggingface/transformers-pytorch-gpu python -c \
  "from transformers import AutoModel; AutoModel.from_pretrained('openai/whisper-large-v3')"
```

**FFmpeg/NVENC Issues**
```bash
# Test NVENC support
ffmpeg -encoders | grep nvenc

# Fallback to CPU encoding (edit cut_render.py)
self.has_nvenc = False
```

**Port Conflicts**
```bash
# Check port usage
netstat -tulpn | grep :8000

# Change ports in docker-compose.vllm.yml
ports:
  - "8010:8000"  # External:Internal
```

### Performance Tuning

**Memory Optimization**
- Reduce `--max-model-len` for smaller contexts
- Lower `--gpu-memory-utilization` if running multiple models
- Use `--enable-chunked-prefill` for better memory efficiency

**Speed Optimization**
- Increase `--gpu-memory-utilization` for faster inference
- Use `--tensor-parallel-size` for multi-GPU setups
- Adjust window stride (smaller = more windows, slower processing)

## 📚 API Reference

### CLI Arguments
- `--url`: YouTube video URL (required)
- `--k`: Number of top clips to generate (default: 5)
- `--output-dir`: Output directory for clips (default: rendered_clips)
- `--config`: Custom configuration JSON file
- `--health-check`: Check service health and exit
- `--verbose`: Enable debug logging

### vLLM Server Endpoints
- **Whisper**: `http://localhost:8000/v1/audio/transcriptions`
- **Chat**: `http://localhost:8001/v1/chat/completions`
- **Health**: `http://localhost:800X/health`

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [vLLM](https://vllm.readthedocs.io/) for efficient LLM serving
- [OpenAI Whisper](https://github.com/openai/whisper) for speech recognition
- [Meta Llama](https://llama.meta.com/) for language modeling
- [KeyBERT](https://github.com/MaartenGr/KeyBERT) for keyphrase extraction
- [PySceneDetect](https://github.com/Breakthrough/PySceneDetect) for scene detection

---

**Ready to create viral clips? Start with:**
```bash
./start-vllm-servers.sh
cd backend && python3 cli.py --health-check
```
