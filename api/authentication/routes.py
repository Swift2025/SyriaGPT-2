"""
Authentication API routes for SyriaGPT.
"""

import logging
from datetime import datetime, timedelta
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession

from models.schemas.request_models import (
    UserRegistrationRequest,
    UserLoginRequest,
    PasswordResetRequest,
    PasswordResetConfirmRequest,
    EmailVerificationRequest,
    TwoFactorSetupRequest,
    TwoFactorVerifyRequest,
    OAuthLoginRequest,
    OAuthCallbackRequest
)
from models.schemas.response_models import (
    LoginResponse,
    RegistrationResponse,
    EmailVerificationResponse,
    PasswordResetResponse,
    TwoFactorSetupResponse,
    OAuthLoginResponse,
    TokenResponse,
    UserResponse
)
from services.database.database import get_db
from services.auth.auth import AuthService
from services.auth.oauth_service import OAuthService
from services.auth.two_factor_auth_service import TwoFactorAuthService
from services.auth.user_management_service import UserManagementService
from services.auth.session_management_service import SessionManagementService
from services.auth.forgot_password_service import ForgotPasswordService
from services.email.email_service import EmailService
from config.config_loader import ConfigLoader

logger = logging.getLogger(__name__)

# Initialize router
auth_router = APIRouter()

# Initialize services
config = ConfigLoader()
auth_service = AuthService(config)
oauth_service = OAuthService(config)
two_factor_service = TwoFactorAuthService(config)
user_management_service = UserManagementService(config)
session_management_service = SessionManagementService(config)
forgot_password_service = ForgotPasswordService(config)
email_service = EmailService(config)

# Security scheme
security = HTTPBearer()


@auth_router.post("/register", response_model=RegistrationResponse, tags=["Authentication"])
async def register_user(
    request: UserRegistrationRequest,
    db: AsyncSession = Depends(get_db)
):
    """Register a new user."""
    try:
        # Create user
        user = await user_management_service.create_user(
            db=db,
            email=request.email,
            password=request.password,
            username=request.username,
            first_name=request.first_name,
            last_name=request.last_name,
            language_preference=request.language_preference,
            timezone=request.timezone
        )
        
        # Generate email verification token
        verification_token = auth_service.create_access_token(
            {"sub": str(user.id), "email": user.email, "type": "email_verification"},
            timedelta(hours=24)
        )
        
        # Update user with verification token
        user.email_verification_token = verification_token
        user.email_verification_expires = datetime.utcnow() + timedelta(hours=24)
        await db.commit()
        
        # Send verification email
        try:
            await email_service.send_verification_email(user, verification_token)
        except Exception as e:
            logger.error(f"Failed to send verification email: {e}")
        
        # Create user response
        user_response = UserResponse(
            id=str(user.id),
            email=user.email,
            username=user.username,
            first_name=user.first_name,
            last_name=user.last_name,
            full_name=user.full_name,
            display_name=user.display_name,
            avatar_url=user.avatar_url,
            bio=user.bio,
            location=user.location,
            website=user.website,
            language_preference=user.language_preference,
            timezone=user.timezone,
            is_active=user.is_active,
            is_verified=user.is_verified,
            is_oauth_user=user.is_oauth_user,
            two_factor_enabled=user.two_factor_enabled,
            last_login_at=user.last_login_at,
            created_at=user.created_at,
            updated_at=user.updated_at
        )
        
        return RegistrationResponse(
            status="success",
            message="User registered successfully. Please check your email for verification.",
            user=user_response
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"User registration error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration failed"
        )


