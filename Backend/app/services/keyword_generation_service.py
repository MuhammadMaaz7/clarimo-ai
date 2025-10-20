"""
Keyword Generation Service - Integrates AI-powered keyword generation with database storage
"""
import requests
import json
import re
from typing import List, Dict, Any, Optional
import time
from datetime import datetime, timezone
import logging
import uuid

from app.db.database import generated_keywords_collection
from app.core.config import settings
import os

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class KeywordGenerationService:
    """Service for generating and storing AI-powered keywords based on user input"""
    
    # API Configuration - Support multiple API keys for failover
    API_URL = "https://openrouter.ai/api/v1/chat/completions"
    MODEL_NAME = "google/gemma-3-27b-it:free"
    
    @classmethod
    def _get_api_keys(cls) -> List[str]:
        """
        Get list of API keys from environment variables
        Supports multiple keys: OPENROUTER_API_KEY, OPENROUTER_API_KEY_2, OPENROUTER_API_KEY_3
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
        for i in range(2, 6):  # Support up to 5 keys (KEY_2 through KEY_5)
            key = os.getenv(f"OPENROUTER_API_KEY_{i}")
            if key and not any(placeholder in key for placeholder in [
                "REPLACE_WITH_YOUR_ACTUAL_API_KEY", 
                "REPLACE_WITH_BACKUP_KEY", 
                "your-api-key-here"
            ]):
                keys.append(key)
        
        return keys
    
    @classmethod
    async def generate_keywords_for_input(
        cls, 
        user_id: str, 
        input_id: str, 
        problem_description: str,
        domain: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate keywords for a user input and store them in the database
        
        Args:
            user_id: ID of the user
            input_id: ID of the user input
            problem_description: The main problem description
            domain: Optional domain context
            
        Returns:
            Dictionary with generated keywords and metadata
        """
        try:
            logger.info(f"Generating keywords for input {input_id} (user: {user_id})")
            
            # Use domain if provided, otherwise use problem description
            search_text = domain if domain and domain.strip() else problem_description
            
            # Generate keywords using AI
            keywords_data = await cls._generate_boolean_query(search_text)
            
            if not keywords_data:
                logger.warning(f"No keywords generated for input {input_id}")
                return {"success": False, "error": "Failed to generate keywords"}
            
            # Create database document
            keywords_doc = {
                "user_id": user_id,
                "input_id": input_id,
                "keywords_id": str(uuid.uuid4()),
                "problem_description": problem_description,
                "domain": domain,
                "search_text_used": search_text,
                "potential_subreddits": keywords_data.get("potential_subreddits", []),
                "domain_anchors": keywords_data.get("domain_anchors", []),
                "problem_phrases": keywords_data.get("problem_phrases", []),
                "generation_status": "completed",
                "created_at": datetime.now(timezone.utc),
                "updated_at": datetime.now(timezone.utc)
            }
            
            # Store in database
            result = generated_keywords_collection.insert_one(keywords_doc)
            
            if not result.inserted_id:
                raise Exception("Failed to store keywords in database")
            
            logger.info(f"Successfully generated and stored keywords for input {input_id}")
            
            # Return success response with generated data
            return {
                "success": True,
                "keywords_id": keywords_doc["keywords_id"],
                "data": {
                    "potential_subreddits": keywords_data["potential_subreddits"],
                    "domain_anchors": keywords_data["domain_anchors"],
                    "problem_phrases": keywords_data["problem_phrases"],
                    "subreddit_count": len(keywords_data["potential_subreddits"]),
                    "anchor_count": len(keywords_data["domain_anchors"]),
                    "phrase_count": len(keywords_data["problem_phrases"])
                },
                "created_at": keywords_doc["created_at"]
            }
            
        except Exception as e:
            logger.error(f"Error generating keywords for input {input_id}: {str(e)}")
            
            # Store error status in database
            try:
                error_doc = {
                    "user_id": user_id,
                    "input_id": input_id,
                    "keywords_id": str(uuid.uuid4()),
                    "problem_description": problem_description,
                    "domain": domain,
                    "search_text_used": search_text if 'search_text' in locals() else problem_description,
                    "potential_subreddits": [],
                    "domain_anchors": [],
                    "problem_phrases": [],
                    "generation_status": "failed",
                    "error_message": str(e),
                    "created_at": datetime.now(timezone.utc),
                    "updated_at": datetime.now(timezone.utc)
                }
                generated_keywords_collection.insert_one(error_doc)
            except Exception as db_error:
                logger.error(f"Failed to store error status: {str(db_error)}")
            
            return {"success": False, "error": str(e)}
    
    @classmethod
    async def _generate_boolean_query(cls, domain: str) -> Dict[str, List[str]]:
        """
        Generate keywords using AI API (adapted from your existing code)
        
        Args:
            domain: Domain or problem description to generate keywords for
            
        Returns:
            Dictionary with potential_subreddits, domain_anchors, and problem_phrases
        """
        if not domain or len(domain.strip()) < 2:
            return {"potential_subreddits": [], "domain_anchors": [], "problem_phrases": []}

        domain_cleaned = re.sub(r'[^a-zA-Z0-9\s]', '', domain.strip())
        
        # Get available API keys
        api_keys = cls._get_api_keys()
        
        if not api_keys:
            logger.error("No valid API keys found - cannot generate keywords")
            return {"potential_subreddits": [], "domain_anchors": [], "problem_phrases": []}

        prompt = f"""
        You are an expert in social listening, user sentiment mining, and Reddit search optimization.
        Your goal is to generate highly relevant subreddit and keyword lists that help analysts find 
        *authentic user complaints, frustrations, or problem discussions, unmet needs, and pain points*
         about tools, technologies, and ecosystems related to the given domain that could inspire startup ideas.

        USER INPUT DOMAIN: "{domain_cleaned}"

        🎯 OBJECTIVE
        Generate a JSON object with:
        1️⃣ Relevant subreddits where users discuss struggles, needs, or product gaps related to this domain.
        2️⃣ Domain anchors — tools, workflows, or activities tied to this domain.
        3️⃣ Problem phrases — natural, Reddit-style expressions that indicate pain points, confusion, or frustration.

         1️⃣ Potential Subreddits
        Generate **2-5 active, discussion-heavy subreddits** that meet these criteria:
        - People share *problems, feedback, or unmet needs* (not just news or memes)
        - Communities focused on building, improving, or struggling with tools, workflows, or careers in "{domain_cleaned}"
        - Examples: users sharing startup challenges, SaaS feedback, automation frustrations, business pain points, or workflow inefficiencies

        💡 Example categories:
        - Founders discussing product gaps → r/startups, r/Entrepreneur, r/SaaS, r/ProductManagement
        - Users complaining about tools → r/TechSupport, r/Productivity, r/AItools
        - Communities focused on domain pain points → r/DataIsBeautiful (for data), r/SmallBusiness, r/Freelance

        ---

         2️⃣ Domain Anchors
        Generate **8–15 anchors** representing:
        - Common tools or software in this domain that could inspire startup ideas.
        - Workflows or goals (e.g., "customer discovery", "automation", "analytics dashboard")
        - Broader ecosystem terms users associate with this space
        - Optional: related trends or buzzwords founders discuss

        💡 Examples:
        - For "AI startups": ["chatbot", "AI tool", "automation", "LLM", "GPT", "no-code", "API", "AI SaaS", "AI agents"]
        - For "health tech": ["telehealth", "fitness app", "mental health", "wearables", "wellness tracker", "doctor booking", "remote patient monitoring"]

        ---

         3️⃣ Problem Phrases
        Generate **10–20 short, casual Reddit-style frustration phrases of 2-3 words** users might say when complaining or describing pain points.

        Focus on human needs and inefficiencies — not just software bugs:
        - "too expensive"
        - "takes too long"
        - "hard to use"
        - "manual work"
        - "need better tool"
        - "can't track progress"
        - "no integrations"
        - "poor UX"
        - "overwhelming"
        - "waste of time"
        - "confusing setup"
        - "not scalable"

        💬 Example Output:
        ["slow", "expensive", "manual", "no automation", "hard to use", "bad UX", "poor support", "no insights", "waste of time", "not user friendly", "too complex"]

        ---

        📦 OUTPUT FORMAT
        Return **only** the following JSON (no text or explanations):

        {{
        "potential_subreddits": ["subreddit1", "subreddit2", ...],
        "domain_anchors": ["anchor1", "anchor2", ...],
        "problem_phrases": ["problem1", "problem2", ...]
        }}
        """
        
        payload = {
            "model": cls.MODEL_NAME,
            "messages": [
                {
                    "role": "system", 
                    "content": "You generate short, natural search phrases that real people use when discussing IT/software problems online. You avoid business jargon and focus on everyday language."
                },
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.6,  
            "max_tokens": 400,
            "timeout": 30
        }

        # Try each API key until one works
        for key_index, api_key in enumerate(api_keys):
            logger.info(f"Trying API key {key_index + 1}/{len(api_keys)} for: {domain_cleaned}")
            
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }
            
            # Retry logic for each API key
            max_retries = 2  # Reduced retries per key since we have multiple keys
            for attempt in range(max_retries):
                try:
                    logger.info(f"Sending request (key {key_index + 1}, attempt {attempt + 1})")
                    response = requests.post(cls.API_URL, headers=headers, json=payload, timeout=30)
                    logger.info(f"Response code: {response.status_code}")

                    if response.status_code == 200:
                        output = response.json()["choices"][0]["message"]["content"].strip()

                        try:
                            # Try to parse JSON directly
                            json_data = json.loads(output)
                        except json.JSONDecodeError:
                            logger.warning("Direct JSON parsing failed. Attempting to extract JSON from output...")
                            # Try to extract JSON from the output using regex
                            json_match = re.search(r'\{.*\}', output, re.DOTALL)
                            if json_match:
                                try:
                                    json_data = json.loads(json_match.group())
                                    logger.info("Successfully extracted JSON from output")
                                except json.JSONDecodeError:
                                    logger.error("Failed to extract valid JSON from output")
                                    json_data = {}
                            else:
                                json_data = {}

                        # Normalize the JSON structure
                        normalized_data = {
                            "potential_subreddits": [],
                            "domain_anchors": [], 
                            "problem_phrases": []
                        }

                        # Handle potential_subreddits
                        if "potential_subreddits" in json_data:
                            normalized_data["potential_subreddits"] = json_data["potential_subreddits"]
                        elif "subreddits" in json_data:
                            normalized_data["potential_subreddits"] = json_data["subreddits"]
                        
                        # Handle domain_anchors  
                        if "domain_anchors" in json_data:
                            normalized_data["domain_anchors"] = json_data["domain_anchors"]
                        elif "anchors" in json_data:
                            normalized_data["domain_anchors"] = json_data["anchors"]
                        
                        # Handle problem_phrases
                        if "problem_phrases" in json_data:
                            normalized_data["problem_phrases"] = json_data["problem_phrases"]
                        elif "problems" in json_data:
                            normalized_data["problem_phrases"] = json_data["problems"]

                        # Ensure all values are lists and clean them
                        for key in normalized_data:
                            if not isinstance(normalized_data[key], list):
                                normalized_data[key] = []
                            # Remove any non-string elements and strip whitespace
                            normalized_data[key] = [str(item).strip() for item in normalized_data[key] if item]

                        # Log success message with counts
                        sub_count = len(normalized_data["potential_subreddits"])
                        anchor_count = len(normalized_data["domain_anchors"])
                        problem_count = len(normalized_data["problem_phrases"])
                        logger.info(f"SUCCESS with API key {key_index + 1}: {sub_count} subreddits, {anchor_count} anchors, {problem_count} problem phrases")

                        return normalized_data

                    elif response.status_code == 401:
                        logger.warning(f"API key {key_index + 1} unauthorized (401) - trying next key")
                        break  # Try next API key
                    
                    elif response.status_code == 429:
                        logger.warning(f"API key {key_index + 1} rate limited (429) - trying next key")
                        break  # Try next API key
                    
                    else:
                        wait_time = 2 * (attempt + 1)
                        logger.warning(f"API key {key_index + 1} issue (status {response.status_code}, attempt {attempt+1}/{max_retries}). Retrying in {wait_time}s...")
                        time.sleep(wait_time)
                        continue

                except Exception as e:
                    logger.error(f"Error with API key {key_index + 1} (attempt {attempt+1}/{max_retries}): {e}")
                    if attempt < max_retries - 1:
                        time.sleep(2 * (attempt + 1))
            
            logger.warning(f"API key {key_index + 1} failed after {max_retries} attempts")

        logger.error(f"Failed to generate data for '{domain_cleaned}' after {max_retries} attempts.")
        return {"potential_subreddits": [], "domain_anchors": [], "problem_phrases": []}
    
    @classmethod
    async def get_keywords_by_input_id(cls, user_id: str, input_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve generated keywords for a specific user input
        
        Args:
            user_id: ID of the user
            input_id: ID of the user input
            
        Returns:
            Keywords document or None if not found
        """
        try:
            keywords = generated_keywords_collection.find_one({
                "user_id": user_id,
                "input_id": input_id
            })
            
            if keywords:
                # Convert ObjectId to string for JSON serialization
                keywords["_id"] = str(keywords["_id"])
                
            return keywords
            
        except Exception as e:
            logger.error(f"Error retrieving keywords for input {input_id}: {str(e)}")
            return None
    
    @classmethod
    async def get_user_keywords(cls, user_id: str, limit: int = 50, skip: int = 0) -> List[Dict[str, Any]]:
        """
        Retrieve all generated keywords for a user
        
        Args:
            user_id: ID of the user
            limit: Maximum number of records to return
            skip: Number of records to skip
            
        Returns:
            List of keyword documents
        """
        try:
            cursor = generated_keywords_collection.find(
                {"user_id": user_id}
            ).sort("created_at", -1).skip(skip).limit(limit)
            
            keywords_list = []
            for doc in cursor:
                doc["_id"] = str(doc["_id"])
                keywords_list.append(doc)
            
            return keywords_list
            
        except Exception as e:
            logger.error(f"Error retrieving keywords for user {user_id}: {str(e)}")
            return []
    
    @classmethod
    async def delete_keywords(cls, user_id: str, input_id: str) -> bool:
        """
        Delete generated keywords for a specific input
        
        Args:
            user_id: ID of the user
            input_id: ID of the user input
            
        Returns:
            True if deletion was successful, False otherwise
        """
        try:
            result = generated_keywords_collection.delete_one({
                "user_id": user_id,
                "input_id": input_id
            })
            
            return result.deleted_count > 0
            
        except Exception as e:
            logger.error(f"Error deleting keywords for input {input_id}: {str(e)}")
