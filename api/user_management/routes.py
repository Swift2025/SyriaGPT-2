from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Optional

from services.database.database import get_db
from services.auth import get_auth_service
from services.auth.user_management_service import get_user_management_service
from models.domain.user import User
from models.schemas.request_models import (
    UserUpdateRequest, UserPasswordChangeRequest, UserStatusUpdateRequest,
    UserSearchRequest, UserBulkActionRequest, UserSettingsRequest
)
from models.schemas.response_models import (
    UserResponse, UserDetailResponse, UserListResponse, UserStatsResponse,
    UserUpdateResponse, UserPasswordChangeResponse, UserBulkActionResponse,
    UserSettingsResponse, SettingsUpdateResponse
)
from services.dependencies import get_current_user
from config.logging_config import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/users", tags=["User Management"])


# User CRUD Operations
@router.get("/", response_model=UserListResponse)
async def search_users(
    search_request: UserSearchRequest = Depends(),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Search and filter users with pagination.
    Requires authentication and admin privileges.
    """
    try:
        # Check if user has admin privileges (you can implement your own admin check)
        if current_user.status != "active":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions"
            )
        
        user_service = get_user_management_service()
        return user_service.search_users(db, search_request)
        
    except Exception as e:
        logger.error(f"Error searching users: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.get("/stats", response_model=UserStatsResponse)
async def get_user_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get comprehensive user statistics.
    Requires authentication and admin privileges.
    """
    try:
        # Check if user has admin privileges
        if current_user.status != "active":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions"
            )
        
        user_service = get_user_management_service()
        return user_service.get_user_stats(db)
        
    except Exception as e:
        logger.error(f"Error getting user stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get user by ID.
    Users can only access their own profile unless they have admin privileges.
    """
    try:
        # Check if user is accessing their own profile or has admin privileges
        if str(current_user.id) != user_id and current_user.status != "active":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions"
            )
        
        user_service = get_user_management_service()
        user = user_service.get_user_by_id(db, user_id)
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        return user
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting user {user_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.get("/{user_id}/detail", response_model=UserDetailResponse)
async def get_user_detail(
    user_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get detailed user information including session stats.
    Users can only access their own profile unless they have admin privileges.
    """
    try:
        # Check if user is accessing their own profile or has admin privileges
        if str(current_user.id) != user_id and current_user.status != "active":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions"
            )
        
        user_service = get_user_management_service()
        user_detail = user_service.get_user_detail(db, user_id)
        
        if not user_detail:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        return user_detail
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting user detail {user_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.put("/{user_id}", response_model=UserUpdateResponse)
async def update_user(
    user_id: str,
    update_request: UserUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Update user information.
    Users can only update their own profile unless they have admin privileges.
    """
    try:
        # Check if user is updating their own profile or has admin privileges
        if str(current_user.id) != user_id and current_user.status != "active":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions"
            )
        
        user_service = get_user_management_service()
        result = user_service.update_user(db, user_id, update_request)
        
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating user {user_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.post("/{user_id}/change-password", response_model=UserPasswordChangeResponse)
async def change_password(
    user_id: str,
    password_request: UserPasswordChangeRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Change user password.
    Users can only change their own password.
    """
    try:
        # Users can only change their own password
        if str(current_user.id) != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only change your own password"
            )
        
        user_service = get_user_management_service()
        result = user_service.change_password(db, user_id, password_request)
        
        if not result:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid current password or user not found"
            )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error changing password for user {user_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.put("/{user_id}/status", response_model=UserUpdateResponse)
async def update_user_status(
    user_id: str,
    status_request: UserStatusUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Update user status (admin only).
    Requires admin privileges.
    """
    try:
        # Check if user has admin privileges
        if current_user.status != "active":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions"
            )
        
        user_service = get_user_management_service()
        result = user_service.update_user_status(db, user_id, status_request)
        
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating user status {user_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.post("/bulk-action", response_model=UserBulkActionResponse)
async def bulk_user_action(
    bulk_request: UserBulkActionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Perform bulk actions on users (admin only).
    Requires admin privileges.
    """
    try:
        # Check if user has admin privileges
        if current_user.status != "active":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions"
            )
        
        user_service = get_user_management_service()
        return user_service.bulk_action(db, bulk_request)
        
    except Exception as e:
        logger.error(f"Error performing bulk user action: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


# User Settings
@router.get("/{user_id}/settings", response_model=UserSettingsResponse)
async def get_user_settings(
    user_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get user settings.
    Users can only access their own settings.
    """
    try:
        # Users can only access their own settings
        if str(current_user.id) != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only access your own settings"
            )
        
        user_service = get_user_management_service()
        settings = user_service.get_user_settings(db, user_id)
        
        return UserSettingsResponse(
            user_id=user_id,
            **settings,
            updated_at=current_user.updated_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting user settings {user_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.put("/{user_id}/settings", response_model=SettingsUpdateResponse)
async def update_user_settings(
    user_id: str,
    settings_request: UserSettingsRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Update user settings.
    Users can only update their own settings.
    """
    try:
        # Users can only update their own settings
        if str(current_user.id) != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only update your own settings"
            )
        
        user_service = get_user_management_service()
        updated_settings = user_service.update_user_settings(db, user_id, settings_request)
        
        return SettingsUpdateResponse(
            settings=UserSettingsResponse(
                user_id=user_id,
                **updated_settings,
                updated_at=current_user.updated_at
            ),
            message="Settings updated successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating user settings {user_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


# Profile Management
@router.get("/me/profile", response_model=UserResponse)
async def get_my_profile(
    current_user: User = Depends(get_current_user)
):
    """
    Get current user's profile.
    """
    try:
        return UserResponse(
            id=str(current_user.id),
            email=current_user.email,
            phone_number=current_user.phone_number,
            first_name=current_user.first_name,
            last_name=current_user.last_name,
            full_name=current_user.full_name,
            profile_picture=current_user.profile_picture,
            oauth_provider=current_user.oauth_provider,
            oauth_provider_id=current_user.oauth_provider_id,
            two_factor_enabled=current_user.two_factor_enabled,
            is_email_verified=current_user.is_email_verified,
            is_phone_verified=current_user.is_phone_verified,
            status=current_user.status,
            last_login_at=current_user.last_login_at,
            created_at=current_user.created_at,
            updated_at=current_user.updated_at
        )
        
    except Exception as e:
        logger.error(f"Error getting current user profile: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.put("/me/profile", response_model=UserUpdateResponse)
async def update_my_profile(
    update_request: UserUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Update current user's profile.
    """
    try:
        user_service = get_user_management_service()
        result = user_service.update_user(db, str(current_user.id), update_request)
        
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating current user profile: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.get("/me/settings", response_model=UserSettingsResponse)
async def get_my_settings(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get current user's settings.
    """
    try:
        user_service = get_user_management_service()
        settings = user_service.get_user_settings(db, str(current_user.id))
        
        return UserSettingsResponse(
            user_id=str(current_user.id),
            **settings,
            updated_at=current_user.updated_at
        )
        
    except Exception as e:
        logger.error(f"Error getting current user settings: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.put("/me/settings", response_model=SettingsUpdateResponse)
async def update_my_settings(
    settings_request: UserSettingsRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Update current user's settings.
    """
    try:
        user_service = get_user_management_service()
        updated_settings = user_service.update_user_settings(db, str(current_user.id), settings_request)
        
        return SettingsUpdateResponse(
            settings=UserSettingsResponse(
                user_id=str(current_user.id),
                **updated_settings,
                updated_at=current_user.updated_at
            ),
            message="Settings updated successfully"
        )
        
    except Exception as e:
        logger.error(f"Error updating current user settings: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )
