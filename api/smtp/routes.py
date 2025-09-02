# /api/smtp/routes.py

import time
from fastapi import APIRouter, HTTPException, status, Depends
from sqlalchemy.orm import Session
from typing import Optional

from models.domain.user import User
from models.schemas.request_models import SMTPTestRequest, SMTPConfigRequest
from models.schemas.response_models import (
    SMTPProvidersResponse, 
    SMTPTestResponse, 
    SMTPConfigResponse,
    SMTPProviderInfo
)
from services.dependencies import get_current_user
from services.database.database import get_db
from services.email.email_service import email_service
from config.logging_config import get_logger, log_function_entry, log_function_exit, log_performance, log_error_with_context

logger = get_logger(__name__)
router = APIRouter(prefix="/smtp", tags=["SMTP Configuration"])


@router.get("/providers", response_model=SMTPProvidersResponse)
async def get_smtp_providers():
    """
    Get all available SMTP providers and their configuration information.
    
    Returns:
        - List of all supported email providers (Gmail, Hotmail, Outlook, etc.)
        - Configuration details for each provider
        - Supported email domains mapping
    """
    log_function_entry(logger, "get_smtp_providers")
    start_time = time.time()
    try:
        providers_info = email_service.get_all_providers_info()
        supported_domains = email_service.get_supported_domains()
        
        return SMTPProvidersResponse(
            providers=providers_info,
            supported_domains=supported_domains
        )
    except Exception as e:
        duration = time.time() - start_time
        log_error_with_context(logger, e, "get_smtp_providers", duration=duration)
        logger.error(f"❌ Error in get_smtp_providers: {e}")
        log_function_exit(logger, "get_smtp_providers", duration=duration)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve SMTP providers: {str(e)}"
        )
    finally:
        duration = time.time() - start_time
        log_performance(logger, "get_smtp_providers", duration)
        log_function_exit(logger, "get_smtp_providers", duration=duration)


@router.get("/providers/{provider}", response_model=SMTPProviderInfo)
async def get_smtp_provider_info(provider: str):
    """
    Get detailed information about a specific SMTP provider.
    
    Args:
        provider: The provider key (e.g., 'gmail', 'hotmail', 'outlook')
    
    Returns:
        - Provider name and configuration details
        - Setup instructions and requirements
        - SMTP server settings
    """
    log_function_entry(logger, "get_smtp_provider_info")
    start_time = time.time()
    try:
        provider_info = email_service.get_provider_info(provider)
        
        if not provider_info:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"SMTP provider '{provider}' not found"
            )
        
        return SMTPProviderInfo(**provider_info)
    except HTTPException:
        raise
    except Exception as e:
        duration = time.time() - start_time
        log_error_with_context(logger, e, "get_smtp_provider_info", duration=duration)
        logger.error(f"❌ Error in get_smtp_provider_info: {e}")
        log_function_exit(logger, "get_smtp_provider_info", duration=duration)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve provider information: {str(e)}"
        )
    finally:
        duration = time.time() - start_time
        log_performance(logger, "get_smtp_provider_info", duration)
        log_function_exit(logger, "get_smtp_provider_info", duration=duration)


@router.post("/test", response_model=SMTPTestResponse)
async def test_smtp_connection(request: SMTPTestRequest):
    """
    Test SMTP connection with provided credentials.
    
    This endpoint will:
    1. Detect the email provider from the email address
    2. Configure SMTP settings automatically
    3. Send a test email to verify the connection
    4. Return detailed results and provider information
    
    Args:
        request: Email, password, and optional provider specification
    
    Returns:
        - Connection test results
        - Detected provider information
        - Success/failure message
    """
    log_function_entry(logger, "test_smtp_connection")
    start_time = time.time()
    try:
        # Validate email format
        if not email_service.validate_email_format(request.email):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid email format"
            )
        
        # Detect provider if not specified
        provider = request.provider
        if not provider:
            provider = email_service.detect_provider_from_email(request.email)
        
        # Test SMTP connection
        success, message = await email_service.test_smtp_connection(
            request.email, 
            request.password, 
            provider
        )
        
        # Get provider info
        provider_info = email_service.get_provider_info(provider)
        
        return SMTPTestResponse(
            success=success,
            message=message,
            provider_detected=provider,
            provider_info=SMTPProviderInfo(**provider_info) if provider_info else None
        )
        
    except HTTPException:
        raise
    except Exception as e:
        duration = time.time() - start_time
        log_error_with_context(logger, e, "test_smtp_connection", duration=duration)
        logger.error(f"❌ Error in test_smtp_connection: {e}")
        log_function_exit(logger, "test_smtp_connection", duration=duration)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"SMTP test failed: {str(e)}"
        )
    finally:
        duration = time.time() - start_time
        log_performance(logger, "test_smtp_connection", duration)
        log_function_exit(logger, "test_smtp_connection", duration=duration)


