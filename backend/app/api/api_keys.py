"""
API Key management endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from pydantic import BaseModel

from app.database.database import get_db
from app.services.api_key_service import api_key_service

router = APIRouter(prefix="/api/keys", tags=["api-keys"])


class APIKeyCreate(BaseModel):
    name: str
    rate_limit: Optional[int] = None  # requests per minute


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_api_key(
    request: APIKeyCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new API key.
    
    Args:
        name: Key name/description
        rate_limit: Optional rate limit (requests per minute)
    
    Returns:
        API key info including the plain key (only shown once!)
    """
    try:
        key_info = await api_key_service.create_key(
            db=db,
            name=request.name,
            rate_limit=request.rate_limit
        )
        
        return key_info
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/")
async def list_api_keys(
    include_inactive: bool = False,
    db: AsyncSession = Depends(get_db)
):
    """
    List all API keys (without showing actual keys).
    
    Args:
        include_inactive: Include revoked keys
    """
    try:
        keys = await api_key_service.list_keys(
            db=db,
            include_inactive=include_inactive
        )
        
        return {
            "keys": keys,
            "count": len(keys)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{key_id}")
async def revoke_api_key(
    key_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Revoke (deactivate) an API key.
    
    Args:
        key_id: API key ID
    """
    try:
        success = await api_key_service.revoke_key(db=db, key_id=key_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="API key not found")
        
        return {
            "message": f"API key {key_id} revoked successfully",
            "key_id": key_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{key_id}/usage")
async def get_key_usage(
    key_id: int,
    days: int = 7,
    db: AsyncSession = Depends(get_db)
):
    """
    Get usage statistics for an API key.
    
    Args:
        key_id: API key ID
        days: Number of days to look back (default: 7)
    """
    try:
        stats = await api_key_service.get_key_usage_stats(
            db=db,
            key_id=key_id,
            days=days
        )
        
        if not stats:
            raise HTTPException(status_code=404, detail="API key not found")
        
        return stats
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

