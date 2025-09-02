import os
import logging
import asyncio
from typing import Dict, List, Optional, Any
from uuid import uuid4

from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance, VectorParams, PointStruct, Filter, FieldCondition, Range, MatchValue
)

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

class QdrantService:
    """
    Service for vector database operations using Qdrant.
    Handles semantic search and storage of Q&A embeddings.
    Payload is kept exactly as provided (no modification).
    """

    def __init__(self):
        self.host = os.getenv("QDRANT_HOST", "qdrant")
        self.port = int(os.getenv("QDRANT_PORT", 6333))
        self.collection_name = os.getenv("QDRANT_COLLECTION", "syria_qa_vectors")
        self.embedding_dimension = int(os.getenv("EMBEDDING_DIM", 768))
        self.client: Optional[QdrantClient] = None

        self._initialize_client()

    def _initialize_client(self):
        """Initialize Qdrant client"""
        try:
            self.client = QdrantClient(host=self.host, port=self.port)
            logger.info(f"Qdrant client connected to {self.host}:{self.port}")
        except Exception as e:
            logger.error(f"Failed to connect to Qdrant: {e}")
            self.client = None

    async def _ensure_collection_exists(self):
        """Create collection if it doesn't exist"""
        if not self.client:
            return

        try:
            collections = await asyncio.to_thread(self.client.get_collections)
            collection_names = [col.name for col in collections.collections]

            if self.collection_name not in collection_names:
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
        """Check if Qdrant client is connected"""
        if not self.client:
            return False
        try:
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
        """Store a Q&A embedding (payload is kept as-is)"""
        if not self.client or not self.is_connected():
            logger.error("Qdrant client not connected")
            return False

        # التحقق من صحة الـ embedding
        if not embedding or not isinstance(embedding, list):
            logger.error(f"Invalid embedding for qa_id {qa_id}: {type(embedding)} - {embedding}")
            return False
        
        # التحقق من أن جميع القيم أرقام
        if not all(isinstance(val, (int, float)) for val in embedding):
            logger.error(f"Embedding contains non-numeric values for qa_id {qa_id}")
            return False

        try:
            payload = metadata or {}
            payload.update({"qa_id": qa_id, "question": question})

            point = PointStruct(
                id=str(uuid4()),
                vector=embedding,
                payload=payload
            )

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
        """Search for similar questions"""
        if not self.client or not self.is_connected():
            logger.error("Qdrant client not connected")
            return []

        # التحقق من صحة الـ query_embedding
        if not query_embedding or not isinstance(query_embedding, list):
            logger.error(f"Invalid query embedding: {type(query_embedding)} - {query_embedding}")
            return []
        
        # التحقق من أن جميع القيم أرقام
        if not all(isinstance(val, (int, float)) for val in query_embedding):
            logger.error("Query embedding contains non-numeric values")
            return []

        try:
            query_filter = None
            if filters:
                conditions = []
                for key, value in filters.items():
                    if isinstance(value, str):
                        conditions.append(FieldCondition(key=key, match=MatchValue(value=value)))
                    elif isinstance(value, (int, float)):
                        conditions.append(FieldCondition(key=key, range=Range(gte=value)))
                if conditions:
                    query_filter = Filter(must=conditions)

            search_result = await asyncio.to_thread(
                self.client.search,
                collection_name=self.collection_name,
                query_vector=query_embedding,
                limit=limit,
                score_threshold=score_threshold,
                query_filter=query_filter
            )

            results = []
            for hit in search_result:
                results.append({
                    "qa_id": hit.payload.get("qa_id"),
                    "question": hit.payload.get("question"),
                    "answer": hit.payload.get("answer"),
                    "similarity_score": float(hit.score),
                    "metadata": {k: v for k, v in hit.payload.items() if k not in ["qa_id", "question", "answer"]}
                })
            return results

        except Exception as e:
            logger.error(f"Failed to search similar questions: {e}")
            return []

    async def batch_store_embeddings(self, qa_data: List[Dict[str, Any]]) -> int:
        """Batch store multiple Q&A embeddings"""
        if not self.client or not self.is_connected():
            return 0

        try:
            points = []
            for data in qa_data:
                payload = data.get("metadata", {}).copy()
                payload.update({
                    "qa_id": data.get("qa_id"),
                    "question": data.get("question")
                })
                point = PointStruct(
                    id=str(uuid4()),
                    vector=data.get("embedding"),
                    payload=payload
                )
                points.append(point)

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


# Global instance
qdrant_service = QdrantService()
