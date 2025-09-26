"""
Hybrid text ranking system for video windows.
Combines keyphrases, information density, LLM cogency scoring, and visual penalties.
"""

import asyncio
import aiohttp
import json
import logging
import re
from typing import Dict, List, Any, Optional, Tuple
import numpy as np
from collections import Counter
import math

# KeyBERT and YAKE for keyphrase extraction
from keybert import KeyBERT
import yake

# Scikit-learn for TF-IDF and text features
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from .windows import VideoWindow

logger = logging.getLogger(__name__)


class KeyphraseExtractor:
    """Extract keyphrases using KeyBERT and YAKE."""
    
    def __init__(self):
        self.keybert = KeyBERT()
        self.yake_extractor = yake.KeywordExtractor(
            lan="en",
            n=3,  # n-gram size
            dedupLim=0.7,
            top=20
        )
    
    def extract_keyphrases(self, text: str, method: str = "keybert") -> List[Tuple[str, float]]:
        """
        Extract keyphrases from text.
        
        Args:
            text: Input text
            method: Extraction method ("keybert", "yake", or "both")
            
        Returns:
            List of (keyphrase, score) tuples
        """
        if not text.strip():
            return []
        
        try:
            if method == "keybert":
                return self.keybert.extract_keywords(
                    text, 
                    keyphrase_ngram_range=(1, 3),
                    stop_words='english',
                    top_k=15
                )
            
            elif method == "yake":
                keywords = self.yake_extractor.extract_keywords(text)
                # YAKE returns (score, keyword) - lower score is better
                # Convert to (keyword, 1/score) for consistency
                return [(kw, 1.0 / (score + 1e-6)) for score, kw in keywords]
            
            elif method == "both":
                keybert_kws = self.extract_keyphrases(text, "keybert")
                yake_kws = self.extract_keyphrases(text, "yake")
                
                # Combine and deduplicate
                combined = {}
                for kw, score in keybert_kws:
                    combined[kw] = score
                
                for kw, score in yake_kws:
                    if kw in combined:
                        combined[kw] = (combined[kw] + score) / 2
                    else:
                        combined[kw] = score * 0.5  # Weight YAKE lower
                
                return sorted(combined.items(), key=lambda x: x[1], reverse=True)
            
        except Exception as e:
            logger.error(f"Error extracting keyphrases: {e}")
            return []


class InformationDensityCalculator:
    """Calculate information density metrics for text."""
    
    def __init__(self):
        self.tfidf = TfidfVectorizer(
            stop_words='english',
            ngram_range=(1, 2),
            max_features=1000
        )
        self.is_fitted = False
    
    def fit_corpus(self, texts: List[str]):
        """Fit TF-IDF on corpus of texts."""
        try:
            self.tfidf.fit(texts)
            self.is_fitted = True
        except Exception as e:
            logger.error(f"Error fitting TF-IDF: {e}")
    
    def calculate_density(self, text: str) -> Dict[str, float]:
        """
        Calculate various information density metrics.
        
        Args:
            text: Input text
            
        Returns:
            Dictionary of density metrics
        """
        if not text.strip():
            return {
                'lexical_diversity': 0.0,
                'entropy': 0.0,
                'tfidf_mean': 0.0,
                'tfidf_max': 0.0,
                'content_word_ratio': 0.0,
                'avg_word_length': 0.0
            }
        
        words = text.lower().split()
        
        # Lexical diversity (unique words / total words)
        unique_words = set(words)
        lexical_diversity = len(unique_words) / len(words) if words else 0
        
        # Shannon entropy
        word_counts = Counter(words)
        total_words = len(words)
        entropy = -sum(
            (count / total_words) * math.log2(count / total_words)
            for count in word_counts.values()
        ) if total_words > 0 else 0
        
        # TF-IDF features (if fitted)
        tfidf_mean = 0.0
        tfidf_max = 0.0
        if self.is_fitted:
            try:
                tfidf_vector = self.tfidf.transform([text])
                if tfidf_vector.nnz > 0:  # Non-zero elements
                    tfidf_values = tfidf_vector.data
                    tfidf_mean = np.mean(tfidf_values)
                    tfidf_max = np.max(tfidf_values)
            except Exception as e:
                logger.warning(f"Error calculating TF-IDF: {e}")
        
        # Content word ratio (non-stopwords)
        stopwords = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
            'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'being',
            'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could',
            'should', 'may', 'might', 'can', 'this', 'that', 'these', 'those'
        }
        content_words = [w for w in words if w not in stopwords]
        content_word_ratio = len(content_words) / len(words) if words else 0
        
        # Average word length
        avg_word_length = np.mean([len(w) for w in words]) if words else 0
        
        return {
            'lexical_diversity': lexical_diversity,
            'entropy': entropy,
            'tfidf_mean': tfidf_mean,
            'tfidf_max': tfidf_max,
            'content_word_ratio': content_word_ratio,
            'avg_word_length': avg_word_length
        }


