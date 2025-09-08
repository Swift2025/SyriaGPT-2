"""
SMTP configuration API routes for SyriaGPT.
"""

import logging
from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession

from models.schemas.request_models import SMTPConfigRequest, SMTPTestRequest
from models.schemas.response_models import SMTPConfigResponse, SMTPTestResponse, SMTPProviderResponse
from services.database.database import get_db
from services.dependencies import get_current_superuser
from config.config_loader import ConfigLoader

logger = logging.getLogger(__name__)

# Initialize router
smtp_router = APIRouter()

# Initialize services
config = ConfigLoader()

# Security scheme
security = HTTPBearer()


@smtp_router.get("/providers", tags=["SMTP Configuration"])
async def get_smtp_providers():
    """Get available SMTP providers."""
    try:
        providers_config = config.get_config_file("smtp_providers") or {}
        
        providers = []
        for provider_name, provider_config in providers_config.items():
            providers.append(SMTPProviderResponse(
                name=provider_config.get("name", provider_name),
                host=provider_config.get("host", ""),
                port=provider_config.get("port", 587),
                use_tls=provider_config.get("use_tls", True),
                use_ssl=provider_config.get("use_ssl", False),
                authentication=provider_config.get("authentication", "login"),
                enabled=provider_config.get("enabled", True),
                icon=provider_config.get("icon"),
                color=provider_config.get("color"),
                description=provider_config.get("description"),
                setup_instructions=provider_config.get("setup_instructions", []),
                limits=provider_config.get("limits", {})
            ))
        
        return {
            "status": "success",
            "message": "SMTP providers retrieved successfully",
            "providers": providers
        }
        
    except Exception as e:
        logger.error(f"Get SMTP providers error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve SMTP providers"
        )


@smtp_router.get("/config", response_model=SMTPConfigResponse, tags=["SMTP Configuration"])
async def get_smtp_config(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
):
    """Get current SMTP configuration."""
    try:
        # Only superusers can access SMTP configuration
        await get_current_superuser(credentials, db)
        
        smtp_config = config.get_smtp_config()
        
        # Get provider info
        providers_config = config.get_config_file("smtp_providers") or {}
        current_provider = None
        
        for provider_name, provider_config in providers_config.items():
            if provider_config.get("host") == smtp_config["host"]:
                current_provider = SMTPProviderResponse(
                    name=provider_config.get("name", provider_name),
                    host=provider_config.get("host", ""),
                    port=provider_config.get("port", 587),
                    use_tls=provider_config.get("use_tls", True),
                    use_ssl=provider_config.get("use_ssl", False),
                    authentication=provider_config.get("authentication", "login"),
                    enabled=provider_config.get("enabled", True),
                    icon=provider_config.get("icon"),
                    color=provider_config.get("color"),
                    description=provider_config.get("description"),
                    setup_instructions=provider_config.get("setup_instructions", []),
                    limits=provider_config.get("limits", {})
                )
                break
        
        if not current_provider:
            # Create a custom provider response
            current_provider = SMTPProviderResponse(
                name="Custom SMTP",
                host=smtp_config["host"],
                port=smtp_config["port"],
                use_tls=smtp_config["use_tls"],
                use_ssl=smtp_config["use_ssl"],
                authentication="login",
                enabled=True,
                description="Custom SMTP configuration"
            )
        
        return SMTPConfigResponse(
            status="success",
            message="SMTP configuration retrieved successfully",
            provider=current_provider,
            configured=bool(smtp_config.get("username") and smtp_config.get("password"))
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get SMTP config error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve SMTP configuration"
        )


@smtp_router.post("/test", response_model=SMTPTestResponse, tags=["SMTP Configuration"])
async def test_smtp_config(
    request: SMTPTestRequest,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
):
    """Test SMTP configuration by sending a test email."""
    try:
        # Only superusers can test SMTP configuration
        await get_current_superuser(credentials, db)
        
        # Import email service
        from services.email.email_service import EmailService
        email_service = EmailService(config)
        
        # Send test email
        success = await email_service.send_email(
            to_email=request.test_email,
            subject=request.subject,
            html_content=f"<p>{request.message}</p><p>This is a test email from SyriaGPT.</p>",
            text_content=f"{request.message}\n\nThis is a test email from SyriaGPT."
        )
        
        if success:
            return SMTPTestResponse(
                status="success",
                message="Test email sent successfully",
                success=True,
                test_details={
                    "recipient": request.test_email,
                    "subject": request.subject,
                    "sent_at": "now"
                }
            )
        else:
            return SMTPTestResponse(
                status="error",
                message="Failed to send test email",
                success=False,
                test_details={
                    "recipient": request.test_email,
                    "error": "SMTP configuration test failed"
                }
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Test SMTP config error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to test SMTP configuration"
        )


@smtp_router.get("/status", tags=["SMTP Configuration"])
async def get_smtp_status(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
):
    """Get SMTP service status."""
    try:
        # Only superusers can check SMTP status
        await get_current_superuser(credentials, db)
        
        smtp_config = config.get_smtp_config()
        
        # Check if SMTP is configured
        is_configured = bool(
            smtp_config.get("host") and 
            smtp_config.get("username") and 
            smtp_config.get("password")
        )
        
        return {
            "status": "success",
            "message": "SMTP status retrieved successfully",
            "smtp_status": {
                "configured": is_configured,
                "host": smtp_config.get("host"),
                "port": smtp_config.get("port"),
                "use_tls": smtp_config.get("use_tls"),
                "use_ssl": smtp_config.get("use_ssl"),
                "from_address": smtp_config.get("from_address"),
                "from_name": smtp_config.get("from_name")
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get SMTP status error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve SMTP status"
        )
