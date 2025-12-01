"""
Module 1 Integration Service
Retrieves and processes pain point data from Module 1 (Problem Discovery)
"""

import json
import os
from typing import List, Optional, Dict, Any
from pathlib import Path
from app.db.models.pain_points_model import PainPoint, PostReference
from app.core.logging import logger


class Module1IntegrationService:
    """Service for integrating with Module 1 pain point data"""
    
    # Base path for pain points data
    PAIN_POINTS_BASE_PATH = Path("data/pain_points")
    
    # Cache for pain point data to improve performance
    _cache: Dict[str, PainPoint] = {}
    
    @staticmethod
    def _get_pain_point_file_path(user_id: str, input_id: str, cluster_id: str) -> Optional[Path]:
        """
        Construct the file path for a pain point cluster
        
        Args:
            user_id: User ID
            input_id: Input ID from Module 1
            cluster_id: Cluster ID
            
        Returns:
            Path to the pain point JSON file, or None if not found
        """
        # Try the individual cluster file first
        cluster_file = Module1IntegrationService.PAIN_POINTS_BASE_PATH / user_id / input_id / f"pain_point_cluster_{cluster_id}.json"
        
        if cluster_file.exists():
            return cluster_file
        
        # Try the all pain points file
        all_file = Module1IntegrationService.PAIN_POINTS_BASE_PATH / user_id / input_id / "marketable_pain_points_all.json"
        
        if all_file.exists():
            return all_file
        
        return None
    
    @staticmethod
    def get_pain_point_by_id(pain_point_id: str) -> Optional[PainPoint]:
        """
        Retrieve a pain point by its ID
        
        Pain point ID format: {user_id}:{input_id}:{cluster_id}
        
        Args:
            pain_point_id: Composite pain point ID
            
        Returns:
            PainPoint object if found, None otherwise
        """
        # Check cache first
        if pain_point_id in Module1IntegrationService._cache:
            return Module1IntegrationService._cache[pain_point_id]
        
        try:
            # Parse pain point ID
            parts = pain_point_id.split(":")
            if len(parts) != 3:
                logger.warning(f"Invalid pain point ID format: {pain_point_id}")
                return None
            
            user_id, input_id, cluster_id = parts
            
            # Get file path
            file_path = Module1IntegrationService._get_pain_point_file_path(user_id, input_id, cluster_id)
            
            if not file_path:
                logger.warning(f"Pain point file not found for ID: {pain_point_id}")
                return None
            
            # Load and parse the file
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Handle both individual cluster files and all pain points file
            if isinstance(data, list):
                # All pain points file - find the specific cluster
                for pp_data in data:
                    if pp_data.get("cluster_id") == cluster_id:
                        pain_point = Module1IntegrationService._parse_pain_point(pp_data)
                        if pain_point:
                            Module1IntegrationService._cache[pain_point_id] = pain_point
                            return pain_point
            else:
                # Individual cluster file
                pain_point = Module1IntegrationService._parse_pain_point(data)
                if pain_point:
                    Module1IntegrationService._cache[pain_point_id] = pain_point
                    return pain_point
            
            return None
            
        except Exception as e:
            logger.error(f"Error loading pain point {pain_point_id}: {str(e)}")
            return None
    
    @staticmethod
    def get_pain_points_by_ids(pain_point_ids: List[str]) -> List[PainPoint]:
        """
        Retrieve multiple pain points by their IDs
        
        Args:
            pain_point_ids: List of pain point IDs
            
        Returns:
            List of PainPoint objects (excludes not found items)
        """
        pain_points = []
        
        for pain_point_id in pain_point_ids:
            pain_point = Module1IntegrationService.get_pain_point_by_id(pain_point_id)
            if pain_point:
                pain_points.append(pain_point)
            else:
                logger.warning(f"Pain point not found: {pain_point_id}")
        
        return pain_points
    
    @staticmethod
    def _parse_pain_point(data: Dict[str, Any]) -> Optional[PainPoint]:
        """
        Parse pain point data from JSON
        
        Args:
            data: Raw pain point data dictionary
            
        Returns:
            PainPoint object or None if parsing fails
        """
        try:
            # Parse post references
            post_references = []
            for post_ref in data.get("post_references", []):
                post_references.append(PostReference(
                    post_id=post_ref.get("post_id", ""),
                    subreddit=post_ref.get("subreddit", ""),
                    created_utc=post_ref.get("created_utc", ""),
                    url=post_ref.get("url", ""),
                    text=post_ref.get("text", ""),
                    title=post_ref.get("title"),
                    score=post_ref.get("score"),
                    num_comments=post_ref.get("num_comments")
                ))
            
            # Create PainPoint object
            pain_point = PainPoint(
                cluster_id=data.get("cluster_id", ""),
                problem_title=data.get("problem_title", ""),
                problem_description=data.get("problem_description", ""),
                post_references=post_references,
                analysis_timestamp=data.get("analysis_timestamp", 0.0),
                source=data.get("source", "reddit_cluster_analysis")
            )
            
            return pain_point
            
        except Exception as e:
            logger.error(f"Error parsing pain point data: {str(e)}")
            return None
    
    @staticmethod
    def get_all_pain_points_for_input(user_id: str, input_id: str) -> List[PainPoint]:
        """
        Get all pain points for a specific input
        
        Args:
            user_id: User ID
            input_id: Input ID from Module 1
            
        Returns:
            List of all pain points for the input
        """
        try:
            all_file = Module1IntegrationService.PAIN_POINTS_BASE_PATH / user_id / input_id / "marketable_pain_points_all.json"
            
            if not all_file.exists():
                logger.warning(f"Pain points file not found for user {user_id}, input {input_id}")
                return []
            
            with open(all_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            pain_points = []
            for pp_data in data:
                pain_point = Module1IntegrationService._parse_pain_point(pp_data)
                if pain_point:
                    pain_points.append(pain_point)
            
            return pain_points
            
        except Exception as e:
            logger.error(f"Error loading all pain points for input {input_id}: {str(e)}")
            return []
    
    @staticmethod
    def clear_cache():
        """Clear the pain point cache"""
        Module1IntegrationService._cache.clear()
    
    @staticmethod
    def validate_pain_point_ids(pain_point_ids: List[str]) -> Dict[str, bool]:
        """
        Validate that pain point IDs exist
        
        Args:
            pain_point_ids: List of pain point IDs to validate
            
        Returns:
            Dictionary mapping pain point ID to existence status
        """
        validation_results = {}
        
        for pain_point_id in pain_point_ids:
            pain_point = Module1IntegrationService.get_pain_point_by_id(pain_point_id)
            validation_results[pain_point_id] = pain_point is not None
        
        return validation_results
