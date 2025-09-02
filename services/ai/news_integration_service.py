import asyncio
import logging
import time
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import json
import hashlib

from .web_scraping_service import web_scraping_service, ScrapedArticle
from .embedding_service import embedding_service
from .qdrant_service import qdrant_service
from .gemini_service import gemini_service
from config.logging_config import get_logger, log_function_entry, log_function_exit, log_performance

logger = get_logger(__name__)

class NewsIntegrationService:
    """
    Service for integrating scraped news articles into the intelligent QA system.
    
    This service:
    1. Scrapes news from Syrian sources
    2. Converts articles into Q&A pairs using Gemini
    3. Stores them in Qdrant for semantic search
    4. Maintains freshness and relevance
    """
    
    def __init__(self):
        self.last_update_time = None
        self.update_interval_hours = 6  # Update every 6 hours
        self.max_articles_per_update = 100
        self.qa_generation_prompt = """
        تحويل المقال الإخباري إلى أسئلة وأجوبة:
        
        المقال: {article_title}
        
        المحتوى: {article_content}
        
        المطلوب:
        1. استخرج 3-5 أسئلة مهمة من المقال
        2. اكتب إجابات واضحة ومفصلة لكل سؤال
        3. ركز على المعلومات المهمة والحديثة
        4. استخدم لغة عربية واضحة
        
        الإجابة المطلوبة بتنسيق JSON:
        {{
            "qa_pairs": [
                {{
                    "question": "السؤال الأول",
                    "answer": "الإجابة الأولى",
                    "keywords": ["كلمة1", "كلمة2"],
                    "confidence": 0.9
                }}
            ]
        }}
        """
        
    async def update_news_knowledge(self, force_update: bool = False) -> Dict[str, Any]:
        """
        Update the knowledge base with fresh news articles.
        
        Args:
            force_update: Force update even if not due
            
        Returns:
            Dictionary with update results
        """
        log_function_entry(logger, "update_news_knowledge", force_update=force_update)
        start_time = time.time()
        
        try:
            # Check if update is needed
            if not force_update and not self._should_update():
                return {
                    "status": "skipped",
                    "message": "No update needed",
                    "last_update": self.last_update_time.isoformat() if self.last_update_time else None
                }
            
            logger.info("🔄 Starting news knowledge update...")
            
            # Step 1: Scrape news articles
            scraping_result = await self._scrape_fresh_news()
            if scraping_result.get("status") != "success":
                return {
                    "status": "error",
                    "error": f"News scraping failed: {scraping_result.get('error')}",
                    "step": "scraping"
                }
            
            articles = scraping_result.get("articles", [])
            if not articles:
                return {
                    "status": "success",
                    "message": "No new articles found",
                    "articles_processed": 0
                }
            
            # Step 2: Convert articles to Q&A pairs
            qa_pairs = await self._convert_articles_to_qa(articles)
            if not qa_pairs:
                return {
                    "status": "error",
                    "error": "Failed to convert articles to Q&A pairs",
                    "step": "conversion"
                }
            
            # Step 3: Store Q&A pairs in knowledge base
            storage_result = await self._store_qa_pairs(qa_pairs)
            
            # Update last update time
            self.last_update_time = datetime.now()
            
            result = {
                "status": "success",
                "articles_scraped": len(articles),
                "qa_pairs_generated": len(qa_pairs),
                "qa_pairs_stored": storage_result.get("stored_count", 0),
                "sources": scraping_result.get("sources_scraped", []),
                "processing_time": time.time() - start_time,
                "last_update": self.last_update_time.isoformat()
            }
            
            duration = time.time() - start_time
            log_performance(logger, "News knowledge update", duration, 
                          articles_count=len(articles), 
                          qa_pairs_count=len(qa_pairs))
            log_function_exit(logger, "update_news_knowledge", result=result, duration=duration)
            
            logger.info(f"✅ News knowledge updated: {len(qa_pairs)} Q&A pairs from {len(articles)} articles")
            return result
            
        except Exception as e:
            duration = time.time() - start_time
            log_function_exit(logger, "update_news_knowledge", duration=duration)
            logger.error(f"❌ News knowledge update failed: {e}")
            return {
                "status": "error",
                "error": str(e),
                "processing_time": time.time() - start_time
            }
    
    def _should_update(self) -> bool:
        """Check if a news update is needed"""
        if not self.last_update_time:
            return True
        
        time_since_update = datetime.now() - self.last_update_time
        return time_since_update >= timedelta(hours=self.update_interval_hours)
    
    async def _scrape_fresh_news(self) -> Dict[str, Any]:
        """Scrape fresh news articles from configured sources"""
        try:
            # Initialize web scraping service if needed
            if not web_scraping_service.session:
                await web_scraping_service.initialize()
            
            # Scrape news sources
            result = await web_scraping_service.scrape_news_sources(
                max_articles=self.max_articles_per_update
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to scrape fresh news: {e}")
            return {"status": "error", "error": str(e)}
    
    async def _convert_articles_to_qa(self, articles: List[ScrapedArticle]) -> List[Dict[str, Any]]:
        """Convert scraped articles to Q&A pairs using Gemini"""
        qa_pairs = []
        
        for article in articles:
            try:
                # Generate Q&A pairs for this article
                article_qa_pairs = await self._generate_qa_from_article(article)
                if article_qa_pairs:
                    qa_pairs.extend(article_qa_pairs)
                    
            except Exception as e:
                logger.warning(f"Failed to convert article {article.url}: {e}")
                continue
        
        return qa_pairs
    
    async def _generate_qa_from_article(self, article: ScrapedArticle) -> List[Dict[str, Any]]:
        """Generate Q&A pairs from a single article using Gemini"""
        try:
            # Prepare the prompt
            prompt = self.qa_generation_prompt.format(
                article_title=article.title,
                article_content=article.content[:2000]  # Limit content length
            )
            
            # Generate Q&A pairs using Gemini
            response = await gemini_service.generate_content(
                prompt=prompt,
                max_tokens=2000,
                temperature=0.7
            )
            
            if not response:
                return []
            
            # Parse the JSON response
            try:
                qa_data = json.loads(response)
                qa_pairs = qa_data.get("qa_pairs", [])
                
                # Process and enhance Q&A pairs
                processed_pairs = []
                for qa_pair in qa_pairs:
                    processed_pair = self._process_qa_pair(qa_pair, article)
                    if processed_pair:
                        processed_pairs.append(processed_pair)
                
                return processed_pairs
                
            except json.JSONDecodeError:
                logger.warning(f"Failed to parse Gemini response for article {article.url}")
                return []
                
        except Exception as e:
            logger.warning(f"Failed to generate Q&A from article {article.url}: {e}")
            return []
    
    def _process_qa_pair(self, qa_pair: Dict[str, Any], article: ScrapedArticle) -> Optional[Dict[str, Any]]:
        """Process and enhance a Q&A pair with metadata"""
        try:
            question = qa_pair.get("question", "").strip()
            answer = qa_pair.get("answer", "").strip()
            
            if not question or not answer:
                return None
            
            # Generate unique ID
            qa_id = f"news_{hashlib.md5(f'{question}{answer}'.encode()).hexdigest()[:16]}"
            
            # Enhance with metadata
            processed_pair = {
                "id": qa_id,
                "question": question,
                "answer": answer,
                "keywords": qa_pair.get("keywords", []),
                "confidence": qa_pair.get("confidence", 0.8),
                "source": f"news_{article.source}",
                "category": "news",
                "metadata": {
                    "original_article": {
                        "title": article.title,
                        "url": article.url,
                        "source": article.source,
                        "published_date": article.published_date,
                        "category": article.category,
                        "tags": article.tags
                    },
                    "generated_at": datetime.now().isoformat(),
                    "language": article.language
                }
            }
            
            return processed_pair
            
        except Exception as e:
            logger.warning(f"Failed to process Q&A pair: {e}")
            return None
    
    async def _store_qa_pairs(self, qa_pairs: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Store Q&A pairs in the knowledge base (Qdrant)"""
        try:
            stored_count = 0
            
            for qa_pair in qa_pairs:
                try:
                    # Generate embedding for the question
                    question_embedding = await embedding_service.generate_embedding(qa_pair["question"])
                    if not question_embedding:
                        continue
                    
                    # Store in Qdrant
                    success = await qdrant_service.store_qa_embedding(
                        qa_id=qa_pair["id"],
                        question=qa_pair["question"],
                        answer=qa_pair["answer"],
                        embedding=question_embedding,
                        metadata=qa_pair["metadata"]
                    )
                    
                    if success:
                        stored_count += 1
                        
                except Exception as e:
                    logger.warning(f"Failed to store Q&A pair {qa_pair.get('id')}: {e}")
                    continue
            
            return {
                "status": "success",
                "stored_count": stored_count,
                "total_pairs": len(qa_pairs)
            }
            
        except Exception as e:
            logger.error(f"Failed to store Q&A pairs: {e}")
            return {
                "status": "error",
                "error": str(e),
                "stored_count": 0
            }
    
    async def get_news_knowledge_stats(self) -> Dict[str, Any]:
        """Get statistics about news knowledge"""
        try:
            # Get Qdrant stats for news category
            qdrant_stats = await qdrant_service.get_collection_stats()
            
            # Get scraping stats
            scraping_stats = await web_scraping_service.get_scraping_stats()
            
            return {
                "last_update": self.last_update_time.isoformat() if self.last_update_time else None,
                "update_interval_hours": self.update_interval_hours,
                "qdrant_stats": qdrant_stats,
                "scraping_stats": scraping_stats,
                "available_sources": list(web_scraping_service.news_sources.keys())
            }
            
        except Exception as e:
            logger.error(f"Failed to get news knowledge stats: {e}")
            return {"error": str(e)}
    
    async def search_news_qa(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Search for Q&A pairs in news knowledge"""
        try:
            # Generate embedding for the query
            query_embedding = await embedding_service.generate_embedding(query)
            if not query_embedding:
                return []
            
            # Search in Qdrant
            results = await qdrant_service.search_similar_questions(
                query_embedding=query_embedding,
                limit=limit,
                score_threshold=0.7
            )
            
            # Filter for news-related results
            news_results = []
            for result in results:
                metadata = result.get("metadata", {})
                if metadata.get("category") == "news" or "news_" in result.get("source", ""):
                    news_results.append(result)
            
            return news_results
            
        except Exception as e:
            logger.error(f"Failed to search news Q&A: {e}")
            return []
    
    async def clear_old_news(self, days_old: int = 30) -> Dict[str, Any]:
        """Clear old news articles from the knowledge base"""
        try:
            cutoff_date = datetime.now() - timedelta(days=days_old)
            
            # This would require implementing a method in Qdrant service to delete old entries
            # For now, we'll just log the intention
            logger.info(f"Would clear news articles older than {cutoff_date.isoformat()}")
            
            return {
                "status": "success",
                "message": f"Would clear news older than {days_old} days",
                "cutoff_date": cutoff_date.isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to clear old news: {e}")
            return {"status": "error", "error": str(e)}

# Global news integration service instance
news_integration_service = NewsIntegrationService()
