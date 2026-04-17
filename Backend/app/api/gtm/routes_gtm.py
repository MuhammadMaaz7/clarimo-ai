"""
Module 6: GTM Strategy Generator – API Routes
Endpoints: create strategy, retrieve by ID, list user history.
"""

from fastapi import APIRouter, HTTPException
from typing import List

from app.db.models.gtm_model import GTMRequest, GTMResponse
from app.services.gtm.gtm_service import GTMService
from app.db.database import gtm_strategies_collection

router = APIRouter(prefix="/gtm", tags=["Go-to-Market Strategy"])
service = GTMService()


@router.post("/strategy/create", response_model=GTMResponse)
async def create_gtm_strategy(request: GTMRequest):
    """
    Generate a full Go-to-Market strategy.
    Accepts manual inputs or references to previous module outputs.
    """
    try:
        strategy = await service.create_strategy(request)
        return strategy
    except ValueError as val_err:
        raise HTTPException(status_code=400, detail=str(val_err))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/strategy/{gtm_id}", response_model=GTMResponse)
async def get_gtm_strategy(gtm_id: str):
    """Retrieve a previously generated GTM strategy by ID."""
    doc = gtm_strategies_collection.find_one({"gtm_id": gtm_id}, {"_id": 0})
    if not doc:
        raise HTTPException(status_code=404, detail="GTM strategy not found")
    return doc


@router.get("/history/{user_id}", response_model=List[GTMResponse])
async def get_user_gtm_history(user_id: str):
    """List all GTM strategies for a user, newest first."""
    docs = list(
        gtm_strategies_collection
        .find({"user_id": user_id}, {"_id": 0})
        .sort("created_at", -1)
        .limit(20)
    )
    return docs
