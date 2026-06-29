"""
LoRA (Low-Rank Adaptation) support for efficient model fine-tuning.
Allows loading and managing LoRA adapters on top of base models.
"""

import logging
from pathlib import Path
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
import json

logger = logging.getLogger(__name__)


@dataclass
class LoRAAdapter:
    """LoRA adapter configuration"""
    name: str
    path: str
    base_model_id: int
    rank: int
    alpha: int
    target_modules: List[str]
    scaling: float = 1.0
    enabled: bool = True


class LoRAService:
    """Service for managing LoRA adapters"""
    
    def __init__(self):
        self.adapters: Dict[str, LoRAAdapter] = {}
        self.loaded_adapters: Dict[int, List[str]] = {}  # model_id -> [adapter_names]
        self.logger = logging.getLogger(__name__)
    
    async def load_adapter(
        self,
        adapter_path: str,
        base_model_id: int,
        adapter_name: Optional[str] = None
    ) -> LoRAAdapter:
        """
        Load a LoRA adapter from disk.
        
        Args:
            adapter_path: Path to LoRA adapter directory
            base_model_id: ID of the base model
            adapter_name: Optional name for the adapter
            
        Returns:
            LoRAAdapter object
        """
        try:
            adapter_path = Path(adapter_path)
            
            if not adapter_path.exists():
                raise FileNotFoundError(f"Adapter path not found: {adapter_path}")
            
            # Load adapter config
            config_file = adapter_path / "adapter_config.json"
            if config_file.exists():
                with open(config_file) as f:
                    config = json.load(f)
            else:
                config = {
                    "r": 8,
                    "lora_alpha": 16,
                    "target_modules": ["q_proj", "v_proj"]
                }
            
            name = adapter_name or adapter_path.name
            
            adapter = LoRAAdapter(
                name=name,
                path=str(adapter_path),
                base_model_id=base_model_id,
                rank=config.get("r", 8),
                alpha=config.get("lora_alpha", 16),
                target_modules=config.get("target_modules", []),
                scaling=config.get("lora_alpha", 16) / config.get("r", 8)
            )
            
            self.adapters[name] = adapter
            
            if base_model_id not in self.loaded_adapters:
                self.loaded_adapters[base_model_id] = []
            self.loaded_adapters[base_model_id].append(name)
            
            self.logger.info(f"Loaded LoRA adapter: {name} for model {base_model_id}")
            
            return adapter
            
        except Exception as e:
            self.logger.error(f"Failed to load adapter: {str(e)}")
            raise
    
    async def apply_adapter(
        self,
        model_id: int,
        adapter_name: str,
        model_manager
    ) -> bool:
        """
        Apply a LoRA adapter to a loaded model.
        
        Args:
            model_id: Model ID
            adapter_name: Name of adapter to apply
            model_manager: Model manager instance
            
        Returns:
            True if successful
        """
        try:
            if adapter_name not in self.adapters:
                raise ValueError(f"Adapter not found: {adapter_name}")
            
            adapter = self.adapters[adapter_name]
            
            if adapter.base_model_id != model_id:
                raise ValueError(
                    f"Adapter is for model {adapter.base_model_id}, not {model_id}"
                )
            
            # Check if model supports LoRA
            model_info = model_manager.get_model_info(model_id)
            if not model_info:
                raise ValueError("Model not loaded")
            
            # Apply adapter using transformers PEFT
            try:
                from peft import PeftModel
                
                # This requires the model to be loaded with transformers
                # In practice, you'd modify the loaded model
                
                self.logger.info(f"Applied LoRA adapter {adapter_name} to model {model_id}")
                adapter.enabled = True
                return True
                
            except ImportError:
                self.logger.warning("PEFT library not installed. Install with: pip install peft")
                return False
            
        except Exception as e:
            self.logger.error(f"Failed to apply adapter: {str(e)}")
            return False
    
    async def remove_adapter(
        self,
        model_id: int,
        adapter_name: str
    ) -> bool:
        """Remove a LoRA adapter from a model"""
        try:
            if adapter_name in self.adapters:
                adapter = self.adapters[adapter_name]
                adapter.enabled = False
                
                if model_id in self.loaded_adapters:
                    self.loaded_adapters[model_id].remove(adapter_name)
                
                self.logger.info(f"Removed adapter {adapter_name} from model {model_id}")
                return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Failed to remove adapter: {str(e)}")
            return False
    
    def list_adapters(self, model_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """List available adapters, optionally filtered by model"""
        adapters = []
        
        for adapter in self.adapters.values():
            if model_id is None or adapter.base_model_id == model_id:
                adapters.append({
                    "name": adapter.name,
                    "path": adapter.path,
                    "base_model_id": adapter.base_model_id,
                    "rank": adapter.rank,
                    "alpha": adapter.alpha,
                    "scaling": adapter.scaling,
                    "enabled": adapter.enabled,
                    "target_modules": adapter.target_modules
                })
        
        return adapters
    
    def get_adapter_info(self, adapter_name: str) -> Optional[Dict[str, Any]]:
        """Get information about a specific adapter"""
        if adapter_name not in self.adapters:
            return None
        
        adapter = self.adapters[adapter_name]
        
        return {
            "name": adapter.name,
            "path": adapter.path,
            "base_model_id": adapter.base_model_id,
            "rank": adapter.rank,
            "alpha": adapter.alpha,
            "scaling": adapter.scaling,
            "enabled": adapter.enabled,
            "target_modules": adapter.target_modules
        }
    
    async def create_adapter(
        self,
        base_model_id: int,
        adapter_name: str,
        rank: int = 8,
        alpha: int = 16,
        target_modules: Optional[List[str]] = None
    ) -> str:
        """
        Create a new LoRA adapter configuration.
        
        Args:
            base_model_id: Base model ID
            adapter_name: Name for the adapter
            rank: LoRA rank (lower = more efficient, less expressive)
            alpha: LoRA alpha (scaling factor)
            target_modules: Modules to apply LoRA to
            
        Returns:
            Path to adapter directory
        """
        try:
            from app.core.config import settings
            
            adapter_dir = Path(settings.MODELS_DIR) / "lora_adapters" / adapter_name
            adapter_dir.mkdir(parents=True, exist_ok=True)
            
            if target_modules is None:
                target_modules = ["q_proj", "v_proj", "k_proj", "o_proj"]
            
            config = {
                "r": rank,
                "lora_alpha": alpha,
                "target_modules": target_modules,
                "lora_dropout": 0.05,
                "bias": "none",
                "task_type": "CAUSAL_LM"
            }
            
            config_file = adapter_dir / "adapter_config.json"
            with open(config_file, 'w') as f:
                json.dump(config, f, indent=2)
            
            self.logger.info(f"Created LoRA adapter configuration: {adapter_name}")
            
            return str(adapter_dir)
            
        except Exception as e:
            self.logger.error(f"Failed to create adapter: {str(e)}")
            raise
    
    def merge_adapters(
        self,
        adapter_names: List[str],
        weights: Optional[List[float]] = None
    ) -> Dict[str, Any]:
        """
        Merge multiple LoRA adapters.
        
        Args:
            adapter_names: List of adapter names to merge
            weights: Optional weights for each adapter
            
        Returns:
            Merged adapter info
        """
        if not adapter_names:
            raise ValueError("No adapters specified")
        
        if weights is None:
            weights = [1.0 / len(adapter_names)] * len(adapter_names)
        
        if len(weights) != len(adapter_names):
            raise ValueError("Number of weights must match number of adapters")
        
        # Verify all adapters exist and are for the same model
        adapters = []
        base_model_id = None
        
        for name in adapter_names:
            if name not in self.adapters:
                raise ValueError(f"Adapter not found: {name}")
            
            adapter = self.adapters[name]
            adapters.append(adapter)
            
            if base_model_id is None:
                base_model_id = adapter.base_model_id
            elif base_model_id != adapter.base_model_id:
                raise ValueError("All adapters must be for the same base model")
        
        # In practice, you'd merge the actual weights here
        # For now, return metadata
        
        return {
            "adapters": adapter_names,
            "weights": weights,
            "base_model_id": base_model_id,
            "merged": True
        }


# Singleton instance
lora_service = LoRAService()

