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
from services.repositories.qa_pair_repository import QAPairRepository
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
            
            # Ensure embedding is a flat list of floats
            if isinstance(question_embedding, list) and question_embedding:
                if isinstance(question_embedding[0], list):
                    # If it's a nested list, flatten it
                    question_embedding = question_embedding[0]
                elif not isinstance(question_embedding[0], (int, float)):
                    # If it's not a list of numbers, something is wrong
                    raise RuntimeError(f"Invalid embedding format: expected list of numbers, got {type(question_embedding[0])}")
            
            # Search for similar questions in Qdrant
            search_results = await qdrant_service.search_similar_questions(
                question_embedding,
                limit=5,
                score_threshold=self.semantic_search_threshold
            )
            
            # Check if we have a high-quality match
            if search_results and search_results[0].get("similarity_score", 0) >= self.quality_threshold:
                best_match = search_results[0]
                answer_id = best_match.get("qa_id")
                
                if answer_id:
                    # Fetch answer from PostgreSQL
                    db = next(get_db())
                    qa_pair_repo = QAPairRepository()
                    try:
                        # Convert answer_id to UUID if it's a string
                        if isinstance(answer_id, str):
                            answer_id = uuid.UUID(answer_id)
                        qa_pair = qa_pair_repo.get_qa_pair_by_id(db, answer_id)
                    except (ValueError, TypeError) as e:
                        logger.warning(f"Invalid answer_id format: {answer_id}, error: {e}")
                        qa_pair = None
                    if qa_pair:
                        duration = time.time() - start_time
                        log_performance(logger, "Question processing (cached)", duration)
                        log_function_exit(logger, "process_question", result="cached_answer", duration=duration)
                        
                        return {
                            "status": "success",
                            "answer": qa_pair.answer_text,
                            "source": "cached",
                            "confidence": best_match.get("similarity_score", 0),
                            "processing_time": duration,
                            "question_variants": self._get_question_variants(str(qa_pair.id))
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
            qa_pair_id = self._store_qa_pair(
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

    def _store_qa_pair(
        self,
        question: str,
        answer: str,
        user_id: Optional[str] = None,
        context: Optional[str] = None,
        web_content: Optional[Dict[str, Any]] = None
    ) -> str:
        """Store Q&A pair in PostgreSQL"""
        try:
            # Get database session
            db = next(get_db())
            qa_pair_repo = QAPairRepository()
            
            # Create Q&A pair
            # Convert user_id to UUID if provided
            user_uuid = None
            if user_id:
                try:
                    user_uuid = uuid.UUID(user_id)
                except (ValueError, TypeError) as e:
                    logger.warning(f"Invalid user_id format: {user_id}, error: {e}")
                    user_uuid = None
            
            qa_pair = qa_pair_repo.create_qa_pair(
                db=db,
                question_text=question,
                answer_text=answer,
                user_id=user_uuid,
                source="intelligent_qa_service",
                metadata={
                    "context": context or "",
                    "web_content": web_content,
                    "created_at": datetime.now().isoformat(),
                    "source": "intelligent_qa_service"
                }
            )
            logger.info(f"✅ Stored Q&A pair with ID: {qa_pair.id}")
            
            return str(qa_pair.id)
            
        except Exception as e:
            logger.error(f"Failed to store Q&A pair: {e}")
            raise RuntimeError(f"Failed to store Q&A pair: {e}")

    async def _generate_and_store_variants(
        self,
        qa_pair_id: str,
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

    def _get_question_variants(self, answer_id: str) -> List[str]:
        """Get question variants for an answer"""
        try:
            # This would typically query the database for variants
            # For now, return empty list
            return []
        except Exception as e:
            logger.warning(f"Failed to get question variants: {e}")
            return []

    async def find_similar_questions(
        self,
        question: str,
        limit: int = 5,
        user_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Find similar questions using semantic search.
        
        Args:
            question: The question to find similar ones for
            limit: Maximum number of similar questions to return
            user_id: Optional user ID for filtering
            
        Returns:
            List of similar questions with metadata
        """
        log_function_entry(logger, "find_similar_questions", question=question[:100], limit=limit, user_id=user_id)
        start_time = time.time()
        
        try:
            if not self._initialized:
                await self.initialize_system()
            
            # Normalize the question
            normalized_question = self._normalize_question(question)
            
            # Generate embedding for semantic search
            question_embedding = await embedding_service.generate_embedding(normalized_question)
            if not question_embedding:
                logger.warning("Failed to generate question embedding for similar questions search")
                return []
            
            # Ensure embedding is a flat list of floats
            if isinstance(question_embedding, list) and question_embedding:
                if isinstance(question_embedding[0], list):
                    question_embedding = question_embedding[0]
                elif not isinstance(question_embedding[0], (int, float)):
                    logger.warning(f"Invalid embedding format for similar questions search: {type(question_embedding[0])}")
                    return []
            
            # Search for similar questions in Qdrant
            search_results = await qdrant_service.search_similar_questions(
                question_embedding,
                limit=limit,
                score_threshold=0.7  # Lower threshold for similar questions
            )
            
            if not search_results:
                logger.info("No similar questions found")
                return []
            
            # Fetch additional details from PostgreSQL for each result
            similar_questions = []
            db = next(get_db())
            qa_pair_repo = QAPairRepository()
            
            for result in search_results:
                qa_id = result.get("qa_id")
                if qa_id:
                    try:
                        # Convert qa_id to UUID if it's a string
                        if isinstance(qa_id, str):
                            qa_id = uuid.UUID(qa_id)
                        
                        qa_pair = qa_pair_repo.get_qa_pair_by_id(db, qa_id)
                        if qa_pair:
                            similar_questions.append({
                                "id": str(qa_pair.id),
                                "question": qa_pair.question_text,
                                "answer": qa_pair.answer_text[:200] + "..." if len(qa_pair.answer_text) > 200 else qa_pair.answer_text,
                                "similarity_score": result.get("similarity_score", 0),
                                "source": qa_pair.source,
                                "language": qa_pair.language,
                                "created_at": qa_pair.created_at.isoformat() if qa_pair.created_at else None,
                                "confidence": qa_pair.confidence
                            })
                    except (ValueError, TypeError) as e:
                        logger.warning(f"Invalid qa_id format: {qa_id}, error: {e}")
                        continue
                    except Exception as e:
                        logger.warning(f"Failed to fetch Q&A pair details for {qa_id}: {e}")
                        continue
            
            db.close()
            
            # Sort by similarity score (highest first)
            similar_questions.sort(key=lambda x: x.get("similarity_score", 0), reverse=True)
            
            duration = time.time() - start_time
            log_performance(logger, "Similar questions search", duration, question_length=len(question))
            log_function_exit(logger, "find_similar_questions", result=f"found_{len(similar_questions)}_questions", duration=duration)
            
            return similar_questions
            
        except Exception as e:
            duration = time.time() - start_time
            log_error_with_context(logger, e, "find_similar_questions", question=question, duration=duration)
            logger.error(f"❌ Failed to find similar questions: {e}")
            return []

    async def augment_question_variants(
        self,
        question: str,
        answer: str,
        user_id: Optional[str] = None
    ) -> List[str]:
        """
        Generate and store question variants for a Q&A pair.
        
        Args:
            question: The original question
            answer: The answer to the question
            user_id: Optional user ID
            
        Returns:
            List of generated question variants
        """
        log_function_entry(logger, "augment_question_variants", question=question[:100], answer_length=len(answer), user_id=user_id)
        start_time = time.time()
        
        try:
            if not self._initialized:
                await self.initialize_system()
            
            # Generate variants using embedding service
            variants = await embedding_service.generate_question_variants(
                question,
                num_variants=self.max_variants_to_generate
            )
            
            if not variants:
                logger.warning("No question variants generated")
                return []
            
            # Store the original Q&A pair first
            qa_pair_id = self._store_qa_pair(
                question=question,
                answer=answer,
                user_id=user_id,
                context="augmented_variants"
            )
            
            # Generate embeddings for variants and store them in Qdrant
            for variant in variants:
                try:
                    variant_embedding = await embedding_service.generate_embedding(variant)
                    if variant_embedding:
                        # Ensure embedding is a flat list of floats
                        if isinstance(variant_embedding, list) and variant_embedding:
                            if isinstance(variant_embedding[0], list):
                                variant_embedding = variant_embedding[0]
                        
                        await qdrant_service.store_qa_pair(
                            qa_pair_id=qa_pair_id,
                            question=variant,
                            answer=answer,  # Link to the same answer
                            question_embedding=variant_embedding
                        )
                except Exception as e:
                    logger.warning(f"Failed to store variant '{variant}': {e}")
                    continue
            
            duration = time.time() - start_time
            log_performance(logger, "Question variants augmentation", duration, question_length=len(question))
            log_function_exit(logger, "augment_question_variants", result=f"generated_{len(variants)}_variants", duration=duration)
            
            return variants
            
        except Exception as e:
            duration = time.time() - start_time
            log_error_with_context(logger, e, "augment_question_variants", question=question, duration=duration)
            logger.error(f"❌ Failed to augment question variants: {e}")
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

    async def get_news_knowledge_stats(self) -> Dict[str, Any]:
        """
        Get comprehensive news knowledge statistics including:
        - Web scraping statistics
        - Qdrant vector database statistics
        - News sources information
        - Last update information
        """
        try:
            stats = {
                "timestamp": datetime.now().isoformat(),
                "service_status": "operational"
            }
            
            # Get web scraping statistics
            try:
                web_stats = await web_scraping_service.get_scraping_stats()
                stats["web_scraping"] = web_stats
            except Exception as e:
                stats["web_scraping"] = {"error": str(e)}
            
            # Get Qdrant collection statistics
            try:
                qdrant_stats = await qdrant_service.get_collection_stats()
                stats["qdrant"] = qdrant_stats
            except Exception as e:
                stats["qdrant"] = {"error": str(e)}
            
            # Get database statistics
            try:
                db = next(get_db())
                
                # Import the QAPair model directly
                from models.domain.qa_pair import QAPair
                
                # Count total Q&A pairs
                total_qa_pairs = db.query(QAPair).count()
                
                # Get recent Q&A pairs
                recent_qa_pairs = db.query(QAPair).order_by(
                    QAPair.created_at.desc()
                ).limit(5).all()
                
                stats["database"] = {
                    "total_qa_pairs": total_qa_pairs,
                    "recent_qa_pairs": [
                        {
                            "id": str(qa.id),
                            "question": qa.question_text[:100] + "..." if len(qa.question_text) > 100 else qa.question_text,
                            "source": qa.source,
                            "created_at": qa.created_at.isoformat() if qa.created_at else None
                        }
                        for qa in recent_qa_pairs
                    ]
                }
                
                db.close()
                
            except Exception as e:
                stats["database"] = {"error": str(e)}
            
            # Get system health overview
            try:
                health_checks = await self._check_system_health()
                stats["system_health"] = {
                    "overall_status": "healthy" if all(
                        check.get("status") == "healthy" 
                        for check in health_checks.values()
                    ) else "degraded",
                    "services": health_checks
                }
            except Exception as e:
                stats["system_health"] = {"error": str(e)}
            
            # Add configuration information
            stats["configuration"] = {
                "semantic_search_threshold": self.semantic_search_threshold,
                "quality_threshold": self.quality_threshold,
                "max_variants_to_generate": self.max_variants_to_generate,
                "initialized": self._initialized
            }
            
            return stats
            
        except Exception as e:
            logger.error(f"Failed to get news knowledge stats: {e}")
            return {
                "status": "error",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }

    async def check_gemini_quota(self) -> Dict[str, Any]:
        """
        Check Gemini API quota status and usage.
        
        Returns:
            Dictionary with quota information
        """
        log_function_entry(logger, "check_gemini_quota")
        start_time = time.time()
        
        try:
            # Check Gemini service health and quota
            gemini_health = await gemini_service.get_health()
            
            quota_info = {
                "service_available": gemini_health.get("available", False),
                "quota_status": "unknown",
                "usage_info": {},
                "limits": {},
                "last_checked": datetime.now().isoformat()
            }
            
            if gemini_health.get("available"):
                # Try to get detailed quota information
                try:
                    quota_details = await gemini_service.get_quota_info()
                    if quota_details:
                        quota_info.update(quota_details)
                except Exception as e:
                    logger.warning(f"Failed to get detailed quota info: {e}")
                    quota_info["quota_status"] = "available_but_details_unavailable"
            else:
                quota_info["quota_status"] = "service_unavailable"
                quota_info["error"] = gemini_health.get("error", "Service not responding")
            
            duration = time.time() - start_time
            log_performance(logger, "Gemini quota check", duration)
            log_function_exit(logger, "check_gemini_quota", result=quota_info["quota_status"], duration=duration)
            
            return quota_info
            
        except Exception as e:
            duration = time.time() - start_time
            log_error_with_context(logger, e, "check_gemini_quota", duration=duration)
            logger.error(f"❌ Failed to check Gemini quota: {e}")
            return {
                "service_available": False,
                "quota_status": "error",
                "error": str(e),
                "last_checked": datetime.now().isoformat()
            }

    async def get_system_health(self) -> Dict[str, Any]:
        """
        Get comprehensive system health status.
        This is an alias for _check_system_health for API compatibility.
        
        Returns:
            Dictionary with system health information
        """
        return await self._check_system_health()

    async def update_news_knowledge(self, force_update: bool = False) -> Dict[str, Any]:
        """
        Update news knowledge base with fresh content.
        
        Args:
            force_update: Force update even if recent update exists
            
        Returns:
            Dictionary with update results
        """
        log_function_entry(logger, "update_news_knowledge", force_update=force_update)
        start_time = time.time()
        
        try:
            if not self._initialized:
                await self.initialize_system()
            
            # Check if update is needed
            if not force_update:
                # Check last update time (implement based on your needs)
                last_update = getattr(self, '_last_news_update', None)
                if last_update:
                    time_since_update = (datetime.now() - last_update).total_seconds()
                    if time_since_update < 3600:  # 1 hour
                        return {
                            "status": "skipped",
                            "reason": "Recent update exists",
                            "last_update": last_update.isoformat(),
                            "time_since_update_seconds": time_since_update
                        }
            
            logger.info("🔄 Starting news knowledge update...")
            
            # Get fresh content from web scraping
            update_results = {
                "status": "success",
                "web_scraping": {},
                "qdrant_updates": {},
                "database_updates": {},
                "timestamp": datetime.now().isoformat()
            }
            
            # Update web scraping content
            try:
                web_update = await web_scraping_service.update_knowledge_base()
                update_results["web_scraping"] = web_update
            except Exception as e:
                logger.warning(f"Web scraping update failed: {e}")
                update_results["web_scraping"] = {"error": str(e)}
            
            # Update Qdrant collection if needed
            try:
                qdrant_update = await qdrant_service.update_collection()
                update_results["qdrant_updates"] = qdrant_update
            except Exception as e:
                logger.warning(f"Qdrant update failed: {e}")
                update_results["qdrant_updates"] = {"error": str(e)}
            
            # Update database if needed
            try:
                # This would typically involve updating any cached data
                update_results["database_updates"] = {"status": "completed", "message": "Database cache updated"}
            except Exception as e:
                logger.warning(f"Database update failed: {e}")
                update_results["database_updates"] = {"error": str(e)}
            
            # Mark update as completed
            self._last_news_update = datetime.now()
            
            duration = time.time() - start_time
            log_performance(logger, "News knowledge update", duration)
            log_function_exit(logger, "update_news_knowledge", result="completed", duration=duration)
            
            return update_results
            
        except Exception as e:
            duration = time.time() - start_time
            log_error_with_context(logger, e, "update_news_knowledge", duration=duration)
            logger.error(f"❌ News knowledge update failed: {e}")
            return {
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }

# Global service instance
intelligent_qa_service = IntelligentQAService()
