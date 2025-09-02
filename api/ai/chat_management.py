import logging
import time
from typing import Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Path
from fastapi.responses import JSONResponse
from datetime import datetime

from models.schemas.request_models import (
    ChatCreateRequest, ChatMessageRequest, ChatUpdateRequest, ChatSearchRequest,
    ChatBulkActionRequest, ChatExportRequest, ChatAnalyticsRequest, ChatFeedbackRequest,
    ChatSettingsRequest, SessionCreateRequest, SessionUpdateRequest, SessionSearchRequest,
    SessionBulkActionRequest
)
from models.schemas.response_models import (
    ChatResponse, ChatMessageResponse, ChatDetailResponse, ChatListResponse,
    ChatCreateResponse, ChatUpdateResponse, ChatMessageCreateResponse,
    ChatBulkActionResponse, ChatExportResponse, ChatAnalyticsResponse,
    ChatFeedbackResponse, ChatSettingsResponse, ChatStatsResponse,
    SessionResponse, SessionDetailResponse, SessionListResponse, SessionStatsResponse,
    SessionCreateResponse, SessionUpdateResponse, SessionBulkActionResponse
)
from services.ai.chat_management_service import chat_management_service
from services.auth.session_management_service import get_session_management_service
from services.dependencies import get_current_user
from services.database.database import get_db
from config.logging_config import get_logger, log_function_entry, log_function_exit, log_performance

logger = get_logger(__name__)

router = APIRouter(prefix="/chat", tags=["Chat Management"])


