import logging
from typing import Dict, List, Optional, Any
import asyncio
import time
from datetime import datetime
import re
import uuid

# Services
from .qdrant_service import qdrant_service
from .embedding_service import embedding_service
from .gemini_service import gemini_service
from .web_scraping_service import web_scraping_service
from services.repositories.qa_pair_repository import qa_pair_repository
from services.database.database import get_db
from config.logging_config import (
    get_logger,
    log_function_entry,
    log_function_exit,
    log_performance,
    log_error_with_context,
)

logger = get_logger(__name__)


class IntelligentQAService:
    """
    Enhanced intelligent Q&A processing service with web scraping integration.
    
    New Flow:
    1. Receive question
    2. Generate embedding using latest GenAI
    3. Semantic search in Qdrant
    4. If high similarity found -> return stored answer from PostgreSQL
    5. If no match -> fetch fresh content from web scraping
    6. Generate new answer with Gemini + web content
    7. Store in both Qdrant and PostgreSQL
    8. Generate question variants and store them
    """

    def __init__(self):
        log_function_entry(logger, "__init__")
        start_time = time.time()

        logger.debug("🔧 Initializing Enhanced IntelligentQAService...")
        self.semantic_search_threshold: float = 0.85   # consider candidates above this
        self.quality_threshold: float = 0.95           # return immediately if >= this
        self.max_variants_to_generate: int = 5
        self._initialized: bool = False

        duration = time.time() - start_time
        logger.debug(
            f"✅ Enhanced IntelligentQAService initialized (semantic≥{self.semantic_search_threshold}, quality≥{self.quality_threshold})"
        )
        log_performance(logger, "Enhanced IntelligentQAService initialization", duration)
        log_function_exit(logger, "__init__", duration=duration)

    async def initialize_system(self) -> Dict[str, Any]:
        """
        Initialize the Q&A system including knowledge base loading.
        Call this during application startup.
        """
        log_function_entry(logger, "initialize_system")
        start_time = time.time()

        logger.info("🚀 Initializing Enhanced Syria GPT Q&A system...")

        try:
            # Ensure Qdrant collection exists
            await qdrant_service._ensure_collection_exists()
            
            # Test all services
            health_checks = await self._check_system_health()
            
            # Count healthy services
            healthy_services = sum(1 for check in health_checks.values() if check.get("status") == "healthy")
            total_services = len(health_checks)
            
            # Allow initialization if core services (Qdrant and Embedding) are healthy
            # Gemini can be unhealthy due to quota limits, but system should still work
            core_services = ["qdrant", "embedding"]
            core_healthy = sum(1 for service in core_services if health_checks.get(service, {}).get("status") == "healthy")
            
            if core_healthy == len(core_services):
                self._initialized = True
                duration = time.time() - start_time
                log_performance(logger, "System initialization", duration)
                logger.info(f"✅ Enhanced Syria GPT Q&A system initialized successfully ({healthy_services}/{total_services} services healthy)")
                return {"status": "success", "health_checks": health_checks, "healthy_count": healthy_services}
            else:
                error_msg = f"Core services are unhealthy ({core_healthy}/{len(core_services)} core services healthy)"
                logger.error(f"❌ Failed to initialize system: {error_msg}")
                log_error_with_context(
                    logger, Exception(error_msg), "initialize_system", health_checks=health_checks
                )
                return {"status": "error", "error": error_msg, "health_checks": health_checks}

        except Exception as e:
            duration = time.time() - start_time
            log_error_with_context(logger, e, "initialize_system", duration=duration)
            logger.error(f"❌ System initialization failed: {e}")
            return {"status": "error", "error": str(e)}

    async def _check_system_health(self) -> Dict[str, Dict[str, Any]]:
        """Check health of all system services"""
        health_checks = {}
        
        # Check Qdrant service
        try:
            qdrant_health = await qdrant_service.get_health()
            health_checks["qdrant"] = {
                "status": "healthy" if qdrant_health.get("available") else "unhealthy",
                "details": qdrant_health
            }
        except Exception as e:
            health_checks["qdrant"] = {"status": "unhealthy", "error": str(e)}
        
        # Check Embedding service
        try:
            embedding_health = await embedding_service.get_system_health()
            health_checks["embedding"] = {
                "status": "healthy" if embedding_health.get("available") else "unhealthy",
                "details": embedding_health
            }
        except Exception as e:
            health_checks["embedding"] = {"status": "unhealthy", "error": str(e)}
        
        # Check Gemini service
        try:
            gemini_health = await gemini_service.get_health()
            health_checks["gemini"] = {
                "status": "healthy" if gemini_health.get("available") else "unhealthy",
                "details": gemini_health
            }
        except Exception as e:
            health_checks["gemini"] = {"status": "unhealthy", "error": str(e)}
        
        # Check Web Scraping service
        try:
            web_health = await web_scraping_service.get_health()
            health_checks["web_scraping"] = {
                "status": "healthy" if web_health.get("available") else "unhealthy",
                "details": web_health
            }
        except Exception as e:
            health_checks["web_scraping"] = {"status": "unhealthy", "error": str(e)}
        
        return health_checks

    async def process_question(
        self,
        question: str,
        user_id: Optional[int] = None,
        language: str = "auto",
        context: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Main method to process a question and return an intelligent answer.
        
        Args:
            question: User's question
            user_id: Optional user ID for tracking
            language: Language preference (auto-detected if "auto")
            context: Optional context information
            
        Returns:
            Dictionary with answer and metadata
        """
        log_function_entry(logger, "process_question", question=question[:100], user_id=user_id)
        start_time = time.time()
        
        if not self._initialized:
            await self.initialize_system()
        
        try:
            # Normalize and preprocess question
            normalized_question = self._normalize_question(question)
            
            # Generate embedding for semantic search
            question_embedding = await embedding_service.generate_embedding(normalized_question)
            if not question_embedding:
                raise RuntimeError("Failed to generate question embedding")
            
            # Search for similar questions in Qdrant
            search_results = await qdrant_service.search_similar_questions(
                question_embedding,
                limit=5,
                threshold=self.semantic_search_threshold
            )
            
            # Check if we have a high-quality match
            if search_results and search_results[0].get("score", 0) >= self.quality_threshold:
                best_match = search_results[0]
                answer_id = best_match.get("payload", {}).get("answer_id")
                
                if answer_id:
                    # Fetch answer from PostgreSQL
                    answer = await qa_pair_repository.get_answer_by_id(answer_id)
                    if answer:
                        duration = time.time() - start_time
                        log_performance(logger, "Question processing (cached)", duration)
                        log_function_exit(logger, "process_question", result="cached_answer", duration=duration)
                        
                        return {
                            "status": "success",
                            "answer": answer.content,
                            "source": "cached",
                            "confidence": best_match.get("score", 0),
                            "processing_time": duration,
                            "question_variants": await self._get_question_variants(answer_id)
                        }
            
            # No high-quality match found, generate fresh answer
            logger.info(f"🔍 No high-quality match found, generating fresh answer for: {normalized_question[:100]}...")
            
            # Get fresh content from web scraping
            web_content = await self._get_fresh_content(normalized_question, context)
            
            # Generate answer using Gemini
            answer_result = await gemini_service.answer_question(
                question=normalized_question,
                context=web_content,
                language=language
            )
            
            if not answer_result or not answer_result.get("answer"):
                raise RuntimeError("Failed to generate answer from Gemini")
            
            # Store the new Q&A pair
            qa_pair_id = await self._store_qa_pair(
                question=normalized_question,
                answer=answer_result["answer"],
                user_id=user_id,
                context=context,
                web_content=web_content
            )
            
            # Store in Qdrant for future semantic search
            await qdrant_service.store_qa_pair(
                qa_pair_id=qa_pair_id,
                question=normalized_question,
                answer=answer_result["answer"],
                question_embedding=question_embedding
            )
            
            # Generate and store question variants
            await self._generate_and_store_variants(
                qa_pair_id=qa_pair_id,
                original_question=normalized_question,
                question_embedding=question_embedding
            )
            
            duration = time.time() - start_time
            log_performance(logger, "Question processing (fresh)", duration)
            log_function_exit(logger, "process_question", result="fresh_answer", duration=duration)
            
            return {
                "status": "success",
                "answer": answer_result["answer"],
                "source": "fresh",
                "confidence": answer_result.get("confidence", 0.8),
                "processing_time": duration,
                "qa_pair_id": qa_pair_id,
                "web_sources": web_content.get("sources", []) if web_content else []
            }
            
        except Exception as e:
            duration = time.time() - start_time
            log_error_with_context(logger, e, "process_question", question=question, duration=duration)
            logger.error(f"❌ Question processing failed: {e}")
            
            return {
                "status": "error",
                "error": str(e),
                "processing_time": duration
            }

    def _normalize_question(self, question: str) -> str:
        """Normalize question for better matching"""
        # Remove extra whitespace
        normalized = " ".join(question.split())
        
        # Remove punctuation for better matching
        normalized = re.sub(r'[^\w\s]', ' ', normalized)
        
        # Convert to lowercase
        normalized = normalized.lower().strip()
        
        return normalized

    async def _get_fresh_content(self, question: str, context: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Get fresh content from web scraping"""
        try:
            # Use web scraping service to get relevant content
            scraped_content = await web_scraping_service.search_and_scrape(
                query=question,
                max_results=3,
                context=context
            )
            
            if scraped_content and scraped_content.get("content"):
                return {
                    "content": scraped_content["content"],
                    "sources": scraped_content.get("sources", []),
                    "metadata": scraped_content.get("metadata", {})
                }
            
            return None
            
        except Exception as e:
            logger.warning(f"Web scraping failed, proceeding without fresh content: {e}")
            return None

    async def _store_qa_pair(
        self,
        question: str,
        answer: str,
        user_id: Optional[int] = None,
        context: Optional[str] = None,
        web_content: Optional[Dict[str, Any]] = None
    ) -> int:
        """Store Q&A pair in PostgreSQL"""
        try:
            # Create Q&A pair
            qa_pair_data = {
                "question": question,
                "answer": answer,
                "user_id": user_id,
                "context": context or "",
                "metadata": {
                    "web_content": web_content,
                    "created_at": datetime.utcnow().isoformat(),
                    "source": "intelligent_qa_service"
                }
            }
            
            qa_pair_id = await qa_pair_repository.create_qa_pair(qa_pair_data)
            logger.info(f"✅ Stored Q&A pair with ID: {qa_pair_id}")
            
            return qa_pair_id
            
        except Exception as e:
            logger.error(f"Failed to store Q&A pair: {e}")
            raise RuntimeError(f"Failed to store Q&A pair: {e}")

    async def _generate_and_store_variants(
        self,
        qa_pair_id: int,
        original_question: str,
        question_embedding: List[float]
    ) -> None:
        """Generate and store question variants"""
        try:
            # Generate variants using embedding service
            variants = await embedding_service.generate_question_variants(
                original_question,
                num_variants=self.max_variants_to_generate
            )
            
            # Store variants in Qdrant for better search coverage
            for variant in variants:
                variant_embedding = await embedding_service.generate_embedding(variant)
                if variant_embedding:
                    await qdrant_service.store_qa_pair(
                        qa_pair_id=qa_pair_id,
                        question=variant,
                        answer="",  # Will be linked to the main answer
                        question_embedding=variant_embedding
                    )
            
            logger.info(f"✅ Generated and stored {len(variants)} question variants")
            
        except Exception as e:
            logger.warning(f"Failed to generate question variants: {e}")

    async def _get_question_variants(self, answer_id: int) -> List[str]:
        """Get question variants for an answer"""
        try:
            # This would typically query the database for variants
            # For now, return empty list
            return []
        except Exception as e:
            logger.warning(f"Failed to get question variants: {e}")
            return []

    async def get_system_status(self) -> Dict[str, Any]:
        """Get comprehensive system status"""
        if not self._initialized:
            return {"status": "not_initialized"}
        
        try:
            health_checks = await self._check_system_health()
            return {
                "status": "initialized",
                "health_checks": health_checks,
                "thresholds": {
                    "semantic_search": self.semantic_search_threshold,
                    "quality": self.quality_threshold
                }
            }
        except Exception as e:
            return {"status": "error", "error": str(e)}

# Global service instance
intelligent_qa_service = IntelligentQAService()
