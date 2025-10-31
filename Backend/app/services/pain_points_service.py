"""
Pain Points Extraction Service

This service analyzes clustered Reddit posts to extract marketable pain points
that could inspire startup ideas. It uses LLM analysis to transform raw clusters
into structured business opportunities.
"""

import json
import time
import math
import os
import asyncio
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from groq import Groq

from app.core.logging import logger

# Import processing lock service
from app.services.processing_lock_service import processing_lock_service, ProcessingStage
from app.services.user_input_service import UserInputService

# ---------- CONFIG ----------
API_KEY = os.getenv("GROQ_API_KEY")
MODEL = "llama-3.3-70b-versatile"
MAX_RESPONSE_TOKENS = 800
CONSERVATIVE_CHAR_PER_TOKEN = 4.0
MAX_CHARS_PER_CLUSTER = 4000
SAMPLE_POSTS_PER_CLUSTER = 4
RETRY_ATTEMPTS = 3
RETRY_BACKOFF_BASE = 2.0
MAX_CLUSTERS_TO_PROCESS = 50  # Safety limit

class PainPointsService:
    """Service for extracting marketable pain points from clustered Reddit posts"""
    
    def __init__(self):
        if not API_KEY:
            raise ValueError("GROQ_API_KEY environment variable is required")
        self.client = Groq(api_key=API_KEY)
    
    def _est_tokens_from_chars(self, chars: int) -> int:
        """Conservative estimate: tokens ~= chars / 4"""
        return math.ceil(chars / CONSERVATIVE_CHAR_PER_TOKEN)
    
    def _safe_truncate(self, text: str, max_chars: int) -> str:
        """Safely truncate text to maximum characters, preserving sentence boundaries when possible."""
        if not text:
            return ""
        if len(text) <= max_chars:
            return text
        
        # Try to cut at the last sentence boundary for nicer output
        cut = text[:max_chars]
        last_period = cut.rfind('.')
        last_exclamation = cut.rfind('!')
        last_question = cut.rfind('?')
        last_sentence_end = max(last_period, last_exclamation, last_question)
        
        if last_sentence_end > int(max_chars * 0.4):
            return cut[:last_sentence_end + 1] + " [TRUNCATED]"
        return cut + " [TRUNCATED]"
    
    def _extract_post_references(self, cluster: Dict, max_posts: int = 5) -> List[Dict]:
        """Extract structured post references from cluster data for frontend display."""
        post_references = []
        
        # Get sample posts from cluster
        sample_posts = cluster.get("sample_posts", [])[:max_posts]
        
        for post in sample_posts:
            post_ref = {
                "post_id": post.get("post_id") or post.get("doc_id") or "unknown",
                "subreddit": post.get("subreddit", ""),
                "created_utc": post.get("created_utc", ""),
                "url": post.get("url", ""),
                "text": self._safe_truncate(post.get("text") or post.get("body") or "", 500),
                "title": post.get("title", ""),
                "score": post.get("score", 0),
                "num_comments": post.get("num_comments", 0)
            }
            # Clean up empty values
            post_ref = {k: v for k, v in post_ref.items() if v}
            post_references.append(post_ref)
        
        return post_references
    
    def _build_cluster_payload(self, cluster: Dict) -> str:
        """Build a compact, human-readable block for a single cluster."""
        parts = []
        cid = cluster.get("cluster_id", cluster.get("id", "unknown"))
        parts.append(f"Cluster ID: {cid}")
        parts.append(f"Count: {cluster.get('count', '')}  Percentage: {cluster.get('percentage', '')}")
        
        # Sample texts
        sample_texts = cluster.get("sample_texts", [])
        if sample_texts:
            # Filter out empty texts and join with separator
            valid_texts = [t for t in sample_texts if t is not None and t.strip() != ""]
            if valid_texts:
                joined = " || ".join(valid_texts)
                joined = self._safe_truncate(joined, 800)
                parts.append("Sample Texts: " + joined)
        
        # Sample posts
        sample_posts = cluster.get("sample_posts", [])[:SAMPLE_POSTS_PER_CLUSTER]
        posts_strs = []
        for p in sample_posts:
            doc_id = p.get("doc_id") or p.get("post_id")
            url = p.get("url", "") or doc_id or ""
            subreddit = p.get("subreddit", "")
            created = p.get("created_utc", "")
            text_snip = p.get("text") or p.get("body") or ""
            text_snip = self._safe_truncate(text_snip, 300)
            posts_strs.append(f"[{subreddit}] {created} {url} // {text_snip}")
        
        if posts_strs:
            parts.append("Sample Posts:\n" + "\n".join(posts_strs))
        
        if "created_at" in cluster:
            parts.append(f"Cluster created_at: {cluster.get('created_at')}")
        
        block = "\n".join(parts)
        # Enforce per-cluster limit
        if len(block) > MAX_CHARS_PER_CLUSTER:
            block = self._safe_truncate(block, MAX_CHARS_PER_CLUSTER)
        return block
    
    def _parse_llm_response(self, response_text: str, cluster_id: str, post_references: List[Dict]) -> Dict:
        """Parse LLM response and structure it with post references."""
        try:
            # Initialize simplified response
            structured_response = {
                "cluster_id": cluster_id,
                "problem_title": "",
                "problem_description": "",
                "post_references": post_references,
                "analysis_timestamp": time.time(),
                "source": "reddit_cluster_analysis"
            }
            
            # Simple parsing of the LLM response
            lines = response_text.split('\n')
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                    
                if line.startswith('**Problem Title:**'):
                    structured_response["problem_title"] = line.replace('**Problem Title:**', '').strip().strip('"')
                elif line.startswith('**Problem Description:**'):
                    structured_response["problem_description"] = line.replace('**Problem Description:**', '').strip()
            
            return structured_response
            
        except Exception as e:
            logger.error(f"Error parsing LLM response for cluster {cluster_id}: {e}")
            # Return a basic structure even if parsing fails
            return {
                "cluster_id": cluster_id,
                "problem_title": "Analysis failed",
                "problem_description": "Failed to parse analysis",
                "post_references": post_references,
                "analysis_timestamp": time.time(),
                "source": "reddit_cluster_analysis",
                "error": True,
                "error_message": str(e)
            }
    
    async def _process_cluster_with_llm(self, cluster_id: str, cluster_block: str, post_references: List[Dict]) -> Dict:
        """Process a single cluster with the LLM and return structured response with post references."""
        
        prompt = f"""
You are a market analyst specializing in identifying real user problems from online discussions.

For the Reddit discussion cluster below, extract and clearly define the PROBLEM that users are experiencing.

Output exactly in this format:

Cluster {cluster_id}
**Problem Title:** "..."
**Problem Description:** ...

Focus on:
- What specific problem/frustration users are experiencing
- Why this problem matters to them
- Keep it concise and clear

Cluster data:
{cluster_block}
"""

        # Token management
        prompt_chars = len(prompt)
        prompt_tokens_est = self._est_tokens_from_chars(prompt_chars)
        logger.info(f"Prompt chars ~{prompt_chars}, est tokens ~{prompt_tokens_est}. Max response tokens: {MAX_RESPONSE_TOKENS}")

        # If prompt seems too large in tokens, do an emergency truncation
        GROQ_TOKEN_LIMIT = 12000
        allowed_prompt_tokens = GROQ_TOKEN_LIMIT - MAX_RESPONSE_TOKENS
        
        if prompt_tokens_est > allowed_prompt_tokens:
            logger.info("Prompt appears large. Truncating cluster content further to fit token budget.")
            reduction_factor = allowed_prompt_tokens / prompt_tokens_est
            new_max_chars = int(len(cluster_block) * reduction_factor * 0.9)  # 10% safety margin
            cluster_block = self._safe_truncate(cluster_block, new_max_chars)
            prompt = prompt.split("Cluster data:")[0] + "Cluster data:\n" + cluster_block
            prompt_chars = len(prompt)
            prompt_tokens_est = self._est_tokens_from_chars(prompt_chars)
            logger.info(f"After truncation: prompt chars ~{prompt_chars}, est tokens ~{prompt_tokens_est}")

        # API call with retries
        last_error = None
        for attempt in range(RETRY_ATTEMPTS):
            try:
                completion = self.client.chat.completions.create(
                    model=MODEL,
                    messages=[
                        {"role": "system", "content": "You are a professional market researcher. Be concise and analytical."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.4,
                    max_completion_tokens=MAX_RESPONSE_TOKENS
                )
                response_text = completion.choices[0].message.content
                logger.info(f"Success: received {len(response_text)} chars response for cluster {cluster_id}")
                
                # Parse and structure the response with post references
                structured_response = self._parse_llm_response(response_text, cluster_id, post_references)
                return structured_response
                
            except Exception as e:
                last_error = e
                logger.error(f"Error on attempt {attempt + 1} for cluster {cluster_id}: {e}")
                if attempt < RETRY_ATTEMPTS - 1:
                    wait = RETRY_BACKOFF_BASE ** (attempt + 1)
                    logger.info(f"Retrying in {wait:.0f}s...")
                    await asyncio.sleep(wait)
                else:
                    logger.error(f"Failed after {RETRY_ATTEMPTS} attempts for cluster {cluster_id}.")
        
        # ✅ FIX: Return error response instead of None
        return {
            "cluster_id": cluster_id,
            "problem_title": "LLM Processing Failed",
            "problem_description": f"Failed to process cluster after {RETRY_ATTEMPTS} attempts: {str(last_error)}",
            "post_references": post_references,
            "analysis_timestamp": time.time(),
            "source": "reddit_cluster_analysis",
            "error": True,
            "error_message": str(last_error)
        }
    
    async def extract_pain_points_from_clusters(
        self,
        user_id: str,
        input_id: str,
        output_dir: Optional[str] = None,
        original_query: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Extract pain points from existing cluster data.
        
        Args:
            user_id: User identifier
            input_id: Input identifier
            output_dir: Optional output directory (defaults to clusters directory)
        
        Returns:
            Dict containing results and structured pain point data
        """
        try:
            # Check if process is already running and update stage
            if not await processing_lock_service.is_processing(user_id, input_id):
                logger.warning(f"Process {user_id}:{input_id} not found in active processes")
                return {
                    "success": False,
                    "error": "Process not found or not in progress",
                    "total_clusters": 0,
                    "processed": 0,
                    "failed": 0,
                    "individual_files": [],
                    "aggregated_file": None,
                    "pain_points_data": None
                }
            
            # Update processing stage to PAIN_POINTS_EXTRACTION
            await processing_lock_service.update_stage(user_id, input_id, ProcessingStage.PAIN_POINTS_EXTRACTION)
            await UserInputService.update_processing_stage(user_id, input_id, ProcessingStage.PAIN_POINTS_EXTRACTION.value)
            
            # Determine cluster paths (source)
            clusters_dir = Path("data/clusters") / user_id / input_id
            cluster_summary_path = clusters_dir / "cluster_summary.json"
            cluster_posts_path = clusters_dir / "cluster_posts.json"
            
            if not cluster_summary_path.exists():
                error_msg = f"Cluster summary not found: {cluster_summary_path}"
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
                    "error": error_msg,
                    "total_clusters": 0,
                    "processed": 0,
                    "failed": 0,
                    "individual_files": [],
                    "aggregated_file": None,
                    "pain_points_data": None
                }
            
            # Set pain points output directory (separate from clusters)
            if output_dir:
                output_path = Path(output_dir)
            else:
                output_path = Path("data/pain_points") / user_id / input_id
            output_path.mkdir(parents=True, exist_ok=True)
            
            logger.info(f"Extracting pain points for user {user_id}, input {input_id}")
            
            # Load cluster summary
            with open(cluster_summary_path, "r", encoding="utf-8") as f:
                cluster_summary = json.load(f)

            # Load cluster posts if available
            cluster_posts = {}
            if cluster_posts_path.exists():
                try:
                    with open(cluster_posts_path, "r", encoding="utf-8") as f:
                        cluster_posts = json.load(f)
                except Exception as e:
                    logger.warning(f"Could not load cluster posts: {e}")

            # Extract clusters
            clusters_dict = cluster_summary.get("clusters") or cluster_summary
            
            # Sort clusters numerically when possible
            cluster_items = []
            for key, cluster in clusters_dict.items():
                try:
                    # Try to convert to int for numeric sorting
                    numeric_key = int(key)
                    cluster_items.append((numeric_key, cluster))
                except (ValueError, TypeError):
                    cluster_items.append((key, cluster))
            
            cluster_items.sort(key=lambda x: x[0] if isinstance(x[0], (int, float)) else str(x[0]))
            
            # ✅ FIX: Limit number of clusters to process for safety
            if len(cluster_items) > MAX_CLUSTERS_TO_PROCESS:
                logger.warning(f"Too many clusters ({len(cluster_items)}), limiting to {MAX_CLUSTERS_TO_PROCESS}")
                cluster_items = cluster_items[:MAX_CLUSTERS_TO_PROCESS]

            # Prepare output files
            aggregated_file = output_path / "marketable_pain_points_all.json"
            
            # Store all pain points with references for frontend
            all_pain_points = {
                "metadata": {
                    "total_clusters": len(cluster_items),
                    "analysis_timestamp": time.time(),
                    "version": "1.0",
                    "user_id": user_id,
                    "input_id": input_id,
                    "source_files": {
                        "cluster_summary": str(cluster_summary_path),
                        "cluster_posts": str(cluster_posts_path) if cluster_posts_path.exists() else None
                    }
                },
                "pain_points": []
            }

            results = {
                "success": True,
                "total_clusters": len(cluster_items),
                "processed": 0,
                "failed": 0,
                "individual_files": [],
                "aggregated_file": str(aggregated_file),
                "pain_points_data": all_pain_points
            }

            # Process each cluster
            for key, cluster in cluster_items:
                cluster_id = str(cluster.get("cluster_id", key))
                logger.info(f"Processing cluster {cluster_id} (key={key}) ...")
                
                try:
                    # Extract post references before processing
                    post_references = self._extract_post_references(cluster)
                    cluster_block = self._build_cluster_payload(cluster)
                    
                    # Process with LLM
                    structured_pain_point = await self._process_cluster_with_llm(
                        cluster_id, cluster_block, post_references
                    )
                    
                    # ✅ FIX: Always add to results, even if LLM failed
                    if structured_pain_point:
                        # Save individual file as JSON
                        out_file = output_path / f"pain_point_cluster_{cluster_id}.json"
                        with open(out_file, "w", encoding="utf-8") as f:
                            json.dump(structured_pain_point, f, indent=2, ensure_ascii=False)
                        results["individual_files"].append(str(out_file))
                        
                        # Add to aggregated pain points
                        all_pain_points["pain_points"].append(structured_pain_point)
                        
                        # Count as processed or failed based on error flag
                        if structured_pain_point.get("error"):
                            results["failed"] += 1
                            logger.error(f"✗ Failed to process cluster {cluster_id}: {structured_pain_point.get('error_message')}")
                        else:
                            results["processed"] += 1
                            logger.info(f"✓ Successfully processed cluster {cluster_id} with {len(post_references)} post references")
                    else:
                        # This should not happen with our fix above, but just in case
                        results["failed"] += 1
                        logger.error(f"✗ LLM returned None for cluster {cluster_id}")
                        
                        # Create consistent error entry
                        error_entry = {
                            "cluster_id": cluster_id,
                            "problem_title": "Processing Failed",
                            "problem_description": "LLM analysis returned no response",
                            "post_references": post_references,
                            "analysis_timestamp": time.time(),
                            "source": "reddit_cluster_analysis",
                            "error": True,
                            "error_message": "LLM returned None"
                        }
                        all_pain_points["pain_points"].append(error_entry)
                        
                except Exception as e:
                    results["failed"] += 1
                    logger.error(f"✗ Error processing cluster {cluster_id}: {e}")
                    
                    # ✅ FIX: Create consistent error entry format
                    error_entry = {
                        "cluster_id": cluster_id,
                        "problem_title": "Processing Error",
                        "problem_description": f"Failed to analyze cluster: {str(e)}",
                        "post_references": self._extract_post_references(cluster),
                        "analysis_timestamp": time.time(),
                        "source": "reddit_cluster_analysis",
                        "error": True,
                        "error_message": str(e)
                    }
                    all_pain_points["pain_points"].append(error_entry)
                
                # Rate limiting delay
                await asyncio.sleep(0.6)

            # Save aggregated JSON file
            with open(aggregated_file, "w", encoding="utf-8") as f:
                json.dump(all_pain_points, f, indent=2, ensure_ascii=False)

            # Save to database
            try:
                from app.services.pain_points_db_service import pain_points_db_service
                
                # Use the provided original query or a fallback
                query_for_db = original_query or "User problem analysis"
                
                await pain_points_db_service.save_pain_points_analysis(
                    user_id=user_id,
                    input_id=input_id,
                    original_query=query_for_db,
                    pain_points_data=all_pain_points
                )
                logger.info(f"Successfully saved pain points to database for {input_id}")
            except Exception as db_error:
                logger.error(f"Error saving pain points to database: {str(db_error)}")
                # Don't fail the entire process if database save fails

            # ✅ FIX: Update processing stage to COMPLETED and release lock
            try:
                await processing_lock_service.update_stage(user_id, input_id, ProcessingStage.COMPLETED)
                await UserInputService.update_input_status(
                    user_id=user_id,
                    input_id=input_id,
                    status="completed",
                    current_stage=ProcessingStage.COMPLETED.value
                )
                logger.info(f"Updated user input status to 'completed' for {input_id}")
            except Exception as status_error:
                logger.error(f"Error updating user input status: {str(status_error)}")

            # ✅ FIX: Release lock after successful completion
            try:
                await processing_lock_service.release_lock(user_id, input_id, completed=True)
                logger.info(f"Released processing lock after successful pain points extraction for {input_id}")
            except Exception as lock_error:
                logger.error(f"Error releasing processing lock: {str(lock_error)}")

            logger.info(f"Pain points extraction complete!")
            logger.info(f"Total clusters: {results['total_clusters']}")
            logger.info(f"Successfully processed: {results['processed']}")
            logger.info(f"Failed: {results['failed']}")
            logger.info(f"Aggregated results: {results['aggregated_file']}")
            logger.info(f"Total pain points with post references: {len(all_pain_points['pain_points'])}")
            
            # ✅ FIX: Return more detailed success information
            return {
                **results,
                "pain_points_count": len(all_pain_points['pain_points']),
                "completed_at": time.time(),
                "success_rate": (results["processed"] / results["total_clusters"] * 100) if results["total_clusters"] > 0 else 0
            }
            
        except Exception as e:
            logger.error(f"Error in pain points extraction: {str(e)}")
            
            # ✅ FIX: Update database status on failure and release lock
            try:
                await UserInputService.update_input_status(
                    user_id=user_id,
                    input_id=input_id,
                    status="failed",
                    current_stage=ProcessingStage.FAILED.value,
                    error_message=f"Pain points extraction failed: {str(e)}"
                )
            except Exception as status_error:
                logger.error(f"Error updating failed status: {str(status_error)}")
            
            try:
                await processing_lock_service.release_lock(user_id, input_id, completed=False)
            except Exception as lock_error:
                logger.error(f"Error releasing lock on failure: {str(lock_error)}")
            
            return {
                "success": False,
                "error": str(e),
                "total_clusters": 0,
                "processed": 0,
                "failed": 0,
                "individual_files": [],
                "aggregated_file": None,
                "pain_points_data": None
            }
    
    async def get_pain_points_results(self, user_id: str, input_id: str) -> Optional[Dict]:
        """Load pain points results for a specific input."""
        try:
            pain_points_dir = Path("data/pain_points") / user_id / input_id
            results_file = pain_points_dir / "marketable_pain_points_all.json"
            
            if not results_file.exists():
                return None
            
            with open(results_file, "r", encoding="utf-8") as f:
                return json.load(f)
                
        except Exception as e:
            logger.error(f"Error loading pain points results: {e}")
            return None
    
    def get_pain_points_by_domain(self, results_data: Dict) -> Dict[str, List[Dict]]:
        """Group pain points by domain for frontend categorization."""
        if not results_data or "pain_points" not in results_data:
            return {}
        
        by_domain = {}
        for pain_point in results_data["pain_points"]:
            domain = pain_point.get("domain", "Uncategorized")
            if domain not in by_domain:
                by_domain[domain] = []
            by_domain[domain].append(pain_point)
        
        return by_domain
    
    async def list_pain_points_results(self, user_id: str) -> List[Dict[str, Any]]:
        """List all pain points results for a user."""
        try:
            user_pain_points_dir = Path("data/pain_points") / user_id
            if not user_pain_points_dir.exists():
                return []
            
            results = []
            for input_dir in user_pain_points_dir.iterdir():
                if input_dir.is_dir():
                    pain_points_file = input_dir / "marketable_pain_points_all.json"
                    if pain_points_file.exists():
                        try:
                            with open(pain_points_file, "r", encoding="utf-8") as f:
                                data = json.load(f)
                            
                            metadata = data.get("metadata", {})
                            results.append({
                                "input_id": input_dir.name,
                                "total_pain_points": len(data.get("pain_points", [])),
                                "analysis_timestamp": metadata.get("analysis_timestamp"),
                                "total_clusters": metadata.get("total_clusters", 0),
                                "file_path": str(pain_points_file)
                            })
                        except Exception as e:
                            logger.error(f"Error reading pain points file {pain_points_file}: {e}")
            
            # Sort by timestamp (newest first)
            results.sort(key=lambda x: x.get("analysis_timestamp", 0), reverse=True)
            return results
            
        except Exception as e:
            logger.error(f"Error listing pain points results: {e}")
            return []

# Global service instance
pain_points_service = PainPointsService()