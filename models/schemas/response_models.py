"""
Pydantic response models for SyriaGPT API.
"""

from datetime import datetime
from typing import Optional, List, Dict, Any, Union
from pydantic import BaseModel, Field
from enum import Enum


class StatusEnum(str, Enum):
    """Status enumeration."""
    SUCCESS = "success"
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


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


# Base Response Models
class BaseResponse(BaseModel):
    """Base response model."""
    status: StatusEnum
    message: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    request_id: Optional[str] = None


class ErrorResponse(BaseResponse):
    """Error response model."""
    status: StatusEnum = StatusEnum.ERROR
    error_code: Optional[str] = None
    error_details: Optional[Dict[str, Any]] = None


class SuccessResponse(BaseResponse):
    """Success response model."""
    status: StatusEnum = StatusEnum.SUCCESS
    data: Optional[Dict[str, Any]] = None


# Authentication Response Models
class TokenResponse(BaseModel):
    """Token response model."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    expires_at: datetime


class UserResponse(BaseModel):
    """User response model."""
    id: str
    email: str
    username: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    full_name: Optional[str] = None
    display_name: str
    avatar_url: Optional[str] = None
    bio: Optional[str] = None
    location: Optional[str] = None
    website: Optional[str] = None
    language_preference: str
    timezone: str
    is_active: bool
    is_verified: bool
    is_oauth_user: bool
    two_factor_enabled: bool
    last_login_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime


class LoginResponse(BaseResponse):
    """Login response model."""
    status: StatusEnum = StatusEnum.SUCCESS
    user: UserResponse
    tokens: TokenResponse
    requires_two_factor: bool = False


class RegistrationResponse(BaseResponse):
    """Registration response model."""
    status: StatusEnum = StatusEnum.SUCCESS
    user: UserResponse
    message: str = "User registered successfully. Please check your email for verification."


class EmailVerificationResponse(BaseResponse):
    """Email verification response model."""
    status: StatusEnum = StatusEnum.SUCCESS
    verified: bool
    message: str


class PasswordResetResponse(BaseResponse):
    """Password reset response model."""
    status: StatusEnum = StatusEnum.SUCCESS
    message: str = "Password reset email sent successfully."


class TwoFactorSetupResponse(BaseResponse):
    """Two-factor setup response model."""
    status: StatusEnum = StatusEnum.SUCCESS
    qr_code: str
    secret_key: str
    backup_codes: List[str]
    message: str = "Two-factor authentication setup successfully."


class OAuthLoginResponse(BaseResponse):
    """OAuth login response model."""
    status: StatusEnum = StatusEnum.SUCCESS
    auth_url: str
    state: str


# Chat Response Models
class ChatMessageResponse(BaseModel):
    """Chat message response model."""
    id: str
    content: str
    role: MessageRoleEnum
    message_type: MessageTypeEnum
    tokens_used: int
    processing_time_ms: Optional[int] = None
    ai_model_used: Optional[str] = None
    context_data: Optional[Dict[str, Any]] = None
    attachments: Optional[List[Dict[str, Any]]] = None
    is_edited: bool
    edited_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime


class ChatResponse(BaseModel):
    """Chat response model."""
    id: str
    title: str
    description: Optional[str] = None
    status: str
    ai_model: str
    language: str
    max_tokens: int
    temperature: str
    message_count: int
    total_tokens_used: int
    last_message_at: Optional[datetime] = None
    settings: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime


class ChatWithMessagesResponse(ChatResponse):
    """Chat with messages response model."""
    messages: List[ChatMessageResponse]


class ChatCreateResponse(BaseResponse):
    """Chat creation response model."""
    status: StatusEnum = StatusEnum.SUCCESS
    chat: ChatResponse
    message: str = "Chat created successfully."


class MessageCreateResponse(BaseResponse):
    """Message creation response model."""
    status: StatusEnum = StatusEnum.SUCCESS
    message: ChatMessageResponse
    chat: ChatResponse
    message_text: str = "Message sent successfully."


class ChatListResponse(BaseResponse):
    """Chat list response model."""
    status: StatusEnum = StatusEnum.SUCCESS
    chats: List[ChatResponse]
    total_count: int
    page: int
    page_size: int
    total_pages: int


class ChatFeedbackResponse(BaseModel):
    """Chat feedback response model."""
    id: str
    feedback_type: FeedbackTypeEnum
    rating: Optional[int] = None
    comment: Optional[str] = None
    feedback_data: Optional[Dict[str, Any]] = None
    created_at: datetime


# Intelligent QA Response Models
class QAAnswerResponse(BaseModel):
    """QA answer response model."""
    answer: str
    confidence_score: float
    sources: Optional[List[Dict[str, Any]]] = None
    related_questions: Optional[List[str]] = None
    processing_time_ms: Optional[int] = None
    ai_model_used: Optional[str] = None


class QuestionResponse(BaseResponse):
    """Question response model."""
    status: StatusEnum = StatusEnum.SUCCESS
    question: str
    answer: QAAnswerResponse
    language: str
    message: str = "Question processed successfully."


class QuestionVariantResponse(BaseResponse):
    """Question variant response model."""
    status: StatusEnum = StatusEnum.SUCCESS
    original_question: str
    variants: List[str]
    language: str
    message: str = "Question variants generated successfully."


class NewsArticleResponse(BaseModel):
    """News article response model."""
    title: str
    content: str
    url: str
    source: str
    published_at: Optional[datetime] = None
    author: Optional[str] = None
    image_url: Optional[str] = None
    summary: Optional[str] = None


class NewsScrapingResponse(BaseResponse):
    """News scraping response model."""
    status: StatusEnum = StatusEnum.SUCCESS
    query: str
    articles: List[NewsArticleResponse]
    total_found: int
    language: str
    message: str = "News articles scraped successfully."


# SMTP Configuration Response Models
class SMTPProviderResponse(BaseModel):
    """SMTP provider response model."""
    name: str
    host: str
    port: int
    use_tls: bool
    use_ssl: bool
    authentication: str
    enabled: bool
    icon: Optional[str] = None
    color: Optional[str] = None
    description: Optional[str] = None
    setup_instructions: Optional[List[str]] = None
    limits: Optional[Dict[str, Any]] = None


class SMTPConfigResponse(BaseResponse):
    """SMTP configuration response model."""
    status: StatusEnum = StatusEnum.SUCCESS
    provider: SMTPProviderResponse
    configured: bool
    message: str = "SMTP configuration retrieved successfully."


class SMTPTestResponse(BaseResponse):
    """SMTP test response model."""
    status: StatusEnum = StatusEnum.SUCCESS
    success: bool
    message: str
    test_details: Optional[Dict[str, Any]] = None


# Session Management Response Models
class SessionResponse(BaseModel):
    """Session response model."""
    id: str
    session_token: str
    is_active: bool
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    device_info: Optional[Dict[str, Any]] = None
    location_info: Optional[Dict[str, Any]] = None
    expires_at: datetime
    last_activity_at: datetime
    created_at: datetime


class SessionListResponse(BaseResponse):
    """Session list response model."""
    status: StatusEnum = StatusEnum.SUCCESS
    sessions: List[SessionResponse]
    total_count: int
    active_count: int


class SessionRefreshResponse(BaseResponse):
    """Session refresh response model."""
    status: StatusEnum = StatusEnum.SUCCESS
    tokens: TokenResponse
    message: str = "Session refreshed successfully."


# User Management Response Models
class UserListResponse(BaseResponse):
    """User list response model."""
    status: StatusEnum = StatusEnum.SUCCESS
    users: List[UserResponse]
    total_count: int
    page: int
    page_size: int
    total_pages: int


class UserUpdateResponse(BaseResponse):
    """User update response model."""
    status: StatusEnum = StatusEnum.SUCCESS
    user: UserResponse
    message: str = "User updated successfully."


class UserPreferencesResponse(BaseResponse):
    """User preferences response model."""
    status: StatusEnum = StatusEnum.SUCCESS
    preferences: Dict[str, Any]
    notification_settings: Dict[str, Any]
    message: str = "User preferences retrieved successfully."


# Health Check Response Models
class ServiceHealthResponse(BaseModel):
    """Service health response model."""
    service: str
    status: str
    response_time_ms: Optional[int] = None
    last_check: datetime
    details: Optional[Dict[str, Any]] = None


class HealthCheckResponse(BaseResponse):
    """Health check response model."""
    status: StatusEnum = StatusEnum.SUCCESS
    overall_status: str
    services: List[ServiceHealthResponse]
    uptime_seconds: int
    version: str
    environment: str


# Analytics Response Models
class AnalyticsResponse(BaseResponse):
    """Analytics response model."""
    status: StatusEnum = StatusEnum.SUCCESS
    metrics: Dict[str, Any]
    period: Dict[str, datetime]
    message: str = "Analytics data retrieved successfully."


# Search Response Models
class SearchResultResponse(BaseModel):
    """Search result response model."""
    id: str
    title: str
    content: str
    relevance_score: float
    category: Optional[str] = None
    tags: Optional[List[str]] = None
    created_at: datetime
    updated_at: datetime


class SearchResponse(BaseResponse):
    """Search response model."""
    status: StatusEnum = StatusEnum.SUCCESS
    query: str
    results: List[SearchResultResponse]
    total_count: int
    page: int
    page_size: int
    total_pages: int
    search_time_ms: int
    message: str = "Search completed successfully."


# File Upload Response Models
class FileUploadResponse(BaseResponse):
    """File upload response model."""
    status: StatusEnum = StatusEnum.SUCCESS
    file_id: str
    filename: str
    file_size: int
    content_type: str
    upload_url: Optional[str] = None
    message: str = "File uploaded successfully."


# Bulk Operations Response Models
class BulkOperationResponse(BaseResponse):
    """Bulk operation response model."""
    status: StatusEnum = StatusEnum.SUCCESS
    operation: str
    total_items: int
    successful_items: int
    failed_items: int
    errors: Optional[List[Dict[str, Any]]] = None
    message: str


# Pagination Models
class PaginationInfo(BaseModel):
    """Pagination information model."""
    page: int
    page_size: int
    total_count: int
    total_pages: int
    has_next: bool
    has_previous: bool


class PaginatedResponse(BaseResponse):
    """Paginated response model."""
    pagination: PaginationInfo


# API Documentation Models
class APIEndpointResponse(BaseModel):
    """API endpoint response model."""
    path: str
    method: str
    summary: str
    description: Optional[str] = None
    parameters: Optional[List[Dict[str, Any]]] = None
    responses: Optional[Dict[str, Any]] = None
    tags: Optional[List[str]] = None


class APIDocumentationResponse(BaseResponse):
    """API documentation response model."""
    status: StatusEnum = StatusEnum.SUCCESS
    title: str
    version: str
    description: str
    endpoints: List[APIEndpointResponse]
    message: str = "API documentation retrieved successfully."
