import logging
from typing import Dict, List, Optional, Any
import time
import uuid
import re
from datetime import datetime

# الخدمات
from .qdrant_service import qdrant_service
from .embedding_service import embedding_service
from .gemini_service import gemini_service
from services.repositories.qa_pair_repository import QAPairRepository
from services.database.database import get_db
from config.logging_config import get_logger, log_function_entry, log_function_exit, log_performance

logger = get_logger(__name__)

class IntelligentQAService:
    """
    خدمة Q&A:
    - البحث الدلالي المتقدم
    - توليد نسخ الأسئلة باستخدام Gemini
    - الإجابة عن الأسئلة غير الموجودة باستخدام Gemini
    - تخزين الأسئلة والأجوبة
    """

    def __init__(self):
        log_function_entry(logger, "__init__")
        start_time = time.time()
        self.semantic_search_threshold: float = 0.85
        self.max_variants_to_generate: int = 5
        self._initialized: bool = True
        log_function_exit(logger, "__init__", duration=time.time() - start_time)

    async def process_question(
        self,
        question: str,
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """البحث عن السؤال والإجابة أو توليد الإجابة الجديدة إذا لم توجد"""


        # البحث الدلالي
        question_embedding = await embedding_service.generate_embedding(question)
        if not question_embedding:
            logger.error(f"Failed to generate embedding for question: {question}")
            return {"status": "error", "error": "فشل في توليد embedding للسؤال"}
            
        search_results = await qdrant_service.search_similar_questions(
            question_embedding,
            limit=5,    
            score_threshold=self.semantic_search_threshold
        )

        # إذا وجدنا جواب عالي الجودة
        if search_results and search_results[0].get("similarity_score", 0) >= 0.95:
            best_match = search_results[0]
            answer_id = best_match.get("qa_id")
            db = next(get_db())
            qa_pair_repo = QAPairRepository()
            try:
                if isinstance(answer_id, str):
                    answer_id = uuid.UUID(answer_id)
                qa_pair = qa_pair_repo.get_qa_pair_by_id(db, answer_id)
                db.close()
                if qa_pair:
                    return {
                        "status": "success",
                        "answer": qa_pair.answer_text,
                        "source": "cached",
                        "confidence": best_match.get("similarity_score", 0)
                    }
            except Exception as e:
                logger.warning(f"فشل جلب الإجابة المخزنة: {e}")

        # الإجابة باستخدام Gemini
        answer_result = await gemini_service.answer_question(question)
        if not answer_result or not answer_result.get("answer"):
            return {"status": "error", "error": "فشل توليد الإجابة باستخدام Gemini"}

        answer_text = answer_result["answer"]

        # تخزين السؤال والجواب
        qa_pair_id = await self.store_qa_pair(question=question, answer=answer_text, user_id=user_id)

        return {
            "status": "success",
            "answer": answer_text,
            "source": "gemini_generated",
            "qa_pair_id": qa_pair_id
        }

    async def store_qa_pair(
        self,
        question: str,
        answer: str,
        user_id: Optional[str] = None
    ) -> str:
        """تخزين السؤال والجواب وتوليد نسخ الأسئلة باستخدام Gemini"""
        db = next(get_db())
        qa_repo = QAPairRepository()

        user_uuid = None
        if user_id:
            try:
                user_uuid = uuid.UUID(user_id)
            except Exception:
                pass

        # تخزين في PostgreSQL
        qa_pair = qa_repo.create_qa_pair(
            db=db,
            question_text=question,
            answer_text=answer,
            user_id=user_uuid,
            source="intelligent_qa_service",
            metadata={"created_at": datetime.now().isoformat()}
        )

        # توليد embedding للسؤال الأصلي
        question_embedding = await embedding_service.generate_embedding(question)
        
        # التحقق من صحة الـ embedding
        if not question_embedding:
            logger.error(f"Failed to generate embedding for question: {question}")
            db.close()
            return str(qa_pair.id)

        # تخزين السؤال الأصلي في Qdrant
        store_success = await qdrant_service.store_qa_embedding(
            qa_id=str(qa_pair.id),
            question=question,
            embedding=question_embedding,
            metadata={"answer": answer}
        )
        
        if not store_success:
            logger.warning(f"Failed to store original question embedding for qa_id: {qa_pair.id}")

        # توليد نسخ الأسئلة باستخدام Gemini
        try:
            variants = await gemini_service.generate_question_variants(question, num_variants=self.max_variants_to_generate)
            
            for variant in variants:
                if variant and variant != question:  # تجنب النسخ المكررة
                    variant_embedding = await embedding_service.generate_embedding(variant)
                    
                    if variant_embedding:
                        await qdrant_service.store_qa_embedding(
                            qa_id=str(qa_pair.id),
                            question=variant,
                            embedding=variant_embedding,
                            metadata={"answer": answer, "is_variant": True}  # مرتبط بالجواب الأصلي
                        )
                    else:
                        logger.warning(f"Failed to generate embedding for variant: {variant}")
                        
        except Exception as e:
            logger.error(f"Failed to process question variants: {e}")

        db.close()
        return str(qa_pair.id)

    async def search_similar_questions(
        self,
        question: str,
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """البحث الدلالي عن الأسئلة المشابهة في Qdrant"""
        try:
            question_embedding = await embedding_service.generate_embedding(question)
            
            if not question_embedding:
                logger.error(f"Failed to generate embedding for search question: {question}")
                return []
                
            results = await qdrant_service.search_similar_questions(
                question_embedding,
                limit=limit,
                score_threshold=self.semantic_search_threshold
            )
            return results
        except Exception as e:
            logger.error(f"Failed to search similar questions: {e}")
            return []

    async def initialize_system(self) -> Dict[str, Any]:
        """Initialize the intelligent QA system"""
        try:
            log_function_entry(logger, "initialize_system")
            start_time = time.time()
            
            # Check if services are available
            if not embedding_service.is_available():
                return {"status": "error", "error": "Embedding service not available"}
            
            if not gemini_service.is_available():
                return {"status": "error", "error": "Gemini service not available"}
            
            # Check Qdrant connection
            if not qdrant_service.is_connected():
                return {"status": "error", "error": "Qdrant service not connected"}
            
            # Ensure Qdrant collection exists
            await qdrant_service._ensure_collection_exists()
            
            duration = time.time() - start_time
            log_function_exit(logger, "initialize_system", duration=duration)
            
            return {"status": "success", "message": "Intelligent QA system initialized successfully"}
            
        except Exception as e:
            log_function_exit(logger, "initialize_system", duration=time.time() - start_time)
            logger.error(f"Failed to initialize intelligent QA system: {e}")
            return {"status": "error", "error": str(e)}

# نسخة الخدمة جاهزة للاستخدام
intelligent_qa_service = IntelligentQAService()
