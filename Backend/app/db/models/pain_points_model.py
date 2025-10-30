"""
Pain Points Database Models
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime

class PostReference(BaseModel):
    """Post reference model"""
    post_id: str
    subreddit: str
    created_utc: str
    url: str
    text: str
    title: Optional[str] = None
    score: Optional[int] = None
    num_comments: Optional[int] = None

class PainPoint(BaseModel):
    """Individual pain point model"""
    cluster_id: str
    problem_title: str
    problem_description: str
    post_references: List[PostReference]
    analysis_timestamp: float
    source: str = "reddit_cluster_analysis"

class PainPointsAnalysis(BaseModel):
    """Complete pain points analysis model for database storage"""
    user_id: str
    input_id: str
    original_query: str
    total_clusters: int
    pain_points_count: int
    pain_points: List[PainPoint]
    analysis_timestamp: datetime
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
class PainPointsHistoryItem(BaseModel):
    """Pain points history item for user profile"""
    input_id: str
    original_query: str
    pain_points_count: int
    total_clusters: int
    analysis_timestamp: datetime
    created_at: datetime