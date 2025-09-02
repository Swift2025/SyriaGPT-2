# /api/authentication/routes.py

from fastapi import APIRouter, Request, HTTPException, status, Query, Depends
from sqlalchemy.orm import Session
from typing import Optional
import logging
import time

from models.domain.user import User
from models.schemas.request_models import UserLoginRequest, SocialLoginRequest, UserRegistrationRequest, ForgotPasswordRequest, ResetPasswordRequest, TwoFactorVerifyRequest, OAuthRefreshRequest
from models.schemas.response_models import LoginResponse, ErrorResponse, UserRegistrationResponse, EmailVerificationResponse, OAuthProvidersResponse, OAuthAuthorizationResponse, HealthResponse, TwoFactorSetupResponse, GeneralResponse
from .authentication import AuthenticationService
from .registration import RegistrationService
from .two_factor import TwoFactorService
from services.auth import get_forgot_password_service
from services.dependencies import get_current_user, limiter
from config.config_loader import config_loader
from config.logging_config import get_logger, log_function_entry, log_function_exit, log_performance, log_error_with_context
from services.database.database import get_db

logger = get_logger(__name__)

authentication_service = AuthenticationService()
registration_service = RegistrationService()
two_factor_service = TwoFactorService()

logger.debug("Authentication services initialized")

router = APIRouter(prefix="/auth", tags=["authentication"])


@router.post(
    "/login",
    response_model=LoginResponse,
    responses={401: {"model": ErrorResponse}}
)
async def login_user(login_data: UserLoginRequest, db: Session = Depends(get_db)):
    log_function_entry(logger, "login_user", user_email=login_data.email)
    start_time = time.time()
    
    try:
        logger.debug(f"🔍 Login attempt for user: {login_data.email}")
        result = await authentication_service.login_user(login_data, db)
        
        if 'access_token' in result:
            duration = time.time() - start_time
            log_performance(logger, "User login (success)", duration, user_email=login_data.email)
            logger.debug(f"✅ Login successful for user: {login_data.email}")
        else:
            duration = time.time() - start_time
            log_performance(logger, "User login (failed)", duration, user_email=login_data.email)
            logger.debug(f"❌ Login failed for user: {login_data.email}")
        
        log_function_exit(logger, "login_user", result="success" if 'access_token' in result else "failed", duration=time.time() - start_time)
        return result
        
    except Exception as e:
        duration = time.time() - start_time
        log_error_with_context(logger, e, "login_user", user_email=login_data.email, duration=duration)
        logger.error(f"❌ Login error for user {login_data.email}: {e}")
        log_function_exit(logger, "login_user", duration=duration)
        raise


@router.post("/register", response_model=UserRegistrationResponse, status_code=status.HTTP_201_CREATED)
async def register_user(registration_data: UserRegistrationRequest, db: Session = Depends(get_db)):
    log_function_entry(logger, "register_user", user_email=registration_data.email, full_name=registration_data.full_name)
    start_time = time.time()
    
    try:
        logger.debug(f"🔍 Registration attempt for user: {registration_data.email}")
        result, error, status_code = await registration_service.register_user(registration_data, db)
        
        if error:
            duration = time.time() - start_time
            log_performance(logger, "User registration (failed)", duration, user_email=registration_data.email, error=error)
            logger.warning(f"❌ Registration failed for {registration_data.email}: {error}")
            log_function_exit(logger, "register_user", result="failed", duration=duration)
            raise HTTPException(status_code=status_code, detail=error)
        
        duration = time.time() - start_time
        log_performance(logger, "User registration (success)", duration, user_email=registration_data.email)
        logger.debug(f"✅ Registration successful for user: {registration_data.email}")
        log_function_exit(logger, "register_user", result="success", duration=duration)
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        duration = time.time() - start_time
        log_error_with_context(logger, e, "register_user", user_email=registration_data.email, duration=duration)
        logger.error(f"❌ Registration error for user {registration_data.email}: {e}")
        log_function_exit(logger, "register_user", duration=duration)
        raise


@router.get("/verify-email/{token}", response_model=EmailVerificationResponse)
async def verify_email(token: str, db: Session = Depends(get_db)):
    success, response, status_code = await registration_service.verify_email(token, db)
    
    if not success:
        error_msg = config_loader.get_message("verification", "invalid_token")
        raise HTTPException(status_code=status_code, detail=error_msg)
    
    return response


@router.get("/oauth/providers", response_model=OAuthProvidersResponse)
async def get_oauth_providers():
    return registration_service.get_oauth_providers_info()


