"""
Global Error Handler Middleware
Ensures users never see technical API errors or LLM failures
Transforms all errors into user-friendly messages
"""

from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
import logging
from typing import Union

logger = logging.getLogger(__name__)


class ErrorHandler:
    """
    Middleware to handle all errors gracefully
    Never exposes technical details to users
    """
    
    @staticmethod
    def get_user_friendly_message(error: Exception, status_code: int) -> str:
        """
        Convert technical errors to user-friendly messages
        """
        error_str = str(error).lower()
        
        # Network/API errors
        if any(keyword in error_str for keyword in ['connection', 'timeout', 'network', 'unreachable']):
            return "Unable to connect to external services. Please try again."
        
        # LLM API errors
        if any(keyword in error_str for keyword in ['groq', 'openrouter', 'api key', 'rate limit']):
            return "Analysis service temporarily unavailable. Using backup analysis method."
        
        # Database errors
        if any(keyword in error_str for keyword in ['database', 'mongodb', 'connection pool']):
            return "Database temporarily unavailable. Please try again in a moment."
        
        # Validation errors
        if status_code == 422:
            return "Invalid input data. Please check your information and try again."
        
        # Authentication errors
        if status_code == 401:
            return "Authentication required. Please log in."
        
        # Authorization errors
        if status_code == 403:
            return "You don't have permission to access this resource."
        
        # Not found errors
        if status_code == 404:
            return "The requested resource was not found."
        
        # Server errors
        if status_code >= 500:
            return "An error occurred while processing your request. Please try again."
        
        # Default message
        return "An unexpected error occurred. Please try again."
    
    @staticmethod
    async def handle_exception(request: Request, exc: Exception) -> JSONResponse:
        """
        Handle any exception and return user-friendly response
        """
        # Log the actual error for debugging
        logger.error(f"Error handling request {request.url}: {str(exc)}", exc_info=True)
        
        # Determine status code
        if isinstance(exc, StarletteHTTPException):
            status_code = exc.status_code
            detail = exc.detail
        elif isinstance(exc, RequestValidationError):
            status_code = status.HTTP_422_UNPROCESSABLE_ENTITY
            detail = "Invalid input data"
        else:
            status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
            detail = str(exc)
        
        # Get user-friendly message
        user_message = ErrorHandler.get_user_friendly_message(exc, status_code)
        
        # Return clean response
        return JSONResponse(
            status_code=status_code,
            content={
                "success": False,
                "error": user_message,
                "detail": detail if status_code < 500 else None,  # Hide server error details
                "message": user_message
            }
        )


async def error_handler_middleware(request: Request, call_next):
    """
    Middleware to catch all errors and transform them
    """
    try:
        response = await call_next(request)
        return response
    except Exception as exc:
        return await ErrorHandler.handle_exception(request, exc)


def setup_error_handlers(app):
    """
    Setup global error handlers for FastAPI app
    """
    from fastapi.exceptions import RequestValidationError
    from starlette.exceptions import HTTPException as StarletteHTTPException
    
    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException):
        return await ErrorHandler.handle_exception(request, exc)
    
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        return await ErrorHandler.handle_exception(request, exc)
    
    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception):
        return await ErrorHandler.handle_exception(request, exc)
    
    logger.info("Error handlers configured")
