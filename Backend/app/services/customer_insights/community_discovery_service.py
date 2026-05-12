"""
Community Discovery Service - Aggregate and rank communities from all sources
"""
import logging
from typing import List, Dict, Any
from collections import defaultdict

# Configure logging
logger = logging.getLogger(__name__)

class CommunityDiscoveryService:
    """Service for discovering and ranking active communities"""
    
    def discover_communities(self, discussions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Discover communities from discussions
        
        Args:
            discussions: List of discussion dictionaries
            
        Returns:
            List of community information dictionaries
        """
        try:
            logger.info(f"Discovering communities from {len(discussions)} discussions...")
            
            # Aggregate discussions by community
            community_data = defaultdict(lambda: {
                "discussions": [],
                "total_score": 0,
                "total_comments": 0,
                "source": None,
                "urls": set()
            })
            
            for discussion in discussions:
                community_name = discussion.get("community") or discussion.get("subreddit", "unknown")
                source = discussion.get("source", "unknown")
                
                community_data[community_name]["discussions"].append(discussion)
                community_data[community_name]["total_score"] += discussion.get("score", 0)
                community_data[community_name]["total_comments"] += discussion.get("comments_count", 0)
                community_data[community_name]["source"] = source
                
                # Collect URLs
                url = discussion.get("url")
                if url:
                    community_data[community_name]["urls"].add(url)
            
            # Convert to list and calculate engagement scores
            communities = []
            for name, data in community_data.items():
                discussion_count = len(data["discussions"])
                avg_score = data["total_score"] / discussion_count if discussion_count > 0 else 0
                
                # Calculate engagement score
                engagement_score = self.calculate_engagement_score(
                    discussion_count=discussion_count,
                    avg_score=avg_score,
                    total_comments=data["total_comments"]
                )
                
                # Get representative URL
                url = list(data["urls"])[0] if data["urls"] else None
                
                communities.append({
                    "name": name,
                    "source": data["source"],
                    "discussion_count": discussion_count,
                    "engagement_score": round(engagement_score, 2),
                    "url": url,
                    "description": self._generate_community_description(name, data["source"])
                })
            
            # Rank communities by engagement score
            ranked_communities = self.rank_communities(communities)
            
            logger.info(f"Discovered {len(ranked_communities)} communities")
            return ranked_communities
            
        except Exception as e:
            logger.error(f"Error discovering communities: {str(e)}")
            return []
    
    def rank_communities(self, communities: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Rank communities by engagement score
        
        Args:
            communities: List of community dictionaries
            
        Returns:
            Sorted list of communities (highest engagement first)
        """
        try:
            # Sort by engagement score (descending)
            ranked = sorted(
                communities,
                key=lambda x: x.get("engagement_score", 0),
                reverse=True
            )
            
            logger.info(f"Ranked {len(ranked)} communities")
            return ranked
            
        except Exception as e:
            logger.error(f"Error ranking communities: {str(e)}")
            return communities
    
    def calculate_engagement_score(
        self, 
        discussion_count: int, 
        avg_score: float, 
        total_comments: int
    ) -> float:
        """
        Calculate engagement score for a community
        
        Formula: (discussion_count * 0.4) + (avg_score * 0.3) + (total_comments * 0.3)
        
        Args:
            discussion_count: Number of discussions in community
            avg_score: Average score of discussions
            total_comments: Total number of comments
            
        Returns:
            Engagement score
        """
        try:
            # Normalize values to similar scales
            normalized_discussions = min(discussion_count / 10, 10)  # Cap at 10
            normalized_score = min(avg_score / 10, 10)  # Cap at 10
            normalized_comments = min(total_comments / 50, 10)  # Cap at 10
            
            # Weighted sum
            engagement_score = (
                normalized_discussions * 0.4 +
                normalized_score * 0.3 +
                normalized_comments * 0.3
            )
            
            return engagement_score
            
        except Exception as e:
            logger.error(f"Error calculating engagement score: {str(e)}")
            return 0.0
    
    def _generate_community_description(self, name: str, source: str) -> str:
        """Generate a simple description for a community"""
        if source == "reddit":
            return f"Reddit community discussing topics related to {name}"
        elif source == "producthunt":
            return f"Product Hunt discussions about {name}"
        else:
            return f"Community: {name}"
    
    def aggregate_by_source(self, discussions: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """
        Aggregate discussions by source
        
        Args:
            discussions: List of discussion dictionaries
            
        Returns:
            Dictionary mapping source to list of discussions
        """
        try:
            aggregated = defaultdict(list)
            
            for discussion in discussions:
                source = discussion.get("source", "unknown")
                aggregated[source].append(discussion)
            
            logger.info(f"Aggregated discussions by source: {dict((k, len(v)) for k, v in aggregated.items())}")
            return dict(aggregated)
            
        except Exception as e:
            logger.error(f"Error aggregating by source: {str(e)}")
            return {}

# Create global instance
community_discovery_service = CommunityDiscoveryService()