@router.post("/oauth/{provider}/authorize", response_model=OAuthAuthorizationResponse)
async def oauth_authorize(
    provider: str,
    request: Request,
    redirect_uri: Optional[str] = Query(None)
):
    if redirect_uri is None:
        redirect_uri = f"{request.base_url}auth/oauth/{provider}/callback"
    
    response, error, status_code = registration_service.get_oauth_authorization_url(provider, redirect_uri)
    
    if error:
        raise HTTPException(status_code=status_code, detail=error)
    
    return response


@router.get("/oauth/{provider}/callback", response_model=LoginResponse)
async def oauth_callback(
    provider: str,
    code: str = Query(...),
    state: Optional[str] = Query(None),
    error: Optional[str] = Query(None),
    request: Request = None,
    db: Session = Depends(get_db)
):
    """
    OAuth callback endpoint - handles both user registration and login.
    If user exists, logs them in. If user doesn't exist, registers and logs them in.
    """
    if error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"OAuth error: {error}"
        )
    
    redirect_uri = f"{request.base_url}auth/oauth/{provider}/callback"
    
    # Use social_login method which handles both registration and login
    from models.schemas.request_models import SocialLoginRequest
    social_request = SocialLoginRequest(
        provider=provider,
        code=code,
        redirect_uri=redirect_uri
    )
    
    return await authentication_service.social_login(social_request, request, db)





@router.get("/health", response_model=HealthResponse)
async def health_check(db: Session = Depends(get_db)):
    return registration_service.get_health_status(db)

@router.post("/oauth/{provider}/refresh", response_model=LoginResponse)
async def refresh_oauth_token(
    provider: str,
    refresh_request: OAuthRefreshRequest,
    db: Session = Depends(get_db)
):
    """
    Refresh OAuth token for a user
    
    This endpoint allows users to refresh their OAuth access tokens using their email
    and the stored refresh token. The provider parameter in the URL must match the
    user's OAuth provider.
    """
    from services.auth import get_oauth_service
    from services.repositories import get_user_repository
    
    oauth_service = get_oauth_service()
    user_repo = get_user_repository()
    
    # Validate that the provider in URL matches the request
    if refresh_request.provider != provider:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Provider mismatch: URL provider must match request provider"
        )
    
    user = user_repo.get_user_by_email(db, refresh_request.email)
    if not user or user.oauth_provider != provider:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="OAuth user not found"
        )
    
    if not user.oauth_refresh_token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No refresh token available for this user"
        )
    
    # Refresh the OAuth token
    new_tokens = await oauth_service.refresh_oauth_token(provider, user.oauth_refresh_token)
    if not new_tokens:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to refresh OAuth token"
        )
    
    # Update user's OAuth tokens
    success, error = user_repo.update_oauth_tokens(
        db, 
        str(user.id), 
        new_tokens['access_token'],
        new_tokens.get('refresh_token'),
        new_tokens.get('expires_in')
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update OAuth tokens: {error}"
        )
    
    # Create new JWT access token
    auth_service = get_auth_service()
    access_token = auth_service.create_access_token(data={"sub": user.email})
    
    return LoginResponse(
        access_token=access_token,
        user_id=str(user.id),
        email=user.email,
        full_name=user.full_name,
        message="OAuth token refreshed successfully"
    )

@router.post("/forgot-password")
async def forgot_password(request: ForgotPasswordRequest, db: Session = Depends(get_db)):
    forgot_password_service = get_forgot_password_service(db)
    token = forgot_password_service.create_reset_token(request.email)
    await forgot_password_service.send_reset_email(request.email, token)
    return {"msg": "تم إرسال رابط إعادة التعيين إلى بريدك الإلكتروني"}

# Endpoint: إعادة التعيين
@router.post("/reset-password")
def reset_password(request: ResetPasswordRequest, db: Session = Depends(get_db)):
    forgot_password_service = get_forgot_password_service(db)
    forgot_password_service.reset_password(request.token, request.new_password, request.confirm_password)
    return {"msg": "تمت إعادة تعيين كلمة المرور بنجاح، وتم تسجيل خروجك من جميع الأجهزة"}

@router.post("/2fa/setup", response_model=TwoFactorSetupResponse)
def setup_2fa_endpoint(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return two_factor_service.setup_2fa(current_user, db)

@router.post("/2fa/verify", response_model=GeneralResponse)
@limiter.limit("5/minute")
def verify_2fa_endpoint(request: Request, verify_data: TwoFactorVerifyRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return two_factor_service.verify_and_enable_2fa(current_user, verify_data, db)

@router.post("/2fa/disable", response_model=GeneralResponse)
def disable_2fa_endpoint(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return two_factor_service.disable_2fa(current_user, db)
