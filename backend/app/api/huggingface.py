"""
HuggingFace Hub API endpoints.
Browse and search models from HuggingFace.
"""

from fastapi import APIRouter, HTTPException, Query
from typing import List, Dict, Any, Optional

from app.services.huggingface_service import huggingface_service

router = APIRouter(prefix="/api/huggingface", tags=["huggingface"])


@router.get("/search", response_model=List[Dict[str, Any]])
async def search_models(
    query: Optional[str] = Query(None, description="Search query"),
    task: Optional[str] = Query(None, description="Task filter (e.g., 'text-generation')"),
    library: Optional[str] = Query(None, description="Library filter (e.g., 'transformers', 'gguf')"),
    language: Optional[str] = Query(None, description="Language filter"),
    limit: int = Query(20, ge=1, le=100, description="Maximum number of results"),
    sort: str = Query("downloads", description="Sort by (downloads, likes, updated)")
):
    """
    Search for models on HuggingFace Hub.
    """
    try:
        return huggingface_service.search_models(
            query=query,
            task=task,
            library=library,
            language=language,
            limit=limit,
            sort=sort
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# NOTE: More specific routes MUST come before generic {model_id:path} routes!
@router.get("/model/{model_id:path}/files", response_model=List[Dict[str, Any]])
async def list_model_files(model_id: str):
    """
    List files in a model repository.
    
    Args:
        model_id: HuggingFace model ID
    
    Returns:
        List of files with name, path, and size
    """
    try:
        return huggingface_service.list_model_files(model_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/model/{model_id:path}", response_model=Dict[str, Any])
async def get_model_info(model_id: str):
    """
    Get detailed information about a specific model.
    
    Args:
        model_id: HuggingFace model ID (e.g., "meta-llama/Llama-2-7b-hf")
    """
    try:
        return huggingface_service.get_model_info(model_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/popular", response_model=List[Dict[str, Any]])
async def get_popular_models(
    task: str = Query("text-generation", description="Task type"),
    limit: int = Query(10, ge=1, le=50, description="Maximum number of results")
):
    """Get popular models for a specific task"""
    try:
        return huggingface_service.get_popular_models(task=task, limit=limit)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/gguf", response_model=List[Dict[str, Any]])
async def get_gguf_models(
    query: Optional[str] = Query(None, description="Search query"),
    limit: int = Query(20, ge=1, le=100, description="Maximum number of results")
):
    """Get GGUF format models"""
    try:
        return huggingface_service.get_gguf_models(query=query, limit=limit)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/download-url/{model_id:path}/{filename:path}")
async def get_download_url(model_id: str, filename: str):
    """
    Get download URL for a specific file.
    
    Args:
        model_id: HuggingFace model ID
        filename: File name within the repository
    """
    try:
        url = huggingface_service.get_download_url(model_id, filename)
        return {"url": url}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

