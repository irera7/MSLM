from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime


class ModelBase(BaseModel):
    name: str
    path: str
    format: str
    size: Optional[float] = None
    source: str
    source_url: Optional[str] = None
    quantization: Optional[str] = None
    parameters: Optional[str] = None
    model_metadata: Optional[Dict[str, Any]] = None


class ModelCreate(ModelBase):
    pass


class ModelUpdate(BaseModel):
    name: Optional[str] = None
    model_metadata: Optional[Dict[str, Any]] = None


class ModelResponse(ModelBase):
    id: int
    is_loaded: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class ModelListResponse(BaseModel):
    models: list[ModelResponse]
    total: int


class ModelLoadRequest(BaseModel):
    model_id: int
    gpu_layers: Optional[int] = None
    context_length: Optional[int] = None
    

class ModelLoadResponse(BaseModel):
    success: bool
    message: str
    model_id: int

