"""
OAuth service for SyriaGPT.
Handles OAuth authentication with various providers.
"""

import logging
import secrets
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, Tuple
from urllib.parse import urlencode, parse_qs, urlparse
import httpx
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import HTTPException, status

from models.domain.user import User
from models.domain.session import UserSession
from config.config_loader import ConfigLoader

logger = logging.getLogger(__name__)


class OAuthService:
    """OAuth service for handling third-party authentication."""
    
    def __init__(self, config: ConfigLoader):
        """Initialize OAuth service.
        
        Args:
            config: Configuration loader instance
        """
        self.config = config
        self.oauth_config = config.get_oauth_config()
        self.providers_config = config.get_config_file("oauth_providers") or {}
        
        # OAuth state storage (in production, use Redis or database)
        self._oauth_states: Dict[str, Dict[str, Any]] = {}
    
    def get_provider_config(self, provider: str) -> Dict[str, Any]:
        """Get OAuth provider configuration.
        
        Args:
            provider: OAuth provider name
            
        Returns:
            Provider configuration
            
        Raises:
            HTTPException: If provider not found or not enabled
        """
        if provider not in self.providers_config:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"OAuth provider '{provider}' not supported"
            )
        
        provider_config = self.providers_config[provider]
        
        if not provider_config.get("enabled", False):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"OAuth provider '{provider}' is not enabled"
            )
        
        return provider_config
    
    def generate_oauth_state(self, provider: str, redirect_uri: Optional[str] = None) -> str:
        """Generate OAuth state parameter for CSRF protection.
        
        Args:
            provider: OAuth provider name
            redirect_uri: Optional redirect URI
            
        Returns:
            OAuth state string
        """
        state = secrets.token_urlsafe(32)
        
        # Store state with metadata
        self._oauth_states[state] = {
            "provider": provider,
            "redirect_uri": redirect_uri,
            "created_at": datetime.utcnow(),
            "expires_at": datetime.utcnow() + timedelta(minutes=10)
        }
        
        return state
    
    def validate_oauth_state(self, state: str) -> Dict[str, Any]:
        """Validate OAuth state parameter.
        
        Args:
            state: OAuth state string
            
        Returns:
            State metadata
            
        Raises:
            HTTPException: If state is invalid or expired
        """
        if state not in self._oauth_states:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid OAuth state"
            )
        
        state_data = self._oauth_states[state]
        
        if datetime.utcnow() > state_data["expires_at"]:
            del self._oauth_states[state]
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="OAuth state has expired"
            )
        
        return state_data
    
    def get_oauth_authorization_url(self, provider: str, redirect_uri: Optional[str] = None) -> Tuple[str, str]:
        """Get OAuth authorization URL.
        
        Args:
            provider: OAuth provider name
            redirect_uri: Optional redirect URI
            
        Returns:
            Tuple of (authorization_url, state)
        """
        provider_config = self.get_provider_config(provider)
        
        # Generate state for CSRF protection
        state = self.generate_oauth_state(provider, redirect_uri)
        
        # Build authorization URL
        auth_params = {
            "client_id": self._get_provider_credential(provider, "client_id"),
            "response_type": provider_config.get("response_type", "code"),
            "redirect_uri": redirect_uri or provider_config.get("redirect_uri"),
            "state": state,
            "scope": " ".join(provider_config.get("scope", []))
        }
        
        # Add provider-specific parameters
        if provider == "google":
            auth_params.update({
                "access_type": provider_config.get("access_type", "offline"),
                "prompt": provider_config.get("prompt", "consent")
            })
        elif provider == "facebook":
            auth_params["response_type"] = "code"
        elif provider == "twitter":
            auth_params["code_challenge_method"] = provider_config.get("code_challenge_method", "S256")
        
        # Build URL
        auth_url = provider_config["authorization_url"]
        authorization_url = f"{auth_url}?{urlencode(auth_params)}"
        
        logger.info(f"Generated OAuth authorization URL for {provider}")
        return authorization_url, state
    
    async def exchange_code_for_token(self, provider: str, code: str, state: str) -> Dict[str, Any]:
        """Exchange authorization code for access token.
        
        Args:
            provider: OAuth provider name
            code: Authorization code
            state: OAuth state
            
        Returns:
            Token response data
        """
        # Validate state
        state_data = self.validate_oauth_state(state)
        if state_data["provider"] != provider:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="OAuth state provider mismatch"
            )
        
        provider_config = self.get_provider_config(provider)
        
        # Prepare token request
        token_data = {
            "client_id": self._get_provider_credential(provider, "client_id"),
            "client_secret": self._get_provider_credential(provider, "client_secret"),
            "code": code,
            "grant_type": "authorization_code",
            "redirect_uri": state_data.get("redirect_uri") or provider_config.get("redirect_uri")
        }
        
        # Add provider-specific parameters
        if provider == "twitter":
            token_data["code_verifier"] = "dummy"  # In production, use PKCE
        
        # Make token request
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    provider_config["token_url"],
                    data=token_data,
                    headers={"Accept": "application/json"}
                )
                response.raise_for_status()
                token_response = response.json()
                
                logger.info(f"Successfully exchanged code for token with {provider}")
                return token_response
                
            except httpx.HTTPStatusError as e:
                logger.error(f"Token exchange failed for {provider}: {e.response.text}")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Failed to exchange authorization code with {provider}"
                )
            except Exception as e:
                logger.error(f"Token exchange error for {provider}: {e}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="OAuth token exchange failed"
                )
    
    async def get_user_info(self, provider: str, access_token: str) -> Dict[str, Any]:
        """Get user information from OAuth provider.
        
        Args:
            provider: OAuth provider name
            access_token: OAuth access token
            
        Returns:
            User information
        """
        provider_config = self.get_provider_config(provider)
        
        # Prepare headers
        headers = {"Authorization": f"Bearer {access_token}"}
        
        # Add provider-specific headers
        if provider == "github":
            headers["Accept"] = "application/vnd.github.v3+json"
        
        # Make user info request
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    provider_config["user_info_url"],
                    headers=headers
                )
                response.raise_for_status()
                user_info = response.json()
                
                logger.info(f"Successfully retrieved user info from {provider}")
                return user_info
                
            except httpx.HTTPStatusError as e:
                logger.error(f"User info request failed for {provider}: {e.response.text}")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Failed to get user information from {provider}"
                )
            except Exception as e:
                logger.error(f"User info request error for {provider}: {e}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to retrieve user information"
                )
    
    def normalize_user_info(self, provider: str, user_info: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize user information from different OAuth providers.
        
        Args:
            provider: OAuth provider name
            user_info: Raw user information from provider
            
        Returns:
            Normalized user information
        """
        normalized = {
            "provider": provider,
            "provider_id": None,
            "email": None,
            "username": None,
            "first_name": None,
            "last_name": None,
            "full_name": None,
            "avatar_url": None
        }
        
        if provider == "google":
            normalized.update({
                "provider_id": user_info.get("id"),
                "email": user_info.get("email"),
                "first_name": user_info.get("given_name"),
                "last_name": user_info.get("family_name"),
                "full_name": user_info.get("name"),
                "avatar_url": user_info.get("picture")
            })
        elif provider == "facebook":
            normalized.update({
                "provider_id": user_info.get("id"),
                "email": user_info.get("email"),
                "first_name": user_info.get("first_name"),
                "last_name": user_info.get("last_name"),
                "full_name": user_info.get("name"),
                "avatar_url": user_info.get("picture", {}).get("data", {}).get("url")
            })
        elif provider == "github":
            normalized.update({
                "provider_id": str(user_info.get("id")),
                "email": user_info.get("email"),
                "username": user_info.get("login"),
                "full_name": user_info.get("name"),
                "avatar_url": user_info.get("avatar_url")
            })
        elif provider == "twitter":
            normalized.update({
                "provider_id": user_info.get("id"),
                "username": user_info.get("username"),
                "full_name": user_info.get("name"),
                "avatar_url": user_info.get("profile_image_url")
            })
        
        return normalized
    
    async def find_or_create_user(self, db: AsyncSession, normalized_info: Dict[str, Any], tokens: Dict[str, Any]) -> User:
        """Find existing user or create new user from OAuth info.
        
        Args:
            db: Database session
            normalized_info: Normalized user information
            tokens: OAuth tokens
            
        Returns:
            User object
        """
        provider = normalized_info["provider"]
        provider_id = normalized_info["provider_id"]
        email = normalized_info["email"]
        
        # Try to find existing user by OAuth provider and ID
        result = await db.execute(
            select(User).where(
                User.oauth_provider == provider,
                User.oauth_provider_id == provider_id,
                User.is_deleted == 'N'
            )
        )
        user = result.scalar_one_or_none()
        
        if user:
            # Update OAuth tokens
            user.oauth_access_token = tokens.get("access_token")
            user.oauth_refresh_token = tokens.get("refresh_token")
            if tokens.get("expires_in"):
                user.oauth_token_expires = datetime.utcnow() + timedelta(seconds=tokens["expires_in"])
            
            await db.commit()
            logger.info(f"Updated OAuth tokens for existing user {user.id}")
            return user
        
        # Try to find existing user by email
        if email:
            result = await db.execute(
                select(User).where(
                    User.email == email,
                    User.is_deleted == 'N'
                )
            )
            user = result.scalar_one_or_none()
            
            if user:
                # Link OAuth account to existing user
                user.oauth_provider = provider
                user.oauth_provider_id = provider_id
                user.oauth_access_token = tokens.get("access_token")
                user.oauth_refresh_token = tokens.get("refresh_token")
                if tokens.get("expires_in"):
                    user.oauth_token_expires = datetime.utcnow() + timedelta(seconds=tokens["expires_in"])
                
                await db.commit()
                logger.info(f"Linked OAuth account to existing user {user.id}")
                return user
        
        # Create new user
        user = User(
            email=email or f"{provider_id}@{provider}.oauth",
            username=normalized_info.get("username"),
            first_name=normalized_info.get("first_name"),
            last_name=normalized_info.get("last_name"),
            full_name=normalized_info.get("full_name"),
            avatar_url=normalized_info.get("avatar_url"),
            oauth_provider=provider,
            oauth_provider_id=provider_id,
            oauth_access_token=tokens.get("access_token"),
            oauth_refresh_token=tokens.get("refresh_token"),
            is_active=True,
            is_verified=True,  # OAuth users are considered verified
            language_preference="ar",
            timezone="Asia/Damascus"
        )
        
        if tokens.get("expires_in"):
            user.oauth_token_expires = datetime.utcnow() + timedelta(seconds=tokens["expires_in"])
        
        db.add(user)
        await db.commit()
        await db.refresh(user)
        
        logger.info(f"Created new OAuth user {user.id} for {provider}")
        return user
    
    def _get_provider_credential(self, provider: str, credential_type: str) -> str:
        """Get OAuth provider credential from environment.
        
        Args:
            provider: OAuth provider name
            credential_type: Type of credential (client_id, client_secret)
            
        Returns:
            Credential value
            
        Raises:
            HTTPException: If credential not found
        """
        provider_config = self.get_provider_config(provider)
        env_key = provider_config.get(f"{credential_type}_env")
        
        if not env_key:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"OAuth provider {provider} configuration incomplete"
            )
        
        credential = self.config.get(env_key)
        if not credential:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"OAuth credential {env_key} not configured"
            )
        
        return credential
    
    def cleanup_expired_states(self):
        """Clean up expired OAuth states."""
        now = datetime.utcnow()
        expired_states = [
            state for state, data in self._oauth_states.items()
            if now > data["expires_at"]
        ]
        
        for state in expired_states:
            del self._oauth_states[state]
        
        if expired_states:
            logger.info(f"Cleaned up {len(expired_states)} expired OAuth states")
