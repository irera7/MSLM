"""
Cache management API endpoints.
"""

from fastapi import APIRouter, HTTPException
from typing import Dict, Any

from app.services.cache_service import cache_service

router = APIRouter(prefix="/api/cache", tags=["cache"])


@router.get("/stats", response_model=Dict[str, Any])
async def get_cache_stats():
    """Get cache statistics"""
    try:
        return cache_service.get_stats()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/clear")
async def clear_cache():
    """Clear all cache entries"""
    try:
        cache_service.clear()
        return {"message": "Cache cleared successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/model/{model_id}")
async def invalidate_model_cache(model_id: int):
    """
    Invalidate cache entries for a specific model.
    
    Args:
        model_id: Model ID
    """
    try:
        count = cache_service.invalidate_model(model_id)
        return {
            "message": f"Invalidated {count} cache entries",
            "count": count
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/cleanup")
async def cleanup_expired():
    """Remove expired cache entries"""
    try:
        count = cache_service.cleanup_expired()
        return {
            "message": f"Removed {count} expired entries",
            "count": count
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

