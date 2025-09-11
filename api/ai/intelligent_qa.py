from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List
import time
import datetime

from services.ai.intelligent_qa_service import intelligent_qa_service
from services.dependencies import get_current_user
from models.domain.user import User
from config.logging_config import get_logger, log_function_entry, log_function_exit, log_performance, log_error_with_context

logger = get_logger(__name__)
router = APIRouter(prefix="/intelligent-qa", tags=["Intelligent Q&A"])


@router.post("/ask")
async def ask_intelligent_question(
    question: str = Query(..., description="The question to ask"),
    current_user: User = Depends(get_current_user),
):
    try:
        result = await intelligent_qa_service.process_question(
            question=question,
            user_id=str(current_user.id),
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))



@router.post("/scrape-news")
async def scrape_news_sources(
    sources: List[str] = Query(None, description="Specific sources to scrape (sana, halab_today, syria_tv, government)"),
    max_articles: int = Query(50, description="Maximum articles per source"),
    update_knowledge_base: bool = Query(False, description="Update knowledge base with scraped content"),
    force_update: bool = Query(False, description="Force update even if not due"),
    include_stats: bool = Query(False, description="Include news knowledge statistics in response"),
    include_status: bool = Query(False, description="Include web scraping service status in response"),
    current_user: User = Depends(get_current_user)
):
    """
    📰 News Scraping and Management Endpoint
    
    Comprehensive news endpoint that can:
    - Scrape news from Syrian sources
    - Update knowledge base with scraped content (if update_knowledge_base=true)
    - Include news statistics (if include_stats=true)
    - Include service status (if include_status=true)
    - Force update knowledge base (if force_update=true)
    """
    log_function_entry(logger, "scrape_news_sources", 
                      sources=sources, 
                      max_articles=max_articles, 
                      update_knowledge_base=update_knowledge_base,
                      force_update=force_update,
                      include_stats=include_stats,
                      include_status=include_status,
                      user_email=current_user.email)
    start_time = time.time()
    
    try:
        from services.ai.web_scraping_service import web_scraping_service
        
        # Initialize web scraping service if needed
        if not web_scraping_service.session:
            await web_scraping_service.initialize()
        
        # Scrape news sources
        scrape_result = await web_scraping_service.scrape_news_sources(
            sources=sources,
            max_articles=max_articles
        )
        
        response_data = {
            "scraping": scrape_result,
            "articles_scraped": len(scrape_result.get("articles", [])),
            "sources_processed": len(scrape_result.get("sources", []))
        }
        
        # Update knowledge base if requested
        if update_knowledge_base:
            try:
                if hasattr(intelligent_qa_service, 'update_news_knowledge'):
                    knowledge_result = await intelligent_qa_service.update_news_knowledge(force_update=force_update)
                    response_data["knowledge_update"] = knowledge_result
                else:
                    response_data["knowledge_update"] = {"status": "not_available", "message": "Knowledge update not implemented"}
            except Exception as e:
                logger.warning("Failed to update knowledge base: %s", str(e))
                response_data["knowledge_update"] = {"status": "error", "error": str(e)}
        
        # Include news statistics if requested
        if include_stats:
            try:
                if hasattr(intelligent_qa_service, 'get_news_knowledge_stats'):
                    stats = await intelligent_qa_service.get_news_knowledge_stats()
                    response_data["news_stats"] = stats
                else:
                    response_data["news_stats"] = {"status": "not_available", "message": "News stats not implemented"}
            except Exception as e:
                logger.warning("Failed to get news stats: %s", str(e))
                response_data["news_stats"] = {"status": "error", "error": str(e)}
        
        # Include service status if requested
        if include_status:
            try:
                # Check if the service has the required methods
                if hasattr(web_scraping_service, 'fetch_fresh_content') and hasattr(web_scraping_service, 'sources'):
                    recent_content = await web_scraping_service.fetch_fresh_content(max_articles=5)
                    response_data["service_status"] = {
                        "status": "active",
                        "recent_articles_count": len(recent_content),
                        "sources": list(web_scraping_service.sources.keys()),
                        "last_fetch": "recent"
                    }
                else:
                    response_data["service_status"] = {"status": "not_available", "message": "Service status not implemented"}
            except Exception as e:
                logger.warning("Failed to get service status: %s", str(e))
                response_data["service_status"] = {"status": "error", "error": str(e)}
        
        response = {
            "status": "success",
            "data": response_data,
            "message": "News scraping completed successfully"
        }
        
        duration = time.time() - start_time
        log_performance(logger, "news sources scraping", duration, 
                       sources_count=len(sources) if sources else 0, 
                       max_articles=max_articles, 
                       update_knowledge_base=update_knowledge_base,
                       user_email=current_user.email)
        log_function_exit(logger, "scrape_news_sources", result=response, duration=duration)
        
        return response
        
    except Exception as e:
        duration = time.time() - start_time
        log_error_with_context(logger, e, "scrape_news_sources", 
                              sources=sources, 
                              max_articles=max_articles, 
                              update_knowledge_base=update_knowledge_base,
                              user_email=current_user.email, 
                              duration=duration)
        logger.error("News scraping failed: %s", str(e))
        log_function_exit(logger, "scrape_news_sources", duration=duration)
        
        return {
            "status": "error",
            "error": str(e),
            "data": {}
        }


# Export the router
intelligent_qa_router = router