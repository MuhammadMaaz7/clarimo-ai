"""
Shared API Utilities
Common API-related functions used across modules
"""

import asyncio
import aiohttp
from typing import Dict, Any, Optional, List
import logging

logger = logging.getLogger(__name__)


async def make_api_request(
    url: str,
    method: str = "GET",
    headers: Optional[Dict[str, str]] = None,
    json_data: Optional[Dict[str, Any]] = None,
    params: Optional[Dict[str, Any]] = None,
    timeout: int = 30,
    retry_count: int = 3,
    retry_delay: float = 1.0
) -> Dict[str, Any]:
    """
    Make an API request with retry logic
    
    Args:
        url: API endpoint URL
        method: HTTP method (GET, POST, etc.)
        headers: Request headers
        json_data: JSON payload for POST/PUT requests
        params: Query parameters
        timeout: Request timeout in seconds
        retry_count: Number of retries on failure
        retry_delay: Delay between retries in seconds
        
    Returns:
        Response data as dictionary
        
    Raises:
        Exception: If all retries fail
    """
    last_error = None
    
    for attempt in range(retry_count):
        try:
            async with aiohttp.ClientSession() as session:
                async with session.request(
                    method=method,
                    url=url,
                    headers=headers,
                    json=json_data,
                    params=params,
                    timeout=aiohttp.ClientTimeout(total=timeout)
                ) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        error_text = await response.text()
                        last_error = f"HTTP {response.status}: {error_text}"
                        logger.warning(f"API request failed (attempt {attempt + 1}/{retry_count}): {last_error}")
                        
                        # Don't retry on client errors (4xx)
                        if 400 <= response.status < 500:
                            raise Exception(last_error)
        
        except asyncio.TimeoutError:
            last_error = "Request timeout"
            logger.warning(f"API request timeout (attempt {attempt + 1}/{retry_count})")
        
        except Exception as e:
            last_error = str(e)
            logger.error(f"API request error (attempt {attempt + 1}/{retry_count}): {last_error}")
            
            # Don't retry on certain errors
            if "authentication" in str(e).lower() or "api key" in str(e).lower():
                raise
        
        # Wait before retry (exponential backoff)
        if attempt < retry_count - 1:
            wait_time = retry_delay * (2 ** attempt)
            await asyncio.sleep(wait_time)
    
    # All retries failed
    raise Exception(f"API request failed after {retry_count} attempts. Last error: {last_error}")


async def batch_api_requests(
    requests: List[Dict[str, Any]],
    max_concurrent: int = 5
) -> List[Dict[str, Any]]:
    """
    Make multiple API requests concurrently with rate limiting
    
    Args:
        requests: List of request configurations (each with url, method, etc.)
        max_concurrent: Maximum concurrent requests
        
    Returns:
        List of responses
    """
    semaphore = asyncio.Semaphore(max_concurrent)
    
    async def limited_request(request_config: Dict[str, Any]) -> Dict[str, Any]:
        async with semaphore:
            try:
                return await make_api_request(**request_config)
            except Exception as e:
                logger.error(f"Batch request failed: {str(e)}")
                return {"error": str(e), "success": False}
    
    tasks = [limited_request(req) for req in requests]
    return await asyncio.gather(*tasks, return_exceptions=True)


def build_query_params(params: Dict[str, Any], exclude_none: bool = True) -> Dict[str, str]:
    """
    Build query parameters, optionally excluding None values
    
    Args:
        params: Parameter dictionary
        exclude_none: Whether to exclude None values
        
    Returns:
        Cleaned parameter dictionary
    """
    if exclude_none:
        return {k: str(v) for k, v in params.items() if v is not None}
    return {k: str(v) for k, v in params.items()}


def parse_api_error(error: Exception) -> Dict[str, Any]:
    """
    Parse API error into user-friendly format
    
    Args:
        error: Exception from API call
        
    Returns:
        Dictionary with error details
    """
    error_str = str(error).lower()
    
    if "timeout" in error_str:
        return {
            "error_type": "timeout",
            "message": "Request timed out. Please try again.",
            "user_message": "The request took too long. Please try again."
        }
    elif "connection" in error_str or "network" in error_str:
        return {
            "error_type": "network",
            "message": "Network error occurred.",
            "user_message": "Unable to connect. Please check your internet connection."
        }
    elif "401" in error_str or "403" in error_str or "authentication" in error_str:
        return {
            "error_type": "authentication",
            "message": "Authentication failed.",
            "user_message": "Authentication error. Please check your API keys."
        }
    elif "429" in error_str or "rate limit" in error_str:
        return {
            "error_type": "rate_limit",
            "message": "Rate limit exceeded.",
            "user_message": "Too many requests. Please try again in a moment."
        }
    elif "500" in error_str or "502" in error_str or "503" in error_str:
        return {
            "error_type": "server_error",
            "message": "Server error occurred.",
            "user_message": "Service temporarily unavailable. Please try again later."
        }
    else:
        return {
            "error_type": "unknown",
            "message": str(error),
            "user_message": "An error occurred. Please try again."
        }


def get_user_friendly_error_message(error: Exception) -> str:
    """
    Get user-friendly error message from exception
    
    Args:
        error: Exception
        
    Returns:
        User-friendly error message
    """
    parsed = parse_api_error(error)
    return parsed["user_message"]
