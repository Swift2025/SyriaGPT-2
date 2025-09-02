from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import Optional, List
import logging
import time

from services.ai.intelligent_qa_service import intelligent_qa_service
from models.schemas.request_models import QuestionCreateRequest
from models.schemas.response_models import GeneralResponse
from services.dependencies import get_current_user
from models.domain.user import User
from config.logging_config import get_logger, log_function_entry, log_function_exit, log_performance, log_error_with_context

logger = get_logger(__name__)
router = APIRouter(prefix="/intelligent-qa", tags=["Intelligent Q&A"])


@router.post("/ask")
async def ask_intelligent_question(
    question: str = Query(..., description="The question to ask"),
    user_id: Optional[str] = Query(None, description="Optional user ID"),
    context: Optional[str] = Query(None, description="Optional additional context"),
    language: str = Query("auto", description="Preferred response language (en, ar, auto)"),
    current_user: User = Depends(get_current_user)
):
    log_function_entry(logger, "ask_intelligent_question", 
                      question_length=len(question), 
                      user_email=current_user.email, 
                      user_id=str(current_user.id),
                      has_context=bool(context), 
                      language=language)
    start_time = time.time()
    
    """
    🤖 Enhanced Intelligent Q&A Endpoint - Complete Processing Pipeline
    
    Implements the enhanced processing flow:
    1. Generate embedding using latest GenAI
    2. Semantic search in Qdrant
    3. If high similarity found -> return stored answer from PostgreSQL
    4. If no match -> fetch fresh content from web scraping
    5. Generate new answer with Gemini + web content
    6. Store in both Qdrant and PostgreSQL
    7. Generate question variants and store them
    
    Returns:
    - answer: The response to the question
    - confidence: Confidence score (0.0 to 1.0)
    - source: Where the answer came from (vector_search, gemini_api)
    - processing_info: Detailed processing metadata
    """
    try:
        logger.debug(f"🔍 Enhanced Intelligent Q&A request received - Question: '{question[:50]}...', User: {current_user.email}, Language: {language}")
        
        if not question or not question.strip():
            logger.warning("❌ Empty question received in intelligent Q&A request")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Question cannot be empty"
            )
        
        logger.info(f"🔧 Processing enhanced intelligent Q&A request: '{question[:100]}...'")
        
        # Use current user's ID if not provided
        if not user_id:
            user_id = str(current_user.id)
            logger.debug(f"🔧 Using current user ID: {user_id}")
        
        logger.debug("🚀 Starting enhanced intelligent Q&A processing pipeline")
        # Process through the enhanced intelligent pipeline
        result = await intelligent_qa_service.process_question(
            question=question.strip(),
            user_id=user_id,
            context=context,
            language=language
        )
        logger.debug(f"✅ Enhanced intelligent Q&A processing completed with status: {result.get('status', 'unknown')}")
        
        if result.get("status") == "error":
            error_reason = result.get("reason", "unknown_error")
            error_detail = result.get("error", "Unknown processing error")
            
            logger.error(f"❌ Enhanced intelligent Q&A processing failed: {error_reason} - {error_detail}")
            
            # Map error reasons to appropriate HTTP status codes
            status_code_mapping = {
                "embedding_failure": status.HTTP_503_SERVICE_UNAVAILABLE,
                "generation_failure": status.HTTP_503_SERVICE_UNAVAILABLE,
                "cache_failure": status.HTTP_503_SERVICE_UNAVAILABLE,
                "vector_search_failure": status.HTTP_503_SERVICE_UNAVAILABLE,
                "storage_failure": status.HTTP_503_SERVICE_UNAVAILABLE,
                "validation_error": status.HTTP_400_BAD_REQUEST,
                "rate_limit_exceeded": status.HTTP_429_TOO_MANY_REQUESTS,
                "authentication_error": status.HTTP_401_UNAUTHORIZED,
                "authorization_error": status.HTTP_403_FORBIDDEN,
                "resource_not_found": status.HTTP_404_NOT_FOUND,
                "service_unavailable": status.HTTP_503_SERVICE_UNAVAILABLE,
                "internal_error": status.HTTP_500_INTERNAL_SERVER_ERROR
            }
            
            status_code = status_code_mapping.get(error_reason, status.HTTP_500_INTERNAL_SERVER_ERROR)
            
            # Sanitize error detail to avoid exposing internal information
            if status_code == status.HTTP_500_INTERNAL_SERVER_ERROR:
                error_detail = "An internal server error occurred. Please try again later."
            
            duration = time.time() - start_time
            log_performance(logger, "Enhanced intelligent Q&A request (error)", duration, error_reason=error_reason)
            log_function_exit(logger, "ask_intelligent_question", duration=duration)
            
            raise HTTPException(
                status_code=status_code,
                detail=error_detail
            )
        
        response = {
            "status": "success",
            "data": result,
            "message": "Question processed successfully"
        }
        
        duration = time.time() - start_time
        log_performance(logger, "Enhanced intelligent Q&A request (success)", duration, 
                       question_length=len(question), user_email=current_user.email)
        log_function_exit(logger, "ask_intelligent_question", result=response, duration=duration)
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Enhanced intelligent Q&A processing failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process question: {str(e)}"
        )


