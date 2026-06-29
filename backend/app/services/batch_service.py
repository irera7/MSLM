"""
Batch processing service for inference.
Allows processing multiple prompts efficiently.
"""

import logging
import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime
from enum import Enum
import json
from pathlib import Path

logger = logging.getLogger(__name__)


class BatchStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class BatchJob:
    """Represents a batch processing job"""
    
    def __init__(
        self,
        job_id: str,
        model_id: int,
        prompts: List[str],
        config: Dict[str, Any]
    ):
        self.job_id = job_id
        self.model_id = model_id
        self.prompts = prompts
        self.config = config
        self.status = BatchStatus.PENDING
        self.results: List[Optional[str]] = [None] * len(prompts)
        self.errors: List[Optional[str]] = [None] * len(prompts)
        self.progress = 0
        self.total = len(prompts)
        self.created_at = datetime.utcnow()
        self.started_at: Optional[datetime] = None
        self.completed_at: Optional[datetime] = None


class BatchProcessingService:
    """
    Service for batch inference processing.
    """
    
    def __init__(self, output_dir: str = "./data/batch_results"):
        self.logger = logging.getLogger(__name__)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.jobs: Dict[str, BatchJob] = {}
        self.lock = asyncio.Lock()
    
    def create_job(
        self,
        model_id: int,
        prompts: List[str],
        config: Dict[str, Any]
    ) -> str:
        """
        Create a new batch job.
        
        Args:
            model_id: Model ID to use
            prompts: List of prompts to process
            config: Generation config
            
        Returns:
            str: Job ID
        """
        import uuid
        
        job_id = str(uuid.uuid4())
        
        job = BatchJob(
            job_id=job_id,
            model_id=model_id,
            prompts=prompts,
            config=config
        )
        
        self.jobs[job_id] = job
        
        self.logger.info(f"Created batch job {job_id} with {len(prompts)} prompts")
        return job_id
    
    async def process_job(
        self,
        job_id: str,
        model_manager,
        db_session
    ) -> bool:
        """
        Process a batch job.
        
        Args:
            job_id: Job ID
            model_manager: Model manager instance
            db_session: Database session
            
        Returns:
            bool: True if successful
        """
        async with self.lock:
            if job_id not in self.jobs:
                self.logger.error(f"Job {job_id} not found")
                return False
            
            job = self.jobs[job_id]
            
            if job.status != BatchStatus.PENDING:
                self.logger.warning(f"Job {job_id} is not pending (status: {job.status})")
                return False
            
            job.status = BatchStatus.PROCESSING
            job.started_at = datetime.utcnow()
        
        self.logger.info(f"Processing batch job {job_id}")
        
        try:
            from app.services.inference.base_engine import GenerationConfig
            
            gen_config = GenerationConfig(**job.config)
            
            # Process each prompt
            for i, prompt in enumerate(job.prompts):
                if job.status == BatchStatus.CANCELLED:
                    self.logger.info(f"Job {job_id} cancelled")
                    break
                
                try:
                    # Generate response
                    response = await model_manager.non_stream_generate_text(
                        model_id=job.model_id,
                        prompt=prompt,
                        config=gen_config,
                        db=db_session
                    )
                    
                    job.results[i] = response
                    job.progress = i + 1
                    
                    self.logger.debug(f"Job {job_id}: Completed {i+1}/{job.total}")
                    
                except Exception as e:
                    self.logger.error(f"Job {job_id}, prompt {i} failed: {str(e)}")
                    job.errors[i] = str(e)
                    job.progress = i + 1
            
            # Mark as completed or failed
            if job.status == BatchStatus.CANCELLED:
                pass  # Already set
            elif all(err is not None for err in job.errors):
                job.status = BatchStatus.FAILED
            else:
                job.status = BatchStatus.COMPLETED
            
            job.completed_at = datetime.utcnow()
            
            # Save results to file
            self._save_results(job)
            
            self.logger.info(f"Batch job {job_id} finished with status: {job.status}")
            return job.status == BatchStatus.COMPLETED
            
        except Exception as e:
            self.logger.error(f"Batch job {job_id} failed: {str(e)}")
            job.status = BatchStatus.FAILED
            job.completed_at = datetime.utcnow()
            return False
    
    def _save_results(self, job: BatchJob):
        """Save job results to file"""
        try:
            output_file = self.output_dir / f"{job.job_id}.json"
            
            results_data = {
                "job_id": job.job_id,
                "model_id": job.model_id,
                "status": job.status.value,
                "progress": job.progress,
                "total": job.total,
                "created_at": job.created_at.isoformat(),
                "started_at": job.started_at.isoformat() if job.started_at else None,
                "completed_at": job.completed_at.isoformat() if job.completed_at else None,
                "config": job.config,
                "results": [
                    {
                        "prompt": job.prompts[i],
                        "response": job.results[i],
                        "error": job.errors[i]
                    }
                    for i in range(len(job.prompts))
                ]
            }
            
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(results_data, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"Saved results for job {job.job_id} to {output_file}")
            
        except Exception as e:
            self.logger.error(f"Failed to save results for job {job.job_id}: {str(e)}")
    
    def get_job(self, job_id: str) -> Optional[BatchJob]:
        """Get job by ID"""
        return self.jobs.get(job_id)
    
    def get_job_status(self, job_id: str) -> Optional[Dict[str, Any]]:
        """
        Get job status.
        
        Returns:
            Dict with job status or None
        """
        job = self.get_job(job_id)
        
        if job is None:
            return None
        
        duration = None
        if job.started_at:
            end_time = job.completed_at or datetime.utcnow()
            duration = (end_time - job.started_at).total_seconds()
        
        return {
            "job_id": job.job_id,
            "model_id": job.model_id,
            "status": job.status.value,
            "progress": job.progress,
            "total": job.total,
            "completion_percent": round((job.progress / job.total) * 100, 2) if job.total > 0 else 0,
            "created_at": job.created_at.isoformat(),
            "started_at": job.started_at.isoformat() if job.started_at else None,
            "completed_at": job.completed_at.isoformat() if job.completed_at else None,
            "duration_seconds": duration
        }
    
    def get_job_results(self, job_id: str) -> Optional[Dict[str, Any]]:
        """
        Get job results.
        
        Returns:
            Dict with results or None
        """
        job = self.get_job(job_id)
        
        if job is None:
            return None
        
        return {
            "job_id": job.job_id,
            "status": job.status.value,
            "results": [
                {
                    "index": i,
                    "prompt": job.prompts[i],
                    "response": job.results[i],
                    "error": job.errors[i]
                }
                for i in range(len(job.prompts))
            ]
        }
    
    def cancel_job(self, job_id: str) -> bool:
        """Cancel a job"""
        job = self.get_job(job_id)
        
        if job is None:
            return False
        
        if job.status in [BatchStatus.PENDING, BatchStatus.PROCESSING]:
            job.status = BatchStatus.CANCELLED
            job.completed_at = datetime.utcnow()
            self.logger.info(f"Cancelled job {job_id}")
            return True
        
        return False
    
    def list_jobs(self, status: Optional[BatchStatus] = None) -> List[Dict[str, Any]]:
        """
        List all jobs, optionally filtered by status.
        
        Args:
            status: Optional status filter
            
        Returns:
            List of job summaries
        """
        jobs = []
        
        for job_id, job in self.jobs.items():
            if status is None or job.status == status:
                jobs.append({
                    "job_id": job.job_id,
                    "model_id": job.model_id,
                    "status": job.status.value,
                    "progress": job.progress,
                    "total": job.total,
                    "created_at": job.created_at.isoformat()
                })
        
        return jobs
    
    def delete_job(self, job_id: str) -> bool:
        """Delete a job and its results"""
        if job_id not in self.jobs:
            return False
        
        # Delete results file
        output_file = self.output_dir / f"{job_id}.json"
        if output_file.exists():
            output_file.unlink()
        
        # Delete job
        del self.jobs[job_id]
        
        self.logger.info(f"Deleted job {job_id}")
        return True


# Singleton instance
batch_service = BatchProcessingService()

