import os
import aiosmtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List, Optional
from jinja2 import Template
import logging
import time

from config.config_loader import config_loader
from services.email.dynamic_smtp_service import dynamic_smtp_service
from config.logging_config import (
    get_logger,
    log_function_entry,
    log_function_exit,
    log_performance,
    log_error_with_context
)

logger = get_logger(__name__)


class EmailService:
    def __init__(self):
        self.smtp_host = os.getenv("SMTP_HOST", "smtp.gmail.com")
        self.smtp_port = int(os.getenv("SMTP_PORT", 587))
        self.smtp_user = os.getenv("SMTP_USER")
        self.smtp_password = os.getenv("SMTP_PASSWORD")
        self.email_from = os.getenv("EMAIL_FROM", "noreply@syriagpt.com")
        self.email_from_name = os.getenv("EMAIL_FROM_NAME", "Syria GPT")
        self.frontend_url = os.getenv("FRONTEND_URL", "http://localhost:3000")
        self.backend_url = os.getenv("BACKEND_URL", "http://localhost:9000")

    async def send_email(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        text_content: Optional[str] = None,
        provider: Optional[str] = None
    ) -> tuple[bool, Optional[str]]:
        """Send email using dynamic SMTP configuration"""
        return await dynamic_smtp_service.send_email(
            to_email=to_email,
            subject=subject,
            html_content=html_content,
            text_content=text_content,
            provider=provider
        )

    async def send_verification_email(
        self,
        to_email: str,
        verification_token: str,
        user_name: Optional[str] = None
    ) -> tuple[bool, Optional[str]]:
        verification_url = f"{self.backend_url}/auth/verify-email/{verification_token}"
        display_name = user_name if user_name else to_email.split('@')[0]
        
        template_config = config_loader.get_email_template("verification")
        subject = template_config.get("subject", "Welcome to Syria GPT - Verify Your Email")
        
        html_content = self._build_verification_html(display_name, verification_url, template_config)
        text_content = template_config.get("text_template", "").format(
            display_name=display_name,
            verification_url=verification_url
        )

        return await self.send_email(
            to_email=to_email,
            subject=subject,
            html_content=html_content,
            text_content=text_content
        )

    async def send_password_reset_email(
        self,
        to_email: str,
        reset_link: str,
        user_name: Optional[str] = None
    ) -> tuple[bool, Optional[str]]:
        display_name = user_name if user_name else to_email.split('@')[0]
        
        template_config = config_loader.get_email_template("password_reset")
        subject = template_config.get("subject", "Reset Your Password - Syria GPT")
        
        html_content = self._build_password_reset_html(display_name, reset_link, template_config)
        text_content = template_config.get("text_template", "").format(
            display_name=display_name,
            reset_link=reset_link
        )

        return await self.send_email(
            to_email=to_email,
            subject=subject,
            html_content=html_content,
            text_content=text_content
        )

    async def send_welcome_email(
        self,
        to_email: str,
        user_name: Optional[str] = None
    ) -> tuple[bool, Optional[str]]:
        display_name = user_name if user_name else to_email.split('@')[0]
        
        template_config = config_loader.get_email_template("welcome")
        subject = template_config.get("subject", "Welcome to Syria GPT - Account Verified!")
        
        html_content = self._build_welcome_html(display_name, template_config)
        text_content = template_config.get("text_template", "").format(
            display_name=display_name,
            frontend_url=self.frontend_url
        )

        return await self.send_email(
            to_email=to_email,
            subject=subject,
            html_content=html_content,
            text_content=text_content
        )

    def is_configured(self) -> bool:
        # For development, allow email service to work without SMTP credentials
        # In production, you would want to require proper SMTP configuration
        if os.getenv("ENV") == "development":
            return True
        return all([
            self.smtp_user,
            self.smtp_password,
            self.smtp_host,
            self.smtp_port
        ])

    async def test_smtp_connection(self, email: str, password: str, provider: Optional[str] = None) -> tuple[bool, str]:
        """Test SMTP connection with the provided credentials"""
        return await dynamic_smtp_service.test_smtp_connection(email, password, provider)

    def get_provider_info(self, provider: str) -> dict:
        """Get information about a specific SMTP provider"""
        return dynamic_smtp_service.get_provider_info(provider)

    def get_all_providers_info(self) -> dict:
        """Get information about all available SMTP providers"""
        return dynamic_smtp_service.get_all_providers_info()

    def detect_provider_from_email(self, email: str) -> str:
        """Detect email provider from email address domain"""
        return dynamic_smtp_service.detect_provider_from_email(email)

    def validate_email_format(self, email: str) -> bool:
        """Validate email format"""
        return dynamic_smtp_service.validate_email_format(email)

    def get_supported_domains(self) -> dict:
        """Get list of supported email domains and their providers"""
        return dynamic_smtp_service.get_supported_domains()

    def _build_verification_html(self, display_name: str, verification_url: str, template_config: dict) -> str:
        html_style = template_config.get("html_style", "")
        
        html_template = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Verify Your Email - Syria GPT</title>
            <style>{html_style}</style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <div class="logo">Syria GPT</div>
                    <h1>Welcome to Syria GPT!</h1>
                </div>
                
                <p>Hello <strong>{display_name}</strong>,</p>
                
                <p>Thank you for signing up with Syria GPT! To complete your registration and start using our services, please verify your email address by clicking the button below:</p>
                
                <div style="text-align: center;">
                    <a href="{verification_url}" class="verify-btn">Verify Email Address</a>
                </div>
                
                <p>If the button above doesn't work, you can also copy and paste the following link into your browser:</p>
                <p style="word-break: break-all; background-color: #f8f9fa; padding: 10px; border-radius: 5px; font-family: monospace;">{verification_url}</p>
                
                <div class="warning">
                    <strong>Security Notice:</strong> This verification link will expire in 24 hours. If you didn't create an account with Syria GPT, please ignore this email.
                </div>
                
                <p>Once verified, you'll be able to access all our features and services. If you have any questions or need assistance, don't hesitate to contact our support team.</p>
                
                <p>Welcome aboard!</p>
                
                <div class="footer">
                    <p>&copy; 2024 Syria GPT. All rights reserved.</p>
                    <p>This is an automated message. Please do not reply to this email.</p>
                </div>
            </div>
        </body>
        </html>
        """
        return html_template

    def _build_welcome_html(self, display_name: str, template_config: dict) -> str:
        html_style = template_config.get("html_style", "")
        
        html_template = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Welcome to Syria GPT</title>
            <style>{html_style}</style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <div class="logo">Syria GPT</div>
                    <h1>Email Successfully Verified!</h1>
                </div>
                
                <div class="success">
                    ✅ Your email has been successfully verified!
                </div>
                
                <p>Hello <strong>{display_name}</strong>,</p>
                
                <p>Congratulations! Your email address has been verified and your Syria GPT account is now fully active.</p>
                
                <p>You can now enjoy all the features and services that Syria GPT has to offer. Start exploring and make the most of your experience with us!</p>
                
                <div style="text-align: center;">
                    <a href="{self.frontend_url}" class="cta-btn">Start Using Syria GPT</a>
                </div>
                
                <p>If you have any questions or need assistance, our support team is here to help.</p>
                
                <p>Thank you for choosing Syria GPT!</p>
                
                <div class="footer">
                    <p>&copy; 2024 Syria GPT. All rights reserved.</p>
                    <p>This is an automated message. Please do not reply to this email.</p>
                </div>
            </div>
        </body>
        </html>
        """
        return html_template

    def _build_password_reset_html(self, display_name: str, reset_link: str, template_config: dict) -> str:
        html_style = template_config.get("html_style", "")
        
        html_template = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Reset Your Password - Syria GPT</title>
            <style>{html_style}</style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <div class="logo">Syria GPT</div>
                    <h1>Reset Your Password</h1>
                </div>
                
                <p>Hello <strong>{display_name}</strong>,</p>
                
                <p>We received a request to reset your password for your Syria GPT account. If you didn't make this request, you can safely ignore this email.</p>
                
                <p>To reset your password, click the button below:</p>
                
                <div style="text-align: center;">
                    <a href="{reset_link}" class="reset-btn">Reset Password</a>
                </div>
                
                <p>If the button above doesn't work, you can also copy and paste the following link into your browser:</p>
                <p style="word-break: break-all; background-color: #f8f9fa; padding: 10px; border-radius: 5px; font-family: monospace;">{reset_link}</p>
                
                <div class="warning">
                    <strong>Security Notice:</strong> This password reset link will expire in 60 minutes. For security reasons, please do not share this link with anyone.
                </div>
                
                <p>If you have any questions or need assistance, please contact our support team.</p>
                
                <div class="footer">
                    <p>&copy; 2024 Syria GPT. All rights reserved.</p>
                    <p>This is an automated message. Please do not reply to this email.</p>
                </div>
            </div>
        </body>
        </html>
        """
        return html_template


# Lazy loading to avoid environment variable issues during import
_email_service_instance = None

def get_email_service():
    log_function_entry(logger, "get_email_service")
    start_time = time.time()
    try:
        global _email_service_instance
        if _email_service_instance is None:
            _email_service_instance = EmailService()
        duration = time.time() - start_time
        log_performance(logger, "get_email_service", duration)
        log_function_exit(logger, "get_email_service", duration=duration)

        return _email_service_instance
    except Exception as e:
        duration = time.time() - start_time
        log_error_with_context(logger, e, "get_email_service", duration=duration)
        logger.error(f"❌ Error in get_email_service: {e}")
        log_function_exit(logger, "get_email_service", duration=duration)
        raise

email_service = get_email_service()