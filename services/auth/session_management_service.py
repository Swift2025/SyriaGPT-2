import logging
import time
import uuid
import secrets
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, desc, asc

from models.domain.session import Session as SessionModel
from models.domain.user import User
from models.schemas.request_models import (
    SessionCreateRequest, SessionUpdateRequest, SessionSearchRequest,
    SessionBulkActionRequest
)
from models.schemas.response_models import (
    SessionResponse, SessionDetailResponse, SessionListResponse, SessionStatsResponse,
    SessionCreateResponse, SessionUpdateResponse, SessionBulkActionResponse
)
from services.repositories import get_user_repository
from config.logging_config import get_logger

logger = get_logger(__name__)


class SessionManagementService:
    """
    Comprehensive session management service with CRUD operations and advanced features.
    """
    
    def __init__(self):
        self.user_repo = get_user_repository()
    
    def create_session(self, db: Session, user_id: str, create_request: SessionCreateRequest) -> Optional[SessionCreateResponse]:
        """Create a new session for a user"""
        try:
            # Check if user exists
            user = self.user_repo.get_user_by_id(db, user_id)
            if not user:
                return None
            
            # Generate session tokens
            session_token = secrets.token_urlsafe(32)
            refresh_token = secrets.token_urlsafe(32)
            
            # Calculate expiry time
            expires_at = datetime.utcnow() + timedelta(hours=create_request.expires_in_hours)
            
            # Create session
            session = SessionModel(
                user_id=uuid.UUID(user_id),
                session_token=session_token,
                refresh_token=refresh_token,
                device_info=create_request.device_info,
                ip_address=create_request.ip_address,
                user_agent=create_request.user_agent,
                location=create_request.location,
                is_mobile=create_request.is_mobile,
                expires_at=expires_at
            )
            
            db.add(session)
            db.commit()
            db.refresh(session)
            
            # Generate JWT access token
            from services.auth import get_auth_service
            auth_service = get_auth_service()
            access_token = auth_service.create_access_token(data={"sub": user.email})
            
            return SessionCreateResponse(
                session=SessionResponse(
                    id=str(session.id),
                    user_id=str(session.user_id),
                    session_token=session.session_token,
                    device_info=session.device_info,
                    ip_address=session.ip_address,
                    user_agent=session.user_agent,
                    location=session.location,
                    is_active=session.is_active,
                    is_mobile=session.is_mobile,
                    last_activity_at=session.last_activity_at,
                    expires_at=session.expires_at,
                    created_at=session.created_at,
                    updated_at=session.updated_at
                ),
                access_token=access_token,
                refresh_token=refresh_token,
                message="Session created successfully"
            )
            
        except Exception as e:
            logger.error(f"Error creating session for user {user_id}: {e}")
            db.rollback()
            return None
    
    def get_session_by_id(self, db: Session, session_id: str) -> Optional[SessionResponse]:
        """Get session by ID"""
        try:
            session = db.query(SessionModel).filter(SessionModel.id == uuid.UUID(session_id)).first()
            if session:
                return SessionResponse(
                    id=str(session.id),
                    user_id=str(session.user_id),
                    session_token=session.session_token,
                    device_info=session.device_info,
                    ip_address=session.ip_address,
                    user_agent=session.user_agent,
                    location=session.location,
                    is_active=session.is_active,
                    is_mobile=session.is_mobile,
                    last_activity_at=session.last_activity_at,
                    expires_at=session.expires_at,
                    created_at=session.created_at,
                    updated_at=session.updated_at
                )
            return None
        except Exception as e:
            logger.error(f"Error getting session by ID {session_id}: {e}")
            return None
    
    def get_session_detail(self, db: Session, session_id: str) -> Optional[SessionDetailResponse]:
        """Get detailed session information including user data"""
        try:
            session = db.query(SessionModel).filter(SessionModel.id == uuid.UUID(session_id)).first()
            if not session:
                return None
            
            # Get user information
            user = self.user_repo.get_user_by_id(db, str(session.user_id))
            user_response = None
            if user:
                from models.schemas.response_models import UserResponse
                user_response = UserResponse(
                    id=str(user.id),
                    email=user.email,
                    phone_number=user.phone_number,
                    first_name=user.first_name,
                    last_name=user.last_name,
                    full_name=user.full_name,
                    profile_picture=user.profile_picture,
                    oauth_provider=user.oauth_provider,
                    oauth_provider_id=user.oauth_provider_id,
                    two_factor_enabled=user.two_factor_enabled,
                    is_email_verified=user.is_email_verified,
                    is_phone_verified=user.is_phone_verified,
                    status=user.status,
                    last_login_at=user.last_login_at,
                    created_at=user.created_at,
                    updated_at=user.updated_at
                )
            
            # Parse device info
            device_summary = self._parse_device_info(session.device_info)
            
            # Get location info
            location_info = self._parse_location_info(session.location)
            
            return SessionDetailResponse(
                session=SessionResponse(
                    id=str(session.id),
                    user_id=str(session.user_id),
                    session_token=session.session_token,
                    device_info=session.device_info,
                    ip_address=session.ip_address,
                    user_agent=session.user_agent,
                    location=session.location,
                    is_active=session.is_active,
                    is_mobile=session.is_mobile,
                    last_activity_at=session.last_activity_at,
                    expires_at=session.expires_at,
                    created_at=session.created_at,
                    updated_at=session.updated_at
                ),
                user=user_response,
                device_summary=device_summary,
                location_info=location_info
            )
            
        except Exception as e:
            logger.error(f"Error getting session detail for {session_id}: {e}")
            return None
    
    def search_sessions(self, db: Session, search_request: SessionSearchRequest) -> SessionListResponse:
        """Search and filter sessions with pagination"""
        try:
            # Build query filters
            filters = []
            
            if search_request.user_id:
                filters.append(SessionModel.user_id == uuid.UUID(search_request.user_id))
            
            if search_request.is_active is not None:
                filters.append(SessionModel.is_active == search_request.is_active)
            
            if search_request.is_mobile is not None:
                filters.append(SessionModel.is_mobile == search_request.is_mobile)
            
            if search_request.ip_address:
                filters.append(SessionModel.ip_address.ilike(f"%{search_request.ip_address}%"))
            
            if search_request.created_after:
                filters.append(SessionModel.created_at >= search_request.created_after)
            
            if search_request.created_before:
                filters.append(SessionModel.created_at <= search_request.created_before)
            
            if search_request.expires_after:
                filters.append(SessionModel.expires_at >= search_request.expires_after)
            
            if search_request.expires_before:
                filters.append(SessionModel.expires_at <= search_request.expires_before)
            
            # Get total count
            total_count = db.query(SessionModel).filter(and_(*filters)).count()
            
            # Calculate pagination
            offset = (search_request.page - 1) * search_request.page_size
            total_pages = (total_count + search_request.page_size - 1) // search_request.page_size
            
            # Get sessions with pagination
            sessions = db.query(SessionModel).filter(and_(*filters)).order_by(
                desc(SessionModel.created_at)
            ).offset(offset).limit(search_request.page_size).all()
            
            # Convert to response models
            session_responses = []
            for session in sessions:
                session_responses.append(SessionResponse(
                    id=str(session.id),
                    user_id=str(session.user_id),
                    session_token=session.session_token,
                    device_info=session.device_info,
                    ip_address=session.ip_address,
                    user_agent=session.user_agent,
                    location=session.location,
                    is_active=session.is_active,
                    is_mobile=session.is_mobile,
                    last_activity_at=session.last_activity_at,
                    expires_at=session.expires_at,
                    created_at=session.created_at,
                    updated_at=session.updated_at
                ))
            
            return SessionListResponse(
                sessions=session_responses,
                total_count=total_count,
                page=search_request.page,
                page_size=search_request.page_size,
                total_pages=total_pages
            )
            
        except Exception as e:
            logger.error(f"Error searching sessions: {e}")
            return SessionListResponse(
                sessions=[],
                total_count=0,
                page=search_request.page,
                page_size=search_request.page_size,
                total_pages=0
            )
    
    def update_session(self, db: Session, session_id: str, update_request: SessionUpdateRequest) -> Optional[SessionUpdateResponse]:
        """Update session information"""
        try:
            session = db.query(SessionModel).filter(SessionModel.id == uuid.UUID(session_id)).first()
            if not session:
                return None
            
            # Update fields
            if update_request.device_info is not None:
                session.device_info = update_request.device_info
            
            if update_request.location is not None:
                session.location = update_request.location
            
            if update_request.is_mobile is not None:
                session.is_mobile = update_request.is_mobile
            
            session.updated_at = datetime.utcnow()
            
            # Save changes
            db.commit()
            db.refresh(session)
            
            return SessionUpdateResponse(
                session=SessionResponse(
                    id=str(session.id),
                    user_id=str(session.user_id),
                    session_token=session.session_token,
                    device_info=session.device_info,
                    ip_address=session.ip_address,
                    user_agent=session.user_agent,
                    location=session.location,
                    is_active=session.is_active,
                    is_mobile=session.is_mobile,
                    last_activity_at=session.last_activity_at,
                    expires_at=session.expires_at,
                    created_at=session.created_at,
                    updated_at=session.updated_at
                ),
                message="Session updated successfully"
            )
            
        except Exception as e:
            logger.error(f"Error updating session {session_id}: {e}")
            db.rollback()
            return None
    
    def revoke_session(self, db: Session, session_id: str) -> bool:
        """Revoke a session"""
        try:
            session = db.query(SessionModel).filter(SessionModel.id == uuid.UUID(session_id)).first()
            if not session:
                return False
            
            session.is_active = False
            session.updated_at = datetime.utcnow()
            
            db.commit()
            return True
            
        except Exception as e:
            logger.error(f"Error revoking session {session_id}: {e}")
            db.rollback()
            return False
    
    def extend_session(self, db: Session, session_id: str, hours: int) -> Optional[SessionResponse]:
        """Extend session expiry time"""
        try:
            session = db.query(SessionModel).filter(SessionModel.id == uuid.UUID(session_id)).first()
            if not session:
                return None
            
            session.expires_at = session.expires_at + timedelta(hours=hours)
            session.updated_at = datetime.utcnow()
            
            db.commit()
            db.refresh(session)
            
            return SessionResponse(
                id=str(session.id),
                user_id=str(session.user_id),
                session_token=session.session_token,
                device_info=session.device_info,
                ip_address=session.ip_address,
                user_agent=session.user_agent,
                location=session.location,
                is_active=session.is_active,
                is_mobile=session.is_mobile,
                last_activity_at=session.last_activity_at,
                expires_at=session.expires_at,
                created_at=session.created_at,
                updated_at=session.updated_at
            )
            
        except Exception as e:
            logger.error(f"Error extending session {session_id}: {e}")
            db.rollback()
            return None
    
    def revoke_all_user_sessions(self, db: Session, user_id: str) -> int:
        """Revoke all active sessions for a user"""
        try:
            result = db.query(SessionModel).filter(
                and_(
                    SessionModel.user_id == uuid.UUID(user_id),
                    SessionModel.is_active == True
                )
            ).update({
                "is_active": False,
                "updated_at": datetime.utcnow()
            })
            
            db.commit()
            return result
            
        except Exception as e:
            logger.error(f"Error revoking all sessions for user {user_id}: {e}")
            db.rollback()
            return 0
    
    def get_user_session_stats(self, db: Session, user_id: str) -> Dict[str, Any]:
        """Get session statistics for a user"""
        try:
            # Get session counts
            total_sessions = db.query(SessionModel).filter(
                SessionModel.user_id == uuid.UUID(user_id)
            ).count()
            
            active_sessions = db.query(SessionModel).filter(
                and_(
                    SessionModel.user_id == uuid.UUID(user_id),
                    SessionModel.is_active == True
                )
            ).count()
            
            # Get last activity
            last_session = db.query(SessionModel).filter(
                SessionModel.user_id == uuid.UUID(user_id)
            ).order_by(desc(SessionModel.last_activity_at)).first()
            
            last_activity = last_session.last_activity_at if last_session else None
            
            return {
                "total_sessions": total_sessions,
                "active_sessions": active_sessions,
                "expired_sessions": total_sessions - active_sessions,
                "last_activity": last_activity
            }
            
        except Exception as e:
            logger.error(f"Error getting session stats for user {user_id}: {e}")
            return {
                "total_sessions": 0,
                "active_sessions": 0,
                "expired_sessions": 0,
                "last_activity": None
            }
    
    def get_session_stats(self, db: Session) -> SessionStatsResponse:
        """Get comprehensive session statistics"""
        try:
            now = datetime.utcnow()
            today = now.date()
            week_ago = now - timedelta(days=7)
            
            # Basic counts
            total_sessions = db.query(SessionModel).count()
            active_sessions = db.query(SessionModel).filter(SessionModel.is_active == True).count()
            expired_sessions = total_sessions - active_sessions
            
            # Device type counts
            mobile_sessions = db.query(SessionModel).filter(SessionModel.is_mobile == True).count()
            desktop_sessions = total_sessions - mobile_sessions
            
            # Time-based counts
            sessions_created_today = db.query(SessionModel).filter(
                func.date(SessionModel.created_at) == today
            ).count()
            
            sessions_created_this_week = db.query(SessionModel).filter(
                SessionModel.created_at >= week_ago
            ).count()
            
            # Calculate average session duration
            active_sessions_data = db.query(SessionModel).filter(
                SessionModel.is_active == True
            ).all()
            
            total_duration = timedelta()
            valid_sessions = 0
            
            for session in active_sessions_data:
                if session.expires_at and session.created_at:
                    duration = session.expires_at - session.created_at
                    total_duration += duration
                    valid_sessions += 1
            
            average_duration_hours = 0
            if valid_sessions > 0:
                average_duration_hours = total_duration.total_seconds() / 3600 / valid_sessions
            
            return SessionStatsResponse(
                total_sessions=total_sessions,
                active_sessions=active_sessions,
                expired_sessions=expired_sessions,
                mobile_sessions=mobile_sessions,
                desktop_sessions=desktop_sessions,
                sessions_created_today=sessions_created_today,
                sessions_created_this_week=sessions_created_this_week,
                average_session_duration_hours=average_duration_hours
            )
            
        except Exception as e:
            logger.error(f"Error getting session stats: {e}")
            return SessionStatsResponse(
                total_sessions=0,
                active_sessions=0,
                expired_sessions=0,
                mobile_sessions=0,
                desktop_sessions=0,
                sessions_created_today=0,
                sessions_created_this_week=0,
                average_session_duration_hours=0.0
            )
    
    def bulk_action(self, db: Session, bulk_request: SessionBulkActionRequest) -> SessionBulkActionResponse:
        """Perform bulk actions on sessions"""
        try:
            success_count = 0
            failed_count = 0
            failed_sessions = []
            
            for session_id in bulk_request.session_ids:
                try:
                    session = db.query(SessionModel).filter(SessionModel.id == uuid.UUID(session_id)).first()
                    if not session:
                        failed_sessions.append({"session_id": session_id, "error": "Session not found"})
                        failed_count += 1
                        continue
                    
                    if bulk_request.action == "revoke":
                        session.is_active = False
                    elif bulk_request.action == "extend" and bulk_request.expires_in_hours:
                        session.expires_at = session.expires_at + timedelta(hours=bulk_request.expires_in_hours)
                    elif bulk_request.action == "update_location":
                        # This would typically update location based on IP or other data
                        pass
                    
                    session.updated_at = datetime.utcnow()
                    success_count += 1
                    
                except Exception as e:
                    failed_sessions.append({"session_id": session_id, "error": str(e)})
                    failed_count += 1
            
            db.commit()
            
            return SessionBulkActionResponse(
                success_count=success_count,
                failed_count=failed_count,
                failed_sessions=failed_sessions,
                message=f"Bulk action '{bulk_request.action}' completed"
            )
            
        except Exception as e:
            logger.error(f"Error performing bulk session action: {e}")
            db.rollback()
            return SessionBulkActionResponse(
                success_count=0,
                failed_count=len(bulk_request.session_ids),
                failed_sessions=[{"session_id": sid, "error": str(e)} for sid in bulk_request.session_ids],
                message=f"Bulk action failed: {str(e)}"
            )
    
    def cleanup_expired_sessions(self, db: Session) -> int:
        """Clean up expired sessions"""
        try:
            now = datetime.utcnow()
            result = db.query(SessionModel).filter(
                and_(
                    SessionModel.expires_at < now,
                    SessionModel.is_active == True
                )
            ).update({
                "is_active": False,
                "updated_at": now
            })
            
            db.commit()
            return result
            
        except Exception as e:
            logger.error(f"Error cleaning up expired sessions: {e}")
            db.rollback()
            return 0
    
    def _parse_device_info(self, device_info: Optional[str]) -> Optional[str]:
        """Parse device information into a readable summary"""
        if not device_info:
            return None
        
        try:
            # This is a simple parser - in a real implementation, you might use a more sophisticated approach
            if "mobile" in device_info.lower():
                return "Mobile Device"
            elif "tablet" in device_info.lower():
                return "Tablet"
            elif "desktop" in device_info.lower():
                return "Desktop"
            else:
                return "Unknown Device"
        except:
            return "Unknown Device"
    
    def _parse_location_info(self, location: Optional[str]) -> Optional[Dict[str, Any]]:
        """Parse location information"""
        if not location:
            return None
        
        try:
            # This is a placeholder - in a real implementation, you might parse IP geolocation data
            return {
                "country": "Unknown",
                "city": "Unknown",
                "timezone": "UTC"
            }
        except:
            return None


# Service instance
session_management_service = SessionManagementService()


def get_session_management_service() -> SessionManagementService:
    """Get session management service instance"""
    return session_management_service
