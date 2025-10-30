from fastapi import APIRouter, HTTPException, status, Depends
from datetime import datetime, timezone
import uuid
import json
from typing import List
import logging
from pathlib import Path

from app.db.models.problem_model import (
    ProblemDiscoveryRequest, 
    ProblemDiscoveryResponse, 
    ProblemDiscoveryResult,
    DiscoveredProblem
)
from app.db.models.user_model import UserResponse
from app.core.security import get_current_user
from app.services.user_input_service import UserInputService
from app.services.keyword_generation_service import KeywordGenerationService
from app.services.reddit_fetching_service import reddit_fetching_service
from app.services.embedding_service import embedding_service
from app.services.semantic_filtering_service import semantic_filtering_service
from app.db.models.input_model import UserInputRequest

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/problems", tags=["Problem Discovery"])

@router.post("/discover", response_model=ProblemDiscoveryResponse)
async def discover_problems(
    request: ProblemDiscoveryRequest,
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Discover problems based on user input.
    Initiates background processing and returns real-time status information.
    """
    try:
        logger.info(f"Processing problem discovery request for user {current_user.id}")
        
        # Convert ProblemDiscoveryRequest to UserInputRequest for database storage
        user_input = UserInputRequest(
            problem_description=request.problemDescription,
            domain=request.domain,
            region=request.region,
            target_audience=request.targetAudience
        )
        
        # Store user input in database
        input_response = await UserInputService.create_user_input(
            user_id=current_user.id,
            input_data=user_input
        )
        
        if not input_response.success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to store user input in database"
            )
        
        # Update status to processing since we're about to process it
        await UserInputService.update_input_status(
            user_id=current_user.id,
            input_id=input_response.input_id,
            status="processing"
        )
        
        # Generate keywords automatically in the background
        keyword_result = None
        try:
            logger.info(f"Generating keywords for problem discovery input {input_response.input_id}")
            keyword_result = await KeywordGenerationService.generate_keywords_for_input(
                user_id=current_user.id,
                input_id=input_response.input_id,
                problem_description=request.problemDescription,
                domain=request.domain
            )
            
            if keyword_result["success"]:
                logger.info(f"Successfully generated keywords for input {input_response.input_id}")
                
                # Automatically fetch Reddit posts based on generated keywords
                try:
                    logger.info(f"Starting Reddit post fetching for input {input_response.input_id}")
                    reddit_data = await reddit_fetching_service.fetch_reddit_posts_for_keywords(
                        user_id=current_user.id,
                        input_id=input_response.input_id,
                        keywords_data=keyword_result["data"],
                        queries_per_domain=8,   # Balanced: Good coverage without excess
                        per_query_limit=75,     # Balanced: Quality over quantity
                        per_subreddit_limit=75  # Balanced: Sufficient diversity
                    )
                    
                    # Save Reddit data to JSON file
                    file_path = await reddit_fetching_service.save_reddit_data_to_file(
                        reddit_data=reddit_data,
                        user_id=current_user.id,
                        input_id=input_response.input_id
                    )
                    
                    logger.info(f"Successfully fetched and saved {reddit_data['total_posts']} Reddit posts to {file_path}")
                    
                    # Import processing lock service
                    from app.services.processing_lock_service import processing_lock_service
                    
                    # Check if embeddings are already being processed or completed
                    embeddings_dir = Path("data/embeddings") / current_user.id / input_response.input_id
                    filtered_dir = Path("data/filtered_posts") / current_user.id / input_response.input_id
                    
                    # Check if already processing
                    is_processing = await processing_lock_service.is_processing(current_user.id, input_response.input_id)
                    
                    if (filtered_dir / "filtered_posts.json").exists():
                        logger.info(f"Semantic filtering already completed for input {input_response.input_id}")
                    elif (embeddings_dir / "faiss_index.bin").exists():
                        logger.info(f"Embeddings already exist for input {input_response.input_id}, running semantic filtering only")
                        # Run only semantic filtering
                        try:
                            filtering_result = await semantic_filtering_service.semantic_filter_posts(
                                user_id=current_user.id,
                                input_id=input_response.input_id,
                                query=request.problemDescription,
                                top_k=500,
                                similarity_threshold=0.55
                            )
                            if filtering_result["success"]:
                                logger.info(f"Successfully filtered {filtering_result.get('filtered_documents', 0)} relevant posts for input {input_response.input_id}")
                        except Exception as e:
                            logger.error(f"Error in semantic filtering for input {input_response.input_id}: {str(e)}")
                    elif is_processing:
                        logger.info(f"Embeddings already being processed for input {input_response.input_id} - skipping duplicate request")
                    elif reddit_data['total_posts'] > 0:  # Only if we have posts and no existing embeddings
                        import asyncio
                        
                        async def background_embedding_task():
                            """Background task for embedding generation and semantic filtering"""
                            # Acquire processing lock
                            lock_acquired = await processing_lock_service.acquire_lock(current_user.id, input_response.input_id)
                            if not lock_acquired:
                                logger.info(f"Could not acquire lock for input {input_response.input_id} - already processing")
                                return
                            
                            try:
                                logger.info(f"Starting background embedding generation for input {input_response.input_id}")
                                embedding_result = await embedding_service.generate_embeddings_for_reddit_data(
                                    user_id=current_user.id,
                                    input_id=input_response.input_id,
                                    reddit_json_path=file_path,
                                    use_gpu=False,  # Use CPU for simplicity
                                    batch_size=128   # Optimized batch size for CPU
                                )
                                
                                if embedding_result["success"]:
                                    logger.info(f"Background: Successfully generated embeddings for {embedding_result.get('documents_processed', 0)} documents for input {input_response.input_id}")
                                    
                                    # Automatically run semantic filtering after successful embedding generation
                                    try:
                                        logger.info(f"Background: Starting semantic filtering for input {input_response.input_id}")
                                        filtering_result = await semantic_filtering_service.semantic_filter_posts(
                                            user_id=current_user.id,
                                            input_id=input_response.input_id,
                                            query=request.problemDescription,  # Use original user query
                                            top_k=500,  # Get top 500 candidates
                                            similarity_threshold=0.55  # Keep posts with similarity >= 0.55
                                        )
                                        
                                        if filtering_result["success"]:
                                            logger.info(f"Background: Successfully filtered {filtering_result.get('filtered_documents', 0)} relevant posts from {filtering_result.get('total_documents', 0)} total for input {input_response.input_id}")
                                        else:
                                            logger.warning(f"Background: Semantic filtering failed for input {input_response.input_id}: {filtering_result.get('message')}")
                                            
                                    except Exception as filtering_error:
                                        logger.error(f"Background: Error in semantic filtering for input {input_response.input_id}: {str(filtering_error)}")
                                    
                                else:
                                    logger.warning(f"Background: Embedding generation failed for input {input_response.input_id}: {embedding_result.get('message')}")
                                    
                            except Exception as embedding_error:
                                logger.error(f"Background: Error generating embeddings for input {input_response.input_id}: {str(embedding_error)}")
                            finally:
                                # Lock will be released by clustering service after complete pipeline
                                pass
                        
                        # Start background task without waiting
                        background_task = asyncio.create_task(background_embedding_task())
                        logger.info(f"Started background embedding generation for input {input_response.input_id} - user can continue without waiting")
                    else:
                        logger.info(f"Skipping embedding generation - no posts fetched for input {input_response.input_id}")
                    
                except Exception as reddit_error:
                    logger.error(f"Error fetching Reddit posts for input {input_response.input_id}: {str(reddit_error)}")
                    # Don't fail the main request if Reddit fetching fails
                
            else:
                logger.warning(f"Failed to generate keywords for input {input_response.input_id}: {keyword_result.get('error')}")
        except Exception as keyword_error:
            logger.error(f"Error generating keywords for input {input_response.input_id}: {str(keyword_error)}")
            # Don't fail the main request if keyword generation fails
        
        # Generate unique request ID for this discovery session
        request_id = input_response.input_id  # Use the same ID for consistency
        timestamp = input_response.created_at
        
        # Determine processing status based on what was completed
        reddit_posts_count = 0
        reddit_fetch_status = "failed"
        embedding_status = "skipped"
        
        # Check if Reddit fetching was successful
        if keyword_result and keyword_result.get("success"):
            try:
                # Try to get reddit_data from the processing above
                if 'reddit_data' in locals() and reddit_data.get('total_posts', 0) > 0:
                    reddit_posts_count = reddit_data['total_posts']
                    reddit_fetch_status = "completed"
                    embedding_status = "in_progress"
            except Exception:
                pass
        
        # Update status to processing since background tasks may be running
        await UserInputService.update_input_status(
            user_id=current_user.id,
            input_id=input_response.input_id,
            status="processing"
        )
        
        logger.info(f"Successfully initiated problem discovery request {request_id}")
        
        return ProblemDiscoveryResponse(
            success=True,
            message="🚀 Problem discovery initiated! Your AI assistant is getting to work...",
            request_id=request_id,
            timestamp=timestamp,
            data={
                "status": "processing",
                "current_stage": "keyword_generation" if not keyword_result else ("reddit_fetch" if reddit_posts_count == 0 else "embedding_generation"),
                "progress_percentage": 10 if not keyword_result else (25 if reddit_posts_count == 0 else 40),
                "interactive_message": "🔑 Generating smart keywords..." if not keyword_result else ("📡 Searching Reddit communities..." if reddit_posts_count == 0 else "🧠 AI analysis starting..."),
                "animation": "startup",
                "processing_stages": {
                    "keyword_generation": {
                        "status": "completed" if keyword_result and keyword_result.get("success") else "in_progress",
                        "message": "✅ Keywords generated" if keyword_result and keyword_result.get("success") else "🔑 Generating keywords...",
                        "icon": "🔑"
                    },
                    "reddit_fetch": {
                        "status": reddit_fetch_status,
                        "message": f"✅ {reddit_posts_count} posts found" if reddit_posts_count > 0 else "📡 Searching communities...",
                        "icon": "📡"
                    },
                    "embedding_generation": {
                        "status": embedding_status,
                        "message": "⏳ Waiting for posts" if reddit_posts_count == 0 else "🧠 AI analysis queued...",
                        "icon": "🧠"
                    },
                    "semantic_filtering": {
                        "status": "pending",
                        "message": "⏳ Waiting for analysis",
                        "icon": "🎯"
                    }
                },
                "reddit_posts_found": reddit_posts_count,
                "estimated_completion_time": "10-15 minutes" if reddit_posts_count > 0 else "Processing...",
                "status_check_url": f"/processing-status/{request_id}",
                "next_steps": [
                    "✨ Check back in a few minutes for progress updates",
                    "📊 Use the status endpoint to track real-time progress", 
                    "🎯 Results will be available once processing completes"
                ],
                "search_parameters": request.dict()
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing problem discovery request for user {current_user.id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing problem discovery request: {str(e)}"
        )

@router.get("/requests", response_model=List[dict])
async def get_user_requests(
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Get all problem discovery requests for the current user from the database.
    """
    try:
        logger.info(f"Retrieving problem discovery requests for user {current_user.id}")
        
        # Get user inputs from database
        user_inputs = await UserInputService.get_user_inputs(
            user_id=current_user.id,
            limit=100  # Get more records for this endpoint
        )
        
        # Convert to the expected format for backward compatibility
        user_requests = []
        for input_data in user_inputs:
            request_record = {
                "request_id": input_data["input_id"],
                "user_id": current_user.id,
                "user_email": current_user.email,
                "timestamp": input_data["created_at"].isoformat() if isinstance(input_data["created_at"], datetime) else input_data["created_at"],
                "problem_description": input_data["problem_description"],
                "domain": input_data.get("domain"),
                "region": input_data.get("region"),
                "target_audience": input_data.get("target_audience"),
                "status": input_data["status"],
                "processed": input_data["status"] in ["completed", "failed"]
            }
            user_requests.append(request_record)
        
        logger.info(f"Retrieved {len(user_requests)} requests for user {current_user.id}")
        return user_requests
        
    except Exception as e:
        logger.error(f"Error retrieving requests for user {current_user.id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving requests: {str(e)}"
        )

@router.get("/requests/{request_id}")
async def get_request_details(
    request_id: str,
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Get details of a specific problem discovery request from the database.
    """
    try:
        logger.info(f"Retrieving request details for {request_id} for user {current_user.id}")
        
        # Get user input from database
        input_data = await UserInputService.get_user_input_by_id(
            user_id=current_user.id,
            input_id=request_id
        )
        
        if not input_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Request not found"
            )
        
        # Convert to the expected format for backward compatibility
        request_data = {
            "request_id": input_data["input_id"],
            "user_id": current_user.id,
            "user_email": current_user.email,
            "timestamp": input_data["created_at"].isoformat() if isinstance(input_data["created_at"], datetime) else input_data["created_at"],
            "problem_description": input_data["problem_description"],
            "domain": input_data.get("domain"),
            "region": input_data.get("region"),
            "target_audience": input_data.get("target_audience"),
            "status": input_data["status"],
            "processed": input_data["status"] in ["completed", "failed"]
        }
        
        logger.info(f"Successfully retrieved request details for {request_id}")
        return request_data
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving request details for {request_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving request details: {str(e)}"
        )

@router.get("/results/{request_id}")
async def get_problem_results(
    request_id: str,
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Get the actual problem discovery results once processing is complete.
    """
    try:
        logger.info(f"Getting results for request {request_id} for user {current_user.id}")
        
        # Check if filtered results exist
        filtered_dir = Path("data/filtered_posts") / current_user.id / request_id
        filtered_file = filtered_dir / "filtered_posts.json"
        
        if not filtered_file.exists():
            # Check processing status
            embeddings_dir = Path("data/embeddings") / current_user.id / request_id
            if (embeddings_dir / "faiss_index.bin").exists():
                return {
                    "success": False,
                    "message": "Results not ready yet. Semantic filtering in progress.",
                    "status": "filtering_posts"
                }
            else:
                return {
                    "success": False,
                    "message": "Results not ready yet. Embedding generation in progress.",
                    "status": "generating_embeddings"
                }
        
        # Load and return the filtered results
        with open(filtered_file, 'r', encoding='utf-8') as f:
            filtered_posts = json.load(f)
        
        # Convert to the expected format
        problems = []
        for idx, post in enumerate(filtered_posts[:50]):  # Limit to top 50 results
            problem = DiscoveredProblem(
                id=idx + 1,
                title=post.get("text", "")[:100] + "..." if len(post.get("text", "")) > 100 else post.get("text", ""),
                description=post.get("text", ""),
                source=f"r/{post.get('subreddit', 'unknown')}",
                score=post.get("score", 0),
                relevance_score=post.get("similarity_score", 0.0),
                tags=[post.get("subreddit", "unknown")]
            )
            problems.append(problem)
        
        logger.info(f"Successfully retrieved {len(problems)} results for request {request_id}")
        
        return ProblemDiscoveryResponse(
            success=True,
            message=f"Found {len(problems)} relevant problems from {len(filtered_posts)} total filtered posts.",
            request_id=request_id,
            timestamp=datetime.now(timezone.utc),
            data={
                "problems": [problem.dict() for problem in problems],
                "total_found": len(filtered_posts),
                "showing": len(problems),
                "status": "completed"
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting results for request {request_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting results: {str(e)}"
        )

@router.delete("/requests/{request_id}")
async def delete_request(
    request_id: str,
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Delete a problem discovery request from the database.
    """
    try:
        logger.info(f"Deleting request {request_id} for user {current_user.id}")
        
        # Delete user input from database
        success = await UserInputService.delete_user_input(
            user_id=current_user.id,
            input_id=request_id
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Request not found"
            )
        
        logger.info(f"Successfully deleted request {request_id}")
        return {"success": True, "message": "Request deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting request {request_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting request: {str(e)}"
        )