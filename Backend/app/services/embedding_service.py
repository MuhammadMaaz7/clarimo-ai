"""
Embedding Service - Direct integration of embedding generation without external scripts
"""
import os
import json
import asyncio
import logging
import hashlib
import re
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone
import uuid
import numpy as np
import pandas as pd
from tqdm import tqdm

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
DEFAULT_BATCH_SIZE = 256  # Larger batch size for better CPU throughput
MIN_WORDS_KEEP = 12  # Balanced threshold - not too aggressive
CHUNK_MAX_WORDS = 350  # Balanced chunk size for context preservation
CHUNK_OVERLAP = 30     # Maintain good overlap for context
EMBED_CACHE_DIRNAME = "embed_cache"
META_FILENAME = "faiss_metadata.json"
FAISS_INDEX_FILENAME = "faiss_index.bin"
EMBED_MATRIX_FILENAME = "embeddings.npy"

# Text cleaning utilities
URL_RE = re.compile(r'https?://\S+|www\.\S+')
MD_LINK_RE = re.compile(r'\[([^\]]+)\]\(([^)]+)\)')
MARKDOWN_CODE_RE = re.compile(r'```.*?```|`[^`]*`', re.DOTALL)
HTML_TAG_RE = re.compile(r'<[^>]+>')
MULTI_WS_RE = re.compile(r'\s+')
REPEATED_PUNC_RE = re.compile(r'([!?.,])\1{1,}')

class EmbedCache:
    """Simple file-based cache for embeddings by content hash"""
    def __init__(self, cache_dir: Path):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
    
    def _hash_to_path(self, content_hash: str) -> Path:
        return self.cache_dir / f"{content_hash}.npy"
    
    def exists(self, content_hash: str) -> bool:
        return self._hash_to_path(content_hash).exists()
    
    def save(self, content_hash: str, embedding: np.ndarray):
        np.save(self._hash_to_path(content_hash), embedding)
    
    def load(self, content_hash: str) -> np.ndarray:
        return np.load(self._hash_to_path(content_hash))

def strip_markdown_and_code(text: str) -> str:
    """Remove markdown formatting and code blocks"""
    if not text:
        return ""
    t = MARKDOWN_CODE_RE.sub(' ', text)
    t = MD_LINK_RE.sub(r'\1', t)
    t = HTML_TAG_RE.sub(' ', t)
    return t

def remove_urls(text: str) -> str:
    """Remove URLs from text"""
    return URL_RE.sub(' ', text)

def normalize_text(text: str) -> str:
    """Normalize whitespace and punctuation"""
    t = text.replace('\n', ' ')
    t = t.strip()
    t = MULTI_WS_RE.sub(' ', t)
    t = REPEATED_PUNC_RE.sub(r'\1', t)
    return t

def remove_emojis(text: str) -> str:
    """Remove emojis from text"""
    return emoji.replace_emoji(text, replace='')

def reddit_preprocess(text: str, keep_emojis: bool = False) -> str:
    """Preprocess Reddit text for embedding"""
    if not text:
        return ""
    t = strip_markdown_and_code(text)
    t = remove_urls(t)
    if not keep_emojis:
        t = remove_emojis(t)
    t = normalize_text(t)
    t = t.strip().lower()
    return t

