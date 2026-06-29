from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from typing import List, Optional
import logging
import json
from datetime import datetime

from app.database.database import get_db
from app.database.models import (
    ChatSession as DBChatSession,
    ChatMessage as DBChatMessage,
    Model as DBModel
)
from app.schemas.chat import (
    ChatSessionCreate,
    ChatSessionUpdate,
    ChatSessionResponse,
    ChatSessionWithMessages,
    ChatMessageResponse,
    ChatRequest,
    GenerationParams
)
from app.services.model_manager import model_manager
from app.services.inference.base_engine import GenerationConfig
from app.services.cache_service import cache_service
from app.core.presets import list_presets, apply_preset_to_session

router = APIRouter()
logger = logging.getLogger(__name__)


# Add these new Pydantic models for message operations
from pydantic import BaseModel

class MessageEdit(BaseModel):
    content: str

class MessageRegenerate(BaseModel):
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None

class MessageCreate(BaseModel):
    role: str  # 'user' or 'assistant'
    content: str


@router.post("/sessions", response_model=ChatSessionResponse, status_code=status.HTTP_201_CREATED)
async def create_session(
    session: ChatSessionCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create a new chat session"""
    # Verify model exists
    result = await db.execute(select(DBModel).where(DBModel.id == session.model_id))
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Model not found")
    
    db_session = DBChatSession(**session.model_dump())
    db.add(db_session)
    await db.commit()
    await db.refresh(db_session)
    
    return ChatSessionResponse.model_validate(db_session)


@router.get("/sessions", response_model=List[ChatSessionResponse])
async def list_sessions(
    model_id: Optional[int] = None,
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db)
):
    """List chat sessions"""
    query = select(DBChatSession)
    
    if model_id:
        query = query.where(DBChatSession.model_id == model_id)
    
    query = query.offset(skip).limit(limit).order_by(DBChatSession.updated_at.desc())
    
    result = await db.execute(query)
    sessions = result.scalars().all()
    
    return [ChatSessionResponse.model_validate(s) for s in sessions]


@router.get("/sessions/{session_id}", response_model=ChatSessionWithMessages)
async def get_session(session_id: int, db: AsyncSession = Depends(get_db)):
    """Get a chat session with its messages"""
    result = await db.execute(
        select(DBChatSession).where(DBChatSession.id == session_id)
    )
    session = result.scalar_one_or_none()
    
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Get messages
    messages_result = await db.execute(
        select(DBChatMessage)
        .where(DBChatMessage.session_id == session_id)
        .order_by(DBChatMessage.timestamp)
    )
    messages = messages_result.scalars().all()
    
    session_dict = ChatSessionResponse.model_validate(session).model_dump()
    session_dict["messages"] = [ChatMessageResponse.model_validate(m) for m in messages]
    
    return ChatSessionWithMessages(**session_dict)


@router.patch("/sessions/{session_id}", response_model=ChatSessionResponse)
async def update_session(
    session_id: int,
    session_update: ChatSessionUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update a chat session"""
    result = await db.execute(select(DBChatSession).where(DBChatSession.id == session_id))
    db_session = result.scalar_one_or_none()
    
    if not db_session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    update_data = session_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_session, field, value)
    
    db_session.updated_at = datetime.utcnow()
    await db.commit()
    await db.refresh(db_session)
    
    return ChatSessionResponse.model_validate(db_session)


