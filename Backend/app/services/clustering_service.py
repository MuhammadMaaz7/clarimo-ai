# """
# Clustering Service - Cluster semantically filtered posts into problem themes
# """
# import json
# import logging
# import numpy as np
# import pandas as pd
# from pathlib import Path
# from sentence_transformers import SentenceTransformer
# from sklearn.preprocessing import normalize
# from sklearn.decomposition import PCA
# import hdbscan
# import umap
# import matplotlib
# matplotlib.use('Agg')  # Use non-GUI backend
# import matplotlib.pyplot as plt
# from typing import Dict, Any, List, Optional, Tuple
# from datetime import datetime
# import asyncio
# import concurrent.futures
# from app.services.embedding_service import get_global_model

# # 🚀 Load global model singleton at module level to avoid repeated imports and thread locks
# GLOBAL_MODEL = get_global_model(use_gpu=False)

# # Configure logging
# logging.basicConfig(level=logging.INFO)
# logger = logging.getLogger(__name__)

# # Constants
# MODEL_NAME = "mixedbread-ai/mxbai-embed-large-v1"
# MIN_CLUSTER_SIZE = 10
# UMAP_N_COMPONENTS = 20
# UMAP_N_NEIGHBORS = 15
# CLUSTER_SUMMARY_FILENAME = "cluster_summary.json"
# CLUSTER_POSTS_FILENAME = "cluster_posts.json"
# CLUSTER_VISUALIZATION_FILENAME = "cluster_visualization.png"
# CLUSTER_CONFIG_FILENAME = "clustering_config.json"

# class ClusteringService:
#     """Service for clustering semantically filtered posts into problem themes"""
    
#     def __init__(self):
#         # 🚀 Use pre-loaded global model singleton
#         self.model = GLOBAL_MODEL
    
#     def _load_filtered_posts(self, filtered_posts_path: Path) -> Tuple[List[Dict], List[str]]:
#         """Load filtered posts and extract text content"""
#         try:
#             with open(filtered_posts_path, "r", encoding="utf-8") as f:
#                 data = json.load(f)
            
#             # Extract text content from posts
#             texts = []
#             for post in data:
#                 text = post.get("text") or post.get("content") or post.get("title", "")
#                 if isinstance(text, str) and text.strip():
#                     texts.append(text.strip())
#                 else:
#                     texts.append("")
            
#             logger.info(f"Loaded {len(data)} filtered posts for clustering")
#             return data, texts
            
#         except Exception as e:
#             logger.error(f"Error loading filtered posts: {str(e)}")
#             raise
    
#     def _load_existing_embeddings(self, user_id: str, input_id: str, posts: List[Dict]) -> np.ndarray:
#         """Load existing embeddings from FAISS index instead of regenerating"""
#         try:
#             import faiss
            
#             # Path to existing embeddings
#             embeddings_dir = Path("data/embeddings") / user_id / input_id
#             faiss_index_path = embeddings_dir / "faiss_index.bin"
#             metadata_path = embeddings_dir / "faiss_metadata.json"
#             embeddings_matrix_path = embeddings_dir / "embeddings.npy"
            
#             if not all(p.exists() for p in [faiss_index_path, metadata_path, embeddings_matrix_path]):
#                 logger.warning("Existing embeddings not found, falling back to generation")
#                 return self._get_embeddings([post.get("text", "") for post in posts])
            
#             logger.info("Loading existing embeddings from FAISS index...")
            
#             # Load metadata to map post IDs to embedding indices
#             with open(metadata_path, 'r', encoding='utf-8') as f:
#                 metadata = json.load(f)
            
#             # Load embedding matrix
#             all_embeddings = np.load(embeddings_matrix_path)
            
#             # Create mapping from post_id to embedding index
#             post_id_to_idx = {}
#             for item in metadata:
#                 if "post_id" in item and "doc_idx" in item:
#                     post_id_to_idx[item["post_id"]] = item["doc_idx"]
            
#             # Extract embeddings for filtered posts
#             filtered_embeddings = []
#             missing_posts = []
            
#             for post in posts:
#                 post_id = post.get("id", "")
#                 if post_id in post_id_to_idx:
#                     idx = post_id_to_idx[post_id]
#                     if idx < len(all_embeddings):
#                         filtered_embeddings.append(all_embeddings[idx])
#                     else:
#                         missing_posts.append(post_id)
#                 else:
#                     missing_posts.append(post_id)
            
#             if missing_posts:
#                 logger.warning(f"Could not find embeddings for {len(missing_posts)} posts, generating them...")
#                 # Generate embeddings for missing posts
#                 missing_texts = [post.get("text", "") for post in posts if post.get("id", "") in missing_posts]
#                 if missing_texts:
#                     missing_embeddings = self._get_embeddings(missing_texts)
#                     filtered_embeddings.extend(missing_embeddings)
            
