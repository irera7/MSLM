"""
HuggingFace Hub integration service.
Search, browse, and download models from HuggingFace.
"""

import logging
from typing import List, Dict, Any, Optional
from huggingface_hub import HfApi, hf_hub_download, snapshot_download, list_models
from huggingface_hub.utils import RepositoryNotFoundError

logger = logging.getLogger(__name__)


class HuggingFaceService:
    """Service for interacting with HuggingFace Hub"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.api = HfApi()
    
    def search_models(
        self,
        query: Optional[str] = None,
        task: Optional[str] = None,
        library: Optional[str] = None,
        language: Optional[str] = None,
        limit: int = 20,
        sort: str = "downloads"
    ) -> List[Dict[str, Any]]:
        """
        Search for models on HuggingFace Hub.
        
        Args:
            query: Search query
            task: Task filter (e.g., "text-generation")
            library: Library filter (e.g., "transformers", "gguf")
            language: Language filter
            limit: Maximum number of results
            sort: Sort by ("downloads", "likes", "updated")
            
        Returns:
            List of model information dictionaries
        """
        try:
            self.logger.info(f"Searching HuggingFace Hub: query='{query}', task='{task}', library='{library}'")
            
            # Build filter arguments
            filter_args = {}
            if task:
                filter_args["task"] = task
            if library:
                filter_args["library"] = library
            if language:
                filter_args["language"] = language
            
            # Search models
            models = list_models(
                search=query,
                filter=filter_args if filter_args else None,
                sort=sort,
                direction=-1,  # Descending
                limit=limit
            )
            
            results = []
            for model in models:
                try:
                    model_info = {
                        "id": model.modelId,
                        "name": model.modelId.split("/")[-1] if "/" in model.modelId else model.modelId,
                        "author": model.author if hasattr(model, "author") else model.modelId.split("/")[0] if "/" in model.modelId else "unknown",
                        "downloads": model.downloads if hasattr(model, "downloads") else 0,
                        "likes": model.likes if hasattr(model, "likes") else 0,
                        "tags": model.tags if hasattr(model, "tags") else [],
                        "pipeline_tag": model.pipeline_tag if hasattr(model, "pipeline_tag") else None,
                        "library_name": model.library_name if hasattr(model, "library_name") else None,
                        "created_at": model.created_at.isoformat() if hasattr(model, "created_at") and model.created_at else None,
                        "last_modified": model.last_modified.isoformat() if hasattr(model, "last_modified") and model.last_modified else None,
                    }
                    results.append(model_info)
                except Exception as e:
                    self.logger.warning(f"Failed to parse model info: {str(e)}")
                    continue
            
            self.logger.info(f"Found {len(results)} models")
            return results
            
        except Exception as e:
            self.logger.error(f"Search failed: {str(e)}")
            raise
    
    def get_model_info(self, model_id: str) -> Dict[str, Any]:
        """
        Get detailed information about a model.
        
        Args:
            model_id: HuggingFace model ID (e.g., "meta-llama/Llama-2-7b-hf")
            
        Returns:
            Dict with model information
        """
        try:
            self.logger.info(f"Getting model info: {model_id}")
            
            model_info = self.api.model_info(model_id)
            
            # Get file list
            files = []
            try:
                file_list = self.api.list_repo_files(model_id)
                for file_path in file_list:
                    files.append({
                        "path": file_path,
                        "size": None  # Size info would require additional API calls
                    })
            except:
                pass
            
            return {
                "id": model_info.modelId,
                "name": model_info.modelId.split("/")[-1] if "/" in model_info.modelId else model_info.modelId,
                "author": model_info.author if hasattr(model_info, "author") else model_info.modelId.split("/")[0] if "/" in model_info.modelId else "unknown",
                "downloads": model_info.downloads if hasattr(model_info, "downloads") else 0,
                "likes": model_info.likes if hasattr(model_info, "likes") else 0,
                "tags": model_info.tags if hasattr(model_info, "tags") else [],
                "pipeline_tag": model_info.pipeline_tag if hasattr(model_info, "pipeline_tag") else None,
                "library_name": model_info.library_name if hasattr(model_info, "library_name") else None,
                "created_at": model_info.created_at.isoformat() if hasattr(model_info, "created_at") and model_info.created_at else None,
                "last_modified": model_info.last_modified.isoformat() if hasattr(model_info, "last_modified") and model_info.last_modified else None,
                "files": files,
                "card_data": model_info.card_data if hasattr(model_info, "card_data") else None,
            }
            
        except RepositoryNotFoundError:
            raise ValueError(f"Model not found: {model_id}")
        except Exception as e:
            self.logger.error(f"Failed to get model info: {str(e)}")
            raise
    
    def list_model_files(self, model_id: str) -> List[Dict[str, Any]]:
        """
        List files in a model repository.
        
        Args:
            model_id: HuggingFace model ID
            
        Returns:
            List of file information with name, size, and path
        """
        try:
            self.logger.info(f"Listing files for model: {model_id}")
            
            # Get model info which includes file details
            model_info = self.api.model_info(model_id, files_metadata=True)
            
            files = []
            if hasattr(model_info, 'siblings') and model_info.siblings:
                for file_info in model_info.siblings:
                    files.append({
                        "name": file_info.rfilename if hasattr(file_info, 'rfilename') else "",
                        "path": file_info.rfilename if hasattr(file_info, 'rfilename') else "",
                        "size": file_info.size if hasattr(file_info, 'size') else 0
                    })
            else:
                # Fallback: just list file paths without size
                file_list = self.api.list_repo_files(model_id)
                for file_path in file_list:
                    files.append({
                        "name": file_path,
                        "path": file_path,
                        "size": 0
                    })
            
            self.logger.info(f"Found {len(files)} files in {model_id}")
            return files
            
        except Exception as e:
            self.logger.error(f"Failed to list files: {str(e)}")
            raise
    
    def get_download_url(self, model_id: str, filename: str) -> str:
        """
        Get direct download URL for a model file.
        
        Args:
            model_id: HuggingFace model ID
            filename: File name within the repository
            
        Returns:
            str: Download URL
        """
        try:
            url = f"https://huggingface.co/{model_id}/resolve/main/{filename}"
            return url
        except Exception as e:
            self.logger.error(f"Failed to get download URL: {str(e)}")
            raise
    
    def get_popular_models(
        self,
        task: str = "text-generation",
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Get popular models for a specific task.
        
        Args:
            task: Task type (default: "text-generation")
            limit: Maximum number of results
            
        Returns:
            List of model information
        """
        return self.search_models(
            task=task,
            limit=limit,
            sort="downloads"
        )
    
    def get_gguf_models(
        self,
        query: Optional[str] = None,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Get GGUF format models.
        
        Args:
            query: Search query
            limit: Maximum number of results
            
        Returns:
            List of GGUF model information
        """
        return self.search_models(
            query=query,
            library="gguf",
            limit=limit
        )


# Singleton instance
huggingface_service = HuggingFaceService()

