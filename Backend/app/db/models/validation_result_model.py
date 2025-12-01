"""
Idea Validation Module - Validation Result Database Models
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum


class ValidationStatus(str, Enum):
    """Validation status enumeration"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


class Score(BaseModel):
    """Individual metric score model"""
    value: int = Field(..., ge=1, le=5, description="Score value from 1 to 5")
    justifications: List[str] = Field(default_factory=list, description="Reasons for the score")
    evidence: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Supporting evidence")
    recommendations: List[str] = Field(default_factory=list, description="Actionable recommendations")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional metadata")


class ValidationConfig(BaseModel):
    """Configuration for validation execution"""
    include_web_search: bool = Field(True, description="Include web search for demand signals")
    include_competitive_analysis: bool = Field(True, description="Include competitive analysis")
    max_competitors_to_analyze: int = Field(10, ge=1, le=50, description="Maximum competitors to analyze")
    use_cached_results: bool = Field(True, description="Use cached results when available")


class ValidationResultCreate(BaseModel):
    """Model for creating a new validation result"""
    idea_id: str
    user_id: Optional[str] = None  # Optional - will be filled from auth token if not provided
    config: Optional[ValidationConfig] = Field(default_factory=ValidationConfig)


class ValidationResultResponse(BaseModel):
    """Model for validation result response"""
    model_config = {"arbitrary_types_allowed": True}
    
    validation_id: str
    idea_id: str
    user_id: str
    status: ValidationStatus
    overall_score: Optional[float] = None
    individual_scores: Optional[Dict[str, Score]] = None
    report_data: Optional[Dict[str, Any]] = None
    created_at: datetime
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None


class ValidationResultInDB(BaseModel):
    """Model for validation result stored in database"""
    validation_id: str
    idea_id: str
    user_id: str
    status: ValidationStatus
    overall_score: Optional[float] = None
    individual_scores: Optional[Dict[str, Any]] = None  # Stored as dict in MongoDB
    report_data: Optional[Dict[str, Any]] = None
    config: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None


class ValidationReport(BaseModel):
    """Comprehensive validation report model"""
    validation_id: str
    idea_id: str
    idea_title: str
    overall_score: float
    validation_date: datetime
    
    # Individual metric scores
    problem_clarity: Optional[Score] = None
    market_demand: Optional[Score] = None
    solution_fit: Optional[Score] = None
    differentiation: Optional[Score] = None
    technical_feasibility: Optional[Score] = None
    market_size: Optional[Score] = None
    monetization_potential: Optional[Score] = None
    risk_level: Optional[Score] = None
    user_validation_evidence: Optional[Score] = None
    
    # Aggregated insights
    strengths: List[str] = Field(default_factory=list, description="Top scoring areas")
    weaknesses: List[str] = Field(default_factory=list, description="Low scoring areas")
    critical_recommendations: List[str] = Field(default_factory=list, description="Top actionable recommendations")
    
    # Visualizations
    radar_chart_data: Dict[str, float] = Field(default_factory=dict, description="Data for radar chart")
    score_distribution: Dict[str, int] = Field(default_factory=dict, description="Score distribution data")
    
    # Detailed sections
    executive_summary: Optional[str] = None
    detailed_analysis: Optional[Dict[str, Any]] = None
    next_steps: List[str] = Field(default_factory=list)


class ComparisonReport(BaseModel):
    """Model for comparing multiple validation results"""
    comparison_id: str
    validation_ids: List[str]
    ideas: List[Dict[str, Any]]
    metric_comparison: Dict[str, List[float]]
    winners: Dict[str, str]  # metric -> idea_id
    overall_recommendation: Optional[str] = None
    created_at: datetime


class ValidationHistoryItem(BaseModel):
    """Model for validation history item"""
    validation_id: str
    idea_id: str
    overall_score: float
    status: ValidationStatus
    created_at: datetime
    completed_at: Optional[datetime] = None


class ValidationVersionComparison(BaseModel):
    """Model for comparing two validation versions"""
    idea_id: str
    validation_1_id: str
    validation_2_id: str
    validation_1_date: datetime
    validation_2_date: datetime
    score_deltas: Dict[str, float]  # metric -> delta
    improved_metrics: List[str]
    declined_metrics: List[str]
    unchanged_metrics: List[str]
    overall_score_delta: float


class SurveyEvidence(BaseModel):
    """Survey validation evidence"""
    respondent_count: int = Field(..., ge=1)
    key_findings: List[str] = Field(default_factory=list)
    satisfaction_score: Optional[float] = Field(None, ge=0.0, le=5.0)


class InterviewEvidence(BaseModel):
    """Interview validation evidence"""
    count: int = Field(..., ge=1)
    key_insights: List[str] = Field(default_factory=list)


class BetaUserEvidence(BaseModel):
    """Beta user validation evidence"""
    count: int = Field(..., ge=1)
    engagement_metrics: Optional[Dict[str, Any]] = None


class WaitlistEvidence(BaseModel):
    """Waitlist validation evidence"""
    count: int = Field(..., ge=1)
    growth_rate: Optional[str] = None


class ValidationEvidence(BaseModel):
    """User-provided validation evidence"""
    surveys: Optional[SurveyEvidence] = None
    interviews: Optional[InterviewEvidence] = None
    beta_users: Optional[BetaUserEvidence] = None
    waitlist: Optional[WaitlistEvidence] = None


class SharePrivacyLevel(str, Enum):
    """Privacy level for shared validation reports"""
    PUBLIC = "public"  # Anyone with link can view
    PRIVATE = "private"  # Only owner can view
    PASSWORD_PROTECTED = "password_protected"  # Requires password


class ShareLinkCreate(BaseModel):
    """Model for creating a shareable link"""
    validation_id: str
    privacy_level: SharePrivacyLevel = SharePrivacyLevel.PUBLIC
    password: Optional[str] = Field(None, min_length=6, description="Password for password-protected links")
    expires_at: Optional[datetime] = Field(None, description="Optional expiration date")


class ShareLinkResponse(BaseModel):
    """Model for shareable link response"""
    share_id: str
    validation_id: str
    share_url: str
    privacy_level: SharePrivacyLevel
    created_at: datetime
    expires_at: Optional[datetime] = None
    is_active: bool = True


class ShareLinkAccess(BaseModel):
    """Model for accessing a shared validation"""
    password: Optional[str] = Field(None, description="Password if link is password-protected")
