"""
Chat models for SyriaGPT application.
"""

from datetime import datetime
from typing import Any
from sqlalchemy import (
    Column, String, Boolean, DateTime, Text, Integer, 
    ForeignKey, Index, CheckConstraint, Enum
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from enum import Enum as PyEnum
from .base import BaseModel


class ChatStatus(PyEnum):
    """Chat status enumeration."""
    ACTIVE = "active"
    ARCHIVED = "archived"
    DELETED = "deleted"


class MessageRole(PyEnum):
    """Message role enumeration."""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class MessageType(PyEnum):
    """Message type enumeration."""
    TEXT = "text"
    IMAGE = "image"
    FILE = "file"
    AUDIO = "audio"
    VIDEO = "video"


class FeedbackType(PyEnum):
    """Feedback type enumeration."""
    POSITIVE = "positive"
    NEGATIVE = "negative"
    NEUTRAL = "neutral"


class Chat(BaseModel):
    """Chat model for storing chat sessions."""
    
    __tablename__ = "chats"
    
    # Basic chat information
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    status = Column(Enum(ChatStatus), default=ChatStatus.ACTIVE, nullable=False)
    
    # User relationship
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    user = relationship("User", back_populates="chats")
    
    # Chat settings
    ai_model = Column(String(100), default="gemini-pro", nullable=False)
    language = Column(String(10), default="ar", nullable=False)
    max_tokens = Column(Integer, default=2048, nullable=False)
    temperature = Column(String(10), default="0.7", nullable=False)
    
    # Chat metadata
    message_count = Column(Integer, default=0, nullable=False)
    total_tokens_used = Column(Integer, default=0, nullable=False)
    last_message_at = Column(DateTime(timezone=True), nullable=True)
    
    # Chat settings and preferences
    settings = Column(JSONB, nullable=True, default=dict)
    
    # Relationships
    messages = relationship("ChatMessage", back_populates="chat", cascade="all, delete-orphan")
    feedback = relationship("ChatFeedback", back_populates="chat", cascade="all, delete-orphan")
    
    # Indexes
    __table_args__ = (
        Index('idx_chat_user_status', 'user_id', 'status'),
        Index('idx_chat_created_at', 'created_at'),
        Index('idx_chat_last_message', 'last_message_at'),
        CheckConstraint('message_count >= 0', name='message_count_positive'),
        CheckConstraint('total_tokens_used >= 0', name='total_tokens_positive'),
        CheckConstraint('max_tokens > 0', name='max_tokens_positive'),
    )
    
    def __repr__(self) -> str:
        return f"<Chat(id={self.id}, title={self.title}, user_id={self.user_id})>"
    
    def update_message_count(self) -> None:
        """Update message count."""
        self.message_count = len([m for m in self.messages if not m.is_deleted])
    
    def update_last_message_time(self) -> None:
        """Update last message timestamp."""
        if self.messages:
            last_message = max(self.messages, key=lambda m: m.created_at)
            self.last_message_at = last_message.created_at
    
    def add_tokens_used(self, tokens: int) -> None:
        """Add tokens to total usage."""
        self.total_tokens_used += tokens
    
    def get_setting(self, key: str, default: Any = None) -> Any:
        """Get chat setting."""
        if self.settings is None:
            return default
        return self.settings.get(key, default)
    
    def set_setting(self, key: str, value: Any) -> None:
        """Set chat setting."""
        if self.settings is None:
            self.settings = {}
        self.settings[key] = value


class ChatMessage(BaseModel):
    """Chat message model for storing individual messages."""
    
    __tablename__ = "chat_messages"
    
    # Message content
    content = Column(Text, nullable=False)
    role = Column(Enum(MessageRole), nullable=False)
    message_type = Column(Enum(MessageType), default=MessageType.TEXT, nullable=False)
    
    # Chat relationship
    chat_id = Column(UUID(as_uuid=True), ForeignKey("chats.id"), nullable=False)
    chat = relationship("Chat", back_populates="messages")
    
    # Message metadata
    tokens_used = Column(Integer, default=0, nullable=False)
    processing_time_ms = Column(Integer, nullable=True)
    
    # AI-specific fields
    ai_model_used = Column(String(100), nullable=True)
    ai_parameters = Column(JSONB, nullable=True)
    
    # Message context
    context_data = Column(JSONB, nullable=True)
    attachments = Column(JSONB, nullable=True)
    
    # Message status
    is_edited = Column(Boolean, default=False, nullable=False)
    edited_at = Column(DateTime(timezone=True), nullable=True)
    original_content = Column(Text, nullable=True)
    
    # Indexes
    __table_args__ = (
        Index('idx_message_chat_created', 'chat_id', 'created_at'),
        Index('idx_message_role', 'role'),
        Index('idx_message_type', 'message_type'),
        CheckConstraint('tokens_used >= 0', name='tokens_used_positive'),
        CheckConstraint('processing_time_ms >= 0', name='processing_time_positive'),
    )
    
    def __repr__(self) -> str:
        return f"<ChatMessage(id={self.id}, chat_id={self.chat_id}, role={self.role})>"
    
    def edit_content(self, new_content: str) -> None:
        """Edit message content."""
        if not self.is_edited:
            self.original_content = self.content
        self.content = new_content
        self.is_edited = True
        self.edited_at = datetime.utcnow()
    
    def get_context(self, key: str, default: Any = None) -> Any:
        """Get message context data."""
        if self.context_data is None:
            return default
        return self.context_data.get(key, default)
    
    def set_context(self, key: str, value: Any) -> None:
        """Set message context data."""
        if self.context_data is None:
            self.context_data = {}
        self.context_data[key] = value


class ChatFeedback(BaseModel):
    """Chat feedback model for storing user feedback on messages."""
    
    __tablename__ = "chat_feedback"
    
    # Feedback content
    feedback_type = Column(Enum(FeedbackType), nullable=False)
    rating = Column(Integer, nullable=True)  # 1-5 scale
    comment = Column(Text, nullable=True)
    
    # Relationships
    chat_id = Column(UUID(as_uuid=True), ForeignKey("chats.id"), nullable=False)
    chat = relationship("Chat", back_populates="feedback")
    
    message_id = Column(UUID(as_uuid=True), ForeignKey("chat_messages.id"), nullable=True)
    message = relationship("ChatMessage")
    
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    user = relationship("User")
    
    # Feedback metadata
    feedback_data = Column(JSONB, nullable=True)
    
    # Indexes
    __table_args__ = (
        Index('idx_feedback_chat', 'chat_id'),
        Index('idx_feedback_message', 'message_id'),
        Index('idx_feedback_user', 'user_id'),
        Index('idx_feedback_type', 'feedback_type'),
        CheckConstraint('rating >= 1 AND rating <= 5', name='rating_range'),
    )
    
    def __repr__(self) -> str:
        return f"<ChatFeedback(id={self.id}, type={self.feedback_type}, rating={self.rating})>"


class ChatSettings(BaseModel):
    """Chat settings model for storing user chat preferences."""
    
    __tablename__ = "chat_settings"
    
    # User relationship
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, unique=True)
    user = relationship("User")
    
    # Default chat settings
    default_ai_model = Column(String(100), default="gemini-pro", nullable=False)
    default_language = Column(String(10), default="ar", nullable=False)
    default_max_tokens = Column(Integer, default=2048, nullable=False)
    default_temperature = Column(String(10), default="0.7", nullable=False)
    
    # Chat behavior settings
    auto_save_chats = Column(Boolean, default=True, nullable=False)
    auto_delete_old_chats = Column(Boolean, default=False, nullable=False)
    chat_retention_days = Column(Integer, default=30, nullable=False)
    
    # Notification settings
    notify_on_new_message = Column(Boolean, default=True, nullable=False)
    notify_on_chat_archived = Column(Boolean, default=False, nullable=False)
    
    # Privacy settings
    share_usage_data = Column(Boolean, default=False, nullable=False)
    allow_ai_learning = Column(Boolean, default=True, nullable=False)
    
    # Advanced settings
    advanced_settings = Column(JSONB, nullable=True, default=dict)
    
    # Indexes
    __table_args__ = (
        Index('idx_chat_settings_user', 'user_id'),
        CheckConstraint('default_max_tokens > 0', name='default_max_tokens_positive'),
        CheckConstraint('chat_retention_days > 0', name='chat_retention_positive'),
    )
    
    def __repr__(self) -> str:
        return f"<ChatSettings(id={self.id}, user_id={self.user_id})>"
    
    def get_advanced_setting(self, key: str, default: Any = None) -> Any:
        """Get advanced setting."""
        if self.advanced_settings is None:
            return default
        return self.advanced_settings.get(key, default)
    
    def set_advanced_setting(self, key: str, value: Any) -> None:
        """Set advanced setting."""
        if self.advanced_settings is None:
            self.advanced_settings = {}
        self.advanced_settings[key] = value
