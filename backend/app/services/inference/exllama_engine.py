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
class EXL2Engine(InferenceEngine):
    """
    Inference engine for EXL2 format using exllamav2.
    Fastest inference for GPU.
    """
    
    def __init__(self, model_id: int, model_path: str):
        super().__init__(model_id, model_path)
        self.model = None
        self.tokenizer = None
        self.generator = None
    
    def load(
        self,
        gpu_layers: int = 0,
        context_length: int = 2048,
        **kwargs
    ) -> ModelInfo:
        """Load EXL2 model"""
        try:
            from exllamav2 import (
                ExLlamaV2,
                ExLlamaV2Config,
                ExLlamaV2Cache,
                ExLlamaV2Tokenizer
            )
            from exllamav2.generator import ExLlamaV2StreamingGenerator, ExLlamaV2Sampler
            
            self.logger.info(f"Loading EXL2 model from {self.model_path}")
            
            # Load config
            config = ExLlamaV2Config()
            config.model_dir = self.model_path
            config.prepare()
            
            # Set context length
            config.max_seq_len = context_length
            
            # Load model
            self.model = ExLlamaV2(config)
            self.model.load()
            
            # Load tokenizer
            self.tokenizer = ExLlamaV2Tokenizer(config)
            
            # Create cache
            cache = ExLlamaV2Cache(self.model)
            
            # Create generator
            self.generator = ExLlamaV2StreamingGenerator(self.model, cache, self.tokenizer)
            
            self.is_loaded = True
            
            self.model_info = ModelInfo(
                model_id=self.model_id,
                model_path=self.model_path,
                format="EXL2",
                context_length=context_length,
                gpu_layers=gpu_layers,
                loaded=True,
                memory_usage=self.get_memory_usage()
            )
            
            self.logger.info(f"EXL2 model loaded successfully")
            return self.model_info
            
        except ImportError:
            error_msg = "exllamav2 is not installed. Install with: pip install exllamav2"
            self.logger.error(error_msg)
            raise ImportError(error_msg)
        except Exception as e:
            self.logger.error(f"Failed to load EXL2 model: {str(e)}")
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
            from exllamav2.generator import ExLlamaV2Sampler
            
            # Create sampler settings
            settings = ExLlamaV2Sampler.Settings()
            settings.temperature = config.temperature
            settings.top_p = config.top_p
            settings.top_k = config.top_k
            settings.token_repetition_penalty = config.repeat_penalty
            
            # Start generation
            input_ids = self.tokenizer.encode(prompt)
            self.generator.begin_stream(input_ids, settings)
            
            generated_tokens = 0
            while generated_tokens < config.max_tokens:
                chunk, eos, _ = self.generator.stream()
                if eos or not chunk:
                    break
                
                yield chunk
                generated_tokens += 1
            
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
            generated_text = ""
            for chunk in self.generate(prompt, config, **kwargs):
                generated_text += chunk
            
            return generated_text
            
        except Exception as e:
            self.logger.error(f"Generation failed: {str(e)}")
            raise
    
    def unload(self) -> bool:
        """Unload model from memory"""
        try:
            if self.model is not None:
                self.logger.info(f"Unloading EXL2 model {self.model_id}")
                
                del self.model
                del self.tokenizer
                del self.generator
                
                self.model = None
                self.tokenizer = None
                self.generator = None
                self.is_loaded = False
                self.model_info = None
                
                import gc
                gc.collect()
                
                try:
                    import torch
                    if torch.cuda.is_available():
                        torch.cuda.empty_cache()
                except:
                    pass
                
                self.logger.info("EXL2 model unloaded successfully")
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
            memory_mb = process.memory_info().rss / (1024 * 1024)
            
            try:
                import torch
                if torch.cuda.is_available():
                    gpu_memory = torch.cuda.memory_allocated() / (1024 * 1024)
                    memory_mb += gpu_memory
            except:
                pass
            
            return memory_mb
        except:
            return 0.0
    
    @staticmethod
    def supports_format(format: str) -> bool:
        """Check if this engine supports the given format"""
        return format.upper() == "EXL2"
    
    @staticmethod
    def get_engine_name() -> str:
        """Get engine name"""
        return "EXL2Engine"
    
    def count_tokens(self, text: str) -> int:
        """Count tokens in text"""
        if not self.tokenizer:
            return len(text) // 4
        
        try:
            tokens = self.tokenizer.encode(text)
            return len(tokens[0]) if hasattr(tokens, '__len__') else len(text) // 4
        except:
            return len(text) // 4

