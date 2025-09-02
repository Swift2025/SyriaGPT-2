# In SyriaGPT/services/two_factor_auth_service.py

import pyotp
import qrcode
import io
import base64
import time
import logging
from config.logging_config import (
    get_logger,
    log_function_entry,
    log_function_exit,
    log_performance,
    log_error_with_context
)

# Initialize logger
logger = get_logger(__name__)

class TwoFactorAuthService:
    def generate_secret(self) -> str:
        """
        Generates a new base32 secret key for 2FA.
        """
        return pyotp.random_base32()

    def verify_code(self, secret: str, code: str) -> bool:
        """
        Verifies the 2FA code provided by the user.
        """
        totp = pyotp.TOTP(secret)
        return totp.verify(code)

    def get_provisioning_uri(self, email: str, secret: str, issuer_name: str = "SyriaGPT") -> str:
        """
        Generates the provisioning URI for the authenticator app.
        """
        return pyotp.totp.TOTP(secret).provisioning_uri(
            name=email,
            issuer_name=issuer_name
        )

    def generate_qr_code(self, uri: str) -> str:
        """
        Generates a QR code image from the provisioning URI and returns it as a base64 encoded string.
        """
        img = qrcode.make(uri)
        buffered = io.BytesIO()
        img.save(buffered, format="PNG")
        img_str = base64.b64encode(buffered.getvalue()).decode("utf-8")
        return f"data:image/png;base64,{img_str}"

# Lazy loading to avoid import issues
_two_factor_auth_service_instance = None

def get_two_factor_auth_service():
    log_function_entry(logger, "get_two_factor_auth_service")
    start_time = time.time()
    try:
        global _two_factor_auth_service_instance
        if _two_factor_auth_service_instance is None:
            _two_factor_auth_service_instance = TwoFactorAuthService()
        duration = time.time() - start_time
        log_performance(logger, "get_two_factor_auth_service", duration)
        log_function_exit(logger, "get_two_factor_auth_service", duration=duration)

        return _two_factor_auth_service_instance
    except Exception as e:
        duration = time.time() - start_time
        log_error_with_context(logger, e, "get_two_factor_auth_service", duration=duration)
        logger.error(f"❌ Error in get_two_factor_auth_service: {e}")
        log_function_exit(logger, "get_two_factor_auth_service", duration=duration)
        raise

two_factor_auth_service = get_two_factor_auth_service()