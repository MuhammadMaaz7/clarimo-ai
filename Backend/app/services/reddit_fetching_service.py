"""
Reddit Fetching Service - Integrates Reddit post extraction with user input workflow
"""
import os
import re
import json
import time
import random
import asyncio
import uuid
import logging
from typing import List, Dict, Any, Optional, Set, Tuple
from datetime import datetime, timezone
from pathlib import Path

from app.services.processing_lock_service import processing_lock_service, ProcessingStage
from app.services.user_input_service import UserInputService

# Configure logging
logger = logging.getLogger(__name__)

# Try import praw (support dry-run if absent)
try:
    import praw
    import prawcore
    PRAW_AVAILABLE = True
except ImportError:
    praw = None
    prawcore = None
    PRAW_AVAILABLE = False
    logger.warning("PRAW not installed - Reddit fetching will run in dry-run mode")

class RedditFetchingService:
    """Service for fetching Reddit posts based on generated keywords"""
    
    def __init__(self):
        self.reddit = None
        self._initialize_reddit()
    
    def _initialize_reddit(self):
        """Initialize Reddit API connection"""
        if not PRAW_AVAILABLE:
            logger.warning("PRAW not available - running in dry-run mode")
            return
            
        # Get Reddit credentials from environment
        client_id = os.getenv("REDDIT_CLIENT_ID")
        client_secret = os.getenv("REDDIT_CLIENT_SECRET")
        user_agent = os.getenv("REDDIT_USER_AGENT", "RedditFetcher/1.0")
        
        if client_id and client_secret:
            try:
                self.reddit = praw.Reddit(
                    client_id=client_id,
                    client_secret=client_secret,
                    user_agent=user_agent,
                    check_for_async=False
                )
                logger.info("Reddit API initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize Reddit API: {e}")
                self.reddit = None
        else:
            logger.warning("Reddit credentials not found - running in dry-run mode")
    
    @staticmethod
    def clean_subreddit_name(subreddit: str) -> str:
        """Clean subreddit name format"""
        if not isinstance(subreddit, str):
            return ""
        
        cleaned = subreddit.strip()
        # Remove r/ or /r/ prefixes
        cleaned = re.sub(r'^/?r/', '', cleaned, flags=re.IGNORECASE)
        # Remove any remaining spaces
        cleaned = cleaned.replace(" ", "")
        return cleaned
    
    @staticmethod
    def quote_if_needed(term: str) -> str:
        """Quote search terms if they contain spaces or special characters"""
        if not term:
            return ""
            
        cleaned_term = term.strip().replace('"', '\\"')
        
        # Quote if contains spaces or special characters that need grouping
        if any(char in cleaned_term for char in " -./"):
            return f'"{cleaned_term}"'
        return cleaned_term
    
    @staticmethod
    def build_consistent_query(anchors: List[str], problems: List[str]) -> str:
        """Build a lucene query: (anchor1 OR anchor2) AND (problem1 OR problem2)"""
        if not anchors or not problems:
            return ""

        # Clean and quote terms
        anchor_terms = [RedditFetchingService.quote_if_needed(anchor) for anchor in anchors if anchor]
        problem_terms = [RedditFetchingService.quote_if_needed(problem) for problem in problems if problem]
        
        if not anchor_terms or not problem_terms:
            return ""

        # Build query parts
        anchor_part = " OR ".join(anchor_terms)
        problem_part = " OR ".join(problem_terms)
        
        # Add parentheses for multiple terms
        if len(anchor_terms) > 1:
            anchor_part = f"({anchor_part})"
        if len(problem_terms) > 1:
            problem_part = f"({problem_part})"
            
        return f"{anchor_part} AND {problem_part}"
    
    def _parse_created_utc_from_praw(self, post) -> Optional[str]:
        """Parse creation timestamp from Reddit post"""
        try:
            timestamp = getattr(post, "created_utc", None)
            if timestamp:
                dt = datetime.fromtimestamp(float(timestamp), tz=timezone.utc)
                return dt.isoformat().replace("+00:00", "Z")
        except (ValueError, TypeError, OSError):
            pass
        return None
    
    def _post_to_dict_fast(self, post) -> Dict[str, Any]:
        """Convert Reddit post to dictionary (optimized without comments)"""
        try:
            post_id = getattr(post, "id", None) or getattr(post, "name", "")
            title = getattr(post, "title", "") or ""
            selftext = getattr(post, "selftext", "") or ""
            url = getattr(post, "url", "") or ""
            
            subreddit_obj = getattr(post, "subreddit", None)
            subreddit_name = getattr(subreddit_obj, "display_name", "") if subreddit_obj else "unknown"
            
            return {
                "id": post_id,
                "title": title,
                "content": selftext,
                "url": url,
                "subreddit": subreddit_name,
                "created_utc": self._parse_created_utc_from_praw(post),
                "score": getattr(post, "score", 0),
                "num_comments": getattr(post, "num_comments", 0),
                "upvote_ratio": getattr(post, "upvote_ratio", 1.0),
                "comments": []  # Empty for performance
            }
        except Exception as e:
            logger.warning(f"Error converting post to dict: {e}")
            return {}
    
    def _run_lucene_search(self, query: str, subreddit: str = "all", limit: int = 100, time_filter: str = "year") -> List[Any]:
        """Run Reddit search with lucene query"""
        if self.reddit is None:
            logger.info(f"[DRY RUN] Would search: {query}")
            return []
        
        try:
            logger.info(f"[REDDIT SEARCH] Query: {query[:100]}...")
            subreddit_obj = self.reddit.subreddit(subreddit)
            posts = list(subreddit_obj.search(
                query=query, 
                time_filter=time_filter, 
                limit=limit, 
                syntax='lucene'
            ))
            logger.info(f"Found {len(posts)} posts for query: {query[:50]}...")
            return posts
        except Exception as e:
            logger.error(f"Search failed for query '{query[:50]}...': {e}")
            return []
    
    def _collect_posts_for_query(self, query: str, subreddit: str = "all", per_query_limit: int = 100, time_filter: str = "year") -> List[Dict[str, Any]]:
        """Collect posts for a single query"""
        if not query:
            return []
            
        posts_objects = self._run_lucene_search(query, subreddit=subreddit, limit=per_query_limit, time_filter=time_filter)
        results = []
        seen_ids = set()
        
        for post in posts_objects:
            post_id = getattr(post, "id", None)
            if not post_id or post_id in seen_ids:
                continue
                
            seen_ids.add(post_id)
            
            try:
                post_dict = self._post_to_dict_fast(post)
                if post_dict:  # Only add if conversion succeeded
                    results.append(post_dict)
            except Exception as e:
                logger.warning(f"Error converting post {post_id}: {e}")
            
            if len(results) >= per_query_limit:
                break
                
        return results
    
    def _generate_search_queries(self, keywords_data: Dict[str, Any], queries_per_domain: int = 8) -> List[Tuple[List[str], List[str], str]]:
        """Generate search queries from keywords data"""
        anchors = keywords_data.get("domain_anchors", [])
        problems = keywords_data.get("problem_phrases", [])
        
        if len(anchors) < 2 or len(problems) < 2:
            logger.warning(f"Need at least 2 anchors and 2 problems. Got {len(anchors)} anchors, {len(problems)} problems")
            return []
        
        # Shuffle to avoid bias
        random.shuffle(anchors)
        random.shuffle(problems)
        
        queries = []
        max_attempts = queries_per_domain * 2  # Allow some retries for unique queries
        
        for _ in range(max_attempts):
            if len(queries) >= queries_per_domain:
                break
                
            # Vary anchor and problem counts with weighted preferences
            anchor_count = random.choices([2, 3], weights=[0.7, 0.3])[0]
            problem_count = random.choices([2, 3], weights=[0.3, 0.7])[0]
            
            anchor_count = min(anchor_count, len(anchors))
            problem_count = min(problem_count, len(problems))
            
            selected_anchors = random.sample(anchors, anchor_count)
            selected_problems = random.sample(problems, problem_count)
            
            query = self.build_consistent_query(selected_anchors, selected_problems)
            if query and len(query) < 700:  # Keep reasonable length
                query_tuple = (tuple(selected_anchors), tuple(selected_problems), query)
                if query_tuple not in [(a, p, q) for a, p, q in queries]:
                    queries.append((selected_anchors, selected_problems, query))
        
        logger.info(f"Generated {len(queries)} unique search queries")
        return queries[:queries_per_domain]
    
    def _check_subreddit_fast(self, name: str) -> Dict[str, Any]:
        """Fast subreddit existence check"""
        result = {
            "name": name,
            "exists": False,
            "accessible": False,
            "subscribers": 0,
            "note": ""
        }
        
        if self.reddit is None:
            result["note"] = "dry-run: reddit not configured"
            return result
        
        try:
            subreddit = self.reddit.subreddit(name)
            try:
                result["subscribers"] = getattr(subreddit, "subscribers", 0) or 0
                result["exists"] = True
                
                # Quick access test - try to fetch one post
                _ = next(subreddit.new(limit=1), None)
                result["accessible"] = True
                
            except (prawcore.exceptions.Forbidden, prawcore.exceptions.NotFound):
                result["accessible"] = False
                result["note"] = "Private or not found"
            except Exception as e:
                result["accessible"] = False
                result["note"] = f"Access test error: {e}"
                
        except Exception as e:
            result["note"] = f"Check failed: {e}"
        
        return result
    
    def _fetch_subreddit_posts(self, subreddit_name: str, limit: int = 100) -> List[Dict[str, Any]]:
        """Fetch posts from a specific subreddit"""
        if self.reddit is None:
            return []
        
        try:
            subreddit = self.reddit.subreddit(subreddit_name)
            candidates = []
            seen_ids = set()
            
            # Fetch from multiple sources with distributed limits
            fetch_sources = [
                ("hot", subreddit.hot(limit=limit//3)),
                ("top", subreddit.top(limit=limit//3, time_filter="year")),
                ("new", subreddit.new(limit=limit//3))
            ]
            
            for source_name, post_iterator in fetch_sources:
                try:
                    for submission in post_iterator:
                        post_id = getattr(submission, "id", None)
                        if post_id and post_id not in seen_ids:
                            seen_ids.add(post_id)
                            candidates.append(submission)
                except Exception as e:
                    logger.warning(f"Failed to fetch {source_name} posts from r/{subreddit_name}: {e}")
            
            # Score posts by engagement and filter low-quality
            scored_posts = []
            for submission in candidates:
                try:
                    score = getattr(submission, "score", 0) or 0
                    num_comments = getattr(submission, "num_comments", 0) or 0
                    
                    # Skip very low engagement posts
                    if score < 1 and num_comments == 0:
                        continue
                    
                    # Calculate engagement score (weight comments higher)
                    engagement_score = float(score) + 2.0 * float(num_comments)
                    post_dict = self._post_to_dict_fast(submission)
                    
                    if post_dict:  # Only add if conversion succeeded
                        scored_posts.append((engagement_score, post_dict))
                except Exception as e:
                    logger.debug(f"Error scoring post: {e}")
                    continue
            
            # Return top posts by engagement
            scored_posts.sort(key=lambda x: x[0], reverse=True)
            return [post for score, post in scored_posts[:limit]]
            
        except Exception as e:
            logger.error(f"Error fetching posts from r/{subreddit_name}: {e}")
            return []
    
    async def fetch_reddit_posts_for_keywords(
        self, 
        user_id: str, 
        input_id: str, 
        keywords_data: Dict[str, Any],
        queries_per_domain: int = 8,
        per_query_limit: int = 100,
        per_subreddit_limit: int = 100
    ) -> Dict[str, Any]:
        """
        Main method to fetch Reddit posts based on generated keywords
        """
        try:
            logger.info(f"Starting Reddit fetch for input {input_id} (user: {user_id})")
            
            # Update processing stage
            await processing_lock_service.update_stage(user_id, input_id, ProcessingStage.POSTS_FETCHING)
            await UserInputService.update_processing_stage(user_id, input_id, ProcessingStage.POSTS_FETCHING.value)
            
            result = {
                "user_id": user_id,
                "input_id": input_id,
                "fetch_id": str(uuid.uuid4()),
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "by_query": [],
                "by_subreddit": [],
                "total_posts": 0,
                "status": "completed"
            }
            
            seen_post_ids = set()
            
            # 1. Search-based extraction
            logger.info("Generating search queries from keywords...")
            queries = self._generate_search_queries(keywords_data, queries_per_domain)
            
            for anchor_combo, problem_combo, query in queries:
                logger.info(f"Executing query: {query[:100]}...")
                posts = self._collect_posts_for_query(
                    query, 
                    per_query_limit=per_query_limit,
                    time_filter="year"
                )
                
                # Deduplicate posts
                unique_posts = []
                for post in posts:
                    post_id = post.get("id")
                    if post_id and post_id not in seen_post_ids:
                        seen_post_ids.add(post_id)
                        unique_posts.append(post)
                
                result["by_query"].append({
                    "query": query,
                    "domain_anchors_used": anchor_combo,
                    "problem_phrases_used": problem_combo,
                    "posts": unique_posts,
                    "n_posts": len(unique_posts)
                })
                
                # Rate limiting between queries
                await asyncio.sleep(0.5)
            
            # 2. Subreddit-based extraction
            logger.info("Fetching from potential subreddits...")
            potential_subreddits = keywords_data.get("potential_subreddits", [])
            
            for subreddit_raw in potential_subreddits:
                subreddit_name = self.clean_subreddit_name(subreddit_raw)
                if not subreddit_name:
                    continue
                
                logger.info(f"Checking r/{subreddit_name}...")
                subreddit_meta = self._check_subreddit_fast(subreddit_name)
                
                subreddit_entry = {
                    "subreddit": subreddit_name,
                    "meta": subreddit_meta,
                    "posts": [],
                    "extracted_count": 0
                }
                
                if subreddit_meta.get("exists") and subreddit_meta.get("accessible"):
                    posts = self._fetch_subreddit_posts(subreddit_name, per_subreddit_limit)
                    
                    # Deduplicate posts
                    unique_posts = []
                    for post in posts:
                        post_id = post.get("id")
                        if post_id and post_id not in seen_post_ids:
                            seen_post_ids.add(post_id)
                            unique_posts.append(post)
                    
                    subreddit_entry["posts"] = unique_posts
                    subreddit_entry["extracted_count"] = len(unique_posts)
                    logger.info(f"Extracted {len(unique_posts)} unique posts from r/{subreddit_name}")
                else:
                    logger.info(f"Skipping r/{subreddit_name} - {subreddit_meta.get('note', 'not accessible')}")
                
                result["by_subreddit"].append(subreddit_entry)
                await asyncio.sleep(0.2)  # Rate limiting between subreddits
            
            # Calculate totals
            query_total = sum(query["n_posts"] for query in result["by_query"])
            subreddit_total = sum(sub["extracted_count"] for sub in result["by_subreddit"])
            result["total_posts"] = query_total + subreddit_total
            
            logger.info(f"Reddit fetch completed: {query_total} from queries, {subreddit_total} from subreddits, {result['total_posts']} total")
            
            return result
            
        except Exception as e:
            logger.error(f"Error during Reddit fetch for input {input_id}: {str(e)}")
            
            # Update user input status to failed
            try:
                await UserInputService.update_input_status(
                    user_id=user_id,
                    input_id=input_id,
                    status="failed",
                    current_stage=ProcessingStage.FAILED.value,
                    error_message=f"Reddit fetching failed: {str(e)}"
                )
            except Exception as update_error:
                logger.error(f"Failed to update user input status: {str(update_error)}")
            
            return {
                "user_id": user_id,
                "input_id": input_id,
                "fetch_id": str(uuid.uuid4()),
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "by_query": [],
                "by_subreddit": [],
                "total_posts": 0,
                "status": "failed",
                "error": str(e)
            }
    
    async def save_reddit_data_to_file(self, reddit_data: Dict[str, Any], user_id: str, input_id: str) -> str:
        """
        Save Reddit data to JSON file
        """
        try:
            # Create directory structure
            base_dir = Path("data/reddit_posts")
            user_dir = base_dir / user_id
            user_dir.mkdir(parents=True, exist_ok=True)
            
            # Create filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"reddit_posts_{input_id}_{timestamp}.json"
            file_path = user_dir / filename
            
            # Save data with proper encoding
            with open(file_path, "w", encoding="utf-8") as file:
                json.dump(reddit_data, file, ensure_ascii=False, indent=2)
            
            logger.info(f"Saved Reddit data to {file_path}")
            return str(file_path)
            
        except Exception as e:
            logger.error(f"Error saving Reddit data to file: {str(e)}")
            raise

# Create global instance
reddit_fetching_service = RedditFetchingService()