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

from app.services.shared.llm_service import get_llm_service_for_module2
from app.services.idea_validation.market_data_fetcher import get_market_data_fetcher
from app.core.logging import logger


class LLMEvaluator:
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
        self.external_data_service = get_market_data_fetcher()
        self.temperature = 0.2  # Lower temp = more consistent, fewer tokens
        self.max_tokens = 800  # Reduced from 1500 for efficiency
    
    async def evaluate_problem_clarity(
        self,
        idea: IdeaResponse
    ) -> Score:
        """
        Evaluate problem clarity with caching and automatic fallback
        """
        # Check cache first
        cache_key = self._get_cache_key("problem_clarity", idea.id)
        if cache_key in self._evaluation_cache:
            logger.info(f"Using cached evaluation for {idea.id}")
            return self._evaluation_cache[cache_key]
        
        prompt = self._create_problem_clarity_prompt(idea)
        
        try:
            response = await self.llm_service.call_llm(
                prompt=prompt,
                response_format="json",
                temperature=self.temperature,
                max_tokens=self.max_tokens
            )
            
            # Parse JSON response with error handling
            try:
                result = json.loads(response)
                
                # Validate response structure
                if not isinstance(result, dict):
                    raise ValueError(f"Expected JSON object, got {type(result).__name__}")
                
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
                
            except (json.JSONDecodeError, ValueError) as parse_error:
                logger.error(f"Failed to parse LLM response as JSON: {str(parse_error)}")
                logger.debug(f"Raw response: {response[:200]}")
                raise Exception(f"LLM returned invalid JSON format: {str(parse_error)}")
            
        except Exception as e:
            logger.error(f"All LLM providers failed for problem clarity: {str(e)}")
            # Re-raise - let orchestrator handle
            raise Exception(f"Unable to evaluate problem clarity. All LLM providers failed: {str(e)}")
    
    async def evaluate_market_demand(
        self,
        idea: IdeaResponse
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
        
        prompt = self._create_market_demand_prompt(idea, external_data)
        
        try:
            response = await self.llm_service.call_llm(
                prompt=prompt,
                response_format="json",
                temperature=self.temperature,
                max_tokens=self.max_tokens
            )
            
            # Parse JSON response with error handling
            try:
                result = json.loads(response)
                
                # Validate response structure
                if not isinstance(result, dict):
                    raise ValueError(f"Expected JSON object, got {type(result).__name__}")
                
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
                
            except (json.JSONDecodeError, ValueError) as parse_error:
                logger.error(f"Failed to parse LLM response as JSON: {str(parse_error)}")
                logger.debug(f"Raw response: {response[:200]}")
                raise Exception(f"LLM returned invalid JSON format: {str(parse_error)}")
            
        except Exception as e:
            logger.error(f"All LLM providers failed for market demand: {str(e)}")
            # Re-raise - let orchestrator handle
            raise Exception(f"Unable to evaluate market demand. All LLM providers failed: {str(e)}")
    
    async def evaluate_solution_fit(
        self,
        idea: IdeaResponse
    ) -> Score:
        """
        Evaluate solution fit with caching and automatic fallback
        """
        cache_key = self._get_cache_key("solution_fit", idea.id)
        if cache_key in self._evaluation_cache:
            return self._evaluation_cache[cache_key]
        
        prompt = self._create_solution_fit_prompt(idea)
        
        try:
            response = await self.llm_service.call_llm(
                prompt=prompt,
                response_format="json",
                temperature=self.temperature,
                max_tokens=self.max_tokens
            )
            
            # Parse JSON response with error handling
            try:
                result = json.loads(response)
                
                # Validate response structure
                if not isinstance(result, dict):
                    raise ValueError(f"Expected JSON object, got {type(result).__name__}")
                
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
                
            except (json.JSONDecodeError, ValueError) as parse_error:
                logger.error(f"Failed to parse LLM response as JSON: {str(parse_error)}")
                logger.debug(f"Raw response: {response[:200]}")
                raise Exception(f"LLM returned invalid JSON format: {str(parse_error)}")
            
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
            
            # Parse JSON response with error handling
            try:
                result = json.loads(response)
                
                # Validate response structure
                if not isinstance(result, dict):
                    raise ValueError(f"Expected JSON object, got {type(result).__name__}")
                
                score = Score(
                    value=result.get("score", 3),
                    justifications=result.get("justifications", [])[:2],
                    recommendations=result.get("recommendations", [])[:2],
                    evidence={
                        "competitors_found": {
                            "total": external_data.get("total_products_found", 0),
                            "hackernews": len(external_data.get("hackernews", {}).get("products", [])),
                            "github": len(external_data.get("github", {}).get("repositories", [])),
                            "app_store": len(external_data.get("app_store", {}).get("apps", [])),
                            "play_store": len(external_data.get("play_store", {}).get("apps", []))
                        },
                        **result.get("evidence", {})  # LLM evidence comes after to avoid overwriting
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
                
            except (json.JSONDecodeError, ValueError) as parse_error:
                logger.error(f"Failed to parse LLM response as JSON: {str(parse_error)}")
                logger.debug(f"Raw response: {response[:200]}")
                raise Exception(f"LLM returned invalid JSON format: {str(parse_error)}")
            
        except Exception as e:
            logger.error(f"All LLM providers failed for differentiation: {str(e)}")
            # Re-raise - let orchestrator handle
            raise Exception(f"Unable to evaluate differentiation. All LLM providers failed: {str(e)}")
    
    def _get_cache_key(self, metric: str, idea_id: str) -> str:
        """Generate cache key for evaluation results"""
        return hashlib.md5(f"{metric}:{idea_id}".encode()).hexdigest()
    
    def _create_problem_clarity_prompt(
        self,
        idea: IdeaResponse
    ) -> str:
        """Create data-driven prompt for problem clarity evaluation"""
        
        return f"""You are a CRITICAL startup evaluator. Be HONEST and STRICT. Most ideas are mediocre - don't be afraid to give low scores.

IDEA DETAILS:
Title: {idea.title}
Problem Statement: {idea.problem_statement}
Target Market: {idea.target_market}
Solution: {idea.solution_description[:200]}

CRITICAL EVALUATION CRITERIA:
1. Specificity: Is the problem CLEARLY defined with SPECIFIC details? (Vague = low score)
2. Target Audience: Is it CRYSTAL CLEAR who experiences this? (Broad = low score)
3. Evidence: Is there CONCRETE evidence this problem exists? (No evidence = low score)
4. Scope: Is the scope well-defined? (Too broad/narrow = low score)
5. Impact: Is the severity QUANTIFIED? (Vague impact = low score)

RED FLAGS (penalize heavily):
- Generic problems everyone has (e.g., "people are busy", "communication is hard")
- Overly broad target market (e.g., "everyone", "businesses")
- No specific pain points or evidence
- Problem that doesn't really exist or is already solved
- Unclear who actually suffers from this

SCORING GUIDELINES (be strict):
- 5: Exceptionally clear, specific problem with quantified impact and strong evidence (RARE)
- 4: Clear problem with good specificity and some evidence (UNCOMMON)
- 3: Moderately clear but missing key details or too broad (COMMON)
- 2: Vague, generic, or overly broad problem (VERY COMMON)
- 1: Unclear, non-existent, or already solved problem (COMMON)

IMPORTANT: Most ideas deserve 2-3. Only truly exceptional ideas get 4-5. Be CRITICAL.

Return JSON with:
- score: 1-5 (be STRICT - most ideas are 2-3)
- justifications: 2-3 CRITICAL observations about weaknesses
- recommendations: 2-3 SPECIFIC actions to fix the problems
- evidence: {{"specificity": "high|medium|low", "target_clarity": "clear|moderate|unclear", "evidence_strength": "strong|moderate|weak"}}

Be brutally honest. Reference specific weaknesses from the idea."""
    
    def _create_market_demand_prompt(
        self,
        idea: IdeaResponse,
        external_data: Dict[str, Any]
    ) -> str:
        """Create data-driven prompt for market demand evaluation"""
        
        market_data = ""
        
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
                rating = app.get('rating')
                rating_count = app.get('rating_count', 0)
                rating_str = f"{rating:.1f}⭐ ({rating_count:,} reviews)" if rating is not None else "No rating"
                competitor_data += f"\n   Rating: {rating_str}"
                competitor_data += f"\n   Price: {'Free' if app.get('price', 0) == 0 else f'${app.get('price', 0)}'}"
        
        if play_store_apps:
            competitor_data += f"\n\nPlay Store Apps Found ({len(play_store_apps)}):"
            for i, app in enumerate(play_store_apps[:5], 1):
                competitor_data += f"\n{i}. {app['name']} by {app['developer']}"
                rating = app.get('rating')
                rating_str = f"{rating:.1f}⭐" if rating is not None else "No rating"
                competitor_data += f"\n   Rating: {rating_str}, Installs: {app.get('installs', 'N/A')}"
                competitor_data += f"\n   Price: {'Free' if app.get('free', True) else f'${app.get('price', 0)}'}"
        
        total_found = len(hn_products) + len(github_repos) + len(app_store_apps) + len(play_store_apps)
        
        if total_found == 0:
            competitor_data += "\nNo similar products found on HackerNews or GitHub."
            competitor_data += "\nThis could mean: (1) Untapped market, (2) Keywords don't match existing solutions, (3) Very niche problem"
        
        return f"""You are a CRITICAL market analyst. Be HONEST and DATA-DRIVEN. Don't inflate scores.

IDEA DETAILS:
Title: {idea.title}
Problem: {idea.problem_statement}
Solution: {idea.solution_description}
Target Market: {idea.target_market}{market_data}{competitor_data}

CRITICAL EVALUATION:
1. Market Validation: Do similar products exist? (None = unproven market = LOW score)
2. Engagement: Are people actually using/discussing these solutions? (Low engagement = LOW score)
3. Market Size: Is this a real market or a niche hobby? (Tiny market = LOW score)
4. Growth: Is this market growing or dying? (Dying = LOW score)

RED FLAGS (penalize heavily):
- No competitors found = unproven market (score 1-2)
- Competitors exist but have low engagement = weak demand (score 2-3)
- Saturated market with giants (Google, Microsoft, etc.) = hard to compete (score 2-3)
- Niche market with <1000 potential users = too small (score 1-2)
- Declining market or outdated problem = bad timing (score 1-2)

SCORING GUIDELINES (be strict):
- 5: Proven market with 10+ competitors AND high engagement (RARE - only for hot markets)
- 4: Validated market with 5-10 competitors AND good engagement (UNCOMMON)
- 3: Some validation with 2-5 competitors OR moderate engagement (COMMON)
- 2: Weak validation with 1-2 competitors OR low engagement (VERY COMMON)
- 1: No competitors = unproven market OR dying market (COMMON)

IMPORTANT: 
- No competitors = LOW score (unproven market is risky)
- Many competitors = HIGHER score (proven demand) BUT penalize if saturated
- Low engagement on existing solutions = LOW score (weak demand)
- Be CRITICAL - most ideas are 2-3

Return JSON with:
- score: 1-5 (be STRICT based on actual data - don't inflate)
- justifications: 2-3 CRITICAL observations about market reality
- recommendations: 2-3 SPECIFIC actions based on market gaps
- evidence: {{"demand_level": "high|medium|low", "competitors_found": {total_found}, "market_validation": "strong|moderate|weak"}}

Be brutally honest about market reality. Cite specific data."""
    
    def _create_solution_fit_prompt(
        self,
        idea: IdeaResponse
    ) -> str:
        """Create data-driven prompt for solution-problem fit evaluation"""
        
        return f"""You are a CRITICAL product evaluator. Be HONEST about solution-problem fit. Most solutions are mediocre.

IDEA DETAILS:
Title: {idea.title}
Problem Statement: {idea.problem_statement}
Solution Description: {idea.solution_description}
Target Market: {idea.target_market}
Business Model: {idea.business_model or "Not specified"}
Team Capabilities: {idea.team_capabilities or "Not specified"}

CRITICAL EVALUATION:
1. Direct Addressing: Does this ACTUALLY solve the problem? (Indirect = LOW score)
2. Completeness: Does it solve the WHOLE problem or just a tiny part? (Partial = LOW score)
3. Feasibility: Can this REALISTICALLY be built? (Unfeasible = LOW score)
4. User Adoption: Would users ACTUALLY switch to this? (Unlikely = LOW score)
5. Complexity: Is it too complex or too simple? (Both = LOW score)

RED FLAGS (penalize heavily):
- Solution doesn't directly address the stated problem (score 1-2)
- Overly complex solution that users won't adopt (score 2-3)
- Technically unfeasible or requires breakthrough tech (score 1-2)
- Solution already exists and works well (score 2-3)
- Solves only 10% of the problem (score 2-3)
- No clear business model or monetization (score 2-3)
- Team lacks capabilities to build this (score 2-3)

SCORING GUIDELINES (be strict):
- 5: Perfect fit, feasible, complete solution (VERY RARE - almost never)
- 4: Strong fit with minor gaps, clearly feasible (RARE)
- 3: Decent fit but missing key aspects or feasibility concerns (COMMON)
- 2: Weak fit, significant gaps, or unfeasible (VERY COMMON)
- 1: Doesn't solve the problem or completely unfeasible (COMMON)

IMPORTANT:
- If solution is vague or generic = LOW score (2-3)
- If solution is just "an app" or "a platform" = LOW score (2-3)
- If no clear differentiation from existing solutions = LOW score (2-3)
- Be CRITICAL - most ideas are 2-3

Return JSON with:
- score: 1-5 (be STRICT - most solutions are flawed)
- justifications: 2-3 CRITICAL observations about gaps and weaknesses
- recommendations: 2-3 SPECIFIC improvements needed
- evidence: {{"alignment": "excellent|good|moderate|poor", "completeness": "complete|partial|incomplete", "feasibility": "high|medium|low"}}

Be brutally honest about whether this solution actually works."""
    
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
                rating = app.get('rating')
                rating_count = app.get('rating_count', 0)
                rating_str = f"{rating:.1f}⭐ ({rating_count:,} reviews)" if rating is not None else "No rating"
                competitor_info += f"\n   Rating: {rating_str}"
                competitor_info += f"\n   Price: {'Free' if app.get('price', 0) == 0 else f'${app.get('price', 0)}'}"
                if app.get('description'):
                    competitor_info += f"\n   What it does: {app['description'][:150]}"
        
        if play_store_apps:
            competitor_info += f"\n\nPlay Store Apps ({len(play_store_apps)}):"
            for i, app in enumerate(play_store_apps[:5], 1):
                competitor_info += f"\n{i}. {app['name']} by {app['developer']}"
                rating = app.get('rating')
                rating_str = f"{rating:.1f}⭐" if rating is not None else "No rating"
                competitor_info += f"\n   Rating: {rating_str}"
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
        
        return f"""You are a CRITICAL competitive analyst. Be BRUTALLY HONEST about differentiation. Most ideas are copycats.

IDEA DETAILS:
Title: {idea.title}
Problem: {idea.problem_statement}
Solution: {idea.solution_description}
Target Market: {idea.target_market}
Business Model: {idea.business_model or "Not specified"}
Team Capabilities: {idea.team_capabilities or "Not specified"}{competitor_info}

CRITICAL EVALUATION:
1. Compare against REAL competitors above - what's ACTUALLY different?
2. Are differences MEANINGFUL or just superficial marketing?
3. Is this 10x better or just 10% better? (10% = LOW score)
4. Can competitors easily copy this? (Easy to copy = LOW score)
5. Does this have defensible moats? (No moats = LOW score)

RED FLAGS (penalize heavily):
- Exact copy of existing solution (score 1)
- Only difference is "better UI" or "easier to use" (score 2)
- Competing with tech giants (Google, Microsoft, etc.) without clear advantage (score 1-2)
- No unique technology, data, or network effects (score 2-3)
- Differences are just marketing fluff, not real innovation (score 2-3)
- "We'll do it better" without explaining how (score 2)
- Entering saturated market with {total_competitors}+ competitors (score 2-3)

SCORING GUIDELINES (be VERY strict):
- 5: Breakthrough innovation, completely new approach (EXTREMELY RARE - almost never)
- 4: Significant differentiation with clear 10x improvement (VERY RARE)
- 3: Some differentiation but incremental improvement (UNCOMMON)
- 2: Minimal differentiation, mostly similar to competitors (VERY COMMON)
- 1: Copycat or commodity, no meaningful difference (COMMON)

IMPORTANT:
- With {total_competitors} competitors, differentiation is {"CRITICAL - score harshly" if total_competitors > 5 else "IMPORTANT - be strict" if total_competitors > 0 else "LESS CRITICAL but still evaluate"}
- "Better" is not differentiation - need UNIQUE approach
- If you can't identify clear differences = LOW score (1-2)
- Most ideas are copycats = score 2-3
- Be CRITICAL - true innovation is rare

Return JSON with:
- score: 1-5 (be BRUTALLY STRICT - most ideas are 1-2)
- justifications: 2-3 CRITICAL comparisons showing why this is NOT differentiated
- recommendations: 2-3 SPECIFIC ways to create REAL differentiation
- evidence: {{"innovation_level": "breakthrough|significant|incremental|minimal", "competition_level": "high|medium|low|none", "differentiation_strength": "strong|moderate|weak"}}

Be brutally honest. Compare directly to actual competitors. Don't sugarcoat."""
