from fastapi import APIRouter, HTTPException, status, Depends
from datetime import datetime, timezone
import uuid
from typing import List
import logging

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
    Stores the request in the database and returns mock problem data for frontend testing.
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
                        queries_per_domain=10,  # Increased: More search queries
                        per_query_limit=100,    # Increased: More posts per query
                        per_subreddit_limit=100 # Increased: More posts per subreddit
                    )
                    
                    # Save Reddit data to JSON file
                    file_path = await reddit_fetching_service.save_reddit_data_to_file(
                        reddit_data=reddit_data,
                        user_id=current_user.id,
                        input_id=input_response.input_id
                    )
                    
                    logger.info(f"Successfully fetched and saved {reddit_data['total_posts']} Reddit posts to {file_path}")
                    
                    # Automatically generate embeddings from Reddit data
                    if reddit_data['total_posts'] > 0:  # Only if we have posts
                        try:
                            logger.info(f"Starting embedding generation for input {input_response.input_id}")
                            embedding_result = await embedding_service.generate_embeddings_for_reddit_data(
                                user_id=current_user.id,
                                input_id=input_response.input_id,
                                reddit_json_path=file_path,
                                use_gpu=False,  # Use CPU for simplicity
                                batch_size=32   # Smaller batch size for CPU
                            )
                            
                            if embedding_result["success"]:
                                logger.info(f"Successfully generated embeddings for {embedding_result.get('documents_processed', 0)} documents for input {input_response.input_id}")
                                
                                # Automatically run semantic filtering after successful embedding generation
                                try:
                                    logger.info(f"Starting semantic filtering for input {input_response.input_id}")
                                    filtering_result = await semantic_filtering_service.semantic_filter_posts(
                                        user_id=current_user.id,
                                        input_id=input_response.input_id,
                                        query=request.problemDescription,  # Use original user query
                                        top_k=500,  # Get top 500 candidates
                                        similarity_threshold=0.55  # Keep posts with similarity >= 0.55
                                    )
                                    
                                    if filtering_result["success"]:
                                        logger.info(f"Successfully filtered {filtering_result.get('filtered_documents', 0)} relevant posts from {filtering_result.get('total_documents', 0)} total for input {input_response.input_id}")
                                    else:
                                        logger.warning(f"Semantic filtering failed for input {input_response.input_id}: {filtering_result.get('message')}")
                                        
                                except Exception as filtering_error:
                                    logger.error(f"Error in semantic filtering for input {input_response.input_id}: {str(filtering_error)}")
                                    # Don't fail the main request if filtering fails
                                
                            else:
                                logger.warning(f"Embedding generation failed for input {input_response.input_id}: {embedding_result.get('message')}")
                                
                        except Exception as embedding_error:
                            logger.error(f"Error generating embeddings for input {input_response.input_id}: {str(embedding_error)}")
                            # Don't fail the main request if embedding generation fails
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
        
        # For now, return mock data to test the frontend
        mock_problems = [
            DiscoveredProblem(
                id=1,
                title="Small businesses struggle with managing customer relationships",
                description="Many small businesses lack affordable CRM solutions that are easy to use and integrate with their existing tools. They often resort to spreadsheets which become unwieldy.",
                source="r/smallbusiness",
                score=247,
                relevance_score=0.85,
                tags=["CRM", "small business", "customer management"]
            ),
            DiscoveredProblem(
                id=2,
                title="Remote teams face coordination challenges",
                description="With the rise of remote work, teams struggle to maintain effective communication and coordination across different time zones and tools.",
                source="r/remotework",
                score=189,
                relevance_score=0.78,
                tags=["remote work", "team coordination", "communication"]
            ),
            DiscoveredProblem(
                id=3,
                title="Freelancers waste time on invoicing and payments",
                description="Independent contractors spend countless hours creating invoices, tracking payments, and following up with clients instead of doing billable work.",
                source="r/freelance",
                score=156,
                relevance_score=0.72,
                tags=["freelancing", "invoicing", "payments", "time management"]
            )
        ]
        
        # Update status to completed after processing
        await UserInputService.update_input_status(
            user_id=current_user.id,
            input_id=input_response.input_id,
            status="completed"
        )
        
        logger.info(f"Successfully processed problem discovery request {request_id}")
        
        return ProblemDiscoveryResponse(
            success=True,
            message=f"Problem discovery request received and processed. Found {len(mock_problems)} related problems.",
            request_id=request_id,
            timestamp=timestamp,
            data={
                "problems": [problem.dict() for problem in mock_problems],
                "total_found": len(mock_problems),
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