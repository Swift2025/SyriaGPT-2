import os
import logging
import asyncio
from typing import List, Union, Optional

from dotenv import load_dotenv
import google.generativeai as genai
from config.logging_config import get_logger

# تحميل ملف .env
load_dotenv()

# إعداد اللوجر
logger = get_logger(__name__)


class EmbeddingService:
    def __init__(self, model_name: str = "models/embedding-001", output_dim: int = 768):
        self.model_name = model_name
        self.output_dim = output_dim  # عدد أبعاد الـ embedding

        api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
        if not api_key:
            logger.warning("GOOGLE_API_KEY or GEMINI_API_KEY not found - using mock mode")
            self.model_available = False
        else:
            try:
                genai.configure(api_key=api_key)
                self.model_available = True
                logger.info(f"Initialized EmbeddingService with model={self.model_name}, output_dim={self.output_dim}")
            except Exception as e:
                logger.error(f"Failed to configure Google AI: {e}")
                self.model_available = False

    async def generate_embedding(
        self,
        text: Union[str, List[str]]
    ) -> Optional[Union[List[float], List[List[float]]]]:
        """
        يُرجع المتجه (vector) للنص أو قائمة المتجهات للنصوص.
        """
        if not self.model_available:
            logger.warning("Embedding service not available - using hash-based embedding")
            # إنشاء embedding مبني على hash النص لضمان التمييز بين النصوص المختلفة
            import hashlib
            if isinstance(text, str):
                # إنشاء hash للنص وتحويله إلى embedding
                text_hash = hashlib.md5(text.encode('utf-8')).hexdigest()
                # تحويل hash إلى قائمة أرقام
                embedding = []
                for i in range(0, len(text_hash), 2):
                    hex_pair = text_hash[i:i+2]
                    embedding.append(int(hex_pair, 16) / 255.0)  # تحويل إلى 0-1
                
                # إكمال الـ embedding إلى الحجم المطلوب
                while len(embedding) < self.output_dim:
                    embedding.append(0.1)
                
                return embedding[:self.output_dim]
            else:
                return [self.generate_embedding(t) for t in text]

        if not text:
            logger.warning("Empty text provided for embedding generation")
            return None

        is_single = isinstance(text, str)
        texts = [text] if is_single else text

        # Retry mechanism for API calls
        max_retries = 3
        for attempt in range(max_retries):
            try:
                logger.debug(f"Attempting embedding generation (attempt {attempt + 1}/{max_retries})")
                
                # استدعاء API بشكل متزامن
                result = await asyncio.get_event_loop().run_in_executor(
                    None,
                    lambda: genai.embed_content(
                        model=self.model_name,
                        content=texts[0] if is_single else texts,
                        task_type="retrieval_query"
                    )
                )
            
                # التحقق من وجود النتيجة
                if not result:
                    logger.error("Empty result from Google AI embedding API")
                    if attempt < max_retries - 1:
                        logger.info(f"Retrying embedding generation (attempt {attempt + 1}/{max_retries})")
                        await asyncio.sleep(1)  # Wait 1 second before retry
                        continue
                    return None

                # إضافة debugging لمعرفة بنية الاستجابة
                logger.debug(f"Google AI API response type: {type(result)}")
                logger.debug(f"Google AI API response attributes: {dir(result)}")
                if hasattr(result, '__dict__'):
                    logger.debug(f"Google AI API response dict: {result.__dict__}")

                # معالجة الاستجابة بناءً على البنية الفعلية
                embedding_data = self._extract_embedding_data(result, is_single)
                
                if embedding_data is not None:
                    logger.debug(f"Successfully generated embeddings for {1 if is_single else len(texts)} text(s)")
                    return embedding_data
                else:
                    logger.error(f"Failed to extract embedding data from response")
                    if attempt < max_retries - 1:
                        logger.info(f"Retrying embedding generation (attempt {attempt + 1}/{max_retries})")
                        await asyncio.sleep(1)
                        continue
                    return None

            except Exception as e:
                logger.error(f"Embedding generation failed (attempt {attempt + 1}/{max_retries}): {e}")
                if attempt < max_retries - 1:
                    logger.info(f"Retrying embedding generation (attempt {attempt + 1}/{max_retries})")
                    await asyncio.sleep(1)  # Wait 1 second before retry
                    continue
                else:
                    logger.error(f"All {max_retries} attempts failed. Final error: {e}")
                    return None

    def _extract_embedding_data(self, result, is_single: bool) -> Optional[Union[List[float], List[List[float]]]]:
        """
        استخراج بيانات الـ embedding من استجابة Google AI API
        """
        try:
            # التعامل مع البنية الجديدة للاستجابة (dict)
            if isinstance(result, dict):
                # البنية الجديدة: dict مع key 'embedding'
                if 'embedding' in result:
                    embedding_data = result['embedding']
                    return self._validate_embedding_data(embedding_data, is_single)
                
                # البنية البديلة: dict مع key 'values'
                elif 'values' in result:
                    embedding_data = result['values']
                    return self._validate_embedding_data(embedding_data, is_single)
                
                # البنية البديلة: dict مع key 'embeddings'
                elif 'embeddings' in result:
                    embedding_data = result['embeddings']
                    return self._validate_embedding_data(embedding_data, is_single)
                
                else:
                    logger.error(f"Dict result missing expected keys. Available keys: {list(result.keys())}")
                    return None

            # التعامل مع البنية القديمة للاستجابة (object)
            elif hasattr(result, 'embedding'):
                # البنية القديمة: object مع attribute 'embedding'
                embedding_data = result.embedding
                if hasattr(embedding_data, 'values'):
                    return self._validate_embedding_data(embedding_data.values, is_single)
                elif isinstance(embedding_data, list):
                    return self._validate_embedding_data(embedding_data, is_single)
                else:
                    logger.error(f"Unexpected embedding attribute type: {type(embedding_data)}")
                    return None

            elif hasattr(result, 'values'):
                # البنية البديلة: object مع method 'values'
                embedding_data = result.values()
                return self._validate_embedding_data(embedding_data, is_single)

            else:
                logger.error(f"Unexpected response structure from Google AI API: {type(result)}")
                return None

        except Exception as e:
            logger.error(f"Error extracting embedding data: {e}")
            return None

    def _validate_embedding_data(self, embedding_data, is_single: bool) -> Optional[Union[List[float], List[List[float]]]]:
        """
        التحقق من صحة بيانات الـ embedding
        """
        try:
            if isinstance(embedding_data, list):
                if is_single:
                    # للـ single text، نتوقع list من الأرقام مباشرة
                    if embedding_data and all(isinstance(v, (int, float)) for v in embedding_data):
                        return embedding_data
                    else:
                        logger.error(f"Single text embedding is not a valid list of numbers: {type(embedding_data)}")
                        return None
                else:
                    # للـ multiple texts، نتوقع list of lists
                    valid_embeddings = []
                    for i, emb in enumerate(embedding_data):
                        if isinstance(emb, list) and all(isinstance(v, (int, float)) for v in emb):
                            valid_embeddings.append(emb)
                        else:
                            logger.warning(f"Invalid embedding at index {i}: {type(emb)}")
                    
                    if valid_embeddings:
                        return valid_embeddings
                    else:
                        logger.error("No valid embeddings found")
                        return None
            else:
                logger.error(f"Embedding data is not a list: {type(embedding_data)}")
                return None

        except Exception as e:
            logger.error(f"Error validating embedding data: {e}")
            return None

    def is_available(self) -> bool:
        """Check if the embedding service is available"""
        return self.model_available

    async def test_connection(self) -> bool:
        """Test the connection to Google Generative AI API"""
        try:
            logger.info("🔍 Testing Google Generative AI API connection...")
            
            if not self.model_available:
                logger.error("❌ Google Generative AI API not available - no API key")
                return False
            
            # Test with a simple text
            test_text = "test connection"
            result = await self.generate_embedding(test_text)
            
            if result is not None:
                logger.info("✅ Google Generative AI API connection test successful")
                return True
            else:
                logger.error("❌ Google Generative AI API connection test failed")
                return False
                
        except Exception as e:
            logger.error(f"❌ Google Generative AI API connection test failed: {e}")
            return False


# إنشاء الخدمة كـ singleton
try:
    embedding_service = EmbeddingService()
except Exception as e:
    logger.error(f"Failed to initialize EmbeddingService: {e}")
    # إنشاء خدمة وهمية في حالة الفشل
    embedding_service = None