import uuid
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from models.domain.qa_pair import QAPair
import logging
from config.logging_config import get_logger

logger = get_logger(__name__)

class QAPairRepository:
    """
    Repository for Q&A pair operations.
    Handles CRUD operations for the intelligent Q&A system.
    """
    
    def create_qa_pair(
        self,
        db: Session,
        question_text: str,
        answer_text: str,
        user_id: Optional[uuid.UUID] = None,
        confidence: float = 0.8,
        source: str = "gemini_api",
        language: str = "auto",
        metadata: Optional[Dict[str, Any]] = None
    ) -> QAPair:
        """
        Create a new Q&A pair.
        
        Args:
            db: Database session
            question_text: The question text
            answer_text: The answer text
            user_id: Optional user ID
            confidence: Confidence score (0.0 to 1.0)
            source: Source of the answer (gemini_api, vector_search, etc.)
            language: Language of the Q&A
            metadata: Additional metadata
            
        Returns:
            Created QAPair instance
        """
        try:
            qa_pair = QAPair(
                question_text=question_text,
                answer_text=answer_text,
                user_id=user_id,
                confidence=confidence,
                source=source,
                language=language,
                qa_metadata=metadata or {}
            )
            
            db.add(qa_pair)
            db.commit()
            db.refresh(qa_pair)
            
            logger.debug(f"Created Q&A pair with ID: {qa_pair.id}")
            return qa_pair
            
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to create Q&A pair: {e}")
            raise
    
    def get_qa_pair_by_id(self, db: Session, qa_id: uuid.UUID) -> Optional[QAPair]:
        """
        Get Q&A pair by ID.
        
        Args:
            db: Database session
            qa_id: Q&A pair ID
            
        Returns:
            QAPair instance or None
        """
        try:
            return db.query(QAPair).filter(QAPair.id == qa_id).first()
        except Exception as e:
            logger.error(f"Failed to get Q&A pair by ID {qa_id}: {e}")
            return None
    
    def get_qa_pair_by_question_id(self, db: Session, question_id: str) -> Optional[QAPair]:
        """
        Get Q&A pair by question ID (for Qdrant integration).
        
        Args:
            db: Database session
            question_id: Question ID from Qdrant
            
        Returns:
            QAPair instance or None
        """
        try:
            # Search in metadata for qa_id
            return db.query(QAPair).filter(
                QAPair.qa_metadata.contains({"qa_id": question_id})
            ).first()
        except Exception as e:
            logger.error(f"Failed to get Q&A pair by question ID {question_id}: {e}")
            return None
    
    def find_similar_questions(
        self,
        db: Session,
        question_text: str,
        limit: int = 5,
        user_id: Optional[uuid.UUID] = None
    ) -> List[QAPair]:
        """
        Find similar questions using text similarity.
        
        Args:
            db: Database session
            question_text: Question to find similar ones for
            limit: Maximum number of results
            user_id: Optional user ID filter
            
        Returns:
            List of similar QAPair instances
        """
        try:
            query = db.query(QAPair)
            
            # Add user filter if provided
            if user_id:
                query = query.filter(QAPair.user_id == user_id)
            
            # Simple text similarity (can be enhanced with full-text search)
            # For now, we'll use a simple LIKE query
            similar_qa_pairs = query.filter(
                or_(
                    QAPair.question_text.ilike(f"%{question_text}%"),
                    QAPair.question_text.ilike(f"%{question_text[:20]}%")
                )
            ).limit(limit).all()
            
            logger.debug(f"Found {len(similar_qa_pairs)} similar questions")
            return similar_qa_pairs
            
        except Exception as e:
            logger.error(f"Failed to find similar questions: {e}")
            return []
    
    def get_recent_qa_pairs(
        self,
        db: Session,
        limit: int = 10,
        user_id: Optional[uuid.UUID] = None
    ) -> List[QAPair]:
        """
        Get recent Q&A pairs.
        
        Args:
            db: Database session
            limit: Maximum number of results
            user_id: Optional user ID filter
            
        Returns:
            List of recent QAPair instances
        """
        try:
            query = db.query(QAPair).order_by(QAPair.created_at.desc())
            
            if user_id:
                query = query.filter(QAPair.user_id == user_id)
            
            return query.limit(limit).all()
            
        except Exception as e:
            logger.error(f"Failed to get recent Q&A pairs: {e}")
            return []
    
    def update_qa_pair(
        self,
        db: Session,
        qa_id: uuid.UUID,
        **kwargs
    ) -> Optional[QAPair]:
        """
        Update Q&A pair.
        
        Args:
            db: Database session
            qa_id: Q&A pair ID
            **kwargs: Fields to update
            
        Returns:
            Updated QAPair instance or None
        """
        try:
            qa_pair = self.get_qa_pair_by_id(db, qa_id)
            if not qa_pair:
                return None
            
            # Update fields
            for key, value in kwargs.items():
                if hasattr(qa_pair, key):
                    setattr(qa_pair, key, value)
            
            db.commit()
            db.refresh(qa_pair)
            
            logger.debug(f"Updated Q&A pair with ID: {qa_id}")
            return qa_pair
            
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to update Q&A pair {qa_id}: {e}")
            return None
    
    def delete_qa_pair(self, db: Session, qa_id: uuid.UUID) -> bool:
        """
        Delete Q&A pair.
        
        Args:
            db: Database session
            qa_id: Q&A pair ID
            
        Returns:
            Success status
        """
        try:
            qa_pair = self.get_qa_pair_by_id(db, qa_id)
            if not qa_pair:
                return False
            
            db.delete(qa_pair)
            db.commit()
            
            logger.debug(f"Deleted Q&A pair with ID: {qa_id}")
            return True
            
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to delete Q&A pair {qa_id}: {e}")
            return False
    
    def get_qa_pairs_by_source(
        self,
        db: Session,
        source: str,
        limit: int = 50
    ) -> List[QAPair]:
        """
        Get Q&A pairs by source.
        
        Args:
            db: Database session
            source: Source filter (gemini_api, vector_search, etc.)
            limit: Maximum number of results
            
        Returns:
            List of QAPair instances
        """
        try:
            return db.query(QAPair).filter(
                QAPair.source == source
            ).order_by(QAPair.created_at.desc()).limit(limit).all()
            
        except Exception as e:
            logger.error(f"Failed to get Q&A pairs by source {source}: {e}")
            return []
    
    def get_qa_pairs_by_language(
        self,
        db: Session,
        language: str,
        limit: int = 50
    ) -> List[QAPair]:
        """
        Get Q&A pairs by language.
        
        Args:
            db: Database session
            language: Language filter
            limit: Maximum number of results
            
        Returns:
            List of QAPair instances
        """
        try:
            return db.query(QAPair).filter(
                QAPair.language == language
            ).order_by(QAPair.created_at.desc()).limit(limit).all()
            
        except Exception as e:
            logger.error(f"Failed to get Q&A pairs by language {language}: {e}")
            return []
    
    def get_qa_pairs_by_confidence_range(
        self,
        db: Session,
        min_confidence: float = 0.0,
        max_confidence: float = 1.0,
        limit: int = 50
    ) -> List[QAPair]:
        """
        Get Q&A pairs by confidence range.
        
        Args:
            db: Database session
            min_confidence: Minimum confidence score
            max_confidence: Maximum confidence score
            limit: Maximum number of results
            
        Returns:
            List of QAPair instances
        """
        try:
            return db.query(QAPair).filter(
                and_(
                    QAPair.confidence >= min_confidence,
                    QAPair.confidence <= max_confidence
                )
            ).order_by(QAPair.confidence.desc()).limit(limit).all()
            
        except Exception as e:
            logger.error(f"Failed to get Q&A pairs by confidence range: {e}")
            return []
    
    def get_statistics(self, db: Session) -> Dict[str, Any]:
        """
        Get Q&A pairs statistics.
        
        Args:
            db: Database session
            
        Returns:
            Dictionary with statistics
        """
        try:
            total_count = db.query(QAPair).count()
            
            # Count by source
            source_counts = {}
            sources = db.query(QAPair.source).distinct().all()
            for source in sources:
                count = db.query(QAPair).filter(QAPair.source == source[0]).count()
                source_counts[source[0]] = count
            
            # Count by language
            language_counts = {}
            languages = db.query(QAPair.language).distinct().all()
            for language in languages:
                count = db.query(QAPair).filter(QAPair.language == language[0]).count()
                language_counts[language[0]] = count
            
            # Average confidence
            avg_confidence = db.query(QAPair.confidence).all()
            avg_confidence = sum([c[0] for c in avg_confidence]) / len(avg_confidence) if avg_confidence else 0
            
            return {
                "total_count": total_count,
                "source_counts": source_counts,
                "language_counts": language_counts,
                "average_confidence": round(avg_confidence, 3)
            }
            
        except Exception as e:
            logger.error(f"Failed to get Q&A pairs statistics: {e}")
            return {}

# Global repository instance
qa_pair_repository = QAPairRepository()
