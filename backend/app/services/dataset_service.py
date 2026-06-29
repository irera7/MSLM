"""
Dataset management service for training and fine-tuning.
Supports various dataset formats and preprocessing.
"""

import logging
from pathlib import Path
from typing import Optional, Dict, Any, List
from enum import Enum
import json
from datetime import datetime

logger = logging.getLogger(__name__)


class DatasetFormat(str, Enum):
    """Supported dataset formats"""
    JSON = "json"
    JSONL = "jsonl"
    CSV = "csv"
    PARQUET = "parquet"
    TEXT = "text"
    ALPACA = "alpaca"
    SHAREGPT = "sharegpt"


class DatasetType(str, Enum):
    """Dataset types"""
    INSTRUCTION = "instruction"
    CHAT = "chat"
    COMPLETION = "completion"
    CLASSIFICATION = "classification"
    QA = "qa"


class DatasetService:
    """Service for managing datasets"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.datasets: Dict[str, Dict[str, Any]] = {}
    
    async def create_dataset(
        self,
        name: str,
        dataset_type: DatasetType,
        description: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a new dataset.
        
        Args:
            name: Dataset name
            dataset_type: Type of dataset
            description: Optional description
            
        Returns:
            Dataset info
        """
        try:
            from app.core.config import settings
            
            dataset_dir = Path(settings.MODELS_DIR) / "datasets" / name
            dataset_dir.mkdir(parents=True, exist_ok=True)
            
            dataset_info = {
                "name": name,
                "type": dataset_type,
                "description": description,
                "path": str(dataset_dir),
                "created_at": datetime.utcnow().isoformat(),
                "num_samples": 0,
                "format": None,
                "metadata": {}
            }
            
            # Save dataset info
            info_file = dataset_dir / "dataset_info.json"
            with open(info_file, 'w') as f:
                json.dump(dataset_info, f, indent=2)
            
            self.datasets[name] = dataset_info
            
            self.logger.info(f"Created dataset: {name}")
            
            return dataset_info
            
        except Exception as e:
            self.logger.error(f"Failed to create dataset: {str(e)}")
            raise
    
    async def load_dataset(
        self,
        path: str,
        format: DatasetFormat,
        name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Load an existing dataset from file.
        
        Args:
            path: Path to dataset file
            format: Dataset format
            name: Optional name for dataset
            
        Returns:
            Dataset info
        """
        try:
            dataset_path = Path(path)
            
            if not dataset_path.exists():
                raise FileNotFoundError(f"Dataset not found: {path}")
            
            name = name or dataset_path.stem
            
            # Load based on format
            if format == DatasetFormat.JSON:
                with open(dataset_path) as f:
                    data = json.load(f)
                    num_samples = len(data) if isinstance(data, list) else 1
                    
            elif format == DatasetFormat.JSONL:
                num_samples = sum(1 for _ in open(dataset_path))
                
            elif format == DatasetFormat.CSV:
                try:
                    import pandas as pd
                    df = pd.read_csv(dataset_path)
                    num_samples = len(df)
                except ImportError:
                    num_samples = sum(1 for _ in open(dataset_path)) - 1  # -1 for header
                    
            elif format == DatasetFormat.TEXT:
                with open(dataset_path) as f:
                    num_samples = len(f.read().split('\n\n'))  # Assume double newline separates samples
            
            else:
                num_samples = 0
            
            dataset_info = {
                "name": name,
                "path": str(dataset_path),
                "format": format,
                "num_samples": num_samples,
                "size_bytes": dataset_path.stat().st_size,
                "loaded_at": datetime.utcnow().isoformat()
            }
            
            self.datasets[name] = dataset_info
            
            self.logger.info(f"Loaded dataset: {name} ({num_samples} samples)")
            
            return dataset_info
            
        except Exception as e:
            self.logger.error(f"Failed to load dataset: {str(e)}")
            raise
    
    async def add_samples(
        self,
        dataset_name: str,
        samples: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Add samples to a dataset.
        
        Args:
            dataset_name: Dataset name
            samples: List of samples to add
            
        Returns:
            Updated dataset info
        """
        try:
            if dataset_name not in self.datasets:
                raise ValueError(f"Dataset not found: {dataset_name}")
            
            dataset_info = self.datasets[dataset_name]
            dataset_path = Path(dataset_info["path"])
            
            # Append to dataset file
            samples_file = dataset_path / "samples.jsonl"
            
            with open(samples_file, 'a') as f:
                for sample in samples:
                    f.write(json.dumps(sample) + '\n')
            
            dataset_info["num_samples"] += len(samples)
            dataset_info["updated_at"] = datetime.utcnow().isoformat()
            
            # Update info file
            info_file = dataset_path / "dataset_info.json"
            with open(info_file, 'w') as f:
                json.dump(dataset_info, f, indent=2)
            
            self.logger.info(f"Added {len(samples)} samples to {dataset_name}")
            
            return dataset_info
            
        except Exception as e:
            self.logger.error(f"Failed to add samples: {str(e)}")
            raise
    
    async def get_samples(
        self,
        dataset_name: str,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        Get samples from a dataset.
        
        Args:
            dataset_name: Dataset name
            limit: Maximum number of samples
            offset: Starting position
            
        Returns:
            List of samples
        """
        try:
            if dataset_name not in self.datasets:
                raise ValueError(f"Dataset not found: {dataset_name}")
            
            dataset_info = self.datasets[dataset_name]
            dataset_path = Path(dataset_info["path"])
            
            samples_file = dataset_path / "samples.jsonl"
            
            if not samples_file.exists():
                return []
            
            samples = []
            
            with open(samples_file) as f:
                for i, line in enumerate(f):
                    if i < offset:
                        continue
                    if len(samples) >= limit:
                        break
                    
                    sample = json.loads(line)
                    samples.append(sample)
            
            return samples
            
        except Exception as e:
            self.logger.error(f"Failed to get samples: {str(e)}")
            raise
    
    async def split_dataset(
        self,
        dataset_name: str,
        train_ratio: float = 0.8,
        val_ratio: float = 0.1,
        test_ratio: float = 0.1
    ) -> Dict[str, Any]:
        """
        Split dataset into train/val/test sets.
        
        Args:
            dataset_name: Dataset name
            train_ratio: Training set ratio
            val_ratio: Validation set ratio
            test_ratio: Test set ratio
            
        Returns:
            Split information
        """
        try:
            if abs(train_ratio + val_ratio + test_ratio - 1.0) > 0.001:
                raise ValueError("Ratios must sum to 1.0")
            
            if dataset_name not in self.datasets:
                raise ValueError(f"Dataset not found: {dataset_name}")
            
            dataset_info = self.datasets[dataset_name]
            num_samples = dataset_info["num_samples"]
            
            train_size = int(num_samples * train_ratio)
            val_size = int(num_samples * val_ratio)
            test_size = num_samples - train_size - val_size
            
            split_info = {
                "total_samples": num_samples,
                "train": {"size": train_size, "ratio": train_ratio},
                "validation": {"size": val_size, "ratio": val_ratio},
                "test": {"size": test_size, "ratio": test_ratio}
            }
            
            dataset_info["split"] = split_info
            
            self.logger.info(f"Split dataset {dataset_name}: train={train_size}, val={val_size}, test={test_size}")
            
            return split_info
            
        except Exception as e:
            self.logger.error(f"Failed to split dataset: {str(e)}")
            raise
    
    async def preprocess_dataset(
        self,
        dataset_name: str,
        operations: List[str]
    ) -> Dict[str, Any]:
        """
        Apply preprocessing operations to dataset.
        
        Args:
            dataset_name: Dataset name
            operations: List of operations (e.g., ["lowercase", "remove_punctuation"])
            
        Returns:
            Preprocessing info
        """
        try:
            if dataset_name not in self.datasets:
                raise ValueError(f"Dataset not found: {dataset_name}")
            
            dataset_info = self.datasets[dataset_name]
            
            preprocessing_info = {
                "operations": operations,
                "applied_at": datetime.utcnow().isoformat()
            }
            
            dataset_info["preprocessing"] = preprocessing_info
            
            self.logger.info(f"Applied preprocessing to {dataset_name}: {operations}")
            
            return preprocessing_info
            
        except Exception as e:
            self.logger.error(f"Failed to preprocess dataset: {str(e)}")
            raise
    
    def list_datasets(self) -> List[Dict[str, Any]]:
        """List all datasets"""
        return list(self.datasets.values())
    
    def get_dataset_info(self, dataset_name: str) -> Optional[Dict[str, Any]]:
        """Get information about a dataset"""
        return self.datasets.get(dataset_name)
    
    async def delete_dataset(self, dataset_name: str) -> bool:
        """Delete a dataset"""
        try:
            if dataset_name not in self.datasets:
                return False
            
            dataset_info = self.datasets[dataset_name]
            dataset_path = Path(dataset_info["path"])
            
            # Delete dataset directory
            if dataset_path.exists() and dataset_path.is_dir():
                import shutil
                shutil.rmtree(dataset_path)
            
            del self.datasets[dataset_name]
            
            self.logger.info(f"Deleted dataset: {dataset_name}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to delete dataset: {str(e)}")
            return False
    
    async def export_dataset(
        self,
        dataset_name: str,
        output_path: str,
        format: DatasetFormat
    ) -> str:
        """
        Export dataset to a specific format.
        
        Args:
            dataset_name: Dataset name
            output_path: Output file path
            format: Output format
            
        Returns:
            Path to exported file
        """
        try:
            if dataset_name not in self.datasets:
                raise ValueError(f"Dataset not found: {dataset_name}")
            
            samples = await self.get_samples(dataset_name, limit=999999)
            
            output_file = Path(output_path)
            output_file.parent.mkdir(parents=True, exist_ok=True)
            
            if format == DatasetFormat.JSON:
                with open(output_file, 'w') as f:
                    json.dump(samples, f, indent=2)
                    
            elif format == DatasetFormat.JSONL:
                with open(output_file, 'w') as f:
                    for sample in samples:
                        f.write(json.dumps(sample) + '\n')
                        
            elif format == DatasetFormat.CSV:
                try:
                    import pandas as pd
                    df = pd.DataFrame(samples)
                    df.to_csv(output_file, index=False)
                except ImportError:
                    raise ImportError("pandas required for CSV export")
            
            self.logger.info(f"Exported dataset {dataset_name} to {output_file}")
            
            return str(output_file)
            
        except Exception as e:
            self.logger.error(f"Failed to export dataset: {str(e)}")
            raise


# Singleton instance
dataset_service = DatasetService()

