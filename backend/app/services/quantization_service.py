"""
Quantization service for converting models to different formats.
Supports conversion to GGUF format with various quantization levels.
"""

import logging
import subprocess
from pathlib import Path
from typing import Optional, Callable, Dict, Any
from enum import Enum
import asyncio

logger = logging.getLogger(__name__)


class QuantizationLevel(str, Enum):
    """Available quantization levels for GGUF"""
    Q2_K = "Q2_K"  # Smallest, lowest quality
    Q3_K_S = "Q3_K_S"
    Q3_K_M = "Q3_K_M"
    Q3_K_L = "Q3_K_L"
    Q4_0 = "Q4_0"
    Q4_1 = "Q4_1"
    Q4_K_S = "Q4_K_S"
    Q4_K_M = "Q4_K_M"
    Q5_0 = "Q5_0"
    Q5_1 = "Q5_1"
    Q5_K_S = "Q5_K_S"
    Q5_K_M = "Q5_K_M"
    Q6_K = "Q6_K"
    Q8_0 = "Q8_0"  # Largest, highest quality
    F16 = "F16"   # Full precision float16
    F32 = "F32"   # Full precision float32


class QuantizationService:
    """
    Service for quantizing models.
    Primarily supports conversion to GGUF format.
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.llama_cpp_path = None
        self._check_llama_cpp()
    
    def _check_llama_cpp(self) -> bool:
        """Check if llama.cpp tools are available"""
        try:
            # Try to find convert.py from llama.cpp
            result = subprocess.run(
                ["python", "-c", "import llama_cpp; print(llama_cpp.__file__)"],
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                self.llama_cpp_path = Path(result.stdout.strip()).parent
                self.logger.info(f"Found llama-cpp-python at {self.llama_cpp_path}")
                return True
        except:
            pass
        
        self.logger.warning("llama-cpp-python not found. Quantization features may be limited.")
        return False
    
    async def convert_to_gguf(
        self,
        input_path: str,
        output_path: str,
        quantization: Optional[QuantizationLevel] = None,
        progress_callback: Optional[Callable[[float, str], None]] = None
    ) -> bool:
        """
        Convert a model to GGUF format.
        
        Args:
            input_path: Path to source model (SafeTensors/PyTorch)
            output_path: Path for output GGUF file
            quantization: Quantization level (None for F16)
            progress_callback: Callback for progress updates (progress: float, message: str)
            
        Returns:
            bool: True if successful
        """
        try:
            input_path = Path(input_path)
            output_path = Path(output_path)
            
            if not input_path.exists():
                raise FileNotFoundError(f"Input path does not exist: {input_path}")
            
            # Ensure output directory exists
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            self.logger.info(f"Converting {input_path} to GGUF format")
            
            if progress_callback:
                progress_callback(0.1, "Starting conversion...")
            
            # Step 1: Convert to GGUF F16 first
            temp_f16_path = output_path.parent / f"{output_path.stem}_f16.gguf"
            
            success = await self._convert_to_f16_gguf(input_path, temp_f16_path, progress_callback)
            
            if not success:
                return False
            
            if progress_callback:
                progress_callback(0.6, "Converted to F16 GGUF")
            
            # Step 2: Quantize if requested
            if quantization and quantization not in [QuantizationLevel.F16, QuantizationLevel.F32]:
                success = await self._quantize_gguf(
                    temp_f16_path,
                    output_path,
                    quantization,
                    progress_callback
                )
                
                # Remove temp file
                if temp_f16_path.exists():
                    temp_f16_path.unlink()
                
                if not success:
                    return False
            else:
                # Just rename F16 file
                temp_f16_path.rename(output_path)
            
            if progress_callback:
                progress_callback(1.0, "Conversion complete")
            
            self.logger.info(f"Successfully converted to {output_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Conversion failed: {str(e)}")
            if progress_callback:
                progress_callback(0, f"Error: {str(e)}")
            return False
    
    async def _convert_to_f16_gguf(
        self,
        input_path: Path,
        output_path: Path,
        progress_callback: Optional[Callable[[float, str], None]] = None
    ) -> bool:
        """Convert model to F16 GGUF using transformers and direct GGUF writing"""
        try:
            self.logger.info("Converting to F16 GGUF format...")
            
            if progress_callback:
                progress_callback(0.1, "Validating input model...")
            
            # Validate input format
            if not self._validate_model_format(input_path):
                raise ValueError("Input model format not supported. Needs SafeTensors or PyTorch format.")
            
            if progress_callback:
                progress_callback(0.2, "Loading model with transformers...")
            
            # Try to load with transformers
            try:
                from transformers import AutoModelForCausalLM, AutoTokenizer
                
                # Load model
                model = AutoModelForCausalLM.from_pretrained(
                    str(input_path),
                    torch_dtype="auto",
                    device_map="cpu",
                    trust_remote_code=True
                )
                
                tokenizer = AutoTokenizer.from_pretrained(
                    str(input_path),
                    trust_remote_code=True
                )
                
                if progress_callback:
                    progress_callback(0.4, "Model loaded, converting to GGUF...")
                
                # Convert to GGUF format
                # Note: This requires gguf library
                try:
                    import gguf
                    import torch
                    
                    # Create GGUF writer
                    writer = gguf.GGUFWriter(str(output_path), "llama")
                    
                    # Add metadata
                    writer.add_name(input_path.name)
                    writer.add_description(f"Converted from {input_path}")
                    
                    if progress_callback:
                        progress_callback(0.5, "Writing tensors...")
                    
                    # Convert model weights
                    state_dict = model.state_dict()
                    total_tensors = len(state_dict)
                    
                    for idx, (name, tensor) in enumerate(state_dict.items()):
                        # Convert to float16
                        tensor_f16 = tensor.to(torch.float16).cpu().numpy()
                        writer.add_tensor(name, tensor_f16)
                        
                        if progress_callback and idx % 10 == 0:
                            progress = 0.5 + (idx / total_tensors) * 0.4
                            progress_callback(progress, f"Writing tensor {idx+1}/{total_tensors}")
                    
                    # Write tokenizer vocab
                    if hasattr(tokenizer, 'get_vocab'):
                        vocab = tokenizer.get_vocab()
                        writer.add_vocab(list(vocab.keys()))
                    
                    if progress_callback:
                        progress_callback(0.95, "Finalizing GGUF file...")
                    
                    # Finalize
                    writer.write_header_to_file()
                    writer.write_kv_data_to_file()
                    writer.write_tensors_to_file()
                    writer.close()
                    
                    self.logger.info(f"Successfully created GGUF file: {output_path}")
                    return True
                    
                except ImportError:
                    self.logger.error("gguf library not installed. Install with: pip install gguf")
                    if progress_callback:
                        progress_callback(0, "Error: gguf library required")
                    return False
                    
            except ImportError:
                self.logger.error("transformers library not installed")
                if progress_callback:
                    progress_callback(0, "Error: transformers library required")
                return False
            
        except Exception as e:
            self.logger.error(f"F16 conversion failed: {str(e)}")
            if progress_callback:
                progress_callback(0, f"Error: {str(e)}")
            return False
    
    async def _quantize_gguf(
        self,
        input_path: Path,
        output_path: Path,
        quantization: QuantizationLevel,
        progress_callback: Optional[Callable[[float, str], None]] = None
    ) -> bool:
        """Quantize an existing GGUF file using llama.cpp quantize tool"""
        try:
            self.logger.info(f"Quantizing to {quantization.value}...")
            
            if progress_callback:
                progress_callback(0.7, f"Quantizing to {quantization.value}...")
            
            # Check if llama.cpp quantize tool is available
            quantize_cmd = self._find_quantize_tool()
            
            if not quantize_cmd:
                # Fallback to Python-based quantization
                return await self._quantize_python(
                    input_path, output_path, quantization, progress_callback
                )
            
            # Run llama.cpp quantize tool
            cmd = [
                quantize_cmd,
                str(input_path),
                str(output_path),
                quantization.value
            ]
            
            if progress_callback:
                progress_callback(0.75, "Running quantization...")
            
            # Run in subprocess
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode == 0:
                if progress_callback:
                    progress_callback(0.95, "Quantization complete")
                self.logger.info(f"Successfully quantized to {output_path}")
                return True
            else:
                error_msg = stderr.decode() if stderr else "Unknown error"
                self.logger.error(f"Quantization failed: {error_msg}")
                if progress_callback:
                    progress_callback(0, f"Error: {error_msg}")
                return False
            
        except Exception as e:
            self.logger.error(f"Quantization failed: {str(e)}")
            if progress_callback:
                progress_callback(0, f"Error: {str(e)}")
            return False
    
    async def _quantize_python(
        self,
        input_path: Path,
        output_path: Path,
        quantization: QuantizationLevel,
        progress_callback: Optional[Callable[[float, str], None]] = None
    ) -> bool:
        """Python-based quantization fallback"""
        try:
            import gguf
            import numpy as np
            
            if progress_callback:
                progress_callback(0.75, "Loading GGUF file...")
            
            # Read input GGUF
            reader = gguf.GGUFReader(str(input_path))
            
            # Create writer
            writer = gguf.GGUFWriter(str(output_path), reader.architecture)
            
            # Copy metadata
            for field in reader.fields.values():
                writer.add_key(field.name, field.parts)
            
            if progress_callback:
                progress_callback(0.80, "Quantizing tensors...")
            
            # Quantize tensors
            total_tensors = len(reader.tensors)
            for idx, tensor in enumerate(reader.tensors):
                quantized = self._quantize_tensor(
                    tensor.data,
                    quantization
                )
                writer.add_tensor(tensor.name, quantized)
                
                if progress_callback and idx % 10 == 0:
                    progress = 0.80 + (idx / total_tensors) * 0.15
                    progress_callback(progress, f"Quantizing {idx+1}/{total_tensors}")
            
            if progress_callback:
                progress_callback(0.95, "Writing output...")
            
            writer.write_header_to_file()
            writer.write_kv_data_to_file()
            writer.write_tensors_to_file()
            writer.close()
            
            return True
            
        except ImportError:
            self.logger.error("gguf library required for Python quantization")
            return False
        except Exception as e:
            self.logger.error(f"Python quantization failed: {str(e)}")
            return False
    
    def _quantize_tensor(self, data: np.ndarray, quantization: QuantizationLevel) -> np.ndarray:
        """Apply quantization to a tensor"""
        import numpy as np
        
        if quantization in [QuantizationLevel.F16, QuantizationLevel.F32]:
            return data.astype(np.float16 if quantization == QuantizationLevel.F16 else np.float32)
        
        # For integer quantization, apply uniform quantization
        # This is a simplified version - real implementation would be more sophisticated
        bits = int(quantization.value[1]) if quantization.value[1].isdigit() else 8
        max_val = 2 ** (bits - 1) - 1
        
        # Scale to quantization range
        data_min = data.min()
        data_max = data.max()
        scale = (data_max - data_min) / (2 * max_val)
        
        quantized = np.round((data - data_min) / scale - max_val)
        quantized = np.clip(quantized, -max_val, max_val).astype(np.int8)
        
        return quantized
    
    def _find_quantize_tool(self) -> Optional[str]:
        """Find llama.cpp quantize executable"""
        import shutil
        
        # Look for quantize in PATH
        quantize_cmd = shutil.which("quantize")
        if quantize_cmd:
            return quantize_cmd
        
        # Look in common locations
        common_paths = [
            "quantize.exe",  # Windows
            "./quantize",
            "../llama.cpp/quantize",
            "~/llama.cpp/quantize"
        ]
        
        for path in common_paths:
            expanded = Path(path).expanduser()
            if expanded.exists():
                return str(expanded)
        
        return None
    
    def _validate_model_format(self, path: Path) -> bool:
        """Validate that the model is in a supported format"""
        if path.is_dir():
            # Check for SafeTensors or PyTorch files
            has_safetensors = any(path.glob("*.safetensors"))
            has_pytorch = any(path.glob("*.bin"))
            has_config = (path / "config.json").exists()
            
            return (has_safetensors or has_pytorch) and has_config
        
        return False
    
    def get_quantization_info(self, quantization: QuantizationLevel) -> Dict[str, Any]:
        """
        Get information about a quantization level.
        
        Args:
            quantization: Quantization level
            
        Returns:
            Dict with quantization info
        """
        info = {
            QuantizationLevel.Q2_K: {
                "size_ratio": 0.15,
                "quality": "Lowest",
                "description": "Smallest size, significant quality loss"
            },
            QuantizationLevel.Q3_K_M: {
                "size_ratio": 0.20,
                "quality": "Low",
                "description": "Small size, noticeable quality loss"
            },
            QuantizationLevel.Q4_K_M: {
                "size_ratio": 0.27,
                "quality": "Medium",
                "description": "Good balance of size and quality"
            },
            QuantizationLevel.Q5_K_M: {
                "size_ratio": 0.33,
                "quality": "Good",
                "description": "Better quality, larger size"
            },
            QuantizationLevel.Q6_K: {
                "size_ratio": 0.40,
                "quality": "High",
                "description": "High quality, minor quality loss"
            },
            QuantizationLevel.Q8_0: {
                "size_ratio": 0.53,
                "quality": "Very High",
                "description": "Near-original quality"
            },
            QuantizationLevel.F16: {
                "size_ratio": 0.50,
                "quality": "Original",
                "description": "Full precision float16"
            },
            QuantizationLevel.F32: {
                "size_ratio": 1.00,
                "quality": "Original",
                "description": "Full precision float32"
            }
        }
        
        return info.get(quantization, {"size_ratio": 1.0, "quality": "Unknown", "description": ""})


# Singleton instance
quantization_service = QuantizationService()

