import json
import logging
import time
import asyncio
from pathlib import Path
from typing import Dict, List, Any, Optional
import os

from .qdrant_service import qdrant_service
from .embedding_service import embedding_service
from config.logging_config import get_logger

logger = get_logger(__name__)

class DataIntegrationService:
    """
    Service for integrating Syria knowledge data from the data folder
    into Qdrant vector database.
    """
    
    def __init__(self):
        self.data_path = Path(__file__).parent.parent.parent / "data" / "syria_knowledge"
        self.knowledge_files = [
            "general.json",
            "cities.json", 
            "culture.json",
            "economy.json",
            "government.json",
            "Real_post_liberation_events.json"
        ]
        
    async def initialize_knowledge_base(self) -> Dict[str, Any]:
        """
        Initialize the complete knowledge base by loading data into Qdrant.
        This should be called during application startup.
        """
        logger.info("🚀 Starting Syria knowledge base initialization...")
        
        try:
            # Test embedding service connection first
            logger.info("🔍 Testing Google Generative AI API connection...")
            if not await embedding_service.test_connection():
                logger.error("❌ Google Generative AI API connection test failed. Please check your API key and configuration.")
                return {
                    "status": "error",
                    "error": "Google Generative AI API connection failed. Please check your API key and configuration."
                }
            
            # Load data into Qdrant vector database
            qdrant_result = await self._load_data_to_qdrant()
            if qdrant_result.get("status") == "error":
                logger.error(f"Qdrant initialization failed: {qdrant_result.get('message')}")
                return {
                    "status": "error",
                    "error": f"Qdrant initialization failed: {qdrant_result.get('message')}"
                }
            
            # Generate summary statistics
            summary = self._generate_summary(qdrant_result)
            
            logger.info(f"✅ Knowledge base initialization completed: {summary}")
            
            return {
                "status": "success",
                "qdrant": qdrant_result,
                "summary": summary
            }
            
        except Exception as e:
            logger.error(f"❌ Knowledge base initialization failed: {e}")
            return {
                "status": "error",
                "error": str(e)
            }
    
    async def _load_data_to_qdrant(self) -> Dict[str, Any]:
        """Load Syria knowledge data into Qdrant vector database"""
        logger.info("📥 Loading data into Qdrant vector database...")
        
        try:
            total_loaded = 0
            total_failed = 0
            file_stats = {}
            
            for filename in self.knowledge_files:
                file_path = self.data_path / filename
                if file_path.exists():
                    loaded_count, failed_count = await self._load_json_file_to_qdrant(file_path)
                    total_loaded += loaded_count
                    total_failed += failed_count
                    file_stats[filename] = {
                        "loaded": loaded_count,
                        "failed": failed_count
                    }
                    logger.info(f"📄 Loaded {loaded_count} items from {filename} (Failed: {failed_count})")
                else:
                    logger.warning(f"⚠️ File not found: {file_path}")
                    file_stats[filename] = {"loaded": 0, "failed": 0}
            
            return {
                "status": "success",
                "total_loaded": total_loaded,
                "total_failed": total_failed,
                "file_stats": file_stats
            }
            
        except Exception as e:
            logger.error(f"❌ Qdrant data loading failed: {e}")
            return {
                "status": "error",
                "message": str(e)
            }
    
    async def _load_json_file_to_qdrant(self, file_path: Path) -> tuple[int, int]:
        """Load a single JSON file's content into Qdrant"""
        loaded_count = 0
        failed_count = 0
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            category = data.get("category", file_path.stem)
            qa_pairs = data.get("qa_pairs", [])
            
            logger.info(f"Processing {len(qa_pairs)} Q&A pairs from {file_path.name}")
            
            for qa_pair in qa_pairs:
                try:
                    # Prepare data for Qdrant
                    qa_id = qa_pair.get("id")
                    if not qa_id:
                        logger.warning(f"Skipping Q&A pair without ID in {file_path.name}")
                        failed_count += 1
                        continue
                    
                    # Create text for embedding
                    question_text = " ".join(qa_pair.get("question_variants", []))
                    answer_text = qa_pair.get("answer", "")
                    keywords_text = " ".join(qa_pair.get("keywords", []))
                    
                    # Combine all text for embedding
                    combined_text = f"{question_text} {answer_text} {keywords_text}"
                    
                    # Skip if text is too short or empty
                    if not combined_text.strip():
                        logger.warning(f"Skipping Q&A pair {qa_id} with empty text content")
                        failed_count += 1
                        continue
                    
                    # Generate embedding with retry logic
                    embedding = await self._generate_embedding_with_retry(combined_text, qa_id)
                    
                    if embedding:
                        # Store in Qdrant
                        await qdrant_service.add_qa_pair(
                            qa_id=qa_id,
                            question_variants=qa_pair.get("question_variants", []),
                            answer=answer_text,
                            keywords=qa_pair.get("keywords", []),
                            confidence=qa_pair.get("confidence", 1.0),
                            source=qa_pair.get("source", ""),
                            category=category,
                            embedding=embedding
                        )
                        loaded_count += 1
                        logger.debug(f"✅ Successfully loaded Q&A pair {qa_id}")
                    else:
                        logger.warning(f"Failed to generate embedding for Q&A pair {qa_id}")
                        failed_count += 1
                        
                except Exception as e:
                    logger.error(f"Error processing Q&A pair {qa_pair.get('id', 'unknown')}: {e}")
                    failed_count += 1
                    continue
            
            logger.info(f"📊 File {file_path.name} processing complete: {loaded_count} loaded, {failed_count} failed")
            return loaded_count, failed_count
            
        except Exception as e:
            logger.error(f"Error loading file {file_path}: {e}")
            return 0, 0
    
    async def _generate_embedding_with_retry(self, text: str, qa_id: str, max_retries: int = 3) -> Optional[List[float]]:
        """
        Generate embedding with retry logic and detailed error logging
        """
        for attempt in range(max_retries):
            try:
                logger.debug(f"Generating embedding for Q&A pair {qa_id} (attempt {attempt + 1}/{max_retries})")
                
                embedding = await embedding_service.generate_embedding(text)
                
                if embedding:
                    logger.debug(f"✅ Successfully generated embedding for Q&A pair {qa_id}")
                    return embedding
                else:
                    logger.warning(f"Embedding generation returned None for Q&A pair {qa_id} (attempt {attempt + 1})")
                    
            except Exception as e:
                logger.warning(f"Embedding generation attempt {attempt + 1} failed for Q&A pair {qa_id}: {e}")
                
                if attempt < max_retries - 1:
                    # Wait before retrying with exponential backoff
                    wait_time = 2 ** attempt
                    logger.info(f"Retrying embedding generation for {qa_id} in {wait_time} seconds...")
                    await asyncio.sleep(wait_time)
                else:
                    logger.error(f"All {max_retries} attempts failed for Q&A pair {qa_id}. Final error: {e}")
        
        logger.error(f"Failed to generate embedding for Q&A pair {qa_id} after {max_retries} attempts")
        return None
    
    def _generate_summary(self, qdrant_result: Dict[str, Any]) -> Dict[str, Any]:
        """Generate summary statistics for the knowledge base"""
        qdrant_total = qdrant_result.get("total_loaded", 0) if qdrant_result.get("status") == "success" else 0
        qdrant_failed = qdrant_result.get("total_failed", 0) if qdrant_result.get("status") == "success" else 0
        
        return {
            "total_qa_pairs": qdrant_total,
            "total_failed": qdrant_failed,
            "success_rate": f"{(qdrant_total / (qdrant_total + qdrant_failed) * 100):.1f}%" if (qdrant_total + qdrant_failed) > 0 else "0%",
            "qdrant_loaded": qdrant_total,
            "qdrant_status": qdrant_result.get("status", "unknown"),
            "files_processed": len(self.knowledge_files)
        }
    
    async def clear_knowledge_base(self) -> Dict[str, Any]:
        """Clear existing data from Qdrant"""
        logger.info("🧹 Clearing knowledge base data...")
        
        try:
            # Clear Qdrant data
            await qdrant_service.clear_collection()
            
            logger.info("✅ Knowledge base cleared successfully")
            return {
                "status": "success",
                "message": "Knowledge base cleared successfully"
            }
            
        except Exception as e:
            logger.error(f"❌ Failed to clear knowledge base: {e}")
            return {
                "status": "error",
                "message": str(e)
            }
    
    async def get_knowledge_base_stats(self) -> Dict[str, Any]:
        """Get statistics about the knowledge base"""
        try:
            qdrant_stats = await qdrant_service.get_collection_stats()
            
            return {
                "qdrant": qdrant_stats,
                "files_available": len(self.knowledge_files),
                "data_path": str(self.data_path)
            }
            
        except Exception as e:
            logger.error(f"Error getting knowledge base stats: {e}")
            return {
                "status": "error",
                "error": str(e)
            }

# Global data integration service instance
data_integration_service = DataIntegrationService()

def get_data_integration_service():
    """Get the global data integration service instance"""
    return data_integration_service
