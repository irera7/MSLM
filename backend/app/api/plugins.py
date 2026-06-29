"""
Plugin management API endpoints.
"""

from fastapi import APIRouter, HTTPException, UploadFile, File
from typing import List, Dict, Any
from pydantic import BaseModel

from app.services.plugin_manager import plugin_manager

router = APIRouter(prefix="/api/plugins", tags=["plugins"])


class PluginLoadRequest(BaseModel):
    path: str


@router.get("/", response_model=List[Dict[str, Any]])
async def list_plugins():
    """List all loaded plugins"""
    try:
        return plugin_manager.list_plugins()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{plugin_name}", response_model=Dict[str, Any])
async def get_plugin_info(plugin_name: str):
    """
    Get information about a specific plugin.
    
    Args:
        plugin_name: Name of the plugin
    """
    try:
        plugin_info = plugin_manager.get_plugin_info(plugin_name)
        
        if plugin_info is None:
            raise HTTPException(status_code=404, detail=f"Plugin not found: {plugin_name}")
        
        return {
            "name": plugin_info.name,
            "version": plugin_info.version,
            "author": plugin_info.author,
            "description": plugin_info.description,
            "supported_formats": plugin_info.supported_formats
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/load")
async def load_plugin(request: PluginLoadRequest):
    """
    Load a plugin from a directory.
    
    Args:
        request: Plugin load request with path
    """
    try:
        success = plugin_manager.load_plugin(request.path)
        
        if not success:
            raise HTTPException(status_code=400, detail="Failed to load plugin")
        
        return {"message": f"Plugin loaded successfully from {request.path}"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/reload")
async def reload_all_plugins():
    """Reload all plugins from the plugin directory"""
    try:
        count = plugin_manager.load_all_plugins()
        return {
            "message": f"Loaded {count} plugin(s)",
            "count": count
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{plugin_name}")
async def unload_plugin(plugin_name: str):
    """
    Unload a plugin.
    
    Args:
        plugin_name: Name of the plugin
    """
    try:
        success = plugin_manager.unload_plugin(plugin_name)
        
        if not success:
            raise HTTPException(status_code=404, detail=f"Plugin not found: {plugin_name}")
        
        return {"message": f"Plugin {plugin_name} unloaded successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

