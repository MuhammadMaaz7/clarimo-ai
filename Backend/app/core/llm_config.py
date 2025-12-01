"""
LLM Configuration for Token-Optimized Validation
Supports free APIs and local models for resource-constrained environments
"""

import os
from typing import Optional

class LLMConfig:
    """
    Configuration for LLM-based validation
    Optimized for free APIs and local models
    """
    
    # API Configuration
    API_PROVIDER = os.getenv("LLM_PROVIDER", "openrouter")  # openrouter, local, openai
    API_KEY = os.getenv("OPENROUTER_API_KEY", "")
    
    # Model Selection (free models from OpenRouter)
    # Free models: mistral-7b, neural-chat-7b, openchat-3.5
    MODEL = os.getenv("LLM_MODEL", "mistral-7b-instruct")
    
    # Token Optimization
    MAX_TOKENS = 800  # Reduced for efficiency
    TEMPERATURE = 0.2  # Lower = more consistent, fewer tokens
    TOP_P = 0.9  # Nucleus sampling for efficiency
    
    # Caching
    ENABLE_CACHE = True
    CACHE_TTL_SECONDS = 86400  # 24 hours
    
    # Rate Limiting (for free APIs)
    REQUESTS_PER_MINUTE = 10  # Conservative for free tier
    BATCH_SIZE = 4  # Process 4 ideas at a time
    
    # Fallback Strategy
    ENABLE_FALLBACK = True
    FALLBACK_SCORE = 3  # Neutral score on error
    
    # Prompt Optimization
    PROMPT_VERSION = "v2"  # Concise, token-optimized prompts
    INCLUDE_EXAMPLES = False  # Skip examples to save tokens
    
    @classmethod
    def get_api_url(cls) -> str:
        """Get API endpoint based on provider"""
        if cls.API_PROVIDER == "openrouter":
            return "https://openrouter.ai/api/v1/chat/completions"
        elif cls.API_PROVIDER == "local":
            return os.getenv("LOCAL_LLM_URL", "http://localhost:8000/v1/chat/completions")
        else:
            return "https://api.openai.com/v1/chat/completions"
    
    @classmethod
    def get_headers(cls) -> dict:
        """Get request headers for API"""
        headers = {
            "Content-Type": "application/json",
        }
        
        if cls.API_PROVIDER == "openrouter":
            headers["Authorization"] = f"Bearer {cls.API_KEY}"
            headers["HTTP-Referer"] = "https://clarimo.ai"
            headers["X-Title"] = "Clarimo AI"
        elif cls.API_PROVIDER == "openai":
            headers["Authorization"] = f"Bearer {cls.API_KEY}"
        
        return headers
    
    @classmethod
    def validate_config(cls) -> bool:
        """Validate configuration"""
        if cls.API_PROVIDER == "openrouter" and not cls.API_KEY:
            raise ValueError("OPENROUTER_API_KEY not set")
        
        if cls.MAX_TOKENS < 500:
            raise ValueError("MAX_TOKENS must be at least 500")
        
        return True


# Free Model Recommendations for Different Use Cases
FREE_MODELS = {
    "fast": "mistral-7b-instruct",  # Fastest, good quality
    "balanced": "neural-chat-7b",  # Balance of speed and quality
    "quality": "openchat-3.5",  # Better quality, slightly slower
}

# Token Estimates for Different Prompts
TOKEN_ESTIMATES = {
    "problem_clarity": 400,  # ~400 tokens
    "market_demand": 450,  # ~450 tokens
    "solution_fit": 400,  # ~400 tokens
    "differentiation": 400,  # ~400 tokens
}

# Total estimated tokens per validation: ~1600 tokens
# With caching, subsequent validations: ~100 tokens (just the request)
