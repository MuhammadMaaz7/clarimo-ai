"""
Performance Logger Service - Track timing and metrics for the entire pipeline
"""
import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict
import time

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class StageMetrics:
    """Metrics for a single processing stage"""
    stage_name: str
    start_time: float
    end_time: Optional[float] = None
    duration_seconds: Optional[float] = None
    success: bool = False
    error_message: Optional[str] = None
    metrics: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metrics is None:
            self.metrics = {}
    
    def finish(self, success: bool = True, error_message: Optional[str] = None, **metrics):
        """Mark stage as finished and calculate duration"""
        self.end_time = time.time()
        self.duration_seconds = self.end_time - self.start_time
        self.success = success
        self.error_message = error_message
        self.metrics.update(metrics)

@dataclass
class PipelineMetrics:
    """Complete pipeline performance metrics"""
    user_id: str
    input_id: str
    problem_description: str
    pipeline_start_time: float
    pipeline_end_time: Optional[float] = None
    total_duration_seconds: Optional[float] = None
    overall_success: bool = False
    stages: Dict[str, StageMetrics] = None
    
    def __post_init__(self):
        if self.stages is None:
            self.stages = {}
    
    def start_stage(self, stage_name: str) -> StageMetrics:
        """Start tracking a new stage"""
        stage = StageMetrics(stage_name=stage_name, start_time=time.time())
        self.stages[stage_name] = stage
        return stage
    
    def finish_pipeline(self, success: bool = True):
        """Mark entire pipeline as finished"""
        self.pipeline_end_time = time.time()
        self.total_duration_seconds = self.pipeline_end_time - self.pipeline_start_time
        self.overall_success = success

