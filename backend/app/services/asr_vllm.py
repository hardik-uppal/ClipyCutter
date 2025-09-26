"""
vLLM Whisper ASR client for transcription with word-level timestamps.
Connects to vLLM server running Whisper-Large-V3 model.
"""

import asyncio
import aiohttp
import json
import logging
from typing import Dict, List, Any, Optional
from pathlib import Path
import time

logger = logging.getLogger(__name__)


class VLLMWhisperClient:
    """Client for vLLM Whisper transcription API."""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url.rstrip('/')
        self.transcription_url = f"{self.base_url}/v1/audio/transcriptions"
        
    async def transcribe_audio(
        self, 
        audio_path: str, 
        model: str = "openai/whisper-large-v3",
        response_format: str = "verbose_json",
        timestamp_granularities: List[str] = None
    ) -> Dict[str, Any]:
        """
        Transcribe audio file using vLLM Whisper API.
        
        Args:
            audio_path: Path to audio file
            model: Whisper model name
            response_format: Response format (json, text, srt, verbose_json, vtt)
            timestamp_granularities: List of timestamp granularities (word, segment)
            
        Returns:
            Transcription result with timestamps
        """
        if timestamp_granularities is None:
            timestamp_granularities = ["word", "segment"]
            
        try:
            # Prepare the multipart form data
            data = aiohttp.FormData()
            data.add_field('model', model)
            data.add_field('response_format', response_format)
            data.add_field('timestamp_granularities', json.dumps(timestamp_granularities))
            
            # Add the audio file
            with open(audio_path, 'rb') as audio_file:
                data.add_field('file', audio_file, filename=Path(audio_path).name)
                
                async with aiohttp.ClientSession() as session:
                    start_time = time.time()
                    async with session.post(self.transcription_url, data=data) as response:
                        if response.status == 200:
                            result = await response.json()
                            duration = time.time() - start_time
                            logger.info(f"Transcription completed in {duration:.2f}s")
                            return result
                        else:
                            error_text = await response.text()
                            logger.error(f"Transcription failed: {response.status} - {error_text}")
                            raise Exception(f"Transcription API error: {response.status}")
                            
        except Exception as e:
            logger.error(f"Error during transcription: {e}")
            raise
    
    async def health_check(self) -> bool:
        """Check if the vLLM Whisper server is healthy."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.base_url}/health") as response:
                    return response.status == 200
        except Exception as e:
            logger.warning(f"Health check failed: {e}")
            return False
    
    def process_transcription_result(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process and structure the transcription result.
        
        Args:
            result: Raw transcription result from vLLM
            
        Returns:
            Processed transcription with structured segments and words
        """
        processed = {
            'text': result.get('text', ''),
            'language': result.get('language', 'en'),
            'duration': result.get('duration', 0),
            'segments': [],
            'words': []
        }
        
        # Process segments
        for segment in result.get('segments', []):
            processed_segment = {
                'id': segment.get('id'),
                'start': segment.get('start'),
                'end': segment.get('end'),
                'text': segment.get('text'),
                'words': []
            }
            
            # Process words within segment
            for word in segment.get('words', []):
                word_data = {
                    'word': word.get('word'),
                    'start': word.get('start'),
                    'end': word.get('end'),
                    'probability': word.get('probability', 1.0)
                }
                processed_segment['words'].append(word_data)
                processed['words'].append(word_data)
            
            processed['segments'].append(processed_segment)
        
        return processed
    
    def align_to_sentences(self, transcription: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Align word-level timestamps to sentence boundaries.
        
        Args:
            transcription: Processed transcription result
            
        Returns:
            List of sentences with start/end times and words
        """
        import re
        
        sentences = []
        current_sentence = {
            'text': '',
            'start': None,
            'end': None,
            'words': []
        }
        
        # Sentence boundary patterns
        sentence_endings = re.compile(r'[.!?]+')
        
        for word_data in transcription['words']:
            word = word_data['word'].strip()
            
            if current_sentence['start'] is None:
                current_sentence['start'] = word_data['start']
            
            current_sentence['text'] += word + ' '
            current_sentence['end'] = word_data['end']
            current_sentence['words'].append(word_data)
            
            # Check if this word ends a sentence
            if sentence_endings.search(word):
                # Finalize current sentence
                current_sentence['text'] = current_sentence['text'].strip()
                sentences.append(current_sentence.copy())
                
                # Start new sentence
                current_sentence = {
                    'text': '',
                    'start': None,
                    'end': None,
                    'words': []
                }
        
        # Add any remaining words as a final sentence
        if current_sentence['words']:
            current_sentence['text'] = current_sentence['text'].strip()
            sentences.append(current_sentence)
        
        return sentences


class TranscriptionProcessor:
    """Higher-level processor for handling transcription workflows."""
    
    def __init__(self, whisper_client: VLLMWhisperClient):
        self.whisper_client = whisper_client
    
    async def process_audio_file(self, audio_path: str) -> Dict[str, Any]:
        """
        Complete transcription processing pipeline.
        
        Args:
            audio_path: Path to audio file
            
        Returns:
            Complete transcription with sentences and metadata
        """
        try:
            # Check if server is healthy
            if not await self.whisper_client.health_check():
                raise Exception("vLLM Whisper server is not healthy")
            
            # Transcribe audio
            raw_result = await self.whisper_client.transcribe_audio(audio_path)
            
            # Process the result
            transcription = self.whisper_client.process_transcription_result(raw_result)
            
            # Align to sentences
            sentences = self.whisper_client.align_to_sentences(transcription)
            
            return {
                'transcription': transcription,
                'sentences': sentences,
                'metadata': {
                    'audio_path': audio_path,
                    'language': transcription['language'],
                    'duration': transcription['duration'],
                    'word_count': len(transcription['words']),
                    'sentence_count': len(sentences)
                }
            }
            
        except Exception as e:
            logger.error(f"Error processing audio file: {e}")
            raise


async def main():
    """Test the vLLM Whisper client."""
    client = VLLMWhisperClient()
    processor = TranscriptionProcessor(client)
    
    # Test with a sample audio file (you'll need to provide this)
    test_audio = "test_audio.wav"
    
    if Path(test_audio).exists():
        try:
            result = await processor.process_audio_file(test_audio)
            print(f"Transcribed {result['metadata']['word_count']} words")
            print(f"Found {result['metadata']['sentence_count']} sentences")
            print(f"Duration: {result['metadata']['duration']:.2f}s")
            
            # Print first few sentences
            for i, sentence in enumerate(result['sentences'][:3]):
                print(f"Sentence {i+1}: {sentence['text']}")
                print(f"  Time: {sentence['start']:.2f}s - {sentence['end']:.2f}s")
                
        except Exception as e:
            print(f"Error: {e}")
    else:
        print(f"Test audio file not found: {test_audio}")


if __name__ == "__main__":
    asyncio.run(main())
