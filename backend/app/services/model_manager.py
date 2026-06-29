from typing import Dict, Optional, List
import logging
from pathlib import Path
import asyncio
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update

from app.database.models import Model as DBModel, UsageStats
from app.services.inference.base_engine import InferenceEngine, EngineRegistry, GenerationConfig, ModelInfo
from app.core.config import settings

logger = logging.getLogger(__name__)


class ModelManager:
    """
    Manages loading, unloading, and tracking of models.
    Supports multiple models loaded simultaneously (up to MAX_CONCURRENT_MODELS).
    """
    
    def __init__(self):
        self.loaded_models: Dict[int, InferenceEngine] = {}
        self.lock = asyncio.Lock()
        self.max_concurrent = settings.MAX_CONCURRENT_MODELS
        self.logger = logging.getLogger(__name__)
    
    async def load_model(
        self,
        model_id: int,
        model_path: str,
        format: str,
        db: AsyncSession,
        gpu_layers: int = 0,
        context_length: int = 2048,
        **kwargs
    ) -> ModelInfo:
        """
        Load a model into memory.
        
        Args:
            model_id: Database model ID
            model_path: Path to model file/directory
            format: Model format (GGUF, SafeTensors, etc.)
            db: Database session
            gpu_layers: Number of GPU layers
            context_length: Context length
            **kwargs: Additional engine-specific parameters
            
        Returns:
            ModelInfo: Information about loaded model
            
        Raises:
            ValueError: If model format not supported or too many models loaded
            RuntimeError: If model loading fails
        """
        async with self.lock:
            # Check if already loaded
            if model_id in self.loaded_models:
                self.logger.info(f"Model {model_id} is already loaded")
                return self.loaded_models[model_id].get_model_info()
            
            # Check concurrent model limit
            if len(self.loaded_models) >= self.max_concurrent:
                raise ValueError(
                    f"Maximum concurrent models ({self.max_concurrent}) reached. "
                    "Unload a model first."
                )
            
            # Get appropriate engine for format
            engine_class = EngineRegistry.get_engine_for_format(format)
            if not engine_class:
                raise ValueError(f"No engine found for format: {format}")
            
            # Create engine instance
            engine = engine_class(model_id=model_id, model_path=model_path)
            
            try:
                # Load the model
                self.logger.info(f"Loading model {model_id} with {engine_class.get_engine_name()}")
                model_info = engine.load(
                    gpu_layers=gpu_layers,
                    context_length=context_length,
                    **kwargs
                )
                
                # Store loaded engine
                self.loaded_models[model_id] = engine
                
                # Update database
                await db.execute(
                    update(DBModel)
                    .where(DBModel.id == model_id)
                    .values(is_loaded=True, updated_at=datetime.utcnow())
                )
                await db.commit()
                
                self.logger.info(f"Model {model_id} loaded successfully")
                return model_info
                
            except Exception as e:
                self.logger.error(f"Failed to load model {model_id}: {str(e)}")
                # Clean up on failure
                if model_id in self.loaded_models:
                    del self.loaded_models[model_id]
                raise RuntimeError(f"Failed to load model: {str(e)}")
    
    async def unload_model(self, model_id: int, db: AsyncSession) -> bool:
        """
        Unload a model from memory.
        
        Args:
            model_id: Database model ID
            db: Database session
            
        Returns:
            bool: True if successful, False otherwise
        """
        async with self.lock:
            if model_id not in self.loaded_models:
                self.logger.warning(f"Model {model_id} is not loaded")
                return False
            
            try:
                engine = self.loaded_models[model_id]
                success = engine.unload()
                
                if success:
                    del self.loaded_models[model_id]
                    
                    # Update database
                    await db.execute(
                        update(DBModel)
                        .where(DBModel.id == model_id)
                        .values(is_loaded=False, updated_at=datetime.utcnow())
                    )
                    await db.commit()
                    
                    self.logger.info(f"Model {model_id} unloaded successfully")
                    return True
                
                return False
                
            except Exception as e:
                self.logger.error(f"Failed to unload model {model_id}: {str(e)}")
                return False
    
    async def unload_all_models(self, db: AsyncSession) -> int:
        """Unload all loaded models"""
        count = 0
        model_ids = list(self.loaded_models.keys())
        
        for model_id in model_ids:
            if await self.unload_model(model_id, db):
                count += 1
        
        return count
    
    def get_loaded_model(self, model_id: int) -> Optional[InferenceEngine]:
        """Get a loaded model engine"""
        return self.loaded_models.get(model_id)
    
    def is_model_loaded(self, model_id: int) -> bool:
        """Check if a model is loaded"""
        return model_id in self.loaded_models
    
    def get_loaded_models_info(self) -> List[ModelInfo]:
        """Get information about all loaded models"""
        return [
            engine.get_model_info()
            for engine in self.loaded_models.values()
            if engine.get_model_info() is not None
        ]
    
    def get_loaded_model_ids(self) -> List[int]:
        """Get list of loaded model IDs"""
        return list(self.loaded_models.keys())
    
    async def generate_text_streaming(
        self,
        model_id: int,
        prompt: str,
        config: GenerationConfig,
        db: AsyncSession,
        **kwargs
    ):
        """
        Generate text using a loaded model (streaming).
        
        Args:
            model_id: Database model ID
            prompt: Input prompt
            config: Generation configuration
            db: Database session
            **kwargs: Additional generation parameters
            
        Yields:
            str: Generated tokens
        """
        engine = self.get_loaded_model(model_id)
        if not engine:
            raise RuntimeError(f"Model {model_id} is not loaded")
        
        start_time = datetime.utcnow()
        generated_text = ""
        
        try:
            for token in engine.generate(prompt, config, **kwargs):
                generated_text += token
                yield token
            
            # Record usage stats
            duration = (datetime.utcnow() - start_time).total_seconds()
            tokens = engine.count_tokens(generated_text)
            await self._record_usage(model_id, tokens, duration, db)
                
        except Exception as e:
            self.logger.error(f"Generation failed for model {model_id}: {str(e)}")
            raise
    
    async def generate_text_non_streaming(
        self,
        model_id: int,
        prompt: str,
        config: GenerationConfig,
        db: AsyncSession,
        **kwargs
    ) -> str:
        """
        Generate text using a loaded model (non-streaming).
        
        Args:
            model_id: Database model ID
            prompt: Input prompt
            config: Generation configuration
            db: Database session
            **kwargs: Additional generation parameters
            
        Returns:
            str: Complete generated text
        """
        engine = self.get_loaded_model(model_id)
        if not engine:
            raise RuntimeError(f"Model {model_id} is not loaded")
        
        start_time = datetime.utcnow()
        
        try:
            # Non-streaming generation
            generated_text = engine.generate_non_streaming(prompt, config, **kwargs)
            
            # Record usage stats
            duration = (datetime.utcnow() - start_time).total_seconds()
            tokens = engine.count_tokens(generated_text)
            await self._record_usage(model_id, tokens, duration, db)
            
            return generated_text
                
        except Exception as e:
            self.logger.error(f"Generation failed for model {model_id}: {str(e)}")
            raise
    
    async def _record_usage(
        self,
        model_id: int,
        tokens: int,
        duration: float,
        db: AsyncSession
    ):
        """Record usage statistics"""
        try:
            usage_stat = UsageStats(
                model_id=model_id,
                tokens=tokens,
                duration=duration,
                timestamp=datetime.utcnow()
            )
            db.add(usage_stat)
            await db.commit()
        except Exception as e:
            self.logger.error(f"Failed to record usage stats: {str(e)}")
    
    def get_memory_usage(self) -> Dict[int, float]:
        """Get memory usage for all loaded models"""
        return {
            model_id: engine.get_memory_usage()
            for model_id, engine in self.loaded_models.items()
        }
    
    def get_total_memory_usage(self) -> float:
        """Get total memory usage of all loaded models"""
        return sum(self.get_memory_usage().values())


# Global model manager instance
model_manager = ModelManager()

