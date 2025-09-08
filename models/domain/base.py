"""
Base model class for all database models.
"""

from datetime import datetime
from typing import Any
from sqlalchemy import Column, DateTime, String, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.dialects.postgresql import UUID
import uuid

Base = declarative_base()


class TimestampMixin:
    """Mixin class to add timestamp fields to models."""
    
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
        server_default=text('CURRENT_TIMESTAMP')
    )
    
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        server_default=text('CURRENT_TIMESTAMP')
    )


class UUIDMixin:
    """Mixin class to add UUID primary key to models."""
    
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        nullable=False
    )


class SoftDeleteMixin:
    """Mixin class to add soft delete functionality to models."""
    
    deleted_at = Column(
        DateTime(timezone=True),
        nullable=True,
        default=None
    )
    
    is_deleted = Column(
        String(1),
        nullable=False,
        default='N',
        server_default='N'
    )
    
    def soft_delete(self):
        """Mark the record as deleted."""
        self.deleted_at = datetime.utcnow()
        self.is_deleted = 'Y'
    
    def restore(self):
        """Restore a soft-deleted record."""
        self.deleted_at = None
        self.is_deleted = 'N'


class BaseModel(Base, UUIDMixin, TimestampMixin, SoftDeleteMixin):
    """Base model class with common fields and functionality."""
    
    __abstract__ = True
    
    def to_dict(self) -> dict[str, Any]:
        """Convert model instance to dictionary."""
        return {
            column.name: getattr(self, column.name)
            for column in self.__table__.columns
        }
    
    def update_from_dict(self, data: dict[str, Any]) -> None:
        """Update model instance from dictionary."""
        for key, value in data.items():
            if hasattr(self, key):
                setattr(self, key, value)
    
    def __repr__(self) -> str:
        """String representation of the model."""
        return f"<{self.__class__.__name__}(id={self.id})>"