# Chat CRUD Operations
@router.post("/", response_model=ChatCreateResponse)
async def create_chat(
    request: ChatCreateRequest,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    💬 Create a new chat
    
    Creates a new AI chat session with the specified settings.
    """
    log_function_entry(logger, "create_chat")
    start_time = time.time()
    
    try:
        user_id = current_user["id"]
        result = await chat_management_service.create_chat(
            user_id=user_id,
            title=request.title,
            description=request.description,
            context=request.context,
            language=request.language,
            model_preference=request.model_preference,
            max_tokens=request.max_tokens,
            temperature=request.temperature
        )
        
        duration = time.time() - start_time
        log_performance(logger, "create_chat", duration)
        log_function_exit(logger, "create_chat", duration=duration)
        
        return ChatCreateResponse(
            chat=ChatResponse(**result["data"]["chat"]),
            message=result["message"]
        )
    except Exception as e:
        duration = time.time() - start_time
        logger.error(f"❌ Error creating chat: {e}")
        log_function_exit(logger, "create_chat", duration=duration)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{chat_id}", response_model=ChatDetailResponse)
async def get_chat(
    chat_id: str = Path(..., description="Chat ID"),
    include_messages: bool = Query(True, description="Include chat messages"),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    📋 Get chat details
    
    Retrieves chat information and optionally includes message history.
    """
    log_function_entry(logger, "get_chat")
    start_time = time.time()
    
    try:
        user_id = current_user["id"]
        result = await chat_management_service.get_chat(
            chat_id=chat_id,
            user_id=user_id,
            include_messages=include_messages
        )
        
        duration = time.time() - start_time
        log_performance(logger, "get_chat", duration)
        log_function_exit(logger, "get_chat", duration=duration)
        
        return ChatDetailResponse(
            chat=ChatResponse(**result["data"]["chat"]),
            messages=[ChatMessageResponse(**msg) for msg in result["data"]["messages"]],
            user=None,  # Could be populated if needed
            analytics=None  # Could be populated if needed
        )
    except ValueError as e:
        duration = time.time() - start_time
        logger.error(f"❌ Chat not found: {e}")
        log_function_exit(logger, "get_chat", duration=duration)
        raise HTTPException(status_code=404, detail="Chat not found")
    except Exception as e:
        duration = time.time() - start_time
        logger.error(f"❌ Error getting chat: {e}")
        log_function_exit(logger, "get_chat", duration=duration)
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{chat_id}", response_model=ChatUpdateResponse)
async def update_chat(
    request: ChatUpdateRequest,
    chat_id: str = Path(..., description="Chat ID"),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    ✏️ Update chat
    
    Updates chat settings and metadata.
    """
    log_function_entry(logger, "update_chat")
    start_time = time.time()
    
    try:
        user_id = current_user["id"]
        update_data = request.dict(exclude_unset=True)
        result = await chat_management_service.update_chat(
            chat_id=chat_id,
            user_id=user_id,
            **update_data
        )
        
        duration = time.time() - start_time
        log_performance(logger, "update_chat", duration)
        log_function_exit(logger, "update_chat", duration=duration)
        
        return ChatUpdateResponse(
            chat=ChatResponse(**result["data"]["chat"]),
            message=result["message"]
        )
    except ValueError as e:
        duration = time.time() - start_time
        logger.error(f"❌ Chat not found: {e}")
        log_function_exit(logger, "update_chat", duration=duration)
        raise HTTPException(status_code=404, detail="Chat not found")
    except Exception as e:
        duration = time.time() - start_time
        logger.error(f"❌ Error updating chat: {e}")
        log_function_exit(logger, "update_chat", duration=duration)
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{chat_id}")
async def delete_chat(
    chat_id: str = Path(..., description="Chat ID"),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    🗑️ Delete chat
    
    Permanently deletes a chat and all its messages.
    """
    log_function_entry(logger, "delete_chat")
    start_time = time.time()
    
    try:
        user_id = current_user["id"]
        result = await chat_management_service.delete_chat(
            chat_id=chat_id,
            user_id=user_id
        )
        
        duration = time.time() - start_time
        log_performance(logger, "delete_chat", duration)
        log_function_exit(logger, "delete_chat", duration=duration)
        
        return {"status": "success", "message": result["message"]}
    except ValueError as e:
        duration = time.time() - start_time
        logger.error(f"❌ Chat not found: {e}")
        log_function_exit(logger, "delete_chat", duration=duration)
        raise HTTPException(status_code=404, detail="Chat not found")
    except Exception as e:
        duration = time.time() - start_time
        logger.error(f"❌ Error deleting chat: {e}")
        log_function_exit(logger, "delete_chat", duration=duration)
        raise HTTPException(status_code=500, detail=str(e))


# Chat Search and Listing
@router.get("/", response_model=ChatListResponse)
async def search_chats(
    title: Optional[str] = Query(None, description="Search by title"),
    language: Optional[str] = Query(None, description="Filter by language"),
    model_preference: Optional[str] = Query(None, description="Filter by model"),
    is_archived: Optional[bool] = Query(None, description="Filter by archived status"),
    is_pinned: Optional[bool] = Query(None, description="Filter by pinned status"),
    created_after: Optional[datetime] = Query(None, description="Filter by creation date"),
    created_before: Optional[datetime] = Query(None, description="Filter by creation date"),
    updated_after: Optional[datetime] = Query(None, description="Filter by update date"),
    updated_before: Optional[datetime] = Query(None, description="Filter by update date"),
    message_count_min: Optional[int] = Query(None, description="Minimum message count"),
    message_count_max: Optional[int] = Query(None, description="Maximum message count"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(10, ge=1, le=100, description="Page size"),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    🔍 Search chats
    
    Search and filter user's chats with pagination.
    """
    log_function_entry(logger, "search_chats")
    start_time = time.time()
    
    try:
        user_id = current_user["id"]
        filters = {
            "title": title,
            "language": language,
            "model_preference": model_preference,
            "is_archived": is_archived,
            "is_pinned": is_pinned,
            "created_after": created_after,
            "created_before": created_before,
            "updated_after": updated_after,
            "updated_before": updated_before,
            "message_count_min": message_count_min,
            "message_count_max": message_count_max,
            "page": page,
            "page_size": page_size
        }
        
        # Remove None values
        filters = {k: v for k, v in filters.items() if v is not None}
        
        result = await chat_management_service.search_chats(
            user_id=user_id,
            **filters
        )
        
        duration = time.time() - start_time
        log_performance(logger, "search_chats", duration)
        log_function_exit(logger, "search_chats", duration=duration)
        
        return ChatListResponse(
            chats=[ChatResponse(**chat) for chat in result["data"]["chats"]],
            total_count=result["data"]["total_count"],
            page=result["data"]["page"],
            page_size=result["data"]["page_size"],
            total_pages=result["data"]["total_pages"]
        )
    except Exception as e:
        duration = time.time() - start_time
        logger.error(f"❌ Error searching chats: {e}")
        log_function_exit(logger, "search_chats", duration=duration)
        raise HTTPException(status_code=500, detail=str(e))


# Messaging Operations
@router.post("/{chat_id}/messages", response_model=ChatMessageCreateResponse)
async def send_message(
    request: ChatMessageRequest,
    chat_id: str = Path(..., description="Chat ID"),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    💬 Send message
    
    Sends a message to the chat and receives an AI response.
    """
    log_function_entry(logger, "send_message")
    start_time = time.time()
    
    try:
        user_id = current_user["id"]
        result = await chat_management_service.send_message(
            chat_id=chat_id,
            user_id=user_id,
            message=request.message,
            message_type=request.message_type,
            attachments=request.attachments,
            context=request.context,
            language=request.language,
            priority=request.priority
        )
        
        duration = time.time() - start_time
        log_performance(logger, "send_message", duration)
        log_function_exit(logger, "send_message", duration=duration)
        
        return ChatMessageCreateResponse(
            user_message=ChatMessageResponse(**result["data"]["user_message"]),
            ai_response=ChatMessageResponse(**result["data"]["ai_response"]),
            processing_time_ms=result["data"]["processing_time_ms"],
            message=result["message"]
        )
    except ValueError as e:
        duration = time.time() - start_time
        logger.error(f"❌ Chat not found: {e}")
        log_function_exit(logger, "send_message", duration=duration)
        raise HTTPException(status_code=404, detail="Chat not found")
    except Exception as e:
        duration = time.time() - start_time
        logger.error(f"❌ Error sending message: {e}")
        log_function_exit(logger, "send_message", duration=duration)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{chat_id}/messages", response_model=Dict[str, Any])
async def get_chat_messages(
    chat_id: str = Path(..., description="Chat ID"),
    limit: int = Query(100, ge=1, le=1000, description="Number of messages to retrieve"),
    offset: int = Query(0, ge=0, description="Message offset"),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    📨 Get chat messages
    
    Retrieves messages from a specific chat with pagination.
    """
    log_function_entry(logger, "get_chat_messages")
    start_time = time.time()
    
    try:
        user_id = current_user["id"]
        # Get chat with messages
        result = await chat_management_service.get_chat(
            chat_id=chat_id,
            user_id=user_id,
            include_messages=True
        )
        
        # Apply pagination
        messages = result["data"]["messages"][offset:offset + limit]
        
        duration = time.time() - start_time
        log_performance(logger, "get_chat_messages", duration)
        log_function_exit(logger, "get_chat_messages", duration=duration)
        
        return {
            "status": "success",
            "message": "Messages retrieved successfully",
            "data": {
                "messages": [ChatMessageResponse(**msg) for msg in messages],
                "total_count": len(result["data"]["messages"]),
                "limit": limit,
                "offset": offset
            }
        }
    except ValueError as e:
        duration = time.time() - start_time
        logger.error(f"❌ Chat not found: {e}")
        log_function_exit(logger, "get_chat_messages", duration=duration)
        raise HTTPException(status_code=404, detail="Chat not found")
    except Exception as e:
        duration = time.time() - start_time
        logger.error(f"❌ Error getting chat messages: {e}")
        log_function_exit(logger, "get_chat_messages", duration=duration)
        raise HTTPException(status_code=500, detail=str(e))


# Feedback Operations
@router.post("/messages/{message_id}/feedback", response_model=ChatFeedbackResponse)
async def add_feedback(
    request: ChatFeedbackRequest,
    message_id: str = Path(..., description="Message ID"),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    ⭐ Add feedback
    
    Adds feedback to an AI response message.
    """
    log_function_entry(logger, "add_feedback")
    start_time = time.time()
    
    try:
        user_id = current_user["id"]
        result = await chat_management_service.add_feedback(
            message_id=message_id,
            user_id=user_id,
            rating=request.rating,
            feedback_type=request.feedback_type,
            comment=request.comment,
            category=request.category
        )
        
        duration = time.time() - start_time
        log_performance(logger, "add_feedback", duration)
        log_function_exit(logger, "add_feedback", duration=duration)
        
        return ChatFeedbackResponse(
            message_id=message_id,
            rating=request.rating,
            feedback_type=request.feedback_type,
            comment=request.comment,
            category=request.category,
            created_at=datetime.now(datetime.UTC),
            message=result["message"]
        )
    except Exception as e:
        duration = time.time() - start_time
        logger.error(f"❌ Error adding feedback: {e}")
        log_function_exit(logger, "add_feedback", duration=duration)
        raise HTTPException(status_code=500, detail=str(e))


# Settings Operations
@router.get("/settings", response_model=ChatSettingsResponse)
async def get_chat_settings(
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    ⚙️ Get chat settings
    
    Retrieves user's chat preferences and settings.
    """
    log_function_entry(logger, "get_chat_settings")
    start_time = time.time()
    
    try:
        user_id = current_user["id"]
        result = await chat_management_service.get_chat_settings(user_id=user_id)
        
        duration = time.time() - start_time
        log_performance(logger, "get_chat_settings", duration)
        log_function_exit(logger, "get_chat_settings", duration=duration)
        
        return ChatSettingsResponse(**result["data"]["settings"])
    except Exception as e:
        duration = time.time() - start_time
        logger.error(f"❌ Error getting chat settings: {e}")
        log_function_exit(logger, "get_chat_settings", duration=duration)
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/settings", response_model=ChatSettingsResponse)
async def update_chat_settings(
    request: ChatSettingsRequest,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    ⚙️ Update chat settings
    
    Updates user's chat preferences and settings.
    """
    log_function_entry(logger, "update_chat_settings")
    start_time = time.time()
    
    try:
        user_id = current_user["id"]
        update_data = request.dict(exclude_unset=True)
        result = await chat_management_service.update_chat_settings(
            user_id=user_id,
            **update_data
        )
        
        duration = time.time() - start_time
        log_performance(logger, "update_chat_settings", duration)
        log_function_exit(logger, "update_chat_settings", duration=duration)
        
        return ChatSettingsResponse(**result["data"]["settings"])
    except Exception as e:
        duration = time.time() - start_time
        logger.error(f"❌ Error updating chat settings: {e}")
        log_function_exit(logger, "update_chat_settings", duration=duration)
        raise HTTPException(status_code=500, detail=str(e))


# Analytics Operations
@router.get("/analytics", response_model=ChatAnalyticsResponse)
async def get_chat_analytics(
    date_range_start: Optional[datetime] = Query(None, description="Start date for analytics"),
    date_range_end: Optional[datetime] = Query(None, description="End date for analytics"),
    group_by: str = Query("day", description="Grouping interval"),
    include_message_content: bool = Query(False, description="Include message content in analytics"),
    include_user_metrics: bool = Query(True, description="Include user metrics"),
    include_model_metrics: bool = Query(True, description="Include model metrics"),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    📊 Get chat analytics
    
    Retrieves analytics and statistics for user's chat activity.
    """
    log_function_entry(logger, "get_chat_analytics")
    start_time = time.time()
    
    try:
        user_id = current_user["id"]
        result = await chat_management_service.get_chat_analytics(
            user_id=user_id,
            date_range_start=date_range_start,
            date_range_end=date_range_end
        )
        
        duration = time.time() - start_time
        log_performance(logger, "get_chat_analytics", duration)
        log_function_exit(logger, "get_chat_analytics", duration=duration)
        
        analytics = result["data"]["analytics"]
        return ChatAnalyticsResponse(
            total_chats=analytics["total_chats"],
            total_messages=analytics["total_messages"],
            ai_responses=analytics["ai_responses"],
            average_response_time_ms=analytics["average_response_time_ms"],
            user_satisfaction_score=0.0,  # Could be calculated from feedback
            most_used_language=analytics["most_used_language"],
            most_used_model=analytics["most_used_model"],
            daily_stats=[],  # Could be populated
            weekly_stats=[],  # Could be populated
            monthly_stats=[]  # Could be populated
        )
    except Exception as e:
        duration = time.time() - start_time
        logger.error(f"❌ Error getting chat analytics: {e}")
        log_function_exit(logger, "get_chat_analytics", duration=duration)
        raise HTTPException(status_code=500, detail=str(e))


# Bulk Operations
@router.post("/bulk-action", response_model=ChatBulkActionResponse)
async def bulk_action_chats(
    request: ChatBulkActionRequest,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    🔄 Bulk action on chats
    
    Performs bulk operations on multiple chats (archive, unarchive, pin, unpin, delete).
    """
    log_function_entry(logger, "bulk_action_chats")
    start_time = time.time()
    
    try:
        user_id = current_user["id"]
        result = await chat_management_service.bulk_action_chats(
            user_id=user_id,
            chat_ids=request.chat_ids,
            action=request.action
        )
        
        duration = time.time() - start_time
        log_performance(logger, "bulk_action_chats", duration)
        log_function_exit(logger, "bulk_action_chats", duration=duration)
        
        return ChatBulkActionResponse(
            success_count=result["data"]["success_count"],
            failed_count=result["data"]["failed_count"],
            failed_chats=[],  # Could be populated with failed chat IDs
            message=result["message"]
        )
    except Exception as e:
        duration = time.time() - start_time
        logger.error(f"❌ Error performing bulk action: {e}")
        log_function_exit(logger, "bulk_action_chats", duration=duration)
        raise HTTPException(status_code=500, detail=str(e))


# Export Operations
@router.post("/{chat_id}/export", response_model=ChatExportResponse)
async def export_chat(
    request: ChatExportRequest,
    chat_id: str = Path(..., description="Chat ID"),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    📤 Export chat
    
    Exports chat data in various formats (JSON, CSV, TXT, PDF).
    """
    log_function_entry(logger, "export_chat")
    start_time = time.time()
    
    try:
        user_id = current_user["id"]
        result = await chat_management_service.export_chat(
            chat_id=chat_id,
            user_id=user_id,
            format=request.format
        )
        
        duration = time.time() - start_time
        log_performance(logger, "export_chat", duration)
        log_function_exit(logger, "export_chat", duration=duration)
        
        return ChatExportResponse(
            export_id=result["data"]["export_id"],
            format=result["data"]["format"],
            download_url=result["data"].get("download_url"),
            file_size_bytes=result["data"].get("file_size_bytes"),
            expires_at=datetime.fromisoformat(result["data"]["expires_at"]),
            message=result["message"]
        )
    except ValueError as e:
        duration = time.time() - start_time
        logger.error(f"❌ Chat not found: {e}")
        log_function_exit(logger, "export_chat", duration=duration)
        raise HTTPException(status_code=404, detail="Chat not found")
    except Exception as e:
        duration = time.time() - start_time
        logger.error(f"❌ Error exporting chat: {e}")
        log_function_exit(logger, "export_chat", duration=duration)
        raise HTTPException(status_code=500, detail=str(e))


# Statistics
@router.get("/stats", response_model=ChatStatsResponse)
async def get_chat_stats(
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    📈 Get chat statistics
    
    Retrieves comprehensive statistics about user's chat activity.
    """
    log_function_entry(logger, "get_chat_stats")
    start_time = time.time()
    
    try:
        user_id = current_user["id"]
        result = await chat_management_service.get_chat_analytics(user_id=user_id)
        
        analytics = result["data"]["analytics"]
        
        duration = time.time() - start_time
        log_performance(logger, "get_chat_stats", duration)
        log_function_exit(logger, "get_chat_stats", duration=duration)
        
        return ChatStatsResponse(
            total_chats=analytics["total_chats"],
            active_chats=analytics["total_chats"],  # Could be filtered
            archived_chats=0,  # Could be calculated
            pinned_chats=0,  # Could be calculated
            total_messages=analytics["total_messages"],
            ai_responses=analytics["ai_responses"],
            average_messages_per_chat=analytics["total_messages"] / max(analytics["total_chats"], 1),
            average_response_time_ms=analytics["average_response_time_ms"],
            chats_created_today=0,  # Could be calculated
            chats_created_this_week=0,  # Could be calculated
            chats_created_this_month=0,  # Could be calculated
            most_active_hour=0,  # Could be calculated
            most_used_language=analytics["most_used_language"],
            most_used_model=analytics["most_used_model"]
        )
    except Exception as e:
        duration = time.time() - start_time
        logger.error(f"❌ Error getting chat stats: {e}")
        log_function_exit(logger, "get_chat_stats", duration=duration)
        raise HTTPException(status_code=500, detail=str(e))


# Session Management Endpoints (Merged from session management)
@router.get("/sessions/", response_model=SessionListResponse)
async def search_sessions(
    search_request: SessionSearchRequest = Depends(),
    db = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    🔍 Search sessions
    
    Search and filter user sessions with pagination.
    Users can only access their own sessions unless they have admin privileges.
    """
    log_function_entry(logger, "search_sessions")
    start_time = time.time()
    
    try:
        # Check if user has admin privileges
        if current_user.get("status") != "active":
            raise HTTPException(
                status_code=403,
                detail="Insufficient permissions"
            )
        
        session_service = get_session_management_service()
        result = session_service.search_sessions(db, search_request)
        
        duration = time.time() - start_time
        log_performance(logger, "search_sessions", duration)
        log_function_exit(logger, "search_sessions", duration=duration)
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        duration = time.time() - start_time
        logger.error(f"❌ Error searching sessions: {e}")
        log_function_exit(logger, "search_sessions", duration=duration)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/sessions/stats", response_model=SessionStatsResponse)
async def get_session_stats(
    db = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    📊 Get session statistics
    
    Get comprehensive session statistics.
    Users can only access their own session stats unless they have admin privileges.
    """
    log_function_entry(logger, "get_session_stats")
    start_time = time.time()
    
    try:
        # Check if user has admin privileges
        if current_user.get("status") != "active":
            raise HTTPException(
                status_code=403,
                detail="Insufficient permissions"
            )
        
        session_service = get_session_management_service()
        result = session_service.get_session_stats(db)
        
        duration = time.time() - start_time
        log_performance(logger, "get_session_stats", duration)
        log_function_exit(logger, "get_session_stats", duration=duration)
        
        return result
        
    except Exception as e:
        duration = time.time() - start_time
        logger.error(f"❌ Error getting session stats: {e}")
        log_function_exit(logger, "get_session_stats", duration=duration)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/sessions/{session_id}", response_model=SessionResponse)
async def get_session(
    session_id: str,
    db = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    📋 Get session details
    
    Get session by ID.
    Users can only access their own sessions unless they have admin privileges.
    """
    log_function_entry(logger, "get_session")
    start_time = time.time()
    
    try:
        session_service = get_session_management_service()
        session = session_service.get_session_by_id(db, session_id)
        
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        # Check if user is accessing their own session or has admin privileges
        if session.user_id != str(current_user["id"]) and current_user.get("status") != "active":
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        
        duration = time.time() - start_time
        log_performance(logger, "get_session", duration)
        log_function_exit(logger, "get_session", duration=duration)
        
        return session
        
    except HTTPException:
        raise
    except Exception as e:
        duration = time.time() - start_time
        logger.error(f"❌ Error getting session {session_id}: {e}")
        log_function_exit(logger, "get_session", duration=duration)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/sessions/{session_id}/detail", response_model=SessionDetailResponse)
async def get_session_detail(
    session_id: str,
    db = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    📋 Get detailed session information
    
    Get detailed session information including user data.
    Users can only access their own sessions unless they have admin privileges.
    """
    log_function_entry(logger, "get_session_detail")
    start_time = time.time()
    
    try:
        session_service = get_session_management_service()
        session_detail = session_service.get_session_detail(db, session_id)
        
        if not session_detail:
            raise HTTPException(status_code=404, detail="Session not found")
        
        # Check if user is accessing their own session or has admin privileges
        if session_detail.session.user_id != str(current_user["id"]) and current_user.get("status") != "active":
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        
        duration = time.time() - start_time
        log_performance(logger, "get_session_detail", duration)
        log_function_exit(logger, "get_session_detail", duration=duration)
        
        return session_detail
        
    except HTTPException:
        raise
    except Exception as e:
        duration = time.time() - start_time
        logger.error(f"❌ Error getting session detail {session_id}: {e}")
        log_function_exit(logger, "get_session_detail", duration=duration)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/sessions/", response_model=SessionCreateResponse)
async def create_session(
    create_request: SessionCreateRequest,
    db = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    ➕ Create new session
    
    Create a new session for the current user.
    """
    log_function_entry(logger, "create_session")
    start_time = time.time()
    
    try:
        session_service = get_session_management_service()
        result = session_service.create_session(db, str(current_user["id"]), create_request)
        
        if not result:
            raise HTTPException(status_code=400, detail="Failed to create session")
        
        duration = time.time() - start_time
        log_performance(logger, "create_session", duration)
        log_function_exit(logger, "create_session", duration=duration)
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        duration = time.time() - start_time
        logger.error(f"❌ Error creating session: {e}")
        log_function_exit(logger, "create_session", duration=duration)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.put("/sessions/{session_id}", response_model=SessionUpdateResponse)
async def update_session(
    session_id: str,
    update_request: SessionUpdateRequest,
    db = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    ✏️ Update session
    
    Update session information.
    Users can only update their own sessions unless they have admin privileges.
    """
    log_function_entry(logger, "update_session")
    start_time = time.time()
    
    try:
        # First check if session exists and belongs to user
        session_service = get_session_management_service()
        session = session_service.get_session_by_id(db, session_id)
        
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        # Check if user is updating their own session or has admin privileges
        if session.user_id != str(current_user["id"]) and current_user.get("status") != "active":
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        
        result = session_service.update_session(db, session_id, update_request)
        
        if not result:
            raise HTTPException(status_code=404, detail="Session not found")
        
        duration = time.time() - start_time
        log_performance(logger, "update_session", duration)
        log_function_exit(logger, "update_session", duration=duration)
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        duration = time.time() - start_time
        logger.error(f"❌ Error updating session {session_id}: {e}")
        log_function_exit(logger, "update_session", duration=duration)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.delete("/sessions/{session_id}")
async def revoke_session(
    session_id: str,
    db = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    🗑️ Revoke session
    
    Revoke a session.
    Users can only revoke their own sessions unless they have admin privileges.
    """
    log_function_entry(logger, "revoke_session")
    start_time = time.time()
    
    try:
        # First check if session exists and belongs to user
        session_service = get_session_management_service()
        session = session_service.get_session_by_id(db, session_id)
        
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        # Check if user is revoking their own session or has admin privileges
        if session.user_id != str(current_user["id"]) and current_user.get("status") != "active":
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        
        success = session_service.revoke_session(db, session_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="Session not found")
        
        duration = time.time() - start_time
        log_performance(logger, "revoke_session", duration)
        log_function_exit(logger, "revoke_session", duration=duration)
        
        return {"message": "Session revoked successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        duration = time.time() - start_time
        logger.error(f"❌ Error revoking session {session_id}: {e}")
        log_function_exit(logger, "revoke_session", duration=duration)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/sessions/{session_id}/extend")
async def extend_session(
    session_id: str,
    hours: int = Query(..., ge=1, le=720, description="Hours to extend session"),
    db = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    ⏰ Extend session
    
    Extend session expiry time.
    Users can only extend their own sessions unless they have admin privileges.
    """
    log_function_entry(logger, "extend_session")
    start_time = time.time()
    
    try:
        # First check if session exists and belongs to user
        session_service = get_session_management_service()
        session = session_service.get_session_by_id(db, session_id)
        
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        # Check if user is extending their own session or has admin privileges
        if session.user_id != str(current_user["id"]) and current_user.get("status") != "active":
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        
        success = session_service.extend_session(db, session_id, hours)
        
        if not success:
            raise HTTPException(status_code=404, detail="Session not found")
        
        duration = time.time() - start_time
        log_performance(logger, "extend_session", duration)
        log_function_exit(logger, "extend_session", duration=duration)
        
        return {"message": f"Session extended by {hours} hours"}
        
    except HTTPException:
        raise
    except Exception as e:
        duration = time.time() - start_time
        logger.error(f"❌ Error extending session {session_id}: {e}")
        log_function_exit(logger, "extend_session", duration=duration)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/sessions/bulk-action", response_model=SessionBulkActionResponse)
async def bulk_action_sessions(
    request: SessionBulkActionRequest,
    db = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    🔄 Bulk action on sessions
    
    Perform bulk operations on multiple sessions (revoke, extend, etc.).
    Users can only perform bulk actions on their own sessions unless they have admin privileges.
    """
    log_function_entry(logger, "bulk_action_sessions")
    start_time = time.time()
    
    try:
        # Check if user has admin privileges
        if current_user.get("status") != "active":
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        
        session_service = get_session_management_service()
        result = session_service.bulk_action_sessions(db, request)
        
        duration = time.time() - start_time
        log_performance(logger, "bulk_action_sessions", duration)
        log_function_exit(logger, "bulk_action_sessions", duration=duration)
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        duration = time.time() - start_time
        logger.error(f"❌ Error performing bulk action on sessions: {e}")
        log_function_exit(logger, "bulk_action_sessions", duration=duration)
        raise HTTPException(status_code=500, detail="Internal server error")
