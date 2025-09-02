import os
import logging
import asyncio
import numpy as np
from typing import Union, List, Optional, Dict, Any
from config.logging_config import get_logger

logger = get_logger(__name__)

# Check if Google GenAI is available
try:
    import google.generativeai as genai
    GENAI_AVAILABLE = True
except ImportError:
    GENAI_AVAILABLE = False
    logger.warning("Google GenAI library not available. Install with: pip install google-generativeai")

class EmbeddingService:
    """
    Service for generating text embeddings using Google GenAI.
    Supports both single and batch text processing.
    """
    
    def __init__(self, output_dim: Optional[int] = None):
        self.api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
        self.model_name = "embedding-001"  # Google's embedding model
        self.output_dim = output_dim
        self.client = None
        
        if GENAI_AVAILABLE and self.api_key:
            self._initialize_client()
        else:
            logger.warning("Embedding service not available - missing API key or library")
    
    def _initialize_client(self):
        """Initialize the GenAI client"""
        try:
            genai.configure(api_key=self.api_key)
            self.client = genai
            logger.info(f"Embedding service initialized with model: {self.model_name}")
        except Exception as e:
            logger.error(f"Failed to initialize embedding client: {e}")
            self.client = None
    
    async def generate_embedding(
        self,
        text: Union[str, List[str]]
    ) -> Optional[Union[List[float], List[List[float]]]]:
        """
        Generate embeddings using Google GenAI.
        
        Args:
            text: Single text string or list of text strings
            
        Returns:
            Single embedding or list of embeddings
        """
        if not text:
            return None

        is_single = isinstance(text, str)
        texts = [text] if is_single else text

        try:
            if not self.client:
                raise RuntimeError("Embedding client not initialized")

            # Generate embeddings using GenAI
            embeddings = []
            for text_item in texts:
                try:
                    # Use the embedding model with the correct API
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

            return embeddings[0] if is_single else embeddings

        except Exception as e:
            logger.error(f"GenAI API embedding failed: {e}", exc_info=True)
            raise RuntimeError(f"Embedding service failed: {e}")

    def get_embedding_dimension(self) -> Optional[int]:
        """Get the embedding dimension"""
        return self.output_dim or 768

    async def compute_similarity(
        self,
        embedding1: List[float],
        embedding2: List[float]
    ) -> float:
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
            
        except Exception as e:
            logger.error(f"Similarity computation failed: {e}", exc_info=True)
            return 0.0

    async def generate_question_variants(
        self,
        original_question: str,
        num_variants: int = 3
    ) -> List[str]:
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
