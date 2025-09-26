#!/usr/bin/env python3
"""
Test script for the vLLM-based ClipyCutter system.
Validates all components and provides sample usage.
"""

import asyncio
import sys
import os
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent / "backend"))

from app.services.io_youtube import YouTubeDownloader, extract_video_id
from app.services.asr_vllm import VLLMWhisperClient, TranscriptionProcessor
from app.services.windows import WindowGenerator
from app.services.rank_text import HybridRanker, VLLMChatClient
from app.services.cut_render import VideoRenderer


async def test_system_health():
    """Test all system components for health."""
    print("🧪 Testing ClipyCutter vLLM System Health")
    print("=" * 50)
    
    # Test 1: vLLM Whisper Server
    print("1. Testing Whisper Server (port 8000)...")
    whisper_client = VLLMWhisperClient()
    whisper_healthy = await whisper_client.health_check()
    print(f"   {'✅' if whisper_healthy else '❌'} Whisper Server: {'Healthy' if whisper_healthy else 'Unhealthy'}")
    
    # Test 2: vLLM Chat Server
    print("2. Testing Chat Server (port 8001)...")
    chat_client = VLLMChatClient()
    try:
        # Simple test request
        test_result = await chat_client.grade_text_cogency("This is a test sentence for grading.")
        chat_healthy = 'cogency' in test_result
        print(f"   {'✅' if chat_healthy else '❌'} Chat Server: {'Healthy' if chat_healthy else 'Unhealthy'}")
        if chat_healthy:
            print(f"   Sample response: cogency={test_result.get('cogency', 'N/A')}")
    except Exception as e:
        print(f"   ❌ Chat Server: Error - {e}")
        chat_healthy = False
    
    # Test 3: YouTube Downloader
    print("3. Testing YouTube Downloader...")
    try:
        downloader = YouTubeDownloader()
        test_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
        video_id = extract_video_id(test_url)
        info = downloader.get_video_info(test_url)
        print(f"   ✅ YouTube Downloader: Working")
        print(f"   Sample video: {info['title'][:50]}... ({info['duration']}s)")
    except Exception as e:
        print(f"   ❌ YouTube Downloader: Error - {e}")
    
    # Test 4: Video Renderer
    print("4. Testing Video Renderer...")
    try:
        renderer = VideoRenderer()
        nvenc_support = renderer.has_nvenc
        print(f"   {'✅' if nvenc_support else '⚠️'} Video Renderer: {'NVENC Available' if nvenc_support else 'CPU Fallback'}")
    except Exception as e:
        print(f"   ❌ Video Renderer: Error - {e}")
    
    print("\n" + "=" * 50)
    overall_health = whisper_healthy and chat_healthy
    print(f"Overall System Health: {'✅ Ready' if overall_health else '❌ Issues Detected'}")
    
    if not overall_health:
        print("\n💡 Troubleshooting:")
        if not whisper_healthy:
            print("   - Check if vLLM Whisper server is running on port 8000")
            print("   - Run: docker-compose -f docker-compose.vllm.yml logs vllm-whisper")
        if not chat_healthy:
            print("   - Check if vLLM Chat server is running on port 8001")
            print("   - Run: docker-compose -f docker-compose.vllm.yml logs vllm-chat")
    
    return overall_health


async def test_sample_processing():
    """Test processing a short sample."""
    print("\n🎬 Testing Sample Video Processing")
    print("=" * 40)
    
    # Use a short, well-known video for testing
    test_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    
    try:
        # Step 1: Get video info
        print("1. Getting video information...")
        downloader = YouTubeDownloader()
        info = downloader.get_video_info(test_url)
        print(f"   Title: {info['title']}")
        print(f"   Duration: {info['duration']}s")
        
        # For testing, we'll simulate the process without full download
        print("2. Simulating transcription...")
        
        # Create sample transcription data
        sample_transcription = {
            'sentences': [
                {
                    'text': 'This is a sample sentence for testing the ranking system.',
                    'start': 10.0,
                    'end': 15.0,
                    'words': []
                },
                {
                    'text': 'Another sentence with some interesting content about technology.',
                    'start': 20.0,
                    'end': 25.0,
                    'words': []
                }
            ]
        }
        
        print("3. Testing window generation...")
        generator = WindowGenerator()
        
        # Create sample windows
        from app.services.windows import VideoWindow
        windows = [
            VideoWindow(0, 90, "test_window_1"),
            VideoWindow(15, 105, "test_window_2")
        ]
        
        # Add sample transcript segments
        for window in windows:
            window.transcript_segments = [
                {
                    'text': 'This is sample transcript text for testing the ranking algorithm.',
                    'start': window.start_time + 10,
                    'end': window.start_time + 20,
                    'overlap_duration': 10.0
                }
            ]
        
        print(f"   Generated {len(windows)} test windows")
        
        print("4. Testing ranking system...")
        ranker = HybridRanker()
        
        # Score the windows
        scored_windows = []
        for window in windows:
            scores = await ranker.score_window(window)
            scored_windows.append((window, scores))
        
        # Sort by score
        scored_windows.sort(key=lambda x: x[1]['final_score'], reverse=True)
        
        print("   Ranking results:")
        for i, (window, scores) in enumerate(scored_windows):
            print(f"   {i+1}. {window.window_id}: {scores['final_score']:.3f}")
            print(f"      Cogency: {scores['cogency_score']:.3f}")
            print(f"      Keyphrases: {scores['keyphrase_score']:.3f}")
            print(f"      Density: {scores['density_score']:.3f}")
        
        print("\n✅ Sample processing completed successfully!")
        return True
        
    except Exception as e:
        print(f"\n❌ Sample processing failed: {e}")
        return False


async def main():
    """Main test function."""
    print("🎬 ClipyCutter vLLM System Test")
    print("=" * 40)
    
    # Test system health first
    health_ok = await test_system_health()
    
    if health_ok:
        # Run sample processing test
        processing_ok = await test_sample_processing()
        
        if processing_ok:
            print("\n🎉 All tests passed!")
            print("\n🚀 Ready to process videos:")
            print("   cd backend")
            print("   python3 cli.py --url 'https://www.youtube.com/watch?v=VIDEO_ID' --k 3")
        else:
            print("\n⚠️ Processing tests failed, but core system is healthy")
            print("   You can still try processing videos manually")
    else:
        print("\n❌ System health check failed")
        print("   Please ensure vLLM servers are running:")
        print("   ./start-vllm-servers.sh")
    
    return health_ok


if __name__ == "__main__":
    asyncio.run(main())
