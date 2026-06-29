from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class APIKeyBase(BaseModel):
    name: str
    rate_limit: int = 60


class APIKeyCreate(APIKeyBase):
    pass


class APIKeyResponse(APIKeyBase):
    id: int
    key: str
    is_active: bool
    created_at: datetime
    last_used: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class APIKeyUpdate(BaseModel):
    name: Optional[str] = None
    rate_limit: Optional[int] = None
    is_active: Optional[bool] = None


class APIKeyListResponse(BaseModel):
    api_keys: list[APIKeyResponse]
    total: int

