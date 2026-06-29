"""
Batch processing API endpoints.
"""

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Dict, Any, Optional
from pydantic import BaseModel

from app.database.database import get_db
from app.services.batch_service import batch_service, BatchStatus
from app.services.model_manager import model_manager

router = APIRouter(prefix="/api/batch", tags=["batch"])


class BatchCreate(BaseModel):
    model_id: int
    prompts: List[str]
    temperature: float = 0.7
    top_p: float = 0.9
    top_k: int = 40
    max_tokens: int = 2048
    repeat_penalty: float = 1.1


@router.post("/jobs")
async def create_batch_job(
    request: BatchCreate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new batch processing job.
    The job will be processed in the background.
    """
    try:
        # Check if model is loaded
        if not model_manager.is_model_loaded(request.model_id):
            raise HTTPException(
                status_code=400,
                detail=f"Model {request.model_id} is not loaded. Load it first."
            )
        
        if not request.prompts:
            raise HTTPException(status_code=400, detail="Prompts list cannot be empty")
        
        if len(request.prompts) > 1000:
            raise HTTPException(status_code=400, detail="Maximum 1000 prompts per batch")
        
        # Create config
        config = {
            "temperature": request.temperature,
            "top_p": request.top_p,
            "top_k": request.top_k,
            "max_tokens": request.max_tokens,
            "repeat_penalty": request.repeat_penalty,
            "stream": False
        }
        
        # Create job
        job_id = batch_service.create_job(
            model_id=request.model_id,
            prompts=request.prompts,
            config=config
        )
        
        # Start processing in background
        background_tasks.add_task(
            batch_service.process_job,
            job_id,
            model_manager,
            db
        )
        
        return {
            "job_id": job_id,
            "status": "pending",
            "total_prompts": len(request.prompts),
            "message": "Batch job created and will be processed in the background"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/jobs")
async def list_batch_jobs(status: Optional[str] = None):
    """
    List all batch jobs, optionally filtered by status.
    
    Args:
        status: Optional status filter (pending, processing, completed, failed, cancelled)
    """
    try:
        status_enum = BatchStatus(status) if status else None
        jobs = batch_service.list_jobs(status=status_enum)
        
        return {
            "jobs": jobs,
            "count": len(jobs)
        }
        
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid status. Must be one of: {[s.value for s in BatchStatus]}"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/jobs/{job_id}/status")
async def get_job_status(job_id: str):
    """Get the status of a batch job"""
    try:
        status = batch_service.get_job_status(job_id)
        
        if status is None:
            raise HTTPException(status_code=404, detail=f"Job {job_id} not found")
        
        return status
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/jobs/{job_id}/results")
async def get_job_results(job_id: str):
    """
    Get the results of a batch job.
    Returns all prompts and their responses.
    """
    try:
        results = batch_service.get_job_results(job_id)
        
        if results is None:
            raise HTTPException(status_code=404, detail=f"Job {job_id} not found")
        
        return results
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/jobs/{job_id}/cancel")
async def cancel_job(job_id: str):
    """Cancel a batch job"""
    try:
        success = batch_service.cancel_job(job_id)
        
        if not success:
            raise HTTPException(
                status_code=400,
                detail="Job cannot be cancelled (not found or already completed)"
            )
        
        return {
            "message": f"Job {job_id} cancelled successfully",
            "job_id": job_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/jobs/{job_id}")
async def delete_job(job_id: str):
    """Delete a batch job and its results"""
    try:
        success = batch_service.delete_job(job_id)
        
        if not success:
            raise HTTPException(status_code=404, detail=f"Job {job_id} not found")
        
        return {
            "message": f"Job {job_id} deleted successfully",
            "job_id": job_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

