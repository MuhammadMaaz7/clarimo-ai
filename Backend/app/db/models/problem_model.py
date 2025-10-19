from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

class ProblemDiscoveryRequest(BaseModel):
    """Problem discovery request with basic validation only"""
    problemDescription: str = Field(..., min_length=10, max_length=1000, description="Description of the problem to discover")
    domain: Optional[str] = Field(None, max_length=100, description="Optional domain/industry context")
    region: Optional[str] = Field(None, max_length=100, description="Optional geographic region")
    targetAudience: Optional[str] = Field(None, max_length=100, description="Optional target audience description")

class ProblemDiscoveryResponse(BaseModel):
    success: bool
    message: str
    request_id: str
    timestamp: datetime
    data: Optional[dict] = None

class DiscoveredProblem(BaseModel):
    id: int
    title: str
    description: str
    source: str
    score: int
    relevance_score: Optional[float] = None
    tags: List[str] = []

class ProblemDiscoveryResult(BaseModel):
    request_id: str
    problems: List[DiscoveredProblem]
    total_found: int
    search_parameters: ProblemDiscoveryRequest
    timestamp: datetime