@router.get("/similar-questions")
async def find_similar_questions(
    question: str = Query(..., description="The question to find similar ones for"),
    limit: int = Query(5, description="Maximum number of similar questions to return"),
    current_user: User = Depends(get_current_user)
):
    """
    🔍 Find Similar Questions
    
    Find similar questions using semantic search in the vector database.
    Returns the top 5 most similar questions from Qdrant based on semantic search.
    """
    log_function_entry(logger, "find_similar_questions", 
                      question_length=len(question), 
                      user_email=current_user.email,
                      limit=limit)
    start_time = time.time()
    
    try:
        if not question or not question.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Question cannot be empty"
            )
        
        logger.info(f"🔍 Finding similar questions for: '{question[:100]}...'")
        
        # Find similar questions using semantic search
        similar_questions = await intelligent_qa_service.find_similar_questions(
            question=question.strip(),
            limit=limit,
            user_id=str(current_user.id)
        )
        
        response = {
            "status": "success",
            "data": {
                "similar_questions": similar_questions,
                "count": len(similar_questions),
                "original_question": question
            },
            "message": f"Found {len(similar_questions)} similar questions"
        }
        
        duration = time.time() - start_time
        log_performance(logger, "similar questions search", duration, 
                       question_length=len(question), user_email=current_user.email)
        log_function_exit(logger, "find_similar_questions", result=response, duration=duration)
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        duration = time.time() - start_time
        log_error_with_context(logger, e, "find_similar_questions", 
                              question=question, user_email=current_user.email, duration=duration)
        logger.error(f"Failed to find similar questions: {e}")
        log_function_exit(logger, "find_similar_questions", duration=duration)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to find similar questions: {str(e)}"
        )


@router.post("/augment-variants")
async def augment_question_variants(
    question: str = Query(..., description="The original question"),
    answer: str = Query(..., description="The answer to the question"),
    current_user: User = Depends(get_current_user)
):
    """
    🔄 Augment Question Variants
    
    Generate and store question variants for a validated Q&A pair.
    Uses Gemini to generate 3-5 variants of the question and stores them in Qdrant.
    """
    log_function_entry(logger, "augment_question_variants", 
                      question_length=len(question), 
                      answer_length=len(answer),
                      user_email=current_user.email)
    start_time = time.time()
    
    try:
        if not question or not question.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Question cannot be empty"
            )
        
        if not answer or not answer.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Answer cannot be empty"
            )
        
        logger.info(f"🔄 Augmenting question variants for: '{question[:100]}...'")
        
        # Generate and store question variants
        variants = await intelligent_qa_service.augment_question_variants(
            question=question.strip(),
            answer=answer.strip(),
            user_id=str(current_user.id)
        )
        
        response = {
            "status": "success",
            "data": {
                "original_question": question,
                "variants": variants,
                "count": len(variants)
            },
            "message": f"Generated {len(variants)} question variants"
        }
        
        duration = time.time() - start_time
        log_performance(logger, "question variants augmentation", duration, 
                       question_length=len(question), user_email=current_user.email)
        log_function_exit(logger, "augment_question_variants", result=response, duration=duration)
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        duration = time.time() - start_time
        log_error_with_context(logger, e, "augment_question_variants", 
                              question=question, user_email=current_user.email, duration=duration)
        logger.error(f"Failed to augment question variants: {e}")
        log_function_exit(logger, "augment_question_variants", duration=duration)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to augment question variants: {str(e)}"
        )


