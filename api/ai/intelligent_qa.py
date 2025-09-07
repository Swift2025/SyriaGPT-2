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
    include_health: bool = Query(False, description="Include system health information in response"),
    include_quota: bool = Query(False, description="Include quota status in response"),
    include_data_stats: bool = Query(False, description="Include knowledge base statistics in response"),
    augment_variants: bool = Query(False, description="Generate question variants for this Q&A pair"),
    current_user: User = Depends(get_current_user),
):
    """
    🤖 Intelligent Q&A Endpoint
    
    Main endpoint for asking questions with optional additional functionality:
    - Core Q&A processing
    - System health check (if include_health=true)
    - Quota status (if include_quota=true) 
    - Knowledge base statistics (if include_data_stats=true)
    - Question variant generation (if augment_variants=true)
    """
    log_function_entry(
        logger,
        "ask_intelligent_question",
        question_length=len(question),
        user_email=current_user.email,
        user_id=str(current_user.id),
        include_health=include_health,
        include_quota=include_quota,
        include_data_stats=include_data_stats,
        augment_variants=augment_variants,
    )
    start_time = time.time()

    try:
        # Process the main question
        result = await intelligent_qa_service.process_question(
            question=question,
            user_id=str(current_user.id),
        )

        # Add additional information if requested
        additional_data = {}
        
        if include_health:
            try:
                # Check if the service has the method before calling it
                if hasattr(intelligent_qa_service, 'get_system_health'):
                    health_status = await intelligent_qa_service.get_system_health()
                    components = ["qdrant", "embedding", "gemini", "web_scraping"]
                    healthy_components = sum(
                        1 for comp in components 
                        if health_status.get("components", {}).get(comp, {}).get("status") == "healthy"
                    )
                    overall_status = "healthy" if healthy_components == len(components) else "unhealthy"
                    
                    additional_data["health"] = {
                        "status": overall_status,
                        "components": health_status.get("components", {}),
                        "healthy_components": f"{healthy_components}/{len(components)}",
                        "initialized": health_status.get("initialized", False)
                    }
                else:
                    additional_data["health"] = {"status": "not_available", "message": "Health check not implemented"}
            except Exception as e:
                logger.warning("Failed to get health status: %s", str(e))
                additional_data["health"] = {"status": "error", "error": str(e)}
        
        if include_quota:
            try:
                # Check if the service has the method before calling it
                if hasattr(intelligent_qa_service, 'check_gemini_quota'):
                    quota_status = await intelligent_qa_service.check_gemini_quota()
                    additional_data["quota"] = {
                        "gemini": quota_status,
                        "timestamp": datetime.datetime.now().isoformat()
                    }
                else:
                    additional_data["quota"] = {"status": "not_available", "message": "Quota check not implemented"}
            except Exception as e:
                logger.warning("Failed to get quota status: %s", str(e))
                additional_data["quota"] = {"status": "error", "error": str(e)}
        
        if include_data_stats:
            try:
                from services.ai.data_integration_service import data_integration_service
                stats = await data_integration_service.get_knowledge_base_stats()
                additional_data["data_stats"] = stats
            except Exception as e:
                logger.warning("Failed to get data stats: %s", str(e))
                additional_data["data_stats"] = {"status": "error", "error": str(e)}
        
        if augment_variants and result.get("answer"):
            try:
                # Check if the service has the method before calling it
                if hasattr(intelligent_qa_service, 'augment_question_variants'):
                    variants = await intelligent_qa_service.augment_question_variants(
                        question=question.strip(),
                        answer=result.get("answer", "").strip(),
                        user_id=str(current_user.id)
                    )
                    additional_data["variants"] = {
                        "original_question": question,
                        "variants": variants,
                        "count": len(variants)
                    }
                else:
                    additional_data["variants"] = {"status": "not_available", "message": "Variant generation not implemented"}
            except Exception as e:
                logger.warning("Failed to generate variants: %s", str(e))
                additional_data["variants"] = {"status": "error", "error": str(e)}
        
        # Merge additional data into result
        if additional_data:
            result["additional_data"] = additional_data

        duration = time.time() - start_time
        log_function_exit(logger, "ask_intelligent_question", duration=duration)
        return result

    except Exception as e:
        duration = time.time() - start_time
        log_error_with_context(logger, e, "ask_intelligent_question", duration=duration)
        logger.error("Error in ask_intelligent_question: %s", str(e))
        log_function_exit(logger, "ask_intelligent_question", duration=duration)
        raise HTTPException(status_code=500, detail="Internal server error") from e




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