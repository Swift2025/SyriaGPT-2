from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, HTTPBearer
from fastapi.openapi.utils import get_openapi
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from services.dependencies import limiter, get_current_user
from api.authentication.routes import router as auth_router
from api.questions.questions import router as questions_router
from api.answers.answers import router as answers_router
from api.ai.intelligent_qa import router as intelligent_qa_router
from api.ai.chat_management import router as chat_management_router
from api.smtp.routes import router as smtp_router
from api.user_management.routes import router as user_management_router

from models.domain.user import User
import asyncio
import logging
import os
import time
from functools import wraps

# Initialize verbose logging
from config.logging_config import setup_logging, get_logger, log_function_entry, log_function_exit, log_performance, log_error_with_context
setup_logging()

logger = get_logger(__name__)

# Security schemes for Swagger UI
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")
http_bearer = HTTPBearer()

logger.info("[STARTUP] Initializing Syria GPT FastAPI application...")

app = FastAPI(
    title="Syria GPT API", 
    version="1.0.0",
    description="""
    # Syria GPT API
    
    Intelligent Q&A system for Syria-related questions powered by Google Gemini AI.
    
    ## 🔐 Authentication
    
    This API uses **Bearer token authentication**. Protected endpoints require a valid JWT token.
    
    ### How to Authenticate:
    
    1. **Get a Token**:
       - **Login**: `POST /auth/login` (with email/password)
       - **OAuth**: Use OAuth endpoints for social login
    
    2. **Use in Swagger UI**:
       - Click the **🔒 Authorize** button (top right)
       - Enter: `Bearer YOUR_ACCESS_TOKEN`
       - Click **Authorize**
       - Now you can access protected endpoints!
    
    3. **Verify Authentication**:
       - Use `GET /auth/me` to check if your token is valid
    
    ### 🔑 Token Management:
    - Tokens are automatically stored in browser localStorage
    - Tokens expire after 30 minutes (configurable)
    - Use refresh tokens to get new access tokens
    
    ## Features
    
    - 🔐 **Secure Authentication** with JWT tokens
    - 🤖 **AI-Powered Q&A** using Google Gemini
    - 💬 **AI Chat Management** with persistent conversations and session management
    - 🔍 **Vector Search** with Qdrant
    - 💾 **Redis Caching** for fast responses
    - 🌍 **Multilingual Support** (Arabic & English)
    - 📧 **Email Verification**
    - 🔐 **Two-Factor Authentication**
    - 🔗 **OAuth Social Login** (Google)
    
    ## Quick Start
    
    1. **Register**: `POST /auth/register`
    2. **Login**: `POST /auth/login` 
    3. **Get Token**: Copy the `access_token` from response
    4. **Authorize**: Click Authorize button in Swagger UI
    5. **Ask Questions**: `POST /intelligent-qa/ask`
    6. **Start Chat**: `POST /chat/` to create a new chat session
    7. **Send Messages**: `POST /chat/{chat_id}/messages` to chat with AI
    8. **Manage Sessions**: `GET /chat/sessions/` to view active sessions
    """,
    openapi_tags=[
        {
            "name": "authentication",
            "description": "User authentication and authorization operations"
        },
        {
            "name": "Questions",
            "description": "Question management operations"
        },
        {
            "name": "Answers", 
            "description": "Answer management operations"
        },
        {
            "name": "Intelligent Q&A",
            "description": "AI-powered intelligent Q&A operations"
        },
        {
            "name": "Chat Management",
            "description": "AI chat session management, messaging operations, and user session management"
        },
        {
            "name": "SMTP Configuration",
            "description": "Dynamic SMTP configuration and email provider management"
        }
    ]
)

logger.debug("[CONFIG] Configuring rate limiter and exception handlers...")
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
logger.debug("[CONFIG] Rate limiter and exception handlers configured")