def content_hash(text: str) -> str:
    """Generate content hash for caching"""
    return hashlib.sha256(text.encode('utf-8')).hexdigest()[:16]

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
        self._model_loading = False  # Prevent concurrent model loading
        
        # Initialize optimized global cache for public Reddit data
        self.optimized_cache = OptimizedEmbeddingCache(
            cache_dir=Path("data/embeddings/global_cache_optimized"),
            similarity_threshold=0.87,  # Lowered from 0.95 to capture semantic similarities
            max_cache_size=5000
        )
    
    def _load_model(self):
        """Load the embedding model on CPU with optimizations"""
        if self.model is None and not self._model_loading:
            self._model_loading = True
            try:
                logger.info("=> Using CPU for embeddings (optimized for throughput)")
                logger.info(f"Loading model {MODEL_NAME} ...")
                
                # Load model with CPU optimizations
                self.model = SentenceTransformer(MODEL_NAME, device="cpu")
                
                # Set number of threads for CPU optimization
                torch.set_num_threads(min(8, torch.get_num_threads()))  # Limit threads to prevent oversubscription
                
                logger.info(f"Model loaded successfully with {torch.get_num_threads()} CPU threads")
            finally:
                self._model_loading = False
    
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
            
            # Save converted format
            converted_path = reddit_json_path.replace('.json', '_converted.json')
            with open(converted_path, 'w', encoding='utf-8') as f:
                json.dump(converted_posts, f, indent=2)
            
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
        """Process Reddit posts into documents ready for embedding"""
        processed_docs = []
        seen_hashes = set()
        
        for p in posts:
            # Combine title and selftext
            title = p.get("title", "")
            selftext = p.get("selftext", "")
            
            if not title and not selftext:
                continue
            
            combined_text = f"{title} {selftext}".strip()
            
            # Preprocess text
            clean_text = reddit_preprocess(combined_text, keep_emojis=False)
            
            # Skip if too short or low quality
            words = clean_text.split()
            if len(words) < MIN_WORDS_KEEP:
                continue
            
            # Skip very short posts (likely low quality) - balanced filtering
            if len(words) < 20 and p.get("score", 0) < 5:
                continue
            
            # Skip posts with very low engagement (likely spam/low quality) - but not too aggressive
            if p.get("score", 0) <= 0 and p.get("num_comments", 0) <= 0:
                continue
            
            # Skip non-English content
            if detect_language_safe(clean_text) != "en":
                continue
            
            # Chunk long posts
            chunks = chunk_text(clean_text, CHUNK_MAX_WORDS, CHUNK_OVERLAP)
            
            for idx, chunk in enumerate(chunks):
                h = content_hash(chunk)
                if h in seen_hashes:
                    continue
                seen_hashes.add(h)
                
                doc_id = f"{p['id']}_{idx}"
                processed_docs.append({
                    "doc_id": doc_id,
                    "post_id": p["id"],
                    "text": chunk,
                    "hash": h,
                    "subreddit": p.get("subreddit"),
                    "url": p.get("url"),
                    "created_utc": p.get("created_utc"),
                    "score": p.get("score")
                })
        
        return processed_docs
    
    async def _generate_embeddings(self, processed_docs: List[Dict], embeddings_dir: Path, batch_size: int) -> np.ndarray:
        """Generate embeddings for processed documents using optimized tiered cache"""
        encoded_map = {}
        cache_stats = {"exact": 0, "normalized": 0, "semantic": 0, "new": 0}
        
        # Process documents with tiered cache lookup
        new_docs = []
        for doc in tqdm(processed_docs, desc="Checking cache tiers"):
            text = doc["text"]
            
            # Try tiered cache lookup
            cached_embedding, cache_type = self.optimized_cache.get_cached_embedding(text)
            
            if cached_embedding is not None:
                encoded_map[doc["hash"]] = cached_embedding
                cache_stats[cache_type] += 1
            else:
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
            
            # Use optimized batch size and enable CPU optimizations
            new_embeddings = self.model.encode(
                texts, 
                batch_size=min(batch_size, 256),  # Cap at 256 for memory efficiency
                show_progress_bar=True,
                convert_to_numpy=True,
                normalize_embeddings=True  # Pre-normalize for cosine similarity
            )
            
            # Cache new embeddings and add to encoded_map
            for doc, emb in zip(new_docs, new_embeddings):
                self.optimized_cache.cache_embedding(doc["text"], emb)
                encoded_map[doc["hash"]] = emb
        
        # Create final embedding matrix
        embeddings = np.array([encoded_map[d["hash"]] for d in processed_docs])
        
        return embeddings
    
    async def _create_and_save_index(self, processed_docs: List[Dict], embeddings: np.ndarray, embeddings_dir: Path):
        """Create FAISS index and save all files"""
        # Normalize embeddings for cosine similarity
        faiss.normalize_L2(embeddings)
        
        # Create FAISS index
        dim = embeddings.shape[1]
        index = faiss.IndexFlatIP(dim)  # Inner product for normalized vectors = cosine similarity
        index.add(embeddings)
        
        # Save index
        faiss.write_index(index, str(embeddings_dir / FAISS_INDEX_FILENAME))
        
        # Save embedding matrix
        np.save(embeddings_dir / EMBED_MATRIX_FILENAME, embeddings)
        
        # Save metadata
        meta_records = [{"doc_idx": i, **doc} for i, doc in enumerate(processed_docs)]
        with open(embeddings_dir / META_FILENAME, "w", encoding="utf-8") as f:
            json.dump(meta_records, f, indent=2)
        
        # Save CSV metadata
        pd.DataFrame(meta_records).to_csv(embeddings_dir / "faiss_metadata.csv", index=False)
        
        logger.info("Index and metadata saved successfully")
    
    def get_cache_statistics(self) -> Dict[str, Any]:
        """Get optimized cache statistics with tiered metrics"""
        try:
            # Get optimized cache statistics
            optimized_stats = self.optimized_cache.get_cache_statistics()
            
            # Also check legacy cache for migration info
            legacy_cache_dir = Path("data/embeddings") / "global_cache"
            legacy_stats = {
                "exists": legacy_cache_dir.exists(),
                "cached_embeddings": 0,
                "cache_size_mb": 0
            }
            
            if legacy_cache_dir.exists():
                legacy_files = list(legacy_cache_dir.glob("*.npy"))
                legacy_size = sum(f.stat().st_size for f in legacy_files) / (1024 * 1024)
                legacy_stats.update({
                    "cached_embeddings": len(legacy_files),
                    "cache_size_mb": round(legacy_size, 2)
                })
            
            # Combine statistics for backward compatibility
            return {
                "cache_exists": True,
                "optimized_cache": optimized_stats,
                "legacy_cache": legacy_stats,
                # Backward compatibility fields
                "cached_embeddings": optimized_stats.get("cache_counts", {}).get("exact", 0),
                "cache_size_mb": optimized_stats.get("cache_sizes_mb", {}).get("total", 0),
                "cache_directory": str(self.optimized_cache.cache_dir),
                "cache_type": "optimized_tiered"
            }
            
        except Exception as e:
            logger.error(f"Error getting cache statistics: {str(e)}")
            return {
                "cache_exists": False,
                "cached_embeddings": 0,
                "cache_size_mb": 0,
                "error": str(e)
            }
    
    def migrate_legacy_cache(self) -> Dict[str, Any]:
        """
        Migrate from legacy cache to optimized cache structure with comprehensive validation and logging
        
        Returns:
            Dictionary with migration results including success status, counts, and error details
        """
        migration_start_time = datetime.now()
        migration_results = {
            "success": False,
            "message": "",
            "migrated_count": 0,
            "failed_count": 0,
            "skipped_count": 0,
            "validation_errors": [],
            "legacy_cache_dir": "",
            "optimized_cache_dir": str(self.optimized_cache.cache_dir),
            "migration_duration_seconds": 0,
            "data_integrity_check": False
        }
        
        try:
            logger.info("🔄 Starting legacy cache migration process...")
            
            # Step 1: Detect existing cache files
            legacy_cache_locations = [
                Path("data/embeddings") / "global_cache",
                Path("data/embeddings") / "embed_cache",  # Alternative legacy location
            ]
            
            legacy_cache_dir = None
            total_legacy_files = 0
            
            # Find the legacy cache directory with files
            for cache_location in legacy_cache_locations:
                if cache_location.exists():
                    legacy_files = list(cache_location.glob("*.npy"))
                    if legacy_files:
                        legacy_cache_dir = cache_location
                        total_legacy_files = len(legacy_files)
                        logger.info(f"📁 Found legacy cache at: {cache_location} ({total_legacy_files} files)")
                        break
            
            if legacy_cache_dir is None:
                migration_results.update({
                    "success": True,
                    "message": "No legacy cache found to migrate",
                    "migration_duration_seconds": (datetime.now() - migration_start_time).total_seconds()
                })
                logger.info("✅ No legacy cache found - migration not needed")
                return migration_results
            
            migration_results["legacy_cache_dir"] = str(legacy_cache_dir)
            
            # Step 2: Pre-migration validation
            logger.info(f"🔍 Validating {total_legacy_files} legacy cache files...")
            
            valid_files = []
            invalid_files = []
            
            for npy_file in legacy_cache_dir.glob("*.npy"):
                try:
                    # Validate file can be loaded
                    embedding = np.load(npy_file)
                    
                    # Validate embedding structure
                    if not isinstance(embedding, np.ndarray):
                        raise ValueError("Not a valid numpy array")
                    
                    if embedding.size == 0:
                        raise ValueError("Empty embedding array")
                    
                    if len(embedding.shape) != 1:
                        raise ValueError(f"Invalid embedding shape: {embedding.shape}")
                    
                    # Validate embedding dimensions (typical range for sentence transformers)
                    if embedding.shape[0] < 100 or embedding.shape[0] > 2048:
                        logger.warning(f"Unusual embedding dimension: {embedding.shape[0]} for file {npy_file.name}")
                    
                    # Validate hash format (should be 16 character hex)
                    hash_key = npy_file.stem
                    if len(hash_key) != 16 or not all(c in '0123456789abcdef' for c in hash_key.lower()):
                        logger.warning(f"Non-standard hash format: {hash_key}")
                    
                    valid_files.append((npy_file, embedding, hash_key))
                    
                except Exception as e:
                    invalid_files.append((npy_file, str(e)))
                    migration_results["validation_errors"].append(f"{npy_file.name}: {str(e)}")
                    logger.warning(f"❌ Invalid cache file {npy_file.name}: {str(e)}")
            
            logger.info(f"✅ Validation complete: {len(valid_files)} valid, {len(invalid_files)} invalid files")
            
            # Step 3: Migration process with progress tracking
            logger.info("🚀 Starting migration of valid cache files...")
            
            migrated_count = 0
            failed_count = len(invalid_files)
            skipped_count = 0
            
            # Create progress tracking
            from tqdm import tqdm
            
            for npy_file, embedding, hash_key in tqdm(valid_files, desc="Migrating cache files"):
                try:
                    # Check if already exists in optimized cache
                    exact_path = self.optimized_cache.exact_cache_dir / f"{hash_key}.npy"
                    
                    if exact_path.exists():
                        # Verify existing file is identical
                        existing_embedding = np.load(exact_path)
                        if np.array_equal(embedding, existing_embedding):
                            skipped_count += 1
                            logger.debug(f"⏭️ Skipped {hash_key} - already exists and identical")
                            continue
                        else:
                            logger.warning(f"⚠️ Hash collision detected for {hash_key} - overwriting with legacy version")
                    
                    # Save to optimized cache exact tier
                    np.save(exact_path, embedding)
                    
                    # Also save to normalized tier (best effort - we don't have original text)
                    normalized_path = self.optimized_cache.normalized_cache_dir / f"{hash_key}.npy"
                    np.save(normalized_path, embedding)
                    
                    migrated_count += 1
                    
                    # Log progress every 100 files
                    if migrated_count % 100 == 0:
                        logger.info(f"📈 Migration progress: {migrated_count}/{len(valid_files)} files completed")
                    
                except Exception as e:
                    failed_count += 1
                    error_msg = f"Failed to migrate {npy_file.name}: {str(e)}"
                    migration_results["validation_errors"].append(error_msg)
                    logger.error(f"❌ {error_msg}")
                    continue
            
            # Step 4: Post-migration data integrity check
            logger.info("🔍 Performing post-migration data integrity check...")
            
            integrity_check_passed = True
            sample_size = min(10, migrated_count)  # Check up to 10 random files
            
            if sample_size > 0:
                import random
                sample_files = random.sample(valid_files[:migrated_count], sample_size)
                
                for npy_file, original_embedding, hash_key in sample_files:
                    try:
                        migrated_path = self.optimized_cache.exact_cache_dir / f"{hash_key}.npy"
                        migrated_embedding = np.load(migrated_path)
                        
                        if not np.array_equal(original_embedding, migrated_embedding):
                            integrity_check_passed = False
                            logger.error(f"❌ Data integrity check failed for {hash_key}")
                            break
                            
                    except Exception as e:
                        integrity_check_passed = False
                        logger.error(f"❌ Data integrity check error for {hash_key}: {str(e)}")
                        break
            
            # Step 5: Update migration results
            migration_duration = (datetime.now() - migration_start_time).total_seconds()
            
            migration_results.update({
                "success": True,
                "migrated_count": migrated_count,
                "failed_count": failed_count,
                "skipped_count": skipped_count,
                "migration_duration_seconds": round(migration_duration, 2),
                "data_integrity_check": integrity_check_passed
            })
            
            # Generate summary message
            if migrated_count > 0:
                migration_results["message"] = (
                    f"Successfully migrated {migrated_count} embeddings from legacy cache. "
                    f"Failed: {failed_count}, Skipped: {skipped_count}. "
                    f"Duration: {migration_duration:.1f}s"
                )
            else:
                migration_results["message"] = "No valid embeddings found to migrate"
            
            # Log final results
            logger.info("🎉 Legacy cache migration completed!")
            logger.info(f"📊 Migration Summary:")
            logger.info(f"   ✅ Migrated: {migrated_count} files")
            logger.info(f"   ❌ Failed: {failed_count} files")
            logger.info(f"   ⏭️ Skipped: {skipped_count} files")
            logger.info(f"   ⏱️ Duration: {migration_duration:.1f} seconds")
            logger.info(f"   🔍 Data integrity: {'✅ PASSED' if integrity_check_passed else '❌ FAILED'}")
            
            if not integrity_check_passed:
                logger.warning("⚠️ Data integrity check failed - please verify migrated data manually")
            
            return migration_results
            
        except Exception as e:
            migration_duration = (datetime.now() - migration_start_time).total_seconds()
            error_message = f"Critical error during legacy cache migration: {str(e)}"
            
            logger.error(f"💥 {error_message}")
            
            migration_results.update({
                "success": False,
                "message": error_message,
                "migration_duration_seconds": round(migration_duration, 2)
            })
            
            return migration_results

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
    
    async def clear_global_cache(self, cache_type: str = "all") -> Dict[str, Any]:
        """Clear the global embedding cache (optimized and/or legacy)"""
        try:
            import shutil
            
            # Get stats before clearing
            stats_before = self.get_cache_statistics()
            embeddings_removed = 0
            space_freed_mb = 0
            
            # Clear optimized cache
            if cache_type in ["all", "optimized"]:
                optimized_stats = stats_before.get("optimized_cache", {})
                optimized_counts = optimized_stats.get("cache_counts", {})
                optimized_sizes = optimized_stats.get("cache_sizes_mb", {})
                
                embeddings_removed += sum(optimized_counts.values())
                space_freed_mb += optimized_sizes.get("total", 0)
                
                self.optimized_cache.clear_cache("all")
                logger.info("Optimized embedding cache cleared")
            
            # Clear legacy cache
            if cache_type in ["all", "legacy"]:
                legacy_cache_dir = Path("data/embeddings") / "global_cache"
                if legacy_cache_dir.exists():
                    legacy_stats = stats_before.get("legacy_cache", {})
                    embeddings_removed += legacy_stats.get("cached_embeddings", 0)
                    space_freed_mb += legacy_stats.get("cache_size_mb", 0)
                    
                    shutil.rmtree(legacy_cache_dir)
                    logger.info("Legacy embedding cache cleared")
            
            message = f"Global embedding cache cleared successfully"
            if cache_type != "all":
                message = f"{cache_type.title()} cache cleared successfully"
            
            return {
                "success": True,
                "message": message,
                "embeddings_removed": embeddings_removed,
                "space_freed_mb": round(space_freed_mb, 2),
                "cache_type_cleared": cache_type
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