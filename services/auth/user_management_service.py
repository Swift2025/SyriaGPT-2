"""
User management service for SyriaGPT.
Handles user registration, profile updates, and account management.
"""

import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from fastapi import HTTPException, status

from models.domain.user import User
from models.domain.chat import ChatSettings
from services.auth.auth import AuthService
from config.config_loader import ConfigLoader

logger = logging.getLogger(__name__)


class UserManagementService:
    """User management service for handling user operations."""
    
    def __init__(self, config: ConfigLoader):
        """Initialize user management service.
        
        Args:
            config: Configuration loader instance
        """
        self.config = config
        self.auth_service = AuthService(config)
    
    async def create_user(
        self,
        db: AsyncSession,
        email: str,
        password: str,
        username: Optional[str] = None,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        language_preference: str = "ar",
        timezone: str = "Asia/Damascus"
    ) -> User:
        """Create a new user.
        
        Args:
            db: Database session
            email: User email
            password: User password
            username: Optional username
            first_name: Optional first name
            last_name: Optional last name
            language_preference: Language preference
            timezone: User timezone
            
        Returns:
            Created user object
            
        Raises:
            HTTPException: If user creation fails
        """
        try:
            # Check if user already exists
            existing_user = await self.auth_service.get_user_by_email(db, email)
            if existing_user:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="User with this email already exists"
                )
            
            # Check username uniqueness if provided
            if username:
                result = await db.execute(
                    select(User).where(
                        and_(
                            User.username == username,
                            User.is_deleted == 'N'
                        )
                    )
                )
                if result.scalar_one_or_none():
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Username already taken"
                    )
            
            # Validate password strength
            is_valid, error_message = self.auth_service.validate_password_strength(password)
            if not is_valid:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=error_message
                )
            
            # Create user
            password_hash = self.auth_service.get_password_hash(password)
            
            user = User(
                email=email,
                username=username,
                first_name=first_name,
                last_name=last_name,
                password_hash=password_hash,
                language_preference=language_preference,
                timezone=timezone,
                is_active=True,
                is_verified=False,
                is_superuser=False,
                login_count=0,
                failed_login_attempts=0,
                preferences={},
                notification_settings={}
            )
            
            db.add(user)
            await db.commit()
            await db.refresh(user)
            
            # Create default chat settings
            chat_settings = ChatSettings(
                user_id=user.id,
                default_ai_model="gemini-pro",
                default_language=language_preference,
                default_max_tokens=2048,
                default_temperature="0.7",
                auto_save_chats=True,
                auto_delete_old_chats=False,
                chat_retention_days=30,
                notify_on_new_message=True,
                notify_on_chat_archived=False,
                share_usage_data=False,
                allow_ai_learning=True,
                advanced_settings={}
            )
            
            db.add(chat_settings)
            await db.commit()
            
            logger.info(f"User created successfully: {user.id}")
            return user
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"User creation error: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create user"
            )
    
    async def update_user_profile(
        self,
        db: AsyncSession,
        user: User,
        username: Optional[str] = None,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        bio: Optional[str] = None,
        location: Optional[str] = None,
        website: Optional[str] = None,
        language_preference: Optional[str] = None,
        timezone: Optional[str] = None
    ) -> User:
        """Update user profile.
        
        Args:
            db: Database session
            user: User object
            username: Optional new username
            first_name: Optional new first name
            last_name: Optional new last name
            bio: Optional new bio
            location: Optional new location
            website: Optional new website
            language_preference: Optional new language preference
            timezone: Optional new timezone
            
        Returns:
            Updated user object
            
        Raises:
            HTTPException: If update fails
        """
        try:
            # Check username uniqueness if changing
            if username and username != user.username:
                result = await db.execute(
                    select(User).where(
                        and_(
                            User.username == username,
                            User.id != user.id,
                            User.is_deleted == 'N'
                        )
                    )
                )
                if result.scalar_one_or_none():
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Username already taken"
                    )
            
            # Update fields
            if username is not None:
                user.username = username
            if first_name is not None:
                user.first_name = first_name
            if last_name is not None:
                user.last_name = last_name
            if bio is not None:
                user.bio = bio
            if location is not None:
                user.location = location
            if website is not None:
                user.website = website
            if language_preference is not None:
                user.language_preference = language_preference
            if timezone is not None:
                user.timezone = timezone
            
            await db.commit()
            await db.refresh(user)
            
            logger.info(f"User profile updated: {user.id}")
            return user
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"User profile update error: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update user profile"
            )
    
    async def change_password(
        self,
        db: AsyncSession,
        user: User,
        current_password: str,
        new_password: str
    ) -> bool:
        """Change user password.
        
        Args:
            db: Database session
            user: User object
            current_password: Current password
            new_password: New password
            
        Returns:
            True if password changed successfully
            
        Raises:
            HTTPException: If password change fails
        """
        try:
            # Verify current password
            if not self.auth_service.verify_password(current_password, user.password_hash):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Current password is incorrect"
                )
            
            # Validate new password strength
            is_valid, error_message = self.auth_service.validate_password_strength(new_password)
            if not is_valid:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=error_message
                )
            
            # Update password
            user.password_hash = self.auth_service.get_password_hash(new_password)
            user.reset_failed_login_attempts()
            
            await db.commit()
            
            logger.info(f"Password changed for user: {user.id}")
            return True
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Password change error for user {user.id}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to change password"
            )
    
    async def update_user_preferences(
        self,
        db: AsyncSession,
        user: User,
        preferences: Dict[str, Any]
    ) -> User:
        """Update user preferences.
        
        Args:
            db: Database session
            user: User object
            preferences: New preferences
            
        Returns:
            Updated user object
        """
        try:
            if user.preferences is None:
                user.preferences = {}
            
            user.preferences.update(preferences)
            await db.commit()
            await db.refresh(user)
            
            logger.info(f"User preferences updated: {user.id}")
            return user
            
        except Exception as e:
            logger.error(f"User preferences update error: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update user preferences"
            )
    
    async def update_notification_settings(
        self,
        db: AsyncSession,
        user: User,
        notification_settings: Dict[str, Any]
    ) -> User:
        """Update user notification settings.
        
        Args:
            db: Database session
            user: User object
            notification_settings: New notification settings
            
        Returns:
            Updated user object
        """
        try:
            if user.notification_settings is None:
                user.notification_settings = {}
            
            user.notification_settings.update(notification_settings)
            await db.commit()
            await db.refresh(user)
            
            logger.info(f"User notification settings updated: {user.id}")
            return user
            
        except Exception as e:
            logger.error(f"User notification settings update error: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update notification settings"
            )
    
    async def deactivate_user(self, db: AsyncSession, user: User) -> bool:
        """Deactivate user account.
        
        Args:
            db: Database session
            user: User object
            
        Returns:
            True if deactivated successfully
        """
        try:
            user.is_active = False
            await db.commit()
            
            logger.info(f"User account deactivated: {user.id}")
            return True
            
        except Exception as e:
            logger.error(f"User deactivation error: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to deactivate user account"
            )
    
    async def delete_user(self, db: AsyncSession, user: User) -> bool:
        """Soft delete user account.
        
        Args:
            db: Database session
            user: User object
            
        Returns:
            True if deleted successfully
        """
        try:
            user.soft_delete()
            await db.commit()
            
            logger.info(f"User account deleted: {user.id}")
            return True
            
        except Exception as e:
            logger.error(f"User deletion error: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete user account"
            )
    
    async def get_user_stats(self, db: AsyncSession, user: User) -> Dict[str, Any]:
        """Get user statistics.
        
        Args:
            db: Database session
            user: User object
            
        Returns:
            User statistics
        """
        try:
            # Get chat count
            from models.domain.chat import Chat
            chat_result = await db.execute(
                select(Chat).where(
                    and_(
                        Chat.user_id == user.id,
                        Chat.is_deleted == 'N'
                    )
                )
            )
            chats = chat_result.scalars().all()
            chat_count = len(chats)
            
            # Get total messages
            from models.domain.chat import ChatMessage
            message_result = await db.execute(
                select(ChatMessage).where(
                    and_(
                        ChatMessage.chat_id.in_([chat.id for chat in chats]),
                        ChatMessage.is_deleted == 'N'
                    )
                )
            )
            messages = message_result.scalars().all()
            message_count = len(messages)
            
            # Get total tokens used
            total_tokens = sum(chat.total_tokens_used for chat in chats)
            
            return {
                "chat_count": chat_count,
                "message_count": message_count,
                "total_tokens_used": total_tokens,
                "account_age_days": (datetime.utcnow() - user.created_at).days,
                "last_login": user.last_login_at,
                "login_count": user.login_count
            }
            
        except Exception as e:
            logger.error(f"User stats error: {e}")
            return {
                "chat_count": 0,
                "message_count": 0,
                "total_tokens_used": 0,
                "account_age_days": 0,
                "last_login": None,
                "login_count": 0
            }
