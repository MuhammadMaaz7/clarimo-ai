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
from app.services.problem_discovery.embedding_service import get_global_model

# Import processing lock service
from app.services.shared.processing_lock_manager import processing_lock_service, ProcessingStage
from app.services.problem_discovery.user_input_service import UserInputService

# Load global model singleton at module level
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
            from app.services.shared.embedding_cache import get_global_cache
            cache = get_global_cache()
            
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
        create_visualization: bool = True,
        original_query: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Cluster semantically filtered posts into problem themes
        """
        try:
            logger.info(f"Starting clustering for input {input_id} (user: {user_id})")
            
            # Check if process is already running and update stage
            if not await processing_lock_service.is_processing(user_id, input_id):
                logger.warning(f"Process {user_id}:{input_id} not found in active processes")
                return {
                    "success": False,
                    "message": "Process not found or not in progress",
                    "total_posts": 0,
                    "clusters_found": 0
                }
            
            # Update processing stage to CLUSTERING
            await processing_lock_service.update_stage(user_id, input_id, ProcessingStage.CLUSTERING)
            await UserInputService.update_processing_stage(user_id, input_id, ProcessingStage.CLUSTERING.value)
            
            # Find filtered posts directory
            filtered_posts_path = Path("data/filtered_posts") / user_id / input_id / "filtered_posts.json"
            
            if not filtered_posts_path.exists():
                error_msg = f"Filtered posts not found: {filtered_posts_path}"
                logger.error(error_msg)
                
                # Update status and release lock on error
                await UserInputService.update_input_status(
                    user_id=user_id,
                    input_id=input_id,
                    status="failed",
                    current_stage=ProcessingStage.FAILED.value,
                    error_message=error_msg
                )
                await processing_lock_service.release_lock(user_id, input_id, completed=False)
                
                return {
                    "success": False,
                    "message": error_msg,
                    "total_posts": 0,
                    "clusters_found": 0
                }
            
            # Create clusters output directory
            clusters_dir = Path("data/clusters") / user_id / input_id
            clusters_dir.mkdir(parents=True, exist_ok=True)
            
            # Load filtered posts
            posts, texts = self._load_filtered_posts(filtered_posts_path)
            
            if len(posts) < 3:
                logger.warning(f"Too few posts ({len(posts)}) for meaningful clustering")
                error_msg = f"Too few posts ({len(posts)}) for clustering. Need at least 3 posts."
                
                # Update status and release lock
                await UserInputService.update_input_status(
                    user_id=user_id,
                    input_id=input_id,
                    status="failed",
                    current_stage=ProcessingStage.FAILED.value,
                    error_message=error_msg
                )
                await processing_lock_service.release_lock(user_id, input_id, completed=False)
                
                return {
                    "success": False,
                    "message": error_msg,
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
            
            # Update stage to PAIN_POINTS_EXTRACTION
            await processing_lock_service.update_stage(user_id, input_id, ProcessingStage.PAIN_POINTS_EXTRACTION)
            await UserInputService.update_processing_stage(user_id, input_id, ProcessingStage.PAIN_POINTS_EXTRACTION.value)
            
            # ✅ FIX: Wait for pain points extraction to complete before returning
            pain_points_success = False
            ranking_success = False
            try:
                logger.info(f"Starting automatic pain points extraction for input {input_id}")
                from app.services.problem_discovery.pain_points_service import pain_points_service
                
                pain_points_result = await pain_points_service.extract_pain_points_from_clusters(
                    user_id=user_id,
                    input_id=input_id,
                    original_query=original_query
                )
                
                pain_points_success = pain_points_result["success"]
                if pain_points_success:
                    pain_points_count = len(pain_points_result["pain_points_data"]["pain_points"]) if pain_points_result["pain_points_data"] else 0
                    logger.info(f"Automatic pain points extraction completed: {pain_points_count} pain points generated")
                    
                    # ✅ NEW: Start ranking after pain points extraction
                    try:
                        logger.info(f"Starting automatic ranking for input {input_id}")
                        from app.services.problem_discovery.ranking_service import ranking_service
                        
                        ranking_result = await ranking_service.rank_pain_points(
                            user_id=user_id,
                            input_id=input_id
                        )
                        
                        ranking_success = ranking_result["success"]
                        if ranking_success:
                            logger.info(f"Automatic ranking completed successfully")
                        else:
                            logger.warning(f"Automatic ranking failed: {ranking_result.get('message', 'Unknown error')}")
                            
                    except Exception as ranking_error:
                        logger.error(f"Error in automatic ranking: {str(ranking_error)}")
                        # Don't fail the pipeline if ranking fails
                        
                else:
                    logger.warning(f"Automatic pain points extraction failed: {pain_points_result.get('error', 'Unknown error')}")
                    
            except Exception as pain_points_error:
                logger.error(f"Error in automatic pain points extraction: {str(pain_points_error)}")
                # Don't fail the clustering if pain points extraction fails
            
            # ✅ FIX: Update database status after complete pipeline
            # Note: Status and lock release are now handled by ranking_service
            # Only update here if ranking was not attempted
            if not pain_points_success:
                try:
                    await UserInputService.update_input_status(
                        user_id=user_id,
                        input_id=input_id,
                        status="completed_with_warnings",
                        current_stage=ProcessingStage.COMPLETED.value
                    )
                    logger.info(f"Updated database status to 'completed_with_warnings' for input {input_id}")
                except Exception as status_error:
                    logger.error(f"Error updating database status: {str(status_error)}")
                
                # Release lock if ranking was not attempted
                try:
                    await processing_lock_service.release_lock(user_id, input_id, completed=False)
                    logger.info(f"Released processing lock after clustering failure for {input_id}")
                except Exception as lock_error:
                    logger.error(f"Error releasing processing lock: {str(lock_error)}")
            
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
                "clusters_directory": str(clusters_dir),
                "pain_points_extraction_success": pain_points_success,
                "ranking_success": ranking_success
            }
            
        except Exception as e:
            logger.error(f"Error in clustering: {str(e)}")
            
            # ✅ FIX: Update status to failed and release lock on error
            try:
                await UserInputService.update_input_status(
                    user_id=user_id,
                    input_id=input_id,
                    status="failed",
                    current_stage=ProcessingStage.FAILED.value,
                    error_message=str(e)
                )
            except Exception as status_error:
                logger.error(f"Error updating failed status: {str(status_error)}")
            
            try:
                await processing_lock_service.release_lock(user_id, input_id, completed=False)
            except Exception as lock_error:
                logger.error(f"Error releasing lock on failure: {str(lock_error)}")
            
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