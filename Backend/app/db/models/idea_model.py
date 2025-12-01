"""
Idea Validation Module - Idea Database Models
"""

from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime


class IdeaCreate(BaseModel):
    """Model for creating a new idea"""
    title: str = Field(..., min_length=5, max_length=200, description="Idea title")
    description: str = Field(..., min_length=50, description="Detailed idea description")
    problem_statement: str = Field(..., min_length=20, description="Problem the idea solves")
    solution_description: str = Field(..., min_length=50, description="Proposed solution description")
    target_market: str = Field(..., min_length=5, description="Target market or audience")
    business_model: Optional[str] = Field(None, description="Business model description")
    team_capabilities: Optional[str] = Field(None, description="Team skills and capabilities")
    linked_pain_point_ids: Optional[List[str]] = Field(default_factory=list, description="Pain point IDs from Module 1")


class IdeaUpdate(BaseModel):
    """Model for updating an existing idea"""
    title: Optional[str] = Field(None, min_length=5, max_length=200)
    description: Optional[str] = Field(None, min_length=50)
    problem_statement: Optional[str] = Field(None, min_length=20)
    solution_description: Optional[str] = Field(None, min_length=50)
    target_market: Optional[str] = Field(None, min_length=5)
    business_model: Optional[str] = None
    team_capabilities: Optional[str] = None
    linked_pain_point_ids: Optional[List[str]] = None


class LatestValidationSummary(BaseModel):
    """Summary of latest validation for idea response"""
    validation_id: str
    overall_score: float
    status: str
    created_at: datetime


class IdeaResponse(BaseModel):
    """Model for idea response"""
    id: str
    user_id: str
    title: str
    description: str
    problem_statement: str
    solution_description: str
    target_market: str
    business_model: Optional[str]
    team_capabilities: Optional[str]
    linked_pain_points: List[str]
    created_at: datetime
    updated_at: datetime
    validation_count: int = 0
    latest_validation_id: Optional[str] = None
    latest_validation: Optional[LatestValidationSummary] = None


class IdeaInDB(BaseModel):
    """Model for idea stored in database"""
    id: str
    user_id: str
    title: str
    description: str
    problem_statement: str
    solution_description: str
    target_market: str
    business_model: Optional[str]
    team_capabilities: Optional[str]
    linked_pain_points: List[str]
    created_at: datetime
    updated_at: datetime
    validation_count: int = 0
    latest_validation_id: Optional[str] = None


class IdeaFilters(BaseModel):
    """Model for filtering ideas"""
    sort_by: Optional[str] = Field(None, description="Field to sort by (e.g., 'created_at', 'overall_score')")
    sort_order: Optional[str] = Field("desc", description="Sort order: 'asc' or 'desc'")
    has_validation: Optional[bool] = Field(None, description="Filter by validation status")
    min_score: Optional[float] = Field(None, ge=1.0, le=5.0, description="Minimum overall score")
    max_score: Optional[float] = Field(None, ge=1.0, le=5.0, description="Maximum overall score")
