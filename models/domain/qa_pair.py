import uuid
from sqlalchemy import Column, String, DateTime, Float, Text, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from .base import Base

class QAPair(Base):
    """
    Q&A Pair model for storing question-answer pairs with metadata.
    This replaces the separate Question and Answer models for the intelligent Q&A system.
    """
    __tablename__ = "qa_pairs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    question_text = Column(Text, nullable=False)
    answer_text = Column(Text, nullable=False)
    user_id = Column(UUID(as_uuid=True), nullable=True)  # Optional, for user-specific Q&A
    confidence = Column(Float, default=0.8)
    source = Column(String(50), default="gemini_api")  # gemini_api, vector_search, etc.
    language = Column(String(10), default="auto")
    qa_metadata = Column(JSON, nullable=True)  # Store additional metadata as JSON
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    def __repr__(self):
        return f"<QAPair(id={self.id}, question={self.question_text[:50]}..., source={self.source})>"
