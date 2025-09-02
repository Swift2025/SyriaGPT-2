import os
import logging
import asyncio
from typing import List, Optional, Union, Dict, Any
import numpy as np
from config.logging_config import get_logger

# Import the latest Google GenAI library
try:
    import google.generativeai as genai
    GENAI_AVAILABLE = True
except ImportError as e:
    GENAI_AVAILABLE = False
from typing import List, Optional, Union

from google import genai
from google.genai.types import EmbedContentConfig
import numpy as np
from config.logging_config import get_logger

logger = get_logger(__name__)

class EmbeddingService:
    """
    Embedding service using Google GenAI library (gemini-embedding-001).
    Requires GOOGLE_API_KEY or GEMINI_API_KEY in environment.
    """
    
    def __init__(self, model_name: str = "models/embedding-001", output_dim: Optional[int] = None):
        self.model_name = model_name
        self.output_dim = output_dim 
        self.api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
        self.client = None
        
        # Initialize client if possible
        if GENAI_AVAILABLE and self.api_key:
            self._initialize_client()
            logger.info(f"Initialized Gemini EmbeddingService with model={self.model_name}, output_dim={self.output_dim}")
        else:
            if not GENAI_AVAILABLE:
                logger.error("Google GenAI library not available. Please install: pip install google-generativeai")
            if not self.api_key:
                logger.error("GOOGLE_API_KEY or GEMINI_API_KEY not found in environment variables")
            logger.warning("EmbeddingService initialized but not fully configured")

    def _initialize_client(self):
        """Initialize GenAI client"""
        try:
            genai.configure(api_key=self.api_key)
            self.client = genai
            logger.info("GenAI client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize GenAI client: {e}")
            self.client = None

    async def generate_embedding(
        self,
        text: Union[str, List[str]]
    ) -> Optional[Union[List[float], List[List[float]]]]:
<<<<<<< HEAD
        """
        Generate embeddings using Google GenAI.
        
        Args:
            text: Single text string or list of text strings
            
        Returns:
            Single embedding or list of embeddings
        """
=======
>>>>>>> 72b87816b64a29691b388b79eb40ec26d86dc91c
        if not text:
            return None

        is_single = isinstance(text, str)
        texts = [text] if is_single else text

        try:
<<<<<<< HEAD
            if not self.client:
                raise RuntimeError("Embedding client not initialized")

            # Generate embeddings using GenAI
            embeddings = []
            for text_item in texts:
                try:
                    # Use the embedding model
                    result = await asyncio.get_event_loop().run_in_executor(
                        None,
                        lambda: self.client.embed_content(
                            model=self.model_name,
                            content=text_item
                        )
                    )
                    
                    if result:
                        # Check different possible attributes for the embedding
                        if hasattr(result, 'embedding'):
                            embedding = result.embedding
                        elif hasattr(result, 'values'):
                            embedding = result.values
                        elif hasattr(result, 'embeddings'):
                            embedding = result.embeddings[0] if isinstance(result.embeddings, list) else result.embeddings
                        else:
                            # Try to access as dictionary
                            if isinstance(result, dict):
                                embedding = result.get('embedding') or result.get('values') or result.get('embeddings')
                            else:
                                logger.warning(f"Unexpected result type: {type(result)}")
                                logger.warning(f"Result attributes: {dir(result)}")
                                embedding = None
                        
                        # If embedding is a callable (function), call it
                        if callable(embedding):
                            embedding = embedding()
                        
                        # Convert to list if needed
                        if embedding:
                            if hasattr(embedding, 'values'):  # dict_values
                                embedding = list(embedding)
                            elif not isinstance(embedding, list):
                                embedding = list(embedding)
                            
                            if self.output_dim and len(embedding) != self.output_dim:
                                # Resize embedding if needed
                                embedding = embedding[:self.output_dim] + [0.0] * (self.output_dim - len(embedding))
                            embeddings.append(embedding)
                        else:
                            logger.warning(f"No embedding found in result for text: {text_item[:50]}...")
                            logger.warning(f"Result type: {type(result)}")
                            logger.warning(f"Result: {result}")
                            raise RuntimeError(f"Failed to extract embedding from result for text: {text_item[:50]}...")
                    else:
                        logger.warning(f"No result returned for text: {text_item[:50]}...")
                        raise RuntimeError(f"Failed to generate embedding for text: {text_item[:50]}...")
                        
                except Exception as e:
                    logger.error(f"Failed to generate embedding for text: {e}")
                    raise RuntimeError(f"Embedding generation failed: {e}")
=======
            config = EmbedContentConfig()
            if self.output_dim:
                config.output_dimensionality = self.output_dim

            result = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self.client.models.embed_content(
                    model=self.model_name,
                    contents=texts,
                    config=config
                )
            )
            embeddings = result.embeddings  # list of embeddings
>>>>>>> 72b87816b64a29691b388b79eb40ec26d86dc91c

            return embeddings[0] if is_single else embeddings

        except Exception as e:
<<<<<<< HEAD
            logger.error(f"GenAI API embedding failed: {e}", exc_info=True)
            raise RuntimeError(f"Embedding service failed: {e}")

    def get_embedding_dimension(self) -> Optional[int]:
        """Get the embedding dimension"""
        return self.output_dim or 768
=======
            logger.error(f"Gemini API embedding failed: {e}", exc_info=True)
            return None

    def get_embedding_dimension(self) -> Optional[int]:
        return self.output_dim
>>>>>>> 72b87816b64a29691b388b79eb40ec26d86dc91c

    async def compute_similarity(
        self,
        embedding1: List[float],
        embedding2: List[float]
    ) -> float:
