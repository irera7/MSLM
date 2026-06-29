"""
RAG (Retrieval-Augmented Generation) API endpoints.
"""

from fastapi import APIRouter, HTTPException, UploadFile, File
from typing import List, Dict, Any, Optional
from pydantic import BaseModel

from app.services.rag_service import rag_service

router = APIRouter(prefix="/api/rag", tags=["rag"])


class CollectionCreate(BaseModel):
    name: str
    metadata: Optional[Dict[str, Any]] = None


class DocumentAdd(BaseModel):
    collection_name: str
    documents: List[str]
    metadatas: Optional[List[Dict[str, Any]]] = None
    ids: Optional[List[str]] = None


class QueryRequest(BaseModel):
    collection_name: str
    query_text: str
    n_results: int = 5
    where: Optional[Dict[str, Any]] = None


class RAGChatRequest(BaseModel):
    collection_name: str
    query: str
    base_prompt: Optional[str] = ""
    n_results: int = 3


@router.get("/status")
async def get_rag_status():
    """Check if RAG service is available"""
    return {
        "available": rag_service.is_available(),
        "message": "RAG service is ready" if rag_service.is_available() 
                   else "Install chromadb and sentence-transformers to enable RAG"
    }


@router.post("/collections")
async def create_collection(request: CollectionCreate):
    """Create a new collection"""
    if not rag_service.is_available():
        raise HTTPException(
            status_code=503,
            detail="RAG service not available. Install: pip install chromadb sentence-transformers"
        )
    
    try:
        success = rag_service.create_collection(
            name=request.name,
            metadata=request.metadata
        )
        
        if success:
            return {
                "message": f"Collection '{request.name}' created successfully",
                "name": request.name
            }
        else:
            raise HTTPException(status_code=400, detail="Failed to create collection")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/collections", response_model=List[Dict[str, Any]])
async def list_collections():
    """List all collections"""
    if not rag_service.is_available():
        # Return empty list instead of error for better UX
        return []
    
    try:
        return rag_service.list_collections()
    except Exception as e:
        # Log error but return empty list for graceful degradation
        import logging
        logging.getLogger(__name__).warning(f"Failed to list collections: {str(e)}")
        return []


@router.get("/collections/{collection_name}")
async def get_collection_stats(collection_name: str):
    """Get statistics for a collection"""
    if not rag_service.is_available():
        raise HTTPException(status_code=503, detail="RAG service not available")
    
    try:
        return rag_service.get_collection_stats(collection_name)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/collections/{collection_name}")
async def delete_collection(collection_name: str):
    """Delete a collection"""
    if not rag_service.is_available():
        raise HTTPException(status_code=503, detail="RAG service not available")
    
    try:
        success = rag_service.delete_collection(collection_name)
        
        if success:
            return {"message": f"Collection '{collection_name}' deleted successfully"}
        else:
            raise HTTPException(status_code=400, detail="Failed to delete collection")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/documents")
async def add_documents(request: DocumentAdd):
    """
    Add documents to a collection.
    """
    if not rag_service.is_available():
        raise HTTPException(status_code=503, detail="RAG service not available")
    
    try:
        success = rag_service.add_documents(
            collection_name=request.collection_name,
            documents=request.documents,
            metadatas=request.metadatas,
            ids=request.ids
        )
        
        if success:
            return {
                "message": f"Added {len(request.documents)} documents to '{request.collection_name}'",
                "count": len(request.documents)
            }
        else:
            raise HTTPException(status_code=400, detail="Failed to add documents")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/query")
async def query_collection(request: QueryRequest):
    """
    Query a collection.
    """
    if not rag_service.is_available():
        raise HTTPException(status_code=503, detail="RAG service not available")
    
    try:
        results = rag_service.query(
            collection_name=request.collection_name,
            query_text=request.query_text,
            n_results=request.n_results,
            where=request.where
        )
        
        return results
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/build-prompt")
async def build_rag_prompt(request: RAGChatRequest):
    """
    Build a RAG-enhanced prompt.
    
    This endpoint retrieves relevant context and builds a prompt
    that can be used with the chat API.
    """
    if not rag_service.is_available():
        raise HTTPException(status_code=503, detail="RAG service not available")
    
    try:
        prompt = rag_service.build_rag_prompt(
            query=request.query,
            collection_name=request.collection_name,
            base_prompt=request.base_prompt or "",
            n_results=request.n_results
        )
        
        return {
            "prompt": prompt,
            "collection": request.collection_name
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/upload-text")
async def upload_text_file(
    collection_name: str,
    file: UploadFile = File(...)
):
    """
    Upload a text file and add it to a collection.
    """
    if not rag_service.is_available():
        raise HTTPException(status_code=503, detail="RAG service not available")
    
    try:
        # Read file content
        content = await file.read()
        text = content.decode('utf-8')
        
        # Split into chunks (simple splitting by paragraphs)
        chunks = [chunk.strip() for chunk in text.split('\n\n') if chunk.strip()]
        
        if not chunks:
            raise HTTPException(status_code=400, detail="File contains no text")
        
        # Add to collection
        metadatas = [{"source": file.filename, "chunk": i} for i in range(len(chunks))]
        
        success = rag_service.add_documents(
            collection_name=collection_name,
            documents=chunks,
            metadatas=metadatas
        )
        
        if success:
            return {
                "message": f"Uploaded '{file.filename}' to '{collection_name}'",
                "chunks": len(chunks),
                "collection": collection_name
            }
        else:
            raise HTTPException(status_code=400, detail="Failed to add documents")
            
    except UnicodeDecodeError:
        raise HTTPException(status_code=400, detail="File must be UTF-8 encoded text")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

