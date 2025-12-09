"""
Idea Management Service
Handles CRUD operations for startup ideas
"""

import uuid
from datetime import datetime
from typing import List, Optional
from pymongo.errors import DuplicateKeyError
from app.db.database import ideas_collection
from app.db.models.idea_model import (
    IdeaCreate,
    IdeaUpdate,
    IdeaResponse,
    IdeaInDB,
    IdeaFilters
)


class IdeaManager:
    """Service for managing startup ideas"""
    
    @staticmethod
    def create_idea(user_id: str, idea_data: IdeaCreate) -> IdeaResponse:
        """
        Create a new idea
        
        Args:
            user_id: ID of the user creating the idea
            idea_data: Idea creation data
            
        Returns:
            IdeaResponse: Created idea
            
        Raises:
            Exception: If creation fails
        """
        now = datetime.utcnow()
        idea_id = str(uuid.uuid4())
        
        idea_dict = {
            "id": idea_id,
            "user_id": user_id,
            "title": idea_data.title,
            "description": idea_data.description,
            "problem_statement": idea_data.problem_statement,
            "solution_description": idea_data.solution_description,
            "target_market": idea_data.target_market,
            "business_model": idea_data.business_model,
            "team_capabilities": idea_data.team_capabilities,

            "created_at": now,
            "updated_at": now,
            "validation_count": 0,
            "latest_validation_id": None
        }
        
        try:
            ideas_collection.insert_one(idea_dict)
        except DuplicateKeyError:
            raise Exception("Idea with this ID already exists")
        except Exception as e:
            raise Exception(f"Failed to create idea: {str(e)}")
        
        return IdeaResponse(**idea_dict)
    
    @staticmethod
    def _populate_latest_validation(idea: IdeaResponse) -> IdeaResponse:
        """
        Populate latest_validation field for an idea
        
        Args:
            idea: IdeaResponse object
            
        Returns:
            IdeaResponse with latest_validation populated
        """
        from app.db.database import validation_results_collection
        from app.db.models.idea_model import LatestValidationSummary
        
        if idea.latest_validation_id:
            # Fetch the latest validation
            validation = validation_results_collection.find_one({
                "validation_id": idea.latest_validation_id
            })
            
            if validation:
                # Only populate if validation is completed and has results
                status = validation.get("status", "")
                if status == "completed" and validation.get("overall_score") is not None:
                    idea.latest_validation = LatestValidationSummary(
                        validation_id=validation["validation_id"],
                        overall_score=validation.get("overall_score", 0.0),
                        status=validation["status"],
                        created_at=validation["created_at"]
                    )
        
        return idea
    
    @staticmethod
    def get_idea(user_id: str, idea_id: str) -> Optional[IdeaResponse]:
        """
        Get a specific idea by ID
        
        Args:
            user_id: ID of the user requesting the idea
            idea_id: ID of the idea to retrieve
            
        Returns:
            IdeaResponse if found, None otherwise
        """
        idea = ideas_collection.find_one({
            "id": idea_id,
            "user_id": user_id
        })
        
        if not idea:
            return None
        
        # Remove MongoDB _id field
        idea.pop("_id", None)
        
        idea_response = IdeaResponse(**idea)
        return IdeaManager._populate_latest_validation(idea_response)
    
    @staticmethod
    def list_ideas(
        user_id: str,
        filters: Optional[IdeaFilters] = None
    ) -> List[IdeaResponse]:
        """
        List all ideas for a user with optional filtering and sorting
        
        Subtask 15.6: Support sorting by overall_score and individual metrics
        Requirement 12.5
        
        Args:
            user_id: ID of the user
            filters: Optional filters for sorting and filtering
            
        Returns:
            List of IdeaResponse objects
        """
        from app.db.database import validation_results_collection
        
        query = {"user_id": user_id}
        
        # Apply filters
        if filters:
            if filters.has_validation is not None:
                if filters.has_validation:
                    query["validation_count"] = {"$gt": 0}
                else:
                    query["validation_count"] = 0
        
        # Check if sorting by validation scores
        validation_score_metrics = [
            "overall_score",
            "problem_clarity",
            "market_demand",
            "solution_fit",
            "differentiation",
            "technical_feasibility",
            "market_size",
            "monetization_potential",
            "risk_level",
            "user_validation_evidence"
        ]
        
        sort_by_validation_score = (
            filters and 
            filters.sort_by and 
            filters.sort_by in validation_score_metrics
        )
        
        if sort_by_validation_score:
            # Need to join with validation_results to sort by scores
            # Use aggregation pipeline
            sort_order = 1 if filters.sort_order == "asc" else -1
            
            # Build aggregation pipeline
            pipeline = [
                {"$match": query},
                # Lookup latest validation for each idea
                {
                    "$lookup": {
                        "from": "validation_results",
                        "let": {"idea_id": "$id"},
                        "pipeline": [
                            {
                                "$match": {
                                    "$expr": {
                                        "$and": [
                                            {"$eq": ["$idea_id", "$$idea_id"]},
                                            {"$eq": ["$status", "completed"]}
                                        ]
                                    }
                                }
                            },
                            {"$sort": {"created_at": -1}},
                            {"$limit": 1}
                        ],
                        "as": "latest_validation"
                    }
                },
                {"$unwind": {"path": "$latest_validation", "preserveNullOnEmpty": True}}
            ]
            
            # Add sort based on metric
            if filters.sort_by == "overall_score":
                pipeline.append({
                    "$sort": {"latest_validation.overall_score": sort_order}
                })
            else:
                # Sorting by individual metric
                metric_path = f"latest_validation.individual_scores.{filters.sort_by}.value"
                pipeline.append({
                    "$sort": {metric_path: sort_order}
                })
            
            # Apply score range filters if provided
            if filters.min_score is not None or filters.max_score is not None:
                score_filter = {}
                if filters.min_score is not None:
                    score_filter["$gte"] = filters.min_score
                if filters.max_score is not None:
                    score_filter["$lte"] = filters.max_score
                
                if filters.sort_by == "overall_score":
                    pipeline.insert(-1, {
                        "$match": {"latest_validation.overall_score": score_filter}
                    })
                else:
                    metric_path = f"latest_validation.individual_scores.{filters.sort_by}.value"
                    pipeline.insert(-1, {
                        "$match": {metric_path: score_filter}
                    })
            
            # Execute aggregation
            cursor = ideas_collection.aggregate(pipeline)
            
            ideas = []
            for doc in cursor:
                doc.pop("_id", None)
                doc.pop("latest_validation", None)  # Remove joined validation data
                idea_response = IdeaResponse(**doc)
                ideas.append(IdeaManager._populate_latest_validation(idea_response))
            
            return ideas
        else:
            # Standard sorting by idea fields
            sort_field = "created_at"
            sort_order = -1  # descending by default
            
            if filters and filters.sort_by:
                sort_field = filters.sort_by
            
            if filters and filters.sort_order == "asc":
                sort_order = 1
            
            # Execute query
            cursor = ideas_collection.find(query).sort(sort_field, sort_order)
            
            ideas = []
            for idea in cursor:
                idea.pop("_id", None)
                idea_response = IdeaResponse(**idea)
                ideas.append(IdeaManager._populate_latest_validation(idea_response))
            
            return ideas
    
    @staticmethod
    def update_idea(
        user_id: str,
        idea_id: str,
        updates: IdeaUpdate
    ) -> Optional[IdeaResponse]:
        """
        Update an existing idea
        
        Args:
            user_id: ID of the user updating the idea
            idea_id: ID of the idea to update
            updates: Update data
            
        Returns:
            Updated IdeaResponse if successful, None if idea not found
        """
        # Get existing idea
        existing_idea = IdeaManager.get_idea(user_id, idea_id)
        if not existing_idea:
            return None
        
        # Build update dict with only provided fields
        update_dict = updates.dict(exclude_unset=True)
        

        
        if not update_dict:
            # No updates provided
            return existing_idea
        
        # Add updated_at timestamp
        update_dict["updated_at"] = datetime.utcnow()
        
        # Update in database
        result = ideas_collection.update_one(
            {"id": idea_id, "user_id": user_id},
            {"$set": update_dict}
        )
        
        if result.modified_count == 0:
            return None
        
        # Return updated idea
        return IdeaManager.get_idea(user_id, idea_id)
    
    @staticmethod
    def delete_idea(user_id: str, idea_id: str) -> bool:
        """
        Delete an idea and all associated validation results
        
        Args:
            user_id: ID of the user deleting the idea
            idea_id: ID of the idea to delete
            
        Returns:
            True if deleted successfully, False otherwise
        """
        from app.db.database import validation_results_collection
        
        # Delete the idea
        result = ideas_collection.delete_one({
            "id": idea_id,
            "user_id": user_id
        })
        
        if result.deleted_count == 0:
            return False
        
        # Delete associated validation results (cascading delete)
        validation_results_collection.delete_many({
            "idea_id": idea_id,
            "user_id": user_id
        })
        
        return True
    
    @staticmethod
    def link_pain_points(
        user_id: str,
        idea_id: str,
        pain_point_ids: List[str]
    ) -> bool:
        """
        Link pain points from Module 1 to an idea
        
        Args:
            user_id: ID of the user
            idea_id: ID of the idea
            pain_point_ids: List of pain point IDs to link
            
        Returns:
            True if successful, False otherwise
        """
        # Verify idea exists and belongs to user
        existing_idea = IdeaManager.get_idea(user_id, idea_id)
        if not existing_idea:
            return False
        
        # Update linked pain points
        result = ideas_collection.update_one(
            {"id": idea_id, "user_id": user_id},
            {
                "$set": {
                    "linked_pain_points": pain_point_ids,
                    "updated_at": datetime.utcnow()
                }
            }
        )
        
        return result.modified_count > 0
    
    @staticmethod
    def increment_validation_count(
        idea_id: str,
        validation_id: str
    ) -> bool:
        """
        Increment validation count and update latest validation ID
        
        Args:
            idea_id: ID of the idea
            validation_id: ID of the new validation
            
        Returns:
            True if successful, False otherwise
        """
        result = ideas_collection.update_one(
            {"id": idea_id},
            {
                "$inc": {"validation_count": 1},
                "$set": {
                    "latest_validation_id": validation_id,
                    "updated_at": datetime.utcnow()
                }
            }
        )
        
        return result.modified_count > 0
