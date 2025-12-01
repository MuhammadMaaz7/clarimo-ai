"""
API routes for Idea Validation
"""

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from typing import Optional
from app.db.models.validation_result_model import (
    ValidationResultCreate,
    ValidationResultResponse,
    ValidationConfig,
    ValidationStatus
)
from app.services.module2_validation.validation_service import ValidationService
from app.core.dependencies import get_current_user
from app.core.logging import logger

router = APIRouter(prefix="/validations", tags=["Validations"])


@router.post("/validate", response_model=ValidationResultResponse, status_code=status.HTTP_202_ACCEPTED)
async def validate_idea(
    validation_request: ValidationResultCreate,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user)
):
    """
    Start validation for an idea
    
    This endpoint initiates the validation process and returns immediately with a validation ID.
    The validation runs in the background, and you can check its status using the status endpoint.
    
    - **idea_id**: ID of the idea to validate
    - **config**: Optional validation configuration
    
    Returns:
        ValidationResultResponse with status IN_PROGRESS and validation_id
    """
    try:
        user_id = current_user.id
        
        # If user_id is provided in request, verify it matches the authenticated user
        if validation_request.user_id and validation_request.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only validate your own ideas"
            )
        
        # Create validation service
        validation_service = ValidationService()
        
        # Start validation (creates validation record and queues background task)
        validation_result = await validation_service.start_validation(
            idea_id=validation_request.idea_id,
            user_id=user_id,
            config=validation_request.config or ValidationConfig(),
            background_tasks=background_tasks
        )
        
        return validation_result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to start validation: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start validation: {str(e)}"
        )


@router.get("/{validation_id}", response_model=ValidationResultResponse)
async def get_validation_result(
    validation_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Get validation result by ID
    
    Returns the complete validation result including all scores, justifications,
    and recommendations. If validation is still in progress, returns current status.
    
    - **validation_id**: Unique validation ID
    """
    try:
        user_id = current_user.id
        
        # Get validation service
        validation_service = ValidationService()
        
        # Get validation result
        validation_result = await validation_service.get_validation_result(
            validation_id=validation_id,
            user_id=user_id
        )
        
        if not validation_result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Validation not found"
            )
        
        return validation_result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get validation result: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get validation result: {str(e)}"
        )


@router.get("/status/{validation_id}", response_model=dict)
async def get_validation_status(
    validation_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Get validation status
    
    Returns a lightweight status check for a validation. Use this endpoint
    to poll for completion status without fetching the full result.
    
    - **validation_id**: Unique validation ID
    
    Returns:
        Dictionary with status, progress, and estimated completion time
    """
    try:
        user_id = current_user.id
        
        # Get validation service
        validation_service = ValidationService()
        
        # Get validation status
        status_info = await validation_service.get_validation_status(
            validation_id=validation_id,
            user_id=user_id
        )
        
        if not status_info:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Validation not found"
            )
        
        return status_info
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get validation status: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get validation status: {str(e)}"
        )


@router.get("/idea/{idea_id}/history", response_model=list)
async def get_validation_history(
    idea_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Get validation history for an idea
    
    Returns all validation results for a specific idea, ordered by date (newest first).
    
    - **idea_id**: ID of the idea
    """
    try:
        user_id = current_user.id
        
        # Get validation service
        validation_service = ValidationService()
        
        # Get validation history
        history = await validation_service.get_validation_history(
            idea_id=idea_id,
            user_id=user_id
        )
        
        return history
        
    except Exception as e:
        logger.error(f"Failed to get validation history: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get validation history: {str(e)}"
        )


@router.get("/compare")
async def compare_validations(
    validation_ids: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Compare multiple validation results side-by-side
    
    Accepts multiple validation IDs and returns a comparison showing:
    - All metrics side-by-side for each idea
    - Winner identification for each metric
    - Overall recommendation
    
    - **validation_ids**: Comma-separated list of validation IDs (e.g., "id1,id2,id3")
    
    Requirements: 12.1, 12.2, 12.3, 12.4
    """
    try:
        user_id = current_user.id
        
        # Parse validation IDs
        validation_id_list = [vid.strip() for vid in validation_ids.split(",")]
        
        if len(validation_id_list) < 2:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="At least 2 validation IDs are required for comparison"
            )
        
        if len(validation_id_list) > 10:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Maximum 10 validations can be compared at once"
            )
        
        # Get validation service
        validation_service = ValidationService()
        
        # Compare validations
        comparison = await validation_service.compare_validations(
            validation_ids=validation_id_list,
            user_id=user_id
        )
        
        return comparison
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to compare validations: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to compare validations: {str(e)}"
        )


@router.get("/compare-versions")
async def compare_validation_versions(
    validation_id_1: str,
    validation_id_2: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Compare two validation versions of the same idea
    
    Calculates score deltas between two validation runs and identifies:
    - Which metrics improved (score increased)
    - Which metrics declined (score decreased)
    - Which metrics stayed the same
    - Overall score delta
    
    - **validation_id_1**: First validation ID (typically older)
    - **validation_id_2**: Second validation ID (typically newer)
    
    Requirements: 13.3, 13.4
    """
    try:
        user_id = current_user.id
        
        # Get validation service
        validation_service = ValidationService()
        
        # Compare versions
        comparison = await validation_service.compare_validation_versions(
            validation_id_1=validation_id_1,
            validation_id_2=validation_id_2,
            user_id=user_id
        )
        
        return comparison
        
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Failed to compare validation versions: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to compare validation versions: {str(e)}"
        )


@router.get("/{validation_id}/export/json")
async def export_validation_json(
    validation_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Export validation result as JSON
    
    Returns the complete validation data including all scores, justifications,
    recommendations, and metadata in JSON format. This export contains all
    information from the validation report and can be used for:
    - Archiving validation results
    - Importing into other systems
    - Programmatic analysis
    - Sharing with stakeholders
    
    - **validation_id**: Unique validation ID
    
    Requirements: 15.2, 15.3
    Subtask: 16.1
    """
    try:
        user_id = current_user.id
        
        # Get validation service
        validation_service = ValidationService()
        
        # Export validation as JSON
        export_data = await validation_service.export_validation_json(
            validation_id=validation_id,
            user_id=user_id
        )
        
        if not export_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Validation not found"
            )
        
        return export_data
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to export validation as JSON: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to export validation: {str(e)}"
        )


