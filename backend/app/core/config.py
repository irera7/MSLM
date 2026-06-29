from pydantic_settings import BaseSettings
from pathlib import Path
from typing import Optional


class Settings(BaseSettings):
    # App Settings
    APP_NAME: str = "LM Studio Clone"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True
    
    # Server Settings
    HOST: str = "0.0.0.0"
    PORT: int = 8078
    
    # Paths
    BASE_DIR: Path = Path(__file__).resolve().parent.parent.parent.parent
    MODELS_DIR: Path = BASE_DIR / "models"
    DATA_DIR: Path = BASE_DIR / "data"
    DATABASE_PATH: Path = DATA_DIR / "app.db"
    
    # Database
    DATABASE_URL: str = f"sqlite+aiosqlite:///{DATABASE_PATH}"
    
    # API Settings
    API_PREFIX: str = "/api"
    OPENAI_API_PREFIX: str = "/v1"
    
    # CORS
    CORS_ORIGINS: list = ["http://localhost:3000", "http://localhost:5173", "http://localhost:3032"]
    
    # Model Settings
    MAX_CONCURRENT_MODELS: int = 3
    DEFAULT_CONTEXT_LENGTH: int = 2048
    DEFAULT_GPU_LAYERS: int = 0  # 0 = CPU only, -1 = all layers on GPU
    
    # Download Settings
    MAX_CONCURRENT_DOWNLOADS: int = 3
    DOWNLOAD_CHUNK_SIZE: int = 8192
    
    # Cache Settings
    ENABLE_CACHE: bool = True
    CACHE_TTL: int = 3600  # 1 hour
    MAX_CACHE_SIZE: int = 1000  # max cached items
    
    # Monitoring
    ENABLE_MONITORING: bool = True
    MONITORING_INTERVAL: int = 5  # seconds
    
    # Security
    SECRET_KEY: str = "your-secret-key-here-change-in-production"
    API_KEY_ENABLED: bool = True
    
    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = 60
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()

# Create necessary directories
settings.MODELS_DIR.mkdir(parents=True, exist_ok=True)
settings.DATA_DIR.mkdir(parents=True, exist_ok=True)

