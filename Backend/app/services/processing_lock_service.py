"""
Processing Lock Service - Prevent duplicate processing requests
"""
import asyncio
import logging
from typing import Set, Optional
from datetime import datetime, timedelta
from enum import Enum

logger = logging.getLogger(__name__)

class ProcessingStage(Enum):
    PENDING = "pending"
    KEYWORD_GENERATION = "keyword_generation"
    POSTS_FETCHING = "posts_fetching"
    EMBEDDINGS = "embeddings"
    SEMANTIC_FILTERING = "semantic_filtering"
    CLUSTERING = "clustering"
    PAIN_POINTS_EXTRACTION = "pain_points_extraction"
    COMPLETED = "completed"
    FAILED = "failed"

class ProcessingLockService:
    """Service to manage processing locks and prevent duplicate requests"""
    
    def __init__(self):
        self._active_processes: Set[str] = set()
        self._process_start_times: dict = {}
        self._process_stages: dict = {}
        self._process_last_update: dict = {}
        self._lock = asyncio.Lock()
    
    async def acquire_lock(self, user_id: str, input_id: str) -> bool:
        """
        Try to acquire a processing lock for a specific user input
        
        Returns:
            True if lock acquired, False if already processing
        """
        async with self._lock:
            process_key = f"{user_id}:{input_id}"
            
            # Check if already processing
            if process_key in self._active_processes:
                # Check if process has been stuck for too long
                if await self._is_process_stuck(process_key):
                    logger.warning(f"Process {process_key} appears stuck, releasing lock")
                    await self._force_release(process_key)
                else:
                    logger.info(f"Process {process_key} already in progress")
                    return False
            
            # Acquire lock
            self._active_processes.add(process_key)
            self._process_start_times[process_key] = datetime.now()
            self._process_last_update[process_key] = datetime.now()
            self._process_stages[process_key] = ProcessingStage.PENDING
            logger.info(f"Acquired processing lock for {process_key}")
            return True
    
    async def update_stage(self, user_id: str, input_id: str, stage: ProcessingStage):
        """Update the current processing stage and timestamp"""
        async with self._lock:
            process_key = f"{user_id}:{input_id}"
            if process_key in self._active_processes:
                self._process_stages[process_key] = stage
                self._process_last_update[process_key] = datetime.now()
                logger.info(f"Updated {process_key} to stage: {stage.value}")
    
    async def release_lock(self, user_id: str, input_id: str, completed: bool = True):
        """Release a processing lock"""
        async with self._lock:
            process_key = f"{user_id}:{input_id}"
            stage = ProcessingStage.COMPLETED if completed else ProcessingStage.FAILED
            
            if process_key in self._active_processes:
                self._process_stages[process_key] = stage
                self._process_last_update[process_key] = datetime.now()
            
            self._active_processes.discard(process_key)
            self._process_start_times.pop(process_key, None)
            self._process_last_update.pop(process_key, None)
            self._process_stages.pop(process_key, None)
            
            status = "completed" if completed else "failed"
            logger.info(f"Released processing lock for {process_key} ({status})")
    
    async def is_processing(self, user_id: str, input_id: str) -> bool:
        """Check if a specific input is currently being processed"""
        process_key = f"{user_id}:{input_id}"
        
        # If process exists but appears stuck, consider it not processing
        if process_key in self._active_processes and await self._is_process_stuck(process_key):
            await self._force_release(process_key)
            return False
            
        return process_key in self._active_processes
    
    async def get_current_stage(self, user_id: str, input_id: str) -> Optional[ProcessingStage]:
        """Get the current processing stage for a request"""
        process_key = f"{user_id}:{input_id}"
        return self._process_stages.get(process_key)
    
    async def _is_process_stuck(self, process_key: str) -> bool:
        """Check if a process appears to be stuck based on last update time"""
        if process_key not in self._process_last_update:
            return True
        
        last_update = self._process_last_update[process_key]
        time_since_update = datetime.now() - last_update
        
        # Different timeouts for different stages
        stage = self._process_stages.get(process_key, ProcessingStage.PENDING)
        
        timeout_minutes = {
            ProcessingStage.PENDING: 2,           # Should move quickly from pending
            ProcessingStage.KEYWORD_GENERATION: 5,
            ProcessingStage.POSTS_FETCHING: 10,   # Posts fetching might take longer
            ProcessingStage.EMBEDDINGS: 20,
            ProcessingStage.SEMANTIC_FILTERING: 4,
            ProcessingStage.CLUSTERING: 5,
            ProcessingStage.PAIN_POINTS_EXTRACTION: 5,
            ProcessingStage.COMPLETED: 0,         # Completed processes aren't stuck
            ProcessingStage.FAILED: 0,            # Failed processes aren't stuck
        }
        
        max_timeout = timeout_minutes.get(stage, 5)
        return time_since_update > timedelta(minutes=max_timeout)
    
    async def _force_release(self, process_key: str):
        """Force release a stuck process"""
        self._active_processes.discard(process_key)
        self._process_start_times.pop(process_key, None)
        self._process_last_update.pop(process_key, None)
        self._process_stages.pop(process_key, None)
        logger.warning(f"Force released stuck process: {process_key}")
    
    async def cleanup_stuck_processes(self):
        """Clean up all stuck processes (call this periodically)"""
        async with self._lock:
            stuck_processes = [
                process_key for process_key in self._active_processes 
                if await self._is_process_stuck(process_key)
            ]
            
            for process_key in stuck_processes:
                await self._force_release(process_key)
            
            if stuck_processes:
                logger.info(f"Cleaned up {len(stuck_processes)} stuck processes")
    
    async def get_active_processes(self) -> dict:
        """Get all active processes with their start times and current stages"""
        async with self._lock:
            # Clean up stuck processes first
            await self.cleanup_stuck_processes()
            
            return {
                process_key: {
                    "started_at": start_time.isoformat(),
                    "current_stage": self._process_stages[process_key].value,
                    "last_updated": self._process_last_update[process_key].isoformat(),
                    "duration_minutes": (datetime.now() - start_time).total_seconds() / 60
                }
                for process_key, start_time in self._process_start_times.items()
            }

# Create singleton instance
processing_lock_service = ProcessingLockService()