@router.get("/quota-status")
async def get_quota_status(current_user: User = Depends(get_current_user)):
    """
    📊 Check API Quota Status
    
    Returns the current quota status for all AI services.
    """
    log_function_entry(logger, "get_quota_status", user_email=current_user.email)
    start_time = time.time()
    
    try:
        quota_status = await intelligent_qa_service.check_gemini_quota()
        
        response = {
            "status": "success",
            "data": {
                "gemini": quota_status,
                "timestamp": datetime.now().isoformat(),
                "user_id": str(current_user.id)
            },
            "message": f"Quota status retrieved successfully"
        }
        
        duration = time.time() - start_time
        log_performance(logger, "quota status check", duration, user_email=current_user.email)
        log_function_exit(logger, "get_quota_status", result=response, duration=duration)
        
        return response
        
    except Exception as e:
        duration = time.time() - start_time
        log_error_with_context(logger, e, "get_quota_status", user_email=current_user.email, duration=duration)
        logger.error(f"Quota status check failed: {e}")
        
        response = {
            "status": "error",
            "error": str(e),
            "data": {
                "gemini": {"status": "unknown", "error": str(e)},
                "timestamp": datetime.now().isoformat()
            }
        }
        
        log_function_exit(logger, "get_quota_status", result=response, duration=duration)
        return response


@router.get("/health")
async def get_ai_health(current_user: User = Depends(get_current_user)):
    """
    🔍 Enhanced System Health Check
    
    Returns the health status of all enhanced Q&A system components:
    - Qdrant (vector database)
    - Gemini API (AI service)
    - Embedding service (vector generation)
    - Web scraping service
    """
    log_function_entry(logger, "get_ai_health", user_email=current_user.email)
    start_time = time.time()
    
    try:
        health_status = await intelligent_qa_service.get_system_health()
        
        # Determine overall health
        components = ["qdrant", "embedding", "gemini", "web_scraping"]
        healthy_components = sum(
            1 for comp in components 
            if health_status.get("components", {}).get(comp, {}).get("status") == "healthy"
        )
        
        overall_status = "healthy" if healthy_components == len(components) else "unhealthy"
        
        response = {
            "status": overall_status,
            "components": health_status.get("components", {}),
            "healthy_components": f"{healthy_components}/{len(components)}",
            "initialized": health_status.get("initialized", False),
            "recommendations": _get_health_recommendations(health_status.get("components", {}))
        }
        
        duration = time.time() - start_time
        log_performance(logger, "Enhanced AI health check", duration, healthy_components=healthy_components)
        log_function_exit(logger, "get_ai_health", result=response, duration=duration)
        
        return response
        
    except Exception as e:
        duration = time.time() - start_time
        log_error_with_context(logger, e, "get_ai_health", user_email=current_user.email, duration=duration)
        logger.error(f"Enhanced health check failed: {e}")
        
        response = {
            "status": "error",
            "error": str(e),
            "components": {},
            "healthy_components": "0/4"
        }
        
        log_function_exit(logger, "get_ai_health", result=response, duration=duration)
        return response


def _get_health_recommendations(health_status: dict) -> List[str]:
    """Generate health recommendations based on system status"""
    recommendations = []
    
    if not health_status.get("qdrant", {}).get("status") == "healthy":
        recommendations.append("Qdrant vector database is not healthy. Check Qdrant service and configuration.")
    
    if not health_status.get("embedding", {}).get("status") == "healthy":
        recommendations.append("Embedding service is not healthy. Check GenAI API key and configuration.")
    
    if not health_status.get("gemini", {}).get("status") == "healthy":
        recommendations.append("Gemini API is not healthy. Set GOOGLE_API_KEY environment variable.")
    
    if not health_status.get("web_scraping", {}).get("status") == "healthy":
        recommendations.append("Web scraping service is not healthy. Check network connectivity.")
    
    if not recommendations:
        recommendations.append("All systems are healthy and operating normally.")
    
    return recommendations


