"""
Model format detection service.
Automatically detects model format from file structure.
"""

import logging
from pathlib import Path
from typing import Optional, Dict, Any
import json

logger = logging.getLogger(__name__)


class FormatDetector:
    """Detects model format from directory or file structure"""
    
    @staticmethod
    def detect_format(model_path: str) -> Optional[str]:
        """
        Detect model format from path.
        
        Args:
            model_path: Path to model file or directory
            
        Returns:
            Optional[str]: Detected format (GGUF, SafeTensors, GPTQ, AWQ, EXL2, ONNX) or None
        """
        path = Path(model_path)
        
        # Single file
        if path.is_file():
            return FormatDetector._detect_from_file(path)
        
        # Directory
        elif path.is_dir():
            return FormatDetector._detect_from_directory(path)
        
        logger.warning(f"Path {model_path} does not exist")
        return None
    
    @staticmethod
    def _detect_from_file(file_path: Path) -> Optional[str]:
        """Detect format from a single file"""
        suffix = file_path.suffix.lower()
        
        if suffix == ".gguf":
            return "GGUF"
        elif suffix == ".onnx":
            return "ONNX"
        elif suffix in [".bin", ".pt", ".pth"]:
            return "PyTorch"
        elif suffix == ".safetensors":
            return "SafeTensors"
        
        return None
    
    @staticmethod
    def _detect_from_directory(dir_path: Path) -> Optional[str]:
        """Detect format from directory contents"""
        
        # Get all files in directory
        files = list(dir_path.iterdir())
        file_names = [f.name for f in files]
        file_suffixes = [f.suffix.lower() for f in files]
        
        # Check for GGUF
        if any(f.endswith(".gguf") for f in file_names):
            return "GGUF"
        
        # Check for EXL2 (exl2 specific files)
        if "config.json" in file_names:
            config_path = dir_path / "config.json"
            try:
                with open(config_path, 'r') as f:
                    config = json.load(f)
                    if "exl2" in str(config).lower():
                        return "EXL2"
            except:
                pass
        
        # Check for quantization.json (indicates quantized model)
        if "quantization_config.json" in file_names or "quantize_config.json" in file_names:
            config_file = dir_path / ("quantization_config.json" if "quantization_config.json" in file_names else "quantize_config.json")
            try:
                with open(config_file, 'r') as f:
                    config = json.load(f)
                    quant_method = config.get("quant_method", "").lower()
                    
                    if "gptq" in quant_method:
                        return "GPTQ"
                    elif "awq" in quant_method:
                        return "AWQ"
            except:
                pass
        
        # Check for ONNX
        if any(suffix == ".onnx" for suffix in file_suffixes):
            return "ONNX"
        
        # Check for SafeTensors
        if any(suffix == ".safetensors" for suffix in file_suffixes):
            # If it has quantize_config, it's GPTQ or AWQ
            if "quantize_config.json" in file_names:
                return "GPTQ"  # Default to GPTQ for safetensors with quantization
            return "SafeTensors"
        
        # Check for PyTorch bins
        if any(suffix in [".bin", ".pt", ".pth"] for suffix in file_suffixes):
            return "PyTorch"
        
        logger.warning(f"Could not detect format for directory: {dir_path}")
        return None
    
    @staticmethod
    def get_model_info(model_path: str) -> Dict[str, Any]:
        """
        Get detailed information about a model.
        
        Args:
            model_path: Path to model
            
        Returns:
            Dict with model information
        """
        path = Path(model_path)
        info = {
            "path": str(path),
            "format": None,
            "size_mb": 0,
            "files": [],
            "config": None
        }
        
        # Detect format
        info["format"] = FormatDetector.detect_format(model_path)
        
        # Get size
        if path.is_file():
            info["size_mb"] = path.stat().st_size / (1024 * 1024)
            info["files"] = [path.name]
        elif path.is_dir():
            total_size = 0
            files = []
            for file in path.rglob("*"):
                if file.is_file():
                    total_size += file.stat().st_size
                    files.append(file.name)
            info["size_mb"] = total_size / (1024 * 1024)
            info["files"] = files
        
        # Try to read config
        if path.is_dir():
            config_path = path / "config.json"
            if config_path.exists():
                try:
                    with open(config_path, 'r') as f:
                        info["config"] = json.load(f)
                except:
                    pass
        
        return info
    
    @staticmethod
    def validate_model_path(model_path: str) -> bool:
        """
        Validate if model path is valid and contains necessary files.
        
        Args:
            model_path: Path to model
            
        Returns:
            bool: True if valid, False otherwise
        """
        path = Path(model_path)
        
        if not path.exists():
            logger.error(f"Model path does not exist: {model_path}")
            return False
        
        format_detected = FormatDetector.detect_format(model_path)
        
        if format_detected is None:
            logger.error(f"Could not detect model format: {model_path}")
            return False
        
        # Format-specific validation
        if format_detected == "GGUF":
            return path.suffix.lower() == ".gguf" or any(f.suffix.lower() == ".gguf" for f in path.glob("*.gguf"))
        
        elif format_detected in ["SafeTensors", "PyTorch", "GPTQ", "AWQ"]:
            # Must have config.json
            config_path = path / "config.json" if path.is_dir() else path.parent / "config.json"
            return config_path.exists()
        
        elif format_detected == "ONNX":
            return path.suffix.lower() == ".onnx" or any(f.suffix.lower() == ".onnx" for f in path.glob("*.onnx"))
        
        return True


# Singleton instance
format_detector = FormatDetector()

