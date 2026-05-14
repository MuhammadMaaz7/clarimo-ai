"""
Debug API routes for troubleshooting validation display issues
"""

from fastapi import APIRouter, Depends, HTTPException, status
from typing import Dict, Any
from app.db.database import ideas_collection, validation_results_collection
from app.core.dependencies import get_current_user
from app.core.logging import logger

router = APIRouter(prefix="/debug", tags=["Debug"])


@router.get("/validation-linkage/{idea_id}")
async def debug_validation_linkage(
    idea_id: str,
    current_user: dict = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Debug endpoint to check validation linkage for a specific idea
    
    Returns detailed information about:
    - Idea document in database
    - Latest validation document
    - Linkage status
    - Potential issues
    """
    user_id = current_user.id
    
    # Fetch idea from database
    idea_doc = ideas_collection.find_one({
        "id": idea_id,
        "user_id": user_id
    })
    
    if not idea_doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Idea {idea_id} not found"
        )
    
    # Remove MongoDB _id for JSON serialization
    idea_doc.pop("_id", None)
    
    # Fetch latest validation if linked
    latest_validation_id = idea_doc.get("latest_validation_id")
    latest_validation_doc = None
    validation_exists = False
    
    if latest_validation_id:
        latest_validation_doc = validation_results_collection.find_one({
            "validation_id": latest_validation_id
        })
        
        if latest_validation_doc:
            validation_exists = True
            latest_validation_doc.pop("_id", None)
    
    # Find all validations for this idea
    all_validations = list(validation_results_collection.find({
        "idea_id": idea_id,
        "user_id": user_id
    }).sort("created_at", -1))
    
    for v in all_validations:
        v.pop("_id", None)
    
    # Analyze issues
    issues = []
    
    if idea_doc.get("validation_count", 0) == 0 and len(all_validations) > 0:
        issues.append(f"validation_count is 0 but {len(all_validations)} validations exist")
    
    if idea_doc.get("validation_count", 0) != len(all_validations):
        issues.append(
            f"validation_count ({idea_doc.get('validation_count', 0)}) "
            f"doesn't match actual count ({len(all_validations)})"
        )
    
    if latest_validation_id and not validation_exists:
        issues.append(f"latest_validation_id points to non-existent validation {latest_validation_id}")
    
    if len(all_validations) > 0 and not latest_validation_id:
        issues.append(f"Idea has {len(all_validations)} validations but no latest_validation_id")
    
    if latest_validation_doc:
        if latest_validation_doc.get("status") != "completed":
            issues.append(f"Latest validation status is '{latest_validation_doc.get('status')}', not 'completed'")
        
        if latest_validation_doc.get("overall_score") is None:
            issues.append("Latest validation has no overall_score")
    
    # Build response
    response = {
        "idea": {
            "id": idea_doc.get("id"),
            "title": idea_doc.get("title"),
            "validation_count": idea_doc.get("validation_count", 0),
            "latest_validation_id": latest_validation_id,
            "created_at": idea_doc.get("created_at").isoformat() if idea_doc.get("created_at") else None,
            "updated_at": idea_doc.get("updated_at").isoformat() if idea_doc.get("updated_at") else None,
        },
        "latest_validation": {
            "exists": validation_exists,
            "validation_id": latest_validation_doc.get("validation_id") if latest_validation_doc else None,
            "status": latest_validation_doc.get("status") if latest_validation_doc else None,
            "overall_score": latest_validation_doc.get("overall_score") if latest_validation_doc else None,
            "created_at": latest_validation_doc.get("created_at").isoformat() if latest_validation_doc and latest_validation_doc.get("created_at") else None,
            "completed_at": latest_validation_doc.get("completed_at").isoformat() if latest_validation_doc and latest_validation_doc.get("completed_at") else None,
        } if latest_validation_doc else None,
        "all_validations_count": len(all_validations),
        "all_validations": [
            {
                "validation_id": v.get("validation_id"),
                "status": v.get("status"),
                "overall_score": v.get("overall_score"),
                "created_at": v.get("created_at").isoformat() if v.get("created_at") else None,
            }
            for v in all_validations
        ],
        "issues": issues,
        "is_healthy": len(issues) == 0,
    }
    
    logger.info(f"Debug validation linkage for idea {idea_id}: {len(issues)} issues found")
    
    return response


@router.get("/all-ideas-linkage")
async def debug_all_ideas_linkage(
    current_user: dict = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Debug endpoint to check validation linkage for all user's ideas
    
    Returns summary of linkage health across all ideas
    """
    user_id = current_user.id
    
    # Fetch all ideas
    ideas = list(ideas_collection.find({"user_id": user_id}))
    
    total_ideas = len(ideas)
    ideas_with_validations = 0
    ideas_with_issues = 0
    all_issues = []
    
    for idea in ideas:
        idea_id = idea.get("id")
        title = idea.get("title")
        
        # Count validations
        validations_count = validation_results_collection.count_documents({
            "idea_id": idea_id,
            "user_id": user_id,
            "status": "completed"
        })
        
        if validations_count > 0:
            ideas_with_validations += 1
        
        # Check for issues
        idea_issues = []
        
        if idea.get("validation_count", 0) != validations_count:
            idea_issues.append(
                f"validation_count mismatch: stored={idea.get('validation_count', 0)}, actual={validations_count}"
            )
        
        if validations_count > 0 and not idea.get("latest_validation_id"):
            idea_issues.append("Has validations but no latest_validation_id")
        
        if idea_issues:
            ideas_with_issues += 1
            all_issues.append({
                "idea_id": idea_id,
                "title": title,
                "issues": idea_issues
            })
    
    return {
        "total_ideas": total_ideas,
        "ideas_with_validations": ideas_with_validations,
        "ideas_with_issues": ideas_with_issues,
        "is_healthy": ideas_with_issues == 0,
        "issues": all_issues,
    }
