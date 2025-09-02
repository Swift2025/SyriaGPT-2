import logging
import time
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any
from fastapi import HTTPException, status, Query, Request, Depends
from sqlalchemy.orm import Session
from fastapi.responses import JSONResponse
import secrets
import uuid
from config.logging_config import get_logger, log_function_entry, log_function_exit, log_performance, log_error_with_context

logger = get_logger(__name__)

from models.schemas.request_models import (
    UserRegistrationRequest,
    OAuthAuthorizationRequest,
    OAuthCallbackRequest
)
from models.schemas.response_models import (
    UserRegistrationResponse,
    EmailVerificationResponse,
    OAuthProvidersResponse,
    OAuthAuthorizationResponse,
    HealthResponse,
    ErrorResponse
)
from services.auth import get_auth_service
from services.repositories import get_user_repository
from services.email import get_email_service
from services.auth import get_oauth_service
from config.config_loader import config_loader
from services.database.database import get_db


class RegistrationService:
    def __init__(self):
        logger.debug("Initializing RegistrationService")
        self.user_repository = get_user_repository()
        self.config_loader = config_loader
        logger.debug("RegistrationService initialized successfully")
    
    @property
    def email_service(self):
        log_function_entry(logger, "email_service")
        start_time = time.time()
        try:
            return get_email_service()
        except Exception as e:
            duration = time.time() - start_time
            log_error_with_context(logger, e, "email_service", duration=duration)
            logger.error(f"❌ Error in email_service: {e}")
            log_function_exit(logger, "email_service", duration=duration)
            raise
    
    @property
    def oauth_service(self):
        log_function_entry(logger, "oauth_service")
        start_time = time.time()
        try:
            return get_oauth_service()
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
            return get_auth_service()
        except Exception as e:
            duration = time.time() - start_time
            log_error_with_context(logger, e, "auth_service", duration=duration)
            logger.error(f"❌ Error in auth_service: {e}")
            log_function_exit(logger, "auth_service", duration=duration)
            raise

    async def register_user(self, registration_data: UserRegistrationRequest, db: Session) -> tuple[Optional[UserRegistrationResponse], Optional[str], int]:
        logger.debug(f"Registration attempt for user: {registration_data.email}")
        try:
            logger.debug("Checking if user already exists")
            existing_user = self.user_repository.get_user_by_email(db, registration_data.email)
            if existing_user:
                logger.warning(f"Registration failed - email already exists: {registration_data.email}")
                return None, self.config_loader.get_message("errors", "email_exists"), status.HTTP_409_CONFLICT

            if registration_data.phone_number:
                logger.debug("Checking if phone number already exists")
                existing_phone = self.user_repository.get_user_by_phone(db, registration_data.phone_number)
                if existing_phone:
                    logger.warning(f"Registration failed - phone number already exists: {registration_data.phone_number}")
                    return None, self.config_loader.get_message("errors", "phone_exists"), status.HTTP_409_CONFLICT

            logger.debug("Creating user account")
            hashed_password = self.auth_service.hash_password(registration_data.password)
            verification_token = self.auth_service.generate_verification_token()
            registration_token = self.auth_service.create_access_token({"sub": registration_data.email})
            
            full_name = self._build_full_name(registration_data.first_name, registration_data.last_name)
            
            user_data = {
                "email": registration_data.email,
                "password_hash": hashed_password,
                "phone_number": registration_data.phone_number,
                "first_name": registration_data.first_name,
                "last_name": registration_data.last_name,
                "full_name": full_name,
                "token": verification_token,
                "token_expiry": datetime.now(timezone.utc) + timedelta(hours=24),
                "status": "pending_verification",
                "is_email_verified": False,
                "is_phone_verified": False,
                "two_factor_enabled": False
            }

            user, error = self.user_repository.create_user(db, user_data)
            if error:
                return None, error, status.HTTP_400_BAD_REQUEST

            message = self.config_loader.get_message("registration", "success")
            if self.email_service.is_configured():
                email_sent, email_error = await self.email_service.send_verification_email(
                    to_email=user.email,
                    verification_token=verification_token,
                    user_name=user.full_name
                )
                if email_sent:
                    message = self.config_loader.get_message("registration", "email_verification_sent")
                else:
                    message = self.config_loader.get_message("registration", "email_send_failed")

            response = UserRegistrationResponse(
                id=str(user.id),
                email=user.email,
                phone_number=user.phone_number,
                full_name=user.full_name,
                profile_picture=user.profile_picture,
                oauth_provider=user.oauth_provider,
                status=user.status,
                is_email_verified=user.is_email_verified,
                is_phone_verified=user.is_phone_verified,
                created_at=user.created_at,
                registration_token=registration_token,
                message=message
            )
            
            return response, None, status.HTTP_201_CREATED
            
        except Exception as e:
            logger.error(f"Registration failed: {e}")
            return None, self.config_loader.get_message("errors", "registration_failed_generic"), status.HTTP_500_INTERNAL_SERVER_ERROR

    async def verify_email(self, token: str, db: Session) -> tuple[bool, Optional[EmailVerificationResponse], int]:
        try:
            user = self.user_repository.get_user_by_token(db, token)
            if not user:
                return False, None, status.HTTP_400_BAD_REQUEST

            if user.is_email_verified:
                response = EmailVerificationResponse(
                    message=self.config_loader.get_message("verification", "already_verified"),
                    verified=True,
                    user_id=str(user.id),
                    email=user.email
                )
                return True, response, status.HTTP_200_OK

            # Update user verification status
            update_data = {
                "is_email_verified": True,
                "status": "active",
                "token": None,
                "token_expiry": None
            }
            
            updated_user, error = self.user_repository.update_user(db, user.id, update_data)
            if error:
                return False, None, status.HTTP_500_INTERNAL_SERVER_ERROR

            # Send welcome email
            if self.email_service.is_configured():
                await self.email_service.send_welcome_email(
                    to_email=user.email,
                    user_name=user.full_name
                )

            response = EmailVerificationResponse(
                message=self.config_loader.get_message("verification", "success"),
                verified=True,
                user_id=str(user.id),
                email=user.email
            )
            
            return True, response, status.HTTP_200_OK
            
        except Exception as e:
            logger.error(f"Email verification failed: {e}")
            return False, None, status.HTTP_500_INTERNAL_SERVER_ERROR

    def get_oauth_providers_info(self) -> OAuthProvidersResponse:
        """Get information about configured OAuth providers"""
        providers = []
        configured_providers = {}
        
        for provider_name in ["google"]:
            # Check environment variables like the OAuth service does
            client_id = self.config_loader.get_config_value(f"{provider_name.upper()}_CLIENT_ID")
            client_secret = self.config_loader.get_config_value(f"{provider_name.upper()}_CLIENT_SECRET")
            
            if client_id and client_secret:
                providers.append(provider_name)
                configured_providers[provider_name] = True
            else:
                configured_providers[provider_name] = False
        
        return OAuthProvidersResponse(
            providers=providers,
            configured_providers=configured_providers
        )

    def get_oauth_authorization_url(self, provider: str, redirect_uri: str) -> tuple[Optional[OAuthAuthorizationResponse], Optional[str], int]:
        """Get OAuth authorization URL for the specified provider"""
        try:
            # Check environment variables like the OAuth service does
            client_id = self.config_loader.get_config_value(f"{provider.upper()}_CLIENT_ID")
            if not client_id:
                return None, self.config_loader.get_message("errors", "oauth_not_configured", provider=provider), status.HTTP_400_BAD_REQUEST

            state = secrets.token_urlsafe(32)
            auth_url = self.oauth_service.get_authorization_url(
                provider,
                redirect_uri,
                state
            )
            
            response = OAuthAuthorizationResponse(
                authorization_url=auth_url,
                redirect_uri=redirect_uri,
                state=state,
                provider=provider
            )
            
            return response, None, status.HTTP_200_OK
            
        except Exception as e:
            logger.error(f"Failed to get OAuth authorization URL: {e}")
            return None, self.config_loader.get_message("errors", "authorization_url_failed", error=str(e)), status.HTTP_500_INTERNAL_SERVER_ERROR

    def get_health_status(self, db: Session) -> HealthResponse:
        """Get health status of registration service"""
        try:
            # Check database connection
            db_connected = True
            try:
                db.execute("SELECT 1")
            except Exception:
                db_connected = False

            # Check email service
            email_configured = self.email_service.is_configured()

            # Get OAuth providers
            oauth_response = self.get_oauth_providers_info()
            oauth_providers = oauth_response.providers

            return HealthResponse(
                status=self.config_loader.get_message("service", "healthy"),
                service=self.config_loader.get_message("service", "registration_service"),
                email_configured=email_configured,
                oauth_providers=oauth_providers,
                database_connected=db_connected,
                version=self.config_loader.get_message("service", "version")
            )
            
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return HealthResponse(
                status="unhealthy",
                service="registration",
                email_configured=False,
                oauth_providers=[],
                database_connected=False,
                version="1.0.0"
            )

    def _build_full_name(self, first_name: Optional[str], last_name: Optional[str]) -> Optional[str]:
        """Build full name from first and last name"""
        if first_name and last_name:
            return f"{first_name} {last_name}"
        elif first_name:
            return first_name
        elif last_name:
            return last_name
        return None