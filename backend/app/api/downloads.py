from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional
import logging
from pathlib import Path

from app.database.database import get_db
from app.database.models import DownloadQueue as DBDownloadQueue
from app.schemas.download import (
    DownloadRequest,
    DownloadResponse,
    DownloadListResponse,
    DownloadStatusResponse
)
from app.services.download_queue import download_manager
from app.core.config import settings

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/", response_model=DownloadResponse, status_code=status.HTTP_201_CREATED)
async def start_download(
    request: DownloadRequest,
    db: AsyncSession = Depends(get_db)
):
    """Start a new download"""
    try:
        # Determine destination path
        filename = Path(request.url).name
        if not filename:
            filename = f"{request.model_name}.gguf"
        
        destination = str(settings.MODELS_DIR / filename)
        
        # Add to queue
        download_id = await download_manager.add_to_queue(
            url=request.url,
            destination=destination,
            model_name=request.model_name,
            model_format=request.model_format,
            priority=request.priority,
            metadata=request.metadata,
            db=db
        )
        
        # Get download entry
        result = await db.execute(
            select(DBDownloadQueue).where(DBDownloadQueue.id == download_id)
        )
        download = result.scalar_one()
        
        return DownloadResponse.model_validate(download)
        
    except Exception as e:
        logger.error(f"Failed to start download: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/", response_model=DownloadListResponse)
async def list_downloads(
    status_filter: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db)
):
    """List all downloads"""
    query = select(DBDownloadQueue)
    
    if status_filter:
        query = query.where(DBDownloadQueue.status == status_filter)
    
    query = query.offset(skip).limit(limit).order_by(DBDownloadQueue.created_at.desc())
    
    result = await db.execute(query)
    downloads = result.scalars().all()
    
    # Get total count
    total_result = await db.execute(select(DBDownloadQueue))
    total = len(total_result.scalars().all())
    
    return DownloadListResponse(
        downloads=[DownloadResponse.model_validate(d) for d in downloads],
        total=total
    )


@router.get("/{download_id}", response_model=DownloadStatusResponse)
async def get_download_status(
    download_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get download status"""
    status_data = await download_manager.get_download_status(download_id, db)
    
    if not status_data:
        raise HTTPException(status_code=404, detail="Download not found")
    
    return DownloadStatusResponse(**status_data)


@router.post("/{download_id}/cancel")
async def cancel_download(
    download_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Cancel a download"""
    success = await download_manager.cancel_download(download_id, db)
    
    if success:
        return {"success": True, "message": "Download cancelled"}
    else:
        raise HTTPException(status_code=500, detail="Failed to cancel download")


@router.get("/active/list")
async def list_active_downloads():
    """Get list of currently active downloads"""
    active_ids = download_manager.get_active_downloads()
    
    return {
        "active_downloads": active_ids,
        "count": len(active_ids)
    }

