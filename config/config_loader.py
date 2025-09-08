"""
Configuration loader for SyriaGPT application.
Handles environment variables and configuration files.
"""

import os
import json
import logging
from typing import Any, Dict, Optional, Union
from pathlib import Path

logger = logging.getLogger(__name__)


class ConfigLoader:
    """Configuration loader that handles environment variables and JSON config files."""
    
    def __init__(self, config_dir: str = "config"):
        """Initialize configuration loader.
        
        Args:
            config_dir: Directory containing configuration files
        """
        self.config_dir = Path(config_dir)
        self._config_cache: Dict[str, Any] = {}
        self._load_config_files()
    
    def _load_config_files(self):
        """Load configuration from JSON files."""
        config_files = [
            "messages.json",
            "oauth_providers.json", 
            "smtp_providers.json",
            "email_templates.json",
            "identity_responses.json"
        ]
        
        for config_file in config_files:
            file_path = self.config_dir / config_file
            if file_path.exists():
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        config_name = config_file.replace('.json', '')
                        self._config_cache[config_name] = json.load(f)
                        logger.debug(f"Loaded configuration from {config_file}")
                except Exception as e:
                    logger.error(f"Failed to load {config_file}: {e}")
            else:
                logger.warning(f"Configuration file {config_file} not found")
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value from environment variables or config files.
        
        Args:
            key: Configuration key
            default: Default value if key not found
            
        Returns:
            Configuration value
        """
        # First check environment variables
        env_value = os.getenv(key)
        if env_value is not None:
            # Try to convert to appropriate type
            if env_value.lower() in ('true', 'false'):
                return env_value.lower() == 'true'
            try:
                # Try to convert to int
                if '.' not in env_value:
                    return int(env_value)
            except ValueError:
                pass
            try:
                # Try to convert to float
                return float(env_value)
            except ValueError:
                pass
            return env_value
        
        # Check config cache
        if key in self._config_cache:
            return self._config_cache[key]
        
        # Check nested keys in config cache (e.g., "database.host")
        if '.' in key:
            keys = key.split('.')
            value = self._config_cache
            try:
                for k in keys:
                    value = value[k]
                return value
            except (KeyError, TypeError):
                pass
        
        return default
    
    def get_database_url(self) -> str:
        """Get database URL from environment or construct from components."""
        database_url = self.get("DATABASE_URL")
        if database_url:
            return database_url
        
        # Construct from components
        host = self.get("DATABASE_HOST", "localhost")
        port = self.get("DATABASE_PORT", "5432")
        name = self.get("DATABASE_NAME", "syriagpt")
        user = self.get("DATABASE_USER", "admin")
        password = self.get("DATABASE_PASSWORD", "admin123")
        
        return f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{name}"
    
    def get_redis_url(self) -> str:
        """Get Redis URL from environment or construct from components."""
        redis_url = self.get("REDIS_URL")
        if redis_url:
            return redis_url
        
        # Construct from components
        host = self.get("REDIS_HOST", "localhost")
        port = self.get("REDIS_PORT", "6379")
        db = self.get("REDIS_DB", "0")
        
        return f"redis://{host}:{port}/{db}"
    
    def get_qdrant_config(self) -> Dict[str, Any]:
        """Get Qdrant configuration."""
        return {
            "host": self.get("QDRANT_HOST", "localhost"),
            "port": int(self.get("QDRANT_PORT", "6333")),
            "collection": self.get("QDRANT_COLLECTION", "syria_qa_vectors"),
            "api_key": self.get("QDRANT_API_KEY"),
            "embedding_dim": int(self.get("EMBEDDING_DIM", "768")),
            "embedding_model": self.get("EMBEDDING_MODEL", "text-embedding-004")
        }
    
    def get_smtp_config(self) -> Dict[str, Any]:
        """Get SMTP configuration."""
        return {
            "host": self.get("SMTP_HOST", "smtp.gmail.com"),
            "port": int(self.get("SMTP_PORT", "587")),
            "username": self.get("SMTP_USERNAME"),
            "password": self.get("SMTP_PASSWORD"),
            "use_tls": str(self.get("SMTP_USE_TLS", "true")).lower() == "true",
            "use_ssl": str(self.get("SMTP_USE_SSL", "false")).lower() == "true",
            "from_name": self.get("EMAIL_FROM_NAME", "SyriaGPT"),
            "from_address": self.get("EMAIL_FROM_ADDRESS", "noreply@syriagpt.com")
        }
    
    def get_jwt_config(self) -> Dict[str, Any]:
        """Get JWT configuration."""
        return {
            "secret_key": self.get("JWT_SECRET_KEY", self.get("SECRET_KEY", "default-secret")),
            "algorithm": self.get("JWT_ALGORITHM", "HS256"),
            "access_token_expire_minutes": int(self.get("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "30")),
            "refresh_token_expire_days": int(self.get("JWT_REFRESH_TOKEN_EXPIRE_DAYS", "7"))
        }
    
    def get_oauth_config(self) -> Dict[str, Any]:
        """Get OAuth configuration."""
        return {
            "google_client_id": self.get("GOOGLE_CLIENT_ID"),
            "google_client_secret": self.get("GOOGLE_CLIENT_SECRET"),
            "google_redirect_uri": self.get("GOOGLE_REDIRECT_URI", "http://localhost:9000/auth/google/callback")
        }
    
    def get_ai_config(self) -> Dict[str, Any]:
        """Get AI configuration."""
        return {
            "google_api_key": self.get("GOOGLE_API_KEY"),
            "gemini_api_key": self.get("GEMINI_API_KEY"),
            "model_name": self.get("AI_MODEL_NAME", "gemini-pro"),
            "max_tokens": int(self.get("AI_MAX_TOKENS", "2048")),
            "temperature": float(self.get("AI_TEMPERATURE", "0.7")),
            "top_p": float(self.get("AI_TOP_P", "0.8")),
            "top_k": int(self.get("AI_TOP_K", "40"))
        }
    
    def get_logging_config(self) -> Dict[str, Any]:
        """Get logging configuration."""
        return {
            "level": self.get("LOG_LEVEL", "INFO"),
            "ultra_verbose": str(self.get("ULTRA_VERBOSE", "false")).lower() == "true",
            "verbose_modules": self.get("VERBOSE_MODULES", "").split(",") if self.get("VERBOSE_MODULES") else [],
            "file_path": self.get("LOG_FILE_PATH", "logs/syriagpt.log"),
            "max_size": int(self.get("LOG_MAX_SIZE", "10485760")),  # 10MB
            "backup_count": int(self.get("LOG_BACKUP_COUNT", "5"))
        }
    
    def get_rate_limit_config(self) -> Dict[str, Any]:
        """Get rate limiting configuration."""
        return {
            "enabled": str(self.get("RATE_LIMIT_ENABLED", "true")).lower() == "true",
            "requests_per_minute": int(self.get("RATE_LIMIT_REQUESTS_PER_MINUTE", "60")),
            "burst": int(self.get("RATE_LIMIT_BURST", "10"))
        }
    
    def get_chat_config(self) -> Dict[str, Any]:
        """Get chat configuration."""
        return {
            "max_messages": int(self.get("CHAT_MAX_MESSAGES", "100")),
            "session_timeout": int(self.get("CHAT_SESSION_TIMEOUT", "3600")),
            "message_max_length": int(self.get("CHAT_MESSAGE_MAX_LENGTH", "4000"))
        }
    
    def get_totp_config(self) -> Dict[str, Any]:
        """Get TOTP configuration."""
        return {
            "issuer_name": self.get("TOTP_ISSUER_NAME", "SyriaGPT"),
            "algorithm": self.get("TOTP_ALGORITHM", "SHA1"),
            "digits": int(self.get("TOTP_DIGITS", "6")),
            "period": int(self.get("TOTP_PERIOD", "30"))
        }
    
    def is_development(self) -> bool:
        """Check if running in development mode."""
        return str(self.get("ENVIRONMENT", "development")).lower() == "development"
    
    def is_docker(self) -> bool:
        """Check if running in Docker."""
        return str(self.get("DOCKER_ENV", "false")).lower() == "true" or \
               str(self.get("RUNNING_IN_DOCKER", "false")).lower() == "true"
    
    def get_config_file(self, config_name: str) -> Optional[Dict[str, Any]]:
        """Get configuration from a specific JSON file.
        
        Args:
            config_name: Name of the configuration file (without .json)
            
        Returns:
            Configuration dictionary or None if not found
        """
        return self._config_cache.get(config_name)
    
    def reload_config(self):
        """Reload configuration files."""
        self._config_cache.clear()
        self._load_config_files()
        logger.info("Configuration reloaded")
