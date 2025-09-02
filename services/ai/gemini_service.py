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
from datetime import datetime
import re

logger = get_logger(__name__)

class GeminiService:
    """
    Service for Google Gemini API integration using the latest GenAI library.
    Handles intelligent question answering with context and quality evaluation.
    """
    
    def __init__(self):
        self.api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
        self.model_name = "gemini-1.5-flash"  # Fast model for Q&A
        self.pro_model_name = "gemini-1.5-pro"  # More capable model for complex queries
        self.client = None
        self.model = None
        self.pro_model = None
        self.max_tokens = 2000
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize Gemini client with latest GenAI library"""
        if not self.api_key:
            logger.warning("GOOGLE_API_KEY or GEMINI_API_KEY not found - Gemini service will be unavailable")
            self.client = None
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
        context: Optional[str] = None,
        language: str = "auto",
        previous_qa_pairs: Optional[List[Dict[str, Any]]] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Answer a question using Gemini AI with optional context and conversation history.
        
        Args:
            question: The question to answer
            context: Optional context information (e.g., web scraped content)
            language: Language preference (auto-detected if "auto")
            previous_qa_pairs: Optional list of previous Q&A pairs for context
            
        Returns:
            Dictionary with answer and metadata, or None if failed
        """
        if not self.is_connected():
            logger.error("Gemini service not connected")
            return None
        
        try:
            start_time = time.time()
            
            # Build the prompt with context
            prompt = self._build_prompt(question, context, language, previous_qa_pairs)
            
            # Use the appropriate model based on complexity
            model_to_use = self.pro_model if self._is_complex_question(question, context) else self.model
            
            # Generate response
            response = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: model_to_use.generate_content(prompt)
            )
            
            if not response or not response.text:
                logger.warning("Empty response from Gemini")
                return None
            
            # Process and validate response
            processed_response = self._process_response(response.text, question, language)
            
            if not processed_response:
                logger.warning("Failed to process Gemini response")
                return None
            
            processing_time = time.time() - start_time
            
            # Extract confidence and other metadata
            confidence = self._extract_confidence(processed_response, context)
            
            return {
                "answer": processed_response,
                "confidence": confidence,
                "language": language,
                "model_used": model_to_use.model_name,
                "processing_time": processing_time,
                "sources": self._extract_sources(context),
                "keywords": self._extract_keywords(processed_response),
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to answer question with Gemini: {e}")
            return None
    
    def _build_prompt(
        self,
        question: str,
        context: Optional[str] = None,
        language: str = "auto",
        previous_qa_pairs: Optional[List[Dict[str, Any]]] = None
    ) -> str:
        """Build a comprehensive prompt for Gemini"""
        prompt_parts = []
        
        # System instructions
        system_instructions = self._get_system_instructions(language)
        prompt_parts.append(system_instructions)
        
        # Context information
        if context:
            prompt_parts.append(f"Context Information:\n{context}\n")
        
        # Previous Q&A pairs for conversation context
        if previous_qa_pairs:
            prompt_parts.append("Previous Questions and Answers:")
            for qa in previous_qa_pairs[-3:]:  # Last 3 Q&A pairs
                prompt_parts.append(f"Q: {qa.get('question', '')}")
                prompt_parts.append(f"A: {qa.get('answer', '')}\n")
        
        # Current question
        prompt_parts.append(f"Question: {question}")
        
        # Language-specific instructions
        if language != "auto":
            lang_instruction = self._get_language_instruction(language)
            if lang_instruction:
                prompt_parts.append(f"\n{lang_instruction}")
        
        return "\n".join(prompt_parts)
    
    def _get_system_instructions(self, language: str) -> str:
        """Get system instructions based on language"""
        base_instructions = """
You are SyriaGPT, an intelligent AI assistant specialized in providing accurate, helpful, and contextually relevant information about Syria. 

Your responses should be:
- Accurate and fact-based
- Helpful and informative
- Respectful of cultural sensitivities
- Well-structured and easy to understand
- Based on the provided context when available

When answering questions:
1. Use the provided context if available
2. Provide comprehensive but concise answers
3. If you're unsure about specific details, acknowledge the limitations
4. Focus on factual information rather than opinions
5. Be sensitive to the complex historical and political context of Syria
"""
        
        if language == "ar" or any(char in "أبتثجحخدذرزسشصضطظعغفقكلمنهوي" for char in language):
            base_instructions += "\nأجب باللغة العربية بشكل واضح ومفهوم."
        
        return base_instructions
    
    def _get_language_instruction(self, language: str) -> str:
        """Get language-specific instruction"""
        language_instructions = {
            "en": "Please respond in English.",
            "ar": "يرجى الإجابة باللغة العربية.",
            "fr": "Veuillez répondre en français.",
            "de": "Bitte antworten Sie auf Deutsch.",
            "es": "Por favor, responda en español."
        }
        return language_instructions.get(language, "")
    
    def _is_complex_question(self, question: str, context: Optional[str] = None) -> bool:
        """Determine if a question is complex enough to use the pro model"""
        # Use pro model for longer questions or when context is provided
        if context and len(context) > 1000:
            return True
        
        # Use pro model for questions that seem complex
        complex_indicators = [
            "explain", "analyze", "compare", "discuss", "evaluate",
            "explain", "حلل", "قارن", "ناقش", "قيّم"
        ]
        
        question_lower = question.lower()
        return any(indicator in question_lower for indicator in complex_indicators)
    
    def _process_response(self, response_text: str, question: str, language: str) -> Optional[str]:
        """Process and validate the Gemini response"""
        if not response_text or len(response_text.strip()) < 10:
            return None
        
        # Clean up the response
        cleaned_response = response_text.strip()
        
        # Remove any markdown formatting if present
        cleaned_response = re.sub(r'```[\w]*\n', '', cleaned_response)
        cleaned_response = re.sub(r'```', '', cleaned_response)
        
        # Ensure the response is relevant to the question
        if not self._is_response_relevant(cleaned_response, question):
            logger.warning("Gemini response seems irrelevant to the question")
            return None
        
        return cleaned_response
    
    def _is_response_relevant(self, response: str, question: str) -> bool:
        """Check if the response is relevant to the question"""
        # Simple relevance check - can be enhanced
        question_words = set(re.findall(r'\w+', question.lower()))
        response_words = set(re.findall(r'\w+', response.lower()))
        
        # Check for common words
        common_words = question_words.intersection(response_words)
        return len(common_words) >= min(2, len(question_words) // 2)
    
    def _extract_confidence(self, response: str, context: Optional[str] = None) -> float:
        """Extract confidence score for the response"""
        base_confidence = 0.8
        
        # Increase confidence if context is provided
        if context:
            base_confidence += 0.1
        
        # Increase confidence for longer, more detailed responses
        if len(response) > 200:
            base_confidence += 0.05
        
        # Decrease confidence for responses with uncertainty indicators
        uncertainty_indicators = [
            "I'm not sure", "I don't know", "might be", "could be",
            "لست متأكداً", "لا أعرف", "قد يكون", "يمكن أن يكون"
        ]
        
        for indicator in uncertainty_indicators:
            if indicator.lower() in response.lower():
                base_confidence -= 0.1
                break
        
        return min(1.0, max(0.0, base_confidence))
    
    def _extract_sources(self, context: Optional[str] = None) -> List[str]:
        """Extract source information from context"""
        sources = []
        
        if context:
            # Look for URL patterns
            url_pattern = r'https?://[^\s]+'
            urls = re.findall(url_pattern, context)
            sources.extend(urls)
            
            # Look for source mentions
            source_patterns = [
                r'source[s]?\s*:\s*([^\n]+)',
                r'from\s+([^\n]+)',
                r'according\s+to\s+([^\n]+)'
            ]
            
            for pattern in source_patterns:
                matches = re.findall(pattern, context, re.IGNORECASE)
                sources.extend(matches)
        
        return list(set(sources))  # Remove duplicates
    
    def _extract_keywords(self, response: str) -> List[str]:
        """Extract key terms from the response"""
        # Simple keyword extraction - can be enhanced with NLP
        words = re.findall(r'\b\w{4,}\b', response.lower())
        
        # Filter out common stop words
        stop_words = {
            'this', 'that', 'with', 'have', 'will', 'from', 'they', 'know',
            'want', 'been', 'good', 'much', 'some', 'time', 'very', 'when',
            'just', 'into', 'than', 'more', 'other', 'about', 'many', 'then',
            'them', 'these', 'people', 'only', 'would', 'there', 'could',
            'their', 'said', 'each', 'which', 'she', 'do', 'how', 'if',
            'up', 'out', 'so', 'but', 'he', 'we', 'my', 'has', 'her',
            'our', 'one', 'all', 'can', 'had', 'by', 'for', 'not',
            'are', 'you', 'or', 'an', 'at', 'as', 'be', 'to', 'of',
            'and', 'in', 'is', 'it', 'the', 'a', 'on', 'was', 'i'
        }
        
        keywords = [word for word in words if word not in stop_words]
        
        # Return top keywords by frequency
        from collections import Counter
        word_counts = Counter(keywords)
        return [word for word, count in word_counts.most_common(10)]
    
    async def generate_question_variants(
        self,
        question: str,
        num_variants: int = 3,
        language: str = "auto"
    ) -> List[str]:
        """
        Generate question variants for better search coverage.
        
        Args:
            question: Original question
            num_variants: Number of variants to generate
            language: Language preference
            
        Returns:
            List of question variants
        """
        if not self.is_connected():
            logger.warning("Gemini not available for question variants, using fallback")
            return await self._generate_fallback_variants(question, num_variants, language)
        
        try:
            prompt = f"""
Generate {num_variants} different ways to ask the same question. 
The variants should be semantically equivalent but use different phrasing.

Original question: {question}

Generate {num_variants} variants:
"""
            
            response = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self.model.generate_content(prompt)
            )
            
            if not response or not response.text:
                return await self._generate_fallback_variants(question, num_variants, language)
            
            # Parse the response to extract variants
            variants = self._parse_variants_from_response(response.text, num_variants)
            
            if len(variants) >= num_variants:
                return variants[:num_variants]
            else:
                # Fill remaining slots with fallback variants
                fallback_variants = await self._generate_fallback_variants(question, num_variants - len(variants), language)
                return variants + fallback_variants
                
        except Exception as e:
            logger.warning(f"Failed to generate variants with Gemini: {e}, using fallback")
            return await self._generate_fallback_variants(question, num_variants, language)
    
    def _parse_variants_from_response(self, response_text: str, num_variants: int) -> List[str]:
        """Parse question variants from Gemini response"""
        variants = []
        
        # Try to extract numbered variants
        lines = response_text.split('\n')
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Remove numbering and clean up
            cleaned_line = re.sub(r'^\d+[\.\)]\s*', '', line)
            cleaned_line = re.sub(r'^[-*]\s*', '', cleaned_line)
            
            if cleaned_line and len(cleaned_line) > 10:
                variants.append(cleaned_line)
            
            if len(variants) >= num_variants:
                break
        
        return variants
    
    async def _generate_fallback_variants(
        self,
        question: str,
        num_variants: int,
        language: str
    ) -> List[str]:
        """Generate fallback variants using simple rules"""
        variants = []
        
        # Detect language
        is_arabic = any(char in question for char in 'أبتثجحخدذرزسشصضطظعغفقكلمنهوي')
        
        if is_arabic:
            # Arabic variants
            arabic_prefixes = [
                "ما هو",
                "أخبرني عن",
                "شرح",
                "ما هي",
                "كيف",
                "متى",
                "أين",
                "لماذا"
            ]
            
            for prefix in arabic_prefixes[:num_variants]:
                if not question.startswith(prefix):
                    variants.append(f"{prefix} {question}")
                else:
                    # Try different prefixes
                    alt_prefixes = ["ما هو", "أخبرني عن", "شرح"]
                    for alt_prefix in alt_prefixes:
                        if alt_prefix != prefix:
                            variants.append(f"{alt_prefix} {question}")
                            break
        else:
            # English variants
            english_prefixes = [
                "What is",
                "Tell me about",
                "Explain",
                "How",
                "When",
                "Where",
                "Why",
                "Can you describe"
            ]
            
            for prefix in english_prefixes[:num_variants]:
                if not question.startswith(prefix):
                    variants.append(f"{prefix} {question}")
                else:
                    # Try different prefixes
                    alt_prefixes = ["What is", "Tell me about", "Explain"]
                    for alt_prefix in alt_prefixes:
                        if alt_prefix != prefix:
                            variants.append(f"{alt_prefix} {question}")
                            break
        
        # Ensure we have unique variants
        unique_variants = []
        seen = set()
        for variant in variants:
            if variant not in seen:
                unique_variants.append(variant)
                seen.add(variant)
        
        return unique_variants[:num_variants]
    
    async def get_health(self) -> Dict[str, Any]:
        """Get health status of the Gemini service"""
        try:
            if not self.is_connected():
                return {
                    "available": False,
                    "error": "Service not connected",
                    "details": "API key missing or client not initialized"
                }
            
            # Test with a simple question
            test_response = await self.answer_question(
                question="Hello, this is a health check.",
                context="Health check test",
                language="en"
            )
            
            if test_response and test_response.get("answer"):
                return {
                    "available": True,
                    "models": {
                        "standard": self.model_name,
                        "pro": self.pro_model_name
                    },
                    "api_key_configured": bool(self.api_key),
                    "response_time": "normal"
                }
            else:
                return {
                    "available": False,
                    "error": "Test question failed",
                    "details": "Service connected but not responding properly"
                }
                
        except Exception as e:
            return {
                "available": False,
                "error": str(e),
                "details": "Health check failed with exception"
            }

# Global Gemini service instance
gemini_service = GeminiService()