"""
Clustering API Routes - Cluster semantically filtered posts into problem themes
"""
from fastapi import APIRouter, HTTPException, status, Depends, BackgroundTasks
from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional
import logging

from app.db.models.user_model import UserResponse
from app.core.security import get_current_user
from app.services.module1_pain_points.clustering_service import clustering_service
from app.services.shared.processing_lock_service import processing_lock_service, ProcessingStage
from app.services.module1_pain_points.user_input_service import UserInputService

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/clustering", tags=["Clustering"])

class ClusteringRequest(BaseModel):
    """Request model for clustering posts"""
    input_id: str = Field(..., description="Input ID to cluster posts for")
    min_cluster_size: Optional[int] = Field(None, description="Minimum cluster size (optional)")
    create_visualization: bool = Field(True, description="Whether to create cluster visualization")

class ClusteringResponse(BaseModel):
    """Response model for clustering results"""
    success: bool
    message: str
    total_posts: int
    clusters_found: int
    clustered_posts: Optional[int] = None
    noise_posts: Optional[int] = None
    clusters: Optional[Dict[str, Any]] = None
    statistics: Optional[Dict[str, Any]] = None
    output_files: Optional[Dict[str, str]] = None
    clusters_directory: Optional[str] = None

@router.post("/cluster", response_model=ClusteringResponse)
async def cluster_posts(
    request: ClusteringRequest,
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Cluster semantically filtered posts into problem themes
    
    This endpoint takes filtered posts and groups them into thematic clusters
    representing different problem areas or pain points.
    """
    try:
        logger.info(f"Clustering request for input {request.input_id} (user: {current_user.id})")
        
        # Check if process is already running
        if await processing_lock_service.is_processing(current_user.id, request.input_id):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Processing already in progress for this input"
            )
        
        # Acquire processing lock
        lock_acquired = await processing_lock_service.acquire_lock(current_user.id, request.input_id)
        if not lock_acquired:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Processing already in progress for this input"
            )
        
        # Update processing stage
        await processing_lock_service.update_stage(current_user.id, request.input_id, ProcessingStage.CLUSTERING)
        await UserInputService.update_processing_stage(current_user.id, request.input_id, ProcessingStage.CLUSTERING.value)
        
        result = await clustering_service.cluster_filtered_posts(
            user_id=current_user.id,
            input_id=request.input_id,
            min_cluster_size=request.min_cluster_size,
            create_visualization=request.create_visualization
        )
        
        if result["success"]:
            logger.info(f"Clustering completed: {result['clusters_found']} clusters from {result['total_posts']} posts")
            
            # ✅ FIXED: For manual clustering, release lock and set completion status
            # Note: Manual clustering doesn't trigger pain points extraction automatically
            try:
                await UserInputService.update_input_status(
                    user_id=current_user.id,
                    input_id=request.input_id,
                    status="completed",
                    current_stage=ProcessingStage.COMPLETED.value
                )
                await processing_lock_service.release_lock(current_user.id, request.input_id, completed=True)
                logger.info(f"Released processing lock after manual clustering for {request.input_id}")
            except Exception as lock_error:
                logger.error(f"Error releasing lock after manual clustering: {str(lock_error)}")
        else:
            logger.warning(f"Clustering failed: {result['message']}")
            # Release lock on failure
            await processing_lock_service.release_lock(current_user.id, request.input_id, completed=False)
        
        return ClusteringResponse(**result)
        
    except HTTPException:
        # Release lock on HTTP exceptions
        await processing_lock_service.release_lock(current_user.id, request.input_id, completed=False)
        raise
    except Exception as e:
        logger.error(f"Error in clustering endpoint: {str(e)}")
        # Release lock on other exceptions
        await processing_lock_service.release_lock(current_user.id, request.input_id, completed=False)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Clustering failed: {str(e)}"
        )

@router.get("/results/{input_id}")
async def get_cluster_results(
    input_id: str,
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Get clustering results for a specific input
    
    Returns the cluster summary, statistics, and file paths for a completed clustering job.
    """
    try:
        from pathlib import Path
        import json
        
        logger.info(f"Getting cluster results for input {input_id} (user: {current_user.id})")
        
        # Find clusters directory
        clusters_dir = Path("data/clusters") / current_user.id / input_id
        summary_path = clusters_dir / "cluster_summary.json"
        config_path = clusters_dir / "clustering_config.json"
        
        if not summary_path.exists():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Cluster results not found for input {input_id}"
            )
        
        # Load cluster summary
        with open(summary_path, 'r', encoding='utf-8') as f:
            summary_data = json.load(f)
        
        # Load clustering config if available
        clustering_config = {}
        if config_path.exists():
            with open(config_path, 'r', encoding='utf-8') as f:
                clustering_config = json.load(f)
        
        return {
            "success": True,
            "input_id": input_id,
            "clusters": summary_data.get("clusters", {}),
            "statistics": summary_data.get("statistics", {}),
            "clustering_metadata": summary_data.get("clustering_metadata", {}),
            "config": clustering_config,
            "files": {
                "summary": str(summary_path),
                "posts": str(clusters_dir / "cluster_posts.json"),
                "config": str(config_path),
                "visualization": str(clusters_dir / "cluster_visualization.png")
            },
            "directory": str(clusters_dir)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting cluster results: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get cluster results: {str(e)}"
        )

