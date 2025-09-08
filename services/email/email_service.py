"""
Email service for SyriaGPT.
Handles email sending with dynamic SMTP configuration.
"""

import logging
import aiosmtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional, Dict, Any
from jinja2 import Template

from models.domain.user import User
from config.config_loader import ConfigLoader

logger = logging.getLogger(__name__)


class EmailService:
    """Email service for sending emails with dynamic SMTP configuration."""
    
    def __init__(self, config: ConfigLoader):
        """Initialize email service.
        
        Args:
            config: Configuration loader instance
        """
        self.config = config
        self.smtp_config = config.get_smtp_config()
        self.email_templates = config.get_config_file("email_templates") or {}
    
    async def send_email(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        text_content: Optional[str] = None,
        from_name: Optional[str] = None,
        from_email: Optional[str] = None
    ) -> bool:
        """Send email using configured SMTP.
        
        Args:
            to_email: Recipient email address
            subject: Email subject
            html_content: HTML email content
            text_content: Plain text email content
            from_name: Sender name
            from_email: Sender email address
            
        Returns:
            True if email sent successfully, False otherwise
        """
        try:
            # Use configured values as defaults
            from_name = from_name or self.smtp_config["from_name"]
            from_email = from_email or self.smtp_config["from_address"]
            
            # Create message
            message = MIMEMultipart("alternative")
            message["From"] = f"{from_name} <{from_email}>"
            message["To"] = to_email
            message["Subject"] = subject
            
            # Add text content if provided
            if text_content:
                text_part = MIMEText(text_content, "plain", "utf-8")
                message.attach(text_part)
            
            # Add HTML content
            html_part = MIMEText(html_content, "html", "utf-8")
            message.attach(html_part)
            
            # Send email
            await self._send_smtp_email(message)
            
            logger.info(f"Email sent successfully to {to_email}")
            return True
            
        except Exception as e:
            logger.error(f"Email sending error: {e}")
            return False
    
    async def send_verification_email(self, user: User, verification_token: str) -> bool:
        """Send email verification email.
        
        Args:
            user: User object
            verification_token: Email verification token
            
        Returns:
            True if email sent successfully
        """
        try:
            template_config = self.email_templates.get("email_verification", {})
            
            # Create verification link
            base_url = self.config.get("BASE_URL", "http://localhost:9000")
            verification_link = f"{base_url}/auth/verify-email?token={verification_token}"
            
            # Prepare template variables
            template_vars = {
                "user_name": user.display_name,
                "verification_link": verification_link,
                "expiry_time": "24 hours"
            }
            
            # Generate subject
            subject = template_config.get("subject", "Email Verification - SyriaGPT")
            if user.language_preference == "ar":
                subject = template_config.get("subject_ar", "تأكيد البريد الإلكتروني - SyriaGPT")
            
            # Generate content
            html_content = self._render_template("email_verification", template_vars, "html")
            text_content = self._render_template("email_verification", template_vars, "text")
            
            return await self.send_email(
                to_email=user.email,
                subject=subject,
                html_content=html_content,
                text_content=text_content
            )
            
        except Exception as e:
            logger.error(f"Verification email error: {e}")
            return False
    
    async def send_password_reset_email(self, user: User, reset_token: str) -> bool:
        """Send password reset email.
        
        Args:
            user: User object
            reset_token: Password reset token
            
        Returns:
            True if email sent successfully
        """
        try:
            template_config = self.email_templates.get("password_reset", {})
            
            # Create reset link
            base_url = self.config.get("BASE_URL", "http://localhost:9000")
            reset_link = f"{base_url}/auth/reset-password?token={reset_token}"
            
            # Prepare template variables
            template_vars = {
                "user_name": user.display_name,
                "reset_link": reset_link,
                "expiry_time": "1 hour"
            }
            
            # Generate subject
            subject = template_config.get("subject", "Password Reset - SyriaGPT")
            if user.language_preference == "ar":
                subject = template_config.get("subject_ar", "إعادة تعيين كلمة المرور - SyriaGPT")
            
            # Generate content
            html_content = self._render_template("password_reset", template_vars, "html")
            text_content = self._render_template("password_reset", template_vars, "text")
            
            return await self.send_email(
                to_email=user.email,
                subject=subject,
                html_content=html_content,
                text_content=text_content
            )
            
        except Exception as e:
            logger.error(f"Password reset email error: {e}")
            return False
    
    async def send_password_changed_notification(self, user: User) -> bool:
        """Send password changed notification email.
        
        Args:
            user: User object
            
        Returns:
            True if email sent successfully
        """
        try:
            template_config = self.email_templates.get("password_changed", {})
            
            # Prepare template variables
            template_vars = {
                "user_name": user.display_name,
                "change_time": user.updated_at.strftime("%Y-%m-%d %H:%M:%S UTC"),
                "ip_address": "Unknown"
            }
            
            # Generate subject
            subject = template_config.get("subject", "Password Changed - SyriaGPT")
            if user.language_preference == "ar":
                subject = template_config.get("subject_ar", "تم تغيير كلمة المرور - SyriaGPT")
            
            # Generate content
            html_content = self._render_template("password_changed", template_vars, "html")
            text_content = self._render_template("password_changed", template_vars, "text")
            
            return await self.send_email(
                to_email=user.email,
                subject=subject,
                html_content=html_content,
                text_content=text_content
            )
            
        except Exception as e:
            logger.error(f"Password changed notification error: {e}")
            return False
    
    async def send_two_factor_code_email(self, user: User, code: str) -> bool:
        """Send two-factor authentication code email.
        
        Args:
            user: User object
            code: 2FA code
            
        Returns:
            True if email sent successfully
        """
        try:
            template_config = self.email_templates.get("two_factor_code", {})
            
            # Prepare template variables
            template_vars = {
                "user_name": user.display_name,
                "verification_code": code,
                "expiry_time": "5 minutes"
            }
            
            # Generate subject
            subject = template_config.get("subject", "Two-Factor Authentication Code - SyriaGPT")
            if user.language_preference == "ar":
                subject = template_config.get("subject_ar", "رمز المصادقة الثنائية - SyriaGPT")
            
            # Generate content
            html_content = self._render_template("two_factor_code", template_vars, "html")
            text_content = self._render_template("two_factor_code", template_vars, "text")
            
            return await self.send_email(
                to_email=user.email,
                subject=subject,
                html_content=html_content,
                text_content=text_content
            )
            
        except Exception as e:
            logger.error(f"2FA code email error: {e}")
            return False
    
    async def _send_smtp_email(self, message: MIMEMultipart) -> None:
        """Send email via SMTP.
        
        Args:
            message: Email message
            
        Raises:
            Exception: If email sending fails
        """
        try:
            # Connect to SMTP server
            if self.smtp_config["use_ssl"]:
                smtp = aiosmtplib.SMTP(
                    hostname=self.smtp_config["host"],
                    port=self.smtp_config["port"],
                    use_tls=False,
                    start_tls=False
                )
            else:
                smtp = aiosmtplib.SMTP(
                    hostname=self.smtp_config["host"],
                    port=self.smtp_config["port"],
                    use_tls=self.smtp_config["use_tls"],
                    start_tls=self.smtp_config["use_tls"]
                )
            
            await smtp.connect()
            
            if self.smtp_config["use_tls"] and not self.smtp_config["use_ssl"]:
                await smtp.starttls()
            
            await smtp.login(
                self.smtp_config["username"],
                self.smtp_config["password"]
            )
            
            await smtp.send_message(message)
            await smtp.quit()
            
        except Exception as e:
            logger.error(f"SMTP sending error: {e}")
            raise
    
    def _render_template(self, template_name: str, variables: Dict[str, Any], format_type: str) -> str:
        """Render email template.
        
        Args:
            template_name: Template name
            variables: Template variables
            format_type: Template format (html or text)
            
        Returns:
            Rendered template content
        """
        try:
            # Get template content (in a real implementation, you'd load from files)
            template_content = self._get_template_content(template_name, format_type)
            
            # Render template
            template = Template(template_content)
            return template.render(**variables)
            
        except Exception as e:
            logger.error(f"Template rendering error: {e}")
            # Return fallback content
            return self._get_fallback_content(template_name, variables, format_type)
    
    def _get_template_content(self, template_name: str, format_type: str) -> str:
        """Get template content.
        
        Args:
            template_name: Template name
            format_type: Template format
            
        Returns:
            Template content
        """
        # In a real implementation, you would load templates from files
        # For now, return basic templates
        
        if template_name == "email_verification":
            if format_type == "html":
                return """
                <html>
                <body>
                    <h2>Email Verification</h2>
                    <p>Hello {{ user_name }},</p>
                    <p>Please click the link below to verify your email address:</p>
                    <p><a href="{{ verification_link }}">Verify Email</a></p>
                    <p>This link will expire in {{ expiry_time }}.</p>
                    <p>If you didn't create an account, please ignore this email.</p>
                </body>
                </html>
                """
            else:
                return """
                Email Verification
                
                Hello {{ user_name }},
                
                Please click the link below to verify your email address:
                {{ verification_link }}
                
                This link will expire in {{ expiry_time }}.
                
                If you didn't create an account, please ignore this email.
                """
        
        elif template_name == "password_reset":
            if format_type == "html":
                return """
                <html>
                <body>
                    <h2>Password Reset</h2>
                    <p>Hello {{ user_name }},</p>
                    <p>You requested to reset your password. Click the link below:</p>
                    <p><a href="{{ reset_link }}">Reset Password</a></p>
                    <p>This link will expire in {{ expiry_time }}.</p>
                    <p>If you didn't request this, please ignore this email.</p>
                </body>
                </html>
                """
            else:
                return """
                Password Reset
                
                Hello {{ user_name }},
                
                You requested to reset your password. Click the link below:
                {{ reset_link }}
                
                This link will expire in {{ expiry_time }}.
                
                If you didn't request this, please ignore this email.
                """
        
        # Add more templates as needed
        return f"Template {template_name} ({format_type}) not found"
    
    def _get_fallback_content(self, template_name: str, variables: Dict[str, Any], format_type: str) -> str:
        """Get fallback content when template rendering fails.
        
        Args:
            template_name: Template name
            variables: Template variables
            format_type: Template format
            
        Returns:
            Fallback content
        """
        if format_type == "html":
            return f"""
            <html>
            <body>
                <h2>SyriaGPT Notification</h2>
                <p>Hello {variables.get('user_name', 'User')},</p>
                <p>This is a notification from SyriaGPT.</p>
            </body>
            </html>
            """
        else:
            return f"""
            SyriaGPT Notification
            
            Hello {variables.get('user_name', 'User')},
            
            This is a notification from SyriaGPT.
            """
