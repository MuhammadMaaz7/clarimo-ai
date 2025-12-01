"""
Validation Orchestrator Service
Coordinates the complete validation pipeline across all scoring components
"""

import asyncio
from typing import Dict, List, Optional
from datetime import datetime
from app.db.models.idea_model import IdeaResponse
from app.db.models.validation_result_model import (
    Score, ValidationStatus, ValidationConfig, ValidationResultResponse
)
from app.db.models.pain_points_model import PainPoint
from app.services.module2_validation.llm_validator import LLMValidator
from app.services.module2_validation.module1_integration_service import Module1IntegrationService
from app.core.logging import logger


class ValidationOrchestrator:
    """
    Orchestrates the complete validation pipeline using LLM-based evaluation
    
    Simplified approach:
    1. Load idea and pain points
    2. Use LLM to evaluate across 4 core metrics
    3. Aggregate results
    4. Handle errors gracefully
    """
    
    def __init__(self):
        # Initialize LLM-based validator (no hardcoded rules)
        self.llm_validator = LLMValidator()
    
    async def validate_idea(
        self,
        idea: IdeaResponse,
        config: Optional[ValidationConfig] = None
    ) -> Dict[str, Score]:
        """
        Execute complete validation pipeline for an idea
        
        Args:
            idea: The idea to validate
            config: Optional validation configuration
            
        Returns:
            Dictionary mapping metric names to Score objects
        """
        if config is None:
            config = ValidationConfig()
        
        logger.info(f"Starting validation for idea {idea.id}")
        
        # Load pain points if linked
        pain_points = []
        if idea.linked_pain_points:
            pain_points = Module1IntegrationService.get_pain_points_by_ids(
                idea.linked_pain_points
            )
            logger.info(f"Loaded {len(pain_points)} pain points for validation")
        
        # Execute all scorers in parallel
        scores = await self._execute_scorers_parallel(idea, pain_points, config)
        
        logger.info(f"Validation completed for idea {idea.id}")
        return scores
    
    async def _execute_scorers_parallel(
        self,
        idea: IdeaResponse,
        pain_points: List[PainPoint],
        config: ValidationConfig
    ) -> Dict[str, Score]:
        """
        Execute all scorers in parallel for optimal performance
        
        Args:
            idea: The idea to validate
            pain_points: Linked pain points
            config: Validation configuration
            
        Returns:
            Dictionary of scores
        """
        # Execute all 4 core metrics using LLM evaluation (no hardcoded rules)
        tasks = {
            "problem_clarity": self._safe_execute(
                "problem_clarity",
                self.llm_validator.evaluate_problem_clarity(idea, pain_points)
            ),
            "market_demand": self._safe_execute(
                "market_demand",
                self.llm_validator.evaluate_market_demand(idea, pain_points)
            ),
            "solution_fit": self._safe_execute(
                "solution_fit",
                self.llm_validator.evaluate_solution_fit(idea, pain_points)
            ),
            "differentiation": self._safe_execute(
                "differentiation",
                self.llm_validator.evaluate_differentiation(idea)
            ),
        }
        
        # Execute all tasks in parallel
        results = await asyncio.gather(*tasks.values(), return_exceptions=True)
        
        # Map results back to metric names
        scores = {}
        for (metric_name, _), result in zip(tasks.items(), results):
            if isinstance(result, Exception):
                logger.error(f"Error in {metric_name} scorer: {str(result)}")
                scores[metric_name] = self._create_error_score(metric_name, str(result))
            else:
                scores[metric_name] = result
        
        return scores
    

    
    async def _safe_execute(self, metric_name: str, coro):
        """
        Safely execute a scorer coroutine with error handling
        
        Args:
            metric_name: Name of the metric being scored
            coro: Coroutine to execute
            
        Returns:
            Score object or raises exception
        """
        try:
            return await coro
        except Exception as e:
            logger.error(f"Error executing {metric_name} scorer: {str(e)}")
            raise
    
    def _create_error_score(self, metric_name: str, error_message: str) -> Score:
        """
        Create an error score when a scorer fails
        
        Args:
            metric_name: Name of the metric
            error_message: Error message
            
        Returns:
            Error Score object
        """
        return Score(
            value=1,
            justifications=[
                f"Unable to evaluate {metric_name} due to an error",
                f"Error: {error_message}"
            ],
            recommendations=[
                "Retry validation",
                "Check system logs for details",
                "Contact support if the issue persists"
            ],
            evidence={
                "error": True,
                "error_message": error_message,
                "metric": metric_name
            },
            metadata={
                "analysis_type": "error",
                "timestamp": datetime.utcnow().isoformat()
            }
        )
    
    def calculate_overall_score(self, scores: Dict[str, Score]) -> float:
        """
        Calculate overall validation score as average of all metrics
        
        Args:
            scores: Dictionary of metric scores
            
        Returns:
            Overall score (1-5)
        """
        if not scores:
            return 1.0
        
        total = sum(score.value for score in scores.values())
        return round(total / len(scores), 2)
    
    def identify_strengths(self, scores: Dict[str, Score]) -> List[str]:
        """
        Identify strengths (metrics with scores >= 4)
        
        Args:
            scores: Dictionary of metric scores
            
        Returns:
            List of strength metric names
        """
        return [
            metric for metric, score in scores.items()
            if score.value >= 4
        ]
    
    def identify_weaknesses(self, scores: Dict[str, Score]) -> List[str]:
        """
        Identify weaknesses (metrics with scores <= 2)
        
        Args:
            scores: Dictionary of metric scores
            
        Returns:
            List of weakness metric names
        """
        return [
            metric for metric, score in scores.items()
            if score.value <= 2
        ]
    
    def aggregate_recommendations(
        self,
        scores: Dict[str, Score],
        max_recommendations: int = 5
    ) -> List[str]:
        """
        Aggregate and prioritize recommendations from all scorers
        
        Args:
            scores: Dictionary of metric scores
            max_recommendations: Maximum number of recommendations to return
            
        Returns:
            List of prioritized recommendations
        """
        all_recommendations = []
        
        # Collect recommendations from weakest areas first
        sorted_scores = sorted(scores.items(), key=lambda x: x[1].value)
        
        for metric, score in sorted_scores:
            for recommendation in score.recommendations:
                # Add metric context to recommendation
                contextualized = f"[{metric.replace('_', ' ').title()}] {recommendation}"
                if contextualized not in all_recommendations:
                    all_recommendations.append(contextualized)
        
        return all_recommendations[:max_recommendations]
    
    async def validate_idea_with_status_tracking(
        self,
        idea: IdeaResponse,
        validation_id: str,
        config: Optional[ValidationConfig] = None
    ) -> ValidationResultResponse:
        """
        Execute validation with status tracking
        
        This method would integrate with your database to track validation status
        
        Args:
            idea: The idea to validate
            validation_id: Unique validation ID
            config: Optional validation configuration
            
        Returns:
            ValidationResultResponse with complete results
        """
        # TODO: Update status to IN_PROGRESS in database
        
        try:
            # Execute validation
            scores = await self.validate_idea(idea, config)
            
            # Calculate overall score
            overall_score = self.calculate_overall_score(scores)
            
            # Identify strengths and weaknesses
            strengths = self.identify_strengths(scores)
            weaknesses = self.identify_weaknesses(scores)
            
            # Aggregate recommendations
            recommendations = self.aggregate_recommendations(scores)
            
            # TODO: Update status to COMPLETED in database
            # TODO: Store scores and report data
            
            return ValidationResultResponse(
                validation_id=validation_id,
                idea_id=idea.id,
                user_id=idea.user_id,
                status=ValidationStatus.COMPLETED,
                overall_score=overall_score,
                individual_scores=scores,
                report_data={
                    "strengths": strengths,
                    "weaknesses": weaknesses,
                    "recommendations": recommendations,
                    "validation_date": datetime.utcnow().isoformat()
                },
                created_at=datetime.utcnow(),
                completed_at=datetime.utcnow(),
                error_message=None
            )
            
        except Exception as e:
            logger.error(f"Validation failed for idea {idea.id}: {str(e)}")
            
            # TODO: Update status to FAILED in database
            
            return ValidationResultResponse(
                validation_id=validation_id,
                idea_id=idea.id,
                user_id=idea.user_id,
                status=ValidationStatus.FAILED,
                overall_score=None,
                individual_scores=None,
                report_data=None,
                created_at=datetime.utcnow(),
                completed_at=datetime.utcnow(),
                error_message=str(e)
            )


# Convenience function for simple validation
async def validate_idea_simple(idea: IdeaResponse) -> Dict[str, Score]:
    """
    Simple validation function for quick use
    
    Args:
        idea: The idea to validate
        
    Returns:
        Dictionary of scores
    """
    orchestrator = ValidationOrchestrator()
    return await orchestrator.validate_idea(idea)
