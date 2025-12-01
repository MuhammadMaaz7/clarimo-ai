"""
LLM Service for interacting with OpenRouter API
"""

import json
import aiohttp
import asyncio
from typing import Optional, Dict, Any
from app.core.config import settings
from app.core.logging import logger


class LLMService:
    """Service for calling LLM APIs via OpenRouter"""
    
    def __init__(self):
        self.api_key = settings.OPENROUTER_API_KEY
        self.api_url = settings.OPENROUTER_API_URL
        self.model = settings.OPENROUTER_MODEL
        
        if not self.api_key:
            logger.warning("OPENROUTER_API_KEY not configured. LLM features will be limited.")
    
    async def call_llm(
        self,
        prompt: str,
        response_format: str = "text",
        temperature: float = 0.7,
        max_tokens: int = 1000,
        retry_count: int = 3
    ) -> str:
        """
        Call LLM API with retry logic
        
        Args:
            prompt: The prompt to send to the LLM
            response_format: Expected response format ("text" or "json")
            temperature: Sampling temperature (0-1)
            max_tokens: Maximum tokens in response
            retry_count: Number of retries on failure
            
        Returns:
            LLM response as string
            
        Raises:
            Exception: If all retries fail
        """
        if not self.api_key:
            raise Exception("OpenRouter API key not configured")
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://clarimo.ai",
            "X-Title": "Clarimo AI - Idea Validation"
        }
        
        # Adjust prompt for JSON response if needed
        if response_format == "json":
            prompt = f"{prompt}\n\nIMPORTANT: Respond with valid JSON only, no additional text."
        
        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "temperature": temperature,
            "max_tokens": max_tokens
        }
        
        last_error = None
        
        for attempt in range(retry_count):
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.post(
                        self.api_url,
                        headers=headers,
                        json=payload,
                        timeout=aiohttp.ClientTimeout(total=30)
                    ) as response:
                        if response.status == 200:
                            data = await response.json()
                            content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
                            
                            # Clean up JSON response if needed
                            if response_format == "json":
                                content = self._extract_json(content)
                            
                            return content
                        else:
                            error_text = await response.text()
                            last_error = f"API returned status {response.status}: {error_text}"
                            logger.warning(f"LLM API error (attempt {attempt + 1}/{retry_count}): {last_error}")
                            
                            # Don't retry on client errors (4xx)
                            if 400 <= response.status < 500:
                                raise Exception(last_error)
                            
            except asyncio.TimeoutError:
                last_error = "Request timeout"
                logger.warning(f"LLM API timeout (attempt {attempt + 1}/{retry_count})")
            except Exception as e:
                last_error = str(e)
                logger.error(f"LLM API error (attempt {attempt + 1}/{retry_count}): {last_error}")
                
                # Don't retry on certain errors
                if "API key" in str(e) or "authentication" in str(e).lower():
                    raise
            
            # Exponential backoff
            if attempt < retry_count - 1:
                wait_time = 2 ** attempt
                await asyncio.sleep(wait_time)
        
        # All retries failed
        raise Exception(f"LLM API call failed after {retry_count} attempts. Last error: {last_error}")
    
    @staticmethod
    def _extract_json(content: str) -> str:
        """
        Extract JSON from LLM response that might contain additional text
        
        Args:
            content: Raw LLM response
            
        Returns:
            Cleaned JSON string
        """
        # Try to find JSON in the response
        content = content.strip()
        
        # Look for JSON object
        start_idx = content.find('{')
        end_idx = content.rfind('}')
        
        if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
            json_str = content[start_idx:end_idx + 1]
            
            # Validate it's valid JSON
            try:
                json.loads(json_str)
                return json_str
            except json.JSONDecodeError:
                pass
        
        # Look for JSON array
        start_idx = content.find('[')
        end_idx = content.rfind(']')
        
        if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
            json_str = content[start_idx:end_idx + 1]
            
            try:
                json.loads(json_str)
                return json_str
            except json.JSONDecodeError:
                pass
        
        # Return as-is if no JSON found
        return content
    
    async def call_llm_with_fallback(
        self,
        prompt: str,
        response_format: str = "text",
        fallback_value: Optional[Any] = None
    ) -> str:
        """
        Call LLM with graceful fallback on error
        
        Args:
            prompt: The prompt to send
            response_format: Expected response format
            fallback_value: Value to return on error
            
        Returns:
            LLM response or fallback value
        """
        try:
            return await self.call_llm(prompt, response_format)
        except Exception as e:
            logger.error(f"LLM call failed, using fallback: {str(e)}")
            
            if fallback_value is not None:
                if response_format == "json":
                    return json.dumps(fallback_value)
                return str(fallback_value)
            
            # Default fallback for JSON
            if response_format == "json":
                return json.dumps({
                    "error": "LLM service unavailable",
                    "fallback": True
                })
            
            return "LLM service unavailable"