<<<<<<< HEAD
        """
        Compute cosine similarity between two embeddings.
        
        Args:
            embedding1: First embedding vector
            embedding2: Second embedding vector
            
        Returns:
            Similarity score between 0.0 and 1.0
        """
        try:
            vec1 = np.array(embedding1)
            vec2 = np.array(embedding2)
            
            # Ensure vectors have the same dimension
            if len(vec1) != len(vec2):
                min_len = min(len(vec1), len(vec2))
                vec1 = vec1[:min_len]
                vec2 = vec2[:min_len]
            
            dot = np.dot(vec1, vec2)
            n1 = np.linalg.norm(vec1)
            n2 = np.linalg.norm(vec2)
            
            if n1 == 0 or n2 == 0:
                return 0.0
                
            return float(dot / (n1 * n2))
            
=======
        try:
            vec1 = np.array(embedding1)
            vec2 = np.array(embedding2)
            dot = np.dot(vec1, vec2)
            n1 = np.linalg.norm(vec1)
            n2 = np.linalg.norm(vec2)
            if n1 == 0 or n2 == 0:
                return 0.0
            return float(dot / (n1 * n2))
>>>>>>> 72b87816b64a29691b388b79eb40ec26d86dc91c
        except Exception as e:
            logger.error(f"Similarity computation failed: {e}", exc_info=True)
            return 0.0

    async def generate_question_variants(
        self,
        original_question: str,
        num_variants: int = 3
    ) -> List[str]:
<<<<<<< HEAD
        """
        Generate question variants using simple rule-based approach.
        This is a fallback when Gemini is not available.
        
        Args:
            original_question: The original question
            num_variants: Number of variants to generate
            
        Returns:
            List of question variants
        """
        variants = []

        # Detect language
        is_arabic = any(char in original_question for char in 'أبتثجحخدذرزسشصضطظعغفقكلمنهوي')

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
                if not original_question.startswith(prefix):
                    variants.append(f"{prefix} {original_question}")
                else:
                    # Try different prefixes
                    alt_prefixes = ["ما هو", "أخبرني عن", "شرح"]
                    for alt_prefix in alt_prefixes:
                        if alt_prefix != prefix:
                            variants.append(f"{alt_prefix} {original_question}")
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
                if not original_question.startswith(prefix):
                    variants.append(f"{prefix} {original_question}")
                else:
                    # Try different prefixes
                    alt_prefixes = ["What is", "Tell me about", "Explain"]
                    for alt_prefix in alt_prefixes:
                        if alt_prefix != prefix:
                            variants.append(f"{alt_prefix} {original_question}")
                            break

        # Ensure we have unique variants
        unique_variants = []
        seen = set()
        for variant in variants:
            if variant not in seen:
                unique_variants.append(variant)
                seen.add(variant)
        
        return unique_variants[:num_variants]

    async def batch_generate_embeddings(
        self,
        texts: List[str],
        batch_size: int = 10
    ) -> List[List[float]]:
        """
        Generate embeddings for a batch of texts.
        
        Args:
            texts: List of text strings
            batch_size: Size of batches to process
            
        Returns:
            List of embeddings
        """
        try:
            all_embeddings = []
            
            for i in range(0, len(texts), batch_size):
                batch = texts[i:i + batch_size]
                batch_embeddings = await self.generate_embedding(batch)
                
                if batch_embeddings:
                    all_embeddings.extend(batch_embeddings)
                else:
                    raise RuntimeError(f"Failed to generate embeddings for batch")
                
                # Small delay between batches to avoid rate limiting
                await asyncio.sleep(0.1)
            
            return all_embeddings
            
        except Exception as e:
            logger.error(f"Batch embedding generation failed: {e}")
            raise RuntimeError(f"Batch embedding generation failed: {e}")

    def is_available(self) -> bool:
        """Check if the embedding service is available"""
        return GENAI_AVAILABLE and self.client is not None and self.api_key is not None

    async def get_system_health(self) -> Dict[str, Any]:
        """Get system health status"""
        try:
            if not GENAI_AVAILABLE:
                return {
                    "available": False,
                    "error": "Google GenAI library not available"
                }
            
            if not self.api_key:
                return {
                    "available": False,
                    "error": "API key not configured"
                }
            
            if not self.client:
                return {
                    "available": False,
                    "error": "Client not initialized"
                }
            
            # Test with a simple text
            test_text = "Hello, this is a health check."
            embedding = await self.generate_embedding(test_text)
            
            if embedding and len(embedding) > 0:
                return {
                    "available": True,
                    "model_name": self.model_name,
                    "embedding_dimension": len(embedding),
                    "response_time": "normal",
                    "api_key_configured": self.api_key is not None
                }
            else:
                return {
                    "available": False,
                    "error": "No embedding generated"
                }
                
        except Exception as e:
            return {
                "available": False,
                "error": str(e)
            }

# Global embedding service instance
embedding_service = EmbeddingService(output_dim=768)
=======
        variants = []

        if any(char in original_question for char in 'أبتثجحخدذرزسشصضطظعغفقكلمنهوي'):
            variants.extend([
                f"ما هو {original_question}",
                f"أخبرني عن {original_question}",
                f"شرح {original_question}",
            ])
        else:
            variants.extend([
                f"What is {original_question}?",
                f"Tell me about {original_question}",
                f"Explain {original_question}",
            ])

        return variants[:num_variants]

# Example global instance
embedding_service = EmbeddingService(output_dim=3072)
>>>>>>> 72b87816b64a29691b388b79eb40ec26d86dc91c
