from typing import Generator, Optional
import logging
from pathlib import Path
import numpy as np

from app.services.inference.base_engine import (
    InferenceEngine,
    GenerationConfig,
    ModelInfo,
    EngineRegistry
)

logger = logging.getLogger(__name__)


@EngineRegistry.register
class ONNXEngine(InferenceEngine):
    """
    Inference engine for ONNX format using onnxruntime.
    Cross-platform and optimized.
    """
    
    def __init__(self, model_id: int, model_path: str):
        super().__init__(model_id, model_path)
        self.session = None
        self.tokenizer = None
    
    def load(
        self,
        gpu_layers: int = 0,
        context_length: int = 2048,
        **kwargs
    ) -> ModelInfo:
        """Load ONNX model"""
        try:
            import onnxruntime as ort
            from transformers import AutoTokenizer
            
            self.logger.info(f"Loading ONNX model from {self.model_path}")
            
            # Setup providers
            providers = []
            if gpu_layers > 0:
                providers.append('CUDAExecutionProvider')
            providers.append('CPUExecutionProvider')
            
            # Find ONNX model file
            model_path = Path(self.model_path)
            onnx_files = list(model_path.glob("*.onnx"))
            
            if not onnx_files:
                raise FileNotFoundError(f"No ONNX files found in {self.model_path}")
            
            onnx_model = str(onnx_files[0])
            
            # Load session
            sess_options = ort.SessionOptions()
            sess_options.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL
            
            self.session = ort.InferenceSession(
                onnx_model,
                sess_options=sess_options,
                providers=providers
            )
            
            # Load tokenizer
            try:
                self.tokenizer = AutoTokenizer.from_pretrained(self.model_path)
            except:
                self.logger.warning("Could not load tokenizer, using basic tokenization")
                self.tokenizer = None
            
            self.is_loaded = True
            
            self.model_info = ModelInfo(
                model_id=self.model_id,
                model_path=self.model_path,
                format="ONNX",
                context_length=context_length,
                gpu_layers=gpu_layers,
                loaded=True,
                memory_usage=self.get_memory_usage()
            )
            
            self.logger.info(f"ONNX model loaded successfully")
            return self.model_info
            
        except ImportError:
            error_msg = "onnxruntime is not installed. Install with: pip install onnxruntime-gpu"
            self.logger.error(error_msg)
            raise ImportError(error_msg)
        except Exception as e:
            self.logger.error(f"Failed to load ONNX model: {str(e)}")
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
            if not self.tokenizer:
                # Basic token-by-token generation
                words = prompt.split()
                for word in words:
                    yield word + " "
                return
            
            # Encode prompt
            inputs = self.tokenizer(prompt, return_tensors="np")
            input_ids = inputs["input_ids"]
            attention_mask = inputs.get("attention_mask")
            
            generated_tokens = []
            
            for _ in range(config.max_tokens):
                # Prepare inputs for ONNX
                ort_inputs = {
                    "input_ids": input_ids.astype(np.int64)
                }
                
                if attention_mask is not None:
                    ort_inputs["attention_mask"] = attention_mask.astype(np.int64)
                
                # Run inference
                outputs = self.session.run(None, ort_inputs)
                logits = outputs[0]
                
                # Sample next token
                next_token_logits = logits[0, -1, :]
                
                # Apply temperature
                if config.temperature > 0:
                    next_token_logits = next_token_logits / config.temperature
                
                # Apply top-k
                if config.top_k > 0:
                    top_k_indices = np.argpartition(next_token_logits, -config.top_k)[-config.top_k:]
                    top_k_logits = next_token_logits[top_k_indices]
                    probabilities = np.exp(top_k_logits) / np.sum(np.exp(top_k_logits))
                    next_token = top_k_indices[np.random.choice(len(top_k_indices), p=probabilities)]
                else:
                    next_token = np.argmax(next_token_logits)
                
                generated_tokens.append(int(next_token))
                
                # Decode and yield
                token_text = self.tokenizer.decode([next_token], skip_special_tokens=True)
                if token_text:
                    yield token_text
                
                # Check for EOS
                if next_token == self.tokenizer.eos_token_id:
                    break
                
                # Update input_ids
                input_ids = np.concatenate([input_ids, [[next_token]]], axis=1)
                if attention_mask is not None:
                    attention_mask = np.concatenate([attention_mask, [[1]]], axis=1)
            
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
            if self.session is not None:
                self.logger.info(f"Unloading ONNX model {self.model_id}")
                
                del self.session
                del self.tokenizer
                
                self.session = None
                self.tokenizer = None
                self.is_loaded = False
                self.model_info = None
                
                import gc
                gc.collect()
                
                self.logger.info("ONNX model unloaded successfully")
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
            
            return memory_mb
        except:
            return 0.0
    
    @staticmethod
    def supports_format(format: str) -> bool:
        """Check if this engine supports the given format"""
        return format.upper() == "ONNX"
    
    @staticmethod
    def get_engine_name() -> str:
        """Get engine name"""
        return "ONNXEngine"
    
    def count_tokens(self, text: str) -> int:
        """Count tokens in text"""
        if not self.tokenizer:
            return len(text) // 4
        
        try:
            tokens = self.tokenizer.encode(text)
            return len(tokens)
        except:
            return len(text) // 4

