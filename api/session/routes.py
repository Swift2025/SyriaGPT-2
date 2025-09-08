"""
Session management API routes for SyriaGPT.
"""

import logging
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession

from models.schemas.response_models import SessionListResponse, SessionResponse
from services.database.database import get_db
from services.dependencies import get_current_user
from services.auth.session_management_service import SessionManagementService
from config.config_loader import ConfigLoader

logger = logging.getLogger(__name__)

# Initialize router
session_router = APIRouter()

# Initialize services
config = ConfigLoader()
session_service = SessionManagementService(config)

# Security scheme
security = HTTPBearer()


@session_router.get("/", response_model=SessionListResponse, tags=["Session Management"])
async def get_user_sessions(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
):
    """Get all active sessions for the current user."""
    try:
        # Get current user
        from services.auth.auth import AuthService
        auth_service = AuthService(config)
        token = credentials.credentials
        user = await auth_service.get_current_user(db, token)
        
        # Get user sessions
        sessions = await session_service.get_user_sessions(db, user, active_only=True)
        
        # Convert to response format
        session_responses = []
        for session in sessions:
            session_responses.append(SessionResponse(
                id=str(session.id),
                session_token=session.session_token,
                is_active=session.is_active,
                ip_address=session.ip_address,
                user_agent=session.user_agent,
                device_info=session.device_info,
                location_info=session.location_info,
                expires_at=session.expires_at,
                last_activity_at=session.last_activity_at,
                created_at=session.created_at
            ))
        
        return SessionListResponse(
            status="success",
            message="Sessions retrieved successfully",
            sessions=session_responses,
            total_count=len(session_responses),
            active_count=len(session_responses)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get user sessions error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve sessions"
        )


@session_router.delete("/{session_id}", tags=["Session Management"])
async def revoke_session(
    session_id: str,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
):
    """Revoke a specific session."""
    try:
        # Get current user
        from services.auth.auth import AuthService
        auth_service = AuthService(config)
        token = credentials.credentials
        user = await auth_service.get_current_user(db, token)
        
        # Get user sessions to verify ownership
        sessions = await session_service.get_user_sessions(db, user, active_only=False)
        target_session = next((s for s in sessions if str(s.id) == session_id), None)
        
        if not target_session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found"
            )
        
        # Revoke session
        success = await session_service.revoke_session(db, target_session)
        
        if success:
            return {
                "status": "success",
                "message": "Session revoked successfully"
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to revoke session"
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Revoke session error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to revoke session"
        )


@session_router.delete("/", tags=["Session Management"])
async def revoke_all_sessions(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
):
    """Revoke all sessions for the current user."""
    try:
        # Get current user
        from services.auth.auth import AuthService
        auth_service = AuthService(config)
        token = credentials.credentials
        user = await auth_service.get_current_user(db, token)
        
        # Revoke all sessions
        revoked_count = await session_service.revoke_all_user_sessions(db, user)
        
        return {
            "status": "success",
            "message": f"Revoked {revoked_count} sessions successfully",
            "revoked_count": revoked_count
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Revoke all sessions error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to revoke sessions"
        )


@session_router.get("/stats", tags=["Session Management"])
async def get_session_stats(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
):
    """Get session statistics for the current user."""
    try:
        # Get current user
        from services.auth.auth import AuthService
        auth_service = AuthService(config)
        token = credentials.credentials
        user = await auth_service.get_current_user(db, token)
        
        # Get session stats
        stats = await session_service.get_session_stats(db, user)
        
        return {
            "status": "success",
            "message": "Session statistics retrieved successfully",
            "stats": stats
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get session stats error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve session statistics"
        )
