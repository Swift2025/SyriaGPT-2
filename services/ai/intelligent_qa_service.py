import logging
from typing import Dict, List, Optional, Any
import time
import uuid
from datetime import datetime

# الخدمات
from .qdrant_service import qdrant_service
from .embedding_service import embedding_service
from .gemini_service import gemini_service
from services.database.database import get_db
from config.logging_config import get_logger
from services.repositories.qa_pair_repository import QAPairRepository

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
        start_time = time.time()
        self.semantic_search_threshold: float = 0.6   # عتبة متوازنة للبحث
        self.high_confidence_threshold: float = 0.8   # عتبة عالية للثقة
        self.medium_confidence_threshold: float = 0.5  # عتبة متوسطة
        self.low_confidence_threshold: float = 0.3     # عتبة منخفضة
        self.max_variants_to_generate: int = 3         # تقليل عدد المتغيرات
        self._initialized: bool = True

    async def process_question(
        self,
        question: str,
        user_id: Optional[str] = None,
        context: Optional[str] = None,
        language: str = "auto",
        model_preference: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """معالجة السؤال بالترتيب الصحيح: هوية -> سوريا -> عام"""
        
        start_time = time.time()

        try:
            # 3. البحث الدلالي في Qdrant
            search_results = await self.search_similar_questions(question)
            if search_results:
                best_match = search_results[0]
                similarity_score = best_match.get("similarity_score", 0)

                if similarity_score >= 0.85:
                    logger.info(f"✅ [INTELLIGENT_QA] تم العثور على إجابة موجودة في Qdrant")
                    answer_id = best_match.get("qa_id")

                    db = next(get_db())
                    try:
                        # تحويل answer_id إلى UUID إذا كان نصيًا
                        if isinstance(answer_id, str):
                            try:
                                answer_id = uuid.UUID(answer_id)
                            except ValueError:
                                logger.warning(f"معرف الإجابة غير صالح: {answer_id}")
                                return {"status": "error", "error": "Invalid QA ID format"}

                        qa_pair_repo = QAPairRepository()
                        qa_pair = qa_pair_repo.get_qa_pair_by_id(db, answer_id)

                        if qa_pair:
                            return {
                                "status": "success",
                                "answer": qa_pair.answer_text,
                                "source": "cached",
                                "confidence": similarity_score
                            }
                        else:
                            logger.warning(f"لم يتم العثور على QA pair للمعرف: {answer_id}")
                            return {"status": "not_found", "message": "QA pair not found"}

                    except Exception as e:
                        logger.warning(f"فشل جلب الإجابة المخزنة: {e}")
                        return {"status": "error", "error": str(e)}

                    finally:
                        db.close()

            else:
                logger.info(f"❌ [INTELLIGENT_QA] لم يتم العثور على إجابة موجودة في Qdrant، المتابعة لـ Gemini")

            # 4. الإجابة باستخدام Gemini للأسئلة العامة
            logger.info(f"🔍 [INTELLIGENT_QA] استخدام Gemini للأسئلة العامة...")
            answer_result = await gemini_service.generate_response(
                question=question,
                context=context,
                language=language,
                model_preference=model_preference,
                max_tokens=max_tokens,
                temperature=temperature
            )
            if not answer_result or not answer_result.get("answer"):
                return {"status": "error", "error": "فشل توليد الإجابة باستخدام Gemini"}

            answer_text = answer_result["answer"]

            # تخزين السؤال والجواب
            qa_pair_id = await self.store_qa_pair(question=question, answer=answer_text, user_id=user_id)

            return {
                "status": "success",
                "answer": answer_text,
                "source": "gemini_general",
                "qa_pair_id": qa_pair_id
            }

        except Exception as e:
            duration = time.time() - start_time
            logger.error(f"Error in process_question: {e}")
            return {"status": "error", "error": str(e)}



            
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

# نسخة الخدمة جاهزة للاستخدام
intelligent_qa_service = IntelligentQAService()
