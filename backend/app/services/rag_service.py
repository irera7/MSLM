"""
RAG (Retrieval-Augmented Generation) service using ChromaDB.
Allows models to access external knowledge base.
"""

import logging
from typing import List, Dict, Any, Optional
from pathlib import Path
import hashlib

logger = logging.getLogger(__name__)


class RAGService:
    """
    Service for RAG functionality.
    Uses ChromaDB for vector storage and retrieval.
    """
    
    def __init__(self, persist_directory: str = "./data/chromadb"):
        self.logger = logging.getLogger(__name__)
        self.persist_directory = Path(persist_directory)
        self.persist_directory.mkdir(parents=True, exist_ok=True)
        
        self.client = None
        self.embedding_function = None
        self.collections: Dict[str, Any] = {}
        
        self._initialize()
    
    def _initialize(self):
        """Initialize ChromaDB client and embedding function"""
        try:
            import chromadb
            from chromadb.config import Settings
            
            self.client = chromadb.Client(Settings(
                persist_directory=str(self.persist_directory),
                anonymized_telemetry=False,
                allow_reset=True
            ))
            
            # Try to use sentence-transformers for embeddings
            try:
                from chromadb.utils import embedding_functions
                self.embedding_function = embedding_functions.SentenceTransformerEmbeddingFunction(
                    model_name="all-MiniLM-L6-v2"
                )
                self.logger.info("Using SentenceTransformer embeddings")
            except ImportError:
                # Fallback to default embedding function
                self.embedding_function = None
                self.logger.warning("sentence-transformers not available, using default embeddings")
            
            self.logger.info(f"RAG service initialized with ChromaDB at {self.persist_directory}")
            
        except ImportError as e:
            self.logger.warning(
                f"ChromaDB not available: {str(e)}. "
                "Install with: pip install chromadb sentence-transformers"
            )
            self.client = None
        except Exception as e:
            self.logger.error(f"Failed to initialize RAG service: {str(e)}")
            self.client = None
    
    def is_available(self) -> bool:
        """Check if RAG service is available"""
        return self.client is not None
    
    def create_collection(
        self,
        name: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Create a new collection.
        
        Args:
            name: Collection name
            metadata: Optional metadata
            
        Returns:
            bool: True if successful
        """
        if not self.is_available():
            raise RuntimeError("RAG service not available")
        
        try:
            collection = self.client.create_collection(
                name=name,
                metadata=metadata or {},
                embedding_function=self.embedding_function
            )
            
            self.collections[name] = collection
            self.logger.info(f"Created collection: {name}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to create collection {name}: {str(e)}")
            return False
    
    def get_or_create_collection(
        self,
        name: str,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Get existing collection or create new one"""
        if not self.is_available():
            raise RuntimeError("RAG service not available")
        
        if name in self.collections:
            return self.collections[name]
        
        try:
            collection = self.client.get_or_create_collection(
                name=name,
                metadata=metadata or {},
                embedding_function=self.embedding_function
            )
            
            self.collections[name] = collection
            return collection
            
        except Exception as e:
            self.logger.error(f"Failed to get/create collection {name}: {str(e)}")
            raise
    
    def add_documents(
        self,
        collection_name: str,
        documents: List[str],
        metadatas: Optional[List[Dict[str, Any]]] = None,
        ids: Optional[List[str]] = None
    ) -> bool:
        """
        Add documents to a collection.
        
        Args:
            collection_name: Name of the collection
            documents: List of document texts
            metadatas: Optional list of metadata dicts
            ids: Optional list of document IDs (auto-generated if not provided)
            
        Returns:
            bool: True if successful
        """
        if not self.is_available():
            raise RuntimeError("RAG service not available")
        
        try:
            collection = self.get_or_create_collection(collection_name)
            
            # Generate IDs if not provided
            if ids is None:
                ids = [
                    hashlib.md5(doc.encode()).hexdigest()
                    for doc in documents
                ]
            
            collection.add(
                documents=documents,
                metadatas=metadatas,
                ids=ids
            )
            
            self.logger.info(f"Added {len(documents)} documents to {collection_name}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to add documents: {str(e)}")
            return False
    
    def query(
        self,
        collection_name: str,
        query_text: str,
        n_results: int = 5,
        where: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Query a collection.
        
        Args:
            collection_name: Name of the collection
            query_text: Query text
            n_results: Number of results to return
            where: Optional metadata filter
            
        Returns:
            Dict with results
        """
        if not self.is_available():
            raise RuntimeError("RAG service not available")
        
        try:
            collection = self.get_or_create_collection(collection_name)
            
            results = collection.query(
                query_texts=[query_text],
                n_results=n_results,
                where=where
            )
            
            # Format results
            formatted_results = {
                "documents": results["documents"][0] if results["documents"] else [],
                "metadatas": results["metadatas"][0] if results["metadatas"] else [],
                "distances": results["distances"][0] if results["distances"] else [],
                "ids": results["ids"][0] if results["ids"] else []
            }
            
            return formatted_results
            
        except Exception as e:
            self.logger.error(f"Query failed: {str(e)}")
            raise
    
    def delete_collection(self, name: str) -> bool:
        """Delete a collection"""
        if not self.is_available():
            raise RuntimeError("RAG service not available")
        
        try:
            self.client.delete_collection(name=name)
            
            if name in self.collections:
                del self.collections[name]
            
            self.logger.info(f"Deleted collection: {name}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to delete collection {name}: {str(e)}")
            return False
    
    def list_collections(self) -> List[Dict[str, Any]]:
        """List all collections"""
        if not self.is_available():
            raise RuntimeError("RAG service not available")
        
        try:
            collections = self.client.list_collections()
            
            return [
                {
                    "name": col.name,
                    "metadata": col.metadata,
                    "count": col.count()
                }
                for col in collections
            ]
            
        except Exception as e:
            self.logger.error(f"Failed to list collections: {str(e)}")
            return []
    
    def get_collection_stats(self, name: str) -> Dict[str, Any]:
        """Get statistics for a collection"""
        if not self.is_available():
            raise RuntimeError("RAG service not available")
        
        try:
            collection = self.get_or_create_collection(name)
            
            return {
                "name": collection.name,
                "count": collection.count(),
                "metadata": collection.metadata
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get stats for {name}: {str(e)}")
            raise
    
    def build_rag_prompt(
        self,
        query: str,
        collection_name: str,
        base_prompt: str = "",
        n_results: int = 3
    ) -> str:
        """
        Build a prompt with retrieved context.
        
        Args:
            query: User query
            collection_name: Collection to search
            base_prompt: Base system prompt
            n_results: Number of context documents to retrieve
            
        Returns:
            str: Enhanced prompt with context
        """
        try:
            # Retrieve relevant documents
            results = self.query(collection_name, query, n_results=n_results)
            
            if not results["documents"]:
                return f"{base_prompt}\n\nUser: {query}" if base_prompt else f"User: {query}"
            
            # Build context
            context = "\n\n".join([
                f"[Context {i+1}]: {doc}"
                for i, doc in enumerate(results["documents"])
            ])
            
            # Build enhanced prompt
            prompt_parts = []
            
            if base_prompt:
                prompt_parts.append(base_prompt)
            
            prompt_parts.append(
                "Use the following context to answer the question. "
                "If the context doesn't contain relevant information, say so.\n\n"
                f"{context}\n\n"
                f"User: {query}"
            )
            
            return "\n\n".join(prompt_parts)
            
        except Exception as e:
            self.logger.error(f"Failed to build RAG prompt: {str(e)}")
            # Fallback to original query
            return f"{base_prompt}\n\nUser: {query}" if base_prompt else f"User: {query}"


# Singleton instance
rag_service = RAGService()

