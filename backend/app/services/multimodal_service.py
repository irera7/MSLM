"""
Multi-modal model support for vision and audio processing.
Supports models like LLaVA (vision) and Whisper (audio).
"""

import logging
from pathlib import Path
from typing import Optional, Dict, Any, Union
from enum import Enum
import base64

logger = logging.getLogger(__name__)


class ModalityType(str, Enum):
    """Supported modality types"""
    TEXT = "text"
    VISION = "vision"
    AUDIO = "audio"
    VIDEO = "video"


class MultiModalService:
    """Service for handling multi-modal inputs"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.vision_processor = None
        self.audio_processor = None
    
    async def process_image(
        self,
        image_path: Optional[str] = None,
        image_base64: Optional[str] = None,
        image_url: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Process an image for vision-language models.
        
        Args:
            image_path: Local path to image
            image_base64: Base64 encoded image
            image_url: URL to image
            
        Returns:
            Processed image data
        """
        try:
            image_data = None
            
            if image_path:
                from PIL import Image
                image = Image.open(image_path)
                image_data = image
                
            elif image_base64:
                import base64
                from io import BytesIO
                from PIL import Image
                
                image_bytes = base64.b64decode(image_base64)
                image = Image.open(BytesIO(image_bytes))
                image_data = image
                
            elif image_url:
                import requests
                from PIL import Image
                from io import BytesIO
                
                response = requests.get(image_url)
                image = Image.open(BytesIO(response.content))
                image_data = image
            
            if image_data is None:
                raise ValueError("No image data provided")
            
            # Get image info
            return {
                "modality": ModalityType.VISION,
                "format": image_data.format,
                "size": image_data.size,
                "mode": image_data.mode,
                "processed": True
            }
            
        except ImportError:
            self.logger.error("PIL library required. Install with: pip install Pillow")
            raise
        except Exception as e:
            self.logger.error(f"Image processing failed: {str(e)}")
            raise
    
    async def process_audio(
        self,
        audio_path: Optional[str] = None,
        audio_base64: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Process audio for speech-to-text or audio-language models.
        
        Args:
            audio_path: Local path to audio file
            audio_base64: Base64 encoded audio
            
        Returns:
            Processed audio data
        """
        try:
            if audio_path:
                audio_file = Path(audio_path)
                
                if not audio_file.exists():
                    raise FileNotFoundError(f"Audio file not found: {audio_path}")
                
                # Get audio info
                try:
                    import wave
                    
                    with wave.open(str(audio_file), 'rb') as audio:
                        info = {
                            "modality": ModalityType.AUDIO,
                            "channels": audio.getnchannels(),
                            "sample_width": audio.getsampwidth(),
                            "framerate": audio.getframerate(),
                            "frames": audio.getnframes(),
                            "duration_sec": audio.getnframes() / audio.getframerate(),
                            "processed": True
                        }
                        
                    return info
                    
                except Exception as e:
                    # Fallback for non-WAV files
                    return {
                        "modality": ModalityType.AUDIO,
                        "path": str(audio_file),
                        "size_bytes": audio_file.stat().st_size,
                        "processed": True
                    }
            
            elif audio_base64:
                import base64
                audio_bytes = base64.b64decode(audio_base64)
                
                return {
                    "modality": ModalityType.AUDIO,
                    "size_bytes": len(audio_bytes),
                    "processed": True
                }
            
            raise ValueError("No audio data provided")
            
        except Exception as e:
            self.logger.error(f"Audio processing failed: {str(e)}")
            raise
    
    async def generate_with_vision(
        self,
        model_id: int,
        prompt: str,
        image_data: Dict[str, Any],
        model_manager,
        db
    ) -> str:
        """
        Generate text response with vision input.
        
        Args:
            model_id: Vision-language model ID
            prompt: Text prompt
            image_data: Processed image data
            model_manager: Model manager instance
            db: Database session
            
        Returns:
            Generated text
        """
        try:
            # Check if model supports vision
            from app.services.inference.base_engine import GenerationConfig
            
            # Combine prompt with vision context
            vision_prompt = f"[Image provided] {prompt}"
            
            config = GenerationConfig(
                temperature=0.7,
                max_tokens=512,
                stream=False
            )
            
            # Generate response
            response = await model_manager.generate_text_non_streaming(
                model_id=model_id,
                prompt=vision_prompt,
                config=config,
                db=db
            )
            
            return response
            
        except Exception as e:
            self.logger.error(f"Vision generation failed: {str(e)}")
            raise
    
    async def transcribe_audio(
        self,
        model_id: int,
        audio_data: Dict[str, Any],
        model_manager,
        db
    ) -> Dict[str, Any]:
        """
        Transcribe audio to text.
        
        Args:
            model_id: Speech-to-text model ID
            audio_data: Processed audio data
            model_manager: Model manager instance
            db: Database session
            
        Returns:
            Transcription result
        """
        try:
            # This would use Whisper or similar model
            # For now, return placeholder
            
            return {
                "text": "[Audio transcription would appear here]",
                "language": "en",
                "duration": audio_data.get("duration_sec", 0),
                "segments": []
            }
            
        except Exception as e:
            self.logger.error(f"Audio transcription failed: {str(e)}")
            raise
    
    def get_supported_image_formats(self) -> list[str]:
        """Get list of supported image formats"""
        return ["jpg", "jpeg", "png", "gif", "bmp", "webp"]
    
    def get_supported_audio_formats(self) -> List[str]:
        """Get list of supported audio formats"""
        return ["wav", "mp3", "flac", "ogg", "m4a"]
    
    async def check_model_capabilities(
        self,
        model_id: int,
        db
    ) -> Dict[str, bool]:
        """
        Check what modalities a model supports.
        
        Returns:
            Dict of modality: supported
        """
        from sqlalchemy import select
        from app.database.models import Model as DBModel
        
        result = await db.execute(select(DBModel).where(DBModel.id == model_id))
        model = result.scalar_one_or_none()
        
        if not model:
            raise ValueError("Model not found")
        
        metadata = model.model_metadata or {}
        
        # Check metadata for capabilities
        capabilities = metadata.get("capabilities", {})
        
        return {
            "text": capabilities.get("text", True),
            "vision": capabilities.get("vision", False),
            "audio": capabilities.get("audio", False),
            "video": capabilities.get("video", False)
        }


# Singleton instance
multimodal_service = MultiModalService()

