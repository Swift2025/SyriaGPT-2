# database.py
import os
import logging
import time
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from models.domain.base import Base
from config.logging_config import get_logger, log_function_entry, log_function_exit, log_performance, log_error_with_context

logger = get_logger(__name__)

# Handle DATABASE_URL for different environments
default_db_url = "postgresql+psycopg2://admin:admin123@localhost:5432/syriagpt"
DATABASE_URL = str(os.getenv("DATABASE_URL", default_db_url))

# For Render, ensure the URL is properly formatted
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql+psycopg2://", 1)

logger.debug(f"🔧 Initializing database connection with URL: {DATABASE_URL.split('@')[1] if '@' in DATABASE_URL else '[REDACTED]'}")

try:
    # Configure engine with proper settings for Render
    engine_kwargs = {
        "pool_pre_ping": True,
        "pool_recycle": 300,
        "pool_size": 5,
        "max_overflow": 10,
        "echo": False
    }
    
    # For Render, use more conservative pool settings
    if os.getenv("RENDER"):
        engine_kwargs.update({
            "pool_size": 2,
            "max_overflow": 5,
            "pool_recycle": 180
        })
    
    engine = create_engine(DATABASE_URL, **engine_kwargs)
    logger.debug("✅ Database engine created successfully")
except Exception as e:
    logger.error(f"❌ Failed to create database engine: {e}")
    log_error_with_context(logger, e, "database_engine_creation", database_url=DATABASE_URL.split('@')[1] if '@' in DATABASE_URL else '[REDACTED]')
    raise

try:
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    logger.debug("✅ Database session maker configured")
except Exception as e:
    logger.error(f"❌ Failed to configure session maker: {e}")
    log_error_with_context(logger, e, "session_maker_configuration")
    raise

def get_db() -> Session:
    """Get database session"""
    log_function_entry(logger, "get_db")
    start_time = time.time()
    
    try:
        logger.debug("🔧 Creating new database session...")
        db = SessionLocal()
        logger.debug("✅ Database session created successfully")
        
        duration = time.time() - start_time
        log_performance(logger, "Database session creation", duration)
        
        yield db
        
    except Exception as e:
        duration = time.time() - start_time
        log_error_with_context(logger, e, "get_db", duration=duration)
        logger.error(f"❌ Failed to create database session: {e}")
        raise
    finally:
        try:
            logger.debug("🔧 Closing database session...")
            db.close()
            logger.debug("✅ Database session closed successfully")
        except Exception as e:
            logger.error(f"❌ Failed to close database session: {e}")
            log_error_with_context(logger, e, "database_session_close")