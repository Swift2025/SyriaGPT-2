import logging
import time
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_, func, desc, asc
from sqlalchemy.exc import SQLAlchemyError
import uuid

from models.domain.chat import Chat, ChatMessage, ChatFeedback, ChatSettings
from models.domain.user import User
from config.logging_config import get_logger, log_function_entry, log_function_exit, log_performance, log_error_with_context

logger = get_logger(__name__)


class ChatRepository:
    """Repository for chat-related database operations"""
    
    def __init__(self, db_session: Session):
        self.db = db_session
    
    def create_chat(self, user_id: str, **kwargs) -> Chat:
        """Create a new chat"""
        start_time = time.time()
        try:
            chat = Chat(
                user_id=uuid.UUID(user_id),
                **kwargs
            )
            self.db.add(chat)
            self.db.commit()
            self.db.refresh(chat)
            
            duration = time.time() - start_time
            log_performance(logger, "create_chat", duration)
            log_function_exit(logger, "create_chat", duration=duration)
            return chat
        except Exception as e:
            self.db.rollback()
            duration = time.time() - start_time
            log_error_with_context(logger, e, "create_chat", duration=duration)
            logger.error(f"❌ Error creating chat: {e}")
            log_function_exit(logger, "create_chat", duration=duration)
            raise
    
    def get_chat_by_id(self, chat_id: str, user_id: str) -> Optional[Chat]:
        """Get chat by ID for specific user"""
        start_time = time.time()
        try:
            chat = self.db.query(Chat).filter(
                and_(
                    Chat.id == uuid.UUID(chat_id),
                    Chat.user_id == uuid.UUID(user_id)
                )
            ).first()
            
            duration = time.time() - start_time
            log_performance(logger, "get_chat_by_id", duration)
            log_function_exit(logger, "get_chat_by_id", duration=duration)
            return chat
        except Exception as e:
            duration = time.time() - start_time
            log_error_with_context(logger, e, "get_chat_by_id", duration=duration)
            logger.error(f"❌ Error getting chat by ID: {e}")
            log_function_exit(logger, "get_chat_by_id", duration=duration)
            raise
    
    def get_chat_with_messages(self, chat_id: str, user_id: str, limit: int = 100) -> Optional[Chat]:
        """Get chat with messages"""
        start_time = time.time()
        try:
            chat = self.db.query(Chat).options(
                joinedload(Chat.messages).joinedload(ChatMessage.user)
            ).filter(
                and_(
                    Chat.id == uuid.UUID(chat_id),
                    Chat.user_id == uuid.UUID(user_id)
                )
            ).first()
            
            if chat:
                # Limit messages to most recent
                chat.messages = sorted(chat.messages, key=lambda x: x.created_at, reverse=True)[:limit]
            
            duration = time.time() - start_time
            log_performance(logger, "get_chat_with_messages", duration)
            log_function_exit(logger, "get_chat_with_messages", duration=duration)
            return chat
        except Exception as e:
            duration = time.time() - start_time
            log_error_with_context(logger, e, "get_chat_with_messages", duration=duration)
            logger.error(f"❌ Error getting chat with messages: {e}")
            log_function_exit(logger, "get_chat_with_messages", duration=duration)
            raise
    
    def update_chat(self, chat_id: str, user_id: str, **kwargs) -> Optional[Chat]:
        """Update chat"""
        start_time = time.time()
        try:
            chat = self.get_chat_by_id(chat_id, user_id)
            if not chat:
                return None
            
            for key, value in kwargs.items():
                if hasattr(chat, key):
                    setattr(chat, key, value)
            
            chat.updated_at = datetime.utcnow()
            self.db.commit()
            self.db.refresh(chat)
            
            duration = time.time() - start_time
            log_performance(logger, "update_chat", duration)
            log_function_exit(logger, "update_chat", duration=duration)
            return chat
        except Exception as e:
            self.db.rollback()
            duration = time.time() - start_time
            log_error_with_context(logger, e, "update_chat", duration=duration)
            logger.error(f"❌ Error updating chat: {e}")
            log_function_exit(logger, "update_chat", duration=duration)
            raise
    
    def delete_chat(self, chat_id: str, user_id: str) -> bool:
        """Delete chat"""
        start_time = time.time()
        try:
            chat = self.get_chat_by_id(chat_id, user_id)
            if not chat:
                return False
            
            self.db.delete(chat)
            self.db.commit()
            
            duration = time.time() - start_time
            log_performance(logger, "delete_chat", duration)
            log_function_exit(logger, "delete_chat", duration=duration)
            return True
        except Exception as e:
            self.db.rollback()
            duration = time.time() - start_time
            log_error_with_context(logger, e, "delete_chat", duration=duration)
            logger.error(f"❌ Error deleting chat: {e}")
            log_function_exit(logger, "delete_chat", duration=duration)
            raise
    
    def search_chats(self, user_id: str, **filters) -> Tuple[List[Chat], int]:
        """Search chats with filters"""
        start_time = time.time()
        try:
            query = self.db.query(Chat).filter(Chat.user_id == uuid.UUID(user_id))
            
            # Apply filters
            if filters.get('title'):
                query = query.filter(Chat.title.ilike(f"%{filters['title']}%"))
            
            if filters.get('language'):
                query = query.filter(Chat.language == filters['language'])
            
            if filters.get('model_preference'):
                query = query.filter(Chat.model_preference == filters['model_preference'])
            
            if filters.get('is_archived') is not None:
                query = query.filter(Chat.is_archived == filters['is_archived'])
            
            if filters.get('is_pinned') is not None:
                query = query.filter(Chat.is_pinned == filters['is_pinned'])
            
            if filters.get('created_after'):
                query = query.filter(Chat.created_at >= filters['created_after'])
            
            if filters.get('created_before'):
                query = query.filter(Chat.created_at <= filters['created_before'])
            
            if filters.get('updated_after'):
                query = query.filter(Chat.updated_at >= filters['updated_after'])
            
            if filters.get('updated_before'):
                query = query.filter(Chat.updated_at <= filters['updated_before'])
            
            if filters.get('message_count_min'):
                query = query.filter(Chat.message_count >= filters['message_count_min'])
            
            if filters.get('message_count_max'):
                query = query.filter(Chat.message_count <= filters['message_count_max'])
            
            # Get total count
            total_count = query.count()
            
            # Apply pagination
            page = filters.get('page', 1)
            page_size = filters.get('page_size', 10)
            offset = (page - 1) * page_size
            
            chats = query.order_by(desc(Chat.updated_at)).offset(offset).limit(page_size).all()
            
            duration = time.time() - start_time
            log_performance(logger, "search_chats", duration)
            log_function_exit(logger, "search_chats", duration=duration)
            return chats, total_count
        except Exception as e:
            duration = time.time() - start_time
            log_error_with_context(logger, e, "search_chats", duration=duration)
            logger.error(f"❌ Error searching chats: {e}")
            log_function_exit(logger, "search_chats", duration=duration)
            raise
    
    def create_message(self, chat_id: str, user_id: str, **kwargs) -> ChatMessage:
        """Create a new chat message"""
        start_time = time.time()
        try:
            message = ChatMessage(
                chat_id=uuid.UUID(chat_id),
                user_id=uuid.UUID(user_id),
                **kwargs
            )
            self.db.add(message)
            
            # Update chat message count and last message time
            chat = self.get_chat_by_id(chat_id, user_id)
            if chat:
                chat.message_count += 1
                chat.last_message_at = datetime.utcnow()
                chat.updated_at = datetime.utcnow()
            
            self.db.commit()
            self.db.refresh(message)
            
            duration = time.time() - start_time
            log_performance(logger, "create_message", duration)
            log_function_exit(logger, "create_message", duration=duration)
            return message
        except Exception as e:
            self.db.rollback()
            duration = time.time() - start_time
            log_error_with_context(logger, e, "create_message", duration=duration)
            logger.error(f"❌ Error creating message: {e}")
            log_function_exit(logger, "create_message", duration=duration)
            raise
    
    def get_message_by_id(self, message_id: str) -> Optional[ChatMessage]:
        """Get message by ID"""
        start_time = time.time()
        try:
            message = self.db.query(ChatMessage).filter(
                ChatMessage.id == uuid.UUID(message_id)
            ).first()
            
            duration = time.time() - start_time
            log_performance(logger, "get_message_by_id", duration)
            log_function_exit(logger, "get_message_by_id", duration=duration)
            return message
        except Exception as e:
            duration = time.time() - start_time
            log_error_with_context(logger, e, "get_message_by_id", duration=duration)
            logger.error(f"❌ Error getting message by ID: {e}")
            log_function_exit(logger, "get_message_by_id", duration=duration)
            raise
    
    def get_chat_messages(self, chat_id: str, user_id: str, limit: int = 100, offset: int = 0) -> List[ChatMessage]:
        """Get messages for a chat"""
        start_time = time.time()
        try:
            messages = self.db.query(ChatMessage).filter(
                and_(
                    ChatMessage.chat_id == uuid.UUID(chat_id),
                    ChatMessage.user_id == uuid.UUID(user_id)
                )
            ).order_by(desc(ChatMessage.created_at)).offset(offset).limit(limit).all()
            
            duration = time.time() - start_time
            log_performance(logger, "get_chat_messages", duration)
            log_function_exit(logger, "get_chat_messages", duration=duration)
            return messages
        except Exception as e:
            duration = time.time() - start_time
            log_error_with_context(logger, e, "get_chat_messages", duration=duration)
            logger.error(f"❌ Error getting chat messages: {e}")
            log_function_exit(logger, "get_chat_messages", duration=duration)
            raise
    
    def create_feedback(self, message_id: str, user_id: str, **kwargs) -> ChatFeedback:
        """Create feedback for a message"""
        start_time = time.time()
        try:
            feedback = ChatFeedback(
                message_id=uuid.UUID(message_id),
                user_id=uuid.UUID(user_id),
                **kwargs
            )
            self.db.add(feedback)
            
            # Update message with feedback
            message = self.get_message_by_id(message_id)
            if message:
                message.feedback_rating = kwargs.get('rating')
                message.feedback_comment = kwargs.get('comment')
            
            self.db.commit()
            self.db.refresh(feedback)
            
            duration = time.time() - start_time
            log_performance(logger, "create_feedback", duration)
            log_function_exit(logger, "create_feedback", duration=duration)
            return feedback
        except Exception as e:
            self.db.rollback()
            duration = time.time() - start_time
            log_error_with_context(logger, e, "create_feedback", duration=duration)
            logger.error(f"❌ Error creating feedback: {e}")
            log_function_exit(logger, "create_feedback", duration=duration)
            raise
    
    def get_or_create_chat_settings(self, user_id: str) -> ChatSettings:
        """Get or create chat settings for user"""
        start_time = time.time()
        try:
            settings = self.db.query(ChatSettings).filter(
                ChatSettings.user_id == uuid.UUID(user_id)
            ).first()
            
            if not settings:
                settings = ChatSettings(user_id=uuid.UUID(user_id))
                self.db.add(settings)
                self.db.commit()
                self.db.refresh(settings)
            
            duration = time.time() - start_time
            log_performance(logger, "get_or_create_chat_settings", duration)
            log_function_exit(logger, "get_or_create_chat_settings", duration=duration)
            return settings
        except Exception as e:
            self.db.rollback()
            duration = time.time() - start_time
            log_error_with_context(logger, e, "get_or_create_chat_settings", duration=duration)
            logger.error(f"❌ Error getting/creating chat settings: {e}")
            log_function_exit(logger, "get_or_create_chat_settings", duration=duration)
            raise
    
    def update_chat_settings(self, user_id: str, **kwargs) -> ChatSettings:
        """Update chat settings"""
        start_time = time.time()
        try:
            settings = self.get_or_create_chat_settings(user_id)
            
            for key, value in kwargs.items():
                if hasattr(settings, key):
                    setattr(settings, key, value)
            
            settings.updated_at = datetime.utcnow()
            self.db.commit()
            self.db.refresh(settings)
            
            duration = time.time() - start_time
            log_performance(logger, "update_chat_settings", duration)
            log_function_exit(logger, "update_chat_settings", duration=duration)
            return settings
        except Exception as e:
            self.db.rollback()
            duration = time.time() - start_time
            log_error_with_context(logger, e, "update_chat_settings", duration=duration)
            logger.error(f"❌ Error updating chat settings: {e}")
            log_function_exit(logger, "update_chat_settings", duration=duration)
            raise
    
    def get_chat_analytics(self, user_id: str, date_range_start: Optional[datetime] = None, 
                          date_range_end: Optional[datetime] = None) -> Dict[str, Any]:
        """Get chat analytics for user"""
        start_time = time.time()
        try:
            query = self.db.query(Chat).filter(Chat.user_id == uuid.UUID(user_id))
            message_query = self.db.query(ChatMessage).join(Chat).filter(Chat.user_id == uuid.UUID(user_id))
            
            if date_range_start:
                query = query.filter(Chat.created_at >= date_range_start)
                message_query = message_query.filter(ChatMessage.created_at >= date_range_start)
            
            if date_range_end:
                query = query.filter(Chat.created_at <= date_range_end)
                message_query = message_query.filter(ChatMessage.created_at <= date_range_end)
            
            total_chats = query.count()
            total_messages = message_query.count()
            ai_responses = message_query.filter(ChatMessage.is_ai_response == True).count()
            
            # Average response time
            avg_response_time = self.db.query(func.avg(ChatMessage.processing_time_ms)).filter(
                and_(
                    ChatMessage.is_ai_response == True,
                    ChatMessage.processing_time_ms.isnot(None)
                )
            ).scalar() or 0
            
            # Most used language
            most_used_language = self.db.query(Chat.language, func.count(Chat.id)).filter(
                Chat.user_id == uuid.UUID(user_id)
            ).group_by(Chat.language).order_by(desc(func.count(Chat.id))).first()
            
            # Most used model
            most_used_model = self.db.query(Chat.model_preference, func.count(Chat.id)).filter(
                Chat.user_id == uuid.UUID(user_id)
            ).group_by(Chat.model_preference).order_by(desc(func.count(Chat.id))).first()
            
            analytics = {
                "total_chats": total_chats,
                "total_messages": total_messages,
                "ai_responses": ai_responses,
                "average_response_time_ms": float(avg_response_time),
                "most_used_language": most_used_language[0] if most_used_language else "auto",
                "most_used_model": most_used_model[0] if most_used_model else "gemini-1.5-flash"
            }
            
            duration = time.time() - start_time
            log_performance(logger, "get_chat_analytics", duration)
            log_function_exit(logger, "get_chat_analytics", duration=duration)
            return analytics
        except Exception as e:
            duration = time.time() - start_time
            log_error_with_context(logger, e, "get_chat_analytics", duration=duration)
            logger.error(f"❌ Error getting chat analytics: {e}")
            log_function_exit(logger, "get_chat_analytics", duration=duration)
            raise
    
    def bulk_action_chats(self, user_id: str, chat_ids: List[str], action: str, **kwargs) -> Dict[str, int]:
        """Perform bulk action on chats"""
        start_time = time.time()
        try:
            success_count = 0
            failed_count = 0
            
            for chat_id in chat_ids:
                try:
                    if action == "archive":
                        self.update_chat(chat_id, user_id, is_archived=True)
                    elif action == "unarchive":
                        self.update_chat(chat_id, user_id, is_archived=False)
                    elif action == "pin":
                        self.update_chat(chat_id, user_id, is_pinned=True)
                    elif action == "unpin":
                        self.update_chat(chat_id, user_id, is_pinned=False)
                    elif action == "delete":
                        self.delete_chat(chat_id, user_id)
                    
                    success_count += 1
                except Exception as e:
                    logger.error(f"❌ Error performing {action} on chat {chat_id}: {e}")
                    failed_count += 1
            
            self.db.commit()
            
            duration = time.time() - start_time
            log_performance(logger, "bulk_action_chats", duration)
            log_function_exit(logger, "bulk_action_chats", duration=duration)
            return {"success_count": success_count, "failed_count": failed_count}
        except Exception as e:
            self.db.rollback()
            duration = time.time() - start_time
            log_error_with_context(logger, e, "bulk_action_chats", duration=duration)
            logger.error(f"❌ Error performing bulk action on chats: {e}")
            log_function_exit(logger, "bulk_action_chats", duration=duration)
            raise
