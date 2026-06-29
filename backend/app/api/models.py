from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, update
from typing import List, Optional
import logging
from pathlib import Path
from pydantic import BaseModel

from app.database.database import get_db
from app.database.models import Model as DBModel
from app.schemas.model import (
    ModelCreate,
    ModelUpdate,
    ModelResponse,
    ModelListResponse,
    ModelLoadRequest,
    ModelLoadResponse
)
from app.services.model_manager import model_manager
from app.services.format_detector import format_detector
from app.services.model_management import (
    model_versioning,
    model_comparison,
    model_benchmarking,
    model_tagging
)

router = APIRouter()
logger = logging.getLogger(__name__)


# Request models
class ImportModelRequest(BaseModel):
    path: str
    name: Optional[str] = None
    format: Optional[str] = None


class DetectFormatRequest(BaseModel):
    path: str


@router.get("/", response_model=ModelListResponse)
async def list_models(
    skip: int = 0,
    limit: int = 100,
    format_filter: Optional[str] = None,
    source_filter: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """List all models with optional filtering"""
    try:
        query = select(DBModel)
        
        if format_filter:
            query = query.where(DBModel.format == format_filter.upper())
        
        if source_filter:
            query = query.where(DBModel.source == source_filter)
        
        query = query.offset(skip).limit(limit)
        
        result = await db.execute(query)
        models = result.scalars().all()
        
        total_query = select(DBModel)
        if format_filter:
            total_query = total_query.where(DBModel.format == format_filter.upper())
        if source_filter:
            total_query = total_query.where(DBModel.source == source_filter)
        
        total_result = await db.execute(total_query)
        total = len(total_result.scalars().all())
        
        return ModelListResponse(
            models=[ModelResponse.model_validate(m) for m in models],
            total=total
        )
    except Exception as e:
        logger.error(f"Failed to list models: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{model_id}", response_model=ModelResponse)
async def get_model(model_id: int, db: AsyncSession = Depends(get_db)):
    """Get a specific model by ID"""
    result = await db.execute(select(DBModel).where(DBModel.id == model_id))
    model = result.scalar_one_or_none()
    
    if not model:
        raise HTTPException(status_code=404, detail="Model not found")
    
    return ModelResponse.model_validate(model)


@router.post("/", response_model=ModelResponse, status_code=status.HTTP_201_CREATED)
async def create_model(model: ModelCreate, db: AsyncSession = Depends(get_db)):
    """Register a new model"""
    try:
        # Check if path exists
        if not Path(model.path).exists():
            raise HTTPException(status_code=400, detail=f"Model path does not exist: {model.path}")
        
        # Check if model already exists
        result = await db.execute(select(DBModel).where(DBModel.path == model.path))
        existing = result.scalar_one_or_none()
        if existing:
            raise HTTPException(status_code=400, detail="Model with this path already exists")
        
        # Create new model
        db_model = DBModel(
            name=model.name,
            path=model.path,
            format=model.format.upper(),
            size=model.size,
            source=model.source,
            source_url=model.source_url,
            quantization=model.quantization,
            parameters=model.parameters,
            model_metadata=model.model_metadata
        )
        
        db.add(db_model)
        await db.commit()
        await db.refresh(db_model)
        
        logger.info(f"Created model: {db_model.name} (ID: {db_model.id})")
        return ModelResponse.model_validate(db_model)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create model: {str(e)}")
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/{model_id}", response_model=ModelResponse)
async def update_model(
    model_id: int,
    model_update: ModelUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update a model"""
    result = await db.execute(select(DBModel).where(DBModel.id == model_id))
    db_model = result.scalar_one_or_none()
    
    if not db_model:
        raise HTTPException(status_code=404, detail="Model not found")
    
    # Update fields
    update_data = model_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_model, field, value)
    
    await db.commit()
    await db.refresh(db_model)
    
    return ModelResponse.model_validate(db_model)


@router.delete("/{model_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_model(model_id: int, db: AsyncSession = Depends(get_db)):
    """Delete a model"""
    # Unload if loaded
    if model_manager.is_model_loaded(model_id):
        await model_manager.unload_model(model_id, db)
    
    # Delete from database
    result = await db.execute(delete(DBModel).where(DBModel.id == model_id))
    
    if result.rowcount == 0:
        raise HTTPException(status_code=404, detail="Model not found")
    
    await db.commit()
    logger.info(f"Deleted model ID: {model_id}")


@router.post("/{model_id}/load", response_model=ModelLoadResponse)
async def load_model(
    model_id: int,
    load_request: ModelLoadRequest,
    db: AsyncSession = Depends(get_db)
):
    """Load a model into memory"""
    # Get model from database
    result = await db.execute(select(DBModel).where(DBModel.id == model_id))
    db_model = result.scalar_one_or_none()
    
    if not db_model:
        raise HTTPException(status_code=404, detail="Model not found")
    
    # Check if already loaded
    if model_manager.is_model_loaded(model_id):
        return ModelLoadResponse(
            success=True,
            message="Model is already loaded",
            model_id=model_id
        )
    
    try:
        # Load model
        gpu_layers = load_request.gpu_layers if load_request.gpu_layers is not None else 0
        context_length = load_request.context_length if load_request.context_length is not None else 2048
        
        model_info = await model_manager.load_model(
            model_id=model_id,
            model_path=db_model.path,
            format=db_model.format,
            db=db,
            gpu_layers=gpu_layers,
            context_length=context_length
        )
        
        return ModelLoadResponse(
            success=True,
            message=f"Model loaded successfully. Memory usage: {model_info.memory_usage:.2f} MB",
            model_id=model_id
        )
        
    except Exception as e:
        logger.error(f"Failed to load model {model_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{model_id}/unload")
async def unload_model(model_id: int, db: AsyncSession = Depends(get_db)):
    """Unload a model from memory"""
    # Check if model exists in database
    result = await db.execute(select(DBModel).where(DBModel.id == model_id))
    model = result.scalar_one_or_none()
    
    if not model:
        raise HTTPException(status_code=404, detail="Model not found")
    
    # If model_manager says it's not loaded, just update database and return
    if not model_manager.is_model_loaded(model_id):
        # Update database to reflect correct state
        await db.execute(
            update(DBModel)
            .where(DBModel.id == model_id)
            .values(is_loaded=False)
        )
        await db.commit()
        return {"success": True, "message": "Model state synchronized (was already unloaded)"}
    
    # Actually unload from memory
    success = await model_manager.unload_model(model_id, db)
    
    if success:
        return {"success": True, "message": "Model unloaded successfully"}
    else:
        raise HTTPException(status_code=500, detail="Failed to unload model")


@router.get("/loaded/list")
async def list_loaded_models():
    """Get list of currently loaded models"""
    loaded_info = model_manager.get_loaded_models_info()
    memory_usage = model_manager.get_memory_usage()
    
    return {
        "loaded_models": [
            {
                "model_id": info.model_id,
                "format": info.format,
                "context_length": info.context_length,
                "gpu_layers": info.gpu_layers,
                "memory_usage_mb": memory_usage.get(info.model_id, 0)
            }
            for info in loaded_info
        ],
        "total_memory_mb": model_manager.get_total_memory_usage(),
        "count": len(loaded_info)
    }


@router.post("/unload_all")
async def unload_all_models(db: AsyncSession = Depends(get_db)):
    """Unload all loaded models"""
    count = await model_manager.unload_all_models(db)
    return {"success": True, "message": f"Unloaded {count} models"}


@router.post("/import", response_model=ModelResponse, status_code=status.HTTP_201_CREATED)
async def import_local_model(
    request: ImportModelRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Import a local model with automatic format detection.
    
    Args:
        request: {path: str, name: str (optional), format: str (optional)}
    """
    try:
        path = request.path
        name = request.name
        
        # Validate path
        model_path = Path(path)
        if not model_path.exists():
            raise HTTPException(status_code=400, detail=f"Path does not exist: {path}")
        
        # Check if already imported
        result = await db.execute(select(DBModel).where(DBModel.path == str(model_path)))
        existing = result.scalar_one_or_none()
        if existing:
            raise HTTPException(status_code=400, detail="Model already imported")
        
        # Detect format
        detected_format = format_detector.detect_format(str(model_path))
        if not detected_format:
            raise HTTPException(
                status_code=400,
                detail="Could not detect model format. Supported formats: GGUF, SafeTensors, GPTQ, AWQ, EXL2, ONNX"
            )
        
        # Get detailed info
        model_info = format_detector.get_model_info(str(model_path))
        
        # Generate name if not provided
        if not name:
            name = model_path.name if model_path.is_file() else model_path.parts[-1]
        
        # Create model entry
        db_model = DBModel(
            name=name,
            path=str(model_path),
            format=detected_format,
            size=model_info.get("size_mb", 0),
            source="Local",
            model_metadata={
                "files": model_info.get("files", []),
                "config": model_info.get("config"),
                "detected_format": detected_format
            }
        )
        
        db.add(db_model)
        await db.commit()
        await db.refresh(db_model)
        
        logger.info(f"Imported local model: {name} (Format: {detected_format})")
        return ModelResponse.model_validate(db_model)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to import model: {str(e)}")
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/detect-format")
async def detect_model_format(request: DetectFormatRequest):
    """
    Detect the format of a model without importing it.
    
    Args:
        request: {path: str}
    """
    try:
        path = request.path
        model_path = Path(path)
        if not model_path.exists():
            raise HTTPException(status_code=400, detail=f"Path does not exist: {path}")
        
        detected_format = format_detector.detect_format(str(model_path))
        if not detected_format:
            raise HTTPException(
                status_code=400,
                detail="Could not detect model format"
            )
        
        model_info = format_detector.get_model_info(str(model_path))
        is_valid = format_detector.validate_model_path(str(model_path))
        
        return {
            "path": str(model_path),
            "format": detected_format,
            "size_mb": model_info.get("size_mb", 0),
            "valid": is_valid,
            "files": model_info.get("files", [])[:10],  # Limit to first 10 files
            "total_files": len(model_info.get("files", []))
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Format detection failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# Model Versioning Endpoints
@router.post("/{model_id}/versions")
async def create_model_version(
    model_id: int,
    version: str,
    notes: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """Create a new version tag for a model"""
    try:
        version_info = await model_versioning.create_version(
            db=db,
            model_id=model_id,
            version=version,
            notes=notes
        )
        return {"message": "Version created", "version": version_info}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{model_id}/versions")
async def list_model_versions(
    model_id: int,
    db: AsyncSession = Depends(get_db)
):
    """List all versions of a model"""
    versions = await model_versioning.list_versions(db=db, model_id=model_id)
    return {"model_id": model_id, "versions": versions}


# Model Comparison Endpoints
@router.post("/compare")
async def compare_models_endpoint(
    model_ids: List[int],
    db: AsyncSession = Depends(get_db)
):
    """Compare specifications of multiple models"""
    try:
        comparison = await model_comparison.compare_models(db=db, model_ids=model_ids)
        return comparison
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Model Benchmarking Endpoints
@router.post("/{model_id}/benchmark")
async def benchmark_model(
    model_id: int,
    num_prompts: int = 5,
    db: AsyncSession = Depends(get_db)
):
    """Run a benchmark on a model"""
    try:
        from app.services.model_manager import model_manager
        
        results = await model_benchmarking.run_benchmark(
            model_id=model_id,
            model_manager=model_manager,
            db=db,
            num_prompts=num_prompts
        )
        return results
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Benchmark failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# Model Tagging Endpoints
@router.post("/{model_id}/tags")
async def add_model_tags(
    model_id: int,
    tags: List[str],
    db: AsyncSession = Depends(get_db)
):
    """Add tags to a model"""
    try:
        updated_tags = await model_tagging.add_tags(db=db, model_id=model_id, tags=tags)
        return {"model_id": model_id, "tags": updated_tags}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{model_id}/category")
async def set_model_category(
    model_id: int,
    category: str,
    db: AsyncSession = Depends(get_db)
):
    """Set category for a model"""
    try:
        updated_category = await model_tagging.set_category(db=db, model_id=model_id, category=category)
        return {"model_id": model_id, "category": updated_category}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

