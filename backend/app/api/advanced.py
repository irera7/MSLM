"""
Advanced features API endpoints:
- LoRA adapters
- Multi-modal (vision, audio)
- Dataset management
"""

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from typing import Optional, List
import base64

from app.database.database import get_db
from app.services.lora_service import lora_service
from app.services.multimodal_service import multimodal_service, ModalityType
from app.services.dataset_service import dataset_service, DatasetFormat, DatasetType

router = APIRouter(prefix="/api/advanced", tags=["advanced"])


# ==================== LoRA Endpoints ====================

class LoadAdapterRequest(BaseModel):
    adapter_path: str
    base_model_id: int
    adapter_name: Optional[str] = None


class CreateAdapterRequest(BaseModel):
    base_model_id: int
    adapter_name: str
    rank: int = 8
    alpha: int = 16
    target_modules: Optional[List[str]] = None


@router.post("/lora/load")
async def load_lora_adapter(request: LoadAdapterRequest):
    """Load a LoRA adapter from disk"""
    try:
        adapter = await lora_service.load_adapter(
            adapter_path=request.adapter_path,
            base_model_id=request.base_model_id,
            adapter_name=request.adapter_name
        )
        
        return {
            "message": "Adapter loaded successfully",
            "adapter": {
                "name": adapter.name,
                "path": adapter.path,
                "rank": adapter.rank,
                "alpha": adapter.alpha
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/lora/create")
async def create_lora_adapter(request: CreateAdapterRequest):
    """Create a new LoRA adapter configuration"""
    try:
        adapter_path = await lora_service.create_adapter(
            base_model_id=request.base_model_id,
            adapter_name=request.adapter_name,
            rank=request.rank,
            alpha=request.alpha,
            target_modules=request.target_modules
        )
        
        return {
            "message": "Adapter configuration created",
            "path": adapter_path
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/lora/list")
async def list_lora_adapters(model_id: Optional[int] = None):
    """List available LoRA adapters"""
    adapters = lora_service.list_adapters(model_id=model_id)
    return {"adapters": adapters, "count": len(adapters)}


@router.get("/lora/{adapter_name}")
async def get_lora_adapter_info(adapter_name: str):
    """Get information about a specific adapter"""
    adapter_info = lora_service.get_adapter_info(adapter_name)
    
    if not adapter_info:
        raise HTTPException(status_code=404, detail="Adapter not found")
    
    return adapter_info


@router.post("/lora/{adapter_name}/apply")
async def apply_lora_adapter(
    adapter_name: str,
    model_id: int
):
    """Apply a LoRA adapter to a loaded model"""
    try:
        from app.services.model_manager import model_manager
        
        success = await lora_service.apply_adapter(
            model_id=model_id,
            adapter_name=adapter_name,
            model_manager=model_manager
        )
        
        if success:
            return {"message": f"Adapter {adapter_name} applied to model {model_id}"}
        else:
            raise HTTPException(status_code=500, detail="Failed to apply adapter")
            
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== Multi-Modal Endpoints ====================

class VisionRequest(BaseModel):
    model_id: int
    prompt: str
    image_path: Optional[str] = None
    image_base64: Optional[str] = None
    image_url: Optional[str] = None


class AudioRequest(BaseModel):
    model_id: int
    audio_path: Optional[str] = None
    audio_base64: Optional[str] = None


@router.post("/multimodal/vision/generate")
async def generate_with_vision(
    request: VisionRequest,
    db: AsyncSession = Depends(get_db)
):
    """Generate text response with vision input"""
    try:
        # Process image
        image_data = await multimodal_service.process_image(
            image_path=request.image_path,
            image_base64=request.image_base64,
            image_url=request.image_url
        )
        
        # Generate response
        from app.services.model_manager import model_manager
        
        response = await multimodal_service.generate_with_vision(
            model_id=request.model_id,
            prompt=request.prompt,
            image_data=image_data,
            model_manager=model_manager,
            db=db
        )
        
        return {
            "response": response,
            "image_info": image_data
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/multimodal/audio/transcribe")
async def transcribe_audio(
    request: AudioRequest,
    db: AsyncSession = Depends(get_db)
):
    """Transcribe audio to text"""
    try:
        # Process audio
        audio_data = await multimodal_service.process_audio(
            audio_path=request.audio_path,
            audio_base64=request.audio_base64
        )
        
        # Transcribe
        from app.services.model_manager import model_manager
        
        transcription = await multimodal_service.transcribe_audio(
            model_id=request.model_id,
            audio_data=audio_data,
            model_manager=model_manager,
            db=db
        )
        
        return transcription
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/multimodal/capabilities/{model_id}")
async def get_model_capabilities(
    model_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Check what modalities a model supports"""
    try:
        capabilities = await multimodal_service.check_model_capabilities(
            model_id=model_id,
            db=db
        )
        return capabilities
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/multimodal/formats")
async def get_supported_formats():
    """Get supported image and audio formats"""
    return {
        "image": multimodal_service.get_supported_image_formats(),
        "audio": multimodal_service.get_supported_audio_formats()
    }


# ==================== Dataset Endpoints ====================

class CreateDatasetRequest(BaseModel):
    name: str
    dataset_type: DatasetType
    description: Optional[str] = None


class LoadDatasetRequest(BaseModel):
    path: str
    format: DatasetFormat
    name: Optional[str] = None


class AddSamplesRequest(BaseModel):
    dataset_name: str
    samples: List[dict]


@router.post("/datasets/")
async def create_dataset(request: CreateDatasetRequest):
    """Create a new dataset"""
    try:
        dataset_info = await dataset_service.create_dataset(
            name=request.name,
            dataset_type=request.dataset_type,
            description=request.description
        )
        return dataset_info
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/datasets/load")
async def load_dataset(request: LoadDatasetRequest):
    """Load an existing dataset from file"""
    try:
        dataset_info = await dataset_service.load_dataset(
            path=request.path,
            format=request.format,
            name=request.name
        )
        return dataset_info
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/datasets/")
async def list_datasets():
    """List all datasets"""
    datasets = dataset_service.list_datasets()
    return {"datasets": datasets, "count": len(datasets)}


@router.get("/datasets/{dataset_name}")
async def get_dataset_info(dataset_name: str):
    """Get information about a dataset"""
    dataset_info = dataset_service.get_dataset_info(dataset_name)
    
    if not dataset_info:
        raise HTTPException(status_code=404, detail="Dataset not found")
    
    return dataset_info


@router.post("/datasets/samples/add")
async def add_samples(request: AddSamplesRequest):
    """Add samples to a dataset"""
    try:
        dataset_info = await dataset_service.add_samples(
            dataset_name=request.dataset_name,
            samples=request.samples
        )
        return dataset_info
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/datasets/{dataset_name}/samples")
async def get_samples(
    dataset_name: str,
    limit: int = 100,
    offset: int = 0
):
    """Get samples from a dataset"""
    try:
        samples = await dataset_service.get_samples(
            dataset_name=dataset_name,
            limit=limit,
            offset=offset
        )
        return {"samples": samples, "count": len(samples)}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/datasets/{dataset_name}/split")
async def split_dataset(
    dataset_name: str,
    train_ratio: float = 0.8,
    val_ratio: float = 0.1,
    test_ratio: float = 0.1
):
    """Split dataset into train/val/test sets"""
    try:
        split_info = await dataset_service.split_dataset(
            dataset_name=dataset_name,
            train_ratio=train_ratio,
            val_ratio=val_ratio,
            test_ratio=test_ratio
        )
        return split_info
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/datasets/{dataset_name}")
async def delete_dataset(dataset_name: str):
    """Delete a dataset"""
    success = await dataset_service.delete_dataset(dataset_name)
    
    if not success:
        raise HTTPException(status_code=404, detail="Dataset not found")
    
    return {"message": f"Dataset {dataset_name} deleted successfully"}


@router.post("/datasets/{dataset_name}/export")
async def export_dataset(
    dataset_name: str,
    output_path: str,
    format: DatasetFormat
):
    """Export dataset to a specific format"""
    try:
        exported_path = await dataset_service.export_dataset(
            dataset_name=dataset_name,
            output_path=output_path,
            format=format
        )
        return {
            "message": "Dataset exported successfully",
            "path": exported_path
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

