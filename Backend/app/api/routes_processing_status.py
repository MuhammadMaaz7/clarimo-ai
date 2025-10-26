"""
Processing Status API Routes - Track background processing status
"""
from fastapi import APIRouter, HTTPException, status, Depends
from typing import Dict, Any
import logging
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
    Get the processing status for a specific input.
    
    Returns the status of Reddit fetching, embedding generation, and semantic filtering.
    """
    try:
        logger.info(f"Checking processing status for input {input_id} (user: {current_user.id})")
        
        status_info = {
            "input_id": input_id,
            "reddit_fetch": "unknown",
            "embeddings": "unknown", 
            "semantic_filtering": "unknown",
            "overall_status": "processing"
        }
        
        # Check Reddit data
        reddit_dir = Path("data/reddit_posts") / current_user.id
        reddit_files = list(reddit_dir.glob(f"reddit_posts_{input_id}_*.json"))
        if reddit_files:
            status_info["reddit_fetch"] = "completed"
        
        # Check embeddings
        embeddings_dir = Path("data/embeddings") / current_user.id / input_id
        if (embeddings_dir / "faiss_index.bin").exists():
            status_info["embeddings"] = "completed"
        
        # Check semantic filtering
        filtered_dir = Path("data/filtered_posts") / current_user.id / input_id
        if (filtered_dir / "filtered_posts.json").exists():
            status_info["semantic_filtering"] = "completed"
            status_info["overall_status"] = "completed"
        
        # Determine overall status
        if status_info["reddit_fetch"] == "completed" and status_info["embeddings"] == "unknown":
            status_info["overall_status"] = "generating_embeddings"
        elif status_info["embeddings"] == "completed" and status_info["semantic_filtering"] == "unknown":
            status_info["overall_status"] = "filtering_posts"
        
        return status_info
        
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