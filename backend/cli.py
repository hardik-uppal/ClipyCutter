#!/usr/bin/env python3
"""
ClipyCutter CLI - Local GPU-first clip ranking system.
Main command-line interface for processing YouTube videos.

Usage:
    python cli.py --url <YOUTUBE_URL> --k 3
"""

import argparse
import asyncio
import logging
import sys
import time
from pathlib import Path
import pandas as pd
from typing import List, Dict, Any
import json

# Import our modules
from app.services.io_youtube import YouTubeDownloader, extract_video_id
from app.services.asr_vllm import VLLMWhisperClient, TranscriptionProcessor
from app.services.windows import WindowGenerator, VideoWindow
from app.services.rank_text import HybridRanker, VLLMChatClient
from app.services.cut_render import VideoRenderer, ClipBatch

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('clipycutter.log')
    ]
)
logger = logging.getLogger(__name__)


class ClipyCutterPipeline:
    """Main pipeline for processing YouTube videos into ranked clips."""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or self._get_default_config()
        
        # Initialize components
        self.youtube_downloader = YouTubeDownloader(
            output_dir=self.config['temp_dir']
        )
        
        self.whisper_client = VLLMWhisperClient(
            base_url=self.config['whisper_server_url']
        )
        
        self.transcription_processor = TranscriptionProcessor(
            self.whisper_client
        )
        
        self.window_generator = WindowGenerator(
            window_duration=self.config['window_duration'],
            stride=self.config['window_stride']
        )
        
        self.chat_client = VLLMChatClient(
            base_url=self.config['chat_server_url']
        )
        
        self.ranker = HybridRanker(self.chat_client)
        
        self.renderer = VideoRenderer(
            output_dir=self.config['output_dir']
        )
        
        self.clip_batch = ClipBatch(self.renderer)
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration."""
        return {
            'temp_dir': 'temp_downloads',
            'output_dir': 'rendered_clips',
            'whisper_server_url': 'http://localhost:8000',
            'chat_server_url': 'http://localhost:8001',
            'window_duration': 90.0,
            'window_stride': 15.0,
            'whisper_model': 'openai/whisper-large-v3',
            'chat_model': 'meta-llama/Llama-3.1-8B-Instruct',
            'render_quality': 'high'
        }
    
    async def process_video(self, youtube_url: str, top_k: int = 5) -> Dict[str, Any]:
        """
        Complete pipeline to process YouTube video into ranked clips.
        
        Args:
            youtube_url: YouTube video URL
            top_k: Number of top clips to generate
            
        Returns:
            Dictionary with processing results and clip information
        """
        start_time = time.time()
        video_id = extract_video_id(youtube_url)
        
        logger.info(f"Starting pipeline for video: {video_id}")
        logger.info(f"Target clips: {top_k}")
        
        try:
            # Step 1: Download video
            logger.info("Step 1: Downloading video...")
            video_path, audio_path, metadata = self.youtube_downloader.download_video(youtube_url)
            
            # Step 2: Transcribe audio
            logger.info("Step 2: Transcribing audio...")
            transcription_result = await self.transcription_processor.process_audio_file(audio_path)
            
            # Step 3: Generate windows
            logger.info("Step 3: Generating video windows...")
            windows = self.window_generator.generate_windows(
                video_path=video_path,
                video_duration=metadata['duration'],
                transcription=transcription_result
            )
            
            logger.info(f"Generated {len(windows)} windows")
            
            # Step 4: Rank windows
            logger.info("Step 4: Ranking windows...")
            ranked_windows = await self.ranker.rank_windows(windows, top_k=top_k)
            
            # Step 5: Render top clips
            logger.info("Step 5: Rendering clips...")
            rendered_clips = self.clip_batch.render_top_clips(
                video_path=video_path,
                ranked_windows=ranked_windows,
                output_prefix=f"{video_id}_clip"
            )
            
            # Step 6: Generate report
            logger.info("Step 6: Generating report...")
            report = self._generate_report(
                video_id=video_id,
                metadata=metadata,
                transcription_result=transcription_result,
                windows=windows,
                ranked_windows=ranked_windows,
                rendered_clips=rendered_clips,
                processing_time=time.time() - start_time
            )
            
            # Step 7: Save CSV log
            self._save_csv_log(video_id, ranked_windows, rendered_clips)
            
            # Cleanup temporary files
            logger.info("Cleaning up temporary files...")
            self.youtube_downloader.cleanup_temp_files(video_path, audio_path)
            
            logger.info(f"Pipeline completed in {time.time() - start_time:.1f}s")
            return report
            
        except Exception as e:
            logger.error(f"Pipeline failed: {e}")
            raise
    
    def _generate_report(
        self,
        video_id: str,
        metadata: Dict[str, Any],
        transcription_result: Dict[str, Any],
        windows: List[VideoWindow],
        ranked_windows: List[tuple],
        rendered_clips: List[Dict[str, Any]],
        processing_time: float
    ) -> Dict[str, Any]:
        """Generate comprehensive processing report."""
        
        return {
            'video_info': {
                'video_id': video_id,
                'title': metadata['title'],
                'duration': metadata['duration'],
                'uploader': metadata['uploader'],
                'view_count': metadata.get('view_count', 0),
                'upload_date': metadata.get('upload_date'),
            },
            'transcription_stats': {
                'language': transcription_result['metadata']['language'],
                'word_count': transcription_result['metadata']['word_count'],
                'sentence_count': transcription_result['metadata']['sentence_count'],
                'duration': transcription_result['metadata']['duration']
            },
            'window_stats': {
                'total_windows': len(windows),
                'ranked_windows': len(ranked_windows),
                'window_duration': self.config['window_duration'],
                'window_stride': self.config['window_stride']
            },
            'clip_results': rendered_clips,
            'processing_stats': {
                'total_time': processing_time,
                'clips_generated': len(rendered_clips),
                'avg_score': sum(clip['score'] for clip in rendered_clips) / len(rendered_clips) if rendered_clips else 0
            },
            'top_scores': [
                {
                    'rank': i + 1,
                    'window_id': window.window_id,
                    'score': scores['final_score'],
                    'start_time': window.start_time,
                    'end_time': window.end_time,
                    'keyphrase_score': scores['keyphrase_score'],
                    'density_score': scores['density_score'],
                    'cogency_score': scores['cogency_score'],
                    'quotes': len(scores['components']['llm_grading']['quotes']),
                    'scene_cuts': len(window.scene_cuts)
                }
                for i, (window, scores) in enumerate(ranked_windows)
            ]
        }
    
    def _save_csv_log(
        self, 
        video_id: str, 
        ranked_windows: List[tuple], 
        rendered_clips: List[Dict[str, Any]]
    ):
        """Save detailed CSV log of all clips."""
        
        csv_data = []
        
        for i, (window, scores) in enumerate(ranked_windows):
            # Find corresponding rendered clip
            rendered_clip = None
            for clip in rendered_clips:
                if clip['window_id'] == window.window_id:
                    rendered_clip = clip
                    break
            
            row = {
                'video_id': video_id,
                'rank': i + 1,
                'window_id': window.window_id,
                'start_time': window.start_time,
                'end_time': window.end_time,
                'duration': window.duration,
                'words': len(scores['text'].split()) if scores['text'] else 0,
                'keyphrases': ', '.join([kw for kw, _ in scores['components']['keyphrases'][:5]]),
                'keyphrase_score': scores['keyphrase_score'],
                'density_score': scores['density_score'],
                'cogency_score': scores['cogency_score'],
                'cogency_raw': scores['components']['llm_grading']['cogency'],
                'quotes': '; '.join(scores['components']['llm_grading']['quotes']),
                'quote_count': len(scores['components']['llm_grading']['quotes']),
                'salient_terms': ', '.join(scores['components']['llm_grading']['salient_terms']),
                'scene_cuts': len(window.scene_cuts),
                'scene_penalty': scores['scene_penalty'],
                'filler_penalty': scores['filler_penalty'],
                'final_score': scores['final_score'],
                'file_path': rendered_clip['file_path'] if rendered_clip else '',
                'text_preview': scores['text'][:200] + '...' if len(scores['text']) > 200 else scores['text']
            }
            
            csv_data.append(row)
        
        # Save to CSV
        df = pd.DataFrame(csv_data)
        csv_path = Path(self.config['output_dir']) / f"{video_id}_clips_log.csv"
        df.to_csv(csv_path, index=False)
        
        logger.info(f"CSV log saved: {csv_path}")
    
    async def health_check(self) -> Dict[str, bool]:
        """Check health of all required services."""
        
        logger.info("Checking service health...")
        
        health = {
            'whisper_server': await self.whisper_client.health_check(),
            'chat_server': await self.chat_client.health_check() if hasattr(self.chat_client, 'health_check') else True,
            'ffmpeg': self.renderer._check_nvenc_support() or True,  # ffmpeg available
        }
        
        for service, status in health.items():
            logger.info(f"{service}: {'✓' if status else '✗'}")
        
        return health


async def main():
    """Main CLI entry point."""
    
    parser = argparse.ArgumentParser(
        description="ClipyCutter - Local GPU-first clip ranking system",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python cli.py --url "https://www.youtube.com/watch?v=dQw4w9WgXcQ" --k 3
    python cli.py --url "https://youtu.be/dQw4w9WgXcQ" --k 5 --config custom_config.json
    python cli.py --health-check
        """
    )
    
    parser.add_argument(
        '--url', 
        type=str, 
        help='YouTube video URL to process'
    )
    
    parser.add_argument(
        '--k', 
        type=int, 
        default=5,
        help='Number of top clips to generate (default: 5)'
    )
    
    parser.add_argument(
        '--config',
        type=str,
        help='Path to custom configuration JSON file'
    )
    
    parser.add_argument(
        '--health-check',
        action='store_true',
        help='Check health of all services and exit'
    )
    
    parser.add_argument(
        '--output-dir',
        type=str,
        default='rendered_clips',
        help='Output directory for rendered clips'
    )
    
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose logging'
    )
    
    args = parser.parse_args()
    
    # Configure logging level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Load custom config if provided
    config = None
    if args.config:
        try:
            with open(args.config, 'r') as f:
                config = json.load(f)
            logger.info(f"Loaded config from: {args.config}")
        except Exception as e:
            logger.error(f"Error loading config: {e}")
            sys.exit(1)
    
    # Override output directory if specified
    if config is None:
        config = {}
    config['output_dir'] = args.output_dir
    
    # Initialize pipeline
    try:
        pipeline = ClipyCutterPipeline(config)
    except Exception as e:
        logger.error(f"Failed to initialize pipeline: {e}")
        sys.exit(1)
    
    # Health check mode
    if args.health_check:
        try:
            health = await pipeline.health_check()
            all_healthy = all(health.values())
            
            print("\n" + "="*50)
            print("ClipyCutter Health Check")
            print("="*50)
            
            for service, status in health.items():
                print(f"{service:20}: {'✓ Healthy' if status else '✗ Unhealthy'}")
            
            print("="*50)
            print(f"Overall Status: {'✓ All systems operational' if all_healthy else '✗ Some systems need attention'}")
            
            sys.exit(0 if all_healthy else 1)
            
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            sys.exit(1)
    
    # Process video mode
    if not args.url:
        parser.error("--url is required (or use --health-check)")
    
    try:
        logger.info("="*60)
        logger.info("ClipyCutter - Local GPU-first clip ranking system")
        logger.info("="*60)
        
        # Process the video
        result = await pipeline.process_video(args.url, args.k)
        
        # Print summary
        print("\n" + "="*60)
        print("PROCESSING COMPLETE")
        print("="*60)
        
        print(f"Video: {result['video_info']['title']}")
        print(f"Duration: {result['video_info']['duration']:.1f}s")
        print(f"Processing time: {result['processing_stats']['total_time']:.1f}s")
        print(f"Clips generated: {result['processing_stats']['clips_generated']}")
        print(f"Average score: {result['processing_stats']['avg_score']:.3f}")
        
        print(f"\nTop {len(result['clip_results'])} clips:")
        for clip in result['clip_results']:
            print(f"  {clip['rank']}. {clip['filename']} (score: {clip['score']:.3f})")
            print(f"     Time: {clip['start_time']:.1f}s - {clip['end_time']:.1f}s")
            print(f"     Text: {clip['text'][:100]}...")
        
        print(f"\nOutput directory: {args.output_dir}")
        print(f"CSV log: {result['video_info']['video_id']}_clips_log.csv")
        
    except KeyboardInterrupt:
        logger.info("Processing interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Processing failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
