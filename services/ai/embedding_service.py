import os
import logging
import asyncio
from typing import List, Union, Optional

from dotenv import load_dotenv
import google.generativeai as genai

# تحميل ملف .env
load_dotenv()

# إعداد اللوجر
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


class EmbeddingService:
    def __init__(self, model_name: str = "models/embedding-001", output_dim: int = 768):
        self.model_name = model_name
        self.output_dim = output_dim  # عدد أبعاد الـ embedding

        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError("GOOGLE_API_KEY غير موجود في متغيرات البيئة")

        genai.configure(api_key=api_key)
        logger.info(f"Initialized EmbeddingService with model={self.model_name}, output_dim={self.output_dim}")

    async def generate_embedding(
        self,
        text: Union[str, List[str]]
    ) -> Optional[Union[List[float], List[List[float]]]]:
        """
        يُرجع المتجه (vector) للنص أو قائمة المتجهات للنصوص.
        """
        if not text:
            logger.warning("Empty text provided for embedding generation")
            return None

        is_single = isinstance(text, str)
        texts = [text] if is_single else text

        try:
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
                return None

            # إضافة debugging لمعرفة بنية الاستجابة
            logger.debug(f"Google AI API response type: {type(result)}")
            logger.debug(f"Google AI API response attributes: {dir(result)}")
            if hasattr(result, '__dict__'):
                logger.debug(f"Google AI API response dict: {result.__dict__}")

            # التعامل مع البنية الجديدة للاستجابة
            if isinstance(result, dict):
                # البنية الجديدة: dict مع key 'embedding'
                if 'embedding' in result:
                    embedding_data = result['embedding']
                    if isinstance(embedding_data, list):
                        # التحقق من أن البيانات صحيحة
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
                else:
                    logger.error(f"Dict result missing 'embedding' key. Available keys: {list(result.keys())}")
                    return None
            elif hasattr(result, 'embedding'):
                # البنية القديمة: object مع attribute 'embedding'
                if is_single:
                    return result.embedding.values
                else:
                    return [item.embedding.values for item in result.embedding]
            elif hasattr(result, 'values'):
                # البنية البديلة: object مع method 'values'
                if is_single:
                    return result.values()
                else:
                    return [item.values() for item in result]
            else:
                logger.error(f"Unexpected response structure from Google AI API: {type(result)}")
                return None

        except Exception as e:
            logger.error(f"Embedding generation failed: {e}", exc_info=True)
            return None

    def is_available(self) -> bool:
        """Check if the embedding service is available"""
        try:
            api_key = os.getenv("GOOGLE_API_KEY")
            return api_key is not None
        except Exception:
            return False


# إنشاء الخدمة كـ singleton
embedding_service = EmbeddingService()
