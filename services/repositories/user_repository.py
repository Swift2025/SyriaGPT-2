from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from sqlalchemy import or_
from models.domain.user import User
from services.database import SessionLocal
import json
import logging
import time
from config.logging_config import get_logger

logger = get_logger(__name__)

class UserRepository:
    def __init__(self):
        logger.debug("Initializing UserRepository")
        self._session = None
    
    def _get_session(self) -> Session:
        """Get or create a database session"""
        if self._session is None:
            logger.debug("Creating new database session for UserRepository")
            self._session = SessionLocal()
        return self._session
    
    def _close_session(self):
        """Close the current session"""
        if self._session:
            logger.debug("Closing UserRepository database session")
            self._session.close()
            self._session = None

    def find_user_by_oauth(self, db: Session, provider: str, provider_id: str) -> Optional[User]:
        logger.debug(f"Finding OAuth user with provider: {provider}, provider_id: {provider_id}")
        try:
            user = db.query(User).filter(
                User.oauth_provider == provider,
                User.oauth_provider_id == provider_id
            ).first()
            logger.debug(f"OAuth user lookup result: {'Found' if user else 'Not found'}")
            return user
        except Exception as e:
            logger.error(f"Error finding OAuth user: {e}")
            return None

    def create_user(self, db: Session, user_data: dict) -> tuple[Optional[User], Optional[str]]:
        try:
            user = User(**user_data)
            db.add(user)
            db.commit()
            db.refresh(user)
            return user, None
        except IntegrityError as e:
            db.rollback()
            error_msg = str(e).lower()
            if "email" in error_msg and "unique" in error_msg:
                return None, "Email already exists"
            elif "phone_number" in error_msg and "unique" in error_msg:
                return None, "Phone number already exists"
            elif "unique" in error_msg:
                return None, "User data conflict - duplicate entry"
            else:
                return None, "Database constraint violation"
        except Exception as e:
            db.rollback()
            logger.error(f"Database error in create_user: {e}")
            return None, "Database error occurred"

    def get_user_by_email(self, db: Session, email: str) -> Optional[User]:
        try:
            return db.query(User).filter(User.email == email).first()
        except Exception as e:
            logger.error(f"Error getting user by email: {e}")
            return None

    def get_user_by_phone(self, db: Session, phone_number: str) -> Optional[User]:
        try:
            return db.query(User).filter(User.phone_number == phone_number).first()
        except Exception as e:
            logger.error(f"Error getting user by phone: {e}")
            return None

    def get_user_by_id(self, db: Session, user_id: str) -> Optional[User]:
        try:
            return db.query(User).filter(User.id == user_id).first()
        except Exception as e:
            logger.error(f"Error getting user by ID: {e}")
            return None

    def get_user_by_token(self, db: Session, token: str) -> Optional[User]:
        try:
            from datetime import datetime, timezone
            return db.query(User).filter(
                User.token == token,
                User.token_expiry > datetime.now(timezone.utc)
            ).first()
        except Exception as e:
            logger.error(f"Error getting user by token: {e}")
            return None

    def update_user(self, db: Session, user_id: str, update_data: dict) -> tuple[Optional[User], Optional[str]]:
        try:
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                return None, "User not found"
            
            for key, value in update_data.items():
                if hasattr(user, key):
                    setattr(user, key, value)
            
            db.commit()
            db.refresh(user)
            return user, None
        except IntegrityError as e:
            db.rollback()
            error_msg = str(e).lower()
            if "email" in error_msg and "unique" in error_msg:
                return None, "Email already exists"
            elif "phone_number" in error_msg and "unique" in error_msg:
                return None, "Phone number already exists"
            elif "unique" in error_msg:
                return None, "Data conflict - duplicate entry"
            else:
                return None, "Database constraint violation"
        except Exception as e:
            db.rollback()
            logger.error(f"Database error in update_user: {e}")
            return None, "Database error occurred"

    def delete_user(self, db: Session, user_id: str) -> tuple[bool, Optional[str]]:
        try:
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                return False, "User not found"
            
            db.delete(user)
            db.commit()
            return True, None
        except Exception as e:
            db.rollback()
            logger.error(f"Database error in delete_user: {e}")
            return False, "Database error occurred"

    def create_oauth_user(self, db: Session, oauth_data: Dict[str, Any]) -> tuple[Optional[User], Optional[str]]:
        try:
            existing_user = None
            if oauth_data.get("email"):
                existing_user = db.query(User).filter(User.email == oauth_data["email"]).first()

            if existing_user:
                if not existing_user.oauth_provider:
                    # Extract OAuth tokens
                    oauth_tokens = oauth_data.get("oauth_tokens", {})
                    from datetime import datetime, timezone, timedelta
                    
                    # Calculate token expiry
                    expires_in = oauth_tokens.get("expires_in")
                    token_expires_at = None
                    if expires_in:
                        token_expires_at = datetime.now(timezone.utc) + timedelta(seconds=expires_in)
                    
                    update_data = {
                        "oauth_provider": oauth_data.get("provider"),
                        "oauth_provider_id": oauth_data.get("provider_id"),
                        "oauth_data": json.dumps(oauth_data) if oauth_data else None,
                        "oauth_access_token": oauth_tokens.get("access_token"),
                        "oauth_refresh_token": oauth_tokens.get("refresh_token"),
                        "oauth_token_expires_at": token_expires_at,
                        "is_email_verified": True,
                        "status": "active",
                        "profile_picture": oauth_data.get("picture"),
                        "full_name": oauth_data.get("name")
                    }
                    
                    for key, value in update_data.items():
                        if hasattr(existing_user, key) and value is not None:
                            setattr(existing_user, key, value)
                    
                    db.commit()
                    db.refresh(existing_user)
                    return existing_user, None
                else:
                    return existing_user, None

            # Extract OAuth tokens
            oauth_tokens = oauth_data.get("oauth_tokens", {})
            from datetime import datetime, timezone, timedelta
            
            # Calculate token expiry
            expires_in = oauth_tokens.get("expires_in")
            token_expires_at = None
            if expires_in:
                token_expires_at = datetime.now(timezone.utc) + timedelta(seconds=expires_in)
            
            user_data = {
                "email": oauth_data.get("email"),
                "oauth_provider": oauth_data.get("provider"),
                "oauth_provider_id": oauth_data.get("provider_id"),
                "oauth_data": json.dumps(oauth_data) if oauth_data else None,
                "oauth_access_token": oauth_tokens.get("access_token"),
                "oauth_refresh_token": oauth_tokens.get("refresh_token"),
                "oauth_token_expires_at": token_expires_at,
                "is_email_verified": True,
                "status": "active",
                "profile_picture": oauth_data.get("picture"),
                "full_name": oauth_data.get("name")
            }

            user = User(**user_data)
            db.add(user)
            db.commit()
            db.refresh(user)
            return user, None

        except IntegrityError as e:
            db.rollback()
            error_msg = str(e).lower()
            if "email" in error_msg and "unique" in error_msg:
                return None, "Email already exists"
            elif "unique" in error_msg:
                return None, "User data conflict - duplicate entry"
            else:
                return None, "Database constraint violation"
        except Exception as e:
            db.rollback()
            logger.error(f"Database error in create_oauth_user: {e}")
            return None, "Database error occurred"

    def find_user_by_email_or_oauth(self, db: Session, email: str = None, provider: str = None, provider_id: str = None) -> Optional[User]:
        try:
            query = db.query(User)
            
            conditions = []
            if email:
                conditions.append(User.email == email)
            if provider and provider_id:
                conditions.append(
                    (User.oauth_provider == provider) & 
                    (User.oauth_provider_id == provider_id)
                )
            
            if conditions:
                return query.filter(or_(*conditions)).first()
            return None
        except Exception as e:
            logger.error(f"Error finding user by email or OAuth: {e}")
            return None

    def update_oauth_tokens(self, db: Session, user_id: str, access_token: str, refresh_token: str = None, expires_in: int = None) -> tuple[bool, Optional[str]]:
        """Update OAuth tokens for a user"""
        try:
            from datetime import datetime, timezone, timedelta
            
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                return False, "User not found"
            
            update_data = {
                "oauth_access_token": access_token,
                "last_login_at": datetime.now(timezone.utc)
            }
            
            if refresh_token:
                update_data["oauth_refresh_token"] = refresh_token
            
            if expires_in:
                update_data["oauth_token_expires_at"] = datetime.now(timezone.utc) + timedelta(seconds=expires_in)
            
            for key, value in update_data.items():
                if hasattr(user, key):
                    setattr(user, key, value)
            
            db.commit()
            db.refresh(user)
            return True, None
            
        except Exception as e:
            db.rollback()
            logger.error(f"Database error in update_oauth_tokens: {e}")
            return False, "Database error occurred"

    def is_oauth_token_expired(self, db: Session, user_id: str) -> bool:
        """Check if OAuth token is expired for a user"""
        try:
            from datetime import datetime, timezone
            
            user = db.query(User).filter(User.id == user_id).first()
            if not user or not user.oauth_token_expires_at:
                return True
            
            return user.oauth_token_expires_at < datetime.now(timezone.utc)
            
        except Exception as e:
            logger.error(f"Error checking OAuth token expiry: {e}")
            return True

    def __del__(self):
        """Cleanup method to ensure session is closed"""
        self._close_session()


user_repository = UserRepository()