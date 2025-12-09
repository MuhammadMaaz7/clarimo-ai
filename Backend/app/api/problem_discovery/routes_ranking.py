"""
Ranking API Routes
"""
from fastapi import APIRouter, HTTPException, status, Depends
from typing import Dict, Any
import logging

from app.core.security import get_current_user
from app.db.models.user_model import UserResponse
from app.services.problem_discovery.ranking_service import ranking_service
from app.services.shared.processing_lock_manager import processing_lock_service, ProcessingStage

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ranking", tags=["Ranking"])


@router.post("/rank/{input_id}")
async def rank_pain_points(
    input_id: str,
    current_user: UserResponse = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Rank pain points for a specific input ID
    """
    try:
        logger.info(f"Manual ranking request for input {input_id} by user {current_user.id}")
        
        # Check if processing is already in progress
        is_processing = await processing_lock_service.is_processing(current_user.id, input_id)
        if is_processing:
            current_stage = await processing_lock_service.get_current_stage(current_user.id, input_id)
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Processing already in progress. Current stage: {current_stage.value if current_stage else 'unknown'}"
            )
        
        result = await ranking_service.rank_pain_points(
            user_id=current_user.id,
            input_id=input_id
        )
        
        if not result["success"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result["message"]
            )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in manual ranking for input {input_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ranking failed: {str(e)}"
        )


@router.get("/results/{input_id}")
async def get_ranking_results(
    input_id: str,
    current_user: UserResponse = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get ranking results for a specific input ID
    """
    try:
        from pathlib import Path
        import json
        
        ranking_path = Path("data/rankings") / current_user.id / input_id / "ranked_pain_points.json"
        
        if not ranking_path.exists():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Ranking results not found"
            )
        
        with open(ranking_path, "r", encoding="utf-8") as f:
            ranking_data = json.load(f)
        
        return {
            "success": True,
            "input_id": input_id,
            "ranked_pain_points": ranking_data.get("ranked_pain_points", []),
            "ranking_metadata": ranking_data.get("ranking_metadata", {}),
            "total_pain_points": len(ranking_data.get("ranked_pain_points", []))
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving ranking results for input {input_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve ranking results: {str(e)}"
        )


@router.get("/list")
async def list_ranking_results(
    current_user: UserResponse = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    List all ranking results for the authenticated user
    """
    try:
        from pathlib import Path
        import json
        from datetime import datetime
        
        user_rankings_dir = Path("data/rankings") / current_user.id
        
        if not user_rankings_dir.exists():
            return {
                "success": True,
                "ranking_results": [],
                "total_results": 0
            }
        
        ranking_results = []
        
        for input_dir in user_rankings_dir.iterdir():
            if not input_dir.is_dir():
                continue
                
            ranking_path = input_dir / "ranked_pain_points.json"
            
            if ranking_path.exists():
                try:
                    with open(ranking_path, 'r', encoding='utf-8') as f:
                        ranking_data = json.load(f)
                    
                    ranking_metadata = ranking_data.get("ranking_metadata", {})
                    
                    ranking_results.append({
                        "input_id": input_dir.name,
                        "total_pain_points": len(ranking_data.get("ranked_pain_points", [])),
                        "ranked_at": ranking_metadata.get("ranked_at", 
                            datetime.fromtimestamp(ranking_path.stat().st_ctime).isoformat()
                        ),
                        "weights_used": ranking_metadata.get("weights_used", {}),
                        "include_optional": ranking_metadata.get("include_optional", False),
                        "model_used": ranking_metadata.get("model_used", "Unknown"),
                        "file_path": str(ranking_path)
                    })
                except Exception as e:
                    logger.warning(f"Error reading ranking results for {input_dir}: {str(e)}")
                    continue
        
        # Sort by ranked_at date, most recent first
        ranking_results.sort(key=lambda x: x["ranked_at"], reverse=True)
        
        return {
            "success": True,
            "ranking_results": ranking_results,
            "total_results": len(ranking_results)
        }
        
    except Exception as e:
        logger.error(f"Error listing ranking results: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list ranking results: {str(e)}"
        )


@router.get("/status/{input_id}")
async def get_ranking_status(
    input_id: str,
    current_user: UserResponse = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get the current ranking status for a specific input ID
    """
    try:
        from pathlib import Path
        
        # Check processing lock status
        is_processing = await processing_lock_service.is_processing(current_user.id, input_id)
        current_stage = await processing_lock_service.get_current_stage(current_user.id, input_id)
        
        # Check if ranking results exist
        ranking_path = Path("data/rankings") / current_user.id / input_id / "ranked_pain_points.json"
        has_results = ranking_path.exists()
        
        ranking_info = None
        if has_results:
            try:
                import json
                with open(ranking_path, "r", encoding="utf-8") as f:
                    ranking_data = json.load(f)
                    ranking_metadata = ranking_data.get("ranking_metadata", {})
                    
                    ranking_info = {
                        "total_pain_points": len(ranking_data.get("ranked_pain_points", [])),
                        "ranked_at": ranking_metadata.get("ranked_at", ""),
                        "weights_used": ranking_metadata.get("weights_used", {}),
                        "include_optional": ranking_metadata.get("include_optional", False),
                        "model_used": ranking_metadata.get("model_used", "Unknown")
                    }
            except Exception as e:
                logger.warning(f"Error reading ranking info: {e}")
        
        return {
            "input_id": input_id,
            "is_processing": is_processing,
            "current_stage": current_stage.value if current_stage else None,
            "is_ranking_stage": current_stage == ProcessingStage.RANKING if current_stage else False,
            "has_results": has_results,
            "ranking_info": ranking_info
        }
        
    except Exception as e:
        logger.error(f"Error getting ranking status for input {input_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get ranking status: {str(e)}"
        )


@router.delete("/results/{input_id}")
async def delete_ranking_results(
    input_id: str,
    current_user: UserResponse = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Delete ranking results for a specific input ID
    """
    try:
        from pathlib import Path
        import shutil
        
        ranking_dir = Path("data/rankings") / current_user.id / input_id
        
        if not ranking_dir.exists():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Ranking results not found"
            )
        
        # Remove the entire ranking directory
        shutil.rmtree(ranking_dir)
        
        logger.info(f"Deleted ranking results for input {input_id} (user: {current_user.id})")
        
        return {
            "success": True,
            "message": f"Ranking results for input {input_id} deleted successfully",
            "deleted_directory": str(ranking_dir)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting ranking results for input {input_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete ranking results: {str(e)}"
        )