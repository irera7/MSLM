"""
Model presets for different use cases.
"""

from typing import Dict, Any

# Preset configurations
PRESETS: Dict[str, Dict[str, Any]] = {
    "Creative": {
        "temperature": 0.9,
        "top_p": 0.95,
        "top_k": 50,
        "max_tokens": 2048,
        "repeat_penalty": 1.05,
        "description": "High creativity, diverse outputs, good for creative writing"
    },
    "Balanced": {
        "temperature": 0.7,
        "top_p": 0.9,
        "top_k": 40,
        "max_tokens": 2048,
        "repeat_penalty": 1.1,
        "description": "Balanced between creativity and accuracy, general purpose"
    },
    "Precise": {
        "temperature": 0.3,
        "top_p": 0.85,
        "top_k": 20,
        "max_tokens": 2048,
        "repeat_penalty": 1.15,
        "description": "Low temperature, focused outputs, good for factual tasks"
    },
    "Coding": {
        "temperature": 0.2,
        "top_p": 0.90,
        "top_k": 30,
        "max_tokens": 4096,
        "repeat_penalty": 1.0,
        "description": "Optimized for code generation with low randomness"
    },
    "Chat": {
        "temperature": 0.8,
        "top_p": 0.92,
        "top_k": 45,
        "max_tokens": 1024,
        "repeat_penalty": 1.1,
        "description": "Natural conversation with moderate creativity"
    }
}


def get_preset(name: str) -> Dict[str, Any]:
    """
    Get a preset by name.
    
    Args:
        name: Preset name
        
    Returns:
        Dict with preset configuration
        
    Raises:
        KeyError: If preset not found
    """
    if name not in PRESETS:
        raise KeyError(f"Preset '{name}' not found. Available: {list(PRESETS.keys())}")
    
    return PRESETS[name].copy()


def list_presets() -> Dict[str, Dict[str, Any]]:
    """
    List all available presets.
    
    Returns:
        Dict of preset name -> configuration
    """
    return PRESETS.copy()


def apply_preset_to_session(preset_name: str) -> Dict[str, Any]:
    """
    Get session parameters from a preset.
    
    Args:
        preset_name: Name of the preset
        
    Returns:
        Dict with session parameters (excluding description)
    """
    preset = get_preset(preset_name)
    return {
        "temperature": preset["temperature"],
        "top_p": preset["top_p"],
        "top_k": preset["top_k"],
        "max_tokens": preset["max_tokens"],
        "repeat_penalty": preset["repeat_penalty"],
        "preset": preset_name
    }