@auth_router.post("/login", response_model=LoginResponse, tags=["Authentication"])
async def login_user(
    request: UserLoginRequest,
    db: AsyncSession = Depends(get_db)
):
    """Login user with email and password."""
    try:
        # Authenticate user
        user = await auth_service.authenticate_user(db, request.email, request.password)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )
        
        # Check if 2FA is required
        if user.two_factor_enabled and not request.two_factor_code:
            return LoginResponse(
                status="success",
                message="Two-factor authentication required",
                user=UserResponse(
                    id=str(user.id),
                    email=user.email,
                    username=user.username,
                    first_name=user.first_name,
                    last_name=user.last_name,
                    full_name=user.full_name,
                    display_name=user.display_name,
                    avatar_url=user.avatar_url,
                    bio=user.bio,
                    location=user.location,
                    website=user.website,
                    language_preference=user.language_preference,
                    timezone=user.timezone,
                    is_active=user.is_active,
                    is_verified=user.is_verified,
                    is_oauth_user=user.is_oauth_user,
                    two_factor_enabled=user.two_factor_enabled,
                    last_login_at=user.last_login_at,
                    created_at=user.created_at,
                    updated_at=user.updated_at
                ),
                tokens=None,
                requires_two_factor=True
            )
        
        # Verify 2FA code if provided
        if user.two_factor_enabled and request.two_factor_code:
            if not await two_factor_service.verify_two_factor(db, user, request.two_factor_code):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid two-factor authentication code"
                )
        
        # Create tokens
        access_token, refresh_token = auth_service.create_token_pair(user)
        
        # Create session
        session = await session_management_service.create_session(
            db=db,
            user=user,
            access_token=access_token,
            refresh_token=refresh_token,
            remember_me=request.remember_me
        )
        
        # Create token response
        token_response = TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=auth_service.access_token_expire_minutes * 60,
            expires_at=datetime.utcnow() + timedelta(minutes=auth_service.access_token_expire_minutes)
        )
        
        # Create user response
        user_response = UserResponse(
            id=str(user.id),
            email=user.email,
            username=user.username,
            first_name=user.first_name,
            last_name=user.last_name,
            full_name=user.full_name,
            display_name=user.display_name,
            avatar_url=user.avatar_url,
            bio=user.bio,
            location=user.location,
            website=user.website,
            language_preference=user.language_preference,
            timezone=user.timezone,
            is_active=user.is_active,
            is_verified=user.is_verified,
            is_oauth_user=user.is_oauth_user,
            two_factor_enabled=user.two_factor_enabled,
            last_login_at=user.last_login_at,
            created_at=user.created_at,
            updated_at=user.updated_at
        )
        
        return LoginResponse(
            status="success",
            message="Login successful",
            user=user_response,
            tokens=token_response,
            requires_two_factor=False
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"User login error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Login failed"
        )


@auth_router.post("/logout", tags=["Authentication"])
async def logout_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
):
    """Logout user and revoke session."""
    try:
        token = credentials.credentials
        await session_management_service.revoke_session_by_token(db, token)
        
        return {
            "status": "success",
            "message": "Logout successful"
        }
        
    except Exception as e:
        logger.error(f"User logout error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Logout failed"
        )


