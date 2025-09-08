"""
User model for SyriaGPT application.
"""

from datetime import datetime, timedelta
from typing import Any
from sqlalchemy import (
    Column, String, Boolean, DateTime, Text, Integer, 
    ForeignKey, Index, CheckConstraint
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from .base import BaseModel


class User(BaseModel):
    """User model for authentication and user management."""
    
    __tablename__ = "users"
    
    # Basic user information
    email = Column(String(255), unique=True, nullable=False, index=True)
    username = Column(String(100), unique=True, nullable=True, index=True)
    first_name = Column(String(100), nullable=True)
    last_name = Column(String(100), nullable=True)
    full_name = Column(String(200), nullable=True)
    
    # Authentication
    password_hash = Column(String(255), nullable=True)  # Nullable for OAuth users
    is_active = Column(Boolean, default=True, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)
    is_superuser = Column(Boolean, default=False, nullable=False)
    
    # Email verification
    email_verification_token = Column(String(255), nullable=True)
    email_verification_expires = Column(DateTime(timezone=True), nullable=True)
    email_verified_at = Column(DateTime(timezone=True), nullable=True)
    
    # Password reset
    password_reset_token = Column(String(255), nullable=True)
    password_reset_expires = Column(DateTime(timezone=True), nullable=True)
    
    # Two-factor authentication
    two_factor_enabled = Column(Boolean, default=False, nullable=False)
    two_factor_secret = Column(String(255), nullable=True)
    two_factor_backup_codes = Column(JSONB, nullable=True)
    
    # OAuth information
    oauth_provider = Column(String(50), nullable=True)  # google, facebook, etc.
    oauth_provider_id = Column(String(255), nullable=True)
    oauth_access_token = Column(Text, nullable=True)
    oauth_refresh_token = Column(Text, nullable=True)
    oauth_token_expires = Column(DateTime(timezone=True), nullable=True)
    
    # Profile information
    avatar_url = Column(String(500), nullable=True)
    bio = Column(Text, nullable=True)
    location = Column(String(200), nullable=True)
    website = Column(String(500), nullable=True)
    language_preference = Column(String(10), default='ar', nullable=False)
    timezone = Column(String(50), default='Asia/Damascus', nullable=False)
    
    # Account status
    last_login_at = Column(DateTime(timezone=True), nullable=True)
    last_login_ip = Column(String(45), nullable=True)  # IPv6 support
    login_count = Column(Integer, default=0, nullable=False)
    failed_login_attempts = Column(Integer, default=0, nullable=False)
    locked_until = Column(DateTime(timezone=True), nullable=True)
    
    # Preferences
    preferences = Column(JSONB, nullable=True, default=dict)
    notification_settings = Column(JSONB, nullable=True, default=dict)
    
    # Relationships
    sessions = relationship("UserSession", back_populates="user", cascade="all, delete-orphan")
    chats = relationship("Chat", back_populates="user", cascade="all, delete-orphan")
    
    # Indexes
    __table_args__ = (
        Index('idx_user_email_active', 'email', 'is_active'),
        Index('idx_user_oauth', 'oauth_provider', 'oauth_provider_id'),
        Index('idx_user_username_active', 'username', 'is_active'),
        CheckConstraint('email ~* \'^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\\.[A-Za-z]{2,}$\'', name='valid_email'),
        CheckConstraint('length(username) >= 3', name='username_min_length'),
        CheckConstraint('length(first_name) >= 1', name='first_name_min_length'),
        CheckConstraint('length(last_name) >= 1', name='last_name_min_length'),
    )
    
    def __repr__(self) -> str:
        return f"<User(id={self.id}, email={self.email}, username={self.username})>"
    
    @property
    def display_name(self) -> str:
        """Get display name for the user."""
        if self.full_name:
            return self.full_name
        elif self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        elif self.first_name:
            return self.first_name
        elif self.username:
            return self.username
        else:
            return self.email.split('@')[0]
    
    @property
    def is_oauth_user(self) -> bool:
        """Check if user is OAuth user."""
        return self.oauth_provider is not None
    
    @property
    def is_locked(self) -> bool:
        """Check if user account is locked."""
        if self.locked_until is None:
            return False
        return datetime.utcnow() < self.locked_until
    
    def lock_account(self, duration_minutes: int = 30) -> None:
        """Lock user account for specified duration."""
        self.locked_until = datetime.utcnow() + timedelta(minutes=duration_minutes)
    
    def unlock_account(self) -> None:
        """Unlock user account."""
        self.locked_until = None
        self.failed_login_attempts = 0
    
    def increment_login_count(self) -> None:
        """Increment login count and update last login."""
        self.login_count += 1
        self.last_login_at = datetime.utcnow()
    
    def increment_failed_login(self) -> None:
        """Increment failed login attempts."""
        self.failed_login_attempts += 1
    
    def reset_failed_login_attempts(self) -> None:
        """Reset failed login attempts."""
        self.failed_login_attempts = 0
    
    def set_preference(self, key: str, value: Any) -> None:
        """Set user preference."""
        if self.preferences is None:
            self.preferences = {}
        self.preferences[key] = value
    
    def get_preference(self, key: str, default: Any = None) -> Any:
        """Get user preference."""
        if self.preferences is None:
            return default
        return self.preferences.get(key, default)
    
    def set_notification_setting(self, key: str, value: Any) -> None:
        """Set notification setting."""
        if self.notification_settings is None:
            self.notification_settings = {}
        self.notification_settings[key] = value
    
    def get_notification_setting(self, key: str, default: Any = None) -> Any:
        """Get notification setting."""
        if self.notification_settings is None:
            return default
        return self.notification_settings.get(key, default)