class PerformanceLogger:
    """Service for logging pipeline performance metrics"""
    
    def __init__(self):
        self.active_pipelines: Dict[str, PipelineMetrics] = {}
        self.logs_dir = Path("logs/performance")
        self.logs_dir.mkdir(parents=True, exist_ok=True)
    
    def start_pipeline(self, user_id: str, input_id: str, problem_description: str) -> PipelineMetrics:
        """Start tracking a new pipeline"""
        pipeline = PipelineMetrics(
            user_id=user_id,
            input_id=input_id,
            problem_description=problem_description,
            pipeline_start_time=time.time()
        )
        self.active_pipelines[input_id] = pipeline
        
        logger.info(f"🚀 Started pipeline tracking for {input_id}")
        return pipeline
    
    def get_pipeline(self, input_id: str) -> Optional[PipelineMetrics]:
        """Get active pipeline metrics"""
        return self.active_pipelines.get(input_id)
    
    def start_stage(self, input_id: str, stage_name: str) -> Optional[StageMetrics]:
        """Start tracking a stage"""
        pipeline = self.active_pipelines.get(input_id)
        if not pipeline:
            logger.warning(f"No active pipeline found for {input_id}")
            return None
        
        stage = pipeline.start_stage(stage_name)
        logger.info(f"⏱️ Started stage '{stage_name}' for {input_id}")
        return stage
    
    def finish_stage(self, input_id: str, stage_name: str, success: bool = True, 
                    error_message: Optional[str] = None, **metrics):
        """Finish tracking a stage"""
        pipeline = self.active_pipelines.get(input_id)
        if not pipeline or stage_name not in pipeline.stages:
            logger.warning(f"No active stage '{stage_name}' found for {input_id}")
            return
        
        stage = pipeline.stages[stage_name]
        stage.finish(success=success, error_message=error_message, **metrics)
        
        status = "✅" if success else "❌"
        duration = f"{stage.duration_seconds:.2f}s" if stage.duration_seconds else "N/A"
        logger.info(f"{status} Finished stage '{stage_name}' for {input_id} in {duration}")
        
        # Log key metrics
        if metrics:
            metrics_str = ", ".join([f"{k}={v}" for k, v in metrics.items()])
            logger.info(f"📊 Stage metrics: {metrics_str}")
    
    def finish_pipeline(self, input_id: str, success: bool = True):
        """Finish tracking entire pipeline and save to file"""
        pipeline = self.active_pipelines.get(input_id)
        if not pipeline:
            logger.warning(f"No active pipeline found for {input_id}")
            return
        
        pipeline.finish_pipeline(success=success)
        
        # Save to file
        self._save_pipeline_log(pipeline)
        
        # Log summary
        self._log_pipeline_summary(pipeline)
        
        # Remove from active pipelines
        del self.active_pipelines[input_id]
    
    def _save_pipeline_log(self, pipeline: PipelineMetrics):
        """Save pipeline metrics to JSON file"""
        try:
            timestamp = datetime.fromtimestamp(pipeline.pipeline_start_time).strftime("%Y%m%d_%H%M%S")
            filename = f"pipeline_{pipeline.input_id}_{timestamp}.json"
            filepath = self.logs_dir / filename
            
            # Convert to dict for JSON serialization
            data = asdict(pipeline)
            
            # Add human-readable timestamps
            data['pipeline_start_time_human'] = datetime.fromtimestamp(pipeline.pipeline_start_time).isoformat()
            if pipeline.pipeline_end_time:
                data['pipeline_end_time_human'] = datetime.fromtimestamp(pipeline.pipeline_end_time).isoformat()
            
            # Add human-readable stage times
            for stage_name, stage in data['stages'].items():
                stage['start_time_human'] = datetime.fromtimestamp(stage['start_time']).isoformat()
                if stage['end_time']:
                    stage['end_time_human'] = datetime.fromtimestamp(stage['end_time']).isoformat()
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"💾 Saved pipeline log to {filepath}")
            
        except Exception as e:
            logger.error(f"Error saving pipeline log: {str(e)}")
    
    def _log_pipeline_summary(self, pipeline: PipelineMetrics):
        """Log a comprehensive pipeline summary"""
        status = "✅ SUCCESS" if pipeline.overall_success else "❌ FAILED"
        total_time = f"{pipeline.total_duration_seconds:.2f}s" if pipeline.total_duration_seconds else "N/A"
        
        logger.info("=" * 80)
        logger.info(f"🎯 PIPELINE SUMMARY - {status}")
        logger.info("=" * 80)
        logger.info(f"📝 Problem: {pipeline.problem_description[:100]}...")
        logger.info(f"🆔 Input ID: {pipeline.input_id}")
        logger.info(f"⏱️ Total Time: {total_time}")
        logger.info("-" * 80)
        
        # Stage breakdown
        for stage_name, stage in pipeline.stages.items():
            status_icon = "✅" if stage.success else "❌"
            duration = f"{stage.duration_seconds:.2f}s" if stage.duration_seconds else "N/A"
            
            logger.info(f"{status_icon} {stage_name.upper()}: {duration}")
            
            # Log key metrics for each stage
            if stage.metrics:
                for key, value in stage.metrics.items():
                    logger.info(f"   📊 {key}: {value}")
            
            if stage.error_message:
                logger.info(f"   ❌ Error: {stage.error_message}")
        
        logger.info("=" * 80)
        
        # Calculate percentages
        if pipeline.total_duration_seconds and pipeline.total_duration_seconds > 0:
            logger.info("⏱️ TIME BREAKDOWN:")
            for stage_name, stage in pipeline.stages.items():
                if stage.duration_seconds:
                    percentage = (stage.duration_seconds / pipeline.total_duration_seconds) * 100
                    logger.info(f"   {stage_name}: {percentage:.1f}% ({stage.duration_seconds:.2f}s)")
            logger.info("=" * 80)
    
    def get_pipeline_summary(self, input_id: str) -> Optional[Dict[str, Any]]:
        """Get current pipeline summary"""
        pipeline = self.active_pipelines.get(input_id)
        if not pipeline:
            return None
        
        current_time = time.time()
        elapsed_time = current_time - pipeline.pipeline_start_time
        
        summary = {
            "input_id": input_id,
            "elapsed_time_seconds": elapsed_time,
            "elapsed_time_formatted": f"{elapsed_time:.2f}s",
            "stages_completed": len([s for s in pipeline.stages.values() if s.end_time is not None]),
            "total_stages": len(pipeline.stages),
            "current_stage": None,
            "stage_details": {}
        }
        
        # Find current stage
        for stage_name, stage in pipeline.stages.items():
            if stage.end_time is None:  # Currently running
                summary["current_stage"] = stage_name
                summary["stage_elapsed"] = current_time - stage.start_time
            
            summary["stage_details"][stage_name] = {
                "completed": stage.end_time is not None,
                "success": stage.success,
                "duration": stage.duration_seconds,
                "metrics": stage.metrics
            }
        
        return summary

# Global instance
performance_logger = PerformanceLogger()