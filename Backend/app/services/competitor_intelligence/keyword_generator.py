"""
LLM-Based Keyword Service for Competitor Analysis
Uses AI to generate high-quality search keywords from product descriptions
"""

import json
import re
import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)


class KeywordGenerator:
    """Generate competitor search keywords using LLM with fallback chain"""
    
    @classmethod
    async def generate_competitor_keywords(
        cls,
        product_name: str,
        product_description: str,
        key_features: List[str],
        max_keywords: int = 5
    ) -> Dict[str, Any]:
        """
        Generate competitor search keywords using LLM with fallback chain:
        GROQ → OpenRouter → Simple extraction
        
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
            
            # Create prompt
            features_text = "\n".join([f"- {f}" for f in key_features])
            
            prompt = f"""You are an expert at analyzing products and generating search keywords for competitor research.

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
}}"""
            
            # Try LLM with fallback chain (GROQ → OpenRouter)
            try:
                from app.services.shared.llm_service import get_llm_service_for_module3
                
                llm_service = get_llm_service_for_module3()
                result = await llm_service.call_llm(
                    prompt=prompt,
                    system_prompt="You are an expert at product analysis and competitor research. You generate precise, relevant search keywords. Return only valid JSON.",
                    temperature=0.3,
                    max_tokens=300,
                    response_format="json"
                )
                
                # Parse JSON response
                try:
                    result_data = json.loads(result)
                except json.JSONDecodeError:
                    # Try to extract JSON from output
                    json_match = re.search(r'\{.*\}', result, re.DOTALL)
                    if json_match:
                        result_data = json.loads(json_match.group())
                    else:
                        raise ValueError("Failed to extract JSON from LLM response")
                
                # Validate and normalize
                keywords = result_data.get("keywords", [])
                if not isinstance(keywords, list):
                    keywords = []
                
                # Clean keywords
                keywords = [str(k).strip().lower() for k in keywords if k][:max_keywords]
                
                if keywords:
                    logger.info(f"SUCCESS: Generated {len(keywords)} keywords via LLM")
                    return {
                        "success": True,
                        "keywords": keywords,
                        "category": result_data.get("category", "general"),
                        "reasoning": result_data.get("reasoning", ""),
                        "method": "llm"
                    }
            
            except Exception as e:
                logger.warning(f"LLM keyword generation failed: {str(e)}, using fallback")
            
            # Fallback: Simple extraction from description
            logger.info("Using fallback keyword extraction")
            return cls._simple_keyword_extraction(product_name, product_description, key_features, max_keywords)
            
        except Exception as e:
            logger.error(f"Error in keyword generation: {str(e)}")
            return cls._simple_keyword_extraction(product_name, product_description, key_features, max_keywords)
    
    @classmethod
    def _simple_keyword_extraction(
        cls,
        product_name: str,
        product_description: str,
        key_features: List[str],
        max_keywords: int = 5
    ) -> Dict[str, Any]:
        """Fallback: Extract keywords from product info"""
        keywords = []
        
        # Extract from description
        words = re.findall(r'\b[a-z]{3,}\b', product_description.lower())
        
        # Common stop words to exclude
        stop_words = {'the', 'and', 'for', 'with', 'that', 'this', 'from', 'are', 'was', 'were', 'been', 'have', 'has', 'had', 'will', 'would', 'could', 'should', 'can', 'may', 'might', 'must', 'our', 'your', 'their'}
        
        # Filter and get unique words
        keywords = [w for w in words if w not in stop_words]
        keywords = list(dict.fromkeys(keywords))[:max_keywords]  # Remove duplicates, keep order
        
        return {
            "success": True,
            "keywords": keywords,
            "category": "general",
            "reasoning": "Extracted from product description (fallback method)",
            "method": "simple_extraction"
        }
