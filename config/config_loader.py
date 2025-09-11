import json
import os
import logging
from config.logging_config import get_logger, log_function_entry, log_function_exit, log_performance, log_error_with_context
import time
from typing import Dict, Any
from pathlib import Path

from .logging_config import get_logger

logger = get_logger(__name__)

class ConfigLoader:
    def __init__(self):
        self.config_path = Path(__file__).parent
        self._messages = None
        self._oauth_providers = None
        self._email_templates = None
        self._smtp_providers = None
        self._identity_responses = None

    def load_messages(self) -> Dict[str, Any]:
        logger.debug("Loading messages configuration")
        if self._messages is None:
            try:
                logger.debug(f"Reading messages from {self.config_path / 'messages.json'}")
                with open(self.config_path / "messages.json", "r", encoding="utf-8") as f:
                    self._messages = json.load(f)
                logger.debug(f"Successfully loaded {len(self._messages)} message categories")
            except FileNotFoundError:
                logger.warning("messages.json not found, using empty dict")
                self._messages = {}
            except json.JSONDecodeError as e:
                logger.error(f"Invalid JSON in messages.json: {e}")
                self._messages = {}
        return self._messages

    def load_oauth_providers(self) -> Dict[str, Any]:
        logger.debug("Loading OAuth providers configuration")
        if self._oauth_providers is None:
            try:
                logger.debug(f"Reading OAuth providers from {self.config_path / 'oauth_providers.json'}")
                with open(self.config_path / "oauth_providers.json", "r", encoding="utf-8") as f:
                    self._oauth_providers = json.load(f)
                logger.debug(f"Successfully loaded {len(self._oauth_providers)} OAuth providers")
            except FileNotFoundError:
                logger.warning("oauth_providers.json not found, using empty dict")
                self._oauth_providers = {}
            except json.JSONDecodeError as e:
                logger.error(f"Invalid JSON in oauth_providers.json: {e}")
                self._oauth_providers = {}
        return self._oauth_providers

    def load_email_templates(self) -> Dict[str, Any]:
        logger.debug("Loading email templates configuration")
        if self._email_templates is None:
            try:
                logger.debug(f"Reading email templates from {self.config_path / 'email_templates.json'}")
                with open(self.config_path / "email_templates.json", "r", encoding="utf-8") as f:
                    self._email_templates = json.load(f)
                logger.debug(f"Successfully loaded {len(self._email_templates)} email templates")
            except FileNotFoundError:
                logger.warning("email_templates.json not found, using empty dict")
                self._email_templates = {}
            except json.JSONDecodeError as e:
                logger.error(f"Invalid JSON in email_templates.json: {e}")
                self._email_templates = {}
        return self._email_templates

    def load_smtp_providers(self) -> Dict[str, Any]:
        logger.debug("Loading SMTP providers configuration")
        if self._smtp_providers is None:
            try:
                logger.debug(f"Reading SMTP providers from {self.config_path / 'smtp_providers.json'}")
                with open(self.config_path / "smtp_providers.json", "r", encoding="utf-8") as f:
                    self._smtp_providers = json.load(f)
                logger.debug(f"Successfully loaded {len(self._smtp_providers)} SMTP providers")
            except FileNotFoundError:
                logger.warning("smtp_providers.json not found, using empty dict")
                self._smtp_providers = {}
            except json.JSONDecodeError as e:
                logger.error(f"Invalid JSON in smtp_providers.json: {e}")
                self._smtp_providers = {}
        return self._smtp_providers

    def load_identity_responses(self) -> Dict[str, Any]:
        """Load identity responses configuration"""
        logger.debug("Loading identity responses configuration")
        if self._identity_responses is None:
            try:
                logger.debug(f"Reading identity responses from {self.config_path / 'identity_responses.json'}")
                with open(self.config_path / "identity_responses.json", "r", encoding="utf-8") as f:
                    self._identity_responses = json.load(f)
                logger.debug(f"Successfully loaded identity responses configuration")
            except FileNotFoundError:
                logger.warning("identity_responses.json not found, using default responses")
                self._identity_responses = self._get_default_identity_responses()
            except json.JSONDecodeError as e:
                logger.error(f"Invalid JSON in identity_responses.json: {e}")
                self._identity_responses = self._get_default_identity_responses()
        return self._identity_responses

    def _get_default_identity_responses(self) -> Dict[str, Any]:
        """Default identity responses if file is not found"""
        return {
            "identity_responses": {
                "who_are_you": {
                    "arabic": "أنا SyriaGPT، نموذج ذكاء اصطناعي تم تدريبي من قبل وكالة نظم المعلومات السورية."
                }
            }
        }

    def get_identity_response(self, response_type: str) -> str:
        """Get identity response for specific type and language"""
        logger.debug(f"Getting identity response for type: {response_type}, language: arabic")
        identity_responses = self.load_identity_responses()
        
        responses = identity_responses.get("identity_responses", {})
        response_data = responses.get(response_type, {})
        
        if response_data:
            response = response_data.get("arabic", response_data.get("arabic", ""))
            if response:
                logger.debug(f"Found identity response: {response[:50]}...")
                return response
        
        # الرد الافتراضي
        default_response = f"أنا SyriaGPT، مساعدك الذكي من وكالة نظم المعلومات السورية."
        logger.warning(f"No identity response found for {response_type}, using default")
        return default_response

    def get_message(self, category: str, key: str, **kwargs) -> str:
        logger.debug(f"Getting message for category: {category}, key: {key}")
        messages = self.load_messages()
        message = messages.get(category, {}).get(key, f"Missing message: {category}.{key}")
        if kwargs:
            try:
                formatted_message = message.format(**kwargs)
                logger.debug(f"Formatted message: {formatted_message}")
                return formatted_message
            except KeyError as e:
                logger.error(f"Message formatting error for {category}.{key}: {e}")
                return f"Message formatting error: {e}"
        logger.debug(f"Returning message: {message}")
        return message

    def get_oauth_provider_config(self, provider: str) -> Dict[str, Any]:
        logger.debug(f"Getting OAuth provider config for: {provider}")
        providers = self.load_oauth_providers()
        config = providers.get(provider, {})
        logger.debug(f"OAuth provider config for {provider}: {len(config)} keys found")
        return config

    def get_email_template(self, template_name: str) -> Dict[str, Any]:
        logger.debug(f"Getting email template: {template_name}")
        templates = self.load_email_templates()
        template = templates.get(template_name, {})
        logger.debug(f"Email template {template_name}: {len(template)} keys found")
        return template

    def get_smtp_provider_config(self, provider: str) -> Dict[str, Any]:
        logger.debug(f"Getting SMTP provider config for: {provider}")
        providers = self.load_smtp_providers()
        config = providers.get(provider, {})
        logger.debug(f"SMTP provider config for {provider}: {len(config)} keys found")
        return config

    def get_all_smtp_providers(self) -> Dict[str, Any]:
        logger.debug("Getting all SMTP providers")
        providers = self.load_smtp_providers()
        logger.debug(f"Found {len(providers)} SMTP providers")
        return providers

    def get_config_value(self, key: str, default: Any = None) -> Any:
        value = os.getenv(key, default)
        logger.debug(f"Config value for {key}: {value if key != 'SECRET_KEY' else '[REDACTED]'}")
        return value


config_loader = ConfigLoader()