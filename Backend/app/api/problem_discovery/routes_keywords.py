"""
Keyword Generation API Routes
"""
from fastapi import APIRouter, HTTPException, status, Depends, BackgroundTasks, Query
from typing import List, Optional
import logging

from app.db.models.keyword_model import (
    KeywordGenerationResponse, 
    KeywordGenerationRequest,
    GeneratedKeywordsData,
    KeywordSummary
)
from app.db.models.user_model import UserResponse
from app.core.security import get_current_user
from app.services.problem_discovery.keyword_generation_service import KeywordGenerationService
from app.services.problem_discovery.user_input_service import UserInputService
from app.services.shared.processing_lock_manager import processing_lock_service, ProcessingStage

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/keywords", tags=["Keyword Generation"])


@router.post("/generate", response_model=KeywordGenerationResponse)
async def generate_keywords(
    request: KeywordGenerationRequest,
    background_tasks: BackgroundTasks,
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Generate keywords for a specific user input.
    
    This endpoint triggers AI-powered keyword generation for a user input.
    The generation happens in the background and results are stored in the database.
    """
    try:
        logger.info(f"Generating keywords for input {request.input_id} (user: {current_user.id})")
        
        # Verify the input belongs to the current user
        user_input = await UserInputService.get_user_input_by_id(
            user_id=current_user.id,
            input_id=request.input_id
        )
        
        if not user_input:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User input not found"
            )
        
        # Check if processing is already in progress
        is_processing = await processing_lock_service.is_processing(current_user.id, request.input_id)
        if is_processing:
            current_stage = await processing_lock_service.get_current_stage(current_user.id, request.input_id)
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Processing already in progress. Current stage: {current_stage.value if current_stage else 'unknown'}"
            )
        
        # Check if keywords already exist (unless force regenerate is requested)
        if not request.force_regenerate:
            existing_keywords = await KeywordGenerationService.get_keywords_by_input_id(
                user_id=current_user.id,
                input_id=request.input_id
            )
            
            if existing_keywords and existing_keywords.get("generation_status") == "completed":
                logger.info(f"Keywords already exist for input {request.input_id}")
                return KeywordGenerationResponse(
                    success=True,
                    keywords_id=existing_keywords["keywords_id"],
                    data={
                        "potential_subreddits": existing_keywords["potential_subreddits"],
                        "domain_anchors": existing_keywords["domain_anchors"],
                        "problem_phrases": existing_keywords["problem_phrases"],
                        "subreddit_count": len(existing_keywords["potential_subreddits"]),
                        "anchor_count": len(existing_keywords["domain_anchors"]),
                        "phrase_count": len(existing_keywords["problem_phrases"])
                    },
                    created_at=existing_keywords["created_at"]
                )
        
        # Start background processing for keyword generation
        background_tasks.add_task(
            generate_keywords_background,
            current_user.id,
            request.input_id,
            user_input["problem_description"],
            user_input.get("domain"),
            request.force_regenerate
        )
        
        logger.info(f"Started background keyword generation for input {request.input_id}")
        return KeywordGenerationResponse(
            success=True,
            keywords_id="processing",
            message="Keyword generation started in background",
            data=None,
            created_at=None
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in keyword generation endpoint for input {request.input_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate keywords: {str(e)}"
        )


async def generate_keywords_background(
    user_id: str,
    input_id: str,
    problem_description: str,
    domain: Optional[str],
    force_regenerate: bool
):
    """
    Background task for keyword generation
    """
    try:
        # Acquire processing lock
        lock_acquired = await processing_lock_service.acquire_lock(user_id, input_id)
        if not lock_acquired:
            logger.warning(f"Processing already in progress for {user_id}:{input_id}")
            return
        
        try:
            # Update user input status to processing
            await UserInputService.update_input_status(
                user_id=user_id,
                input_id=input_id,
                status="processing",
                current_stage=ProcessingStage.KEYWORD_GENERATION.value
            )
            
            # Generate keywords
            result = await KeywordGenerationService.generate_keywords_for_input(
                user_id=user_id,
                input_id=input_id,
                problem_description=problem_description,
                domain=domain
            )
            
            if not result["success"]:
                logger.error(f"Keyword generation failed for input {input_id}: {result.get('error')}")
                # Status update is handled within the service for failures
                
        except Exception as processing_error:
            logger.error(f"Error in background keyword generation for {input_id}: {str(processing_error)}")
            # Update status to failed
            await UserInputService.update_input_status(
                user_id=user_id,
                input_id=input_id,
                status="failed",
                current_stage=ProcessingStage.FAILED.value,
                error_message=str(processing_error)
            )
            
        finally:
            # Always release the lock
            await processing_lock_service.release_lock(user_id, input_id)
            
    except Exception as e:
        logger.error(f"Background keyword generation failed for {user_id}:{input_id}: {str(e)}")


@router.get("/input/{input_id}", response_model=dict)
async def get_keywords_for_input(
    input_id: str,
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Get generated keywords for a specific user input.
    """
    try:
        logger.info(f"Retrieving keywords for input {input_id} (user: {current_user.id})")
        
        keywords = await KeywordGenerationService.get_keywords_by_input_id(
            user_id=current_user.id,
            input_id=input_id
        )
        
        if not keywords:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Keywords not found for this input"
            )
        
        # Check if processing is stuck
        is_processing = await processing_lock_service.is_processing(current_user.id, input_id)
        if keywords.get("generation_status") == "processing" and not is_processing:
            # Keyword generation appears stuck
            keywords["generation_status"] = "failed"
            keywords["error_message"] = "Processing appears to have stalled"
        
        logger.info(f"Successfully retrieved keywords for input {input_id}")
        return keywords
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving keywords for input {input_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve keywords: {str(e)}"
        )


