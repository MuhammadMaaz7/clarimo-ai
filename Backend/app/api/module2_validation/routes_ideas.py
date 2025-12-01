"""
API routes for Idea Management
"""

from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional
from app.db.models.idea_model import (
    IdeaCreate,
    IdeaUpdate,
    IdeaResponse,
    IdeaFilters
)
from app.services.module2_validation.idea_management_service import IdeaManagementService
from app.core.dependencies import get_current_user

router = APIRouter(prefix="/ideas", tags=["Ideas"])


@router.post("", response_model=IdeaResponse, status_code=status.HTTP_201_CREATED)
async def create_idea(
    idea_data: IdeaCreate,
    current_user: dict = Depends(get_current_user)
):
    """
    Create a new startup idea
    
    - **title**: Idea title (5-200 characters)
    - **description**: Detailed description (min 50 characters)
    - **problem_statement**: Problem the idea solves (min 20 characters)
    - **solution_description**: Proposed solution (min 50 characters)
    - **target_market**: Target market or audience (min 5 characters)
    - **business_model**: Optional business model description
    - **team_capabilities**: Optional team skills and capabilities
    - **linked_pain_point_ids**: Optional list of pain point IDs from Module 1
    """
    try:
        user_id = current_user.id
        idea = IdeaManagementService.create_idea(user_id, idea_data)
        return idea
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create idea: {str(e)}"
        )


@router.get("/{idea_id}", response_model=IdeaResponse)
async def get_idea(
    idea_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Get a specific idea by ID
    
    Returns the idea if it exists and belongs to the current user.
    """
    user_id = current_user.id
    idea = IdeaManagementService.get_idea(user_id, idea_id)
    
    if not idea:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Idea not found"
        )
    
    return idea


@router.get("", response_model=List[IdeaResponse])
async def list_ideas(
    sort_by: Optional[str] = None,
    sort_order: Optional[str] = "desc",
    has_validation: Optional[bool] = None,
    min_score: Optional[float] = None,
    max_score: Optional[float] = None,
    current_user: dict = Depends(get_current_user)
):
    """
    List all ideas for the current user
    
    Query parameters:
    - **sort_by**: Field to sort by (e.g., 'created_at', 'updated_at', 'validation_count')
    - **sort_order**: Sort order ('asc' or 'desc', default: 'desc')
    - **has_validation**: Filter by validation status (true/false)
    - **min_score**: Minimum overall validation score (1.0-5.0)
    - **max_score**: Maximum overall validation score (1.0-5.0)
    """
    user_id = current_user.id
    
    filters = IdeaFilters(
        sort_by=sort_by,
        sort_order=sort_order,
        has_validation=has_validation,
        min_score=min_score,
        max_score=max_score
    )
    
    ideas = IdeaManagementService.list_ideas(user_id, filters)
    return ideas


@router.put("/{idea_id}", response_model=IdeaResponse)
async def update_idea(
    idea_id: str,
    updates: IdeaUpdate,
    current_user: dict = Depends(get_current_user)
):
    """
    Update an existing idea
    
    Only provided fields will be updated. All fields are optional.
    """
    user_id = current_user.id
    updated_idea = IdeaManagementService.update_idea(user_id, idea_id, updates)
    
    if not updated_idea:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Idea not found"
        )
    
    return updated_idea


@router.delete("/{idea_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_idea(
    idea_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Delete an idea and all associated validation results
    
    This operation cannot be undone.
    """
    user_id = current_user.id
    success = IdeaManagementService.delete_idea(user_id, idea_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Idea not found"
        )
    
    return None


@router.post("/{idea_id}/link-pain-points", status_code=status.HTTP_200_OK)
async def link_pain_points(
    idea_id: str,
    pain_point_ids: List[str],
    current_user: dict = Depends(get_current_user)
):
    """
    Link pain points from Module 1 to an idea
    
    - **pain_point_ids**: List of pain point IDs to associate with the idea
    """
    user_id = current_user.id
    success = IdeaManagementService.link_pain_points(
        user_id,
        idea_id,
        pain_point_ids
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Idea not found"
        )
    
    return {"message": "Pain points linked successfully", "count": len(pain_point_ids)}
