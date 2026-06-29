"""
Advanced model management service.
Supports versioning, comparison, benchmarking, and tagging.
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
import json
import time
import asyncio

from app.database.models import Model as DBModel

logger = logging.getLogger(__name__)


class ModelVersioning:
    """Handle model versioning"""
    
    @staticmethod
    async def create_version(
        db: AsyncSession,
        model_id: int,
        version: str,
        notes: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create a new version tag for a model"""
        result = await db.execute(
            select(DBModel).where(DBModel.id == model_id)
        )
        model = result.scalar_one_or_none()
        
        if not model:
            raise ValueError("Model not found")
        
        # Update metadata with version info
        metadata = model.model_metadata or {}
        
        if "versions" not in metadata:
            metadata["versions"] = []
        
        version_info = {
            "version": version,
            "created_at": datetime.utcnow().isoformat(),
            "notes": notes,
            "snapshot": {
                "name": model.name,
                "format": model.format,
                "size": model.size
            }
        }
        
        metadata["versions"].append(version_info)
        metadata["current_version"] = version
        
        model.model_metadata = metadata
        await db.commit()
        await db.refresh(model)
        
        return version_info
    
    @staticmethod
    async def list_versions(
        db: AsyncSession,
        model_id: int
    ) -> List[Dict[str, Any]]:
        """List all versions of a model"""
        result = await db.execute(
            select(DBModel).where(DBModel.id == model_id)
        )
        model = result.scalar_one_or_none()
        
        if not model:
            return []
        
        metadata = model.model_metadata or {}
        return metadata.get("versions", [])


class ModelComparison:
    """Compare multiple models"""
    
    @staticmethod
    async def compare_models(
        db: AsyncSession,
        model_ids: List[int]
    ) -> Dict[str, Any]:
        """Compare specifications of multiple models"""
        result = await db.execute(
            select(DBModel).where(DBModel.id.in_(model_ids))
        )
        models = result.scalars().all()
        
        if len(models) != len(model_ids):
            raise ValueError("Some models not found")
        
        comparison = {
            "models": [],
            "differences": [],
            "similarities": []
        }
        
        for model in models:
            comparison["models"].append({
                "id": model.id,
                "name": model.name,
                "format": model.format,
                "size": model.size,
                "size_mb": round(model.size / 1024 / 1024, 2),
                "source": model.source,
                "created_at": model.created_at.isoformat(),
                "metadata": model.model_metadata
            })
        
        # Analyze differences
        formats = set(m.format for m in models)
        sizes = [m.size for m in models]
        sources = set(m.source for m in models)
        
        if len(formats) > 1:
            comparison["differences"].append({
                "attribute": "format",
                "values": list(formats)
            })
        
        if max(sizes) / min(sizes) > 1.5:  # More than 50% difference
            comparison["differences"].append({
                "attribute": "size",
                "values": [f"{s/1024/1024:.2f} MB" for s in sizes]
            })
        
        if len(sources) > 1:
            comparison["differences"].append({
                "attribute": "source",
                "values": list(sources)
            })
        
        # Find similarities
        if len(formats) == 1:
            comparison["similarities"].append({
                "attribute": "format",
                "value": list(formats)[0]
            })
        
        return comparison
    
    @staticmethod
    async def compare_performance(
        db: AsyncSession,
        model_ids: List[int]
    ) -> Dict[str, Any]:
        """Compare performance metrics of models"""
        result = await db.execute(
            select(DBModel).where(DBModel.id.in_(model_ids))
        )
        models = result.scalars().all()
        
        performance = {
            "models": []
        }
        
        for model in models:
            metadata = model.model_metadata or {}
            benchmark = metadata.get("benchmark", {})
            
            performance["models"].append({
                "id": model.id,
                "name": model.name,
                "format": model.format,
                "benchmark": benchmark,
                "has_benchmark": bool(benchmark)
            })
        
        return performance


