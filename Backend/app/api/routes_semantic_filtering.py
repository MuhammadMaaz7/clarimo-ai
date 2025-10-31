"""
Semantic Filtering API Routes
"""
from fastapi import APIRouter, HTTPException, status, Depends, Query, BackgroundTasks
from pydantic import BaseModel
from typing import List, Optional
import logging
from pathlib import Path

from app.db.models.user_model import UserResponse
from app.core.security import get_current_user
from app.services.semantic_filtering_service import semantic_filtering_service
from app.services.processing_lock_service import processing_lock_service, ProcessingStage
from app.services.user_input_service import UserInputService

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/semantic-filtering", tags=["Semantic Filtering"])

class SemanticFilterRequest(BaseModel):
    query: str
    domain: Optional[str] = None
    top_k: Optional[int] = 500
    similarity_threshold: Optional[float] = 0.55

@router.post("/filter/{input_id}")
async def filter_posts_semantically(
    input_id: str,
    request: SemanticFilterRequest,
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Manually trigger semantic filtering for a specific input.
    
    This endpoint allows manual semantic filtering if automatic filtering failed
    or if you want to filter with different parameters.
    """
    try:
        logger.info(f"Manual semantic filtering requested for input {input_id} by user {current_user.id}")
        
        # Check if process is already running
        if await processing_lock_service.is_processing(current_user.id, input_id):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Processing already in progress for this input"
            )
        
        # Acquire processing lock
        lock_acquired = await processing_lock_service.acquire_lock(current_user.id, input_id)
        if not lock_acquired:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Processing already in progress for this input"
            )
        
        # Update processing stage
        await processing_lock_service.update_stage(current_user.id, input_id, ProcessingStage.SEMANTIC_FILTERING)
        await UserInputService.update_processing_stage(current_user.id, input_id, ProcessingStage.SEMANTIC_FILTERING.value)
        
        # Check if embeddings exist for this input
        embeddings_dir = Path("data/embeddings") / current_user.id / input_id
        if not embeddings_dir.exists():
            # Release lock if no embeddings found
            await processing_lock_service.release_lock(current_user.id, input_id, completed=False)
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No embeddings found for this input. Generate embeddings first."
            )
        
        # Run semantic filtering
        result = await semantic_filtering_service.semantic_filter_posts(
            user_id=current_user.id,
            input_id=input_id,
            query=request.query,
            domain=request.domain,
            top_k=request.top_k,
            similarity_threshold=request.similarity_threshold
        )
        
        if result["success"]:
            logger.info(f"Manual semantic filtering completed for input {input_id}")
            # Don't release lock here - let the pipeline continue to clustering
            return {
                "success": True,
                "message": result["message"],
                "total_documents": result["total_documents"],
                "filtered_documents": result["filtered_documents"],
                "similarity_threshold": result["similarity_threshold"],
                "similarity_stats": result["similarity_stats"],
                "output_files": result["output_files"],
                "query_used": result["query_used"],
                "clustering_triggered": result.get("clustering_triggered", False)
            }
        else:
            logger.error(f"Manual semantic filtering failed for input {input_id}: {result.get('message')}")
            # Release lock on failure
            await processing_lock_service.release_lock(current_user.id, input_id, completed=False)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Semantic filtering failed: {result.get('message')}"
            )
        
    except HTTPException:
        # Release lock on HTTP exceptions
        await processing_lock_service.release_lock(current_user.id, input_id, completed=False)
        raise
    except Exception as e:
        logger.error(f"Error in manual semantic filtering for input {input_id}: {str(e)}")
        # Release lock on other exceptions
        await processing_lock_service.release_lock(current_user.id, input_id, completed=False)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to filter posts: {str(e)}"
        )


@router.get("/")
async def get_user_filtered_results(
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Get list of filtered results for the authenticated user.
    """
    try:
        logger.info(f"Getting filtered results for user {current_user.id}")
        
        filtered_results = await semantic_filtering_service.list_filtered_results(current_user.id)
        
        logger.info(f"Retrieved {len(filtered_results)} filtered result records for user {current_user.id}")
        return {
            "filtered_results": filtered_results,
            "total_results": len(filtered_results)
        }
        
    except Exception as e:
        logger.error(f"Error getting filtered results for user {current_user.id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get filtered results: {str(e)}"
        )


@router.get("/{input_id}")
async def get_filtered_posts_details(
    input_id: str,
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Get details of filtered posts for a specific input.
    """
    try:
        logger.info(f"Getting filtered posts details for input {input_id} (user: {current_user.id})")
        
        # Check if filtered results exist for this input
        filtered_posts_dir = Path("data/filtered_posts") / current_user.id / input_id
        filtered_posts_path = filtered_posts_dir / "filtered_posts.json"
        
        if not filtered_posts_path.exists():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No filtered results found for this input"
            )
        
        # Read filtered posts
        import json
        with open(filtered_posts_path, 'r', encoding='utf-8') as f:
            filtered_posts = json.load(f)
        
        # Calculate statistics
        similarity_scores = [p.get("similarity_score", 0) for p in filtered_posts]
        
        # List files in the filtered posts directory
        files = []
        for file_path in filtered_posts_dir.iterdir():
            if file_path.is_file():
                files.append({
                    "name": file_path.name,
                    "path": str(file_path),
                    "size_bytes": file_path.stat().st_size,
                    "created_at": file_path.stat().st_ctime
                })
        
        return {
            "input_id": input_id,
            "filtered_posts_count": len(filtered_posts),
            "similarity_stats": {
                "min_similarity": float(min(similarity_scores)) if similarity_scores else 0.0,
                "max_similarity": float(max(similarity_scores)) if similarity_scores else 0.0,
                "avg_similarity": float(sum(similarity_scores) / len(similarity_scores)) if similarity_scores else 0.0
            },
            "sample_posts": filtered_posts[:5],  # Return first 5 posts as sample
            "files": files,
            "total_files": len(files)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting filtered posts details for input {input_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get filtered posts details: {str(e)}"
        )


@router.delete("/{input_id}")
async def delete_filtered_results(
    input_id: str,
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Delete filtered results for a specific input.
    """
    try:
        logger.info(f"Deleting filtered results for input {input_id} (user: {current_user.id})")
        
        # Check if filtered results exist
        filtered_posts_dir = Path("data/filtered_posts") / current_user.id / input_id
        filtered_posts_path = filtered_posts_dir / "filtered_posts.json"
        filtered_csv_path = filtered_posts_dir / "filtered_metadata.csv"
        config_path = filtered_posts_dir / "filtering_config.json"
        
        if not filtered_posts_path.exists():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No filtered results found for this input"
            )
        
        # Delete filtered files
        files_deleted = []
        if filtered_posts_path.exists():
            filtered_posts_path.unlink()
            files_deleted.append("filtered_posts.json")
        
        if filtered_csv_path.exists():
            filtered_csv_path.unlink()
            files_deleted.append("filtered_metadata.csv")
        
        if config_path.exists():
            config_path.unlink()
            files_deleted.append("filtering_config.json")
        
        # Remove directory if empty
        try:
            if filtered_posts_dir.exists() and not any(filtered_posts_dir.iterdir()):
                filtered_posts_dir.rmdir()
        except:
            pass  # Directory not empty or other issue
        
        logger.info(f"Successfully deleted filtered results for input {input_id}")
        return {
            "success": True,
            "message": f"Filtered results deleted for input {input_id}",
            "files_deleted": files_deleted
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting filtered results for input {input_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete filtered results: {str(e)}"
        )


# Background task function for automatic semantic filtering
async def auto_filter_posts(user_id: str, input_id: str, query: str, domain: str = None):
    """
    Background task to automatically filter posts after embeddings are generated
    """
    try:
        logger.info(f"Starting automatic semantic filtering for input {input_id} (user: {user_id})")
        
        result = await semantic_filtering_service.semantic_filter_posts(
            user_id=user_id,
            input_id=input_id,
            query=query,
            domain=domain,
            top_k=500,
            similarity_threshold=0.55
        )
        
        if result["success"]:
            logger.info(f"Automatic semantic filtering completed: {result['filtered_documents']} posts")
        else:
            logger.warning(f"Automatic semantic filtering failed: {result['message']}")
            
    except Exception as e:
        logger.error(f"Error in automatic semantic filtering: {str(e)}")

@router.post("/auto-filter/{input_id}")
@router.post("/auto-filter/{input_id}")
async def trigger_auto_semantic_filtering(
    input_id: str,
    query: str,
    background_tasks: BackgroundTasks,
    domain: Optional[str] = None,
    current_user: UserResponse = Depends(get_current_user)
):

    """
    Trigger automatic semantic filtering as a background task
    
    This endpoint starts semantic filtering in the background and returns immediately.
    Use the results endpoints to check when filtering is complete.
    """
    try:
        logger.info(f"Triggering auto semantic filtering for input {input_id} (user: {current_user.id})")
        
        # Check if process is already running
        if await processing_lock_service.is_processing(current_user.id, input_id):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Processing already in progress for this input"
            )
        
        # Acquire processing lock
        lock_acquired = await processing_lock_service.acquire_lock(current_user.id, input_id)
        if not lock_acquired:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Processing already in progress for this input"
            )
        
        # Update processing stage
        await processing_lock_service.update_stage(current_user.id, input_id, ProcessingStage.SEMANTIC_FILTERING)
        await UserInputService.update_processing_stage(current_user.id, input_id, ProcessingStage.SEMANTIC_FILTERING.value)
        
        # Add semantic filtering task to background tasks
        background_tasks.add_task(auto_filter_posts, current_user.id, input_id, query, domain)
        
        return {
            "success": True,
            "message": f"Automatic semantic filtering started for input {input_id}",
            "input_id": input_id,
            "query": query,
            "domain": domain,
            "status": "filtering_started"
        }
        
    except HTTPException:
        # Release lock on HTTP exceptions
        await processing_lock_service.release_lock(current_user.id, input_id, completed=False)
        raise
    except Exception as e:
        logger.error(f"Error triggering auto semantic filtering: {str(e)}")
        # Release lock on other exceptions
        await processing_lock_service.release_lock(current_user.id, input_id, completed=False)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start automatic semantic filtering: {str(e)}"
        )