"""
Keyword Generation Models
"""
from datetime import datetime
from typing import Optional, List
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


# Response Models for API
class KeywordGenerationResponse(BaseModel):
    """Response model for keyword generation"""
    success: bool
    keywords_id: Optional[str] = None
    data: Optional[dict] = None
    error: Optional[str] = None
    created_at: Optional[datetime] = None

class GeneratedKeywordsData(BaseModel):
    """Model for the generated keywords data structure"""
    potential_subreddits: List[str] = Field(default_factory=list, description="Relevant subreddits for the domain")
    domain_anchors: List[str] = Field(default_factory=list, description="Tools and workflows related to the domain")
    problem_phrases: List[str] = Field(default_factory=list, description="Common problem expressions")
    subreddit_count: int = Field(default=0, description="Number of subreddits found")
    anchor_count: int = Field(default=0, description="Number of domain anchors found")
    phrase_count: int = Field(default=0, description="Number of problem phrases found")

class KeywordGenerationRequest(BaseModel):
    """Request model for manual keyword generation"""
    input_id: str = Field(..., description="ID of the user input to generate keywords for")
    force_regenerate: bool = Field(default=False, description="Force regeneration even if keywords already exist")

# Database Models
class GeneratedKeywordsDB(BaseModel):
    """Database model for generated keywords"""
    id: Optional[PyObjectId] = Field(default_factory=PyObjectId, alias="_id")
    user_id: str  # User ID is a UUID string
    input_id: str  # Reference to the user input
    keywords_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    problem_description: str
    domain: Optional[str] = None
    search_text_used: str  # The text that was actually used for generation
    potential_subreddits: List[str] = Field(default_factory=list)
    domain_anchors: List[str] = Field(default_factory=list)
    problem_phrases: List[str] = Field(default_factory=list)
    generation_status: str = Field(default="pending")  # pending, completed, failed
    error_message: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    model_config = {
        "populate_by_name": True,
        "arbitrary_types_allowed": True,
        "json_encoders": {ObjectId: str}
    }

class KeywordSummary(BaseModel):
    """Summary model for keyword statistics"""
    keywords_id: str
    input_id: str
    generation_status: str
    subreddit_count: int
    anchor_count: int
    phrase_count: int
    created_at: datetime
    domain: Optional[str] = None
    search_text_used: str