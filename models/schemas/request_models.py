from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, EmailStr, Field, validator
import re
import time
import logging
from config.logging_config import (
    get_logger,
    log_function_entry,
    log_function_exit,
    log_performance,
    log_error_with_context
)

logger = get_logger(__name__)


class UserRegistrationRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8)
    phone_number: Optional[str] = Field(None, pattern=r'^\+?[1-9]\d{1,14}$')
    first_name: Optional[str] = Field(None, max_length=100)
    last_name: Optional[str] = Field(None, max_length=100)
    
    @validator('password')
    def validate_password(cls, v):
        log_function_entry(logger, "validate_password")
        start_time = time.time()
        try:
            # Basic password validation to avoid circular imports
            if len(v) < 8:
                raise ValueError("Password must be at least 8 characters long")
            if not any(c.isupper() for c in v):
                raise ValueError("Password must contain at least one uppercase letter")
            if not any(c.islower() for c in v):
                raise ValueError("Password must contain at least one lowercase letter")
            if not any(c.isdigit() for c in v):
                raise ValueError("Password must contain at least one number")
            if not any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in v):
                raise ValueError("Password must contain at least one special character")
            
            duration = time.time() - start_time
            log_performance(logger, "validate_password", duration)
            log_function_exit(logger, "validate_password", duration=duration)
            return v
        except Exception as e:
            duration = time.time() - start_time
            log_error_with_context(logger, e, "validate_password", duration=duration)
            logger.error(f"❌ Error in validate_password: {e}")
            log_function_exit(logger, "validate_password", duration=duration)
            raise
    
    @validator('phone_number')
    def validate_phone(cls, v):
        log_function_entry(logger, "validate_phone")
        start_time = time.time()
        try:
            if v and not re.match(r'^\+?[1-9]\d{1,14}$', v):
                raise ValueError("Invalid phone number format")
            
            duration = time.time() - start_time
            log_performance(logger, "validate_phone", duration)
            log_function_exit(logger, "validate_phone", duration=duration)
            return v
        except Exception as e:
            duration = time.time() - start_time
            log_error_with_context(logger, e, "validate_phone", duration=duration)
            logger.error(f"❌ Error in validate_phone: {e}")
            log_function_exit(logger, "validate_phone", duration=duration)
            raise


class OAuthAuthorizationRequest(BaseModel):
    provider: str = Field(..., pattern=r'^google$')
    redirect_uri: Optional[str] = None


class OAuthCallbackRequest(BaseModel):
    provider: str = Field(..., pattern=r'^google$')
    code: str
    state: Optional[str] = None
    redirect_uri: Optional[str] = None


class SocialLoginRequest(BaseModel):
    provider: str = Field(..., pattern=r'^google$')
    code: str
    redirect_uri: Optional[str] = None    


class OAuthRefreshRequest(BaseModel):
    email: EmailStr = Field(..., description="User email for OAuth token refresh")
    provider: str = Field(..., pattern=r'^google$', description="OAuth provider name")


class UserLoginRequest(BaseModel):
    email: EmailStr
    password: str
    remember_me: Optional[bool] = False
    two_factor_code: Optional[str] = None


class TwoFactorVerifyRequest(BaseModel):
    code: str = Field(..., min_length=6, max_length=6)


class QuestionCreateRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=10000)


