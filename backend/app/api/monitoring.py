"""
Monitoring API endpoints.
Provides system metrics and performance monitoring.
"""

from fastapi import APIRouter, HTTPException
from typing import Dict, Any, List

from app.services.monitoring_service import monitoring_service

router = APIRouter(prefix="/api/monitoring", tags=["monitoring"])


@router.get("/system", response_model=Dict[str, Any])
async def get_system_info():
    """Get static system information"""
    try:
        return monitoring_service.get_system_info()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/metrics", response_model=Dict[str, Any])
async def get_current_metrics():
    """Get current system metrics"""
    try:
        return monitoring_service.get_current_metrics()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/metrics/history", response_model=List[Dict[str, Any]])
async def get_metrics_history(limit: int = 50):
    """
    Get metrics history.
    
    Args:
        limit: Maximum number of entries to return (default: 50)
    """
    try:
        return monitoring_service.get_metrics_history(limit=limit)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/process", response_model=Dict[str, Any])
async def get_process_metrics():
    """Get metrics for the current process"""
    try:
        return monitoring_service.get_process_metrics()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/metrics/history")
async def clear_metrics_history():
    """Clear metrics history"""
    try:
        monitoring_service.clear_history()
        return {"message": "Metrics history cleared"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/gpu", response_model=List[Dict[str, Any]])
async def get_gpu_info():
    """Get GPU information"""
    try:
        system_info = monitoring_service.get_system_info()
        if not system_info.get("gpu_available"):
            raise HTTPException(status_code=404, detail="No GPU available")
        
        return system_info.get("gpus", [])
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

