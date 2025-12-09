"""
Reddit Engagement Metrics Service
Calculates engagement metrics from pain point Reddit data
"""

from typing import List, Dict, Any
from datetime import datetime
from collections import defaultdict
from app.db.models.pain_points_model import PainPoint, PostReference
from app.core.logging import logger


class RedditMetrics:
    """Container for Reddit engagement metrics"""
    
    def __init__(self):
        self.total_posts = 0
        self.total_upvotes = 0
        self.total_comments = 0
        self.avg_upvotes = 0.0
        self.avg_comments = 0.0
        self.posts_per_month = 0.0
        self.unique_subreddits = set()
        self.subreddit_counts = {}
        self.date_range_days = 0
        self.earliest_post = None
        self.latest_post = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert metrics to dictionary"""
        return {
            "total_posts": self.total_posts,
            "total_upvotes": self.total_upvotes,
            "total_comments": self.total_comments,
            "avg_upvotes": round(self.avg_upvotes, 2),
            "avg_comments": round(self.avg_comments, 2),
            "posts_per_month": round(self.posts_per_month, 2),
            "unique_subreddits": len(self.unique_subreddits),
            "subreddit_distribution": self.subreddit_counts,
            "date_range_days": self.date_range_days,
            "earliest_post": self.earliest_post,
            "latest_post": self.latest_post
        }


class RedditMetricsService:
    """Service for calculating Reddit engagement metrics"""
    
    @staticmethod
    def calculate_engagement_metrics(pain_points: List[PainPoint]) -> RedditMetrics:
        """
        Calculate aggregate engagement metrics from pain points
        
        Args:
            pain_points: List of pain points with post references
            
        Returns:
            RedditMetrics object with calculated metrics
        """
        metrics = RedditMetrics()
        
        if not pain_points:
            return metrics
        
        all_posts = []
        subreddit_counts = defaultdict(int)
        
        # Collect all post references
        for pain_point in pain_points:
            for post_ref in pain_point.post_references:
                all_posts.append(post_ref)
                subreddit_counts[post_ref.subreddit] += 1
                metrics.unique_subreddits.add(post_ref.subreddit)
        
        metrics.total_posts = len(all_posts)
        metrics.subreddit_counts = dict(subreddit_counts)
        
        if metrics.total_posts == 0:
            return metrics
        
        # Calculate engagement metrics
        total_upvotes = 0
        total_comments = 0
        dates = []
        
        for post in all_posts:
            # Aggregate upvotes
            if post.score is not None:
                total_upvotes += post.score
            
            # Aggregate comments
            if post.num_comments is not None:
                total_comments += post.num_comments
            
            # Parse dates
            try:
                # Handle different date formats
                if isinstance(post.created_utc, str):
                    # Try parsing as ISO format
                    try:
                        date = datetime.fromisoformat(post.created_utc.replace('Z', '+00:00'))
                    except:
                        # Try parsing as timestamp
                        try:
                            date = datetime.fromtimestamp(float(post.created_utc))
                        except:
                            continue
                else:
                    date = datetime.fromtimestamp(float(post.created_utc))
                
                dates.append(date)
            except Exception as e:
                logger.warning(f"Could not parse date: {post.created_utc}")
                continue
        
        metrics.total_upvotes = total_upvotes
        metrics.total_comments = total_comments
        metrics.avg_upvotes = total_upvotes / metrics.total_posts
        metrics.avg_comments = total_comments / metrics.total_posts
        
        # Calculate posting frequency
        if dates:
            dates.sort()
            metrics.earliest_post = dates[0].isoformat()
            metrics.latest_post = dates[-1].isoformat()
            
            date_range = (dates[-1] - dates[0]).days
            metrics.date_range_days = date_range
            
            if date_range > 0:
                # Calculate posts per month
                metrics.posts_per_month = (metrics.total_posts / date_range) * 30
            else:
                # All posts on same day
                metrics.posts_per_month = metrics.total_posts
        
        return metrics
    
    @staticmethod
    def get_subreddit_subscriber_counts(pain_points: List[PainPoint]) -> Dict[str, int]:
        """
        Get subscriber counts for subreddits mentioned in pain points
        
        Note: This is a placeholder. In production, you would:
        1. Use Reddit API to fetch real subscriber counts
        2. Cache the results to avoid rate limiting
        3. Update counts periodically
        
        For now, we'll estimate based on post engagement
        
        Args:
            pain_points: List of pain points
            
        Returns:
            Dictionary mapping subreddit name to estimated subscriber count
        """
        subreddit_data = defaultdict(lambda: {"posts": 0, "total_upvotes": 0})
        
        for pain_point in pain_points:
            for post_ref in pain_point.post_references:
                subreddit = post_ref.subreddit
                subreddit_data[subreddit]["posts"] += 1
                if post_ref.score:
                    subreddit_data[subreddit]["total_upvotes"] += post_ref.score
        
        # Estimate subscriber counts based on engagement
        # Rough heuristic: avg_upvotes * 1000 (very rough approximation)
        subscriber_counts = {}
        for subreddit, data in subreddit_data.items():
            if data["posts"] > 0:
                avg_upvotes = data["total_upvotes"] / data["posts"]
                # Estimate: popular posts get ~0.1% of subscriber engagement
                estimated_subscribers = int(avg_upvotes * 1000)
                # Cap at reasonable values
                estimated_subscribers = max(1000, min(estimated_subscribers, 50000000))
                subscriber_counts[subreddit] = estimated_subscribers
        
        return subscriber_counts
    
    @staticmethod
    def analyze_discussion_trend(pain_points: List[PainPoint]) -> Dict[str, Any]:
        """
        Analyze discussion trends over time
        
        Args:
            pain_points: List of pain points
            
        Returns:
            Dictionary with trend analysis
        """
        all_posts = []
        for pain_point in pain_points:
            all_posts.extend(pain_point.post_references)
        
        if not all_posts:
            return {
                "trend": "unknown",
                "confidence": "low",
                "reason": "No posts available"
            }
        
        # Parse dates
        dated_posts = []
        for post in all_posts:
            try:
                if isinstance(post.created_utc, str):
                    try:
                        date = datetime.fromisoformat(post.created_utc.replace('Z', '+00:00'))
                    except:
                        date = datetime.fromtimestamp(float(post.created_utc))
                else:
                    date = datetime.fromtimestamp(float(post.created_utc))
                
                dated_posts.append((date, post))
            except:
                continue
        
        if len(dated_posts) < 3:
            return {
                "trend": "insufficient_data",
                "confidence": "low",
                "reason": "Not enough dated posts for trend analysis"
            }
        
        # Sort by date
        dated_posts.sort(key=lambda x: x[0])
        
        # Split into first half and second half
        mid_point = len(dated_posts) // 2
        first_half = dated_posts[:mid_point]
        second_half = dated_posts[mid_point:]
        
        # Calculate average engagement for each half
        first_half_engagement = sum(p.score or 0 for _, p in first_half) / len(first_half)
        second_half_engagement = sum(p.score or 0 for _, p in second_half) / len(second_half)
        
        # Determine trend
        if second_half_engagement > first_half_engagement * 1.2:
            trend = "growing"
            confidence = "medium"
        elif second_half_engagement < first_half_engagement * 0.8:
            trend = "declining"
            confidence = "medium"
        else:
            trend = "stable"
            confidence = "medium"
        
        return {
            "trend": trend,
            "confidence": confidence,
            "first_half_avg_engagement": round(first_half_engagement, 2),
            "second_half_avg_engagement": round(second_half_engagement, 2),
            "change_percentage": round(((second_half_engagement - first_half_engagement) / first_half_engagement * 100), 2) if first_half_engagement > 0 else 0
        }
    
    @staticmethod
    def calculate_demand_score(metrics: RedditMetrics) -> int:
        """
        Calculate a demand score (1-5) based on engagement metrics
        
        Args:
            metrics: RedditMetrics object
            
        Returns:
            Score from 1 to 5
        """
        score = 1
        
        # Factor 1: Total discussions
        if metrics.total_posts > 100:
            score += 1
        if metrics.total_posts > 500:
            score += 1
        
        # Factor 2: Average engagement
        avg_engagement = (metrics.avg_upvotes + metrics.avg_comments) / 2
        if avg_engagement > 50:
            score += 1
        
        # Factor 3: Discussion frequency
        if metrics.posts_per_month > 10:
            score += 1
        
        # Cap at 5
        return min(5, score)
