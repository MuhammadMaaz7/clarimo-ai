"""
Reddit Data API Routes
"""
from fastapi import APIRouter, HTTPException, status, Depends, Query
from typing import List, Optional
import logging
import json
import os
from pathlib import Path

from app.db.models.user_model import UserResponse
from app.core.security import get_current_user
from app.services.reddit_fetching_service import reddit_fetching_service

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/reddit", tags=["Reddit Data"])


@router.post("/fetch/{input_id}")
async def fetch_reddit_posts_for_input(
    input_id: str,
    current_user: UserResponse = Depends(get_current_user),
    queries_per_domain: int = Query(10, ge=1, le=30, description="Number of search queries"),
    per_query_limit: int = Query(100, ge=10, le=500, description="Posts per query"),
    per_subreddit_limit: int = Query(100, ge=10, le=500, description="Posts per subreddit")
):
    """
    Manually trigger Reddit post fetching for a specific input.
    
    This endpoint allows manual fetching if automatic fetching failed or 
    if you want to fetch with different parameters.
    """
    try:
        logger.info(f"Manual Reddit fetch requested for input {input_id} by user {current_user.id}")
        
        # Get keywords for the input
        from app.services.keyword_generation_service import KeywordGenerationService
        keywords = await KeywordGenerationService.get_keywords_by_input_id(
            user_id=current_user.id,
            input_id=input_id
        )
        
        if not keywords:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Keywords not found for this input. Generate keywords first."
            )
        
        if keywords.get("generation_status") != "completed":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Keywords generation not completed yet."
            )
        
        # Prepare keywords data
        keywords_data = {
            "potential_subreddits": keywords.get("potential_subreddits", []),
            "domain_anchors": keywords.get("domain_anchors", []),
            "problem_phrases": keywords.get("problem_phrases", [])
        }
        
        # Fetch Reddit posts
        reddit_data = await reddit_fetching_service.fetch_reddit_posts_for_keywords(
            user_id=current_user.id,
            input_id=input_id,
            keywords_data=keywords_data,
            queries_per_domain=queries_per_domain,
            per_query_limit=per_query_limit,
            per_subreddit_limit=per_subreddit_limit
        )
        
        # Save to file
        file_path = await reddit_fetching_service.save_reddit_data_to_file(
            reddit_data=reddit_data,
            user_id=current_user.id,
            input_id=input_id
        )
        
        logger.info(f"Manual Reddit fetch completed: {reddit_data['total_posts']} posts saved to {file_path}")
        
        return {
            "success": True,
            "message": f"Successfully fetched {reddit_data['total_posts']} Reddit posts",
            "fetch_id": reddit_data["fetch_id"],
            "total_posts": reddit_data["total_posts"],
            "by_query_count": len(reddit_data["by_query"]),
            "by_subreddit_count": len(reddit_data["by_subreddit"]),
            "file_path": file_path,
            "status": reddit_data["status"]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in manual Reddit fetch for input {input_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch Reddit posts: {str(e)}"
        )


@router.get("/files/{input_id}")
async def get_reddit_files_for_input(
    input_id: str,
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Get list of Reddit data files for a specific input.
    """
    try:
        logger.info(f"Getting Reddit files for input {input_id} (user: {current_user.id})")
        
        # Check user directory
        user_dir = Path("data/reddit_posts") / current_user.id
        if not user_dir.exists():
            return {"files": [], "total_files": 0}
        
        # Find files for this input
        pattern = f"reddit_posts_{input_id}_*.json"
        files = list(user_dir.glob(pattern))
        
        file_info = []
        for file_path in files:
            try:
                stat = file_path.stat()
                # Try to get basic info from file
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    total_posts = data.get("total_posts", 0)
                    status = data.get("status", "unknown")
                    generated_at = data.get("generated_at", "")
                
                file_info.append({
                    "filename": file_path.name,
                    "file_path": str(file_path),
                    "size_bytes": stat.st_size,
                    "created_at": stat.st_ctime,
                    "total_posts": total_posts,
                    "status": status,
                    "generated_at": generated_at
                })
            except Exception as e:
                logger.warning(f"Error reading file {file_path}: {e}")
                continue
        
        # Sort by creation time (newest first)
        file_info.sort(key=lambda x: x["created_at"], reverse=True)
        
        logger.info(f"Found {len(file_info)} Reddit data files for input {input_id}")
        return {"files": file_info, "total_files": len(file_info)}
        
    except Exception as e:
        logger.error(f"Error getting Reddit files for input {input_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get Reddit files: {str(e)}"
        )


@router.get("/data/{input_id}")
async def get_reddit_data_for_input(
    input_id: str,
    current_user: UserResponse = Depends(get_current_user),
    latest: bool = Query(True, description="Get latest file if multiple exist"),
    include_posts: bool = Query(False, description="Include full post data (can be large)")
):
    """
    Get Reddit data for a specific input.
    
    Returns summary by default, full data if include_posts=true.
    """
    try:
        logger.info(f"Getting Reddit data for input {input_id} (user: {current_user.id})")
        
        # Find files for this input
        user_dir = Path("data/reddit_posts") / current_user.id
        if not user_dir.exists():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No Reddit data found for this input"
            )
        
        pattern = f"reddit_posts_{input_id}_*.json"
        files = list(user_dir.glob(pattern))
        
        if not files:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No Reddit data files found for this input"
            )
        
        # Get the latest file or first one
        if latest:
            target_file = max(files, key=lambda f: f.stat().st_ctime)
        else:
            target_file = files[0]
        
        # Load data
        with open(target_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        if not include_posts:
            # Return summary without full post content
            summary = {
                "input_id": data.get("input_id"),
                "fetch_id": data.get("fetch_id"),
                "generated_at": data.get("generated_at"),
                "total_posts": data.get("total_posts", 0),
                "status": data.get("status"),
                "file_path": str(target_file),
                "query_summary": [],
                "subreddit_summary": []
            }
            
            # Add query summaries
            for query_data in data.get("by_query", []):
                summary["query_summary"].append({
                    "query": query_data.get("query", ""),
                    "domain_anchors_used": query_data.get("domain_anchors_used", []),
                    "problem_phrases_used": query_data.get("problem_phrases_used", []),
                    "n_posts": query_data.get("n_posts", 0)
                })
            
            # Add subreddit summaries
            for sub_data in data.get("by_subreddit", []):
                summary["subreddit_summary"].append({
                    "subreddit": sub_data.get("subreddit", ""),
                    "extracted_count": sub_data.get("extracted_count", 0),
                    "meta": sub_data.get("meta", {})
                })
            
            return summary
        else:
            # Return full data
            logger.info(f"Returning full Reddit data for input {input_id} ({data.get('total_posts', 0)} posts)")
            return data
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting Reddit data for input {input_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get Reddit data: {str(e)}"
        )


@router.get("/stats")
async def get_reddit_stats(
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Get Reddit fetching statistics for the user.
    """
    try:
        logger.info(f"Getting Reddit stats for user {current_user.id}")
        
        user_dir = Path("data/reddit_posts") / current_user.id
        if not user_dir.exists():
            return {
                "total_files": 0,
                "total_posts": 0,
                "total_inputs": 0,
                "recent_fetches": []
            }
        
        # Get all JSON files
        files = list(user_dir.glob("reddit_posts_*.json"))
        
        total_posts = 0
        inputs = set()
        recent_fetches = []
        
        for file_path in files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                posts_count = data.get("total_posts", 0)
                input_id = data.get("input_id", "")
                
                total_posts += posts_count
                if input_id:
                    inputs.add(input_id)
                
                recent_fetches.append({
                    "input_id": input_id,
                    "fetch_id": data.get("fetch_id", ""),
                    "generated_at": data.get("generated_at", ""),
                    "total_posts": posts_count,
                    "status": data.get("status", "unknown")
                })
                
            except Exception as e:
                logger.warning(f"Error reading stats from {file_path}: {e}")
                continue
        
        # Sort recent fetches by date (newest first)
        recent_fetches.sort(key=lambda x: x["generated_at"], reverse=True)
        
        stats = {
            "total_files": len(files),
            "total_posts": total_posts,
            "total_inputs": len(inputs),
            "recent_fetches": recent_fetches[:10]  # Last 10 fetches
        }
        
        logger.info(f"Reddit stats for user {current_user.id}: {stats['total_files']} files, {stats['total_posts']} posts")
        return stats
        
    except Exception as e:
        logger.error(f"Error getting Reddit stats for user {current_user.id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get Reddit stats: {str(e)}"
        )