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
class AWQEngine(InferenceEngine):
    """
    Inference engine for AWQ quantized models using autoawq.
    Optimized for GPU inference with better quality.
    """
    
    def __init__(self, model_id: int, model_path: str):
        super().__init__(model_id, model_path)
        self.model = None
        self.tokenizer = None
    
    def load(
        self,
        gpu_layers: int = 0,
        context_length: int = 2048,
        **kwargs
    ) -> ModelInfo:
        """Load AWQ model"""
        try:
            from awq import AutoAWQForCausalLM
            from transformers import AutoTokenizer
            
            self.logger.info(f"Loading AWQ model from {self.model_path}")
            
            # Load tokenizer
            self.tokenizer = AutoTokenizer.from_pretrained(
                self.model_path,
                trust_remote_code=True
            )
            
            # Load model
            self.model = AutoAWQForCausalLM.from_quantized(
                self.model_path,
                fuse_layers=True,
                trust_remote_code=True,
                safetensors=True,
                **kwargs
            )
            
            self.is_loaded = True
            
            self.model_info = ModelInfo(
                model_id=self.model_id,
                model_path=self.model_path,
                format="AWQ",
                context_length=context_length,
                gpu_layers=gpu_layers,
                loaded=True,
                memory_usage=self.get_memory_usage()
            )
            
            self.logger.info(f"AWQ model loaded successfully")
            return self.model_info
            
        except ImportError:
            error_msg = "autoawq is not installed. Install with: pip install autoawq"
            self.logger.error(error_msg)
            raise ImportError(error_msg)
        except Exception as e:
            self.logger.error(f"Failed to load AWQ model: {str(e)}")
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
            import torch
            from transformers import TextIteratorStreamer
            from threading import Thread
            
            inputs = self.tokenizer(prompt, return_tensors="pt").to(self.model.device)
            
            streamer = TextIteratorStreamer(
                self.tokenizer,
                skip_special_tokens=True,
                skip_prompt=True
            )
            
            generation_kwargs = {
                **inputs,
                "max_new_tokens": config.max_tokens,
                "temperature": config.temperature,
                "top_p": config.top_p,
                "top_k": config.top_k,
                "repetition_penalty": config.repeat_penalty,
                "streamer": streamer,
                "do_sample": config.temperature > 0,
            }
            
            thread = Thread(target=self.model.generate, kwargs=generation_kwargs)
            thread.start()
            
            for text in streamer:
                if text:
                    yield text
            
            thread.join()
            
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
            import torch
            
            inputs = self.tokenizer(prompt, return_tensors="pt").to(self.model.device)
            
            with torch.no_grad():
                outputs = self.model.generate(
                    **inputs,
                    max_new_tokens=config.max_tokens,
                    temperature=config.temperature,
                    top_p=config.top_p,
                    top_k=config.top_k,
                    repetition_penalty=config.repeat_penalty,
                    do_sample=config.temperature > 0,
                )
            
            generated_ids = outputs[0][inputs['input_ids'].shape[1]:]
            generated_text = self.tokenizer.decode(generated_ids, skip_special_tokens=True)
            
            return generated_text
            
        except Exception as e:
            self.logger.error(f"Generation failed: {str(e)}")
            raise
    
    def unload(self) -> bool:
        """Unload model from memory"""
        try:
            if self.model is not None:
                self.logger.info(f"Unloading AWQ model {self.model_id}")
                
                del self.model
                del self.tokenizer
                
                self.model = None
                self.tokenizer = None
                self.is_loaded = False
                self.model_info = None
                
                import torch
                import gc
                
                if torch.cuda.is_available():
                    torch.cuda.empty_cache()
                
                gc.collect()
                
                self.logger.info("AWQ model unloaded successfully")
                return True
            return False
        except Exception as e:
            self.logger.error(f"Failed to unload model: {str(e)}")
            return False
    
    def get_memory_usage(self) -> float:
        """Get memory usage in MB"""
        try:
            import psutil
            import torch
            import os
            
            process = psutil.Process(os.getpid())
            memory_mb = process.memory_info().rss / (1024 * 1024)
            
            if torch.cuda.is_available():
                gpu_memory = torch.cuda.memory_allocated() / (1024 * 1024)
                memory_mb += gpu_memory
            
            return memory_mb
        except:
            return 0.0
    
    @staticmethod
    def supports_format(format: str) -> bool:
        """Check if this engine supports the given format"""
        return format.upper() == "AWQ"
    
    @staticmethod
    def get_engine_name() -> str:
        """Get engine name"""
        return "AWQEngine"
    
    def count_tokens(self, text: str) -> int:
        """Count tokens in text"""
        if not self.tokenizer:
            return len(text) // 4
        
        try:
            tokens = self.tokenizer.encode(text)
            return len(tokens)
        except:
            return len(text) // 4

