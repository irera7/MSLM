from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class ChatMessageBase(BaseModel):
    role: str = Field(..., pattern="^(system|user|assistant)$")
    content: str


class ChatMessageCreate(ChatMessageBase):
    session_id: int
    tokens: Optional[int] = None


class ChatMessageResponse(ChatMessageBase):
    id: int
    session_id: int
    timestamp: datetime
    tokens: Optional[int] = None
    
    class Config:
        from_attributes = True


class ChatSessionBase(BaseModel):
    model_id: int
    name: str
    system_prompt: Optional[str] = None
    preset: str = "Balanced"
    temperature: float = 0.7
    top_p: float = 0.9
    top_k: int = 40
    max_tokens: int = 2048
    repeat_penalty: float = 1.1


class ChatSessionCreate(ChatSessionBase):
    pass


class ChatSessionUpdate(BaseModel):
    name: Optional[str] = None
    system_prompt: Optional[str] = None
    preset: Optional[str] = None
    temperature: Optional[float] = None
    top_p: Optional[float] = None
    top_k: Optional[int] = None
    max_tokens: Optional[int] = None
    repeat_penalty: Optional[float] = None


class ChatSessionResponse(ChatSessionBase):
    id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class ChatSessionWithMessages(ChatSessionResponse):
    messages: List[ChatMessageResponse] = []


class ChatRequest(BaseModel):
    session_id: int
    message: str
    stream: bool = True


class ChatResponse(BaseModel):
    message: str
    tokens: Optional[int] = None
    duration: Optional[float] = None


class GenerationParams(BaseModel):
    temperature: float = 0.7
    top_p: float = 0.9
    top_k: int = 40
    max_tokens: int = 2048
    repeat_penalty: float = 1.1
    stop: Optional[List[str]] = None

