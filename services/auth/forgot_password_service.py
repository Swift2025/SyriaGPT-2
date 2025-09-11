from datetime import datetime, timedelta, timezone
import smtplib
from jose import JWTError, jwt
import os
from email.mime.text import MIMEText
from sqlalchemy.orm import Session
from models.domain.user import User
from services.auth import get_auth_service
from services.database import SessionLocal
from services.email import get_email_service
from fastapi import HTTPException, Depends
from config.config_loader import config_loader
import logging
import time
from services.database.database import get_db
from config.logging_config import (
    get_logger,
    log_function_entry,
    log_function_exit,
    log_performance,
    log_error_with_context
)

logger = get_logger(__name__)


class ForgotPasswordService:
    def __init__(self, db: Session):
        self.db = db
        self.auth_service = get_auth_service()
        self.secret_key = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
        self.algorithm = "HS256"
        self.reset_token_expire_minutes = 60
        
    def create_reset_token(self, email: str) -> str:
        log_function_entry(logger, "create_reset_token", email=email)
        start_time = time.time()
        try:
            user = self.db.query(User).filter(User.email == email).first()
            if not user:
                raise HTTPException(status_code=400, detail="المستخدم غير موجود")

            expire = datetime.now(timezone.utc) + timedelta(minutes=self.reset_token_expire_minutes)
            payload = {"sub": email, "exp": expire}
            token = jwt.encode(payload, self.secret_key, algorithm=self.algorithm)

            user.reset_token = token
            user.reset_token_expiry = expire
            self.db.commit()

            duration = time.time() - start_time
            log_performance(logger, "create_reset_token", duration)
            log_function_exit(logger, "create_reset_token", result=token, duration=duration)
            return token
        except Exception as e:
            duration = time.time() - start_time
            log_error_with_context(logger, e, "create_reset_token", duration=duration)
            logger.error(f"❌ Error in create_reset_token: {e}")
            log_function_exit(logger, "create_reset_token", duration=duration)
            raise
    
    async def send_reset_email(self, email: str, token: str):
        log_function_entry(logger, "send_reset_email", email=email)
        start_time = time.time()
        try:
            """Send password reset email using the email service"""
            reset_link = f"{config_loader.get_config_value('FRONTEND_URL', 'http://localhost:3000')}/reset-password?token={token}"
            
            # Use the email service instead of direct SMTP
            email_service = get_email_service()
            success, error = await email_service.send_password_reset_email(email, reset_link)
            
            if not success:
                logger.error(f"Failed to send reset email to {email}: {error}")
                # In development mode, don't fail the request, just log the error
                if os.getenv("ENV") == "development":
                    logger.warning(f"Development mode: Email not sent, but reset token created for {email}")
                    duration = time.time() - start_time
                    log_performance(logger, "send_reset_email", duration)
                    log_function_exit(logger, "send_reset_email", duration=duration)
                    return
                else:
                    raise HTTPException(status_code=500, detail=f"Failed to send reset email: {error}")
            
            logger.info(f"Password reset email sent successfully to {email}")
            duration = time.time() - start_time
            log_performance(logger, "send_reset_email", duration)
            log_function_exit(logger, "send_reset_email", duration=duration)
        except Exception as e:
            duration = time.time() - start_time
            log_error_with_context(logger, e, "send_reset_email", duration=duration)
            logger.error(f"❌ Error in send_reset_email: {e}")
            log_function_exit(logger, "send_reset_email", duration=duration)
            raise
    
    def verify_reset_token(self, token: str):
        log_function_entry(logger, "verify_reset_token")
        start_time = time.time()
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            email: str = payload.get("sub")
            if email is None:
                duration = time.time() - start_time
                log_function_exit(logger, "verify_reset_token", result=None, duration=duration)
                return None

            user = self.db.query(User).filter(User.email == email).first()
            if not user or user.reset_token != token:
                duration = time.time() - start_time
                log_function_exit(logger, "verify_reset_token", result=None, duration=duration)
                return None
            if user.reset_token_expiry < datetime.now(timezone.utc):
                duration = time.time() - start_time
                log_function_exit(logger, "verify_reset_token", result=None, duration=duration)
                return None
            
            duration = time.time() - start_time
            log_performance(logger, "verify_reset_token", duration)
            log_function_exit(logger, "verify_reset_token", result=user, duration=duration)
            return user
        except JWTError:
            duration = time.time() - start_time
            log_function_exit(logger, "verify_reset_token", result=None, duration=duration)
            return None
        except Exception as e:
            duration = time.time() - start_time
            log_error_with_context(logger, e, "verify_reset_token", duration=duration)
            logger.error(f"❌ Error in verify_reset_token: {e}")
            log_function_exit(logger, "verify_reset_token", duration=duration)
            raise
    
    def reset_password(self, token: str, new_password: str, confirm_password: str):
        log_function_entry(logger, "reset_password")
        start_time = time.time()
        try:
            user = self.verify_reset_token(token)
            if not user:
                raise HTTPException(status_code=400, detail="رمز إعادة التعيين غير صالح أو منتهي الصلاحية")

            if new_password != confirm_password:
                raise HTTPException(status_code=400, detail="كلمتا المرور غير متطابقتين")

            valid, msg = self.auth_service.validate_password_strength(new_password)
            if not valid:
                raise HTTPException(status_code=400, detail=msg)

            user.password_hash = self.auth_service.hash_password(new_password)
            user.reset_token = None
            user.reset_token_expiry = None
            user.token = None
            user.token_expiry = None
            user.last_password_change = datetime.now(timezone.utc)
            self.db.commit()
            
            duration = time.time() - start_time
            log_performance(logger, "reset_password", duration)
            log_function_exit(logger, "reset_password", result=True, duration=duration)
            return True
        except Exception as e:
            duration = time.time() - start_time
            log_error_with_context(logger, e, "reset_password", duration=duration)
            logger.error(f"❌ Error in reset_password: {e}")
            log_function_exit(logger, "reset_password", duration=duration)
            raise

# Factory function to create forgot password service with database session
def get_forgot_password_service(db: Session):
    return ForgotPasswordService(db)