from fastapi import APIRouter, Depends, HTTPException, Header
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional
import logging
import json
import time
import uuid

from app.database.database import get_db
from app.database.models import Model as DBModel, APIKey as DBAPIKey
from app.schemas.openai import (
    OpenAIChatCompletionRequest,
    OpenAICompletionRequest,
    OpenAIChatCompletionResponse,
    OpenAICompletionResponse,
    OpenAIModelsResponse,
    OpenAIModel,
    OpenAIChoice,
    OpenAIMessage,
    OpenAIUsage
)
from app.services.model_manager import model_manager
from app.services.inference.base_engine import GenerationConfig

router = APIRouter()
logger = logging.getLogger(__name__)


async def verify_api_key(
    authorization: Optional[str] = Header(None),
    db: AsyncSession = Depends(get_db)
) -> Optional[DBAPIKey]:
    """Verify API key if API_KEY_ENABLED is True"""
    from app.core.config import settings
    
    # For development/testing, allow requests without API key
    if not settings.API_KEY_ENABLED or settings.DEBUG:
        return None
    
    if not authorization:
        raise HTTPException(status_code=401, detail="API key required")
    
    # Extract token from "Bearer <token>"
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid authorization header")
    
    token = authorization[7:]  # Remove "Bearer "
    
    # Verify token
    result = await db.execute(
        select(DBAPIKey).where(DBAPIKey.key == token, DBAPIKey.is_active == True)
    )
    api_key = result.scalar_one_or_none()
    
    if not api_key:
        raise HTTPException(status_code=401, detail="Invalid API key")
    
    return api_key


