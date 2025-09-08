"""
Database service for SyriaGPT.
Handles database connection and session management.
"""

import logging
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import NullPool
from config.config_loader import ConfigLoader

logger = logging.getLogger(__name__)


class DatabaseManager:
    """Database manager for handling database connections."""
    
    def __init__(self, config: ConfigLoader):
        """Initialize database manager.
        
        Args:
            config: Configuration loader instance
        """
        self.config = config
        self.database_url = config.get_database_url()
        self.engine = None
        self.session_factory = None
    
    async def initialize(self):
        """Initialize database engine and session factory."""
        try:
            # Convert sync URL to async URL
            async_url = self.database_url.replace("postgresql+psycopg2://", "postgresql+asyncpg://")
            
            # Create async engine
            self.engine = create_async_engine(
                async_url,
                poolclass=NullPool,
                echo=self.config.get("LOG_LEVEL") == "DEBUG",
                future=True
            )
            
            # Create session factory
            self.session_factory = async_sessionmaker(
                self.engine,
                class_=AsyncSession,
                expire_on_commit=False
            )
            
            logger.info("Database manager initialized successfully")
            
        except Exception as e:
            logger.error(f"Database initialization error: {e}")
            raise
    
    async def close(self):
        """Close database connections."""
        try:
            if self.engine:
                await self.engine.dispose()
                logger.info("Database connections closed")
        except Exception as e:
            logger.error(f"Database close error: {e}")
    
    def get_session(self) -> AsyncSession:
        """Get database session.
        
        Returns:
            Database session
        """
        if not self.session_factory:
            raise RuntimeError("Database not initialized")
        return self.session_factory()


# Global database manager instance
db_manager: DatabaseManager = None


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Get database session dependency.
    
    Yields:
        Database session
    """
    global db_manager
    if not db_manager:
        raise RuntimeError("Database manager not initialized")
    
    session = db_manager.get_session()
    try:
        yield session
    finally:
        await session.close()