@router.get("/", response_model=List[dict])
async def get_user_keywords(
    current_user: UserResponse = Depends(get_current_user),
    limit: int = Query(50, ge=1, le=100, description="Maximum number of records to return"),
    skip: int = Query(0, ge=0, description="Number of records to skip for pagination")
):
    """
    Get all generated keywords for the authenticated user.
    
    Supports pagination.
    """
    try:
        logger.info(f"Retrieving keywords for user {current_user.id} (limit: {limit}, skip: {skip})")
        
        keywords_list = await KeywordGenerationService.get_user_keywords(
            user_id=current_user.id,
            limit=limit,
            skip=skip
        )
        
        logger.info(f"Retrieved {len(keywords_list)} keyword records for user {current_user.id}")
        return keywords_list
        
    except Exception as e:
        logger.error(f"Error retrieving keywords for user {current_user.id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve keywords: {str(e)}"
        )


@router.get("/summary", response_model=List[KeywordSummary])
async def get_keywords_summary(
    current_user: UserResponse = Depends(get_current_user),
    limit: int = Query(20, ge=1, le=50, description="Maximum number of records to return")
):
    """
    Get a summary of generated keywords for the authenticated user.
    
    Returns condensed information about keyword generation status and counts.
    """
    try:
        logger.info(f"Retrieving keywords summary for user {current_user.id}")
        
        keywords_list = await KeywordGenerationService.get_user_keywords(
            user_id=current_user.id,
            limit=limit,
            skip=0
        )
        
        # Convert to summary format
        summaries = []
        for keywords in keywords_list:
            summary = KeywordSummary(
                keywords_id=keywords["keywords_id"],
                input_id=keywords["input_id"],
                generation_status=keywords["generation_status"],
                subreddit_count=len(keywords.get("potential_subreddits", [])),
                anchor_count=len(keywords.get("domain_anchors", [])),
                phrase_count=len(keywords.get("problem_phrases", [])),
                created_at=keywords["created_at"],
                domain=keywords.get("domain"),
                search_text_used=keywords.get("search_text_used", "")
            )
            summaries.append(summary)
        
        logger.info(f"Retrieved {len(summaries)} keyword summaries for user {current_user.id}")
        return summaries
        
    except Exception as e:
        logger.error(f"Error retrieving keywords summary for user {current_user.id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve keywords summary: {str(e)}"
        )


@router.delete("/input/{input_id}")
async def delete_keywords_for_input(
    input_id: str,
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Delete generated keywords for a specific user input.
    """
    try:
        logger.info(f"Deleting keywords for input {input_id} (user: {current_user.id})")
        
        success = await KeywordGenerationService.delete_keywords(
            user_id=current_user.id,
            input_id=input_id
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Keywords not found for this input"
            )
        
        logger.info(f"Successfully deleted keywords for input {input_id}")
        return {"success": True, "message": "Keywords deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting keywords for input {input_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete keywords: {str(e)}"
        )


@router.post("/auto-generate/{input_id}", response_model=KeywordGenerationResponse)
async def auto_generate_keywords_for_input(
    input_id: str,
    background_tasks: BackgroundTasks,
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Automatically generate keywords for a user input (convenience endpoint).
    
    This is a simpler endpoint that doesn't require a request body.
    """
    try:
        # Create a request object
        request = KeywordGenerationRequest(input_id=input_id, force_regenerate=False)
        
        # Use the main generate_keywords function
        return await generate_keywords(request, background_tasks, current_user)
        
    except Exception as e:
        logger.error(f"Error in auto-generate endpoint for input {input_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to auto-generate keywords: {str(e)}"
        )


@router.get("/processing-status/{input_id}")
async def get_keyword_generation_status(
    input_id: str,
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Get the current status of keyword generation for a specific input.
    """
    try:
        # Check processing lock status
        is_processing = await processing_lock_service.is_processing(current_user.id, input_id)
        current_stage = await processing_lock_service.get_current_stage(current_user.id, input_id)
        
        # Get keywords data
        keywords = await KeywordGenerationService.get_keywords_by_input_id(
            user_id=current_user.id,
            input_id=input_id
        )
        
        return {
            "input_id": input_id,
            "is_processing": is_processing,
            "current_stage": current_stage.value if current_stage else None,
            "keywords_exists": keywords is not None,
            "generation_status": keywords.get("generation_status") if keywords else None,
            "has_error": keywords.get("error_message") if keywords else None
        }
        
    except Exception as e:
        logger.error(f"Error getting keyword generation status for {input_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get keyword generation status: {str(e)}"
        )