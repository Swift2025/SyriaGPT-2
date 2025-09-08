"""
Forgot password service for SyriaGPT.
Handles password reset functionality.
"""

import logging
from datetime import datetime, timedelta
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import HTTPException, status

from models.domain.user import User
from services.auth.auth import AuthService
from services.email.email_service import EmailService
from config.config_loader import ConfigLoader

logger = logging.getLogger(__name__)


class ForgotPasswordService:
    """Forgot password service for handling password reset."""
    
    def __init__(self, config: ConfigLoader):
        """Initialize forgot password service.
        
        Args:
            config: Configuration loader instance
        """
        self.config = config
        self.auth_service = AuthService(config)
        self.email_service = EmailService(config)
    
    async def send_password_reset_email(self, db: AsyncSession, email: str) -> bool:
        """Send password reset email to user.
        
        Args:
            db: Database session
            email: User email address
            
        Returns:
            True if email sent successfully
            
        Raises:
            HTTPException: If email sending fails
        """
        try:
            # Get user by email
            result = await db.execute(
                select(User).where(
                    User.email == email,
                    User.is_active == True,
                    User.is_deleted == 'N'
                )
            )
            user = result.scalar_one_or_none()
            
            if not user:
                # Don't reveal if user exists or not for security
                logger.warning(f"Password reset requested for non-existent email: {email}")
                return True
            
            # Generate password reset token
            reset_token = self.auth_service.generate_password_reset_token(user)
            
            # Update user with reset token
            user.password_reset_token = reset_token
            user.password_reset_expires = datetime.utcnow() + timedelta(hours=1)
            
            await db.commit()
            
            # Send password reset email
            try:
                await self.email_service.send_password_reset_email(user, reset_token)
                logger.info(f"Password reset email sent to user {user.id}")
            except Exception as e:
                logger.error(f"Failed to send password reset email: {e}")
                # Don't fail the request if email sending fails
                pass
            
            return True
            
        except Exception as e:
            logger.error(f"Send password reset email error: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to send password reset email"
            )
    
    async def reset_password_with_token(
        self,
        db: AsyncSession,
        token: str,
        new_password: str
    ) -> bool:
        """Reset user password with token.
        
        Args:
            db: Database session
            token: Password reset token
            new_password: New password
            
        Returns:
            True if password reset successfully
            
        Raises:
            HTTPException: If password reset fails
        """
        try:
            # Verify token
            payload = self.auth_service.verify_password_reset_token(token)
            user_id = payload.get("sub")
            
            if not user_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid password reset token"
                )
            
            # Get user
            user = await self.auth_service.get_user_by_id(db, user_id)
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User not found"
                )
            
            # Check if token matches and is not expired
            if (user.password_reset_token != token or 
                not user.password_reset_expires or 
                datetime.utcnow() > user.password_reset_expires):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid or expired password reset token"
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
            user.password_reset_token = None
            user.password_reset_expires = None
            user.reset_failed_login_attempts()
            
            await db.commit()
            
            # Send password changed notification email
            try:
                await self.email_service.send_password_changed_notification(user)
                logger.info(f"Password changed notification sent to user {user.id}")
            except Exception as e:
                logger.error(f"Failed to send password changed notification: {e}")
                # Don't fail the request if email sending fails
                pass
            
            logger.info(f"Password reset successfully for user {user.id}")
            return True
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Password reset error: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Password reset failed"
            )
    
    async def validate_reset_token(self, db: AsyncSession, token: str) -> bool:
        """Validate password reset token.
        
        Args:
            db: Database session
            token: Password reset token
            
        Returns:
            True if token is valid, False otherwise
        """
        try:
            # Verify token
            payload = self.auth_service.verify_password_reset_token(token)
            user_id = payload.get("sub")
            
            if not user_id:
                return False
            
            # Get user
            user = await self.auth_service.get_user_by_id(db, user_id)
            if not user:
                return False
            
            # Check if token matches and is not expired
            if (user.password_reset_token != token or 
                not user.password_reset_expires or 
                datetime.utcnow() > user.password_reset_expires):
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Validate reset token error: {e}")
            return False
    
    async def cleanup_expired_tokens(self, db: AsyncSession) -> int:
        """Clean up expired password reset tokens.
        
        Args:
            db: Database session
            
        Returns:
            Number of tokens cleaned up
        """
        try:
            result = await db.execute(
                select(User).where(
                    User.password_reset_expires < datetime.utcnow()
                )
            )
            users_with_expired_tokens = result.scalars().all()
            
            cleaned_count = 0
            for user in users_with_expired_tokens:
                user.password_reset_token = None
                user.password_reset_expires = None
                cleaned_count += 1
            
            await db.commit()
            
            if cleaned_count > 0:
                logger.info(f"Cleaned up {cleaned_count} expired password reset tokens")
            
            return cleaned_count
            
        except Exception as e:
            logger.error(f"Cleanup expired tokens error: {e}")
            return 0
