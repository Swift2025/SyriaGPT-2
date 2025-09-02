import logging
import time
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
import uuid
import json

from services.repositories.chat_repository import ChatRepository
from services.ai.intelligent_qa_service import intelligent_qa_service
from services.ai.gemini_service import gemini_service
from services.ai.embedding_service import embedding_service
from services.database.database import get_db
from config.logging_config import get_logger, log_function_entry, log_function_exit, log_performance, log_error_with_context

logger = get_logger(__name__)


class ChatManagementService:
    """Service for managing AI chat operations"""
    
    def __init__(self):
        pass
    
    async def create_chat(self, user_id: str, **kwargs) -> Dict[str, Any]:
        """Create a new chat"""
        start_time = time.time()
        try:
            db = next(get_db())
            chat_repository = ChatRepository(db)
            
            # Get user's default chat settings
            settings = chat_repository.get_or_create_chat_settings(user_id)
            
            # Merge with provided kwargs
            chat_data = {
                "language": settings.default_language,
                "model_preference": settings.default_model,
                "max_tokens": settings.default_max_tokens,
                "temperature": settings.default_temperature,
                **kwargs
            }
            
            chat = chat_repository.create_chat(user_id, **chat_data)
            
            response = {
                "status": "success",
                "message": "Chat created successfully",
                "data": {
                    "chat": chat.to_dict(),
                    "settings": settings.to_dict()
                }
            }
            
            duration = time.time() - start_time
            log_performance(logger, "create_chat", duration)
            log_function_exit(logger, "create_chat", duration=duration)
            return response
        except Exception as e:
            duration = time.time() - start_time
            log_error_with_context(logger, e, "create_chat", duration=duration)
            logger.error(f"❌ Error creating chat: {e}")
            log_function_exit(logger, "create_chat", duration=duration)
            raise
    
    async def send_message(self, chat_id: str, user_id: str, message: str, **kwargs) -> Dict[str, Any]:
        """Send a message and get AI response"""
        start_time = time.time()
        try:
            db = next(get_db())
            chat_repository = ChatRepository(db)
            
            # Get chat and settings
            chat = chat_repository.get_chat_by_id(chat_id, user_id)
            if not chat:
                raise ValueError("Chat not found")
            
            settings = chat_repository.get_or_create_chat_settings(user_id)
            
            # Create user message
            user_message = chat_repository.create_message(
                chat_id=chat_id,
                user_id=user_id,
                message=message,
                is_ai_response=False,
                **kwargs
            )
            
            # Get chat context (recent messages)
            recent_messages = chat_repository.get_chat_messages(chat_id, user_id, limit=10)
            context_messages = []
            
            for msg in recent_messages[-5:]:  # Last 5 messages for context
                context_messages.append({
                    "role": "ai" if msg.is_ai_response else "user",
                    "content": msg.message
                })
            
            # Prepare context for AI
            context = {
                "chat_title": chat.title,
                "chat_description": chat.description,
                "chat_context": chat.context,
                "language": chat.language,
                "model_preference": chat.model_preference,
                "max_tokens": chat.max_tokens,
                "temperature": chat.temperature,
                "recent_messages": context_messages,
                "user_settings": settings.to_dict()
            }
            
            # Get AI response using intelligent QA service
            ai_response_start = time.time()
            try:
                ai_response = await intelligent_qa_service.process_question(
                    question=message,
                    context=json.dumps(context),
                    language=chat.language,
                    model_preference=chat.model_preference,
                    max_tokens=chat.max_tokens,
                    temperature=chat.temperature
                )
                ai_processing_time = int((time.time() - ai_response_start) * 1000)
            except Exception as e:
                logger.warning(f"⚠️ Intelligent QA service failed: {e}")
                # Fallback response when AI service is unavailable
                ai_response = {
                    "answer": f"عذراً، خدمة الذكاء الاصطناعي غير متاحة حالياً. يرجى المحاولة لاحقاً. (Error: {str(e)})",
                    "model_used": "fallback",
                    "confidence": 0.0,
                    "source": "fallback",
                    "status": "error"
                }
                ai_processing_time = int((time.time() - ai_response_start) * 1000)
            
            # Create AI message
            ai_message = chat_repository.create_message(
                chat_id=chat_id,
                user_id=user_id,
                message=ai_response.get("answer", "Sorry, I couldn't generate a response."),
                is_ai_response=True,
                ai_model_used=ai_response.get("model_used", chat.model_preference),
                processing_time_ms=ai_processing_time,
                confidence_score=ai_response.get("confidence", 0.0),
                message_type=kwargs.get("message_type", "text")
            )
            
            response = {
                "status": "success",
                "message": "Message sent and AI response generated",
                "data": {
                    "user_message": user_message.to_dict(),
                    "ai_response": ai_message.to_dict(),
                    "processing_time_ms": ai_processing_time,
                    "confidence_score": ai_response.get("confidence", 0.0),
                    "model_used": ai_response.get("model_used", chat.model_preference)
                }
            }
            
            duration = time.time() - start_time
            log_performance(logger, "send_message", duration)
            log_function_exit(logger, "send_message", duration=duration)
            return response
        except Exception as e:
            duration = time.time() - start_time
            log_error_with_context(logger, e, "send_message", duration=duration)
            logger.error(f"❌ Error sending message: {e}")
            log_function_exit(logger, "send_message", duration=duration)
            raise
    
    async def get_chat(self, chat_id: str, user_id: str, include_messages: bool = True) -> Dict[str, Any]:
        """Get chat details"""
        start_time = time.time()
        try:
            db = next(get_db())
            chat_repository = ChatRepository(db)
            
            if include_messages:
                chat = chat_repository.get_chat_with_messages(chat_id, user_id)
            else:
                chat = chat_repository.get_chat_by_id(chat_id, user_id)
            
            if not chat:
                raise ValueError("Chat not found")
            
            response = {
                "status": "success",
                "message": "Chat retrieved successfully",
                "data": {
                    "chat": chat.to_dict(),
                    "messages": [msg.to_dict() for msg in chat.messages] if include_messages else []
                }
            }
            
            duration = time.time() - start_time
            log_performance(logger, "get_chat", duration)
            log_function_exit(logger, "get_chat", duration=duration)
            return response
        except Exception as e:
            duration = time.time() - start_time
            log_error_with_context(logger, e, "get_chat", duration=duration)
            logger.error(f"❌ Error getting chat: {e}")
            log_function_exit(logger, "get_chat", duration=duration)
            raise
    
    async def update_chat(self, chat_id: str, user_id: str, **kwargs) -> Dict[str, Any]:
        """Update chat"""
        start_time = time.time()
        try:
            db = next(get_db())
            chat_repository = ChatRepository(db)
            
            chat = chat_repository.update_chat(chat_id, user_id, **kwargs)
            
            if not chat:
                raise ValueError("Chat not found")
            
            response = {
                "status": "success",
                "message": "Chat updated successfully",
                "data": {
                    "chat": chat.to_dict()
                }
            }
            
            duration = time.time() - start_time
            log_performance(logger, "update_chat", duration)
            log_function_exit(logger, "update_chat", duration=duration)
            return response
        except Exception as e:
            duration = time.time() - start_time
            log_error_with_context(logger, e, "update_chat", duration=duration)
            logger.error(f"❌ Error updating chat: {e}")
            log_function_exit(logger, "update_chat", duration=duration)
            raise
    
    async def delete_chat(self, chat_id: str, user_id: str) -> Dict[str, Any]:
        """Delete chat"""
        start_time = time.time()
        try:
            db = next(get_db())
            chat_repository = ChatRepository(db)
            
            success = chat_repository.delete_chat(chat_id, user_id)
            
            if not success:
                raise ValueError("Chat not found")
            
            response = {
                "status": "success",
                "message": "Chat deleted successfully"
            }
            
            duration = time.time() - start_time
            log_performance(logger, "delete_chat", duration)
            log_function_exit(logger, "delete_chat", duration=duration)
            return response
        except Exception as e:
            duration = time.time() - start_time
            log_error_with_context(logger, e, "delete_chat", duration=duration)
            logger.error(f"❌ Error deleting chat: {e}")
            log_function_exit(logger, "delete_chat", duration=duration)
            raise
    
    async def search_chats(self, user_id: str, **filters) -> Dict[str, Any]:
        """Search chats"""
        start_time = time.time()
        try:
            db = next(get_db())
            chat_repository = ChatRepository(db)
            
            chats, total_count = chat_repository.search_chats(user_id, **filters)
            
            response = {
                "status": "success",
                "message": "Chats retrieved successfully",
                "data": {
                    "chats": [chat.to_dict() for chat in chats],
                    "total_count": total_count,
                    "page": filters.get("page", 1),
                    "page_size": filters.get("page_size", 10),
                    "total_pages": (total_count + filters.get("page_size", 10) - 1) // filters.get("page_size", 10)
                }
            }
            
            duration = time.time() - start_time
            log_performance(logger, "search_chats", duration)
            log_function_exit(logger, "search_chats", duration=duration)
            return response
        except Exception as e:
            duration = time.time() - start_time
            log_error_with_context(logger, e, "search_chats", duration=duration)
            logger.error(f"❌ Error searching chats: {e}")
            log_function_exit(logger, "search_chats", duration=duration)
            raise
    
    async def add_feedback(self, message_id: str, user_id: str, **kwargs) -> Dict[str, Any]:
        """Add feedback to a message"""
        start_time = time.time()
        try:
            db = next(get_db())
            chat_repository = ChatRepository(db)
            
            feedback = chat_repository.create_feedback(message_id, user_id, **kwargs)
            
            response = {
                "status": "success",
                "message": "Feedback added successfully",
                "data": {
                    "feedback": feedback.to_dict()
                }
            }
            
            duration = time.time() - start_time
            log_performance(logger, "add_feedback", duration)
            log_function_exit(logger, "add_feedback", duration=duration)
            return response
        except Exception as e:
            duration = time.time() - start_time
            log_error_with_context(logger, e, "add_feedback", duration=duration)
            logger.error(f"❌ Error adding feedback: {e}")
            log_function_exit(logger, "add_feedback", duration=duration)
            raise
    
    async def get_chat_settings(self, user_id: str) -> Dict[str, Any]:
        """Get user's chat settings"""
        start_time = time.time()
        try:
            db = next(get_db())
            chat_repository = ChatRepository(db)
            
            settings = chat_repository.get_or_create_chat_settings(user_id)
            
            response = {
                "status": "success",
                "message": "Chat settings retrieved successfully",
                "data": {
                    "settings": settings.to_dict()
                }
            }
            
            duration = time.time() - start_time
            log_performance(logger, "get_chat_settings", duration)
            log_function_exit(logger, "get_chat_settings", duration=duration)
            return response
        except Exception as e:
            duration = time.time() - start_time
            log_error_with_context(logger, e, "get_chat_settings", duration=duration)
            logger.error(f"❌ Error getting chat settings: {e}")
            log_function_exit(logger, "get_chat_settings", duration=duration)
            raise
    
    async def update_chat_settings(self, user_id: str, **kwargs) -> Dict[str, Any]:
        """Update user's chat settings"""
        start_time = time.time()
        try:
            db = next(get_db())
            chat_repository = ChatRepository(db)
            
            settings = chat_repository.update_chat_settings(user_id, **kwargs)
            
            response = {
                "status": "success",
                "message": "Chat settings updated successfully",
                "data": {
                    "settings": settings.to_dict()
                }
            }
            
            duration = time.time() - start_time
            log_performance(logger, "update_chat_settings", duration)
            log_function_exit(logger, "update_chat_settings", duration=duration)
            return response
        except Exception as e:
            duration = time.time() - start_time
            log_error_with_context(logger, e, "update_chat_settings", duration=duration)
            logger.error(f"❌ Error updating chat settings: {e}")
            log_function_exit(logger, "update_chat_settings", duration=duration)
            raise
    
    async def get_chat_analytics(self, user_id: str, **kwargs) -> Dict[str, Any]:
        """Get chat analytics"""
        start_time = time.time()
        try:
            db = next(get_db())
            chat_repository = ChatRepository(db)
            
            analytics = chat_repository.get_chat_analytics(
                user_id,
                date_range_start=kwargs.get("date_range_start"),
                date_range_end=kwargs.get("date_range_end")
            )
            
            response = {
                "status": "success",
                "message": "Chat analytics retrieved successfully",
                "data": {
                    "analytics": analytics
                }
            }
            
            duration = time.time() - start_time
            log_performance(logger, "get_chat_analytics", duration)
            log_function_exit(logger, "get_chat_analytics", duration=duration)
            return response
        except Exception as e:
            duration = time.time() - start_time
            log_error_with_context(logger, e, "get_chat_analytics", duration=duration)
            logger.error(f"❌ Error getting chat analytics: {e}")
            log_function_exit(logger, "get_chat_analytics", duration=duration)
            raise
    
    async def bulk_action_chats(self, user_id: str, chat_ids: List[str], action: str) -> Dict[str, Any]:
        """Perform bulk action on chats"""
        start_time = time.time()
        try:
            db = next(get_db())
            chat_repository = ChatRepository(db)
            
            result = chat_repository.bulk_action_chats(user_id, chat_ids, action)
            
            response = {
                "status": "success",
                "message": f"Bulk action '{action}' completed",
                "data": {
                    "success_count": result["success_count"],
                    "failed_count": result["failed_count"]
                }
            }
            
            duration = time.time() - start_time
            log_performance(logger, "bulk_action_chats", duration)
            log_function_exit(logger, "bulk_action_chats", duration=duration)
            return response
        except Exception as e:
            duration = time.time() - start_time
            log_error_with_context(logger, e, "bulk_action_chats", duration=duration)
            logger.error(f"❌ Error performing bulk action on chats: {e}")
            log_function_exit(logger, "bulk_action_chats", duration=duration)
            raise
    
    async def export_chat(self, chat_id: str, user_id: str, format: str = "json") -> Dict[str, Any]:
        """Export chat data"""
        start_time = time.time()
        try:
            db = next(get_db())
            chat_repository = ChatRepository(db)
            
            chat = chat_repository.get_chat_with_messages(chat_id, user_id)
            if not chat:
                raise ValueError("Chat not found")
            
            # Generate export data
            export_data = {
                "chat": chat.to_dict(),
                "messages": [msg.to_dict() for msg in chat.messages],
                "export_info": {
                    "exported_at": datetime.now(datetime.UTC).isoformat(),
                    "format": format,
                    "total_messages": len(chat.messages)
                }
            }
            
            # For now, return the data as JSON
            # In a real implementation, you would save to file and return download URL
            response = {
                "status": "success",
                "message": "Chat exported successfully",
                "data": {
                    "export_id": str(uuid.uuid4()),
                    "format": format,
                    "data": export_data,
                    "expires_at": (datetime.now(datetime.UTC) + timedelta(hours=24)).isoformat()
                }
            }
            
            duration = time.time() - start_time
            log_performance(logger, "export_chat", duration)
            log_function_exit(logger, "export_chat", duration=duration)
            return response
        except Exception as e:
            duration = time.time() - start_time
            log_error_with_context(logger, e, "export_chat", duration=duration)
            logger.error(f"❌ Error exporting chat: {e}")
            log_function_exit(logger, "export_chat", duration=duration)
            raise


# Global chat management service instance
chat_management_service = ChatManagementService()