class AnswerCreateRequest(BaseModel):
    answer: str = Field(..., min_length=1, max_length=10000)
    question_id: str = Field(..., description="UUID of the question")
    author: str = Field(..., min_length=1, max_length=255)


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str = Field(..., min_length=8)
    confirm_password: str = Field(..., min_length=8)
    
    @validator('confirm_password')
    def validate_passwords_match(cls, v, values):
        log_function_entry(logger, "validate_passwords_match")
        start_time = time.time()
        try:
            if 'new_password' in values and v != values['new_password']:
                raise ValueError("Passwords do not match")
            
            duration = time.time() - start_time
            log_performance(logger, "validate_passwords_match", duration)
            log_function_exit(logger, "validate_passwords_match", duration=duration)
            return v
        except Exception as e:
            duration = time.time() - start_time
            log_error_with_context(logger, e, "validate_passwords_match", duration=duration)
            logger.error(f"❌ Error in validate_passwords_match: {e}")
            log_function_exit(logger, "validate_passwords_match", duration=duration)
            raise
    
    @validator('new_password')
    def validate_password_strength(cls, v):
        log_function_entry(logger, "validate_password_strength")
        start_time = time.time()
        try:
            # Basic password validation to avoid circular imports
            if len(v) < 8:
                raise ValueError("Password must be at least 8 characters long")
            if not any(c.isupper() for c in v):
                raise ValueError("Password must contain at least one uppercase letter")
            if not any(c.islower() for c in v):
                raise ValueError("Password must contain at least one lowercase letter")
            if not any(c.isdigit() for c in v):
                raise ValueError("Password must contain at least one number")
            if not any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in v):
                raise ValueError("Password must contain at least one special character")
            
            duration = time.time() - start_time
            log_performance(logger, "validate_password_strength", duration)
            log_function_exit(logger, "validate_password_strength", duration=duration)
            return v
        except Exception as e:
            duration = time.time() - start_time
            log_error_with_context(logger, e, "validate_password_strength", duration=duration)
            logger.error(f"❌ Error in validate_password_strength: {e}")
            log_function_exit(logger, "validate_password_strength", duration=duration)
            raise


# User Management Request Models
class UserUpdateRequest(BaseModel):
    first_name: Optional[str] = Field(None, max_length=100)
    last_name: Optional[str] = Field(None, max_length=100)
    phone_number: Optional[str] = Field(None, pattern=r'^\+?[1-9]\d{1,14}$')
    profile_picture: Optional[str] = Field(None, max_length=500)
    
    @validator('phone_number')
    def validate_phone(cls, v):
        log_function_entry(logger, "validate_phone")
        start_time = time.time()
        try:
            if v and not re.match(r'^\+?[1-9]\d{1,14}$', v):
                raise ValueError("Invalid phone number format")
            
            duration = time.time() - start_time
            log_performance(logger, "validate_phone", duration)
            log_function_exit(logger, "validate_phone", duration=duration)
            return v
        except Exception as e:
            duration = time.time() - start_time
            log_error_with_context(logger, e, "validate_phone", duration=duration)
            logger.error(f"❌ Error in validate_phone: {e}")
            log_function_exit(logger, "validate_phone", duration=duration)
            raise


class UserPasswordChangeRequest(BaseModel):
    current_password: str
    new_password: str = Field(..., min_length=8)
    confirm_password: str = Field(..., min_length=8)
    
    @validator('confirm_password')
    def validate_passwords_match(cls, v, values):
        log_function_entry(logger, "validate_passwords_match")
        start_time = time.time()
        try:
            if 'new_password' in values and v != values['new_password']:
                raise ValueError("Passwords do not match")
            
            duration = time.time() - start_time
            log_performance(logger, "validate_passwords_match", duration)
            log_function_exit(logger, "validate_passwords_match", duration=duration)
            return v
        except Exception as e:
            duration = time.time() - start_time
            log_error_with_context(logger, e, "validate_passwords_match", duration=duration)
            logger.error(f"❌ Error in validate_passwords_match: {e}")
            log_function_exit(logger, "validate_passwords_match", duration=duration)
            raise
    
    @validator('new_password')
    def validate_password_strength(cls, v):
        log_function_entry(logger, "validate_password_strength")
        start_time = time.time()
        try:
            if len(v) < 8:
                raise ValueError("Password must be at least 8 characters long")
            if not any(c.isupper() for c in v):
                raise ValueError("Password must contain at least one uppercase letter")
            if not any(c.islower() for c in v):
                raise ValueError("Password must contain at least one lowercase letter")
            if not any(c.isdigit() for c in v):
                raise ValueError("Password must contain at least one number")
            if not any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in v):
                raise ValueError("Password must contain at least one special character")
            
            duration = time.time() - start_time
            log_performance(logger, "validate_password_strength", duration)
            log_function_exit(logger, "validate_password_strength", duration=duration)
            return v
        except Exception as e:
            duration = time.time() - start_time
            log_error_with_context(logger, e, "validate_password_strength", duration=duration)
            logger.error(f"❌ Error in validate_password_strength: {e}")
            log_function_exit(logger, "validate_password_strength", duration=duration)
            raise