#             if not filtered_embeddings:
#                 logger.error("No embeddings found, falling back to generation")
#                 return self._get_embeddings([post.get("text", "") for post in posts])
            
#             embeddings = np.array(filtered_embeddings)
#             logger.info(f"✅ Loaded {len(embeddings)} existing embeddings (saved regeneration time!)")
#             return embeddings
            
#         except Exception as e:
#             logger.error(f"Error loading existing embeddings: {str(e)}, falling back to generation")
#             return self._get_embeddings([post.get("text", "") for post in posts])
    
#     def _get_embeddings(self, texts: List[str]) -> np.ndarray:
#         """Generate embeddings for text content (fallback method)"""
#         try:
#             if self.model is None:
#                 raise ValueError("Global model not available for clustering")
                
#             logger.info("Generating embeddings for clustering...")
            
#             # Filter out empty texts
#             valid_texts = [text for text in texts if text.strip()]
#             if len(valid_texts) != len(texts):
#                 logger.warning(f"Filtered out {len(texts) - len(valid_texts)} empty texts")
            
#             if not valid_texts:
#                 raise ValueError("No valid text content found for clustering")
            
#             embeddings = self.model.encode(
#                 valid_texts, 
#                 show_progress_bar=True, 
#                 convert_to_numpy=True,
#                 batch_size=32
#             )
            
#             logger.info(f"Generated embeddings with shape: {embeddings.shape}")
#             return embeddings
            
#         except Exception as e:
#             logger.error(f"Error generating embeddings: {str(e)}")
#             raise
    
#     def _reduce_dimensions(self, embeddings: np.ndarray) -> np.ndarray:
#         """Reduce embedding dimensions using UMAP"""
#         try:
#             logger.info("Reducing dimensions with UMAP for clustering...")
            
#             n_samples = len(embeddings)
            
#             # Adjust parameters for small datasets
#             if n_samples < 15:
#                 # For very small datasets, use PCA instead of UMAP
#                 logger.info(f"Small dataset ({n_samples} samples), using PCA instead of UMAP")
#                 from sklearn.decomposition import PCA
#                 n_components = min(5, n_samples - 1, embeddings.shape[1])
#                 reducer = PCA(n_components=n_components, random_state=42)
#                 reduced_embeddings = reducer.fit_transform(embeddings)
#             else:
#                 # Use UMAP for larger datasets
#                 n_neighbors = min(UMAP_N_NEIGHBORS, n_samples - 1, 5)  # Ensure at least 5 neighbors
#                 n_components = min(UMAP_N_COMPONENTS, n_samples - 1, 10)  # Reduce components for small datasets
                
#                 reducer = umap.UMAP(
#                     n_neighbors=n_neighbors,
#                     n_components=n_components,
#                     metric='cosine',
#                     random_state=42,
#                     verbose=False
#                 )
                
#                 reduced_embeddings = reducer.fit_transform(embeddings)
            
#             # Normalize the reduced embeddings
#             reduced_embeddings = normalize(reduced_embeddings, norm='l2')
            
#             logger.info(f"Reduced embeddings to shape: {reduced_embeddings.shape}")
#             return reduced_embeddings
            
#         except Exception as e:
#             logger.error(f"Error reducing dimensions: {str(e)}")
#             raise
    
#     def _cluster_embeddings(self, embeddings: np.ndarray) -> np.ndarray:
#         """Cluster embeddings using HDBSCAN"""
#         try:
#             logger.info("Clustering embeddings with HDBSCAN...")
            
#             # Adjust min_cluster_size based on data size
#             min_cluster_size = min(MIN_CLUSTER_SIZE, max(3, len(embeddings) // 10))
            
#             clusterer = hdbscan.HDBSCAN(
#                 min_cluster_size=min_cluster_size,
#                 min_samples=2,
#                 metric='euclidean',
#                 cluster_selection_method='eom'
#             )
            
#             cluster_labels = clusterer.fit_predict(embeddings)
            
#             # Count clusters (excluding noise cluster -1)
#             unique_labels = set(cluster_labels)
#             n_clusters = len(unique_labels) - (1 if -1 in unique_labels else 0)
#             n_noise = list(cluster_labels).count(-1)
            
#             logger.info(f"Found {n_clusters} clusters with {n_noise} noise points")
            
#             return cluster_labels
            
#         except Exception as e:
#             logger.error(f"Error clustering embeddings: {str(e)}")
#             raise
    
#     def _summarize_clusters(
#         self, 
#         posts: List[Dict], 
#         texts: List[str], 
#         cluster_labels: np.ndarray,
#         output_dir: Path
#     ) -> Dict[str, Any]:
#         """Create cluster summaries and save results"""
#         try:
#             logger.info("Creating cluster summaries...")
            
#             # Create DataFrame for analysis
#             df = pd.DataFrame({
#                 "text": texts,
#                 "cluster": cluster_labels,
#                 "post_data": posts
#             })
            
