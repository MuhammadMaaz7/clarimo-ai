"""
Shared Validation Utilities
Common validation functions used across modules
"""

import re
from typing import Dict, Any, List, Optional
from datetime import datetime


def validate_email(email: str) -> bool:
    """
    Validate email format
    
    Args:
        email: Email address to validate
        
    Returns:
        True if valid, False otherwise
    """
    if not email:
        return False
    
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def validate_url(url: str) -> bool:
    """
    Validate URL format
    
    Args:
        url: URL to validate
        
    Returns:
        True if valid, False otherwise
    """
    if not url:
        return False
    
    pattern = r'^https?://[^\s/$.?#].[^\s]*$'
    return bool(re.match(pattern, url, re.IGNORECASE))


def validate_required_fields(data: Dict[str, Any], required_fields: List[str]) -> Dict[str, Any]:
    """
    Validate that required fields are present and non-empty
    
    Args:
        data: Data dictionary to validate
        required_fields: List of required field names
        
    Returns:
        Dictionary with 'valid' boolean and 'missing_fields' list
    """
    missing_fields = []
    
    for field in required_fields:
        if field not in data or not data[field]:
            missing_fields.append(field)
    
    return {
        "valid": len(missing_fields) == 0,
        "missing_fields": missing_fields
    }


def sanitize_input(text: str, max_length: Optional[int] = None) -> str:
    """
    Sanitize user input by removing potentially harmful content
    
    Args:
        text: Text to sanitize
        max_length: Maximum allowed length
        
    Returns:
        Sanitized text
    """
    if not text:
        return ""
    
    # Remove HTML tags
    text = re.sub(r'<[^>]+>', '', text)
    
    # Remove script tags and content
    text = re.sub(r'<script[^>]*>.*?</script>', '', text, flags=re.DOTALL | re.IGNORECASE)
    
    # Trim whitespace
    text = text.strip()
    
    # Apply max length if specified
    if max_length and len(text) > max_length:
        text = text[:max_length]
    
    return text


def validate_score(score: float, min_score: float = 0.0, max_score: float = 10.0) -> bool:
    """
    Validate that a score is within acceptable range
    
    Args:
        score: Score to validate
        min_score: Minimum acceptable score
        max_score: Maximum acceptable score
        
    Returns:
        True if valid, False otherwise
    """
    try:
        score = float(score)
        return min_score <= score <= max_score
    except (ValueError, TypeError):
        return False


def validate_date_range(start_date: datetime, end_date: datetime) -> bool:
    """
    Validate that date range is logical
    
    Args:
        start_date: Start date
        end_date: End date
        
    Returns:
        True if valid (start before end), False otherwise
    """
    if not start_date or not end_date:
        return False
    
    return start_date <= end_date


def validate_list_length(items: List[Any], min_length: int = 0, max_length: Optional[int] = None) -> bool:
    """
    Validate list length
    
    Args:
        items: List to validate
        min_length: Minimum required length
        max_length: Maximum allowed length
        
    Returns:
        True if valid, False otherwise
    """
    if not isinstance(items, list):
        return False
    
    if len(items) < min_length:
        return False
    
    if max_length is not None and len(items) > max_length:
        return False
    
    return True


def normalize_score(score: float, old_min: float, old_max: float, new_min: float = 0.0, new_max: float = 10.0) -> float:
    """
    Normalize a score from one range to another
    
    Args:
        score: Score to normalize
        old_min: Old minimum value
        old_max: Old maximum value
        new_min: New minimum value
        new_max: New maximum value
        
    Returns:
        Normalized score
    """
    if old_max == old_min:
        return new_min
    
    normalized = ((score - old_min) / (old_max - old_min)) * (new_max - new_min) + new_min
    return max(new_min, min(new_max, normalized))
