"""
Market Demand Analyzer Service
Assesses market interest using Reddit data and search trends
"""

import json
import re
from typing import List, Optional, Dict, Any
from datetime import datetime
from app.db.models.pain_points_model import PainPoint
from app.db.models.idea_model import IdeaResponse
from app.db.models.validation_result_model import Score
from app.services.module2_validation.module1_integration_service import Module1IntegrationService
from app.services.module1_pain_points.reddit_metrics_service import RedditMetricsService, RedditMetrics
from app.services.shared.llm_service import LLMService
from app.core.logging import logger


class MarketDemandAnalyzer:
    """Service for analyzing market demand for startup ideas"""
    
    def __init__(self):
        self.llm_service = LLMService()
        self.reddit_metrics_service = RedditMetricsService()
        self.module1_service = Module1IntegrationService()
    
    async def analyze_market_demand(
        self,
        idea: IdeaResponse,
        linked_pain_points: Optional[List[PainPoint]] = None,
        include_web_search: bool = False
    ) -> Score:
        """
        Analyze market demand for an idea
        
        Args:
            idea: The idea to analyze
            linked_pain_points: Optional list of linked pain points from Module 1
            include_web_search: Whether to include web search for demand signals
            
        Returns:
            Score object with market demand assessment
        """
        score = 1
        justifications = []
        evidence = {}
        recommendations = []
        
        # Strategy 1: Analyze Reddit data from linked pain points
        if linked_pain_points and len(linked_pain_points) > 0:
            reddit_score, reddit_justifications, reddit_evidence = self._analyze_reddit_engagement(
                linked_pain_points
            )
            score = max(score, reddit_score)
            justifications.extend(reddit_justifications)
            evidence.update(reddit_evidence)
        else:
            justifications.append("No pain points linked - limited market data available")
            recommendations.append("Link pain points from Module 1 for better market demand analysis")
        
        # Strategy 2: Analyze trend direction
        if linked_pain_points and len(linked_pain_points) > 0:
            trend_analysis = self._analyze_discussion_trend(linked_pain_points)
            
            if trend_analysis.get("trend") == "growing":
                score = min(5, score + 1)
                justifications.append(
                    f"Growing interest trend detected ({trend_analysis.get('change_percentage', 0):.1f}% increase)"
                )
                evidence["trend"] = "growing"
                evidence["trend_details"] = trend_analysis
            elif trend_analysis.get("trend") == "stable":
                justifications.append("Stable discussion trend over time")
                evidence["trend"] = "stable"
                evidence["trend_details"] = trend_analysis
            elif trend_analysis.get("trend") == "declining":
                justifications.append(
                    f"Declining interest trend ({trend_analysis.get('change_percentage', 0):.1f}% decrease)"
                )
                evidence["trend"] = "declining"
                evidence["trend_details"] = trend_analysis
                recommendations.append("Investigate why interest is declining and consider pivoting")
        
        # Strategy 3: Optional web search for demand signals
        if include_web_search:
            try:
                search_results = await self._search_demand_signals(idea)
                if search_results:
                    justifications.extend(search_results.get("justifications", []))
                    evidence["web_search"] = search_results
                    
                    # Adjust score based on web search findings
                    if search_results.get("demand_level") == "high":
                        score = min(5, score + 1)
                    elif search_results.get("demand_level") == "low":
                        score = max(1, score - 1)
            except Exception as e:
                logger.warning(f"Web search failed: {str(e)}")
                evidence["web_search_error"] = str(e)
        
        # Generate recommendations based on score
        recommendations.extend(self._generate_demand_recommendations(score, evidence))
        
        return Score(
            value=min(5, score),
            justifications=justifications,
            evidence=evidence,
            recommendations=recommendations,
            metadata={
                "analysis_timestamp": datetime.utcnow().isoformat(),
                "pain_points_analyzed": len(linked_pain_points) if linked_pain_points else 0,
                "web_search_included": include_web_search
            }
        )
    
    def _analyze_reddit_engagement(
        self,
        pain_points: List[PainPoint]
    ) -> tuple[int, List[str], Dict[str, Any]]:
        """
        Analyze Reddit engagement metrics from pain points
        
        Args:
            pain_points: List of pain points with post references
            
        Returns:
            Tuple of (score, justifications, evidence)
        """
        score = 1
        justifications = []
        evidence = {}
        
        # Calculate engagement metrics
        metrics = self.reddit_metrics_service.calculate_engagement_metrics(pain_points)
        
        # Store metrics in evidence
        evidence["reddit_metrics"] = metrics.to_dict()
        
        # Scoring based on total discussions
        total_discussions = metrics.total_posts
        if total_discussions > 100:
            score += 2
            justifications.append(f"Strong discussion volume: {total_discussions} relevant posts found")
        elif total_discussions > 50:
            score += 1
            justifications.append(f"Moderate discussion volume: {total_discussions} relevant posts found")
        elif total_discussions > 10:
            justifications.append(f"Limited discussion volume: {total_discussions} relevant posts found")
        else:
            justifications.append(f"Very limited discussion volume: {total_discussions} relevant posts found")
        
        # Scoring based on average engagement
        avg_upvotes = metrics.avg_upvotes
        avg_comments = metrics.avg_comments
        avg_engagement = (avg_upvotes + avg_comments) / 2
        
        if avg_engagement > 50:
            score = min(5, score + 1)
            justifications.append(
                f"High engagement per post: avg {avg_upvotes:.1f} upvotes, {avg_comments:.1f} comments"
            )
        elif avg_engagement > 20:
            justifications.append(
                f"Moderate engagement per post: avg {avg_upvotes:.1f} upvotes, {avg_comments:.1f} comments"
            )
        else:
            justifications.append(
                f"Low engagement per post: avg {avg_upvotes:.1f} upvotes, {avg_comments:.1f} comments"
            )
        
        # Scoring based on discussion frequency
        posts_per_month = metrics.posts_per_month
        if posts_per_month > 10:
            score = min(5, score + 1)
            justifications.append(f"Active ongoing discussions: {posts_per_month:.1f} posts per month")
        elif posts_per_month > 5:
            justifications.append(f"Regular discussions: {posts_per_month:.1f} posts per month")
        else:
            justifications.append(f"Infrequent discussions: {posts_per_month:.1f} posts per month")
        
        # Add subreddit diversity info
        unique_subreddits = len(metrics.unique_subreddits)
        if unique_subreddits > 1:
            justifications.append(f"Problem discussed across {unique_subreddits} different communities")
            evidence["subreddit_diversity"] = unique_subreddits
        
        return score, justifications, evidence
    
    def _analyze_discussion_trend(self, pain_points: List[PainPoint]) -> Dict[str, Any]:
        """
        Analyze discussion frequency over time
        
        Args:
            pain_points: List of pain points
            
        Returns:
            Dictionary with trend analysis
        """
        return self.reddit_metrics_service.analyze_discussion_trend(pain_points)
    
    async def _search_demand_signals(self, idea: IdeaResponse) -> Dict[str, Any]:
        """
        Search for demand signals using web search (optional feature)
        
        Note: This is a placeholder implementation. In production, you would:
        1. Use a web search API (SerpAPI, Google Custom Search, etc.)
        2. Analyze search results for demand indicators
        3. Look for related products, discussions, and market signals
        
        For now, we use LLM to generate search queries and simulate analysis
        
        Args:
            idea: The idea to search for
            
        Returns:
            Dictionary with search results and demand signals
        """
        # Generate search queries from idea
        search_queries = self._generate_search_queries(idea)
        
        # Use LLM to assess demand based on idea characteristics
        # This is a simplified approach - in production, you'd actually perform web searches
        prompt = f"""Analyze the potential market demand for this startup idea based on the problem and solution.

Idea Title: {idea.title}
Problem: {idea.problem_statement}
Solution: {idea.solution_description}
Target Market: {idea.target_market}

Consider:
1. Is this a problem people actively search for solutions to?
2. Are there existing products/services in this space (indicating demand)?
3. What search terms would people use to find solutions?
4. Is this a growing or declining market trend?

Return JSON with:
{{
  "demand_level": "high|medium|low",
  "search_volume_estimate": "high|medium|low",
  "existing_solutions_indicator": "many|some|few|none",
  "trend_direction": "growing|stable|declining",
  "justifications": ["list of reasons for assessment"],
  "recommended_search_queries": ["list of search queries to validate demand"]
}}"""
        
        try:
            response = await self.llm_service.call_llm(prompt, response_format="json")
            analysis = json.loads(response)
            
            # Add generated search queries
            analysis["generated_queries"] = search_queries
            
            return analysis
        except Exception as e:
            logger.error(f"Error in demand signal search: {str(e)}")
            return {
                "demand_level": "unknown",
                "error": str(e),
                "generated_queries": search_queries
            }
    
    def _generate_search_queries(self, idea: IdeaResponse) -> List[str]:
        """
        Generate search queries from idea keywords
        
        Args:
            idea: The idea to generate queries for
            
        Returns:
            List of search queries
        """
        queries = []
        
        # Extract key terms from problem statement
        problem_terms = self._extract_keywords(idea.problem_statement)
        solution_terms = self._extract_keywords(idea.solution_description)
        
        # Generate query variations
        if problem_terms:
            queries.append(f"{' '.join(problem_terms[:3])} solution")
            queries.append(f"how to solve {' '.join(problem_terms[:2])}")
        
        if solution_terms:
            queries.append(f"{' '.join(solution_terms[:3])} tool")
            queries.append(f"{' '.join(solution_terms[:2])} software")
        
        # Add target market specific queries
        if idea.target_market:
            market_terms = self._extract_keywords(idea.target_market)
            if market_terms and problem_terms:
                queries.append(f"{' '.join(market_terms[:2])} {' '.join(problem_terms[:2])}")
        
        return queries[:5]  # Limit to 5 queries
    
    def _extract_keywords(self, text: str) -> List[str]:
        """
        Extract keywords from text (simple implementation)
        
        Args:
            text: Text to extract keywords from
            
        Returns:
            List of keywords
        """
        # Remove common stop words
        stop_words = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
            'of', 'with', 'by', 'from', 'as', 'is', 'was', 'are', 'were', 'been',
            'be', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would',
            'could', 'should', 'may', 'might', 'can', 'this', 'that', 'these',
            'those', 'i', 'you', 'he', 'she', 'it', 'we', 'they', 'my', 'your',
            'his', 'her', 'its', 'our', 'their'
        }
        
        # Simple tokenization and filtering
        words = re.findall(r'\b[a-z]{3,}\b', text.lower())
        keywords = [w for w in words if w not in stop_words]
        
        # Return unique keywords, preserving order
        seen = set()
        unique_keywords = []
        for keyword in keywords:
            if keyword not in seen:
                seen.add(keyword)
                unique_keywords.append(keyword)
        
        return unique_keywords[:10]  # Limit to 10 keywords
    
    def _generate_demand_recommendations(
        self,
        score: int,
        evidence: Dict[str, Any]
    ) -> List[str]:
        """
        Generate recommendations based on market demand score
        
        Args:
            score: Market demand score (1-5)
            evidence: Evidence dictionary
            
        Returns:
            List of recommendations
        """
        recommendations = []
        
        if score <= 2:
            recommendations.append(
                "Low market demand detected. Consider validating the problem through user interviews"
            )
            recommendations.append(
                "Explore alternative problem spaces or refine your target market"
            )
        elif score == 3:
            recommendations.append(
                "Moderate market demand. Conduct user surveys to validate willingness to pay"
            )
            recommendations.append(
                "Monitor discussion trends to identify if interest is growing"
            )
        else:
            recommendations.append(
                "Strong market demand validated. Focus on solution differentiation"
            )
            recommendations.append(
                "Engage with the community to understand specific pain points better"
            )
        
        # Trend-specific recommendations
        trend = evidence.get("trend")
        if trend == "declining":
            recommendations.append(
                "Interest is declining - investigate root causes and consider pivoting"
            )
        elif trend == "growing":
            recommendations.append(
                "Growing trend detected - move quickly to capture market opportunity"
            )
        
        # Engagement-specific recommendations
        reddit_metrics = evidence.get("reddit_metrics", {})
        if reddit_metrics.get("avg_upvotes", 0) < 10:
            recommendations.append(
                "Low engagement suggests niche problem - ensure target market is large enough"
            )
        
        return recommendations


# Singleton instance
_market_demand_analyzer = None


def get_market_demand_analyzer() -> MarketDemandAnalyzer:
    """Get singleton instance of MarketDemandAnalyzer"""
    global _market_demand_analyzer
    if _market_demand_analyzer is None:
        _market_demand_analyzer = MarketDemandAnalyzer()
    return _market_demand_analyzer
