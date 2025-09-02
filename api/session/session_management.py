import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional, List
from fastapi import HTTPException, status, Request
from sqlalchemy.orm import Session
from sqlalchemy import and_

from models.domain.session import Session as SessionModel
from models.domain.user import User
from models.schemas.response_models import SessionResponse, SessionListResponse, LogoutResponse, RefreshTokenResponse
from services.database import SessionLocal
from services.auth import get_auth_service
from config.config_loader import config_loader


class SessionManager:
    def __init__(self):
        self.default_session_duration = timedelta(hours=24)
        self.remember_me_duration = timedelta(days=30)
    
    @property
    def auth_service(self):
log_function_entry(logger, "auth_service")
start_time = time.time()
try:
except Exception as e:
    duration = time.time() - start_time
    log_error_with_context(logger, e, "auth_service", duration=duration)
    logger.error(f"❌ Error in auth_service: {e}")
    log_function_exit(logger, "auth_service", duration=duration)
    raise
        return get_auth_service()

    def _get_db(self) -> Session:
        return SessionLocal()

    def create_session(
        self, 
        user_id: str, 
        request: Request,
        remember_me: bool = False,
        device_info: Optional[str] = None,
        location: Optional[str] = None
    ) -> tuple[str, str, datetime]:
        """Create a new session and return access token, refresh token, and expiry"""
        db = self._get_db()
        try:
            # Generate tokens
            session_token = self.auth_service.generate_verification_token(64)
            refresh_token = self.auth_service.generate_verification_token(64)
            
            # Set expiry based on remember_me
            duration = self.remember_me_duration if remember_me else self.default_session_duration
            expires_at = datetime.now(timezone.utc) + duration
            
            # Extract request information
            ip_address = request.client.host if request.client else None
            user_agent = request.headers.get("user-agent")
            is_mobile = self._is_mobile_device(user_agent)
            
            # Create session record
            session = SessionModel(
                user_id=user_id,
                session_token=session_token,
                refresh_token=refresh_token,
                device_info=device_info,
                ip_address=ip_address,
                user_agent=user_agent,
                location=location,
                is_mobile=is_mobile,
                expires_at=expires_at
            )
            
            db.add(session)
            db.commit()
            
            # Create JWT access token
            access_token = self.auth_service.create_access_token(
                data={"sub": user_id, "session_id": str(session.id)},
                expires_delta=duration
            )
            
            return access_token, refresh_token, expires_at
            
        except Exception as e:
            db.rollback()
            logger.error(f"Session creation failed: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=config_loader.get_message("errors", "session_creation_failed")
            )
        finally:
            db.close()

    def get_user_sessions(self, user_id: str) -> SessionListResponse:
        """Get all sessions for a user"""
        db = self._get_db()
        try:
            sessions = db.query(SessionModel).filter(
                SessionModel.user_id == user_id
            ).order_by(SessionModel.last_activity_at.desc()).all()
            
            active_sessions = [s for s in sessions if s.is_active and s.expires_at > datetime.now(timezone.utc)]
            
            session_responses = [
                SessionResponse(
                    id=str(session.id),
                    device_info=session.device_info,
                    ip_address=session.ip_address,
                    user_agent=session.user_agent,
                    location=session.location,
                    is_active=session.is_active,
                    is_mobile=session.is_mobile,
                    last_activity_at=session.last_activity_at,
                    created_at=session.created_at
                )
                for session in sessions
            ]
            
            return SessionListResponse(
                sessions=session_responses,
                active_sessions_count=len(active_sessions),
                total_sessions_count=len(sessions)
            )
            
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to get sessions: {str(e)}"
            )
        finally:
            db.close()

    def logout_session(self, user_id: str, session_id: Optional[str] = None, logout_all: bool = False) -> LogoutResponse:
        """Logout specific session or all sessions"""
        db = self._get_db()
        try:
            if logout_all:
                # Deactivate all sessions for the user
                updated = db.query(SessionModel).filter(
                    and_(
                        SessionModel.user_id == user_id,
                        SessionModel.is_active == True
                    )
                ).update({"is_active": False})
                
                db.commit()
                
                return LogoutResponse(
                    message="Successfully logged out from all sessions",
                    logged_out_sessions=updated
                )
            
            elif session_id:
                # Logout specific session
                session = db.query(SessionModel).filter(
                    and_(
                        SessionModel.id == session_id,
                        SessionModel.user_id == user_id,
                        SessionModel.is_active == True
                    )
                ).first()
                
                if not session:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail="Session not found or already inactive"
                    )
                
                session.is_active = False
                db.commit()
                
                return LogoutResponse(
                    message="Successfully logged out from session",
                    logged_out_sessions=1
                )
            
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Either session_id or logout_all must be specified"
                )
                
        except HTTPException:
            raise
        except Exception as e:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to logout: {str(e)}"
            )
        finally:
            db.close()

    def refresh_access_token(self, refresh_token: str) -> RefreshTokenResponse:
        """Refresh access token using refresh token"""
        db = self._get_db()
        try:
            # Find session with refresh token
            session = db.query(SessionModel).filter(
                and_(
                    SessionModel.refresh_token == refresh_token,
                    SessionModel.is_active == True,
                    SessionModel.expires_at > datetime.now(timezone.utc)
                )
            ).first()
            
            if not session:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid or expired refresh token"
                )
            
            # Generate new tokens
            new_session_token = self.auth_service.generate_verification_token(64)
            new_refresh_token = self.auth_service.generate_verification_token(64)
            
            # Update session
            session.session_token = new_session_token
            session.refresh_token = new_refresh_token
            session.last_activity_at = datetime.now(timezone.utc)
            
            db.commit()
            
            # Create new access token
            duration = session.expires_at - datetime.now(timezone.utc)
            access_token = self.auth_service.create_access_token(
                data={"sub": str(session.user_id), "session_id": str(session.id)},
                expires_delta=duration
            )
            
            return RefreshTokenResponse(
                access_token=access_token,
                refresh_token=new_refresh_token,
                expires_in=int(duration.total_seconds())
            )
            
        except HTTPException:
            raise
        except Exception as e:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to refresh token: {str(e)}"
            )
        finally:
            db.close()

    def validate_session(self, session_id: str, user_id: str) -> bool:
        """Validate if session is active and belongs to user"""
        db = self._get_db()
        try:
            session = db.query(SessionModel).filter(
                and_(
                    SessionModel.id == session_id,
                    SessionModel.user_id == user_id,
                    SessionModel.is_active == True,
                    SessionModel.expires_at > datetime.now(timezone.utc)
                )
            ).first()
            
            if session:
                # Update last activity
                session.last_activity_at = datetime.now(timezone.utc)
                db.commit()
                return True
            
            return False
            
        except Exception:
            return False
        finally:
            db.close()

    def cleanup_expired_sessions(self):
