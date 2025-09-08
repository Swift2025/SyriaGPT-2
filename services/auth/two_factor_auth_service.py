"""
Two-factor authentication service for SyriaGPT.
Handles TOTP (Time-based One-Time Password) generation and verification.
"""

import logging
import pyotp
import qrcode
import io
import base64
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import HTTPException, status

from models.domain.user import User
from config.config_loader import ConfigLoader

logger = logging.getLogger(__name__)


class TwoFactorAuthService:
    """Two-factor authentication service using TOTP."""
    
    def __init__(self, config: ConfigLoader):
        """Initialize 2FA service.
        
        Args:
            config: Configuration loader instance
        """
        self.config = config
        self.totp_config = config.get_totp_config()
        
        # TOTP settings
        self.issuer_name = self.totp_config["issuer_name"]
        self.algorithm = self.totp_config["algorithm"]
        self.digits = self.totp_config["digits"]
        self.period = self.totp_config["period"]
    
    def generate_secret(self) -> str:
        """Generate a new TOTP secret.
        
        Returns:
            TOTP secret string
        """
        return pyotp.random_base32()
    
    def generate_qr_code(self, user: User, secret: str) -> str:
        """Generate QR code for TOTP setup.
        
        Args:
            user: User object
            secret: TOTP secret
            
        Returns:
            Base64 encoded QR code image
        """
        # Create TOTP URI
        totp_uri = pyotp.totp.TOTP(secret).provisioning_uri(
            name=user.email,
            issuer_name=self.issuer_name,
            algorithm=self.algorithm
        )
        
        # Generate QR code
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(totp_uri)
        qr.make(fit=True)
        
        # Create image
        img = qr.make_image(fill_color="black", back_color="white")
        
        # Convert to base64
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        img_str = base64.b64encode(buffer.getvalue()).decode()
        
        return f"data:image/png;base64,{img_str}"
    
    def generate_backup_codes(self, count: int = 10) -> List[str]:
        """Generate backup codes for 2FA.
        
        Args:
            count: Number of backup codes to generate
            
        Returns:
            List of backup codes
        """
        import secrets
        import string
        
        codes = []
        for _ in range(count):
            # Generate 8-character alphanumeric code
            code = ''.join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(8))
            codes.append(code)
        
        return codes
    
    def verify_totp_code(self, secret: str, code: str, window: int = 1) -> bool:
        """Verify TOTP code.
        
        Args:
            secret: TOTP secret
            code: TOTP code to verify
            window: Time window for verification (default: 1)
            
        Returns:
            True if code is valid, False otherwise
        """
        try:
            totp = pyotp.TOTP(secret)
            return totp.verify(code, valid_window=window)
        except Exception as e:
            logger.error(f"TOTP verification error: {e}")
            return False
    
    def verify_backup_code(self, user: User, code: str) -> bool:
        """Verify backup code.
        
        Args:
            user: User object
            code: Backup code to verify
            
        Returns:
            True if code is valid, False otherwise
        """
        if not user.two_factor_backup_codes:
            return False
        
        backup_codes = user.two_factor_backup_codes
        if code in backup_codes:
            # Remove used backup code
            backup_codes.remove(code)
            return True
        
        return False
    
    async def setup_two_factor(self, db: AsyncSession, user: User, password: str) -> Dict[str, Any]:
        """Setup two-factor authentication for user.
        
        Args:
            db: Database session
            user: User object
            password: User password for verification
            
        Returns:
            Setup information including QR code and backup codes
            
        Raises:
            HTTPException: If setup fails
        """
        try:
            # Verify password
            from services.auth.auth import AuthService
            auth_service = AuthService(self.config)
            
            if not auth_service.verify_password(password, user.password_hash):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid password"
                )
            
            # Generate new secret and backup codes
            secret = self.generate_secret()
            backup_codes = self.generate_backup_codes()
            qr_code = self.generate_qr_code(user, secret)
            
            # Update user with 2FA information
            user.two_factor_secret = secret
            user.two_factor_backup_codes = backup_codes
            user.two_factor_enabled = True
            
            await db.commit()
            
            logger.info(f"2FA setup completed for user {user.id}")
            
            return {
                "secret": secret,
                "qr_code": qr_code,
                "backup_codes": backup_codes,
                "issuer": self.issuer_name,
                "algorithm": self.algorithm,
                "digits": self.digits,
                "period": self.period
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"2FA setup error for user {user.id}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to setup two-factor authentication"
            )
    
    async def verify_two_factor(self, db: AsyncSession, user: User, code: str) -> bool:
        """Verify two-factor authentication code.
        
        Args:
            db: Database session
            user: User object
            code: 2FA code to verify
            
        Returns:
            True if verification successful, False otherwise
        """
        try:
            if not user.two_factor_enabled or not user.two_factor_secret:
                return False
            
            # Try TOTP code first
            if self.verify_totp_code(user.two_factor_secret, code):
                logger.info(f"TOTP verification successful for user {user.id}")
                return True
            
            # Try backup code
            if self.verify_backup_code(user, code):
                # Update user with new backup codes list
                await db.commit()
                logger.info(f"Backup code verification successful for user {user.id}")
                return True
            
            logger.warning(f"2FA verification failed for user {user.id}")
            return False
            
        except Exception as e:
            logger.error(f"2FA verification error for user {user.id}: {e}")
            return False
    
    async def disable_two_factor(self, db: AsyncSession, user: User, password: str) -> bool:
        """Disable two-factor authentication for user.
        
        Args:
            db: Database session
            user: User object
            password: User password for verification
            
        Returns:
            True if disabled successfully, False otherwise
            
        Raises:
            HTTPException: If disable fails
        """
        try:
            # Verify password
            from services.auth.auth import AuthService
            auth_service = AuthService(self.config)
            
            if not auth_service.verify_password(password, user.password_hash):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid password"
                )
            
            # Disable 2FA
            user.two_factor_enabled = False
            user.two_factor_secret = None
            user.two_factor_backup_codes = None
            
            await db.commit()
            
            logger.info(f"2FA disabled for user {user.id}")
            return True
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"2FA disable error for user {user.id}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to disable two-factor authentication"
            )
    
    async def regenerate_backup_codes(self, db: AsyncSession, user: User, password: str) -> List[str]:
        """Regenerate backup codes for user.
        
        Args:
            db: Database session
            user: User object
            password: User password for verification
            
        Returns:
            New backup codes
            
        Raises:
            HTTPException: If regeneration fails
        """
        try:
            # Verify password
            from services.auth.auth import AuthService
            auth_service = AuthService(self.config)
            
            if not auth_service.verify_password(password, user.password_hash):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid password"
                )
            
            if not user.two_factor_enabled:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Two-factor authentication is not enabled"
                )
            
            # Generate new backup codes
            backup_codes = self.generate_backup_codes()
            user.two_factor_backup_codes = backup_codes
            
            await db.commit()
            
            logger.info(f"Backup codes regenerated for user {user.id}")
            return backup_codes
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Backup codes regeneration error for user {user.id}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to regenerate backup codes"
            )
    
    def get_remaining_backup_codes(self, user: User) -> int:
        """Get number of remaining backup codes.
        
        Args:
            user: User object
            
        Returns:
            Number of remaining backup codes
        """
        if not user.two_factor_backup_codes:
            return 0
        return len(user.two_factor_backup_codes)
    
    def is_two_factor_enabled(self, user: User) -> bool:
        """Check if two-factor authentication is enabled for user.
        
        Args:
            user: User object
            
        Returns:
            True if 2FA is enabled, False otherwise
        """
        return user.two_factor_enabled and user.two_factor_secret is not None
    
    def get_totp_info(self, user: User) -> Dict[str, Any]:
        """Get TOTP information for user.
        
        Args:
            user: User object
            
        Returns:
            TOTP information
        """
        return {
            "enabled": self.is_two_factor_enabled(user),
            "issuer": self.issuer_name,
            "algorithm": self.algorithm,
            "digits": self.digits,
            "period": self.period,
            "remaining_backup_codes": self.get_remaining_backup_codes(user)
        }
    
    async def validate_setup_code(self, user: User, code: str) -> bool:
        """Validate setup code during 2FA setup process.
        
        Args:
            user: User object
            code: Setup code to validate
            
        Returns:
            True if code is valid, False otherwise
        """
        if not user.two_factor_secret:
            return False
        
        return self.verify_totp_code(user.two_factor_secret, code)
