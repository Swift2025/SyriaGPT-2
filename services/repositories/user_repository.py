"""
User repository for SyriaGPT.
Handles user data access operations.
"""

import logging
from typing import Optional, List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func
from sqlalchemy.orm import selectinload

from models.domain.user import User
from models.domain.chat import Chat
from models.domain.session import UserSession

logger = logging.getLogger(__name__)


class UserRepository:
    """Repository for user data access operations."""
    
    def __init__(self, db: AsyncSession):
        """Initialize user repository.
        
        Args:
            db: Database session
        """
        self.db = db
    
    async def create_user(self, user_data: Dict[str, Any]) -> User:
        """Create a new user.
        
        Args:
            user_data: User data dictionary
            
        Returns:
            Created user object
        """
        try:
            user = User(**user_data)
            self.db.add(user)
            await self.db.commit()
            await self.db.refresh(user)
            return user
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error creating user: {e}")
            raise
    
    async def get_user_by_id(self, user_id: str) -> Optional[User]:
        """Get user by ID.
        
        Args:
            user_id: User ID
            
        Returns:
            User object if found, None otherwise
        """
        try:
            result = await self.db.execute(
                select(User).where(
                    and_(
                        User.id == user_id,
                        User.is_deleted == 'N'
                    )
                )
            )
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Error getting user by ID: {e}")
            return None
    
    async def get_user_by_email(self, email: str) -> Optional[User]:
        """Get user by email.
        
        Args:
            email: User email
            
        Returns:
            User object if found, None otherwise
        """
        try:
            result = await self.db.execute(
                select(User).where(
                    and_(
                        User.email == email,
                        User.is_deleted == 'N'
                    )
                )
            )
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Error getting user by email: {e}")
            return None
    
    async def get_user_by_username(self, username: str) -> Optional[User]:
        """Get user by username.
        
        Args:
            username: Username
            
        Returns:
            User object if found, None otherwise
        """
        try:
            result = await self.db.execute(
                select(User).where(
                    and_(
                        User.username == username,
                        User.is_deleted == 'N'
                    )
                )
            )
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Error getting user by username: {e}")
            return None
    
    async def get_user_by_oauth(self, provider: str, provider_id: str) -> Optional[User]:
        """Get user by OAuth provider and ID.
        
        Args:
            provider: OAuth provider name
            provider_id: OAuth provider ID
            
        Returns:
            User object if found, None otherwise
        """
        try:
            result = await self.db.execute(
                select(User).where(
                    and_(
                        User.oauth_provider == provider,
                        User.oauth_provider_id == provider_id,
                        User.is_deleted == 'N'
                    )
                )
            )
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Error getting user by OAuth: {e}")
            return None
    
    async def update_user(self, user: User, update_data: Dict[str, Any]) -> User:
        """Update user data.
        
        Args:
            user: User object
            update_data: Data to update
            
        Returns:
            Updated user object
        """
        try:
            for key, value in update_data.items():
                if hasattr(user, key):
                    setattr(user, key, value)
            
            await self.db.commit()
            await self.db.refresh(user)
            return user
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error updating user: {e}")
            raise
    
    async def delete_user(self, user: User) -> bool:
        """Soft delete user.
        
        Args:
            user: User object
            
        Returns:
            True if successful, False otherwise
        """
        try:
            user.soft_delete()
            await self.db.commit()
            return True
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error deleting user: {e}")
            return False
    
    async def get_users(
        self,
        skip: int = 0,
        limit: int = 100,
        active_only: bool = True,
        verified_only: bool = False
    ) -> List[User]:
        """Get list of users with pagination and filters.
        
        Args:
            skip: Number of records to skip
            limit: Maximum number of records to return
            active_only: Return only active users
            verified_only: Return only verified users
            
        Returns:
            List of user objects
        """
        try:
            query = select(User).where(User.is_deleted == 'N')
            
            if active_only:
                query = query.where(User.is_active == True)
            
            if verified_only:
                query = query.where(User.is_verified == True)
            
            query = query.offset(skip).limit(limit)
            
            result = await self.db.execute(query)
            return result.scalars().all()
        except Exception as e:
            logger.error(f"Error getting users: {e}")
            return []
    
    async def count_users(self, active_only: bool = True) -> int:
        """Count total number of users.
        
        Args:
            active_only: Count only active users
            
        Returns:
            Total number of users
        """
        try:
            query = select(func.count(User.id)).where(User.is_deleted == 'N')
            
            if active_only:
                query = query.where(User.is_active == True)
            
            result = await self.db.execute(query)
            return result.scalar() or 0
        except Exception as e:
            logger.error(f"Error counting users: {e}")
            return 0
    
    async def search_users(
        self,
        search_term: str,
        skip: int = 0,
        limit: int = 100
    ) -> List[User]:
        """Search users by name, email, or username.
        
        Args:
            search_term: Search term
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List of matching user objects
        """
        try:
            search_pattern = f"%{search_term}%"
            
            query = select(User).where(
                and_(
                    User.is_deleted == 'N',
                    or_(
                        User.email.ilike(search_pattern),
                        User.username.ilike(search_pattern),
                        User.first_name.ilike(search_pattern),
                        User.last_name.ilike(search_pattern),
                        User.full_name.ilike(search_pattern)
                    )
                )
            ).offset(skip).limit(limit)
            
            result = await self.db.execute(query)
            return result.scalars().all()
        except Exception as e:
            logger.error(f"Error searching users: {e}")
            return []
    
    async def get_user_with_sessions(self, user_id: str) -> Optional[User]:
        """Get user with their active sessions.
        
        Args:
            user_id: User ID
            
        Returns:
            User object with sessions if found, None otherwise
        """
        try:
            result = await self.db.execute(
                select(User)
                .options(selectinload(User.sessions))
                .where(
                    and_(
                        User.id == user_id,
                        User.is_deleted == 'N'
                    )
                )
            )
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Error getting user with sessions: {e}")
            return None
    
    async def get_user_with_chats(self, user_id: str) -> Optional[User]:
        """Get user with their chats.
        
        Args:
            user_id: User ID
            
        Returns:
            User object with chats if found, None otherwise
        """
        try:
            result = await self.db.execute(
                select(User)
                .options(selectinload(User.chats))
                .where(
                    and_(
                        User.id == user_id,
                        User.is_deleted == 'N'
                    )
                )
            )
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Error getting user with chats: {e}")
            return None
