from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging

from app.core.config import settings
from app.database.database import init_db, close_db

# Configure logging
logging.basicConfig(
    level=logging.INFO if not settings.DEBUG else logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events"""
    # Startup
    logger.info("Starting up LM Studio Clone...")
    await init_db()
    logger.info("Database initialized")
    
    # Reset all is_loaded flags (models unloaded on restart)
    from app.database.database import AsyncSessionLocal
    from app.database.models import Model as DBModel
    from sqlalchemy import update
    
    async with AsyncSessionLocal() as db:
        await db.execute(
            update(DBModel).values(is_loaded=False)
        )
        await db.commit()
    logger.info("Reset all model loaded states")
    
    # Load plugins
    from app.services.plugin_manager import plugin_manager
    plugin_count = plugin_manager.load_all_plugins()
    logger.info(f"Loaded {plugin_count} plugin(s)")
    
    yield
    
    # Shutdown
    logger.info("Shutting down...")
    await close_db()
    logger.info("Database connections closed")


# Create FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    debug=settings.DEBUG,
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "running"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}


# Import and include routers
from app.api import models, chat, downloads, openai_compat, monitoring, cache, plugins, huggingface, rag, functions, batch, api_keys, quantization, advanced
app.include_router(models.router, prefix=f"{settings.API_PREFIX}/models", tags=["models"])
app.include_router(chat.router, prefix=f"{settings.API_PREFIX}/chat", tags=["chat"])
app.include_router(downloads.router, prefix=f"{settings.API_PREFIX}/downloads", tags=["downloads"])
app.include_router(openai_compat.router, prefix=settings.OPENAI_API_PREFIX, tags=["openai"])
app.include_router(monitoring.router)
app.include_router(cache.router)
app.include_router(plugins.router)
app.include_router(huggingface.router)
app.include_router(rag.router)
app.include_router(functions.router)
app.include_router(batch.router)
app.include_router(api_keys.router)
app.include_router(quantization.router, tags=["quantization"])
app.include_router(advanced.router)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG
    )

