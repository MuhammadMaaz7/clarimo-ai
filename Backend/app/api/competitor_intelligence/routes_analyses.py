"""
API routes for Competitor Analysis
"""

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from typing import List
from app.db.models.competitor_analysis_model import (
    CompetitiveAnalysisCreate,
    CompetitiveAnalysisResponse,
    AnalysisStatusResponse,
    AnalysisHistoryItem
)
from app.services.competitor_intelligence.analysis_lifecycle_manager import AnalysisLifecycleManager
from app.core.dependencies import get_current_user
from app.core.logging import logger

router = APIRouter(prefix="/analyses", tags=["Competitor Analyses"])


@router.post("/", response_model=CompetitiveAnalysisResponse, status_code=status.HTTP_202_ACCEPTED)
async def start_analysis(
    analysis_request: CompetitiveAnalysisCreate,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user)
):
    """
    Start a new competitor analysis for a product
    
    This endpoint initiates the analysis process and returns immediately.
    The analysis runs in the background, and you can check its status using the status endpoint.
    
    - **product_id**: ID of the product to analyze
    """
    try:
        user_id = current_user.id
        
        analysis = await AnalysisLifecycleManager.start_analysis(
            product_id=analysis_request.product_id,
            user_id=user_id,
            background_tasks=background_tasks
        )
        
        return analysis
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Failed to start analysis: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start analysis: {str(e)}"
        )


@router.get("/{analysis_id}", response_model=CompetitiveAnalysisResponse)
async def get_analysis_result(
    analysis_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Get analysis result by ID
    
    Returns the complete analysis result including all competitors,
    market insights, and recommendations.
    
    - **analysis_id**: Unique analysis ID
    """
    try:
        user_id = current_user.id
        
        analysis = AnalysisLifecycleManager.get_analysis_result(
            analysis_id=analysis_id,
            user_id=user_id
        )
        
        if not analysis:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Analysis not found"
            )
        
        return analysis
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get analysis result: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get analysis result: {str(e)}"
        )


@router.get("/status/{analysis_id}", response_model=AnalysisStatusResponse)
async def get_analysis_status(
    analysis_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Get analysis status for polling
    
    Returns a lightweight status check for an analysis. Use this endpoint
    to poll for completion status without fetching the full result.
    
    - **analysis_id**: Unique analysis ID
    """
    try:
        user_id = current_user.id
        
        status_info = AnalysisLifecycleManager.get_analysis_status(
            analysis_id=analysis_id,
            user_id=user_id
        )
        
        if not status_info:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Analysis not found"
            )
        
        return status_info
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get analysis status: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get analysis status: {str(e)}"
        )


@router.get("/product/{product_id}/history", response_model=List[AnalysisHistoryItem])
async def get_analysis_history(
    product_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Get analysis history for a product
    
    Returns all analysis results for a specific product, ordered by date (newest first).
    
    - **product_id**: ID of the product
    """
    try:
        user_id = current_user.id
        
        history = AnalysisLifecycleManager.get_analysis_history(
            product_id=product_id,
            user_id=user_id
        )
        
        return history
        
    except Exception as e:
        logger.error(f"Failed to get analysis history: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get analysis history: {str(e)}"
        )