#             # Generate cluster summaries
#             clusters = {}
#             cluster_stats = {
#                 "total_posts": len(posts),
#                 "clustered_posts": 0,
#                 "noise_posts": 0,
#                 "n_clusters": 0
#             }
            
#             for label, group in df.groupby("cluster"):
#                 if label == -1:
#                     # Noise cluster
#                     cluster_stats["noise_posts"] = len(group)
#                     continue
                
#                 cluster_stats["clustered_posts"] += len(group)
#                 cluster_stats["n_clusters"] += 1
                
#                 # Get sample posts for this cluster
#                 sample_texts = group["text"].head(15).tolist()
#                 sample_posts = group["post_data"].head(15).tolist()
                
#                 # Calculate cluster statistics
#                 cluster_info = {
#                     "cluster_id": int(label),
#                     "count": len(group),
#                     "percentage": round((len(group) / len(posts)) * 100, 2),
#                     "sample_texts": sample_texts,
#                     "sample_posts": sample_posts,
#                     "created_at": datetime.utcnow().isoformat()
#                 }
                
#                 clusters[int(label)] = cluster_info
            
#             # Save cluster summary
#             summary_path = output_dir / CLUSTER_SUMMARY_FILENAME
#             with open(summary_path, "w", encoding="utf-8") as f:
#                 json.dump({
#                     "clusters": clusters,
#                     "statistics": cluster_stats,
#                     "clustering_metadata": {
#                         "created_at": datetime.utcnow().isoformat(),
#                         "model_used": MODEL_NAME,
#                         "min_cluster_size": MIN_CLUSTER_SIZE,
#                         "umap_components": UMAP_N_COMPONENTS,
#                         "umap_neighbors": UMAP_N_NEIGHBORS
#                     }
#                 }, f, indent=2)
            
#             # Save detailed cluster posts
#             posts_path = output_dir / CLUSTER_POSTS_FILENAME
#             df_output = df.copy()
#             df_output["post_data"] = df_output["post_data"].apply(lambda x: x if isinstance(x, dict) else {})
#             df_output.to_json(posts_path, orient="records", indent=2)
            
#             logger.info(f"Cluster summaries saved to {summary_path}")
#             logger.info(f"Detailed cluster posts saved to {posts_path}")
            
#             return {
#                 "clusters": clusters,
#                 "statistics": cluster_stats,
#                 "output_files": {
#                     "summary": str(summary_path),
#                     "posts": str(posts_path)
#                 }
#             }
            
#         except Exception as e:
#             logger.error(f"Error summarizing clusters: {str(e)}")
#             raise
    
#     def _create_visualization(
#         self, 
#         embeddings: np.ndarray, 
#         cluster_labels: np.ndarray, 
#         output_dir: Path
#     ) -> Optional[str]:
#         """Create cluster visualization"""
#         try:
#             logger.info("Creating cluster visualization...")
            
#             # Reduce to 2D for visualization
#             pca_2d = PCA(n_components=2, random_state=42)
#             embeddings_2d = pca_2d.fit_transform(embeddings)
            
#             # Create plot
#             plt.figure(figsize=(12, 8))
#             scatter = plt.scatter(
#                 embeddings_2d[:, 0], 
#                 embeddings_2d[:, 1],
#                 c=cluster_labels, 
#                 cmap="tab10", 
#                 s=20, 
#                 alpha=0.7
#             )
            
#             plt.colorbar(scatter, label="Cluster ID")
#             plt.title("Problem Theme Clusters (2D Visualization)")
#             plt.xlabel("PCA Component 1")
#             plt.ylabel("PCA Component 2")
#             plt.grid(True, alpha=0.3)
#             plt.tight_layout()
            
#             # Save visualization
#             viz_path = output_dir / CLUSTER_VISUALIZATION_FILENAME
#             plt.savefig(viz_path, dpi=300, bbox_inches='tight')
#             plt.close()
            
#             logger.info(f"Cluster visualization saved to {viz_path}")
#             return str(viz_path)
            
#         except Exception as e:
#             logger.warning(f"Could not create visualization: {str(e)}")
#             return None
    
#     async def cluster_filtered_posts(
#         self,
#         user_id: str,
#         input_id: str,
#         min_cluster_size: Optional[int] = None,
#         create_visualization: bool = True
#     ) -> Dict[str, Any]:
#         """
#         Cluster semantically filtered posts into problem themes
        
#         Args:
#             user_id: User ID
#             input_id: Input ID
#             min_cluster_size: Minimum cluster size (optional)
#             create_visualization: Whether to create visualization
            
#         Returns:
#             Dictionary with clustering results and metadata
#         """
#         try:
#             logger.info(f"Starting clustering for input {input_id} (user: {user_id})")
            
#             # Find filtered posts directory
#             filtered_posts_dir = Path("data/filtered_posts") / user_id / input_id
#             filtered_posts_path = filtered_posts_dir / "filtered_posts.json"
            
