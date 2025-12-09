"""
Unified LLM Service with Multi-Provider Fallback
Used by both Module 2 (Idea Validation) and Module 3 (Competitor Analysis)

Fallback Order (Configurable):
- Module 2: OpenRouter → Groq → HuggingFace
- Module 3: Groq → OpenRouter → HuggingFace

NO HARDCODED RESPONSES - Always uses actual LLM inference
"""

import json
import os
import asyncio
import aiohttp
from typing import Optional, Dict, Any, List, Callable
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class LLMProvider(Enum):
    """Available LLM providers"""
    OPENROUTER = "openrouter"
    GROQ = "groq"
    HUGGINGFACE = "huggingface"


class UnifiedLLMService:
    """
    Unified LLM service with configurable fallback chain
    Supports multiple providers with automatic failover
    """
    
    def __init__(self, provider_order: List[str] = None):
        """
        Initialize with custom provider order
        
        Args:
            provider_order: List of providers to try in order
                          Default: ["openrouter", "groq", "huggingface"]
        """
        self.provider_order = provider_order or ["openrouter", "groq", "huggingface"]
        self.timeout = 30
        self.retry_per_key = 2
        self.last_successful_provider = None  # Cache the working provider
    
    @staticmethod
    def _get_api_keys(provider: str) -> List[str]:
        """Get all API keys for a provider"""
        keys = []
        
        if provider == "openrouter":
            primary = os.getenv("OPENROUTER_API_KEY")
            if primary and "your-api-key" not in primary.lower() and primary.strip():
                keys.append(primary)
            
            for i in range(2, 11):
                key = os.getenv(f"OPENROUTER_API_KEY_{i}")
                if key and "your-api-key" not in key.lower() and key.strip():
                    keys.append(key)
        
        elif provider == "groq":
            primary = os.getenv("GROQ_API_KEY")
            if primary and "your-api-key" not in primary.lower() and primary.strip():
                keys.append(primary)
            
            for i in range(2, 11):
                key = os.getenv(f"GROQ_API_KEY_{i}")
                if key and "your-api-key" not in key.lower() and key.strip():
                    keys.append(key)
        
        return keys
    
    async def call_llm(
        self,
        prompt: str,
        response_format: str = "text",
        temperature: float = 0.7,
        max_tokens: int = 1000,
        system_prompt: Optional[str] = None
    ) -> str:
        """
        Call LLM with automatic fallback chain
        
        Args:
            prompt: User prompt
            response_format: "text" or "json"
            temperature: Sampling temperature
            max_tokens: Maximum tokens
            system_prompt: Optional system prompt
            
        Returns:
            LLM response (raises exception if all providers fail)
        """
        
        # Adjust prompt for JSON if needed
        if response_format == "json":
            prompt = f"{prompt}\n\nIMPORTANT: Respond with valid JSON only, no additional text."
        
        # Optimize: Try last successful provider first
        providers_to_try = list(self.provider_order)
        if self.last_successful_provider and self.last_successful_provider in providers_to_try:
            # Move last successful provider to front
            providers_to_try.remove(self.last_successful_provider)
            providers_to_try.insert(0, self.last_successful_provider)
            logger.debug(f"Trying last successful provider first: {self.last_successful_provider}")
        
        # Try providers in optimized order
        for provider in providers_to_try:
            logger.info(f"Trying {provider.upper()} API...")
            
            if provider == "openrouter":
                result = await self._try_openrouter(prompt, system_prompt, temperature, max_tokens)
            elif provider == "groq":
                result = await self._try_groq(prompt, system_prompt, temperature, max_tokens)
            elif provider == "huggingface":
                result = await self._try_huggingface(prompt, system_prompt, max_tokens)
            else:
                logger.warning(f"Unknown provider: {provider}")
                continue
            
            if result["success"]:
                content = self._extract_json(result["content"]) if response_format == "json" else result["content"]
                logger.info(f"✓ {provider.upper()} succeeded")
                # Cache successful provider for next call
                self.last_successful_provider = provider
                return content
            
            logger.warning(f"{provider.upper()} failed, trying next provider...")
        
        # All providers failed
        error_msg = "All LLM providers failed. Please check your API keys or install HuggingFace (pip install transformers torch)."
        logger.error(error_msg)
        raise Exception(error_msg)
    
    async def _try_openrouter(
        self,
        prompt: str,
        system_prompt: Optional[str],
        temperature: float,
        max_tokens: int
    ) -> Dict[str, Any]:
        """Try OpenRouter API with all available keys"""
        keys = self._get_api_keys("openrouter")
        
        if not keys:
            logger.debug("No OpenRouter API keys configured")
            return {"success": False, "content": None}
        
        model = os.getenv("OPENROUTER_MODEL", "google/gemini-2.0-flash-exp:free")
        api_url = os.getenv("OPENROUTER_API_URL", "https://openrouter.ai/api/v1/chat/completions")
        
        for i, api_key in enumerate(keys, 1):
            for attempt in range(self.retry_per_key):
                try:
                    logger.debug(f"Trying OpenRouter key {i}/{len(keys)} (attempt {attempt + 1}/{self.retry_per_key})...")
                    
                    headers = {
                        "Authorization": f"Bearer {api_key}",
                        "Content-Type": "application/json",
                        "HTTP-Referer": "https://clarimo.ai",
                        "X-Title": "Clarimo AI"
                    }
                    
                    messages = []
                    if system_prompt:
                        messages.append({"role": "system", "content": system_prompt})
                    messages.append({"role": "user", "content": prompt})
                    
                    payload = {
                        "model": model,
                        "messages": messages,
                        "temperature": temperature,
                        "max_tokens": max_tokens
                    }
                    
                    async with aiohttp.ClientSession() as session:
                        async with session.post(
                            api_url,
                            headers=headers,
                            json=payload,
                            timeout=aiohttp.ClientTimeout(total=self.timeout)
                        ) as response:
                            if response.status == 200:
                                data = await response.json()
                                content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
                                return {"success": True, "content": content}
                            else:
                                logger.warning(f"OpenRouter key {i} attempt {attempt + 1} failed: HTTP {response.status}")
                                if response.status in [401, 403]:
                                    break
                
                except asyncio.TimeoutError:
                    logger.warning(f"OpenRouter key {i} attempt {attempt + 1} timed out")
                except Exception as e:
                    logger.warning(f"OpenRouter key {i} attempt {attempt + 1} error: {str(e)}")
                
                if attempt < self.retry_per_key - 1:
                    await asyncio.sleep(1)
        
        return {"success": False, "content": None}
    
    async def _try_groq(
        self,
        prompt: str,
        system_prompt: Optional[str],
        temperature: float,
        max_tokens: int
    ) -> Dict[str, Any]:
        """Try Groq API with all available keys"""
        keys = self._get_api_keys("groq")
        
        if not keys:
            logger.debug("No Groq API keys configured")
            return {"success": False, "content": None}
        
        model = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
        api_url = "https://api.groq.com/openai/v1/chat/completions"
        
        for i, api_key in enumerate(keys, 1):
            for attempt in range(self.retry_per_key):
                try:
                    logger.debug(f"Trying Groq key {i}/{len(keys)} (attempt {attempt + 1}/{self.retry_per_key})...")
                    
                    headers = {
                        "Authorization": f"Bearer {api_key}",
                        "Content-Type": "application/json"
                    }
                    
                    messages = []
                    if system_prompt:
                        messages.append({"role": "system", "content": system_prompt})
                    messages.append({"role": "user", "content": prompt})
                    
                    payload = {
                        "model": model,
                        "messages": messages,
                        "temperature": temperature,
                        "max_tokens": max_tokens
                    }
                    
                    async with aiohttp.ClientSession() as session:
                        async with session.post(
                            api_url,
                            headers=headers,
                            json=payload,
                            timeout=aiohttp.ClientTimeout(total=self.timeout)
                        ) as response:
                            if response.status == 200:
                                data = await response.json()
                                content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
                                return {"success": True, "content": content}
                            else:
                                logger.warning(f"Groq key {i} attempt {attempt + 1} failed: HTTP {response.status}")
                                if response.status in [401, 403]:
                                    break
                
                except asyncio.TimeoutError:
                    logger.warning(f"Groq key {i} attempt {attempt + 1} timed out")
                except Exception as e:
                    logger.warning(f"Groq key {i} attempt {attempt + 1} error: {str(e)}")
                
                if attempt < self.retry_per_key - 1:
                    await asyncio.sleep(1)
        
        return {"success": False, "content": None}
    
    async def _try_huggingface(
        self,
        prompt: str,
        system_prompt: Optional[str],
        max_tokens: int
    ) -> Dict[str, Any]:
        """Try HuggingFace local model - DISABLED (not working reliably)"""
        # HuggingFace local models are not reliable for JSON generation
        # Even Phi-2 and Flan-T5-Large struggle with structured outputs
        # Keeping this disabled until proper JSON mode is implemented
        logger.debug("HuggingFace fallback disabled - use API keys (OpenRouter/Groq)")
        return {"success": False, "content": None}
    
    @staticmethod
    def _extract_json(content: str) -> str:
        """Extract JSON from LLM response"""
        content = content.strip()
        content = content.replace("```json", "").replace("```", "").strip()
        
        # Try JSON object
        start_idx = content.find('{')
        end_idx = content.rfind('}')
        
        if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
            json_str = content[start_idx:end_idx + 1]
            try:
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
                json.loads(json_str)
                return json_str
            except json.JSONDecodeError:
                pass
        
        return content
    
    async def call_llm_with_fallback(
        self,
        prompt: str,
        response_format: str = "text",
        temperature: float = 0.7,
        max_tokens: int = 1000,
        system_prompt: Optional[str] = None,
        fallback_handler: Optional[Callable] = None
    ) -> str:
        """
        Call LLM with graceful fallback handler
        
        Args:
            prompt: User prompt
            response_format: "text" or "json"
            temperature: Sampling temperature
            max_tokens: Maximum tokens
            system_prompt: Optional system prompt
            fallback_handler: Optional function to generate fallback response
            
        Returns:
            LLM response (always succeeds if fallback_handler provided)
        """
        try:
            return await self.call_llm(
                prompt=prompt,
                response_format=response_format,
                temperature=temperature,
                max_tokens=max_tokens,
                system_prompt=system_prompt
            )
        except Exception as e:
            logger.error(f"All LLM providers failed: {str(e)}")
            
            if fallback_handler:
                try:
                    logger.info("Using custom fallback handler...")
                    fallback_content = fallback_handler()
                    
                    if response_format == "json":
                        if isinstance(fallback_content, dict):
                            return json.dumps(fallback_content)
                        return fallback_content
                    
                    return str(fallback_content)
                except Exception as fb_error:
                    logger.error(f"Fallback handler failed: {str(fb_error)}")
            
            raise Exception(
                "Unable to generate analysis. All LLM providers are unavailable. "
                "Please check your API keys or install HuggingFace transformers."
            )
    
    def get_provider_status(self) -> Dict[str, Any]:
        """Get status of all LLM providers"""
        status = {
            "openrouter": {
                "available": len(self._get_api_keys("openrouter")) > 0,
                "keys_configured": len(self._get_api_keys("openrouter"))
            },
            "groq": {
                "available": len(self._get_api_keys("groq")) > 0,
                "keys_configured": len(self._get_api_keys("groq"))
            },
            "huggingface": {
                "available": False,
                "installed": False
            }
        }
        
        try:
            import transformers
            status["huggingface"]["installed"] = True
            status["huggingface"]["available"] = True
        except ImportError:
            pass
        
        return status


# Convenience functions for different modules
def get_llm_service_for_module2() -> UnifiedLLMService:
    """Get LLM service configured for Module 2 (Idea Validation)"""
    return UnifiedLLMService(provider_order=["openrouter", "groq", "huggingface"])


def get_llm_service_for_module3() -> UnifiedLLMService:
    """Get LLM service configured for Module 3 (Competitor Analysis)"""
    return UnifiedLLMService(provider_order=["groq", "openrouter", "huggingface"])
