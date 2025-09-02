import uuid
from sqlalchemy import Column, String, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from .base import Base

class Answer(Base):
    __tablename__ = "answers"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    answer = Column(String(10000), nullable=False)
    question_id = Column(UUID(as_uuid=True), nullable=False)
    user_id = Column(UUID(as_uuid=True), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    author = Column(String(255), nullable=False)
    
    def __repr__(self):
        return f"<Answer(id={self.id}, answer={self.answer}, question_id={self.question_id}, user_id={self.user_id})>"
