"""
SyriaGPT - FastAPI-based AI Chatbot System
Main application entry point with comprehensive features.
"""

import asyncio
import logging
import os
import sys
from contextlib import asynccontextmanager
from typing import Dict, Any

import uvicorn
from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

# Add project root to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config.config_loader import ConfigLoader
from config.logging_config import setup_logging
from services.database.database import DatabaseManager
from services.database.health_check import HealthChecker
from api.authentication.routes import auth_router
from api.session.routes import session_router
from api.smtp.routes import smtp_router
from api.user_management.routes import user_router
from api.ai.intelligent_qa import intelligent_qa_router
from api.ai.chat_management import chat_router

# Initialize configuration
config = ConfigLoader()

# Setup logging
logger = setup_logging(config)

# Initialize rate limiter
limiter = Limiter(key_func=get_remote_address)

# Global variables for services
db_manager: DatabaseManager = None
health_checker: HealthChecker = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager for startup and shutdown events."""
    global db_manager, health_checker
    
    logger.info("🚀 Starting SyriaGPT application...")
    
    try:
        # Initialize database manager
        db_manager = DatabaseManager(config)
        await db_manager.initialize()
        logger.info("✅ Database manager initialized")
        
        # Initialize health checker
        health_checker = HealthChecker(db_manager, config)
        await health_checker.initialize()
        logger.info("✅ Health checker initialized")
        
        # Initialize AI services
        from services.ai.gemini_service import gemini_service
        from services.ai.qdrant_service import qdrant_service
        from services.ai.embedding_service import embedding_service
        
        # Initialize services
        await gemini_service.initialize()
        await qdrant_service.initialize()
        await embedding_service.initialize()
        
        logger.info("✅ AI services initialized")
        
        # Store services in app state
        app.state.db_manager = db_manager
        app.state.health_checker = health_checker
        app.state.gemini_service = gemini_service
        app.state.qdrant_service = qdrant_service
        app.state.embedding_service = embedding_service
        
        logger.info("🎉 SyriaGPT application started successfully!")
        
    except Exception as e:
        logger.error(f"❌ Failed to initialize application: {e}")
        raise
    
    yield
    
    # Shutdown
    logger.info("🛑 Shutting down SyriaGPT application...")
    
    if db_manager:
        await db_manager.close()
        logger.info("✅ Database connections closed")
    
    logger.info("👋 SyriaGPT application shutdown complete")


# Create FastAPI application
app = FastAPI(
    title="SyriaGPT - AI Chatbot System",
    description="""
    ## SyriaGPT - Intelligent Q&A System for Syria
    
    A sophisticated FastAPI-based AI chatbot system that provides intelligent Q&A capabilities about Syria.
    
    ### Features:
    - 🤖 **AI Integration**: Google Gemini AI for intelligent responses
    - 🔐 **Authentication**: JWT-based auth with OAuth (Google), 2FA, email verification
    - 🔍 **Vector Search**: Qdrant vector database for semantic search
    - 💬 **Chat Management**: Persistent chat sessions with message history
    - 📧 **Email System**: Dynamic SMTP configuration with multiple providers
    - 🗄️ **Database**: PostgreSQL with Alembic migrations
    - 📊 **Logging**: Comprehensive structured logging system
    - 🐳 **Docker Support**: Full containerization with docker-compose
    
    ### Authentication:
    Most endpoints require authentication. Use the `/auth/login` endpoint to get a JWT token,
    then include it in the Authorization header: `Bearer <your-token>`
    """,
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan
)

# Add rate limiting middleware
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

# CORS middleware
cors_origins = config.get("CORS_ORIGINS", "").split(",") if config.get("CORS_ORIGINS") else []
cors_allow_all = str(config.get("CORS_ALLOW_ALL", "false")).lower() == "true"

if cors_allow_all:
    cors_origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Trusted host middleware
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["*"] if str(config.get("DOCKER_ENV", "false")).lower() == "true" else ["localhost", "127.0.0.1"]
)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all HTTP requests."""
    start_time = asyncio.get_event_loop().time()
    
    # Log request
    logger.info(f"📥 {request.method} {request.url.path} - {request.client.host if request.client else 'unknown'}")
    
    # Process request
    response = await call_next(request)
    
    # Log response
    process_time = asyncio.get_event_loop().time() - start_time
    logger.info(f"📤 {request.method} {request.url.path} - {response.status_code} - {process_time:.3f}s")
    
    return response


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler for unhandled errors."""
    logger.error(f"💥 Unhandled exception in {request.method} {request.url.path}: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "message": "An unexpected error occurred. Please try again later.",
            "detail": str(exc) if config.get("LOG_LEVEL") == "DEBUG" else None
        }
    )


# Health check endpoints
@app.get("/health", tags=["Health"])
async def health_check():
    """Basic health check endpoint."""
    return {
        "status": "healthy",
        "service": "SyriaGPT",
        "version": "2.0.0"
    }


@app.get("/health/detailed", tags=["Health"])
async def detailed_health_check():
    """Detailed health check with service status."""
    if not health_checker:
        raise HTTPException(status_code=503, detail="Health checker not initialized")
    
    health_status = await health_checker.check_all_services()
    return health_status


# Include routers
app.include_router(auth_router, prefix="/auth", tags=["Authentication"])
app.include_router(session_router, prefix="/session", tags=["Session Management"])
app.include_router(smtp_router, prefix="/smtp", tags=["SMTP Configuration"])
app.include_router(user_router, prefix="/user", tags=["User Management"])
app.include_router(intelligent_qa_router, prefix="/intelligent-qa", tags=["Intelligent Q&A"])
app.include_router(chat_router, prefix="/chat", tags=["Chat Management"])


# Root endpoint
@app.get("/", tags=["General"])
async def root():
    """Root endpoint with API information."""
    return {
        "message": "Welcome to SyriaGPT - AI Chatbot System",
        "version": "2.0.0",
        "docs": "/docs",
        "health": "/health",
        "features": [
            "AI-powered Q&A about Syria",
            "JWT Authentication with OAuth",
            "Vector search with Qdrant",
            "Chat session management",
            "Dynamic email configuration",
            "Comprehensive logging"
        ]
    }


if __name__ == "__main__":
    # Get configuration
    host = config.get("HOST", "0.0.0.0")
    port = int(config.get("PORT", "9000"))
    reload = str(config.get("RELOAD", "false")).lower() == "true"
    log_level = str(config.get("LOG_LEVEL", "info")).lower()
    
    logger.info(f"🌐 Starting server on {host}:{port}")
    logger.info(f"📚 API documentation available at http://{host}:{port}/docs")
    
    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        reload=reload,
        log_level=log_level,
        access_log=True
    )
