"""
User Input API Routes
"""
from fastapi import APIRouter, HTTPException, status, Depends, Query, BackgroundTasks
from typing import List, Optional
import logging

from app.db.models.input_model import UserInputRequest, UserInputResponse
from app.db.models.user_model import UserResponse
from app.core.security import get_current_user
from app.services.user_input_service import UserInputService
from app.services.processing_lock_service import processing_lock_service, ProcessingStage

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/user-input", tags=["User Input"])


@router.post("/", response_model=UserInputResponse, status_code=status.HTTP_201_CREATED)
async def create_user_input(
    request: UserInputRequest,
    background_tasks: BackgroundTasks,
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Create a new user input record and start the processing pipeline.
    
    This endpoint accepts user input data, validates it, stores it in the database,
    and starts the background processing pipeline.
    """
    try:
        # Log the incoming request
        logger.info(f"Creating user input for user {current_user.id}: {request.problem_description[:50]}...")
        
        # Create user input in database
        response = await UserInputService.create_user_input(
            user_id=current_user.id,
            input_data=request
        )
        
        # Start background processing
        background_tasks.add_task(
            process_user_input_background,
            current_user.id,
            response.input_id,
            request
        )
        
        logger.info(f"Successfully created user input with ID: {response.input_id} and started processing")
        return response
        
    except Exception as e:
        logger.error(f"Error creating user input for user {current_user.id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to store user input: {str(e)}"
        )


async def process_user_input_background(
    user_id: str, 
    input_id: str, 
    input_data: UserInputRequest
):
    """
    Background task to process user input through the entire pipeline
    """
    try:
        # Acquire processing lock
        lock_acquired = await processing_lock_service.acquire_lock(user_id, input_id)
        if not lock_acquired:
            logger.warning(f"Processing already in progress for {user_id}:{input_id}")
            return
        
        try:
            # Update status to processing
            await UserInputService.update_input_status(
                user_id=user_id,
                input_id=input_id,
                status="processing",
                current_stage=ProcessingStage.KEYWORD_GENERATION.value
            )
            
            logger.info(f"Starting processing pipeline for input {input_id} (user: {user_id})")
            
            # Import required services
            from app.services.keyword_generation_service import KeywordGenerationService
            from app.services.reddit_fetching_service import reddit_fetching_service
            from app.services.embedding_service import embedding_service
            from app.services.semantic_filtering_service import semantic_filtering_service
            from app.services.performance_logger import performance_logger
            from pathlib import Path
            
            # Start performance tracking
            pipeline_metrics = performance_logger.start_pipeline(
                user_id=user_id,
                input_id=input_id,
                problem_description=input_data.problem_description
            )
            
            # Step 1: Generate keywords
            performance_logger.start_stage(input_id, "keyword_generation")
            logger.info(f"Generating keywords for input {input_id}")
            
            keyword_result = await KeywordGenerationService.generate_keywords_for_input(
                user_id=user_id,
                input_id=input_id,
                problem_description=input_data.problem_description,
                domain=input_data.domain
            )
            
            if not keyword_result["success"]:
                error_msg = keyword_result.get('error', 'Unknown error')
                performance_logger.finish_stage(input_id, "keyword_generation", success=False, error_message=error_msg)
                if keyword_result.get("validation_failed"):
                    raise Exception(f"Validation failed: {error_msg}")
                else:
                    raise Exception(f"Keyword generation failed: {error_msg}")
            
            # Extract keyword metrics
            keywords_data = keyword_result.get("data", {})
            keyword_metrics = {
                "subreddits_count": len(keywords_data.get("potential_subreddits", [])),
                "domain_anchors_count": len(keywords_data.get("domain_anchors", [])),
                "problem_phrases_count": len(keywords_data.get("problem_phrases", []))
            }
            
            performance_logger.finish_stage(input_id, "keyword_generation", success=True, **keyword_metrics)
            logger.info(f"Successfully generated keywords for input {input_id}")
            
            # Step 2: Fetch Reddit posts
            performance_logger.start_stage(input_id, "reddit_fetching")
            logger.info(f"Fetching Reddit posts for input {input_id}")
            
            reddit_data = await reddit_fetching_service.fetch_reddit_posts_for_keywords(
                user_id=user_id,
                input_id=input_id,
                keywords_data=keyword_result["data"],
                queries_per_domain=8,
                per_query_limit=75,
                per_subreddit_limit=75
            )
            
            # Save Reddit data
            file_path = await reddit_fetching_service.save_reddit_data_to_file(
                reddit_data=reddit_data,
                user_id=user_id,
                input_id=input_id
            )
            
            total_posts = reddit_data['total_posts']
            logger.info(f"Successfully fetched {total_posts} Reddit posts for input {input_id}")
            
            if total_posts == 0:
                performance_logger.finish_stage(input_id, "reddit_fetching", success=False, 
                                              error_message="No Reddit posts found", total_posts=0)
                raise Exception("No Reddit posts found for the given criteria")
            
            # Reddit metrics
            reddit_metrics = {
                "total_posts": total_posts,
                "posts_from_queries": reddit_data.get('posts_from_queries', 0),
                "posts_from_subreddits": reddit_data.get('posts_from_subreddits', 0),
                "unique_subreddits": len(set(post.get('subreddit', '') for post in reddit_data.get('all_posts', [])))
            }
            
            performance_logger.finish_stage(input_id, "reddit_fetching", success=True, **reddit_metrics)
            
            # Step 3: Generate embeddings
            performance_logger.start_stage(input_id, "embedding_generation")
            logger.info(f"Generating embeddings for input {input_id}")
            
            embedding_result = await embedding_service.generate_embeddings_for_reddit_data(
                user_id=user_id,
                input_id=input_id,
                reddit_json_path=file_path,
                use_gpu=False,
                batch_size=32
            )
            
            if not embedding_result["success"]:
                error_msg = embedding_result.get('message', 'Unknown error')
                performance_logger.finish_stage(input_id, "embedding_generation", success=False, error_message=error_msg)
                raise Exception(f"Embedding generation failed: {error_msg}")
            
            # Embedding metrics
            embedding_metrics = {
                "documents_processed": embedding_result.get("documents_processed", 0),
                "embedding_model": "mixedbread-ai/mxbai-embed-large-v1",
                "batch_size": 32,
                "use_gpu": False
            }
            
            performance_logger.finish_stage(input_id, "embedding_generation", success=True, **embedding_metrics)
            logger.info(f"Successfully generated embeddings for input {input_id}")
            
            # Step 4: Semantic filtering
            performance_logger.start_stage(input_id, "semantic_filtering")
            logger.info(f"Running semantic filtering for input {input_id}")
            
            filtering_result = await semantic_filtering_service.semantic_filter_posts(
                user_id=user_id,
                input_id=input_id,
                query=input_data.problem_description,
                domain=input_data.domain,
                top_k=500,
                similarity_threshold=0.55
            )
            
            if not filtering_result["success"]:
                error_msg = filtering_result.get('message', 'Unknown error')
                performance_logger.finish_stage(input_id, "semantic_filtering", success=False, error_message=error_msg)
                raise Exception(f"Semantic filtering failed: {error_msg}")
            
            filtered_count = filtering_result.get('filtered_documents', 0)
            logger.info(f"Successfully filtered {filtered_count} relevant posts for input {input_id}")
            
            # Filtering metrics
            filtering_metrics = {
                "total_documents": filtering_result.get("total_documents", 0),
                "filtered_documents": filtered_count,
                "similarity_threshold": 0.55,
                "top_k": 500,
                "min_similarity": filtering_result.get("similarity_stats", {}).get("min_similarity", 0),
                "max_similarity": filtering_result.get("similarity_stats", {}).get("max_similarity", 0),
                "avg_similarity": filtering_result.get("similarity_stats", {}).get("avg_similarity", 0)
            }
            
            performance_logger.finish_stage(input_id, "semantic_filtering", success=True, **filtering_metrics)
            
            # Step 5: Clustering (this will also trigger pain points extraction)
            performance_logger.start_stage(input_id, "clustering_and_pain_points")
            logger.info(f"Starting clustering for input {input_id}")
            from app.services.clustering_service import clustering_service
            
            clustering_result = await clustering_service.cluster_filtered_posts(
                user_id=user_id,
                input_id=input_id,
                min_cluster_size=None,
                create_visualization=False,
                original_query=input_data.problem_description
            )
            
            if not clustering_result["success"]:
                error_msg = clustering_result.get('message', 'Unknown error')
                performance_logger.finish_stage(input_id, "clustering_and_pain_points", success=False, error_message=error_msg)
                raise Exception(f"Clustering failed: {error_msg}")
            
            logger.info(f"Successfully completed clustering and pain points extraction for input {input_id}")
            
            # Clustering and pain points metrics
            clustering_metrics = {
                "total_posts_clustered": clustering_result.get("total_posts", 0),
                "clusters_found": clustering_result.get("clusters_found", 0),
                "clustered_posts": clustering_result.get("clustered_posts", 0),
                "noise_posts": clustering_result.get("noise_posts", 0),
                "pain_points_extraction_success": clustering_result.get("pain_points_extraction_success", False)
            }
            
            performance_logger.finish_stage(input_id, "clustering_and_pain_points", success=True, **clustering_metrics)
            
            # Finish pipeline tracking
            performance_logger.finish_pipeline(input_id, success=True)
            
            # Update final status - this will be done by the clustering service
            # No need to update here as clustering service handles completion
            
        except Exception as processing_error:
            # Finish pipeline tracking with failure
            try:
                performance_logger.finish_pipeline(input_id, success=False)
            except Exception:
                pass  # Don't fail on logging errors
            
            # Update status to failed
            await UserInputService.update_input_status(
                user_id=user_id,
                input_id=input_id,
                status="failed",
                current_stage=ProcessingStage.FAILED.value,
                error_message=str(processing_error)
            )
            logger.error(f"Error processing user input {input_id}: {str(processing_error)}")
            raise
            
        finally:
            # Release the lock (clustering service will also release it, but this is a safety net)
            try:
                await processing_lock_service.release_lock(user_id, input_id)
            except Exception as lock_error:
                logger.error(f"Error releasing lock for {user_id}:{input_id}: {str(lock_error)}")
            
    except Exception as e:
        logger.error(f"Background processing failed for {user_id}:{input_id}: {str(e)}")


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
    include_keywords: bool = Query(False, description="Include generated keywords in the response"),
    include_results: bool = Query(True, description="Include processing results in the response")
):
    """
    Retrieve a specific user input by ID.
    
    Only returns inputs that belong to the authenticated user.
    Optionally includes generated keywords and processing results if available.
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
        
        # Check if processing is stuck
        is_processing = await processing_lock_service.is_processing(current_user.id, input_id)
        if user_input.get("status") == "processing" and not is_processing:
            # Process appears stuck, update status
            await UserInputService.update_input_status(
                user_id=current_user.id,
                input_id=input_id,
                status="failed",
                current_stage=ProcessingStage.FAILED.value,
                error_message="Processing appears to have stalled"
            )
            user_input["status"] = "failed"
            user_input["current_stage"] = ProcessingStage.FAILED.value
        
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
        
        # Release any active lock first
        await processing_lock_service.release_lock(current_user.id, input_id)
        
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


@router.get("/{input_id}/processing-status")
async def get_processing_status(
    input_id: str,
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Get detailed processing status for a specific user input.
    """
    try:
        # Get user input
        user_input = await UserInputService.get_user_input_by_id(
            user_id=current_user.id,
            input_id=input_id
        )
        
        if not user_input:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User input not found"
            )
        
        # Get lock service status
        is_processing = await processing_lock_service.is_processing(current_user.id, input_id)
        current_stage = await processing_lock_service.get_current_stage(current_user.id, input_id)
        
        return {
            "input_id": input_id,
            "status": user_input.get("status"),
            "current_stage": user_input.get("current_stage"),
            "is_processing": is_processing,
            "lock_service_stage": current_stage.value if current_stage else None,
            "created_at": user_input.get("created_at"),
            "updated_at": user_input.get("updated_at"),
            "processing_started_at": user_input.get("processing_started_at"),
            "completed_at": user_input.get("completed_at"),
            "error_message": user_input.get("error_message")
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting processing status for {input_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get processing status: {str(e)}"
        )