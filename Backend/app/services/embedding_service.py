"""
Embedding Service - Direct integration of embedding generation without external scripts
"""
import os
import json
import asyncio
import logging
import re
from pathlib import Path
from typing import Dict, Any, Optional, List
import numpy as np
import pandas as pd
from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor

# Fast JSON serialization
try:
    import orjson
    HAS_ORJSON = True
except ImportError:
    HAS_ORJSON = False

# NLP / utils
from langdetect import detect, DetectorFactory
import emoji

# Embedding model
from sentence_transformers import SentenceTransformer
import torch   
# FAISS
import faiss

# Optimized cache
from .optimized_embedding_cache import OptimizedEmbeddingCache

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Stable langdetect
DetectorFactory.seed = 0

# ------------------------
# CONFIG - BALANCED FOR PERFORMANCE AND QUALITY
# ------------------------
MODEL_NAME = "mixedbread-ai/mxbai-embed-large-v1"
# DEFAULT_BATCH_SIZE = 256  # Larger batch size for better CPU throughput
# MIN_WORDS_KEEP = 12  # Balanced threshold - not too aggressive
# CHUNK_MAX_WORDS = 350  # Balanced chunk size for context preservation
# CHUNK_OVERLAP = 30     # Maintain good overlap for context

# Suggested final config:
DEFAULT_BATCH_SIZE = 128   # Better for CPU memory
MIN_WORDS_KEEP = 8         # Less aggressive filtering  
CHUNK_MAX_WORDS = 400      # Larger chunks = fewer embeddings
CHUNK_OVERLAP = 20         # Reduced overlap for speed

EMBED_CACHE_DIRNAME = "embed_cache"
META_FILENAME = "faiss_metadata.json"
FAISS_INDEX_FILENAME = "faiss_index.bin"
EMBED_MATRIX_FILENAME = "embeddings.npy"

# ------------------------
# GLOBAL MODEL SINGLETON - SHARED ACROSS ALL INSTANCES
# ------------------------
_MODEL_INSTANCE = None
_MODEL_LOADING = False  # Prevent concurrent loading

def get_global_model(use_gpu: bool = False) -> SentenceTransformer:
    """
    Get the optimized global model singleton - loads once, shared by all embedding requests
    
    Args:
        use_gpu: Whether to use GPU acceleration
        
    Returns:
        Global SentenceTransformer model instance with CPU/GPU optimizations
    """
    global _MODEL_INSTANCE, _MODEL_LOADING
    
    if _MODEL_INSTANCE is None and not _MODEL_LOADING:
        _MODEL_LOADING = True
        try:
            device = "cuda" if use_gpu and torch.cuda.is_available() else "cpu"
            logger.info(f"🌍 Loading optimized global embedding model singleton: {MODEL_NAME}")
            logger.info(f"🔧 Device: {device.upper()}")
            
            # Load model with optimizations
            _MODEL_INSTANCE = SentenceTransformer(
                MODEL_NAME, 
                device=device,
                # Model loading optimizations
                use_auth_token=False,
                trust_remote_code=True
            )
            
            if device == "cpu":
                # 🚀 CPU Performance Optimizations
                # Reduced threads for better throughput (avoid oversubscription)
                torch.set_num_threads(min(4, torch.get_num_threads()))
                # Single interop thread for better CPU performance
                torch.set_num_interop_threads(1)
                
                # Enable better memory management for CPU
                if hasattr(torch, 'set_float32_matmul_precision'):
                    torch.set_float32_matmul_precision('medium')  # Faster with minimal quality loss
                
                logger.info(f"✅ Optimized global model loaded on CPU:")
                logger.info(f"   🧵 Compute threads: {torch.get_num_threads()}")
                logger.info(f"   🔄 Interop threads: 1")
                logger.info(f"   🎯 Precision: medium (optimized)")
                
            else:
                # 🚀 GPU Performance Optimizations
                # Force GPU model placement - prevents accidental CPU fallback
                if hasattr(_MODEL_INSTANCE, '_modules'):
                    for module in _MODEL_INSTANCE._modules.values():
                        if hasattr(module, 'to'):
                            module.to(device)
                
                # GPU memory optimizations
                if hasattr(torch, 'set_float32_matmul_precision'):
                    torch.set_float32_matmul_precision('high')  # Better precision for GPU
                
                logger.info(f"✅ Optimized global model loaded on GPU: {torch.cuda.get_device_name(0)}")
                logger.info(f"   🎯 Precision: high (GPU optimized)")
            
            logger.info("🚀 Optimized global model singleton ready - shared across all requests!")
            
        except Exception as e:
            logger.error(f"Failed to load optimized global model: {str(e)}")
            _MODEL_INSTANCE = None
        finally:
            _MODEL_LOADING = False
    
    return _MODEL_INSTANCE