@router.post("/chat/completions")
async def chat_completions(
    request: OpenAIChatCompletionRequest,
    db: AsyncSession = Depends(get_db),
    api_key: Optional[DBAPIKey] = Depends(verify_api_key)
):
    """
    OpenAI-compatible chat completions endpoint.
    Supports both streaming and non-streaming responses.
    """
    try:
        # Find model by name
        result = await db.execute(
            select(DBModel).where(DBModel.name == request.model)
        )
        model = result.scalar_one_or_none()
        
        if not model:
            raise HTTPException(status_code=404, detail=f"Model '{request.model}' not found")
        
        # Check if model is loaded
        if not model_manager.is_model_loaded(model.id):
            raise HTTPException(
                status_code=400,
                detail=f"Model '{request.model}' is not loaded. Load it first."
            )
        
        # Build prompt from messages
        prompt = _build_chat_prompt(request.messages)
        
        # Prepare generation config
        stop_sequences = []
        if request.stop:
            stop_sequences = [request.stop] if isinstance(request.stop, str) else request.stop
        
        config = GenerationConfig(
            temperature=request.temperature,
            top_p=request.top_p,
            max_tokens=request.max_tokens,
            repeat_penalty=1.0 + request.frequency_penalty,  # Convert frequency_penalty to repeat_penalty
            stop=stop_sequences if stop_sequences else None,
            stream=request.stream
        )
        
        completion_id = f"chatcmpl-{uuid.uuid4().hex[:24]}"
        created = int(time.time())
        
        if request.stream:
            # Streaming response
            async def generate_stream():
                generated_text = ""
                
                try:
                    async for token in model_manager.generate_text_streaming(
                        model_id=model.id,
                        prompt=prompt,
                        config=config,
                        db=db
                    ):
                        generated_text += token
                        
                        chunk = {
                            "id": completion_id,
                            "object": "chat.completion.chunk",
                            "created": created,
                            "model": request.model,
                            "choices": [{
                                "index": 0,
                                "delta": {"content": token},
                                "finish_reason": None
                            }]
                        }
                        yield f"data: {json.dumps(chunk)}\n\n"
                    
                    # Final chunk
                    final_chunk = {
                        "id": completion_id,
                        "object": "chat.completion.chunk",
                        "created": created,
                        "model": request.model,
                        "choices": [{
                            "index": 0,
                            "delta": {},
                            "finish_reason": "stop"
                        }]
                    }
                    yield f"data: {json.dumps(final_chunk)}\n\n"
                    yield "data: [DONE]\n\n"
                    
                except Exception as e:
                    logger.error(f"Streaming generation failed: {str(e)}")
                    error_chunk = {"error": str(e)}
                    yield f"data: {json.dumps(error_chunk)}\n\n"
            
            return StreamingResponse(
                generate_stream(),
                media_type="text/event-stream"
            )
        
        else:
            # Non-streaming response
            generated_text = await model_manager.generate_text_non_streaming(
                model_id=model.id,
                prompt=prompt,
                config=config,
                db=db
            )
            
            # Count tokens (rough estimation)
            engine = model_manager.get_loaded_model(model.id)
            prompt_tokens = engine.count_tokens(prompt) if engine else len(prompt) // 4
            completion_tokens = engine.count_tokens(generated_text) if engine else len(generated_text) // 4
            
            response = OpenAIChatCompletionResponse(
                id=completion_id,
                created=created,
                model=request.model,
                choices=[
                    OpenAIChoice(
                        index=0,
                        message=OpenAIMessage(role="assistant", content=generated_text),
                        finish_reason="stop"
                    )
                ],
                usage=OpenAIUsage(
                    prompt_tokens=prompt_tokens,
                    completion_tokens=completion_tokens,
                    total_tokens=prompt_tokens + completion_tokens
                )
            )
            
            return response
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Chat completion failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/completions")
async def completions(
    request: OpenAICompletionRequest,
    db: AsyncSession = Depends(get_db),
    api_key: Optional[DBAPIKey] = Depends(verify_api_key)
):
    """OpenAI-compatible completions endpoint"""
    try:
        # Find model
        result = await db.execute(
            select(DBModel).where(DBModel.name == request.model)
        )
        model = result.scalar_one_or_none()
        
        if not model:
            raise HTTPException(status_code=404, detail=f"Model '{request.model}' not found")
        
        if not model_manager.is_model_loaded(model.id):
            raise HTTPException(
                status_code=400,
                detail=f"Model '{request.model}' is not loaded"
            )
        
        # Get prompt
        prompt = request.prompt if isinstance(request.prompt, str) else request.prompt[0]
        
        # Prepare config
        stop_sequences = []
        if request.stop:
            stop_sequences = [request.stop] if isinstance(request.stop, str) else request.stop
        
        config = GenerationConfig(
            temperature=request.temperature,
            top_p=request.top_p,
            max_tokens=request.max_tokens,
            repeat_penalty=1.0 + request.frequency_penalty,
            stop=stop_sequences if stop_sequences else None,
            stream=request.stream
        )
        
        completion_id = f"cmpl-{uuid.uuid4().hex[:24]}"
        created = int(time.time())
        
        if request.stream:
            async def generate_stream():
                try:
                    async for token in model_manager.generate_text_streaming(
                        model_id=model.id,
                        prompt=prompt,
                        config=config,
                        db=db
                    ):
                        chunk = {
                            "id": completion_id,
                            "object": "text_completion.chunk",
                            "created": created,
                            "model": request.model,
                            "choices": [{
                                "index": 0,
                                "text": token,
                                "finish_reason": None
                            }]
                        }
                        yield f"data: {json.dumps(chunk)}\n\n"
                    
                    yield "data: [DONE]\n\n"
                except Exception as e:
                    logger.error(f"Streaming failed: {str(e)}")
            
            return StreamingResponse(generate_stream(), media_type="text/event-stream")
        
        else:
            generated_text = await model_manager.generate_text_non_streaming(
                model_id=model.id,
                prompt=prompt,
                config=config,
                db=db
            )
            
            engine = model_manager.get_loaded_model(model.id)
            prompt_tokens = engine.count_tokens(prompt) if engine else len(prompt) // 4
            completion_tokens = engine.count_tokens(generated_text) if engine else len(generated_text) // 4
            
            return OpenAICompletionResponse(
                id=completion_id,
                created=created,
                model=request.model,
                choices=[
                    OpenAIChoice(
                        index=0,
                        text=generated_text,
                        finish_reason="stop"
                    )
                ],
                usage=OpenAIUsage(
                    prompt_tokens=prompt_tokens,
                    completion_tokens=completion_tokens,
                    total_tokens=prompt_tokens + completion_tokens
                )
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Completion failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/models")
async def list_models(
    db: AsyncSession = Depends(get_db),
    api_key: Optional[DBAPIKey] = Depends(verify_api_key)
):
    """List available models (OpenAI-compatible)"""
    result = await db.execute(select(DBModel))
    models = result.scalars().all()
    
    openai_models = [
        OpenAIModel(
            id=model.name,
            created=int(model.created_at.timestamp()),
            owned_by="user"
        )
        for model in models
    ]
    
    return OpenAIModelsResponse(data=openai_models)


def _build_chat_prompt(messages: list) -> str:
    """Build prompt from chat messages"""
    prompt_parts = []
    
    for message in messages:
        role = message.role.capitalize()
        content = message.content
        prompt_parts.append(f"{role}: {content}")
    
    prompt_parts.append("Assistant:")
    
    return "\n".join(prompt_parts)

