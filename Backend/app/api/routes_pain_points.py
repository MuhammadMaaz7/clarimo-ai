"""
Pain Points API Routes

This module provides endpoints for extracting and managing pain points
from clustered Reddit data.
"""

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from pydantic import BaseModel, Field
from typing import Dict, List, Any, Optional

from app.core.logging import logger
from app.db.models.user_model import UserResponse
from app.core.security import get_current_user
from app.services.pain_points_service import pain_points_service
from app.services.processing_lock_service import processing_lock_service, ProcessingStage
from app.services.user_input_service import UserInputService

router = APIRouter(prefix="/pain-points", tags=["pain-points"])

# ---------- REQUEST/RESPONSE MODELS ----------

class PainPointsRequest(BaseModel):
    """Request model for pain points extraction"""
    input_id: str = Field(..., description="Input ID to extract pain points for")
    output_dir: Optional[str] = Field(None, description="Optional output directory")

class PainPointsResponse(BaseModel):
    """Response model for pain points extraction results"""
    success: bool
    message: str
    total_clusters: int
    processed: int
    failed: int
    individual_files: Optional[List[str]] = None
    aggregated_file: Optional[str] = None
    pain_points_count: Optional[int] = None

class PainPointData(BaseModel):
    """Individual pain point data structure"""
    cluster_id: str
    problem_title: str
    problem_description: str
    post_references: List[Dict[str, Any]]
    analysis_timestamp: float
    source: str
    error: Optional[bool] = None
    error_message: Optional[str] = None

class PainPointsResultsResponse(BaseModel):
    """Response model for pain points results"""
    success: bool
    metadata: Dict[str, Any]
    pain_points: List[PainPointData]
    total_pain_points: int
    domains: Optional[Dict[str, List[PainPointData]]] = None

# ---------- API ENDPOINTS ----------

@router.post("/extract", response_model=PainPointsResponse)
async def extract_pain_points(
    request: PainPointsRequest,
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Extract marketable pain points from clustered posts
    
    This endpoint analyzes existing cluster data and uses LLM analysis
    to extract structured pain points that could inspire startup ideas.
    """
    try:
        logger.info(f"Pain points extraction request for input {request.input_id} (user: {current_user.id})")
        
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
        await processing_lock_service.update_stage(current_user.id, request.input_id, ProcessingStage.PAIN_POINTS_EXTRACTION)
        await UserInputService.update_processing_stage(current_user.id, request.input_id, ProcessingStage.PAIN_POINTS_EXTRACTION.value)
        
        result = await pain_points_service.extract_pain_points_from_clusters(
            user_id=current_user.id,
            input_id=request.input_id,
            output_dir=request.output_dir
        )
        
        if result["success"]:
            pain_points_count = len(result["pain_points_data"]["pain_points"]) if result["pain_points_data"] else 0
            logger.info(f"Pain points extraction completed: {pain_points_count} pain points from {result['total_clusters']} clusters")
            
            # ✅ FIXED: For manual extraction, we need to release the lock and set completion status
            try:
                await UserInputService.update_input_status(
                    user_id=current_user.id,
                    input_id=request.input_id,
                    status="completed",
                    current_stage=ProcessingStage.COMPLETED.value
                )
                await processing_lock_service.release_lock(current_user.id, request.input_id, completed=True)
                logger.info(f"Released processing lock after manual pain points extraction for {request.input_id}")
            except Exception as lock_error:
                logger.error(f"Error releasing lock after manual extraction: {str(lock_error)}")
            
            return PainPointsResponse(
                success=True,
                message=f"Successfully extracted {pain_points_count} pain points from {result['total_clusters']} clusters",
                total_clusters=result["total_clusters"],
                processed=result["processed"],
                failed=result["failed"],
                individual_files=result["individual_files"],
                aggregated_file=result["aggregated_file"],
                pain_points_count=pain_points_count
            )
        else:
            logger.warning(f"Pain points extraction failed: {result.get('error', 'Unknown error')}")
            # Release lock on failure
            await processing_lock_service.release_lock(current_user.id, request.input_id, completed=False)
            
            return PainPointsResponse(
                success=False,
                message=f"Pain points extraction failed: {result.get('error', 'Unknown error')}",
                total_clusters=result.get("total_clusters", 0),
                processed=result.get("processed", 0),
                failed=result.get("failed", 0)
            )
        
    except HTTPException:
        # Release lock on HTTP exceptions
        await processing_lock_service.release_lock(current_user.id, request.input_id, completed=False)
        raise
    except Exception as e:
        logger.error(f"Error in pain points extraction endpoint: {str(e)}")
        # Release lock on other exceptions
        await processing_lock_service.release_lock(current_user.id, request.input_id, completed=False)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Pain points extraction failed: {str(e)}"
        )

@router.get("/results/{input_id}", response_model=PainPointsResultsResponse)
async def get_pain_points_results(
    input_id: str,
    include_domains: bool = False,
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Get pain points results for a specific input
    
    Returns structured pain points data with optional domain grouping.
    """
    try:
        logger.info(f"Getting pain points results for input {input_id} (user: {current_user.id})")
        
        results = await pain_points_service.get_pain_points_results(current_user.id, input_id)
        
        if not results:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No pain points results found for input {input_id}"
            )
        
        response_data = {
            "success": True,
            "metadata": results["metadata"],
            "pain_points": results["pain_points"],
            "total_pain_points": len(results["pain_points"])
        }
        
        # Add domain grouping if requested
        if include_domains:
            domains = pain_points_service.get_pain_points_by_domain(results)
            response_data["domains"] = domains
        
        return PainPointsResultsResponse(**response_data)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting pain points results: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get pain points results: {str(e)}"
        )

