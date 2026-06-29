import asyncio
import aiohttp
from typing import Dict, Optional
from pathlib import Path
import logging
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update

from app.database.models import DownloadQueue as DBDownloadQueue, Model as DBModel
from app.database.database import AsyncSessionLocal
from app.core.config import settings

logger = logging.getLogger(__name__)


class DownloadManager:
    """Manages download queue with concurrent downloads and resume support"""
    
    def __init__(self):
        self.active_downloads: Dict[int, asyncio.Task] = {}
        self.lock = asyncio.Lock()
        self.max_concurrent = settings.MAX_CONCURRENT_DOWNLOADS
        self.chunk_size = settings.DOWNLOAD_CHUNK_SIZE
        self.logger = logging.getLogger(__name__)
    
    async def add_to_queue(
        self,
        url: str,
        destination: str,
        model_name: str,
        model_format: Optional[str],
        priority: int,
        metadata: Optional[dict],
        db: AsyncSession
    ) -> int:
        """Add a download to the queue"""
        download_entry = DBDownloadQueue(
            url=url,
            destination=destination,
            model_name=model_name,
            model_format=model_format,
            priority=priority,
            status="pending",
            model_metadata=metadata
        )
        
        db.add(download_entry)
        await db.commit()
        await db.refresh(download_entry)
        
        self.logger.info(f"Added download to queue: {model_name} (ID: {download_entry.id})")
        
        # Start processing queue with a NEW session (not the request's session)
        asyncio.create_task(self._process_queue())
        
        return download_entry.id
    
    async def _process_queue(self):
        """Process pending downloads"""
        async with self.lock:
            # Check if we can start more downloads
            if len(self.active_downloads) >= self.max_concurrent:
                return
            
            # Create a new session for this background task
            async with AsyncSessionLocal() as db:
                # Get pending downloads
                result = await db.execute(
                    select(DBDownloadQueue)
                    .where(DBDownloadQueue.status == "pending")
                    .order_by(DBDownloadQueue.priority.desc(), DBDownloadQueue.created_at)
                    .limit(self.max_concurrent - len(self.active_downloads))
                )
                pending = result.scalars().all()
                
                for download in pending:
                    if download.id not in self.active_downloads:
                        task = asyncio.create_task(self._download_file(download.id))
                        self.active_downloads[download.id] = task
    
    async def _download_file(self, download_id: int):
        """Download a file with progress tracking and resume support"""
        # Create a new session for this download task
        async with AsyncSessionLocal() as db:
            try:
                # Get download entry
                result = await db.execute(
                    select(DBDownloadQueue).where(DBDownloadQueue.id == download_id)
                )
                download = result.scalar_one_or_none()
                
                if not download:
                    return
                
                # Update status
                await db.execute(
                    update(DBDownloadQueue)
                    .where(DBDownloadQueue.id == download_id)
                    .values(status="downloading", started_at=datetime.utcnow())
                )
                await db.commit()
                
                self.logger.info(f"Starting download: {download.model_name}")
                
                # Check if this is a full repo download (for HuggingFace models)
                metadata = download.model_metadata or {}
                is_full_repo = metadata.get('download_type') == 'full_repo'
                
                if is_full_repo:
                    # Download full HuggingFace repo using snapshot_download
                    await self._download_hf_repo(download_id, download, db)
                else:
                    # Download single file
                    await self._download_single_file(download_id, download, db)
                
                self.logger.info(f"Download completed: {download.model_name}")
                
                # Create model entry
                await self._create_model_entry(download, db)
                
            except asyncio.CancelledError:
                # Download was cancelled
                await db.execute(
                    update(DBDownloadQueue)
                    .where(DBDownloadQueue.id == download_id)
                    .values(status="cancelled")
                )
                await db.commit()
                self.logger.info(f"Download cancelled: {download_id}")
                
            except Exception as e:
                self.logger.error(f"Download failed: {str(e)}")
                await db.execute(
                    update(DBDownloadQueue)
                    .where(DBDownloadQueue.id == download_id)
                    .values(status="failed", error_message=str(e))
                )
                await db.commit()
                
            finally:
                # Remove from active downloads
                if download_id in self.active_downloads:
                    del self.active_downloads[download_id]
                
                # Process next in queue
                asyncio.create_task(self._process_queue())
    
    async def _download_hf_repo(self, download_id: int, download: DBDownloadQueue, db: AsyncSession):
        """Download full HuggingFace repository using snapshot_download"""
        from huggingface_hub import snapshot_download
        from tqdm import tqdm
        
        # Determine destination directory
        repo_name = download.model_name
        dest_dir = settings.MODELS_DIR / repo_name
        dest_dir.mkdir(parents=True, exist_ok=True)
        
        self.logger.info(f"Downloading HuggingFace repo: {download.url} to {dest_dir}")
        
        try:
            # Update status to show download started
            await db.execute(
                update(DBDownloadQueue)
                .where(DBDownloadQueue.id == download_id)
                .values(progress=5.0)  # Show some initial progress
            )
            await db.commit()
            
            # Create a progress callback for tqdm
            class ProgressCallback:
                def __init__(self, download_id, db_session):
                    self.download_id = download_id
                    self.db = db_session
                    self.last_update = 0
                    self.total_files = 0
                    self.downloaded_files = 0
                
                def __call__(self, t):
                    """Called by tqdm for progress updates"""
                    self.downloaded_files += 1
                    if self.total_files > 0:
                        progress = (self.downloaded_files / self.total_files) * 90 + 5  # 5-95%
                        
                        # Update every file or every 5%
                        if progress - self.last_update >= 5:
                            import asyncio
                            asyncio.create_task(self._update_progress(progress))
                            self.last_update = progress
                
                async def _update_progress(self, progress):
                    try:
                        async with AsyncSessionLocal() as new_db:
                            await new_db.execute(
                                update(DBDownloadQueue)
                                .where(DBDownloadQueue.id == self.download_id)
                                .values(progress=progress)
                            )
                            await new_db.commit()
                    except:
                        pass  # Ignore errors in progress updates
            
            # Download the full repository
            # Note: snapshot_download is synchronous, we should run it in executor
            import asyncio
            from functools import partial
            
            # Update progress periodically in background
            progress_task = asyncio.create_task(self._update_download_progress(download_id, db))
            
            try:
                loop = asyncio.get_event_loop()
                downloaded_path = await loop.run_in_executor(
                    None,
                    partial(
                        snapshot_download,
                        repo_id=download.url,  # URL field contains the repo ID
                        local_dir=str(dest_dir),
                        local_dir_use_symlinks=False,
                        resume_download=True,
                    )
                )
            finally:
                progress_task.cancel()
            
            # Update as completed
            await db.execute(
                update(DBDownloadQueue)
                .where(DBDownloadQueue.id == download_id)
                .values(
                    status="completed",
                    progress=100.0,
                    destination=str(dest_dir),
                    completed_at=datetime.utcnow()
                )
            )
            await db.commit()
            
            self.logger.info(f"HuggingFace repo downloaded successfully to: {dest_dir}")
            
        except Exception as e:
            self.logger.error(f"Failed to download HuggingFace repo: {str(e)}")
            raise
    
    async def _update_download_progress(self, download_id: int, db: AsyncSession):
        """Update download progress periodically for HF repo downloads"""
        progress = 10.0
        try:
            while True:
                await asyncio.sleep(3)  # Update every 3 seconds
                
                # Increment progress gradually (10% -> 90%)
                if progress < 90:
                    progress += 5
                
                await db.execute(
                    update(DBDownloadQueue)
                    .where(DBDownloadQueue.id == download_id)
                    .values(progress=progress)
                )
                await db.commit()
        except asyncio.CancelledError:
            # Task cancelled when download completes
            pass
        except Exception as e:
            self.logger.warning(f"Progress update error: {str(e)}")
    
    async def _download_single_file(self, download_id: int, download: DBDownloadQueue, db: AsyncSession):
        """Download a single file with progress tracking"""
        # Create destination directory
        dest_path = Path(download.destination)
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Check if partial download exists
        downloaded_size = 0
        mode = "wb"
        if dest_path.exists():
            downloaded_size = dest_path.stat().st_size
            mode = "ab"
            self.logger.info(f"Resuming download from {downloaded_size} bytes")
        
        # Download file
        async with aiohttp.ClientSession() as session:
            headers = {}
            if downloaded_size > 0:
                headers["Range"] = f"bytes={downloaded_size}-"
            
            async with session.get(download.url, headers=headers) as response:
                if response.status not in [200, 206]:
                    raise Exception(f"HTTP {response.status}: {await response.text()}")
                
                # Get total size
                total_size = int(response.headers.get("Content-Length", 0))
                if downloaded_size > 0:
                    total_size += downloaded_size
                
                # Update total size in database
                await db.execute(
                    update(DBDownloadQueue)
                    .where(DBDownloadQueue.id == download_id)
                    .values(total_size=total_size, downloaded_size=downloaded_size)
                )
                await db.commit()
                
                # Download chunks
                with open(dest_path, mode) as f:
                    chunk_count = 0
                    async for chunk in response.content.iter_chunked(self.chunk_size):
                        f.write(chunk)
                        downloaded_size += len(chunk)
                        chunk_count += 1
                        
                        # Update progress every 10 chunks (reduce DB writes)
                        if chunk_count % 10 == 0:
                            progress = (downloaded_size / total_size * 100) if total_size > 0 else 0
                            await db.execute(
                                update(DBDownloadQueue)
                                .where(DBDownloadQueue.id == download_id)
                                .values(downloaded_size=downloaded_size, progress=progress)
                            )
                            await db.commit()
        
        # Final update - mark as completed
        await db.execute(
            update(DBDownloadQueue)
            .where(DBDownloadQueue.id == download_id)
            .values(
                status="completed",
                progress=100.0,
                downloaded_size=downloaded_size,
                completed_at=datetime.utcnow()
            )
        )
        await db.commit()
    
    async def _create_model_entry(self, download: DBDownloadQueue, db: AsyncSession):
        """Create a model entry after successful download"""
        try:
            # Check if destination is a directory or file
            dest_path = Path(download.destination)
            
            if dest_path.is_dir():
                # For directories, calculate total size
                file_size = sum(f.stat().st_size for f in dest_path.rglob('*') if f.is_file())
            else:
                # For files
                file_size = dest_path.stat().st_size
            
            # Create model entry
            model = DBModel(
                name=download.model_name,
                path=download.destination,
                format=download.model_format or "PyTorch",
                size=file_size,
                source="HuggingFace",
                source_url=download.url,
                model_metadata=download.model_metadata
            )
            
            db.add(model)
            await db.commit()
            
            self.logger.info(f"Created model entry: {model.name} (ID: {model.id})")
            
        except Exception as e:
            self.logger.error(f"Failed to create model entry: {str(e)}")
    
    async def cancel_download(self, download_id: int, db: AsyncSession) -> bool:
        """Cancel an active download"""
        if download_id in self.active_downloads:
            task = self.active_downloads[download_id]
            task.cancel()
            return True
        
        # If not active, just update status
        await db.execute(
            update(DBDownloadQueue)
            .where(DBDownloadQueue.id == download_id)
            .values(status="cancelled")
        )
        await db.commit()
        return True
    
    async def get_download_status(self, download_id: int, db: AsyncSession) -> Optional[dict]:
        """Get status of a download"""
        result = await db.execute(
            select(DBDownloadQueue).where(DBDownloadQueue.id == download_id)
        )
        download = result.scalar_one_or_none()
        
        if not download:
            return None
        
        return {
            "id": download.id,
            "status": download.status,
            "progress": download.progress,
            "downloaded_size": download.downloaded_size,
            "total_size": download.total_size,
            "error_message": download.error_message
        }
    
    def get_active_downloads(self) -> list:
        """Get list of active download IDs"""
        return list(self.active_downloads.keys())


# Global download manager instance
download_manager = DownloadManager()