@router.post("/initialize")
async def initialize_system():
    """
    🚀 Initialize Enhanced Syria GPT Q&A System
    
    Initializes the enhanced Q&A system with web scraping integration.
    This should be called during application startup or when the system needs to be reinitialized.
    """
    log_function_entry(logger, "initialize_system")
    start_time = time.time()
    
    try:
        logger.info("Initializing enhanced Syria GPT Q&A system...")
        
        result = await intelligent_qa_service.initialize_system()
        
        if result.get("status") == "success":
            response = {
                "status": "success",
                "data": result,
                "message": "Enhanced Syria GPT Q&A system initialized successfully"
            }
            
            duration = time.time() - start_time
            log_performance(logger, "Enhanced system initialization", duration)
            log_function_exit(logger, "initialize_system", result=response, duration=duration)
            
            return response
        else:
            duration = time.time() - start_time
            log_function_exit(logger, "initialize_system", duration=duration)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result.get("error", "Initialization failed")
            )
        
    except HTTPException:
        duration = time.time() - start_time
        log_function_exit(logger, "initialize_system", duration=duration)
        raise
    except Exception as e:
        duration = time.time() - start_time
        log_error_with_context(logger, e, "initialize_system", duration=duration)
        logger.error(f"Enhanced system initialization failed: {e}")
        log_function_exit(logger, "initialize_system", duration=duration)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to initialize enhanced system: {str(e)}"
        )


@router.get("/web-scraping-status")
async def get_web_scraping_status(current_user: User = Depends(get_current_user)):
    """
    🌐 Web Scraping Status
    
    Get the status of the web scraping service and recent content.
    """
    log_function_entry(logger, "get_web_scraping_status", user_email=current_user.email)
    start_time = time.time()
    
    try:
        from services.ai.web_scraping_service import web_scraping_service
        
        # Get recent content (limited to avoid performance issues)
        recent_content = await web_scraping_service.fetch_fresh_content(max_articles=5)
        
        response = {
            "status": "success",
            "data": {
                "service_status": "active",
                "recent_articles_count": len(recent_content),
                "sources": list(web_scraping_service.sources.keys()),
                "last_fetch": "recent"
            },
            "message": f"Web scraping service is active with {len(recent_content)} recent articles"
        }
        
        duration = time.time() - start_time
        log_performance(logger, "web scraping status check", duration, user_email=current_user.email)
        log_function_exit(logger, "get_web_scraping_status", result=response, duration=duration)
        
        return response
        
    except Exception as e:
        duration = time.time() - start_time
        log_error_with_context(logger, e, "get_web_scraping_status", user_email=current_user.email, duration=duration)
        logger.error(f"Web scraping status check failed: {e}")
        
        response = {
            "status": "error",
            "error": str(e),
            "data": {
                "service_status": "inactive",
                "recent_articles_count": 0,
                "sources": []
            }
        }
        
        log_function_exit(logger, "get_web_scraping_status", result=response, duration=duration)
        return response


@router.post("/update-news")
async def update_news_knowledge(
    force_update: bool = Query(False, description="Force update even if not due"),
    current_user: User = Depends(get_current_user)
):
    """
    📰 Update News Knowledge Base
    
    Scrapes fresh news from Syrian sources and integrates them into the knowledge base.
    This endpoint:
    1. Scrapes news from SANA, Halab Today, Syria TV, and government websites
    2. Converts articles to Q&A pairs using Gemini
    3. Stores them in Qdrant for semantic search
    4. Updates every 6 hours by default
    """
    log_function_entry(logger, "update_news_knowledge", 
                      force_update=force_update, 
                      user_email=current_user.email)
    start_time = time.time()
    
    try:
        result = await intelligent_qa_service.update_news_knowledge(force_update=force_update)
        
        if result.get("status") == "success":
            response = {
                "status": "success",
                "data": result,
                "message": "News knowledge updated successfully"
            }
        elif result.get("status") == "skipped":
            response = {
                "status": "skipped",
                "data": result,
                "message": "No update needed"
            }
        else:
            response = {
                "status": "error",
                "error": result.get("error", "Unknown error"),
                "data": result
            }
        
        duration = time.time() - start_time
        log_performance(logger, "news knowledge update", duration, 
                       force_update=force_update, 
                       user_email=current_user.email)
        log_function_exit(logger, "update_news_knowledge", result=response, duration=duration)
        
        return response
        
    except Exception as e:
        duration = time.time() - start_time
        log_error_with_context(logger, e, "update_news_knowledge", 
                              force_update=force_update, 
                              user_email=current_user.email, 
                              duration=duration)
        logger.error(f"News knowledge update failed: {e}")
        log_function_exit(logger, "update_news_knowledge", duration=duration)
        
        return {
            "status": "error",
            "error": str(e),
            "data": {}
        }


