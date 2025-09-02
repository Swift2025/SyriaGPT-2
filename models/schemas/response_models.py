from datetime import datetime
from typing import Optional, Dict, Any, List, Union
from pydantic import BaseModel


class UserRegistrationResponse(BaseModel):
    id: str
    email: str
    phone_number: Optional[str]
    full_name: Optional[str]
    profile_picture: Optional[str]
    oauth_provider: Optional[str]
    status: str
    is_email_verified: bool
    is_phone_verified: bool
    created_at: datetime
    registration_token: Optional[str]
    message: str


class EmailVerificationResponse(BaseModel):
    message: str
    verified: bool
    user_id: str
    email: str


class OAuthProvidersResponse(BaseModel):
    providers: list[str]
    configured_providers: Dict[str, bool]


class OAuthAuthorizationResponse(BaseModel):
    authorization_url: str
    redirect_uri: str
    state: str
    provider: str


class HealthResponse(BaseModel):
    status: str
    service: str
    email_configured: bool
    oauth_providers: list[str]
    database_connected: bool
    version: str


class ErrorResponse(BaseModel):
    error: str
    message: str
    details: Optional[Dict[str, Any]] = None
    status_code: int


class LoginResponse(BaseModel):
    access_token: Optional[str] = None
    token_type: str = "bearer"
    user_id: str
    email: str
    full_name: Optional[str] = None
    two_factor_required: bool = False
    message: Optional[str] = None    

class TwoFactorSetupResponse(BaseModel):
    secret_key: str
    qr_code: str # This will be a base64 encoded image string

class GeneralResponse(BaseModel):
    status: str
    message: str


class QuestionResponse(BaseModel):
    id: str
    user_id: str
    question: str
    created_at: datetime
    updated_at: datetime


class AnswerResponse(BaseModel):
    id: str
    answer: str
    question_id: str
    user_id: str
    created_at: datetime
    author: str


class QuestionWithAnswersResponse(BaseModel):
    question: QuestionResponse
    answers: list[AnswerResponse]


class SMTPProviderInfo(BaseModel):
    name: str
    instructions: str
    setup_url: str
    app_password_required: bool


# User Management Response Models
class UserResponse(BaseModel):
    id: str
    email: str
    phone_number: Optional[str]
    first_name: Optional[str]
    last_name: Optional[str]
    full_name: Optional[str]
    profile_picture: Optional[str]
    oauth_provider: Optional[str]
    oauth_provider_id: Optional[str]
    two_factor_enabled: bool
    is_email_verified: bool
    is_phone_verified: bool
    status: str
    last_login_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime


class UserDetailResponse(BaseModel):
    user: UserResponse
    active_sessions_count: int
    total_sessions_count: int
    last_activity: Optional[datetime]
    settings: Dict[str, Any]


class UserListResponse(BaseModel):
    users: List[UserResponse]
    total_count: int
    page: int
    page_size: int
    total_pages: int


class UserStatsResponse(BaseModel):
    total_users: int
    active_users: int
    suspended_users: int
    banned_users: int
    pending_verification: int
    email_verified_users: int
    phone_verified_users: int
    oauth_users: int
    two_factor_enabled_users: int
    users_created_today: int
    users_created_this_week: int
    users_created_this_month: int


class UserUpdateResponse(BaseModel):
    user: UserResponse
    message: str


class UserPasswordChangeResponse(BaseModel):
    message: str
    password_changed_at: datetime


class UserBulkActionResponse(BaseModel):
    success_count: int
    failed_count: int
    failed_users: List[Dict[str, str]]
    message: str


# Session Management Response Models
class SessionResponse(BaseModel):
    id: str
    user_id: str
    session_token: str
    device_info: Optional[str]
    ip_address: Optional[str]
    user_agent: Optional[str]
    location: Optional[str]
    is_active: bool
    is_mobile: bool
    last_activity_at: datetime
    expires_at: datetime
    created_at: datetime
    updated_at: datetime


class SessionDetailResponse(BaseModel):
    session: SessionResponse
    user: Optional[UserResponse]
    device_summary: Optional[str]
    location_info: Optional[Dict[str, Any]]


class SessionListResponse(BaseModel):
    sessions: List[SessionResponse]
    total_count: int
    page: int
    page_size: int
    total_pages: int


class SessionStatsResponse(BaseModel):
    total_sessions: int
    active_sessions: int
    expired_sessions: int
    mobile_sessions: int
    desktop_sessions: int
    sessions_created_today: int
    sessions_created_this_week: int
    average_session_duration_hours: float


class SessionCreateResponse(BaseModel):
    session: SessionResponse
    access_token: str
    refresh_token: Optional[str]
    message: str


class SessionUpdateResponse(BaseModel):
    session: SessionResponse
    message: str


class SessionBulkActionResponse(BaseModel):
    success_count: int
    failed_count: int
    failed_sessions: List[Dict[str, str]]
    message: str


