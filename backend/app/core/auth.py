"""
Authentication and authorization utilities.
"""

import logging
from fastapi import Security, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.api_key_service import api_key_service
from app.database.models import APIKey

logger = logging.getLogger(__name__)

# Security scheme
security = HTTPBearer(auto_error=False)


async def verify_api_key(
    credentials: HTTPAuthorizationCredentials = Security(security),
    db: AsyncSession = None
) -> APIKey:
    """
    Verify API key from Authorization header.
    
    Usage in endpoints:
        @router.get("/protected")
        async def protected_endpoint(
            api_key: APIKey = Depends(verify_api_key),
            db: AsyncSession = Depends(get_db)
        ):
            ...
    
    Args:
        credentials: HTTP Bearer credentials
        db: Database session
        
    Returns:
        APIKey object if valid
        
    Raises:
        HTTPException: If key is invalid or rate limit exceeded
    """
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Extract key
    plain_key = credentials.credentials
    
    if not plain_key.startswith("sk-"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key format",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Validate key
    api_key = await api_key_service.validate_key(db, plain_key)
    
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or revoked API key",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Check rate limit
    if not await api_key_service.check_rate_limit(api_key):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded. Please try again later.",
            headers={"Retry-After": "60"},
        )
    
    return api_key


async def optional_api_key(
    credentials: HTTPAuthorizationCredentials = Security(security),
    db: AsyncSession = None
) -> APIKey | None:
    """
    Optional API key verification.
    Returns None if no key provided, validates if present.
    """
    if not credentials:
        return None
    
    try:
        return await verify_api_key(credentials, db)
    except HTTPException:
        return None

