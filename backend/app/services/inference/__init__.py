"""
Inference engines for different model formats.
"""

# Import all engines to register them
from app.services.inference.base_engine import InferenceEngine, EngineRegistry, GenerationConfig, ModelInfo
from app.services.inference.gguf_engine import GGUFEngine
from app.services.inference.transformers_engine import TransformersEngine

# Optional engines (will only register if dependencies are available)
try:
    from app.services.inference.gptq_engine import GPTQEngine
except ImportError:
    pass

try:
    from app.services.inference.awq_engine import AWQEngine
except ImportError:
    pass

try:
    from app.services.inference.exllama_engine import EXL2Engine
except ImportError:
    pass

try:
    from app.services.inference.onnx_engine import ONNXEngine
except ImportError:
    pass

__all__ = [
    "InferenceEngine",
    "EngineRegistry",
    "GenerationConfig",
    "ModelInfo",
    "GGUFEngine",
    "TransformersEngine",
]