#             if not filtered_posts_path.exists():
#                 raise FileNotFoundError(f"Filtered posts not found: {filtered_posts_path}")
            
#             # Create clusters output directory
#             clusters_dir = Path("data/clusters") / user_id / input_id
#             clusters_dir.mkdir(parents=True, exist_ok=True)
            
#             # Load filtered posts
#             posts, texts = self._load_filtered_posts(filtered_posts_path)
            
#             if len(posts) < 3:
#                 logger.warning(f"Too few posts ({len(posts)}) for meaningful clustering")
#                 return {
#                     "success": False,
#                     "message": f"Too few posts ({len(posts)}) for clustering. Need at least 3 posts.",
#                     "total_posts": len(posts),
#                     "clusters_found": 0
#                 }
            
#             # Run clustering in thread pool to avoid blocking
#             loop = asyncio.get_event_loop()
            
#             with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
#                 # Load existing embeddings instead of regenerating them
#                 embeddings = await loop.run_in_executor(
#                     executor, self._load_existing_embeddings, user_id, input_id, posts
#                 )
                
#                 # Reduce dimensions
#                 reduced_embeddings = await loop.run_in_executor(
#                     executor, self._reduce_dimensions, embeddings
#                 )
                
#                 # Cluster
#                 cluster_labels = await loop.run_in_executor(
#                     executor, self._cluster_embeddings, reduced_embeddings
#                 )
                
#                 # Summarize clusters
#                 cluster_results = await loop.run_in_executor(
#                     executor, self._summarize_clusters, posts, texts, cluster_labels, clusters_dir
#                 )
                
#                 # Create visualization if requested
#                 visualization_path = None
#                 if create_visualization:
#                     visualization_path = await loop.run_in_executor(
#                         executor, self._create_visualization, reduced_embeddings, cluster_labels, clusters_dir
#                     )
            
#             # Save clustering configuration
#             clustering_config = {
#                 "user_id": user_id,
#                 "input_id": input_id,
#                 "source_file": str(filtered_posts_path),
#                 "total_posts": len(posts),
#                 "clusters_found": cluster_results["statistics"]["n_clusters"],
#                 "clustered_posts": cluster_results["statistics"]["clustered_posts"],
#                 "noise_posts": cluster_results["statistics"]["noise_posts"],
#                 "min_cluster_size": min_cluster_size or MIN_CLUSTER_SIZE,
#                 "model_used": MODEL_NAME,
#                 "created_at": datetime.utcnow().isoformat(),
#                 "visualization_created": visualization_path is not None
#             }
            
#             config_path = clusters_dir / CLUSTER_CONFIG_FILENAME
#             with open(config_path, "w", encoding="utf-8") as f:
#                 json.dump(clustering_config, f, indent=2)
            
#             logger.info(f"Clustering completed successfully for input {input_id}")
#             logger.info(f"Found {cluster_results['statistics']['n_clusters']} clusters from {len(posts)} posts")
            
#             return {
#                 "success": True,
#                 "message": f"Successfully clustered {len(posts)} posts into {cluster_results['statistics']['n_clusters']} themes",
#                 "total_posts": len(posts),
#                 "clusters_found": cluster_results["statistics"]["n_clusters"],
#                 "clustered_posts": cluster_results["statistics"]["clustered_posts"],
#                 "noise_posts": cluster_results["statistics"]["noise_posts"],
#                 "clusters": cluster_results["clusters"],
#                 "statistics": cluster_results["statistics"],
#                 "output_files": {
#                     **cluster_results["output_files"],
#                     "config": str(config_path),
#                     "visualization": visualization_path
#                 },
#                 "clusters_directory": str(clusters_dir)
#             }
            
#         except Exception as e:
#             logger.error(f"Error in clustering: {str(e)}")
#             return {
#                 "success": False,
#                 "message": f"Clustering failed: {str(e)}",
#                 "total_posts": 0,
#                 "clusters_found": 0
#             }
    
#     async def list_cluster_results(self, user_id: str) -> List[Dict[str, Any]]:
#         """
#         List all cluster results for a specific user
        
#         Args:
#             user_id: User ID to list cluster results for
            
#         Returns:
#             List of dictionaries containing cluster results metadata
#         """
#         try:
#             user_clusters_dir = Path("data/clusters") / user_id
            
#             if not user_clusters_dir.exists():
#                 return []
            
#             cluster_results = []
            
#             for input_dir in user_clusters_dir.iterdir():
#                 if input_dir.is_dir():
#                     summary_path = input_dir / CLUSTER_SUMMARY_FILENAME
#                     config_path = input_dir / CLUSTER_CONFIG_FILENAME
                    
#                     if summary_path.exists():
#                         try:
#                             # Read cluster summary
#                             with open(summary_path, 'r', encoding='utf-8') as f:
#                                 summary_data = json.load(f)
                            