@router.get("/list")
async def list_pain_points_results(
    current_user: UserResponse = Depends(get_current_user)
):
    """
    List all pain points results for the authenticated user
    
    Returns a list of all completed pain points extractions with metadata.
    """
    try:
        logger.info(f"Listing pain points results for user {current_user.id}")
        
        results = await pain_points_service.list_pain_points_results(current_user.id)
        
        return {
            "success": True,
            "pain_points_results": results,
            "total_results": len(results)
        }
        
    except Exception as e:
        logger.error(f"Error listing pain points results: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list pain points results: {str(e)}"
        )

@router.get("/domains/{input_id}")
async def get_pain_points_by_domain(
    input_id: str,
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Get pain points grouped by domain for a specific input
    
    Returns pain points organized by business domain/industry.
    """
    try:
        logger.info(f"Getting pain points by domain for input {input_id} (user: {current_user.id})")
        
        results = await pain_points_service.get_pain_points_results(current_user.id, input_id)
        
        if not results:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No pain points results found for input {input_id}"
            )
        
        domains = pain_points_service.get_pain_points_by_domain(results)
        
        return {
            "success": True,
            "input_id": input_id,
            "domains": domains,
            "total_domains": len(domains),
            "total_pain_points": sum(len(pain_points) for pain_points in domains.values())
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting pain points by domain: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get pain points by domain: {str(e)}"
        )

@router.delete("/results/{input_id}")
async def delete_pain_points_results(
    input_id: str,
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Delete pain points results for a specific input
    
    Removes pain points files for the specified input.
    """
    try:
        from pathlib import Path
        import os
        
        logger.info(f"Deleting pain points results for input {input_id} (user: {current_user.id})")
        
        # Find pain points files in dedicated directory
        pain_points_dir = Path("data/pain_points") / current_user.id / input_id
        
        if not pain_points_dir.exists():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No pain points results found for input {input_id}"
            )
        
        # Delete pain points files
        deleted_files = []
        
        # Delete aggregated file
        aggregated_file = pain_points_dir / "marketable_pain_points_all.json"
        if aggregated_file.exists():
            os.remove(aggregated_file)
            deleted_files.append(str(aggregated_file))
        
        # Delete individual pain point files
        for file_path in pain_points_dir.glob("pain_point_cluster_*.json"):
            os.remove(file_path)
            deleted_files.append(str(file_path))
        
        # Remove the directory if it's empty
        try:
            pain_points_dir.rmdir()
        except OSError:
            pass  # Directory not empty, that's fine
        
        if not deleted_files:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No pain points results found for input {input_id}"
            )
        
        logger.info(f"Successfully deleted {len(deleted_files)} pain points files for input {input_id}")
        
        return {
            "success": True,
            "message": f"Pain points results for input {input_id} have been deleted",
            "deleted_files": deleted_files,
            "files_deleted": len(deleted_files)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting pain points results: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete pain points results: {str(e)}"
        )

# ---------- BACKGROUND TASKS ----------

