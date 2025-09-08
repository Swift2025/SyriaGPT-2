"""
Session management service for SyriaGPT.
Handles user session creation, validation, and management.
"""

import logging
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from fastapi import HTTPException, status

from models.domain.user import User
from models.domain.session import UserSession
from config.config_loader import ConfigLoader

logger = logging.getLogger(__name__)


class SessionManagementService:
    """Session management service for handling user sessions."""
    
    def __init__(self, config: ConfigLoader):
        """Initialize session management service.
        
        Args:
            config: Configuration loader instance
        """
        self.config = config
        self.jwt_config = config.get_jwt_config()
    
    async def create_session(
        self,
        db: AsyncSession,
        user: User,
        access_token: str,
        refresh_token: str,
        remember_me: bool = False,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        device_info: Optional[Dict[str, Any]] = None,
        location_info: Optional[Dict[str, Any]] = None
    ) -> UserSession:
        """Create a new user session.
        
        Args:
            db: Database session
            user: User object
            access_token: JWT access token
            refresh_token: JWT refresh token
            remember_me: Whether to remember the session longer
            ip_address: Client IP address
            user_agent: Client user agent
            device_info: Device information
            location_info: Location information
            
        Returns:
            Created session object
        """
        try:
            # Determine session duration
            if remember_me:
                expires_hours = 30 * 24  # 30 days
            else:
                expires_hours = 24  # 1 day
            
            # Create session
            session = UserSession.create_session(
                user_id=str(user.id),
                session_token=access_token,
                refresh_token=refresh_token,
                expires_hours=expires_hours,
                ip_address=ip_address,
                user_agent=user_agent,
                device_info=device_info,
                location_info=location_info
            )
            
            db.add(session)
            await db.commit()
            await db.refresh(session)
            
            logger.info(f"Session created for user {user.id}")
            return session
            
        except Exception as e:
            logger.error(f"Session creation error: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create session"
            )
    
    async def get_session_by_token(self, db: AsyncSession, token: str) -> Optional[UserSession]:
        """Get session by token.
        
        Args:
            db: Database session
            token: Session token
            
        Returns:
            Session object if found and valid, None otherwise
        """
        try:
            result = await db.execute(
                select(UserSession).where(
                    and_(
                        UserSession.session_token == token,
                        UserSession.is_active == True,
                        UserSession.is_revoked == False,
                        UserSession.expires_at > datetime.utcnow(),
                        UserSession.is_deleted == 'N'
                    )
                )
            )
            session = result.scalar_one_or_none()
            
            if session:
                # Update last activity
                session.update_activity()
                await db.commit()
            
            return session
            
        except Exception as e:
            logger.error(f"Session retrieval error: {e}")
            return None
    
    async def get_session_by_refresh_token(self, db: AsyncSession, refresh_token: str) -> Optional[UserSession]:
        """Get session by refresh token.
        
        Args:
            db: Database session
            refresh_token: Refresh token
            
        Returns:
            Session object if found and valid, None otherwise
        """
        try:
            result = await db.execute(
                select(UserSession).where(
                    and_(
                        UserSession.refresh_token == refresh_token,
                        UserSession.is_active == True,
                        UserSession.is_revoked == False,
                        UserSession.expires_at > datetime.utcnow(),
                        UserSession.is_deleted == 'N'
                    )
                )
            )
            return result.scalar_one_or_none()
            
        except Exception as e:
            logger.error(f"Session retrieval by refresh token error: {e}")
            return None
    
    async def revoke_session(self, db: AsyncSession, session: UserSession) -> bool:
        """Revoke a session.
        
        Args:
            db: Database session
            session: Session object
            
        Returns:
            True if revoked successfully
        """
        try:
            session.revoke_session()
            await db.commit()
            
            logger.info(f"Session revoked: {session.id}")
            return True
            
        except Exception as e:
            logger.error(f"Session revocation error: {e}")
            return False
    
    async def revoke_session_by_token(self, db: AsyncSession, token: str) -> bool:
        """Revoke session by token.
        
        Args:
            db: Database session
            token: Session token
            
        Returns:
            True if revoked successfully
        """
        try:
            session = await self.get_session_by_token(db, token)
            if session:
                return await self.revoke_session(db, session)
            return False
            
        except Exception as e:
            logger.error(f"Session revocation by token error: {e}")
            return False
    
    async def revoke_all_user_sessions(self, db: AsyncSession, user: User) -> int:
        """Revoke all sessions for a user.
        
        Args:
            db: Database session
            user: User object
            
        Returns:
            Number of sessions revoked
        """
        try:
            result = await db.execute(
                select(UserSession).where(
                    and_(
                        UserSession.user_id == user.id,
                        UserSession.is_active == True,
                        UserSession.is_revoked == False,
                        UserSession.is_deleted == 'N'
                    )
                )
            )
            sessions = result.scalars().all()
            
            revoked_count = 0
            for session in sessions:
                session.revoke_session()
                revoked_count += 1
            
            await db.commit()
            
            logger.info(f"Revoked {revoked_count} sessions for user {user.id}")
            return revoked_count
            
        except Exception as e:
            logger.error(f"Revoke all sessions error: {e}")
            return 0
    
    async def get_user_sessions(self, db: AsyncSession, user: User, active_only: bool = True) -> List[UserSession]:
        """Get all sessions for a user.
        
        Args:
            db: Database session
            user: User object
            active_only: Whether to return only active sessions
            
        Returns:
            List of session objects
        """
        try:
            query = select(UserSession).where(
                and_(
                    UserSession.user_id == user.id,
                    UserSession.is_deleted == 'N'
                )
            )
            
            if active_only:
                query = query.where(
                    and_(
                        UserSession.is_active == True,
                        UserSession.is_revoked == False,
                        UserSession.expires_at > datetime.utcnow()
                    )
                )
            
            result = await db.execute(query)
            return result.scalars().all()
            
        except Exception as e:
            logger.error(f"Get user sessions error: {e}")
            return []
    
    async def update_session_tokens(
        self,
        db: AsyncSession,
        old_refresh_token: str,
        new_access_token: str,
        new_refresh_token: str
    ) -> bool:
        """Update session tokens.
        
        Args:
            db: Database session
            old_refresh_token: Old refresh token
            new_access_token: New access token
            new_refresh_token: New refresh token
            
        Returns:
            True if updated successfully
        """
        try:
            session = await self.get_session_by_refresh_token(db, old_refresh_token)
            if not session:
                return False
            
            session.session_token = new_access_token
            session.refresh_token = new_refresh_token
            session.update_activity()
            
            await db.commit()
            return True
            
        except Exception as e:
            logger.error(f"Update session tokens error: {e}")
            return False
    
    async def extend_session(self, db: AsyncSession, session: UserSession, hours: int = 24) -> bool:
        """Extend session expiration.
        
        Args:
            db: Database session
            session: Session object
            hours: Hours to extend
            
        Returns:
            True if extended successfully
        """
        try:
            session.extend_session(hours)
            await db.commit()
            return True
            
        except Exception as e:
            logger.error(f"Extend session error: {e}")
            return False
    
    async def cleanup_expired_sessions(self, db: AsyncSession) -> int:
        """Clean up expired sessions.
        
        Args:
            db: Database session
            
        Returns:
            Number of sessions cleaned up
        """
        try:
            result = await db.execute(
                select(UserSession).where(
                    and_(
                        UserSession.expires_at < datetime.utcnow(),
                        UserSession.is_deleted == 'N'
                    )
                )
            )
            expired_sessions = result.scalars().all()
            
            cleaned_count = 0
            for session in expired_sessions:
                session.revoke_session()
                cleaned_count += 1
            
            await db.commit()
            
            if cleaned_count > 0:
                logger.info(f"Cleaned up {cleaned_count} expired sessions")
            
            return cleaned_count
            
        except Exception as e:
            logger.error(f"Cleanup expired sessions error: {e}")
            return 0
    
    async def get_session_stats(self, db: AsyncSession, user: User) -> Dict[str, Any]:
        """Get session statistics for user.
        
        Args:
            db: Database session
            user: User object
            
        Returns:
            Session statistics
        """
        try:
            sessions = await self.get_user_sessions(db, user, active_only=False)
            
            active_sessions = [s for s in sessions if s.is_valid]
            expired_sessions = [s for s in sessions if s.is_expired]
            revoked_sessions = [s for s in sessions if s.is_revoked]
            
            return {
                "total_sessions": len(sessions),
                "active_sessions": len(active_sessions),
                "expired_sessions": len(expired_sessions),
                "revoked_sessions": len(revoked_sessions),
                "last_activity": max([s.last_activity_at for s in active_sessions]) if active_sessions else None
            }
            
        except Exception as e:
            logger.error(f"Get session stats error: {e}")
            return {
                "total_sessions": 0,
                "active_sessions": 0,
                "expired_sessions": 0,
                "revoked_sessions": 0,
                "last_activity": None
            }
