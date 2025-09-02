import os
from typing import Optional, Dict, Any
from authlib.integrations.httpx_client import AsyncOAuth2Client
from fastapi import HTTPException, status
import httpx
import logging
import time

from config.config_loader import config_loader
from config.logging_config import get_logger, log_function_entry, log_function_exit, log_performance, log_error_with_context

logger = get_logger(__name__)


class OAuthProvider:
    def __init__(self, name: str, client_id: str, client_secret: str, config: Dict[str, Any]):
        self.name = name
        self.client_id = client_id
        self.client_secret = client_secret
        self.authorize_url = config.get("authorize_url")
        self.access_token_url = config.get("access_token_url")
        self.user_info_url = config.get("user_info_url")
        self.scope = config.get("scope", "openid email profile")
        self.user_info_mapping = config.get("user_info_mapping", {})

    def get_authorization_url(self, redirect_uri: str, state: str) -> str:
        client = AsyncOAuth2Client(
            client_id=self.client_id,
            client_secret=self.client_secret
        )
        
        authorization_url, _ = client.create_authorization_url(
            self.authorize_url,
            redirect_uri=redirect_uri,
            state=state,
            scope=self.scope
        )
        
        return authorization_url

    async def get_user_info(self, code: str, redirect_uri: str) -> Optional[Dict[str, Any]]:
        try:
            client = AsyncOAuth2Client(
                client_id=self.client_id,
                client_secret=self.client_secret
            )
            
            token = await client.fetch_token(
                self.access_token_url,
                code=code,
                redirect_uri=redirect_uri
            )
            
            async with httpx.AsyncClient() as http_client:
                response = await http_client.get(
                    self.user_info_url,
                    headers={'Authorization': f"Bearer {token['access_token']}"}
                )
                response.raise_for_status()
                user_info = response.json()
                
                # Add token information to user info
                user_info['oauth_tokens'] = {
                    'access_token': token.get('access_token'),
                    'refresh_token': token.get('refresh_token'),
                    'expires_in': token.get('expires_in'),
                    'token_type': token.get('token_type', 'Bearer')
                }
                
                return user_info
                
        except Exception as e:
            logger.error(f"Failed to get user info from {self.name}: {str(e)}")
            return None


class OAuthService:
    def __init__(self):
        self.providers = {}
        self._setup_providers()

    def _setup_providers(self):
        provider_configs = config_loader.load_oauth_providers()
        
        for provider_name, config in provider_configs.items():
            client_id = config_loader.get_config_value(f"{provider_name.upper()}_CLIENT_ID")
            client_secret = config_loader.get_config_value(f"{provider_name.upper()}_CLIENT_SECRET")
            
            if client_id and client_secret:
                self.providers[provider_name] = OAuthProvider(
                    name=provider_name,
                    client_id=client_id,
                    client_secret=client_secret,
                    config=config
                )
            else:
                logger.warning(f"OAuth provider {provider_name} not configured - missing credentials")

    def get_provider(self, provider_name: str) -> Optional[OAuthProvider]:
        return self.providers.get(provider_name.lower())

    def get_available_providers(self) -> list:
        return list(self.providers.keys())

    def get_authorization_url(self, provider_name: str, redirect_uri: str, state: str) -> str:
        provider = self.get_provider(provider_name)
        if not provider:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"OAuth provider '{provider_name}' is not supported"
            )
        
        return provider.get_authorization_url(redirect_uri, state)

    async def get_user_info(self, provider_name: str, code: str, redirect_uri: str) -> Optional[Dict[str, Any]]:
        provider = self.get_provider(provider_name)
        if not provider:
            return None
        
        user_info = await provider.get_user_info(code, redirect_uri)
        if not user_info:
            return None

        return self._normalize_user_info(provider_name, user_info)

    def _normalize_user_info(self, provider_name: str, user_info: Dict[str, Any]) -> Dict[str, Any]:
        normalized = {
            "provider": provider_name,
            "provider_id": None,
            "email": None,
            "name": None,
            "picture": None,
            "oauth_tokens": user_info.get('oauth_tokens', {})
        }

        provider = self.get_provider(provider_name)
        if provider and provider.user_info_mapping:
            mapping = provider.user_info_mapping
            
            for field, path in mapping.items():
                value = self._get_nested_value(user_info, path)
                normalized[field] = value

        return normalized

    def _get_nested_value(self, data: Dict[str, Any], path: str) -> Any:
        keys = path.split(".")
        value = data
        
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return None
        
        return value

    def is_configured(self, provider_name: str = None) -> bool:
        if provider_name:
            return provider_name.lower() in self.providers
        return len(self.providers) > 0

    async def refresh_oauth_token(self, provider_name: str, refresh_token: str) -> Optional[Dict[str, Any]]:
        """Refresh OAuth access token using refresh token"""
        try:
            provider = self.get_provider(provider_name)
            if not provider:
                logger.error(f"OAuth provider {provider_name} not found")
                return None
            
            client = AsyncOAuth2Client(
                client_id=provider.client_id,
                client_secret=provider.client_secret
            )
            
            # Refresh the token
            token = await client.refresh_token(
                provider.access_token_url,
                refresh_token=refresh_token
            )
            
            return {
                'access_token': token.get('access_token'),
                'refresh_token': token.get('refresh_token'),
                'expires_in': token.get('expires_in'),
                'token_type': token.get('token_type', 'Bearer')
            }
            
        except Exception as e:
            logger.error(f"Failed to refresh OAuth token for {provider_name}: {str(e)}")
            return None


# Lazy loading to avoid environment variable issues during import
_oauth_service_instance = None

def get_oauth_service():
    log_function_entry(logger, "get_oauth_service")
    start_time = time.time()
    try:
        global _oauth_service_instance
        if _oauth_service_instance is None:
            _oauth_service_instance = OAuthService()
        duration = time.time() - start_time
        log_performance(logger, "get_oauth_service", duration)
        log_function_exit(logger, "get_oauth_service", duration=duration)

        return _oauth_service_instance
    except Exception as e:
        duration = time.time() - start_time
        log_error_with_context(logger, e, "get_oauth_service", duration=duration)
        logger.error(f"❌ Error in get_oauth_service: {e}")
        log_function_exit(logger, "get_oauth_service", duration=duration)
        raise

oauth_service = get_oauth_service()