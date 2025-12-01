"""
Validation Service
Handles validation lifecycle, database operations, and status tracking
"""

import uuid
from typing import Optional, Dict, Any, List
from datetime import datetime
from fastapi import BackgroundTasks
from app.db.models.validation_result_model import (
    ValidationResultResponse,
    ValidationConfig,
    ValidationStatus,
    Score,
    ValidationHistoryItem
)
from app.db.models.idea_model import IdeaResponse
from app.services.module2_validation.validation_orchestrator import ValidationOrchestrator
from app.services.module2_validation.idea_management_service import IdeaManagementService
from app.db.database import db, validation_results_collection, ideas_collection
from app.core.logging import logger


class ValidationService:
    """Service for managing validation lifecycle and persistence"""
    
    def __init__(self):
        self.orchestrator = ValidationOrchestrator()
        self.validations_collection = validation_results_collection
    
    async def start_validation(
        self,
        idea_id: str,
        user_id: str,
        config: ValidationConfig,
        background_tasks: BackgroundTasks
    ) -> ValidationResultResponse:
        """
        Start a new validation
        
        Creates a validation record with IN_PROGRESS status and queues
        the validation execution as a background task.
        
        Args:
            idea_id: ID of the idea to validate
            user_id: ID of the user requesting validation
            config: Validation configuration
            background_tasks: FastAPI background tasks
            
        Returns:
            ValidationResultResponse with IN_PROGRESS status
        """
        # Generate validation ID
        validation_id = str(uuid.uuid4())
        
        # Verify idea exists and belongs to user
        idea = IdeaManagementService.get_idea(user_id, idea_id)
        if not idea:
            raise ValueError(f"Idea {idea_id} not found or does not belong to user")
        
        # Create validation record with IN_PROGRESS status (Subtask 13.3)
        validation_record = {
            "validation_id": validation_id,
            "idea_id": idea_id,
            "user_id": user_id,
            "status": ValidationStatus.IN_PROGRESS.value,
            "overall_score": None,
            "individual_scores": None,
            "report_data": None,
            "config": config.dict(),
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "completed_at": None,
            "error_message": None
        }
        
        # Insert into database (pymongo is synchronous, no await needed)
        self.validations_collection.insert_one(validation_record)
        
        logger.info(f"Created validation {validation_id} for idea {idea_id}")
        
        # Queue background task to execute validation
        background_tasks.add_task(
            self._execute_validation_background,
            validation_id,
            idea,
            config
        )
        
        return ValidationResultResponse(
            validation_id=validation_id,
            idea_id=idea_id,
            user_id=user_id,
            status=ValidationStatus.IN_PROGRESS,
            overall_score=None,
            individual_scores=None,
            report_data=None,
            created_at=validation_record["created_at"],
            completed_at=None,
            error_message=None
        )
    
    async def _execute_validation_background(
        self,
        validation_id: str,
        idea: IdeaResponse,
        config: ValidationConfig
    ):
        """
        Execute validation in background
        
        This method runs the complete validation pipeline and updates
        the database with results or errors.
        
        Args:
            validation_id: Validation ID
            idea: Idea to validate
            config: Validation configuration
        """
        try:
            logger.info(f"Starting background validation {validation_id}")
            
            # Execute validation using orchestrator
            result = await self.orchestrator.validate_idea_with_status_tracking(
                idea=idea,
                validation_id=validation_id,
                config=config
            )
            
            # Update database with COMPLETED status (Subtask 13.3)
            await self._update_validation_completed(
                validation_id=validation_id,
                result=result
            )
            
            logger.info(f"Completed validation {validation_id} successfully")
            
        except Exception as e:
            logger.error(f"Validation {validation_id} failed: {str(e)}")
            
            # Update database with FAILED status (Subtask 13.3)
            await self._update_validation_failed(
                validation_id=validation_id,
                error_message=str(e)
            )
    
    async def _update_validation_completed(
        self,
        validation_id: str,
        result: ValidationResultResponse
    ):
        """
        Update validation record with completed results
        
        Subtask 13.3: Update to COMPLETED when finished, store validation results
        
        Args:
            validation_id: Validation ID
            result: Validation result
        """
        # Convert Score objects to dicts for MongoDB storage
        individual_scores_dict = {}
        if result.individual_scores:
            for metric, score in result.individual_scores.items():
                individual_scores_dict[metric] = score.dict()
        
        update_data = {
            "status": ValidationStatus.COMPLETED.value,
            "overall_score": result.overall_score,
            "individual_scores": individual_scores_dict,
            "report_data": result.report_data,
            "updated_at": datetime.utcnow(),
            "completed_at": datetime.utcnow(),
            "error_message": None
        }
        
        self.validations_collection.update_one(
            {"validation_id": validation_id},
            {"$set": update_data}
        )
        
        # Update the idea with latest validation info
        ideas_collection.update_one(
            {"id": result.idea_id},
            {
                "$set": {
                    "latest_validation_id": validation_id,
                    "updated_at": datetime.utcnow()
                },
                "$inc": {"validation_count": 1}
            }
        )
        
        logger.info(f"Updated validation {validation_id} to COMPLETED and updated idea {result.idea_id}")
    
    async def _update_validation_failed(
        self,
        validation_id: str,
        error_message: str
    ):
        """
        Update validation record with failure status
        
        Subtask 13.3: Update to FAILED on errors
        
        Args:
            validation_id: Validation ID
            error_message: Error message
        """
        update_data = {
            "status": ValidationStatus.FAILED.value,
            "updated_at": datetime.utcnow(),
            "completed_at": datetime.utcnow(),
            "error_message": error_message
        }
        
        self.validations_collection.update_one(
            {"validation_id": validation_id},
            {"$set": update_data}
        )
        
        logger.info(f"Updated validation {validation_id} to FAILED")
    
    async def get_validation_result(
        self,
        validation_id: str,
        user_id: str
    ) -> Optional[ValidationResultResponse]:
        """
        Get validation result by ID
        
        Args:
            validation_id: Validation ID
            user_id: User ID (for authorization)
            
        Returns:
            ValidationResultResponse or None if not found
        """
        # Query database
        validation_doc = self.validations_collection.find_one({
            "validation_id": validation_id,
            "user_id": user_id
        })
        
        if not validation_doc:
            return None
        
        # Convert individual_scores back to Score objects
        individual_scores = None
        if validation_doc.get("individual_scores"):
            individual_scores = {}
            for metric, score_dict in validation_doc["individual_scores"].items():
                individual_scores[metric] = Score(**score_dict)
        
        return ValidationResultResponse(
            validation_id=validation_doc["validation_id"],
            idea_id=validation_doc["idea_id"],
            user_id=validation_doc["user_id"],
            status=ValidationStatus(validation_doc["status"]),
            overall_score=validation_doc.get("overall_score"),
            individual_scores=individual_scores,
            report_data=validation_doc.get("report_data"),
            created_at=validation_doc["created_at"],
            completed_at=validation_doc.get("completed_at"),
            error_message=validation_doc.get("error_message")
        )
    
    async def get_validation_status(
        self,
        validation_id: str,
        user_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get lightweight validation status
        
        Args:
            validation_id: Validation ID
            user_id: User ID (for authorization)
            
        Returns:
            Dictionary with status information or None if not found
        """
        # Query database (only fetch status fields)
        validation_doc = self.validations_collection.find_one(
            {"validation_id": validation_id, "user_id": user_id},
            {"status": 1, "created_at": 1, "completed_at": 1, "error_message": 1}
        )
        
        if not validation_doc:
            return None
        
        status_info = {
            "validation_id": validation_id,
            "status": validation_doc["status"],
            "created_at": validation_doc["created_at"].isoformat(),
        }
        
        if validation_doc.get("completed_at"):
            status_info["completed_at"] = validation_doc["completed_at"].isoformat()
            
            # Calculate duration
            duration = (validation_doc["completed_at"] - validation_doc["created_at"]).total_seconds()
            status_info["duration_seconds"] = duration
        
        if validation_doc.get("error_message"):
            status_info["error_message"] = validation_doc["error_message"]
        
        # Add progress estimate for in-progress validations
        if validation_doc["status"] == ValidationStatus.IN_PROGRESS:
            elapsed = (datetime.utcnow() - validation_doc["created_at"]).total_seconds()
            # Estimate: validation typically takes 30-60 seconds
            estimated_total = 45
            progress_percentage = min(95, int((elapsed / estimated_total) * 100))
            status_info["progress_percentage"] = progress_percentage
            status_info["estimated_completion_seconds"] = max(0, estimated_total - elapsed)
        
        return status_info
    
    async def get_validation_history(
        self,
        idea_id: str,
        user_id: str
    ) -> List[ValidationHistoryItem]:
        """
        Get validation history for an idea
        
        Args:
            idea_id: Idea ID
            user_id: User ID (for authorization)
            
        Returns:
            List of validation history items, ordered by date (newest first)
        """
        # Query database
        cursor = self.validations_collection.find(
            {"idea_id": idea_id, "user_id": user_id},
            {"validation_id": 1, "idea_id": 1, "overall_score": 1, "status": 1, "created_at": 1, "completed_at": 1}
        ).sort("created_at", -1)  # Newest first
        
        history = []
        for doc in cursor:
            history.append(ValidationHistoryItem(
                validation_id=doc["validation_id"],
                idea_id=doc["idea_id"],
                overall_score=doc.get("overall_score", 0.0),
                status=ValidationStatus(doc["status"]),
                created_at=doc["created_at"],
                completed_at=doc.get("completed_at")
            ))
        
        return history
    
    async def compare_validations(
        self,
        validation_ids: List[str],
        user_id: str
    ) -> Dict[str, Any]:
        """
        Compare multiple validation results side-by-side
        
        Subtasks 15.1, 15.3, 15.5
        Requirements: 12.1, 12.2, 12.3, 12.4
        
        Args:
            validation_ids: List of validation IDs to compare
            user_id: User ID (for authorization)
            
        Returns:
            Dictionary containing comparison data with:
            - ideas: List of idea summaries
            - metric_comparison: Side-by-side metric scores
            - winners: Winner for each metric
            - overall_recommendation: Recommendation on which idea to pursue
        """
        import uuid
        from app.services.module2_validation.idea_management_service import IdeaManagementService
        
        # Fetch all validations
        validations = []
        for validation_id in validation_ids:
            validation = await self.get_validation_result(validation_id, user_id)
            if not validation:
                raise ValueError(f"Validation {validation_id} not found or access denied")
            
            # Only include completed validations
            if validation.status != ValidationStatus.COMPLETED:
                raise ValueError(f"Validation {validation_id} is not completed (status: {validation.status})")
            
            validations.append(validation)
        
        # Fetch idea details for each validation
        ideas_data = []
        for validation in validations:
            idea = IdeaManagementService.get_idea(user_id, validation.idea_id)
            if idea:
                ideas_data.append({
                    "idea_id": idea.id,
                    "validation_id": validation.validation_id,
                    "title": idea.title,
                    "description": idea.description[:200] + "..." if len(idea.description) > 200 else idea.description,
                    "overall_score": validation.overall_score
                })
        
        # Build metric comparison (Requirement 12.2)
        # Core metrics for comparison
        metric_names = [
            "problem_clarity",
            "market_demand",
            "solution_fit",
            "differentiation"
        ]
        
        metric_comparison = {}
        for metric in metric_names:
            metric_comparison[metric] = []
            for validation in validations:
                if validation.individual_scores and metric in validation.individual_scores:
                    score = validation.individual_scores[metric].value
                else:
                    score = None
                metric_comparison[metric].append({
                    "validation_id": validation.validation_id,
                    "idea_id": validation.idea_id,
                    "score": score
                })
        
        # Identify winners for each metric (Subtask 15.3, Requirement 12.3)
        winners = {}
        for metric, scores_list in metric_comparison.items():
            # Find the highest score for this metric
            max_score = -1
            winner_validation_id = None
            winner_idea_id = None
            
            for score_data in scores_list:
                if score_data["score"] is not None and score_data["score"] > max_score:
                    max_score = score_data["score"]
                    winner_validation_id = score_data["validation_id"]
                    winner_idea_id = score_data["idea_id"]
            
            if winner_validation_id:
                winners[metric] = {
                    "validation_id": winner_validation_id,
                    "idea_id": winner_idea_id,
                    "score": max_score
                }
        
        # Determine overall recommendation (Subtask 15.5, Requirement 12.4)
        # Find idea with highest overall score
        best_validation = max(validations, key=lambda v: v.overall_score or 0)
        best_idea = next((idea for idea in ideas_data if idea["idea_id"] == best_validation.idea_id), None)
        
        # Count how many metrics each idea wins
        win_counts = {}
        for validation in validations:
            win_counts[validation.idea_id] = 0
        
        for winner_data in winners.values():
            win_counts[winner_data["idea_id"]] += 1
        
        # Build recommendation
        if best_idea:
            wins = win_counts.get(best_idea["idea_id"], 0)
            total_metrics = len([w for w in winners.values() if w is not None])
            
            overall_recommendation = {
                "recommended_idea_id": best_idea["idea_id"],
                "recommended_validation_id": best_validation.validation_id,
                "idea_title": best_idea["title"],
                "overall_score": best_validation.overall_score,
                "metrics_won": wins,
                "total_metrics": total_metrics,
                "justification": self._generate_recommendation_justification(
                    best_idea,
                    best_validation,
                    wins,
                    total_metrics,
                    validations
                )
            }
        else:
            overall_recommendation = None
        
        # Build comparison report
        comparison_id = str(uuid.uuid4())
        comparison = {
            "comparison_id": comparison_id,
            "validation_ids": validation_ids,
            "ideas": ideas_data,
            "metric_comparison": metric_comparison,
            "winners": winners,
            "overall_recommendation": overall_recommendation,
            "created_at": datetime.utcnow().isoformat()
        }
        
        return comparison
    
    def _generate_recommendation_justification(
        self,
        best_idea: Dict[str, Any],
        best_validation: ValidationResultResponse,
        wins: int,
        total_metrics: int,
        all_validations: List[ValidationResultResponse]
    ) -> str:
        """
        Generate justification for overall recommendation
        
        Args:
            best_idea: Best idea data
            best_validation: Best validation result
            wins: Number of metrics won
            total_metrics: Total number of metrics
            all_validations: All validations being compared
            
        Returns:
            Justification string
        """
        justification_parts = []
        
        # Overall score comparison
        overall_score = best_validation.overall_score or 0
        justification_parts.append(
            f"'{best_idea['title']}' has the highest overall validation score of {overall_score:.2f}/5.0"
        )
        
        # Metric wins
        if wins > 0:
            win_percentage = (wins / total_metrics * 100) if total_metrics > 0 else 0
            justification_parts.append(
                f"It wins in {wins} out of {total_metrics} metrics ({win_percentage:.0f}%)"
            )
        
        # Score gap analysis
        other_scores = [v.overall_score or 0 for v in all_validations if v.validation_id != best_validation.validation_id]
        if other_scores:
            second_best = max(other_scores)
            gap = overall_score - second_best
            if gap > 0.5:
                justification_parts.append(
                    f"It has a significant lead of {gap:.2f} points over the next best idea"
                )
            elif gap > 0:
                justification_parts.append(
                    f"It has a moderate lead of {gap:.2f} points over the next best idea"
                )
        
        # Strength analysis
        if best_validation.individual_scores:
            strong_metrics = [
                metric for metric, score in best_validation.individual_scores.items()
                if score.value >= 4
            ]
            if strong_metrics:
                justification_parts.append(
                    f"Strong performance in: {', '.join(strong_metrics[:3])}"
                )
        
        return ". ".join(justification_parts) + "."
    
    async def compare_validation_versions(
        self,
        validation_id_1: str,
        validation_id_2: str,
        user_id: str
    ) -> Dict[str, Any]:
        """
        Compare two validation versions of the same idea
        
        Subtask 15.9
        Requirements: 13.3, 13.4
        
        Args:
            validation_id_1: First validation ID
            validation_id_2: Second validation ID
            user_id: User ID (for authorization)
            
        Returns:
            Dictionary containing version comparison with:
            - score_deltas: Delta for each metric
            - improved_metrics: List of metrics that improved
            - declined_metrics: List of metrics that declined
            - unchanged_metrics: List of metrics that stayed the same
            - overall_score_delta: Overall score change
        """
        # Fetch both validations
        validation_1 = await self.get_validation_result(validation_id_1, user_id)
        validation_2 = await self.get_validation_result(validation_id_2, user_id)
        
        if not validation_1:
            raise ValueError(f"Validation {validation_id_1} not found or access denied")
        if not validation_2:
            raise ValueError(f"Validation {validation_id_2} not found or access denied")
        
        # Verify both validations are for the same idea
        if validation_1.idea_id != validation_2.idea_id:
            raise ValueError(
                f"Validations are for different ideas: {validation_1.idea_id} vs {validation_2.idea_id}"
            )
        
        # Verify both validations are completed
        if validation_1.status != ValidationStatus.COMPLETED:
            raise ValueError(f"Validation {validation_id_1} is not completed")
        if validation_2.status != ValidationStatus.COMPLETED:
            raise ValueError(f"Validation {validation_id_2} is not completed")
        
        # Calculate score deltas for core metrics
        metric_names = [
            "problem_clarity",
            "market_demand",
            "solution_fit",
            "differentiation"
        ]
        
        score_deltas = {}
        improved_metrics = []
        declined_metrics = []
        unchanged_metrics = []
        
        for metric in metric_names:
            score_1 = None
            score_2 = None
            
            if validation_1.individual_scores and metric in validation_1.individual_scores:
                score_1 = validation_1.individual_scores[metric].value
            
            if validation_2.individual_scores and metric in validation_2.individual_scores:
                score_2 = validation_2.individual_scores[metric].value
            
            # Calculate delta
            if score_1 is not None and score_2 is not None:
                delta = score_2 - score_1
                score_deltas[metric] = {
                    "score_1": score_1,
                    "score_2": score_2,
                    "delta": delta,
                    "delta_percentage": (delta / score_1 * 100) if score_1 > 0 else 0
                }
                
                # Categorize change
                if delta > 0:
                    improved_metrics.append({
                        "metric": metric,
                        "delta": delta,
                        "from": score_1,
                        "to": score_2
                    })
                elif delta < 0:
                    declined_metrics.append({
                        "metric": metric,
                        "delta": delta,
                        "from": score_1,
                        "to": score_2
                    })
                else:
                    unchanged_metrics.append({
                        "metric": metric,
                        "score": score_1
                    })
            elif score_1 is None and score_2 is not None:
                # New metric in version 2
                score_deltas[metric] = {
                    "score_1": None,
                    "score_2": score_2,
                    "delta": None,
                    "delta_percentage": None,
                    "note": "New metric in version 2"
                }
            elif score_1 is not None and score_2 is None:
                # Metric removed in version 2
                score_deltas[metric] = {
                    "score_1": score_1,
                    "score_2": None,
                    "delta": None,
                    "delta_percentage": None,
                    "note": "Metric not present in version 2"
                }
        
        # Calculate overall score delta
        overall_score_1 = validation_1.overall_score or 0
        overall_score_2 = validation_2.overall_score or 0
        overall_score_delta = overall_score_2 - overall_score_1
        
        # Sort metrics by delta magnitude
        improved_metrics.sort(key=lambda x: x["delta"], reverse=True)
        declined_metrics.sort(key=lambda x: x["delta"])
        
        # Generate summary
        summary = self._generate_version_comparison_summary(
            improved_metrics,
            declined_metrics,
            unchanged_metrics,
            overall_score_delta
        )
        
        return {
            "idea_id": validation_1.idea_id,
            "validation_1_id": validation_id_1,
            "validation_2_id": validation_id_2,
            "validation_1_date": validation_1.created_at.isoformat(),
            "validation_2_date": validation_2.created_at.isoformat(),
            "overall_score_1": overall_score_1,
            "overall_score_2": overall_score_2,
            "overall_score_delta": overall_score_delta,
            "overall_score_delta_percentage": (overall_score_delta / overall_score_1 * 100) if overall_score_1 > 0 else 0,
            "score_deltas": score_deltas,
            "improved_metrics": improved_metrics,
            "declined_metrics": declined_metrics,
            "unchanged_metrics": unchanged_metrics,
            "summary": summary
        }
    
    def _generate_version_comparison_summary(
        self,
        improved_metrics: List[Dict[str, Any]],
        declined_metrics: List[Dict[str, Any]],
        unchanged_metrics: List[Dict[str, Any]],
        overall_score_delta: float
    ) -> str:
        """
        Generate summary text for version comparison
        
        Args:
            improved_metrics: List of improved metrics
            declined_metrics: List of declined metrics
            unchanged_metrics: List of unchanged metrics
            overall_score_delta: Overall score change
            
        Returns:
            Summary string
        """
        summary_parts = []
        
        # Overall trend
        if overall_score_delta > 0.5:
            summary_parts.append(f"Significant improvement: overall score increased by {overall_score_delta:.2f} points")
        elif overall_score_delta > 0:
            summary_parts.append(f"Moderate improvement: overall score increased by {overall_score_delta:.2f} points")
        elif overall_score_delta < -0.5:
            summary_parts.append(f"Significant decline: overall score decreased by {abs(overall_score_delta):.2f} points")
        elif overall_score_delta < 0:
            summary_parts.append(f"Slight decline: overall score decreased by {abs(overall_score_delta):.2f} points")
        else:
            summary_parts.append("Overall score remained unchanged")
        
        # Improved metrics
        if improved_metrics:
            top_improvements = improved_metrics[:3]
            improvement_names = [m["metric"] for m in top_improvements]
            summary_parts.append(
                f"{len(improved_metrics)} metric(s) improved, notably: {', '.join(improvement_names)}"
            )
        
        # Declined metrics
        if declined_metrics:
            top_declines = declined_metrics[:3]
            decline_names = [m["metric"] for m in top_declines]
            summary_parts.append(
                f"{len(declined_metrics)} metric(s) declined: {', '.join(decline_names)}"
            )
        
        # Unchanged metrics
        if unchanged_metrics:
            summary_parts.append(f"{len(unchanged_metrics)} metric(s) remained stable")
        
        return ". ".join(summary_parts) + "."
    
    async def export_validation_json(
        self,
        validation_id: str,
        user_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Export validation result as complete JSON
        
        Subtask 16.1
        Requirements: 15.2, 15.3
        
        Returns complete validation data including:
        - All scores with justifications and recommendations
        - Report data with executive summary
        - Idea information
        - Metadata (validation date, version, linked pain points)
        
        Args:
            validation_id: Validation ID
            user_id: User ID (for authorization)
            
        Returns:
            Dictionary containing complete validation export or None if not found
        """
        from app.services.module2_validation.idea_management_service import IdeaManagementService
        
        # Get validation result
        validation = await self.get_validation_result(validation_id, user_id)
        
        if not validation:
            return None
        
        # Get idea details
        idea = IdeaManagementService.get_idea(user_id, validation.idea_id)
        
        if not idea:
            return None
        
        # Build comprehensive export
        export_data = {
            # Metadata
            "export_version": "1.0",
            "export_date": datetime.utcnow().isoformat(),
            "validation_id": validation.validation_id,
            
            # Validation information
            "validation": {
                "validation_id": validation.validation_id,
                "status": validation.status.value,
                "created_at": validation.created_at.isoformat(),
                "completed_at": validation.completed_at.isoformat() if validation.completed_at else None,
                "overall_score": validation.overall_score,
                "error_message": validation.error_message
            },
            
            # Idea information
            "idea": {
                "idea_id": idea.id,
                "title": idea.title,
                "description": idea.description,
                "problem_statement": idea.problem_statement,
                "solution_description": idea.solution_description,
                "target_market": idea.target_market,
                "business_model": idea.business_model,
                "team_capabilities": idea.team_capabilities,
                "linked_pain_points": idea.linked_pain_points,
                "created_at": idea.created_at.isoformat(),
                "updated_at": idea.updated_at.isoformat()
            },
            
            # Individual scores with full details
            "scores": {},
            
            # Report data
            "report": validation.report_data if validation.report_data else {}
        }
        
        # Convert Score objects to detailed dictionaries
        if validation.individual_scores:
            for metric, score in validation.individual_scores.items():
                export_data["scores"][metric] = {
                    "value": score.value,
                    "justifications": score.justifications,
                    "evidence": score.evidence,
                    "recommendations": score.recommendations,
                    "metadata": score.metadata
                }
        
        # Add pain point information if available
        if idea.linked_pain_points:
            export_data["linked_pain_points_count"] = len(idea.linked_pain_points)
            export_data["linked_pain_point_ids"] = idea.linked_pain_points
        
        # Add validation configuration if available
        validation_doc = self.validations_collection.find_one(
            {"validation_id": validation_id}
        )
        if validation_doc and validation_doc.get("config"):
            export_data["validation_config"] = validation_doc["config"]
        
        return export_data
    
    async def create_share_link(
        self,
        validation_id: str,
        user_id: str,
        privacy_level: str,
        password: Optional[str] = None,
        expires_at: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Create a shareable link for a validation result
        
        Subtask 16.4
        Requirements: 15.5
        
        Args:
            validation_id: Validation ID to share
            user_id: User ID (for authorization)
            privacy_level: Privacy level (public/private/password_protected)
            password: Optional password for password-protected links
            expires_at: Optional expiration date
            
        Returns:
            Dictionary containing share link information
        """
        from app.db.database import db
        import hashlib
        import secrets
        
        # Verify validation exists and belongs to user
        validation = await self.get_validation_result(validation_id, user_id)
        if not validation:
            raise ValueError(f"Validation {validation_id} not found or access denied")
        
        # Verify validation is completed
        if validation.status != ValidationStatus.COMPLETED:
            raise ValueError(f"Cannot share incomplete validation (status: {validation.status})")
        
        # Generate unique share ID
        share_id = secrets.token_urlsafe(16)
        
        # Hash password if provided
        password_hash = None
        if password and privacy_level == "password_protected":
            password_hash = hashlib.sha256(password.encode()).hexdigest()
        
        # Create share record
        share_record = {
            "share_id": share_id,
            "validation_id": validation_id,
            "user_id": user_id,
            "privacy_level": privacy_level,
            "password_hash": password_hash,
            "created_at": datetime.utcnow(),
            "expires_at": expires_at,
            "is_active": True,
            "access_count": 0
        }
        
        # Store in database
        shares_collection = db["validation_shares"]
        shares_collection.insert_one(share_record)
        
        logger.info(f"Created share link {share_id} for validation {validation_id}")
        
        # Generate share URL (in production, this would be the actual domain)
        share_url = f"/shared/validations/{share_id}"
        
        return {
            "share_id": share_id,
            "validation_id": validation_id,
            "share_url": share_url,
            "privacy_level": privacy_level,
            "created_at": share_record["created_at"].isoformat(),
            "expires_at": expires_at.isoformat() if expires_at else None,
            "is_active": True
        }
    
    async def get_shared_validation(
        self,
        share_id: str,
        password: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Get validation result via share link
        
        Subtask 16.4
        Requirements: 15.5
        
        Args:
            share_id: Share ID
            password: Optional password for password-protected links
            
        Returns:
            Validation export data or None if not found/unauthorized
        """
        from app.db.database import db
        import hashlib
        
        # Get share record
        shares_collection = db["validation_shares"]
        share_record = shares_collection.find_one({"share_id": share_id})
        
        if not share_record:
            return None
        
        # Check if share is active
        if not share_record.get("is_active", True):
            raise ValueError("This share link has been deactivated")
        
        # Check expiration
        if share_record.get("expires_at"):
            if datetime.utcnow() > share_record["expires_at"]:
                raise ValueError("This share link has expired")
        
        # Check privacy level
        privacy_level = share_record.get("privacy_level", "public")
        
        if privacy_level == "private":
            raise ValueError("This validation is private and cannot be accessed via share link")
        
        if privacy_level == "password_protected":
            if not password:
                raise ValueError("Password required to access this validation")
            
            # Verify password
            password_hash = hashlib.sha256(password.encode()).hexdigest()
            if password_hash != share_record.get("password_hash"):
                raise ValueError("Incorrect password")
        
        # Increment access count
        shares_collection.update_one(
            {"share_id": share_id},
            {"$inc": {"access_count": 1}}
        )
        
        # Get validation data
        validation_id = share_record["validation_id"]
        user_id = share_record["user_id"]
        
        # Export validation data (without requiring user authentication)
        validation_doc = self.validations_collection.find_one({
            "validation_id": validation_id,
            "user_id": user_id
        })
        
        if not validation_doc:
            return None
        
        # Get idea details
        from app.services.module2_validation.idea_management_service import IdeaManagementService
        idea = IdeaManagementService.get_idea(user_id, validation_doc["idea_id"])
        
        if not idea:
            return None
        
        # Build export data (similar to export_validation_json but without sensitive info)
        export_data = {
            "share_id": share_id,
            "validation_id": validation_id,
            "shared_at": share_record["created_at"].isoformat(),
            "access_count": share_record.get("access_count", 0) + 1,
            
            "validation": {
                "validation_id": validation_id,
                "status": validation_doc["status"],
                "created_at": validation_doc["created_at"].isoformat(),
                "completed_at": validation_doc.get("completed_at").isoformat() if validation_doc.get("completed_at") else None,
                "overall_score": validation_doc.get("overall_score")
            },
            
            "idea": {
                "title": idea.title,
                "description": idea.description,
                "problem_statement": idea.problem_statement,
                "solution_description": idea.solution_description,
                "target_market": idea.target_market,
                "business_model": idea.business_model
                # Note: Exclude sensitive fields like user_id, team_capabilities
            },
            
            "scores": {},
            "report": validation_doc.get("report_data", {})
        }
        
        # Convert scores
        if validation_doc.get("individual_scores"):
            for metric, score_dict in validation_doc["individual_scores"].items():
                export_data["scores"][metric] = score_dict
        
        return export_data
    
    async def revoke_share_link(
        self,
        share_id: str,
        user_id: str
    ) -> bool:
        """
        Revoke a share link
        
        Subtask 16.4
        Requirements: 15.5
        
        Args:
            share_id: Share ID to revoke
            user_id: User ID (for authorization)
            
        Returns:
            True if revoked, False if not found
        """
        from app.db.database import db
        
        shares_collection = db["validation_shares"]
        
        # Update share to inactive
        result = shares_collection.update_one(
            {"share_id": share_id, "user_id": user_id},
            {"$set": {"is_active": False, "revoked_at": datetime.utcnow()}}
        )
        
        if result.modified_count > 0:
            logger.info(f"Revoked share link {share_id}")
            return True
        
        return False
    
    async def list_share_links(
        self,
        validation_id: str,
        user_id: str
    ) -> List[Dict[str, Any]]:
        """
        List all share links for a validation
        
        Subtask 16.4
        Requirements: 15.5
        
        Args:
            validation_id: Validation ID
            user_id: User ID (for authorization)
            
        Returns:
            List of share link information
        """
        from app.db.database import db
        
        # Verify validation belongs to user
        validation = await self.get_validation_result(validation_id, user_id)
        if not validation:
            raise ValueError(f"Validation {validation_id} not found or access denied")
        
        # Get all share links
        shares_collection = db["validation_shares"]
        cursor = shares_collection.find(
            {"validation_id": validation_id, "user_id": user_id}
        ).sort("created_at", -1)
        
        share_links = []
        async for share_doc in cursor:
            share_links.append({
                "share_id": share_doc["share_id"],
                "share_url": f"/shared/validations/{share_doc['share_id']}",
                "privacy_level": share_doc.get("privacy_level", "public"),
                "created_at": share_doc["created_at"].isoformat(),
                "expires_at": share_doc.get("expires_at").isoformat() if share_doc.get("expires_at") else None,
                "is_active": share_doc.get("is_active", True),
                "access_count": share_doc.get("access_count", 0)
            })
        
        return share_links
