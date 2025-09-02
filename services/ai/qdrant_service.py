import os
import logging
import time
from typing import Dict, List, Optional, Any
from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance, VectorParams, PointStruct, SearchRequest,
    Filter, FieldCondition, Range, MatchValue
)
import asyncio
from uuid import uuid4, UUID
from config.logging_config import get_logger

logger = get_logger(__name__)

class QdrantService:
    """
    Service for vector database operations using Qdrant.
    Handles semantic search and storage of Q&A embeddings.
    """
    
    def __init__(self):
        # Use Docker service name 'qdrant' as default in containerized environment
        self.host = os.getenv("QDRANT_HOST", "qdrant")
        self.port = int(os.getenv("QDRANT_PORT", "6333"))
        self.collection_name = "syria_qa_vectors"
        self.client: Optional[QdrantClient] = None
        self.embedding_dimension = 768  # Dimension for Gemini embeddings
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize Qdrant client and create collection if needed"""
        try:
            self.client = QdrantClient(host=self.host, port=self.port)
            logger.info(f"Qdrant client connected to {self.host}:{self.port}")
            
            # Initialize collection - will be done when needed
            # asyncio.create_task(self._ensure_collection_exists())
            
        except Exception as e:
            logger.warning(f"Failed to connect to Qdrant: {e}")
            self.client = None
    
    async def _ensure_collection_exists(self):
        """Create collection if it doesn't exist"""
        if not self.client:
            return
        
        try:
            # Check if collection exists
            collections = await asyncio.to_thread(self.client.get_collections)
            collection_names = [col.name for col in collections.collections]
            
            if self.collection_name not in collection_names:
                # Create collection
                await asyncio.to_thread(
                    self.client.create_collection,
                    collection_name=self.collection_name,
                    vectors_config=VectorParams(
                        size=self.embedding_dimension,
                        distance=Distance.COSINE
                    )
                )
                logger.info(f"Created Qdrant collection: {self.collection_name}")
            else:
                logger.info(f"Qdrant collection {self.collection_name} already exists")
                
        except Exception as e:
            logger.error(f"Failed to ensure collection exists: {e}")
    
    def is_connected(self) -> bool:
        """Check if Qdrant client is connected and responsive"""
        if not self.client:
            return False
        try:
            # Try a simple operation to check the connection
            collections = self.client.get_collections()
            return collections is not None
        except Exception as e:
            logger.error(f"Qdrant connection check failed: {e}")
            return False
    
    async def store_qa_embedding(
        self,
        qa_id: str,
        question: str,
        embedding: List[float],
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Store a Q&A pair with its embedding in Qdrant
        
        Args:
            qa_id: Unique identifier for the Q&A pair
            question: The question text
            embedding: Vector embedding of the question
            metadata: Additional metadata (category, confidence, etc.)
        
        Returns:
            Success status
        """
        if not self.client or not self.is_connected():
            logger.error("Qdrant client not connected")
            return False
        
        try:
            # Prepare metadata
            payload = {
                "question": question,
                "qa_id": qa_id,
                "question_id": qa_id,  # For PostgreSQL lookup
                **(metadata or {})
            }
            
            # Create point
            point = PointStruct(
                id=str(uuid4()),  # Qdrant point ID
                vector=embedding,
                payload=payload
            )
            
            # Store in Qdrant
            await asyncio.to_thread(
                self.client.upsert,
                collection_name=self.collection_name,
                points=[point]
            )
            
            logger.debug(f"Stored Q&A embedding: {qa_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to store Q&A embedding {qa_id}: {e}")
            return False
    
    async def search_similar_questions(
        self,
        query_embedding: List[float],
        limit: int = 5,
        score_threshold: float = 0.85,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Search for similar questions using vector similarity
        
        Args:
            query_embedding: Vector embedding of the query
            limit: Maximum number of results
            score_threshold: Minimum similarity score (0.0 to 1.0)
            filters: Optional filters for metadata
        
        Returns:
            List of similar Q&A pairs with similarity scores
        """
        if not self.client or not self.is_connected():
            logger.error("Qdrant client not connected")
            return []
        
        try:
            # Build filter if provided
            filter_condition = None
            if filters:
                conditions = []
                for key, value in filters.items():
                    if isinstance(value, str):
                        conditions.append(
                            FieldCondition(key=key, match=MatchValue(value=value))
                        )
                    elif isinstance(value, (int, float)):
                        conditions.append(
                            FieldCondition(key=key, range=Range(gte=value))
                        )
                
                if conditions:
                    filter_condition = Filter(must=conditions)
            
            # Perform search
            search_result = await asyncio.to_thread(
                self.client.search,
                collection_name=self.collection_name,
                query_vector=query_embedding,
                limit=limit,
                score_threshold=score_threshold,
                query_filter=filter_condition
            )
            
            # Format results
            results = []
            for hit in search_result:
                result = {
                    "qa_id": hit.payload.get("qa_id"),
                    "question": hit.payload.get("question"),
                    "answer": hit.payload.get("answer"),
                    "similarity_score": float(hit.score),
                    "metadata": {
                        k: v for k, v in hit.payload.items() 
                        if k not in ["qa_id", "question", "answer"]
                    }
                }
                results.append(result)
            
            logger.debug(f"Found {len(results)} similar questions")
            return results
            
        except Exception as e:
            logger.error(f"Failed to search similar questions: {e}")
            return []
    
    async def delete_qa_embedding(self, qa_id: str) -> bool:
        """Delete Q&A embedding by qa_id"""
        if not self.client or not self.is_connected():
            return False
        
        try:
            # Search for points with this qa_id
            search_result = await asyncio.to_thread(
                self.client.scroll,
                collection_name=self.collection_name,
                scroll_filter=Filter(
                    must=[FieldCondition(key="qa_id", match=MatchValue(value=qa_id))]
                ),
                limit=100
            )
            
            # Delete found points
            point_ids = [point.id for point in search_result[0]]
            if point_ids:
                await asyncio.to_thread(
                    self.client.delete,
                    collection_name=self.collection_name,
                    points_selector=point_ids
                )
                logger.debug(f"Deleted {len(point_ids)} points for qa_id: {qa_id}")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete Q&A embedding {qa_id}: {e}")
            return False
    
    async def update_qa_embedding(
        self,
        qa_id: str,
        question: str,
        embedding: List[float],
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Update existing Q&A embedding"""
        # Delete existing and insert new (simple approach)
        await self.delete_qa_embedding(qa_id)
        return await self.store_qa_embedding(qa_id, question, embedding, metadata)
    
    async def get_collection_stats(self) -> Dict[str, Any]:
        """Get statistics about the vector collection"""
        if not self.client or not self.is_connected():
            return {"connected": False}
        
        try:
            collection_info = await asyncio.to_thread(
                self.client.get_collection,
                collection_name=self.collection_name
            )
            
            return {
                "connected": True,
                "collection_name": self.collection_name,
                "vectors_count": collection_info.vectors_count,
                "indexed_vectors_count": collection_info.indexed_vectors_count,
                "points_count": collection_info.points_count,
                "segments_count": collection_info.segments_count,
                "status": collection_info.status.value
            }
            
        except Exception as e:
            logger.error(f"Failed to get collection stats: {e}")
            return {"connected": False, "error": str(e)}
    
    async def batch_store_embeddings(
        self,
        qa_data: List[Dict[str, Any]]
    ) -> int:
        """
        Batch store multiple Q&A embeddings
        
        Args:
            qa_data: List of dicts containing qa_id, question, answer, embedding, metadata
        
        Returns:
            Number of successfully stored embeddings
        """
        if not self.client or not self.is_connected():
            return 0
        
        try:
            points = []
            for data in qa_data:
                payload = {
                    "question": data.get("question"),
                    "qa_id": data.get("qa_id"),
                    **(data.get("metadata", {}))
                }
                
                point = PointStruct(
                    id=str(uuid4()),
                    vector=data.get("embedding"),
                    payload=payload
                )
                points.append(point)
            
            # Batch upsert
            await asyncio.to_thread(
                self.client.upsert,
                collection_name=self.collection_name,
                points=points
            )
            
            logger.info(f"Batch stored {len(points)} Q&A embeddings")
            return len(points)
            
        except Exception as e:
            logger.error(f"Failed to batch store embeddings: {e}")
            return 0

# Global Qdrant service instance
qdrant_service = QdrantService()