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
class GPTQEngine(InferenceEngine):
    """
    Inference engine for GPTQ quantized models using auto-gptq.
    Optimized for GPU inference.
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
        """Load GPTQ model"""
        try:
            from auto_gptq import AutoGPTQForCausalLM
            from transformers import AutoTokenizer
            
            self.logger.info(f"Loading GPTQ model from {self.model_path}")
            
            # Load tokenizer
            self.tokenizer = AutoTokenizer.from_pretrained(
                self.model_path,
                use_fast=True
            )
            
            # Load model
            self.model = AutoGPTQForCausalLM.from_quantized(
                self.model_path,
                device="cuda:0" if gpu_layers > 0 else "cpu",
                use_triton=False,
                use_safetensors=True,
                **kwargs
            )
            
            self.is_loaded = True
            
            self.model_info = ModelInfo(
                model_id=self.model_id,
                model_path=self.model_path,
                format="GPTQ",
                context_length=context_length,
                gpu_layers=gpu_layers,
                loaded=True,
                memory_usage=self.get_memory_usage()
            )
            
            self.logger.info(f"GPTQ model loaded successfully")
            return self.model_info
            
        except ImportError:
            error_msg = "auto-gptq is not installed. Install with: pip install auto-gptq"
            self.logger.error(error_msg)
            raise ImportError(error_msg)
        except Exception as e:
            self.logger.error(f"Failed to load GPTQ model: {str(e)}")
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
            
            inputs = self.tokenizer(prompt, return_tensors="pt").to(self.model.device)
            
            with torch.no_grad():
                for i in range(config.max_tokens):
                    outputs = self.model.generate(
                        **inputs,
                        max_new_tokens=1,
                        temperature=config.temperature,
                        top_p=config.top_p,
                        top_k=config.top_k,
                        do_sample=config.temperature > 0,
                    )
                    
                    new_token = outputs[0][-1:]
                    token_text = self.tokenizer.decode(new_token, skip_special_tokens=True)
                    
                    if token_text:
                        yield token_text
                    
                    inputs = {"input_ids": outputs}
                    
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
                self.logger.info(f"Unloading GPTQ model {self.model_id}")
                
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
                
                self.logger.info("GPTQ model unloaded successfully")
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
        return format.upper() == "GPTQ"
    
    @staticmethod
    def get_engine_name() -> str:
        """Get engine name"""
        return "GPTQEngine"
    
    def count_tokens(self, text: str) -> int:
        """Count tokens in text"""
        if not self.tokenizer:
            return len(text) // 4
        
        try:
            tokens = self.tokenizer.encode(text)
            return len(tokens)
        except:
            return len(text) // 4