@router.delete("/sessions/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_session(session_id: int, db: AsyncSession = Depends(get_db)):
    """Delete a chat session"""
    result = await db.execute(delete(DBChatSession).where(DBChatSession.id == session_id))
    
    if result.rowcount == 0:
        raise HTTPException(status_code=404, detail="Session not found")
    
    await db.commit()


@router.post("/generate")
async def generate(
    request: ChatRequest,
    db: AsyncSession = Depends(get_db)
):
    """Generate a response to a chat message (with streaming support)"""
    # Get session
    result = await db.execute(
        select(DBChatSession).where(DBChatSession.id == request.session_id)
    )
    session = result.scalar_one_or_none()
    
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Check if model is loaded
    if not model_manager.is_model_loaded(session.model_id):
        raise HTTPException(
            status_code=400,
            detail=f"Model {session.model_id} is not loaded. Load it first."
        )
    
    # Save user message
    user_message = DBChatMessage(
        session_id=request.session_id,
        role="user",
        content=request.message
    )
    db.add(user_message)
    await db.commit()
    
    # Build prompt from conversation history
    messages_result = await db.execute(
        select(DBChatMessage)
        .where(DBChatMessage.session_id == request.session_id)
        .order_by(DBChatMessage.timestamp)
    )
    messages = messages_result.scalars().all()
    
    prompt = _build_prompt(session, messages)
    
    # Generate config
    config = GenerationConfig(
        temperature=session.temperature,
        top_p=session.top_p,
        top_k=session.top_k,
        max_tokens=session.max_tokens,
        repeat_penalty=session.repeat_penalty,
        stream=request.stream
    )
    
    if request.stream:
        # Streaming response
        async def generate_stream():
            assistant_message_content = ""
            
            try:
                async for token in model_manager.generate_text_streaming(
                    model_id=session.model_id,
                    prompt=prompt,
                    config=config,
                    db=db
                ):
                    assistant_message_content += token
                    yield f"data: {json.dumps({'token': token})}\n\n"
                
                # Save assistant message
                assistant_message = DBChatMessage(
                    session_id=request.session_id,
                    role="assistant",
                    content=assistant_message_content
                )
                db.add(assistant_message)
                
                # Update session timestamp
                session.updated_at = datetime.utcnow()
                await db.commit()
                
                yield f"data: {json.dumps({'done': True})}\n\n"
                
            except Exception as e:
                logger.error(f"Streaming generation failed: {str(e)}")
                yield f"data: {json.dumps({'error': str(e)})}\n\n"
        
        return StreamingResponse(
            generate_stream(),
            media_type="text/event-stream"
        )
    
    else:
        # Non-streaming response
        try:
            # Check cache first (for non-streaming only)
            cache_config = {
                "temperature": session.temperature,
                "top_p": session.top_p,
                "top_k": session.top_k,
                "max_tokens": session.max_tokens
            }
            
            cached_response = cache_service.get(
                model_id=session.model_id,
                prompt=prompt,
                config=cache_config
            )
            
            if cached_response:
                logger.info(f"Cache hit for session {request.session_id}")
                generated_text = cached_response
            else:
                # Generate new response
                generated_text = await model_manager.generate_text_non_streaming(
                    model_id=session.model_id,
                    prompt=prompt,
                    config=config,
                    db=db
                )
                
                # Cache the response
                cache_service.set(
                    model_id=session.model_id,
                    prompt=prompt,
                    config=cache_config,
                    response=generated_text
                )
            
            # Save assistant message
            assistant_message = DBChatMessage(
                session_id=request.session_id,
                role="assistant",
                content=generated_text
            )
            db.add(assistant_message)
            
            # Update session timestamp
            session.updated_at = datetime.utcnow()
            await db.commit()
            
            return {
                "message": generated_text,
                "session_id": request.session_id
            }
            
        except Exception as e:
            logger.error(f"Generation failed: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))


@router.get("/sessions/{session_id}/export")
async def export_session(session_id: int, db: AsyncSession = Depends(get_db)):
    """Export a chat session to JSON"""
    result = await db.execute(
        select(DBChatSession).where(DBChatSession.id == session_id)
    )
    session = result.scalar_one_or_none()
    
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Get messages
    messages_result = await db.execute(
        select(DBChatMessage)
        .where(DBChatMessage.session_id == session_id)
        .order_by(DBChatMessage.timestamp)
    )
    messages = messages_result.scalars().all()
    
    export_data = {
        "session": ChatSessionResponse.model_validate(session).model_dump(),
        "messages": [
            {
                "role": m.role,
                "content": m.content,
                "timestamp": m.timestamp.isoformat()
            }
            for m in messages
        ]
    }
    
    return export_data


def _build_prompt(session: DBChatSession, messages: List[DBChatMessage]) -> str:
    """Build a prompt from session and message history"""
    prompt_parts = []
    
    if session.system_prompt:
        prompt_parts.append(f"System: {session.system_prompt}\n")
    
    for message in messages:
        role = message.role.capitalize()
        prompt_parts.append(f"{role}: {message.content}\n")
    
    prompt_parts.append("Assistant:")
    
    return "\n".join(prompt_parts)


@router.get("/presets")
async def get_presets():
    """Get available model presets"""
    return list_presets()


@router.post("/sessions/{session_id}/apply-preset")
async def apply_preset(
    session_id: int,
    preset_name: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Apply a preset to a chat session.
    
    Args:
        session_id: Session ID
        preset_name: Name of the preset (Creative, Balanced, Precise, Coding, Chat)
    """
    # Get session
    result = await db.execute(
        select(DBChatSession).where(DBChatSession.id == session_id)
    )
    session = result.scalar_one_or_none()
    
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    try:
        # Apply preset
        preset_params = apply_preset_to_session(preset_name)
        
        for key, value in preset_params.items():
            setattr(session, key, value)
        
        session.updated_at = datetime.utcnow()
        await db.commit()
        await db.refresh(session)
        
        return {
            "message": f"Applied preset '{preset_name}' to session {session_id}",
            "session": ChatSessionResponse.model_validate(session)
        }
        
    except KeyError as e:
        raise HTTPException(status_code=400, detail=str(e))


def _build_prompt(session: DBChatSession, messages: List[DBChatMessage]) -> str:
    """Build prompt from conversation history"""
    prompt_parts = []
    
    # Add system prompt if exists
    if session.system_prompt:
        prompt_parts.append(f"System: {session.system_prompt}\n")
    
    # Add conversation history
    for message in messages:
        if message.role == "user":
            prompt_parts.append(f"User: {message.content}\n")
        elif message.role == "assistant":
            prompt_parts.append(f"Assistant: {message.content}\n")
    
    # Add assistant prefix
    prompt_parts.append("Assistant:")
    
    return "\n".join(prompt_parts)


@router.patch("/messages/{message_id}")
async def edit_message(
    message_id: int,
    edit: MessageEdit,
    db: AsyncSession = Depends(get_db)
):
    """
    Edit a message in the chat history.
    This will update the message content and delete all messages after it.
    """
    # Get the message
    result = await db.execute(
        select(DBChatMessage).where(DBChatMessage.id == message_id)
    )
    message = result.scalar_one_or_none()
    
    if not message:
        raise HTTPException(status_code=404, detail="Message not found")
    
    # Delete all messages after this one
    await db.execute(
        delete(DBChatMessage).where(
            DBChatMessage.session_id == message.session_id,
            DBChatMessage.timestamp > message.timestamp
        )
    )
    
    # Update the message
    message.content = edit.content
    message.timestamp = datetime.utcnow()
    
    # Update session timestamp
    result = await db.execute(
        select(DBChatSession).where(DBChatSession.id == message.session_id)
    )
    session = result.scalar_one_or_none()
    if session:
        session.updated_at = datetime.utcnow()
    
    await db.commit()
    await db.refresh(message)
    
    return {
        "message": "Message edited successfully",
        "updated_message": ChatMessageResponse.model_validate(message)
    }


@router.post("/messages/{message_id}/regenerate")
async def regenerate_message(
    message_id: int,
    regenerate: MessageRegenerate,
    db: AsyncSession = Depends(get_db)
):
    """
    Regenerate an assistant's message.
    This will delete the message and generate a new response.
    """
    # Get the message
    result = await db.execute(
        select(DBChatMessage).where(DBChatMessage.id == message_id)
    )
    message = result.scalar_one_or_none()
    
    if not message:
        raise HTTPException(status_code=404, detail="Message not found")
    
    if message.role != "assistant":
        raise HTTPException(status_code=400, detail="Can only regenerate assistant messages")
    
    # Get session
    result = await db.execute(
        select(DBChatSession).where(DBChatSession.id == message.session_id)
    )
    session = result.scalar_one_or_none()
    
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Delete messages after this one
    await db.execute(
        delete(DBChatMessage).where(
            DBChatMessage.session_id == message.session_id,
            DBChatMessage.timestamp >= message.timestamp
        )
    )
    
    # Get conversation history up to this point
    messages_result = await db.execute(
        select(DBChatMessage)
        .where(DBChatMessage.session_id == message.session_id)
        .order_by(DBChatMessage.timestamp)
    )
    history = messages_result.scalars().all()
    
    # Build prompt
    prompt = _build_prompt(session, history)
    
    # Generate new response
    config = GenerationConfig(
        temperature=regenerate.temperature or session.temperature or 0.7,
        max_tokens=regenerate.max_tokens or session.max_tokens or 2048,
        top_p=session.top_p or 0.9,
        top_k=session.top_k or 40,
        repeat_penalty=session.repeat_penalty or 1.1,
        stop=session.stop_sequences or []
    )
    
    try:
        generated_text = await model_manager.generate_text_non_streaming(
            model_id=session.model_id,
            prompt=prompt,
            config=config,
            db=db
        )
        
        # Save new message
        new_message = DBChatMessage(
            session_id=message.session_id,
            role="assistant",
            content=generated_text
        )
        db.add(new_message)
        
        # Update session
        session.updated_at = datetime.utcnow()
        
        await db.commit()
        await db.refresh(new_message)
        
        return {
            "message": "Response regenerated successfully",
            "new_message": ChatMessageResponse.model_validate(new_message)
        }
        
    except Exception as e:
        logger.error(f"Regeneration failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/sessions/{session_id}/branch")
async def branch_conversation(
    session_id: int,
    from_message_id: Optional[int] = None,
    new_name: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """
    Create a branch from an existing conversation.
    Copies the session and messages up to a specific point.
    """
    # Get original session
    result = await db.execute(
        select(DBChatSession).where(DBChatSession.id == session_id)
    )
    original_session = result.scalar_one_or_none()
    
    if not original_session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Create new session (branch)
    new_session = DBChatSession(
        model_id=original_session.model_id,
        name=new_name or f"{original_session.name} (Branch)",
        system_prompt=original_session.system_prompt,
        temperature=original_session.temperature,
        max_tokens=original_session.max_tokens,
        top_p=original_session.top_p,
        top_k=original_session.top_k,
        repeat_penalty=original_session.repeat_penalty,
        stop_sequences=original_session.stop_sequences,
        preset=original_session.preset
    )
    
    db.add(new_session)
    await db.commit()
    await db.refresh(new_session)
    
    # Copy messages
    query = select(DBChatMessage).where(DBChatMessage.session_id == session_id).order_by(DBChatMessage.timestamp)
    
    if from_message_id:
        # Only copy messages up to from_message_id
        query = query.where(DBChatMessage.id <= from_message_id)
    
    messages_result = await db.execute(query)
    messages = messages_result.scalars().all()
    
    for msg in messages:
        new_message = DBChatMessage(
            session_id=new_session.id,
            role=msg.role,
            content=msg.content
        )
        db.add(new_message)
    
    await db.commit()
    
    return {"success": True, "new_session_id": new_session.id, "message": f"Created branch: {new_session.name}"}


@router.post("/sessions/{session_id}/messages", response_model=ChatMessageResponse, status_code=status.HTTP_201_CREATED)
async def add_message(
    session_id: int,
    message: MessageCreate,
    db: AsyncSession = Depends(get_db)
):
    """Add a message to a session manually"""
    # Verify session exists
    result = await db.execute(
        select(DBChatSession).where(DBChatSession.id == session_id)
    )
    session = result.scalar_one_or_none()
    
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Validate role
    if message.role not in ['user', 'assistant', 'system']:
        raise HTTPException(status_code=400, detail="Role must be 'user', 'assistant', or 'system'")
    
    # Create message
    db_message = DBChatMessage(
        session_id=session_id,
        role=message.role,
        content=message.content
    )
    db.add(db_message)
    await db.commit()
    await db.refresh(db_message)
    
    return ChatMessageResponse.model_validate(db_message)


@router.get("/sessions/{session_id}/export-markdown")
async def export_session_markdown(session_id: int, db: AsyncSession = Depends(get_db)):
    """Export a chat session to Markdown format"""
    result = await db.execute(
        select(DBChatSession).where(DBChatSession.id == session_id)
    )
    session = result.scalar_one_or_none()
    
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Get messages
    messages_result = await db.execute(
        select(DBChatMessage)
        .where(DBChatMessage.session_id == session_id)
        .order_by(DBChatMessage.timestamp)
    )
    messages = messages_result.scalars().all()
    
    # Build markdown
    md_lines = [
        f"# {session.name}",
        "",
        f"**Created**: {session.created_at.strftime('%Y-%m-%d %H:%M:%S')}",
        f"**Updated**: {session.updated_at.strftime('%Y-%m-%d %H:%M:%S')}",
        ""
    ]
    
    if session.system_prompt:
        md_lines.extend([
            "## System Prompt",
            "",
            session.system_prompt,
            "",
            "---",
            ""
        ])
    
    md_lines.append("## Conversation")
    md_lines.append("")
    
    for msg in messages:
        role_display = "🧑 **User**" if msg.role == "user" else "🤖 **Assistant**"
        md_lines.extend([
            f"### {role_display}",
            "",
            msg.content,
            "",
            "---",
            ""
        ])
    
    markdown_content = "\n".join(md_lines)
    
    return {
        "format": "markdown",
        "content": markdown_content,
        "filename": f"{session.name.replace(' ', '_')}.md"
    }