#                             # Read clustering config if available
#                             clustering_config = {}
#                             if config_path.exists():
#                                 with open(config_path, 'r', encoding='utf-8') as f:
#                                     clustering_config = json.load(f)
                            
#                             cluster_results.append({
#                                 "input_id": input_dir.name,
#                                 "clusters_count": len(summary_data.get("clusters", {})),
#                                 "total_posts": clustering_config.get("total_posts", 0),
#                                 "clustered_posts": clustering_config.get("clustered_posts", 0),
#                                 "noise_posts": clustering_config.get("noise_posts", 0),
#                                 "created_date": clustering_config.get("created_at", 
#                                     datetime.fromtimestamp(summary_path.stat().st_ctime).isoformat()
#                                 ),
#                                 "files": {
#                                     "summary": str(summary_path),
#                                     "posts": str(input_dir / CLUSTER_POSTS_FILENAME),
#                                     "config": str(config_path),
#                                     "visualization": str(input_dir / CLUSTER_VISUALIZATION_FILENAME)
#                                 },
#                                 "directory": str(input_dir)
#                             })
#                         except Exception as e:
#                             logger.warning(f"Error reading cluster results for {input_dir}: {str(e)}")
#                             continue
            
#             return sorted(cluster_results, key=lambda x: x["created_date"], reverse=True)
            
#         except Exception as e:
#             logger.error(f"Error listing cluster results: {str(e)}")
#             return []

# # Create a singleton instance for use across the application
# clustering_service = ClusteringService()


"""
Clustering Service - Cluster semantically filtered posts into problem themes
"""
import json
import logging
import numpy as np
import pandas as pd
from pathlib import Path
from sentence_transformers import SentenceTransformer
from sklearn.preprocessing import normalize
from sklearn.decomposition import PCA
import hdbscan
import umap
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
import asyncio
import concurrent.futures
from app.services.embedding_service import get_global_model

# 🚀 Load global model singleton at module level
GLOBAL_MODEL = get_global_model(use_gpu=False)

# Configure logging
logger = logging.getLogger(__name__)

# Constants
MODEL_NAME = "mixedbread-ai/mxbai-embed-large-v1"
MIN_CLUSTER_SIZE = 10
UMAP_N_COMPONENTS = 20
UMAP_N_NEIGHBORS = 15
CLUSTER_SUMMARY_FILENAME = "cluster_summary.json"
CLUSTER_POSTS_FILENAME = "cluster_posts.json"
CLUSTER_VISUALIZATION_FILENAME = "cluster_visualization.png"
CLUSTER_CONFIG_FILENAME = "clustering_config.json"