class UserStatusUpdateRequest(BaseModel):
    status: str = Field(..., pattern=r'^(active|suspended|banned|pending_verification)$')


class UserSearchRequest(BaseModel):
    email: Optional[str] = None
    phone_number: Optional[str] = None
    status: Optional[str] = None
    oauth_provider: Optional[str] = None
    is_email_verified: Optional[bool] = None
    is_phone_verified: Optional[bool] = None
    two_factor_enabled: Optional[bool] = None
    created_after: Optional[datetime] = None
    created_before: Optional[datetime] = None
    page: int = Field(1, ge=1)
    page_size: int = Field(10, ge=1, le=100)


class UserBulkActionRequest(BaseModel):
    user_ids: List[str] = Field(..., min_items=1)
    action: str = Field(..., pattern=r'^(activate|suspend|ban|delete|verify_email|verify_phone)$')


# Session Management Request Models
class SessionCreateRequest(BaseModel):
    device_info: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    location: Optional[str] = None
    is_mobile: Optional[bool] = False
    expires_in_hours: int = Field(24, ge=1, le=720)  # 1 hour to 30 days


class SessionUpdateRequest(BaseModel):
    device_info: Optional[str] = None
    location: Optional[str] = None
    is_mobile: Optional[bool] = None


class SessionSearchRequest(BaseModel):
    user_id: Optional[str] = None
    is_active: Optional[bool] = None
    is_mobile: Optional[bool] = None
    ip_address: Optional[str] = None
    created_after: Optional[datetime] = None
    created_before: Optional[datetime] = None
    expires_after: Optional[datetime] = None
    expires_before: Optional[datetime] = None
    page: int = Field(1, ge=1)
    page_size: int = Field(10, ge=1, le=100)


class SessionBulkActionRequest(BaseModel):
    session_ids: List[str] = Field(..., min_items=1)
    action: str = Field(..., pattern=r'^(revoke|extend|update_location)$')
    expires_in_hours: Optional[int] = Field(None, ge=1, le=720)


# Settings Management Request Models
class UserSettingsRequest(BaseModel):
    email_notifications: Optional[bool] = True
    sms_notifications: Optional[bool] = False
    two_factor_enabled: Optional[bool] = False
    session_timeout_hours: Optional[int] = Field(24, ge=1, le=720)
    max_concurrent_sessions: Optional[int] = Field(5, ge=1, le=20)
    language: Optional[str] = Field("en", pattern=r'^(en|ar)$')
    timezone: Optional[str] = Field("UTC", max_length=50)
    theme: Optional[str] = Field("light", pattern=r'^(light|dark|auto)$')


class SystemSettingsRequest(BaseModel):
    max_users: Optional[int] = Field(None, ge=1)
    max_sessions_per_user: Optional[int] = Field(10, ge=1, le=50)
    session_timeout_hours: Optional[int] = Field(24, ge=1, le=720)
    password_expiry_days: Optional[int] = Field(90, ge=1, le=365)
    require_email_verification: Optional[bool] = True
    require_phone_verification: Optional[bool] = False
    allow_oauth_registration: Optional[bool] = True
    allow_oauth_login: Optional[bool] = True
    maintenance_mode: Optional[bool] = False
    maintenance_message: Optional[str] = None


# SMTP Configuration Request Models
class SMTPTestRequest(BaseModel):
    email: EmailStr
    password: str
    provider: Optional[str] = None


class SMTPConfigRequest(BaseModel):
    email: EmailStr
    password: str
    provider: Optional[str] = None
    use_ssl: Optional[bool] = False
    custom_host: Optional[str] = None
    custom_port: Optional[int] = None


