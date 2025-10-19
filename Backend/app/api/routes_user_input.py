"""
User Input API Routes
"""
from fastapi import APIRouter, HTTPException, status, Depends, Query
from typing import List, Optional
import logging

from app.db.models.input_model import UserInputRequest, UserInputResponse
from app.db.models.user_model import UserResponse
from app.core.security import get_current_user
from app.services.user_input_service import UserInputService

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/user-input", tags=["User Input"])


@router.post("/", response_model=UserInputResponse, status_code=status.HTTP_201_CREATED)
async def create_user_input(
    request: UserInputRequest,
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Create a new user input record in the database.
    
    This endpoint accepts user input data, validates it, and stores it in the database
    with proper user association and timestamps.
    """
    try:
        # Log the incoming request
        logger.info(f"Creating user input for user {current_user.id}: {request.problem_description[:50]}...")
        
        # Create user input in database
        response = await UserInputService.create_user_input(
            user_id=current_user.id,
            input_data=request
        )
        
        logger.info(f"Successfully created user input with ID: {response.input_id}")
        return response
        
    except Exception as e:
        logger.error(f"Error creating user input for user {current_user.id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to store user input: {str(e)}"
        )


@router.get("/", response_model=List[dict])
async def get_user_inputs(
    current_user: UserResponse = Depends(get_current_user),
    limit: int = Query(50, ge=1, le=100, description="Maximum number of records to return"),
    skip: int = Query(0, ge=0, description="Number of records to skip for pagination"),
    status: Optional[str] = Query(None, description="Filter by status (received, processing, completed, failed)")
):
    """
    Retrieve user inputs for the authenticated user.
    
    Supports pagination and optional status filtering.
    """
    try:
        logger.info(f"Retrieving user inputs for user {current_user.id} (limit: {limit}, skip: {skip}, status: {status})")
        
        user_inputs = await UserInputService.get_user_inputs(
            user_id=current_user.id,
            limit=limit,
            skip=skip,
            status=status
        )
        
        logger.info(f"Retrieved {len(user_inputs)} user inputs for user {current_user.id}")
        return user_inputs
        
    except Exception as e:
        logger.error(f"Error retrieving user inputs for user {current_user.id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve user inputs: {str(e)}"
        )


@router.get("/{input_id}")
async def get_user_input_by_id(
    input_id: str,
    current_user: UserResponse = Depends(get_current_user),
    include_keywords: bool = Query(False, description="Include generated keywords in the response")
):
    """
    Retrieve a specific user input by ID.
    
    Only returns inputs that belong to the authenticated user.
    Optionally includes generated keywords if available.
    """
    try:
        logger.info(f"Retrieving user input {input_id} for user {current_user.id}")
        
        user_input = await UserInputService.get_user_input_by_id(
            user_id=current_user.id,
            input_id=input_id
        )
        
        if not user_input:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User input not found"
            )
        
        # Include keywords if requested
        if include_keywords:
            try:
                from app.services.keyword_generation_service import KeywordGenerationService
                keywords = await KeywordGenerationService.get_keywords_by_input_id(
                    user_id=current_user.id,
                    input_id=input_id
                )
                user_input["generated_keywords"] = keywords
            except Exception as keyword_error:
                logger.warning(f"Failed to retrieve keywords for input {input_id}: {str(keyword_error)}")
                user_input["generated_keywords"] = None
        
        logger.info(f"Successfully retrieved user input {input_id}")
        return user_input
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving user input {input_id} for user {current_user.id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve user input: {str(e)}"
        )


@router.put("/{input_id}/status")
async def update_input_status(
    input_id: str,
    status: str,
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Update the status of a user input.
    
    Valid statuses: received, processing, completed, failed
    """
    try:
        # Validate status
        valid_statuses = ["received", "processing", "completed", "failed"]
        if status not in valid_statuses:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid status. Must be one of: {', '.join(valid_statuses)}"
            )
        
        logger.info(f"Updating status of user input {input_id} to {status} for user {current_user.id}")
        
        success = await UserInputService.update_input_status(
            user_id=current_user.id,
            input_id=input_id,
            status=status
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User input not found or no changes made"
            )
        
        logger.info(f"Successfully updated status of user input {input_id}")
        return {"success": True, "message": f"Status updated to {status}"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating status of user input {input_id} for user {current_user.id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update user input status: {str(e)}"
        )


@router.delete("/{input_id}")
async def delete_user_input(
    input_id: str,
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Delete a user input record.
    
    Only allows deletion of inputs that belong to the authenticated user.
    """
    try:
        logger.info(f"Deleting user input {input_id} for user {current_user.id}")
        
        success = await UserInputService.delete_user_input(
            user_id=current_user.id,
            input_id=input_id
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User input not found"
            )
        
        logger.info(f"Successfully deleted user input {input_id}")
        return {"success": True, "message": "User input deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting user input {input_id} for user {current_user.id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete user input: {str(e)}"
        )


@router.get("/stats/count")
async def get_input_count(
    current_user: UserResponse = Depends(get_current_user),
    status: Optional[str] = Query(None, description="Filter by status")
):
    """
    Get count of user inputs for the authenticated user.
    
    Optionally filter by status.
    """
    try:
        logger.info(f"Getting input count for user {current_user.id} (status: {status})")
        
        count = await UserInputService.get_input_count_by_user(
            user_id=current_user.id,
            status=status
        )
        
        logger.info(f"User {current_user.id} has {count} inputs (status: {status})")
        return {"count": count, "status_filter": status}
        
    except Exception as e:
        logger.error(f"Error getting input count for user {current_user.id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get input count: {str(e)}"
        )