"""
API Key management service.
Generate, validate, and manage API keys.
"""

import logging
import secrets
import hashlib
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update

from app.database.models import APIKey, APIKeyUsage

logger = logging.getLogger(__name__)


class APIKeyService:
    """Service for managing API keys"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self._rate_limit_cache: Dict[str, List[datetime]] = {}
    
    def generate_key(self) -> str:
        """
        Generate a secure API key.
        
        Returns:
            str: API key in format 'sk-...'
        """
        random_bytes = secrets.token_bytes(32)
        key = "sk-" + secrets.token_urlsafe(32)
        return key
    
    def hash_key(self, key: str) -> str:
        """
        Hash an API key for secure storage.
        
        Args:
            key: Plain API key
            
        Returns:
            str: Hashed key
        """
        return hashlib.sha256(key.encode()).hexdigest()
    
    async def create_key(
        self,
        db: AsyncSession,
        name: str,
        rate_limit: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Create a new API key.
        
        Args:
            db: Database session
            name: Key name/description
            rate_limit: Requests per minute (None = unlimited)
            
        Returns:
            Dict with key info (includes plain key)
        """
        try:
            # Generate key
            plain_key = self.generate_key()
            hashed_key = self.hash_key(plain_key)
            
            # Create database entry
            api_key = APIKey(
                key=hashed_key,
                name=name,
                rate_limit=rate_limit,
                is_active=True,
                created_at=datetime.utcnow()
            )
            
            db.add(api_key)
            await db.commit()
            await db.refresh(api_key)
            
            self.logger.info(f"Created API key: {name} (ID: {api_key.id})")
            
            return {
                "id": api_key.id,
                "key": plain_key,  # Only returned once!
                "name": name,
                "rate_limit": rate_limit,
                "created_at": api_key.created_at.isoformat(),
                "warning": "Save this key securely. It won't be shown again."
            }
            
        except Exception as e:
            self.logger.error(f"Failed to create API key: {str(e)}")
            await db.rollback()
            raise
    
    async def validate_key(
        self,
        db: AsyncSession,
        plain_key: str
    ) -> Optional[APIKey]:
        """
        Validate an API key.
        
        Args:
            db: Database session
            plain_key: Plain API key
            
        Returns:
            APIKey object if valid, None otherwise
        """
        try:
            hashed_key = self.hash_key(plain_key)
            
            result = await db.execute(
                select(APIKey).where(
                    APIKey.key == hashed_key,
                    APIKey.is_active == True
                )
            )
            api_key = result.scalar_one_or_none()
            
            if api_key:
                # Update last used
                api_key.last_used = datetime.utcnow()
                await db.commit()
            
            return api_key
            
        except Exception as e:
            self.logger.error(f"Key validation failed: {str(e)}")
            return None
    
    async def check_rate_limit(
        self,
        api_key: APIKey
    ) -> bool:
        """
        Check if API key has exceeded rate limit.
        
        Args:
            api_key: APIKey object
            
        Returns:
            bool: True if within limit, False if exceeded
        """
        if api_key.rate_limit is None:
            return True  # No limit
        
        # Get request times for this key
        key_id = str(api_key.id)
        now = datetime.utcnow()
        one_minute_ago = now - timedelta(minutes=1)
        
        if key_id not in self._rate_limit_cache:
            self._rate_limit_cache[key_id] = []
        
        # Remove old entries
        self._rate_limit_cache[key_id] = [
            t for t in self._rate_limit_cache[key_id]
            if t > one_minute_ago
        ]
        
        # Check limit
        if len(self._rate_limit_cache[key_id]) >= api_key.rate_limit:
            return False
        
        # Add current request
        self._rate_limit_cache[key_id].append(now)
        return True
    
    async def record_usage(
        self,
        db: AsyncSession,
        api_key_id: int,
        endpoint: str,
        tokens: int
    ):
        """
        Record API key usage.
        
        Args:
            db: Database session
            api_key_id: API key ID
            endpoint: Endpoint called
            tokens: Tokens used
        """
        try:
            usage = APIKeyUsage(
                api_key_id=api_key_id,
                endpoint=endpoint,
                tokens=tokens,
                timestamp=datetime.utcnow()
            )
            
            db.add(usage)
            await db.commit()
            
        except Exception as e:
            self.logger.error(f"Failed to record usage: {str(e)}")
            await db.rollback()
    
    async def revoke_key(
        self,
        db: AsyncSession,
        key_id: int
    ) -> bool:
        """
        Revoke (deactivate) an API key.
        
        Args:
            db: Database session
            key_id: API key ID
            
        Returns:
            bool: True if successful
        """
        try:
            result = await db.execute(
                update(APIKey)
                .where(APIKey.id == key_id)
                .values(is_active=False)
            )
            
            await db.commit()
            
            if result.rowcount > 0:
                self.logger.info(f"Revoked API key ID: {key_id}")
                
                # Clear from cache
                if str(key_id) in self._rate_limit_cache:
                    del self._rate_limit_cache[str(key_id)]
                
                return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Failed to revoke key: {str(e)}")
            await db.rollback()
            return False
    
    async def list_keys(
        self,
        db: AsyncSession,
        include_inactive: bool = False
    ) -> List[Dict[str, Any]]:
        """
        List all API keys (without showing actual keys).
        
        Args:
            db: Database session
            include_inactive: Include revoked keys
            
        Returns:
            List of key info
        """
        try:
            query = select(APIKey)
            
            if not include_inactive:
                query = query.where(APIKey.is_active == True)
            
            result = await db.execute(query)
            keys = result.scalars().all()
            
            return [
                {
                    "id": key.id,
                    "name": key.name,
                    "rate_limit": key.rate_limit,
                    "is_active": key.is_active,
                    "created_at": key.created_at.isoformat(),
                    "last_used": key.last_used.isoformat() if key.last_used else None,
                    "key_preview": "sk-***" + key.key[-4:]  # Show last 4 chars of hash
                }
                for key in keys
            ]
            
        except Exception as e:
            self.logger.error(f"Failed to list keys: {str(e)}")
            return []
    
    async def get_key_usage_stats(
        self,
        db: AsyncSession,
        key_id: int,
        days: int = 7
    ) -> Dict[str, Any]:
        """
        Get usage statistics for an API key.
        
        Args:
            db: Database session
            key_id: API key ID
            days: Number of days to look back
            
        Returns:
            Dict with usage stats
        """
        try:
            since = datetime.utcnow() - timedelta(days=days)
            
            result = await db.execute(
                select(APIKeyUsage)
                .where(
                    APIKeyUsage.api_key_id == key_id,
                    APIKeyUsage.timestamp >= since
                )
            )
            usage_records = result.scalars().all()
            
            total_requests = len(usage_records)
            total_tokens = sum(r.tokens for r in usage_records if r.tokens)
            
            # Group by endpoint
            endpoints: Dict[str, int] = {}
            for record in usage_records:
                endpoints[record.endpoint] = endpoints.get(record.endpoint, 0) + 1
            
            return {
                "key_id": key_id,
                "period_days": days,
                "total_requests": total_requests,
                "total_tokens": total_tokens,
                "endpoints": endpoints,
                "requests_per_day": round(total_requests / days, 2) if days > 0 else 0
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get usage stats: {str(e)}")
            return {}


# Singleton instance
api_key_service = APIKeyService()