# Optimized text cleaning - combined regex for better performance
FAST_CLEANUP_RE = re.compile(
    r"(https?://\S+|www\.\S+)|"          # URLs
    r"```.*?```|`[^`]*`|"                # Code blocks
    r"<[^>]+>|"                          # HTML tags
    r"\[([^\]]+)\]\([^)]+\)|"            # Markdown links
    r"([!?.,])\1{1,}|"                   # Repeated punctuation
    r"\s+",                              # Multiple whitespace
    re.DOTALL
)

MULTI_WS_RE = re.compile(r'\s+')

def fast_clean(text: str, keep_emojis: bool = False) -> str:
    """Optimized preprocessing pipeline"""
    if not text or len(text.strip()) == 0:
        return ""
    
    # Combine operations for better performance
    t = text.lower().strip()
    
    # Single pass regex substitution
    def replace_func(match):
        groups = match.groups()
        if groups[0]:  # URL
            return ' '
        elif groups[1]:  # Markdown link - keep the text part
            return groups[1]
        elif groups[2]:  # Repeated punctuation - keep single
            return groups[2]
        else:  # Code blocks, HTML tags, whitespace
            return ' '
    
    # Apply all transformations in one pass
    t = FAST_CLEANUP_RE.sub(replace_func, t)
    
    # Remove emojis if requested
    if not keep_emojis:
        t = emoji.replace_emoji(t, replace='')
    
    # Final normalization
    t = t.replace('\n', ' ')
    t = MULTI_WS_RE.sub(' ', t)
    
    return t.strip()

# content_hash function removed - now handled by OptimizedEmbeddingCache

def detect_language_safe(text: str) -> str:
    """Safely detect language, return 'unknown' if detection fails"""
    try:
        return detect(text)
    except:
        return "unknown"

def chunk_text(text: str, max_words: int = CHUNK_MAX_WORDS, overlap: int = CHUNK_OVERLAP) -> List[str]:
    """Split text into overlapping chunks"""
    words = text.split()
    if len(words) <= max_words:
        return [text]
    
    chunks = []
    start = 0
    while start < len(words):
        end = min(start + max_words, len(words))
        chunk = ' '.join(words[start:end])
        chunks.append(chunk)
        if end >= len(words):
            break
        start = end - overlap
    
    return chunks

