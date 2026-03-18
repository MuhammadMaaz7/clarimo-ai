from fastapi import APIRouter, HTTPException, Depends
from typing import List
from app.db.models.launch_plan_model import LaunchPlanRequest, LaunchPlanResponse
from app.services.launch_planning.launch_planning_service import LaunchPlanningService
from app.db.database import launch_plans_collection
from datetime import datetime

router = APIRouter(prefix="/launch-planning", tags=["Launch Planning"])
service = LaunchPlanningService()

@router.post("/plan/create", response_model=LaunchPlanResponse)
async def create_launch_plan(request: LaunchPlanRequest):
    """
    Generate a new startup launch plan.
    """
    try:
        plan = await service.create_plan(request)
        return plan
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/plan/{plan_id}", response_model=LaunchPlanResponse)
async def get_launch_plan(plan_id: str):
    """
    Retrieve a specific launch plan.
    """
    plan = launch_plans_collection.find_one({"plan_id": plan_id})
    if not plan:
        raise HTTPException(status_code=404, detail="Launch plan not found")
    return plan

@router.get("/history/{user_id}", response_model=List[LaunchPlanResponse])
async def get_user_history(user_id: str):
    """
    Get all launch plans for a user.
    """
    plans = list(launch_plans_collection.find({"user_id": user_id}).sort("created_at", -1))
    return plans
