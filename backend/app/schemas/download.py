from pydantic import BaseModel, HttpUrl
from typing import Optional, Dict, Any
from datetime import datetime


class DownloadRequest(BaseModel):
    url: str
    model_name: str
    model_format: Optional[str] = None
    priority: int = 0
    metadata: Optional[Dict[str, Any]] = None


class DownloadResponse(BaseModel):
    id: int
    url: str
    status: str
    progress: float
    model_name: str
    total_size: Optional[float] = None
    downloaded_size: float
    error_message: Optional[str] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


class DownloadListResponse(BaseModel):
    downloads: list[DownloadResponse]
    total: int


class DownloadStatusResponse(BaseModel):
    id: int
    status: str
    progress: float
    error_message: Optional[str] = None

