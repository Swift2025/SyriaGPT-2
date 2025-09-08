"""
User management API routes for SyriaGPT.
"""

import logging
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession

from models.schemas.request_models import (
    UserUpdateRequest, 
    PasswordChangeRequest, 
    UserPreferencesUpdateRequest
)
from models.schemas.response_models import (
    UserResponse, 
    UserUpdateResponse, 
    UserListResponse,
    UserPreferencesResponse
)
from services.database.database import get_db
from services.dependencies import get_current_user, get_current_superuser
from services.auth.user_management_service import UserManagementService
from config.config_loader import ConfigLoader

logger = logging.getLogger(__name__)

# Initialize router
user_router = APIRouter()

# Initialize services
config = ConfigLoader()
user_management_service = UserManagementService(config)

# Security scheme
security = HTTPBearer()


@user_router.get("/profile", response_model=UserResponse, tags=["User Management"])
async def get_user_profile(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
):
    """Get current user profile."""
    try:
        user = await get_current_user(credentials, db)
        
        return UserResponse(
            id=str(user.id),
            email=user.email,
            username=user.username,
            first_name=user.first_name,
            last_name=user.last_name,
            full_name=user.full_name,
            display_name=user.display_name,
            avatar_url=user.avatar_url,
            bio=user.bio,
            location=user.location,
            website=user.website,
            language_preference=user.language_preference,
            timezone=user.timezone,
            is_active=user.is_active,
            is_verified=user.is_verified,
            is_oauth_user=user.is_oauth_user,
            two_factor_enabled=user.two_factor_enabled,
            last_login_at=user.last_login_at,
            created_at=user.created_at,
            updated_at=user.updated_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get user profile error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve user profile"
        )


@user_router.put("/profile", response_model=UserUpdateResponse, tags=["User Management"])
async def update_user_profile(
    request: UserUpdateRequest,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
):
    """Update current user profile."""
    try:
        user = await get_current_user(credentials, db)
        
        # Update user profile
        updated_user = await user_management_service.update_user_profile(
            db=db,
            user=user,
            username=request.username,
            first_name=request.first_name,
            last_name=request.last_name,
            bio=request.bio,
            location=request.location,
            website=request.website,
            language_preference=request.language_preference,
            timezone=request.timezone
        )
        
        return UserUpdateResponse(
            status="success",
            message="User profile updated successfully",
            user=UserResponse(
                id=str(updated_user.id),
                email=updated_user.email,
                username=updated_user.username,
                first_name=updated_user.first_name,
                last_name=updated_user.last_name,
                full_name=updated_user.full_name,
                display_name=updated_user.display_name,
                avatar_url=updated_user.avatar_url,
                bio=updated_user.bio,
                location=updated_user.location,
                website=updated_user.website,
                language_preference=updated_user.language_preference,
                timezone=updated_user.timezone,
                is_active=updated_user.is_active,
                is_verified=updated_user.is_verified,
                is_oauth_user=updated_user.is_oauth_user,
                two_factor_enabled=updated_user.two_factor_enabled,
                last_login_at=updated_user.last_login_at,
                created_at=updated_user.created_at,
                updated_at=updated_user.updated_at
            )
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Update user profile error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update user profile"
        )


@user_router.post("/change-password", tags=["User Management"])
async def change_password(
    request: PasswordChangeRequest,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
):
    """Change user password."""
    try:
        user = await get_current_user(credentials, db)
        
        # Change password
        success = await user_management_service.change_password(
            db=db,
            user=user,
            current_password=request.current_password,
            new_password=request.new_password
        )
        
        if success:
            return {
                "status": "success",
                "message": "Password changed successfully"
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to change password"
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Change password error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to change password"
        )


@user_router.get("/preferences", response_model=UserPreferencesResponse, tags=["User Management"])
async def get_user_preferences(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
):
    """Get user preferences."""
    try:
        user = await get_current_user(credentials, db)
        
        return UserPreferencesResponse(
            status="success",
            message="User preferences retrieved successfully",
            preferences=user.preferences or {},
            notification_settings=user.notification_settings or {}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get user preferences error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve user preferences"
        )


@user_router.put("/preferences", tags=["User Management"])
async def update_user_preferences(
    request: UserPreferencesUpdateRequest,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
):
    """Update user preferences."""
    try:
        user = await get_current_user(credentials, db)
        
        # Update preferences
        if request.preferences:
            await user_management_service.update_user_preferences(db, user, request.preferences)
        
        # Update notification settings
        if request.notification_settings:
            await user_management_service.update_notification_settings(db, user, request.notification_settings)
        
        return {
            "status": "success",
            "message": "User preferences updated successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Update user preferences error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update user preferences"
        )


@user_router.get("/stats", tags=["User Management"])
async def get_user_stats(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
):
    """Get user statistics."""
    try:
        user = await get_current_user(credentials, db)
        
        # Get user stats
        stats = await user_management_service.get_user_stats(db, user)
        
        return {
            "status": "success",
            "message": "User statistics retrieved successfully",
            "stats": stats
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get user stats error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve user statistics"
        )


@user_router.delete("/account", tags=["User Management"])
async def delete_user_account(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
):
    """Delete user account (soft delete)."""
    try:
        user = await get_current_user(credentials, db)
        
        # Delete user account
        success = await user_management_service.delete_user(db, user)
        
        if success:
            return {
                "status": "success",
                "message": "User account deleted successfully"
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete user account"
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Delete user account error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete user account"
        )


@user_router.get("/", response_model=UserListResponse, tags=["User Management"])
async def get_all_users(
    page: int = 1,
    page_size: int = 20,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
):
    """Get all users (superuser only)."""
    try:
        # Only superusers can access this endpoint
        await get_current_superuser(credentials, db)
        
        # This would require implementing a user repository
        # For now, return empty list
        return UserListResponse(
            status="success",
            message="Users retrieved successfully",
            users=[],
            total_count=0,
            page=page,
            page_size=page_size,
            total_pages=0
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get all users error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve users"
        )
