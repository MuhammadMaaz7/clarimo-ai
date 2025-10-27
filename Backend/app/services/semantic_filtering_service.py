"""
Semantic Filtering Service - Filter Reddit posts using semantic similarity
"""
import json
import logging
import numpy as np
import faiss
from pathlib import Path
from sentence_transformers import SentenceTransformer
from tqdm import tqdm
import pandas as pd
from typing import Dict, Any, List, Optional
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Constants
MODEL_NAME = "mixedbread-ai/mxbai-embed-large-v1"
META_FILENAME = "faiss_metadata.json"
FAISS_INDEX_FILENAME = "faiss_index.bin"
EMBED_MATRIX_FILENAME = "embeddings.npy"
FILTERED_POSTS_FILENAME = "filtered_posts.json"
FILTERED_METADATA_CSV = "filtered_metadata.csv"

class SemanticFilteringService:
    """Service for semantic filtering of Reddit posts using FAISS similarity search"""
    
    def __init__(self):
        self.model: Optional[SentenceTransformer] = None
    
    def _load_model(self):
        """Load the embedding model (same as used for embedding generation)"""
        if self.model is None:
            logger.info(f"Loading model {MODEL_NAME} for semantic filtering...")
            self.model = SentenceTransformer(MODEL_NAME, device="cpu")
    
    def _load_index_and_metadata(self, index_dir: Path) -> tuple:
        """Load FAISS index, metadata, and embedding matrix"""
        try:
            # Load FAISS index
            index_path = index_dir / FAISS_INDEX_FILENAME
            if not index_path.exists():
                raise FileNotFoundError(f"FAISS index not found: {index_path}")
            
            index = faiss.read_index(str(index_path))
            
            # Load metadata
            metadata_path = index_dir / META_FILENAME
            if not metadata_path.exists():
                raise FileNotFoundError(f"Metadata file not found: {metadata_path}")
            
            with open(metadata_path, "r", encoding="utf-8") as f:
                metadata = json.load(f)
            
            # Load embedding matrix
            emb_matrix_path = index_dir / EMBED_MATRIX_FILENAME
            if not emb_matrix_path.exists():
                raise FileNotFoundError(f"Embedding matrix not found: {emb_matrix_path}")
            
            emb_matrix = np.load(emb_matrix_path)
            
            logger.info(f"Loaded index with {len(metadata)} documents")
            return index, metadata, emb_matrix
            
        except Exception as e:
            logger.error(f"Error loading index and metadata: {str(e)}")
            raise
    
    async def semantic_filter_posts(
        self,
        user_id: str,
        input_id: str,
        query: str,
        top_k: int = 500,
        similarity_threshold: float = 0.55
    ) -> Dict[str, Any]:
        """
        Filter Reddit posts using semantic similarity to user query
        
        Args:
            user_id: User ID
            input_id: Input ID
            query: User query for semantic filtering
            top_k: Number of candidates to retrieve before filtering
            similarity_threshold: Minimum cosine similarity to keep
            
        Returns:
            Dictionary with filtering results and metadata
        """
        try:
            logger.info(f"Starting semantic filtering for input {input_id} (user: {user_id})")
            logger.info(f"Query: '{query}', top_k: {top_k}, threshold: {similarity_threshold}")
            
            # Find embeddings directory
            embeddings_dir = Path("data/embeddings") / user_id / input_id
            if not embeddings_dir.exists():
                raise FileNotFoundError(f"Embeddings directory not found: {embeddings_dir}")
            
            # Load FAISS index and metadata
            index, metadata, emb_matrix = self._load_index_and_metadata(embeddings_dir)
            
            # Load model and encode query
            self._load_model()
            logger.info("Encoding user query...")
            query_emb = self.model.encode([query], convert_to_numpy=True).astype('float32')
            faiss.normalize_L2(query_emb)
            
            # Search for similar posts
            logger.info(f"Searching top {top_k} semantically similar posts...")
            scores, indices = index.search(query_emb, min(top_k, len(metadata)))
            scores = scores[0]
            indices = indices[0]
            
            # Filter by similarity threshold
            relevant_posts = []
            for score, idx in zip(scores, indices):
                if score >= similarity_threshold:
                    doc = metadata[idx].copy()  # Make a copy to avoid modifying original
                    doc["similarity_score"] = float(score)
                    doc["filtered_at"] = datetime.utcnow().isoformat()
                    relevant_posts.append(doc)
            
            logger.info(f"Found {len(relevant_posts)} relevant posts (similarity ≥ {similarity_threshold})")
            
            # Create separate directory for filtered posts
            filtered_posts_dir = Path("data/filtered_posts") / user_id / input_id
            filtered_posts_dir.mkdir(parents=True, exist_ok=True)
            
            # Save filtered results
            filtered_posts_path = filtered_posts_dir / FILTERED_POSTS_FILENAME
            with open(filtered_posts_path, "w", encoding="utf-8") as f:
                json.dump(relevant_posts, f, indent=2)
            
            # Save CSV metadata
            if relevant_posts:
                filtered_csv_path = filtered_posts_dir / FILTERED_METADATA_CSV
                pd.DataFrame(relevant_posts).to_csv(filtered_csv_path, index=False)
                logger.info(f"Filtered metadata saved to {filtered_csv_path}")
            
            # Save filtering configuration for reference
            filtering_config = {
                "query": query,
                "top_k": top_k,
                "similarity_threshold": similarity_threshold,
                "total_documents": len(metadata),
                "filtered_documents": len(relevant_posts),
                "filtered_at": datetime.utcnow().isoformat(),
                "embeddings_source": str(embeddings_dir)
            }
            
            config_path = filtered_posts_dir / "filtering_config.json"
            with open(config_path, "w", encoding="utf-8") as f:
                json.dump(filtering_config, f, indent=2)
            
            logger.info(f"Filtered posts saved to {filtered_posts_path}")
            logger.info(f"Filtering config saved to {config_path}")
            
            # Trigger automatic clustering if we have enough posts
            if len(relevant_posts) >= 5:
                try:
                    logger.info("Triggering automatic clustering after filtering...")
                    from app.services.clustering_service import clustering_service
                    
                    # Run clustering in background (don't wait for completion)
                    import asyncio
                    asyncio.create_task(clustering_service.cluster_filtered_posts(
                        user_id=user_id,
                        input_id=input_id,
                        create_visualization=True
                    ))
                    
                    logger.info("Automatic clustering task started")
                except Exception as e:
                    logger.warning(f"Failed to start automatic clustering: {str(e)}")
            else:
                logger.info(f"Skipping clustering - too few posts ({len(relevant_posts)})")
            
            # Create summary statistics
            similarity_stats = {
                "min_similarity": float(min([p["similarity_score"] for p in relevant_posts])) if relevant_posts else 0.0,
                "max_similarity": float(max([p["similarity_score"] for p in relevant_posts])) if relevant_posts else 0.0,
                "avg_similarity": float(np.mean([p["similarity_score"] for p in relevant_posts])) if relevant_posts else 0.0
            }
            
            return {
                "success": True,
                "message": f"Successfully filtered {len(relevant_posts)} relevant posts from {len(metadata)} total",
                "total_documents": len(metadata),
                "filtered_documents": len(relevant_posts),
                "similarity_threshold": similarity_threshold,
                "similarity_stats": similarity_stats,
                "output_files": {
                    "filtered_posts": str(filtered_posts_path),
                    "filtered_csv": str(filtered_posts_dir / FILTERED_METADATA_CSV) if relevant_posts else None,
                    "filtering_config": str(filtered_posts_dir / "filtering_config.json")
                },
                "filtered_posts_directory": str(filtered_posts_dir),
                "query_used": query
            }
            
        except Exception as e:
            logger.error(f"Error in semantic filtering: {str(e)}")
            return {
                "success": False,
                "message": f"Semantic filtering failed: {str(e)}",
                "total_documents": 0,
                "filtered_documents": 0
            }
    
    async def list_filtered_results(self, user_id: str) -> List[Dict[str, Any]]:
        """
        List all filtered results for a specific user
        
        Args:
            user_id: User ID to list filtered results for
            
        Returns:
            List of dictionaries containing filtered results metadata
        """
        try:
            user_filtered_dir = Path("data/filtered_posts") / user_id
            
            if not user_filtered_dir.exists():
                return []
            
            filtered_results = []
            
            for input_dir in user_filtered_dir.iterdir():
                if input_dir.is_dir():
                    filtered_posts_path = input_dir / FILTERED_POSTS_FILENAME
                    config_path = input_dir / "filtering_config.json"
                    
                    if filtered_posts_path.exists():
                        try:
                            # Read filtered posts to get count and metadata
                            with open(filtered_posts_path, 'r', encoding='utf-8') as f:
                                filtered_posts = json.load(f)
                            
                            # Read filtering config if available
                            filtering_config = {}
                            if config_path.exists():
                                with open(config_path, 'r', encoding='utf-8') as f:
                                    filtering_config = json.load(f)
                            
                            # Calculate statistics
                            similarity_scores = [p.get("similarity_score", 0) for p in filtered_posts]
                            
                            filtered_results.append({
                                "input_id": input_dir.name,
                                "filtered_count": len(filtered_posts),
                                "total_documents": filtering_config.get("total_documents", 0),
                                "query_used": filtering_config.get("query", ""),
                                "similarity_threshold": filtering_config.get("similarity_threshold", 0.55),
                                "created_date": filtering_config.get("filtered_at", 
                                    datetime.fromtimestamp(filtered_posts_path.stat().st_ctime).isoformat()
                                ),
                                "similarity_stats": {
                                    "min_similarity": float(min(similarity_scores)) if similarity_scores else 0.0,
                                    "max_similarity": float(max(similarity_scores)) if similarity_scores else 0.0,
                                    "avg_similarity": float(np.mean(similarity_scores)) if similarity_scores else 0.0
                                },
                                "files": {
                                    "filtered_posts": str(filtered_posts_path),
                                    "filtered_csv": str(input_dir / FILTERED_METADATA_CSV),
                                    "filtering_config": str(config_path)
                                },
                                "directory": str(input_dir)
                            })
                        except Exception as e:
                            logger.warning(f"Error reading filtered results for {input_dir}: {str(e)}")
                            continue
            
            return sorted(filtered_results, key=lambda x: x["created_date"], reverse=True)
            
        except Exception as e:
            logger.error(f"Error listing filtered results: {str(e)}")
            return []

# Create a singleton instance for use across the application
semantic_filtering_service = SemanticFilteringService()