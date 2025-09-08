"""
Embedding service for SyriaGPT.
Handles text embedding generation using Google AI.
"""

import logging
from typing import List, Dict, Any, Optional
import google.generativeai as genai
from config.config_loader import ConfigLoader
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)


class EmbeddingService:
    """Embedding service for generating text embeddings."""
    
    def __init__(self, config: ConfigLoader):
        """Initialize embedding service.
        
        Args:
            config: Configuration loader instance
        """
        self.config = config
        self.ai_config = config.get_ai_config()
        self.embedding_model = self.ai_config.get("embedding_model", "text-embedding-004")
        self.embedding_dim = config.get("EMBEDDING_DIM", 768)
        self.initialized = False
    
    async def initialize(self):
        """Initialize the embedding service."""
        try:
            # Configure Google AI
            api_key = self.ai_config.get("gemini_api_key") or self.ai_config.get("google_api_key")
            if not api_key:
                logger.warning("Google AI API key not configured for embeddings")
                return
            
            genai.configure(api_key=api_key)
            
            self.initialized = True
            logger.info(f"Embedding service initialized with model: {self.embedding_model}")
            
        except Exception as e:
            logger.error(f"Embedding service initialization error: {e}")
            self.initialized = False
    
    async def generate_embedding(self, text: str) -> Optional[List[float]]:
        """Generate embedding for a single text.
        
        Args:
            text: Input text
            
        Returns:
            Embedding vector or None if failed
        """
        try:
            if not self.initialized:
                raise RuntimeError("Embedding service not initialized")
            
            # Generate embedding using Google AI
            result = genai.embed_content(
                model=self.embedding_model,
                content=text,
                task_type="retrieval_document"
            )
            
            embedding = result['embedding']
            logger.debug(f"Generated embedding for text: {text[:50]}...")
            return embedding
            
        except Exception as e:
            logger.error(f"Error generating embedding: {e}")
            return None
    
    async def generate_embeddings(self, texts: List[str]) -> List[Optional[List[float]]]:
        """Generate embeddings for multiple texts.
        
        Args:
            texts: List of input texts
            
        Returns:
            List of embedding vectors (None for failed embeddings)
        """
        try:
            if not self.initialized:
                raise RuntimeError("Embedding service not initialized")
            
            embeddings = []
            for text in texts:
                embedding = await self.generate_embedding(text)
                embeddings.append(embedding)
            
            logger.info(f"Generated {len(embeddings)} embeddings")
            return embeddings
            
        except Exception as e:
            logger.error(f"Error generating embeddings: {e}")
            return [None] * len(texts)
    
    
    def is_available(self) -> bool:
        """Check if embedding service is available.
        
        Returns:
            True if service is available, False otherwise
        """
        return self.initialized
    
    def get_service_info(self) -> Dict[str, Any]:
        """Get service information.
        
        Returns:
            Service information
        """
        return {
            "initialized": self.initialized,
            "embedding_model": self.embedding_model,
            "embedding_dim": self.embedding_dim,
            "config": self.ai_config
        }


# Initialize with config
config = ConfigLoader()
embedding_service = EmbeddingService(config)