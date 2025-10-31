from datetime import datetime
from typing import Optional, Dict, Any
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


# Request/Response Models for API
class UserInputRequest(BaseModel):
    """Request model for submitting user input - simplified with basic validation only"""
    problem_description: str = Field(..., min_length=10, max_length=1000, description="Description of the problem or need")
    domain: Optional[str] = Field(None, max_length=100, description="Optional domain or industry context")
    region: Optional[str] = Field(None, max_length=100, description="Optional geographic region")
    target_audience: Optional[str] = Field(None, max_length=100, description="Optional target audience description")

class UserInputResponse(BaseModel):
    """Response model for user input submission"""
    success: bool
    input_id: str
    message: str
    created_at: datetime

# Database Models
class UserInputDB(BaseModel):
    """Database model for user inputs"""
    id: Optional[PyObjectId] = Field(default_factory=PyObjectId, alias="_id")
    user_id: str  # User ID is a UUID string, not ObjectId
    input_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    problem_description: str
    domain: Optional[str] = None
    region: Optional[str] = None
    target_audience: Optional[str] = None
    status: str = Field(default="received")
    current_stage: str = Field(default="received")  # Track current processing stage
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    processing_started_at: Optional[datetime] = None  # When processing actually starts
    completed_at: Optional[datetime] = None  # When processing completes
    error_message: Optional[str] = None  # Store any error messages
    results: Optional[Dict[str, Any]] = None  # Store final pain points results

    model_config = {
        "populate_by_name": True,
        "arbitrary_types_allowed": True,
        "json_encoders": {ObjectId: str}
    }