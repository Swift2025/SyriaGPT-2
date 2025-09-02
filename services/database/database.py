# database.py
import os
import logging
import time
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from models.domain.base import Base
from config.logging_config import get_logger, log_function_entry, log_function_exit, log_performance, log_error_with_context

logger = get_logger(__name__)

DATABASE_URL = str(os.getenv("DATABASE_URL", "postgresql+psycopg2://admin:admin123@localhost:5432/syriagpt"))

logger.debug(f"🔧 Initializing database connection with URL: {DATABASE_URL.split('@')[1] if '@' in DATABASE_URL else '[REDACTED]'}")

try:
    engine = create_engine(DATABASE_URL)
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