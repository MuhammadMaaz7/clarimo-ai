from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum

class ProductStage(str, Enum):
    IDEA = "idea"
    PROTOTYPE = "prototype"
    MVP = "mvp"
    BETA = "beta"
    LIVE = "live"

class LaunchPlanRequest(BaseModel):
    idea_description: str
    target_audience: Optional[str] = None
    product_stage: ProductStage = ProductStage.IDEA
    estimated_budget: float = 0.0
    team_size: int = 1
    target_market: Optional[str] = None
    expected_timeline_months: int = 6
    
    # Optional references to previous modules
    problem_discovery_id: Optional[str] = None
    validation_id: Optional[str] = None
    competitor_analysis_id: Optional[str] = None
    
    # Auth context (passed internaly)
    user_id: Optional[str] = None

class BudgetBreakdown(BaseModel):
    category: str
    percentage: float
    amount: float
    description: str

class Milestone(BaseModel):
    title: str
    duration_weeks: int
    tasks: List[str]
    description: str

class ChecklistItem(BaseModel):
    task: str
    priority: str  # high, medium, low
    category: str  # legal, marketing, technical, ops

class LaunchPlanResponse(BaseModel):
    plan_id: str
    user_id: str
    idea_id: Optional[str] = None
    
    # Core Plan Data
    launch_timing_recommendation: str
    readiness_score: float  # 0 to 100
    
    budget_allocation: List[BudgetBreakdown]
    timeline: List[Milestone]
    checklist: List[ChecklistItem]
    
    # Extra insights (often from LLM)
    executive_summary: str
    risk_factors: List[str]
    success_metrics: List[str]
    market_saturation_analysis: Optional[str] = None
    
    # Reference to inputs
    inputs: Optional[LaunchPlanRequest] = None
    
    created_at: datetime
    status: str = "completed"

class LaunchPlanInDB(LaunchPlanResponse):
    inputs: LaunchPlanRequest
    updated_at: datetime
