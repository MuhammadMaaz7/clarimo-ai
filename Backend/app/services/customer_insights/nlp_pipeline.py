"""
NLP Pipeline Service - Handle embeddings, clustering, and text processing for Customer Insights
"""
import logging
import re
import numpy as np
from typing import List, Dict, Any, Tuple
from sentence_transformers import SentenceTransformer
import hdbscan
from sklearn.cluster import KMeans
from sklearn.preprocessing import normalize
import emoji

# Reuse existing services
from app.services.problem_discovery.embedding_service import get_global_model, fast_clean
from app.services.shared.embedding_cache import get_global_cache

# Configure logging
logger = logging.getLogger(__name__)

# Constants
MIN_CLUSTER_SIZE = 5
MIN_WORDS_KEEP = 8

class NLPPipeline:
    """NLP Pipeline for Customer Insights - reuses existing embedding and clustering infrastructure"""
    
    def __init__(self):
        self.model = get_global_model(use_gpu=False)
        self.cache = get_global_cache()
    
    def clean_text(self, text: str) -> str:
        """Clean and preprocess text - reuses existing fast_clean function"""
        if not text or not isinstance(text, str):
            return ""
        
        # Use existing optimized cleaning function
        cleaned = fast_clean(text, keep_emojis=False)
        
        # Additional filtering for customer insights
        words = cleaned.split()
        if len(words) < MIN_WORDS_KEEP:
            return ""
        
        return cleaned
    
    async def generate_embeddings(self, texts: List[str]) -> np.ndarray:
        """
        Generate embeddings for texts using optimized cache
        
        Args:
            texts: List of text strings to embed
            
        Returns:
            Numpy array of embeddings
        """
        if not texts:
            return np.array([])
        
        try:
            logger.info(f"Generating embeddings for {len(texts)} texts...")
            
            # Try to get embeddings from cache
            cached_embeddings = []
            missing_texts = []
            missing_indices = []
            
            for idx, text in enumerate(texts):
                cached_embedding, cache_type = self.cache.get_cached_embedding(text)
                if cached_embedding is not None:
                    cached_embeddings.append((idx, cached_embedding))
                else:
                    missing_texts.append(text)
                    missing_indices.append(idx)
            
            # Calculate cache hit rate
            cache_hits = len(cached_embeddings)
            cache_hit_rate = (cache_hits / len(texts) * 100) if texts else 0
            
            if cache_hits > 0:
                logger.info(f"🚀 Cache hit rate: {cache_hit_rate:.1f}% ({cache_hits}/{len(texts)} embeddings)")
            
            # Generate missing embeddings
            if missing_texts:
                logger.info(f"Generating {len(missing_texts)} new embeddings...")
                
                new_embeddings = self.model.encode(
                    missing_texts,
                    show_progress_bar=True,
                    convert_to_numpy=True,
                    batch_size=128,
                    normalize_embeddings=True
                )
                
                # Cache new embeddings
                for text, embedding in zip(missing_texts, new_embeddings):
                    self.cache.cache_embedding(text, embedding)
                
                # Combine cached and new embeddings
                all_embeddings = [None] * len(texts)
                
                # Fill in cached embeddings
                for idx, embedding in cached_embeddings:
                    all_embeddings[idx] = embedding
                
                # Fill in new embeddings
                for idx, embedding in zip(missing_indices, new_embeddings):
                    all_embeddings[idx] = embedding
                
                embeddings = np.array(all_embeddings)
            else:
                # All embeddings were cached
                embeddings = np.array([emb for _, emb in sorted(cached_embeddings, key=lambda x: x[0])])
            
            logger.info(f"✅ Generated embeddings with shape: {embeddings.shape}")
            return embeddings
            
        except Exception as e:
            logger.error(f"Error generating embeddings: {str(e)}")
            return np.array([])
    
    def cluster_discussions(
        self, 
        embeddings: np.ndarray, 
        min_cluster_size: int = MIN_CLUSTER_SIZE
    ) -> np.ndarray:
        """
        Cluster embeddings using HDBSCAN with KMeans fallback
        
        Args:
            embeddings: Numpy array of embeddings
            min_cluster_size: Minimum cluster size for HDBSCAN
            
        Returns:
            Numpy array of cluster labels
        """
        if len(embeddings) == 0:
            return np.array([])
        
        try:
            n_samples = len(embeddings)
            
            # Adjust min_cluster_size based on dataset size
            adjusted_min_size = min(min_cluster_size, max(3, n_samples // 10))
            
            logger.info(f"Clustering {n_samples} embeddings with HDBSCAN (min_cluster_size={adjusted_min_size})")
            
            # Try HDBSCAN first
            try:
                clusterer = hdbscan.HDBSCAN(
                    min_cluster_size=adjusted_min_size,
                    min_samples=2,
                    metric='euclidean',
                    cluster_selection_method='eom'
                )
                
                cluster_labels = clusterer.fit_predict(embeddings)
                
                # Count clusters (excluding noise cluster -1)
                unique_labels = set(cluster_labels)
                n_clusters = len(unique_labels) - (1 if -1 in unique_labels else 0)
                n_noise = list(cluster_labels).count(-1)
                
                logger.info(f"HDBSCAN found {n_clusters} clusters with {n_noise} noise points")
                
                # If too many noise points or too few clusters, fallback to KMeans
                if n_noise > n_samples * 0.5 or n_clusters < 2:
                    logger.info("Too many noise points or too few clusters, falling back to KMeans")
                    raise ValueError("HDBSCAN produced poor clustering")
                
                return cluster_labels
                
            except Exception as hdbscan_error:
                logger.warning(f"HDBSCAN failed: {str(hdbscan_error)}, falling back to KMeans")
                
                # Fallback to KMeans
                n_clusters = min(8, max(3, n_samples // 20))
                logger.info(f"Using KMeans with {n_clusters} clusters")
                
                kmeans = KMeans(
                    n_clusters=n_clusters,
                    random_state=42,
                    n_init=10
                )
                
                cluster_labels = kmeans.fit_predict(embeddings)
                
                logger.info(f"KMeans found {n_clusters} clusters")
                return cluster_labels
                
        except Exception as e:
            logger.error(f"Error clustering embeddings: {str(e)}")
            return np.array([])
    
    def extract_keywords(self, texts: List[str], top_n: int = 10) -> List[str]:
        """
        Extract keywords from texts using simple frequency-based approach
        
        Args:
            texts: List of text strings
            top_n: Number of top keywords to return
            
        Returns:
            List of top keywords
        """
        try:
            # Combine all texts
            combined_text = " ".join(texts)
            
            # Clean and tokenize
            cleaned = self.clean_text(combined_text)
            words = cleaned.split()
            
            # Filter out common stop words
            stop_words = {
                'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
                'of', 'with', 'by', 'from', 'as', 'is', 'was', 'are', 'were', 'been',
                'be', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would',
                'could', 'should', 'may', 'might', 'can', 'this', 'that', 'these',
                'those', 'i', 'you', 'he', 'she', 'it', 'we', 'they', 'my', 'your',
                'his', 'her', 'its', 'our', 'their', 'me', 'him', 'us', 'them'
            }
            
            # Count word frequencies
            word_freq = {}
            for word in words:
                if len(word) > 3 and word.lower() not in stop_words:
                    word_freq[word.lower()] = word_freq.get(word.lower(), 0) + 1
            
            # Sort by frequency and return top N
            sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
            keywords = [word for word, freq in sorted_words[:top_n]]
            
            logger.info(f"Extracted {len(keywords)} keywords from {len(texts)} texts")
            return keywords
            
        except Exception as e:
            logger.error(f"Error extracting keywords: {str(e)}")
            return []

# Create global instance
nlp_pipeline = NLPPipeline()
