"""
Shared Text Utilities
Common text processing functions used across modules
"""

import re
from typing import List, Optional


def truncate_at_sentence(text: str, max_length: int = 300) -> str:
    """
    Truncate text at sentence boundary, not mid-sentence
    Ensures complete sentences without trailing ...
    
    Args:
        text: Text to truncate
        max_length: Maximum length
        
    Returns:
        Truncated text at sentence boundary
    """
    if not text or len(text) <= max_length:
        return text
    
    truncated = text[:max_length]
    
    # Look for sentence endings: . ! ?
    sentence_endings = ['.', '!', '?']
    last_ending = -1
    
    for ending in sentence_endings:
        pos = truncated.rfind(ending)
        if pos > last_ending:
            last_ending = pos
    
    # If we found a sentence ending, cut there
    if last_ending > 50:  # At least 50 chars
        return text[:last_ending + 1].strip()
    
    # Otherwise, cut at last space to avoid mid-word
    last_space = truncated.rfind(' ')
    if last_space > 50:
        return text[:last_space].strip()
    
    # Fallback: just return truncated
    return truncated.strip()


def extract_json_from_text(content: str) -> Optional[str]:
    """
    Extract JSON from text that might contain additional content
    
    Args:
        content: Raw text possibly containing JSON
        
    Returns:
        Extracted JSON string or None
    """
    content = content.strip()
    
    # Remove markdown code blocks
    content = content.replace("```json", "").replace("```", "").strip()
    
    # Try JSON object
    start_idx = content.find('{')
    end_idx = content.rfind('}')
    
    if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
        json_str = content[start_idx:end_idx + 1]
        
        # Validate it's valid JSON
        try:
            import json
            json.loads(json_str)
            return json_str
        except json.JSONDecodeError:
            pass
    
    # Try JSON array
    start_idx = content.find('[')
    end_idx = content.rfind(']')
    
    if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
        json_str = content[start_idx:end_idx + 1]
        
        try:
            import json
            json.loads(json_str)
            return json_str
        except json.JSONDecodeError:
            pass
    
    return None


def clean_text(text: str) -> str:
    """
    Clean text by removing extra whitespace and special characters
    
    Args:
        text: Text to clean
        
    Returns:
        Cleaned text
    """
    if not text:
        return ""
    
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text)
    
    # Remove special characters but keep basic punctuation
    text = re.sub(r'[^\w\s.,!?-]', '', text)
    
    return text.strip()


def extract_keywords(text: str, max_keywords: int = 10) -> List[str]:
    """
    Extract keywords from text using simple frequency analysis
    
    Args:
        text: Text to extract keywords from
        max_keywords: Maximum number of keywords
        
    Returns:
        List of keywords
    """
    if not text:
        return []
    
    # Convert to lowercase and split
    words = text.lower().split()
    
    # Remove common stop words
    stop_words = {
        'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
        'of', 'with', 'by', 'from', 'as', 'is', 'was', 'are', 'were', 'be',
        'been', 'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will',
        'would', 'should', 'could', 'may', 'might', 'must', 'can', 'this',
        'that', 'these', 'those', 'i', 'you', 'he', 'she', 'it', 'we', 'they'
    }
    
    # Filter and count
    word_freq = {}
    for word in words:
        word = re.sub(r'[^\w]', '', word)
        if len(word) > 3 and word not in stop_words:
            word_freq[word] = word_freq.get(word, 0) + 1
    
    # Sort by frequency
    sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
    
    return [word for word, _ in sorted_words[:max_keywords]]


def format_list_as_text(items: List[str], separator: str = ", ", max_items: Optional[int] = None) -> str:
    """
    Format a list as readable text
    
    Args:
        items: List of items
        separator: Separator between items
        max_items: Maximum items to include
        
    Returns:
        Formatted string
    """
    if not items:
        return ""
    
    if max_items:
        items = items[:max_items]
    
    if len(items) == 1:
        return items[0]
    elif len(items) == 2:
        return f"{items[0]} and {items[1]}"
    else:
        return separator.join(items[:-1]) + f", and {items[-1]}"