log_function_entry(logger, "cleanup_expired_sessions")
start_time = time.time()
try:
        """Clean up expired sessions (can be called by a cron job)"""
        db = self._get_db()
        try:
            expired_count = db.query(SessionModel).filter(
                SessionModel.expires_at <= datetime.now(timezone.utc)
            ).update({"is_active": False})
            
            db.commit()
    duration = time.time() - start_time
    log_performance(logger, "cleanup_expired_sessions", duration)
    log_function_exit(logger, "cleanup_expired_sessions", duration=duration)

            return expired_count
            
        except Exception as e:
            db.rollback()
            raise Exception(f"Failed to cleanup sessions: {str(e)}")
        finally:
            db.close()
except Exception as e:
    duration = time.time() - start_time
    log_error_with_context(logger, e, "cleanup_expired_sessions", duration=duration)
    logger.error(f"❌ Error in cleanup_expired_sessions: {e}")
    log_function_exit(logger, "cleanup_expired_sessions", duration=duration)
    raise

    def _is_mobile_device(self, user_agent: Optional[str]) -> bool:
        """Check if the request is from a mobile device"""
        if not user_agent:
            return False
        
        mobile_keywords = [
            'Mobile', 'Android', 'iPhone', 'iPad', 'iPod', 
            'BlackBerry', 'Windows Phone', 'Opera Mini'
        ]
        
        return any(keyword in user_agent for keyword in mobile_keywords)


# Global session manager instance
session_manager = SessionManager()