# Configure security schemes for Swagger UI
logger.debug("[CONFIG] Configuring Swagger UI parameters...")
app.swagger_ui_parameters = {
    "defaultModelsExpandDepth": -1,
    "defaultModelExpandDepth": 2,
    "displayRequestDuration": True,
    "docExpansion": "list",
    "filter": True,
    "showExtensions": True,
    "showCommonExtensions": True,
    "syntaxHighlight.theme": "monokai",
    "tryItOutEnabled": True,
    "persistAuthorization": True,
    "requestInterceptor": """
    function(request) {
        // Add Bearer token to Authorization header if available
        const token = localStorage.getItem('swagger_token');
        if (token && !request.headers['Authorization']) {
            request.headers['Authorization'] = 'Bearer ' + token;
        }
        return request;
    }
    """,
    "responseInterceptor": """
    function(response) {
        // Store token from login response
        if (response.url.includes('/auth/login') && response.status === 200) {
            try {
                const data = JSON.parse(response.body);
                if (data.access_token) {
                    localStorage.setItem('swagger_token', data.access_token);
                    console.log('Token stored successfully');
                }
            } catch (e) {
                console.log('Could not parse response body');
            }
        }
        return response;
    }
    """,
    "onComplete": """
    function() {
        // Auto-fill the Authorize dialog with stored token
        const token = localStorage.getItem('swagger_token');
        if (token) {
            const authorizeBtn = document.querySelector('.authorize');
            if (authorizeBtn) {
                authorizeBtn.click();
                setTimeout(() => {
                    const tokenInput = document.querySelector('#swagger-ui input[type="text"]');
                    if (tokenInput) {
                        tokenInput.value = 'Bearer ' + token;
                        const authorizeSubmitBtn = document.querySelector('.authorize button.btn.authorize');
                        if (authorizeSubmitBtn) {
                            authorizeSubmitBtn.click();
                        }
                    }
                }, 100);
            }
        }
    }
    """
}
logger.debug("[CONFIG] Swagger UI parameters configured")

# Include routers
logger.debug("[ROUTER] Including API routers...")
app.include_router(auth_router)
logger.debug("[ROUTER] Auth router included")
app.include_router(questions_router)
logger.debug("[ROUTER] Questions router included")
app.include_router(answers_router)
logger.debug("[ROUTER] Answers router included")
app.include_router(intelligent_qa_router)
logger.debug("[ROUTER] Intelligent Q&A router included")
app.include_router(chat_management_router)
logger.debug("[ROUTER] Chat management router included")
app.include_router(smtp_router)
logger.debug("[ROUTER] SMTP router included")
app.include_router(user_management_router)
logger.debug("[ROUTER] User management router included")

logger.info("[ROUTER] All API routers included successfully")

# Customize OpenAPI schema to include security schemes
def custom_openapi():
    log_function_entry(logger, "custom_openapi")
    start_time = time.time()
    
    try:
        if app.openapi_schema:
            logger.debug("📄 Returning cached OpenAPI schema")
            return app.openapi_schema
        
        logger.debug("🔧 Generating new OpenAPI schema...")
        openapi_schema = get_openapi(
            title=app.title,
            version=app.version,
            description=app.description,
            routes=app.routes,
        )
        
        # Add security schemes
        logger.debug("🔧 Adding security schemes to OpenAPI schema...")
        openapi_schema["components"]["securitySchemes"] = {
            "BearerAuth": {
                "type": "http",
                "scheme": "bearer",
                "bearerFormat": "JWT",
                "description": "Enter your JWT token in the format: Bearer <token>"
            }
        }
        
        # Add security requirements to specific paths that need authentication
        # Public endpoints (no authentication required)
        public_paths = [
            "/",
            "/hello/{name}",
            "/test/health",
            "/auth/login",
            "/auth/register", 
            "/auth/verify-email/{token}",
            "/auth/oauth/providers",
            "/auth/oauth/{provider}/authorize",
            "/auth/oauth/{provider}/callback",
            "/auth/health",
            "/auth/forgot-password",
            "/auth/reset-password",
            "/auth/debug-token",
            "/auth/refresh-oauth/{email}",
            "/smtp/providers",
            "/smtp/providers/{provider}",
            "/smtp/supported-domains",
            "/smtp/health"
        ]
        
        logger.debug(f"🔧 Configuring security for {len(openapi_schema['paths'])} API paths...")
        protected_count = 0
        
        # Add security to protected paths
        for path in openapi_schema["paths"]:
            if path not in public_paths:
                # Add security requirement to all operations in this path
                for operation in openapi_schema["paths"][path]:
                    if operation in ["get", "post", "put", "delete", "patch"]:
                        openapi_schema["paths"][path][operation]["security"] = [
                            {"BearerAuth": []}
                        ]
                        protected_count += 1
        
        logger.debug(f"✅ Security configured for {protected_count} protected endpoints")
        
        app.openapi_schema = openapi_schema
        duration = time.time() - start_time
        log_performance(logger, "OpenAPI schema generation", duration)
        log_function_exit(logger, "custom_openapi", duration=duration)
        return app.openapi_schema
        
    except Exception as e:
        duration = time.time() - start_time
        log_error_with_context(logger, e, "custom_openapi", duration=duration)
        log_function_exit(logger, "custom_openapi", duration=duration)
        raise

