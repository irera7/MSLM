from typing import Generator, Optional
import logging
from pathlib import Path

from app.services.inference.base_engine import (
    InferenceEngine,
    GenerationConfig,
    ModelInfo,
    EngineRegistry
)

logger = logging.getLogger(__name__)


@EngineRegistry.register
class GGUFEngine(InferenceEngine):
    """
    Inference engine for GGUF format models using llama-cpp-python.
    Supports CPU and GPU (CUDA/Metal) acceleration.
    """
    
    def __init__(self, model_id: int, model_path: str):
        super().__init__(model_id, model_path)
        self.llama_model = None
    
    def load(
        self,
        gpu_layers: int = 0,
        context_length: int = 2048,
        **kwargs
    ) -> ModelInfo:
        """Load GGUF model using llama-cpp-python"""
        try:
            # Import here to avoid dependency issues if not installed
            from llama_cpp import Llama
            
            self.logger.info(f"Loading GGUF model from {self.model_path}")
            self.logger.info(f"GPU layers: {gpu_layers}, Context length: {context_length}")
            
            # Check if file exists
            if not Path(self.model_path).exists():
                raise FileNotFoundError(f"Model file not found: {self.model_path}")
            
            # Load model
            self.llama_model = Llama(
                model_path=self.model_path,
                n_ctx=context_length,
                n_gpu_layers=gpu_layers,
                verbose=False,
                **kwargs
            )
            
            self.model = self.llama_model
            self.is_loaded = True
            
            # Create model info
            self.model_info = ModelInfo(
                model_id=self.model_id,
                model_path=self.model_path,
                format="GGUF",
                context_length=context_length,
                gpu_layers=gpu_layers,
                loaded=True,
                memory_usage=self.get_memory_usage()
            )
            
            self.logger.info(f"Model loaded successfully. Memory usage: {self.model_info.memory_usage:.2f} MB")
            return self.model_info
            
        except ImportError:
            error_msg = "llama-cpp-python is not installed. Install with: pip install llama-cpp-python"
            self.logger.error(error_msg)
            raise ImportError(error_msg)
        except Exception as e:
            self.logger.error(f"Failed to load model: {str(e)}")
            self.is_loaded = False
            raise
    
    def generate(
        self,
        prompt: str,
        config: GenerationConfig,
        **kwargs
    ) -> Generator[str, None, None]:
        """Generate text with streaming"""
        if not self.is_model_loaded():
            raise RuntimeError("Model is not loaded")
        
        try:
            self.logger.debug(f"Generating with prompt length: {len(prompt)}")
            
            # Prepare generation parameters
            gen_params = {
                "prompt": prompt,
                "max_tokens": config.max_tokens,
                "temperature": config.temperature,
                "top_p": config.top_p,
                "top_k": config.top_k,
                "repeat_penalty": config.repeat_penalty,
                "stream": True,
            }
            
            if config.stop:
                gen_params["stop"] = config.stop
            
            # Merge with additional kwargs
            gen_params.update(kwargs)
            
            # Generate with streaming
            for output in self.llama_model(**gen_params):
                if "choices" in output and len(output["choices"]) > 0:
                    choice = output["choices"][0]
                    if "text" in choice:
                        yield choice["text"]
            
        except Exception as e:
            self.logger.error(f"Generation failed: {str(e)}")
            raise
    
    def generate_non_streaming(
        self,
        prompt: str,
        config: GenerationConfig,
        **kwargs
    ) -> str:
        """Generate text without streaming"""
        if not self.is_model_loaded():
            raise RuntimeError("Model is not loaded")
        
        try:
            # Prepare generation parameters
            gen_params = {
                "prompt": prompt,
                "max_tokens": config.max_tokens,
                "temperature": config.temperature,
                "top_p": config.top_p,
                "top_k": config.top_k,
                "repeat_penalty": config.repeat_penalty,
                "stream": False,
            }
            
            if config.stop:
                gen_params["stop"] = config.stop
            
            # Merge with additional kwargs
            gen_params.update(kwargs)
            
            # Generate
            output = self.llama_model(**gen_params)
            
            if "choices" in output and len(output["choices"]) > 0:
                return output["choices"][0]["text"]
            
            return ""
            
        except Exception as e:
            self.logger.error(f"Generation failed: {str(e)}")
            raise
    
    def unload(self) -> bool:
        """Unload model from memory"""
        try:
            if self.llama_model is not None:
                self.logger.info(f"Unloading model {self.model_id}")
                # llama-cpp-python handles cleanup automatically
                del self.llama_model
                self.llama_model = None
                self.model = None
                self.is_loaded = False
                self.model_info = None
                
                # Force garbage collection
                import gc
                gc.collect()
                
                self.logger.info("Model unloaded successfully")
                return True
            return False
        except Exception as e:
            self.logger.error(f"Failed to unload model: {str(e)}")
            return False
    
    def get_memory_usage(self) -> float:
        """Get memory usage in MB"""
        try:
            import psutil
            import os
            
            process = psutil.Process(os.getpid())
            memory_info = process.memory_info()
            return memory_info.rss / (1024 * 1024)  # Convert to MB
        except:
            return 0.0
    
    @staticmethod
    def supports_format(format: str) -> bool:
        """Check if this engine supports the given format"""
        return format.upper() in ["GGUF", "GGML"]
    
    @staticmethod
    def get_engine_name() -> str:
        """Get engine name"""
        return "GGUFEngine"
    
    def get_context_length(self) -> int:
        """Get current context length"""
        if self.model_info:
            return self.model_info.context_length
        return 0
    
    def count_tokens(self, text: str) -> int:
        """Count tokens in text"""
        if not self.is_model_loaded():
            # Rough estimation
            return len(text) // 4
        
        try:
            tokens = self.llama_model.tokenize(text.encode('utf-8'))
            return len(tokens)
        except:
            return len(text) // 4

