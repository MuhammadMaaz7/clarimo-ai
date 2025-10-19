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
                "user_id": user_id,  # Keep as string since users use UUID format
                "input_id": input_id,
                "problem_description": input_data.problem_description,
                "domain": input_data.domain,
                "region": input_data.region,
                "target_audience": input_data.target_audience,
                "status": "received",
                "created_at": current_time,
                "updated_at": current_time
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
                "user_id": user_id,  # user_id is already a string
                "input_id": input_id
            })
            
            if user_input:
                # Convert ObjectId to string for JSON serialization
                user_input["_id"] = str(user_input["_id"])
                # user_id is already a string, no conversion needed
                
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
            query = {"user_id": user_id}  # user_id is already a string
            
            if status:
                query["status"] = status
            
            cursor = user_inputs_collection.find(query).sort("created_at", -1).skip(skip).limit(limit)
            
            user_inputs = []
            for doc in cursor:
                # Convert ObjectId to string for JSON serialization
                doc["_id"] = str(doc["_id"])
                # user_id is already a string, no conversion needed
                user_inputs.append(doc)
            
            return user_inputs
            
        except Exception as e:
            raise Exception(f"Database error while retrieving user inputs: {str(e)}")
    
    @staticmethod
    async def update_input_status(user_id: str, input_id: str, status: str) -> bool:
        """
        Update the status of a user input
        
        Args:
            user_id: ID of the authenticated user
            input_id: Unique input identifier
            status: New status value
            
        Returns:
            True if update was successful, False otherwise
        """
        try:
            result = user_inputs_collection.update_one(
                {
                    "user_id": user_id,  # user_id is already a string
                    "input_id": input_id
                },
                {
                    "$set": {
                        "status": status,
                        "updated_at": datetime.now(timezone.utc)
                    }
                }
            )
            
            return result.modified_count > 0
            
        except Exception as e:
            raise Exception(f"Database error while updating user input status: {str(e)}")
    
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
                "user_id": user_id,  # user_id is already a string
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
            query = {"user_id": user_id}  # user_id is already a string
            
            if status:
                query["status"] = status
            
            return user_inputs_collection.count_documents(query)
            
        except Exception as e:
            raise Exception(f"Database error while counting user inputs: {str(e)}")