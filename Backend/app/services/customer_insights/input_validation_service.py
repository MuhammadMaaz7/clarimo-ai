"""
Customer Insights Input Validation Service

Validates user input before processing to prevent gibberish, random text, or inappropriate content.
Similar to Problem Discovery validation but tailored for customer insights analysis.
"""
import re
import os
import json
import requests
import logging
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)


class CustomerInsightsInputValidator:
    """Service for validating customer insights input"""
    
    # API Configuration
    API_URL = "https://openrouter.ai/api/v1/chat/completions"
    MODEL_NAME = "google/gemma-3-27b-it:free"
    
    @classmethod
    def _get_api_keys(cls) -> List[str]:
        """
        Get list of API keys from environment variables
        Supports multiple keys: OPENROUTER_API_KEY, OPENROUTER_API_KEY_2, etc.
        """
        keys = []
        
        # Primary key
        primary_key = os.getenv("OPENROUTER_API_KEY")
        if primary_key and not any(placeholder in primary_key for placeholder in [
            "REPLACE_WITH_YOUR_ACTUAL_API_KEY", 
            "REPLACE_WITH_BACKUP_KEY", 
            "your-api-key-here"
        ]):
            keys.append(primary_key)
        
        # Secondary keys
        for i in range(2, 6):  # Support up to 5 keys
            key = os.getenv(f"OPENROUTER_API_KEY_{i}")
            if key and not any(placeholder in key for placeholder in [
                "REPLACE_WITH_YOUR_ACTUAL_API_KEY", 
                "REPLACE_WITH_BACKUP_KEY", 
                "your-api-key-here"
            ]):
                keys.append(key)
        
        return keys
    
    @classmethod
    async def validate_input(
        cls,
        startup_idea: str,
        target_market: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Validate customer insights input before processing
        
        Args:
            startup_idea: The startup idea or problem to analyze
            target_market: Optional target market description
            
        Returns:
            Dictionary with validation result:
            {
                "is_valid": bool,
                "reason": str,
                "confidence": float (0.0-1.0)
            }
        """
        logger.info(f"Validating customer insights input: {startup_idea[:50]}...")
        
        # Step 1: Basic validation (fast rejection)
        basic_validation = cls._basic_validation(startup_idea, target_market)
        if not basic_validation["is_valid"]:
            logger.warning(f"Basic validation failed: {basic_validation['reason']}")
            return basic_validation
        
        # Step 2: Pattern-based validation (detect obvious gibberish)
        pattern_validation = cls._pattern_validation(startup_idea, target_market)
        if not pattern_validation["is_valid"]:
            logger.warning(f"Pattern validation failed: {pattern_validation['reason']}")
            return pattern_validation
        
        # Step 3: AI-powered validation (semantic understanding)
        ai_validation = await cls._ai_validation(startup_idea, target_market)
        if not ai_validation["is_valid"]:
            logger.warning(f"AI validation failed: {ai_validation['reason']}")
            return ai_validation
        
        logger.info(f"Validation passed: {ai_validation['reason']}")
        return ai_validation
    
    @classmethod
    def _basic_validation(cls, startup_idea: str, target_market: Optional[str]) -> Dict[str, Any]:
        """
        Basic validation checks (length, empty strings, etc.)
        """
        # Check startup idea
        if not startup_idea or not startup_idea.strip():
            return {
                "is_valid": False,
                "reason": "Startup idea cannot be empty. Please describe your startup idea or problem.",
                "confidence": 1.0
            }
        
        idea_stripped = startup_idea.strip()
        
        # Length checks
        if len(idea_stripped) < 10:
            return {
                "is_valid": False,
                "reason": "Startup idea is too short. Please provide at least 10 characters describing your idea.",
                "confidence": 1.0
            }
        
        if len(idea_stripped) > 500:
            return {
                "is_valid": False,
                "reason": "Startup idea is too long. Please keep it under 500 characters.",
                "confidence": 1.0
            }
        
        # Check target market if provided
        if target_market and target_market.strip():
            market_stripped = target_market.strip()
            
            if len(market_stripped) > 200:
                return {
                    "is_valid": False,
                    "reason": "Target market description is too long. Please keep it under 200 characters.",
                    "confidence": 1.0
                }
        
        return {
            "is_valid": True,
            "reason": "Basic validation passed",
            "confidence": 0.5
        }
    
    @classmethod
    def _pattern_validation(cls, startup_idea: str, target_market: Optional[str]) -> Dict[str, Any]:
        """
        Pattern-based validation to detect obvious gibberish and inappropriate content
        """
        text = startup_idea.lower().strip()
        
        # Check for personal information patterns
        personal_patterns = [
            (r'\bmy name is\b', "Input contains personal information. Please describe a startup idea instead."),
            (r'\bi am\b.*\b(years old|from|live in)\b', "Input contains personal information. Please describe a startup idea instead."),
            (r'\bmy (phone|email|address)\b', "Input contains personal information. Please describe a startup idea instead."),
            (r'\bcall me\b', "Input contains personal information. Please describe a startup idea instead."),
            (r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b', "Input contains phone numbers. Please describe a startup idea instead."),
            (r'\b[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}\b', "Input contains email addresses. Please describe a startup idea instead.")
        ]
        
        for pattern, message in personal_patterns:
            if re.search(pattern, text):
                return {
                    "is_valid": False,
                    "reason": message,
                    "confidence": 0.95
                }
        
        # Check for casual conversation patterns
        casual_patterns = [
            (r'^\s*(hi|hello|hey)\s*$', "Input appears to be a greeting. Please describe your startup idea."),
            (r'^\s*(hi|hello|hey)\s*,', "Input appears to be a greeting. Please describe your startup idea."),
            (r'\bhow are you\b', "Input appears to be casual conversation. Please describe your startup idea."),
            (r'\bnice to meet\b', "Input appears to be casual conversation. Please describe your startup idea."),
            (r'\bwhat\'?s your name\b', "Input appears to be casual conversation. Please describe your startup idea.")
        ]
        
        for pattern, message in casual_patterns:
            if re.search(pattern, text):
                return {
                    "is_valid": False,
                    "reason": message,
                    "confidence": 0.95
                }
        
        # Check for test inputs
        test_patterns = [
            (r'^(test|testing)\s*$', "Input appears to be test content. Please describe a real startup idea."),
            (r'^(abc|123)+\s*$', "Input appears to be test content. Please describe a real startup idea."),
            (r'^[a-z]\s*$', "Input is too short. Please provide a meaningful startup idea description."),
            (r'^(asdf|qwerty|lorem ipsum)', "Input appears to be test content. Please describe a real startup idea."),
            (r'^(.)\1{5,}', "Input contains repeated characters. Please describe a real startup idea.")
        ]
        
        for pattern, message in test_patterns:
            if re.search(pattern, text):
                return {
                    "is_valid": False,
                    "reason": message,
                    "confidence": 0.95
                }
        
        # Check for keyboard mashing patterns
        keyboard_patterns = ['qwerty', 'asdfgh', 'zxcvbn', 'qazwsx', 'poiuyt']
        for pattern in keyboard_patterns:
            if pattern in text.replace(' ', ''):
                return {
                    "is_valid": False,
                    "reason": "Input appears to be random keyboard characters. Please describe a real startup idea.",
                    "confidence": 0.9
                }
        
        # Check for very short inputs (less than 3 words)
        words = text.split()
        if len(words) < 3:
            return {
                "is_valid": False,
                "reason": "Input is too brief. Please provide more details about your startup idea (at least 3 words).",
                "confidence": 0.8
            }
        
        # Check for excessive special characters (more than 30% of text)
        special_char_count = sum(1 for c in text if not c.isalnum() and not c.isspace())
        if len(text) > 0 and (special_char_count / len(text)) > 0.3:
            return {
                "is_valid": False,
                "reason": "Input contains too many special characters. Please describe your startup idea in plain text.",
                "confidence": 0.85
            }
        
        # Check for excessive numbers (more than 50% of text)
        number_count = sum(1 for c in text if c.isdigit())
        if len(text) > 0 and (number_count / len(text)) > 0.5:
            return {
                "is_valid": False,
                "reason": "Input contains too many numbers. Please describe your startup idea in words.",
                "confidence": 0.85
            }
        
        # Check target market if provided
        if target_market and target_market.strip():
            market_text = target_market.lower().strip()
            
            # Check for nonsensical target market
            if len(market_text) < 3:
                return {
                    "is_valid": False,
                    "reason": "Target market is too short. Please provide a meaningful target market description.",
                    "confidence": 0.9
                }
            
            # Check for repeated characters in target market
            if len(set(market_text.replace(' ', ''))) < 3:
                return {
                    "is_valid": False,
                    "reason": "Target market appears to be invalid. Please provide a real target market description.",
                    "confidence": 0.9
                }
            
            # Check for keyboard patterns in target market
            for pattern in keyboard_patterns:
                if pattern in market_text.replace(' ', ''):
                    return {
                        "is_valid": False,
                        "reason": "Target market appears to be random characters. Please provide a real target market description.",
                        "confidence": 0.9
                    }
        
        return {
            "is_valid": True,
            "reason": "Pattern validation passed",
            "confidence": 0.7
        }
    
    @classmethod
    async def _ai_validation(cls, startup_idea: str, target_market: Optional[str]) -> Dict[str, Any]:
        """
        AI-powered validation using LLM to understand semantic meaning
        """
        # Get available API keys
        api_keys = cls._get_api_keys()
        
        if not api_keys:
            logger.warning("No API keys available for AI validation - using rule-based validation only")
            return {
                "is_valid": True,
                "reason": "Input passed rule-based validation (AI validation unavailable)",
                "confidence": 0.6
            }
        
        # Create validation prompt
        validation_text = f"Startup Idea: {startup_idea}"
        if target_market:
            validation_text += f"\nTarget Market: {target_market}"
        
        prompt = f"""
You are a STRICT input validator for a customer insights analysis engine. Your job is to determine if user input describes a legitimate startup idea, product, or business problem that could benefit from customer insights analysis.

USER INPUT:
{validation_text}

VALIDATION CRITERIA:
✅ VALID inputs describe:
- Startup ideas or product concepts
- Business problems or opportunities
- Product features or services
- Market needs or gaps
- Customer pain points to solve
- Technology solutions or platforms
- Business models or value propositions
- Real products or services that could exist

❌ INVALID inputs include:
- Personal information (names, addresses, phone numbers, emails)
- Inappropriate or offensive content
- Random text or gibberish (keyboard mashing, repeated characters)
- Casual conversation or greetings
- Test inputs (test, testing, abc123)
- Non-business topics (personal relationships, entertainment preferences)
- Simple statements without business context
- Vague or meaningless phrases

TARGET MARKET VALIDATION (if provided):
- Must describe a real, identifiable group of people or businesses
- Should include demographics, psychographics, or industry
- REJECT random characters, keyboard mashing, or nonsensical text
- VALID examples: "working professionals 25-45", "small businesses", "college students", "healthcare providers"
- INVALID examples: "HAFFUUU", "asdfgh", "AAAAAAA", "qwerty123"

EXAMPLES:
✅ Valid: "AI-powered meal planning app for busy professionals"
✅ Valid: "Project management tool for remote teams"
✅ Valid: "Sustainable fashion marketplace for eco-conscious consumers"
✅ Valid: "Automated invoice processing for small businesses"
❌ Invalid: "My name is John Smith"
❌ Invalid: "I like pizza"
❌ Invalid: "asdfghjkl random text"
❌ Invalid: "hello world"
❌ Invalid: "test testing 123"
❌ Invalid: "Meal planning app" + target market: "HAFFUUU" (random characters)
❌ Invalid: "Business tool" + target market: "qwerty123" (keyboard mashing)

IMPORTANT:
- If target market is provided and appears to be gibberish, mark the ENTIRE input as invalid
- Be strict about target market validation - reject anything that doesn't look like a real demographic
- Focus on whether the input describes something that could realistically be a startup or product

Return ONLY this JSON format (no other text):
{{
    "is_valid": true/false,
    "reason": "Brief explanation of why input is valid/invalid",
    "confidence": 0.0-1.0
}}
"""
        
        payload = {
            "model": cls.MODEL_NAME,
            "messages": [
                {
                    "role": "system",
                    "content": "You are a strict input validator that determines if text describes legitimate startup ideas or products. You respond only with JSON."
                },
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.1,  # Low temperature for consistent validation
            "max_tokens": 150
        }
        
        # Try each API key until one works
        for key_index, api_key in enumerate(api_keys):
            logger.info(f"Trying AI validation with API key {key_index + 1}/{len(api_keys)}")
            
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }
            
            try:
                response = requests.post(cls.API_URL, headers=headers, json=payload, timeout=15)
                
                if response.status_code == 200:
                    output = response.json()["choices"][0]["message"]["content"].strip()
                    logger.info(f"AI validation response: {output}")
                    
                    try:
                        # Try to parse JSON directly
                        validation_data = json.loads(output)
                        
                        # Ensure required fields exist
                        if "is_valid" not in validation_data:
                            validation_data["is_valid"] = True
                        
                        if "reason" not in validation_data:
                            validation_data["reason"] = "Input appears to describe a startup idea"
                        
                        if "confidence" not in validation_data:
                            validation_data["confidence"] = 0.8
                        
                        logger.info(f"SUCCESS: AI validation completed with key {key_index + 1}")
                        return validation_data
                        
                    except json.JSONDecodeError:
                        logger.warning("Failed to parse validation JSON - trying to extract JSON from response")
                        # Try to extract JSON from the output using regex
                        json_match = re.search(r'\{[^{}]*"is_valid"[^{}]*\}', output, re.DOTALL)
                        if json_match:
                            try:
                                validation_data = json.loads(json_match.group())
                                if "confidence" not in validation_data:
                                    validation_data["confidence"] = 0.8
                                logger.info("Successfully extracted validation JSON from output")
                                return validation_data
                            except json.JSONDecodeError:
                                logger.error("Failed to extract valid validation JSON from output")
                        
                        # If JSON parsing fails, try next API key
                        logger.warning(f"JSON parsing failed with API key {key_index + 1} - trying next key")
                        continue
                
                elif response.status_code in [401, 429]:
                    logger.warning(f"API key {key_index + 1} failed with status {response.status_code} - trying next key")
                    continue
                
                else:
                    logger.warning(f"API key {key_index + 1} failed with status {response.status_code} - trying next key")
                    continue
                    
            except Exception as e:
                logger.error(f"Error with API key {key_index + 1}: {str(e)} - trying next key")
                continue
        
        # If all API keys failed, return success with low confidence
        # (pattern validation already passed, so input is probably okay)
        logger.warning("All API keys failed for AI validation - accepting input with low confidence")
        return {
            "is_valid": True,
            "reason": "Input passed pattern validation (AI validation unavailable)",
            "confidence": 0.6
        }
