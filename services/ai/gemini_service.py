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

    async def answer_question(self, question: str) -> Optional[Dict[str, Any]]:
        """Generate an answer for a given question"""
        if not self.model_available:
            return {"answer": f"[MOCK ANSWER] {question}", "model_used": "mock"}

        prompt = f"""أجب على السؤال التالي بما يتوافق مع المجتمع السوري:
            لا تعد اي شيئ مثل (بالطبع اليك جواب يتوافق مع الشعب السوري) 
            السؤال:
            {question}"""

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
            return {"answer": answer, "model_used": self.model_name}
        except Exception as e:
            logger.error(f"Failed to get answer from Gemini: {e}")
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