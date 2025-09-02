import os
import re
import aiosmtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, Any, Optional, Tuple
import logging
import time
from dataclasses import dataclass

from config.config_loader import config_loader
from config.logging_config import (
    get_logger,
    log_function_entry,
    log_function_exit,
    log_performance,
    log_error_with_context
)

logger = get_logger(__name__)


@dataclass
class SMTPConfig:
    """Configuration for SMTP connection"""
    host: str
    port: int
    username: str
    password: str
    use_tls: bool = True
    use_ssl: bool = False
    requires_auth: bool = True


class DynamicSMTPService:
    """Dynamic SMTP service that automatically configures based on email provider"""
    
    def __init__(self):
        self.email_from = os.getenv("EMAIL_FROM", "noreply@syriagpt.com")
        self.email_from_name = os.getenv("EMAIL_FROM_NAME", "Syria GPT")
        self.frontend_url = os.getenv("FRONTEND_URL", "http://localhost:3000")
        self.backend_url = os.getenv("BACKEND_URL", "http://localhost:9000")
        
        # Domain to provider mapping
        self.domain_provider_map = {
            'gmail.com': 'gmail',
            'googlemail.com': 'gmail',
            'hotmail.com': 'hotmail',
            'outlook.com': 'outlook',
            'live.com': 'outlook',
            'msn.com': 'outlook',
            'yahoo.com': 'yahoo',
            'ymail.com': 'yahoo',
            'rocketmail.com': 'yahoo',
            'protonmail.com': 'protonmail',
            'proton.me': 'protonmail',
            'icloud.com': 'icloud',
            'me.com': 'icloud',
            'mac.com': 'icloud',
            'zoho.com': 'zoho'
        }

    def detect_provider_from_email(self, email: str) -> str:
        """Detect email provider from email address domain"""
        domain = email.lower().split('@')[-1]
        
        # Check domain mapping first
        if domain in self.domain_provider_map:
            return self.domain_provider_map[domain]
        
        # Check if it's a custom domain by looking at SMTP providers
        providers = config_loader.get_all_smtp_providers()
        
        # For custom domains, we'll use the 'custom' provider
        # but the user needs to configure the SMTP settings manually
        return 'custom'

    def get_smtp_config(self, email: str, password: str, provider: Optional[str] = None) -> SMTPConfig:
        """Get SMTP configuration for the specified provider or auto-detect from email"""
        
        if not provider:
            provider = self.detect_provider_from_email(email)
        
        provider_config = config_loader.get_smtp_provider_config(provider)
        
        if not provider_config:
            raise ValueError(f"Unknown SMTP provider: {provider}")
        
        # For Gmail, prefer TLS (port 587) over SSL (port 465) for better compatibility
        if provider == 'gmail':
            port = provider_config.get('smtp_port', 587)  # Use TLS port by default
            use_ssl = False
            use_tls = True
        else:
            # Use SSL port if specified, otherwise use regular port
            port = provider_config.get('smtp_port_ssl', provider_config.get('smtp_port', 587))
            use_ssl = provider_config.get('use_ssl', False)
            use_tls = provider_config.get('use_tls', True) if not use_ssl else False
        
        return SMTPConfig(
            host=provider_config['smtp_host'],
            port=port,
            username=email,
            password=password,
            use_tls=use_tls,
            use_ssl=use_ssl,
            requires_auth=provider_config.get('requires_auth', True)
        )

    async def test_smtp_connection(self, email: str, password: str, provider: Optional[str] = None) -> Tuple[bool, str]:
        """Test SMTP connection with the provided credentials"""
        try:
            smtp_config = self.get_smtp_config(email, password, provider)
            
            # Create a test message
            message = MIMEMultipart("alternative")
            message["Subject"] = "SMTP Test - Syria GPT"
            message["From"] = f"{self.email_from_name} <{email}>"
            message["To"] = email
            
            text_part = MIMEText("This is a test email to verify SMTP configuration.", "plain")
            message.attach(text_part)
            
            # Send test email
            await aiosmtplib.send(
                message,
                hostname=smtp_config.host,
                port=smtp_config.port,
                start_tls=smtp_config.use_tls,
                use_tls=smtp_config.use_ssl,
                username=smtp_config.username if smtp_config.requires_auth else None,
                password=smtp_config.password if smtp_config.requires_auth else None,
            )
            
            return True, "SMTP connection test successful"
            
        except Exception as e:
            error_msg = f"SMTP connection test failed: {str(e)}"
            logger.error(error_msg)
            return False, error_msg

    async def send_email(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        text_content: Optional[str] = None,
        from_email: Optional[str] = None,
        from_password: Optional[str] = None,
        provider: Optional[str] = None
    ) -> Tuple[bool, Optional[str]]:
        """Send email using dynamic SMTP configuration with retry logic"""
        
        # Use environment variables if not provided
        if not from_email:
            from_email = os.getenv("SMTP_USER")
        if not from_password:
            from_password = os.getenv("SMTP_PASSWORD")
        
        if not from_email or not from_password:
            # Fallback to development mode
            if os.getenv("ENV") == "development":
                logger.info(f"DEVELOPMENT MODE: Email would be sent to {to_email}")
                logger.info(f"Subject: {subject}")
                logger.info(f"Content: {text_content or html_content[:200]}...")
                return True, None
            else:
                return False, "SMTP credentials not configured"
        
        # Try different SMTP configurations for Gmail
        if not provider:
            provider = self.detect_provider_from_email(from_email)
        
        configs_to_try = []
        
        if provider == 'gmail':
            # Try TLS first (port 587), then SSL (port 465) as fallback
            configs_to_try = [
                {'port': 587, 'use_tls': True, 'use_ssl': False},
                {'port': 465, 'use_tls': False, 'use_ssl': True}
            ]
        else:
            # Use default configuration for other providers
            smtp_config = self.get_smtp_config(from_email, from_password, provider)
            configs_to_try = [{
                'port': smtp_config.port,
                'use_tls': smtp_config.use_tls,
                'use_ssl': smtp_config.use_ssl
            }]
        
        last_error = None
        
        for config in configs_to_try:
            try:
                # Get base SMTP configuration
                smtp_config = self.get_smtp_config(from_email, from_password, provider)
                
                # Override with current config
                smtp_config.port = config['port']
                smtp_config.use_tls = config['use_tls']
                smtp_config.use_ssl = config['use_ssl']
                
                # Create message
                message = MIMEMultipart("alternative")
                message["Subject"] = subject
                message["From"] = f"{self.email_from_name} <{from_email}>"
                message["To"] = to_email
                
                if text_content:
                    text_part = MIMEText(text_content, "plain")
                    message.attach(text_part)
                
                html_part = MIMEText(html_content, "html")
                message.attach(html_part)
                
                # Send email
                await aiosmtplib.send(
                    message,
                    hostname=smtp_config.host,
                    port=smtp_config.port,
                    start_tls=smtp_config.use_tls,
                    use_tls=smtp_config.use_ssl,
                    username=smtp_config.username if smtp_config.requires_auth else None,
                    password=smtp_config.password if smtp_config.requires_auth else None,
                    timeout=30  # Add timeout to prevent hanging
                )
                
                logger.info(f"Email sent successfully to {to_email} using {smtp_config.host}:{smtp_config.port}")
                return True, None
                
            except Exception as e:
                last_error = e
                error_msg = f"Failed to send email using {smtp_config.host}:{smtp_config.port} (TLS:{smtp_config.use_tls}, SSL:{smtp_config.use_ssl}): {str(e)}"
                logger.warning(error_msg)
                continue
        
        # If all configurations failed
        final_error_msg = f"Failed to send email to {to_email} after trying all configurations. Last error: {str(last_error)}"
        logger.error(final_error_msg)
        return False, final_error_msg

    def get_provider_info(self, provider: str) -> Dict[str, Any]:
        """Get information about a specific SMTP provider"""
        provider_config = config_loader.get_smtp_provider_config(provider)
        if not provider_config:
            return {}
        
        return {
            'name': provider_config.get('name', provider),
            'instructions': provider_config.get('instructions', ''),
            'setup_url': provider_config.get('setup_url', ''),
            'app_password_required': provider_config.get('app_password_required', False),
            'smtp_host': provider_config.get('smtp_host', ''),
            'smtp_port': provider_config.get('smtp_port', 587),
            'smtp_port_ssl': provider_config.get('smtp_port_ssl', 465),
            'use_tls': provider_config.get('use_tls', True),
            'use_ssl': provider_config.get('use_ssl', False)
        }

    def get_all_providers_info(self) -> Dict[str, Dict[str, Any]]:
        """Get information about all available SMTP providers"""
        providers = config_loader.get_all_smtp_providers()
        result = {}
        
        for provider_key, provider_config in providers.items():
            result[provider_key] = self.get_provider_info(provider_key)
        
        return result

    def validate_email_format(self, email: str) -> bool:
        """Validate email format"""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None

    def get_supported_domains(self) -> Dict[str, str]:
        """Get list of supported email domains and their providers"""
        return self.domain_provider_map.copy()


# Lazy loading to avoid environment variable issues during import
_dynamic_smtp_service_instance = None

def get_dynamic_smtp_service():
    log_function_entry(logger, "get_dynamic_smtp_service")
    start_time = time.time()
    try:
        global _dynamic_smtp_service_instance
        if _dynamic_smtp_service_instance is None:
            _dynamic_smtp_service_instance = DynamicSMTPService()
        duration = time.time() - start_time
        log_performance(logger, "get_dynamic_smtp_service", duration)
        log_function_exit(logger, "get_dynamic_smtp_service", duration=duration)

        return _dynamic_smtp_service_instance
    except Exception as e:
        duration = time.time() - start_time
        log_error_with_context(logger, e, "get_dynamic_smtp_service", duration=duration)
        logger.error(f"❌ Error in get_dynamic_smtp_service: {e}")
        log_function_exit(logger, "get_dynamic_smtp_service", duration=duration)
        raise

dynamic_smtp_service = get_dynamic_smtp_service()
