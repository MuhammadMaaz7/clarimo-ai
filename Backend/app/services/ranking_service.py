"""
Ranking Service - Rank pain points/clusters by multiple metrics
"""
import json
import math
import logging
import asyncio
import concurrent.futures
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional
from datetime import datetime

import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.cluster import DBSCAN
from sklearn.neighbors import NearestNeighbors, LocalOutlierFactor
from sklearn.preprocessing import normalize

# Import processing lock service
from app.services.processing_lock_service import processing_lock_service, ProcessingStage
from app.services.user_input_service import UserInputService

# Try to use sentence-transformers; fallback to TF-IDF
USE_SENTENCE_TRANSFORMERS = True
try:
    from sentence_transformers import SentenceTransformer
    from app.services.embedding_service import get_global_model
except Exception:
    USE_SENTENCE_TRANSFORMERS = False
    from sklearn.feature_extraction.text import TfidfVectorizer

# Configure logging
logger = logging.getLogger(__name__)

# ---------- CONFIG ----------
EMBED_MODEL = "mixedbread-ai/mxbai-embed-large-v1"  # Match the global model
K_FOR_EPS = 5
EPS_PERCENTILE = 10.0  # percentile of k-distance for DBSCAN eps
DBSCAN_MIN_SAMPLES = 2

# Default weights (sum to 1.0)
WEIGHTS = {
    "coherence": 0.35,
    "distinctiveness": 0.25,
    "demand": 0.25,
    "label_confidence": 0.15
}

# Optional pain intensity weight
INCLUDE_OPTIONAL = True
OPTIONAL_PAIN_WEIGHT = 0.05  # 5% extra for pain intensity

# Small negative lexicon for fallback sentiment -> pain intensity
NEG_WORDS = set([
    "problem", "issue", "error", "fail", "failed", "sue", "sued", "expensive", "broken", 
    "hard", "difficult", "lost", "complain", "complaint", "frustrat", "annoy", "angry", 
    "hate", "can't", "cant", "doesn't", "doesnt", "bug", "worst", "terrible", "awful",
    "suck", "sucks", "useless", "waste", "slow", "crash", "freeze", "stuck"
])

