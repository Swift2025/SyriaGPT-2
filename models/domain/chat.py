from datetime import datetime
from typing import Optional, List, Dict, Any
from sqlalchemy import Column, String, Text, Integer, Float, Boolean, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
import uuid

from .base import Base


class Chat(Base):
    """Chat domain model for AI conversations"""
    
    __tablename__ = "chats"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    title = Column(String(255), nullable=True)
    description = Column(Text, nullable=True)
    context = Column(Text, nullable=True)
    language = Column(String(10), default="auto", nullable=False)
    model_preference = Column(String(50), default="gemini-1.5-flash", nullable=False)
    max_tokens = Column(Integer, default=2000, nullable=False)
    temperature = Column(Float, default=0.7, nullable=False)
    message_count = Column(Integer, default=0, nullable=False)
    is_archived = Column(Boolean, default=False, nullable=False)
    is_pinned = Column(Boolean, default=False, nullable=False)
    last_message_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    messages = relationship("ChatMessage", back_populates="chat", cascade="all, delete-orphan")
    user = relationship("User", back_populates="chats")
    
    def __repr__(self):
        return f"<Chat(id={self.id}, title='{self.title}', user_id={self.user_id})>"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert chat to dictionary"""
        return {
            "id": str(self.id),
            "user_id": str(self.user_id),
            "title": self.title,
            "description": self.description,
            "context": self.context,
            "language": self.language,
            "model_preference": self.model_preference,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
            "message_count": self.message_count,
            "is_archived": self.is_archived,
            "is_pinned": self.is_pinned,
            "last_message_at": self.last_message_at.isoformat() if self.last_message_at else None,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }


class ChatMessage(Base):
    """Chat message domain model"""
    
    __tablename__ = "chat_messages"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    chat_id = Column(UUID(as_uuid=True), ForeignKey("chats.id"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    message = Column(Text, nullable=False)
    message_type = Column(String(20), default="text", nullable=False)
    attachments = Column(JSON, nullable=True)  # List of attachment URLs or file IDs
    context = Column(Text, nullable=True)
    language = Column(String(10), default="auto", nullable=False)
    priority = Column(String(20), default="normal", nullable=False)
    is_ai_response = Column(Boolean, default=False, nullable=False)
    ai_model_used = Column(String(50), nullable=True)
    processing_time_ms = Column(Integer, nullable=True)
    confidence_score = Column(Float, nullable=True)
    feedback_rating = Column(Integer, nullable=True)
    feedback_comment = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    chat = relationship("Chat", back_populates="messages")
    user = relationship("User", back_populates="chat_messages")
    
    def __repr__(self):
        return f"<ChatMessage(id={self.id}, chat_id={self.chat_id}, is_ai={self.is_ai_response})>"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert chat message to dictionary"""
        return {
            "id": str(self.id),
            "chat_id": str(self.chat_id),
            "user_id": str(self.user_id),
            "message": self.message,
            "message_type": self.message_type,
            "attachments": self.attachments,
            "context": self.context,
            "language": self.language,
            "priority": self.priority,
            "is_ai_response": self.is_ai_response,
            "ai_model_used": self.ai_model_used,
            "processing_time_ms": self.processing_time_ms,
            "confidence_score": self.confidence_score,
            "feedback_rating": self.feedback_rating,
            "feedback_comment": self.feedback_comment,
            "created_at": self.created_at.isoformat()
        }


class ChatFeedback(Base):
    """Chat feedback domain model for user feedback on AI responses"""
    
    __tablename__ = "chat_feedbacks"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    message_id = Column(UUID(as_uuid=True), ForeignKey("chat_messages.id"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    rating = Column(Integer, nullable=False)  # 1-5 scale
    feedback_type = Column(String(50), nullable=False)
    comment = Column(Text, nullable=True)
    category = Column(String(50), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    message = relationship("ChatMessage")
    user = relationship("User")
    
    def __repr__(self):
        return f"<ChatFeedback(id={self.id}, message_id={self.message_id}, rating={self.rating})>"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert chat feedback to dictionary"""
        return {
            "id": str(self.id),
            "message_id": str(self.message_id),
            "user_id": str(self.user_id),
            "rating": self.rating,
            "feedback_type": self.feedback_type,
            "comment": self.comment,
            "category": self.category,
            "created_at": self.created_at.isoformat()
        }


class ChatSettings(Base):
    """Chat settings domain model for user preferences"""
    
    __tablename__ = "chat_settings"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, unique=True)
    default_language = Column(String(10), default="auto", nullable=False)
    default_model = Column(String(50), default="gemini-1.5-flash", nullable=False)
    default_max_tokens = Column(Integer, default=2000, nullable=False)
    default_temperature = Column(Float, default=0.7, nullable=False)
    auto_archive_after_days = Column(Integer, default=30, nullable=False)
    max_chats_per_user = Column(Integer, default=100, nullable=False)
    max_messages_per_chat = Column(Integer, default=1000, nullable=False)
    enable_voice_input = Column(Boolean, default=True, nullable=False)
    enable_file_upload = Column(Boolean, default=True, nullable=False)
    enable_image_analysis = Column(Boolean, default=True, nullable=False)
    enable_context_memory = Column(Boolean, default=True, nullable=False)
    enable_chat_history = Column(Boolean, default=True, nullable=False)
    enable_analytics = Column(Boolean, default=True, nullable=False)
    enable_feedback = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="chat_settings")
    
    def __repr__(self):
        return f"<ChatSettings(user_id={self.user_id}, default_model='{self.default_model}')>"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert chat settings to dictionary"""
        return {
            "id": str(self.id),
            "user_id": str(self.user_id),
            "default_language": self.default_language,
            "default_model": self.default_model,
            "default_max_tokens": self.default_max_tokens,
            "default_temperature": self.default_temperature,
            "auto_archive_after_days": self.auto_archive_after_days,
            "max_chats_per_user": self.max_chats_per_user,
            "max_messages_per_chat": self.max_messages_per_chat,
            "enable_voice_input": self.enable_voice_input,
            "enable_file_upload": self.enable_file_upload,
            "enable_image_analysis": self.enable_image_analysis,
            "enable_context_memory": self.enable_context_memory,
            "enable_chat_history": self.enable_chat_history,
            "enable_analytics": self.enable_analytics,
            "enable_feedback": self.enable_feedback,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }

