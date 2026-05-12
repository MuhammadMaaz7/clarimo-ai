"""
Analysis Manager Service - Orchestrate the entire Customer Insights analysis pipeline
"""
import logging
import asyncio
import uuid
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone
from pathlib import Path

# Import database
from app.db.database import (
    customer_insights_analyses_collection,
    customer_raw_discussions_collection,
    audience_segments_collection,
    community_insights_collection
)

# Import models
from app.db.models.customer_insights_model import (
    CustomerInsightsAnalysisDB,
    RawDiscussionDB,
    AudienceSegmentDB,
    CommunityInsightDB
)

# Import services
from app.services.problem_discovery.reddit_fetching_service import reddit_fetching_service
from app.services.customer_insights.producthunt_fetcher import producthunt_fetcher
from app.services.customer_insights.community_discovery_service import community_discovery_service
from app.services.customer_insights.nlp_pipeline import nlp_pipeline
from app.services.customer_insights.audience_segmentation_service import audience_segmentation_service
from app.services.customer_insights.insights_extraction_service import insights_extraction_service

# Configure logging
logger = logging.getLogger(__name__)

class AnalysisManager:
    """Manager for orchestrating Customer Insights analysis pipeline"""
    
    async def start_analysis(
        self, 
        user_id: str, 
        startup_idea: str, 
        target_market: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Start a new customer insights analysis
        
        Args:
            user_id: User ID
            startup_idea: Startup idea to analyze
            target_market: Optional target market description
            
        Returns:
            Dictionary with analysis_id and initial status
        """
        try:
            analysis_id = str(uuid.uuid4())
            logger.info(f"Starting customer insights analysis {analysis_id} for user {user_id}")
            
            # Create analysis record in database
            analysis_record = CustomerInsightsAnalysisDB(
                analysis_id=analysis_id,
                user_id=user_id,
                startup_idea=startup_idea,
                target_market=target_market,
                status="processing",
                current_stage="data_collection",
                progress_percentage=0,
                created_at=datetime.utcnow()
            )
            
            # Insert into database (pymongo is synchronous, no await needed)
            customer_insights_analyses_collection.insert_one(
                analysis_record.model_dump(by_alias=True, exclude={"id"})
            )
            
            logger.info(f"Created analysis record {analysis_id}")
            
            # Start analysis pipeline in background
            asyncio.create_task(self.run_analysis_pipeline(analysis_id))
            
            return {
                "success": True,
                "analysis_id": analysis_id,
                "message": "Analysis started successfully",
                "status": "processing"
            }
            
        except Exception as e:
            logger.error(f"Error starting analysis: {str(e)}")
            return {
                "success": False,
                "message": f"Failed to start analysis: {str(e)}"
            }
    
    async def run_analysis_pipeline(self, analysis_id: str):
        """
        Run the complete analysis pipeline
        
        Pipeline stages:
        1. Data collection (Reddit + Product Hunt)
        2. Generate embeddings
        3. Cluster discussions
        4. Segment audience
        5. Extract insights
        6. Save results
        """
        try:
            logger.info(f"Running analysis pipeline for {analysis_id}")
            
            # Get analysis record
            analysis = customer_insights_analyses_collection.find_one({"analysis_id": analysis_id})
            if not analysis:
                logger.error(f"Analysis {analysis_id} not found")
                return
            
            user_id = analysis["user_id"]
            startup_idea = analysis["startup_idea"]
            target_market = analysis.get("target_market")  # Get target_market from analysis record
            
            # Stage 1: Data Collection (10% -> 50%)
            await self.update_analysis_status(
                analysis_id, "processing", "data_collection", 10
            )
            
            logger.info(f"[{analysis_id}] Stage 1: Collecting data from Reddit and Product Hunt...")
            
            # Fetch from Reddit (reuse existing service)
            reddit_discussions = await self._fetch_reddit_discussions(user_id, startup_idea)
            
            await self.update_analysis_status(
                analysis_id, "processing", "data_collection", 30
            )
            
            # Fetch from Product Hunt
            producthunt_discussions = await producthunt_fetcher.fetch_product_discussions(
                startup_idea, limit=50
            )
            
            await self.update_analysis_status(
                analysis_id, "processing", "data_collection", 50
            )
            
            # Combine all discussions
            all_discussions = reddit_discussions + producthunt_discussions
            
            if len(all_discussions) == 0:
                logger.warning(f"[{analysis_id}] No discussions found")
                await self.update_analysis_status(
                    analysis_id, "failed", "data_collection", 50,
                    error_message="No discussions found for the given startup idea"
                )
                return
            
            logger.info(f"[{analysis_id}] Collected {len(all_discussions)} discussions")
            
            # Save raw discussions to database
            await self._save_raw_discussions(analysis_id, all_discussions)
            
            # Update discussion counts
            customer_insights_analyses_collection.update_one(
                {"analysis_id": analysis_id},
                {"$set": {
                    "total_discussions": len(all_discussions),
                    "reddit_discussions": len(reddit_discussions),
                    "producthunt_discussions": len(producthunt_discussions)
                }}
            )
            
            # Stage 2: AI-Powered Insights Generation (50% -> 85%)
            await self.update_analysis_status(
                analysis_id, "processing", "insights_generation", 60
            )
            
            logger.info(f"[{analysis_id}] Stage 2: Generating AI-powered insights...")
            
            # Generate comprehensive insights using AI
            try:
                insights_result = await self._generate_ai_insights(
                    all_discussions, 
                    startup_idea,
                    target_market
                )
            except Exception as insights_error:
                logger.error(f"Error generating AI insights: {str(insights_error)}")
                # Fallback to basic insights
                insights_result = self._generate_basic_insights(all_discussions)
            
            await self.update_analysis_status(
                analysis_id, "processing", "finalizing", 90
            )
            
            # Stage 3: Save Results (90% -> 100%)
            logger.info(f"[{analysis_id}] Stage 3: Saving results...")
            
            # Calculate execution time
            execution_time = (datetime.utcnow() - analysis["created_at"]).total_seconds()
            
            # Update analysis record with results
            customer_insights_analyses_collection.update_one(
                {"analysis_id": analysis_id},
                {"$set": {
                    "status": "completed",
                    "current_stage": "completed",
                    "progress_percentage": 100,
                    "completed_at": datetime.utcnow(),
                    "execution_time": execution_time,
                    "insights": insights_result
                }}
            )
            
            logger.info(f"[{analysis_id}] Analysis completed successfully in {execution_time:.2f}s")
            
        except Exception as e:
            logger.error(f"Error in analysis pipeline for {analysis_id}: {str(e)}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            
            # Update status to failed
            await self.update_analysis_status(
                analysis_id, "failed", "error", 0,
                error_message=str(e)
            )
    
    async def _fetch_reddit_discussions(
        self, 
        user_id: str, 
        startup_idea: str
    ) -> List[Dict[str, Any]]:
        """Fetch discussions from Reddit using AI-powered keyword generation"""
        try:
            # Import the proper keyword generation service
            from app.services.problem_discovery.keyword_generation_service import KeywordGenerationService
            
            # Generate proper keywords using AI (same as Problem Discovery)
            logger.info(f"Generating AI-powered keywords for: {startup_idea[:100]}...")
            keywords_data = await KeywordGenerationService._generate_boolean_query(startup_idea)
            
            if not keywords_data or not any([
                keywords_data.get("domain_anchors"),
                keywords_data.get("problem_phrases"),
                keywords_data.get("potential_subreddits")
            ]):
                logger.warning("No keywords generated - using fallback")
                # Fallback to simple keywords
                keywords_data = {
                    "domain_anchors": startup_idea.split()[:5],
                    "problem_phrases": ["problem", "issue", "need", "looking for"],
                    "potential_subreddits": []
                }
            
            logger.info(f"Generated keywords: {len(keywords_data.get('domain_anchors', []))} anchors, "
                       f"{len(keywords_data.get('problem_phrases', []))} phrases, "
                       f"{len(keywords_data.get('potential_subreddits', []))} subreddits")
            
            # Use existing Reddit fetcher with proper keywords
            input_id = str(uuid.uuid4())
            reddit_data = await reddit_fetching_service.fetch_reddit_posts_for_keywords(
                user_id=user_id,
                input_id=input_id,
                keywords_data=keywords_data,
                queries_per_domain=5,  # Increased from 3
                per_query_limit=100    # Increased from 50
            )
            
            # Convert Reddit data to discussion format
            discussions = []
            
            # Extract from by_query results
            for query_result in reddit_data.get("by_query", []):
                for post in query_result.get("posts", []):
                    discussions.append({
                        "id": f"reddit_{post.get('id', '')}",
                        "title": post.get("title", ""),
                        "content": post.get("content", post.get("selftext", "")),
                        "url": post.get("url", ""),
                        "source": "reddit",
                        "community": post.get("subreddit", ""),
                        "created_at": post.get("created_utc", ""),
                        "score": post.get("score", 0),
                        "comments_count": post.get("num_comments", 0)
                    })
            
            # Extract from by_subreddit results
            for subreddit_result in reddit_data.get("by_subreddit", []):
                for post in subreddit_result.get("posts", []):
                    discussions.append({
                        "id": f"reddit_{post.get('id', '')}",
                        "title": post.get("title", ""),
                        "content": post.get("content", post.get("selftext", "")),
                        "url": post.get("url", ""),
                        "source": "reddit",
                        "community": post.get("subreddit", ""),
                        "created_at": post.get("created_utc", ""),
                        "score": post.get("score", 0),
                        "comments_count": post.get("num_comments", 0)
                    })
            
            # CRITICAL: Filter for relevance using AI
            logger.info(f"Fetched {len(discussions)} discussions, now filtering for relevance...")
            
            if len(discussions) > 0:
                relevant_discussions = await self._ai_smart_filter(discussions, startup_idea, keywords_data)
            else:
                relevant_discussions = []
            
            logger.info(f"Filtered to {len(relevant_discussions)} relevant discussions from Reddit")
            return relevant_discussions
            
        except Exception as e:
            logger.error(f"Error fetching Reddit discussions: {str(e)}")
            return []
    
    async def _save_raw_discussions(
        self, 
        analysis_id: str, 
        discussions: List[Dict[str, Any]]
    ):
        """Save raw discussions to database"""
        try:
            discussion_records = []
            
            for discussion in discussions:
                record = RawDiscussionDB(
                    analysis_id=analysis_id,
                    source=discussion.get("source", "unknown"),
                    discussion_id=discussion.get("id", ""),
                    title=discussion.get("title", ""),
                    content=discussion.get("content", ""),
                    url=discussion.get("url"),
                    created_at=datetime.utcnow(),
                    score=discussion.get("score", 0),
                    comments_count=discussion.get("comments_count", 0),
                    community=discussion.get("community"),
                    metadata=discussion.get("metadata")
                )
                
                discussion_records.append(
                    record.model_dump(by_alias=True, exclude={"id"})
                )
            
            if discussion_records:
                customer_raw_discussions_collection.insert_many(discussion_records)
                logger.info(f"Saved {len(discussion_records)} raw discussions")
                
        except Exception as e:
            logger.error(f"Error saving raw discussions: {str(e)}")
    
    async def _save_communities(
        self, 
        analysis_id: str, 
        communities: List[Dict[str, Any]]
    ):
        """Save communities to database"""
        try:
            community_records = []
            
            for community in communities:
                record = CommunityInsightDB(
                    analysis_id=analysis_id,
                    community_name=community["name"],
                    source=community["source"],
                    discussion_count=community["discussion_count"],
                    engagement_score=community["engagement_score"],
                    url=community.get("url"),
                    description=community.get("description"),
                    top_keywords=[]
                )
                
                community_records.append(
                    record.model_dump(by_alias=True, exclude={"id"})
                )
            
            if community_records:
                community_insights_collection.insert_many(community_records)
                logger.info(f"Saved {len(community_records)} communities")
                
        except Exception as e:
            logger.error(f"Error saving communities: {str(e)}")
    
    async def _create_simple_segments(
        self,
        discussions: List[Dict[str, Any]],
        communities: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Create audience segments without embeddings - fast method
        Groups by top communities and extracts characteristics
        """
        try:
            logger.info("Creating segments using fast community-based method...")
            
            # Group discussions by community
            community_groups = {}
            for discussion in discussions:
                community = discussion.get("community", "unknown")
                if community not in community_groups:
                    community_groups[community] = []
                community_groups[community].append(discussion)
            
            # Create segments from top communities
            segments = []
            top_communities = sorted(
                communities, 
                key=lambda x: x["discussion_count"], 
                reverse=True
            )[:5]  # Top 5 communities
            
            for idx, community in enumerate(top_communities):
                community_name = community["name"]
                community_discussions = community_groups.get(community_name, [])
                
                if not community_discussions:
                    continue
                
                # Extract pain points and interests from discussions
                pain_points = []
                interests = []
                
                for disc in community_discussions[:10]:  # Sample first 10
                    title = disc.get("title", "")
                    content = disc.get("content", "")
                    
                    # Simple heuristics for pain points
                    if any(word in title.lower() for word in ["problem", "issue", "help", "struggling", "difficult"]):
                        pain_points.append(title[:100])
                    
                    # Simple heuristics for interests
                    if any(word in title.lower() for word in ["looking for", "recommend", "best", "advice", "tips"]):
                        interests.append(title[:100])
                
                # Create segment
                segment = {
                    "segment_id": str(uuid.uuid4()),
                    "segment_name": f"{community_name} Community",
                    "summary": f"Active users in {community_name} discussing related topics",
                    "pain_points": pain_points[:5] if pain_points else ["No specific pain points identified"],
                    "interests": interests[:5] if interests else ["General interest in the topic"],
                    "discussion_count": len(community_discussions),
                    "cluster_id": idx
                }
                
                segments.append(segment)
            
            logger.info(f"Created {len(segments)} segments from top communities")
            return segments
            
        except Exception as e:
            logger.error(f"Error creating simple segments: {str(e)}")
            return []
    
    async def _ai_smart_filter(
        self,
        discussions: List[Dict[str, Any]],
        startup_idea: str,
        keywords_data: Dict[str, List[str]]
    ) -> List[Dict[str, Any]]:
        """
        Smart AI-powered filter with fallback to keyword matching
        Balances strictness with ensuring we get some results
        """
        try:
            from app.services.problem_discovery.keyword_generation_service import KeywordGenerationService
            import requests
            import json
            import re
            
            if len(discussions) == 0:
                return []
            
            logger.info(f"AI smart filtering {len(discussions)} discussions...")
            
            # Get API keys
            api_keys = KeywordGenerationService._get_api_keys()
            
            # Extract domain keywords for fallback
            domain_anchors = [anchor.lower() for anchor in keywords_data.get("domain_anchors", [])][:10]
            core_words = [
                word.lower() for word in startup_idea.split()
                if len(word) > 4 and word.lower() not in {
                    'the', 'and', 'for', 'with', 'that', 'this', 'from', 'have', 'will',
                    'features', 'include', 'connecting', 'platform', 'marketplace'
                }
            ][:5]
            relevant_keywords = set(domain_anchors + core_words)
            
            logger.info(f"Relevant keywords for fallback: {relevant_keywords}")
            
            # If no API keys, use keyword fallback immediately
            if not api_keys:
                logger.warning("No API keys - using keyword fallback")
                return self._keyword_fallback_filter(discussions, relevant_keywords)
            
            # Try AI filtering in batches
            batch_size = 20
            all_relevant = []
            ai_success = False
            
            for batch_start in range(0, min(len(discussions), 60), batch_size):  # Max 60 discussions
                batch = discussions[batch_start:batch_start + batch_size]
                
                # Create prompt with subreddit context
                discussion_list = []
                for idx, disc in enumerate(batch):
                    title = disc.get("title", "")[:150]
                    subreddit = disc.get("community", "unknown")
                    discussion_list.append(f"{idx+1}. r/{subreddit}: {title}")
                
                discussions_text = "\n".join(discussion_list)
                
                prompt = f"""Filter Reddit discussions for relevance to a startup idea.

STARTUP IDEA: "{startup_idea}"

DISCUSSIONS:
{discussions_text}

Return discussion numbers that are RELEVANT (same industry/domain).
Be reasonable - include discussions that could provide customer insights.

RELEVANT examples for "pet care marketplace":
✅ r/dogs, r/pets, r/DogAdvice, r/AskVet
✅ Discussions about pet problems, pet services, pet owners

NOT RELEVANT:
❌ r/nba, r/politics, r/gaming (different domains)
❌ r/pettyrevenge (different context)

JSON only: {{"relevant": [1, 2, 5]}}"""

                payload = {
                    "model": KeywordGenerationService.MODEL_NAME,
                    "messages": [
                        {"role": "system", "content": "You filter discussions. Respond with JSON only."},
                        {"role": "user", "content": prompt}
                    ],
                    "temperature": 0.3,
                    "max_tokens": 150
                }
                
                # Try API keys for this batch
                batch_relevant = []
                for api_key in api_keys:
                    headers = {
                        "Authorization": f"Bearer {api_key}",
                        "Content-Type": "application/json"
                    }
                    
                    try:
                        response = requests.post(
                            KeywordGenerationService.API_URL,
                            headers=headers,
                            json=payload,
                            timeout=15
                        )
                        
                        if response.status_code == 200:
                            output = response.json()["choices"][0]["message"]["content"].strip()
                            
                            # Try to parse JSON
                            try:
                                result = json.loads(output)
                            except:
                                json_match = re.search(r'\{[^{}]*"relevant"[^{}]*\}', output, re.DOTALL)
                                if json_match:
                                    result = json.loads(json_match.group())
                                else:
                                    continue
                            
                            relevant_indices = result.get("relevant", [])
                            for idx in relevant_indices:
                                if 1 <= idx <= len(batch):
                                    batch_relevant.append(batch[idx - 1])
                            
                            ai_success = True
                            logger.info(f"Batch: {len(batch_relevant)}/{len(batch)} relevant")
                            break
                            
                    except Exception as e:
                        continue
                
                all_relevant.extend(batch_relevant)
                await asyncio.sleep(0.3)
            
            # If AI worked and found some results, return them
            if ai_success and len(all_relevant) > 0:
                logger.info(f"AI filter: {len(all_relevant)} relevant discussions")
                return all_relevant
            
            # Fallback to keyword matching if AI failed or found nothing
            logger.warning(f"AI filter found {len(all_relevant)} results, using keyword fallback")
            return self._keyword_fallback_filter(discussions, relevant_keywords)
            
        except Exception as e:
            logger.error(f"Error in AI smart filter: {str(e)}")
            # Fallback to keyword matching
            return self._keyword_fallback_filter(discussions, relevant_keywords)
    
    def _keyword_fallback_filter(
        self,
        discussions: List[Dict[str, Any]],
        relevant_keywords: set
    ) -> List[Dict[str, Any]]:
        """
        Fallback keyword-based filter when AI is unavailable
        """
        try:
            logger.info(f"Using keyword fallback filter with {len(relevant_keywords)} keywords")
            
            filtered = []
            for discussion in discussions:
                title = discussion.get("title", "").lower()
                content = discussion.get("content", "")[:500].lower()
                subreddit = discussion.get("community", "").lower()
                combined = f"{title} {content} {subreddit}"
                
                # Count keyword matches
                matches = sum(1 for keyword in relevant_keywords if keyword in combined)
                
                # Keep if has at least 2 keyword matches
                if matches >= 2:
                    filtered.append(discussion)
            
            logger.info(f"Keyword fallback: {len(filtered)}/{len(discussions)} discussions kept")
            
            # If still too few, relax to 1 match
            if len(filtered) < 10:
                logger.warning("Relaxing keyword filter to 1 match")
                filtered = []
                for discussion in discussions:
                    title = discussion.get("title", "").lower()
                    content = discussion.get("content", "")[:500].lower()
                    subreddit = discussion.get("community", "").lower()
                    combined = f"{title} {content} {subreddit}"
                    
                    matches = sum(1 for keyword in relevant_keywords if keyword in combined)
                    if matches >= 1:
                        filtered.append(discussion)
            
            return filtered[:50]  # Cap at 50
            
        except Exception as e:
            logger.error(f"Error in keyword fallback: {str(e)}")
            return discussions[:30]  # Return first 30 as last resort
    
    async def _generate_ai_insights(
        self,
        discussions: List[Dict[str, Any]],
        startup_idea: str,
        target_market: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate comprehensive insights using AI instead of showing raw communities
        Returns actionable insights and only highly relevant community links
        """
        try:
            import requests
            import json
            import re
            import os
            
            logger.info(f"Generating AI insights from {len(discussions)} discussions...")
            
            # Get Groq API keys
            api_keys = []
            for i in range(1, 6):
                if i == 1:
                    key = os.getenv("GROQ_API_KEY")
                else:
                    key = os.getenv(f"GROQ_API_KEY_{i}")
                
                if key and key not in ["your-fourth-groq-key-here", "your-fifth-groq-key-here"]:
                    api_keys.append(key)
            
            if not api_keys:
                logger.warning("No Groq API keys found")
                return self._generate_basic_insights(discussions)
            
            logger.info(f"Found {len(api_keys)} Groq API keys for insights generation")
            
            # Sample discussions for AI analysis (max 30)
            sampled = discussions[:30]
            
            # Extract community information
            community_counts = {}
            for disc in discussions:
                comm = disc.get("community", "unknown")
                community_counts[comm] = community_counts.get(comm, 0) + 1
            
            top_communities = sorted(community_counts.items(), key=lambda x: x[1], reverse=True)[:10]
            
            # Prepare discussion samples
            discussion_samples = []
            for disc in sampled[:15]:
                title = disc.get("title", "")[:150]
                content = disc.get("content", "")[:200]
                subreddit = disc.get("community", "")
                discussion_samples.append(f"- r/{subreddit}: {title}")
            
            discussions_text = "\n".join(discussion_samples)
            communities_text = "\n".join([f"- r/{comm} ({count} discussions)" for comm, count in top_communities])
            
            target_info = f"\nTarget Market: {target_market}" if target_market else ""
            
            prompt = f"""Analyze customer discussions for a startup idea and provide actionable insights.

STARTUP IDEA:
{startup_idea}{target_info}

TOP COMMUNITIES FOUND:
{communities_text}

SAMPLE DISCUSSIONS:
{discussions_text}

Generate a comprehensive analysis with:

1. **Customer Segments** (2-4 distinct groups):
   - Who they are
   - Their main pain points
   - What they're looking for

2. **Key Insights**:
   - Main problems customers face
   - Unmet needs in the market
   - Common frustrations or complaints

3. **Recommended Communities** (ONLY if highly relevant):
   - List 3-5 subreddits that are DIRECTLY related to the startup idea
   - Only include communities where the target audience actively discusses related problems
   - Format: r/subredditname - brief description

4. **Actionable Recommendations**:
   - What features to prioritize
   - How to position the product
   - Where to find early adopters

Be specific and actionable. Focus on insights that help validate and build the product.

Return ONLY valid JSON (no markdown, no code blocks):
{{
  "customer_segments": [
    {{"name": "segment name", "description": "who they are", "pain_points": ["point1", "point2"], "needs": ["need1", "need2"]}}
  ],
  "key_insights": {{
    "main_problems": ["problem1", "problem2"],
    "unmet_needs": ["need1", "need2"],
    "common_frustrations": ["frustration1", "frustration2"]
  }},
  "recommended_communities": [
    {{"name": "subreddit", "url": "https://reddit.com/r/subreddit", "description": "why relevant", "relevance": "high"}}
  ],
  "recommendations": ["recommendation1", "recommendation2"]
}}"""

            payload = {
                "model": "llama-3.3-70b-versatile",  # Groq's best model
                "messages": [
                    {"role": "system", "content": "You are an expert at analyzing customer discussions and generating actionable startup insights. Respond with valid JSON only, no markdown formatting."},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.4,
                "max_tokens": 2000
            }
            
            # Try Groq API keys
            for key_index, api_key in enumerate(api_keys):
                headers = {
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                }
                
                try:
                    logger.info(f"Trying Groq API key {key_index + 1}/{len(api_keys)}")
                    response = requests.post(
                        "https://api.groq.com/openai/v1/chat/completions",
                        headers=headers,
                        json=payload,
                        timeout=30
                    )
                    
                    if response.status_code == 200:
                        output = response.json()["choices"][0]["message"]["content"].strip()
                        
                        logger.info(f"Groq response received: {output[:200]}...")
                        
                        # Remove markdown code blocks if present
                        output = re.sub(r'^```json\s*', '', output)
                        output = re.sub(r'\s*```$', '', output)
                        output = output.strip()
                        
                        try:
                            insights = json.loads(output)
                            logger.info("✅ Successfully generated AI insights with Groq")
                            return insights
                        except json.JSONDecodeError as json_err:
                            logger.error(f"JSON decode error: {str(json_err)}")
                            logger.error(f"Raw output: {output[:500]}")
                            # Try to extract JSON
                            json_match = re.search(r'\{.*\}', output, re.DOTALL)
                            if json_match:
                                try:
                                    insights = json.loads(json_match.group())
                                    logger.info("✅ Successfully extracted AI insights from response")
                                    return insights
                                except Exception as extract_err:
                                    logger.error(f"Failed to extract JSON: {str(extract_err)}")
                        continue
                    else:
                        logger.error(f"Groq API returned status {response.status_code}: {response.text[:200]}")
                        continue
                    
                except Exception as e:
                    logger.error(f"Error with Groq API key {key_index + 1}: {str(e)}")
                    import traceback
                    logger.error(f"Traceback: {traceback.format_exc()}")
                    continue
            
            # Fallback to basic insights
            logger.warning("All Groq API keys failed, using basic insights")
            return self._generate_basic_insights(discussions)
            
        except Exception as e:
            logger.error(f"Error in AI insights generation: {str(e)}")
            return self._generate_basic_insights(discussions)
    
    def _generate_basic_insights(self, discussions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate basic insights when AI is unavailable"""
        # Count communities
        community_counts = {}
        for disc in discussions:
            comm = disc.get("community", "unknown")
            community_counts[comm] = community_counts.get(comm, 0) + 1
        
        top_communities = sorted(community_counts.items(), key=lambda x: x[1], reverse=True)[:5]
        
        return {
            "customer_segments": [
                {
                    "name": "General Users",
                    "description": "Users discussing related topics",
                    "pain_points": ["Various challenges identified in discussions"],
                    "needs": ["Solutions to common problems"]
                }
            ],
            "key_insights": {
                "main_problems": ["Analysis based on discussion patterns"],
                "unmet_needs": ["Opportunities identified in conversations"],
                "common_frustrations": ["User feedback from communities"]
            },
            "recommended_communities": [
                {
                    "name": comm,
                    "url": f"https://reddit.com/r/{comm}",
                    "description": f"Active community with {count} related discussions",
                    "relevance": "medium"
                }
                for comm, count in top_communities
            ],
            "recommendations": [
                "Engage with users in identified communities",
                "Validate assumptions through direct conversations",
                "Monitor discussions for emerging needs"
            ]
        }
    
    async def _save_segments(
        self, 
        analysis_id: str, 
        segments: List[Dict[str, Any]]
    ):
        """Save audience segments to database"""
        try:
            segment_records = []
            
            for segment in segments:
                record = AudienceSegmentDB(
                    analysis_id=analysis_id,
                    segment_id=segment.get("segment_id", str(uuid.uuid4())),
                    segment_name=segment["segment_name"],
                    summary=segment["summary"],
                    pain_points=segment["pain_points"],
                    interests=segment["interests"],
                    discussion_ids=segment.get("discussion_ids", []),
                    discussion_count=segment["discussion_count"],
                    cluster_id=segment.get("cluster_id")
                )
                
                segment_records.append(
                    record.model_dump(by_alias=True, exclude={"id"})
                )
            
            if segment_records:
                audience_segments_collection.insert_many(segment_records)
                logger.info(f"Saved {len(segment_records)} audience segments")
                
        except Exception as e:
            logger.error(f"Error saving segments: {str(e)}")
    
    async def update_analysis_status(
        self, 
        analysis_id: str, 
        status: str, 
        stage: str, 
        progress: int,
        error_message: Optional[str] = None
    ):
        """Update analysis status in database"""
        try:
            update_data = {
                "status": status,
                "current_stage": stage,
                "progress_percentage": progress
            }
            
            if error_message:
                update_data["error_message"] = error_message
            
            customer_insights_analyses_collection.update_one(
                {"analysis_id": analysis_id},
                {"$set": update_data}
            )
            
            logger.info(f"Updated analysis {analysis_id}: {status} - {stage} ({progress}%)")
            
        except Exception as e:
            logger.error(f"Error updating analysis status: {str(e)}")
    
    async def get_analysis_results(
        self, 
        analysis_id: str, 
        user_id: str
    ) -> Optional[Dict[str, Any]]:
        """Get analysis results"""
        try:
            analysis = customer_insights_analyses_collection.find_one({
                "analysis_id": analysis_id,
                "user_id": user_id
            })
            
            if not analysis:
                return None
            
            return {
                "analysis_id": analysis["analysis_id"],
                "startup_idea": analysis["startup_idea"],
                "target_market": analysis.get("target_market"),
                "status": analysis["status"],
                "current_stage": analysis.get("current_stage"),
                "progress_percentage": analysis.get("progress_percentage", 0),
                "created_at": analysis["created_at"],
                "completed_at": analysis.get("completed_at"),
                "execution_time": analysis.get("execution_time"),
                "total_discussions": analysis.get("total_discussions", 0),
                "insights": analysis.get("insights", {}),
                "error_message": analysis.get("error_message")
            }
            
        except Exception as e:
            logger.error(f"Error getting analysis results: {str(e)}")
            return None
    
    async def get_analysis_history(self, user_id: str) -> List[Dict[str, Any]]:
        """Get analysis history for a user"""
        try:
            # Find all analyses for the user
            cursor = customer_insights_analyses_collection.find(
                {"user_id": user_id}
            ).sort("created_at", -1).limit(50)
            
            # Convert cursor to list (synchronous operation)
            analyses = []
            for doc in cursor:
                analyses.append(doc)
            
            logger.info(f"Found {len(analyses)} analyses for user {user_id}")
            
            # Build history response
            history = []
            for analysis in analyses:
                # Get counts from the analysis document
                communities = analysis.get("communities", [])
                segments = analysis.get("segments", [])
                
                history_item = {
                    "analysis_id": analysis["analysis_id"],
                    "startup_idea": analysis["startup_idea"],
                    "status": analysis["status"],
                    "created_at": analysis["created_at"].isoformat() if hasattr(analysis["created_at"], "isoformat") else str(analysis["created_at"]),
                    "completed_at": analysis["completed_at"].isoformat() if analysis.get("completed_at") and hasattr(analysis["completed_at"], "isoformat") else None,
                    "communities_found": len(communities) if isinstance(communities, list) else 0,
                    "segments_found": len(segments) if isinstance(segments, list) else 0
                }
                history.append(history_item)
            
            logger.info(f"Returning {len(history)} history items")
            return history
            
        except Exception as e:
            logger.error(f"Error getting analysis history: {str(e)}", exc_info=True)
            return []

# Create global instance
analysis_manager = AnalysisManager()