# Settings Management Response Models
class UserSettingsResponse(BaseModel):
    user_id: str
    email_notifications: bool
    sms_notifications: bool
    two_factor_enabled: bool
    session_timeout_hours: int
    max_concurrent_sessions: int
    language: str
    timezone: str
    theme: str
    updated_at: datetime


class SystemSettingsResponse(BaseModel):
    max_users: Optional[int]
    max_sessions_per_user: int
    session_timeout_hours: int
    password_expiry_days: int
    require_email_verification: bool
    require_phone_verification: bool
    allow_oauth_registration: bool
    allow_oauth_login: bool
    maintenance_mode: bool
    maintenance_message: Optional[str]
    updated_at: datetime


class SettingsUpdateResponse(BaseModel):
    settings: Union[UserSettingsResponse, SystemSettingsResponse]
    message: str


# Pagination and Search Response Models
class PaginationInfo(BaseModel):
    page: int
    page_size: int
    total_count: int
    total_pages: int
    has_next: bool
    has_previous: bool


class SearchResponse(BaseModel):
    items: List[Any]
    pagination: PaginationInfo
    filters_applied: Dict[str, Any]


# SMTP Configuration Response Models
class SMTPProvidersResponse(BaseModel):
    providers: Dict[str, SMTPProviderInfo]
    supported_domains: Dict[str, str]


class SMTPTestResponse(BaseModel):
    success: bool
    message: str
    provider_detected: Optional[str] = None
    provider_info: Optional[SMTPProviderInfo] = None


class SMTPConfigResponse(BaseModel):
    success: bool
    message: str
    provider: str
    host: str
    port: int
    use_ssl: bool
    use_tls: bool


# AI Chat Management Response Models
class ChatResponse(BaseModel):
    id: str
    user_id: str
    title: Optional[str]
    description: Optional[str]
    context: Optional[str]
    language: str
    model_preference: str
    max_tokens: int
    temperature: float
    message_count: int
    is_archived: bool
    is_pinned: bool
    last_message_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime


class ChatMessageResponse(BaseModel):
    id: str
    chat_id: str
    user_id: str
    message: str
    message_type: str
    attachments: Optional[List[str]]
    context: Optional[str]
    language: str
    priority: str
    is_ai_response: bool
    ai_model_used: Optional[str]
    processing_time_ms: Optional[int]
    confidence_score: Optional[float]
    feedback_rating: Optional[int]
    feedback_comment: Optional[str]
    created_at: datetime


class ChatDetailResponse(BaseModel):
    chat: ChatResponse
    messages: List[ChatMessageResponse]
    user: Optional[UserResponse]
    analytics: Optional[Dict[str, Any]]


class ChatListResponse(BaseModel):
    chats: List[ChatResponse]
    total_count: int
    page: int
    page_size: int
    total_pages: int


class ChatCreateResponse(BaseModel):
    chat: ChatResponse
    message: str


class ChatUpdateResponse(BaseModel):
    chat: ChatResponse
    message: str


class ChatMessageCreateResponse(BaseModel):
    user_message: ChatMessageResponse
    ai_response: Optional[ChatMessageResponse]
    processing_time_ms: int
    message: str


class ChatBulkActionResponse(BaseModel):
    success_count: int
    failed_count: int
    failed_chats: List[Dict[str, str]]
    message: str


class ChatExportResponse(BaseModel):
    export_id: str
    format: str
    download_url: Optional[str]
    file_size_bytes: Optional[int]
    expires_at: datetime
    message: str


class ChatAnalyticsResponse(BaseModel):
    total_chats: int
    total_messages: int
    ai_responses: int
    average_response_time_ms: float
    user_satisfaction_score: float
    most_used_language: str
    most_used_model: str
    daily_stats: List[Dict[str, Any]]
    weekly_stats: List[Dict[str, Any]]
    monthly_stats: List[Dict[str, Any]]


class ChatFeedbackResponse(BaseModel):
    message_id: str
    rating: int
    feedback_type: str
    comment: Optional[str]
    category: Optional[str]
    created_at: datetime
    message: str


class ChatSettingsResponse(BaseModel):
    user_id: str
    default_language: str
    default_model: str
    default_max_tokens: int
    default_temperature: float
    auto_archive_after_days: int
    max_chats_per_user: int
    max_messages_per_chat: int
    enable_voice_input: bool
    enable_file_upload: bool
    enable_image_analysis: bool
    enable_context_memory: bool
    enable_chat_history: bool
    enable_analytics: bool
    enable_feedback: bool
    updated_at: datetime


class ChatStatsResponse(BaseModel):
    total_chats: int
    active_chats: int
    archived_chats: int
    pinned_chats: int
    total_messages: int
    ai_responses: int
    average_messages_per_chat: float
    average_response_time_ms: float
    chats_created_today: int
    chats_created_this_week: int
    chats_created_this_month: int
    most_active_hour: int
    most_used_language: str
    most_used_model: str    