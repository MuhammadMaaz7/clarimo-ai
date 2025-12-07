"""
Competitor Analysis Model
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any, Literal
from datetime import datetime


class Competitor(BaseModel):
    """Individual competitor information"""
    name: str
    description: str
    source: Literal['app_store', 'play_store', 'github', 'product_hunt', 'hackernews', 'web']
    url: Optional[str] = None
    rating: Optional[float] = None
    rating_count: Optional[int] = None
    price: Optional[float] = None
    installs: Optional[str] = None
    stars: Optional[int] = None
    forks: Optional[int] = None
    votes: Optional[int] = None  # For Product Hunt
    comments: Optional[int] = None  # For Product Hunt/HackerNews
    topics: Optional[List[str]] = None  # For Product Hunt
    relevance_score: Optional[int] = None  # For Google Search (how many queries returned it)
    features: Optional[List[str]] = None  # Scraped features
    pricing: Optional[Any] = None  # Scraped pricing info
    target_audience: Optional[Any] = None  # Scraped target audience
    key_benefits: Optional[List[str]] = None  # Scraped benefits
    product_type: Optional[str] = None  # Scraped product type
    enriched: Optional[bool] = None  # Whether data was enriched via scraping
    strengths: Optional[List[str]] = None
    weaknesses: Optional[List[str]] = None
    market_position: Optional[Literal['leader', 'challenger', 'niche', 'emerging']] = None


class MarketInsights(BaseModel):
    """Market insights from analysis"""
    total_competitors: int
    market_saturation: Literal['low', 'medium', 'high']
    opportunity_score: float = Field(..., ge=0, le=10)
    key_trends: List[str]


class PositioningAnalysis(BaseModel):
    """SWOT-style positioning analysis"""
    your_strengths: List[str]
    your_weaknesses: List[str]
    opportunities: List[str]
    threats: List[str]


class FeatureComparison(BaseModel):
    """Feature comparison data"""
    feature: str
    your_product: bool
    competitors_with_feature: int
    competitive_advantage: Literal['strong', 'moderate', 'weak']


class CompetitiveAnalysisCreate(BaseModel):
    """Model for creating analysis"""
    product_id: str


class CompetitiveAnalysisResponse(BaseModel):
    """Complete analysis response"""
    analysis_id: str
    product_id: str
    user_id: str
    status: Literal['pending', 'in_progress', 'completed', 'failed']
    competitors: List[Competitor]
    market_insights: Optional[MarketInsights] = None
    positioning_analysis: Optional[PositioningAnalysis] = None
    feature_comparison: Optional[List[FeatureComparison]] = None
    recommendations: List[str]
    created_at: str
    completed_at: Optional[str] = None
    error_message: Optional[str] = None

    class Config:
        from_attributes = True


class AnalysisStatusResponse(BaseModel):
    """Analysis status for polling"""
    analysis_id: str
    status: Literal['pending', 'in_progress', 'completed', 'failed']
    progress: int = Field(..., ge=0, le=100)
    current_stage: str
    estimated_completion: Optional[str] = None


class AnalysisHistoryItem(BaseModel):
    """History item for analysis"""
    analysis_id: str
    product_id: str
    competitors_found: int
    opportunity_score: float
    status: str
    created_at: str
    completed_at: Optional[str] = None
