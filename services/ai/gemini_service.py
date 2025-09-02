import os
import logging
from typing import Optional, Dict, Any, List
import asyncio
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold
import json
from config.logging_config import get_logger
import time
import ast
<<<<<<< HEAD
from datetime import datetime
import re
=======
>>>>>>> 72b87816b64a29691b388b79eb40ec26d86dc91c

logger = get_logger(__name__)

class GeminiService:
    """
    Service for Google Gemini API integration using the latest GenAI library.
    Handles intelligent question answering with context and quality evaluation.
    """
    
    def __init__(self):
<<<<<<< HEAD
        self.api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
        self.model_name = "gemini-1.5-flash"  # Fast model for Q&A
        self.pro_model_name = "gemini-1.5-pro"  # More capable model for complex queries
=======
        self.api_key = os.getenv("GOOGLE_API_KEY")
        self.model_name = "gemini-2.5-flash"  # Fast model for Q&A
        self.pro_model_name = "gemini-2.5-pro"  # More capable model for complex queries
>>>>>>> 72b87816b64a29691b388b79eb40ec26d86dc91c
        self.client = None
        self.model = None
        self.pro_model = None
        self.max_tokens = 2000
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize Gemini client with latest GenAI library"""
        if not self.api_key:
<<<<<<< HEAD
            logger.warning("GOOGLE_API_KEY or GEMINI_API_KEY not found - Gemini service will be unavailable")
            self.client = None
=======
            logger.warning("GOOGLE_API_KEY not found - using mock mode")
>>>>>>> 72b87816b64a29691b388b79eb40ec26d86dc91c
            self.model = None
            self.pro_model = None
            return
        
        try:
            genai.configure(api_key=self.api_key)
            
            # Configure safety settings for more permissive responses
            safety_settings = {
                HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
                HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
                HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
                HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
            }
            
            # Initialize the models
            self.model = genai.GenerativeModel(
                model_name=self.model_name,
                safety_settings=safety_settings
            )
            
            self.pro_model = genai.GenerativeModel(
                model_name=self.pro_model_name,
                safety_settings=safety_settings
            )
            
            logger.info(f"Gemini client initialized successfully with models: {self.model_name}, {self.pro_model_name}")
        except Exception as e:
            logger.error(f"Failed to initialize Gemini client: {e}")
            raise RuntimeError(f"Failed to initialize Gemini client: {e}")
    
    def is_connected(self) -> bool:
        """Check if Gemini client is available and can connect"""
        if not self.api_key or not self.model:
            return False
        
        try:
            # For now, just check if the model is initialized
            # The actual connection test will be done when needed
            return self.model is not None
        except Exception as e:
            logger.warning(f"Gemini connection check failed: {e}")
            return False
    
    async def answer_question(
        self,
        question: str,
<<<<<<< HEAD
        context: Optional[str] = None,
        language: str = "auto",
        previous_qa_pairs: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        Answer a question using Gemini API with context and previous Q&A pairs.
        
        Args:
            question: The user's question
            context: Additional context (e.g., from web scraping)
            language: Preferred response language
            previous_qa_pairs: Previous Q&A pairs for context
            
        Returns:
            Dictionary with answer and metadata
        """
        log_function_entry(logger, "answer_question", question_length=len(question), has_context=bool(context))
        start_time = time.time()
        
        try:
            if not self.api_key or not self.model:
                raise RuntimeError("Gemini API key not configured or model not initialized")
            
            # Build the prompt
            prompt_parts = []
            
            # System instruction
            system_instruction = """أنت مساعد ذكي متخصص في الإجابة على الأسئلة المتعلقة بسوريا. 
            يجب أن تكون إجاباتك دقيقة ومحدثة ومفيدة. استخدم المعلومات المتاحة في السياق المقدم.
            إذا لم تكن متأكداً من إجابة، اعترف بذلك وقدم أفضل ما يمكنك من معلومات."""
            
            prompt_parts.append(system_instruction)
            
            # Add context if provided
            if context:
                prompt_parts.append(f"معلومات خلفية:\n{context}")
            
            # Add previous Q&A pairs for context
            if previous_qa_pairs:
                prompt_parts.append("أسئلة وأجوبة سابقة للسياق:")
                for i, qa in enumerate(previous_qa_pairs[:3]):  # Limit to 3 previous Q&A
                    prompt_parts.append(f"س: {qa.get('question', '')}")
                    prompt_parts.append(f"ج: {qa.get('answer', '')}")
                prompt_parts.append("")
            
            # Add the current question
            prompt_parts.append(f"السؤال: {question}")
            prompt_parts.append("الإجابة:")
            
            full_prompt = "\n".join(prompt_parts)
            
            # Generate response
            response = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self.model.generate_content(full_prompt)
            )
            
            if not response or not response.text:
                raise RuntimeError("Empty response from Gemini")
            
            answer = response.text.strip()
            
            # Calculate confidence based on response length and content
            confidence = self._calculate_confidence(answer, question)
            
            # Extract keywords
            keywords = self._extract_keywords(answer)
            
            # Determine language
            detected_language = self._detect_language(answer) if language == "auto" else language
            
            result = {
                "answer": answer,
                "confidence": confidence,
                "language": detected_language,
                "keywords": keywords,
                "model_used": self.model_name,
                "processing_time": time.time() - start_time,
                "sources": [],  # Will be populated if we have web scraping data
                "created_at": datetime.now().isoformat()
            }
            
            duration = time.time() - start_time
            log_performance(logger, "Gemini question answering", duration, question_length=len(question))
            log_function_exit(logger, "answer_question", result={"answer_length": len(answer)}, duration=duration)
            
            return result
            
        except Exception as e:
            duration = time.time() - start_time
            log_error_with_context(logger, e, "answer_question", question=question, duration=duration)
            logger.error(f"Failed to get answer from Gemini: {e}")
            log_function_exit(logger, "answer_question", duration=duration)
            raise RuntimeError(f"Failed to get answer from Gemini: {e}")
