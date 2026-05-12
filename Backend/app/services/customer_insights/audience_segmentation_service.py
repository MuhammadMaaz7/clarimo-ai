"""
Audience Segmentation Service - Convert clusters into meaningful audience segments with LLM labeling
"""
import logging
import json
import asyncio
from typing import List, Dict, Any, Optional
import httpx
from collections import Counter

# Import LLM configuration
from app.core.llm_config import LLMConfig

# Configure logging
logger = logging.getLogger(__name__)

# LLM Prompt Template for Segment Labeling
SEGMENT_LABELING_PROMPT = """Analyze these customer discussions and create an audience segment profile.

Discussions:
{sample_discussions}

Provide a JSON response with:
1. segment_name: A concise 2-4 word name for this audience segment
2. summary: A 1-2 sentence description of this segment
3. pain_points: List of 3-5 main pain points or frustrations
4. interests: List of 3-5 main interests or needs

Format your response as valid JSON only, no additional text:
{{
  "segment_name": "...",
  "summary": "...",
  "pain_points": ["...", "...", "..."],
  "interests": ["...", "...", "..."]
}}"""

class AudienceSegmentationService:
    """Service for converting discussion clusters into audience segments"""
    
    def __init__(self):
        self.llm_config = LLMConfig()
    
    async def segment_audience(
        self, 
        discussions: List[Dict[str, Any]], 
        cluster_labels: List[int]
    ) -> List[Dict[str, Any]]:
        """
        Convert clustered discussions into audience segments
        
        Args:
            discussions: List of discussion dictionaries
            cluster_labels: List of cluster labels (same length as discussions)
            
        Returns:
            List of audience segment dictionaries
        """
        try:
            logger.info(f"Segmenting {len(discussions)} discussions into audience segments...")
            
            # Group discussions by cluster
            clusters = {}
            for discussion, label in zip(discussions, cluster_labels):
                if label == -1:  # Skip noise cluster
                    continue
                
                if label not in clusters:
                    clusters[label] = []
                
                clusters[label].append(discussion)
            
            logger.info(f"Found {len(clusters)} clusters to segment")
            
            # Generate segments for each cluster
            segments = []
            for cluster_id, cluster_discussions in clusters.items():
                logger.info(f"Processing cluster {cluster_id} with {len(cluster_discussions)} discussions")
                
                # Generate segment using LLM
                segment = await self.generate_segment_labels(cluster_discussions)
                
                if segment:
                    segment["cluster_id"] = cluster_id
                    segment["discussion_count"] = len(cluster_discussions)
                    segment["discussion_ids"] = [d.get("id") for d in cluster_discussions]
                    segments.append(segment)
                
                # Rate limiting
                await asyncio.sleep(0.5)
            
            logger.info(f"Generated {len(segments)} audience segments")
            return segments
            
        except Exception as e:
            logger.error(f"Error segmenting audience: {str(e)}")
            return []
    
    async def generate_segment_labels(
        self, 
        cluster_discussions: List[Dict[str, Any]]
    ) -> Optional[Dict[str, Any]]:
        """
        Generate segment labels using LLM
        
        Args:
            cluster_discussions: List of discussions in this cluster
            
        Returns:
            Dictionary with segment_name, summary, pain_points, interests
        """
        try:
            # Sample discussions for LLM (max 10 to keep prompt short)
            sample_size = min(10, len(cluster_discussions))
            sample_discussions = cluster_discussions[:sample_size]
            
            # Format discussions for prompt
            formatted_discussions = []
            for i, discussion in enumerate(sample_discussions, 1):
                title = discussion.get("title", "")
                content = discussion.get("content", "")
                text = f"{title} {content}".strip()
                
                # Truncate long discussions
                if len(text) > 300:
                    text = text[:300] + "..."
                
                formatted_discussions.append(f"{i}. {text}")
            
            discussions_text = "\n".join(formatted_discussions)
            
            # Create prompt
            prompt = SEGMENT_LABELING_PROMPT.format(sample_discussions=discussions_text)
            
            # Call LLM
            response = await self._call_llm(prompt)
            
            if response:
                # Parse JSON response
                try:
                    segment_data = json.loads(response)
                    
                    # Validate required fields
                    if all(key in segment_data for key in ["segment_name", "summary", "pain_points", "interests"]):
                        logger.info(f"Generated segment: {segment_data['segment_name']}")
                        return segment_data
                    else:
                        logger.warning("LLM response missing required fields")
                        return self._generate_fallback_segment(cluster_discussions)
                        
                except json.JSONDecodeError as e:
                    logger.warning(f"Failed to parse LLM response as JSON: {str(e)}")
                    return self._generate_fallback_segment(cluster_discussions)
            else:
                logger.warning("No response from LLM")
                return self._generate_fallback_segment(cluster_discussions)
                
        except Exception as e:
            logger.error(f"Error generating segment labels: {str(e)}")
            return self._generate_fallback_segment(cluster_discussions)
    
    async def _call_llm(self, prompt: str) -> Optional[str]:
        """Call LLM API for segment labeling"""
        try:
            api_url = self.llm_config.get_api_url()
            headers = self.llm_config.get_headers()
            
            payload = {
                "model": self.llm_config.MODEL,
                "messages": [
                    {
                        "role": "system",
                        "content": "You are an expert at analyzing customer discussions and identifying audience segments. Always respond with valid JSON only."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                "temperature": 0.3,
                "max_tokens": 500
            }
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    api_url,
                    json=payload,
                    headers=headers
                )
                
                response.raise_for_status()
                data = response.json()
                
                # Extract response text
                if "choices" in data and len(data["choices"]) > 0:
                    content = data["choices"][0].get("message", {}).get("content", "")
                    return content.strip()
                
                return None
                
        except httpx.HTTPStatusError as e:
            logger.error(f"LLM API error: {e.response.status_code} - {e.response.text}")
            return None
        except Exception as e:
            logger.error(f"Error calling LLM: {str(e)}")
            return None
    
    def _generate_fallback_segment(
        self, 
        cluster_discussions: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Generate fallback segment using simple heuristics"""
        try:
            logger.info("Generating fallback segment using heuristics")
            
            # Extract pain points and interests from discussions
            pain_points = self.extract_pain_points(cluster_discussions)
            interests = self.identify_interests(cluster_discussions)
            
            # Generate simple segment name
            segment_name = f"Segment {len(cluster_discussions)} users"
            if pain_points:
                segment_name = f"Users with {pain_points[0]}"
            
            # Generate summary
            summary = f"A group of {len(cluster_discussions)} users discussing related topics."
            
            return {
                "segment_name": segment_name,
                "summary": summary,
                "pain_points": pain_points[:5],
                "interests": interests[:5]
            }
            
        except Exception as e:
            logger.error(f"Error generating fallback segment: {str(e)}")
            return {
                "segment_name": "Unknown Segment",
                "summary": "Unable to generate segment profile",
                "pain_points": [],
                "interests": []
            }
    
    def extract_pain_points(self, discussions: List[Dict[str, Any]]) -> List[str]:
        """Extract pain points from discussions using keyword matching"""
        try:
            pain_keywords = [
                "problem", "issue", "difficult", "hard", "frustrating", "annoying",
                "slow", "expensive", "complicated", "confusing", "broken", "bad",
                "hate", "dislike", "struggle", "challenge", "pain", "trouble"
            ]
            
            pain_points = []
            
            for discussion in discussions:
                text = f"{discussion.get('title', '')} {discussion.get('content', '')}".lower()
                
                for keyword in pain_keywords:
                    if keyword in text:
                        # Extract sentence containing keyword
                        sentences = text.split('.')
                        for sentence in sentences:
                            if keyword in sentence:
                                pain_points.append(sentence.strip())
                                break
            
            # Return most common pain points
            if pain_points:
                pain_counter = Counter(pain_points)
                return [pain for pain, count in pain_counter.most_common(5)]
            
            return ["No specific pain points identified"]
            
        except Exception as e:
            logger.error(f"Error extracting pain points: {str(e)}")
            return []
    
    def identify_interests(self, discussions: List[Dict[str, Any]]) -> List[str]:
        """Identify interests from discussions using keyword matching"""
        try:
            interest_keywords = [
                "want", "need", "looking for", "interested in", "love", "like",
                "prefer", "wish", "hope", "desire", "seeking", "searching"
            ]
            
            interests = []
            
            for discussion in discussions:
                text = f"{discussion.get('title', '')} {discussion.get('content', '')}".lower()
                
                for keyword in interest_keywords:
                    if keyword in text:
                        # Extract sentence containing keyword
                        sentences = text.split('.')
                        for sentence in sentences:
                            if keyword in sentence:
                                interests.append(sentence.strip())
                                break
            
            # Return most common interests
            if interests:
                interest_counter = Counter(interests)
                return [interest for interest, count in interest_counter.most_common(5)]
            
            return ["No specific interests identified"]
            
        except Exception as e:
            logger.error(f"Error identifying interests: {str(e)}")
            return []

# Create global instance
audience_segmentation_service = AudienceSegmentationService()
