from abc import ABC, abstractmethod
from typing import Generator, Dict, Any, Optional, List
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class GenerationConfig:
    """Configuration for text generation"""
    temperature: float = 0.7
    top_p: float = 0.9
    top_k: int = 40
    max_tokens: int = 2048
    repeat_penalty: float = 1.1
    stop: Optional[List[str]] = None
    stream: bool = True


@dataclass
class ModelInfo:
    """Information about a loaded model"""
    model_id: int
    model_path: str
    format: str
    context_length: int
    gpu_layers: int = 0
    loaded: bool = False
    memory_usage: Optional[float] = None  # MB


class InferenceEngine(ABC):
    """
    Abstract base class for all inference engines.
    Each engine implementation must inherit from this class.
    """
    
    def __init__(self, model_id: int, model_path: str):
        self.model_id = model_id
        self.model_path = model_path
        self.model = None
        self.is_loaded = False
        self.model_info: Optional[ModelInfo] = None
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
    
    @abstractmethod
    def load(
        self,
        gpu_layers: int = 0,
        context_length: int = 2048,
        **kwargs
    ) -> ModelInfo:
        """
        Load the model into memory.
        
        Args:
            gpu_layers: Number of layers to offload to GPU (0 = CPU only, -1 = all)
            context_length: Maximum context length
            **kwargs: Additional engine-specific parameters
            
        Returns:
            ModelInfo: Information about the loaded model
            
        Raises:
            Exception: If model fails to load
        """
        pass
    
    @abstractmethod
    def generate(
        self,
        prompt: str,
        config: GenerationConfig,
        **kwargs
    ) -> Generator[str, None, None]:
        """
        Generate text from a prompt (streaming).
        
        Args:
            prompt: The input prompt
            config: Generation configuration
            **kwargs: Additional engine-specific parameters
            
        Yields:
            str: Generated tokens as they are produced
            
        Raises:
            Exception: If generation fails
        """
        pass
    
    @abstractmethod
    def generate_non_streaming(
        self,
        prompt: str,
        config: GenerationConfig,
        **kwargs
    ) -> str:
        """
        Generate text from a prompt (non-streaming).
        
        Args:
            prompt: The input prompt
            config: Generation configuration
            **kwargs: Additional engine-specific parameters
            
        Returns:
            str: Complete generated text
            
        Raises:
            Exception: If generation fails
        """
        pass
    
    @abstractmethod
    def unload(self) -> bool:
        """
        Unload the model from memory.
        
        Returns:
            bool: True if successful, False otherwise
        """
        pass
    
    @abstractmethod
    def get_memory_usage(self) -> float:
        """
        Get current memory usage in MB.
        
        Returns:
            float: Memory usage in MB
        """
        pass
    
    def is_model_loaded(self) -> bool:
        """Check if model is loaded"""
        return self.is_loaded and self.model is not None
    
    def get_model_info(self) -> Optional[ModelInfo]:
        """Get information about the loaded model"""
        return self.model_info
    
    @staticmethod
    @abstractmethod
    def supports_format(format: str) -> bool:
        """
        Check if this engine supports a given format.
        
        Args:
            format: Model format (e.g., "GGUF", "SafeTensors")
            
        Returns:
            bool: True if supported, False otherwise
        """
        pass
    
    @staticmethod
    @abstractmethod
    def get_engine_name() -> str:
        """
        Get the name of this engine.
        
        Returns:
            str: Engine name
        """
        pass
    
    @abstractmethod
    def count_tokens(self, text: str) -> int:
        """
        Count the number of tokens in the given text.
        
        Args:
            text: Text to count tokens for
            
        Returns:
            int: Number of tokens
        """
        pass
    
    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(model_id={self.model_id}, loaded={self.is_loaded})"


class EngineRegistry:
    """Registry for all available inference engines"""
    
    _engines: Dict[str, type] = {}
    
    @classmethod
    def register(cls, engine_class: type):
        """Register an engine class"""
        if not issubclass(engine_class, InferenceEngine):
            raise ValueError(f"{engine_class} must inherit from InferenceEngine")
        
        name = engine_class.get_engine_name()
        cls._engines[name] = engine_class
        logger.info(f"Registered engine: {name}")
        return engine_class
    
    @classmethod
    def get_engine_for_format(cls, format: str) -> Optional[type]:
        """Get the appropriate engine class for a model format"""
        format_upper = format.upper()
        
        for engine_class in cls._engines.values():
            if engine_class.supports_format(format_upper):
                return engine_class
        
        logger.warning(f"No engine found for format: {format}")
        return None
    
    @classmethod
    def get_all_engines(cls) -> Dict[str, type]:
        """Get all registered engines"""
        return cls._engines.copy()
    
    @classmethod
    def get_supported_formats(cls) -> List[str]:
        """Get list of all supported formats"""
        formats = []
        for engine_class in cls._engines.values():
            # This would need to be implemented per engine
            # For now, we'll return a static list
            pass
        return ["GGUF", "SafeTensors", "GPTQ", "AWQ", "EXL2", "ONNX"]

