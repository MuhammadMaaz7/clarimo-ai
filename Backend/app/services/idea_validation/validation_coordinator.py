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
from app.services.idea_validation.llm_evaluator import LLMEvaluator
from app.core.logging import logger


class ValidationCoordinator:
    """
    Orchestrates the complete validation pipeline using LLM-based evaluation
    
    Simplified approach:
    1. Load idea
    2. Use LLM to evaluate across 4 core metrics
    3. Aggregate results
    4. Handle errors gracefully
    
    Note: Pain points integration removed - Module 1 and Module 2 are now separate
    """
    
    def __init__(self):
        # Initialize LLM-based validator (no hardcoded rules)
        self.llm_validator = LLMEvaluator()
    
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
        
        # Execute all scorers sequentially to avoid rate limiting
        scores = await self._execute_scorers_sequential(idea, config)
        
        logger.info(f"Validation completed for idea {idea.id}")
        return scores
    
    async def _execute_scorers_sequential(
        self,
        idea: IdeaResponse,
        config: ValidationConfig
    ) -> Dict[str, Score]:
        """
        Execute all scorers sequentially to avoid API rate limiting
        
        Running in parallel causes all 4 metrics to hit the same API simultaneously,
        leading to rate limits. Sequential execution is more reliable.
        
        Args:
            idea: The idea to validate
            config: Validation configuration
            
        Returns:
            Dictionary of scores
        """
        scores = {}
        
        # Execute metrics one by one
        metrics = [
            ("problem_clarity", self.llm_validator.evaluate_problem_clarity),
            ("market_demand", self.llm_validator.evaluate_market_demand),
            ("solution_fit", self.llm_validator.evaluate_solution_fit),
            ("differentiation", self.llm_validator.evaluate_differentiation),
        ]
        
        for metric_name, evaluator_func in metrics:
            try:
                logger.info(f"Evaluating {metric_name}...")
                score = await evaluator_func(idea)
                scores[metric_name] = score
                logger.info(f"✓ {metric_name} completed")
            except Exception as e:
                logger.error(f"Error in {metric_name} scorer: {str(e)}")
                scores[metric_name] = self._create_error_score(metric_name, str(e))
        
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
            },
            error=True,
            error_message=error_message
        )
    
    # Metric weights for overall score calculation
    METRIC_WEIGHTS = {
        "problem_clarity": 0.30,      # 30% - Most critical: no problem = no startup
        "market_demand": 0.30,        # 30% - Equally critical: no market = no business
        "solution_fit": 0.25,         # 25% - Very important: bad solution = failure
        "differentiation": 0.15       # 15% - Important but can evolve through pivots
    }
    
    def calculate_overall_score(self, scores: Dict[str, Score]) -> float:
        """
        Calculate overall validation score as WEIGHTED average
        
        Weights reflect importance in startup success:
        - Problem Clarity: 30% (most important - no problem = no startup)
        - Market Demand: 30% (critical - no market = no business)
        - Solution Fit: 25% (important - bad solution = failure)
        - Differentiation: 15% (nice to have - can pivot later)
        
        Why weighted?
        - Not all metrics are equally important for startup success
        - Problem and market are foundational - can't succeed without them
        - Solution can be iterated and improved
        - Differentiation can evolve through pivots
        
        Args:
            scores: Dictionary of metric scores
            
        Returns:
            Weighted overall score (1-5)
        """
        if not scores:
            return 1.0
        
        # Calculate weighted sum
        weighted_sum = 0.0
        total_weight = 0.0
        
        for metric_name, score in scores.items():
            weight = self.METRIC_WEIGHTS.get(metric_name, 0.25)  # Default weight if metric not in dict
            weighted_sum += score.value * weight
            total_weight += weight
        
        # Normalize by total weight (in case some metrics are missing)
        if total_weight == 0:
            return 1.0
        
        weighted_average = weighted_sum / total_weight
        return round(weighted_average, 2)
    
    @classmethod
    def get_metric_weights(cls) -> Dict[str, float]:
        """
        Get the metric weights used for overall score calculation
        
        Returns:
            Dictionary of metric names to weights
        """
        return cls.METRIC_WEIGHTS.copy()
    
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
            
            # Check if ALL metrics failed (all have error=True)
            all_failed = all(
                score.error == True 
                for score in scores.values()
            )
            
            if all_failed:
                # If all metrics failed, mark validation as FAILED
                error_messages = [score.error_message for score in scores.values() if score.error_message]
                combined_error = error_messages[0] if error_messages else "All validation metrics failed"
                
                logger.error(f"All metrics failed for validation {validation_id}")
                
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
                    error_message=f"Validation failed: {combined_error}. Please check your API keys or try again later."
                )
            
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
    orchestrator = ValidationCoordinator()
    return await orchestrator.validate_idea(idea)