class ModelBenchmarking:
    """Benchmark model performance"""
    
    @staticmethod
    async def run_benchmark(
        model_id: int,
        model_manager,
        db: AsyncSession,
        num_prompts: int = 5
    ) -> Dict[str, Any]:
        """Run a simple benchmark on a model"""
        from app.services.inference.base_engine import GenerationConfig
        
        result = await db.execute(
            select(DBModel).where(DBModel.id == model_id)
        )
        model = result.scalar_one_or_none()
        
        if not model:
            raise ValueError("Model not found")
        
        logger.info(f"Starting benchmark for model {model_id}")
        
        # Test prompts
        test_prompts = [
            "Hello, how are you?",
            "Write a short poem.",
            "Explain quantum physics.",
            "What is 2+2?",
            "Tell me a joke."
        ][:num_prompts]
        
        results = {
            "model_id": model_id,
            "model_name": model.name,
            "format": model.format,
            "timestamp": datetime.utcnow().isoformat(),
            "prompts_tested": num_prompts,
            "metrics": []
        }
        
        config = GenerationConfig(
            temperature=0.7,
            max_tokens=100,
            stream=False
        )
        
        total_tokens = 0
        total_time = 0
        
        for idx, prompt in enumerate(test_prompts):
            try:
                start_time = time.time()
                
                # Generate response
                response = await model_manager.generate_text_non_streaming(
                    model_id=model_id,
                    prompt=prompt,
                    config=config,
                    db=db
                )
                
                end_time = time.time()
                duration = end_time - start_time
                
                # Count tokens (approximate)
                tokens = len(response.split())
                tokens_per_sec = tokens / duration if duration > 0 else 0
                
                results["metrics"].append({
                    "prompt": prompt,
                    "tokens": tokens,
                    "duration_sec": round(duration, 3),
                    "tokens_per_sec": round(tokens_per_sec, 2)
                })
                
                total_tokens += tokens
                total_time += duration
                
            except Exception as e:
                results["metrics"].append({
                    "prompt": prompt,
                    "error": str(e)
                })
        
        # Calculate averages
        results["summary"] = {
            "total_tokens": total_tokens,
            "total_time_sec": round(total_time, 3),
            "avg_tokens_per_sec": round(total_tokens / total_time, 2) if total_time > 0 else 0,
            "avg_time_per_prompt": round(total_time / num_prompts, 3)
        }
        
        # Save benchmark to model metadata
        metadata = model.model_metadata or {}
        metadata["benchmark"] = results
        metadata["last_benchmark"] = datetime.utcnow().isoformat()
        
        model.model_metadata = metadata
        await db.commit()
        
        logger.info(f"Benchmark completed for model {model_id}")
        
        return results


class ModelTagging:
    """Manage model tags and categories"""
    
    @staticmethod
    async def add_tags(
        db: AsyncSession,
        model_id: int,
        tags: List[str]
    ) -> List[str]:
        """Add tags to a model"""
        result = await db.execute(
            select(DBModel).where(DBModel.id == model_id)
        )
        model = result.scalar_one_or_none()
        
        if not model:
            raise ValueError("Model not found")
        
        metadata = model.model_metadata or {}
        
        existing_tags = set(metadata.get("tags", []))
        existing_tags.update(tags)
        
        metadata["tags"] = list(existing_tags)
        model.model_metadata = metadata
        
        await db.commit()
        await db.refresh(model)
        
        return metadata["tags"]
    
    @staticmethod
    async def remove_tags(
        db: AsyncSession,
        model_id: int,
        tags: List[str]
    ) -> List[str]:
        """Remove tags from a model"""
        result = await db.execute(
            select(DBModel).where(DBModel.id == model_id)
        )
        model = result.scalar_one_or_none()
        
        if not model:
            raise ValueError("Model not found")
        
        metadata = model.model_metadata or {}
        existing_tags = set(metadata.get("tags", []))
        
        for tag in tags:
            existing_tags.discard(tag)
        
        metadata["tags"] = list(existing_tags)
        model.model_metadata = metadata
        
        await db.commit()
        await db.refresh(model)
        
        return metadata["tags"]
    
    @staticmethod
    async def set_category(
        db: AsyncSession,
        model_id: int,
        category: str
    ) -> str:
        """Set category for a model"""
        result = await db.execute(
            select(DBModel).where(DBModel.id == model_id)
        )
        model = result.scalar_one_or_none()
        
        if not model:
            raise ValueError("Model not found")
        
        metadata = model.model_metadata or {}
        metadata["category"] = category
        model.model_metadata = metadata
        
        await db.commit()
        await db.refresh(model)
        
        return category
    
    @staticmethod
    async def search_by_tags(
        db: AsyncSession,
        tags: List[str],
        match_all: bool = False
    ) -> List[DBModel]:
        """Search models by tags"""
        result = await db.execute(select(DBModel))
        models = result.scalars().all()
        
        matching_models = []
        
        for model in models:
            metadata = model.model_metadata or {}
            model_tags = set(metadata.get("tags", []))
            search_tags = set(tags)
            
            if match_all:
                # All tags must match
                if search_tags.issubset(model_tags):
                    matching_models.append(model)
            else:
                # Any tag matches
                if search_tags.intersection(model_tags):
                    matching_models.append(model)
        
        return matching_models


# Singleton instances
model_versioning = ModelVersioning()
model_comparison = ModelComparison()
model_benchmarking = ModelBenchmarking()
model_tagging = ModelTagging()

