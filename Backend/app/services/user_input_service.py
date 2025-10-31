"""
User Input Service for database operations
"""
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from bson import ObjectId
import uuid

from app.db.database import user_inputs_collection
from app.db.models.input_model import UserInputDB, UserInputRequest, UserInputResponse


class UserInputService:
    """Service for managing user input data in the database"""
    
    @staticmethod
    async def create_user_input(
        user_id: str, 
        input_data: UserInputRequest
    ) -> UserInputResponse:
        """
        Create a new user input record in the database
        
        Args:
            user_id: ID of the authenticated user
            input_data: Validated user input data
            
        Returns:
            UserInputResponse with success status and created input details
            
        Raises:
            Exception: If database operation fails
        """
        try:
            # Generate unique input ID
            input_id = str(uuid.uuid4())
            current_time = datetime.now(timezone.utc)
            
            # Create database document
            user_input_doc = {
                "user_id": user_id,
                "input_id": input_id,
                "problem_description": input_data.problem_description,
                "domain": input_data.domain,
                "region": input_data.region,
                "target_audience": input_data.target_audience,
                "status": "received",
                "current_stage": "received",  # Track current processing stage
                "created_at": current_time,
                "updated_at": current_time,
                "processing_started_at": None,  # When processing actually starts
                "completed_at": None,  # When processing completes
                "error_message": None,  # Store any error messages
                "results": None  # Store final pain points results
            }
            
            # Insert into database
            result = user_inputs_collection.insert_one(user_input_doc)
            
            if not result.inserted_id:
                raise Exception("Failed to insert user input into database")
            
            return UserInputResponse(
                success=True,
                input_id=input_id,
                message="User input successfully stored",
                created_at=current_time
            )
            
        except Exception as e:
            raise Exception(f"Database error while creating user input: {str(e)}")
    
    @staticmethod
    async def get_user_input_by_id(user_id: str, input_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve a specific user input by ID
        
        Args:
            user_id: ID of the authenticated user
            input_id: Unique input identifier
            
        Returns:
            User input document or None if not found
        """
        try:
            user_input = user_inputs_collection.find_one({
                "user_id": user_id,
                "input_id": input_id
            })
            
            if user_input:
                # Convert ObjectId to string for JSON serialization
                user_input["_id"] = str(user_input["_id"])
                
            return user_input
            
        except Exception as e:
            raise Exception(f"Database error while retrieving user input: {str(e)}")
    
    @staticmethod
    async def get_user_inputs(
        user_id: str, 
        limit: int = 50, 
        skip: int = 0,
        status: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Retrieve user inputs for a specific user
        
        Args:
            user_id: ID of the authenticated user
            limit: Maximum number of records to return
            skip: Number of records to skip (for pagination)
            status: Optional status filter
            
        Returns:
            List of user input documents
        """
        try:
            query = {"user_id": user_id}
            
            if status:
                query["status"] = status
            
            cursor = user_inputs_collection.find(query).sort("created_at", -1).skip(skip).limit(limit)
            
            user_inputs = []
            for doc in cursor:
                # Convert ObjectId to string for JSON serialization
                doc["_id"] = str(doc["_id"])
                user_inputs.append(doc)
            
            return user_inputs
            
        except Exception as e:
            raise Exception(f"Database error while retrieving user inputs: {str(e)}")
    
    @staticmethod
    async def update_input_status(
        user_id: str, 
        input_id: str, 
        status: str, 
        current_stage: Optional[str] = None,
        error_message: Optional[str] = None
    ) -> bool:
        """
        Update the status and stage of a user input
        
        Args:
            user_id: ID of the authenticated user
            input_id: Unique input identifier
            status: New status value
            current_stage: Current processing stage
            error_message: Optional error message
            
        Returns:
            True if update was successful, False otherwise
        """
        try:
            update_data = {
                "status": status,
                "updated_at": datetime.now(timezone.utc)
            }
            
            if current_stage:
                update_data["current_stage"] = current_stage
            
            if error_message:
                update_data["error_message"] = error_message
            
            # Set processing start time when first moving to processing status
            if status == "processing":
                update_data["processing_started_at"] = datetime.now(timezone.utc)
            
            # Set completion time when moving to completed status
            if status == "completed":
                update_data["completed_at"] = datetime.now(timezone.utc)
            
            result = user_inputs_collection.update_one(
                {
                    "user_id": user_id,
                    "input_id": input_id
                },
                {
                    "$set": update_data
                }
            )
            
            return result.modified_count > 0
            
        except Exception as e:
            raise Exception(f"Database error while updating user input status: {str(e)}")
    
    @staticmethod
    async def update_processing_stage(
        user_id: str, 
        input_id: str, 
        current_stage: str
    ) -> bool:
        """
        Update only the current processing stage
        
        Args:
            user_id: ID of the authenticated user
            input_id: Unique input identifier
            current_stage: Current processing stage
            
        Returns:
            True if update was successful, False otherwise
        """
        try:
            result = user_inputs_collection.update_one(
                {
                    "user_id": user_id,
                    "input_id": input_id
                },
                {
                    "$set": {
                        "current_stage": current_stage,
                        "updated_at": datetime.now(timezone.utc)
                    }
                }
            )
            
            return result.modified_count > 0
            
        except Exception as e:
            raise Exception(f"Database error while updating processing stage: {str(e)}")
    
    @staticmethod
    async def store_processing_results(
        user_id: str, 
        input_id: str, 
        results: Dict[str, Any]
    ) -> bool:
        """
        Store the final processing results
        
        Args:
            user_id: ID of the authenticated user
            input_id: Unique input identifier
            results: Processing results (pain points, clusters, etc.)
            
        Returns:
            True if update was successful, False otherwise
        """
        try:
            result = user_inputs_collection.update_one(
                {
                    "user_id": user_id,
                    "input_id": input_id
                },
                {
                    "$set": {
                        "results": results,
                        "updated_at": datetime.now(timezone.utc)
                    }
                }
            )
            
            return result.modified_count > 0
            
        except Exception as e:
            raise Exception(f"Database error while storing processing results: {str(e)}")
    
    @staticmethod
    async def delete_user_input(user_id: str, input_id: str) -> bool:
        """
        Delete a user input record
        
        Args:
            user_id: ID of the authenticated user
            input_id: Unique input identifier
            
        Returns:
            True if deletion was successful, False otherwise
        """
        try:
            result = user_inputs_collection.delete_one({
                "user_id": user_id,
                "input_id": input_id
            })
            
            return result.deleted_count > 0
            
        except Exception as e:
            raise Exception(f"Database error while deleting user input: {str(e)}")
    
    @staticmethod
    async def get_input_count_by_user(user_id: str, status: Optional[str] = None) -> int:
        """
        Get count of user inputs for a specific user
        
        Args:
            user_id: ID of the authenticated user
            status: Optional status filter
            
        Returns:
            Count of matching user inputs
        """
        try:
            query = {"user_id": user_id}
            
            if status:
                query["status"] = status
            
            return user_inputs_collection.count_documents(query)
            
        except Exception as e:
            raise Exception(f"Database error while counting user inputs: {str(e)}")