@router.get("/news-stats")
async def get_news_knowledge_statistics(current_user: User = Depends(get_current_user)):
    """
    📊 News Knowledge Statistics
    
    Returns detailed statistics about the news knowledge base including:
    - Last update time
    - Update interval
    - Scraping statistics
    - Available news sources
    - Qdrant vector database statistics
    """
    log_function_entry(logger, "get_news_knowledge_statistics", user_email=current_user.email)
    start_time = time.time()
    
    try:
        stats = await intelligent_qa_service.get_news_knowledge_stats()
        
        response = {
            "status": "success",
            "data": stats,
            "message": "News knowledge statistics retrieved successfully"
        }
        
        duration = time.time() - start_time
        log_performance(logger, "news knowledge statistics retrieval", duration, 
                       user_email=current_user.email)
        log_function_exit(logger, "get_news_knowledge_statistics", result=response, duration=duration)
        
        return response
        
    except Exception as e:
        duration = time.time() - start_time
        log_error_with_context(logger, e, "get_news_knowledge_statistics", 
                              user_email=current_user.email, 
                              duration=duration)
        logger.error(f"Failed to get news knowledge stats: {e}")
        
        response = {
            "status": "error",
            "error": str(e),
            "data": {}
        }
        
        log_function_exit(logger, "get_news_knowledge_statistics", result=response, duration=duration)
        return response


@router.post("/scrape-news")
async def scrape_news_sources(
    sources: List[str] = Query(None, description="Specific sources to scrape (sana, halab_today, syria_tv, government)"),
    max_articles: int = Query(50, description="Maximum articles per source"),
    current_user: User = Depends(get_current_user)
):
    """
    🔍 Scrape News Sources
    
    Directly scrape news from Syrian sources without converting to Q&A pairs.
    This is useful for testing scraping functionality or getting raw articles.
    """
    log_function_entry(logger, "scrape_news_sources", 
                      sources=sources, 
                      max_articles=max_articles, 
                      user_email=current_user.email)
    start_time = time.time()
    
    try:
        from services.ai.web_scraping_service import web_scraping_service
        
        # Initialize web scraping service if needed
        if not web_scraping_service.session:
            await web_scraping_service.initialize()
        
        result = await web_scraping_service.scrape_news_sources(
            sources=sources,
            max_articles=max_articles
        )
        
        response = {
            "status": "success",
            "data": result,
            "message": "News scraping completed successfully"
        }
        
        duration = time.time() - start_time
        log_performance(logger, "news sources scraping", duration, 
                       sources_count=len(sources) if sources else 0, 
                       max_articles=max_articles, 
                       user_email=current_user.email)
        log_function_exit(logger, "scrape_news_sources", result=response, duration=duration)
        
        return response
        
    except Exception as e:
        duration = time.time() - start_time
        log_error_with_context(logger, e, "scrape_news_sources", 
                              sources=sources, 
                              max_articles=max_articles, 
                              user_email=current_user.email, 
                              duration=duration)
        logger.error(f"News scraping failed: {e}")
        log_function_exit(logger, "scrape_news_sources", duration=duration)
        
        return {
            "status": "error",
            "error": str(e),
            "data": {}
        }


# Export the router
intelligent_qa_router = router