=======
    ) -> Optional[Dict[str, Any]]:
        
        try:
            prompt = f"أجب على السؤال التالي بما يتوافق مع المجتمع السوري: {question}"
            answer = self.model.generate_answer(prompt)
            return {
                "answer": answer,
                "model_used": self.model_name
            }
            
        except Exception as e:
            logger.error(f"Failed to get answer from Gemini: {e}")
            return None
    
>>>>>>> 72b87816b64a29691b388b79eb40ec26d86dc91c
    
    async def generate_question_variants(
        self,
        original_question: str,
        num_variants: int = 5
    ) -> List[str]:
<<<<<<< HEAD
        """
        Generate question variants using Gemini.
        
        Args:
            original_question: The original question
            num_variants: Number of variants to generate
            
        Returns:
            List of question variants
        """
        try:
            if not self.model:
                raise RuntimeError("Gemini model not available")
            
            prompt = f"""أنشئ {num_variants} أسئلة مشابهة وتملك معنى السؤال الأصلي وبما يتوافق مع المجتمع السوري.
            أعد النتيجة بتنسيق list من {num_variants} عناصر هكذا:
            ["سؤال 1", "سؤال 2", "سؤال 3", "سؤال 4", "سؤال 5"]
            لا تعد أي شيء مثل (إليك 5 أسئلة مشابهة تتناسب مع السياق السوري:) مباشرة اعط القائمة.
            
            السؤال الأصلي:
            {original_question}"""
            
            response = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self.model.generate_content(prompt)
            )
            
            if not response or not response.text:
                raise RuntimeError("Empty response from Gemini for question variants")
            
            # Try to parse the response as a list
            try:
                # Clean the response text
                text = response.text.strip()
                if text.startswith('[') and text.endswith(']'):
                    variants = ast.literal_eval(text)
                    if isinstance(variants, list):
                        return variants[:num_variants]
            except (ValueError, SyntaxError):
                pass
            
            # Fallback: split by newlines and clean
            lines = response.text.strip().split('\n')
            variants = []
            for line in lines:
                line = line.strip()
                if line and not line.startswith('[') and not line.startswith(']'):
                    # Remove numbering and quotes
                    line = re.sub(r'^\d+\.\s*', '', line)
                    line = re.sub(r'^["\']|["\']$', '', line)
                    if line:
                        variants.append(line)
            
            return variants[:num_variants]
            
        except Exception as e:
            logger.error(f"Failed to generate question variants: {e}")
            raise RuntimeError(f"Failed to generate question variants: {e}")
    
    def _calculate_confidence(self, answer: str, question: str) -> float:
        """Calculate confidence score based on answer quality"""
        try:
            confidence = 0.8  # Base confidence
            
            # Adjust based on answer length
            if len(answer) > 100:
                confidence += 0.1
            elif len(answer) < 50:
                confidence -= 0.1
            
            # Adjust based on question-answer relevance
            question_words = set(question.lower().split())
            answer_words = set(answer.lower().split())
            
            if question_words and answer_words:
                overlap = len(question_words.intersection(answer_words))
                relevance = overlap / len(question_words)
                confidence += relevance * 0.1
            
            # Ensure confidence is between 0.0 and 1.0
            return max(0.0, min(1.0, confidence))
            
        except Exception as e:
            logger.warning(f"Failed to calculate confidence: {e}")
            return 0.8
    
    def _extract_keywords(self, text: str) -> List[str]:
        """Extract keywords from text"""
        try:
            # Simple keyword extraction
            words = text.lower().split()
            # Filter out common words and short words
            stop_words = {'في', 'من', 'إلى', 'على', 'هذا', 'هذه', 'التي', 'الذي', 'كان', 'هو', 'هي', 'و', 'أو', 'لكن', 'إذا', 'عندما', 'the', 'a', 'an', 'and', 'or', 'but', 'if', 'when', 'is', 'are', 'was', 'were', 'be', 'been', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should'}
            
            keywords = []
            for word in words:
                word = re.sub(r'[^\w\s]', '', word)
                if len(word) > 3 and word not in stop_words:
                    keywords.append(word)
            
            # Return unique keywords, limited to 10
            return list(set(keywords))[:10]
            
        except Exception as e:
            logger.warning(f"Failed to extract keywords: {e}")
            return []
    
    def _detect_language(self, text: str) -> str:
        """Detect language of text"""
        try:
            # Simple language detection based on character sets
            arabic_chars = sum(1 for char in text if '\u0600' <= char <= '\u06FF')
            english_chars = sum(1 for char in text if '\u0020' <= char <= '\u007F')
            
            if arabic_chars > english_chars:
                return "ar"
            else:
                return "en"
                
        except Exception as e:
            logger.warning(f"Failed to detect language: {e}")
            return "auto"
=======
        prompt = f"""أنشئ 5 أسئلة مشابهة و تملك معنى السؤال الأصلي و بما يتوافق مع المجتمع السوري:
                    أعد النتيجة بتنسيق list من  5 عناصر هكذا:
                    [ , , , , ]
                    لا تعد اي شيئ مثل (إليك 5 أسئلة مشابهة تتناسب مع السياق السوري:) مباشرة اعط القائمة
                    السؤال الأصلي:
                    {original_question}"""
        response = self.model.generate_answer(prompt)
        variants = ast.literal_eval(response.candidates[0].content.parts[0].text)
        return variants[:num_variants]
>>>>>>> 72b87816b64a29691b388b79eb40ec26d86dc91c
    
    async def check_content_safety(self, text: str) -> Dict[str, Any]:
        """Check content safety using Gemini"""
        try:
            if not self.model:
                return {"is_safe": True, "safety_ratings": []}
            
            prompt = f"""تحقق من سلامة المحتوى التالي وأعد تقييم السلامة:
            {text}
            
            أعد النتيجة بتنسيق JSON:
            {{"is_safe": true/false, "safety_ratings": [{{"category": "...", "probability": "..."}}]}}"""
            
            response = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self.model.generate_content(prompt)
            )
            
            if response and response.text:
                try:
                    return json.loads(response.text)
                except json.JSONDecodeError:
                    pass
            
            return {"is_safe": True, "safety_ratings": []}
            
        except Exception as e:
            logger.warning(f"Failed to check content safety: {e}")
            return {"is_safe": True, "safety_ratings": []}
    
    async def get_system_health(self) -> Dict[str, Any]:
        """Get system health status"""
        try:
            if not self.is_connected():
                return {
                    "connected": False,
                    "error": "Gemini client not initialized - missing API key"
                }
            
            # Test with a simple prompt
            test_prompt = "Hello, this is a health check."
            response = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self.model.generate_content(test_prompt)
            )
            
            if response and response.text:
                return {
                    "connected": True,
                    "model_name": self.model_name,
                    "response_time": "normal",
                    "api_key_configured": self.api_key is not None
                }
            else:
                return {
                    "connected": False,
                    "error": "No response from Gemini API"
                }
                
        except Exception as e:
            return {
                "connected": False,
                "error": str(e)
            }

# Global Gemini service instance
gemini_service = GeminiService()