@auth_router.post("/verify-email", response_model=EmailVerificationResponse, tags=["Authentication"])
async def verify_email(
    request: EmailVerificationRequest,
    db: AsyncSession = Depends(get_db)
):
    """Verify user email address."""
    try:
        # Verify token
        payload = auth_service.verify_token(request.token, "email_verification")
        user_id = payload.get("sub")
        
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid verification token"
            )
        
        # Get user
        user = await auth_service.get_user_by_id(db, user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Check if already verified
        if user.is_verified:
            return EmailVerificationResponse(
                status="success",
                message="Email already verified",
                verified=True
            )
        
        # Verify email
        user.is_verified = True
        user.email_verified_at = datetime.utcnow()
        user.email_verification_token = None
        user.email_verification_expires = None
        
        await db.commit()
        
        return EmailVerificationResponse(
            status="success",
            message="Email verified successfully",
            verified=True
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Email verification error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Email verification failed"
        )


@auth_router.post("/forgot-password", response_model=PasswordResetResponse, tags=["Authentication"])
async def forgot_password(
    request: PasswordResetRequest,
    db: AsyncSession = Depends(get_db)
):
    """Send password reset email."""
    try:
        await forgot_password_service.send_password_reset_email(db, request.email)
        
        return PasswordResetResponse(
            status="success",
            message="Password reset email sent successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Forgot password error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send password reset email"
        )


@auth_router.post("/reset-password", tags=["Authentication"])
async def reset_password(
    request: PasswordResetConfirmRequest,
    db: AsyncSession = Depends(get_db)
):
    """Reset user password with token."""
    try:
        await forgot_password_service.reset_password_with_token(
            db, request.token, request.new_password
        )
        
        return {
            "status": "success",
            "message": "Password reset successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Password reset error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Password reset failed"
        )


@auth_router.post("/2fa/setup", response_model=TwoFactorSetupResponse, tags=["Two-Factor Authentication"])
async def setup_two_factor(
    request: TwoFactorSetupRequest,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
):
    """Setup two-factor authentication for user."""
    try:
        token = credentials.credentials
        user = await auth_service.get_current_user(db, token)
        
        setup_info = await two_factor_service.setup_two_factor(db, user, request.password)
        
        return TwoFactorSetupResponse(
            status="success",
            message="Two-factor authentication setup successfully",
            qr_code=setup_info["qr_code"],
            secret_key=setup_info["secret"],
            backup_codes=setup_info["backup_codes"]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"2FA setup error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Two-factor authentication setup failed"
        )


@auth_router.post("/2fa/verify", tags=["Two-Factor Authentication"])
async def verify_two_factor(
    request: TwoFactorVerifyRequest,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
):
    """Verify two-factor authentication code."""
    try:
        token = credentials.credentials
        user = await auth_service.get_current_user(db, token)
        
        if await two_factor_service.verify_two_factor(db, user, request.code):
            return {
                "status": "success",
                "message": "Two-factor authentication verified successfully"
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid two-factor authentication code"
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"2FA verification error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Two-factor authentication verification failed"
        )


@auth_router.post("/2fa/disable", tags=["Two-Factor Authentication"])
async def disable_two_factor(
    request: TwoFactorSetupRequest,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
):
    """Disable two-factor authentication for user."""
    try:
        token = credentials.credentials
        user = await auth_service.get_current_user(db, token)
        
        await two_factor_service.disable_two_factor(db, user, request.password)
        
        return {
            "status": "success",
            "message": "Two-factor authentication disabled successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"2FA disable error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to disable two-factor authentication"
        )


@auth_router.get("/oauth/{provider}", response_model=OAuthLoginResponse, tags=["OAuth"])
async def oauth_login(provider: str, request: Request):
    """Initiate OAuth login with provider."""
    try:
        auth_url, state = oauth_service.get_oauth_authorization_url(provider)
        
        return OAuthLoginResponse(
            status="success",
            message=f"OAuth login initiated with {provider}",
            auth_url=auth_url,
            state=state
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"OAuth login error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="OAuth login failed"
        )


@auth_router.post("/oauth/{provider}/callback", response_model=LoginResponse, tags=["OAuth"])
async def oauth_callback(
    provider: str,
    request: OAuthCallbackRequest,
    db: AsyncSession = Depends(get_db)
):
    """Handle OAuth callback."""
    try:
        # Exchange code for token
        tokens = await oauth_service.exchange_code_for_token(provider, request.code, request.state)
        
        # Get user info
        user_info = await oauth_service.get_user_info(provider, tokens["access_token"])
        
        # Normalize user info
        normalized_info = oauth_service.normalize_user_info(provider, user_info)
        
        # Find or create user
        user = await oauth_service.find_or_create_user(db, normalized_info, tokens)
        
        # Create tokens
        access_token, refresh_token = auth_service.create_token_pair(user)
        
        # Create session
        session = await session_management_service.create_session(
            db=db,
            user=user,
            access_token=access_token,
            refresh_token=refresh_token,
            remember_me=True
        )
        
        # Create token response
        token_response = TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=auth_service.access_token_expire_minutes * 60,
            expires_at=datetime.utcnow() + timedelta(minutes=auth_service.access_token_expire_minutes)
        )
        
        # Create user response
        user_response = UserResponse(
            id=str(user.id),
            email=user.email,
            username=user.username,
            first_name=user.first_name,
            last_name=user.last_name,
            full_name=user.full_name,
            display_name=user.display_name,
            avatar_url=user.avatar_url,
            bio=user.bio,
            location=user.location,
            website=user.website,
            language_preference=user.language_preference,
            timezone=user.timezone,
            is_active=user.is_active,
            is_verified=user.is_verified,
            is_oauth_user=user.is_oauth_user,
            two_factor_enabled=user.two_factor_enabled,
            last_login_at=user.last_login_at,
            created_at=user.created_at,
            updated_at=user.updated_at
        )
        
        return LoginResponse(
            status="success",
            message=f"OAuth login successful with {provider}",
            user=user_response,
            tokens=token_response,
            requires_two_factor=False
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"OAuth callback error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="OAuth callback failed"
        )


@auth_router.post("/refresh", response_model=TokenResponse, tags=["Authentication"])
async def refresh_token(
    request: dict,
    db: AsyncSession = Depends(get_db)
):
    """Refresh access token using refresh token."""
    try:
        refresh_token = request.get("refresh_token")
        if not refresh_token:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Refresh token required"
            )
        
        # Verify refresh token
        payload = auth_service.verify_token(refresh_token, "refresh")
        user_id = payload.get("sub")
        
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token"
            )
        
        # Get user
        user = await auth_service.get_user_by_id(db, user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found"
            )
        
        # Create new tokens
        access_token, new_refresh_token = auth_service.create_token_pair(user)
        
        # Update session
        await session_management_service.update_session_tokens(db, refresh_token, access_token, new_refresh_token)
        
        return TokenResponse(
            access_token=access_token,
            refresh_token=new_refresh_token,
            token_type="bearer",
            expires_in=auth_service.access_token_expire_minutes * 60,
            expires_at=datetime.utcnow() + timedelta(minutes=auth_service.access_token_expire_minutes)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Token refresh error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Token refresh failed"
        )
