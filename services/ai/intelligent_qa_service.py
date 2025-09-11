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
from .identity_service import identity_service
from services.repositories.qa_pair_repository import QAPairRepository
from services.database.database import get_db
from config.logging_config import get_logger, log_function_entry, log_function_exit, log_performance, log_error_with_context

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
        self.semantic_search_threshold: float = 0.6   # عتبة متوازنة للبحث
        self.high_confidence_threshold: float = 0.8   # عتبة عالية للثقة
        self.medium_confidence_threshold: float = 0.5  # عتبة متوسطة
        self.low_confidence_threshold: float = 0.3     # عتبة منخفضة
        self.max_variants_to_generate: int = 3         # تقليل عدد المتغيرات
        self._initialized: bool = True
        log_function_exit(logger, "__init__", duration=time.time() - start_time)

    async def process_question(
        self,
        question: str,
        user_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """معالجة السؤال بالترتيب الصحيح: هوية -> سوريا -> عام"""
        
        log_function_entry(logger, "process_question", question_length=len(question), user_id=user_id)
        start_time = time.time()

        try:
            # 1. التحقق من أسئلة الهوية أولاً
            logger.info(f"🔍 [INTELLIGENT_QA] فحص سؤال الهوية: {question[:50]}...")
            identity_response = identity_service.get_identity_response(question)
            if identity_response:
                logger.info(f"✅ [INTELLIGENT_QA] تم اكتشاف سؤال هوية وإرجاع رد من خدمة الهوية")
                log_function_exit(logger, "process_question", duration=time.time() - start_time)
                return identity_response
            else:
                logger.info(f"❌ [INTELLIGENT_QA] لم يتم اكتشاف سؤال هوية، المتابعة للبحث في بيانات سوريا")

            # 2. البحث في بيانات سوريا المحلية
            logger.info(f"🔍 [INTELLIGENT_QA] البحث في بيانات سوريا المحلية...")
            syria_response = await self._search_local_data_directly(question)
            if syria_response and syria_response.get("status") == "success":
                logger.info(f"✅ [INTELLIGENT_QA] تم العثور على إجابة من بيانات سوريا المحلية")
                log_function_exit(logger, "process_question", duration=time.time() - start_time)
                return syria_response
            else:
                logger.info(f"❌ [INTELLIGENT_QA] لم يتم العثور على إجابة في بيانات سوريا، المتابعة لـ Gemini")
            
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
            answer_result = await gemini_service.answer_question(
                question=question
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
            log_error_with_context(logger, e, "process_question", duration=duration)
            logger.error(f"Error in process_question: {e}")
            log_function_exit(logger, "process_question", duration=duration)
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
        limit: int = 3
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

            # Load Syria knowledge data into Qdrant
            logger.info("🔄 Loading Syria knowledge data...")
            from services.ai.data_integration_service import data_integration_service
            data_result = await data_integration_service.initialize_knowledge_base()

            if data_result.get("status") == "success":
                logger.info("✅ Syria knowledge data loaded successfully")
            else:
                logger.warning(f"⚠️ Failed to load Syria knowledge data: {data_result.get('error', 'Unknown error')}")

            duration = time.time() - start_time
            log_function_exit(logger, "initialize_system", duration=duration)

            return {
                "status": "success",
                "message": "Intelligent QA system initialized successfully",
                "data_loading": data_result
            }

        except Exception as e:
            log_function_exit(logger, "initialize_system", duration=time.time() - start_time)
            logger.error(f"Failed to initialize intelligent QA system: {e}")
            return {"status": "error", "error": str(e)}


    async def _search_local_data_directly(self, question: str) -> Dict[str, Any]:
        """البحث المباشر في البيانات المحلية بدون استخدام embedding"""
        try:
            import json
            from pathlib import Path
            
            # مسار البيانات - استخدام مسار مرن
            base_path = Path(__file__).parent.parent.parent
            data_path = base_path / "frontend_folder" / "public" / "data" / "syria_knowledge"
            
            # إذا لم يوجد المسار، جرب المسار البديل
            if not data_path.exists():
                data_path = base_path / "data" / "syria_knowledge"
            knowledge_files = [
                "general.json",
                "cities.json", 
                "culture.json",
                "economy.json",
                "government.json",
                "Real_post_liberation_events.json",
                "modern_syria.json"
            ]
            
            # البحث في الملفات مع إعطاء أولوية للملفات الحديثة
            priority_files = ["modern_syria.json", "government.json", "general.json"]
            all_files = priority_files + [f for f in knowledge_files if f not in priority_files]
            
            best_match = None
            best_score = 0
            
            for filename in all_files:
                file_path = data_path / filename
                if file_path.exists():
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                    except (json.JSONDecodeError, IOError) as e:
                        logger.warning(f"خطأ في قراءة الملف {filename}: {e}")
                        continue
                    
                    qa_pairs = data.get("qa_pairs", [])
                    for qa_pair in qa_pairs:
                        # البحث في الأسئلة والإجابات
                        question_variants = qa_pair.get("question_variants", [])
                        answer = qa_pair.get("answer", "")
                        keywords = qa_pair.get("keywords", [])
                        
                        # البحث البسيط في النص
                        search_text = f"{' '.join(question_variants)} {answer} {' '.join(keywords)}".lower()
                        question_lower = question.lower()
                        
                        # البحث عن كلمات مفتاحية
                        question_words = question_lower.split()
                        matches = 0
                        for word in question_words:
                            if word in search_text:
                                matches += 1
                        
                        # حساب النقاط مع إعطاء أولوية للملفات الحديثة
                        score = matches / len(question_words) if question_words else 0
                        if filename in priority_files:
                            score *= 1.5  # زيادة النقاط للملفات المهمة
                        
                        # إذا كان هناك تطابق جيد
                        if score >= 0.3 and score > best_score:  # 30% من الكلمات (تقليل العتبة)
                            best_match = {
                                "answer": answer,
                                "filename": filename,
                                "qa_id": qa_pair.get('id', 'unknown'),
                                "score": score,
                                "category": data.get("category", "syria")
                            }
                            best_score = score
            
            if best_match and best_score >= 0.3:  # تأكد من وجود تطابق مقبول
                logger.info(f"✅ [SYRIA_DATA] Found best match in {best_match['filename']}: {best_match['qa_id']} (score: {best_score:.2f})")
                return {
                    "status": "success",
                    "answer": best_match["answer"],
                    "source": "syria_data_local",
                    "confidence": best_match["score"],
                    "category": best_match["category"]
                }
            
            # إذا لم نجد تطابق، ارجع فشل للبحث في Gemini
            logger.info("❌ [SYRIA_DATA] No match found in local Syria data")
            return {"status": "not_found", "message": "No Syria data found"}
            
        except Exception as e:
            logger.error(f"Error in direct search: {e}")
            return {"status": "error", "error": str(e)}
    
    async def _fallback_to_gemini(self, question: str) -> Dict[str, Any]:
        """الرجوع إلى Gemini AI"""
        answer_result = await gemini_service.answer_question(question=question)
        if not answer_result or not answer_result.get("answer"):
            return {"status": "error", "error": "فشل توليد الإجابة باستخدام Gemini"}

        answer_text = answer_result["answer"]
        return {
            "status": "success",
            "answer": answer_text,
            "source": "gemini_generated",
            "confidence": 0.5
        }

# نسخة الخدمة جاهزة للاستخدام
intelligent_qa_service = IntelligentQAService()
