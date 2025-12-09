"""
API routes for shared validations (public access, no authentication required)
"""

from fastapi import APIRouter, HTTPException, status
from typing import Optional
from app.services.idea_validation.validation_lifecycle_manager import ValidationLifecycleManager
from app.core.logging import logger

router = APIRouter(prefix="/shared/validations", tags=["Shared Validations"])


@router.get("/{share_id}")
async def get_shared_validation(
    share_id: str,
    password: Optional[str] = None
):
    """
    Access a shared validation via share link
    
    This endpoint allows public access to validation reports that have been
    shared by their owners. No authentication is required.
    
    Privacy levels:
    - **public**: Anyone with the link can view
    - **password_protected**: Requires password parameter
    - **private**: Access denied
    
    The endpoint tracks access count and enforces expiration dates.
    
    - **share_id**: Unique share ID from the share link
    - **password**: Optional password for password-protected links
    
    Requirements: 15.5
    Subtask: 16.4
    """
    try:
        # Get validation service
        validation_service = ValidationLifecycleManager()
        
        # Get shared validation
        validation_data = await validation_service.get_shared_validation(
            share_id=share_id,
            password=password
        )
        
        if not validation_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Shared validation not found"
            )
        
        return validation_data
        
    except ValueError as e:
        # Handle specific errors (expired, password required, etc.)
        error_message = str(e)
        
        if "expired" in error_message.lower():
            raise HTTPException(
                status_code=status.HTTP_410_GONE,
                detail=error_message
            )
        elif "password" in error_message.lower():
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=error_message
            )
        elif "private" in error_message.lower() or "deactivated" in error_message.lower():
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=error_message
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_message
            )
    except Exception as e:
        logger.error(f"Failed to get shared validation: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve shared validation"
        )


@router.get("/{share_id}/export/json")
async def export_shared_validation_json(
    share_id: str,
    password: Optional[str] = None
):
    """
    Export shared validation as JSON
    
    Returns the complete validation data in JSON format for a shared validation.
    Same access rules apply as the main shared validation endpoint.
    
    - **share_id**: Unique share ID from the share link
    - **password**: Optional password for password-protected links
    
    Requirements: 15.5
    Subtask: 16.4
    """
    try:
        # Get validation service
        validation_service = ValidationLifecycleManager()
        
        # Get shared validation (this already returns JSON format)
        validation_data = await validation_service.get_shared_validation(
            share_id=share_id,
            password=password
        )
        
        if not validation_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Shared validation not found"
            )
        
        return validation_data
        
    except ValueError as e:
        error_message = str(e)
        
        if "expired" in error_message.lower():
            raise HTTPException(
                status_code=status.HTTP_410_GONE,
                detail=error_message
            )
        elif "password" in error_message.lower():
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=error_message
            )
        elif "private" in error_message.lower() or "deactivated" in error_message.lower():
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=error_message
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_message
            )
    except Exception as e:
        logger.error(f"Failed to export shared validation: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to export shared validation"
        )


@router.get("/{share_id}/export/pdf")
async def export_shared_validation_pdf(
    share_id: str,
    password: Optional[str] = None
):
    """
    Export shared validation as PDF
    
    Generates a PDF report for a shared validation.
    Same access rules apply as the main shared validation endpoint.
    
    - **share_id**: Unique share ID from the share link
    - **password**: Optional password for password-protected links
    
    Requirements: 15.5
    Subtask: 16.4
    """
    from fastapi.responses import Response
    from app.services.idea_validation.pdf_report_exporter import PDFReportExporter
    
    try:
        # Get validation service
        validation_service = ValidationLifecycleManager()
        
        # Get shared validation data
        validation_data = await validation_service.get_shared_validation(
            share_id=share_id,
            password=password
        )
        
        if not validation_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Shared validation not found"
            )
        
        # Generate PDF
        pdf_service = PDFReportExporter()
        pdf_bytes = pdf_service.generate_validation_pdf(validation_data)
        
        # Generate filename
        idea_title = validation_data.get("idea", {}).get("title", "idea")
        safe_title = "".join(c for c in idea_title if c.isalnum() or c in (' ', '-', '_')).strip()
        safe_title = safe_title.replace(' ', '_')[:50]
        filename = f"validation_report_{safe_title}_{share_id[:8]}.pdf"
        
        # Return PDF response
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"'
            }
        )
        
    except ValueError as e:
        error_message = str(e)
        
        if "expired" in error_message.lower():
            raise HTTPException(
                status_code=status.HTTP_410_GONE,
                detail=error_message
            )
        elif "password" in error_message.lower():
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=error_message
            )
        elif "private" in error_message.lower() or "deactivated" in error_message.lower():
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=error_message
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_message
            )
    except Exception as e:
        logger.error(f"Failed to export shared validation as PDF: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to export shared validation as PDF"
        )
