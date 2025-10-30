"""
Processing Status API Routes - Track background processing status
"""
from fastapi import APIRouter, HTTPException, status, Depends
from typing import Dict, Any
import logging
import json
from pathlib import Path

from app.db.models.user_model import UserResponse
from app.core.security import get_current_user

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/processing-status", tags=["Processing Status"])

@router.get("/{input_id}")
async def get_processing_status(
    input_id: str,
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Get the interactive processing status for a specific input with engaging messages.
    
    Returns detailed status with user-friendly messages and progress indicators.
    """
    try:
        logger.info(f"Checking processing status for input {input_id} (user: {current_user.id})")
        
        # Check Reddit data
        reddit_dir = Path("data/reddit_posts") / current_user.id
        reddit_files = list(reddit_dir.glob(f"reddit_posts_{input_id}_*.json"))
        reddit_posts_count = 0
        
        if reddit_files:
            # Try to get post count from the file
            try:
                import json
                with open(reddit_files[0], 'r', encoding='utf-8') as f:
                    reddit_data = json.load(f)
                    reddit_posts_count = reddit_data.get('total_posts', 0)
            except Exception:
                reddit_posts_count = 0
        
        # Check embeddings
        embeddings_dir = Path("data/embeddings") / current_user.id / input_id
        embeddings_completed = (embeddings_dir / "faiss_index.bin").exists()
        
        # Check semantic filtering
        filtered_dir = Path("data/filtered_posts") / current_user.id / input_id
        filtering_completed = (filtered_dir / "filtered_posts.json").exists()
        
        # Check clustering
        clusters_dir = Path("data/clusters") / current_user.id / input_id
        clustering_completed = (clusters_dir / "cluster_summary.json").exists()
        
        # Check pain points extraction in dedicated directory
        pain_points_dir = Path("data/pain_points") / current_user.id / input_id
        pain_points_completed = (pain_points_dir / "marketable_pain_points_all.json").exists()
        pain_points_count = 0
        if pain_points_completed:
            try:
                with open(pain_points_dir / "marketable_pain_points_all.json", 'r', encoding='utf-8') as f:
                    pain_points_data = json.load(f)
                    pain_points_count = len(pain_points_data.get("pain_points", []))
            except Exception:
                pain_points_count = 0
        
        # Determine current stage and create engaging messages
        if pain_points_completed:
            # All done including clustering!
            try:
                with open(filtered_dir / "filtered_posts.json", 'r', encoding='utf-8') as f:
                    filtered_posts = json.load(f)
                    filtered_count = len(filtered_posts)
                
                with open(clusters_dir / "cluster_summary.json", 'r', encoding='utf-8') as f:
                    cluster_data = json.load(f)
                    clusters_count = len(cluster_data.get("clusters", {}))
            except Exception:
                filtered_count = 0
                clusters_count = 0
                
            return {
                "input_id": input_id,
                "overall_status": "completed",
                "progress_percentage": 100,
                "current_stage": "completed",
                "message": "Analysis complete. Opportunities discovered.",
                "description": f"Found {pain_points_count} marketable problems from {filtered_count} posts across {clusters_count} themes",
                "animation": "celebration",
                "next_action": "View your startup opportunities with real user evidence",
                "stages": {
                    "keyword_generation": {"status": "completed", "message": "Keywords generated", "icon": "key"},
                    "reddit_fetch": {"status": "completed", "message": f"{reddit_posts_count} posts collected", "icon": "search"},
                    "embedding_generation": {"status": "completed", "message": "AI analysis complete", "icon": "brain"},
                    "semantic_filtering": {"status": "completed", "message": f"{filtered_count} problems discovered", "icon": "target"},
                    "clustering": {"status": "completed", "message": f"{clusters_count} themes identified", "icon": "folder"},
                    "pain_points": {"status": "completed", "message": f"{pain_points_count} opportunities found", "icon": "lightbulb"}
                },
                "estimated_time_remaining": "0 minutes",
                "can_view_results": True,
                "pain_points_available": True,
                "pain_points_count": pain_points_count
            }
            
        elif clustering_completed:
            # Clustering done, pain points extraction in progress
            try:
                with open(filtered_dir / "filtered_posts.json", 'r', encoding='utf-8') as f:
                    filtered_posts = json.load(f)
                    filtered_count = len(filtered_posts)
                
                with open(clusters_dir / "cluster_summary.json", 'r', encoding='utf-8') as f:
                    cluster_data = json.load(f)
                    clusters_count = len(cluster_data.get("clusters", {}))
            except Exception:
                filtered_count = 0
                clusters_count = 0
                
            return {
                "input_id": input_id,
                "overall_status": "extracting_pain_points",
                "progress_percentage": 98,
                "current_stage": "pain_points_extraction",
                "message": "💡 Discovering startup opportunities...",
                "description": f"AI is analyzing {clusters_count} problem themes to find marketable opportunities",
                "animation": "analyzing",
                "next_action": "Generating business-ready problem insights",
                "stages": {
                    "keyword_generation": {"status": "completed", "message": "✅ Keywords generated", "icon": "🔑"},
                    "reddit_fetch": {"status": "completed", "message": f"✅ {reddit_posts_count} posts collected", "icon": "📡"},
                    "embedding_generation": {"status": "completed", "message": "✅ AI analysis complete", "icon": "🧠"},
                    "semantic_filtering": {"status": "completed", "message": f"✅ {filtered_count} problems discovered", "icon": "🎯"},
                    "clustering": {"status": "completed", "message": f"✅ {clusters_count} themes identified", "icon": "🗂️"},
                    "pain_points": {"status": "in_progress", "message": "💡 Finding opportunities...", "icon": "⚡"}
                },
                "estimated_time_remaining": "30 seconds",
                "can_view_results": False,
                "pain_points_available": False
            }
            
        elif filtering_completed:
            # Filtering done, clustering in progress
            try:
                with open(filtered_dir / "filtered_posts.json", 'r', encoding='utf-8') as f:
                    filtered_posts = json.load(f)
                    filtered_count = len(filtered_posts)
            except Exception:
                filtered_count = 0
                
            return {
                "input_id": input_id,
                "overall_status": "clustering",
                "progress_percentage": 95,
                "current_stage": "clustering",
                "message": "🗂️ Organizing problems into themes...",
                "description": f"Grouping {filtered_count} problems into thematic clusters for better insights",
                "animation": "organizing",
                "next_action": "Creating problem themes and categories",
                "stages": {
                    "keyword_generation": {"status": "completed", "message": "✅ Keywords generated", "icon": "🔑"},
                    "reddit_fetch": {"status": "completed", "message": f"✅ {reddit_posts_count} posts collected", "icon": "📡"},
                    "embedding_generation": {"status": "completed", "message": "✅ AI analysis complete", "icon": "🧠"},
                    "semantic_filtering": {"status": "completed", "message": f"✅ {filtered_count} problems discovered", "icon": "🎯"},
                    "clustering": {"status": "in_progress", "message": "🗂️ Organizing into themes...", "icon": "⚡"}
                },
                "estimated_time_remaining": "1-2 minutes",
                "can_view_results": False
            }
            
        elif embeddings_completed:
            # Embeddings done, filtering in progress
            return {
                "input_id": input_id,
                "overall_status": "filtering_posts",
                "progress_percentage": 85,
                "current_stage": "semantic_filtering",
                "message": "🎯 Discovering relevant problems...",
                "description": "AI is analyzing posts to find the most relevant problems for you",
                "animation": "filtering",
                "next_action": "Almost ready! Filtering posts by relevance",
                "stages": {
                    "keyword_generation": {"status": "completed", "message": "✅ Keywords generated", "icon": "🔑"},
                    "reddit_fetch": {"status": "completed", "message": f"✅ {reddit_posts_count} posts collected", "icon": "📡"},
                    "embedding_generation": {"status": "completed", "message": "✅ AI analysis complete", "icon": "🧠"},
                    "semantic_filtering": {"status": "in_progress", "message": "🎯 Finding relevant problems...", "icon": "⚡"},
                    "clustering": {"status": "pending", "message": "⏳ Waiting for filtering", "icon": "⏳"}
                },
                "estimated_time_remaining": "2-3 minutes",
                "can_view_results": False
            }
            
        elif reddit_posts_count > 0:
            # Reddit data exists, embeddings in progress
            return {
                "input_id": input_id,
                "overall_status": "generating_embeddings",
                "progress_percentage": 60,
                "current_stage": "embedding_generation",
                "message": "🧠 AI is analyzing the content...",
                "description": f"Processing {reddit_posts_count} posts with advanced AI to understand context and meaning",
                "animation": "thinking",
                "next_action": "Creating semantic understanding of posts",
                "stages": {
                    "keyword_generation": {"status": "completed", "message": "✅ Keywords generated", "icon": "🔑"},
                    "reddit_fetch": {"status": "completed", "message": f"✅ {reddit_posts_count} posts collected", "icon": "📡"},
                    "embedding_generation": {"status": "in_progress", "message": "🧠 AI analyzing content...", "icon": "⚡"},
                    "semantic_filtering": {"status": "pending", "message": "⏳ Waiting for analysis", "icon": "⏳"},
                    "clustering": {"status": "pending", "message": "⏳ Waiting for filtering", "icon": "⏳"}
                },
                "estimated_time_remaining": "8-12 minutes",
                "can_view_results": False
            }
            
        else:
            # Still fetching or failed
            return {
                "input_id": input_id,
                "overall_status": "fetching_posts",
                "progress_percentage": 25,
                "current_stage": "reddit_fetch",
                "message": "📡 Gathering posts from Reddit...",
                "description": "Searching through relevant communities to find discussions about your topic",
                "animation": "searching",
                "next_action": "Collecting posts from multiple subreddits",
                "stages": {
                    "keyword_generation": {"status": "completed", "message": "✅ Keywords generated", "icon": "🔑"},
                    "reddit_fetch": {"status": "in_progress", "message": "📡 Collecting posts...", "icon": "⚡"},
                    "embedding_generation": {"status": "pending", "message": "⏳ Waiting for posts", "icon": "⏳"},
                    "semantic_filtering": {"status": "pending", "message": "⏳ Waiting for analysis", "icon": "⏳"},
                    "clustering": {"status": "pending", "message": "⏳ Waiting for filtering", "icon": "⏳"}
                },
                "estimated_time_remaining": "15-20 minutes",
                "can_view_results": False
            }
        
    except Exception as e:
        logger.error(f"Error checking processing status for input {input_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to check processing status: {str(e)}"
        )

@router.get("/")
async def get_all_processing_status(
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Get processing status for all inputs for the authenticated user.
    """
    try:
        logger.info(f"Getting all processing status for user {current_user.id}")
        
        # Get all user directories
        reddit_dir = Path("data/reddit_posts") / current_user.id
        embeddings_dir = Path("data/embeddings") / current_user.id
        filtered_dir = Path("data/filtered_posts") / current_user.id
        
        all_inputs = set()
        
        # Collect all input IDs from different directories
        if reddit_dir.exists():
            for file in reddit_dir.glob("reddit_posts_*_*.json"):
                # Extract input_id from filename
                parts = file.stem.split('_')
                if len(parts) >= 4:
                    input_id = parts[2]
                    all_inputs.add(input_id)
        
        if embeddings_dir.exists():
            for dir_path in embeddings_dir.iterdir():
                if dir_path.is_dir():
                    all_inputs.add(dir_path.name)
        
        if filtered_dir.exists():
            for dir_path in filtered_dir.iterdir():
                if dir_path.is_dir():
                    all_inputs.add(dir_path.name)
        
        # Get status for each input
        status_list = []
        for input_id in all_inputs:
            try:
                # Reuse the single input status logic
                status_info = {
                    "input_id": input_id,
                    "reddit_fetch": "unknown",
                    "embeddings": "unknown", 
                    "semantic_filtering": "unknown",
                    "overall_status": "processing"
                }
                
                # Check each stage
                reddit_files = list(reddit_dir.glob(f"reddit_posts_{input_id}_*.json")) if reddit_dir.exists() else []
                if reddit_files:
                    status_info["reddit_fetch"] = "completed"
                
                embeddings_path = embeddings_dir / input_id
                if embeddings_path.exists() and (embeddings_path / "faiss_index.bin").exists():
                    status_info["embeddings"] = "completed"
                
                filtered_path = filtered_dir / input_id
                if filtered_path.exists() and (filtered_path / "filtered_posts.json").exists():
                    status_info["semantic_filtering"] = "completed"
                    status_info["overall_status"] = "completed"
                
                # Determine overall status
                if status_info["reddit_fetch"] == "completed" and status_info["embeddings"] == "unknown":
                    status_info["overall_status"] = "generating_embeddings"
                elif status_info["embeddings"] == "completed" and status_info["semantic_filtering"] == "unknown":
                    status_info["overall_status"] = "filtering_posts"
                
                status_list.append(status_info)
                
            except Exception as e:
                logger.warning(f"Error getting status for input {input_id}: {str(e)}")
                continue
        
        return {
            "processing_status": status_list,
            "total_inputs": len(status_list)
        }
        
    except Exception as e:
        logger.error(f"Error getting all processing status for user {current_user.id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get processing status: {str(e)}"
        )