"""
Plugin system for custom inference engines.
Allows users to add support for additional model formats.
"""

import logging
import importlib.util
from pathlib import Path
from typing import Dict, Any, Optional, List, Type
import json

from app.services.inference.base_engine import InferenceEngine, EngineRegistry

logger = logging.getLogger(__name__)


class PluginInfo:
    """Information about a plugin"""
    
    def __init__(
        self,
        name: str,
        version: str,
        author: str,
        description: str,
        engine_class: Type[InferenceEngine],
        supported_formats: List[str]
    ):
        self.name = name
        self.version = version
        self.author = author
        self.description = description
        self.engine_class = engine_class
        self.supported_formats = supported_formats


class PluginManager:
    """
    Manages custom inference engine plugins.
    """
    
    def __init__(self, plugin_dir: str = "plugins"):
        self.logger = logging.getLogger(__name__)
        self.plugin_dir = Path(plugin_dir)
        self.plugins: Dict[str, PluginInfo] = {}
        
        # Create plugin directory if it doesn't exist
        self.plugin_dir.mkdir(parents=True, exist_ok=True)
        
        # Create example plugin manifest
        self._create_example_manifest()
    
    def _create_example_manifest(self):
        """Create example plugin manifest"""
        example_manifest = self.plugin_dir / "example_plugin.json.example"
        
        if not example_manifest.exists():
            manifest_data = {
                "name": "ExampleEngine",
                "version": "1.0.0",
                "author": "Your Name",
                "description": "Example custom inference engine",
                "entry_point": "example_plugin.py",
                "class_name": "ExampleEngine",
                "supported_formats": ["CUSTOM"]
            }
            
            with open(example_manifest, 'w') as f:
                json.dump(manifest_data, f, indent=2)
    
    def load_plugin(self, plugin_path: str) -> bool:
        """
        Load a plugin from a directory.
        
        Args:
            plugin_path: Path to plugin directory
            
        Returns:
            bool: True if loaded successfully
        """
        try:
            plugin_path = Path(plugin_path)
            
            if not plugin_path.exists():
                self.logger.error(f"Plugin path does not exist: {plugin_path}")
                return False
            
            # Read manifest
            manifest_path = plugin_path / "manifest.json"
            if not manifest_path.exists():
                self.logger.error(f"Plugin manifest not found: {manifest_path}")
                return False
            
            with open(manifest_path, 'r') as f:
                manifest = json.load(f)
            
            # Validate manifest
            required_fields = ["name", "version", "entry_point", "class_name", "supported_formats"]
            for field in required_fields:
                if field not in manifest:
                    self.logger.error(f"Plugin manifest missing required field: {field}")
                    return False
            
            # Load plugin module
            entry_point = plugin_path / manifest["entry_point"]
            if not entry_point.exists():
                self.logger.error(f"Plugin entry point not found: {entry_point}")
                return False
            
            spec = importlib.util.spec_from_file_location(manifest["name"], entry_point)
            if spec is None or spec.loader is None:
                self.logger.error(f"Failed to load plugin spec: {entry_point}")
                return False
            
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            # Get engine class
            if not hasattr(module, manifest["class_name"]):
                self.logger.error(f"Plugin class not found: {manifest['class_name']}")
                return False
            
            engine_class = getattr(module, manifest["class_name"])
            
            # Validate engine class
            if not issubclass(engine_class, InferenceEngine):
                self.logger.error(f"Plugin class must inherit from InferenceEngine")
                return False
            
            # Register with engine registry
            EngineRegistry.register(engine_class)
            
            # Create plugin info
            plugin_info = PluginInfo(
                name=manifest["name"],
                version=manifest["version"],
                author=manifest.get("author", "Unknown"),
                description=manifest.get("description", ""),
                engine_class=engine_class,
                supported_formats=manifest["supported_formats"]
            )
            
            self.plugins[manifest["name"]] = plugin_info
            
            self.logger.info(f"Loaded plugin: {manifest['name']} v{manifest['version']}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to load plugin: {str(e)}")
            return False
    
    def load_all_plugins(self) -> int:
        """
        Load all plugins from the plugin directory.
        
        Returns:
            int: Number of plugins loaded
        """
        if not self.plugin_dir.exists():
            self.logger.warning(f"Plugin directory does not exist: {self.plugin_dir}")
            return 0
        
        loaded_count = 0
        
        for item in self.plugin_dir.iterdir():
            if item.is_dir():
                manifest_path = item / "manifest.json"
                if manifest_path.exists():
                    if self.load_plugin(str(item)):
                        loaded_count += 1
        
        if loaded_count > 0:
            self.logger.info(f"Loaded {loaded_count} plugin(s)")
        
        return loaded_count
    
    def unload_plugin(self, plugin_name: str) -> bool:
        """
        Unload a plugin.
        
        Args:
            plugin_name: Name of the plugin
            
        Returns:
            bool: True if unloaded successfully
        """
        if plugin_name not in self.plugins:
            self.logger.warning(f"Plugin not found: {plugin_name}")
            return False
        
        # Note: We can't actually unregister from EngineRegistry in this simple implementation
        # In a production system, you'd want to implement unregistration
        
        del self.plugins[plugin_name]
        self.logger.info(f"Unloaded plugin: {plugin_name}")
        return True
    
    def get_plugin_info(self, plugin_name: str) -> Optional[PluginInfo]:
        """
        Get information about a plugin.
        
        Args:
            plugin_name: Name of the plugin
            
        Returns:
            Optional[PluginInfo]: Plugin info or None
        """
        return self.plugins.get(plugin_name)
    
    def list_plugins(self) -> List[Dict[str, Any]]:
        """
        List all loaded plugins.
        
        Returns:
            List of plugin information
        """
        return [
            {
                "name": info.name,
                "version": info.version,
                "author": info.author,
                "description": info.description,
                "supported_formats": info.supported_formats
            }
            for info in self.plugins.values()
        ]
    
    def get_plugin_for_format(self, format: str) -> Optional[Type[InferenceEngine]]:
        """
        Get plugin engine class for a specific format.
        
        Args:
            format: Model format
            
        Returns:
            Optional[Type[InferenceEngine]]: Engine class or None
        """
        format_upper = format.upper()
        
        for plugin_info in self.plugins.values():
            if format_upper in [f.upper() for f in plugin_info.supported_formats]:
                return plugin_info.engine_class
        
        return None


# Singleton instance
plugin_manager = PluginManager()

