import json
import os
import logging
import time
from typing import Dict, List, Optional, Any
import redis
from redis import Redis
import asyncio
from pathlib import Path
from config.logging_config import get_logger, log_function_entry, log_function_exit, log_performance, log_error_with_context

logger = get_logger(__name__)

class RedisService:
    def __init__(self):
        log_function_entry(logger, "__init__")
        start_time = time.time()
        
        logger.debug("🔧 Initializing RedisService...")
        default_redis_url = "redis://redis:6379" 
        self.redis_url = os.getenv("REDIS_URL", default_redis_url)
        logger.debug(f"🔧 Redis URL: {self.redis_url}")
        self.client: Optional[Redis] = None
        self.syria_data_path = Path(__file__).parent.parent / "data" / "syria_knowledge"
        logger.debug(f"🔧 Syria data path: {self.syria_data_path}")
        
        try:
            self._ensure_connection()
            duration = time.time() - start_time
            log_performance(logger, "RedisService initialization", duration)
            logger.debug("✅ RedisService initialized successfully")
        except Exception as e:
            duration = time.time() - start_time
            log_error_with_context(logger, e, "RedisService initialization", duration=duration)
            logger.error(f"❌ RedisService initialization failed: {e}")
        
        log_function_exit(logger, "__init__", duration=time.time() - start_time)
        
    def _ensure_connection(self):
        """Ensure Redis connection is established"""
        log_function_entry(logger, "_ensure_connection", redis_url=self.redis_url)
        start_time = time.time()
        
        logger.debug("🔧 Establishing Redis connection...")
        try:
            self.client = redis.from_url(self.redis_url, decode_responses=True)
            logger.debug("✅ Redis client created")
            
            # Test connection
            logger.debug("🔧 Testing Redis connection...")
            self.client.ping()
            duration = time.time() - start_time
            log_performance(logger, "Redis connection establishment", duration)
            logger.info("✅ Redis connection established successfully")
            
        except Exception as e:
            duration = time.time() - start_time
            log_error_with_context(logger, e, "_ensure_connection", redis_url=self.redis_url, duration=duration)
            logger.warning(f"❌ Failed to connect to Redis: {e}")
            self.client = None
            # Don't raise exception - allow graceful degradation
        
        log_function_exit(logger, "_ensure_connection", duration=time.time() - start_time)
    
    def is_connected(self) -> bool:
        """Check if Redis is connected"""
        try:
            if self.client:
                self.client.ping()
                return True
        except Exception:
            return False
        return False
    
    def load_syria_knowledge_to_cache(self) -> bool:
        """Load all Syria knowledge JSON files into Redis cache"""
        if not self.is_connected():
            logger.error("Redis not connected, cannot load Syria knowledge")
            return False
            
        try:
            json_files = [
                "general.json",
                "cities.json", 
                "culture.json",
                "economy.json",
                "government.json",
                "Real_post_liberation_events.json"
            ]
            
            total_cached = 0
            
            for filename in json_files:
                file_path = self.syria_data_path / filename
                if file_path.exists():
                    cached_count = self._cache_json_file(file_path)
                    total_cached += cached_count
                    logger.info(f"Cached {cached_count} items from {filename}")
                else:
                    logger.warning(f"File not found: {file_path}")
            
            # Cache metadata
            self.client.set("syria:metadata:total_items", total_cached)
            self.client.set("syria:metadata:last_updated", str(asyncio.get_event_loop().time()))
            
            logger.info(f"Successfully cached {total_cached} Syria knowledge items")
            return True
            
        except Exception as e:
            logger.error(f"Error loading Syria knowledge to cache: {e}")
            return False
    
    def _cache_json_file(self, file_path: Path) -> int:
        """Cache a single JSON file's content"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            category = data.get("category", file_path.stem)
            qa_pairs = data.get("qa_pairs", [])
            
            cached_count = 0
            
            # Cache each Q&A pair
            for qa_pair in qa_pairs:
                qa_id = qa_pair.get("id")
                if qa_id:
                    # Cache the full Q&A pair
                    self.client.hset(f"syria:qa:{qa_id}", mapping={
                        "question_variants": json.dumps(qa_pair.get("question_variants", []), ensure_ascii=False),
                        "answer": qa_pair.get("answer", ""),
                        "keywords": json.dumps(qa_pair.get("keywords", []), ensure_ascii=False),
                        "confidence": str(qa_pair.get("confidence", 1.0)),
                        "source": qa_pair.get("source", ""),
                        "category": category
                    })
                    
                    # Create keyword indexes for fast searching
                    for keyword in qa_pair.get("keywords", []):
                        self.client.sadd(f"syria:keyword:{keyword.lower()}", qa_id)
                    
                    # Create category index
                    self.client.sadd(f"syria:category:{category}", qa_id)
                    
                    cached_count += 1
            
            # Cache category metadata
            self.client.hset(f"syria:category_info:{category}", mapping={
                "description": data.get("description", ""),
                "total_items": str(len(qa_pairs))
            })
            
            return cached_count
            
        except Exception as e:
            logger.error(f"Error caching file {file_path}: {e}")
            return 0
    
    def search_by_keyword(self, keyword: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Search Syria knowledge by keyword"""
        if not self.is_connected():
            return []
        
        try:
            keyword_lower = keyword.lower()
            qa_ids = self.client.smembers(f"syria:keyword:{keyword_lower}")
            
            results = []
            for qa_id in list(qa_ids)[:limit]:
                qa_data = self.client.hgetall(f"syria:qa:{qa_id}")
                if qa_data:
                    results.append({
                        "id": qa_id,
                        "question_variants": json.loads(qa_data.get("question_variants", "[]")),
                        "answer": qa_data.get("answer", ""),
                        "keywords": json.loads(qa_data.get("keywords", "[]")),
                        "confidence": float(qa_data.get("confidence", 1.0)),
                        "source": qa_data.get("source", ""),
                        "category": qa_data.get("category", "")
                    })
            
            return results
            
        except Exception as e:
            logger.error(f"Error searching by keyword '{keyword}': {e}")
            return []
    
    def search_by_category(self, category: str, limit: int = 20) -> List[Dict[str, Any]]:
        """Get all items from a specific category"""
        if not self.is_connected():
            return []
        
        try:
            qa_ids = self.client.smembers(f"syria:category:{category}")
            
            results = []
            for qa_id in list(qa_ids)[:limit]:
                qa_data = self.client.hgetall(f"syria:qa:{qa_id}")
                if qa_data:
                    results.append({
                        "id": qa_id,
                        "question_variants": json.loads(qa_data.get("question_variants", "[]")),
                        "answer": qa_data.get("answer", ""),
                        "keywords": json.loads(qa_data.get("keywords", "[]")),
                        "confidence": float(qa_data.get("confidence", 1.0)),
                        "source": qa_data.get("source", ""),
                        "category": qa_data.get("category", "")
                    })
            
            return results
            
        except Exception as e:
            logger.error(f"Error searching by category '{category}': {e}")
            return []
    
    def get_qa_by_id(self, qa_id: str) -> Optional[Dict[str, Any]]:
        """Get specific Q&A pair by ID"""
        if not self.is_connected():
            return None
        
        try:
            qa_data = self.client.hgetall(f"syria:qa:{qa_id}")
            if qa_data:
                return {
                    "id": qa_id,
                    "question_variants": json.loads(qa_data.get("question_variants", "[]")),
                    "answer": qa_data.get("answer", ""),
                    "keywords": json.loads(qa_data.get("keywords", "[]")),
                    "confidence": float(qa_data.get("confidence", 1.0)),
                    "source": qa_data.get("source", ""),
                    "category": qa_data.get("category", "")
                }
            return None
            
        except Exception as e:
            logger.error(f"Error getting Q&A by ID '{qa_id}': {e}")
            return None
    
    def get_all_categories(self) -> List[str]:
        """Get all available categories"""
        if not self.is_connected():
            return []
        
        try:
            pattern = "syria:category_info:*"
            keys = self.client.keys(pattern)
            categories = [key.replace("syria:category_info:", "") for key in keys]
            return categories
            
        except Exception as e:
            logger.error(f"Error getting categories: {e}")
            return []
    
    def get_category_info(self, category: str) -> Optional[Dict[str, Any]]:
        """Get information about a specific category"""
        if not self.is_connected():
            return None
        
        try:
            info = self.client.hgetall(f"syria:category_info:{category}")
            if info:
                return {
                    "category": category,
                    "description": info.get("description", ""),
                    "total_items": int(info.get("total_items", 0))
                }
            return None
            
        except Exception as e:
            logger.error(f"Error getting category info for '{category}': {e}")
            return None
    
    def fuzzy_search(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Perform fuzzy search across all Syria knowledge with improved relevance scoring"""
        if not self.is_connected():
            return []
        
        try:
            query_lower = query.lower().strip()
            query_words = query_lower.split()
            all_results = []
            
            # First, try to find exact question matches
            exact_question_matches = self._search_exact_question_matches(query_lower)
            if exact_question_matches:
                # If we find exact matches, return them with high confidence
                return exact_question_matches[:limit]
            
            # If no exact matches, perform semantic search with relevance scoring
            scored_results = []
            
            # Get all Q&A pairs
            all_qa_keys = self.client.keys("syria:qa:*")
            
            for qa_key in all_qa_keys:
                qa_id = qa_key.replace("syria:qa:", "")
                qa_data = self.client.hgetall(qa_key)
                
                if qa_data:
                    # Calculate relevance score
                    relevance_score = self._calculate_relevance_score(
                        query_lower, query_words, qa_data
                    )
                    
                    if relevance_score > 0:  # Only include relevant results
                        result = {
                            "id": qa_id,
                            "question_variants": json.loads(qa_data.get("question_variants", "[]")),
                            "answer": qa_data.get("answer", ""),
                            "keywords": json.loads(qa_data.get("keywords", "[]")),
                            "confidence": float(qa_data.get("confidence", 1.0)),
                            "source": qa_data.get("source", ""),
                            "category": qa_data.get("category", ""),
                            "relevance_score": relevance_score
                        }
                        scored_results.append(result)
            
            # Sort by relevance score (highest first) and return top results
            scored_results.sort(key=lambda x: x["relevance_score"], reverse=True)
            
            # Remove relevance_score from final results
            for result in scored_results[:limit]:
                result.pop("relevance_score", None)
            
            return scored_results[:limit]
            
        except Exception as e:
            logger.error(f"Error in fuzzy search for '{query}': {e}")
            return []
    
    def _search_exact_question_matches(self, query: str) -> List[Dict[str, Any]]:
        """Search for exact question matches in question variants"""
        if not self.is_connected():
            return []
        
        try:
            exact_matches = []
            all_qa_keys = self.client.keys("syria:qa:*")
            
            for qa_key in all_qa_keys:
                qa_id = qa_key.replace("syria:qa:", "")
                qa_data = self.client.hgetall(qa_key)
                
                if qa_data:
                    question_variants = json.loads(qa_data.get("question_variants", "[]"))
                    
                    # Check for exact matches in question variants
                    for variant in question_variants:
                        if query == variant.lower().strip():
                            result = {
                                "id": qa_id,
                                "question_variants": question_variants,
                                "answer": qa_data.get("answer", ""),
                                "keywords": json.loads(qa_data.get("keywords", "[]")),
                                "confidence": float(qa_data.get("confidence", 1.0)),
                                "source": qa_data.get("source", ""),
                                "category": qa_data.get("category", "")
                            }
                            exact_matches.append(result)
                            break
            
            return exact_matches
            
        except Exception as e:
            logger.error(f"Error in exact question search: {e}")
            return []
    
    def _calculate_relevance_score(self, query: str, query_words: List[str], qa_data: Dict[str, str]) -> float:
        """Calculate relevance score for a Q&A pair based on the query"""
        try:
            score = 0.0
            
            # Get question variants and keywords
            question_variants = json.loads(qa_data.get("question_variants", "[]"))
            keywords = json.loads(qa_data.get("keywords", "[]"))
            
            # Check for exact question match (highest priority)
            for variant in question_variants:
                if query == variant.lower().strip():
                    return 100.0  # Maximum score for exact match
            
            # Check for partial question matches
            for variant in question_variants:
                variant_lower = variant.lower()
                if query in variant_lower or variant_lower in query:
                    score += 50.0
                elif any(word in variant_lower for word in query_words if len(word) > 2):
                    score += 20.0
            
            # Check keyword matches
            keywords_lower = [kw.lower() for kw in keywords]
            for word in query_words:
                if len(word) > 2:  # Only consider words longer than 2 characters
                    if word in keywords_lower:
                        score += 10.0
                    elif any(word in kw for kw in keywords_lower):
                        score += 5.0
            
            # Bonus for important keywords like "عاصمة" (capital)
            important_keywords = ["عاصمة", "capital", "دمشق", "damascus"]
            if any(keyword in query for keyword in important_keywords):
                if any(keyword in keywords_lower for keyword in important_keywords):
                    score += 15.0
            
            return score
            
        except Exception as e:
            logger.error(f"Error calculating relevance score: {e}")
            return 0.0
    
    def cache_custom_data(self, key: str, data: Any, expiry: int = 3600) -> bool:
        """Cache custom data with optional expiry"""
        if not self.is_connected():
            return False
        
        try:
            serialized_data = json.dumps(data, ensure_ascii=False)
            self.client.setex(f"syria:custom:{key}", expiry, serialized_data)
            return True
            
        except Exception as e:
            logger.error(f"Error caching custom data '{key}': {e}")
            return False
    
    def get_custom_data(self, key: str) -> Any:
        """Retrieve custom cached data"""
        if not self.is_connected():
            return None
        
        try:
            data = self.client.get(f"syria:custom:{key}")
            if data:
                return json.loads(data)
            return None
            
        except Exception as e:
            logger.error(f"Error getting custom data '{key}': {e}")
            return None
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get Redis cache statistics"""
        if not self.is_connected():
            return {"connected": False}
        
        try:
            total_items = self.client.get("syria:metadata:total_items") or "0"
            last_updated = self.client.get("syria:metadata:last_updated") or "Never"
            
            # Count different types of keys
            qa_keys = len(self.client.keys("syria:qa:*"))
            keyword_keys = len(self.client.keys("syria:keyword:*"))
            category_keys = len(self.client.keys("syria:category:*"))
            
            return {
                "connected": True,
                "total_syria_items": int(total_items),
                "last_updated": last_updated,
                "qa_pairs_cached": qa_keys,
                "keyword_indexes": keyword_keys,
                "category_indexes": category_keys,
                "redis_memory_info": self.client.info("memory")
            }
            
        except Exception as e:
            logger.error(f"Error getting cache stats: {e}")
            return {"connected": False, "error": str(e)}


# Global Redis service instance
redis_service = RedisService()

def get_redis_service():
    """Get the global Redis service instance"""
    return redis_service