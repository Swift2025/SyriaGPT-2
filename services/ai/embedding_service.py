import os
import logging
import asyncio
from typing import List, Optional

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
        self.output_dim = output_dim
        self.initialized = False

        api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
        if not api_key:
            msg = " GOOGLE_API_KEY or GEMINI_API_KEY not found"
            logger.error(msg)
            raise RuntimeError(msg)

        try:
            genai.configure(api_key=api_key)
            self.model_available = True
            logger.info(f" Initialized EmbeddingService with model={self.model_name}, output_dim={self.output_dim}")
        except Exception as e:
            msg = f" Failed to configure Google AI: {e}"
            logger.error(msg)
            raise RuntimeError(msg)

    async def initialize(self):
        """Initialize the embedding service."""
        try:
            self.initialized = True
            logger.info(f"Embedding service initialized with model: {self.model_name}")
        except Exception as e:
            logger.error(f"Embedding service initialization error: {e}")
            self.initialized = False

    async def generate_embedding(self, text: str) -> Optional[List[float]]:
        """Generate embedding for a single text."""
        try:
            if not self.initialized:
                raise RuntimeError("Embedding service not initialized")

            result = genai.embed_content(
                model=self.model_name,
                content=text,
                task_type="retrieval_document"
            )
            embedding = result['embedding']
            logger.debug(f"Generated embedding for text: {text[:50]}...")
            return embedding
        except Exception as e:
            logger.error(f"Error generating embedding: {e}")
            return None


    def is_available(self) -> bool:
        return getattr(self, "model_available", False)

    async def test_connection(self) -> bool:
        """Test the connection to Google Generative AI API"""
        result = await self.generate_embedding("test connection")
        return result is not None


# Singleton
embedding_service = EmbeddingService()