class ClusteringService:
    """Service for clustering semantically filtered posts into problem themes"""
    
    def __init__(self):
        self.model = GLOBAL_MODEL
    
    def _load_filtered_posts(self, filtered_posts_path: Path) -> Tuple[List[Dict], List[str]]:
        """Load filtered posts and extract text content"""
        try:
            with open(filtered_posts_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            # Extract text content efficiently
            texts = []
            valid_posts = []
            
            for post in data:
                text = post.get("text") or post.get("content") or post.get("title", "")
                if isinstance(text, str) and text.strip():
                    texts.append(text.strip())
                    valid_posts.append(post)
                else:
                    # Keep post but with empty text for consistency
                    texts.append("")
                    valid_posts.append(post)
            
            logger.info(f"Loaded {len(valid_posts)} filtered posts for clustering")
            return valid_posts, texts
            
        except Exception as e:
            logger.error(f"Error loading filtered posts: {str(e)}")
            raise
    
    def _load_existing_embeddings(self, user_id: str, input_id: str, posts: List[Dict]) -> np.ndarray:
        """🚀 Load existing embeddings using optimized cache lookup"""
        try:
            # Use the global embedding cache for much faster lookups
            from app.services.optimized_embedding_cache import get_global_embedding_cache
            cache = get_global_embedding_cache()
            
            logger.info("Loading existing embeddings from optimized cache...")
            
            # Extract text content from filtered posts
            texts = []
            for post in posts:
                title = post.get("title", "")
                content = post.get("text", post.get("content", post.get("selftext", "")))
                combined_text = f"{title} {content}".strip()
                texts.append(combined_text)
            
            # Try to get embeddings from cache
            cached_embeddings = []
            missing_texts = []
            
            for text in texts:
                cached_embedding, _ = cache.get_cached_embedding(text)
                if cached_embedding is not None:
                    cached_embeddings.append(cached_embedding)
                else:
                    missing_texts.append(text)
                    cached_embeddings.append(None)  # Placeholder
            
            # Calculate cache hit rate
            cache_hits = len([e for e in cached_embeddings if e is not None])
            cache_hit_rate = (cache_hits / len(texts) * 100) if texts else 0
            
            if cache_hits > 0:
                logger.info(f"🚀 Cache hit rate: {cache_hit_rate:.1f}% ({cache_hits}/{len(texts)} embeddings)")
            
            # Generate missing embeddings if needed
            if missing_texts:
                logger.info(f"Generating {len(missing_texts)} missing embeddings for clustering...")
                missing_embeddings = self._generate_embeddings_for_texts(missing_texts)
                
                # Fill in the missing embeddings
                missing_idx = 0
                for i, embedding in enumerate(cached_embeddings):
                    if embedding is None:
                        cached_embeddings[i] = missing_embeddings[missing_idx]
                        missing_idx += 1
            
            # Convert to numpy array
            embeddings = np.array([e for e in cached_embeddings if e is not None])
            
            if len(embeddings) == 0:
                logger.warning("No embeddings found, falling back to full generation")
                return self._generate_embeddings(posts)
            
            logger.info(f"✅ Loaded {len(embeddings)} embeddings for clustering ({cache_hit_rate:.1f}% from cache)")
            return embeddings
            
        except Exception as e:
            logger.error(f"Error loading existing embeddings: {str(e)}, falling back to generation")
            return self._generate_embeddings(posts)
    
    def _generate_embeddings_for_texts(self, texts: List[str]) -> np.ndarray:
        """Generate embeddings for text content"""
        if self.model is None:
            logger.error("Model not available for embedding generation")
            return np.array([])
        
        try:
            embeddings = self.model.encode(
                texts,
                show_progress_bar=True,
                convert_to_numpy=True,
                batch_size=32
            )
            return embeddings
        except Exception as e:
            logger.error(f"Error generating embeddings for texts: {str(e)}")
            return np.array([])
    
    def _generate_embeddings(self, posts: List[Dict]) -> np.ndarray:
        """Generate embeddings for posts"""
        if self.model is None:
            raise ValueError("Global model not available for clustering")
        
        # Extract texts from posts
        texts = []
        for post in posts:
            text = post.get("text") or post.get("content") or post.get("title", "")
            texts.append(text.strip() if isinstance(text, str) and text.strip() else "")
        
        valid_texts = [text for text in texts if text.strip()]
        if len(valid_texts) != len(texts):
            logger.warning(f"Filtered out {len(texts) - len(valid_texts)} empty texts")
        
        if not valid_texts:
            raise ValueError("No valid text content found for clustering")
        
        logger.info(f"Generating embeddings for {len(valid_texts)} texts...")
        
        embeddings = self.model.encode(
            valid_texts, 
            show_progress_bar=True, 
            convert_to_numpy=True,
            batch_size=32
        )
        
        logger.info(f"Generated embeddings with shape: {embeddings.shape}")
        return embeddings
    
    def _reduce_dimensions(self, embeddings: np.ndarray) -> np.ndarray:
        """Reduce embedding dimensions using UMAP or PCA"""
        n_samples = len(embeddings)
        
        # For very small datasets, use PCA instead of UMAP
        if n_samples < 15:
            logger.info(f"Small dataset ({n_samples} samples), using PCA")
            n_components = min(5, n_samples - 1, embeddings.shape[1])
            reducer = PCA(n_components=n_components, random_state=42)
            reduced_embeddings = reducer.fit_transform(embeddings)
        else:
            # Use UMAP for larger datasets with adjusted parameters
            n_neighbors = min(UMAP_N_NEIGHBORS, n_samples - 1, 5)
            n_components = min(UMAP_N_COMPONENTS, n_samples - 1, 10)
            
            logger.info(f"Reducing dimensions with UMAP (n_neighbors={n_neighbors}, n_components={n_components})")
            
            reducer = umap.UMAP(
                n_neighbors=n_neighbors,
                n_components=n_components,
                metric='cosine',
                random_state=42,
                verbose=False
            )
            reduced_embeddings = reducer.fit_transform(embeddings)
        
        # Normalize the reduced embeddings
        reduced_embeddings = normalize(reduced_embeddings, norm='l2')
        logger.info(f"Reduced embeddings to shape: {reduced_embeddings.shape}")
        return reduced_embeddings
    
    def _cluster_embeddings(self, embeddings: np.ndarray) -> np.ndarray:
        """Cluster embeddings using HDBSCAN"""
        n_samples = len(embeddings)
        min_cluster_size = min(MIN_CLUSTER_SIZE, max(3, n_samples // 10))
        
        logger.info(f"Clustering {n_samples} embeddings with HDBSCAN (min_cluster_size={min_cluster_size})")
        
        clusterer = hdbscan.HDBSCAN(
            min_cluster_size=min_cluster_size,
            min_samples=2,
            metric='euclidean',
            cluster_selection_method='eom'
        )
        
        cluster_labels = clusterer.fit_predict(embeddings)
        
        # Count clusters (excluding noise cluster -1)
        unique_labels = set(cluster_labels)
        n_clusters = len(unique_labels) - (1 if -1 in unique_labels else 0)
        n_noise = list(cluster_labels).count(-1)
        
        logger.info(f"Found {n_clusters} clusters with {n_noise} noise points")
        return cluster_labels
    
    def _summarize_clusters(
        self, 
        posts: List[Dict], 
        texts: List[str], 
        cluster_labels: np.ndarray,
        output_dir: Path
    ) -> Dict[str, Any]:
        """Create cluster summaries and save results"""
        # Create DataFrame for analysis
        df = pd.DataFrame({
            "text": texts,
            "cluster": cluster_labels,
            "post_data": posts
        })
        
        # Generate cluster summaries
        clusters = {}
        cluster_stats = {
            "total_posts": len(posts),
            "clustered_posts": 0,
            "noise_posts": 0,
            "n_clusters": 0
        }
        
        for label, group in df.groupby("cluster"):
            if label == -1:
                cluster_stats["noise_posts"] = len(group)
                continue
            
            cluster_stats["clustered_posts"] += len(group)
            cluster_stats["n_clusters"] += 1
            
            # Get sample posts for this cluster
            sample_texts = group["text"].head(15).tolist()
            sample_posts = group["post_data"].head(15).tolist()
            
            clusters[int(label)] = {
                "cluster_id": int(label),
                "count": len(group),
                "percentage": round((len(group) / len(posts)) * 100, 2),
                "sample_texts": sample_texts,
                "sample_posts": sample_posts,
                "created_at": datetime.utcnow().isoformat()
            }
        
        # Save cluster summary
        summary_path = output_dir / CLUSTER_SUMMARY_FILENAME
        summary_data = {
            "clusters": clusters,
            "statistics": cluster_stats,
            "clustering_metadata": {
                "created_at": datetime.utcnow().isoformat(),
                "model_used": MODEL_NAME,
                "min_cluster_size": MIN_CLUSTER_SIZE,
                "umap_components": UMAP_N_COMPONENTS,
                "umap_neighbors": UMAP_N_NEIGHBORS
            }
        }
        
        with open(summary_path, "w", encoding="utf-8") as f:
            json.dump(summary_data, f, indent=2)
        
        # Save detailed cluster posts
        posts_path = output_dir / CLUSTER_POSTS_FILENAME
        df.to_json(posts_path, orient="records", indent=2)
        
        logger.info(f"Cluster summaries saved to {summary_path}")
        
        return {
            "clusters": clusters,
            "statistics": cluster_stats,
            "output_files": {
                "summary": str(summary_path),
                "posts": str(posts_path)
            }
        }
    
    def _create_visualization(
        self, 
        embeddings: np.ndarray, 
        cluster_labels: np.ndarray, 
        output_dir: Path
    ) -> Optional[str]:
        """Create cluster visualization"""
        try:
            # Reduce to 2D for visualization
            embeddings_2d = PCA(n_components=2, random_state=42).fit_transform(embeddings)
            
            # Create plot
            plt.figure(figsize=(12, 8))
            scatter = plt.scatter(
                embeddings_2d[:, 0], 
                embeddings_2d[:, 1],
                c=cluster_labels, 
                cmap="tab10", 
                s=20, 
                alpha=0.7
            )
            
            plt.colorbar(scatter, label="Cluster ID")
            plt.title("Problem Theme Clusters (2D Visualization)")
            plt.xlabel("PCA Component 1")
            plt.ylabel("PCA Component 2")
            plt.grid(True, alpha=0.3)
            plt.tight_layout()
            
            # Save visualization
            viz_path = output_dir / CLUSTER_VISUALIZATION_FILENAME
            plt.savefig(viz_path, dpi=300, bbox_inches='tight')
            plt.close()
            
            logger.info(f"Cluster visualization saved to {viz_path}")
            return str(viz_path)
            
        except Exception as e:
            logger.warning(f"Could not create visualization: {str(e)}")
            return None
    
    async def cluster_filtered_posts(
        self,
        user_id: str,
        input_id: str,
        min_cluster_size: Optional[int] = None,
        create_visualization: bool = True
    ) -> Dict[str, Any]:
        """
        Cluster semantically filtered posts into problem themes
        """
        try:
            logger.info(f"Starting clustering for input {input_id} (user: {user_id})")
            
            # Find filtered posts directory
            filtered_posts_path = Path("data/filtered_posts") / user_id / input_id / "filtered_posts.json"
            
            if not filtered_posts_path.exists():
                raise FileNotFoundError(f"Filtered posts not found: {filtered_posts_path}")
            
            # Create clusters output directory
            clusters_dir = Path("data/clusters") / user_id / input_id
            clusters_dir.mkdir(parents=True, exist_ok=True)
            
            # Load filtered posts
            posts, texts = self._load_filtered_posts(filtered_posts_path)
            
            if len(posts) < 3:
                logger.warning(f"Too few posts ({len(posts)}) for meaningful clustering")
                return {
                    "success": False,
                    "message": f"Too few posts ({len(posts)}) for clustering. Need at least 3 posts.",
                    "total_posts": len(posts),
                    "clusters_found": 0
                }
            
            # Run clustering in thread pool
            loop = asyncio.get_event_loop()
            
            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
                # Load existing embeddings
                embeddings = await loop.run_in_executor(
                    executor, self._load_existing_embeddings, user_id, input_id, posts
                )
                
                # Reduce dimensions
                reduced_embeddings = await loop.run_in_executor(
                    executor, self._reduce_dimensions, embeddings
                )
                
                # Cluster
                cluster_labels = await loop.run_in_executor(
                    executor, self._cluster_embeddings, reduced_embeddings
                )
                
                # Summarize clusters
                cluster_results = await loop.run_in_executor(
                    executor, self._summarize_clusters, posts, texts, cluster_labels, clusters_dir
                )
                
                # Create visualization if requested
                visualization_path = None
                if create_visualization:
                    visualization_path = await loop.run_in_executor(
                        executor, self._create_visualization, reduced_embeddings, cluster_labels, clusters_dir
                    )
            
            # Save clustering configuration
            clustering_config = {
                "user_id": user_id,
                "input_id": input_id,
                "source_file": str(filtered_posts_path),
                "total_posts": len(posts),
                "clusters_found": cluster_results["statistics"]["n_clusters"],
                "clustered_posts": cluster_results["statistics"]["clustered_posts"],
                "noise_posts": cluster_results["statistics"]["noise_posts"],
                "min_cluster_size": min_cluster_size or MIN_CLUSTER_SIZE,
                "model_used": MODEL_NAME,
                "created_at": datetime.utcnow().isoformat(),
                "visualization_created": visualization_path is not None
            }
            
            config_path = clusters_dir / CLUSTER_CONFIG_FILENAME
            with open(config_path, "w", encoding="utf-8") as f:
                json.dump(clustering_config, f, indent=2)
            
            logger.info(f"Clustering completed: {cluster_results['statistics']['n_clusters']} clusters from {len(posts)} posts")
            
            return {
                "success": True,
                "message": f"Successfully clustered {len(posts)} posts into {cluster_results['statistics']['n_clusters']} themes",
                "total_posts": len(posts),
                "clusters_found": cluster_results["statistics"]["n_clusters"],
                "clustered_posts": cluster_results["statistics"]["clustered_posts"],
                "noise_posts": cluster_results["statistics"]["noise_posts"],
                "clusters": cluster_results["clusters"],
                "statistics": cluster_results["statistics"],
                "output_files": {
                    **cluster_results["output_files"],
                    "config": str(config_path),
                    "visualization": visualization_path
                },
                "clusters_directory": str(clusters_dir)
            }
            
        except Exception as e:
            logger.error(f"Error in clustering: {str(e)}")
            return {
                "success": False,
                "message": f"Clustering failed: {str(e)}",
                "total_posts": 0,
                "clusters_found": 0
            }
    
    async def list_cluster_results(self, user_id: str) -> List[Dict[str, Any]]:
        """
        List all cluster results for a specific user
        """
        try:
            user_clusters_dir = Path("data/clusters") / user_id
            
            if not user_clusters_dir.exists():
                return []
            
            cluster_results = []
            
            for input_dir in user_clusters_dir.iterdir():
                if not input_dir.is_dir():
                    continue
                    
                summary_path = input_dir / CLUSTER_SUMMARY_FILENAME
                config_path = input_dir / CLUSTER_CONFIG_FILENAME
                
                if summary_path.exists():
                    try:
                        # Read cluster summary
                        with open(summary_path, 'r', encoding='utf-8') as f:
                            summary_data = json.load(f)
                        
                        # Read clustering config if available
                        clustering_config = {}
                        if config_path.exists():
                            with open(config_path, 'r', encoding='utf-8') as f:
                                clustering_config = json.load(f)
                        
                        cluster_results.append({
                            "input_id": input_dir.name,
                            "clusters_count": len(summary_data.get("clusters", {})),
                            "total_posts": clustering_config.get("total_posts", 0),
                            "clustered_posts": clustering_config.get("clustered_posts", 0),
                            "noise_posts": clustering_config.get("noise_posts", 0),
                            "created_date": clustering_config.get("created_at", 
                                datetime.fromtimestamp(summary_path.stat().st_ctime).isoformat()
                            ),
                            "files": {
                                "summary": str(summary_path),
                                "posts": str(input_dir / CLUSTER_POSTS_FILENAME),
                                "config": str(config_path),
                                "visualization": str(input_dir / CLUSTER_VISUALIZATION_FILENAME)
                            },
                            "directory": str(input_dir)
                        })
                    except Exception as e:
                        logger.warning(f"Error reading cluster results for {input_dir}: {str(e)}")
                        continue
            
            return sorted(cluster_results, key=lambda x: x["created_date"], reverse=True)
            
        except Exception as e:
            logger.error(f"Error listing cluster results: {str(e)}")
            return []

# Create a singleton instance for use across the application
clustering_service = ClusteringService()