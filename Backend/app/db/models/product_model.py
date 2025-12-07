"""
Product Model for Competitor Analysis Module
"""

from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime


class ProductBase(BaseModel):
    """Base product model"""
    product_name: str = Field(..., min_length=1, max_length=200)
    product_description: str = Field(..., min_length=20, max_length=2000)
    key_features: List[str] = Field(..., min_items=1)


class ProductCreate(ProductBase):
    """Model for creating a product"""
    pass


class ProductUpdate(BaseModel):
    """Model for updating a product"""
    product_name: Optional[str] = Field(None, min_length=1, max_length=200)
    product_description: Optional[str] = Field(None, min_length=20, max_length=2000)
    key_features: Optional[List[str]] = Field(None, min_items=1)


class LatestAnalysisSummary(BaseModel):
    """Summary of latest analysis"""
    analysis_id: str
    competitors_found: int
    status: str
    created_at: str


class ProductResponse(ProductBase):
    """Product response model"""
    id: str
    user_id: str
    created_at: str
    updated_at: str
    latest_analysis: Optional[LatestAnalysisSummary] = None

    class Config:
        from_attributes = True