app.openapi = custom_openapi

@app.on_event("startup")
async def startup_event():
    """
    Initialize the Syria GPT Q&A system on startup.
    This loads all knowledge data from the data folder into Redis and Qdrant.
    """
    log_function_entry(logger, "startup_event")
    start_time = time.time()
    
    try:
        logger.info("[STARTUP] Starting Syria GPT application...")
        
        # Import here to avoid circular imports
        logger.debug("[IMPORT] Importing intelligent Q&A service...")
        from services.ai.intelligent_qa_service import intelligent_qa_service
        logger.debug("[IMPORT] Intelligent Q&A service imported successfully")
        
        # Initialize the system
        logger.debug("[INIT] Initializing intelligent Q&A system...")
        init_result = await intelligent_qa_service.initialize_system()
        
        if init_result.get("status") == "success":
            duration = time.time() - start_time
            log_performance(logger, "System initialization", duration)
            logger.info("[STARTUP] Syria GPT system initialized successfully")
        else:
            error_msg = init_result.get('error', 'Unknown error')
            logger.error(f"[STARTUP] System initialization failed: {error_msg}")
            log_error_with_context(logger, Exception(error_msg), "startup_event", init_result=init_result)
            
    except Exception as e:
        duration = time.time() - start_time
        log_error_with_context(logger, e, "startup_event", duration=duration)
        logger.error(f"[STARTUP] Startup initialization failed: {e}")
        # Don't fail the startup, just log the error
    
    log_function_exit(logger, "startup_event", duration=time.time() - start_time)

@app.get("/")
def read_root():
    log_function_entry(logger, "read_root")
    start_time = time.time()
    
    try:
        response = {
            "message": "Welcome to Syria GPT!", 
            "version": "1.0.0",
            "ai_provider": "Google Gemini",
            "features": ["Intelligent Q&A", "Vector Search", "Redis Caching", "Multilingual Support"]
        }
        
        duration = time.time() - start_time
        log_performance(logger, "Root endpoint", duration)
        log_function_exit(logger, "read_root", result=response, duration=duration)
        return response
        
    except Exception as e:
        duration = time.time() - start_time
        log_error_with_context(logger, e, "read_root", duration=duration)
        log_function_exit(logger, "read_root", duration=duration)
        raise

@app.get("/hello/{name}")
def say_hello(name: str):
    log_function_entry(logger, "say_hello", name=name)
    start_time = time.time()
    
    try:
        response = {"message": f"Hello, {name}! Welcome to Syria GPT."}
        
        duration = time.time() - start_time
        log_performance(logger, "Hello endpoint", duration, name=name)
        log_function_exit(logger, "say_hello", result=response, duration=duration)
        return response
        
    except Exception as e:
        duration = time.time() - start_time
        log_error_with_context(logger, e, "say_hello", name=name, duration=duration)
        log_function_exit(logger, "say_hello", duration=duration)
        raise

@app.get("/protected/profile", tags=["authentication"])
def get_user_profile(current_user: User = Depends(get_current_user)):
    """
    Get current user profile - Protected endpoint example
    
    This endpoint requires authentication. Use the Authorize button in Swagger UI
    with your Bearer token to access this endpoint.
    """
    log_function_entry(logger, "get_user_profile", user_id=str(current_user.id), user_email=current_user.email)
    start_time = time.time()
    
    try:
        response = {
            "user_id": str(current_user.id),
            "email": current_user.email,
            "full_name": current_user.full_name,
            "is_email_verified": current_user.is_email_verified,
            "two_factor_enabled": current_user.two_factor_enabled,
            "status": current_user.status,
            "created_at": current_user.created_at
        }
        
        duration = time.time() - start_time
        log_performance(logger, "User profile retrieval", duration, user_id=str(current_user.id))
        log_function_exit(logger, "get_user_profile", result=response, duration=duration)
        return response
        
    except Exception as e:
        duration = time.time() - start_time
        log_error_with_context(logger, e, "get_user_profile", user_id=str(current_user.id), duration=duration)
        log_function_exit(logger, "get_user_profile", duration=duration)
        raise

