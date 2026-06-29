"""
System monitoring service.
Tracks CPU, GPU, RAM, VRAM, and performance metrics.
"""

import logging
import psutil
import platform
from typing import Dict, Any, Optional, List
from datetime import datetime
import threading
import time

logger = logging.getLogger(__name__)


class MonitoringService:
    """
    Monitors system resources and performance metrics.
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self._metrics_history: List[Dict[str, Any]] = []
        self._max_history = 100
        self._lock = threading.Lock()
        
        # Check GPU availability
        self.has_cuda = False
        self.has_nvidia_gpu = False
        try:
            import torch
            self.has_cuda = torch.cuda.is_available()
            if self.has_cuda:
                self.has_nvidia_gpu = True
                self.gpu_count = torch.cuda.device_count()
                self.logger.info(f"CUDA available with {self.gpu_count} GPU(s)")
        except ImportError:
            self.logger.debug("PyTorch not installed, GPU monitoring disabled")
        
        # Try GPUtil as fallback
        if not self.has_nvidia_gpu:
            try:
                import GPUtil
                gpus = GPUtil.getGPUs()
                if gpus:
                    self.has_nvidia_gpu = True
                    self.gpu_count = len(gpus)
                    self.logger.info(f"Found {self.gpu_count} GPU(s) via GPUtil")
            except:
                self.logger.debug("GPUtil not available")
    
    def get_system_info(self) -> Dict[str, Any]:
        """
        Get static system information.
        
        Returns:
            Dict with system info
        """
        info = {
            "platform": platform.system(),
            "platform_release": platform.release(),
            "platform_version": platform.version(),
            "architecture": platform.machine(),
            "processor": platform.processor(),
            "cpu_count": psutil.cpu_count(logical=False),
            "cpu_threads": psutil.cpu_count(logical=True),
            "ram_total_gb": round(psutil.virtual_memory().total / (1024**3), 2),
            "gpu_available": self.has_nvidia_gpu,
            "gpu_count": self.gpu_count if self.has_nvidia_gpu else 0,
        }
        
        # Add GPU info if available
        if self.has_nvidia_gpu:
            info["gpus"] = self._get_gpu_info()
        
        return info
    
    def get_current_metrics(self) -> Dict[str, Any]:
        """
        Get current system metrics.
        
        Returns:
            Dict with current metrics
        """
        # CPU metrics
        cpu_percent = psutil.cpu_percent(interval=0.1, percpu=False)
        cpu_freq = psutil.cpu_freq()
        
        # RAM metrics
        ram = psutil.virtual_memory()
        
        # Disk metrics
        disk = psutil.disk_usage('/')
        
        metrics = {
            "timestamp": datetime.now().isoformat(),
            "cpu": {
                "percent": cpu_percent,
                "frequency_mhz": cpu_freq.current if cpu_freq else 0,
                "count": psutil.cpu_count(logical=True)
            },
            "ram": {
                "total_gb": round(ram.total / (1024**3), 2),
                "used_gb": round(ram.used / (1024**3), 2),
                "available_gb": round(ram.available / (1024**3), 2),
                "percent": ram.percent
            },
            "disk": {
                "total_gb": round(disk.total / (1024**3), 2),
                "used_gb": round(disk.used / (1024**3), 2),
                "free_gb": round(disk.free / (1024**3), 2),
                "percent": disk.percent
            }
        }
        
        # GPU metrics
        if self.has_nvidia_gpu:
            metrics["gpu"] = self._get_gpu_metrics()
        
        # Store in history
        with self._lock:
            self._metrics_history.append(metrics)
            if len(self._metrics_history) > self._max_history:
                self._metrics_history.pop(0)
        
        return metrics
    
    def _get_gpu_info(self) -> List[Dict[str, Any]]:
        """Get static GPU information"""
        gpus = []
        
        if self.has_cuda:
            try:
                import torch
                for i in range(self.gpu_count):
                    props = torch.cuda.get_device_properties(i)
                    gpus.append({
                        "id": i,
                        "name": props.name,
                        "total_memory_gb": round(props.total_memory / (1024**3), 2),
                        "compute_capability": f"{props.major}.{props.minor}",
                        "multiprocessors": props.multi_processor_count
                    })
                return gpus
            except:
                pass
        
        # Fallback to GPUtil
        try:
            import GPUtil
            gpu_list = GPUtil.getGPUs()
            for gpu in gpu_list:
                gpus.append({
                    "id": gpu.id,
                    "name": gpu.name,
                    "total_memory_gb": round(gpu.memoryTotal / 1024, 2),
                    "uuid": gpu.uuid
                })
        except:
            pass
        
        return gpus
    
    def _get_gpu_metrics(self) -> List[Dict[str, Any]]:
        """Get current GPU metrics"""
        metrics = []
        
        if self.has_cuda:
            try:
                import torch
                for i in range(self.gpu_count):
                    allocated = torch.cuda.memory_allocated(i) / (1024**3)
                    reserved = torch.cuda.memory_reserved(i) / (1024**3)
                    total = torch.cuda.get_device_properties(i).total_memory / (1024**3)
                    
                    metrics.append({
                        "id": i,
                        "memory_allocated_gb": round(allocated, 2),
                        "memory_reserved_gb": round(reserved, 2),
                        "memory_total_gb": round(total, 2),
                        "memory_percent": round((allocated / total) * 100, 2) if total > 0 else 0
                    })
                return metrics
            except:
                pass
        
        # Fallback to GPUtil
        try:
            import GPUtil
            gpu_list = GPUtil.getGPUs()
            for gpu in gpu_list:
                metrics.append({
                    "id": gpu.id,
                    "memory_used_gb": round(gpu.memoryUsed / 1024, 2),
                    "memory_total_gb": round(gpu.memoryTotal / 1024, 2),
                    "memory_percent": round(gpu.memoryUtil * 100, 2),
                    "utilization_percent": round(gpu.load * 100, 2),
                    "temperature_c": gpu.temperature
                })
        except:
            pass
        
        return metrics
    
    def get_metrics_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Get metrics history.
        
        Args:
            limit: Maximum number of entries to return
            
        Returns:
            List of metrics
        """
        with self._lock:
            return self._metrics_history[-limit:] if limit else self._metrics_history.copy()
    
    def get_process_metrics(self) -> Dict[str, Any]:
        """
        Get metrics for current process.
        
        Returns:
            Dict with process metrics
        """
        process = psutil.Process()
        
        with process.oneshot():
            cpu_times = process.cpu_times()
            memory_info = process.memory_info()
            
            return {
                "pid": process.pid,
                "cpu_percent": process.cpu_percent(),
                "cpu_times": {
                    "user": cpu_times.user,
                    "system": cpu_times.system
                },
                "memory": {
                    "rss_mb": round(memory_info.rss / (1024**2), 2),
                    "vms_mb": round(memory_info.vms / (1024**2), 2),
                },
                "threads": process.num_threads(),
                "open_files": len(process.open_files()),
                "connections": len(process.connections()),
                "create_time": datetime.fromtimestamp(process.create_time()).isoformat()
            }
    
    def clear_history(self) -> None:
        """Clear metrics history"""
        with self._lock:
            self._metrics_history.clear()
            self.logger.info("Metrics history cleared")


# Singleton instance
monitoring_service = MonitoringService()

