# /api/session/routes.py

from fastapi import APIRouter, Request, Depends, HTTPException, status
from typing import Optional

from models.domain.user import User
from models.schemas.request_models import LogoutRequest, RefreshTokenRequest, SessionInfoRequest
from models.schemas.response_models import SessionListResponse, LogoutResponse, RefreshTokenResponse
from requests.session.session_management import session_manager
from services.dependencies import get_current_user
from config.config_loader import config_loader
import logging
import time
from config.logging_config import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/sessions", tags=["session_management"])


@router.get("/", response_model=SessionListResponse)
async def get_user_sessions(current_user: User = Depends(get_current_user)):
    """Get all sessions for the current user"""
    return session_manager.get_user_sessions(str(current_user.id))


@router.post("/logout", response_model=LogoutResponse)
async def logout_session(
    logout_data: LogoutRequest,
    current_user: User = Depends(get_current_user)
):
    """Logout from specific session or all sessions"""
    return session_manager.logout_session(
        user_id=str(current_user.id),
        session_id=logout_data.session_id,
        logout_all=logout_data.logout_all
    )


@router.post("/refresh", response_model=RefreshTokenResponse)
async def refresh_token(refresh_data:
log_function_entry(logger, "refresh_token")
start_time = time.time()
try: RefreshTokenRequest):
    """Refresh access token using refresh token"""
    duration = time.time() - start_time
    log_performance(logger, "refresh_token", duration)
    log_function_exit(logger, "refresh_token", duration=duration)

    return session_manager.refresh_access_token(refresh_data.refresh_token)
except Exception as e:
    duration = time.time() - start_time
    log_error_with_context(logger, e, "refresh_token", duration=duration)
    logger.error(f"❌ Error in refresh_token: {e}")
    log_function_exit(logger, "refresh_token", duration=duration)
    raise


@router.delete("/cleanup")
async def cleanup_expired_sessions():
    """Clean up expired sessions (admin endpoint)"""
    try:
        cleaned_count = session_manager.cleanup_expired_sessions()
        return {
            "message": f"Successfully cleaned up {cleaned_count} expired sessions",
            "cleaned_sessions": cleaned_count
        }
    except Exception as e:
        logger.error(f"Session cleanup failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=config_loader.get_message("errors", "session_cleanup_failed")
        )


@router.get("/current")
async def get_current_session_info(current_user: User = Depends(get_current_user)):
    """Get current session information"""
    # This would typically extract session_id from JWT token
    # For now, returning basic user session info
    return {
        "user_id": str(current_user.id),
        "email": current_user.email,
        "message": "Current session information - session tracking via JWT tokens"
    }