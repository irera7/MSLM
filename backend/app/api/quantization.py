"""
Quantization API endpoints.
Convert and quantize models to different formats.
"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from typing import Optional
from pathlib import Path

from app.database.database import get_db
from app.database.models import Model as DBModel
from app.services.quantization_service import quantization_service, QuantizationLevel
from sqlalchemy import select
import logging

router = APIRouter(prefix="/api/quantization", tags=["quantization"])
logger = logging.getLogger(__name__)


class QuantizeRequest(BaseModel):
    model_id: int
    output_name: str
    quantization_level: QuantizationLevel
    
class QuantizeResponse(BaseModel):
    job_id: str
    message: str
    estimated_size_ratio: float


# Track quantization jobs
quantization_jobs = {}


@router.post("/", response_model=QuantizeResponse)
async def quantize_model(
    request: QuantizeRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """
    Quantize a model to GGUF format.
    
    Args:
        model_id: Source model ID
        output_name: Name for quantized model
        quantization_level: Quantization level (Q4_K_M, Q5_K_M, etc.)
    
    Returns:
        Job ID for tracking progress
    """
    # Get source model
    result = await db.execute(
        select(DBModel).where(DBModel.id == request.model_id)
    )
    source_model = result.scalar_one_or_none()
    
    if not source_model:
        raise HTTPException(status_code=404, detail="Source model not found")
    
    # Check if source is in compatible format
    if source_model.format not in ["SafeTensors", "PyTorch"]:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot quantize {source_model.format} format. Only SafeTensors and PyTorch supported."
        )
    
    # Generate job ID
    import uuid
    job_id = str(uuid.uuid4())
    
    # Get quantization info
    quant_info = quantization_service.get_quantization_info(request.quantization_level)
    
    # Create output path
    from app.core.config import settings
    output_dir = Path(settings.MODELS_DIR) / "quantized"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"{request.output_name}.gguf"
    
    # Initialize job status
    quantization_jobs[job_id] = {
        "status": "pending",
        "progress": 0.0,
        "message": "Waiting to start...",
        "source_model_id": request.model_id,
        "output_path": str(output_path)
    }
    
    # Start quantization in background
    background_tasks.add_task(
        run_quantization,
        job_id,
        source_model.path,
        str(output_path),
        request.quantization_level,
        request.output_name,
        db
    )
    
    return QuantizeResponse(
        job_id=job_id,
        message=f"Quantization job started. Quality: {quant_info['quality']}",
        estimated_size_ratio=quant_info['size_ratio']
    )


@router.get("/{job_id}")
async def get_quantization_status(job_id: str):
    """Get status of a quantization job"""
    if job_id not in quantization_jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    
    return quantization_jobs[job_id]


@router.get("/")
async def list_quantization_jobs():
    """List all quantization jobs"""
    return {
        "jobs": [
            {"job_id": jid, **job}
            for jid, job in quantization_jobs.items()
        ]
    }


@router.get("/info/levels")
async def get_quantization_levels():
    """Get information about all quantization levels"""
    levels = {}
    for level in QuantizationLevel:
        levels[level.value] = quantization_service.get_quantization_info(level)
    
    return {
        "levels": levels,
        "recommended": ["Q4_K_M", "Q5_K_M", "Q8_0"]
    }


async def run_quantization(
    job_id: str,
    input_path: str,
    output_path: str,
    quantization: QuantizationLevel,
    model_name: str,
    db: AsyncSession
):
    """Background task to run quantization"""
    try:
        def progress_callback(progress: float, message: str):
            """Update job status"""
            quantization_jobs[job_id]["progress"] = progress
            quantization_jobs[job_id]["message"] = message
            quantization_jobs[job_id]["status"] = "running" if progress < 1.0 else "completed"
            logger.info(f"Quantization {job_id}: {progress:.1%} - {message}")
        
        # Run quantization
        success = await quantization_service.convert_to_gguf(
            input_path=input_path,
            output_path=output_path,
            quantization=quantization,
            progress_callback=progress_callback
        )
        
        if success:
            # Register quantized model
            from app.database.models import Model as DBModel
            
            output_file = Path(output_path)
            
            new_model = DBModel(
                name=model_name,
                path=str(output_path),
                format="GGUF",
                size=output_file.stat().st_size if output_file.exists() else 0,
                source="quantized",
                model_metadata={
                    "quantization": quantization.value,
                    "source_model_id": quantization_jobs[job_id]["source_model_id"]
                }
            )
            
            db.add(new_model)
            await db.commit()
            await db.refresh(new_model)
            
            quantization_jobs[job_id]["status"] = "completed"
            quantization_jobs[job_id]["progress"] = 1.0
            quantization_jobs[job_id]["message"] = "Quantization successful"
            quantization_jobs[job_id]["model_id"] = new_model.id
            
            logger.info(f"Quantization {job_id} completed successfully")
        else:
            quantization_jobs[job_id]["status"] = "failed"
            quantization_jobs[job_id]["message"] = "Quantization failed"
            logger.error(f"Quantization {job_id} failed")
            
    except Exception as e:
        quantization_jobs[job_id]["status"] = "failed"
        quantization_jobs[job_id]["message"] = f"Error: {str(e)}"
        logger.error(f"Quantization {job_id} error: {str(e)}")

