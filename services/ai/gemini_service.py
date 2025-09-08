"""
Google Gemini AI service for SyriaGPT.
Handles AI model interactions and response generation.
"""
import os
import asyncio
import ast
import logging
from typing import Optional, Dict, Any, List
import google.generativeai as genai
from config.config_loader import ConfigLoader

logger = logging.getLogger(__name__)


class GeminiService:
    """Google Gemini AI service for handling AI interactions."""
    
    def __init__(self, config: ConfigLoader):
        """Initialize Gemini service."""
        self.config = config
        self.ai_config = config.get_ai_config()
        self.model = None
        self.model_name = None
        self.initialized = False
    
    async def initialize(self):
        """Initialize the Gemini service."""
        try:
            api_key = self.ai_config.get("gemini_api_key") or self.ai_config.get("google_api_key")
            if not api_key:
                logger.warning("Gemini API key not configured")
                return
            
            genai.configure(api_key=api_key)
            
            # Initialize model
            self.model_name = self.ai_config.get("model_name", "gemini-pro")
            self.model = genai.GenerativeModel(self.model_name)
            
            self.initialized = True
            logger.info(f"Gemini service initialized with model: {self.model_name}")
            
        except Exception as e:
            logger.error(f"Gemini service initialization error: {e}")
            self.initialized = False
    
    async def generate_response(self, question: str) -> Dict[str, Any]:
        """Generate AI response using Gemini."""
        try:
            if not self.initialized:
                raise RuntimeError("Gemini service not initialized")
            
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

                    السؤال: {question}

                    تعليمات مهمة:
                    - أجب باللغة العربية فقط
                    - إذا لم تكن متأكداً من معلومة، قل "لا أستطيع التأكد من هذه المعلومة"
                    - لا تخترع معلومات غير موجودة أو غير مؤكدة
                    - ركز على المعلومات الرسمية والموثقة
                    - اجعل إجابتك مختصرة ومفيدة
                    - إذا سُئلت عن هويتك، قل أنك SyriaGPT من وكالة نظم المعلومات السورية"""
            
            generation_config = genai.types.GenerationConfig(
                max_output_tokens=self.ai_config.get("max_tokens", 2048),
                temperature=float(self.ai_config.get("temperature", "0.7")),
                top_p=float(self.ai_config.get("top_p", "0.8")),
                top_k=int(self.ai_config.get("top_k", "40"))
            )
            
            response = await self._generate_async(prompt, generation_config)
            
            # استخراج النص
            text = getattr(response, "text", None)
            if not text and hasattr(response, "candidates"):
                text = response.candidates[0].content.parts[0].text
            
            return {
                "response": text or "",
                "model_used": self.model_name,
                "tokens_used": getattr(response, "usage_metadata", {}).get("total_token_count", 0)
            }
            
        except Exception as e:
            logger.error(f"Gemini response generation error: {e}")
            raise
    
    async def generate_question_variants(self, question: str, num_variants: int = 3) -> List[str]:
        """Generate variants of a question."""
        try:
            if not self.initialized:
                raise RuntimeError("Gemini service not initialized")
            
            prompt = f"""أنشئ {num_variants} أسئلة مشابهة وتملك معنى السؤال الأصلي وبما يتوافق مع المجتمع السوري:
                    أعد النتيجة بتنسيق list من {num_variants} عناصر هكذا:
                    ["سؤال1", "سؤال2", "سؤال3"]
                    لا تعد أي شيء آخر.
                    السؤال الأصلي:
                    {question}"""
            
            response = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self.model.generate_content(prompt)
            )
            
            text = getattr(response, "text", None)
            if not text and hasattr(response, "candidates"):
                text = response.candidates[0].content.parts[0].text
            
            if not text:
                logger.warning("Empty response from Gemini for question variants")
                return [question]
            
            text = text.strip()
            
            try:
                variants = ast.literal_eval(text)
                if isinstance(variants, list):
                    variants = [str(v).strip() for v in variants if isinstance(v, str) and len(v.strip()) > 3]
                    if variants:
                        return variants[:num_variants]
            except Exception as e:
                logger.warning(f"فشل تحويل النص إلى قائمة باستخدام ast: {e}")
                return [question]

        except Exception as e:
            logger.error(f"Question variant generation error: {e}")
            return [question]
    
    async def _generate_async(self, prompt: str, generation_config: Optional[genai.types.GenerationConfig] = None) -> Any:
        """Generate response asynchronously."""
        def _generate_sync():
            return self.model.generate_content(
                prompt,
                generation_config=generation_config
            )
        
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, _generate_sync)
    
    def is_available(self) -> bool:
        """Check if Gemini service is available."""
        return self.initialized and self.model is not None
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get model information."""
        return {
            "model_name": self.model_name,
            "initialized": self.initialized,
            "config": self.ai_config
        }


# Initialize with config
config = ConfigLoader()
gemini_service = GeminiService(config)