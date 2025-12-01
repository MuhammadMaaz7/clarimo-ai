"""
Solution Fit Evaluator Service
Assesses how well a proposed solution addresses the identified problem
"""

import json
from typing import List, Optional, Dict, Any
from app.db.models.validation_result_model import Score
from app.db.models.idea_model import IdeaResponse
from app.db.models.pain_points_model import PainPoint
from app.services.shared.llm_service import LLMService
from app.services.module1_pain_points.pain_point_extractor_service import PainPointExtractorService
from app.core.logging import logger


class SolutionFitEvaluator:
    """Service for evaluating solution-problem fit"""
    
    def __init__(self):
        self.llm_service = LLMService()
        self.pain_point_extractor = PainPointExtractorService()
    
    async def evaluate_solution_fit(
        self,
        idea: IdeaResponse,
        linked_pain_points: List[PainPoint]
    ) -> Score:
        """
        Evaluate how well the proposed solution addresses the problem
        
        Args:
            idea: The idea to evaluate
            linked_pain_points: Pain points linked to the idea
            
        Returns:
            Score object with fit assessment
        """
        try:
            # If pain points are linked, use them for detailed analysis
            if linked_pain_points:
                return await self._evaluate_with_pain_points(idea, linked_pain_points)
            else:
                # Without pain points, assess based on idea's own problem statement
                return await self._evaluate_standalone(idea)
                
        except Exception as e:
            logger.error(f"Error evaluating solution fit: {str(e)}")
            return self._create_error_score(str(e))
    
    async def _evaluate_with_pain_points(
        self,
        idea: IdeaResponse,
        pain_points: List[PainPoint]
    ) -> Score:
        """
        Evaluate solution fit with pain point context
        
        Args:
            idea: The idea to evaluate
            pain_points: Linked pain points
            
        Returns:
            Score object
        """
        # Extract problem characteristics from pain points
        problem_characteristics = self.pain_point_extractor.format_for_solution_fit_analysis(pain_points)
        
        # Create LLM prompt
        prompt = self._create_solution_fit_prompt_with_pain_points(
            solution=idea.solution_description,
            problem_statement=idea.problem_statement,
            problem_characteristics=problem_characteristics,
            pain_point_descriptions=[pp.problem_description for pp in pain_points]
        )
        
        # Call LLM
        try:
            response = await self.llm_service.call_llm(
                prompt=prompt,
                response_format="json",
                temperature=0.3,  # Lower temperature for more consistent scoring
                max_tokens=1500
            )
            
            # Parse response
            fit_analysis = json.loads(response)
            
            # Extract score and details
            fit_score = fit_analysis.get("fit_score", 3)
            justifications = fit_analysis.get("justifications", [])
            identified_gaps = fit_analysis.get("identified_gaps", [])
            recommendations = fit_analysis.get("recommendations", [])
            
            # Validate score range
            fit_score = max(1, min(5, fit_score))
            
            # Build metadata
            metadata = {
                "analysis_type": "with_pain_points",
                "pain_point_count": len(pain_points),
                "gaps_identified": len(identified_gaps)
            }
            
            return Score(
                value=fit_score,
                justifications=justifications,
                recommendations=recommendations,
                evidence={
                    "identified_gaps": identified_gaps,
                    "pain_points_analyzed": len(pain_points)
                },
                metadata=metadata
            )
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse LLM response for solution fit: {str(e)}")
            return self._create_fallback_score(idea, pain_points)
        except Exception as e:
            logger.error(f"LLM call failed for solution fit: {str(e)}")
            return self._create_fallback_score(idea, pain_points)
    
    async def _evaluate_standalone(self, idea: IdeaResponse) -> Score:
        """
        Evaluate solution fit without pain points
        
        Args:
            idea: The idea to evaluate
            
        Returns:
            Score object
        """
        # Create LLM prompt
        prompt = self._create_solution_fit_prompt_standalone(
            solution=idea.solution_description,
            problem_statement=idea.problem_statement,
            description=idea.description
        )
        
        # Call LLM
        try:
            response = await self.llm_service.call_llm(
                prompt=prompt,
                response_format="json",
                temperature=0.3,
                max_tokens=1500
            )
            
            # Parse response
            fit_analysis = json.loads(response)
            
            # Extract score and details
            fit_score = fit_analysis.get("fit_score", 3)
            justifications = fit_analysis.get("justifications", [])
            identified_gaps = fit_analysis.get("identified_gaps", [])
            recommendations = fit_analysis.get("recommendations", [])
            
            # Validate score range
            fit_score = max(1, min(5, fit_score))
            
            # Build metadata
            metadata = {
                "analysis_type": "standalone",
                "pain_point_count": 0
            }
            
            return Score(
                value=fit_score,
                justifications=justifications,
                recommendations=recommendations,
                evidence={
                    "identified_gaps": identified_gaps
                },
                metadata=metadata
            )
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse LLM response for solution fit: {str(e)}")
            return self._create_fallback_score(idea, [])
        except Exception as e:
            logger.error(f"LLM call failed for solution fit: {str(e)}")
            return self._create_fallback_score(idea, [])
    
    def _create_solution_fit_prompt_with_pain_points(
        self,
        solution: str,
        problem_statement: str,
        problem_characteristics: str,
        pain_point_descriptions: List[str]
    ) -> str:
        """
        Create LLM prompt for solution fit evaluation with pain points
        
        Args:
            solution: Proposed solution description
            problem_statement: Problem statement from idea
            problem_characteristics: Formatted pain point characteristics
            pain_point_descriptions: List of pain point descriptions
            
        Returns:
            Formatted prompt string
        """
        pain_points_text = "\n".join([f"  - {desc}" for desc in pain_point_descriptions])
        
        prompt = f"""You are evaluating how well a proposed solution addresses a problem based on real user pain points discovered from Reddit discussions.

Problem Statement (from entrepreneur):
{problem_statement}

Validated Pain Points from Reddit:
{pain_points_text}

{problem_characteristics}

Proposed Solution:
{solution}

Evaluate the solution-problem fit on a scale of 1-5:
1 = Weak connection, solution doesn't address core problem
2 = Partial fit, addresses some aspects but misses key elements
3 = Moderate fit, addresses main problem but not comprehensively
4 = Strong fit, directly solves most aspects of the problem
5 = Perfect fit, comprehensively addresses all problem dimensions

Consider:
1. Does the solution directly address the pain points mentioned in Reddit discussions?
2. Does it solve the root cause or just symptoms?
3. Are there aspects of the problem that the solution doesn't address?
4. Does the solution align with what users are actually asking for?

Return JSON:
{{
  "fit_score": 1-5,
  "justifications": [list of 3-5 specific reasons for the score],
  "identified_gaps": [aspects of problem not addressed by solution],
  "recommendations": [3-5 specific ways to improve solution-problem fit]
}}

IMPORTANT: Respond with valid JSON only, no additional text."""
        
        return prompt
    
    def _create_solution_fit_prompt_standalone(
        self,
        solution: str,
        problem_statement: str,
        description: str
    ) -> str:
        """
        Create LLM prompt for solution fit evaluation without pain points
        
        Args:
            solution: Proposed solution description
            problem_statement: Problem statement from idea
            description: Full idea description
            
        Returns:
            Formatted prompt string
        """
        prompt = f"""You are evaluating how well a proposed solution addresses a stated problem.

Problem Statement:
{problem_statement}

Full Idea Description:
{description}

Proposed Solution:
{solution}

Evaluate the solution-problem fit on a scale of 1-5:
1 = Weak connection, solution doesn't address core problem
2 = Partial fit, addresses some aspects but misses key elements
3 = Moderate fit, addresses main problem but not comprehensively
4 = Strong fit, directly solves most aspects of the problem
5 = Perfect fit, comprehensively addresses all problem dimensions

Consider:
1. Is there a clear logical connection between the problem and solution?
2. Does the solution address the root cause or just symptoms?
3. Are there obvious gaps in how the solution addresses the problem?
4. Is the solution scope appropriate for the problem scope?

Return JSON:
{{
  "fit_score": 1-5,
  "justifications": [list of 3-5 specific reasons for the score],
  "identified_gaps": [aspects of problem not addressed by solution],
  "recommendations": [3-5 specific ways to improve solution-problem fit]
}}

IMPORTANT: Respond with valid JSON only, no additional text."""
        
        return prompt
    
    def _create_fallback_score(
        self,
        idea: IdeaResponse,
        pain_points: List[PainPoint]
    ) -> Score:
        """
        Create a fallback score when LLM fails
        
        Args:
            idea: The idea being evaluated
            pain_points: Linked pain points
            
        Returns:
            Fallback Score object
        """
        # Use simple heuristics for fallback
        score = 3  # Default moderate score
        justifications = []
        recommendations = []
        
        # Check if solution description is detailed
        if len(idea.solution_description) > 200:
            justifications.append("Solution description is detailed")
        else:
            justifications.append("Solution description could be more detailed")
            recommendations.append("Provide more details about how the solution works")
        
        # Check if problem statement is clear
        if len(idea.problem_statement) > 100:
            justifications.append("Problem statement is well-defined")
        else:
            justifications.append("Problem statement could be more specific")
            recommendations.append("Clarify the specific problem being solved")
        
        # Check if pain points are linked
        if pain_points:
            justifications.append(f"Solution is linked to {len(pain_points)} validated pain points")
        else:
            justifications.append("No validated pain points linked - consider connecting to real user problems")
            recommendations.append("Link pain points from Module 1 to validate problem-solution fit")
        
        recommendations.append("Retry validation when LLM service is available for detailed analysis")
        
        return Score(
            value=score,
            justifications=justifications,
            recommendations=recommendations,
            evidence={
                "fallback": True,
                "reason": "LLM service unavailable"
            },
            metadata={
                "analysis_type": "fallback",
                "pain_point_count": len(pain_points)
            }
        )
    
    def _create_error_score(self, error_message: str) -> Score:
        """
        Create an error score
        
        Args:
            error_message: Error message
            
        Returns:
            Error Score object
        """
        return Score(
            value=1,
            justifications=[
                "Unable to evaluate solution fit due to an error",
                f"Error: {error_message}"
            ],
            recommendations=[
                "Retry validation",
                "Check that all required fields are properly filled",
                "Contact support if the issue persists"
            ],
            evidence={
                "error": True,
                "error_message": error_message
            },
            metadata={
                "analysis_type": "error"
            }
        )
