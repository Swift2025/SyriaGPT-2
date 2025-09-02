# In SyriaGPT/api/authentication/two_factor.py

from fastapi import HTTPException, status, Depends
from sqlalchemy.orm import Session
from models.domain.user import User
from models.schemas.response_models import TwoFactorSetupResponse, GeneralResponse
from models.schemas.request_models import TwoFactorVerifyRequest
from services.repositories import get_user_repository
from services.auth import get_two_factor_auth_service
from services.database.database import get_db
from services.database.redis_service import redis_service
import time
from config.logging_config import get_logger, log_function_entry, log_function_exit, log_performance, log_error_with_context
import logging

logger = get_logger(__name__)

class TwoFactorService:
    def __init__(self):
        self.max_attempts = 5  # Maximum attempts per user
        self.lockout_duration = 300  # 5 minutes lockout
        self.attempt_window = 600  # 10 minutes window for attempts
    
    def _get_rate_limit_key(self, user_id: str) -> str:
        """Generate Redis key for rate limiting"""
        return f"2fa_rate_limit:{user_id}"
    
    def _check_rate_limit(self, user_id: str) -> bool:
        """Check if user is rate limited"""
        try:
            if not redis_service.is_connected():
                return False  # Allow if Redis is not available
            
            key = self._get_rate_limit_key(user_id)
            current_time = int(time.time())
            
            # Get current attempts
            attempts_data = redis_service.get_custom_data(key)
            if not attempts_data:
                return False  # No previous attempts
            
            attempts = attempts_data.get("attempts", [])
            window_start = current_time - self.attempt_window
            
            # Remove old attempts outside the window
            recent_attempts = [t for t in attempts if t > window_start]
            
            # Check if user is locked out
            if len(recent_attempts) >= self.max_attempts:
                return True  # Rate limited
            
            return False
            
        except Exception as e:
            logger.error(f"Rate limit check failed: {e}")
            return False  # Allow if rate limiting fails
    
    def _record_attempt(self, user_id: str, success: bool):
        """Record a 2FA attempt"""
        try:
            if not redis_service.is_connected():
                return
            
            key = self._get_rate_limit_key(user_id)
            current_time = int(time.time())
            
            attempts_data = redis_service.get_custom_data(key) or {"attempts": []}
            attempts = attempts_data.get("attempts", [])
            
            if success:
                # Clear attempts on success
                attempts_data["attempts"] = []
            else:
                # Add failed attempt
                attempts.append(current_time)
                attempts_data["attempts"] = attempts
            
            # Store with expiry
            redis_service.cache_custom_data(key, attempts_data, expiry=self.lockout_duration)
            
        except Exception as e:
            logger.error(f"Failed to record 2FA attempt: {e}")

    def setup_2fa(self, current_user: User, db: Session):
        log_function_entry(logger, "setup_2fa")
        start_time = time.time()
        try:
            # 1. Generate a new secret
            two_factor_service = get_two_factor_auth_service()
            secret = two_factor_service.generate_secret()

            # 2. Update user with the new secret (but don't enable it yet)
            user_repo = get_user_repository()
            user_repo.update_user(db, str(current_user.id), {"two_factor_secret": secret, "two_factor_enabled": False})

            # 3. Generate QR code
            uri = two_factor_service.get_provisioning_uri(current_user.email, secret)
            qr_code = two_factor_service.generate_qr_code(uri)

            return TwoFactorSetupResponse(secret_key=secret, qr_code=qr_code)
        except Exception as e:
            duration = time.time() - start_time
            log_error_with_context(logger, e, "setup_2fa", duration=duration)
            logger.error(f"❌ Error in setup_2fa: {e}")
            log_function_exit(logger, "setup_2fa", duration=duration)
            raise

    def verify_and_enable_2fa(self, current_user: User, verify_data: TwoFactorVerifyRequest, db: Session):
        if not current_user.two_factor_secret:
            raise HTTPException(status_code=400, detail="2FA is not set up. Please set it up first.")

        # Check rate limiting
        if self._check_rate_limit(str(current_user.id)):
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS, 
                detail="Too many 2FA verification attempts. Please try again later."
            )

        # 1. Verify the code
        two_factor_service = get_two_factor_auth_service()
        is_valid = two_factor_service.verify_code(current_user.two_factor_secret, verify_data.code)
        
        # Record the attempt
        self._record_attempt(str(current_user.id), is_valid)
        
        if not is_valid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, 
                detail="Invalid 2FA code."
            )

        # 2. Enable 2FA for the user
        user_repo = get_user_repository()
        user_repo.update_user(db, str(current_user.id), {"two_factor_enabled": True})

        return GeneralResponse(status="success", message="2FA has been successfully enabled.")

    def disable_2fa(self, current_user: User, db: Session):
        if not current_user.two_factor_enabled:
            raise HTTPException(status_code=400, detail="2FA is not currently enabled.")

        # Disable 2FA
        user_repo = get_user_repository()
        user_repo.update_user(db, str(current_user.id), {"two_factor_enabled": False, "two_factor_secret": None})
        
        return GeneralResponse(status="success", message="2FA has been disabled.")