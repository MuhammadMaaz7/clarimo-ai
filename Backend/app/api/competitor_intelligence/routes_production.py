"""
Production API Routes for Competitor Analysis
Clean, user-friendly endpoints for frontend integration
"""

from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from app.services.competitor_intelligence.competitor_analysis_pipeline import CompetitorAnalysisPipeline
from app.core.logging import logger
from app.core.dependencies import get_current_user

router = APIRouter(prefix="/competitor-analysis", tags=["Competitor Analysis"])


class ProductSubmission(BaseModel):
    """Product submission for analysis"""
    name: str = Field(..., description="Product name")
    description: str = Field(..., description="Product description")
    features: List[str] = Field(default=[], description="List of product features")
    pricing: Optional[str] = Field(None, description="Pricing information")
    target_audience: Optional[str] = Field(None, description="Target audience")


class CompetitorInfo(BaseModel):
    """Competitor information"""
    name: str
    description: str
    url: str
    features: List[str]
    pricing: Optional[str]
    target_audience: Optional[str]
    source: str


class FeatureMatrix(BaseModel):
    """Feature comparison matrix"""
    features: List[str]
    products: List[Dict[str, Any]]


class ComparisonData(BaseModel):
    """Comparison dashboard data"""
    pricing: Dict[str, Any]
    feature_count: Dict[str, Any]
    positioning: str


class GapAnalysis(BaseModel):
    """Gap analysis results"""
    opportunities: List[str]
    unique_strengths: List[str]
    areas_to_improve: List[str]
    market_gaps: List[str]


class AnalysisResponse(BaseModel):
    """Complete analysis response"""
    success: bool
    analysis_id: str
    execution_time: float
    product: Dict[str, Any]
    top_competitors: List[Dict[str, Any]]
    feature_matrix: Dict[str, Any]
    comparison: Dict[str, Any]
    gap_analysis: Dict[str, Any]
    insights: Dict[str, Any]
    metadata: Dict[str, Any]


@router.post("/analyze", response_model=AnalysisResponse, status_code=status.HTTP_200_OK)
async def analyze_product(
    product: ProductSubmission,
    current_user: dict = Depends(get_current_user)
):
    """
    Analyze product and discover competitors
    
    This endpoint performs a complete competitor analysis:
    1. AI-Powered Competitor Discovery - Automatically finds similar solutions
    2. Comparison Dashboard - Provides visual comparison data
    3. Gap Analysis - Identifies opportunities and market gaps
    
    **Request Body:**
    - name: Product name (required)
    - description: Product description (required)
    - features: List of product features (optional)
    - pricing: Pricing information (optional)
    - target_audience: Target audience (optional)
    
    **Response:**
    - top_competitors: Top 5 most relevant competitors
    - feature_matrix: Feature comparison matrix for visualization
    - comparison: Pricing and feature comparison data
    - gap_analysis: Market opportunities and gaps
    - insights: Strategic insights and recommendations
    
    **Execution Time:** Typically 30-60 seconds
    """
    try:
        logger.info(f"Received analysis request for product: {product.name}")
        
        # Convert to dict
        product_info = {
            "name": product.name,
            "description": product.description,
            "features": product.features,
            "pricing": product.pricing,
            "target_audience": product.target_audience
        }
        
        # Run analysis
        result = await CompetitorAnalysisPipeline.analyze_product(
            product_info,
            user_id=current_user.id,
            save_to_db=True
        )
        
        if not result.get('success'):
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result.get('error', 'Analysis failed')
            )
        
        logger.info(f"Analysis complete: {result['analysis_id']}")
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Analysis failed: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Analysis failed. Please try again later."
        )


@router.get("/health", status_code=status.HTTP_200_OK)
async def health_check():
    """
    Health check endpoint
    
    Returns the status of the competitor analysis service
    """
    return {
        "status": "healthy",
        "service": "competitor-analysis",
        "version": "1.0.0"
    }



@router.get("/analyses", status_code=status.HTTP_200_OK)
async def list_analyses(
    current_user: dict = Depends(get_current_user),
    limit: int = 50
):
    """
    List all competitor analyses for the current user
    
    Returns a list of previous analyses with summary information
    """
    try:
        analyses = CompetitorAnalysisPipeline.get_user_analyses(
            user_id=current_user.id,
            limit=limit
        )
        
        return {
            "success": True,
            "analyses": analyses,
            "total": len(analyses)
        }
        
    except Exception as e:
        logger.error(f"Failed to list analyses: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve analyses"
        )


@router.get("/analyses/{analysis_id}", response_model=AnalysisResponse, status_code=status.HTTP_200_OK)
async def get_analysis(
    analysis_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Get a specific analysis by ID
    
    Returns the complete analysis result
    """
    try:
        result = CompetitorAnalysisPipeline.get_analysis_by_id(
            analysis_id=analysis_id,
            user_id=current_user.id
        )
        
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Analysis not found"
            )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get analysis: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve analysis"
        )


@router.delete("/analyses/{analysis_id}", status_code=status.HTTP_200_OK)
async def delete_analysis(
    analysis_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Delete a specific analysis by ID
    
    Removes the analysis from the database
    """
    try:
        success = CompetitorAnalysisPipeline.delete_analysis(
            analysis_id=analysis_id,
            user_id=current_user.id
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Analysis not found or you don't have permission to delete it"
            )
        
        logger.info(f"Analysis deleted: {analysis_id} by user: {current_user.id}")
        return {
            "success": True,
            "message": "Analysis deleted successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete analysis: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete analysis"
        )
