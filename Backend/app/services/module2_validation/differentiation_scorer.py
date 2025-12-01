"""
Differentiation Scorer Service
Assesses idea uniqueness and differentiation potential (lightweight version)

Note: This is a basic uniqueness assessment. For comprehensive competitor analysis,
users should use Module 3 - Competitor Analysis.
"""

import json
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from app.db.models.idea_model import IdeaResponse
from app.db.models.validation_result_model import Score
from app.core.logging import logger


class DifferentiationScorer:
    """Service for assessing idea uniqueness and differentiation potential"""
    
    @staticmethod
    async def assess_uniqueness_llm(
        idea_description: str,
        solution: str,
        problem_statement: str,
        target_market: str
    ) -> Dict[str, Any]:
        """
        Use LLM to assess idea uniqueness based on description alone
        
        Subtask 7.1: Use LLM to assess idea uniqueness based on description alone
        Subtask 7.2: Create prompt asking LLM to identify unique aspects of the idea,
                     ask LLM to estimate likelihood of existing solutions,
                     parse differentiation score (1-5) based on uniqueness
        
        Args:
            idea_description: Full idea description
            solution: Proposed solution description
            problem_statement: Problem the idea solves
            target_market: Target market or audience
            
        Returns:
            Dictionary with uniqueness assessment results
        """
        try:
            # Import here to avoid circular dependencies
            from app.services.shared.llm_service import LLMService
            
            # Create prompt template for uniqueness assessment
            # Subtask 7.2: Create prompt asking LLM to identify unique aspects
            prompt = f"""Analyze the uniqueness and differentiation potential of this startup idea.

Idea: {idea_description}
Problem: {problem_statement}
Solution: {solution}
Target Market: {target_market}

Based ONLY on the idea description (without searching for competitors), assess:
1. What unique aspects or innovations does this idea have?
2. What is the likelihood that similar solutions already exist?
3. What makes this idea potentially different from typical solutions in this space?
4. What are the key value propositions that could differentiate this idea?

Assign a uniqueness score (1-5):
1 = Very common idea, likely many existing solutions
2 = Somewhat common, minor unique aspects
3 = Moderate uniqueness, some differentiating factors
4 = Strong uniqueness, clear innovative elements
5 = Highly unique, breakthrough concept

Return JSON:
{{
  "uniqueness_score": 1-5,
  "justifications": [reasons for score],
  "unique_aspects": [list of unique/innovative elements in the idea],
  "likely_competition_level": "high|medium|low",
  "recommendations": [how to strengthen differentiation]
}}

Note: This is a preliminary assessment. For comprehensive competitor analysis, 
the user should use Module 3 - Competitor Analysis."""
            
            # Call LLM API
            llm_service = LLMService()
            response = await llm_service.call_llm(prompt, response_format="json")
            
            # Parse LLM response
            assessment = json.loads(response)
            
            # Validate and extract fields
            uniqueness_score = assessment.get("uniqueness_score", 3)
            
            # Ensure score is in valid range
            if not isinstance(uniqueness_score, int) or uniqueness_score < 1 or uniqueness_score > 5:
                logger.warning(f"Invalid uniqueness score from LLM: {uniqueness_score}, defaulting to 3")
                uniqueness_score = 3
            
            return {
                "uniqueness_score": uniqueness_score,
                "justifications": assessment.get("justifications", []),
                "unique_aspects": assessment.get("unique_aspects", []),
                "likely_competition_level": assessment.get("likely_competition_level", "medium"),
                "recommendations": assessment.get("recommendations", [])
            }
            
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing LLM JSON response in uniqueness assessment: {str(e)}")
            # Return default assessment on JSON parse error
            return {
                "uniqueness_score": 3,
                "justifications": ["Unable to parse LLM response"],
                "unique_aspects": [],
                "likely_competition_level": "medium",
                "recommendations": ["Retry assessment or conduct manual competitor research"],
                "error": str(e)
            }
        except Exception as e:
            logger.error(f"Error in LLM uniqueness assessment: {str(e)}")
            # Return default assessment on error
            return {
                "uniqueness_score": 3,
                "justifications": ["Unable to complete LLM analysis due to service error"],
                "unique_aspects": [],
                "likely_competition_level": "medium",
                "recommendations": ["Retry assessment when LLM service is available"],
                "error": str(e)
            }
    
    @staticmethod
    def generate_differentiation_recommendations(
        uniqueness_score: int,
        unique_aspects: List[str],
        likely_competition_level: str,
        llm_recommendations: List[str]
    ) -> List[str]:
        """
        Generate recommendations to strengthen differentiation
        
        Subtask 7.3: Suggest ways to strengthen unique value proposition,
                     recommend conducting full competitor analysis (Module 3)
        
        Args:
            uniqueness_score: The uniqueness score (1-5)
            unique_aspects: List of unique aspects identified
            likely_competition_level: Estimated competition level
            llm_recommendations: Recommendations from LLM
            
        Returns:
            List of actionable recommendations
        """
        recommendations = []
        
        # Recommendations based on uniqueness score
        if uniqueness_score <= 2:
            recommendations.append(
                "Identify and emphasize unique features that set your solution apart from competitors"
            )
            recommendations.append(
                "Consider targeting a specific niche market to differentiate from broader solutions"
            )
            recommendations.append(
                "Explore innovative approaches or technologies that competitors may not be using"
            )
        elif uniqueness_score == 3:
            recommendations.append(
                "Strengthen your unique value proposition by highlighting key differentiators"
            )
            recommendations.append(
                "Research competitor offerings to identify gaps you can fill"
            )
        elif uniqueness_score >= 4:
            recommendations.append(
                "Document and protect your unique innovations (consider IP strategy)"
            )
            recommendations.append(
                "Focus on maintaining your competitive advantage as you scale"
            )
        
        # Recommendations based on competition level
        if likely_competition_level == "high":
            recommendations.append(
                "High competition detected - focus on clear differentiation and niche positioning"
            )
            recommendations.append(
                "Consider what makes your approach 10x better, not just incrementally better"
            )
        elif likely_competition_level == "medium":
            recommendations.append(
                "Moderate competition expected - identify your 2-3 key differentiators"
            )
        
        # Add LLM recommendations (limit to avoid duplication)
        for rec in llm_recommendations[:2]:
            if rec and rec not in recommendations:
                recommendations.append(rec)
        
        # Always recommend comprehensive competitor analysis
        recommendations.append(
            "Conduct comprehensive competitor analysis using Module 3 for detailed insights"
        )
        
        # Remove duplicates while preserving order
        seen = set()
        unique_recommendations = []
        for rec in recommendations:
            if rec not in seen:
                seen.add(rec)
                unique_recommendations.append(rec)
        
        return unique_recommendations
    
    @staticmethod
    async def score_differentiation(
        idea: IdeaResponse
    ) -> Score:
        """
        Complete differentiation scoring using LLM-based uniqueness assessment
        
        This is a lightweight assessment focused on identifying unique value propositions
        in the idea itself. For comprehensive competitor analysis, users should use Module 3.
        
        Args:
            idea: The idea to score
            
        Returns:
            Score object with value, justifications, evidence, and recommendations
        """
        # Subtask 7.1 & 7.2: LLM uniqueness assessment
        uniqueness_assessment = await DifferentiationScorer.assess_uniqueness_llm(
            idea_description=idea.description,
            solution=idea.solution_description,
            problem_statement=idea.problem_statement,
            target_market=idea.target_market
        )
        
        # Extract score and justifications from LLM assessment
        score = uniqueness_assessment.get("uniqueness_score", 3)
        justifications = uniqueness_assessment.get("justifications", [])
        unique_aspects = uniqueness_assessment.get("unique_aspects", [])
        likely_competition_level = uniqueness_assessment.get("likely_competition_level", "medium")
        
        # Build evidence dictionary
        evidence = {
            "unique_aspects": unique_aspects,
            "likely_competition_level": likely_competition_level,
            "assessment_type": "basic_uniqueness",
            "llm_assessment": uniqueness_assessment
        }
        
        # Add context about unique aspects to justifications
        if unique_aspects:
            justifications.append(
                f"Identified {len(unique_aspects)} unique aspect(s): {', '.join(unique_aspects[:3])}"
            )
        
        # Add competition level context
        competition_context = {
            "high": "High likelihood of existing solutions in this space",
            "medium": "Moderate likelihood of existing solutions",
            "low": "Low likelihood of existing solutions - potentially novel space"
        }
        if likely_competition_level in competition_context:
            justifications.append(competition_context[likely_competition_level])
        
        # Subtask 7.3: Generate recommendations
        recommendations = DifferentiationScorer.generate_differentiation_recommendations(
            uniqueness_score=score,
            unique_aspects=unique_aspects,
            likely_competition_level=likely_competition_level,
            llm_recommendations=uniqueness_assessment.get("recommendations", [])
        )
        
        return Score(
            value=score,
            justifications=justifications,
            evidence=evidence,
            recommendations=recommendations,
            metadata={
                "scorer": "differentiation",
                "version": "1.0",
                "analysis_type": "basic_uniqueness",
                "full_analysis_available_in": "module_3_competitor_analysis"
            }
        )