class VLLMChatClient:
    """Client for vLLM chat completions API."""
    
    def __init__(self, base_url: str = "http://localhost:8001"):
        self.base_url = base_url.rstrip('/')
        self.chat_url = f"{self.base_url}/v1/chat/completions"
        self.rerank_url = f"{self.base_url}/v1/rerank"
    
    async def grade_text_cogency(
        self, 
        text: str, 
        model: str = "meta-llama/Llama-3.1-8B-Instruct"
    ) -> Dict[str, Any]:
        """
        Grade text for cogency and extract quotes using LLM.
        
        Args:
            text: Text to grade
            model: LLM model name
            
        Returns:
            Dictionary with cogency score, quotes, and salient terms
        """
        prompt = f"""You grade a 90-second transcript chunk for a short.
Criteria: clear claim → brief reason → one example; minimal dangling pronouns; quote-worthiness.
Output: {{ "cogency": 1-5, "quotes": [up to 3 concise sentences], "salient_terms": [up to 8 non-stopwords] }}
TEXT:
<<<{text}>>>"""
        
        try:
            payload = {
                "model": model,
                "messages": [
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.1,
                "max_tokens": 500,
                "response_format": {"type": "json_object"}
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(self.chat_url, json=payload) as response:
                    if response.status == 200:
                        result = await response.json()
                        content = result['choices'][0]['message']['content']
                        
                        try:
                            parsed = json.loads(content)
                            return {
                                'cogency': parsed.get('cogency', 1),
                                'quotes': parsed.get('quotes', []),
                                'salient_terms': parsed.get('salient_terms', []),
                                'raw_response': content
                            }
                        except json.JSONDecodeError:
                            logger.error(f"Failed to parse LLM JSON response: {content}")
                            return {
                                'cogency': 1,
                                'quotes': [],
                                'salient_terms': [],
                                'raw_response': content
                            }
                    else:
                        error_text = await response.text()
                        logger.error(f"Chat API error: {response.status} - {error_text}")
                        raise Exception(f"Chat API error: {response.status}")
                        
        except Exception as e:
            logger.error(f"Error grading text cogency: {e}")
            return {
                'cogency': 1,
                'quotes': [],
                'salient_terms': [],
                'error': str(e)
            }
    
    async def rerank_texts(
        self, 
        query: str, 
        documents: List[str], 
        model: str = "BAAI/bge-reranker-large"
    ) -> List[Dict[str, Any]]:
        """
        Rerank documents using cross-encoder model.
        
        Args:
            query: Query text
            documents: List of documents to rerank
            model: Reranker model name
            
        Returns:
            List of reranked documents with scores
        """
        try:
            payload = {
                "model": model,
                "query": query,
                "documents": documents,
                "top_n": len(documents)
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(self.rerank_url, json=payload) as response:
                    if response.status == 200:
                        result = await response.json()
                        return result.get('results', [])
                    else:
                        error_text = await response.text()
                        logger.error(f"Rerank API error: {response.status} - {error_text}")
                        return []
                        
        except Exception as e:
            logger.error(f"Error reranking texts: {e}")
            return []


class HybridRanker:
    """Hybrid ranking system combining multiple scoring methods."""
    
    def __init__(self, chat_client: VLLMChatClient = None):
        self.keyphrase_extractor = KeyphraseExtractor()
        self.density_calculator = InformationDensityCalculator()
        self.chat_client = chat_client or VLLMChatClient()
        
        # Scoring weights
        self.weights = {
            'keyphrase_coverage': 0.35,
            'info_density': 0.20,
            'llm_cogency': 0.25,
            'quote_bonus': 0.10,
            'scene_cut_penalty': 0.05,
            'filler_penalty': 0.05
        }
    
    def fit_corpus(self, windows: List[VideoWindow]):
        """Fit models on corpus of window texts."""
        texts = []
        for window in windows:
            text = self._extract_window_text(window)
            if text:
                texts.append(text)
        
        if texts:
            self.density_calculator.fit_corpus(texts)
    
    def _extract_window_text(self, window: VideoWindow) -> str:
        """Extract text from window transcript segments."""
        texts = []
        for segment in window.transcript_segments:
            texts.append(segment.get('text', ''))
        return ' '.join(texts)
    
    async def score_window(self, window: VideoWindow) -> Dict[str, Any]:
        """
        Calculate comprehensive score for a video window.
        
        Args:
            window: VideoWindow to score
            
        Returns:
            Dictionary with scores and components
        """
        text = self._extract_window_text(window)
        
        if not text.strip():
            return {
                'final_score': 0.0,
                'keyphrase_score': 0.0,
                'density_score': 0.0,
                'cogency_score': 0.0,
                'quote_bonus': 0.0,
                'scene_penalty': 0.0,
                'filler_penalty': 0.0,
                'components': {},
                'text': text
            }
        
        # Extract keyphrases
        keyphrases = self.keyphrase_extractor.extract_keyphrases(text, method="both")
        
        # Calculate information density
        density_metrics = self.density_calculator.calculate_density(text)
        
        # Get LLM grading
        llm_grading = await self.chat_client.grade_text_cogency(text)
        
        # Calculate component scores
        keyphrase_score = self._calculate_keyphrase_score(keyphrases, text)
        density_score = self._calculate_density_score(density_metrics)
        cogency_score = llm_grading['cogency'] / 5.0  # Normalize to 0-1
        quote_bonus = len(llm_grading['quotes']) * 0.1  # Bonus for quotable content
        
        # Calculate penalties
        scene_penalty = len(window.scene_cuts) * 0.1
        filler_penalty = self._calculate_filler_penalty(text)
        
        # Calculate final score
        final_score = (
            self.weights['keyphrase_coverage'] * keyphrase_score +
            self.weights['info_density'] * density_score +
            self.weights['llm_cogency'] * cogency_score +
            self.weights['quote_bonus'] * quote_bonus -
            self.weights['scene_cut_penalty'] * scene_penalty -
            self.weights['filler_penalty'] * filler_penalty
        )
        
        return {
            'final_score': max(0.0, final_score),  # Ensure non-negative
            'keyphrase_score': keyphrase_score,
            'density_score': density_score,
            'cogency_score': cogency_score,
            'quote_bonus': quote_bonus,
            'scene_penalty': scene_penalty,
            'filler_penalty': filler_penalty,
            'components': {
                'keyphrases': keyphrases[:10],  # Top 10
                'density_metrics': density_metrics,
                'llm_grading': llm_grading,
                'scene_cuts': len(window.scene_cuts),
                'word_count': len(text.split())
            },
            'text': text
        }
    
    def _calculate_keyphrase_score(self, keyphrases: List[Tuple[str, float]], text: str) -> float:
        """Calculate keyphrase coverage score."""
        if not keyphrases:
            return 0.0
        
        # Weight by keyphrase importance and coverage
        total_score = 0.0
        text_lower = text.lower()
        
        for phrase, importance in keyphrases:
            # Count occurrences
            occurrences = text_lower.count(phrase.lower())
            coverage = min(occurrences / 3.0, 1.0)  # Cap at 3 occurrences
            total_score += importance * coverage
        
        # Normalize by number of keyphrases
        return min(total_score / len(keyphrases), 1.0)
    
    def _calculate_density_score(self, metrics: Dict[str, float]) -> float:
        """Calculate information density score."""
        # Weighted combination of density metrics
        score = (
            0.3 * metrics['lexical_diversity'] +
            0.2 * min(metrics['entropy'] / 5.0, 1.0) +  # Normalize entropy
            0.2 * metrics['tfidf_mean'] +
            0.15 * metrics['content_word_ratio'] +
            0.15 * min(metrics['avg_word_length'] / 6.0, 1.0)  # Normalize word length
        )
        
        return min(score, 1.0)
    
    def _calculate_filler_penalty(self, text: str) -> float:
        """Calculate penalty for filler words and phrases."""
        filler_patterns = [
            r'\b(um|uh|er|ah|like|you know|sort of|kind of)\b',
            r'\b(basically|actually|literally|obviously)\b',
            r'\b(i mean|i think|i guess|i suppose)\b'
        ]
        
        text_lower = text.lower()
        total_fillers = 0
        
        for pattern in filler_patterns:
            matches = re.findall(pattern, text_lower)
            total_fillers += len(matches)
        
        word_count = len(text.split())
        filler_ratio = total_fillers / word_count if word_count > 0 else 0
        
        return min(filler_ratio * 2.0, 1.0)  # Cap penalty at 1.0
    
    async def rank_windows(
        self, 
        windows: List[VideoWindow], 
        top_k: int = 5
    ) -> List[Tuple[VideoWindow, Dict[str, Any]]]:
        """
        Rank all windows and return top K.
        
        Args:
            windows: List of VideoWindow objects
            top_k: Number of top windows to return
            
        Returns:
            List of (window, scores) tuples, sorted by score
        """
        # Fit models on corpus
        self.fit_corpus(windows)
        
        # Score all windows
        scored_windows = []
        for window in windows:
            scores = await self.score_window(window)
            scored_windows.append((window, scores))
        
        # Sort by final score
        scored_windows.sort(key=lambda x: x[1]['final_score'], reverse=True)
        
        return scored_windows[:top_k]


if __name__ == "__main__":
    # Test the ranking system
    async def test_ranker():
        ranker = HybridRanker()
        
        # Create test windows with sample text
        test_texts = [
            "This is a fascinating discussion about artificial intelligence and its impact on society. The key insight is that AI will transform how we work.",
            "Um, so like, I think that, you know, this is basically just another way to, uh, do the same thing we've always done.",
            "The breakthrough came when researchers discovered that neural networks could learn complex patterns. This revolutionized machine learning completely."
        ]
        
        windows = []
        for i, text in enumerate(test_texts):
            window = VideoWindow(i * 90, (i + 1) * 90, f"test_window_{i}")
            window.transcript_segments = [{'text': text, 'start': i * 90, 'end': (i + 1) * 90}]
            window.scene_cuts = [i * 45] if i > 0 else []  # Add some scene cuts
            windows.append(window)
        
        # Rank windows
        ranked = await ranker.rank_windows(windows, top_k=3)
        
        print("Ranking Results:")
        for i, (window, scores) in enumerate(ranked):
            print(f"\n{i+1}. {window.window_id} (Score: {scores['final_score']:.3f})")
            print(f"   Text: {scores['text'][:100]}...")
            print(f"   Keyphrase: {scores['keyphrase_score']:.3f}")
            print(f"   Density: {scores['density_score']:.3f}")
            print(f"   Cogency: {scores['cogency_score']:.3f}")
            print(f"   Quotes: {len(scores['components']['llm_grading']['quotes'])}")
    
    asyncio.run(test_ranker())
