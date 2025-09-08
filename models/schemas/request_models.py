"""
Pydantic request models for SyriaGPT API.
"""

from datetime import datetime
from typing import Optional, List, Dict, Any, Union
from pydantic import BaseModel, EmailStr, Field, field_validator
from enum import Enum


class LanguageEnum(str, Enum):
    """Language enumeration."""
    ARABIC = "ar"
    ENGLISH = "en"


class MessageRoleEnum(str, Enum):
    """Message role enumeration."""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class MessageTypeEnum(str, Enum):
    """Message type enumeration."""
    TEXT = "text"
    IMAGE = "image"
    FILE = "file"
    AUDIO = "audio"
    VIDEO = "video"


class FeedbackTypeEnum(str, Enum):
    """Feedback type enumeration."""
    POSITIVE = "positive"
    NEGATIVE = "negative"
    NEUTRAL = "neutral"


# Authentication Models
class UserRegistrationRequest(BaseModel):
    """User registration request model."""
    email: EmailStr
    username: Optional[str] = Field(None, min_length=3, max_length=100)
    first_name: Optional[str] = Field(None, min_length=1, max_length=100)
    last_name: Optional[str] = Field(None, min_length=1, max_length=100)
    password: str = Field(..., min_length=8, max_length=128)
    confirm_password: str = Field(..., min_length=8, max_length=128)
    language_preference: LanguageEnum = LanguageEnum.ARABIC
    timezone: str = Field(default="Asia/Damascus", max_length=50)
    
    @field_validator('confirm_password')
    @classmethod
    def passwords_match(cls, v, info):
        if 'password' in info.data and v != info.data['password']:
            raise ValueError('Passwords do not match')
        return v
    
    @field_validator('password')
    @classmethod
    def validate_password_strength(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not any(c.islower() for c in v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain at least one digit')
        return v


class UserLoginRequest(BaseModel):
    """User login request model."""
    email: EmailStr
    password: str = Field(..., min_length=1, max_length=128)
    remember_me: bool = False
    two_factor_code: Optional[str] = Field(None, min_length=6, max_length=6)


class PasswordResetRequest(BaseModel):
    """Password reset request model."""
    email: EmailStr


class PasswordResetConfirmRequest(BaseModel):
    """Password reset confirmation request model."""
    token: str = Field(..., min_length=1)
    new_password: str = Field(..., min_length=8, max_length=128)
    confirm_password: str = Field(..., min_length=8, max_length=128)
    
    @field_validator('confirm_password')
    @classmethod
    def passwords_match(cls, v, info):
        if 'new_password' in info.data and v != info.data['new_password']:
            raise ValueError('Passwords do not match')
        return v


class EmailVerificationRequest(BaseModel):
    """Email verification request model."""
    token: str = Field(..., min_length=1)


class TwoFactorSetupRequest(BaseModel):
    """Two-factor authentication setup request model."""
    password: str = Field(..., min_length=1, max_length=128)


class TwoFactorVerifyRequest(BaseModel):
    """Two-factor authentication verification request model."""
    code: str = Field(..., min_length=6, max_length=6)


class OAuthLoginRequest(BaseModel):
    """OAuth login request model."""
    provider: str = Field(..., min_length=1, max_length=50)
    redirect_uri: Optional[str] = None


class OAuthCallbackRequest(BaseModel):
    """OAuth callback request model."""
    code: str = Field(..., min_length=1)
    state: Optional[str] = None


# User Management Models
class UserUpdateRequest(BaseModel):
    """User update request model."""
    username: Optional[str] = Field(None, min_length=3, max_length=100)
    first_name: Optional[str] = Field(None, min_length=1, max_length=100)
    last_name: Optional[str] = Field(None, min_length=1, max_length=100)
    bio: Optional[str] = Field(None, max_length=1000)
    location: Optional[str] = Field(None, max_length=200)
    website: Optional[str] = Field(None, max_length=500)
    language_preference: Optional[LanguageEnum] = None
    timezone: Optional[str] = Field(None, max_length=50)


class PasswordChangeRequest(BaseModel):
    """Password change request model."""
    current_password: str = Field(..., min_length=1, max_length=128)
    new_password: str = Field(..., min_length=8, max_length=128)
    confirm_password: str = Field(..., min_length=8, max_length=128)
    
    @field_validator('confirm_password')
    @classmethod
    def passwords_match(cls, v, info):
        if 'new_password' in info.data and v != info.data['new_password']:
            raise ValueError('Passwords do not match')
        return v


class UserPreferencesUpdateRequest(BaseModel):
    """User preferences update request model."""
    preferences: Dict[str, Any] = Field(default_factory=dict)
    notification_settings: Dict[str, Any] = Field(default_factory=dict)


# Chat Models
class ChatCreateRequest(BaseModel):
    """Chat creation request model."""
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    ai_model: str = Field(default="gemini-pro", max_length=100)
    language: LanguageEnum = LanguageEnum.ARABIC
    max_tokens: int = Field(default=2048, ge=1, le=8192)
    temperature: str = Field(default="0.7", pattern=r'^[0-9]*\.?[0-9]+$')
    settings: Dict[str, Any] = Field(default_factory=dict)


class ChatUpdateRequest(BaseModel):
    """Chat update request model."""
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    ai_model: Optional[str] = Field(None, max_length=100)
    language: Optional[LanguageEnum] = None
    max_tokens: Optional[int] = Field(None, ge=1, le=8192)
    temperature: Optional[str] = Field(None, pattern=r'^[0-9]*\.?[0-9]+$')
    settings: Optional[Dict[str, Any]] = None


class MessageCreateRequest(BaseModel):
    """Message creation request model."""
    content: str = Field(..., min_length=1, max_length=4000)
    role: MessageRoleEnum = MessageRoleEnum.USER
    message_type: MessageTypeEnum = MessageTypeEnum.TEXT
    context_data: Optional[Dict[str, Any]] = Field(default_factory=dict)
    attachments: Optional[List[Dict[str, Any]]] = Field(default_factory=list)


class MessageUpdateRequest(BaseModel):
    """Message update request model."""
    content: str = Field(..., min_length=1, max_length=4000)


class ChatFeedbackRequest(BaseModel):
    """Chat feedback request model."""
    feedback_type: FeedbackTypeEnum
    rating: Optional[int] = Field(None, ge=1, le=5)
    comment: Optional[str] = Field(None, max_length=1000)
    feedback_data: Optional[Dict[str, Any]] = Field(default_factory=dict)


# Intelligent QA Models
class QuestionRequest(BaseModel):
    """Question request model."""
    question: str = Field(..., min_length=1, max_length=1000)
    language: LanguageEnum = LanguageEnum.ARABIC
    context: Optional[str] = Field(None, max_length=2000)
    include_sources: bool = True
    max_results: int = Field(default=5, ge=1, le=20)


class QuestionVariantRequest(BaseModel):
    """Question variant generation request model."""
    question: str = Field(..., min_length=1, max_length=1000)
    language: LanguageEnum = LanguageEnum.ARABIC
    num_variants: int = Field(default=3, ge=1, le=10)


class NewsScrapingRequest(BaseModel):
    """News scraping request model."""
    query: str = Field(..., min_length=1, max_length=200)
    language: LanguageEnum = LanguageEnum.ARABIC
    max_articles: int = Field(default=10, ge=1, le=50)
    sources: Optional[List[str]] = Field(default_factory=list)


# SMTP Configuration Models
class SMTPConfigRequest(BaseModel):
    """SMTP configuration request model."""
    provider: str = Field(..., min_length=1, max_length=50)
    host: str = Field(..., min_length=1, max_length=255)
    port: int = Field(..., ge=1, le=65535)
    username: str = Field(..., min_length=1, max_length=255)
    password: str = Field(..., min_length=1, max_length=255)
    use_tls: bool = True
    use_ssl: bool = False
    from_name: str = Field(..., min_length=1, max_length=100)
    from_address: EmailStr


class SMTPTestRequest(BaseModel):
    """SMTP test request model."""
    test_email: EmailStr
    subject: str = Field(default="SMTP Test", max_length=200)
    message: str = Field(default="This is a test email from SyriaGPT", max_length=1000)


# Session Management Models
class SessionRefreshRequest(BaseModel):
    """Session refresh request model."""
    refresh_token: str = Field(..., min_length=1)


class SessionRevokeRequest(BaseModel):
    """Session revoke request model."""
    session_token: Optional[str] = None  # If None, revoke all sessions


# Search and Filter Models
class SearchRequest(BaseModel):
    """Search request model."""
    query: str = Field(..., min_length=1, max_length=200)
    filters: Optional[Dict[str, Any]] = Field(default_factory=dict)
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)
    sort_by: Optional[str] = None
    sort_order: str = Field(default="desc", pattern=r'^(asc|desc)$')


class FilterRequest(BaseModel):
    """Filter request model."""
    filters: Dict[str, Any] = Field(default_factory=dict)
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)
    sort_by: Optional[str] = None
    sort_order: str = Field(default="desc", pattern=r'^(asc|desc)$')


# Bulk Operations Models
class BulkDeleteRequest(BaseModel):
    """Bulk delete request model."""
    ids: List[str] = Field(..., min_items=1, max_items=100)


class BulkUpdateRequest(BaseModel):
    """Bulk update request model."""
    ids: List[str] = Field(..., min_items=1, max_items=100)
    updates: Dict[str, Any] = Field(..., min_items=1)


# File Upload Models
class FileUploadRequest(BaseModel):
    """File upload request model."""
    filename: str = Field(..., min_length=1, max_length=255)
    content_type: str = Field(..., min_length=1, max_length=100)
    file_size: int = Field(..., ge=1, le=10485760)  # 10MB max


# Analytics Models
class AnalyticsRequest(BaseModel):
    """Analytics request model."""
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    metrics: List[str] = Field(default_factory=list)
    group_by: Optional[str] = None
    filters: Optional[Dict[str, Any]] = Field(default_factory=dict)


# Health Check Models
class HealthCheckRequest(BaseModel):
    """Health check request model."""
    include_details: bool = False
    check_services: List[str] = Field(default_factory=list)