class RankingService:
    """Service for ranking pain points/clusters by multiple metrics"""
    
    def __init__(self):
        if USE_SENTENCE_TRANSFORMERS:
            self.model = get_global_model(use_gpu=False)
        else:
            self.model = None
    
    def _load_pain_points_data(self, pain_points_path: Path) -> Dict[str, Any]:
        """Load pain points data from JSON file"""
        try:
            with open(pain_points_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading pain points data: {str(e)}")
            raise
    
    def _safe_get_posts(self, pain_points_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Safely extract pain points from data"""
        return pain_points_data.get("pain_points", [])
    
    def _estimate_dbscan_eps(self, embeddings: np.ndarray, k: int = K_FOR_EPS, percentile: float = EPS_PERCENTILE) -> float:
        """Estimate eps using the k-distance heuristic (cosine distances). Returns value in [0,1]."""
        n = embeddings.shape[0]
        if n <= k:
            return 0.35
        nn = NearestNeighbors(n_neighbors=min(k+1, n), metric='cosine').fit(embeddings)
        dists, _ = nn.kneighbors(embeddings, return_distance=True)
        # dists[:,0] is zero (self); take k-th column
        k_index = min(k, dists.shape[1]-1)
        kth = dists[:, k_index]
        eps = float(np.percentile(kth, percentile))
        eps = max(1e-6, min(0.9999, eps))
        return eps
    
    def _compute_centroid(self, embs: np.ndarray) -> np.ndarray:
        """Compute normalized centroid of embeddings"""
        if embs.size == 0:
            return np.zeros((embs.shape[1],), dtype=float)
        c = np.mean(embs, axis=0)
        norm = np.linalg.norm(c)
        return c / norm if norm != 0 else c
    
    def _safe_cosine(self, a: np.ndarray, b: np.ndarray) -> float:
        """Safe cosine similarity calculation"""
        if a is None or b is None:
            return 0.0
        na = np.linalg.norm(a)
        nb = np.linalg.norm(b)
        if na == 0 or nb == 0:
            return 0.0
        return float(np.dot(a, b) / (na * nb))
    
    def _scale_to_0_10(self, arr: np.ndarray) -> np.ndarray:
        """Scale array values to 0-10 range"""
        if arr.size == 0:
            return arr
        mn = float(np.min(arr))
        mx = float(np.max(arr))
        if np.isclose(mx, mn):
            return np.full_like(arr, 5.0, dtype=float)
        scaled = (arr - mn) / (mx - mn) * 10.0
        return scaled
    
    def _embed_texts_sent_transformer(self, texts: List[str], batch_size: int = 64) -> np.ndarray:
        """Generate embeddings using sentence transformer"""
        if self.model is None:
            raise ValueError("Sentence transformer model not available")
        
        emb = self.model.encode(texts, batch_size=batch_size, show_progress_bar=False, convert_to_numpy=True)
        # normalize
        emb = normalize(emb, norm='l2', axis=1)
        return emb
    
    def _embed_texts_tfidf(self, texts: List[str]) -> np.ndarray:
        """Generate embeddings using TF-IDF"""
        vect = TfidfVectorizer(max_features=4096, ngram_range=(1,2))
        X = vect.fit_transform(texts).toarray()
        # normalize
        X = normalize(X, norm='l2', axis=1)
        return X
    
    def _embed_texts(self, texts: List[str]) -> np.ndarray:
        """Generate embeddings for texts"""
        if len(texts) == 0:
            return np.zeros((0, 768))
        
        if USE_SENTENCE_TRANSFORMERS and self.model is not None:
            try:
                return self._embed_texts_sent_transformer(texts)
            except Exception as e:
                logger.warning(f"Sentence transformer failed, falling back to TF-IDF: {e}")
                return self._embed_texts_tfidf(texts)
        else:
            return self._embed_texts_tfidf(texts)
    
    def _detect_noise_dbscan(self, embeddings: np.ndarray, eps: float = None, min_samples: int = DBSCAN_MIN_SAMPLES) -> List[bool]:
        """Detect noise using DBSCAN"""
        if embeddings.shape[0] == 0:
            return []
        if eps is None:
            eps = self._estimate_dbscan_eps(embeddings)
        clustering = DBSCAN(eps=eps, min_samples=min_samples, metric='cosine').fit(embeddings)
        labels = clustering.labels_  # -1 indicates noise
        return [lab == -1 for lab in labels]
    
    def _lof_cleanliness_scores(self, embeddings: np.ndarray, n_neighbors: int = 20) -> np.ndarray:
        """Return cleanliness 0-10 where higher = cleaner (less outlier)."""
        if embeddings.shape[0] == 0:
            return np.array([], dtype=float)
        n_neighbors = min(max(2, int(n_neighbors)), embeddings.shape[0] - 1)
        lof = LocalOutlierFactor(n_neighbors=n_neighbors, metric='cosine', novelty=False)
        lof.fit(embeddings)
        neg = lof.negative_outlier_factor_
        mn, mx = float(np.min(neg)), float(np.max(neg))
        if np.isclose(mx, mn):
            return np.full_like(neg, 5.0, dtype=float)
        scaled = (neg - mn) / (mx - mn) * 10.0
        return np.clip(scaled, 0.0, 10.0)
    
    def _simple_negative_ratio(self, texts: List[str]) -> float:
        """Return percent of texts that contain any NEG_WORDS (0-10 scaled)."""
        if not texts:
            return 0.0
        neg_count = 0
        for t in texts:
            tt = (t or "").lower()
            for w in NEG_WORDS:
                if w in tt:
                    neg_count += 1
                    break
        pct = neg_count / len(texts)
        return float(pct * 10.0)  # 0-10
    
    def _rank_clusters(self, pain_points_data: Dict[str, Any]) -> Dict[str, Any]:
        """Main ranking logic"""
        clusters = self._safe_get_posts(pain_points_data)
        
        # Flatten posts and keep mapping cluster -> indices
        all_texts = []
        cluster_post_ranges: List[Tuple[int,int]] = []  # start,end indexes for each cluster
        labels = []
        cluster_ids = []
        
        for c in clusters:
            posts = c.get("post_references", []) or []
            start = len(all_texts)
            for p in posts:
                # use 'text' field if available, else try title or url as string
                txt = p.get("text") or p.get("title") or p.get("body") or ""
                all_texts.append(txt)
            end = len(all_texts)
            cluster_post_ranges.append((start, end))
            labels.append(c.get("problem_title", "") or "")
            cluster_ids.append(str(c.get("cluster_id", "")))
        
        total_posts = len(all_texts) or 1
        
        logger.info(f"Found {len(clusters)} clusters and {len(all_texts)} total posts (flattened).")
        
        # Create embeddings (for posts) and label embeddings
        post_embeddings = self._embed_texts(all_texts) if len(all_texts) > 0 else np.zeros((0, 768))
        # label embeddings
        label_embeddings = self._embed_texts(labels) if len(labels) > 0 else np.zeros((0, post_embeddings.shape[1] if post_embeddings.size else 768))
        
        # Per-cluster embeddings lists and centroids
        centroids = []
        per_cluster_embs = []
        cluster_sizes = []
        for (start, end) in cluster_post_ranges:
            embs = post_embeddings[start:end] if end > start else np.zeros((0, post_embeddings.shape[1] if post_embeddings.size else 768))
            per_cluster_embs.append(embs)
            c = self._compute_centroid(embs) if embs.size else np.zeros((post_embeddings.shape[1],))
            centroids.append(c)
            cluster_sizes.append(embs.shape[0])
        
        centroids_arr = np.vstack(centroids) if len(centroids) > 0 else np.zeros((0, post_embeddings.shape[1] if post_embeddings.size else 768))
        
        # Distinctiveness: mean Euclidean distance from centroid to other centroids -> scale 0-10
        distinct_raw = []
        for i, c in enumerate(centroids):
            if centroids_arr.shape[0] <= 1:
                distinct_raw.append(0.0)
                continue
            others = np.delete(centroids_arr, i, axis=0)
            dists = np.linalg.norm(others - c, axis=1)
            distinct_raw.append(float(np.mean(dists)))
        distinct_raw = np.array(distinct_raw, dtype=float)
        distinct_0_10 = self._scale_to_0_10(distinct_raw)
        
        # Coherence, Label confidence, Demand, Noise, Sentiment
        metrics_list = []
        # For DBSCAN eps estimation, use global eps based on all post embeddings when available
        global_eps = None
        if post_embeddings.shape[0] > 0:
            try:
                global_eps = self._estimate_dbscan_eps(post_embeddings, k=K_FOR_EPS, percentile=EPS_PERCENTILE)
            except Exception:
                global_eps = None
        
        # Compute LOF cleanliness per post (continuous)
        lof_scores_per_post = self._lof_cleanliness_scores(post_embeddings) if post_embeddings.shape[0] > 0 else np.array([])
        
        for idx, c in enumerate(clusters):
            embs = per_cluster_embs[idx]
            centroid = centroids[idx] if centroids_arr.size else np.zeros((post_embeddings.shape[1],))
            size = embs.shape[0]
            
            # Coherence
            if size == 0:
                coherence = 0.0
            elif size == 1:
                coherence = 10.0
            else:
                sims = cosine_similarity(embs, centroid.reshape(1, -1)).reshape(-1)
                # map [-1,1] -> [0,10]
                coherence = float(np.mean((sims + 1.0) / 2.0 * 10.0))
            
            # Label confidence
            label_emb = label_embeddings[idx] if label_embeddings.size else np.zeros_like(centroid)
            lab_cos = self._safe_cosine(label_emb, centroid)
            label_confidence = float((lab_cos + 1.0) / 2.0 * 10.0)
            
            # Demand / Size
            demand = float(size / total_posts * 10.0)
            
            # Noise detection: DBSCAN per-cluster if cluster large enough else use global DBSCAN mapping
            noise_flags = []
            if size > 0:
                try:
                    # choose eps: if cluster big enough estimate from its emb, else use global_eps
                    eps = None
                    if embs.shape[0] > K_FOR_EPS:
                        eps = self._estimate_dbscan_eps(embs, k=min(K_FOR_EPS, embs.shape[0]-1), percentile=EPS_PERCENTILE)
                    elif global_eps is not None:
                        eps = global_eps
                    else:
                        eps = 0.35
                    local_noise = self._detect_noise_dbscan(embs, eps=eps, min_samples=DBSCAN_MIN_SAMPLES)
                    noise_flags = local_noise
                except Exception:
                    # fallback to LOF continuous decision: mark points with cleanliness < some percentile as noise
                    if lof_scores_per_post.size:
                        # map to the slice for this cluster
                        start, end = cluster_post_ranges[idx]
                        lof_slice = lof_scores_per_post[start:end]
                        # threshold at 20th percentile of cluster
                        if lof_slice.size:
                            thresh = float(np.percentile(lof_slice, 20))
                            noise_flags = [s < thresh for s in lof_slice]
                        else:
                            noise_flags = [False] * size
                    else:
                        noise_flags = [False] * size
            else:
                noise_flags = []
            
            noise_frac = (sum(1 for f in noise_flags if f) / size) if size > 0 else 0.0
            noise_ratio_0_10 = float(noise_frac * 10.0)  # 0 = clean, 10 = all noisy
            noise_score_cleanliness = float(10.0 - noise_ratio_0_10)  # 10 = clean, 0 = very noisy
            
            # Optional: pain_intensity via simple negative lexicon ratio
            post_texts = [p.get("text", "") or p.get("title", "") or "" for p in c.get("post_references", [])]
            pain_intensity = self._simple_negative_ratio(post_texts)  # 0-10 where higher=more negative/complaint
            
            metrics_list.append({
                "cluster_index": idx,
                "cluster_id": str(c.get("cluster_id", idx)),
                "coherence_raw": coherence,
                "distinctiveness_raw": float(distinct_raw[idx]) if len(distinct_raw)>idx else 0.0,
                "distinctiveness": float(distinct_0_10[idx]) if len(distinct_0_10)>idx else 0.0,
                "demand_raw": demand,
                "label_confidence_raw": label_confidence,
                "noise_ratio_raw": noise_ratio_0_10,
                "noise_score_raw": noise_score_cleanliness,
                "pain_intensity_raw": pain_intensity,
                "cluster_size": size,
                "centroid": centroid.tolist(),
            })
        
        # Normalize/scaling: ensure all fields present and in bounds
        for m in metrics_list:
            for key in ["coherence_raw","distinctiveness","demand_raw","label_confidence_raw","noise_ratio_raw","noise_score_raw","pain_intensity_raw"]:
                if m.get(key) is None:
                    m[key] = 0.0
                m[key] = max(0.0, min(10.0, float(m[key])))
        
        # Compute final weighted score
        for m in metrics_list:
            final = (
                WEIGHTS.get("coherence", 0.0) * m["coherence_raw"]
                + WEIGHTS.get("distinctiveness", 0.0) * m["distinctiveness"]
                + WEIGHTS.get("demand", 0.0) * m["demand_raw"]
                + WEIGHTS.get("label_confidence", 0.0) * m["label_confidence_raw"]
            )
            
            # If user requested optional metrics to be included, add them here.
            if INCLUDE_OPTIONAL:
                final += OPTIONAL_PAIN_WEIGHT * m.get("pain_intensity_raw", 0.0)
            
            m["final_score"] = round(float(final), 6)
        
        # Sort by final score
        ranked = sorted(metrics_list, key=lambda x: x["final_score"], reverse=True)
        
        # Build output structure (attach metrics into original clusters structure)
        output = {
            "metadata": pain_points_data.get("metadata", {}),
            "ranked_pain_points": []
        }
        
        for r in ranked:
            idx = r["cluster_index"]
            cluster_obj = clusters[idx].copy()
            cluster_obj.setdefault("metrics", {}).update({
                "coherence": round(r["coherence_raw"], 4),
                "distinctiveness": round(r["distinctiveness"], 4),
                "demand": round(r["demand_raw"], 4),
                "label_confidence": round(r["label_confidence_raw"], 4),
                "noise_ratio": round(r["noise_ratio_raw"], 4),
                "noise_score": round(r["noise_score_raw"], 4),
                "pain_intensity": round(r["pain_intensity_raw"], 4),
                "cluster_size": r["cluster_size"],
                "final_score": r["final_score"]
            })
            output["ranked_pain_points"].append(cluster_obj)
        
        # Add ranking metadata
        output["ranking_metadata"] = {
            "ranked_at": datetime.utcnow().isoformat(),
            "total_clusters": len(clusters),
            "weights_used": WEIGHTS,
            "optional_pain_weight": OPTIONAL_PAIN_WEIGHT if INCLUDE_OPTIONAL else 0.0,
            "include_optional": INCLUDE_OPTIONAL,
            "model_used": EMBED_MODEL if USE_SENTENCE_TRANSFORMERS else "TF-IDF"
        }
        
        return output
    
    async def rank_pain_points(
        self,
        user_id: str,
        input_id: str
        ) -> Dict[str, Any]:
        """
        Rank pain points by multiple metrics
        
        Args:
            user_id: User identifier
            input_id: Input identifier
            
        Returns:
            Dict containing ranking results
        """
        try:
            logger.info(f"Starting ranking for input {input_id} (user: {user_id})")
            
            # ✅ FIXED: Check if we have the processing lock (should be held by pain points service)
            if not await processing_lock_service.is_processing(user_id, input_id):
                logger.warning(f"No active processing lock found for {user_id}:{input_id}. Attempting to reacquire.")
                
                # Try to reacquire the lock for ranking stage
                lock_acquired = await processing_lock_service.acquire_lock(user_id, input_id)
                if not lock_acquired:
                    logger.error(f"Could not acquire processing lock for ranking {user_id}:{input_id}")
                    return {
                        "success": False,
                        "message": "Could not acquire processing lock for ranking"
                    }
            
            # ✅ FIXED: Update processing stage to RANKING
            await processing_lock_service.update_stage(user_id, input_id, ProcessingStage.RANKING)
            await UserInputService.update_processing_stage(user_id, input_id, ProcessingStage.RANKING.value)
            
            # ✅ FIXED: Use the correct pain points file path
            pain_points_path = Path("data/pain_points") / user_id / input_id / "marketable_pain_points_all.json"
            
            if not pain_points_path.exists():
                error_msg = f"Pain points file not found: {pain_points_path}"
                logger.error(error_msg)
                
                # ✅ FIXED: Update status and release lock on error
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
                    "message": error_msg
                }
            
            # Create ranking output directory
            ranking_dir = Path("data/rankings") / user_id / input_id
            ranking_dir.mkdir(parents=True, exist_ok=True)
            
            # Load pain points data
            pain_points_data = self._load_pain_points_data(pain_points_path)
            
            # Run ranking in thread pool
            loop = asyncio.get_event_loop()
            
            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
                ranked_data = await loop.run_in_executor(
                    executor, self._rank_clusters, pain_points_data
                )
            
            # Save ranked results
            ranked_path = ranking_dir / "ranked_pain_points.json"
            with open(ranked_path, "w", encoding="utf-8") as f:
                json.dump(ranked_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Ranking completed: {len(ranked_data['ranked_pain_points'])} pain points ranked")
            
            # Log ranking table
            self._log_ranking_table(ranked_data["ranked_pain_points"])
            
            # ✅ FIXED: Update final status to completed and release lock
            await UserInputService.update_input_status(
                user_id=user_id,
                input_id=input_id,
                status="completed",
                current_stage=ProcessingStage.COMPLETED.value
            )
            
            await processing_lock_service.release_lock(user_id, input_id, completed=True)
            logger.info(f"Released processing lock after ranking completion for {input_id}")
            
            return {
                "success": True,
                "message": f"Successfully ranked {len(ranked_data['ranked_pain_points'])} pain points",
                "ranked_pain_points": ranked_data["ranked_pain_points"],
                "ranking_metadata": ranked_data["ranking_metadata"],
                "output_file": str(ranked_path)
            }
            
        except Exception as e:
            logger.error(f"Error in ranking: {str(e)}")
            
            # ✅ FIXED: Update status to failed and release lock on error
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
                "message": f"Ranking failed: {str(e)}"
            }

    def _log_ranking_table(self, ranked_pain_points: List[Dict[str, Any]]):
        """Log a formatted ranking table"""
        try:
            header = f"{'Rank':<5}{'Cluster':<10}{'Coherence':>10}{'Distinct.':>12}{'Demand':>10}{'LabelConf':>12}{'PainInt':>9}{'Noise%':>8}{'Final':>10}"
            logger.info("Ranking Results:")
            logger.info(header)
            logger.info("-" * len(header))
            
            for i, pain_point in enumerate(ranked_pain_points[:10], start=1):  # Show top 10
                metrics = pain_point.get("metrics", {})
                cluster_id = pain_point.get("cluster_id", "N/A")
                
                log_line = (
                    f"{i:<5}{cluster_id:<10}"
                    f"{metrics.get('coherence', 0):10.2f}"
                    f"{metrics.get('distinctiveness', 0):12.2f}"
                    f"{metrics.get('demand', 0):10.2f}"
                    f"{metrics.get('label_confidence', 0):12.2f}"
                    f"{metrics.get('pain_intensity', 0):9.2f}"
                    f"{metrics.get('noise_ratio', 0):8.2f}"
                    f"{metrics.get('final_score', 0):10.4f}"
                )
                logger.info(log_line)
            
            if len(ranked_pain_points) > 10:
                logger.info(f"... and {len(ranked_pain_points) - 10} more")
                
        except Exception as e:
            logger.warning(f"Error logging ranking table: {str(e)}")

# Create singleton instance
ranking_service = RankingService()