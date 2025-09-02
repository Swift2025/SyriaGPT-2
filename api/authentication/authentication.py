# /api/authentication/authentication.py

from fastapi import HTTPException, status, Request, Depends
from sqlalchemy.orm import Session
from datetime import datetime, timezone, timedelta
import logging
import time

from models.schemas.request_models import SocialLoginRequest, UserLoginRequest
from models.schemas.response_models import LoginResponse, ErrorResponse
from services.auth import get_oauth_service
from services.repositories import get_user_repository
from services.auth import get_auth_service
from config.config_loader import config_loader
from services.auth import get_two_factor_auth_service
from services.database.database import get_db
from config.logging_config import (
    get_logger,
    log_function_entry,
    log_function_exit,
    log_performance,
    log_error_with_context
)

logger = get_logger(__name__)

class AuthenticationService:
    def __init__(self):
        logger.debug("Initializing AuthenticationService")
        self.user_repository = get_user_repository()
        self.config_loader = config_loader
        logger.debug("AuthenticationService initialized successfully")
    
    @property
    def oauth_service(self):
        log_function_entry(logger, "oauth_service")
        start_time = time.time()
        try:
            service = get_oauth_service()
            duration = time.time() - start_time
            log_performance(logger, "oauth_service", duration)
            log_function_exit(logger, "oauth_service", duration=duration)
            return service
        except Exception as e:
            duration = time.time() - start_time
            log_error_with_context(logger, e, "oauth_service", duration=duration)
            logger.error(f"❌ Error in oauth_service: {e}")
            log_function_exit(logger, "oauth_service", duration=duration)
            raise
    
    @property
    def auth_service(self):
        log_function_entry(logger, "auth_service")
        start_time = time.time()
        try:
            service = get_auth_service()
            duration = time.time() - start_time
            log_performance(logger, "auth_service", duration)
            log_function_exit(logger, "auth_service", duration=duration)
            return service
        except Exception as e:
            duration = time.time() - start_time
            log_error_with_context(logger, e, "auth_service", duration=duration)
            logger.error(f"❌ Error in auth_service: {e}")
            log_function_exit(logger, "auth_service", duration=duration)
            raise

    async def social_login(self, request_data: SocialLoginRequest, request: Request, db: Session):
        log_function_entry(logger, "social_login", provider=request_data.provider)
        start_time = time.time()
        try:
            logger.debug(f"Social login attempt for provider: {request_data.provider}")
            redirect_uri = request_data.redirect_uri or f"{request.base_url}auth/oauth/{request_data.provider}/callback"
            
            # 1. الحصول على معلومات المستخدم من جوجل
            logger.debug("Getting user info from OAuth provider")
            user_info = await self.oauth_service.get_user_info(
                request_data.provider, request_data.code, redirect_uri
            )
            if not user_info:
                logger.error("Failed to get user info from OAuth provider")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=self.config_loader.get_message("errors", "oauth_user_info_failed")
                )
                
            # 2. البحث عن المستخدم في قاعدة البيانات
            provider_id = user_info.get("provider_id")
            logger.debug(f"Looking up user by OAuth provider: {request_data.provider}, provider_id: {provider_id}")
            user = self.user_repository.find_user_by_oauth(db, request_data.provider, provider_id)

            # 3. إذا لم يكن المستخدم موجوداً، قم بإنشاء حساب جديد
            if not user:
                logger.debug("OAuth user not found, creating new user")
                user, error = self.user_repository.create_oauth_user(db, user_info)
                if error:
                    logger.error(f"OAuth user creation failed: {error}")
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST, 
                        detail=self.config_loader.get_message("errors", "oauth_account_creation_failed")
                    )
                logger.debug(f"OAuth user created successfully: {user.email}")
            else:
                logger.debug(f"OAuth user found: {user.email}")
            
            # 4. تحديث تاريخ آخر تسجيل دخول و OAuth tokens
            logger.debug("Updating user login information and OAuth tokens")
            oauth_tokens = user_info.get("oauth_tokens", {})
            update_data = {
                "last_login_at": datetime.now(timezone.utc)
            }
            
            # Update OAuth tokens if available
            if oauth_tokens.get("access_token"):
                logger.debug("Updating OAuth tokens")
                update_data.update({
                    "oauth_access_token": oauth_tokens.get("access_token"),
                    "oauth_refresh_token": oauth_tokens.get("refresh_token")
                })
                
                # Calculate token expiry
                expires_in = oauth_tokens.get("expires_in")
                if expires_in:
                    update_data["oauth_token_expires_at"] = datetime.now(timezone.utc) + timedelta(seconds=expires_in)
                    logger.debug(f"OAuth token expires in {expires_in} seconds")
            
            self.user_repository.update_user(db, str(user.id), update_data)
            logger.debug("User information updated successfully")

            # 5. إنشاء Access Token
            logger.debug("Creating access token for user")
            access_token = self.auth_service.create_access_token(data={"sub": user.email})

            logger.info(f"Social login successful for user: {user.email} via {request_data.provider}")
            
            duration = time.time() - start_time
            log_performance(logger, "social_login", duration)
            log_function_exit(logger, "social_login", duration=duration)
            
            return LoginResponse(
                access_token=access_token,
                user_id=str(user.id),
                email=user.email,
                full_name=user.full_name,
                message=self.config_loader.get_message("login", "success_oauth", provider=request_data.provider)
            )
        except Exception as e:
            duration = time.time() - start_time
            log_error_with_context(logger, e, "social_login", duration=duration)
            logger.error(f"❌ Error in social_login: {e}")
            log_function_exit(logger, "social_login", duration=duration)
            raise
    
    async def login_user(self, login_data: UserLoginRequest, db: Session):
        log_function_entry(logger, "login_user", email=login_data.email)
        start_time = time.time()
        try:
            logger.debug(f"Login attempt for user: {login_data.email}")
            
            # 1. البحث عن المستخدم والتحقق من كلمة المرور (نفس الكود السابق)
            user = self.user_repository.get_user_by_email(db, login_data.email)
            if not user or not user.password_hash:
                logger.warning(f"Login failed - user not found or no password hash: {login_data.email}")
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail=self.config_loader.get_message("errors", "invalid_credentials")
                )
            
            logger.debug("Verifying password")
            is_password_valid = self.auth_service.verify_password(login_data.password, user.password_hash)
            if not is_password_valid:
                logger.warning(f"Login failed - invalid password for user: {login_data.email}")
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail=self.config_loader.get_message("errors", "invalid_credentials")
                )

            # 2. التحقق من المصادقة الثنائية
            if user.two_factor_enabled:
                logger.debug("User has 2FA enabled, checking 2FA code")
                if not login_data.two_factor_code:
                    logger.debug("2FA code not provided, requesting user input")
                    # إذا كانت 2FA مفعلة ولم يتم إرسال الرمز، اطلب من المستخدم إدخاله
                    duration = time.time() - start_time
                    log_function_exit(logger, "login_user", duration=duration)
                    return LoginResponse(
                        user_id=str(user.id),
                        email=user.email,
                        full_name=user.full_name,
                        two_factor_required=True,
                        message=self.config_loader.get_message("login", "two_factor_required")
                    )
                
                # تحقق من صحة الرمز
                logger.debug("Verifying 2FA code")
                two_factor_service = get_two_factor_auth_service()
                is_code_valid = two_factor_service.verify_code(
                    user.two_factor_secret, login_data.two_factor_code
                )
                if not is_code_valid:
                    logger.warning(f"Invalid 2FA code for user: {user.email}")
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="Invalid 2FA code."
                    )
                logger.debug("2FA code verified successfully")

            # 3. تحديث تاريخ آخر تسجيل دخول وإنشاء Token (نفس الكود السابق)
            logger.debug("Updating user last login time")
            self.user_repository.update_user(db, str(user.id), {"last_login_at": datetime.now(timezone.utc)})
            
            if login_data.remember_me:
                expires_delta = timedelta(days=30)
                logger.debug("Creating long-term access token (30 days)")
            else:
                expires_delta = timedelta(minutes=self.auth_service.access_token_expire_minutes)
                logger.debug(f"Creating standard access token ({self.auth_service.access_token_expire_minutes} minutes)")
            
            logger.debug("Creating access token")
            access_token = self.auth_service.create_access_token(
                data={"sub": user.email}, expires_delta=expires_delta
            )

            logger.info(f"Login successful for user: {user.email}")
            
            duration = time.time() - start_time
            log_performance(logger, "login_user", duration)
            log_function_exit(logger, "login_user", duration=duration)
            
            return LoginResponse(
                access_token=access_token,
                user_id=str(user.id),
                email=user.email,
                full_name=user.full_name,
                message=self.config_loader.get_message("login", "success")
            )
        except Exception as e:
            duration = time.time() - start_time
            log_error_with_context(logger, e, "login_user", duration=duration)
            logger.error(f"❌ Error in login_user: {e}")
            log_function_exit(logger, "login_user", duration=duration)
            raise


