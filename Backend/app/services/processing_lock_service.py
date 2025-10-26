"""
Processing Lock Service - Prevent duplicate processing requests
"""
import asyncio
import logging
from typing import Set
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class ProcessingLockService:
    """Service to manage processing locks and prevent duplicate requests"""
    
    def __init__(self):
        self._active_processes: Set[str] = set()
        self._process_start_times: dict = {}
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
                # Check if process has been running too long (timeout after 30 minutes)
                start_time = self._process_start_times.get(process_key)
                if start_time and datetime.now() - start_time > timedelta(minutes=30):
                    logger.warning(f"Process {process_key} timed out, releasing lock")
                    self._active_processes.discard(process_key)
                    self._process_start_times.pop(process_key, None)
                else:
                    logger.info(f"Process {process_key} already in progress")
                    return False
            
            # Acquire lock
            self._active_processes.add(process_key)
            self._process_start_times[process_key] = datetime.now()
            logger.info(f"Acquired processing lock for {process_key}")
            return True
    
    async def release_lock(self, user_id: str, input_id: str):
        """Release a processing lock"""
        async with self._lock:
            process_key = f"{user_id}:{input_id}"
            self._active_processes.discard(process_key)
            self._process_start_times.pop(process_key, None)
            logger.info(f"Released processing lock for {process_key}")
    
    async def is_processing(self, user_id: str, input_id: str) -> bool:
        """Check if a specific input is currently being processed"""
        process_key = f"{user_id}:{input_id}"
        return process_key in self._active_processes
    
    async def get_active_processes(self) -> dict:
        """Get all active processes with their start times"""
        async with self._lock:
            return {
                process_key: {
                    "started_at": start_time.isoformat(),
                    "duration_minutes": (datetime.now() - start_time).total_seconds() / 60
                }
                for process_key, start_time in self._process_start_times.items()
            }

# Create singleton instance
processing_lock_service = ProcessingLockService()