async def auto_extract_pain_points(user_id: str, input_id: str):
    """
    Background task to automatically extract pain points after clustering is complete
    """
    try:
        logger.info(f"Starting automatic pain points extraction for input {input_id} (user: {user_id})")
        
        result = await pain_points_service.extract_pain_points_from_clusters(
            user_id=user_id,
            input_id=input_id
        )
        
        if result["success"]:
            pain_points_count = len(result["pain_points_data"]["pain_points"]) if result["pain_points_data"] else 0
            logger.info(f"Automatic pain points extraction completed: {pain_points_count} pain points")
            
            # ✅ FIXED: For background task, we need to release the lock and set completion status
            try:
                await UserInputService.update_input_status(
                    user_id=user_id,
                    input_id=input_id,
                    status="completed",
                    current_stage=ProcessingStage.COMPLETED.value
                )
                await processing_lock_service.release_lock(user_id, input_id, completed=True)
                logger.info(f"Released processing lock after automatic pain points extraction for {input_id}")
            except Exception as lock_error:
                logger.error(f"Error releasing lock after automatic extraction: {str(lock_error)}")
        else:
            logger.warning(f"Automatic pain points extraction failed: {result.get('error', 'Unknown error')}")
            # Release lock on failure
            try:
                await processing_lock_service.release_lock(user_id, input_id, completed=False)
            except Exception as lock_error:
                logger.error(f"Error releasing lock on failure: {str(lock_error)}")
            
    except Exception as e:
        logger.error(f"Error in automatic pain points extraction: {str(e)}")
        # Release lock on exception
        try:
            await processing_lock_service.release_lock(user_id, input_id, completed=False)
        except Exception as lock_error:
            logger.error(f"Error releasing lock on exception: {str(lock_error)}")

@router.post("/trigger-auto/{input_id}")
async def trigger_auto_pain_points_extraction(
    input_id: str,
    background_tasks: BackgroundTasks,
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Trigger automatic pain points extraction as a background task
    
    This endpoint starts pain points extraction in the background and returns immediately.
    Use the results endpoints to check when extraction is complete.
    """
    try:
        logger.info(f"Triggering auto pain points extraction for input {input_id} (user: {current_user.id})")
        
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
        await processing_lock_service.update_stage(current_user.id, input_id, ProcessingStage.PAIN_POINTS_EXTRACTION)
        await UserInputService.update_processing_stage(current_user.id, input_id, ProcessingStage.PAIN_POINTS_EXTRACTION.value)
        
        # Add pain points extraction task to background tasks
        background_tasks.add_task(auto_extract_pain_points, current_user.id, input_id)
        
        return {
            "success": True,
            "message": f"Automatic pain points extraction started for input {input_id}",
            "input_id": input_id,
            "status": "extraction_started"
        }
        
    except HTTPException:
        # Release lock on HTTP exceptions
        await processing_lock_service.release_lock(current_user.id, input_id, completed=False)
        raise
    except Exception as e:
        logger.error(f"Error triggering auto pain points extraction: {str(e)}")
        # Release lock on other exceptions
        await processing_lock_service.release_lock(current_user.id, input_id, completed=False)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start automatic pain points extraction: {str(e)}"
        )

# ---------- USER HISTORY ENDPOINTS ----------

@router.get("/history")
async def get_user_pain_points_history(
    limit: int = 50,
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Get user's pain points analysis history
    
    Returns a list of all pain points analyses performed by the user.
    """
    try:
        logger.info(f"Getting pain points history for user {current_user.id}")
        
        from app.services.pain_points_db_service import pain_points_db_service
        
        history = await pain_points_db_service.get_user_pain_points_history(
            user_id=current_user.id,
            limit=limit
        )
        
        return {
            "success": True,
            "history": [item.dict() for item in history],
            "total_items": len(history)
        }
        
    except Exception as e:
        logger.error(f"Error getting pain points history: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get pain points history: {str(e)}"
        )

@router.get("/stats")
async def get_user_pain_points_stats(
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Get user's pain points analysis statistics
    
    Returns summary statistics about the user's pain points analyses.
    """
    try:
        logger.info(f"Getting pain points stats for user {current_user.id}")
        
        from app.services.pain_points_db_service import pain_points_db_service
        
        stats = await pain_points_db_service.get_user_stats(current_user.id)
        
        return {
            "success": True,
            "stats": stats
        }
        
    except Exception as e:
        logger.error(f"Error getting pain points stats: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get pain points stats: {str(e)}"
        )

@router.get("/analysis/{input_id}")
async def get_pain_points_analysis_from_db(
    input_id: str,
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Get pain points analysis from database
    
    Returns the complete pain points analysis for a specific input.
    """
    try:
        logger.info(f"Getting pain points analysis from DB for input {input_id} (user: {current_user.id})")
        
        from app.services.pain_points_db_service import pain_points_db_service
        
        analysis = await pain_points_db_service.get_pain_points_analysis(
            user_id=current_user.id,
            input_id=input_id
        )
        
        if not analysis:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No pain points analysis found for input {input_id}"
            )
        
        return {
            "success": True,
            "analysis": analysis
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting pain points analysis from DB: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get pain points analysis: {str(e)}"
        )