from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text, Boolean, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database.database import Base


class Model(Base):
    """Model registry table"""
    __tablename__ = "models"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, index=True)
    path = Column(String, nullable=False, unique=True)
    format = Column(String, nullable=False, index=True)  # GGUF, SafeTensors, GPTQ, AWQ, EXL2, ONNX
    size = Column(Float)  # Size in bytes
    source = Column(String, index=True)  # HuggingFace, Local
    source_url = Column(String, nullable=True)  # Original download URL
    quantization = Column(String, nullable=True)  # Q4_K_M, Q5_K_S, etc.
    parameters = Column(String, nullable=True)  # 7B, 13B, 70B, etc.
    model_metadata = Column(JSON, nullable=True)  # Additional metadata
    is_loaded = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    chat_sessions = relationship("ChatSession", back_populates="model", cascade="all, delete-orphan")
    usage_stats = relationship("UsageStats", back_populates="model", cascade="all, delete-orphan")


class ChatSession(Base):
    """Chat session table"""
    __tablename__ = "chat_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    model_id = Column(Integer, ForeignKey("models.id", ondelete="CASCADE"), nullable=False)
    name = Column(String, nullable=False)
    system_prompt = Column(Text, nullable=True)
    preset = Column(String, default="Balanced")  # Creative, Balanced, Precise
    temperature = Column(Float, default=0.7)
    top_p = Column(Float, default=0.9)
    top_k = Column(Integer, default=40)
    max_tokens = Column(Integer, default=2048)
    repeat_penalty = Column(Float, default=1.1)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    model = relationship("Model", back_populates="chat_sessions")
    messages = relationship("ChatMessage", back_populates="session", cascade="all, delete-orphan")


class ChatMessage(Base):
    """Chat message table"""
    __tablename__ = "chat_messages"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("chat_sessions.id", ondelete="CASCADE"), nullable=False)
    role = Column(String, nullable=False)  # system, user, assistant
    content = Column(Text, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    tokens = Column(Integer, nullable=True)
    
    # Relationships
    session = relationship("ChatSession", back_populates="messages")


class APIKey(Base):
    """API key management table"""
    __tablename__ = "api_keys"
    
    id = Column(Integer, primary_key=True, index=True)
    key = Column(String, nullable=False, unique=True, index=True)
    name = Column(String, nullable=False)
    rate_limit = Column(Integer, default=60)  # requests per minute
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_used = Column(DateTime, nullable=True)
    
    # Relationships
    usage_logs = relationship("APIKeyUsage", back_populates="api_key", cascade="all, delete-orphan")


class APIKeyUsage(Base):
    """API key usage tracking"""
    __tablename__ = "api_key_usage"
    
    id = Column(Integer, primary_key=True, index=True)
    api_key_id = Column(Integer, ForeignKey("api_keys.id", ondelete="CASCADE"), nullable=False)
    endpoint = Column(String, nullable=False)
    tokens = Column(Integer, default=0)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    
    # Relationships
    api_key = relationship("APIKey", back_populates="usage_logs")


class UsageStats(Base):
    """Model usage statistics"""
    __tablename__ = "usage_stats"
    
    id = Column(Integer, primary_key=True, index=True)
    model_id = Column(Integer, ForeignKey("models.id", ondelete="CASCADE"), nullable=False)
    tokens = Column(Integer, nullable=False)
    duration = Column(Float, nullable=False)  # seconds
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    
    # Relationships
    model = relationship("Model", back_populates="usage_stats")


class DownloadQueue(Base):
    """Download queue table"""
    __tablename__ = "download_queue"
    
    id = Column(Integer, primary_key=True, index=True)
    url = Column(String, nullable=False)
    destination = Column(String, nullable=False)
    status = Column(String, default="pending", index=True)  # pending, downloading, completed, failed, cancelled
    progress = Column(Float, default=0.0)  # 0-100
    priority = Column(Integer, default=0)  # higher = more priority
    total_size = Column(Float, nullable=True)  # bytes
    downloaded_size = Column(Float, default=0.0)  # bytes
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    
    # Model info (for creating Model entry after download)
    model_name = Column(String, nullable=True)
    model_format = Column(String, nullable=True)
    model_metadata = Column(JSON, nullable=True)

