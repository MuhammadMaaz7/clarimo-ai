"""
API routes for Customer Insights Communities
"""
from fastapi import APIRouter, Depends, HTTPException, status
from app.core.dependencies import get_current_user
from app.core.logging import logger
from app.db.database import customer_insights_analyses_collection

router = APIRouter(prefix="/customer-insights/communities", tags=["Customer Insights - Communities"])


@router.get("/{analysis_id}", response_model=dict)
async def get_communities(
    analysis_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Get all communities for an analysis
    
    Returns all discovered communities with engagement scores and discussion counts.
    
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
        
        communities = analysis.get("communities", [])
        
        return {
            "analysis_id": analysis_id,
            "communities": communities,
            "total_communities": len(communities)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get communities: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get communities: {str(e)}"
        )


@router.get("/{analysis_id}/top", response_model=dict)
async def get_top_communities(
    analysis_id: str,
    limit: int = 10,
    current_user: dict = Depends(get_current_user)
):
    """
    Get top communities by engagement score
    
    Returns the top N communities sorted by engagement score.
    
    - **analysis_id**: Unique analysis ID
    - **limit**: Number of top communities to return (default: 10)
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
        
        communities = analysis.get("communities", [])
        
        # Sort by engagement score and limit
        top_communities = sorted(
            communities,
            key=lambda x: x.get("engagement_score", 0),
            reverse=True
        )[:limit]
        
        return {
            "analysis_id": analysis_id,
            "top_communities": top_communities,
            "total_communities": len(communities)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get top communities: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get top communities: {str(e)}"
        )
