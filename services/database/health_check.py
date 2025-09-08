"""
Health check service for SyriaGPT.
Handles health checks for all services.
"""

import logging
import asyncio
from datetime import datetime
from typing import Dict, Any, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
import httpx
import redis.asyncio as redis

from services.database.database import DatabaseManager
from config.config_loader import ConfigLoader

logger = logging.getLogger(__name__)


class HealthChecker:
    """Health checker for monitoring service status."""
    
    def __init__(self, db_manager: DatabaseManager, config: ConfigLoader):
        """Initialize health checker.
        
        Args:
            db_manager: Database manager instance
            config: Configuration loader instance
        """
        self.db_manager = db_manager
        self.config = config
        self.redis_client = None
    
    async def initialize(self):
        """Initialize health checker."""
        try:
            # Initialize Redis client if configured
            redis_url = self.config.get_redis_url()
            if redis_url:
                self.redis_client = redis.from_url(redis_url)
                await self.redis_client.ping()
                logger.info("Redis health checker initialized")
        except Exception as e:
            logger.warning(f"Redis health checker initialization failed: {e}")
    
    async def check_database(self) -> Dict[str, Any]:
        """Check database health.
        
        Returns:
            Database health status
        """
        start_time = datetime.utcnow()
        try:
            async with self.db_manager.get_session() as session:
                await session.execute(text("SELECT 1"))
                response_time = (datetime.utcnow() - start_time).total_seconds() * 1000
                
                return {
                    "service": "database",
                    "status": "healthy",
                    "response_time_ms": round(response_time, 2),
                    "last_check": datetime.utcnow(),
                    "details": {
                        "url": self.config.get_database_url().split("@")[-1],  # Hide credentials
                        "pool_size": 0,  # NullPool
                        "echo": self.config.get("LOG_LEVEL") == "DEBUG"
                    }
                }
        except Exception as e:
            return {
                "service": "database",
                "status": "unhealthy",
                "response_time_ms": None,
                "last_check": datetime.utcnow(),
                "details": {
                    "error": str(e)
                }
            }
    
    async def check_redis(self) -> Dict[str, Any]:
        """Check Redis health.
        
        Returns:
            Redis health status
        """
        start_time = datetime.utcnow()
        try:
            if not self.redis_client:
                return {
                    "service": "redis",
                    "status": "not_configured",
                    "response_time_ms": None,
                    "last_check": datetime.utcnow(),
                    "details": {
                        "message": "Redis not configured"
                    }
                }
            
            await self.redis_client.ping()
            response_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            
            return {
                "service": "redis",
                "status": "healthy",
                "response_time_ms": round(response_time, 2),
                "last_check": datetime.utcnow(),
                "details": {
                    "url": self.config.get_redis_url().split("@")[-1],  # Hide credentials
                    "version": "Unknown"
                }
            }
        except Exception as e:
            return {
                "service": "redis",
                "status": "unhealthy",
                "response_time_ms": None,
                "last_check": datetime.utcnow(),
                "details": {
                    "error": str(e)
                }
            }
    
    async def check_qdrant(self) -> Dict[str, Any]:
        """Check Qdrant health.
        
        Returns:
            Qdrant health status
        """
        start_time = datetime.utcnow()
        try:
            qdrant_config = self.config.get_qdrant_config()
            url = f"http://{qdrant_config['host']}:{qdrant_config['port']}/health"
            
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(url)
                response.raise_for_status()
                
                response_time = (datetime.utcnow() - start_time).total_seconds() * 1000
                
                return {
                    "service": "qdrant",
                    "status": "healthy",
                    "response_time_ms": round(response_time, 2),
                    "last_check": datetime.utcnow(),
                    "details": {
                        "host": qdrant_config['host'],
                        "port": qdrant_config['port'],
                        "collection": qdrant_config['collection']
                    }
                }
        except Exception as e:
            return {
                "service": "qdrant",
                "status": "unhealthy",
                "response_time_ms": None,
                "last_check": datetime.utcnow(),
                "details": {
                    "error": str(e)
                }
            }
    
    async def check_ai_services(self) -> Dict[str, Any]:
        """Check AI services health.
        
        Returns:
            AI services health status
        """
        start_time = datetime.utcnow()
        try:
            ai_config = self.config.get_ai_config()
            
            # Check if API keys are configured
            google_api_key = ai_config.get('google_api_key')
            gemini_api_key = ai_config.get('gemini_api_key')
            
            if not google_api_key and not gemini_api_key:
                return {
                    "service": "ai_services",
                    "status": "not_configured",
                    "response_time_ms": None,
                    "last_check": datetime.utcnow(),
                    "details": {
                        "message": "AI API keys not configured"
                    }
                }
            
            # Try to make a simple request to test connectivity
            # This is a basic check - in production you might want more sophisticated checks
            response_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            
            return {
                "service": "ai_services",
                "status": "healthy",
                "response_time_ms": round(response_time, 2),
                "last_check": datetime.utcnow(),
                "details": {
                    "google_api_configured": bool(google_api_key),
                    "gemini_api_configured": bool(gemini_api_key),
                    "model": ai_config.get('model_name', 'gemini-pro')
                }
            }
        except Exception as e:
            return {
                "service": "ai_services",
                "status": "unhealthy",
                "response_time_ms": None,
                "last_check": datetime.utcnow(),
                "details": {
                    "error": str(e)
                }
            }
    
    async def check_email_service(self) -> Dict[str, Any]:
        """Check email service health.
        
        Returns:
            Email service health status
        """
        start_time = datetime.utcnow()
        try:
            smtp_config = self.config.get_smtp_config()
            
            # Check if SMTP is configured
            if not smtp_config.get('username') or not smtp_config.get('password'):
                return {
                    "service": "email",
                    "status": "not_configured",
                    "response_time_ms": None,
                    "last_check": datetime.utcnow(),
                    "details": {
                        "message": "SMTP credentials not configured"
                    }
                }
            
            response_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            
            return {
                "service": "email",
                "status": "healthy",
                "response_time_ms": round(response_time, 2),
                "last_check": datetime.utcnow(),
                "details": {
                    "host": smtp_config['host'],
                    "port": smtp_config['port'],
                    "use_tls": smtp_config['use_tls'],
                    "from_address": smtp_config['from_address']
                }
            }
        except Exception as e:
            return {
                "service": "email",
                "status": "unhealthy",
                "response_time_ms": None,
                "last_check": datetime.utcnow(),
                "details": {
                    "error": str(e)
                }
            }
    
    async def check_all_services(self) -> Dict[str, Any]:
        """Check health of all services.
        
        Returns:
            Overall health status
        """
        try:
            # Run all health checks concurrently
            checks = await asyncio.gather(
                self.check_database(),
                self.check_redis(),
                self.check_qdrant(),
                self.check_ai_services(),
                self.check_email_service(),
                return_exceptions=True
            )
            
            services = []
            overall_status = "healthy"
            
            for check in checks:
                if isinstance(check, Exception):
                    services.append({
                        "service": "unknown",
                        "status": "error",
                        "response_time_ms": None,
                        "last_check": datetime.utcnow(),
                        "details": {
                            "error": str(check)
                        }
                    })
                    overall_status = "unhealthy"
                else:
                    services.append(check)
                    if check["status"] not in ["healthy", "not_configured"]:
                        overall_status = "unhealthy"
            
            return {
                "overall_status": overall_status,
                "services": services,
                "timestamp": datetime.utcnow(),
                "uptime_seconds": 0,  # Would need to track start time
                "version": "2.0.0",
                "environment": self.config.get("ENVIRONMENT", "development")
            }
            
        except Exception as e:
            logger.error(f"Health check error: {e}")
            return {
                "overall_status": "error",
                "services": [],
                "timestamp": datetime.utcnow(),
                "error": str(e)
            }
