# Authentication utilities to break circular dependencies
from fastapi import Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError
import logging
import os
from datetime import datetime, timedelta, timezone
from jose import jwt
from passlib.context import CryptContext

from services.database.database import get_db
from config.logging_config import get_logger

logger = get_logger(__name__)

# OAuth2 scheme for token validation
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_token_direct(token: str) -> dict:
    """Verify JWT token without importing auth service"""
    try:
        secret_key = os.getenv("SECRET_KEY")
        if not secret_key:
            raise ValueError("SECRET_KEY environment variable must be set")
        
        algorithm = "HS256"
        payload = jwt.decode(token, secret_key, algorithms=[algorithm])
        return payload
    except JWTError as e:
        logger.error(f"JWT token validation error: {e}")
        return None
    except Exception as e:
        logger.error(f"Token verification error: {e}")
        return None

def get_current_user_simple(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    """Simplified current user dependency that avoids circular imports"""
    logger.debug("Authenticating user with token")
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        logger.debug("Verifying token")
        payload = verify_token_direct(token)
        if payload is None:
            logger.error("Token verification failed - payload is None")
            raise credentials_exception
        
        email: str = payload.get("sub")
        if email is None:
            logger.error("Token payload missing 'sub' field")
            raise credentials_exception
        
        logger.info(f"Token validated successfully for email: {email}")
        
    except JWTError as e:
        logger.error(f"JWT token validation error: {e}")
        raise credentials_exception
    
    logger.debug("Getting user repository")
    # Import here to avoid circular dependency
    from services.repositories import get_user_repository
    user_repo = get_user_repository()
    logger.debug(f"Looking up user by email: {email}")
    user = user_repo.get_user_by_email(db, email)
    
    if user is None:
        logger.error(f"User not found in database for email: {email}")
        raise credentials_exception
    
    logger.info(f"User authenticated successfully: {user.email}")
    return user
