"""
User session model for SyriaGPT application.
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


class UserSession(BaseModel):
    """User session model for managing user sessions."""
    
    __tablename__ = "user_sessions"
    
    # Session identification
    session_token = Column(String(255), unique=True, nullable=False, index=True)
    refresh_token = Column(String(255), unique=True, nullable=True, index=True)
    
    # User relationship
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    user = relationship("User", back_populates="sessions")
    
    # Session information
    ip_address = Column(String(45), nullable=True)  # IPv6 support
    user_agent = Column(Text, nullable=True)
    device_info = Column(JSONB, nullable=True)
    location_info = Column(JSONB, nullable=True)
    
    # Session status
    is_active = Column(Boolean, default=True, nullable=False)
    is_revoked = Column(Boolean, default=False, nullable=False)
    
    # Session timing
    expires_at = Column(DateTime(timezone=True), nullable=False)
    last_activity_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    revoked_at = Column(DateTime(timezone=True), nullable=True)
    
    # Session metadata
    session_data = Column(JSONB, nullable=True, default=dict)
    security_flags = Column(JSONB, nullable=True, default=dict)
    
    # Indexes
    __table_args__ = (
        Index('idx_session_user_active', 'user_id', 'is_active'),
        Index('idx_session_expires', 'expires_at'),
        Index('idx_session_last_activity', 'last_activity_at'),
        Index('idx_session_token_active', 'session_token', 'is_active'),
        CheckConstraint('expires_at > created_at', name='expires_after_created'),
    )
    
    def __repr__(self) -> str:
        return f"<UserSession(id={self.id}, user_id={self.user_id}, active={self.is_active})>"
    
    @property
    def is_expired(self) -> bool:
        """Check if session is expired."""
        return datetime.utcnow() > self.expires_at
    
    @property
    def is_valid(self) -> bool:
        """Check if session is valid (active, not revoked, not expired)."""
        return self.is_active and not self.is_revoked and not self.is_expired
    
    def extend_session(self, duration_hours: int = 24) -> None:
        """Extend session expiration time."""
        self.expires_at = datetime.utcnow() + timedelta(hours=duration_hours)
        self.last_activity_at = datetime.utcnow()
    
    def revoke_session(self) -> None:
        """Revoke the session."""
        self.is_active = False
        self.is_revoked = True
        self.revoked_at = datetime.utcnow()
    
    def update_activity(self) -> None:
        """Update last activity timestamp."""
        self.last_activity_at = datetime.utcnow()
    
    def set_session_data(self, key: str, value: Any) -> None:
        """Set session data."""
        if self.session_data is None:
            self.session_data = {}
        self.session_data[key] = value
    
    def get_session_data(self, key: str, default: Any = None) -> Any:
        """Get session data."""
        if self.session_data is None:
            return default
        return self.session_data.get(key, default)
    
    def set_security_flag(self, key: str, value: Any) -> None:
        """Set security flag."""
        if self.security_flags is None:
            self.security_flags = {}
        self.security_flags[key] = value
    
    def get_security_flag(self, key: str, default: Any = None) -> Any:
        """Get security flag."""
        if self.security_flags is None:
            return default
        return self.security_flags.get(key, default)
    
    def check_security_flag(self, key: str) -> bool:
        """Check if security flag is set."""
        return self.get_security_flag(key, False)
    
    @classmethod
    def create_session(
        cls,
        user_id: str,
        session_token: str,
        refresh_token: str = None,
        expires_hours: int = 24,
        ip_address: str = None,
        user_agent: str = None,
        device_info: dict = None,
        location_info: dict = None
    ) -> "UserSession":
        """Create a new user session."""
        now = datetime.utcnow()
        expires_at = now + timedelta(hours=expires_hours)
        
        return cls(
            user_id=user_id,
            session_token=session_token,
            refresh_token=refresh_token,
            expires_at=expires_at,
            last_activity_at=now,
            ip_address=ip_address,
            user_agent=user_agent,
            device_info=device_info,
            location_info=location_info,
            session_data={},
            security_flags={}
        )
