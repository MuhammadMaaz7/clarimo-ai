"""
Problem Clarity Scorer Service
Assesses how clearly an idea defines the problem it solves
"""

import json
import re
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from app.db.models.idea_model import IdeaResponse
from app.db.models.pain_points_model import PainPoint
from app.db.models.validation_result_model import Score
from app.core.logging import logger


class ProblemClarityScorer:
    """Service for scoring problem clarity of startup ideas"""
    
    @staticmethod
    def calculate_engagement_metrics(pain_points: List[PainPoint]) -> Dict[str, Any]:
        """
        Calculate aggregate engagement metrics from pain point post references
        
        Args:
            pain_points: List of pain points with post references
            
        Returns:
            Dictionary with engagement metrics
        """
        if not pain_points:
            return {
                "total_posts": 0,
                "avg_upvotes": 0,
                "avg_comments": 0,
                "total_engagement": 0
            }
        
        total_posts = 0
        total_upvotes = 0
        total_comments = 0
        
        for pain_point in pain_points:
            for post_ref in pain_point.post_references:
                total_posts += 1
                total_upvotes += post_ref.score or 0
                total_comments += post_ref.num_comments or 0
        
        avg_upvotes = total_upvotes / total_posts if total_posts > 0 else 0
        avg_comments = total_comments / total_posts if total_posts > 0 else 0
        total_engagement = avg_upvotes + avg_comments
        
        return {
            "total_posts": total_posts,
            "avg_upvotes": avg_upvotes,
            "avg_comments": avg_comments,
            "total_engagement": total_engagement
        }
    
    @staticmethod
    def score_problem_clarity_rule_based(
        idea: IdeaResponse,
        linked_pain_points: List[PainPoint]
    ) -> tuple[int, List[str], Dict[str, Any]]:
        """
        Rule-based problem clarity scoring
        
        Subtask 4.1: Check for detailed problem statement, award points for linked pain points,
        calculate engagement bonus from pain point metrics
        
        Args:
            idea: The idea to score
            linked_pain_points: Pain points linked to the idea
            
        Returns:
            Tuple of (score, justifications, evidence)
        """
        score = 1  # Base score
        justifications = []
        evidence = {}
        
        # Rule 1: Check if problem statement exists and is detailed (length, specificity)
        problem_length = len(idea.problem_statement.strip())
        evidence["problem_statement_length"] = problem_length
        
        if problem_length > 100:
            score += 1
            justifications.append(f"Detailed problem statement provided ({problem_length} characters)")
        elif problem_length > 50:
            justifications.append(f"Moderate problem statement length ({problem_length} characters)")
        else:
            justifications.append(f"Brief problem statement ({problem_length} characters)")
        
        # Check for specific problem indicators (numbers, examples, specific terms)
        specificity_indicators = [
            r'\d+',  # Numbers
            r'(for example|such as|specifically|particularly)',  # Example phrases
            r'(users?|customers?|people) (struggle|face|experience|need|want)',  # User-focused language
        ]
        
        specificity_count = sum(
            1 for pattern in specificity_indicators
            if re.search(pattern, idea.problem_statement, re.IGNORECASE)
        )
        
        if specificity_count >= 2:
            score = min(5, score + 1)
            justifications.append("Problem statement includes specific details and examples")
            evidence["specificity_indicators"] = specificity_count
        
        # Rule 2: Award points for linked pain points from Module 1
        if linked_pain_points:
            num_pain_points = len(linked_pain_points)
            score += 1
            justifications.append(f"Linked to {num_pain_points} validated pain point(s) from Module 1")
            evidence["linked_pain_points_count"] = num_pain_points
            
            # Rule 3: Calculate engagement bonus from pain point metrics
            engagement_metrics = ProblemClarityScorer.calculate_engagement_metrics(linked_pain_points)
            evidence["engagement_metrics"] = engagement_metrics
            
            # High engagement threshold: avg engagement > 50
            if engagement_metrics["total_engagement"] > 50:
                score = min(5, score + 1)
                justifications.append(
                    f"Pain points show strong user engagement "
                    f"(avg {engagement_metrics['avg_upvotes']:.1f} upvotes, "
                    f"{engagement_metrics['avg_comments']:.1f} comments)"
                )
            elif engagement_metrics["total_engagement"] > 20:
                justifications.append(
                    f"Pain points show moderate user engagement "
                    f"(avg {engagement_metrics['avg_upvotes']:.1f} upvotes, "
                    f"{engagement_metrics['avg_comments']:.1f} comments)"
                )
        else:
            justifications.append("No pain points linked from Module 1")
        
        return score, justifications, evidence
    
    @staticmethod
    async def assess_problem_specificity_llm(
        problem_statement: str,
        description: str
    ) -> Dict[str, Any]:
        """
        Use LLM to assess problem specificity
        
        Subtask 4.2: Create prompt template for problem specificity analysis,
        call LLM API with problem statement and description,
        parse LLM response for concrete examples and specificity level
        
        Args:
            problem_statement: The problem statement to analyze
            description: Full idea description
            
        Returns:
            Dictionary with LLM assessment results
        """
        try:
            # Import here to avoid circular dependencies
            from app.services.shared.llm_service import LLMService
            
            # Create prompt template for problem specificity analysis
            prompt = f"""Analyze this problem statement and determine:
1. Does it reference specific user pain points?
2. Does it include concrete examples or scenarios?
3. Is the problem well-defined or vague?

Problem Statement: {problem_statement}

Idea Description: {description}

Return JSON:
{{
  "has_concrete_examples": boolean,
  "specificity_level": "vague" | "moderate" | "specific",
  "identified_pain_points": [list of specific pain points mentioned],
  "missing_elements": [what would make this clearer]
}}"""
            
            # Call LLM API
            llm_service = LLMService()
            response = await llm_service.call_llm(prompt, response_format="json")
            
            # Parse LLM response
            assessment = json.loads(response)
            
            return {
                "has_concrete_examples": assessment.get("has_concrete_examples", False),
                "specificity_level": assessment.get("specificity_level", "moderate"),
                "identified_pain_points": assessment.get("identified_pain_points", []),
                "missing_elements": assessment.get("missing_elements", [])
            }
            
        except Exception as e:
            logger.error(f"Error in LLM problem specificity assessment: {str(e)}")
            # Return default assessment on error
            return {
                "has_concrete_examples": False,
                "specificity_level": "moderate",
                "identified_pain_points": [],
                "missing_elements": ["Unable to complete LLM analysis"],
                "error": str(e)
            }
    
    @staticmethod
    def generate_clarity_recommendations(
        score: int,
        llm_assessment: Dict[str, Any],
        has_pain_points: bool
    ) -> List[str]:
        """
        Generate specific recommendations based on score
        
        Subtask 4.3: Generate specific recommendations based on score,
        suggest improvements for vague problem statements
        
        Args:
            score: The problem clarity score
            llm_assessment: LLM assessment results
            has_pain_points: Whether pain points are linked
            
        Returns:
            List of actionable recommendations
        """
        recommendations = []
        
        # Recommendations based on score level
        if score <= 2:
            recommendations.append(
                "Provide a more detailed problem statement with specific examples of user pain points"
            )
            recommendations.append(
                "Include concrete scenarios or use cases that illustrate the problem"
            )
            
            if not has_pain_points:
                recommendations.append(
                    "Link validated pain points from Module 1 to strengthen problem definition"
                )
        
        elif score == 3:
            recommendations.append(
                "Add more specific details about who experiences this problem and in what contexts"
            )
            
            if not has_pain_points:
                recommendations.append(
                    "Consider linking pain points from Module 1 for additional validation"
                )
        
        elif score >= 4:
            recommendations.append(
                "Problem is well-defined. Consider gathering user interviews to deepen understanding"
            )
        
        # Recommendations based on LLM assessment
        if llm_assessment.get("specificity_level") == "vague":
            recommendations.append(
                "Make the problem statement more specific by including quantifiable impacts or frequency"
            )
        
        if not llm_assessment.get("has_concrete_examples"):
            recommendations.append(
                "Add concrete examples or real-world scenarios that demonstrate the problem"
            )
        
        # Add missing elements from LLM
        missing_elements = llm_assessment.get("missing_elements", [])
        for element in missing_elements[:2]:  # Limit to top 2 missing elements
            if element and "Unable to complete" not in element:
                recommendations.append(f"Consider adding: {element}")
        
        # Remove duplicates while preserving order
        seen = set()
        unique_recommendations = []
        for rec in recommendations:
            if rec not in seen:
                seen.add(rec)
                unique_recommendations.append(rec)
        
        return unique_recommendations
    
    @staticmethod
    async def score_problem_clarity(
        idea: IdeaResponse,
        linked_pain_points: List[PainPoint]
    ) -> Score:
        """
        Complete problem clarity scoring combining rule-based and LLM assessment
        
        Args:
            idea: The idea to score
            linked_pain_points: Pain points linked to the idea
            
        Returns:
            Score object with value, justifications, evidence, and recommendations
        """
        # Subtask 4.1: Rule-based scoring
        score, justifications, evidence = ProblemClarityScorer.score_problem_clarity_rule_based(
            idea, linked_pain_points
        )
        
        # Subtask 4.2: LLM problem specificity assessment
        llm_assessment = await ProblemClarityScorer.assess_problem_specificity_llm(
            idea.problem_statement,
            idea.description
        )
        
        # Adjust score based on LLM assessment
        if llm_assessment.get("has_concrete_examples") and score < 5:
            score = min(5, score + 1)
            justifications.append("Problem includes concrete examples (LLM verified)")
        
        if llm_assessment.get("specificity_level") == "specific" and score < 5:
            score = min(5, score + 1)
            justifications.append("Problem statement is highly specific (LLM verified)")
        elif llm_assessment.get("specificity_level") == "vague" and score > 1:
            justifications.append("Problem statement could be more specific (LLM assessment)")
        
        # Add LLM assessment to evidence
        evidence["llm_assessment"] = llm_assessment
        
        # Subtask 4.3: Generate recommendations
        recommendations = ProblemClarityScorer.generate_clarity_recommendations(
            score,
            llm_assessment,
            has_pain_points=len(linked_pain_points) > 0
        )
        
        return Score(
            value=min(5, score),
            justifications=justifications,
            evidence=evidence,
            recommendations=recommendations,
            metadata={
                "scorer": "problem_clarity",
                "version": "1.0"
            }
        )
