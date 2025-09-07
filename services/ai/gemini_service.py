import os
import logging
from typing import Optional, Dict, Any, List
import asyncio
import google.generativeai as genai
import ast
from config.logging_config import get_logger

logger = get_logger(__name__)

class GeminiService:
    """
    Service for Google Gemini API integration.
    Handles intelligent question answering and question variants generation.
    """
    def __init__(self):
        self.api_key = os.getenv("GOOGLE_API_KEY")
        self.model_name = "gemini-2.5-flash"
        self.max_tokens = 2000

        if not self.api_key:
            logger.warning("GOOGLE_API_KEY not found - using mock mode")
            self.model_available = False
        else:
            genai.configure(api_key=self.api_key)
            self.model_available = True
            logger.info(f"GeminiService initialized with model: {self.model_name}")

    def is_connected(self) -> bool:
        return self.model_available

    def is_available(self) -> bool:
        """Check if the Gemini service is available"""
        return self.model_available

    async def test_connection(self) -> bool:
        """Test the connection to Google Gemini API"""
        try:
            logger.info("🔍 Testing Google Gemini API connection...")
            
            if not self.model_available:
                logger.error("❌ Google Gemini API not available - no API key")
                return False
            
            # Test with a simple question
            test_result = await self.answer_question("What is 2+2?")
            
            if test_result and test_result.get("answer"):
                logger.info("✅ Google Gemini API connection test successful")
                return True
            else:
                logger.error("❌ Google Gemini API connection test failed")
                return False
                
        except Exception as e:
            logger.error(f"❌ Google Gemini API connection test failed: {e}")
            return False

    async def answer_question(self, question: str, context: Optional[str] = None, language: str = "auto", **kwargs) -> Optional[Dict[str, Any]]:
        """Generate an answer for a given question"""
        logger.info(f"🔍 [GEMINI_SERVICE] معالجة السؤال: {question[:50]}...")
        if not self.model_available:
            logger.warning("❌ [GEMINI_SERVICE] النموذج غير متاح، إرجاع رد وهمي")
            return {"answer": f"[MOCK ANSWER] {question}", "model_used": "mock"}

        # بناء السياق من البيانات المحلية إذا لم يتم توفيره
        if not context:
            context = """
            أنت مساعد ذكي متخصص في المعلومات السورية. استخدم المعلومات التالية كمرجع:
            
            - سوريا جمهورية ديمقراطية حديثة
            - العاصمة: دمشق
            - اللغة الرسمية: العربية
            - العملة: الليرة السورية
            - عدد المحافظات: 14 محافظة
            - النظام السياسي: جمهوري ديمقراطي
            - الدستور: دستور الجمهورية العربية السورية (2012)
            - البرلمان: مجلس الشعب (250 عضو)
            - الرئيس الحالي: أحمد الشرع (بعد تحرير سوريا)
            - الحزب الحاكم: منتخب ديمقراطياً
            """

        prompt = f"""أنت SyriaGPT، مساعد ذكي متخصص في المعلومات السورية تم تدريبه من قبل وكالة نظم المعلومات السورية. أجب على السؤال التالي بدقة ووضوح:

معلومات مهمة:
- إذا سُئلت عن هويتك، قل أنك SyriaGPT من وكالة نظم المعلومات السورية
- الرئيس الحالي لسوريا هو أحمد الشرع (بعد تحرير سوريا من نظام الأسد)
- سوريا جمهورية ديمقراطية حديثة
- النظام السياسي مبني على دستور الجمهورية العربية السورية

السياق المرجعي:
{context}

السؤال: {question}

تعليمات مهمة:
- أجب باللغة العربية فقط
- كن دقيقاً ومحدداً في المعلومات
- إذا لم تكن متأكداً من معلومة، قل "لا أستطيع التأكد من هذه المعلومة"
- لا تخترع معلومات غير موجودة أو غير مؤكدة
- ركز على المعلومات الرسمية والموثقة
- اجعل إجابتك مختصرة ومفيدة
- تجنب التكرار والتفاصيل غير الضرورية
- إذا سُئلت عن هويتك، قل أنك SyriaGPT من وكالة نظم المعلومات السورية"""

        try:
            # إنشاء نموذج GenerativeModel
            model = genai.GenerativeModel(self.model_name)
            
            # توليد المحتوى
            response = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: model.generate_content(prompt)
            )
            
            # الوصول للنص الناتج
            answer = response.text
            
            # التحقق من جودة الإجابة
            if not answer or len(answer.strip()) < 5:
                logger.warning("Received empty or very short answer from Gemini")
                return {"answer": "عذراً، لم أتمكن من توليد إجابة مناسبة. يرجى إعادة صياغة السؤال.", "model_used": self.model_name}
            
            # تنظيف الإجابة من النصوص غير المرغوب فيها
            answer = answer.strip()
            if answer.startswith("أعتذر") and len(answer) < 20:
                logger.warning("Received apology response from Gemini")
                return {"answer": "عذراً، لا أستطيع الإجابة على هذا السؤال بدقة. يرجى طرح سؤال أكثر تحديداً.", "model_used": self.model_name}
            
            logger.info(f"✅ [GEMINI_SERVICE] تم توليد إجابة بنجاح من Gemini")
            return {
                "answer": answer, 
                "model_used": self.model_name,
                "source": "gemini_service",
                "debug_info": {
                    "model_name": self.model_name,
                    "answer_length": len(answer),
                    "question_length": len(question)
                }
            }
        except Exception as e:
            logger.error(f"❌ [GEMINI_SERVICE] فشل في الحصول على إجابة من Gemini: {e}")
            return None

    async def generate_question_variants(
        self, original_question: str, num_variants: int = 5
    ) -> List[str]:
        """Generate variants of a question"""
        if not self.model_available:
            return [original_question]

        # تنظيف النص من الأحرف الخاصة
        cleaned_question = original_question.strip()
        if not cleaned_question:
            logger.warning("Empty question provided for variant generation")
            return [original_question]

        prompt = f"""أنشئ 5 أسئلة مشابهة و تملك معنى السؤال الأصلي و بما يتوافق مع المجتمع السوري:
                    أعد النتيجة بتنسيق list من  5 عناصر هكذا:
                    [ , , , , ]
                    لا تعد اي شيئ مثل (إليك 5 أسئلة مشابهة تتناسب مع السياق السوري:) مباشرة اعط القائمة
                    السؤال الأصلي:
                    {cleaned_question}"""
        
        try:
            # إنشاء نموذج GenerativeModel
            model = genai.GenerativeModel(self.model_name)
            
            # توليد المحتوى
            response = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: model.generate_content(prompt)
            )
            
            if not response or not response.text:
                logger.warning("Empty response from Gemini for question variants")
                return [original_question]
            
            text = response.text.strip()
            
            # تنظيف النص من الأحرف الخاصة
            text = text.replace('؟', '?').replace('،', ',').replace('؛', ';')
            
            # محاولة تحويل النص إلى قائمة بأمان
            try:
                if text.startswith("[") and text.endswith("]"):
                    # إزالة الأقواس والمسافات الزائدة
                    content = text[1:-1].strip()
                    if content:
                        # تقسيم حسب الفواصل
                        variants = [v.strip().strip('"\'') for v in content.split(",")]
                        # تصفية العناصر الفارغة
                        variants = [v for v in variants if v and len(v) > 3]
                        if variants:
                            return variants[:num_variants]
                
                # إذا فشل التحليل، إرجاع السؤال الأصلي
                logger.warning(f"Failed to parse variants from response: {text}")
                return [original_question]
                
            except Exception as parse_error:
                logger.error(f"Failed to parse question variants: {parse_error}")
                return [original_question]
                
        except Exception as e:
            logger.error(f"Failed to generate question variants: {e}")
            return [original_question]

    async def check_content_safety(self, text: str) -> Dict[str, Any]:
        """Mock content safety check"""
        return {"is_safe": True, "safety_ratings": []}

# Global instance
gemini_service = GeminiService()