@app.get("/auth/me", tags=["authentication"])
def get_current_user_info(current_user: User = Depends(get_current_user)):
    """
    Get current authenticated user information
    
    This endpoint helps verify that your authentication is working correctly.
    Returns basic user information if the token is valid.
    """
    log_function_entry(logger, "get_current_user_info", user_id=str(current_user.id), user_email=current_user.email)
    start_time = time.time()
    
    try:
        response = {
            "authenticated": True,
            "user_id": str(current_user.id),
            "email": current_user.email,
            "full_name": current_user.full_name,
            "message": "Authentication successful! Your token is valid."
        }
        
        duration = time.time() - start_time
        log_performance(logger, "Current user info retrieval", duration, user_id=str(current_user.id))
        log_function_exit(logger, "get_current_user_info", result=response, duration=duration)
        return response
        
    except Exception as e:
        duration = time.time() - start_time
        log_error_with_context(logger, e, "get_current_user_info", user_id=str(current_user.id), duration=duration)
        log_function_exit(logger, "get_current_user_info", duration=duration)
        raise

@app.post("/auth/debug-token", tags=["authentication"])
def debug_token(request: dict):
    log_function_entry(logger, "debug_token", request_keys=list(request.keys()) if request else [])
    start_time = time.time()
    
    try:
        token = request.get("token")
        if not token:
            logger.warning("[DEBUG] Debug token request received without token")
            response = {"valid": False, "error": "Token is required"}
            duration = time.time() - start_time
            log_performance(logger, "Token debug (no token)", duration)
            log_function_exit(logger, "debug_token", result=response, duration=duration)
            return response
        
        logger.debug("[DEBUG] Debugging token validation...")
        """
        Debug token validation - Check if a token is valid and what user it represents
        
        This endpoint helps troubleshoot authentication issues.
        """
        from services.auth import get_auth_service
        from services.repositories import get_user_repository
        from services.database.database import get_db
        
        auth_service = get_auth_service()
        
        try:
            # Verify token
            logger.debug("[DEBUG] Verifying token with auth service...")
            payload = auth_service.verify_token(token)
            if payload is None:
                logger.warning("[DEBUG] Token verification failed - payload is None")
                response = {
                    "valid": False,
                    "error": "Token verification failed - payload is None"
                }
                duration = time.time() - start_time
                log_performance(logger, "Token debug (verification failed)", duration)
                log_function_exit(logger, "debug_token", result=response, duration=duration)
                return response
            
            email = payload.get("sub")
            if email is None:
                logger.warning("[DEBUG] Token payload missing 'sub' field")
                response = {
                    "valid": False,
                    "error": "Token payload missing 'sub' field",
                    "payload": payload
                }
                duration = time.time() - start_time
                log_performance(logger, "Token debug (missing sub)", duration)
                log_function_exit(logger, "debug_token", result=response, duration=duration)
                return response
            
            # Check if user exists in database
            logger.debug(f"[DEBUG] Checking if user exists in database: {email}")
            db = next(get_db())
            user_repo = get_user_repository()
            user = user_repo.get_user_by_email(db, email)
            
            if user is None:
                logger.warning(f"[DEBUG] User not found in database: {email}")
                response = {
                    "valid": False,
                    "error": f"User not found in database for email: {email}",
                    "token_payload": payload,
                    "suggestion": "User may need to register or login again"
                }
                duration = time.time() - start_time
                log_performance(logger, "Token debug (user not found)", duration)
                log_function_exit(logger, "debug_token", result=response, duration=duration)
                return response
            
            logger.info(f"[DEBUG] Token validation successful for user: {email}")
            response = {
                "valid": True,
                "user": {
                    "id": str(user.id),
                    "email": user.email,
                    "full_name": user.full_name,
                    "is_email_verified": user.is_email_verified
                },
                "token_payload": payload
            }
            
            duration = time.time() - start_time
            log_performance(logger, "Token debug (success)", duration, user_email=email)
            log_function_exit(logger, "debug_token", result=response, duration=duration)
            return response
            
        except Exception as e:
            logger.error(f"[DEBUG] Token validation error: {str(e)}")
            response = {
                "valid": False,
                "error": f"Token validation error: {str(e)}"
            }
            duration = time.time() - start_time
            log_performance(logger, "Token debug (validation error)", duration)
            log_function_exit(logger, "debug_token", result=response, duration=duration)
            return response
            
    except Exception as e:
        duration = time.time() - start_time
        log_error_with_context(logger, e, "debug_token", duration=duration)
        log_function_exit(logger, "debug_token", duration=duration)
        raise

