"""
Report Generator Service
Generates comprehensive validation reports with executive summaries and visualizations
"""

import json
from typing import Dict, List, Optional, Any
from datetime import datetime
from app.db.models.idea_model import IdeaResponse
from app.db.models.validation_result_model import (
    Score, ValidationReport
)
from app.services.shared.unified_llm_service import get_llm_service_for_module2
from app.core.logging import logger


class ReportGeneratorService:
    """
    Service for generating comprehensive validation reports
    
    Responsibilities:
    - Calculate overall scores from individual metrics
    - Identify strengths and weaknesses
    - Aggregate and prioritize recommendations
    - Generate executive summaries using LLM
    - Prepare visualization data structures
    """
    
    def __init__(self):
        self.llm_service = get_llm_service_for_module2()
    
    async def generate_validation_report(
        self,
        validation_id: str,
        scores: Dict[str, Score],
        idea: IdeaResponse
    ) -> ValidationReport:
        """
        Generate comprehensive validation report
        
        Args:
            validation_id: Unique validation identifier
            scores: Dictionary mapping metric names to Score objects
            idea: The idea being validated
            
        Returns:
            ValidationReport with complete analysis
        """
        logger.info(f"Generating validation report for validation {validation_id}")
        
        # Calculate overall score
        overall_score = self._calculate_overall_score(scores)
        
        # Identify strengths and weaknesses
        strengths = self._identify_strengths(scores)
        weaknesses = self._identify_weaknesses(scores)
        
        # Aggregate recommendations
        critical_recommendations = self._aggregate_recommendations(scores, weaknesses)
        
        # Prepare visualization data
        radar_chart_data = self._prepare_radar_chart_data(scores)
        score_distribution = self._prepare_score_distribution(scores)
        
        # Generate executive summary using LLM
        executive_summary = await self._generate_executive_summary(
            idea=idea,
            overall_score=overall_score,
            strengths=strengths,
            weaknesses=weaknesses,
            scores=scores
        )
        
        # Build detailed analysis
        detailed_analysis = self._build_detailed_analysis(scores)
        
        # Generate next steps
        next_steps = self._generate_next_steps(overall_score, weaknesses, scores)
        
        # Create report
        report = ValidationReport(
            validation_id=validation_id,
            idea_id=idea.id,
            idea_title=idea.title,
            overall_score=overall_score,
            validation_date=datetime.utcnow(),
            strengths=strengths,
            weaknesses=weaknesses,
            critical_recommendations=critical_recommendations,
            radar_chart_data=radar_chart_data,
            score_distribution=score_distribution,
            executive_summary=executive_summary,
            detailed_analysis=detailed_analysis,
            next_steps=next_steps
        )
        
        # Add individual scores to report
        if "problem_clarity" in scores:
            report.problem_clarity = scores["problem_clarity"]
        if "market_demand" in scores:
            report.market_demand = scores["market_demand"]
        if "solution_fit" in scores:
            report.solution_fit = scores["solution_fit"]
        if "differentiation" in scores:
            report.differentiation = scores["differentiation"]
        if "technical_feasibility" in scores:
            report.technical_feasibility = scores["technical_feasibility"]
        if "market_size" in scores:
            report.market_size = scores["market_size"]
        if "monetization_potential" in scores:
            report.monetization_potential = scores["monetization_potential"]
        if "risk_level" in scores:
            report.risk_level = scores["risk_level"]
        if "user_validation_evidence" in scores:
            report.user_validation_evidence = scores["user_validation_evidence"]
        
        logger.info(f"Report generated successfully for validation {validation_id}")
        return report
    
    def _calculate_overall_score(self, scores: Dict[str, Score]) -> float:
        """
        Calculate overall validation score as average of all metrics
        
        Args:
            scores: Dictionary of metric scores
            
        Returns:
            Overall score (1-5) rounded to 2 decimal places
        """
        if not scores:
            return 1.0
        
        total = sum(score.value for score in scores.values())
        overall = total / len(scores)
        
        return round(overall, 2)
    
    def _identify_strengths(self, scores: Dict[str, Score]) -> List[str]:
        """
        Identify strengths (metrics with scores >= 4)
        
        Args:
            scores: Dictionary of metric scores
            
        Returns:
            List of strength metric names (formatted for display)
        """
        strengths = []
        
        for metric, score in scores.items():
            if score.value >= 4:
                # Format metric name for display
                formatted_name = self._format_metric_name(metric)
                strengths.append(formatted_name)
        
        # Sort by score (highest first)
        strengths.sort(
            key=lambda m: scores[self._unformat_metric_name(m, scores)].value,
            reverse=True
        )
        
        return strengths
    
    def _identify_weaknesses(self, scores: Dict[str, Score]) -> List[str]:
        """
        Identify weaknesses (metrics with scores <= 2)
        
        Args:
            scores: Dictionary of metric scores
            
        Returns:
            List of weakness metric names (formatted for display)
        """
        weaknesses = []
        
        for metric, score in scores.items():
            if score.value <= 2:
                # Format metric name for display
                formatted_name = self._format_metric_name(metric)
                weaknesses.append(formatted_name)
        
        # Sort by score (lowest first)
        weaknesses.sort(
            key=lambda m: scores[self._unformat_metric_name(m, scores)].value
        )
        
        return weaknesses
    
    def _aggregate_recommendations(
        self,
        scores: Dict[str, Score],
        weaknesses: List[str],
        max_recommendations: int = 5
    ) -> List[str]:
        """
        Aggregate and prioritize recommendations from all scorers
        
        Prioritizes recommendations from weakest areas first
        
        Args:
            scores: Dictionary of metric scores
            weaknesses: List of weakness areas
            max_recommendations: Maximum number of recommendations to return
            
        Returns:
            List of prioritized recommendations
        """
        all_recommendations = []
        seen_recommendations = set()
        
        # First, collect recommendations from weakness areas
        weakness_metrics = [self._unformat_metric_name(w, scores) for w in weaknesses]
        
        for metric in weakness_metrics:
            if metric in scores:
                score = scores[metric]
                for recommendation in score.recommendations:
                    # Add metric context to recommendation
                    formatted_metric = self._format_metric_name(metric)
                    contextualized = f"[{formatted_metric}] {recommendation}"
                    
                    # Avoid duplicates
                    if contextualized not in seen_recommendations:
                        all_recommendations.append(contextualized)
                        seen_recommendations.add(contextualized)
        
        # Then, collect recommendations from other areas (sorted by score)
        other_metrics = [m for m in scores.keys() if m not in weakness_metrics]
        sorted_other = sorted(other_metrics, key=lambda m: scores[m].value)
        
        for metric in sorted_other:
            score = scores[metric]
            for recommendation in score.recommendations:
                formatted_metric = self._format_metric_name(metric)
                contextualized = f"[{formatted_metric}] {recommendation}"
                
                if contextualized not in seen_recommendations:
                    all_recommendations.append(contextualized)
                    seen_recommendations.add(contextualized)
        
        return all_recommendations[:max_recommendations]
    
    def _prepare_radar_chart_data(self, scores: Dict[str, Score]) -> Dict[str, float]:
        """
        Prepare data structure for radar chart visualization
        
        Args:
            scores: Dictionary of metric scores
            
        Returns:
            Dictionary mapping formatted metric names to score values
        """
        radar_data = {}
        
        for metric, score in scores.items():
            formatted_name = self._format_metric_name(metric)
            radar_data[formatted_name] = float(score.value)
        
        return radar_data
    
    def _prepare_score_distribution(self, scores: Dict[str, Score]) -> Dict[str, int]:
        """
        Prepare score distribution data for visualization
        
        Shows how many metrics fall into each score range
        
        Args:
            scores: Dictionary of metric scores
            
        Returns:
            Dictionary mapping score ranges to counts
        """
        distribution = {
            "1": 0,  # Critical (1)
            "2": 0,  # Weak (2)
            "3": 0,  # Moderate (3)
            "4": 0,  # Strong (4)
            "5": 0   # Excellent (5)
        }
        
        for score in scores.values():
            distribution[str(score.value)] += 1
        
        return distribution
    
    async def _generate_executive_summary(
        self,
        idea: IdeaResponse,
        overall_score: float,
        strengths: List[str],
        weaknesses: List[str],
        scores: Dict[str, Score]
    ) -> str:
        """
        Generate executive summary using LLM
        
        Args:
            idea: The idea being validated
            overall_score: Overall validation score
            strengths: List of strength areas
            weaknesses: List of weakness areas
            scores: All metric scores
            
        Returns:
            Executive summary text
        """
        # Build prompt for LLM
        prompt = self._build_executive_summary_prompt(
            idea, overall_score, strengths, weaknesses, scores
        )
        
        try:
            # Call LLM
            summary = await self.llm_service.call_llm(
                prompt=prompt,
                response_format="text",
                temperature=0.7,
                max_tokens=500
            )
            
            return summary.strip()
            
        except Exception as e:
            logger.error(f"Failed to generate executive summary: {str(e)}")
            
            # Fallback to template-based summary
            return self._generate_fallback_summary(
                idea, overall_score, strengths, weaknesses
            )
    
    def _build_executive_summary_prompt(
        self,
        idea: IdeaResponse,
        overall_score: float,
        strengths: List[str],
        weaknesses: List[str],
        scores: Dict[str, Score]
    ) -> str:
        """
        Build prompt for executive summary generation
        
        Args:
            idea: The idea being validated
            overall_score: Overall validation score
            strengths: List of strength areas
            weaknesses: List of weakness areas
            scores: All metric scores
            
        Returns:
            Formatted prompt string
        """
        # Format scores for prompt
        scores_text = "\n".join([
            f"- {self._format_metric_name(metric)}: {score.value}/5"
            for metric, score in scores.items()
        ])
        
        strengths_text = ", ".join(strengths) if strengths else "None identified"
        weaknesses_text = ", ".join(weaknesses) if weaknesses else "None identified"
        
        prompt = f"""Generate a concise executive summary for this startup idea validation.

Idea Title: {idea.title}
Problem: {idea.problem_statement[:200]}...
Solution: {idea.solution_description[:200]}...
Target Market: {idea.target_market}

Overall Validation Score: {overall_score}/5

Individual Scores:
{scores_text}

Key Strengths: {strengths_text}
Key Weaknesses: {weaknesses_text}

Write a 3-4 paragraph executive summary that:
1. Briefly describes the idea and its validation score
2. Highlights the strongest aspects and opportunities
3. Identifies the main challenges and risks
4. Provides a balanced recommendation on whether to pursue this idea

Keep the tone professional and objective. Focus on actionable insights."""

        return prompt
    
    def _generate_fallback_summary(
        self,
        idea: IdeaResponse,
        overall_score: float,
        strengths: List[str],
        weaknesses: List[str]
    ) -> str:
        """
        Generate template-based summary when LLM is unavailable
        
        Args:
            idea: The idea being validated
            overall_score: Overall validation score
            strengths: List of strength areas
            weaknesses: List of weakness areas
            
        Returns:
            Template-based summary
        """
        # Determine overall assessment
        if overall_score >= 4.0:
            assessment = "strong validation"
            recommendation = "This idea shows strong potential and is recommended for further development."
        elif overall_score >= 3.0:
            assessment = "moderate validation"
            recommendation = "This idea has potential but requires improvements in key areas before proceeding."
        else:
            assessment = "weak validation"
            recommendation = "This idea faces significant challenges and requires substantial refinement before pursuing."
        
        # Build summary
        summary_parts = [
            f"The idea '{idea.title}' received an overall validation score of {overall_score}/5, indicating {assessment}."
        ]
        
        if strengths:
            summary_parts.append(
                f"Key strengths include: {', '.join(strengths)}. "
                "These areas provide a solid foundation for the idea."
            )
        
        if weaknesses:
            summary_parts.append(
                f"Areas requiring attention: {', '.join(weaknesses)}. "
                "Addressing these weaknesses will be critical for success."
            )
        
        summary_parts.append(recommendation)
        
        return " ".join(summary_parts)
    
    def _build_detailed_analysis(self, scores: Dict[str, Score]) -> Dict[str, Any]:
        """
        Build detailed analysis section with all metric details
        
        Args:
            scores: Dictionary of metric scores
            
        Returns:
            Dictionary containing detailed analysis for each metric
        """
        detailed_analysis = {}
        
        for metric, score in scores.items():
            formatted_name = self._format_metric_name(metric)
            
            detailed_analysis[formatted_name] = {
                "score": score.value,
                "justifications": score.justifications,
                "recommendations": score.recommendations,
                "evidence": score.evidence,
                "metadata": score.metadata
            }
        
        return detailed_analysis
    
    def _generate_next_steps(
        self,
        overall_score: float,
        weaknesses: List[str],
        scores: Dict[str, Score]
    ) -> List[str]:
        """
        Generate prioritized next steps based on validation results
        
        Args:
            overall_score: Overall validation score
            weaknesses: List of weakness areas
            scores: All metric scores
            
        Returns:
            List of next steps
        """
        next_steps = []
        
        # High-level next steps based on overall score
        if overall_score >= 4.0:
            next_steps.append("Proceed with MVP development and user testing")
            next_steps.append("Develop detailed business plan and financial projections")
        elif overall_score >= 3.0:
            next_steps.append("Address key weaknesses before proceeding to development")
            next_steps.append("Conduct additional market research and user validation")
        else:
            next_steps.append("Significantly refine the idea based on validation feedback")
            next_steps.append("Consider pivoting or exploring alternative approaches")
        
        # Add specific next steps for weaknesses
        weakness_metrics = [self._unformat_metric_name(w, scores) for w in weaknesses]
        
        for metric in weakness_metrics[:3]:  # Top 3 weaknesses
            if metric in scores:
                score = scores[metric]
                # Add first recommendation as next step
                if score.recommendations:
                    next_steps.append(score.recommendations[0])
        
        # Add general next steps
        next_steps.append("Re-run validation after implementing improvements")
        next_steps.append("Share results with advisors and potential stakeholders")
        
        return next_steps[:6]  # Limit to 6 next steps
    
    @staticmethod
    def _format_metric_name(metric: str) -> str:
        """
        Format metric name for display
        
        Args:
            metric: Raw metric name (e.g., "problem_clarity")
            
        Returns:
            Formatted name (e.g., "Problem Clarity")
        """
        return metric.replace("_", " ").title()
    
    @staticmethod
    def _unformat_metric_name(formatted: str, scores: Dict[str, Score]) -> str:
        """
        Convert formatted metric name back to raw name
        
        Args:
            formatted: Formatted metric name
            scores: Dictionary of scores to search in
            
        Returns:
            Raw metric name
        """
        # Try to find matching metric in scores
        formatted_lower = formatted.lower().replace(" ", "_")
        
        for metric in scores.keys():
            if metric == formatted_lower:
                return metric
        
        # Fallback: return as-is
        return formatted_lower

    async def export_report_json(self, report: ValidationReport) -> Dict[str, Any]:
        """
        Export validation report as JSON
        
        Args:
            report: ValidationReport to export
            
        Returns:
            Dictionary containing all report data in JSON-serializable format
        """
        logger.info(f"Exporting report {report.validation_id} to JSON")
        
        # Build JSON export
        export_data = {
            "validation_id": report.validation_id,
            "idea_id": report.idea_id,
            "idea_title": report.idea_title,
            "overall_score": report.overall_score,
            "validation_date": report.validation_date.isoformat() if report.validation_date else None,
            "executive_summary": report.executive_summary,
            "strengths": report.strengths,
            "weaknesses": report.weaknesses,
            "critical_recommendations": report.critical_recommendations,
            "next_steps": report.next_steps,
            "scores": {},
            "radar_chart_data": report.radar_chart_data,
            "score_distribution": report.score_distribution,
            "detailed_analysis": report.detailed_analysis
        }
        
        # Add individual scores
        score_fields = [
            "problem_clarity",
            "market_demand",
            "solution_fit",
            "differentiation",
            "technical_feasibility",
            "market_size",
            "monetization_potential",
            "risk_level",
            "user_validation_evidence"
        ]
        
        for field in score_fields:
            score = getattr(report, field, None)
            if score:
                export_data["scores"][field] = {
                    "value": score.value,
                    "justifications": score.justifications,
                    "recommendations": score.recommendations,
                    "evidence": score.evidence,
                    "metadata": score.metadata
                }
        
        logger.info(f"Report {report.validation_id} exported successfully")
        return export_data
    
    async def export_report_pdf(self, report: ValidationReport) -> bytes:
        """
        Export validation report as PDF
        
        Args:
            report: ValidationReport to export
            
        Returns:
            PDF file as bytes
        """
        logger.info(f"Exporting report {report.validation_id} to PDF")
        
        # This would use a PDF generation library like ReportLab or WeasyPrint
        # For now, return a placeholder
        logger.warning("PDF export not yet implemented, returning placeholder")
        
        return b"PDF export not yet implemented"
