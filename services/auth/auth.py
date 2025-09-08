"""
Authentication service for SyriaGPT.
Handles JWT token generation, validation, and user authentication.
"""

import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, Tuple
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import HTTPException, status

from models.domain.user import User
from models.domain.session import UserSession
from config.config_loader import ConfigLoader

logger = logging.getLogger(__name__)


class AuthService:
    """Authentication service for handling JWT tokens and user authentication."""
    
    def __init__(self, config: ConfigLoader):
        """Initialize authentication service.
        
        Args:
            config: Configuration loader instance
        """
        self.config = config
        self.jwt_config = config.get_jwt_config()
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        
        # JWT settings
        self.secret_key = self.jwt_config["secret_key"]
        self.algorithm = self.jwt_config["algorithm"]
        self.access_token_expire_minutes = self.jwt_config["access_token_expire_minutes"]
        self.refresh_token_expire_days = self.jwt_config["refresh_token_expire_days"]
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash.
        
        Args:
            plain_password: Plain text password
            hashed_password: Hashed password
            
        Returns:
            True if password matches, False otherwise
        """
        try:
            return self.pwd_context.verify(plain_password, hashed_password)
        except Exception as e:
            logger.error(f"Password verification error: {e}")
            return False
    
    def get_password_hash(self, password: str) -> str:
        """Generate password hash.
        
        Args:
            password: Plain text password
            
        Returns:
            Hashed password
        """
        return self.pwd_context.hash(password)
    
    def create_access_token(self, data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
        """Create JWT access token.
        
        Args:
            data: Token payload data
            expires_delta: Token expiration time
            
        Returns:
            JWT access token
        """
        to_encode = data.copy()
        
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=self.access_token_expire_minutes)
        
        to_encode.update({"exp": expire, "type": "access"})
        
        try:
            encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
            return encoded_jwt
        except Exception as e:
            logger.error(f"Token creation error: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Token creation failed"
            )
    
    def create_refresh_token(self, data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
        """Create JWT refresh token.
        
        Args:
            data: Token payload data
            expires_delta: Token expiration time
            
        Returns:
            JWT refresh token
        """
        to_encode = data.copy()
        
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(days=self.refresh_token_expire_days)
        
        to_encode.update({"exp": expire, "type": "refresh"})
        
        try:
            encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
            return encoded_jwt
        except Exception as e:
            logger.error(f"Refresh token creation error: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Refresh token creation failed"
            )
    
    def verify_token(self, token: str, token_type: str = "access") -> Dict[str, Any]:
        """Verify and decode JWT token.
        
        Args:
            token: JWT token to verify
            token_type: Expected token type (access or refresh)
            
        Returns:
            Decoded token payload
            
        Raises:
            HTTPException: If token is invalid or expired
        """
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            
            # Check token type
            if payload.get("type") != token_type:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail=f"Invalid token type. Expected {token_type}"
                )
            
            # Check expiration
            exp = payload.get("exp")
            if exp is None or datetime.utcnow() > datetime.fromtimestamp(exp):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Token has expired"
                )
            
            return payload
            
        except JWTError as e:
            logger.error(f"Token verification error: {e}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )
    
    async def authenticate_user(self, db: AsyncSession, email: str, password: str) -> Optional[User]:
        """Authenticate user with email and password.
        
        Args:
            db: Database session
            email: User email
            password: User password
            
        Returns:
            User object if authentication successful, None otherwise
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
                logger.warning(f"Authentication failed: User not found for email {email}")
                return None
            
            # Check if account is locked
            if user.is_locked:
                logger.warning(f"Authentication failed: Account locked for user {user.id}")
                return None
            
            # Verify password
            if not self.verify_password(password, user.password_hash):
                # Increment failed login attempts
                user.increment_failed_login()
                await db.commit()
                
                logger.warning(f"Authentication failed: Invalid password for user {user.id}")
                return None
            
            # Reset failed login attempts on successful login
            user.reset_failed_login_attempts()
            user.increment_login_count()
            await db.commit()
            
            logger.info(f"User {user.id} authenticated successfully")
            return user
            
        except Exception as e:
            logger.error(f"Authentication error: {e}")
            return None
    
    async def get_user_by_id(self, db: AsyncSession, user_id: str) -> Optional[User]:
        """Get user by ID.
        
        Args:
            db: Database session
            user_id: User ID
            
        Returns:
            User object if found, None otherwise
        """
        try:
            result = await db.execute(
                select(User).where(
                    User.id == user_id,
                    User.is_active == True,
                    User.is_deleted == 'N'
                )
            )
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Error getting user by ID {user_id}: {e}")
            return None
    
    async def get_user_by_email(self, db: AsyncSession, email: str) -> Optional[User]:
        """Get user by email.
        
        Args:
            db: Database session
            email: User email
            
        Returns:
            User object if found, None otherwise
        """
        try:
            result = await db.execute(
                select(User).where(
                    User.email == email,
                    User.is_deleted == 'N'
                )
            )
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Error getting user by email {email}: {e}")
            return None
    
    def create_token_pair(self, user: User) -> Tuple[str, str]:
        """Create access and refresh token pair for user.
        
        Args:
            user: User object
            
        Returns:
            Tuple of (access_token, refresh_token)
        """
        token_data = {
            "sub": str(user.id),
            "email": user.email,
            "username": user.username,
            "is_verified": user.is_verified,
            "is_superuser": user.is_superuser
        }
        
        access_token = self.create_access_token(token_data)
        refresh_token = self.create_refresh_token(token_data)
        
        return access_token, refresh_token
    
    def extract_token_from_header(self, authorization: str) -> str:
        """Extract token from Authorization header.
        
        Args:
            authorization: Authorization header value
            
        Returns:
            Extracted token
            
        Raises:
            HTTPException: If header format is invalid
        """
        if not authorization:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authorization header missing"
            )
        
        try:
            scheme, token = authorization.split()
            if scheme.lower() != "bearer":
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid authentication scheme"
                )
            return token
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authorization header format"
            )
    
    async def get_current_user(self, db: AsyncSession, token: str) -> User:
        """Get current user from JWT token.
        
        Args:
            db: Database session
            token: JWT access token
            
        Returns:
            Current user object
            
        Raises:
            HTTPException: If token is invalid or user not found
        """
        try:
            payload = self.verify_token(token, "access")
            user_id = payload.get("sub")
            
            if not user_id:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid token payload"
                )
            
            user = await self.get_user_by_id(db, user_id)
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="User not found"
                )
            
            return user
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error getting current user: {e}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication failed"
            )
    
    def validate_password_strength(self, password: str) -> Tuple[bool, str]:
        """Validate password strength.
        
        Args:
            password: Password to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if len(password) < 8:
            return False, "Password must be at least 8 characters long"
        
        if not any(c.isupper() for c in password):
            return False, "Password must contain at least one uppercase letter"
        
        if not any(c.islower() for c in password):
            return False, "Password must contain at least one lowercase letter"
        
        if not any(c.isdigit() for c in password):
            return False, "Password must contain at least one digit"
        
        if not any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password):
            return False, "Password must contain at least one special character"
        
        return True, ""
    
    def generate_password_reset_token(self, user: User) -> str:
        """Generate password reset token.
        
        Args:
            user: User object
            
        Returns:
            Password reset token
        """
        data = {
            "sub": str(user.id),
            "email": user.email,
            "type": "password_reset"
        }
        
        # Password reset tokens expire in 1 hour
        expires_delta = timedelta(hours=1)
        return self.create_access_token(data, expires_delta)
    
    def verify_password_reset_token(self, token: str) -> Dict[str, Any]:
        """Verify password reset token.
        
        Args:
            token: Password reset token
            
        Returns:
            Decoded token payload
            
        Raises:
            HTTPException: If token is invalid
        """
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            
            if payload.get("type") != "password_reset":
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid token type"
                )
            
            return payload
            
        except JWTError as e:
            logger.error(f"Password reset token verification error: {e}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired password reset token"
            )