@app.get("/auth/refresh-oauth/{email}", tags=["authentication"])
def get_oauth_refresh_url(email: str):
    """
    Get OAuth refresh URL for a specific user
    
    This endpoint helps users get a fresh token when their current token has expired.
    """
    log_function_entry(logger, "get_oauth_refresh_url", email=email)
    start_time = time.time()
    
    try:
        from services.repositories import get_user_repository
        from services.database.database import get_db
        
        logger.debug(f"[OAUTH] Looking up user for OAuth refresh: {email}")
        db = next(get_db())
        user_repo = get_user_repository()
        user = user_repo.get_user_by_email(db, email)
        
        if user is None:
            logger.warning(f"[OAUTH] User not found for OAuth refresh: {email}")
            response = {
                "error": f"User not found: {email}",
                "suggestion": "User may need to register first"
            }
            duration = time.time() - start_time
            log_performance(logger, "OAuth refresh URL (user not found)", duration)
            log_function_exit(logger, "get_oauth_refresh_url", result=response, duration=duration)
            return response
        
        if not user.oauth_provider:
            logger.warning(f"[OAUTH] User {email} is not an OAuth user")
            response = {
                "error": f"User {email} is not an OAuth user",
                "suggestion": "Use regular login instead"
            }
            duration = time.time() - start_time
            log_performance(logger, "OAuth refresh URL (not OAuth user)", duration)
            log_function_exit(logger, "get_oauth_refresh_url", result=response, duration=duration)
            return response
        
        # Generate OAuth authorization URL
        logger.debug(f"[OAUTH] Generating OAuth authorization URL for {user.oauth_provider}")
        from api.authentication.routes import registration_service
        
        try:
            response, error, status_code = registration_service.get_oauth_authorization_url(
                provider=user.oauth_provider,
                redirect_uri=f"http://localhost:9000/auth/oauth/{user.oauth_provider}/callback"
            )
            
            if error:
                logger.error(f"[OAUTH] Failed to generate OAuth URL: {error}")
                response = {
                    "error": f"Failed to generate OAuth URL: {error}",
                    "user": {
                        "email": user.email,
                        "oauth_provider": user.oauth_provider
                    }
                }
                duration = time.time() - start_time
                log_performance(logger, "OAuth refresh URL (generation failed)", duration)
                log_function_exit(logger, "get_oauth_refresh_url", result=response, duration=duration)
                return response
            
            auth_url = response.authorization_url
            logger.info(f"[OAUTH] OAuth authorization URL generated successfully for {email}")
            
            response = {
                "user": {
                    "email": user.email,
                    "full_name": user.full_name,
                    "oauth_provider": user.oauth_provider
                },
                "oauth_url": auth_url,
                "state": response.state,
                "instructions": [
                    "1. Click the oauth_url above",
                    "2. Complete the OAuth flow",
                    "3. You'll get a fresh token",
                    "4. Use the new token in Swagger UI"
                ]
            }
            
            duration = time.time() - start_time
            log_performance(logger, "OAuth refresh URL (success)", duration, user_email=email, provider=user.oauth_provider)
            log_function_exit(logger, "get_oauth_refresh_url", result=response, duration=duration)
            return response
            
        except Exception as e:
            logger.error(f"[OAUTH] Failed to generate OAuth URL: {str(e)}")
            response = {
                "error": f"Failed to generate OAuth URL: {str(e)}",
                "user": {
                    "email": user.email,
                    "oauth_provider": user.oauth_provider
                }
            }
            duration = time.time() - start_time
            log_performance(logger, "OAuth refresh URL (exception)", duration)
            log_function_exit(logger, "get_oauth_refresh_url", result=response, duration=duration)
            return response
            
    except Exception as e:
        duration = time.time() - start_time
        log_error_with_context(logger, e, "get_oauth_refresh_url", email=email, duration=duration)
        log_function_exit(logger, "get_oauth_refresh_url", duration=duration)
        raise

@app.get("/test/health", tags=["system"])
def health_check():
    """
    System health check - No authentication required
    """
    log_function_entry(logger, "health_check")
    start_time = time.time()
    
    try:
        response = {
            "status": "healthy",
            "service": "Syria GPT API",
            "version": "1.0.0",
            "timestamp": "2024-01-01T00:00:00Z"
        }
        
        duration = time.time() - start_time
        log_performance(logger, "Health check", duration)
        log_function_exit(logger, "health_check", result=response, duration=duration)
        return response
        
    except Exception as e:
        duration = time.time() - start_time
        log_error_with_context(logger, e, "health_check", duration=duration)
        log_function_exit(logger, "health_check", duration=duration)
        raise
