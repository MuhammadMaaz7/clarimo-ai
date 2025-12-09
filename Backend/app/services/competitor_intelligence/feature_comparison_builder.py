"""
Feature Matrix Service
Uses LLM (Groq) to intelligently match features between user's product and competitors
"""

import os
import requests
import json
from typing import List, Dict, Any
import logging

logger = logging.getLogger(__name__)


class FeatureComparisonBuilder:
    """
    Creates a feature comparison matrix using LLM to intelligently match features
    Uses Groq API for fast inference
    """
    
    API_URL = "https://api.groq.com/openai/v1/chat/completions"
    MODEL_NAME = "llama-3.3-70b-versatile"  # Fast and accurate
    
    @classmethod
    def _get_api_keys(cls) -> List[str]:
        """Get list of Groq API keys from environment variables"""
        keys = []
        
        # Primary key
        primary_key = os.getenv("GROQ_API_KEY")
        if primary_key and "your-api-key-here" not in primary_key.lower():
            keys.append(primary_key)
        
        # Secondary keys
        for i in range(2, 6):
            key = os.getenv(f"GROQ_API_KEY_{i}")
            if key and "your-api-key-here" not in key.lower():
                keys.append(key)
        
        return keys
    
    @classmethod
    async def build_feature_matrix(
        cls,
        user_product_name: str,
        user_features: List[str],
        competitors: List[Dict[str, Any]],
        max_competitors: int = 10
    ) -> Dict[str, Any]:
        """
        Build a comprehensive feature comparison matrix showing ALL features from user and competitors
        
        Args:
            user_product_name: Name of user's product
            user_features: List of features from user's product
            competitors: List of competitor dictionaries with name, description, url
            max_competitors: Maximum number of competitors to include
            
        Returns:
            Feature matrix with ALL features (user + competitors)
        """
        try:
            logger.info(f"Building comprehensive feature matrix for {len(competitors)} competitors...")
            
            # Limit competitors
            competitors = competitors[:max_competitors]
            
            # Step 1: Collect ALL unique features from user + competitors
            all_features = set(user_features)
            
            # Add competitor features
            for competitor in competitors:
                competitor_features = competitor.get('features', [])
                if competitor_features:
                    all_features.update(competitor_features)
            
            # Convert to sorted list for consistent ordering
            all_features_list = sorted(list(all_features))
            
            logger.info(f"Total unique features across all products: {len(all_features_list)}")
            logger.info(f"  - User features: {len(user_features)}")
            logger.info(f"  - Additional competitor features: {len(all_features_list) - len(user_features)}")
            
            # Build matrix structure with ALL features
            matrix = {
                "features": all_features_list,
                "products": []
            }
            
            # Step 2: Add user's product - check which features they have
            user_product_entry = {
                "name": user_product_name,
                "is_user_product": True,
                "feature_support": {}
            }
            
            # User has their own features (TRUE), need to check competitor features
            for feature in all_features_list:
                if feature in user_features:
                    user_product_entry["feature_support"][feature] = True
                else:
                    # This is a competitor feature - user doesn't have it
                    user_product_entry["feature_support"][feature] = False
            
            matrix["products"].append(user_product_entry)
            
            # Step 3: For each competitor, check ALL features
            for competitor in competitors:
                logger.info(f"Analyzing features for: {competitor.get('name')}")
                
                competitor_features = competitor.get('features', [])
                
                # Use LLM to check if competitor has each feature
                feature_support = await cls._analyze_competitor_features(
                    competitor_name=competitor.get('name', ''),
                    competitor_description=competitor.get('description', ''),
                    competitor_scraped_features=competitor_features,
                    user_features=all_features_list  # Check ALL features
                )
                
                competitor_entry = {
                    "name": competitor.get('name'),
                    "is_user_product": False,
                    "url": competitor.get('url'),
                    "feature_support": {}
                }
                
                # Check each feature
                for feature in all_features_list:
                    if feature in competitor_features:
                        # Competitor explicitly has this feature
                        competitor_entry["feature_support"][feature] = True
                    else:
                        # Check LLM analysis
                        competitor_entry["feature_support"][feature] = feature_support.get(feature, {}).get('has_feature', False)
                
                matrix["products"].append(competitor_entry)
            
            logger.info(f"✓ Feature matrix built for {len(matrix['products'])} products with {len(all_features_list)} features")
            return matrix
            
        except Exception as e:
            logger.error(f"Failed to build feature matrix: {str(e)}")
            return {
                "features": user_features,
                "products": [{
                    "name": user_product_name,
                    "is_user_product": True,
                    "feature_support": {feature: True for feature in user_features}
                }]
            }
    
    @classmethod
    async def _analyze_competitor_features(
        cls,
        competitor_name: str,
        competitor_description: str,
        user_features: List[str],
        competitor_scraped_features: List[str] = None
    ) -> Dict[str, Any]:
        """
        Use LLM to analyze if competitor has each feature
        
        Args:
            competitor_name: Name of the competitor
            competitor_description: Description of the competitor
            user_features: List of features to check
            competitor_scraped_features: Optional list of scraped features (preferred)
            
        Returns:
            Dictionary mapping feature to dict with has_feature, evidence, confidence
        """
        api_keys = cls._get_api_keys()
        
        if not api_keys:
            logger.warning("No API keys available for feature analysis")
            return {feature: {"has_feature": False, "evidence": "No API keys"} for feature in user_features}
        
        # Build context from scraped features if available
        context = f"Description: {competitor_description}"
        if competitor_scraped_features and len(competitor_scraped_features) > 0:
            context += f"\n\nScraped Features:\n" + "\n".join([f"- {f}" for f in competitor_scraped_features])
        
        # Create prompt for LLM
        features_list = "\n".join([f"{i+1}. {feature}" for i, feature in enumerate(user_features)])
        
        prompt = f"""
You are an expert at analyzing software products and their features.

COMPETITOR PRODUCT:
Name: {competitor_name}
{context}

FEATURES TO CHECK:
{features_list}

TASK:
For each feature listed above, determine if the competitor has that feature or similar functionality based ONLY on the information provided above.

IMPORTANT RULES:
- Look for the FUNCTIONALITY, not exact wording (e.g., "AI voice generation" = "Voice synthesis with AI")
- If the SAME or SIMILAR functionality is mentioned → mark TRUE
- If NOT mentioned at all → mark FALSE
- DO NOT assume or invent features - be conservative
- If unsure → mark FALSE
- Provide brief evidence for your decision

EXAMPLES:
- Feature: "Real-time collaboration" → Competitor has "Team editing" → TRUE (same functionality)
- Feature: "Cloud storage" → Competitor has "Online backup" → TRUE (similar functionality)
- Feature: "Dark mode" → Not mentioned → FALSE
- Feature: "AI-powered" → Competitor has "Machine learning" → TRUE (same technology)

Return ONLY a JSON object in this exact format (no other text):
{{
    "feature_analysis": [
        {{"feature": "feature name", "has_feature": true/false, "evidence": "brief reason"}},
        ...
    ]
}}
"""
        
        payload = {
            "model": cls.MODEL_NAME,
            "messages": [
                {
                    "role": "system",
                    "content": "You are an expert at analyzing software products. You understand that features can be described differently but serve the same purpose. Never invent features."
                },
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.1,
            "max_tokens": 1500
        }
        
        # Try each API key
        for key_index, api_key in enumerate(api_keys):
            try:
                headers = {
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                }
                
                response = requests.post(cls.API_URL, headers=headers, json=payload, timeout=30)
                
                if response.status_code == 200:
                    output = response.json()["choices"][0]["message"]["content"].strip()
                    
                    # Parse JSON response
                    try:
                        # Try to extract JSON from response
                        import re
                        json_match = re.search(r'\{.*\}', output, re.DOTALL)
                        if json_match:
                            result_data = json.loads(json_match.group())
                        else:
                            result_data = json.loads(output)
                        
                        # Build feature support dictionary with evidence
                        feature_support = {}
                        for analysis in result_data.get("feature_analysis", []):
                            feature_name = analysis.get("feature")
                            has_feature = analysis.get("has_feature", False)
                            evidence = analysis.get("evidence", "")
                            
                            feature_support[feature_name] = {
                                "has_feature": has_feature,
                                "evidence": evidence,
                                "confidence": "high" if competitor_scraped_features else "medium"
                            }
                        
                        # Ensure ALL user features are present
                        for feature in user_features:
                            if feature not in feature_support:
                                feature_support[feature] = {
                                    "has_feature": False,
                                    "evidence": "not mentioned",
                                    "confidence": "medium"
                                }
                        
                        logger.info(f"  ✓ Analyzed {len(feature_support)} features")
                        return feature_support
                        
                    except Exception as e:
                        logger.error(f"Failed to parse LLM response: {str(e)}")
                        continue
                
                elif response.status_code in [401, 429]:
                    logger.warning(f"API key {key_index + 1} failed with status {response.status_code}")
                    continue
                else:
                    logger.warning(f"API key {key_index + 1} failed with status {response.status_code}")
                    continue
                    
            except Exception as e:
                logger.error(f"Error with API key {key_index + 1}: {str(e)}")
                continue
        
        # All API keys failed - return all False with proper structure
        logger.warning(f"All API keys failed for {competitor_name}, marking all features as False")
        return {feature: {"has_feature": False, "evidence": "API failed", "confidence": "low"} for feature in user_features}
