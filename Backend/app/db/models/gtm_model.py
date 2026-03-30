"""
Module 6: Go-to-Market Strategy Generator
Pydantic models for request/response validation and MongoDB storage.
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum


class BusinessModel(str, Enum):
    B2B = "b2b"
    B2C = "b2c"
    B2B2C = "b2b2c"
    MARKETPLACE = "marketplace"
    SAAS = "saas"
    ECOMMERCE = "ecommerce"


class GTMRequest(BaseModel):
    # Core inputs (always required)
    startup_description: str
    target_audience: str
    unique_value_proposition: Optional[str] = None
    business_model: BusinessModel = BusinessModel.SAAS
    budget: float = 5000.0
    launch_date_weeks: int = 12  # weeks until launch

    # Optional links to previous modules
    problem_discovery_id: Optional[str] = None
    validation_id: Optional[str] = None
    competitor_analysis_id: Optional[str] = None
    launch_plan_id: Optional[str] = None

    # Auth context
    user_id: Optional[str] = None


# ── Sub-models ──────────────────────────────────────────────────────────────

class ChannelRecommendation(BaseModel):
    channel: str                  # e.g. "LinkedIn Ads"
    category: str                 # paid / organic / community / partnership
    priority: str                 # high / medium / low
    rationale: str
    estimated_reach: str          # e.g. "10k–50k impressions/month"
    estimated_cost: str           # e.g. "$500–$1,000/month"
    tactics: List[str]            # 2-3 concrete tactics


class MessagingGuide(BaseModel):
    headline: str                 # Primary value prop headline
    tagline: str                  # Short punchy tagline
    elevator_pitch: str           # 2-sentence pitch
    tone: str                     # e.g. "Professional & Empathetic"
    key_messages: List[str]       # 3-5 core messages
    differentiators: List[str]    # What sets you apart
    pain_points_addressed: List[str]
    call_to_action: str


class CampaignMilestone(BaseModel):
    phase: str                    # e.g. "Pre-Launch Awareness"
    week_start: int
    week_end: int
    objective: str
    activities: List[str]
    kpis: List[str]
    budget_allocation_pct: float  # % of total budget


class GTMResponse(BaseModel):
    gtm_id: str
    user_id: str

    # Core outputs
    executive_summary: str
    channel_recommendations: List[ChannelRecommendation]
    messaging_guide: MessagingGuide
    campaign_roadmap: List[CampaignMilestone]

    # Insights
    positioning_statement: str
    target_segment_analysis: str
    competitive_differentiation: str
    risk_factors: List[str]
    success_metrics: List[str]

    created_at: datetime
    status: str = "completed"


class GTMInDB(GTMResponse):
    """Extended model stored in MongoDB, includes raw inputs."""
    inputs: GTMRequest
    domain_detected: Optional[str] = None
    updated_at: datetime