@router.post("/detect-provider", response_model=SMTPTestResponse)
async def detect_email_provider(email: str):
    """
    Detect the SMTP provider from an email address domain.
    
    Args:
        email: The email address to analyze
    
    Returns:
        - Detected provider information
        - Provider configuration details
    """
    try:
        # Validate email format
        if not email_service.validate_email_format(email):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid email format"
            )
        
        # Detect provider
        provider = email_service.detect_provider_from_email(email)
        
        # Get provider info
        provider_info = email_service.get_provider_info(provider)
        
        return SMTPTestResponse(
            success=True,
            message=f"Provider detected: {provider}",
            provider_detected=provider,
            provider_info=SMTPProviderInfo(**provider_info) if provider_info else None
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Provider detection failed: {str(e)}"
        )


@router.get("/supported-domains")
async def get_supported_domains():
    """
    Get list of supported email domains and their corresponding providers.
    
    Returns:
        - Mapping of email domains to SMTP providers
    """
    log_function_entry(logger, "get_supported_domains")
    start_time = time.time()
    try:
        domains = email_service.get_supported_domains()
        
        return {
            "supported_domains": domains,
            "total_domains": len(domains)
        }
    except Exception as e:
        duration = time.time() - start_time
        log_error_with_context(logger, e, "get_supported_domains", duration=duration)
        logger.error(f"❌ Error in get_supported_domains: {e}")
        log_function_exit(logger, "get_supported_domains", duration=duration)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve supported domains: {str(e)}"
        )
    finally:
        duration = time.time() - start_time
        log_performance(logger, "get_supported_domains", duration)
        log_function_exit(logger, "get_supported_domains", duration=duration)


@router.post("/configure", response_model=SMTPConfigResponse)
async def configure_smtp_settings(request: SMTPConfigRequest):
    """
    Configure SMTP settings for the application.
    
    This endpoint validates the SMTP configuration and provides
    the recommended settings for the specified provider.
    
    Args:
        request: SMTP configuration details
    
    Returns:
        - Recommended SMTP configuration
        - Provider-specific settings
    """
    try:
        # Validate email format
        if not email_service.validate_email_format(request.email):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid email format"
            )
        
        # Detect provider if not specified
        provider = request.provider
        if not provider:
            provider = email_service.detect_provider_from_email(request.email)
        
        # Get provider configuration
        provider_info = email_service.get_provider_info(provider)
        
        if not provider_info:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported provider: {provider}"
            )
        
        # Determine port based on SSL preference
        port = provider_info['smtp_port_ssl'] if request.use_ssl else provider_info['smtp_port']
        
        # Use custom settings if provided
        host = request.custom_host or provider_info['smtp_host']
        port = request.custom_port or port
        
        return SMTPConfigResponse(
            success=True,
            message=f"SMTP configuration for {provider_info['name']}",
            provider=provider,
            host=host,
            port=port,
            use_ssl=request.use_ssl,
            use_tls=provider_info['use_tls'] and not request.use_ssl
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"SMTP configuration failed: {str(e)}"
        )


@router.get("/health")
async def smtp_health_check():
    """
    Check SMTP service health and configuration status.
    
    Returns:
        - Service status
        - Configuration status
        - Available providers
    """
    try:
        is_configured = email_service.is_configured()
        providers_info = email_service.get_all_providers_info()
        supported_domains = email_service.get_supported_domains()
        
        return {
            "status": "healthy",
            "service": "SMTP Configuration",
            "configured": is_configured,
            "available_providers": len(providers_info),
            "supported_domains": len(supported_domains),
            "providers": list(providers_info.keys()),
            "message": "SMTP configuration service is operational"
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"SMTP health check failed: {str(e)}"
        )