class EmbeddingService:
    """Service for generating embeddings from Reddit posts with direct integration"""
    
    def __init__(self):
        self.use_gpu = False  # Use CPU for simplicity and reliability
        self.batch_size = 256  # Optimized batch size for CPU throughput
        self.model: Optional[SentenceTransformer] = None
        
        # Initialize optimized global cache for public Reddit data
        try:
            self.optimized_cache = OptimizedEmbeddingCache(
                cache_dir=Path("data/embeddings/global_cache_optimized"),
                similarity_threshold=0.87,  # Lowered from 0.95 to capture semantic similarities
                max_cache_size=5000
            )
        except Exception as e:
            logger.warning(f"Failed to initialize optimized cache: {e}. Proceeding without cache.")
            self.optimized_cache = None
        
        # 🧠 Language detection cache - 10x faster for large datasets
        self.lang_cache = {}  # Cache by subreddit for efficiency
    
    def _fast_json_save(self, data: Any, file_path: Path, indent: bool = True):
        """🗃️ Fast JSON serialization with orjson (up to 5x faster)"""
        if HAS_ORJSON:
            # Use orjson for much faster serialization
            options = orjson.OPT_INDENT_2 if indent else 0
            json_bytes = orjson.dumps(data, option=options)
            with open(file_path, "wb") as f:
                f.write(json_bytes)
        else:
            # Fallback to standard json
            with open(file_path, "w", encoding="utf-8") as f:
                if indent:
                    json.dump(data, f, indent=2)
                else:
                    json.dump(data, f)
    
    def _load_model(self):
        """Simplified - just get global singleton"""
        if self.model is None:
            logger.info("🧠 Getting global model singleton...")
            self.model = get_global_model(use_gpu=self.use_gpu)
    
    def _get_cached_language(self, text: str, subreddit: str) -> str:
        """🧠 Get language with optimized caching - 10x faster than per-post detection"""
        # Check cache first
        lang = self.lang_cache.get(subreddit)
        if lang is None:
            # Detect language for sample only (first 300 chars for speed)
            sample_text = text[:300] if len(text) > 300 else text
            lang = detect_language_safe(sample_text)
            self.lang_cache[subreddit] = lang
            logger.debug(f"🌍 Cached language '{lang}' for subreddit r/{subreddit}")
        return lang
    
    def clear_language_cache(self):
        """Clear language detection cache"""
        cache_size = len(self.lang_cache)
        self.lang_cache.clear()
        logger.info(f"🧹 Cleared language cache ({cache_size} subreddits)")
    
    async def _convert_reddit_data_format(self, reddit_json_path: str) -> str:
        """
        Convert Reddit JSON format to the format expected by embedding pipeline
        """
        try:
            with open(reddit_json_path, 'r', encoding='utf-8') as f:
                reddit_data = json.load(f)
            
            # Convert to expected format (list of posts with id, title, selftext, etc.)
            converted_posts = []
            
            # Extract posts from by_query results
            if "by_query" in reddit_data:
                for query_result in reddit_data["by_query"]:
                    if "posts" in query_result:
                        for post in query_result["posts"]:
                            converted_post = {
                                "id": post.get("id", ""),
                                "title": post.get("title", ""),
                                "selftext": post.get("content", post.get("selftext", "")),  # Use 'content' field, fallback to 'selftext'
                                "subreddit": post.get("subreddit", ""),
                                "url": post.get("url", ""),
                                "created_utc": post.get("created_utc", 0),
                                "score": post.get("score", 0),
                                "num_comments": post.get("num_comments", 0)
                            }
                            converted_posts.append(converted_post)
            
            # Extract posts from by_subreddit results
            if "by_subreddit" in reddit_data:
                for subreddit_result in reddit_data["by_subreddit"]:
                    if "posts" in subreddit_result:
                        for post in subreddit_result["posts"]:
                            converted_post = {
                                "id": post.get("id", ""),
                                "title": post.get("title", ""),
                                "selftext": post.get("content", post.get("selftext", "")),  # Use 'content' field, fallback to 'selftext'
                                "subreddit": post.get("subreddit", ""),
                                "url": post.get("url", ""),
                                "created_utc": post.get("created_utc", 0),
                                "score": post.get("score", 0),
                                "num_comments": post.get("num_comments", 0)
                            }
                            converted_posts.append(converted_post)
            
            # 🗃️ Save converted format with fast JSON serialization
            converted_path = reddit_json_path.replace('.json', '_converted.json')
            self._fast_json_save(converted_posts, Path(converted_path), indent=True)
            
            logger.info(f"Converted Reddit data format: {converted_path}")
            return converted_path
            
        except Exception as e:
            logger.error(f"Error converting Reddit data format: {str(e)}")
            raise

    async def generate_embeddings_for_reddit_data(
        self, 
        user_id: str, 
        input_id: str, 
        reddit_json_path: str,
        use_gpu: bool = False,
        batch_size: int = 32
    ) -> Dict[str, Any]:
        """
        Generate embeddings for Reddit data using direct integration
        
        Args:
            user_id: User ID
            input_id: Input ID
            reddit_json_path: Path to the Reddit JSON file
            use_gpu: Whether to use GPU acceleration
            batch_size: Batch size for embedding generation
            
        Returns:
            Dictionary with embedding generation results and metadata
        """
        try:
            self.use_gpu = use_gpu
            self.batch_size = batch_size
            logger.info(f"Starting embedding generation for input {input_id} (user: {user_id})")
            
            # Create output directory for embeddings
            embeddings_dir = Path("data/embeddings") / user_id / input_id
            embeddings_dir.mkdir(parents=True, exist_ok=True)
            
            # Check if Reddit JSON file exists
            if not Path(reddit_json_path).exists():
                raise FileNotFoundError(f"Reddit JSON file not found: {reddit_json_path}")
            
            # Convert Reddit data to expected format
            converted_json_path = await self._convert_reddit_data_format(reddit_json_path)
            
            # Load and process the data
            with open(converted_json_path, 'r', encoding='utf-8') as f:
                posts = json.load(f)
            
            logger.info(f"Loaded {len(posts)} posts for embedding generation")
            
            # Process posts into documents
            processed_docs = await self._process_posts_for_embedding(posts)
            
            if len(processed_docs) == 0:
                logger.warning("No documents to embed after preprocessing")
                return {
                    "success": False,
                    "message": "No documents to embed after preprocessing",
                    "documents_processed": 0
                }
            
            logger.info(f"After cleaning/chunking/dedup: {len(processed_docs)} documents to embed")
            
            # Load model
            self._load_model()
            
            # Generate embeddings
            embeddings = await self._generate_embeddings(processed_docs, embeddings_dir, batch_size)
            
            # Create FAISS index and save
            await self._create_and_save_index(processed_docs, embeddings, embeddings_dir)
            
            logger.info(f"Successfully generated embeddings for input {input_id}")
            
            return {
                "success": True,
                "message": f"Successfully generated embeddings for {len(processed_docs)} documents",
                "documents_processed": len(processed_docs),
                "output_directory": str(embeddings_dir),
                "files_created": [
                    str(embeddings_dir / FAISS_INDEX_FILENAME),
                    str(embeddings_dir / EMBED_MATRIX_FILENAME),
                    str(embeddings_dir / META_FILENAME),
                    str(embeddings_dir / "faiss_metadata.csv")
                ]
            }
            
        except Exception as e:
            logger.error(f"Error generating embeddings: {str(e)}")
            return {
                "success": False,
                "message": f"Error generating embeddings: {str(e)}",
                "documents_processed": 0
            }
    
    async def _process_posts_for_embedding(self, posts: List[Dict]) -> List[Dict]:
        """🚀 Process Reddit posts with parallel processing optimization"""
        # Use ThreadPool for CPU-bound preprocessing
        max_workers = min(4, os.cpu_count() or 1)
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Process posts in parallel
            loop = asyncio.get_event_loop()
            processed_results = await loop.run_in_executor(
                executor, self._process_posts_parallel, posts
            )
        
        return processed_results
    
    def _process_posts_parallel(self, posts: List[Dict]) -> List[Dict]:
        """Process posts in parallel with deduplication"""
        processed_docs = []
        seen_hashes = set()
        
        # Process each post
        for p in posts:
            docs = self._process_single_post(p)
            
            # Add to results with deduplication
            for doc in docs:
                if doc["hash"] not in seen_hashes:
                    seen_hashes.add(doc["hash"])
                    processed_docs.append(doc)
        
        return processed_docs
    
    def _process_single_post(self, post: Dict) -> List[Dict]:
        """Process single post (optimized for parallel execution)"""
        # Combine title and selftext
        title = post.get("title", "")
        selftext = post.get("selftext", "")
        
        if not title and not selftext:
            return []
        
        combined_text = f"{title} {selftext}".strip()
        
        # Truncate overly long posts before processing
        combined_text = " ".join(combined_text.split()[:400])
        
        # Use optimized preprocessing pipeline
        clean_text = fast_clean(combined_text, keep_emojis=False)
        
        # Skip if too short or low quality
        words = clean_text.split()
        if len(words) < MIN_WORDS_KEEP:
            return []
        
        # Skip very short posts (likely low quality)
        if len(words) < 20 and post.get("score", 0) < 5:
            return []
        
        # Skip posts with very low engagement
        if post.get("score", 0) <= 0 and post.get("num_comments", 0) <= 0:
            return []
        
        # Optimized language detection with subreddit caching
        subreddit = post.get("subreddit", "unknown")
        lang = self._get_cached_language(clean_text, subreddit)
        
        # Skip non-English content
        if lang != "en":
            return []
        
        # Chunk long posts
        chunks = chunk_text(clean_text, CHUNK_MAX_WORDS, CHUNK_OVERLAP)
        
        # Create document entries
        docs = []
        for idx, chunk in enumerate(chunks):
            if self.optimized_cache:
                h = self.optimized_cache._create_hash(chunk)
            else:
                import hashlib
                h = hashlib.sha256(chunk.encode('utf-8')).hexdigest()[:16]
            doc_id = f"{post['id']}_{idx}"
            docs.append({
                "doc_id": doc_id,
                "post_id": post["id"],
                "text": chunk,
                "hash": h,
                "subreddit": post.get("subreddit"),
                "url": post.get("url"),
                "created_utc": post.get("created_utc"),
                "score": post.get("score")
            })
        
        return docs
    
    async def _generate_embeddings(self, processed_docs: List[Dict], embeddings_dir: Path, batch_size: int) -> np.ndarray:
        """Generate embeddings for processed documents using optimized tiered cache"""
        encoded_map = {}
        cache_stats = {"exact": 0, "normalized": 0, "semantic": 0, "new": 0}
        
        # Process documents with tiered cache lookup
        new_docs = []
        for doc in tqdm(processed_docs, desc="Checking cache tiers"):
            text = doc["text"]
            
            # Try tiered cache lookup if cache is available
            if self.optimized_cache:
                cached_embedding, cache_type = self.optimized_cache.get_cached_embedding(text)
                
                if cached_embedding is not None:
                    encoded_map[doc["hash"]] = cached_embedding
                    cache_stats[cache_type] += 1
                else:
                    new_docs.append(doc)
                    cache_stats["new"] += 1
            else:
                # No cache available, all documents are new
                new_docs.append(doc)
                cache_stats["new"] += 1
        
        # Log cache statistics
        total_docs = len(processed_docs)
        total_hits = cache_stats["exact"] + cache_stats["normalized"] + cache_stats["semantic"]
        cache_hit_rate = (total_hits / total_docs * 100) if total_docs > 0 else 0
        
        logger.info("🧠 Optimized Cache Statistics:")
        logger.info(f"   📊 Total documents: {total_docs}")
        logger.info(f"   ⚡ Exact hits: {cache_stats['exact']} ({cache_stats['exact']/total_docs*100:.1f}%)")
        logger.info(f"   🔄 Normalized hits: {cache_stats['normalized']} ({cache_stats['normalized']/total_docs*100:.1f}%)")
        logger.info(f"   🎯 Semantic hits: {cache_stats['semantic']} ({cache_stats['semantic']/total_docs*100:.1f}%)")
        logger.info(f"   🆕 New to compute: {cache_stats['new']} ({cache_stats['new']/total_docs*100:.1f}%)")
        logger.info(f"   📈 Overall hit rate: {cache_hit_rate:.1f}%")
        
        if cache_hit_rate > 0:
            logger.info(f"   💰 Cache saved {total_hits} embedding computations!")
        
        # Generate new embeddings for cache misses
        if new_docs:
            texts = [d["text"] for d in new_docs]
            logger.info(f"Encoding {len(texts)} new documents...")
            
            # 🚀 Dynamic batch sizing based on document length
            avg_length = np.mean([len(text.split()) for text in texts])
            
            if avg_length < 50:  # Short texts
                optimal_batch_size = min(512, batch_size * 2)
                logger.info(f"📝 Short texts detected (avg: {avg_length:.1f} words) → batch_size: {optimal_batch_size}")
            elif avg_length > 200:  # Long texts
                optimal_batch_size = max(64, batch_size // 2)
                logger.info(f"📚 Long texts detected (avg: {avg_length:.1f} words) → batch_size: {optimal_batch_size}")
            else:  # Medium texts
                optimal_batch_size = batch_size
                logger.info(f"📄 Medium texts detected (avg: {avg_length:.1f} words) → batch_size: {optimal_batch_size}")
            
            # 🚀 Use torch autocast for mixed precision speedup (safe for quality)
            device_type = "cuda" if self.use_gpu else "cpu"
            with torch.autocast(device_type=device_type, dtype=torch.float32):
                new_embeddings = self.model.encode(
                    texts,
                    batch_size=optimal_batch_size,
                    show_progress_bar=True,
                    convert_to_numpy=True,
                    normalize_embeddings=True  # This is sufficient - model handles normalization
                )
            
            # Cache new embeddings and add to encoded_map
            for doc, emb in zip(new_docs, new_embeddings):
                if self.optimized_cache:
                    self.optimized_cache.cache_embedding(doc["text"], emb)
                encoded_map[doc["hash"]] = emb
        
        # Create final embedding matrix
        embeddings = np.array([encoded_map[d["hash"]] for d in processed_docs])
        
        return embeddings
    
    async def _create_and_save_index(self, processed_docs: List[Dict], embeddings: np.ndarray, embeddings_dir: Path):
        """🚀 Create FAISS index with optimizations and parallel I/O"""
        # Check if embeddings are already normalized (from model.encode with normalize_embeddings=True)
        norms = np.linalg.norm(embeddings, axis=1)
        if not np.allclose(norms, 1.0, atol=1e-6):
            faiss.normalize_L2(embeddings)
            logger.debug("Applied normalization to embeddings")
        else:
            logger.debug("Embeddings already normalized, skipping normalization")
        
        # Create FAISS index
        dim = embeddings.shape[1]
        index = faiss.IndexFlatIP(dim)  # Inner product for normalized vectors = cosine similarity
        index.add(embeddings.astype(np.float32))  # 🚀 Ensure float32 for better performance
        
        # � Savee files in parallel for faster I/O
        await asyncio.gather(
            self._save_index_async(index, embeddings_dir),
            self._save_embeddings_async(embeddings, embeddings_dir),
            self._save_metadata_async(processed_docs, embeddings_dir)
        )
        
        logger.info("Index and metadata saved successfully")
    
    async def _save_index_async(self, index, embeddings_dir: Path):
        """Save FAISS index asynchronously"""
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, faiss.write_index, index, str(embeddings_dir / FAISS_INDEX_FILENAME))
    
    async def _save_embeddings_async(self, embeddings: np.ndarray, embeddings_dir: Path):
        """Save embeddings asynchronously"""
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, np.save, embeddings_dir / EMBED_MATRIX_FILENAME, embeddings)
    
    async def _save_metadata_async(self, processed_docs: List[Dict], embeddings_dir: Path):
        """Save metadata asynchronously"""
        loop = asyncio.get_event_loop()
        
        # JSON metadata
        meta_records = [{"doc_idx": i, **doc} for i, doc in enumerate(processed_docs)]
        await loop.run_in_executor(None, self._fast_json_save, meta_records, embeddings_dir / META_FILENAME, True)
        
        # CSV metadata
        def save_csv():
            pd.DataFrame(meta_records).to_csv(embeddings_dir / "faiss_metadata.csv", index=False)
        await loop.run_in_executor(None, save_csv)
    
    def get_cache_statistics(self) -> Dict[str, Any]:
        """Simplified cache statistics"""
        try:
            if self.optimized_cache:
                optimized_stats = self.optimized_cache.get_cache_statistics()
                
                return {
                    "cache_exists": True,
                    "optimized_cache": optimized_stats,
                    "cache_directory": str(self.optimized_cache.cache_dir),
                    "cache_type": "optimized_tiered"
                }
            else:
                return {"cache_exists": False, "error": "Cache not initialized"}
        except Exception as e:
            logger.error(f"Error getting cache statistics: {str(e)}")
            return {"cache_exists": False, "error": str(e)}
    
    async def list_user_embeddings(self, user_id: str) -> List[Dict[str, Any]]:
        """
        List all embedding sets for a specific user
        
        Args:
            user_id: User ID to list embeddings for
            
        Returns:
            List of dictionaries containing embedding metadata
        """
        try:
            user_embeddings_dir = Path("data/embeddings") / user_id
            
            if not user_embeddings_dir.exists():
                return []
            
            embeddings_list = []
            
            for input_dir in user_embeddings_dir.iterdir():
                if input_dir.is_dir():
                    # Check if this directory contains embedding files
                    faiss_index_path = input_dir / FAISS_INDEX_FILENAME
                    metadata_path = input_dir / META_FILENAME
                    
                    if faiss_index_path.exists() and metadata_path.exists():
                        # Read metadata to get document count
                        try:
                            with open(metadata_path, 'r', encoding='utf-8') as f:
                                metadata = json.load(f)
                            
                            embeddings_list.append({
                                "input_id": input_dir.name,
                                "document_count": len(metadata),
                                "created_date": datetime.fromtimestamp(
                                    faiss_index_path.stat().st_ctime
                                ).isoformat(),
                                "directory_path": str(input_dir),
                                "files": {
                                    "faiss_index": str(faiss_index_path),
                                    "embeddings": str(input_dir / EMBED_MATRIX_FILENAME),
                                    "metadata": str(metadata_path),
                                    "metadata_csv": str(input_dir / "faiss_metadata.csv")
                                }
                            })
                        except Exception as e:
                            logger.warning(f"Error reading metadata for {input_dir}: {str(e)}")
                            continue
            
            return sorted(embeddings_list, key=lambda x: x["created_date"], reverse=True)
            
        except Exception as e:
            logger.error(f"Error listing user embeddings: {str(e)}")
            return []
    
    async def clear_global_cache(self) -> Dict[str, Any]:
        """Clear the global embedding cache"""
        try:
            # Get stats before clearing
            stats_before = self.get_cache_statistics()
            optimized_stats = stats_before.get("optimized_cache", {})
            optimized_counts = optimized_stats.get("cache_counts", {})
            optimized_sizes = optimized_stats.get("cache_sizes_mb", {})
            
            embeddings_removed = sum(optimized_counts.values())
            space_freed_mb = optimized_sizes.get("total", 0)
            
            # Clear optimized cache
            if self.optimized_cache:
                self.optimized_cache.clear_cache("all")
                logger.info("Global embedding cache cleared")
            else:
                logger.info("No cache to clear")
            
            return {
                "success": True,
                "message": "Global embedding cache cleared successfully",
                "embeddings_removed": embeddings_removed,
                "space_freed_mb": round(space_freed_mb, 2)
            }
                
        except Exception as e:
            logger.error(f"Error clearing global cache: {str(e)}")
            return {
                "success": False,
                "message": f"Error clearing cache: {str(e)}",
                "embeddings_removed": 0,
                "space_freed_mb": 0
            }

# Create a singleton instance for use across the application
embedding_service = EmbeddingService()