"""
Pain Points Database Service

Handles database operations for pain points storage and retrieval.
"""

import json
from datetime import datetime
from typing import List, Optional, Dict, Any
from pymongo.collection import Collection
from app.db.database import db
from app.db.models.pain_points_model import PainPointsAnalysis, PainPointsHistoryItem, PainPoint, PostReference
from app.core.logging import logger

class PainPointsDBService:
    """Service for pain points database operations"""
    
    def __init__(self):
        self.db = db
        self.collection: Collection = self.db.pain_points_analyses
        
        # Create indexes for better performance
        self.collection.create_index([("user_id", 1), ("created_at", -1)])
        self.collection.create_index([("user_id", 1), ("input_id", 1)], unique=True)
    
    async def save_pain_points_analysis(
        self, 
        user_id: str, 
        input_id: str, 
        original_query: str,
        pain_points_data: Dict[str, Any]
    ) -> bool:
        """
        Save pain points analysis to database
        
        Args:
            user_id: User ID
            input_id: Input ID
            original_query: Original user query/problem description
            pain_points_data: Pain points data from service
            
        Returns:
            bool: Success status
        """
        try:
            # Convert pain points data to database model
            pain_points = []
            for pp_data in pain_points_data.get("pain_points", []):
                # Convert post references
                post_refs = []
                for ref in pp_data.get("post_references", []):
                    post_refs.append(PostReference(**ref))
                
                # Create pain point
                pain_point = PainPoint(
                    cluster_id=pp_data["cluster_id"],
                    problem_title=pp_data["problem_title"],
                    problem_description=pp_data["problem_description"],
                    post_references=post_refs,
                    analysis_timestamp=pp_data["analysis_timestamp"],
                    source=pp_data.get("source", "reddit_cluster_analysis")
                )
                pain_points.append(pain_point)
            
            # Create analysis document
            analysis = PainPointsAnalysis(
                user_id=user_id,
                input_id=input_id,
                original_query=original_query,
                total_clusters=pain_points_data.get("metadata", {}).get("total_clusters", 0),
                pain_points_count=len(pain_points),
                pain_points=pain_points,
                analysis_timestamp=datetime.fromtimestamp(
                    pain_points_data.get("metadata", {}).get("analysis_timestamp", datetime.utcnow().timestamp())
                )
            )
            
            # Save to database (upsert to handle duplicates)
            result = self.collection.replace_one(
                {"user_id": user_id, "input_id": input_id},
                analysis.dict(),
                upsert=True
            )
            
            logger.info(f"Saved pain points analysis to database: user={user_id}, input={input_id}, pain_points={len(pain_points)}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving pain points analysis to database: {str(e)}")
            return False
    
    async def get_pain_points_analysis(self, user_id: str, input_id: str) -> Optional[Dict[str, Any]]:
        """
        Get pain points analysis from database
        
        Args:
            user_id: User ID
            input_id: Input ID
            
        Returns:
            Pain points analysis data or None
        """
        try:
            result = self.collection.find_one({"user_id": user_id, "input_id": input_id})
            if result:
                # Remove MongoDB _id field
                result.pop("_id", None)
                return result
            return None
            
        except Exception as e:
            logger.error(f"Error getting pain points analysis from database: {str(e)}")
            return None
    
    async def get_user_pain_points_history(self, user_id: str, limit: int = 50) -> List[PainPointsHistoryItem]:
        """
        Get user's pain points history
        
        Args:
            user_id: User ID
            limit: Maximum number of items to return
            
        Returns:
            List of pain points history items
        """
        try:
            cursor = self.collection.find(
                {"user_id": user_id},
                {
                    "input_id": 1,
                    "original_query": 1,
                    "pain_points_count": 1,
                    "total_clusters": 1,
                    "analysis_timestamp": 1,
                    "created_at": 1
                }
            ).sort("created_at", -1).limit(limit)
            
            history_items = []
            for doc in cursor:
                history_items.append(PainPointsHistoryItem(
                    input_id=doc["input_id"],
                    original_query=doc["original_query"],
                    pain_points_count=doc["pain_points_count"],
                    total_clusters=doc["total_clusters"],
                    analysis_timestamp=doc["analysis_timestamp"],
                    created_at=doc["created_at"]
                ))
            
            return history_items
            
        except Exception as e:
            logger.error(f"Error getting user pain points history: {str(e)}")
            return []
    
    async def delete_pain_points_analysis(self, user_id: str, input_id: str) -> bool:
        """
        Delete pain points analysis from database
        
        Args:
            user_id: User ID
            input_id: Input ID
            
        Returns:
            bool: Success status
        """
        try:
            result = self.collection.delete_one({"user_id": user_id, "input_id": input_id})
            logger.info(f"Deleted pain points analysis from database: user={user_id}, input={input_id}")
            return result.deleted_count > 0
            
        except Exception as e:
            logger.error(f"Error deleting pain points analysis from database: {str(e)}")
            return False
    
    async def get_user_stats(self, user_id: str) -> Dict[str, Any]:
        """
        Get user statistics
        
        Args:
            user_id: User ID
            
        Returns:
            User statistics
        """
        try:
            pipeline = [
                {"$match": {"user_id": user_id}},
                {"$group": {
                    "_id": None,
                    "total_analyses": {"$sum": 1},
                    "total_pain_points": {"$sum": "$pain_points_count"},
                    "total_clusters": {"$sum": "$total_clusters"},
                    "latest_analysis": {"$max": "$created_at"}
                }}
            ]
            
            result = list(self.collection.aggregate(pipeline))
            if result:
                stats = result[0]
                return {
                    "total_analyses": stats.get("total_analyses", 0),
                    "total_pain_points": stats.get("total_pain_points", 0),
                    "total_clusters": stats.get("total_clusters", 0),
                    "latest_analysis": stats.get("latest_analysis")
                }
            else:
                return {
                    "total_analyses": 0,
                    "total_pain_points": 0,
                    "total_clusters": 0,
                    "latest_analysis": None
                }
                
        except Exception as e:
            logger.error(f"Error getting user stats: {str(e)}")
            return {
                "total_analyses": 0,
                "total_pain_points": 0,
                "total_clusters": 0,
                "latest_analysis": None
            }

# Global service instance
pain_points_db_service = PainPointsDBService()