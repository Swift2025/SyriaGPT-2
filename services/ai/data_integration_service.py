import json
import logging
import time
import asyncio
from pathlib import Path
from typing import Dict, List, Any, Optional
import os

from services.database.redis_service import redis_service
from .qdrant_service import qdrant_service
from .embedding_service import embedding_service
from config.logging_config import get_logger

logger = get_logger(__name__)

class DataIntegrationService:
    """
    Service for integrating Syria knowledge data from the data folder
    into Redis cache and Qdrant vector database.
    """
    
    def __init__(self):
        self.data_path = Path(__file__).parent.parent.parent / "data" / "syria_knowledge"
        self.knowledge_files = [
            "general.json",
            "cities.json", 
            "culture.json",
            "economy.json",
            "government.json",
            "Real_post_liberation_events.json"
        ]
        
    async def initialize_knowledge_base(self) -> Dict[str, Any]:
        """
        Initialize the complete knowledge base by loading data into both Redis and Qdrant.
        This should be called during application startup.
        """
        logger.info("🚀 Starting Syria knowledge base initialization...")
        
        try:
            # Step 1: Load data into Redis cache
            redis_result = await self._load_data_to_redis()
            if redis_result.get("status") == "error":
                logger.error(f"Redis initialization failed: {redis_result.get('message')}")
                # Continue with Qdrant even if Redis fails
                redis_result = {"status": "error", "message": "Redis service unavailable"}
            
            # Step 2: Load data into Qdrant vector database
            qdrant_result = await self._load_data_to_qdrant()
            if qdrant_result.get("status") == "error":
                logger.error(f"Qdrant initialization failed: {qdrant_result.get('message')}")
                # Continue with Redis even if Qdrant fails
                qdrant_result = {"status": "error", "message": "Qdrant service unavailable"}
            
            # Step 3: Generate summary statistics
            summary = self._generate_summary(redis_result, qdrant_result)
            
            # Determine overall status
            if redis_result.get("status") == "success" or qdrant_result.get("status") == "success":
                overall_status = "success"
                logger.info(f"✅ Knowledge base initialization completed: {summary}")
            else:
                overall_status = "error"
                logger.error("❌ Both Redis and Qdrant initialization failed")
            
            return {
                "status": overall_status,
                "redis": redis_result,
                "qdrant": qdrant_result,
                "summary": summary
            }
            
        except Exception as e:
            logger.error(f"❌ Knowledge base initialization failed: {e}")
            return {
                "status": "error",
                "error": str(e)
            }
    
    async def _load_data_to_redis(self) -> Dict[str, Any]:
        """Load Syria knowledge data into Redis cache"""
        logger.info("📥 Loading data into Redis cache...")
        
        if not redis_service.is_connected():
            return {"status": "error", "message": "Redis not connected"}
        
        try:
            total_cached = 0
            file_stats = {}
            
            for filename in self.knowledge_files:
                file_path = self.data_path / filename
                if file_path.exists():
                    cached_count = await self._cache_json_file_redis(file_path)
                    total_cached += cached_count
                    file_stats[filename] = cached_count
                    logger.info(f"📄 Cached {cached_count} items from {filename}")
                else:
                    logger.warning(f"⚠️ File not found: {file_path}")
                    file_stats[filename] = 0
            
            # Cache metadata
            redis_service.client.set("syria:metadata:total_items", total_cached)
            redis_service.client.set("syria:metadata:last_updated", str(asyncio.get_event_loop().time()))
            
            return {
                "status": "success",
                "total_cached": total_cached,
                "file_stats": file_stats
            }
            
        except Exception as e:
            logger.error(f"❌ Redis data loading failed: {e}")
            return {"status": "error", "message": str(e)}
    
    async def _load_data_to_qdrant(self) -> Dict[str, Any]:
        """Load Syria knowledge data into Qdrant vector database"""
        logger.info("📥 Loading data into Qdrant vector database...")
        
        if not qdrant_service.is_connected():
            return {"status": "error", "message": "Qdrant not connected"}
        
        try:
            total_vectors = 0
            file_stats = {}
            
            for filename in self.knowledge_files:
                file_path = self.data_path / filename
                if file_path.exists():
                    vector_count = await self._load_json_file_to_qdrant(file_path)
                    total_vectors += vector_count
                    file_stats[filename] = vector_count
                    logger.info(f"📄 Loaded {vector_count} vectors from {filename}")
                else:
                    logger.warning(f"⚠️ File not found: {file_path}")
                    file_stats[filename] = 0
            
            return {
                "status": "success",
                "total_vectors": total_vectors,
                "file_stats": file_stats
            }
            
        except Exception as e:
            logger.error(f"❌ Qdrant data loading failed: {e}")
            return {"status": "error", "message": str(e)}
    
    async def _cache_json_file_redis(self, file_path: Path) -> int:
        """Cache a single JSON file's content into Redis"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            category = data.get("category", file_path.stem)
            qa_pairs = data.get("qa_pairs", [])
            
            cached_count = 0
            
            for qa_pair in qa_pairs:
                qa_id = qa_pair.get("id")
                if qa_id:
                    # Cache the full Q&A pair
                    redis_service.client.hset(f"syria:qa:{qa_id}", mapping={
                        "question_variants": json.dumps(qa_pair.get("question_variants", []), ensure_ascii=False),
                        "answer": qa_pair.get("answer", ""),
                        "keywords": json.dumps(qa_pair.get("keywords", []), ensure_ascii=False),
                        "confidence": str(qa_pair.get("confidence", 1.0)),
                        "source": qa_pair.get("source", ""),
                        "category": category
                    })
                    
                    # Create keyword indexes for fast searching
                    for keyword in qa_pair.get("keywords", []):
                        redis_service.client.sadd(f"syria:keyword:{keyword.lower()}", qa_id)
                    
                    # Create category index
                    redis_service.client.sadd(f"syria:category:{category}", qa_id)
                    
                    cached_count += 1
            
            # Cache category metadata
            redis_service.client.hset(f"syria:category_info:{category}", mapping={
                "description": data.get("description", ""),
                "total_items": str(len(qa_pairs))
            })
            
            return cached_count
            
        except Exception as e:
            logger.error(f"❌ Error caching file {file_path}: {e}")
            return 0
    
    async def _load_json_file_to_qdrant(self, file_path: Path) -> int:
        """Load a single JSON file's content into Qdrant vector database"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            category = data.get("category", file_path.stem)
            qa_pairs = data.get("qa_pairs", [])
            
            vector_count = 0
            
            # Process Q&A pairs in batches for efficiency
            batch_size = 50
            for i in range(0, len(qa_pairs), batch_size):
                batch = qa_pairs[i:i + batch_size]
                batch_data = []
                
                for qa_pair in batch:
                    qa_id = qa_pair.get("id")
                    if not qa_id:
                        continue
                    
                    # Use the first question variant for embedding
                    question_text = qa_pair.get("question_variants", [qa_pair.get("question", "")])[0]
                    
                    # Generate embedding for the question
                    embedding = await embedding_service.generate_embedding(question_text)
                    if not embedding:
                        continue
                    
                    # Prepare metadata
                    metadata = {
                        "category": category,
                        "confidence": qa_pair.get("confidence", 1.0),
                        "keywords": qa_pair.get("keywords", []),
                        "source": qa_pair.get("source", "syria_knowledge"),
                        "question_variants": qa_pair.get("question_variants", []),
                        "file_source": file_path.name
                    }
                    
                    batch_data.append({
                        "qa_id": qa_id,
                        "question": question_text,
                        "answer": qa_pair.get("answer", ""),
                        "embedding": embedding,
                        "metadata": metadata
                    })
                
                # Batch store in Qdrant
                if batch_data:
                    stored_count = await qdrant_service.batch_store_embeddings(batch_data)
                    vector_count += stored_count
            
            return vector_count
            
        except Exception as e:
            logger.error(f"❌ Error loading file {file_path} to Qdrant: {e}")
            return 0
    
    def _generate_summary(self, redis_result: Dict[str, Any], qdrant_result: Dict[str, Any]) -> Dict[str, Any]:
        """Generate summary statistics for the knowledge base"""
        redis_total = redis_result.get("total_cached", 0) if redis_result.get("status") == "success" else 0
        qdrant_total = qdrant_result.get("total_vectors", 0) if qdrant_result.get("status") == "success" else 0
        
        return {
            "total_qa_pairs": max(redis_total, qdrant_total),
            "redis_cached": redis_total,
            "qdrant_vectors": qdrant_total,
            "files_processed": len(self.knowledge_files),
            "redis_status": redis_result.get("status", "unknown"),
            "qdrant_status": qdrant_result.get("status", "unknown")
        }
    
    async def reload_knowledge_base(self) -> Dict[str, Any]:
        """Reload the entire knowledge base (useful for updates)"""
        logger.info("🔄 Reloading Syria knowledge base...")
        
        # Clear existing data
        await self._clear_existing_data()
        
        # Reload data
        return await self.initialize_knowledge_base()
    
    async def _clear_existing_data(self):
        """Clear existing data from Redis and Qdrant"""
        try:
            # Clear Redis data
            if redis_service.is_connected():
                # Get all Syria-related keys
                syria_keys = redis_service.client.keys("syria:*")
                if syria_keys:
                    redis_service.client.delete(*syria_keys)
                    logger.info(f"🗑️ Cleared {len(syria_keys)} Redis keys")
            
            # Clear Qdrant collection
            if qdrant_service.is_connected():
                # This would require recreating the collection
                # For now, we'll just log it
                logger.info("🗑️ Qdrant collection would be cleared (requires collection recreation)")
                
        except Exception as e:
            logger.error(f"❌ Error clearing existing data: {e}")
    
    async def get_knowledge_base_stats(self) -> Dict[str, Any]:
        """Get comprehensive statistics about the knowledge base"""
        try:
            redis_stats = redis_service.get_cache_stats() if redis_service.is_connected() else {"connected": False}
            qdrant_stats = await qdrant_service.get_collection_stats() if qdrant_service.is_connected() else {"connected": False}
            
            # Get file information
            file_info = {}
            total_file_size = 0
            for filename in self.knowledge_files:
                file_path = self.data_path / filename
                if file_path.exists():
                    file_size = file_path.stat().st_size
                    total_file_size += file_size
                    file_info[filename] = {
                        "size_bytes": file_size,
                        "size_mb": round(file_size / (1024 * 1024), 2),
                        "exists": True
                    }
                else:
                    file_info[filename] = {
                        "exists": False
                    }
            
            return {
                "redis": redis_stats,
                "qdrant": qdrant_stats,
                "files": file_info,
                "total_file_size_mb": round(total_file_size / (1024 * 1024), 2),
                "knowledge_files_count": len(self.knowledge_files)
            }
            
        except Exception as e:
            logger.error(f"❌ Error getting knowledge base stats: {e}")
            return {"error": str(e)}

# Global data integration service instance
data_integration_service = DataIntegrationService()