# AI Chat Management Request Models
class ChatCreateRequest(BaseModel):
    title: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    context: Optional[str] = Field(None, max_length=5000)
    language: str = Field("auto", pattern=r'^(auto|en|ar)$')
    model_preference: Optional[str] = Field("gemini-1.5-flash", pattern=r'^(gemini-1\.5-flash|gemini-1\.5-pro|gemini-2\.0-flash)$')
    max_tokens: Optional[int] = Field(2000, ge=100, le=8000)
    temperature: Optional[float] = Field(0.7, ge=0.0, le=2.0)


class ChatMessageRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=10000)
    message_type: str = Field("text", pattern=r'^(text|image|file|voice)$')
    attachments: Optional[List[str]] = Field(None, max_items=5)  # URLs or file IDs
    context: Optional[str] = Field(None, max_length=2000)
    language: Optional[str] = Field(None, pattern=r'^(auto|en|ar)$')
    priority: str = Field("normal", pattern=r'^(low|normal|high|urgent)$')


class ChatUpdateRequest(BaseModel):
    title: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    context: Optional[str] = Field(None, max_length=5000)
    language: Optional[str] = Field(None, pattern=r'^(auto|en|ar)$')
    model_preference: Optional[str] = Field(None, pattern=r'^(gemini-1\.5-flash|gemini-1\.5-pro|gemini-2\.0-flash)$')
    max_tokens: Optional[int] = Field(None, ge=100, le=8000)
    temperature: Optional[float] = Field(None, ge=0.0, le=2.0)
    is_archived: Optional[bool] = None
    is_pinned: Optional[bool] = None


class ChatSearchRequest(BaseModel):
    title: Optional[str] = None
    language: Optional[str] = None
    model_preference: Optional[str] = None
    is_archived: Optional[bool] = None
    is_pinned: Optional[bool] = None
    created_after: Optional[datetime] = None
    created_before: Optional[datetime] = None
    updated_after: Optional[datetime] = None
    updated_before: Optional[datetime] = None
    message_count_min: Optional[int] = Field(None, ge=0)
    message_count_max: Optional[int] = Field(None, ge=0)
    page: int = Field(1, ge=1)
    page_size: int = Field(10, ge=1, le=100)


class ChatBulkActionRequest(BaseModel):
    chat_ids: List[str] = Field(..., min_items=1)
    action: str = Field(..., pattern=r'^(archive|unarchive|pin|unpin|delete|export)$')


class ChatExportRequest(BaseModel):
    format: str = Field("json", pattern=r'^(json|csv|txt|pdf)$')
    include_metadata: bool = True
    include_context: bool = True
    include_attachments: bool = False
    date_range_start: Optional[datetime] = None
    date_range_end: Optional[datetime] = None


class ChatAnalyticsRequest(BaseModel):
    date_range_start: Optional[datetime] = None
    date_range_end: Optional[datetime] = None
    group_by: str = Field("day", pattern=r'^(hour|day|week|month)$')
    include_message_content: bool = False
    include_user_metrics: bool = True
    include_model_metrics: bool = True


class ChatFeedbackRequest(BaseModel):
    message_id: str
    rating: int = Field(..., ge=1, le=5)
    feedback_type: str = Field(..., pattern=r'^(helpful|unhelpful|inaccurate|inappropriate|other)$')
    comment: Optional[str] = Field(None, max_length=1000)
    category: Optional[str] = Field(None, pattern=r'^(accuracy|relevance|completeness|clarity|speed|other)$')


class ChatSettingsRequest(BaseModel):
    default_language: str = Field("auto", pattern=r'^(auto|en|ar)$')
    default_model: str = Field("gemini-1.5-flash", pattern=r'^(gemini-1\.5-flash|gemini-1\.5-pro|gemini-2\.0-flash)$')
    default_max_tokens: int = Field(2000, ge=100, le=8000)
    default_temperature: float = Field(0.7, ge=0.0, le=2.0)
    auto_archive_after_days: int = Field(30, ge=1, le=365)
    max_chats_per_user: int = Field(100, ge=1, le=1000)
    max_messages_per_chat: int = Field(1000, ge=10, le=10000)
    enable_voice_input: bool = True
    enable_file_upload: bool = True
    enable_image_analysis: bool = True
    enable_context_memory: bool = True
    enable_chat_history: bool = True
    enable_analytics: bool = True
    enable_feedback: bool = True