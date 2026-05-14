"""
API routes for Customer Insights Analysis
"""
from fastapi import APIRouter, Depends, HTTPException, status
from typing import Optional

# Import models
from app.db.models.customer_insights_model import (
    CustomerInsightsRequest,
    CustomerInsightsResponse,
    AnalysisStatusResponse,
    AnalysisHistoryItem
)

# Import services
from app.services.customer_insights.analysis_manager import analysis_manager
from app.services.shared.relevance_checker import relevance_checker

# Import dependencies
from app.core.dependencies import get_current_user
from app.core.logging import logger

router = APIRouter(prefix="/customer-insights", tags=["Customer Insights"])


@router.post("/analyze", response_model=dict, status_code=status.HTTP_202_ACCEPTED)
async def start_analysis(
    request: CustomerInsightsRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Start customer insights analysis
    
    This endpoint initiates the analysis process and returns immediately with an analysis ID.
    The analysis runs in the background, and you can check its status using the status endpoint.
    
    - **startup_idea**: Startup idea or problem to analyze (10-500 characters)
    - **target_market**: Optional target market description
    
    Returns:
        Dictionary with analysis_id and initial status
    """
    try:
        user_id = current_user.id
        
        logger.info(f"Starting customer insights analysis for user {user_id}")
        
        # STEP 1: Validate input relevance (same approach as GTM and Launch Planning)
        logger.info(f"Validating input: {request.startup_idea[:50]}...")
        
        # Combine startup_idea and target_market for validation
        validation_text = request.startup_idea
        if request.target_market:
            validation_text += f" | Target Market: {request.target_market}"
        
        is_valid, reason = await relevance_checker.validate_relevance(
            input_text=validation_text,
            context_type="customer insights analysis"
        )
        
        if not is_valid:
            logger.warning(f"Customer insights request rejected: {reason}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=reason
            )
        
        logger.info(f"Input validation passed: {reason}")
        
        # STEP 2: Start analysis
        result = await analysis_manager.start_analysis(
            user_id=user_id,
            startup_idea=request.startup_idea,
            target_market=request.target_market
        )
        
        if not result.get("success"):
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result.get("message", "Failed to start analysis")
            )
        
        return {
            "success": True,
            "analysis_id": result["analysis_id"],
            "message": "Analysis started successfully. Use the status endpoint to check progress.",
            "status": "processing"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to start analysis: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start analysis: {str(e)}"
        )


@router.get("/analysis/{analysis_id}", response_model=dict)
async def get_analysis(
    analysis_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Get complete analysis results
    
    Returns the complete analysis including communities, segments, and insights.
    If analysis is still in progress, returns current status.
    
    - **analysis_id**: Unique analysis ID
    """
    try:
        user_id = current_user.id
        
        # Get analysis results
        results = await analysis_manager.get_analysis_results(
            analysis_id=analysis_id,
            user_id=user_id
        )
        
        if not results:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Analysis not found"
            )
        
        return results
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get analysis: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get analysis: {str(e)}"
        )


@router.get("/status/{analysis_id}", response_model=dict)
async def get_analysis_status(
    analysis_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Get analysis status
    
    Returns a lightweight status check for an analysis. Use this endpoint
    to poll for completion status without fetching the full result.
    
    - **analysis_id**: Unique analysis ID
    
    Returns:
        Dictionary with status, current_stage, and progress_percentage
    """
    try:
        user_id = current_user.id
        
        # Get analysis results (lightweight)
        results = await analysis_manager.get_analysis_results(
            analysis_id=analysis_id,
            user_id=user_id
        )
        
        if not results:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Analysis not found"
            )
        
        return {
            "analysis_id": results["analysis_id"],
            "status": results["status"],
            "current_stage": results.get("current_stage"),
            "progress_percentage": results.get("progress_percentage", 0),
            "message": f"Analysis is {results['status']}",
            "created_at": results["created_at"],
            "estimated_completion": "1-2 minutes" if results["status"] == "processing" else None
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get analysis status: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get analysis status: {str(e)}"
        )


@router.get("/history", response_model=list)
async def get_analysis_history(
    current_user: dict = Depends(get_current_user)
):
    """
    Get analysis history for current user
    
    Returns all analyses for the current user, ordered by date (newest first).
    """
    try:
        user_id = current_user.id
        
        logger.info(f"Fetching analysis history for user {user_id}")
        
        # Get analysis history
        history = await analysis_manager.get_analysis_history(user_id=user_id)
        
        logger.info(f"Returning {len(history)} analyses for user {user_id}")
        
        return history
        
    except Exception as e:
        logger.error(f"Failed to get analysis history: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get analysis history: {str(e)}"
        )


@router.delete("/analysis/{analysis_id}", response_model=dict)
async def delete_analysis(
    analysis_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Delete an analysis
    
    Deletes an analysis and all associated data (discussions, segments, communities).
    
    - **analysis_id**: Unique analysis ID
    """
    try:
        user_id = current_user.id
        
        # Import database collections
        from app.db.database import (
            customer_insights_analyses_collection,
            customer_raw_discussions_collection,
            audience_segments_collection,
            community_insights_collection
        )
        
        # Verify ownership
        analysis = await customer_insights_analyses_collection.find_one({
            "analysis_id": analysis_id,
            "user_id": user_id
        })
        
        if not analysis:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Analysis not found"
            )
        
        # Delete all associated data
        await customer_raw_discussions_collection.delete_many({"analysis_id": analysis_id})
        await audience_segments_collection.delete_many({"analysis_id": analysis_id})
        await community_insights_collection.delete_many({"analysis_id": analysis_id})
        await customer_insights_analyses_collection.delete_one({"analysis_id": analysis_id})
        
        logger.info(f"Deleted analysis {analysis_id}")
        
        return {
            "success": True,
            "message": "Analysis deleted successfully",
            "analysis_id": analysis_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete analysis: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete analysis: {str(e)}"
        )


@router.post("/validate-input", response_model=dict)
async def validate_input(
    request: CustomerInsightsRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Validate user input without starting analysis
    
    Useful for frontend validation before submitting the full request.
    Checks if the startup idea and target market are valid and meaningful.
    Uses the same validation logic as GTM Strategy and Launch Planning modules.
    
    - **startup_idea**: Startup idea or problem to validate
    - **target_market**: Optional target market to validate
    
    Returns:
        Dictionary with validation result:
        {
            "success": true,
            "is_valid": true/false,
            "reason": "Explanation",
            "message": "Validation message"
        }
    """
    try:
        logger.info(f"Validating input for user {current_user.id}")
        
        # Combine startup_idea and target_market for validation
        validation_text = request.startup_idea
        if request.target_market:
            validation_text += f" | Target Market: {request.target_market}"
        
        # Use the same relevance checker as GTM and Launch Planning
        is_valid, reason = await relevance_checker.validate_relevance(
            input_text=validation_text,
            context_type="customer insights analysis"
        )
        
        return {
            "success": True,
            "is_valid": is_valid,
            "reason": reason,
            "message": "Input is valid and ready for analysis" if is_valid else "Input validation failed"
        }
        
    except Exception as e:
        logger.error(f"Failed to validate input: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to validate input: {str(e)}"
        )