@router.get("/list")
async def list_cluster_results(
    current_user: UserResponse = Depends(get_current_user)
):
    """
    List all clustering results for the authenticated user
    
    Returns a list of all completed clustering jobs with metadata.
    """
    try:
        logger.info(f"Listing cluster results for user {current_user.id}")
        
        results = await clustering_service.list_cluster_results(current_user.id)
        
        return {
            "success": True,
            "cluster_results": results,
            "total_results": len(results)
        }
        
    except Exception as e:
        logger.error(f"Error listing cluster results: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list cluster results: {str(e)}"
        )

@router.delete("/results/{input_id}")
async def delete_cluster_results(
    input_id: str,
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Delete clustering results for a specific input
    
    Removes all clustering files and directories for the specified input.
    """
    try:
        import shutil
        from pathlib import Path
        
        logger.info(f"Deleting cluster results for input {input_id} (user: {current_user.id})")
        
        # Find clusters directory
        clusters_dir = Path("data/clusters") / current_user.id / input_id
        
        if not clusters_dir.exists():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Cluster results not found for input {input_id}"
            )
        
        # Remove the entire directory
        shutil.rmtree(clusters_dir)
        
        logger.info(f"Successfully deleted cluster results for input {input_id}")
        
        return {
            "success": True,
            "message": f"Cluster results for input {input_id} have been deleted",
            "deleted_directory": str(clusters_dir)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting cluster results: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete cluster results: {str(e)}"
        )

# Background task function for automatic clustering
async def auto_cluster_posts(user_id: str, input_id: str):
    """
    Background task to automatically cluster posts after filtering is complete
    """
    try:
        logger.info(f"Starting automatic clustering for input {input_id} (user: {user_id})")
        
        result = await clustering_service.cluster_filtered_posts(
            user_id=user_id,
            input_id=input_id,
            create_visualization=True
        )
        
        if result["success"]:
            logger.info(f"Automatic clustering completed: {result['clusters_found']} clusters")
        else:
            logger.warning(f"Automatic clustering failed: {result['message']}")
            
    except Exception as e:
        logger.error(f"Error in automatic clustering: {str(e)}")

@router.post("/auto-cluster/{input_id}")
async def trigger_auto_clustering(
    input_id: str,
    background_tasks: BackgroundTasks,
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Trigger automatic clustering as a background task
    
    This endpoint starts clustering in the background and returns immediately.
    Use the status endpoints to check when clustering is complete.
    """
    try:
        logger.info(f"Triggering auto-clustering for input {input_id} (user: {current_user.id})")
        
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
        await processing_lock_service.update_stage(current_user.id, input_id, ProcessingStage.CLUSTERING)
        await UserInputService.update_processing_stage(current_user.id, input_id, ProcessingStage.CLUSTERING.value)
        
        # Add clustering task to background tasks
        background_tasks.add_task(auto_cluster_posts, current_user.id, input_id)
        
        return {
            "success": True,
            "message": f"Automatic clustering started for input {input_id}",
            "input_id": input_id,
            "status": "clustering_started"
        }
        
    except HTTPException:
        # Release lock on HTTP exceptions
        await processing_lock_service.release_lock(current_user.id, input_id, completed=False)
        raise
    except Exception as e:
        logger.error(f"Error triggering auto-clustering: {str(e)}")
        # Release lock on other exceptions
        await processing_lock_service.release_lock(current_user.id, input_id, completed=False)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start automatic clustering: {str(e)}"
        )