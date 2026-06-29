from typing import Generator, Optional
import logging
from pathlib import Path
import torch

from app.services.inference.base_engine import (
    InferenceEngine,
    GenerationConfig,
    ModelInfo,
    EngineRegistry
)

logger = logging.getLogger(__name__)


@EngineRegistry.register
class TransformersEngine(InferenceEngine):
    """
    Inference engine for SafeTensors/PyTorch models using HuggingFace Transformers.
    Supports various model architectures with GPU acceleration.
    """
    
    def __init__(self, model_id: int, model_path: str):
        super().__init__(model_id, model_path)
        self.tokenizer = None
        self.pipeline = None
        self.device = None
    
    def load(
        self,
        gpu_layers: int = 0,
        context_length: int = 2048,
        **kwargs
    ) -> ModelInfo:
        """Load model using Transformers"""
        try:
            from transformers import AutoModelForCausalLM, AutoTokenizer, TextGenerationPipeline
            
            self.logger.info(f"Loading Transformers model from {self.model_path}")
            
            # Check if path exists
            model_path = Path(self.model_path)
            if not model_path.exists():
                raise FileNotFoundError(f"Model path not found: {self.model_path}")
            
            # Determine device
            if gpu_layers > 0 and torch.cuda.is_available():
                self.device = "cuda"
                self.logger.info("Using CUDA for inference")
            elif gpu_layers > 0 and torch.backends.mps.is_available():
                self.device = "mps"
                self.logger.info("Using Metal (MPS) for inference")
            else:
                self.device = "cpu"
                self.logger.info("Using CPU for inference")
            
            # Load tokenizer
            self.logger.info("Loading tokenizer...")
            self.tokenizer = AutoTokenizer.from_pretrained(
                self.model_path,
                trust_remote_code=kwargs.get("trust_remote_code", False)
            )
            
            # Set pad token if not exists
            if self.tokenizer.pad_token is None:
                self.tokenizer.pad_token = self.tokenizer.eos_token
            
            # Load model
            self.logger.info("Loading model...")
            load_kwargs = {
                "pretrained_model_name_or_path": self.model_path,
                "device_map": "auto" if self.device == "cuda" else None,
                "torch_dtype": torch.float16 if self.device in ["cuda", "mps"] else torch.float32,
                "trust_remote_code": kwargs.get("trust_remote_code", False),
            }
            
            # Add low_cpu_mem_usage for large models
            if self.device == "cuda":
                load_kwargs["low_cpu_mem_usage"] = True
            
            # Try to load model with different Auto classes
            model_loaded = False
            
            # Try CausalLM first (for generation models)
            try:
                from transformers import AutoModelForCausalLM
                self.logger.info("Attempting to load as CausalLM...")
                self.model = AutoModelForCausalLM.from_pretrained(**load_kwargs)
                model_loaded = True
                self.logger.info("✅ Loaded as CausalLM (Text Generation)")
            except Exception as e1:
                self.logger.warning(f"Not a CausalLM model: {str(e1)[:100]}")
                
                # Try Seq2SeqLM (for T5, BART, etc.)
                try:
                    from transformers import AutoModelForSeq2SeqLM
                    self.logger.info("Attempting to load as Seq2SeqLM...")
                    self.model = AutoModelForSeq2SeqLM.from_pretrained(**load_kwargs)
                    model_loaded = True
                    self.logger.info("✅ Loaded as Seq2SeqLM (Text-to-Text Generation)")
                except Exception as e2:
                    self.logger.warning(f"Not a Seq2SeqLM model: {str(e2)[:100]}")
                    
                    # Try generic AutoModel (for BERT, etc. - will be used for embeddings)
                    try:
                        from transformers import AutoModel
                        self.logger.info("Attempting to load as AutoModel...")
                        self.model = AutoModel.from_pretrained(**load_kwargs)
                        model_loaded = True
                        self.logger.warning("⚠️ Loaded as AutoModel (Classification/Embeddings model)")
                        self.logger.warning("⚠️ This model may not work well for text generation")
                    except Exception as e3:
                        error_msg = (
                            f"Failed to load model with any Auto class.\n"
                            f"CausalLM error: {str(e1)[:100]}\n"
                            f"Seq2SeqLM error: {str(e2)[:100]}\n"
                            f"AutoModel error: {str(e3)[:100]}"
                        )
                        self.logger.error(error_msg)
                        raise Exception(error_msg)
            
            if not model_loaded:
                raise Exception("Failed to load model with any supported architecture")
            
            # Move to device if not using device_map
            if self.device != "cuda":
                self.model.to(self.device)
            
            self.is_loaded = True
            
            # Create model info
            self.model_info = ModelInfo(
                model_id=self.model_id,
                model_path=self.model_path,
                format="SafeTensors",
                context_length=context_length,
                gpu_layers=gpu_layers,
                loaded=True,
                memory_usage=self.get_memory_usage()
            )
            
            self.logger.info(f"Model loaded successfully. Memory usage: {self.model_info.memory_usage:.2f} MB")
            return self.model_info
            
        except ImportError as e:
            error_msg = f"Required libraries not installed: {str(e)}. Install with: pip install transformers accelerate"
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
        
        # Check if model has generate method (for generation models)
        if not hasattr(self.model, 'generate'):
            raise RuntimeError(
                "This model does not support text generation. "
                "It appears to be a BERT-like model designed for classification or embeddings. "
                "Please use a model designed for text generation, such as:\n"
                "- TinyLlama/TinyLlama-1.1B-Chat-v1.0 (1.1B, fast)\n"
                "- microsoft/phi-2 (2.7B, good quality)\n"
                "- gpt2 (124M, very fast)\n"
                "- meta-llama/Llama-2-7b-chat-hf (7B, high quality)"
            )
        
        try:
            from transformers import TextIteratorStreamer
            from threading import Thread
            
            self.logger.debug(f"Generating with prompt length: {len(prompt)}")
            
            # Tokenize input
            inputs = self.tokenizer(prompt, return_tensors="pt").to(self.device)
            
            # Create streamer
            streamer = TextIteratorStreamer(
                self.tokenizer,
                skip_special_tokens=True,
                skip_prompt=True
            )
            
            # Prepare generation kwargs
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
            
            # Add stop tokens if provided
            if config.stop:
                # Convert stop strings to token ids
                stop_token_ids = []
                for stop_str in config.stop:
                    stop_ids = self.tokenizer.encode(stop_str, add_special_tokens=False)
                    stop_token_ids.extend(stop_ids)
                if stop_token_ids:
                    generation_kwargs["eos_token_id"] = stop_token_ids
            
            # Start generation in a separate thread
            thread = Thread(target=self.model.generate, kwargs=generation_kwargs)
            thread.start()
            
            # Stream tokens
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
        
        # Check if model has generate method (for generation models)
        if not hasattr(self.model, 'generate'):
            raise RuntimeError(
                "This model does not support text generation. "
                "It appears to be a BERT-like model designed for classification or embeddings. "
                "Please use a model designed for text generation, such as:\n"
                "- TinyLlama/TinyLlama-1.1B-Chat-v1.0 (1.1B, fast)\n"
                "- microsoft/phi-2 (2.7B, good quality)\n"
                "- gpt2 (124M, very fast)\n"
                "- meta-llama/Llama-2-7b-chat-hf (7B, high quality)"
            )
        
        try:
            # Tokenize input
            inputs = self.tokenizer(prompt, return_tensors="pt").to(self.device)
            
            # Prepare generation kwargs
            generation_kwargs = {
                **inputs,
                "max_new_tokens": config.max_tokens,
                "temperature": config.temperature,
                "top_p": config.top_p,
                "top_k": config.top_k,
                "repetition_penalty": config.repeat_penalty,
                "do_sample": config.temperature > 0,
            }
            
            # Add stop tokens if provided
            if config.stop:
                stop_token_ids = []
                for stop_str in config.stop:
                    stop_ids = self.tokenizer.encode(stop_str, add_special_tokens=False)
                    stop_token_ids.extend(stop_ids)
                if stop_token_ids:
                    generation_kwargs["eos_token_id"] = stop_token_ids
            
            # Generate
            with torch.no_grad():
                output_ids = self.model.generate(**generation_kwargs)
            
            # Decode output (skip input tokens)
            generated_ids = output_ids[0][inputs['input_ids'].shape[1]:]
            generated_text = self.tokenizer.decode(generated_ids, skip_special_tokens=True)
            
            return generated_text
            
        except Exception as e:
            self.logger.error(f"Generation failed: {str(e)}")
            raise
    
    def unload(self) -> bool:
        """Unload model from memory"""
        try:
            if self.model is not None:
                self.logger.info(f"Unloading model {self.model_id}")
                
                # Move to CPU first to free GPU memory
                if self.device in ["cuda", "mps"]:
                    self.model.to("cpu")
                
                del self.model
                del self.tokenizer
                
                self.model = None
                self.tokenizer = None
                self.pipeline = None
                self.is_loaded = False
                self.model_info = None
                
                # Clear CUDA cache if applicable
                if torch.cuda.is_available():
                    torch.cuda.empty_cache()
                
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
            memory_mb = memory_info.rss / (1024 * 1024)
            
            # Add GPU memory if using CUDA
            if self.device == "cuda" and torch.cuda.is_available():
                gpu_memory = torch.cuda.memory_allocated() / (1024 * 1024)
                memory_mb += gpu_memory
            
            return memory_mb
        except:
            return 0.0
    
    @staticmethod
    def supports_format(format: str) -> bool:
        """Check if this engine supports the given format"""
        return format.upper() in ["SAFETENSORS", "PYTORCH", "PT", "BIN"]
    
    @staticmethod
    def get_engine_name() -> str:
        """Get engine name"""
        return "TransformersEngine"
    
    def count_tokens(self, text: str) -> int:
        """Count tokens in text"""
        if not self.tokenizer:
            return len(text) // 4
        
        try:
            tokens = self.tokenizer.encode(text)
            return len(tokens)
        except:
            return len(text) // 4

