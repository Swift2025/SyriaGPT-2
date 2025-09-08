"""
Intelligent Q&A API routes for SyriaGPT.
"""

import logging
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession

from models.domain.user import User
from models.schemas.request_models import QuestionRequest, QuestionVariantRequest, NewsScrapingRequest
from models.schemas.response_models import QuestionResponse, QuestionVariantResponse, NewsScrapingResponse
from services.database.database import get_db
from services.dependencies import get_current_user
from services.ai.intelligent_qa_service import intelligent_qa_service
from config.config_loader import ConfigLoader

logger = logging.getLogger(__name__)

# Initialize router
intelligent_qa_router = APIRouter()

# Initialize services
config = ConfigLoader()

# Security scheme
security = HTTPBearer()


@intelligent_qa_router.post("/ask", response_model=QuestionResponse, tags=["Intelligent Q&A"])
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


@intelligent_qa_router.post("/scrape-news", response_model=NewsScrapingResponse, tags=["Intelligent Q&A"])
async def scrape_news(
    request: NewsScrapingRequest,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
):
    """Scrape news articles related to Syria."""
    try:
        # Get current user
        user = await get_current_user(credentials, db)
        
        # Mock news articles
        from models.schemas.response_models import NewsArticleResponse
        from datetime import datetime
        
        articles = [
            NewsArticleResponse(
                title="Syria News Update",
                content="This is a sample news article about Syria. In a real implementation, this would be scraped from actual news sources.",
                url="https://example.com/syria-news-1",
                source="Example News",
                published_at=datetime.utcnow(),
                author="News Reporter",
                image_url="https://example.com/image.jpg",
                summary="Summary of the news article about Syria."
            ),
            NewsArticleResponse(
                title="Another Syria News Article",
                content="Another sample news article about Syria with more detailed information.",
                url="https://example.com/syria-news-2",
                source="Another News Source",
                published_at=datetime.utcnow(),
                author="Another Reporter",
                image_url="https://example.com/image2.jpg",
                summary="Another summary of news about Syria."
            )
        ]
        
        # Limit to requested number
        articles = articles[:request.max_articles]
        
        return NewsScrapingResponse(
            status="success",
            message="News articles scraped successfully",
            query=request.query,
            articles=articles,
            total_found=len(articles),
            language=request.language
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Scrape news error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to scrape news articles"
        )
