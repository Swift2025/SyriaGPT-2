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
            logger.info(f"🔍 [OAUTH_PROVIDER] Getting user info from {self.name} with code: {code[:10]}...")
            logger.info(f"🔍 [OAUTH_PROVIDER] Redirect URI: {redirect_uri}")
            logger.info(f"🔍 [OAUTH_PROVIDER] Access token URL: {self.access_token_url}")
            logger.info(f"🔍 [OAUTH_PROVIDER] User info URL: {self.user_info_url}")
            logger.info(f"🔍 [OAUTH_PROVIDER] Client ID: {self.client_id[:10]}...")
            
            if not self.client_id or not self.client_secret:
                logger.error(f"❌ [OAUTH_PROVIDER] Missing client credentials for {self.name}")
                return None
            
            client = AsyncOAuth2Client(
                client_id=self.client_id,
                client_secret=self.client_secret
            )
            
            logger.info(f"🔍 [OAUTH_PROVIDER] Fetching token from {self.access_token_url}")
            token = await client.fetch_token(
                self.access_token_url,
                code=code,
                redirect_uri=redirect_uri
            )
            logger.info(f"✅ [OAUTH_PROVIDER] Successfully got token")
            
            logger.info(f"🔍 [OAUTH_PROVIDER] Getting user info from {self.user_info_url}")
            async with httpx.AsyncClient() as http_client:
                response = await http_client.get(
                    self.user_info_url,
                    headers={'Authorization': f"Bearer {token['access_token']}"}
                )
                response.raise_for_status()
                user_info = response.json()
                logger.info(f"✅ [OAUTH_PROVIDER] Successfully got user info: {user_info}")
                
                # Add token information to user info
                user_info['oauth_tokens'] = {
                    'access_token': token.get('access_token'),
                    'refresh_token': token.get('refresh_token'),
                    'expires_in': token.get('expires_in'),
                    'token_type': token.get('token_type', 'Bearer')
                }
                
                return user_info
                
        except Exception as e:
            logger.error(f"❌ [OAUTH_PROVIDER] Failed to get user info from {self.name}: {str(e)}")
            logger.error(f"❌ [OAUTH_PROVIDER] Exception type: {type(e).__name__}")
            logger.error(f"❌ [OAUTH_PROVIDER] Exception details: {str(e)}")
            return None


class OAuthService:
    def __init__(self):
        self.providers = {}
        self._setup_providers()

    def _setup_providers(self):
        provider_configs = config_loader.load_oauth_providers()
        logger.info(f"🔍 [OAUTH_SERVICE] Loaded {len(provider_configs)} provider configs: {list(provider_configs.keys())}")
        
        for provider_name, config in provider_configs.items():
            client_id = config_loader.get_config_value(f"{provider_name.upper()}_CLIENT_ID")
            client_secret = config_loader.get_config_value(f"{provider_name.upper()}_CLIENT_SECRET")
            
            logger.info(f"🔍 [OAUTH_SERVICE] Checking {provider_name}: client_id={'***' if client_id else 'MISSING'}, client_secret={'***' if client_secret else 'MISSING'}")
            
            if client_id and client_secret and client_id != "your-google-client-id-here" and client_secret != "your-google-client-secret-here":
                self.providers[provider_name] = OAuthProvider(
                    name=provider_name,
                    client_id=client_id,
                    client_secret=client_secret,
                    config=config
                )
                logger.info(f"✅ [OAUTH_SERVICE] Successfully configured {provider_name}")
            else:
                logger.warning(f"❌ [OAUTH_SERVICE] OAuth provider {provider_name} not configured - missing or invalid credentials")
                logger.warning(f"❌ [OAUTH_SERVICE] Please set {provider_name.upper()}_CLIENT_ID and {provider_name.upper()}_CLIENT_SECRET in your environment variables")
        
        logger.info(f"🔍 [OAUTH_SERVICE] Total configured providers: {list(self.providers.keys())}")

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
        logger.info(f"🔍 [OAUTH_SERVICE] Getting user info for provider: {provider_name}")
        provider = self.get_provider(provider_name)
        if not provider:
            logger.error(f"❌ [OAUTH_SERVICE] Provider {provider_name} not found. Available providers: {list(self.providers.keys())}")
            logger.error(f"❌ [OAUTH_SERVICE] Please check your OAuth configuration and environment variables")
            return None
        
        logger.info(f"✅ [OAUTH_SERVICE] Provider {provider_name} found, getting user info...")
        try:
            user_info = await provider.get_user_info(code, redirect_uri)
            if not user_info:
                logger.error(f"❌ [OAUTH_SERVICE] Failed to get user info from {provider_name}")
                return None

            logger.info(f"✅ [OAUTH_SERVICE] Successfully got user info from {provider_name}")
            return self._normalize_user_info(provider_name, user_info)
        except Exception as e:
            logger.error(f"❌ [OAUTH_SERVICE] Exception while getting user info from {provider_name}: {str(e)}")
            return None

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