@router.get("/{validation_id}/export/pdf")
async def export_validation_pdf(
    validation_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Export validation result as PDF
    
    Generates a comprehensive PDF report including:
    - Executive summary
    - Overall validation score
    - Visual charts (radar chart, bar chart)
    - Detailed metric scores with justifications
    - Strengths and weaknesses analysis
    - Critical recommendations
    - Complete idea details
    
    The PDF is suitable for:
    - Presenting to stakeholders
    - Sharing with co-founders or investors
    - Archiving validation results
    - Offline review
    
    - **validation_id**: Unique validation ID
    
    Requirements: 15.1, 15.3
    Subtask: 16.3
    """
    from fastapi.responses import Response
    from app.services.module2_validation.pdf_export_service import PDFExportService
    
    try:
        user_id = current_user.id
        
        # Get validation service
        validation_service = ValidationService()
        
        # Get validation export data
        export_data = await validation_service.export_validation_json(
            validation_id=validation_id,
            user_id=user_id
        )
        
        if not export_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Validation not found"
            )
        
        # Generate PDF
        pdf_service = PDFExportService()
        pdf_bytes = pdf_service.generate_validation_pdf(export_data)
        
        # Generate filename
        idea_title = export_data.get("idea", {}).get("title", "idea")
        # Sanitize filename
        safe_title = "".join(c for c in idea_title if c.isalnum() or c in (' ', '-', '_')).strip()
        safe_title = safe_title.replace(' ', '_')[:50]  # Limit length
        filename = f"validation_report_{safe_title}_{validation_id[:8]}.pdf"
        
        # Return PDF response
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"'
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to export validation as PDF: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to export validation as PDF: {str(e)}"
        )


@router.post("/{validation_id}/share")
async def create_share_link(
    validation_id: str,
    share_request: dict,
    current_user: dict = Depends(get_current_user)
):
    """
    Create a shareable link for a validation result
    
    Generates a unique shareable link that allows others to view the validation
    report without requiring authentication. Supports different privacy levels:
    
    - **public**: Anyone with the link can view
    - **private**: Only the owner can view (share link disabled)
    - **password_protected**: Requires password to view
    
    Optional expiration date can be set to automatically disable the link.
    
    - **validation_id**: Unique validation ID
    - **privacy_level**: Privacy level (public/private/password_protected)
    - **password**: Optional password for password-protected links
    - **expires_at**: Optional expiration date (ISO format)
    
    Requirements: 15.5
    Subtask: 16.4
    """
    try:
        user_id = current_user.id
        
        # Parse request
        privacy_level = share_request.get("privacy_level", "public")
        password = share_request.get("password")
        expires_at_str = share_request.get("expires_at")
        
        # Parse expiration date
        expires_at = None
        if expires_at_str:
            try:
                expires_at = datetime.fromisoformat(expires_at_str.replace('Z', '+00:00'))
            except:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid expires_at format. Use ISO format (e.g., 2024-12-31T23:59:59Z)"
                )
        
        # Validate privacy level
        if privacy_level not in ["public", "private", "password_protected"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid privacy_level. Must be: public, private, or password_protected"
            )
        
        # Validate password for password-protected links
        if privacy_level == "password_protected" and not password:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Password required for password-protected links"
            )
        
        if password and len(password) < 6:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Password must be at least 6 characters"
            )
        
        # Get validation service
        validation_service = ValidationService()
        
        # Create share link
        share_link = await validation_service.create_share_link(
            validation_id=validation_id,
            user_id=user_id,
            privacy_level=privacy_level,
            password=password,
            expires_at=expires_at
        )
        
        return share_link
        
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Failed to create share link: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create share link: {str(e)}"
        )


@router.get("/{validation_id}/shares")
async def list_share_links(
    validation_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    List all share links for a validation
    
    Returns all shareable links created for this validation, including:
    - Share ID and URL
    - Privacy level
    - Creation and expiration dates
    - Active status
    - Access count
    
    - **validation_id**: Unique validation ID
    
    Requirements: 15.5
    Subtask: 16.4
    """
    try:
        user_id = current_user.id
        
        # Get validation service
        validation_service = ValidationService()
        
        # List share links
        share_links = await validation_service.list_share_links(
            validation_id=validation_id,
            user_id=user_id
        )
        
        return {"share_links": share_links}
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Failed to list share links: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list share links: {str(e)}"
        )


@router.delete("/shares/{share_id}")
async def revoke_share_link(
    share_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Revoke a share link
    
    Deactivates a shareable link, preventing further access. The link will
    return an error if accessed after revocation.
    
    - **share_id**: Share ID to revoke
    
    Requirements: 15.5
    Subtask: 16.4
    """
    try:
        user_id = current_user.id
        
        # Get validation service
        validation_service = ValidationService()
        
        # Revoke share link
        revoked = await validation_service.revoke_share_link(
            share_id=share_id,
            user_id=user_id
        )
        
        if not revoked:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Share link not found or already revoked"
            )
        
        return {"message": "Share link revoked successfully", "share_id": share_id}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to revoke share link: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to revoke share link: {str(e)}"
        )
