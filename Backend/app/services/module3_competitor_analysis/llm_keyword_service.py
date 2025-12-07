"""
LLM-Based Keyword Service for Competitor Analysis
Uses AI to generate high-quality search keywords from product descriptions
"""

import requests
import json
import re
import os
import logging
from typing import List, Dict, Any
from datetime import datetime

logger = logging.getLogger(__name__)


class LLMKeywordService:
    """Generate competitor search keywords using LLM"""
    
    API_URL = "https://openrouter.ai/api/v1/chat/completions"
    MODEL_NAME = "google/gemma-3-27b-it:free"
    
    @classmethod
    def _get_api_keys(cls) -> List[str]:
        """Get list of API keys from environment variables"""
        keys = []
        
        # Primary key
        primary_key = os.getenv("OPENROUTER_API_KEY")
        if primary_key and "your-api-key-here" not in primary_key.lower():
            keys.append(primary_key)
        
        # Secondary keys
        for i in range(2, 6):
            key = os.getenv(f"OPENROUTER_API_KEY_{i}")
            if key and "your-api-key-here" not in key.lower():
                keys.append(key)
        
        return keys
    
    @classmethod
    async def generate_competitor_keywords(
        cls,
        product_name: str,
        product_description: str,
        key_features: List[str],
        max_keywords: int = 5
    ) -> Dict[str, Any]:
        """
        Generate competitor search keywords using LLM
        
        Args:
            product_name: Name of the product
            product_description: Description of the product
            key_features: List of key features
            max_keywords: Maximum number of keywords to return
            
        Returns:
            Dictionary with keywords and metadata
        """
        try:
            logger.info(f"Generating LLM keywords for: {product_name}")
            
            # Get API keys
            api_keys = cls._get_api_keys()
            
            if not api_keys:
                logger.warning("No API keys available - falling back to simple extraction")
                return {
                    "success": False,
                    "keywords": [],
                    "method": "none",
                    "error": "No API keys configured"
                }
            
            # Create prompt
            features_text = "\n".join([f"- {f}" for f in key_features])
            
            prompt = f"""
You are an expert at analyzing products and generating search keywords for competitor research.

PRODUCT INFORMATION:
Name: {product_name}
Description: {product_description}
Key Features:
{features_text}

TASK:
Generate {max_keywords} highly relevant search keywords that would help find competitors for this product.

GUIDELINES:
1. Focus on the CORE FUNCTIONALITY and CATEGORY of the product
2. Include technology keywords (AI, SaaS, mobile, etc.) if relevant
3. Include problem domain keywords (productivity, fitness, finance, etc.)
4. Use terms that competitors would likely use in their descriptions
5. Avoid brand-specific terms - focus on generic category terms
6. Keep keywords 1-3 words each
7. Prioritize keywords that would find the most relevant competitors

EXAMPLES:
- For a task management app: ["task management", "productivity", "project planning", "team collaboration", "workflow"]
- For a fitness tracker: ["fitness tracking", "workout app", "health monitoring", "exercise logging", "wellness"]
- For a budgeting tool: ["budget management", "expense tracking", "personal finance", "money management", "financial planning"]

Return ONLY a JSON object in this exact format (no other text):
{{
    "keywords": ["keyword1", "keyword2", "keyword3", "keyword4", "keyword5"],
    "category": "main product category",
    "reasoning": "brief explanation of keyword choices"
}}
"""
            
            payload = {
                "model": cls.MODEL_NAME,
                "messages": [
                    {
                        "role": "system",
                        "content": "You are an expert at product analysis and competitor research. You generate precise, relevant search keywords."
                    },
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.3,  # Low temperature for consistent results
                "max_tokens": 300
            }
            
            # Try each API key
            for key_index, api_key in enumerate(api_keys):
                logger.info(f"Trying API key {key_index + 1}/{len(api_keys)}")
                
                headers = {
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                }
                
                try:
                    response = requests.post(cls.API_URL, headers=headers, json=payload, timeout=20)
                    
                    if response.status_code == 200:
                        output = response.json()["choices"][0]["message"]["content"].strip()
                        logger.info(f"LLM response: {output[:200]}...")
                        
                        try:
                            # Try to parse JSON directly
                            result_data = json.loads(output)
                        except json.JSONDecodeError:
                            # Try to extract JSON from output
                            json_match = re.search(r'\{.*\}', output, re.DOTALL)
                            if json_match:
                                result_data = json.loads(json_match.group())
                            else:
                                logger.error("Failed to extract JSON from LLM response")
                                continue
                        
                        # Validate and normalize
                        keywords = result_data.get("keywords", [])
                        if not isinstance(keywords, list):
                            keywords = []
                        
                        # Clean keywords
                        keywords = [str(k).strip().lower() for k in keywords if k][:max_keywords]
                        
                        if keywords:
                            logger.info(f"SUCCESS: Generated {len(keywords)} keywords with API key {key_index + 1}")
                            return {
                                "success": True,
                                "keywords": keywords,
                                "category": result_data.get("category", "general"),
                                "reasoning": result_data.get("reasoning", ""),
                                "method": "llm",
                                "model": cls.MODEL_NAME
                            }
                    
                    elif response.status_code in [401, 429]:
                        logger.warning(f"API key {key_index + 1} failed with status {response.status_code}")
                        continue
                    
                except Exception as e:
                    logger.error(f"Error with API key {key_index + 1}: {str(e)}")
                    continue
            
            # All API keys failed
            logger.error("All API keys failed for LLM keyword generation")
            return {
                "success": False,
                "keywords": [],
                "method": "failed",
                "error": "All API keys failed"
            }
            
        except Exception as e:
            logger.error(f"Error in LLM keyword generation: {str(e)}")
            return {
                "success": False,
                "keywords": [],
                "method": "error",
                "error": str(e)
            }
