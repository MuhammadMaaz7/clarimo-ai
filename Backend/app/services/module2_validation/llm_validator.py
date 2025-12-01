"""
LLM-Based Validation Service (Token-Optimized)
Uses LLM to evaluate ideas efficiently with minimal token usage
Supports free APIs (OpenRouter) and local models
"""

import json
import hashlib
from typing import Dict, List, Optional, Any
from datetime import datetime
from app.db.models.validation_result_model import Score
from app.db.models.idea_model import IdeaResponse
from app.db.models.pain_points_model import PainPoint
from app.services.shared.llm_service import LLMService
from app.core.logging import logger


class LLMValidator:
    """
    Token-optimized LLM validator using:
    - Prompt caching to reduce token usage
    - Concise prompts with structured output
    - Free APIs (OpenRouter with free models)
    - Batch evaluation when possible
    """
    
    # Cache for evaluation results (in-memory, can be extended to Redis)
    _evaluation_cache: Dict[str, Score] = {}
    
    def __init__(self):
        self.llm_service = LLMService()
        # Use efficient free models from OpenRouter
        self.model = "mistral-7b-instruct"  # Fast, free model
        self.temperature = 0.2  # Lower temp = more consistent, fewer tokens
        self.max_tokens = 800  # Reduced from 1500 for efficiency
    
    async def evaluate_problem_clarity(
        self,
        idea: IdeaResponse,
        pain_points: List[PainPoint]
    ) -> Score:
        """
        Evaluate problem clarity with caching and token optimization
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
                    "evaluation_type": "llm_based",
                    "timestamp": datetime.utcnow().isoformat(),
                    "model": self.model,
                    "cached": False
                }
            )
            
            # Cache the result
            self._evaluation_cache[cache_key] = score
            return score
            
        except Exception as e:
            logger.error(f"LLM evaluation failed for problem clarity: {str(e)}")
            return self._create_fallback_score("problem_clarity", str(e))
    
    async def evaluate_market_demand(
        self,
        idea: IdeaResponse,
        pain_points: List[PainPoint]
    ) -> Score:
        """
        Evaluate market demand with caching and token optimization
        """
        cache_key = self._get_cache_key("market_demand", idea.id)
        if cache_key in self._evaluation_cache:
            return self._evaluation_cache[cache_key]
        
        prompt = self._create_market_demand_prompt(idea, pain_points)
        
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
                    "evaluation_type": "llm_based",
                    "timestamp": datetime.utcnow().isoformat(),
                    "model": self.model,
                    "cached": False
                }
            )
            
            self._evaluation_cache[cache_key] = score
            return score
            
        except Exception as e:
            logger.error(f"LLM evaluation failed for market demand: {str(e)}")
            return self._create_fallback_score("market_demand", str(e))
    
    async def evaluate_solution_fit(
        self,
        idea: IdeaResponse,
        pain_points: List[PainPoint]
    ) -> Score:
        """
        Evaluate solution fit with caching and token optimization
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
                    "evaluation_type": "llm_based",
                    "timestamp": datetime.utcnow().isoformat(),
                    "model": self.model,
                    "cached": False
                }
            )
            
            self._evaluation_cache[cache_key] = score
            return score
            
        except Exception as e:
            logger.error(f"LLM evaluation failed for solution fit: {str(e)}")
            return self._create_fallback_score("solution_fit", str(e))
    
    async def evaluate_differentiation(
        self,
        idea: IdeaResponse
    ) -> Score:
        """
        Evaluate differentiation with caching and token optimization
        """
        cache_key = self._get_cache_key("differentiation", idea.id)
        if cache_key in self._evaluation_cache:
            return self._evaluation_cache[cache_key]
        
        prompt = self._create_differentiation_prompt(idea)
        
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
                    "evaluation_type": "llm_based",
                    "timestamp": datetime.utcnow().isoformat(),
                    "model": self.model,
                    "cached": False
                }
            )
            
            self._evaluation_cache[cache_key] = score
            return score
            
        except Exception as e:
            logger.error(f"LLM evaluation failed for differentiation: {str(e)}")
            return self._create_fallback_score("differentiation", str(e))
    
    def _get_cache_key(self, metric: str, idea_id: str) -> str:
        """Generate cache key for evaluation results"""
        return hashlib.md5(f"{metric}:{idea_id}".encode()).hexdigest()
    
    def _create_problem_clarity_prompt(
        self,
        idea: IdeaResponse,
        pain_points: List[PainPoint]
    ) -> str:
        """Create concise, token-optimized prompt for problem clarity"""
        
        pain_context = ""
        if pain_points:
            pain_context = f"\nPain Points: {len(pain_points)} found"
            if pain_points:
                pain_context += f" - Top: {pain_points[0].problem_description[:80]}"
        
        return f"""Rate problem clarity (1-5):
Title: {idea.title}
Problem: {idea.problem_statement[:200]}
Market: {idea.target_market}{pain_context}

Score based on: specificity, target audience clarity, evidence, scope.
5=excellent clarity, 1=very unclear

JSON: {{"score": <1-5>, "justifications": ["reason1", "reason2"], "recommendations": ["action1"], "evidence": {{"specificity": "high|med|low"}}}}"""
    
    def _create_market_demand_prompt(
        self,
        idea: IdeaResponse,
        pain_points: List[PainPoint]
    ) -> str:
        """Create concise, token-optimized prompt for market demand"""
        
        engagement = ""
        if pain_points:
            total = sum(len(pp.post_references) for pp in pain_points)
            engagement = f"\nMarket signals: {total} discussions, {len(pain_points)} pain points"
        
        return f"""Rate market demand (1-5):
Title: {idea.title}
Problem: {idea.problem_statement[:150]}
Solution: {idea.solution_description[:150]}{engagement}

Score based on: market signals, problem frequency, engagement, market size, urgency.
5=strong demand evidence, 1=no demand

JSON: {{"score": <1-5>, "justifications": ["reason1", "reason2"], "recommendations": ["action1"], "evidence": {{"demand": "high|med|low"}}}}"""
    
    def _create_solution_fit_prompt(
        self,
        idea: IdeaResponse,
        pain_points: List[PainPoint]
    ) -> str:
        """Create concise, token-optimized prompt for solution fit"""
        
        return f"""Rate solution-problem fit (1-5):
Title: {idea.title}
Problem: {idea.problem_statement[:150]}
Solution: {idea.solution_description[:150]}

Score based on: direct addressing, completeness, feasibility, user adoption, gaps.
5=perfect fit, 1=poor fit

JSON: {{"score": <1-5>, "justifications": ["reason1", "reason2"], "recommendations": ["action1"], "evidence": {{"alignment": "excellent|good|moderate|poor"}}}}"""
    
    def _create_differentiation_prompt(
        self,
        idea: IdeaResponse
    ) -> str:
        """Create concise, token-optimized prompt for differentiation"""
        
        return f"""Rate differentiation & uniqueness (1-5):
Title: {idea.title}
Problem: {idea.problem_statement[:100]}
Solution: {idea.solution_description[:100]}
Market: {idea.target_market}
Model: {(idea.business_model or "Not specified")[:100]}

Score based on: novelty, unique value, competitive advantage, market positioning, innovation.
5=highly innovative, 1=commodity

JSON: {{"score": <1-5>, "justifications": ["reason1", "reason2"], "recommendations": ["action1"], "evidence": {{"innovation": "breakthrough|significant|incremental"}}}}"""
    
    def _create_fallback_score(self, metric_name: str, error_message: str) -> Score:
        """Create a fallback score when LLM evaluation fails"""
        return Score(
            value=3,
            justifications=[
                f"Unable to complete LLM evaluation for {metric_name}",
                "Using neutral score due to evaluation error",
                f"Error: {error_message[:100]}"
            ],
            recommendations=[
                "Retry validation to get proper evaluation",
                "Check system logs for details"
            ],
            evidence={
                "error": True,
                "error_message": error_message,
                "evaluation_type": "fallback"
            },
            metadata={
                "evaluation_type": "fallback",
                "timestamp": datetime.utcnow().isoformat()
            }
        )
