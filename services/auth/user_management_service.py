import logging
import time
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, desc, asc
from passlib.context import CryptContext

from models.domain.user import User
from models.schemas.request_models import (
    UserUpdateRequest, UserPasswordChangeRequest, UserStatusUpdateRequest,
    UserSearchRequest, UserBulkActionRequest, UserSettingsRequest
)
from models.schemas.response_models import (
    UserResponse, UserDetailResponse, UserListResponse, UserStatsResponse,
    UserUpdateResponse, UserPasswordChangeResponse, UserBulkActionResponse
)
from services.repositories import get_user_repository
from config.logging_config import get_logger

logger = get_logger(__name__)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class UserManagementService:
    """
    Comprehensive user management service with CRUD operations and advanced features.
    """
    
    def __init__(self):
        self.user_repo = get_user_repository()
    
    def get_user_by_id(self, db: Session, user_id: str) -> Optional[UserResponse]:
        """Get user by ID"""
        try:
            user = self.user_repo.get_user_by_id(db, user_id)
            if user:
                return UserResponse(
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
            return None
        except Exception as e:
            logger.error(f"Error getting user by ID {user_id}: {e}")
            return None
    
    def get_user_detail(self, db: Session, user_id: str) -> Optional[UserDetailResponse]:
        """Get detailed user information including session stats"""
        try:
            user = self.user_repo.get_user_by_id(db, user_id)
            if not user:
                return None
            
            # Get session statistics
            from services.auth.session_management_service import SessionManagementService
            session_service = SessionManagementService()
            session_stats = session_service.get_user_session_stats(db, user_id)
            
            # Get user settings
            settings = self.get_user_settings(db, user_id)
            
            return UserDetailResponse(
                user=UserResponse(
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
                ),
                active_sessions_count=session_stats.get('active_sessions', 0),
                total_sessions_count=session_stats.get('total_sessions', 0),
                last_activity=session_stats.get('last_activity'),
                settings=settings
            )
        except Exception as e:
            logger.error(f"Error getting user detail for {user_id}: {e}")
            return None
    
    def search_users(self, db: Session, search_request: UserSearchRequest) -> UserListResponse:
        """Search and filter users with pagination"""
        try:
            # Build query filters
            filters = []
            
            if search_request.email:
                filters.append(User.email.ilike(f"%{search_request.email}%"))
            
            if search_request.phone_number:
                filters.append(User.phone_number.ilike(f"%{search_request.phone_number}%"))
            
            if search_request.status:
                filters.append(User.status == search_request.status)
            
            if search_request.oauth_provider:
                filters.append(User.oauth_provider == search_request.oauth_provider)
            
            if search_request.is_email_verified is not None:
                filters.append(User.is_email_verified == search_request.is_email_verified)
            
            if search_request.is_phone_verified is not None:
                filters.append(User.is_phone_verified == search_request.is_phone_verified)
            
            if search_request.two_factor_enabled is not None:
                filters.append(User.two_factor_enabled == search_request.two_factor_enabled)
            
            if search_request.created_after:
                filters.append(User.created_at >= search_request.created_after)
            
            if search_request.created_before:
                filters.append(User.created_at <= search_request.created_before)
            
            # Get total count
            total_count = db.query(User).filter(and_(*filters)).count()
            
            # Calculate pagination
            offset = (search_request.page - 1) * search_request.page_size
            total_pages = (total_count + search_request.page_size - 1) // search_request.page_size
            
            # Get users with pagination
            users = db.query(User).filter(and_(*filters)).order_by(
                desc(User.created_at)
            ).offset(offset).limit(search_request.page_size).all()
            
            # Convert to response models
            user_responses = []
            for user in users:
                user_responses.append(UserResponse(
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
                ))
            
            return UserListResponse(
                users=user_responses,
                total_count=total_count,
                page=search_request.page,
                page_size=search_request.page_size,
                total_pages=total_pages
            )
            
        except Exception as e:
            logger.error(f"Error searching users: {e}")
            return UserListResponse(
                users=[],
                total_count=0,
                page=search_request.page,
                page_size=search_request.page_size,
                total_pages=0
            )
    
    def update_user(self, db: Session, user_id: str, update_request: UserUpdateRequest) -> Optional[UserUpdateResponse]:
        """Update user information"""
        try:
            user = self.user_repo.get_user_by_id(db, user_id)
            if not user:
                return None
            
            # Update fields
            if update_request.first_name is not None:
                user.first_name = update_request.first_name
            
            if update_request.last_name is not None:
                user.last_name = update_request.last_name
            
            if update_request.phone_number is not None:
                user.phone_number = update_request.phone_number
            
            if update_request.profile_picture is not None:
                user.profile_picture = update_request.profile_picture
            
            # Update full name if first or last name changed
            if update_request.first_name or update_request.last_name:
                first_name = update_request.first_name or user.first_name or ""
                last_name = update_request.last_name or user.last_name or ""
                user.full_name = f"{first_name} {last_name}".strip()
            
            user.updated_at = datetime.utcnow()
            
            # Save changes
            db.commit()
            db.refresh(user)
            
            return UserUpdateResponse(
                user=UserResponse(
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
                ),
                message="User updated successfully"
            )
            
        except Exception as e:
            logger.error(f"Error updating user {user_id}: {e}")
            db.rollback()
            return None
    
    def change_password(self, db: Session, user_id: str, password_request: UserPasswordChangeRequest) -> Optional[UserPasswordChangeResponse]:
        """Change user password"""
        try:
            user = self.user_repo.get_user_by_id(db, user_id)
            if not user:
                return None
            
            # Verify current password
            if not pwd_context.verify(password_request.current_password, user.password_hash):
                return None
            
            # Hash new password
            new_password_hash = pwd_context.hash(password_request.new_password)
            
            # Update password
            user.password_hash = new_password_hash
            user.last_password_change = datetime.utcnow()
            user.updated_at = datetime.utcnow()
            
            # Save changes
            db.commit()
            
            return UserPasswordChangeResponse(
                message="Password changed successfully",
                password_changed_at=user.last_password_change
            )
            
        except Exception as e:
            logger.error(f"Error changing password for user {user_id}: {e}")
            db.rollback()
            return None
    
    def update_user_status(self, db: Session, user_id: str, status_request: UserStatusUpdateRequest) -> Optional[UserUpdateResponse]:
        """Update user status"""
        try:
            user = self.user_repo.get_user_by_id(db, user_id)
            if not user:
                return None
            
            user.status = status_request.status
            user.updated_at = datetime.utcnow()
            
            # If user is banned or suspended, revoke all active sessions
            if status_request.status in ['banned', 'suspended']:
                from services.auth.session_management_service import SessionManagementService
                session_service = SessionManagementService()
                session_service.revoke_all_user_sessions(db, user_id)
            
            db.commit()
            db.refresh(user)
            
            return UserUpdateResponse(
                user=UserResponse(
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
                ),
                message=f"User status updated to {status_request.status}"
            )
            
        except Exception as e:
            logger.error(f"Error updating user status for {user_id}: {e}")
            db.rollback()
            return None
    
    def bulk_action(self, db: Session, bulk_request: UserBulkActionRequest) -> UserBulkActionResponse:
        """Perform bulk actions on users"""
        try:
            success_count = 0
            failed_count = 0
            failed_users = []
            
            for user_id in bulk_request.user_ids:
                try:
                    user = self.user_repo.get_user_by_id(db, user_id)
                    if not user:
                        failed_users.append({"user_id": user_id, "error": "User not found"})
                        failed_count += 1
                        continue
                    
                    if bulk_request.action == "activate":
                        user.status = "active"
                    elif bulk_request.action == "suspend":
                        user.status = "suspended"
                    elif bulk_request.action == "ban":
                        user.status = "banned"
                    elif bulk_request.action == "delete":
                        db.delete(user)
                    elif bulk_request.action == "verify_email":
                        user.is_email_verified = True
                    elif bulk_request.action == "verify_phone":
                        user.is_phone_verified = True
                    
                    user.updated_at = datetime.utcnow()
                    success_count += 1
                    
                except Exception as e:
                    failed_users.append({"user_id": user_id, "error": str(e)})
                    failed_count += 1
            
            db.commit()
            
            return UserBulkActionResponse(
                success_count=success_count,
                failed_count=failed_count,
                failed_users=failed_users,
                message=f"Bulk action '{bulk_request.action}' completed"
            )
            
        except Exception as e:
            logger.error(f"Error performing bulk action: {e}")
            db.rollback()
            return UserBulkActionResponse(
                success_count=0,
                failed_count=len(bulk_request.user_ids),
                failed_users=[{"user_id": uid, "error": str(e)} for uid in bulk_request.user_ids],
                message=f"Bulk action failed: {str(e)}"
            )
    
    def get_user_stats(self, db: Session) -> UserStatsResponse:
        """Get comprehensive user statistics"""
        try:
            now = datetime.utcnow()
            today = now.date()
            week_ago = now - timedelta(days=7)
            month_ago = now - timedelta(days=30)
            
            # Basic counts
            total_users = db.query(User).count()
            active_users = db.query(User).filter(User.status == "active").count()
            suspended_users = db.query(User).filter(User.status == "suspended").count()
            banned_users = db.query(User).filter(User.status == "banned").count()
            pending_verification = db.query(User).filter(User.status == "pending_verification").count()
            
            # Verification counts
            email_verified_users = db.query(User).filter(User.is_email_verified == True).count()
            phone_verified_users = db.query(User).filter(User.is_phone_verified == True).count()
            
            # OAuth and 2FA counts
            oauth_users = db.query(User).filter(User.oauth_provider.isnot(None)).count()
            two_factor_enabled_users = db.query(User).filter(User.two_factor_enabled == True).count()
            
            # Time-based counts
            users_created_today = db.query(User).filter(
                func.date(User.created_at) == today
            ).count()
            
            users_created_this_week = db.query(User).filter(
                User.created_at >= week_ago
            ).count()
            
            users_created_this_month = db.query(User).filter(
                User.created_at >= month_ago
            ).count()
            
            return UserStatsResponse(
                total_users=total_users,
                active_users=active_users,
                suspended_users=suspended_users,
                banned_users=banned_users,
                pending_verification=pending_verification,
                email_verified_users=email_verified_users,
                phone_verified_users=phone_verified_users,
                oauth_users=oauth_users,
                two_factor_enabled_users=two_factor_enabled_users,
                users_created_today=users_created_today,
                users_created_this_week=users_created_this_week,
                users_created_this_month=users_created_this_month
            )
            
        except Exception as e:
            logger.error(f"Error getting user stats: {e}")
            return UserStatsResponse(
                total_users=0,
                active_users=0,
                suspended_users=0,
                banned_users=0,
                pending_verification=0,
                email_verified_users=0,
                phone_verified_users=0,
                oauth_users=0,
                two_factor_enabled_users=0,
                users_created_today=0,
                users_created_this_week=0,
                users_created_this_month=0
            )
    
    def get_user_settings(self, db: Session, user_id: str) -> Dict[str, Any]:
        """Get user settings (placeholder for future implementation)"""
        # This would typically fetch from a user_settings table
        # For now, return default settings
        return {
            "email_notifications": True,
            "sms_notifications": False,
            "two_factor_enabled": False,
            "session_timeout_hours": 24,
            "max_concurrent_sessions": 5,
            "language": "en",
            "timezone": "UTC",
            "theme": "light"
        }
    
    def update_user_settings(self, db: Session, user_id: str, settings_request: UserSettingsRequest) -> Dict[str, Any]:
        """Update user settings (placeholder for future implementation)"""
        # This would typically save to a user_settings table
        # For now, just return the updated settings
        return {
            "email_notifications": settings_request.email_notifications,
            "sms_notifications": settings_request.sms_notifications,
            "two_factor_enabled": settings_request.two_factor_enabled,
            "session_timeout_hours": settings_request.session_timeout_hours,
            "max_concurrent_sessions": settings_request.max_concurrent_sessions,
            "language": settings_request.language,
            "timezone": settings_request.timezone,
            "theme": settings_request.theme
        }


# Service instance
user_management_service = UserManagementService()


def get_user_management_service() -> UserManagementService:
    """Get user management service instance"""
    return user_management_service
