# In SyriaGPT/services/dependencies.py

from fastapi import Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError
from slowapi import Limiter
from slowapi.util import get_remote_address
import logging
import time

from services.auth import get_auth_service, oauth2_scheme
from services.database.database import get_db
from config.logging_config import get_logger

logger = get_logger(__name__)
# Removed direct import - using get_user_repository() function instead

limiter = Limiter(key_func=get_remote_address)

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    logger.debug("Authenticating user with token")
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        logger.debug("Getting auth service")
        auth_service = get_auth_service()
        logger.debug("Verifying token")
        payload = auth_service.verify_token(token)
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
    from services.repositories import get_user_repository
    user_repo = get_user_repository()
    logger.debug(f"Looking up user by email: {email}")
    user = user_repo.get_user_by_email(db, email)
    
    if user is None:
        logger.error(f"User not found in database for email: {email}")
        raise credentials_exception
    
    logger.info(f"User authenticated successfully: {user.email}")
    return user
