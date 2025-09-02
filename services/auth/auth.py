from datetime import datetime, timedelta, timezone
from typing import Optional, Union
from passlib.context import CryptContext
from jose import JWTError, jwt
import os
import secrets
import string
import logging
import time
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from config.config_loader import config_loader
from config.logging_config import get_logger, log_function_entry, log_function_exit, log_performance, log_error_with_context
from services.repositories import get_user_repository

logger = get_logger(__name__)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

class AuthService:
    def __init__(self):
        log_function_entry(logger, "__init__")
        start_time = time.time()
        
        logger.debug("🔧 Initializing AuthService...")
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        self.secret_key = os.getenv("SECRET_KEY")
        if not self.secret_key:
            logger.error("❌ SECRET_KEY environment variable must be set")
            log_error_with_context(logger, ValueError("SECRET_KEY not set"), "AuthService initialization")
            raise ValueError("SECRET_KEY environment variable must be set")
        self.algorithm = "HS256"
        self.access_token_expire_minutes = 30
        
        duration = time.time() - start_time
        log_performance(logger, "AuthService initialization", duration)
        logger.debug(f"✅ AuthService initialized with algorithm: {self.algorithm}, token expiry: {self.access_token_expire_minutes} minutes")
        log_function_exit(logger, "__init__", duration=duration)

    def hash_password(self, password: str) -> str:
        log_function_entry(logger, "hash_password", password_length=len(password))
        start_time = time.time()
        
        logger.debug("🔧 Hashing password...")
        try:
            hashed_password = self.pwd_context.hash(password)
            duration = time.time() - start_time
            log_performance(logger, "Password hashing", duration)
            logger.debug("✅ Password hashed successfully")
            log_function_exit(logger, "hash_password", duration=duration)
            return hashed_password
        except Exception as e:
            duration = time.time() - start_time
            log_error_with_context(logger, e, "hash_password", password_length=len(password), duration=duration)
            logger.error(f"❌ Password hashing failed: {e}")
            log_function_exit(logger, "hash_password", duration=duration)
            raise

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        log_function_entry(logger, "verify_password", plain_password_length=len(plain_password), hashed_password_length=len(hashed_password))
        start_time = time.time()
        
        logger.debug("🔧 Verifying password...")
        try:
            is_valid = self.pwd_context.verify(plain_password, hashed_password)
            duration = time.time() - start_time
            log_performance(logger, "Password verification", duration)
            logger.debug(f"✅ Password verification result: {is_valid}")
            log_function_exit(logger, "verify_password", result=is_valid, duration=duration)
            return is_valid
        except Exception as e:
            duration = time.time() - start_time
            log_error_with_context(logger, e, "verify_password", plain_password_length=len(plain_password), duration=duration)
            logger.error(f"❌ Password verification failed: {e}")
            log_function_exit(logger, "verify_password", duration=duration)
            raise

    def create_access_token(self, data: dict, expires_delta: Optional[timedelta] = None) -> str:
        log_function_entry(logger, "create_access_token", data_keys=list(data.keys()), has_expires_delta=expires_delta is not None)
        start_time = time.time()
        
        logger.debug(f"🔧 Creating access token for data: {list(data.keys())}")
        try:
            to_encode = data.copy()
            if expires_delta:
                expire = datetime.now(timezone.utc) + expires_delta
                logger.debug(f"🔧 Token expiry set to: {expire}")
            else:
                # Set default expiration to 30 minutes if not provided
                expire = datetime.now(timezone.utc) + timedelta(minutes=self.access_token_expire_minutes)
                logger.debug(f"🔧 Token expiry set to default: {expire}")
            
            to_encode.update({"exp": expire})
            encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
            
            duration = time.time() - start_time
            log_performance(logger, "Access token creation", duration)
            logger.debug("✅ Access token created successfully")
            log_function_exit(logger, "create_access_token", duration=duration)
            return encoded_jwt
            
        except Exception as e:
            duration = time.time() - start_time
            log_error_with_context(logger, e, "create_access_token", data_keys=list(data.keys()), duration=duration)
            logger.error(f"❌ Access token creation failed: {e}")
            log_function_exit(logger, "create_access_token", duration=duration)
            raise

    def verify_token(self, token: str) -> Optional[dict]:
        log_function_entry(logger, "verify_token", token_length=len(token))
        start_time = time.time()
        
        logger.debug("🔧 Verifying JWT token...")
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            duration = time.time() - start_time
            log_performance(logger, "Token verification", duration)
            logger.debug(f"✅ Token verified successfully, payload keys: {list(payload.keys())}")
            log_function_exit(logger, "verify_token", result="success", duration=duration)
            return payload
        except JWTError as e:
            duration = time.time() - start_time
            log_error_with_context(logger, e, "verify_token", token_length=len(token), duration=duration)
            logger.warning(f"❌ Token verification failed: {e}")
            log_function_exit(logger, "verify_token", result="failed", duration=duration)
            return None

    def generate_verification_token(self, length: int = 32) -> str:
        logger.debug(f"Generating verification token with length: {length}")
        alphabet = string.ascii_letters + string.digits
        token = ''.join(secrets.choice(alphabet) for _ in range(length))
        logger.debug("Verification token generated successfully")
        return token

    def validate_password_strength(self, password: str) -> tuple[bool, str]:
        logger.debug("Validating password strength")
        
        if len(password) < 8:
            logger.debug("Password validation failed: too short")
            return False, config_loader.get_message("validation", "password_too_short")
        
        if not any(c.isupper() for c in password):
            logger.debug("Password validation failed: no uppercase")
            return False, config_loader.get_message("validation", "password_no_uppercase")
        
        if not any(c.islower() for c in password):
            logger.debug("Password validation failed: no lowercase")
            return False, config_loader.get_message("validation", "password_no_lowercase")
        
        if not any(c.isdigit() for c in password):
            logger.debug("Password validation failed: no number")
            return False, config_loader.get_message("validation", "password_no_number")
        
        if not any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password):
            logger.debug("Password validation failed: no special character")
            return False, config_loader.get_message("validation", "password_no_special")
        
        logger.debug("Password validation passed: strong password")
        return True, config_loader.get_message("validation", "password_strong")
    

# get_current_user function moved to services/dependencies.py to avoid duplication

# Lazy loading to avoid environment variable issues during import
_auth_service_instance = None

def get_auth_service():
    global _auth_service_instance
    if _auth_service_instance is None:
        logger.debug("Creating new AuthService instance")
        _auth_service_instance = AuthService()
    else:
        logger.debug("Returning existing AuthService instance")
    return _auth_service_instance