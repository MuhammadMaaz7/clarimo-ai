"""
API routes for Customer Insights Audience Segments
"""
from fastapi import APIRouter, Depends, HTTPException, status
from app.core.dependencies import get_current_user
from app.core.logging import logger
from app.db.database import customer_insights_analyses_collection, audience_segments_collection

router = APIRouter(prefix="/customer-insights/segments", tags=["Customer Insights - Segments"])


@router.get("/{analysis_id}", response_model=dict)
async def get_segments(
    analysis_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Get all audience segments for an analysis
    
    Returns all identified audience segments with pain points and interests.
    
    - **analysis_id**: Unique analysis ID
    """
    try:
        user_id = current_user.id
        
        # Get analysis
        analysis = await customer_insights_analyses_collection.find_one({
            "analysis_id": analysis_id,
            "user_id": user_id
        })
        
        if not analysis:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Analysis not found"
            )
        
        segments = analysis.get("segments", [])
        
        return {
            "analysis_id": analysis_id,
            "segments": segments,
            "total_segments": len(segments)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get segments: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get segments: {str(e)}"
        )


@router.get("/segment/{segment_id}", response_model=dict)
async def get_segment_details(
    segment_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Get detailed information for a specific segment
    
    Returns detailed segment information including all discussions in the segment.
    
    - **segment_id**: Unique segment ID
    """
    try:
        user_id = current_user.id
        
        # Get segment from database
        segment = await audience_segments_collection.find_one({
            "segment_id": segment_id
        })
        
        if not segment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Segment not found"
            )
        
        # Verify ownership through analysis
        analysis = await customer_insights_analyses_collection.find_one({
            "analysis_id": segment["analysis_id"],
            "user_id": user_id
        })
        
        if not analysis:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
        
        return {
            "segment_id": segment["segment_id"],
            "segment_name": segment["segment_name"],
            "summary": segment["summary"],
            "pain_points": segment["pain_points"],
            "interests": segment["interests"],
            "discussion_count": segment["discussion_count"],
            "cluster_id": segment.get("cluster_id"),
            "created_at": segment["created_at"]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get segment details: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get segment details: {str(e)}"
        )
