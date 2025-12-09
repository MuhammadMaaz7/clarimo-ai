"""
LLM-Based Validation Service with Multi-Provider Fallback
Uses LLM to evaluate ideas with automatic fallback:
1. OpenRouter API (all keys)
2. Groq API (all keys)
3. HuggingFace local model

NO HARDCODED RESPONSES - Always uses actual LLM inference
"""

import json
import hashlib
from typing import Dict, List, Optional, Any
from datetime import datetime
from app.db.models.validation_result_model import Score
from app.db.models.idea_model import IdeaResponse
from app.db.models.pain_points_model import PainPoint
from app.services.shared.unified_llm_service import get_llm_service_for_module2
from app.services.module2_validation.external_data_service import get_external_data_service
from app.core.logging import logger


class LLMValidator:
    """
    Token-optimized LLM validator with automatic fallback:
    1. OpenRouter API (all keys)
    2. Groq API (all keys)
    3. HuggingFace local model
    
    NO HARDCODED RESPONSES - Always uses actual LLM inference
    """
    
    # Cache for evaluation results (in-memory, can be extended to Redis)
    _evaluation_cache: Dict[str, Score] = {}
    
    def __init__(self):
        self.llm_service = get_llm_service_for_module2()
        self.external_data_service = get_external_data_service()
        self.temperature = 0.2  # Lower temp = more consistent, fewer tokens
        self.max_tokens = 800  # Reduced from 1500 for efficiency
    
    async def evaluate_problem_clarity(
        self,
        idea: IdeaResponse,
        pain_points: List[PainPoint]
    ) -> Score:
        """
        Evaluate problem clarity with caching and automatic fallback
        """
        # Check cache first
        cache_key = self._get_cache_key("problem_clarity", idea.id)
        if cache_key in self._evaluation_cache:
            logger.info(f"Using cached evaluation for {idea.id}")
            return self._evaluation_cache[cache_key]
        
        prompt = self._create_problem_clarity_prompt(idea, pain_points)
        
        try:
            response = await self.llm_service.call_llm(
                prompt=prompt,
                response_format="json",
                temperature=self.temperature,
                max_tokens=self.max_tokens
            )
            
            result = json.loads(response)
            score = Score(
                value=result.get("score", 3),
                justifications=result.get("justifications", [])[:2],  # Limit to 2
                recommendations=result.get("recommendations", [])[:2],  # Limit to 2
                evidence=result.get("evidence", {}),
                metadata={
                    "evaluation_type": "llm_based_with_fallback",
                    "timestamp": datetime.utcnow().isoformat(),
                    "cached": False
                }
            )
            
            # Cache the result
            self._evaluation_cache[cache_key] = score
            return score
            
        except Exception as e:
            logger.error(f"All LLM providers failed for problem clarity: {str(e)}")
            # Re-raise - let orchestrator handle
            raise Exception(f"Unable to evaluate problem clarity. All LLM providers failed: {str(e)}")
    
    async def evaluate_market_demand(
        self,
        idea: IdeaResponse,
        pain_points: List[PainPoint]
    ) -> Score:
        """
        Evaluate market demand with real external data and automatic fallback
        """
        cache_key = self._get_cache_key("market_demand", idea.id)
        if cache_key in self._evaluation_cache:
            return self._evaluation_cache[cache_key]
        
        # Fetch real competitor data
        keywords = self.external_data_service.extract_keywords_from_idea(
            idea.title,
            idea.problem_statement,
            idea.solution_description,
            idea.target_market
        )
        
        external_data = await self.external_data_service.search_similar_products(
            keywords=keywords,
            max_results=10
        )
        
        prompt = self._create_market_demand_prompt(idea, pain_points, external_data)
        
        try:
            response = await self.llm_service.call_llm(
                prompt=prompt,
                response_format="json",
                temperature=self.temperature,
                max_tokens=self.max_tokens
            )
            
            result = json.loads(response)
            score = Score(
                value=result.get("score", 3),
                justifications=result.get("justifications", [])[:2],
                recommendations=result.get("recommendations", [])[:2],
                evidence={
                    **result.get("evidence", {}),
                    "external_data": {
                        "total_products_found": external_data.get("total_products_found", 0),
                        "hackernews_products": len(external_data.get("hackernews", {}).get("products", [])),
                        "github_repos": len(external_data.get("github", {}).get("repositories", [])),
                        "app_store_apps": len(external_data.get("app_store", {}).get("apps", [])),
                        "play_store_apps": len(external_data.get("play_store", {}).get("apps", []))
                    }
                },
                metadata={
                    "evaluation_type": "llm_based_with_fallback",
                    "timestamp": datetime.utcnow().isoformat(),
                    "cached": False,
                    "data_sources": ["reddit", "hackernews", "github"]
                }
            )
            
            self._evaluation_cache[cache_key] = score
            return score
            
        except Exception as e:
            logger.error(f"All LLM providers failed for market demand: {str(e)}")
            # Re-raise - let orchestrator handle
            raise Exception(f"Unable to evaluate market demand. All LLM providers failed: {str(e)}")
    
    async def evaluate_solution_fit(
        self,
        idea: IdeaResponse,
        pain_points: List[PainPoint]
    ) -> Score:
        """
        Evaluate solution fit with caching and automatic fallback
        """
        cache_key = self._get_cache_key("solution_fit", idea.id)
        if cache_key in self._evaluation_cache:
            return self._evaluation_cache[cache_key]
        
        prompt = self._create_solution_fit_prompt(idea, pain_points)
        
        try:
            response = await self.llm_service.call_llm(
                prompt=prompt,
                response_format="json",
                temperature=self.temperature,
                max_tokens=self.max_tokens
            )
            
            result = json.loads(response)
            score = Score(
                value=result.get("score", 3),
                justifications=result.get("justifications", [])[:2],
                recommendations=result.get("recommendations", [])[:2],
                evidence=result.get("evidence", {}),
                metadata={
                    "evaluation_type": "llm_based_with_fallback",
                    "timestamp": datetime.utcnow().isoformat(),
                    "cached": False
                }
            )
            
            self._evaluation_cache[cache_key] = score
            return score
            
        except Exception as e:
            logger.error(f"All LLM providers failed for solution fit: {str(e)}")
            # Re-raise - let orchestrator handle
            raise Exception(f"Unable to evaluate solution fit. All LLM providers failed: {str(e)}")
    
    async def evaluate_differentiation(
        self,
        idea: IdeaResponse
    ) -> Score:
        """
        Evaluate differentiation with real competitor data and automatic fallback
        """
        cache_key = self._get_cache_key("differentiation", idea.id)
        if cache_key in self._evaluation_cache:
            return self._evaluation_cache[cache_key]
        
        # Fetch real competitor data
        keywords = self.external_data_service.extract_keywords_from_idea(
            idea.title,
            idea.problem_statement,
            idea.solution_description,
            idea.target_market
        )
        
        external_data = await self.external_data_service.search_similar_products(
            keywords=keywords,
            max_results=10
        )
        
        prompt = self._create_differentiation_prompt(idea, external_data)
        
        try:
            response = await self.llm_service.call_llm(
                prompt=prompt,
                response_format="json",
                temperature=self.temperature,
                max_tokens=self.max_tokens
            )
            
            result = json.loads(response)
            score = Score(
                value=result.get("score", 3),
                justifications=result.get("justifications", [])[:2],
                recommendations=result.get("recommendations", [])[:2],
                evidence={
                    **result.get("evidence", {}),
                    "competitors_found": {
                        "total": external_data.get("total_products_found", 0),
                        "hackernews": len(external_data.get("hackernews", {}).get("products", [])),
                        "github": len(external_data.get("github", {}).get("repositories", [])),
                        "app_store": len(external_data.get("app_store", {}).get("apps", [])),
                        "play_store": len(external_data.get("play_store", {}).get("apps", []))
                    }
                },
                metadata={
                    "evaluation_type": "llm_based_with_fallback",
                    "timestamp": datetime.utcnow().isoformat(),
                    "cached": False,
                    "data_sources": ["hackernews", "github"]
                }
            )
            
            self._evaluation_cache[cache_key] = score
            return score
            
        except Exception as e:
            logger.error(f"All LLM providers failed for differentiation: {str(e)}")
            # Re-raise - let orchestrator handle
            raise Exception(f"Unable to evaluate differentiation. All LLM providers failed: {str(e)}")
    
    def _get_cache_key(self, metric: str, idea_id: str) -> str:
        """Generate cache key for evaluation results"""
        return hashlib.md5(f"{metric}:{idea_id}".encode()).hexdigest()
    
    def _create_problem_clarity_prompt(
        self,
        idea: IdeaResponse,
        pain_points: List[PainPoint]
    ) -> str:
        """Create data-driven prompt for problem clarity evaluation"""
        
        pain_context = ""
        if pain_points:
            pain_context = f"\n\nLinked Pain Points Data ({len(pain_points)} found):"
            for i, pp in enumerate(pain_points[:3], 1):
                pain_context += f"\n{i}. {pp.problem_description[:150]}"
                pain_context += f"\n   - Found in: {', '.join(pp.subreddits[:3])}"
                pain_context += f"\n   - References: {len(pp.post_references)} discussions"
        
        return f"""Analyze the problem clarity for this startup idea. Provide a personalized assessment based on the specific details provided.

IDEA DETAILS:
Title: {idea.title}
Problem Statement: {idea.problem_statement}
Target Market: {idea.target_market}
Solution: {idea.solution_description[:200]}{pain_context}

EVALUATION CRITERIA:
1. Specificity: Is the problem clearly defined with specific details?
2. Target Audience: Is it clear who experiences this problem?
3. Evidence: Is there evidence that this problem exists (pain points, market data)?
4. Scope: Is the problem scope well-defined (not too broad or narrow)?
5. Impact: Is the impact/severity of the problem clear?

Provide a score from 1-5 where:
- 5: Exceptionally clear problem with strong evidence and specificity
- 4: Clear problem with good details and some evidence
- 3: Moderately clear but missing some specificity or evidence
- 2: Vague problem statement with limited clarity
- 1: Very unclear or poorly defined problem

Return JSON with:
- score: 1-5 (based on the specific idea, not generic)
- justifications: 2-3 specific observations about THIS idea's problem clarity
- recommendations: 2-3 actionable, personalized suggestions to improve THIS specific problem statement
- evidence: {{"specificity": "high|medium|low", "target_clarity": "clear|moderate|unclear", "evidence_strength": "strong|moderate|weak"}}

Be specific and personalized - reference actual details from the idea, not generic advice."""
    
    def _create_market_demand_prompt(
        self,
        idea: IdeaResponse,
        pain_points: List[PainPoint],
        external_data: Dict[str, Any]
    ) -> str:
        """Create data-driven prompt for market demand evaluation"""
        
        market_data = ""
        if pain_points:
            total_discussions = sum(len(pp.post_references) for pp in pain_points)
            total_upvotes = sum(ref.get('upvotes', 0) for pp in pain_points for ref in pp.post_references)
            total_comments = sum(ref.get('num_comments', 0) for pp in pain_points for ref in pp.post_references)
            unique_subreddits = set()
            for pp in pain_points:
                unique_subreddits.update(pp.subreddits)
            
            market_data = f"\n\nREAL MARKET DATA FROM REDDIT:"
            market_data += f"\n- Total Discussions: {total_discussions} posts"
            market_data += f"\n- Total Engagement: {total_upvotes} upvotes, {total_comments} comments"
            market_data += f"\n- Communities: {len(unique_subreddits)} subreddits ({', '.join(list(unique_subreddits)[:5])})"
            market_data += f"\n- Average Engagement: {total_upvotes/max(total_discussions,1):.1f} upvotes/post, {total_comments/max(total_discussions,1):.1f} comments/post"
            
            market_data += f"\n\nTop Pain Points:"
            for i, pp in enumerate(pain_points[:3], 1):
                market_data += f"\n{i}. {pp.problem_description[:100]}"
                market_data += f"\n   Discussed in: {', '.join(pp.subreddits[:3])}"
        else:
            market_data = "\n\nNO REDDIT DATA: No pain points linked."
        
        # Add external competitor data
        competitor_data = "\n\nEXTERNAL MARKET VALIDATION:"
        hn_products = external_data.get("hackernews", {}).get("products", [])
        github_repos = external_data.get("github", {}).get("repositories", [])
        app_store_apps = external_data.get("app_store", {}).get("apps", [])
        play_store_apps = external_data.get("play_store", {}).get("apps", [])
        
        if hn_products:
            competitor_data += f"\n\nHackerNews Products Found ({len(hn_products)}):"
            for i, product in enumerate(hn_products[:5], 1):
                competitor_data += f"\n{i}. {product['title']}"
                competitor_data += f"\n   Points: {product['points']}, Comments: {product['num_comments']}"
                if product.get('story_text'):
                    competitor_data += f"\n   Description: {product['story_text'][:100]}"
        
        if github_repos:
            competitor_data += f"\n\nGitHub Projects Found ({len(github_repos)}):"
            for i, repo in enumerate(github_repos[:5], 1):
                competitor_data += f"\n{i}. {repo['name']}"
                competitor_data += f"\n   Stars: {repo['stars']}, Forks: {repo['forks']}"
                if repo.get('description'):
                    competitor_data += f"\n   Description: {repo['description'][:100]}"
        
        if app_store_apps:
            competitor_data += f"\n\nApp Store Apps Found ({len(app_store_apps)}):"
            for i, app in enumerate(app_store_apps[:5], 1):
                competitor_data += f"\n{i}. {app['name']} by {app['developer']}"
                competitor_data += f"\n   Rating: {app['rating']:.1f}⭐ ({app['rating_count']:,} reviews)"
                competitor_data += f"\n   Price: {'Free' if app['price'] == 0 else f'${app['price']}'}"
        
        if play_store_apps:
            competitor_data += f"\n\nPlay Store Apps Found ({len(play_store_apps)}):"
            for i, app in enumerate(play_store_apps[:5], 1):
                competitor_data += f"\n{i}. {app['name']} by {app['developer']}"
                competitor_data += f"\n   Rating: {app['rating']:.1f}⭐, Installs: {app.get('installs', 'N/A')}"
                competitor_data += f"\n   Price: {'Free' if app.get('free', True) else f'${app.get('price', 0)}'}"
        
        total_found = len(hn_products) + len(github_repos) + len(app_store_apps) + len(play_store_apps)
        
        if total_found == 0:
            competitor_data += "\nNo similar products found on HackerNews or GitHub."
            competitor_data += "\nThis could mean: (1) Untapped market, (2) Keywords don't match existing solutions, (3) Very niche problem"
        
        return f"""Analyze the market demand for this startup idea based on REAL data provided.

IDEA DETAILS:
Title: {idea.title}
Problem: {idea.problem_statement}
Solution: {idea.solution_description}
Target Market: {idea.target_market}{market_data}{competitor_data}

EVALUATION CRITERIA:
1. Market Validation: Finding similar products PROVES market demand exists
2. Competition Level: More competitors = validated market (good for demand score)
3. Engagement: High engagement on similar products = strong demand
4. Reddit Signals: Real user discussions validate the problem
5. Market Size: Number of products + discussions indicate market size

KEY INSIGHT: Finding competitors is POSITIVE for market demand (proves people want solutions)

Provide a score from 1-5 where:
- 5: Many similar products found (10+) with high engagement = VALIDATED MARKET
- 4: Several products found (5-10) with good engagement = STRONG DEMAND
- 3: Few products found (2-5) or moderate engagement = MODERATE DEMAND
- 2: Very few products (1-2) with low engagement = LIMITED DEMAND
- 1: No similar products found = UNVALIDATED MARKET (risky)

Return JSON with:
- score: 1-5 (based on ACTUAL competitor data - more competitors = higher demand score)
- justifications: 2-3 specific observations citing the REAL products/repos found above
- recommendations: 2-3 personalized actions based on the actual market data
- evidence: {{"demand_level": "high|medium|low", "competitors_found": {total_found}, "market_validation": "strong|moderate|weak"}}

Be data-driven - cite specific products, stars, upvotes from the data above."""
    
    def _create_solution_fit_prompt(
        self,
        idea: IdeaResponse,
        pain_points: List[PainPoint]
    ) -> str:
        """Create data-driven prompt for solution-problem fit evaluation"""
        
        pain_analysis = ""
        if pain_points:
            pain_analysis = f"\n\nUSER PAIN POINTS (from real discussions):"
            for i, pp in enumerate(pain_points[:3], 1):
                pain_analysis += f"\n{i}. {pp.problem_description}"
                if pp.user_quotes:
                    pain_analysis += f"\n   User quote: \"{pp.user_quotes[0][:150]}\""
        
        return f"""Analyze how well this solution addresses the stated problem. Be specific and critical.

IDEA DETAILS:
Title: {idea.title}
Problem Statement: {idea.problem_statement}
Solution Description: {idea.solution_description}
Target Market: {idea.target_market}
Business Model: {idea.business_model or "Not specified"}
Team Capabilities: {idea.team_capabilities or "Not specified"}{pain_analysis}

EVALUATION CRITERIA:
1. Direct Addressing: Does the solution directly solve the stated problem?
2. Completeness: Does it address all aspects of the problem or just part of it?
3. Feasibility: Is the solution technically and practically feasible?
4. User Adoption: Would users actually use this solution?
5. Gaps: What's missing or could be improved?

Provide a score from 1-5 where:
- 5: Solution perfectly addresses the problem with clear feasibility
- 4: Strong solution with minor gaps
- 3: Decent solution but missing some key aspects
- 2: Solution partially addresses problem with significant gaps
- 1: Solution doesn't effectively address the problem

Return JSON with:
- score: 1-5 (based on THIS specific solution-problem pair)
- justifications: 2-3 specific observations about how well THIS solution fits THIS problem
- recommendations: 2-3 actionable suggestions to improve THIS specific solution
- evidence: {{"alignment": "excellent|good|moderate|poor", "completeness": "complete|partial|incomplete", "feasibility": "high|medium|low"}}

Reference specific details from the problem and solution - not generic advice."""
    
    def _create_differentiation_prompt(
        self,
        idea: IdeaResponse,
        external_data: Dict[str, Any]
    ) -> str:
        """Create data-driven prompt for differentiation evaluation with real competitors"""
        
        # Build competitor list from external data
        competitor_info = "\n\nREAL COMPETITORS FOUND:"
        hn_products = external_data.get("hackernews", {}).get("products", [])
        github_repos = external_data.get("github", {}).get("repositories", [])
        app_store_apps = external_data.get("app_store", {}).get("apps", [])
        play_store_apps = external_data.get("play_store", {}).get("apps", [])
        total_competitors = len(hn_products) + len(github_repos) + len(app_store_apps) + len(play_store_apps)
        
        if hn_products:
            competitor_info += f"\n\nHackerNews Products ({len(hn_products)}):"
            for i, product in enumerate(hn_products[:5], 1):
                competitor_info += f"\n{i}. {product['title']}"
                competitor_info += f"\n   Engagement: {product['points']} points, {product['num_comments']} comments"
                if product.get('story_text'):
                    competitor_info += f"\n   What they do: {product['story_text'][:150]}"
        
        if github_repos:
            competitor_info += f"\n\nGitHub Projects ({len(github_repos)}):"
            for i, repo in enumerate(github_repos[:5], 1):
                competitor_info += f"\n{i}. {repo['name']}"
                competitor_info += f"\n   Popularity: {repo['stars']} stars, {repo['forks']} forks"
                if repo.get('description'):
                    competitor_info += f"\n   What it does: {repo['description'][:150]}"
                if repo.get('topics'):
                    competitor_info += f"\n   Topics: {', '.join(repo['topics'])}"
        
        if app_store_apps:
            competitor_info += f"\n\nApp Store Apps ({len(app_store_apps)}):"
            for i, app in enumerate(app_store_apps[:5], 1):
                competitor_info += f"\n{i}. {app['name']} by {app['developer']}"
                competitor_info += f"\n   Rating: {app['rating']:.1f}⭐ ({app['rating_count']:,} reviews)"
                competitor_info += f"\n   Price: {'Free' if app['price'] == 0 else f'${app['price']}'}"
                if app.get('description'):
                    competitor_info += f"\n   What it does: {app['description'][:150]}"
        
        if play_store_apps:
            competitor_info += f"\n\nPlay Store Apps ({len(play_store_apps)}):"
            for i, app in enumerate(play_store_apps[:5], 1):
                competitor_info += f"\n{i}. {app['name']} by {app['developer']}"
                competitor_info += f"\n   Rating: {app['rating']:.1f}⭐"
                competitor_info += f"\n   Installs: {app.get('installs', 'N/A')}"
                competitor_info += f"\n   Price: {'Free' if app.get('free', True) else f'${app.get('price', 0)}'}"
                if app.get('description'):
                    competitor_info += f"\n   What it does: {app['description'][:150]}"
        
        if total_competitors == 0:
            competitor_info += "\n\nNo direct competitors found on HackerNews or GitHub."
            competitor_info += "\nThis could mean: (1) Highly unique idea, (2) Untapped market, (3) Keywords don't match existing solutions"
        else:
            competitor_info += f"\n\nTOTAL COMPETITORS: {total_competitors}"
            competitor_info += "\nNote: More competitors = Need stronger differentiation"
        
        return f"""Analyze the uniqueness and competitive differentiation of this startup idea against REAL competitors found. Be critical and specific.

IDEA DETAILS:
Title: {idea.title}
Problem: {idea.problem_statement}
Solution: {idea.solution_description}
Target Market: {idea.target_market}
Business Model: {idea.business_model or "Not specified"}
Team Capabilities: {idea.team_capabilities or "Not specified"}{competitor_info}

EVALUATION CRITERIA:
1. Compare against REAL competitors listed above
2. Identify what's truly different vs what's similar
3. Assess if differences are meaningful or superficial
4. Consider if this is 10x better or just incrementally better
5. Evaluate defensibility and barriers to entry

KEY INSIGHT: With {total_competitors} competitors found, differentiation is {"CRITICAL" if total_competitors > 5 else "IMPORTANT" if total_competitors > 0 else "LESS CRITICAL"}

Provide a score from 1-5 where:
- 5: Breakthrough innovation, clearly different from all competitors found
- 4: Significant differentiation with unique approach vs competitors
- 3: Some differentiation but similar to several competitors found
- 2: Limited differentiation, very similar to existing solutions
- 1: Commodity/copycat, no clear difference from competitors

Return JSON with:
- score: 1-5 (based on comparison with ACTUAL competitors found above)
- justifications: 2-3 specific comparisons with the REAL competitors listed
- recommendations: 2-3 actionable ways to differentiate from the SPECIFIC competitors found
- evidence: {{"innovation_level": "breakthrough|significant|incremental|minimal", "competition_level": "high|medium|low|none", "differentiation_strength": "strong|moderate|weak"}}

Be specific - compare this idea directly to the actual competitors found. Cite specific product names."""

