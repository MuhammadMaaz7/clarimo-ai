"""
Customer Insights Module - Database Models
"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from bson import ObjectId
import uuid


class PyObjectId(ObjectId):
    """Custom ObjectId type for Pydantic models"""
    @classmethod
    def __get_pydantic_core_schema__(cls, source_type, handler):
        from pydantic_core import core_schema
        return core_schema.no_info_plain_validator_function(cls.validate)

    @classmethod
    def validate(cls, v):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid ObjectId")
        return ObjectId(v)

    @classmethod
    def __get_pydantic_json_schema__(cls, field_schema):
        field_schema.update(type="string")


# ==================== REQUEST/RESPONSE MODELS ====================

class CustomerInsightsRequest(BaseModel):
    """Request model for starting customer insights analysis"""
    startup_idea: str = Field(..., min_length=10, max_length=500, description="Startup idea or problem to analyze")
    target_market: Optional[str] = Field(None, max_length=200, description="Optional target market description")
    
    class Config:
        json_schema_extra = {
            "example": {
                "startup_idea": "AI-powered meal planning app for busy professionals",
                "target_market": "Working professionals aged 25-45"
            }
        }


class CommunityInfo(BaseModel):
    """Community information"""
    name: str
    source: str  # "reddit" or "producthunt"
    discussion_count: int
    engagement_score: float
    url: Optional[str] = None
    description: Optional[str] = None


class AudienceSegment(BaseModel):
    """Audience segment information"""
    segment_id: str
    segment_name: str
    summary: str
    pain_points: List[str]
    interests: List[str]
    discussion_count: int
    sample_discussions: Optional[List[str]] = None


class InsightSummary(BaseModel):
    """Insight summary"""
    pain_points: List[str]
    desired_features: List[str]
    recurring_themes: List[str]
    keywords: List[str]


class CustomerInsightsResponse(BaseModel):
    """Response model for customer insights analysis"""
    success: bool
    analysis_id: str
    message: str
    status: str  # "processing", "completed", "failed"
    communities: Optional[List[CommunityInfo]] = None
    segments: Optional[List[AudienceSegment]] = None
    insights: Optional[InsightSummary] = None
    created_at: datetime
    completed_at: Optional[datetime] = None
    execution_time: Optional[float] = None


class AnalysisStatusResponse(BaseModel):
    """Response model for analysis status"""
    analysis_id: str
    status: str
    current_stage: Optional[str] = None
    progress_percentage: int
    message: str
    created_at: datetime
    estimated_completion: Optional[str] = None


class AnalysisHistoryItem(BaseModel):
    """History item for user's analyses"""
    analysis_id: str
    startup_idea: str
    status: str
    created_at: datetime
    completed_at: Optional[datetime] = None
    communities_found: int
    segments_found: int


# ==================== DATABASE MODELS ====================

class CustomerInsightsAnalysisDB(BaseModel):
    """Database model for customer insights analysis"""
    id: Optional[PyObjectId] = Field(default_factory=PyObjectId, alias="_id")
    analysis_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str  # UUID string
    startup_idea: str
    target_market: Optional[str] = None
    status: str = Field(default="processing")  # processing, completed, failed
    current_stage: Optional[str] = None  # data_collection, segmentation, insights_extraction
    progress_percentage: int = Field(default=0)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    execution_time: Optional[float] = None
    error_message: Optional[str] = None
    
    # Results
    communities: Optional[List[Dict[str, Any]]] = None
    segments: Optional[List[Dict[str, Any]]] = None
    insights: Optional[Dict[str, Any]] = None
    
    # Metadata
    total_discussions: int = Field(default=0)
    reddit_discussions: int = Field(default=0)
    producthunt_discussions: int = Field(default=0)
    
    model_config = {
        "populate_by_name": True,
        "arbitrary_types_allowed": True,
        "json_encoders": {ObjectId: str}
    }


class RawDiscussionDB(BaseModel):
    """Database model for raw discussions"""
    id: Optional[PyObjectId] = Field(default_factory=PyObjectId, alias="_id")
    analysis_id: str
    source: str  # "reddit" or "producthunt"
    discussion_id: str
    title: str
    content: str
    url: Optional[str] = None
    author: Optional[str] = None
    created_at: datetime
    score: int = Field(default=0)
    comments_count: int = Field(default=0)
    community: Optional[str] = None  # subreddit or product name
    metadata: Optional[Dict[str, Any]] = None
    fetched_at: datetime = Field(default_factory=datetime.utcnow)
    
    model_config = {
        "populate_by_name": True,
        "arbitrary_types_allowed": True,
        "json_encoders": {ObjectId: str}
    }


class AudienceSegmentDB(BaseModel):
    """Database model for audience segments"""
    id: Optional[PyObjectId] = Field(default_factory=PyObjectId, alias="_id")
    analysis_id: str
    segment_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    segment_name: str
    summary: str
    pain_points: List[str] = Field(default_factory=list)
    interests: List[str] = Field(default_factory=list)
    discussion_ids: List[str] = Field(default_factory=list)
    discussion_count: int = Field(default=0)
    cluster_id: Optional[int] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    model_config = {
        "populate_by_name": True,
        "arbitrary_types_allowed": True,
        "json_encoders": {ObjectId: str}
    }


class CommunityInsightDB(BaseModel):
    """Database model for community insights"""
    id: Optional[PyObjectId] = Field(default_factory=PyObjectId, alias="_id")
    analysis_id: str
    community_name: str
    source: str  # "reddit" or "producthunt"
    discussion_count: int
    engagement_score: float
    url: Optional[str] = None
    description: Optional[str] = None
    top_keywords: List[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    model_config = {
        "populate_by_name": True,
        "arbitrary_types_allowed": True,
        "json_encoders": {ObjectId: str}
    }
