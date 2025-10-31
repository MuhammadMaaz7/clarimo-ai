"""
Reddit Data API Routes
"""
from fastapi import APIRouter, HTTPException, status, Depends, Query, BackgroundTasks
from typing import List, Optional, Any, Dict
import logging
import json
import os
from pathlib import Path

from app.db.models.user_model import UserResponse
from app.core.security import get_current_user
from app.services.reddit_fetching_service import reddit_fetching_service
from app.services.processing_lock_service import processing_lock_service, ProcessingStage
from app.services.user_input_service import UserInputService

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/reddit", tags=["Reddit Data"])


@router.post("/fetch/{input_id}")
async def fetch_reddit_posts_for_input(
    input_id: str,
    background_tasks: BackgroundTasks,
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
        
        # Check if processing is already in progress
        is_processing = await processing_lock_service.is_processing(current_user.id, input_id)
        if is_processing:
            current_stage = await processing_lock_service.get_current_stage(current_user.id, input_id)
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Processing already in progress. Current stage: {current_stage.value if current_stage else 'unknown'}"
            )
        
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
        
        # Start background processing for Reddit fetching
        background_tasks.add_task(
            fetch_reddit_posts_background,
            current_user.id,
            input_id,
            keywords,
            queries_per_domain,
            per_query_limit,
            per_subreddit_limit
        )
        
        logger.info(f"Started background Reddit fetching for input {input_id}")
        return {
            "success": True,
            "message": "Reddit fetching started in background",
            "input_id": input_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in manual Reddit fetch for input {input_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch Reddit posts: {str(e)}"
        )


async def fetch_reddit_posts_background(
    user_id: str,
    input_id: str,
    keywords: Dict[str, Any],
    queries_per_domain: int,
    per_query_limit: int,
    per_subreddit_limit: int
):
    """
    Background task for Reddit fetching
    """
    try:
        # Acquire processing lock
        lock_acquired = await processing_lock_service.acquire_lock(user_id, input_id)
        if not lock_acquired:
            logger.warning(f"Processing already in progress for {user_id}:{input_id}")
            return
        
        try:
            # Update user input status to processing
            await UserInputService.update_input_status(
                user_id=user_id,
                input_id=input_id,
                status="processing",
                current_stage=ProcessingStage.POSTS_FETCHING.value
            )
            
            # Prepare keywords data
            keywords_data = {
                "potential_subreddits": keywords.get("potential_subreddits", []),
                "domain_anchors": keywords.get("domain_anchors", []),
                "problem_phrases": keywords.get("problem_phrases", [])
            }
            
            # Fetch Reddit posts
            reddit_data = await reddit_fetching_service.fetch_reddit_posts_for_keywords(
                user_id=user_id,
                input_id=input_id,
                keywords_data=keywords_data,
                queries_per_domain=queries_per_domain,
                per_query_limit=per_query_limit,
                per_subreddit_limit=per_subreddit_limit
            )
            
            # Save results to file only (no database)
            if reddit_data["status"] == "completed":
                try:
                    file_path = await reddit_fetching_service.save_reddit_data_to_file(
                        reddit_data=reddit_data,
                        user_id=user_id,
                        input_id=input_id
                    )
                    logger.info(f"Reddit fetch completed: {reddit_data['total_posts']} posts, saved to: {file_path}")
                except Exception as file_error:
                    logger.error(f"Failed to save Reddit data to file: {str(file_error)}")
            
        except Exception as processing_error:
            logger.error(f"Error in background Reddit fetching for {input_id}: {str(processing_error)}")
            # Update status to failed
            await UserInputService.update_input_status(
                user_id=user_id,
                input_id=input_id,
                status="failed",
                current_stage=ProcessingStage.FAILED.value,
                error_message=f"Reddit fetching failed: {str(processing_error)}"
            )
            
        finally:
            # Always release the lock
            await processing_lock_service.release_lock(user_id, input_id)
            
    except Exception as e:
        logger.error(f"Background Reddit fetching failed for {user_id}:{input_id}: {str(e)}")


@router.get("/data/{input_id}")
async def get_reddit_data_for_input(
    input_id: str,
    current_user: UserResponse = Depends(get_current_user),
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
        
        # Get the latest file
        target_file = max(files, key=lambda f: f.stat().st_ctime)
        
        # Load data
        with open(target_file, 'r', encoding='utf-8') as f:
            data_content = json.load(f)
        
        if not include_posts:
            # Return summary without full post content
            summary = {
                "input_id": data_content.get("input_id"),
                "fetch_id": data_content.get("fetch_id"),
                "generated_at": data_content.get("generated_at"),
                "total_posts": data_content.get("total_posts", 0),
                "status": data_content.get("status"),
                "file_path": str(target_file),
                "query_summary": [],
                "subreddit_summary": []
            }
            
            # Add query summaries
            for query_data in data_content.get("by_query", []):
                summary["query_summary"].append({
                    "query": query_data.get("query", ""),
                    "domain_anchors_used": query_data.get("domain_anchors_used", []),
                    "problem_phrases_used": query_data.get("problem_phrases_used", []),
                    "n_posts": query_data.get("n_posts", 0)
                })
            
            # Add subreddit summaries
            for sub_data in data_content.get("by_subreddit", []):
                summary["subreddit_summary"].append({
                    "subreddit": sub_data.get("subreddit", ""),
                    "extracted_count": sub_data.get("extracted_count", 0),
                    "meta": sub_data.get("meta", {})
                })
            
            return summary
        else:
            # Return full data
            logger.info(f"Returning full Reddit data for input {input_id} ({data_content.get('total_posts', 0)} posts)")
            return data_content
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting Reddit data for input {input_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get Reddit data: {str(e)}"
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


@router.delete("/data/{input_id}")
async def delete_reddit_data(
    input_id: str,
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Delete Reddit data files for a specific input.
    """
    try:
        logger.info(f"Deleting Reddit data for input {input_id} (user: {current_user.id})")
        
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
        
        deleted_count = 0
        for file_path in files:
            try:
                file_path.unlink()
                deleted_count += 1
            except Exception as e:
                logger.warning(f"Error deleting file {file_path}: {e}")
        
        logger.info(f"Successfully deleted {deleted_count} Reddit data files for input {input_id}")
        return {
            "success": True,
            "message": f"Deleted {deleted_count} Reddit data files",
            "input_id": input_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting Reddit data for input {input_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete Reddit data: {str(e)}"
        )


@router.get("/processing-status/{input_id}")
async def get_reddit_fetching_status(
    input_id: str,
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Get the current status of Reddit fetching for a specific input.
    """
    try:
        # Check processing lock status
        is_processing = await processing_lock_service.is_processing(current_user.id, input_id)
        current_stage = await processing_lock_service.get_current_stage(current_user.id, input_id)
        
        # Check if there are any files
        user_dir = Path("data/reddit_posts") / current_user.id
        has_files = False
        latest_file_info = None
        
        if user_dir.exists():
            pattern = f"reddit_posts_{input_id}_*.json"
            files = list(user_dir.glob(pattern))
            has_files = len(files) > 0
            
            if has_files:
                # Get the latest file info
                latest_file = max(files, key=lambda f: f.stat().st_ctime)
                try:
                    with open(latest_file, 'r', encoding='utf-8') as f:
                        file_data = json.load(f)
                        latest_file_info = {
                            "total_posts": file_data.get("total_posts", 0),
                            "status": file_data.get("status", "unknown"),
                            "generated_at": file_data.get("generated_at", "")
                        }
                except Exception as e:
                    logger.warning(f"Error reading latest file: {e}")
        
        return {
            "input_id": input_id,
            "is_processing": is_processing,
            "current_stage": current_stage.value if current_stage else None,
            "has_file_data": has_files,
            "latest_file": latest_file_info
        }
        
    except Exception as e:
        logger.error(f"Error getting Reddit fetching status for {input_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get Reddit fetching status: {str(e)}"
        )